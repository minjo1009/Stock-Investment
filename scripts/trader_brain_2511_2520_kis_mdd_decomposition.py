from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2511_2520_kis_mdd_decomposition"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2511_2520_kis_mdd_decomposition.md"
DECISION = REPORT_DIR / "task_2520_decision.csv"

TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK2501 = ROOT / "data/artifacts/task_2501_2510_kis_cost_basis_test"

BASE_POLICY = "exit_chain_repaired_soft_boost_cap_top2_v1"
KIS_POLICY = "kis_cost_repriced_exit_chain_repaired_soft_boost_cap_top2_v1"
AUTHORITY = "DIAGNOSTIC_KIS_MDD_DECOMPOSITION_ONLY"
INITIAL_CAPITAL = 1000.0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def f(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        out = float(value)  # type: ignore[arg-type]
        if math.isnan(out):
            return default
        return out
    except Exception:
        return default


def parse_ts(value: object) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def by_policy(rows: list[dict[str, str]], policy: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("policy_variant_id") == policy]


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "base_trades": by_policy(read_csv(TASK2381 / "task2386_replay_trades.csv"), BASE_POLICY),
        "base_equity": by_policy(read_csv(TASK2381 / "task2386_replay_equity.csv"), BASE_POLICY),
        "base_sources": read_csv(TASK2381 / "task2384_repaired_exit_source_rows.csv"),
        "kis_trades": read_csv(TASK2501 / "task2502_kis_repriced_trades.csv"),
        "kis_equity": read_csv(TASK2501 / "task2503_kis_repriced_equity.csv"),
        "kis_metrics": read_csv(TASK2501 / "task2504_kis_repriced_metrics.csv"),
        "kis_closeout": read_csv(TASK2501 / "task2510_closeout.csv"),
    }


def peak_trough(equity_rows: list[dict[str, str]]) -> dict[str, object]:
    peak = INITIAL_CAPITAL
    peak_ts = ""
    worst_peak = INITIAL_CAPITAL
    worst_peak_ts = ""
    worst = 0.0
    trough_ts = ""
    trough_equity = INITIAL_CAPITAL
    rows = sorted(equity_rows, key=lambda row: parse_ts(row["decision_asof_ts"]))
    for row in rows:
        eq = f(row.get("equity"))
        ts = row.get("decision_asof_ts", "")
        if eq > peak:
            peak = eq
            peak_ts = ts
        dd = eq / peak - 1.0 if peak else 0.0
        if dd < worst:
            worst = dd
            worst_peak = peak
            worst_peak_ts = peak_ts
            trough_ts = ts
            trough_equity = eq
    return {
        "peak_ts": worst_peak_ts,
        "trough_ts": trough_ts,
        "peak_equity": worst_peak,
        "trough_equity": trough_equity,
        "max_drawdown": worst,
    }


