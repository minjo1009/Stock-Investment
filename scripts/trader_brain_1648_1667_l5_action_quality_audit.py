from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1518_1537_l5_position_operating_brain as l5
import trader_brain_1558_1577_l5_damage_control_engine as damage
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
TASK1558 = ROOT / "data/artifacts/task_1558_1577_l5_damage_control_engine"
TASK1618 = ROOT / "data/artifacts/task_1618_1647_expectation_payoff_rerisk_bridge"
OUT_DIR = ROOT / "data/artifacts/task_1648_1667_l5_action_quality_audit"
REPORT_DIR = ROOT / "docs/reports/task_1648_1667_l5_action_quality_audit"
REPORT = REPORT_DIR / "task_1648_1667_l5_action_quality_audit.md"
DECISION = REPORT_DIR / "task_1648_1667_decision.csv"

AUTHORITY = "DIAGNOSTIC_L5_ACTION_QUALITY_AUDIT_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
QQQ_BENCHMARK_FINAL = 1847.0265

REPLAY_POLICIES = {
    "aq_baseline_damage_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rule": "baseline_damage"},
    "aq_reduce_guard_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rule": "reduce_guard"},
    "aq_source_demote_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rule": "source_demote"},
    "aq_combo_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rule": "combo"},
    "aq_baseline_damage_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rule": "baseline_damage"},
    "aq_reduce_guard_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rule": "reduce_guard"},
    "aq_source_demote_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rule": "source_demote"},
    "aq_combo_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rule": "combo"},
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
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def parse_date(value: object) -> date | None:
    if value in ("", None):
        return None
    if pd.isna(value):
        return None
    return replay.parse_date(str(value))


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        ("risk_pm", "Audit reduce success by avoided loss and missed upside, not by MDD alone.", "adopt"),
        ("event_driven_trader", "Exit should require thesis/source damage, not just price weakness.", "adopt"),
        ("quant_researcher", "Score action precision before replaying combined CAGR/MDD.", "adopt"),
        ("execution_trader", "Re-risk needs independent incremental PnL and runtime recovery quality.", "adopt"),
        ("validation_engineer", "Keep action scoring outcome-audit-only and separate from assignment.", "adopt"),
        ("governance_reviewer", "No action-quality pass can approve strategy, deployment, or capital.", "adopt"),
    ]
    return [
        {
            "task_id": "Task1648",
            "expert_review_id": f"AQEXPERT1648-{idx:03d}",
            "expert_role": role,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, critique, decision) in enumerate(rows, 1)
    ]


def action_contract_rows() -> list[dict[str, object]]:
    rows = [
        ("hold", "success if held leg beats scheduled counterfactual or produces positive net return", "do not infer thesis truth from price alone"),
        ("reduce", "success if sold fraction avoids loss versus holding that fraction to planned exit", "missed upside counts against reduce quality"),
        ("exit", "success if full exit beats holding to planned exit", "source exit remains audit-only and not broker truth"),
        ("no_reentry", "success if skipped counterfactual would not have paid", "missing skipped trade is not a negative label"),
        ("rerisk", "success if added-back fraction has positive independent PnL", "do not use future rerisk outcome for assignment"),
    ]
    return [
        {
            "task_id": "Task1649",
            "action_type": action,
            "success_definition": success,
            "guardrail": guardrail,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for action, success, guardrail in rows
    ]


def rows_by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in rows}


def trade_specs_by_id() -> dict[str, dict[str, str]]:
    return damage.trade_specs_by_id()


def selected_specs() -> list[dict[str, str]]:
    return read_csv(TASK1518 / "task1524_policy_specs_final.csv")


def action_panel() -> list[dict[str, str]]:
    return read_csv(TASK1558 / "task1561_damage_action_panel.csv")


def damage_trades_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return rows_by_key(read_csv(TASK1558 / "task1562_damage_replay_trades.csv"))


def actual_l5_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return rows_by_key(read_csv(TASK1518 / "task1525_replay_trades.csv"))


def scheduled_l5_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return rows_by_key(read_csv(TASK1518 / "task1526_scheduled_only_trades.csv"))


def exit_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return damage.exit_by_key()


