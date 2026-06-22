from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1878 = ROOT / "data/artifacts/task_1878_1885_desk_specific_policy_replay"
TASK1896 = ROOT / "data/artifacts/task_1896_1900_watch_subtype_calibration"
OUT_DIR = ROOT / "data/artifacts/task_1901_1910_watch_recovery_replay"
REPORT_DIR = ROOT / "docs/reports/task_1901_1910_watch_recovery_replay"
REPORT = REPORT_DIR / "task_1901_1910_watch_recovery_replay.md"
DECISION = REPORT_DIR / "task_1901_1910_decision.csv"

AUTHORITY = "DIAGNOSTIC_WATCH_RECOVERY_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "watch_recovery_top3_v1": {
        "source_policy": "winner_defense_budget_top3_v1",
        "baseline_policy": "sleeve_split_top3_v1",
        "desk_policy": "desk_specific_top3_v1",
        "slot_cap": 3,
    },
    "watch_recovery_top5_v1": {
        "source_policy": "winner_defense_budget_top5_v1",
        "baseline_policy": "sleeve_split_top5_v1",
        "desk_policy": "desk_specific_top5_v1",
        "slot_cap": 5,
    },
}

RECOVERY_SUBTYPES = {"normal_winner_volatility_watch", "upgrade_candidate_watch"}


def read_csv(path: Path) -> list[dict[str, str]]:
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def parse_date(value: object) -> date | None:
    if value in {"", None}:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def source_trade_map() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv")
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in rows}


def subtype_map() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(TASK1896 / "task1896_watch_subtype_panel.csv")
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in rows}