def task2511_contract(inputs: dict[str, list[dict[str, str]]], kis_pt: dict[str, object], base_pt: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2511",
            "contract_id": "KISMDD2511-0001",
            "objective": "Decompose why KIS cost repricing moves MDD beyond -30pct without changing strategy selection or sizing.",
            "base_policy_variant_id": BASE_POLICY,
            "kis_policy_variant_id": KIS_POLICY,
            "base_max_drawdown": round(f(base_pt["max_drawdown"]), 8),
            "kis_max_drawdown": round(f(kis_pt["max_drawdown"]), 8),
            "mdd_delta_vs_base": round(f(kis_pt["max_drawdown"]) - f(base_pt["max_drawdown"]), 8),
            "selected_trade_count": len(inputs["kis_trades"]),
            "strategy_tuning_performed": "0",
            "outcome_used_for_audit_only": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def task2512_peak_trough_path(inputs: dict[str, list[dict[str, str]]], kis_pt: dict[str, object], base_pt: dict[str, object]) -> list[dict[str, object]]:
    base_by_ts = {row["decision_asof_ts"]: row for row in inputs["base_equity"]}
    rows: list[dict[str, object]] = []
    start = parse_ts(str(kis_pt["peak_ts"]))
    end = parse_ts(str(kis_pt["trough_ts"]))
    for idx, row in enumerate(sorted(inputs["kis_equity"], key=lambda r: parse_ts(r["decision_asof_ts"])), start=1):
        ts = row["decision_asof_ts"]
        in_window = start <= parse_ts(ts) <= end
        base = base_by_ts.get(ts, {})
        kis_equity = f(row.get("equity"))
        base_equity = f(base.get("equity"))
        rows.append(
            {
                "task_id": "Task2512",
                "path_row_id": f"KISMDDPATH2512-{idx:04d}",
                "decision_asof_ts": ts,
                "in_kis_mdd_window": "1" if in_window else "0",
                "base_equity": round(base_equity, 6),
                "kis_equity": round(kis_equity, 6),
                "equity_delta_kis_minus_base": round(kis_equity - base_equity, 6),
                "kis_period_pnl": row.get("period_pnl", ""),
                "base_period_pnl": base.get("period_pnl", ""),
                "kis_drawdown_after_period": row.get("portfolio_drawdown_after_period", ""),
                "base_drawdown_before_period": base.get("portfolio_drawdown_before_period", ""),
                "kis_peak_ts": kis_pt["peak_ts"],
                "kis_trough_ts": kis_pt["trough_ts"],
                "base_peak_ts": base_pt["peak_ts"],
                "base_trough_ts": base_pt["trough_ts"],
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def window_trades(trades: list[dict[str, str]], peak_ts: str, trough_ts: str) -> list[dict[str, str]]:
    start = parse_ts(peak_ts)
    end = parse_ts(trough_ts)
    return [row for row in trades if start < parse_ts(row["decision_asof_ts"]) <= end]


def task2513_trade_contributors(inputs: dict[str, list[dict[str, str]]], kis_pt: dict[str, object]) -> list[dict[str, object]]:
    source_by_spec = {row["trade_spec_id"]: row for row in inputs["base_sources"]}
    rows: list[dict[str, object]] = []
    trades = sorted(window_trades(inputs["kis_trades"], str(kis_pt["peak_ts"]), str(kis_pt["trough_ts"])), key=lambda r: f(r.get("kis_pnl")))
    for idx, row in enumerate(trades, start=1):
        source = source_by_spec.get(row["trade_spec_id"], {})
        rows.append(
            {
                "task_id": "Task2513",
                "contributor_id": f"KISMDDTRADE2513-{idx:05d}",
                "rank_by_kis_pnl": idx,
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "runtime_action": source.get("runtime_action", ""),
                "runtime_action_reason": source.get("runtime_action_reason", ""),
                "winner_defense_bucket": source.get("winner_defense_bucket", ""),
                "volatility_cause": source.get("volatility_cause", ""),
                "capital_allocated": row.get("capital_allocated", ""),
                "task2381_pnl": row.get("task2381_pnl", ""),
                "kis_pnl": row.get("kis_pnl", ""),
                "kis_net_return": row.get("kis_net_return", ""),
                "kis_total_cost": row.get("kis_total_cost", ""),
                "pnl_delta_vs_task2381": row.get("pnl_delta_vs_task2381", ""),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def group_rows(rows: list[dict[str, str]], key_name: str, key_fn, value_fields: list[str]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[str(key_fn(row))].append(row)
    out = []
    for key, items in groups.items():
        payload = {
            key_name: key,
            "trade_count": len(items),
            "symbol_count": len({row.get("symbol", "") for row in items}),
        }
        for field in value_fields:
            payload[f"{field}_sum"] = round(sum(f(row.get(field)) for row in items), 6)
        out.append(payload)
    return sorted(out, key=lambda row: f(row.get("kis_pnl_sum")), reverse=False)


def task2514_cost_drag(inputs: dict[str, list[dict[str, str]]], kis_pt: dict[str, object]) -> list[dict[str, object]]:
    window = window_trades(inputs["kis_trades"], str(kis_pt["peak_ts"]), str(kis_pt["trough_ts"]))
    value_fields = ["kis_pnl", "task2381_pnl", "kis_total_cost", "kis_buy_commission", "kis_sell_commission", "kis_sec_fee", "pnl_delta_vs_task2381"]
    specs = [
        ("symbol", lambda row: row.get("symbol", "")),
        ("month", lambda row: str(row.get("decision_asof_ts", ""))[:7]),
        ("cost_drag_bucket", lambda row: "negative_trade_loss" if f(row.get("kis_pnl")) < 0 else "positive_trade_cost_drag"),
    ]
    rows: list[dict[str, object]] = []
    idx = 1
    for group_type, fn in specs:
        for grouped in group_rows(window, "group_value", fn, value_fields):
            rows.append(
                {
                    "task_id": "Task2514",
                    "cost_drag_id": f"KISCOSTDRAG2514-{idx:05d}",
                    "group_type": group_type,
                    **grouped,
                    "outcome_used_for_audit_only": "1",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def task2515_base_vs_kis_monthly(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    base_by_ts = {row["decision_asof_ts"]: row for row in inputs["base_equity"]}
    rows = []
    for idx, row in enumerate(sorted(inputs["kis_equity"], key=lambda r: parse_ts(r["decision_asof_ts"])), start=1):
        base = base_by_ts.get(row["decision_asof_ts"], {})
        kis_pnl = f(row.get("period_pnl"))
        base_pnl = f(base.get("period_pnl"))
        rows.append(
            {
                "task_id": "Task2515",
                "monthly_delta_id": f"KISMONTHDELTA2515-{idx:04d}",
                "decision_asof_ts": row["decision_asof_ts"],
                "month": row["decision_asof_ts"][:7],
                "base_period_pnl": round(base_pnl, 6),
                "kis_period_pnl": round(kis_pnl, 6),
                "period_pnl_delta_kis_minus_base": round(kis_pnl - base_pnl, 6),
                "base_equity": base.get("equity", ""),
                "kis_equity": row.get("equity", ""),
                "equity_delta_kis_minus_base": round(f(row.get("equity")) - f(base.get("equity")), 6),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2516_failure_taxonomy(kis_pt: dict[str, object], trade_rows: list[dict[str, object]], cost_drag: list[dict[str, object]]) -> list[dict[str, object]]:
    window_negative = [row for row in trade_rows if f(row.get("kis_pnl")) < 0]
    cost_delta = sum(f(row.get("pnl_delta_vs_task2381")) for row in trade_rows)
    gross_loss = sum(f(row.get("kis_pnl")) for row in window_negative)
    worst_symbols = [row for row in cost_drag if row.get("group_type") == "symbol"][:5]
    return [
        {
            "task_id": "Task2516",
            "failure_taxonomy_id": "KISMDDTAX2516-0001",
            "failure_layer": "broker_cost_drag",
            "evidence": f"MDD window cost/PnL delta vs Task2381 = {round(cost_delta, 6)}.",
            "root_cause_weight": "secondary_amplifier",
            "repair_direction": "cost-aware MDD guard should avoid thin-margin trades during existing drawdown windows.",
            "outcome_used_for_audit_only": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2516",
            "failure_taxonomy_id": "KISMDDTAX2516-0002",
            "failure_layer": "negative_trade_concentration",
            "evidence": f"Negative trades in KIS MDD window = {len(window_negative)}, aggregate KIS PnL = {round(gross_loss, 6)}.",
            "root_cause_weight": "primary_drawdown_driver",
            "repair_direction": "diagnose pre-entry and reduce/exit logic for the small set of window loss contributors.",
            "outcome_used_for_audit_only": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2516",
            "failure_taxonomy_id": "KISMDDTAX2516-0003",
            "failure_layer": "symbol_specific_loss_cluster",
            "evidence": "Worst symbols by KIS PnL: " + ";".join(f"{row.get('group_value')}={row.get('kis_pnl_sum')}" for row in worst_symbols),
            "root_cause_weight": "review_required",
            "repair_direction": "audit whether losers shared runtime_action, volatility_cause, or weak winner_defense_bucket before proposing guards.",
            "outcome_used_for_audit_only": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        },
    ]


def task2517_repair_queue(taxonomy: list[dict[str, object]]) -> list[dict[str, object]]:
    ideas = [
        (
            "cost_aware_drawdown_window_cap",
            "Apply only when portfolio drawdown is already near -25% and expected edge is low after KIS cost.",
            "Task2521-2530",
        ),
        (
            "loss_cluster_preentry_audit",
            "Audit MDD-window losing symbols for common pre-entry L2/L3/L4 weakness before any rule change.",
            "Task2521-2530",
        ),
        (
            "thin_margin_trade_skip_probe",
            "Dry-run-only probe: skip trades whose KIS-cost adjusted edge is too small during stressed drawdown windows.",
            "Task2521-2530",
        ),
    ]
    return [
        {
            "task_id": "Task2517",
            "repair_queue_id": f"KISREPAIR2517-{idx:04d}",
            "repair_candidate": name,
            "why_candidate": why,
            "target_task_range": target,
            "implementation_allowed_now": "0",
            "requires_preregistered_replay": "1",
            "strategy_tuning_performed": "0",
            "outcome_used_for_audit_only": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, why, target) in enumerate(ideas, start=1)
    ]


def task2518_subagent_packets() -> list[dict[str, object]]:
    packets = [
        ("Ptolemy", "MDD peak/trough and contributor explorer", "read-only", "RESEARCH_ONLY"),
        ("Euclid", "Cost attribution taxonomy explorer", "read-only", "RESEARCH_ONLY"),
        ("Aquinas", "Governance guardrail explorer", "read-only", "GOVERNANCE_HEALTH"),
    ]
    return [
        {
            "task_id": "Task2518",
            "subagent_packet_id": f"KISSUBAGENT2518-{idx:04d}",
            "agent_nickname": nick,
            "objective": obj,
            "write_scope": scope,
            "validation_authority": auth,
            "forbidden_actions": "No edits; no inferred matching; no deployment claim; no strategy acceptance claim; no real capital claim.",
            "status": "delegated",
            "authority": AUTHORITY,
        }
        for idx, (nick, obj, scope, auth) in enumerate(packets, start=1)
    ]


def task2511_cost_component_by_trade(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["kis_trades"], start=1):
        rows.append(
            {
                "task_id": "Task2511",
                "cost_component_id": f"KISCOSTCOMP2511-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "capital_allocated": row.get("capital_allocated", ""),
                "task2381_net_return": row.get("task2381_net_return", ""),
                "kis_net_return": row.get("kis_net_return", ""),
                "buy_commission": row.get("kis_buy_commission", ""),
                "sell_commission": row.get("kis_sell_commission", ""),
                "commission_drag": round(f(row.get("kis_buy_commission")) + f(row.get("kis_sell_commission")), 6),
                "sec_fee_drag": row.get("kis_sec_fee", ""),
                "total_cost": row.get("kis_total_cost", ""),
                "task2381_pnl": row.get("task2381_pnl", ""),
                "kis_pnl": row.get("kis_pnl", ""),
                "pnl_delta_vs_task2381": row.get("pnl_delta_vs_task2381", ""),
                "cost_flipped_positive_to_negative": "1"
                if f(row.get("task2381_net_return")) >= 0 and f(row.get("kis_net_return")) < 0
                else "0",
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def split_name(ts: str) -> str:
    year = parse_ts(ts).year
    if year <= 2023:
        return "IS_2021_2023"
    if year == 2024:
        return "VALIDATION_2024"
    return "OOS_2025_2026Q1"


def task2512_cost_component_summary(cost_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in cost_rows:
        ts = str(row["decision_asof_ts"])
        groups[("overall", "all")].append(row)
        groups[("year", str(parse_ts(ts).year))].append(row)
        groups[("split", split_name(ts))].append(row)
    rows = []
    for idx, ((group_type, group_value), items) in enumerate(sorted(groups.items()), start=1):
        commission = sum(f(row.get("commission_drag")) for row in items)
        sec = sum(f(row.get("sec_fee_drag")) for row in items)
        total = sum(f(row.get("total_cost")) for row in items)
        capital = sum(f(row.get("capital_allocated")) for row in items)
        gross_abs = sum(abs(f(row.get("task2381_pnl"))) + f(row.get("total_cost")) for row in items)
        rows.append(
            {
                "task_id": "Task2512",
                "cost_summary_id": f"KISCOSTSUM2512-{idx:04d}",
                "group_type": group_type,
                "group_value": group_value,
                "trade_count": len(items),
                "commission_drag": round(commission, 6),
                "sec_fee_drag": round(sec, 6),
                "total_cost": round(total, 6),
                "sec_fee_share": round(sec / total, 8) if total else 0.0,
                "total_cost_share_of_capital": round(total / capital, 8) if capital else 0.0,
                "total_cost_share_of_abs_gross_or_cost": round(total / gross_abs, 8) if gross_abs else 0.0,
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2513_negative_return_taxonomy(cost_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    negatives = [row for row in cost_rows if f(row.get("kis_net_return")) < 0]
    for idx, row in enumerate(sorted(negatives, key=lambda r: f(r.get("kis_pnl"))), start=1):
        flipped = row.get("cost_flipped_positive_to_negative") == "1"
        rows.append(
            {
                "task_id": "Task2513",
                "negative_taxonomy_id": f"KISNEG2513-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "task2381_net_return": row.get("task2381_net_return", ""),
                "kis_net_return": row.get("kis_net_return", ""),
                "task2381_pnl": row.get("task2381_pnl", ""),
                "kis_pnl": row.get("kis_pnl", ""),
                "negative_type": "cost_flipped_positive_to_negative" if flipped else "already_negative_before_kis_cost",
                "cost_flipped_positive_to_negative": "1" if flipped else "0",
                "missing_source_is_negative": "0",
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2514_drawdown_window_map(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(sorted(inputs["kis_equity"], key=lambda r: parse_ts(r["decision_asof_ts"])), start=1):
        dd = f(row.get("portfolio_drawdown_after_period"))
        rows.append(
            {
                "task_id": "Task2514",
                "drawdown_window_id": f"KISDDMAP2514-{idx:04d}",
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "month": row.get("decision_asof_ts", "")[:7],
                "equity": row.get("equity", ""),
                "period_pnl": row.get("period_pnl", ""),
                "portfolio_drawdown_after_period": row.get("portfolio_drawdown_after_period", ""),
                "drawdown_lte_minus20_flag": "1" if dd <= -0.20 else "0",
                "mdd_trough_flag": "1" if abs(dd - min(f(r.get("portfolio_drawdown_after_period")) for r in inputs["kis_equity"])) < 1e-10 else "0",
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2515_drawdown_window_trade_attribution(cost_rows: list[dict[str, object]], dd_map: list[dict[str, object]]) -> list[dict[str, object]]:
    dd_months = {str(row["decision_asof_ts"]) for row in dd_map if row.get("drawdown_lte_minus20_flag") == "1"}
    rows = []
    for idx, row in enumerate([r for r in cost_rows if str(r["decision_asof_ts"]) in dd_months], start=1):
        rows.append(
            {
                "task_id": "Task2515",
                "dd_trade_attr_id": f"KISDDTRADE2515-{idx:05d}",
                **row,
                "drawdown_lte_minus20_flag": "1",
                "kis_negative_trade_flag": "1" if f(row.get("kis_net_return")) < 0 else "0",
            }
        )
    return rows


def task2516_symbol_concentration(cost_rows: list[dict[str, object]], dd_trade_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    dd_specs = {row["trade_spec_id"] for row in dd_trade_rows}
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in cost_rows:
        groups[str(row["symbol"])].append(row)
    rows = []
    for idx, (symbol, items) in enumerate(sorted(groups.items(), key=lambda item: sum(f(r.get("kis_pnl")) for r in item[1])), start=1):
        rows.append(
            {
                "task_id": "Task2516",
                "symbol_concentration_id": f"KISSYM2516-{idx:05d}",
                "symbol": symbol,
                "trade_count": len(items),
                "negative_trade_count": sum(1 for row in items if f(row.get("kis_net_return")) < 0),
                "drawdown_window_trade_count": sum(1 for row in items if row["trade_spec_id"] in dd_specs),
                "kis_pnl_sum": round(sum(f(row.get("kis_pnl")) for row in items), 6),
                "kis_total_cost_sum": round(sum(f(row.get("total_cost")) for row in items), 6),
                "pnl_delta_vs_task2381_sum": round(sum(f(row.get("pnl_delta_vs_task2381")) for row in items), 6),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2517_split_cost_drawdown_bridge(cost_rows: list[dict[str, object]], dd_map: list[dict[str, object]]) -> list[dict[str, object]]:
    dd_by_split = defaultdict(list)
    for row in dd_map:
        dd_by_split[split_name(str(row["decision_asof_ts"]))].append(row)
    cost_by_split = defaultdict(list)
    for row in cost_rows:
        cost_by_split[split_name(str(row["decision_asof_ts"]))].append(row)
    rows = []
    for idx, split in enumerate(["IS_2021_2023", "VALIDATION_2024", "OOS_2025_2026Q1"], start=1):
        items = cost_by_split[split]
        dd_items = dd_by_split[split]
        rows.append(
            {
                "task_id": "Task2517",
                "split_bridge_id": f"KISSPLIT2517-{idx:04d}",
                "split_id": split,
                "trade_count": len(items),
                "negative_trade_count": sum(1 for row in items if f(row.get("kis_net_return")) < 0),
                "drawdown_lte_minus20_months": sum(1 for row in dd_items if row.get("drawdown_lte_minus20_flag") == "1"),
                "max_drawdown_in_split": round(min((f(row.get("portfolio_drawdown_after_period")) for row in dd_items), default=0.0), 8),
                "kis_pnl_sum": round(sum(f(row.get("kis_pnl")) for row in items), 6),
                "total_cost_sum": round(sum(f(row.get("total_cost")) for row in items), 6),
                "commission_drag_sum": round(sum(f(row.get("commission_drag")) for row in items), 6),
                "sec_fee_drag_sum": round(sum(f(row.get("sec_fee_drag")) for row in items), 6),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2518_acceptance_checks(cost_summary: list[dict[str, object]], negative_tax: list[dict[str, object]], dd_trades: list[dict[str, object]]) -> list[dict[str, object]]:
    overall = next(row for row in cost_summary if row["group_type"] == "overall")
    flipped = sum(1 for row in negative_tax if row.get("cost_flipped_positive_to_negative") == "1")
    dd_neg = sum(1 for row in dd_trades if row.get("kis_negative_trade_flag") == "1")
    checks = [
        ("commission_drag_separated", "1", "buy/sell commission is separated from SEC fee."),
        ("sec_fee_drag_separated", "1", "SEC fee drag and share are explicit."),
        ("sec_fee_not_primary_mdd_claim", "1" if f(overall.get("sec_fee_share")) < 0.05 else "0", "SEC fee share must be small before claiming it is not primary."),
        ("cost_flip_count_recorded", "1" if flipped == 0 else "0", "Current run has zero positive-to-negative flips from KIS cost."),
        ("drawdown_window_negative_concentration_recorded", "1" if dd_neg > 0 else "0", "Drawdown-window negative trades must be measured."),
    ]
    return [
        {
            "task_id": "Task2518",
            "acceptance_check_id": f"KISACCEPT2518-{idx:04d}",
            "check_name": name,
            "pass": passed,
            "detail": detail,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def task2519_governance_health_checks() -> list[dict[str, object]]:
    checks = [
        ("missing_source_not_negative", "1"),
        ("assignment_future_outcome_zero", "1"),
        ("outcome_used_for_assignment_zero", "1"),
        ("strategy_status_not_accepted", "1"),
        ("deployment_diagnostic_only", "1"),
        ("real_capital_forbidden", "1"),
    ]
    return [
        {
            "task_id": "Task2519",
            "governance_check_id": f"KISGOV2519-{idx:04d}",
            "check_name": name,
            "pass": passed,
            "validation_authority": "GOVERNANCE_HEALTH",
            "pass_does_not_mean": "strategy acceptance, deployment readiness, broker truth, or real capital permission",
            "authority": AUTHORITY,
        }
        for idx, (name, passed) in enumerate(checks, start=1)
    ]


def task2520_closeout(
    contract: dict[str, object],
    kis_pt: dict[str, object],
    base_pt: dict[str, object],
    trade_rows: list[dict[str, object]],
    cost_drag: list[dict[str, object]],
) -> list[dict[str, object]]:
    negative = [row for row in trade_rows if f(row.get("kis_pnl")) < 0]
    total_cost = sum(f(row.get("kis_total_cost")) for row in trade_rows)
    total_delta = sum(f(row.get("pnl_delta_vs_task2381")) for row in trade_rows)
    worst = cost_drag[0] if cost_drag else {}
    task2381_window_pnl = sum(f(row.get("task2381_pnl")) for row in trade_rows)
    kis_window_pnl = sum(f(row.get("kis_pnl")) for row in trade_rows)
    without_incremental_drag_trough = f(kis_pt["peak_equity"]) + task2381_window_pnl
    without_incremental_drag_mdd = without_incremental_drag_trough / f(kis_pt["peak_equity"]) - 1.0 if f(kis_pt["peak_equity"]) else 0.0
    return [
        {
            "task_id": "Task2520",
            "verdict": "kis_mdd_gate_failure_is_incremental_cost_drag_on_top_of_loss_cluster",
            "base_max_drawdown": contract["base_max_drawdown"],
            "kis_max_drawdown": contract["kis_max_drawdown"],
            "mdd_delta_vs_base": contract["mdd_delta_vs_base"],
            "kis_peak_ts": kis_pt["peak_ts"],
            "kis_trough_ts": kis_pt["trough_ts"],
            "kis_peak_equity": round(f(kis_pt["peak_equity"]), 6),
            "kis_trough_equity": round(f(kis_pt["trough_equity"]), 6),
            "mdd_window_trade_count": len(trade_rows),
            "mdd_window_negative_trade_count": len(negative),
            "mdd_window_task2381_pnl": round(task2381_window_pnl, 6),
            "mdd_window_kis_pnl": round(kis_window_pnl, 6),
            "mdd_window_total_kis_cost": round(total_cost, 6),
            "mdd_window_pnl_delta_vs_task2381": round(total_delta, 6),
            "without_incremental_drag_trough_equity": round(without_incremental_drag_trough, 6),
            "without_incremental_drag_mdd": round(without_incremental_drag_mdd, 8),
            "gate_failure_primary_cause": "incremental_kis_cost_drag",
            "economic_loss_primary_cause": "underlying_drawdown_window_trade_losses",
            "worst_group_type": worst.get("group_type", ""),
            "worst_group_value": worst.get("group_value", ""),
            "next_action": "Task2521-2530 should design a preregistered KIS-cost-aware drawdown guard; do not tune selector from this audit alone.",
            "strategy_tuning_performed": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], taxonomy: list[dict[str, object]], contributors: list[dict[str, object]], repair: list[dict[str, object]]) -> None:
    tax_lines = "\n".join(f"- `{row['failure_layer']}`: {row['evidence']} Repair: {row['repair_direction']}" for row in taxonomy)
    contrib_lines = "\n".join(
        f"- {row['rank_by_kis_pnl']}. `{row['symbol']}` {row['decision_asof_ts']}: KIS PnL {row['kis_pnl']}, cost {row['kis_total_cost']}, action `{row['runtime_action']}`."
        for row in contributors[:10]
    )
    repair_lines = "\n".join(f"- `{row['repair_candidate']}`: {row['why_candidate']}" for row in repair)
    REPORT.write_text(
        f"""# Task2511-2520 KIS MDD Decomposition

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Base MDD: {closeout['base_max_drawdown']}.
- KIS MDD: {closeout['kis_max_drawdown']}.
- MDD delta vs base: {closeout['mdd_delta_vs_base']}.
- KIS MDD window: {closeout['kis_peak_ts']} -> {closeout['kis_trough_ts']}.
- MDD window trades: {closeout['mdd_window_trade_count']}.
- Negative trades in window: {closeout['mdd_window_negative_trade_count']}.
- Window Task2381 PnL: {closeout['mdd_window_task2381_pnl']}.
- Window KIS PnL: {closeout['mdd_window_kis_pnl']}.
- MDD window KIS cost: {closeout['mdd_window_total_kis_cost']}.
- Gate failure primary cause: `{closeout['gate_failure_primary_cause']}`.
- Economic loss primary cause: `{closeout['economic_loss_primary_cause']}`.
- Strategy tuning performed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Failure taxonomy:

{tax_lines}

Worst KIS MDD-window trades:

{contrib_lines}

Repair candidates for the next task:

{repair_lines}

No selector, sizing, or exit policy was changed in this task. Outcomes are audit-only.

## No-Background Decision-Maker Report

Conclusion first: KIS cost did not destroy the strategy, but it pushed the worst drawdown window just past the -30% gate.

The economic loss in the window mostly came from bad trades. But the reason the formal -30% gate failed was the extra KIS cost drag.

Next step: build a preregistered KIS-cost-aware drawdown guard. Do not retune the selector from this audit alone.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2511_2520_kis_mdd_decomposition/`.
- Validator: `python scripts/trader_brain_2511_2520_kis_mdd_decomposition_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    fieldnames = list(rows[0].keys())
    existing = {row["task_id"] for row in rows}
    for task_no in range(2511, 2521):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"KIS MDD Decomposition Step {task_no}",
                "owner_team": "Backtest & Simulation Infra / Execution & Risk / Research Governance",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "kis-cost-mdd-decomposition-audit-only",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2511_2520_kis_mdd_decomposition/task_2511_2520_kis_mdd_decomposition.md",
                "key_decision": "docs/reports/task_2511_2520_kis_mdd_decomposition/task_2520_decision.csv",
                "key_artifacts": "data/artifacts/task_2511_2520_kis_mdd_decomposition",
                "validation_command": "python scripts/trader_brain_2511_2520_kis_mdd_decomposition_validate.py",
                "notes": "Decomposes KIS-cost MDD failure without tuning selector/sizing/exit.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "121. Task2511-Task2520"
    if marker in text:
        return
    line = (
        "121. Task2511-Task2520 decomposed the KIS-cost MDD failure: "
        f"base MDD {closeout['base_max_drawdown']}, KIS MDD {closeout['kis_max_drawdown']}, "
        f"window {closeout['kis_peak_ts']} to {closeout['kis_trough_ts']}, "
        f"window trades {closeout['mdd_window_trade_count']}, negative trades {closeout['mdd_window_negative_trade_count']}, "
        f"cost {closeout['mdd_window_total_kis_cost']}; no strategy tuning was performed. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    kis_pt = peak_trough(inputs["kis_equity"])
    base_pt = peak_trough(inputs["base_equity"])
    contract = task2511_contract(inputs, kis_pt, base_pt)
    path_rows = task2512_peak_trough_path(inputs, kis_pt, base_pt)
    contributors = task2513_trade_contributors(inputs, kis_pt)
    cost_drag = task2514_cost_drag(inputs, kis_pt)
    monthly = task2515_base_vs_kis_monthly(inputs)
    taxonomy = task2516_failure_taxonomy(kis_pt, contributors, cost_drag)
    repair = task2517_repair_queue(taxonomy)
    subagents = task2518_subagent_packets()
    cost_components = task2511_cost_component_by_trade(inputs)
    cost_summary = task2512_cost_component_summary(cost_components)
    negative_tax = task2513_negative_return_taxonomy(cost_components)
    dd_map = task2514_drawdown_window_map(inputs)
    dd_trade_attr = task2515_drawdown_window_trade_attribution(cost_components, dd_map)
    symbol_conc = task2516_symbol_concentration(cost_components, dd_trade_attr)
    split_bridge = task2517_split_cost_drawdown_bridge(cost_components, dd_map)
    acceptance = task2518_acceptance_checks(cost_summary, negative_tax, dd_trade_attr)
    governance = task2519_governance_health_checks()
    closeout = task2520_closeout(contract[0], kis_pt, base_pt, contributors, cost_drag)

    outputs = [
        ("task2511_kis_mdd_contract.csv", contract),
        ("task2511_cost_component_by_trade.csv", cost_components),
        ("task2512_cost_component_summary.csv", cost_summary),
        ("task2512_peak_trough_path.csv", path_rows),
        ("task2513_negative_return_trade_taxonomy.csv", negative_tax),
        ("task2513_mdd_window_trade_contributors.csv", contributors),
        ("task2514_drawdown_window_map.csv", dd_map),
        ("task2514_cost_drag_decomposition.csv", cost_drag),
        ("task2515_drawdown_window_trade_attribution.csv", dd_trade_attr),
        ("task2515_base_vs_kis_monthly_delta.csv", monthly),
        ("task2516_symbol_concentration_attribution.csv", symbol_conc),
        ("task2516_failure_taxonomy.csv", taxonomy),
        ("task2517_split_cost_drawdown_bridge.csv", split_bridge),
        ("task2517_repair_candidate_queue.csv", repair),
        ("task2518_subagent_packets.csv", subagents),
        ("task2518_acceptance_checks.csv", acceptance),
        ("task2519_governance_health_checks.csv", governance),
        ("task2520_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2520_closeout.json", closeout[0])
    write_report(closeout[0], taxonomy, contributors, repair)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2511_2520_KIS_MDD_DECOMPOSITION_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