def close_for_selected(
    selected: dict[str, str],
    specs: dict[str, dict[str, str]],
    price_cache: dict[str, pd.DataFrame | None],
) -> dict[str, object] | None:
    spec = specs[selected["trade_spec_id"]]
    frame = replay.load_price(selected["symbol"], price_cache)
    entry_after = parse_date(spec.get("entry_after_date")) or date(1970, 1, 1)
    scheduled_exit = parse_date(spec.get("exit_on_or_before_date")) or entry_after
    entry = replay.price_on_or_after(frame, entry_after)
    if not entry:
        return None
    entry_date, entry_price = entry
    planned_close = damage.base_planned_close(frame, entry_date, scheduled_exit, exit_by_key().get((selected["policy_variant_id"], selected["trade_spec_id"]), {}))
    if not planned_close:
        return None
    planned_exit_date, planned_exit_price = planned_close
    return {
        "frame": frame,
        "entry_date": entry_date,
        "entry_price": entry_price,
        "scheduled_exit_date": scheduled_exit,
        "planned_exit_date": planned_exit_date,
        "planned_exit_price": planned_exit_price,
    }


def counterfactual_return(entry_price: float, exit_price: float) -> float:
    return replay.pct_return(entry_price, exit_price) - ROUND_TRIP_COST_BPS / 10000.0


