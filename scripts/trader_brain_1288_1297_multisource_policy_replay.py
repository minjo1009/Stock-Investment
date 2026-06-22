from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1228 = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
TASK1268 = ROOT / "data/artifacts/task_1268_1287_source_extractors"
OUT_DIR = ROOT / "data/artifacts/task_1288_1297_multisource_policy_replay"
REPORT_DIR = ROOT / "docs/reports/task_1288_1297_multisource_policy_replay"

AUTHORITY = "DIAGNOSTIC_MULTISOURCE_POLICY_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0

POLICIES = {
    "multisource_shadow_only_slot5_v1": {
        "hard_survival_review_required": 1.00,
        "validated_growth_multisource_confirmed": 1.00,
        "revenue_validation_market_confirmed": 1.00,
        "management_narrative_market_confirmed": 1.00,
        "policy_market_confirmed_but_company_source_gap": 1.00,
        "multisource_incomplete_or_watch": 1.00,
    },
    "multisource_hard_event_only_slot5_v1": {
        "hard_survival_review_required": 0.25,
        "validated_growth_multisource_confirmed": 1.00,
        "revenue_validation_market_confirmed": 1.00,
        "management_narrative_market_confirmed": 1.00,
        "policy_market_confirmed_but_company_source_gap": 1.00,
        "multisource_incomplete_or_watch": 1.00,
    },
    "multisource_quality_haircut_slot5_v1": {
        "hard_survival_review_required": 0.50,
        "validated_growth_multisource_confirmed": 1.00,
        "revenue_validation_market_confirmed": 0.95,
        "management_narrative_market_confirmed": 0.90,
        "policy_market_confirmed_but_company_source_gap": 0.85,
        "multisource_incomplete_or_watch": 0.70,
    },
    "multisource_source_complete_slot5_v1": {
        "hard_survival_review_required": 0.25,
        "validated_growth_multisource_confirmed": 1.00,
        "revenue_validation_market_confirmed": 0.90,
        "management_narrative_market_confirmed": 0.85,
        "policy_market_confirmed_but_company_source_gap": 0.70,
        "multisource_incomplete_or_watch": 0.50,
    },
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


def cagr(start_value: float, end_value: float, start: date, end: date) -> float:
    years = (end - start).days / 365.25
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def max_drawdown(values: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def policy_catalog() -> list[dict[str, object]]:
    rows = []
    for policy_id, route_map in POLICIES.items():
        for interpretation, multiplier in route_map.items():
            rows.append(
                {
                    "task_id": "Task1288",
                    "policy_variant_id": policy_id,
                    "enhanced_composite_interpretation": interpretation,
                    "position_multiplier": multiplier,
                    "policy_intent": "shadow" if "shadow" in policy_id else "diagnostic_size_overlay",
                    "selection_promoted": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_specs() -> list[dict[str, object]]:
    base_specs = read_csv(TASK1228 / "task1233_policy_specs.csv")
    l2 = {row["selection_id"]: row for row in read_csv(TASK1268 / "task1274_enhanced_l2_multisource_interpretation.csv")}
    readiness = {row["selection_id"]: row for row in read_csv(TASK1268 / "task1276_backtest_readiness_panel.csv")}
    specs = []
    for policy_id, route_map in POLICIES.items():
        for row in sorted(base_specs, key=lambda item: (item["decision_asof_ts"], int(item["candidate_rank"]))):
            interp = l2[row["selection_id"]]["enhanced_composite_interpretation"]
            multiplier = route_map.get(interp, 1.0)
            base_multiplier = to_float(row["position_multiplier"])
            specs.append(
                {
                    "task_id": "Task1289",
                    "policy_spec_id": f"MSPOL1289-{len(specs)+1:07d}",
                    "policy_variant_id": policy_id,
                    "selection_id": row["selection_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "symbol": row["symbol"],
                    "candidate_rank": row["candidate_rank"],
                    "derived_theme": row["derived_theme"],
                    "enhanced_composite_interpretation": interp,
                    "backtest_readiness_state": readiness[row["selection_id"]]["backtest_readiness_state"],
                    "entry_date": row["entry_date"],
                    "entry_price": row["entry_price"],
                    "scheduled_exit_date": row["scheduled_exit_date"],
                    "scheduled_exit_price": row["scheduled_exit_price"],
                    "adjusted_exit_date": row["adjusted_exit_date"],
                    "adjusted_exit_price": row["adjusted_exit_price"],
                    "exit_reason": row["exit_reason"] if "shadow" in policy_id else f"multisource_size_overlay:{row['exit_reason']}",
                    "base_position_multiplier": base_multiplier,
                    "multisource_position_multiplier": multiplier,
                    "position_multiplier": round(base_multiplier * multiplier, 6),
                    "selection_promoted": "0",
                    "assignment_uses_future_outcome": "0",
                    "exit_uses_post_entry_price_path": "1",
                    "authority": AUTHORITY,
                }
            )
    return specs


def run_replay(specs: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    trades = []
    equity = []
    specs_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spec in specs:
        specs_by_policy[str(spec["policy_variant_id"])].append(spec)
    for policy_id, policy_specs in sorted(specs_by_policy.items()):
        by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
        for spec in policy_specs:
            by_decision[str(spec["decision_asof_ts"])].append(spec)
        capital = INITIAL_CAPITAL
        for decision_ts, items in sorted(by_decision.items()):
            base_slot = capital / 5.0
            invested = 0.0
            period_pnl = 0.0
            new_capital = capital
            for item in sorted(items, key=lambda row: int(str(row["candidate_rank"]))):
                allocation = base_slot * to_float(item["position_multiplier"])
                invested += allocation
                entry = to_float(item["entry_price"])
                exit_ = to_float(item["adjusted_exit_price"])
                net_return = exit_ / entry - 1.0 - ROUND_TRIP_COST_BPS / 10000.0 if allocation > 0 and entry > 0 else 0.0
                pnl = allocation * net_return
                period_pnl += pnl
                new_capital += pnl
                trades.append(
                    {
                        "task_id": "Task1290",
                        "trade_id": f"MSTRADE1290-{len(trades)+1:07d}",
                        **item,
                        "capital_allocated": round(allocation, 4),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "authority": AUTHORITY,
                    }
                )
            cash_weight = max(0.0, 1.0 - invested / capital) if capital > 0 else 0.0
            period_return = new_capital / capital - 1.0 if capital > 0 else 0.0
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1291",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_return": round(period_return, 8),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "cash_weight_after_routing": round(cash_weight, 6),
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    task1228_metric = read_csv(TASK1228 / "task1234_replay_metrics.csv")[0]
    base_metrics = read_csv(TASK1201 / "task1207_replay_metrics.csv")
    base_slot5 = next(row for row in base_metrics if row["policy_variant_id"] == "l0_l3_slot5_v1")
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = datetime.fromisoformat(str(eq_rows[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
        end = max(datetime.fromisoformat(str(row["adjusted_exit_date"])).date() for row in tr_rows)
        executed = [row for row in tr_rows if to_float(row["capital_allocated"]) > 0]
        rows.append(
            {
                "task_id": "Task1292",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr(INITIAL_CAPITAL, final, start, end), 6),
                "max_drawdown": round(max_drawdown(values), 6),
                "trade_count": len(executed),
                "task1228_final_equity": task1228_metric["final_equity"],
                "task1228_delta": round(final - float(task1228_metric["final_equity"]), 4),
                "beats_task1228": "1" if final > float(task1228_metric["final_equity"]) else "0",
                "benchmark_symbol": base_slot5["benchmark_symbol"],
                "benchmark_final_equity": base_slot5["benchmark_final_equity"],
                "beats_benchmark": "1" if final > float(base_slot5["benchmark_final_equity"]) else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def attribution(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        grouped[(str(row["policy_variant_id"]), str(row["enhanced_composite_interpretation"]))].append(row)
    rows = []
    for (policy, interp), items in sorted(grouped.items()):
        executed = [row for row in items if to_float(row["capital_allocated"]) > 0]
        rows.append(
            {
                "task_id": "Task1293",
                "policy_variant_id": policy,
                "enhanced_composite_interpretation": interp,
                "row_count": len(items),
                "executed_count": len(executed),
                "pnl": round(sum(to_float(row["pnl"]) for row in items), 4),
                "avg_net_return": round(sum(to_float(row["net_return"]) for row in executed) / len(executed), 6) if executed else 0,
                "selection_promoted": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def write_report(closeout: dict[str, object], metric_rows: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric_lines = ["| Policy | Final | CAGR | MDD | Beats Task1228 | Beats QQQ |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in metric_rows:
        metric_lines.append(f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['beats_task1228']} | {row['beats_benchmark']} |")
    report = [
        "# Task1288-1297 Multi-Source Policy Replay",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Best policy: `{closeout['best_policy_variant_id']}`.",
        f"- Best final equity: {closeout['best_final_equity']}.",
        f"- Best CAGR: {closeout['best_cagr']}.",
        f"- Best MDD: {closeout['best_max_drawdown']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "",
        "## Quant Expert Report",
        "",
        "Four diagnostic policies were replayed after attaching SEC exhibit-derived IR/CEO and contract/order extractors.",
        "",
        *metric_lines,
        "",
        "Leakage audit:",
        "",
        "- Source features come from prior-known SEC accession evidence and Task1228 decision-time features.",
        "- Assignment does not use future return, PnL, or outcome labels.",
        "- Post-entry prices are used only by the inherited L5 exit simulation.",
        "",
        "Remaining blockers:",
        "",
        "- Analyst expectation PIT source remains absent.",
        "- Full earnings-call transcript Q&A remains absent.",
        "- Contract/customer-side confirmation remains absent.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We tested whether the newly attached multi-source evidence improves the replay.",
        "",
        "This is still diagnostic and does not approve the strategy.",
        "",
        "## Artifact Manifest",
        "",
        "- `task1288_policy_catalog.csv`",
        "- `task1289_policy_specs.csv`",
        "- `task1290_replay_trades.csv`",
        "- `task1291_replay_equity.csv`",
        "- `task1292_replay_metrics.csv`",
        "- `task1293_multisource_attribution.csv`",
        "- `task1294_acceptance_gate.csv`",
        "- `task1297_closeout.csv/json`",
        "",
        "Validation commands:",
        "",
        "- `python scripts/trader_brain_1288_1297_multisource_policy_replay_validate.py`",
        "- `python -m unittest tests.test_trader_brain_1288_1297_multisource_policy_replay`",
        "",
        "```text",
        "Test results do not modify strategy acceptance status.",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "```",
    ]
    (REPORT_DIR / "task_1288_1297_multisource_policy_replay.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    catalog = policy_catalog()
    specs = build_specs()
    trades, equity = run_replay(specs)
    metric_rows = metrics(trades, equity)
    attribution_rows = attribution(trades)
    gate_rows = [
        {
            "task_id": "Task1294",
            **row,
            "target_cagr_30pct_pass": "1" if to_float(row["cagr"]) >= 0.30 else "0",
            "target_mdd_minus30pct_pass": "1" if to_float(row["max_drawdown"]) >= -0.30 else "0",
            "selection_promoted": "0",
        }
        for row in metric_rows
    ]
    best = max(metric_rows, key=lambda row: to_float(row["final_equity"]))
    closeout = {
        "task_id": "Task1297",
        "verdict": "multisource_policy_replay_executed_not_accepted",
        "policy_variants": len(POLICIES),
        "policy_spec_rows": len(specs),
        "trade_rows": len(trades),
        "equity_rows": len(equity),
        "best_policy_variant_id": best["policy_variant_id"],
        "best_final_equity": best["final_equity"],
        "best_cagr": best["cagr"],
        "best_max_drawdown": best["max_drawdown"],
        "best_beats_task1228": best["beats_task1228"],
        "best_beats_benchmark": best["beats_benchmark"],
        "replay_executed": "1",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "Review attribution and build rank replacement instead of size-only overlay if action policies underperform shadow.",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1288_policy_catalog.csv", catalog)
    write_csv(OUT_DIR / "task1289_policy_specs.csv", specs)
    write_csv(OUT_DIR / "task1290_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1291_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1292_replay_metrics.csv", metric_rows)
    write_csv(OUT_DIR / "task1293_multisource_attribution.csv", attribution_rows)
    write_csv(OUT_DIR / "task1294_acceptance_gate.csv", gate_rows)
    write_csv(OUT_DIR / "task1297_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1297_closeout.json", closeout)
    write_csv(REPORT_DIR / "task_1288_1297_decision.csv", [closeout])
    write_report(closeout, metric_rows)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