def input_manifest_rows() -> list[dict[str, object]]:
    inputs = [
        ("desk_specific_budget", TASK1878 / "task1884_l5_desk_specific_budget.csv"),
        ("watch_subtype_panel", TASK1896 / "task1896_watch_subtype_panel.csv"),
        ("hold_calibration_contract", TASK1896 / "task1900_hold_calibration_contract.csv"),
        ("source_winner_defense_trades", TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        ("desk_specific_metrics", TASK1878 / "task1885_desk_replay_metrics.csv"),
    ]
    return [
        {
            "task_id": "Task1901",
            "input_manifest_id": f"WATCHREPLAYINPUT-1901-{idx:03d}",
            "input_name": name,
            "input_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "exists": "1" if path.exists() else "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, path) in enumerate(inputs, 1)
    ]


def recovery_multiplier(base_multiplier: float, desk_multiplier: float, subtype: str) -> tuple[str, float, str]:
    if subtype == "upgrade_candidate_watch":
        return "restore_full_hold", clamp(max(base_multiplier, 1.05), 0.0, 1.18), "upgrade_candidate_watch_full_hold_restore"
    if subtype == "normal_winner_volatility_watch":
        return "near_full_hold", clamp(max(desk_multiplier, min(base_multiplier, 1.0)), 0.0, 1.08), "normal_winner_volatility_near_full_hold"
    return "unchanged", desk_multiplier, "not_recovery_eligible"


def build_budget_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_budget = read_csv(TASK1878 / "task1884_l5_desk_specific_budget.csv")
    subtypes = subtype_map()
    rows: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []
    idx = 1
    for row in source_budget:
        desk_policy = "desk_specific_top3_v1" if row["target_policy_variant_id"].endswith("top3_v1") else "desk_specific_top5_v1"
        subtype = subtypes.get((desk_policy, row["trade_spec_id"]), {})
        watch_subtype = subtype.get("watch_subtype", "")
        base_mult = to_float(row["base_sleeve_budget_multiplier"])
        desk_mult = to_float(row["desk_budget_multiplier"])
        recovery_action, final_mult, reason = recovery_multiplier(base_mult, desk_mult, watch_subtype)
        if watch_subtype not in RECOVERY_SUBTYPES:
            final_mult = desk_mult
        rows.append(
            {
                "task_id": "Task1904",
                "watch_recovery_budget_id": f"WATCHRECOVBUDGET-1904-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "previous_desk_action": row["desk_action"],
                "watch_subtype": watch_subtype,
                "recovery_action": recovery_action,
                "recovery_reason": reason,
                "base_sleeve_budget_multiplier": row["base_sleeve_budget_multiplier"],
                "previous_desk_budget_multiplier": row["desk_budget_multiplier"],
                "watch_recovery_budget_multiplier": round(final_mult, 6),
                "desk_thesis_state": row["desk_thesis_state"],
                "financing_specificity_state": row["financing_specificity_state"],
                "theme_breadth_state": row["theme_breadth_state"],
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        if watch_subtype:
            audit_rows.append(
                {
                    "task_id": "Task1903",
                    "recovery_candidate_audit_id": f"WATCHRECOVAUDIT-1903-{len(audit_rows)+1:05d}",
                    "target_policy_variant_id": row["target_policy_variant_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "watch_subtype": watch_subtype,
                    "eligible_for_recovery": "1" if watch_subtype in RECOVERY_SUBTYPES else "0",
                    "recovery_action": recovery_action,
                    "previous_desk_budget_multiplier": row["desk_budget_multiplier"],
                    "watch_recovery_budget_multiplier": round(final_mult, 6),
                    "multiplier_delta": round(final_mult - desk_mult, 6),
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
        idx += 1
    return rows, audit_rows


def replay_budget(budget_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_trades = source_trade_map()
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in budget_rows:
        grouped[(str(row["target_policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    trade_idx = 1
    for policy_id, config in POLICIES.items():
        source_policy = str(config["source_policy"])
        capital = INITIAL_CAPITAL
        decisions = sorted({key[1] for key in grouped if key[0] == source_policy})
        for decision_ts in decisions:
            rows = sorted(
                grouped[(source_policy, decision_ts)],
                key=lambda item: to_float(item["watch_recovery_budget_multiplier"]),
                reverse=True,
            )
            base_alloc = capital / int(config["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            subtype_counts: Counter[str] = Counter()
            for row in rows:
                source = source_trades.get((source_policy, str(row["trade_spec_id"])))
                if not source:
                    continue
                mult = to_float(row["watch_recovery_budget_multiplier"])
                if mult <= 0.0:
                    continue
                allocated = base_alloc * mult
                pnl = allocated * to_float(source.get("net_return"))
                capital += pnl
                period_pnl += pnl
                allocated_count += 1
                subtype_counts[str(row["watch_subtype"] or "not_watch")] += 1
                trades.append(
                    {
                        "task_id": "Task1905",
                        "trade_row_id": f"WATCHRECOVTRADE-1905-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": row["trade_spec_id"],
                        "candidate_source_id": row["candidate_source_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "strategy_sleeve": row["strategy_sleeve"],
                        "previous_desk_action": row["previous_desk_action"],
                        "watch_subtype": row["watch_subtype"],
                        "recovery_action": row["recovery_action"],
                        "watch_recovery_budget_multiplier": mult,
                        "financing_specificity_state": row["financing_specificity_state"],
                        "theme_breadth_state": row["theme_breadth_state"],
                        "source_net_return": source.get("net_return", ""),
                        "capital_allocated": round(allocated, 4),
                        "pnl": round(pnl, 4),
                        "net_return": source.get("net_return", ""),
                        "entry_date": source.get("entry_date", ""),
                        "actual_exit_date": source.get("actual_exit_date", ""),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task1905",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(rows),
                    "allocated_count": allocated_count,
                    "normal_winner_volatility_watch_count": subtype_counts["normal_winner_volatility_watch"],
                    "upgrade_candidate_watch_count": subtype_counts["upgrade_candidate_watch"],
                    "damage_watch_count": subtype_counts["damage_watch"],
                    "not_watch_count": subtype_counts["not_watch"],
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def metric_rows(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    baseline = {row["policy_variant_id"]: row for row in read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv")}
    desk = {row["policy_variant_id"]: row for row in read_csv(TASK1878 / "task1885_desk_replay_metrics.csv")}
    trade_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trade_groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_groups[str(row["policy_variant_id"])].append(row)
    out = []
    for policy_id, eq_rows in sorted(equity_groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        tr_rows = trade_groups[policy_id]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end_dates = [parse_date(row.get("actual_exit_date")) for row in tr_rows]
        end = max([item for item in end_dates if item is not None] or [start])
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        base_id = str(POLICIES[policy_id]["baseline_policy"])
        desk_id = str(POLICIES[policy_id]["desk_policy"])
        base = baseline[base_id]
        prev = desk[desk_id]
        out.append(
            {
                "task_id": "Task1906",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": base_id,
                "desk_policy_variant_id": desk_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "baseline_final_equity": base["final_equity"],
                "baseline_cagr": base["cagr"],
                "baseline_max_drawdown": base["max_drawdown"],
                "desk_final_equity": prev["final_equity"],
                "desk_cagr": prev["cagr"],
                "desk_max_drawdown": prev["max_drawdown"],
                "delta_vs_baseline_final": round(final - to_float(base["final_equity"]), 4),
                "delta_vs_baseline_cagr": round(cagr - to_float(base["cagr"]), 6),
                "delta_vs_baseline_mdd": round(mdd - to_float(base["max_drawdown"]), 6),
                "delta_vs_desk_final": round(final - to_float(prev["final_equity"]), 4),
                "delta_vs_desk_cagr": round(cagr - to_float(prev["cagr"]), 6),
                "delta_vs_desk_mdd": round(mdd - to_float(prev["max_drawdown"]), 6),
                "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
                "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return out


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        parsed = replay.parse_ts(str(row["decision_asof_ts"]))
        window = "IS_2021_2023" if parsed and parsed.year <= 2023 else "OOS_2024_2026Q1"
        groups[(str(row["policy_variant_id"]), window)].append(row)
    rows = []
    for (policy_id, window), items in sorted(groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1906",
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


def cost_stress_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for metric in metrics:
        trades = int(metric["trade_count"])
        for bps in [0, 25, 50, 100]:
            haircut = trades * (bps / 10000.0) * 0.35
            stressed_final = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
            rows.append(
                {
                    "task_id": "Task1907",
                    "cost_stress_id": f"WATCHRECOVCOST-1907-{idx:04d}",
                    "policy_variant_id": metric["policy_variant_id"],
                    "round_trip_cost_bps": bps,
                    "approx_trade_count": trades,
                    "stressed_final_equity": round(stressed_final, 4),
                    "beats_qqq_after_stress": "1" if stressed_final > QQQ_BENCHMARK_FINAL else "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def attribution_rows(trades: list[dict[str, object]], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for label in ["strategy_sleeve", "watch_subtype", "recovery_action", "financing_specificity_state"]:
        grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            grouped[(str(trade["policy_variant_id"]), str(trade[label] or "not_applicable"))].append(trade)
        for (policy, bucket), items in sorted(grouped.items()):
            rows.append(
                {
                    "task_id": "Task1908",
                    "attribution_id": f"WATCHRECOVATTR-1908-{idx:05d}",
                    "policy_variant_id": policy,
                    "failure_area": label,
                    "bucket": bucket,
                    "trade_count": len(items),
                    "pnl_sum_audit_only": round(sum(to_float(item["pnl"]) for item in items), 4),
                    "negative_trade_count_audit_only": sum(1 for item in items if to_float(item["pnl"]) < 0),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    for metric in metrics:
        rows.append(
            {
                "task_id": "Task1908",
                "attribution_id": f"WATCHRECOVATTR-1908-{idx:05d}",
                "policy_variant_id": metric["policy_variant_id"],
                "failure_area": "policy_metric",
                "bucket": metric["policy_variant_id"],
                "trade_count": metric["trade_count"],
                "pnl_sum_audit_only": round(to_float(metric["final_equity"]) - INITIAL_CAPITAL, 4),
                "negative_trade_count_audit_only": "",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def config_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1902",
            "policy_config_id": f"WATCHRECOVPOLICY-1902-{idx:03d}",
            "policy_variant_id": policy,
            "source_policy_variant_id": cfg["source_policy"],
            "slot_cap": cfg["slot_cap"],
            "policy_freeze_state": "frozen_before_replay",
            "recovery_subtypes": "|".join(sorted(RECOVERY_SUBTYPES)),
            "non_recovery_subtypes": "damage_watch|information_gap_watch|overhang_watch",
            "forbidden_fields": "future_price/future_return/pnl/drawdown/outcome_label",
            "authority": AUTHORITY,
        }
        for idx, (policy, cfg) in enumerate(POLICIES.items(), 1)
    ]


def gate_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    verdict = "watch_recovery_replay_complete_target_not_met"
    if best["joint_target_met"] == "1":
        verdict = "watch_recovery_replay_complete_target_met_diagnostic_only"
    gate = [
        {
            "task_id": "Task1909",
            "gate_decision": "diagnostic_replay_complete_not_accepted",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "joint_target_met": best["joint_target_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1910",
            "verdict": verdict,
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit whether recovery candidates improved CAGR without unacceptable MDD before expanding beyond 36 rows",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], split: list[dict[str, object]], cost: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1901-1910 Watch Recovery Replay",
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
        "Replay contract:",
        "",
        "- Only `normal_winner_volatility_watch` and `upgrade_candidate_watch` are restored to full or near-full hold.",
        "- `damage_watch`, `information_gap_watch`, and `overhang_watch` remain unchanged from Task1878-1885.",
        "- Replay uses prior controlled winner-defense trade returns only; no new price matching.",
        "- PnL, drawdown, and return fields are audit-only.",
        "",
        "| Policy | Final | CAGR | MDD | Desk Final | Delta vs Desk | Base Final | Delta vs Base | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['desk_final_equity']} | {row['delta_vs_desk_final']} | {row['baseline_final_equity']} | {row['delta_vs_baseline_final']} | {row['trade_count']} | {row['joint_target_met']} |"
        )
    lines.extend(["", "Split/OOS metrics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Cost/slippage stress:", "", "| Policy | Cost bps | Stressed Final | Beats QQQ |", "| --- | ---: | ---: | ---: |"])
    for row in cost:
        lines.append(f"| `{row['policy_variant_id']}` | {row['round_trip_cost_bps']} | {row['stressed_final_equity']} | {row['beats_qqq_after_stress']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. We tested only the 36 good-watch candidates.",
            "2. Damage-watch names stayed defensive.",
            "3. This is still diagnostic, not live approval.",
            "4. If CAGR improves but MDD explodes, the recovery rule is not good enough.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1901_input_manifest.csv`",
            "- `task1902_frozen_policy_config.csv`",
            "- `task1903_recovery_candidate_audit.csv`",
            "- `task1904_watch_recovery_budget.csv`",
            "- `task1905_watch_recovery_replay_trades.csv/equity`",
            "- `task1906_watch_recovery_metrics.csv/split_oos`",
            "- `task1907_cost_stress_metrics.csv`",
            "- `task1908_failure_attribution.csv`",
            "- `task1909_acceptance_gate.csv`",
            "- `task1910_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1901_1910_watch_recovery_replay_validate.py`",
            "- `python scripts/task_registry_validate.py`",
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
    budget, audit = build_budget_rows()
    trades, equity = replay_budget(budget)
    metrics = metric_rows(trades, equity)
    split = split_rows(equity)
    cost = cost_stress_rows(metrics)
    attr = attribution_rows(trades, metrics)
    gate, closeout = gate_closeout(metrics)
    outputs = [
        ("task1901_input_manifest.csv", input_manifest_rows()),
        ("task1902_frozen_policy_config.csv", config_rows()),
        ("task1903_recovery_candidate_audit.csv", audit),
        ("task1904_watch_recovery_budget.csv", budget),
        ("task1905_watch_recovery_replay_trades.csv", trades),
        ("task1905_watch_recovery_replay_equity.csv", equity),
        ("task1906_watch_recovery_metrics.csv", metrics),
        ("task1906_split_oos_metrics.csv", split),
        ("task1907_cost_stress_metrics.csv", cost),
        ("task1908_failure_attribution.csv", attr),
        ("task1909_acceptance_gate.csv", gate),
        ("task1910_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1910_closeout.json", closeout[0])
    write_report(metrics, split, cost, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1901_1910] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