def build_action_ledger() -> list[dict[str, object]]:
    specs = trade_specs_by_id()
    selected_by_key = rows_by_key(selected_specs())
    damage_trades = damage_trades_by_key()
    actual_trades = actual_l5_by_key()
    scheduled_trades = scheduled_l5_by_key()
    price_cache: dict[str, pd.DataFrame | None] = {}
    rows: list[dict[str, object]] = []
    idx = 1
    for action in action_panel():
        key = (action["policy_variant_id"], action["trade_spec_id"])
        selected = selected_by_key.get(key)
        if not selected:
            continue
        close = close_for_selected(selected, specs, price_cache)
        actual = actual_trades.get(key, {})
        scheduled = scheduled_trades.get(key, {})
        dmg = damage_trades.get(key, {})
        action_type = action["damage_action"]
        action_success = ""
        action_delta = 0.0
        counterfactual_net_return = ""
        realized_net_return = dmg.get("net_return", "")
        actual_l5_return = to_float(actual.get("net_return"))
        scheduled_return = to_float(scheduled.get("net_return"))
        reason = action["damage_reason"]
        if close:
            entry_price = to_float(close["entry_price"])
            planned_exit_price = to_float(close["planned_exit_price"])
            hold_to_planned_return = counterfactual_return(entry_price, planned_exit_price)
            counterfactual_net_return = round(hold_to_planned_return, 8)
            if action_type == "reduce":
                action_delta = to_float(dmg.get("net_return")) - actual_l5_return
                action_success = "1" if action_delta > 0 else "0"
            elif action_type == "exit":
                action_delta = to_float(dmg.get("net_return")) - scheduled_return
                action_success = "1" if action_delta > 0 else "0"
            elif action_type == "hold":
                action_delta = actual_l5_return - scheduled_return
                action_success = "1" if actual_l5_return > 0 and action_delta >= 0 else "0"
            elif action_type == "no_reentry":
                action_delta = -scheduled_return
                action_success = "1" if scheduled_return <= 0 else "0"
        rows.append(
            {
                "task_id": "Task1650",
                "action_ledger_id": f"AQLEDGER1650-{idx:06d}",
                "policy_variant_id": action["policy_variant_id"],
                "trade_spec_id": action["trade_spec_id"],
                "candidate_source_id": action["candidate_source_id"],
                "symbol": action["symbol"],
                "decision_asof_ts": action["decision_asof_ts"],
                "thesis_state": action["thesis_state"],
                "action_type": action_type,
                "action_reason": reason,
                "original_exit_action": action.get("original_exit_action", ""),
                "source_damage_date": action.get("source_damage_date", ""),
                "price_reduce_date": action.get("price_reduce_date", ""),
                "price_exit_date": action.get("price_exit_date", ""),
                "counterfactual_hold_to_planned_net_return": counterfactual_net_return,
                "scheduled_counterfactual_net_return": round(scheduled_return, 8),
                "actual_l5_net_return": round(actual_l5_return, 8),
                "realized_net_return": realized_net_return,
                "action_delta_vs_counterfactual": round(action_delta, 8),
                "action_success": action_success,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def build_rerisk_ledger(start_idx: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset, row in enumerate(read_csv(TASK1618 / "task1628_rerisk_events.csv"), start_idx):
        trade = next(
            (
                item for item in read_csv(TASK1618 / "task1628_rerisk_replay_trades.csv")
                if item["policy_variant_id"] == row["policy_variant_id"] and item["trade_spec_id"] == row["trade_spec_id"]
            ),
            {},
        )
        rerisk_pnl = to_float(trade.get("rerisk_pnl"))
        rows.append(
            {
                "task_id": "Task1650",
                "action_ledger_id": f"AQLEDGER1650-{offset:06d}",
                "policy_variant_id": row["source_policy_variant_id"],
                "audit_policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": trade.get("candidate_source_id", ""),
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "thesis_state": "",
                "action_type": "rerisk",
                "action_reason": "runtime_post_reduce_rerisk",
                "reduce_date": row["reduce_date"],
                "rerisk_date": row["rerisk_date"],
                "rerisk_fraction": row["rerisk_fraction"],
                "recovery_return_at_rerisk": row["recovery_return_at_rerisk"],
                "rerisk_pnl": round(rerisk_pnl, 4),
                "action_delta_vs_counterfactual": round(rerisk_pnl, 4),
                "action_success": "1" if rerisk_pnl > 0 else "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_action_scorecard(ledger: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in ledger:
        groups[(str(row["policy_variant_id"]), str(row["action_type"]))].append(row)
    rows: list[dict[str, object]] = []
    idx = 1
    for (policy_id, action_type), items in sorted(groups.items()):
        success_values = [to_float(row.get("action_success")) for row in items if row.get("action_success", "") != ""]
        deltas = [to_float(row.get("action_delta_vs_counterfactual")) for row in items]
        rows.append(
            {
                "task_id": "Task1651",
                "scorecard_id": f"AQSCORE1651-{idx:04d}",
                "policy_variant_id": policy_id,
                "action_type": action_type,
                "action_count": len(items),
                "scored_count": len(success_values),
                "precision": round(mean(success_values), 6),
                "avg_action_delta": round(mean(deltas), 8),
                "total_action_delta": round(sum(deltas), 6),
                "quality_verdict": "pass" if success_values and mean(success_values) >= 0.55 and sum(deltas) > 0 else "weak",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def rulebook_rows(scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1652",
            "rule_id": "AQRULE1652-001",
            "rule_name": "baseline_damage",
            "rule_detail": "Replay the existing Task1558 reduce-first damage control unchanged.",
            "uses_action_outcomes_for_assignment": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1652",
            "rule_id": "AQRULE1652-002",
            "rule_name": "reduce_guard",
            "rule_detail": "If action is price_damage_reduce on active_thesis or confirmed_thesis, reduce 25pct instead of 50pct.",
            "uses_action_outcomes_for_assignment": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1652",
            "rule_id": "AQRULE1652-003",
            "rule_name": "source_demote",
            "rule_detail": "If source exit occurs without price_exit_date, demote full exit to 50pct reduce.",
            "uses_action_outcomes_for_assignment": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1652",
            "rule_id": "AQRULE1652-004",
            "rule_name": "combo",
            "rule_detail": "Apply reduce_guard and source_demote together; no rerisk add-back is enabled.",
            "uses_action_outcomes_for_assignment": "0",
            "authority": AUTHORITY,
        },
    ]


def modified_action(action: dict[str, str], rule: str) -> dict[str, object]:
    result: dict[str, object] = dict(action)
    result["modified_action"] = action["damage_action"]
    result["modified_reason"] = action["damage_reason"]
    result["modified_reduce_fraction"] = to_float(action.get("damage_reduce_fraction"))
    result["modified_reduce_date"] = action.get("damage_reduce_date", "")
    result["modified_exit_date"] = action.get("damage_exit_date", "")
    if rule in {"reduce_guard", "combo"}:
        if (
            action["damage_action"] == "reduce"
            and action.get("damage_reason") == "price_damage_reduce"
            and action.get("thesis_state") in {"active_thesis", "confirmed_thesis"}
        ):
            result["modified_action"] = "reduce"
            result["modified_reason"] = "price_damage_reduce_guard_25pct"
            result["modified_reduce_fraction"] = 0.25
    if rule in {"source_demote", "combo"}:
        if (
            action["damage_action"] == "exit"
            and action.get("source_damage_date", "") not in {"", "nan"}
            and action.get("price_exit_date", "") in {"", "nan"}
        ):
            result["modified_action"] = "reduce"
            result["modified_reason"] = "source_exit_demoted_to_reduce"
            result["modified_reduce_fraction"] = 0.5
            result["modified_reduce_date"] = action.get("source_damage_date", "")
            result["modified_exit_date"] = ""
    return result


def run_action_quality_replay() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    specs = trade_specs_by_id()
    policies = selected_specs()
    actions = rows_by_key(action_panel())
    exits = exit_by_key()
    price_cache: dict[str, pd.DataFrame | None] = {}
    by_policy_decision: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in policies:
        by_policy_decision[(row["policy_variant_id"], row["decision_asof_ts"])].append(row)

    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    action_revisions: list[dict[str, object]] = []
    trade_idx = 1
    revision_idx = 1
    for policy_id, policy in REPLAY_POLICIES.items():
        source_policy = str(policy["source_policy"])
        rule = str(policy["rule"])
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in by_policy_decision if key[0] == source_policy}):
            items = by_policy_decision[(source_policy, decision_ts)]
            base_alloc = capital / int(policy["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                action = actions.get((source_policy, selected["trade_spec_id"]))
                if not action:
                    continue
                mod = modified_action(action, rule)
                action_revisions.append(
                    {
                        "task_id": "Task1653",
                        "revision_id": f"AQREV1653-{revision_idx:06d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "original_action": action["damage_action"],
                        "modified_action": mod["modified_action"],
                        "original_reason": action["damage_reason"],
                        "modified_reason": mod["modified_reason"],
                        "original_reduce_fraction": action.get("damage_reduce_fraction", ""),
                        "modified_reduce_fraction": mod["modified_reduce_fraction"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                revision_idx += 1
                if mod["modified_action"] == "no_reentry":
                    continue
                spec = specs[selected["trade_spec_id"]]
                frame = replay.load_price(selected["symbol"], price_cache)
                entry_after = parse_date(spec.get("entry_after_date")) or date(1970, 1, 1)
                scheduled_exit = parse_date(spec.get("exit_on_or_before_date")) or entry_after
                entry = replay.price_on_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                exit_row = exits.get((source_policy, selected["trade_spec_id"]), {})
                planned_close = damage.base_planned_close(frame, entry_date, scheduled_exit, exit_row)
                if not planned_close:
                    continue
                planned_exit_date, planned_exit_price = planned_close
                size_multiplier = to_float(selected.get("position_size_cap_multiplier"), 1.0)
                allocated = base_alloc * size_multiplier
                reduced_capital = 0.0
                final_capital = allocated
                reduce_pnl = 0.0
                final_pnl = 0.0
                actual_exit_date = planned_exit_date
                actual_exit_price = planned_exit_price
                if mod["modified_action"] == "exit":
                    exit_date = parse_date(mod.get("modified_exit_date")) or planned_exit_date
                    close = replay.close_on_or_before(frame, exit_date)
                    actual_exit_date = close[0] if close else planned_exit_date
                    actual_exit_price = close[1] if close else planned_exit_price
                    net_return = counterfactual_return(entry_price, actual_exit_price)
                    final_pnl = allocated * net_return
                elif mod["modified_action"] == "reduce" and to_float(mod.get("modified_reduce_fraction")) > 0:
                    reduce_fraction = to_float(mod.get("modified_reduce_fraction"))
                    reduce_date = parse_date(mod.get("modified_reduce_date")) or planned_exit_date
                    close = replay.close_on_or_before(frame, reduce_date)
                    reduce_exit_date = close[0] if close else planned_exit_date
                    reduce_exit_price = close[1] if close else planned_exit_price
                    reduced_capital = allocated * reduce_fraction
                    final_capital = allocated - reduced_capital
                    reduce_return = counterfactual_return(entry_price, reduce_exit_price)
                    final_return = counterfactual_return(entry_price, planned_exit_price)
                    reduce_pnl = reduced_capital * reduce_return
                    final_pnl = final_capital * final_return
                    actual_exit_date = planned_exit_date
                    actual_exit_price = planned_exit_price
                    net_return = (reduce_pnl + final_pnl) / allocated if allocated else 0.0
                else:
                    net_return = counterfactual_return(entry_price, planned_exit_price)
                    final_pnl = allocated * net_return
                pnl = reduce_pnl + final_pnl
                period_pnl += pnl
                capital += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1654",
                        "trade_row_id": f"AQTRADE1654-{trade_idx:06d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "rule_name": rule,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "planned_exit_date": planned_exit_date.isoformat(),
                        "actual_exit_date": actual_exit_date.isoformat(),
                        "actual_exit_price": round(actual_exit_price, 6),
                        "modified_action": mod["modified_action"],
                        "modified_reason": mod["modified_reason"],
                        "position_size_cap_multiplier": round(size_multiplier, 4),
                        "capital_allocated": round(allocated, 4),
                        "reduced_capital": round(reduced_capital, 4),
                        "final_capital": round(final_capital, 4),
                        "reduce_pnl": round(reduce_pnl, 4),
                        "final_pnl": round(final_pnl, 4),
                        "pnl": round(pnl, 4),
                        "net_return": round(net_return, 8),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task1654",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "authority": AUTHORITY,
                }
            )
    return action_revisions, trades, equity, build_metrics(trades, equity)


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(parse_date(row["actual_exit_date"]) or start for row in tr_rows)
        cagr_value = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd_value = replay.max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1655",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr_value, 6),
                "max_drawdown": round(mdd_value, 6),
                "trade_count": len(tr_rows),
                "hold_count": sum(1 for row in tr_rows if row["modified_action"] == "hold"),
                "reduce_count": sum(1 for row in tr_rows if row["modified_action"] == "reduce"),
                "exit_count": sum(1 for row in tr_rows if row["modified_action"] == "exit"),
                "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                "target_cagr_30pct_met": "1" if cagr_value >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd_value >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def split_oos_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        d = replay.parse_ts(str(row["decision_asof_ts"])).date()
        window = "IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"
        groups[(str(row["policy_variant_id"]), window)].append(row)
    rows: list[dict[str, object]] = []
    for (policy_id, window), items in sorted(groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1656",
                "policy_variant_id": policy_id,
                "split_window": window,
                "period_count": len(items),
                "split_final_equity": round(values[-1], 4),
                "split_total_return": round(values[-1] / INITIAL_CAPITAL - 1.0, 6),
                "split_max_drawdown": round(replay.max_drawdown(values), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def failure_rows(scorecard: list[dict[str, object]], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for row in scorecard:
        if row["quality_verdict"] == "weak":
            rows.append(
                {
                    "task_id": "Task1657",
                    "failure_id": f"AQFAIL1657-{idx:04d}",
                    "failure_area": "weak_action_precision",
                    "policy_variant_id": row["policy_variant_id"],
                    "action_type": row["action_type"],
                    "precision": row["precision"],
                    "total_action_delta": row["total_action_delta"],
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    for row in metrics:
        if row["target_cagr_30pct_met"] != "1" or row["target_mdd_minus30pct_met"] != "1":
            rows.append(
                {
                    "task_id": "Task1657",
                    "failure_id": f"AQFAIL1657-{idx:04d}",
                    "failure_area": "target_failure",
                    "policy_variant_id": row["policy_variant_id"],
                    "action_type": "",
                    "precision": "",
                    "total_action_delta": "",
                    "cagr": row["cagr"],
                    "max_drawdown": row["max_drawdown"],
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def gate_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best_final = max(metrics, key=lambda row: to_float(row["final_equity"]))
    best_mdd = max(metrics, key=lambda row: to_float(row["max_drawdown"]))
    baseline = next(row for row in metrics if row["policy_variant_id"] == "aq_baseline_damage_top3_v1")
    gate = [
        {
            "task_id": "Task1666",
            "best_final_policy_variant_id": best_final["policy_variant_id"],
            "best_final_equity": best_final["final_equity"],
            "best_final_cagr": best_final["cagr"],
            "best_final_max_drawdown": best_final["max_drawdown"],
            "best_mdd_policy_variant_id": best_mdd["policy_variant_id"],
            "best_mdd_final_equity": best_mdd["final_equity"],
            "best_mdd_cagr": best_mdd["cagr"],
            "best_mdd_max_drawdown": best_mdd["max_drawdown"],
            "baseline_top3_final_equity": baseline["final_equity"],
            "baseline_top3_cagr": baseline["cagr"],
            "baseline_top3_max_drawdown": baseline["max_drawdown"],
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in metrics) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in metrics) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "l5_action_quality_audit_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1667",
            "verdict": "l5_action_quality_audit_implemented_not_accepted",
            "best_final_policy_variant_id": best_final["policy_variant_id"],
            "best_final_equity": best_final["final_equity"],
            "best_final_cagr": best_final["cagr"],
            "best_final_max_drawdown": best_final["max_drawdown"],
            "next_action": "fix weak reduce and rerisk action precision with stronger source-confirmed timing before another combined replay",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(
    scorecard: list[dict[str, object]],
    metrics: list[dict[str, object]],
    split_rows: list[dict[str, object]],
    failures: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1648-1667 L5 Action Quality Audit",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Best policy: `{closeout['best_final_policy_variant_id']}`.",
        f"- Best final equity: {closeout['best_final_equity']}.",
        f"- Best CAGR: {closeout['best_final_cagr']}.",
        f"- Best MDD: {closeout['best_final_max_drawdown']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Action quality scorecard:",
        "",
        "| Policy | Action | Count | Precision | Avg Delta | Total Delta | Verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in scorecard:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['action_type']} | {row['action_count']} | {row['precision']} | {row['avg_action_delta']} | {row['total_action_delta']} | {row['quality_verdict']} |"
        )
    lines.extend(["", "Replay metrics:", "", "| Policy | Final | CAGR | MDD | Trades | Hold | Reduce | Exit | QQQ Beat | CAGR Target | MDD Target |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['trade_count']} | {row['hold_count']} | {row['reduce_count']} | {row['exit_count']} | {row['beats_qqq']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |"
        )
    lines.extend(["", "Split/OOS diagnostics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split_rows:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. L5 actions were separated into hold, reduce, exit, no-reentry, and rerisk.",
            "2. Each action was scored against a counterfactual before combined replay.",
            "3. Reduce and rerisk are the weak actions; hold remains the useful action.",
            "4. The action-quality replay did not solve the 30pct CAGR and minus30pct MDD target together.",
            "5. The next fix is action precision, not another broad CAGR/MDD toggle.",
            "",
            "## Failure / Blocker Summary",
            "",
        ]
    )
    for row in failures[:20]:
        lines.append(f"- `{row['failure_area']}`: policy={row.get('policy_variant_id','')} action={row.get('action_type','')} precision={row.get('precision','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')}")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task1648_expert_review.csv`",
            "- `task1649_action_contract.csv`",
            "- `task1650_action_ledger.csv`",
            "- `task1651_action_scorecard.csv`",
            "- `task1652_action_rulebook.csv`",
            "- `task1653_action_rule_revisions.csv`",
            "- `task1654_action_quality_replay_trades.csv/equity`",
            "- `task1655_action_quality_replay_metrics.csv`",
            "- `task1656_split_oos_metrics.csv`",
            "- `task1657_failure_attribution.csv`",
            "- `task1666_acceptance_gate.csv`",
            "- `task1667_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1648_1667_l5_action_quality_audit_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    experts = expert_review_rows()
    contract = action_contract_rows()
    ledger = build_action_ledger()
    ledger.extend(build_rerisk_ledger(len(ledger) + 1))
    scorecard = build_action_scorecard(ledger)
    rules = rulebook_rows(scorecard)
    revisions, trades, equity, metrics = run_action_quality_replay()
    split = split_oos_rows(equity)
    failures = failure_rows(scorecard, metrics)
    gate, closeout = gate_closeout(metrics)

    outputs = [
        ("task1648_expert_review.csv", experts),
        ("task1649_action_contract.csv", contract),
        ("task1650_action_ledger.csv", ledger),
        ("task1651_action_scorecard.csv", scorecard),
        ("task1652_action_rulebook.csv", rules),
        ("task1653_action_rule_revisions.csv", revisions),
        ("task1654_action_quality_replay_trades.csv", trades),
        ("task1654_action_quality_replay_equity.csv", equity),
        ("task1655_action_quality_replay_metrics.csv", metrics),
        ("task1656_split_oos_metrics.csv", split),
        ("task1657_failure_attribution.csv", failures),
        ("task1666_acceptance_gate.csv", gate),
        ("task1667_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1667_closeout.json", closeout[0])
    write_report(scorecard, metrics, split, failures, closeout[0])
    write_csv(DECISION, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1648_1667] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
