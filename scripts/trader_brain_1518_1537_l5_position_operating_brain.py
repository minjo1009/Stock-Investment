from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1508 = ROOT / "data/artifacts/task_1508_1517_bottleneck_verification"
OUT_DIR = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
REPORT_DIR = ROOT / "docs/reports/task_1518_1537_l5_position_operating_brain"

AUTHORITY = "DIAGNOSTIC_L5_POSITION_OPERATING_BRAIN_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0

POLICIES = {
    "l5_operating_top3_v1": 3,
    "l5_operating_top5_v1": 5,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def cagr(start_value: float, end_value: float, start: date, end: date) -> float:
    return replay.cagr(start_value, end_value, start, end)


def expert_audit_rows() -> list[dict[str, object]]:
    rows = [
        ("institutional_pm", "adopt", "L5 must become a position operating layer, not another broad ranker"),
        ("event_driven_trader", "adopt", "thesis state must decide hold versus exit; price drop alone is not thesis invalidation"),
        ("quant_risk", "modify", "position sizing must remain cap-only or shadow until entry/exit delta improves"),
        ("portfolio_construction", "adopt", "replacement must be narrow, same-cohort, and turnover constrained"),
        ("implementation_shortfall", "adopt", "actual L5 must beat scheduled-only before claiming implementation value"),
        ("momentum_research", "adopt", "market absorption and continuation can support hold extension but must be audited"),
        ("backend_governance", "adopt", "outcome returns can only appear in delta audit, never assignment"),
    ]
    return [
        {
            "task_id": "Task1518",
            "audit_id": f"L5AUDIT1518-{idx:03d}",
            "expert_role": role,
            "verdict": verdict,
            "feedback": feedback,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, verdict, feedback) in enumerate(rows, 1)
    ]


def preregister_policy_rows() -> list[dict[str, object]]:
    rules = [
        ("thesis_state_machine", "derive active/confirmed/stale/invalidated/source_gap states from L2/L3 semantic v6 fields"),
        ("top3_top5_entry_only", "only top3 and top5 policies are replayed; top10 remains shadow because breadth decays"),
        ("entry_gate", "block invalidated, survival, dilution, negative expectation, and market rejection candidates"),
        ("hold_extension", "extend only when thesis is active/confirmed and a post-entry hold receipt exists before scheduled exit"),
        ("exit_separation", "source receipt exit, price risk exit, thesis stale, and scheduled exit are separate reasons"),
        ("narrow_replacement_hurdle", "same-decision replacements only; replace weak selected slots only when challenger clears state and score hurdle"),
        ("cap_only_sizing", "confirmed gets full cap, active gets full cap, confirmation wait gets half cap, no leverage or conviction enlargement"),
        ("delta_validation", "scheduled-only counterfactual and actual L5 replay are compared for every policy"),
    ]
    return [
        {
            "task_id": "Task1519",
            "rule_id": f"L5RULE1519-{idx:03d}",
            "rule_name": name,
            "pre_registered_rule": rule,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, rule) in enumerate(rules, 1)
    ]


def classify_thesis_state(row: dict[str, str]) -> tuple[str, str, str, float]:
    family = row["event_family"]
    expectation = row["expectation_v6_state"]
    absorption = row["absorption_v6_state"]
    materiality = row["materiality_v6_state"]
    route = row["route"]
    score = to_float(row["semantic_v6_rank_score"])
    if family in {"survival", "dilution"} or expectation == "negative_expectation_proxy" or absorption == "market_rejection_or_reversal":
        return "invalidated", "entry_block", "hard_semantic_risk", 0.0
    if family == "positive" and expectation in {"true_surprise_proxy", "guidance_change_proxy"} and absorption == "sustained_market_acceptance":
        return "confirmed_thesis", "entry_allowed", "positive_surprise_absorption_confirmed", 1.0
    if family == "positive" and absorption in {"sustained_market_acceptance", "initial_reaction_only"}:
        return "active_thesis", "entry_allowed", "positive_with_market_receipt", 1.0
    if family == "positive" and expectation in {"true_surprise_proxy", "guidance_change_proxy"}:
        return "active_thesis", "entry_allowed", "positive_with_expectation_receipt", 1.0
    if family == "mixed" and expectation in {"true_surprise_proxy", "guidance_change_proxy"} and absorption in {"sustained_market_acceptance", "initial_reaction_only"}:
        return "confirmation_wait", "entry_allowed_cap_only", "mixed_but_has_expectation_and_absorption", 0.5
    if route == "watch_or_size_cap" or materiality in {"unconfirmed_materiality_capped", "materiality_source_gap_neutral"}:
        return "source_gap_watch", "entry_watch_only", "insufficient_confirmation_for_entry", 0.0
    if score >= 45 and absorption == "sustained_market_acceptance":
        return "active_thesis", "entry_allowed", "high_score_absorption_preserve", 1.0
    return "source_gap_watch", "entry_watch_only", "default_watch_state", 0.0


def build_state_machine() -> list[dict[str, object]]:
    ranks = read_csv(TASK1488 / "task1494_payoff_ranker_v6.csv")
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(ranks, 1):
        state, entry_gate, reason, size_cap = classify_thesis_state(row)
        rows.append(
            {
                "task_id": "Task1520",
                "state_row_id": f"L5STATE1520-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "semantic_v6_rank_within_decision": row["semantic_v6_rank_within_decision"],
                "semantic_v6_rank_score": row["semantic_v6_rank_score"],
                "event_family": row["event_family"],
                "expectation_v6_state": row["expectation_v6_state"],
                "absorption_v6_state": row["absorption_v6_state"],
                "materiality_v6_state": row["materiality_v6_state"],
                "thesis_state": state,
                "entry_gate_state": entry_gate,
                "state_reason": reason,
                "position_size_cap_multiplier": size_cap,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_entry_gate_specs(state_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in state_rows:
        by_decision[str(row["decision_asof_ts"])].append(row)
    policy_specs: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []
    for policy_id, slot_cap in POLICIES.items():
        for decision_ts, rows in by_decision.items():
            ordered = sorted(rows, key=lambda item: (int(to_float(item["semantic_v6_rank_within_decision"], 9999)), -to_float(item["semantic_v6_rank_score"])))
            eligible = [row for row in ordered if row["entry_gate_state"] in {"entry_allowed", "entry_allowed_cap_only"}]
            selected = eligible[:slot_cap]
            for rank, row in enumerate(ordered, 1):
                gate_rows.append(
                    {
                        "task_id": "Task1521",
                        "entry_gate_row_id": f"ENTRY1521-{policy_id}-{decision_ts[:10]}-{rank:03d}",
                        "policy_variant_id": policy_id,
                        "candidate_source_id": row["candidate_source_id"],
                        "trade_spec_id": row["trade_spec_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "entry_gate_state": row["entry_gate_state"],
                        "thesis_state": row["thesis_state"],
                        "selected_by_entry_gate": "1" if row in selected else "0",
                        "selection_reason": "top_ranked_entry_eligible" if row in selected else ("blocked_or_watch" if row["entry_gate_state"] not in {"entry_allowed", "entry_allowed_cap_only"} else "eligible_below_slot"),
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
            for row in selected:
                policy_specs.append(
                    {
                        "task_id": "Task1521",
                        "policy_spec_id": f"{policy_id}:{row['trade_spec_id']}",
                        "policy_variant_id": policy_id,
                        "slot_cap": slot_cap,
                        "candidate_source_id": row["candidate_source_id"],
                        "trade_spec_id": row["trade_spec_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "thesis_state": row["thesis_state"],
                        "entry_gate_state": row["entry_gate_state"],
                        "semantic_v6_rank_score": row["semantic_v6_rank_score"],
                        "position_size_cap_multiplier": row["position_size_cap_multiplier"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
    return policy_specs, gate_rows


def build_replacement_hurdle(
    state_rows: list[dict[str, object]],
    policy_specs: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    selected_keys = {(row["policy_variant_id"], row["decision_asof_ts"], row["trade_spec_id"]) for row in policy_specs}
    rows_by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in state_rows:
        rows_by_decision[str(row["decision_asof_ts"])].append(row)
    specs_by_policy_decision: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in policy_specs:
        specs_by_policy_decision[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    replacement_rows: list[dict[str, object]] = []
    final_specs = [dict(row) for row in policy_specs]
    for policy_id, slot_cap in POLICIES.items():
        for decision_ts, candidates in rows_by_decision.items():
            selected = specs_by_policy_decision[(policy_id, decision_ts)]
            if not selected:
                continue
            weakest = min(selected, key=lambda item: to_float(item["semantic_v6_rank_score"]))
            challengers = [
                row
                for row in sorted(candidates, key=lambda item: -to_float(item["semantic_v6_rank_score"]))
                if (policy_id, decision_ts, row["trade_spec_id"]) not in selected_keys
                and row["entry_gate_state"] == "entry_allowed"
                and row["thesis_state"] == "confirmed_thesis"
            ]
            chosen = None
            for challenger in challengers:
                if to_float(challenger["semantic_v6_rank_score"]) >= to_float(weakest["semantic_v6_rank_score"]) + 6.0:
                    chosen = challenger
                    break
            state = "no_replacement_hurdle_met"
            if chosen:
                state = "same_decision_one_for_one_replacement"
                final_specs = [
                    row
                    for row in final_specs
                    if not (row["policy_variant_id"] == policy_id and row["decision_asof_ts"] == decision_ts and row["trade_spec_id"] == weakest["trade_spec_id"])
                ]
                final_specs.append(
                    {
                        "task_id": "Task1524",
                        "policy_spec_id": f"{policy_id}:{chosen['trade_spec_id']}",
                        "policy_variant_id": policy_id,
                        "slot_cap": slot_cap,
                        "candidate_source_id": chosen["candidate_source_id"],
                        "trade_spec_id": chosen["trade_spec_id"],
                        "symbol": chosen["symbol"],
                        "decision_asof_ts": decision_ts,
                        "thesis_state": chosen["thesis_state"],
                        "entry_gate_state": chosen["entry_gate_state"],
                        "semantic_v6_rank_score": chosen["semantic_v6_rank_score"],
                        "position_size_cap_multiplier": chosen["position_size_cap_multiplier"],
                        "replacement_source": f"replaced:{weakest['trade_spec_id']}",
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
            replacement_rows.append(
                {
                    "task_id": "Task1524",
                    "replacement_row_id": f"REPL1524-{policy_id}-{decision_ts[:10]}",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "weakest_selected_trade_spec_id": weakest["trade_spec_id"],
                    "weakest_selected_score": weakest["semantic_v6_rank_score"],
                    "challenger_trade_spec_id": chosen["trade_spec_id"] if chosen else "",
                    "challenger_score": chosen["semantic_v6_rank_score"] if chosen else "",
                    "replacement_hurdle_state": state,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    for row in final_specs:
        row.setdefault("replacement_source", "original_entry_gate_selection")
        row["task_id"] = "Task1524"
    return final_specs, replacement_rows


def build_exit_decision_panel(
    policy_specs: list[dict[str, object]],
    specs: dict[str, dict[str, str]],
    source_exits: list[dict[str, object]],
    price_exits: list[dict[str, object]],
    hold_receipts: list[dict[str, object]],
) -> list[dict[str, object]]:
    source_by_key = {(str(row["policy_variant_id"]), str(row["trade_spec_id"])): row for row in source_exits}
    price_by_key = {(str(row["policy_variant_id"]), str(row["trade_spec_id"])): row for row in price_exits}
    hold_by_key = {(str(row["policy_variant_id"]), str(row["trade_spec_id"])): row for row in hold_receipts}
    rows: list[dict[str, object]] = []
    for idx, selected in enumerate(policy_specs, 1):
        key = (str(selected["policy_variant_id"]), str(selected["trade_spec_id"]))
        spec = specs[str(selected["trade_spec_id"])]
        scheduled_exit = spec["exit_on_or_before_date"]
        thesis_state = str(selected["thesis_state"])
        source = source_by_key.get(key, {})
        price = price_by_key.get(key, {})
        hold = hold_by_key.get(key, {})
        exit_action = "scheduled_exit"
        exit_date = scheduled_exit
        exit_reason = "scheduled_thesis_review"
        hold_extension_ready = "0"
        if (
            str(hold.get("hold_extend_receipt_ready", "")) == "1"
            and thesis_state in {"confirmed_thesis", "active_thesis"}
        ):
            hold_extension_ready = "1"
            exit_action = "hold_extend"
            exit_date = ""
            exit_reason = "positive_source_hold_receipt"
        if (
            str(source.get("source_receipt_exit_ready", "")) == "1"
            and thesis_state in {"confirmation_wait", "source_gap_watch"}
        ):
            exit_action = "source_receipt_exit"
            exit_date = str(source.get("source_receipt_ts", ""))[:10]
            exit_reason = str(source.get("source_receipt_exit_type", "source_receipt_exit"))
        if (
            str(price.get("price_path_risk_exit_ready", "")) == "1"
            and str(price.get("price_path_risk_exit_type", "")) == "price_path_10d_drawdown_risk"
            and thesis_state not in {"confirmed_thesis"}
        ):
            exit_action = "price_path_exit"
            exit_date = str(price.get("price_path_risk_exit_date", ""))
            exit_reason = "severe_10d_price_path_risk"
        rows.append(
            {
                "task_id": "Task1523",
                "exit_decision_id": f"EXIT1523-{idx:07d}",
                "policy_variant_id": selected["policy_variant_id"],
                "trade_spec_id": selected["trade_spec_id"],
                "candidate_source_id": selected["candidate_source_id"],
                "symbol": selected["symbol"],
                "decision_asof_ts": selected["decision_asof_ts"],
                "thesis_state": thesis_state,
                "source_exit_ready": source.get("source_receipt_exit_ready", "0"),
                "price_exit_ready": price.get("price_path_risk_exit_ready", "0"),
                "hold_extension_ready": hold_extension_ready,
                "exit_action": exit_action,
                "exit_reason": exit_reason,
                "exit_date_override": exit_date,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def close_for_exit(frame: pd.DataFrame | None, entry_date: date, scheduled_exit: date, exit_action: str, exit_override: str) -> tuple[date, float] | None:
    if frame is None:
        return None
    if exit_action == "hold_extend":
        extended = replay.close_n_sessions_after(frame, scheduled_exit, 21)
        if extended:
            return extended[0], extended[1]
    override_date = replay.parse_date(exit_override) if exit_override else scheduled_exit
    close = replay.close_on_or_before(frame, override_date or scheduled_exit)
    if close:
        return close[0], close[1]
    fallback = replay.close_n_sessions_after(frame, entry_date, 1, scheduled_exit)
    if fallback:
        return fallback[0], fallback[1]
    return None


def run_operating_replay(
    policy_specs: list[dict[str, object]],
    specs: dict[str, dict[str, str]],
    exit_decisions: list[dict[str, object]],
    scheduled_only: bool = False,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    exits = {(str(row["policy_variant_id"]), str(row["trade_spec_id"])): row for row in exit_decisions}
    by_policy_decision: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in policy_specs:
        by_policy_decision[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    price_cache: dict[str, pd.DataFrame | None] = {}
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    for policy_id, slot_cap in POLICIES.items():
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in by_policy_decision if key[0] == policy_id}):
            items = by_policy_decision[(policy_id, decision_ts)]
            period_pnl = 0.0
            new_capital = capital
            base_alloc = capital / slot_cap
            allocated_count = 0
            for selected in items:
                spec = specs[str(selected["trade_spec_id"])]
                symbol = str(selected["symbol"])
                frame = replay.load_price(symbol, price_cache)
                entry_after = replay.parse_date(spec["entry_after_date"]) or date(1970, 1, 1)
                scheduled_exit = replay.parse_date(spec["exit_on_or_before_date"]) or entry_after
                entry = replay.price_on_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                exit_row = exits.get((policy_id, str(selected["trade_spec_id"])), {})
                if scheduled_only:
                    exit_action = "scheduled_only_counterfactual"
                    exit_reason = "scheduled_only_counterfactual"
                    exit_override = scheduled_exit.isoformat()
                else:
                    exit_action = str(exit_row.get("exit_action", "scheduled_exit"))
                    exit_reason = str(exit_row.get("exit_reason", "scheduled_thesis_review"))
                    exit_override = str(exit_row.get("exit_date_override", ""))
                close = close_for_exit(frame, entry_date, scheduled_exit, exit_action, exit_override)
                if not close:
                    continue
                exit_date, exit_price = close
                size_multiplier = to_float(selected.get("position_size_cap_multiplier"), 1.0)
                capital_allocated = base_alloc * size_multiplier
                gross_return = replay.pct_return(entry_price, exit_price)
                net_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
                pnl = capital_allocated * net_return
                new_capital += pnl
                period_pnl += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1526" if scheduled_only else "Task1525",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": symbol,
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "scheduled_exit_date": scheduled_exit.isoformat(),
                        "actual_exit_date": exit_date.isoformat(),
                        "actual_exit_price": round(exit_price, 6),
                        "exit_reason": exit_reason,
                        "thesis_state": selected["thesis_state"],
                        "position_size_cap_multiplier": round(size_multiplier, 4),
                        "capital_allocated": round(capital_allocated, 4),
                        "cash_unallocated_from_cap": round(base_alloc * (1.0 - size_multiplier), 4),
                        "gross_return": round(gross_return, 8),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "source_receipt_exit_used": "1" if exit_action == "source_receipt_exit" else "0",
                        "price_path_exit_used": "1" if exit_action == "price_path_exit" else "0",
                        "hold_extension_used": "1" if exit_action == "hold_extend" and not scheduled_only else "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1" if scheduled_only else "0",
                        "authority": AUTHORITY,
                    }
                )
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1526" if scheduled_only else "Task1525",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = {row["policy_variant_id"]: row for row in read_csv(TASK1201 / "task1207_replay_metrics.csv")}
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        slot = POLICIES[policy_id]
        baseline = base_metrics.get(f"l0_l3_slot{slot}_v1", base_metrics["l0_l3_slot5_v1"])
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(replay.parse_date(str(row["actual_exit_date"])) or start for row in tr_rows)
        cagr_value = cagr(INITIAL_CAPITAL, final, start, end)
        mdd_value = replay.max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1525",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr_value, 6),
                "max_drawdown": round(mdd_value, 6),
                "trade_count": len(tr_rows),
                "source_receipt_exit_count": sum(1 for row in tr_rows if row.get("source_receipt_exit_used") == "1"),
                "price_path_exit_count": sum(1 for row in tr_rows if row.get("price_path_exit_used") == "1"),
                "hold_extension_count": sum(1 for row in tr_rows if row.get("hold_extension_used") == "1"),
                "baseline_slot_variant": baseline["policy_variant_id"],
                "baseline_final_equity": baseline["final_equity"],
                "baseline_delta": round(final - to_float(baseline["final_equity"]), 4),
                "benchmark_symbol": baseline["benchmark_symbol"],
                "benchmark_final_equity": baseline["benchmark_final_equity"],
                "beats_benchmark": "1" if final > to_float(baseline["benchmark_final_equity"]) else "0",
                "target_cagr_30pct_met": "1" if cagr_value >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd_value >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_delta_audit(actual_trades: list[dict[str, object]], scheduled_trades: list[dict[str, object]], actual_metrics: list[dict[str, object]], scheduled_metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scheduled_by_key = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in scheduled_trades}
    rows: list[dict[str, object]] = []
    for idx, actual in enumerate(actual_trades, 1):
        scheduled = scheduled_by_key.get((actual["policy_variant_id"], actual["trade_spec_id"]), {})
        delta = to_float(actual["net_return"]) - to_float(scheduled.get("net_return"))
        rows.append(
            {
                "task_id": "Task1527",
                "delta_id": f"L5OPDELTA1527-{idx:07d}",
                "policy_variant_id": actual["policy_variant_id"],
                "trade_spec_id": actual["trade_spec_id"],
                "candidate_source_id": actual["candidate_source_id"],
                "symbol": actual["symbol"],
                "decision_asof_ts": actual["decision_asof_ts"],
                "thesis_state": actual["thesis_state"],
                "exit_reason": actual["exit_reason"],
                "scheduled_net_return": scheduled.get("net_return", ""),
                "actual_net_return": actual["net_return"],
                "l5_operating_delta": round(delta, 8),
                "l5_helped_vs_scheduled": "1" if delta > 0 else "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    actual_by_policy = {row["policy_variant_id"]: row for row in actual_metrics}
    scheduled_by_policy = {row["policy_variant_id"]: row for row in scheduled_metrics}
    summary: list[dict[str, object]] = []
    for policy_id in POLICIES:
        actual = actual_by_policy[policy_id]
        scheduled = scheduled_by_policy[policy_id]
        deltas = [to_float(row["l5_operating_delta"]) for row in rows if row["policy_variant_id"] == policy_id]
        summary.append(
            {
                "task_id": "Task1527",
                "policy_variant_id": policy_id,
                "scheduled_final_equity": scheduled["final_equity"],
                "actual_final_equity": actual["final_equity"],
                "actual_minus_scheduled_final_equity": round(to_float(actual["final_equity"]) - to_float(scheduled["final_equity"]), 4),
                "scheduled_max_drawdown": scheduled["max_drawdown"],
                "actual_max_drawdown": actual["max_drawdown"],
                "actual_minus_scheduled_mdd": round(to_float(actual["max_drawdown"]) - to_float(scheduled["max_drawdown"]), 6),
                "avg_l5_operating_delta": round(mean(deltas), 8),
                "l5_delta_positive": "1" if to_float(actual["final_equity"]) > to_float(scheduled["final_equity"]) else "0",
                "mdd_improved": "1" if to_float(actual["max_drawdown"]) > to_float(scheduled["max_drawdown"]) else "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows, summary


def build_summaries(state_rows: list[dict[str, object]], exit_rows: list[dict[str, object]], metrics: list[dict[str, object]], delta_summary: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    summary: list[dict[str, object]] = []
    for area, rows, field in [
        ("thesis_state_all", state_rows, "thesis_state"),
        ("entry_gate_all", state_rows, "entry_gate_state"),
        ("exit_action_selected", exit_rows, "exit_action"),
    ]:
        for key, value in sorted(Counter(str(row[field]) for row in rows).items()):
            summary.append({"task_id": "Task1528", "summary_area": area, "metric": key, "value": value, "authority": AUTHORITY})
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    best_delta = next(row for row in delta_summary if row["policy_variant_id"] == best["policy_variant_id"])
    gate = [
        {
            "task_id": "Task1536",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "best_l5_delta_positive": best_delta["l5_delta_positive"],
            "best_mdd_improved": best_delta["mdd_improved"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "l5_position_operating_brain_diagnostic_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1537",
            "verdict": "l5_position_operating_brain_implemented_not_accepted",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "l5_delta_positive": best_delta["l5_delta_positive"],
            "mdd_improved": best_delta["mdd_improved"],
            "next_action": "audit hold extensions and cap-only sizing before any stronger sizing or broader top10 policy",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return summary, gate, closeout


def write_report(metrics: list[dict[str, object]], scheduled_metrics: list[dict[str, object]], delta_summary: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    report = f"""# Task1518-1537 L5 Position Operating Brain

## Decision Summary

- Verdict: `l5_position_operating_brain_implemented_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: L5 now has thesis states, top3/top5 entry gates, hold extension, separated exits, narrow replacement hurdle, cap-only sizing, and delta validation.

## Quant Expert Report

Actual L5 operating replay:

| Policy | Final | CAGR | MDD | Trades | Source exit | Price exit | Hold ext | Beats QQQ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in metrics:
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | "
            f"{row['trade_count']} | {row['source_receipt_exit_count']} | {row['price_path_exit_count']} | {row['hold_extension_count']} | {row['beats_benchmark']} |\n"
        )
    report += "\nScheduled-only versus actual L5 operating delta:\n\n"
    report += "| Policy | Scheduled final | Actual final | Delta final | Scheduled MDD | Actual MDD | Delta positive | MDD improved |\n"
    report += "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n"
    for row in delta_summary:
        report += (
            f"| `{row['policy_variant_id']}` | {row['scheduled_final_equity']} | {row['actual_final_equity']} | "
            f"{row['actual_minus_scheduled_final_equity']} | {row['scheduled_max_drawdown']} | {row['actual_max_drawdown']} | "
            f"{row['l5_delta_positive']} | {row['mdd_improved']} |\n"
        )
    report += """

## No-Background Decision-Maker Report

L5를 단순 exit 규칙에서 포지션 운영 뇌로 바꿨다.

이제 후보마다 thesis 상태를 만든다.

살 후보만 top3/top5 안에서 들어간다.

보유 연장, source exit, price exit, scheduled exit을 분리했다.

비중 확대는 하지 않았다.

아직은 cap-only sizing만 했다.

그래도 전략 승인은 아니다.

## Artifact Manifest

- `task1518_expert_audit.csv`
- `task1519_l5_operating_preregistered_rules.csv`
- `task1520_thesis_state_machine.csv`
- `task1521_entry_gate_panel.csv`
- `task1522_policy_specs_pre_replacement.csv`
- `task1524_replacement_hurdle_panel.csv`
- `task1524_policy_specs_final.csv`
- `task1523_exit_decision_panel.csv`
- `task1525_replay_trades.csv`
- `task1525_replay_equity.csv`
- `task1525_replay_metrics.csv`
- `task1526_scheduled_only_trades.csv`
- `task1526_scheduled_only_equity.csv`
- `task1526_scheduled_only_metrics.csv`
- `task1527_l5_delta_audit.csv`
- `task1527_l5_delta_summary.csv`
- `task1528_summary.csv`
- `task1536_acceptance_gate.csv`
- `task1537_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1518_1537_l5_position_operating_brain_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1518_1537_l5_position_operating_brain.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1518_1537_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    replay.AUTHORITY = AUTHORITY
    replay.POLICIES = POLICIES
    expert = expert_audit_rows()
    rules = preregister_policy_rows()
    states = build_state_machine()
    pre_specs, entry_gate = build_entry_gate_specs(states)
    final_specs, replacements = build_replacement_hurdle(states, pre_specs)
    _enriched, specs, _bindings, filing_bindings, evidence = replay.load_inputs()
    price_cache: dict[str, pd.DataFrame | None] = {}
    symbol_filings, accession_text = replay.build_filing_indexes(filing_bindings, evidence)
    source_exits, price_exits, hold_receipts = replay.build_exit_panels(final_specs, specs, symbol_filings, accession_text, price_cache)
    exit_decisions = build_exit_decision_panel(final_specs, specs, source_exits, price_exits, hold_receipts)
    actual_trades, actual_equity = run_operating_replay(final_specs, specs, exit_decisions, scheduled_only=False)
    scheduled_trades, scheduled_equity = run_operating_replay(final_specs, specs, exit_decisions, scheduled_only=True)
    metrics = build_metrics(actual_trades, actual_equity)
    scheduled_metrics = build_metrics(scheduled_trades, scheduled_equity)
    for row in scheduled_metrics:
        row["task_id"] = "Task1526"
    delta_rows, delta_summary = build_delta_audit(actual_trades, scheduled_trades, metrics, scheduled_metrics)
    summary, gate, closeout = build_summaries(states, exit_decisions, metrics, delta_summary)
    outputs = [
        ("task1518_expert_audit.csv", expert),
        ("task1519_l5_operating_preregistered_rules.csv", rules),
        ("task1520_thesis_state_machine.csv", states),
        ("task1521_entry_gate_panel.csv", entry_gate),
        ("task1522_policy_specs_pre_replacement.csv", pre_specs),
        ("task1524_replacement_hurdle_panel.csv", replacements),
        ("task1524_policy_specs_final.csv", final_specs),
        ("task1523_source_receipt_exit_panel.csv", source_exits),
        ("task1523_price_path_exit_panel.csv", price_exits),
        ("task1523_hold_receipt_panel.csv", hold_receipts),
        ("task1523_exit_decision_panel.csv", exit_decisions),
        ("task1525_replay_trades.csv", actual_trades),
        ("task1525_replay_equity.csv", actual_equity),
        ("task1525_replay_metrics.csv", metrics),
        ("task1526_scheduled_only_trades.csv", scheduled_trades),
        ("task1526_scheduled_only_equity.csv", scheduled_equity),
        ("task1526_scheduled_only_metrics.csv", scheduled_metrics),
        ("task1527_l5_delta_audit.csv", delta_rows),
        ("task1527_l5_delta_summary.csv", delta_summary),
        ("task1528_summary.csv", summary),
        ("task1536_acceptance_gate.csv", gate),
        ("task1537_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1537_closeout.json", closeout[0])
    write_report(metrics, scheduled_metrics, delta_summary, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
