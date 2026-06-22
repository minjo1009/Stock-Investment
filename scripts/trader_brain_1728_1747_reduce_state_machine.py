from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1558_1577_l5_damage_control_engine as damage
import trader_brain_1668_1687_l5_thesis_aware_action_engine as thesis_l5
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
TASK1668 = ROOT / "data/artifacts/task_1668_1687_l5_thesis_aware_action_engine"
OUT_DIR = ROOT / "data/artifacts/task_1728_1747_reduce_state_machine"
REPORT_DIR = ROOT / "docs/reports/task_1728_1747_reduce_state_machine"
REPORT = REPORT_DIR / "task_1728_1747_reduce_state_machine.md"
DECISION = REPORT_DIR / "task_1728_1747_decision.csv"

AUTHORITY = "DIAGNOSTIC_REDUCE_STATE_MACHINE_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "reduce_state_machine_top3_v1": {"source_policy": "bad_trade_gate_top3_v1", "slot_cap": 3},
    "reduce_state_machine_top5_v1": {"source_policy": "bad_trade_gate_top5_v1", "slot_cap": 5},
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
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    return thesis_l5.parse_date(value)


def pct_return(start: float, end: float) -> float:
    if start <= 0:
        return 0.0
    return end / start - 1.0


def net_return(start: float, end: float) -> float:
    return pct_return(start, end) - ROUND_TRIP_COST_BPS / 10000.0


def source_review_rows() -> list[dict[str, object]]:
    rows = [
        ("risk_manager", "CME 2% risk rule", "risk per trade must be defined before entry; reduce cannot be an afterthought", "adopt"),
        ("execution_trader", "CME position and risk management", "stop or reduction logic must protect against a loss larger than tolerance", "adopt"),
        ("portfolio_pm", "CFA active equity portfolio construction", "position size and active risk must be constrained before concentration increases", "adopt"),
        ("factor_pm", "AQR portfolio construction matters", "portfolio construction can dominate signal quality when exposures cluster", "adopt"),
        ("risk_layer_pm", "BlackRock risk decomposition", "risk should be decomposed into drivers rather than viewed security-by-security only", "adopt"),
        ("event_study_quant", "MacKinlay event studies", "post-event price response must be interpreted as information, not ignored until month-end", "adopt"),
        ("distress_researcher", "Campbell-Hilscher-Szilagyi distress risk", "terminal risk and drawdown risk need different exits", "adopt"),
        ("momentum_quant", "AQR momentum everywhere", "failed relative strength after entry is a different state than temporary noise", "adopt"),
        ("backend_engineer", "project harness discipline", "runtime checks must not use future outcomes for assignment", "adopt"),
        ("governance_reviewer", "Task747 validation map", "diagnostic pass cannot approve strategy or deployment", "adopt"),
    ]
    return [
        {
            "task_id": "Task1728",
            "expert_review_id": f"REDUCE1728-{idx:03d}",
            "expert_role": role,
            "source_anchor": source,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, source, critique, decision) in enumerate(rows, 1)
    ]


def contract_rows() -> list[dict[str, object]]:
    specs = [
        ("preventive_reduce", "risk is fragile before large damage", "reduce 20-30 percent early; never treat as solved"),
        ("damage_reduce", "drawdown and relative weakness have already appeared", "reduce 35-60 percent and start recovery clock"),
        ("failed_reduce_to_exit", "recovery does not occur after reduce", "exit remaining position instead of carrying wounded exposure"),
        ("direct_exit", "terminal or thesis-break state appears", "skip reduce and exit"),
        ("hold", "high-quality thesis survives and relative weakness is not confirmed", "hold to planned exit"),
    ]
    return [
        {
            "task_id": "Task1729",
            "reduce_contract_id": f"REDUCECON1729-{idx:03d}",
            "reduce_state": state,
            "condition": condition,
            "action_rule": rule,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (state, condition, rule) in enumerate(specs, 1)
    ]


def selected_rows() -> list[dict[str, str]]:
    return read_csv(TASK1698 / "task1702_top3_top5_candidate_compressor.csv")


def baseline_metrics() -> dict[str, dict[str, str]]:
    return {row["policy_variant_id"]: row for row in read_csv(TASK1698 / "task1705_bad_trade_gate_replay_metrics.csv")}


def selected_by_policy_decision() -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in selected_rows():
        groups[(row["policy_variant_id"], row["decision_asof_ts"])].append(row)
    return groups


def close_before_or_on(frame: pd.DataFrame | None, d: date) -> tuple[date, float] | None:
    close = replay.close_on_or_before(frame, d)
    if not close:
        return None
    return close[0], close[1]


def relative_return(qqq: pd.DataFrame | None, entry_date: date, current_date: date, qqq_entry_price: float | None, stock_ret: float) -> float:
    if qqq is None or not qqq_entry_price:
        return stock_ret
    qqq_close = replay.close_on_or_before(qqq, current_date)
    if not qqq_close:
        return stock_ret
    return stock_ret - pct_return(qqq_entry_price, qqq_close[1])


def decide_reduce_state(
    frame: pd.DataFrame | None,
    qqq: pd.DataFrame | None,
    entry_date: date,
    planned_exit: date,
    entry_price: float,
    qqq_entry_price: float | None,
    risk_bucket: str,
    quality_bucket: str,
    payoff_score: float,
) -> dict[str, object]:
    if frame is None:
        return {
            "reduce_state": "hold",
            "action": "hold",
            "reason": "missing_price_path_hold",
            "reduce_date": "",
            "reduce_price": "",
            "reduce_fraction": 0.0,
            "exit_date": "",
            "exit_price": "",
        }
    sub = frame[(frame["Date"] >= entry_date) & (frame["Date"] <= planned_exit)]
    if sub.empty:
        return {
            "reduce_state": "hold",
            "action": "hold",
            "reason": "empty_price_path_hold",
            "reduce_date": "",
            "reduce_price": "",
            "reduce_fraction": 0.0,
            "exit_date": "",
            "exit_price": "",
        }
    fragile = risk_bucket in {"terminal_business_risk", "listing_compliance_risk", "dilution_pressure", "financing_stress"} or quality_bucket in {"low_payoff_candidate", "watch_or_cap_candidate"}
    high_quality = quality_bucket == "top3_payoff_candidate" and payoff_score >= 80 and risk_bucket in {"ordinary_pass", "theme_volatility"}
    reduce_event: dict[str, object] | None = None
    for row in sub.itertuples(index=False):
        current_date = row.Date
        close = float(row.Close)
        stock_ret = pct_return(entry_price, close)
        rel = relative_return(qqq, entry_date, current_date, qqq_entry_price, stock_ret)
        if fragile and stock_ret <= -0.055 and rel <= -0.025:
            return {
                "reduce_state": "direct_exit",
                "action": "exit",
                "reason": "fragile_thesis_relative_damage_direct_exit",
                "reduce_date": "",
                "reduce_price": "",
                "reduce_fraction": 0.0,
                "exit_date": current_date.isoformat(),
                "exit_price": round(close, 6),
            }
        if reduce_event is None:
            if high_quality and stock_ret <= -0.09 and rel <= -0.06:
                reduce_event = {
                    "reduce_state": "preventive_reduce",
                    "action": "reduce",
                    "reason": "high_quality_relative_break_preventive_reduce",
                    "reduce_date": current_date,
                    "reduce_price": close,
                    "reduce_fraction": 0.25,
                    "stock_ret_at_reduce": stock_ret,
                    "rel_ret_at_reduce": rel,
                }
            elif stock_ret <= -0.08 and rel <= -0.05:
                reduce_event = {
                    "reduce_state": "damage_reduce",
                    "action": "reduce",
                    "reason": "relative_damage_reduce",
                    "reduce_date": current_date,
                    "reduce_price": close,
                    "reduce_fraction": 0.55,
                    "stock_ret_at_reduce": stock_ret,
                    "rel_ret_at_reduce": rel,
                }
            elif stock_ret <= -0.12:
                reduce_event = {
                    "reduce_state": "damage_reduce",
                    "action": "reduce",
                    "reason": "absolute_damage_reduce",
                    "reduce_date": current_date,
                    "reduce_price": close,
                    "reduce_fraction": 0.45,
                    "stock_ret_at_reduce": stock_ret,
                    "rel_ret_at_reduce": rel,
                }
        else:
            reduce_date = reduce_event["reduce_date"]
            reduce_price = float(reduce_event["reduce_price"])
            days_after = len(sub[(sub["Date"] >= reduce_date) & (sub["Date"] <= current_date)])
            post_reduce_ret = pct_return(reduce_price, close)
            if days_after >= 6 and (post_reduce_ret <= -0.015 or stock_ret <= float(reduce_event["stock_ret_at_reduce"]) - 0.035):
                return {
                    "reduce_state": "failed_reduce_to_exit",
                    "action": "reduce_then_exit",
                    "reason": "reduce_recovery_failed_exit_remaining",
                    "reduce_date": reduce_date.isoformat(),
                    "reduce_price": round(reduce_price, 6),
                    "reduce_fraction": reduce_event["reduce_fraction"],
                    "exit_date": current_date.isoformat(),
                    "exit_price": round(close, 6),
                }
    if reduce_event:
        return {
            "reduce_state": reduce_event["reduce_state"],
            "action": "reduce",
            "reason": reduce_event["reason"],
            "reduce_date": reduce_event["reduce_date"].isoformat(),
            "reduce_price": round(float(reduce_event["reduce_price"]), 6),
            "reduce_fraction": reduce_event["reduce_fraction"],
            "exit_date": "",
            "exit_price": "",
        }
    return {
        "reduce_state": "hold",
        "action": "hold",
        "reason": "no_reduce_trigger_hold",
        "reduce_date": "",
        "reduce_price": "",
        "reduce_fraction": 0.0,
        "exit_date": "",
        "exit_price": "",
    }


def run_replay() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    specs = damage.trade_specs_by_id()
    groups = selected_by_policy_decision()
    cache: dict[str, pd.DataFrame | None] = {}
    qqq = replay.load_price("QQQ", cache)
    state_rows: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    state_idx = 1
    trade_idx = 1
    for policy_id, policy in POLICIES.items():
        source_policy = policy["source_policy"]
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in groups if key[0] == source_policy}):
            items = sorted(groups[(source_policy, decision_ts)], key=lambda row: to_float(row["compressed_rank"]))
            base_alloc = capital / int(policy["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                spec = specs.get(selected["trade_spec_id"], {})
                frame = replay.load_price(selected["symbol"], cache)
                entry_after = parse_date(spec.get("entry_after_date")) or date(1970, 1, 1)
                scheduled_exit = parse_date(spec.get("exit_on_or_before_date")) or entry_after
                entry = replay.price_on_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                planned = close_before_or_on(frame, scheduled_exit)
                if not planned:
                    continue
                planned_exit_date, planned_exit_price = planned
                qqq_entry = replay.price_on_or_after(qqq, entry_date)
                qqq_entry_price = qqq_entry[1] if qqq_entry else None
                decision = decide_reduce_state(
                    frame,
                    qqq,
                    entry_date,
                    planned_exit_date,
                    entry_price,
                    qqq_entry_price,
                    selected["collapse_risk_bucket"],
                    selected["payoff_quality_bucket"],
                    to_float(selected["payoff_quality_score"]),
                )
                state_rows.append(
                    {
                        "task_id": "Task1730",
                        "reduce_state_id": f"REDUCESTATE1730-{state_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "selection_reason": selected["selection_reason"],
                        "collapse_risk_bucket": selected["collapse_risk_bucket"],
                        "payoff_quality_bucket": selected["payoff_quality_bucket"],
                        "payoff_quality_score": selected["payoff_quality_score"],
                        "reduce_state": decision["reduce_state"],
                        "runtime_action": decision["action"],
                        "runtime_reason": decision["reason"],
                        "reduce_date": decision["reduce_date"],
                        "reduce_fraction": decision["reduce_fraction"],
                        "failed_reduce_exit_date": decision["exit_date"] if decision["reduce_state"] == "failed_reduce_to_exit" else "",
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                state_idx += 1
                size_multiplier = to_float(selected.get("position_size_cap_multiplier"), 1.0)
                allocated = base_alloc * size_multiplier
                reduced_capital = 0.0
                reduce_pnl = 0.0
                final_pnl = 0.0
                actual_exit_date = planned_exit_date
                actual_exit_price = planned_exit_price
                action = str(decision["action"])
                if action == "exit":
                    actual_exit_date = parse_date(decision["exit_date"]) or planned_exit_date
                    actual_exit_price = to_float(decision["exit_price"], planned_exit_price)
                    final_pnl = allocated * net_return(entry_price, actual_exit_price)
                elif action in {"reduce", "reduce_then_exit"}:
                    reduce_fraction = to_float(decision["reduce_fraction"])
                    reduce_date = parse_date(decision["reduce_date"]) or planned_exit_date
                    reduce_price = to_float(decision["reduce_price"], planned_exit_price)
                    reduced_capital = allocated * reduce_fraction
                    reduce_pnl = reduced_capital * net_return(entry_price, reduce_price)
                    remaining_capital = allocated - reduced_capital
                    if action == "reduce_then_exit":
                        actual_exit_date = parse_date(decision["exit_date"]) or planned_exit_date
                        actual_exit_price = to_float(decision["exit_price"], planned_exit_price)
                    final_pnl = remaining_capital * net_return(entry_price, actual_exit_price)
                else:
                    final_pnl = allocated * net_return(entry_price, planned_exit_price)
                pnl = reduce_pnl + final_pnl
                period_pnl += pnl
                capital += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1731",
                        "trade_row_id": f"REDUCETRADE1731-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "planned_exit_date": planned_exit_date.isoformat(),
                        "actual_exit_date": actual_exit_date.isoformat(),
                        "actual_exit_price": round(actual_exit_price, 6),
                        "reduce_state": decision["reduce_state"],
                        "runtime_action": action,
                        "runtime_reason": decision["reason"],
                        "position_size_cap_multiplier": round(size_multiplier, 4),
                        "capital_allocated": round(allocated, 4),
                        "reduced_capital": round(reduced_capital, 4),
                        "reduce_pnl": round(reduce_pnl, 4),
                        "final_pnl": round(final_pnl, 4),
                        "pnl": round(pnl, 4),
                        "net_return": round(pnl / allocated, 8) if allocated else 0.0,
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task1731",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "authority": AUTHORITY,
                }
            )
    return state_rows, trades, equity


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base = baseline_metrics()
    base_map = {
        "reduce_state_machine_top3_v1": "bad_trade_gate_top3_v1",
        "reduce_state_machine_top5_v1": "bad_trade_gate_top5_v1",
    }
    trade_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trade_groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_groups[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(equity_groups.items()):
        tr_rows = trade_groups[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(parse_date(row["actual_exit_date"]) or start for row in tr_rows)
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        base_row = base[base_map[policy_id]]
        rows.append(
            {
                "task_id": "Task1732",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": base_map[policy_id],
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "hold_count": sum(1 for row in tr_rows if row["runtime_action"] == "hold"),
                "reduce_count": sum(1 for row in tr_rows if row["runtime_action"] == "reduce"),
                "reduce_then_exit_count": sum(1 for row in tr_rows if row["runtime_action"] == "reduce_then_exit"),
                "exit_count": sum(1 for row in tr_rows if row["runtime_action"] == "exit"),
                "baseline_final_equity": base_row["final_equity"],
                "baseline_cagr": base_row["cagr"],
                "baseline_max_drawdown": base_row["max_drawdown"],
                "delta_final_equity": round(final - to_float(base_row["final_equity"]), 4),
                "delta_cagr": round(cagr - to_float(base_row["cagr"]), 6),
                "delta_mdd": round(mdd - to_float(base_row["max_drawdown"]), 6),
                "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
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


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
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
                "task_id": "Task1733",
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


def attribution_rows(state_rows: list[dict[str, object]], trades: list[dict[str, object]], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for label, counts in [
        ("reduce_state", Counter(str(row["reduce_state"]) for row in state_rows)),
        ("runtime_action", Counter(str(row["runtime_action"]) for row in state_rows)),
    ]:
        for reason, count in counts.most_common():
            rows.append(
                {
                    "task_id": "Task1734",
                    "attribution_id": f"REDUCEATTR1734-{idx:05d}",
                    "failure_area": label,
                    "reason": reason,
                    "row_count": count,
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    by_action: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        by_action[str(row["runtime_action"])].append(row)
    for action, group in sorted(by_action.items()):
        pnl = sum(to_float(row["pnl"]) for row in group)
        rows.append(
            {
                "task_id": "Task1734",
                "attribution_id": f"REDUCEATTR1734-{idx:05d}",
                "failure_area": "action_pnl",
                "reason": action,
                "row_count": len(group),
                "pnl_sum": round(pnl, 4),
                "avg_net_return": round(sum(to_float(row["net_return"]) for row in group) / len(group), 6) if group else 0.0,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for row in metrics:
        if row["target_cagr_30pct_met"] != "1" or row["target_mdd_minus30pct_met"] != "1":
            rows.append(
                {
                    "task_id": "Task1734",
                    "attribution_id": f"REDUCEATTR1734-{idx:05d}",
                    "failure_area": "target_failure",
                    "policy_variant_id": row["policy_variant_id"],
                    "cagr": row["cagr"],
                    "max_drawdown": row["max_drawdown"],
                    "delta_final_equity": row["delta_final_equity"],
                    "delta_mdd": row["delta_mdd"],
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def gate_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1746",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in metrics) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in metrics) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "reduce_state_machine_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1747",
            "verdict": "reduce_state_machine_implemented_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit whether failed-reduce exits improve true daily drawdown and calibrate cluster-aware pre-entry risk budget before another candidate expansion",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], split: list[dict[str, object]], attr: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1728-1747 Reduce State Machine",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Best policy: `{closeout['best_policy_variant_id']}`.",
        f"- Best final equity: {closeout['best_final_equity']}.",
        f"- Best CAGR: {closeout['best_cagr']}.",
        f"- Best MDD: {closeout['best_max_drawdown']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Hold | Reduce | Reduce Then Exit | Exit | CAGR Target | MDD Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['baseline_final_equity']} | {row['baseline_max_drawdown']} | {row['delta_final_equity']} | {row['delta_mdd']} | {row['trade_count']} | {row['hold_count']} | {row['reduce_count']} | {row['reduce_then_exit_count']} | {row['exit_count']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |"
        )
    lines.extend(["", "Split/OOS diagnostics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Failure / attribution:", ""])
    for row in attr[:30]:
        lines.append(
            f"- `{row['failure_area']}`: {row.get('reason', row.get('policy_variant_id', ''))} count={row.get('row_count','')} pnl={row.get('pnl_sum','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')}"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Reduce is now a state machine, not a weaker exit.",
            "2. The machine can reduce early, reduce after damage, or exit remaining exposure if recovery fails.",
            "3. This tests the user's core diagnosis: late/weak reduce was a direct cause of drawdown.",
            "4. The replay is diagnostic only and does not approve strategy.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1728_expert_review.csv`",
            "- `task1729_reduce_contract.csv`",
            "- `task1730_reduce_state_panel.csv`",
            "- `task1731_reduce_state_replay_trades.csv/equity`",
            "- `task1732_reduce_state_replay_metrics.csv`",
            "- `task1733_split_oos_metrics.csv`",
            "- `task1734_failure_attribution.csv`",
            "- `task1746_acceptance_gate.csv`",
            "- `task1747_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1728_1747_reduce_state_machine_validate.py`",
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
    experts = source_review_rows()
    contract = contract_rows()
    states, trades, equity = run_replay()
    metrics = build_metrics(trades, equity)
    splits = split_rows(equity)
    attr = attribution_rows(states, trades, metrics)
    gate, closeout = gate_closeout(metrics)
    outputs = [
        ("task1728_expert_review.csv", experts),
        ("task1729_reduce_contract.csv", contract),
        ("task1730_reduce_state_panel.csv", states),
        ("task1731_reduce_state_replay_trades.csv", trades),
        ("task1731_reduce_state_replay_equity.csv", equity),
        ("task1732_reduce_state_replay_metrics.csv", metrics),
        ("task1733_split_oos_metrics.csv", splits),
        ("task1734_failure_attribution.csv", attr),
        ("task1746_acceptance_gate.csv", gate),
        ("task1747_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1747_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(metrics, splits, attr, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1728_1747] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
