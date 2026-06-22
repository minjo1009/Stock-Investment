from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2521_2530_kis_cost_aware_guard_feasibility"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2521_2530_kis_cost_aware_guard_feasibility.md"
DECISION = REPORT_DIR / "task_2530_decision.csv"

TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK2501 = ROOT / "data/artifacts/task_2501_2510_kis_cost_basis_test"
TASK2511 = ROOT / "data/artifacts/task_2511_2520_kis_mdd_decomposition"

AUTHORITY = "DIAGNOSTIC_KIS_COST_AWARE_GUARD_FEASIBILITY_ONLY"
INITIAL_CAPITAL = 1000.0
BASE_KIS_POLICY = "kis_cost_repriced_exit_chain_repaired_soft_boost_cap_top2_v1"


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


def load_inputs() -> dict[str, list[dict[str, str]]]:
    source_rows = read_csv(TASK2381 / "task2384_repaired_exit_source_rows.csv")
    source_by_spec = {row["trade_spec_id"]: row for row in source_rows}
    trades = read_csv(TASK2501 / "task2502_kis_repriced_trades.csv")
    enriched = []
    for row in trades:
        src = source_by_spec.get(row["trade_spec_id"], {})
        enriched.append({**row, **{f"source_{k}": v for k, v in src.items()}})
    return {
        "trades": enriched,
        "baseline_equity": read_csv(TASK2501 / "task2503_kis_repriced_equity.csv"),
        "baseline_metrics": read_csv(TASK2501 / "task2504_kis_repriced_metrics.csv"),
        "mdd_closeout": read_csv(TASK2511 / "task2520_closeout.csv"),
        "mdd_contributors": read_csv(TASK2511 / "task2513_mdd_window_trade_contributors.csv"),
    }


def source_context_rows() -> list[dict[str, object]]:
    sources = [
        (
            "Research Affiliates",
            "Harnessing Volatility Targeting in Multi-Asset Portfolios",
            "2024-01",
            "Volatility targeting is primarily a stability/risk-control overlay, not a return enhancement promise.",
            "https://www.researchaffiliates.com/content/dam/ra/publications/pdf/1014-harnessing-volatility-targeting.pdf",
        ),
        (
            "Frontiers in Applied Mathematics and Statistics",
            "On transaction costs in minimum-risk portfolios",
            "2025",
            "Transaction costs should be incorporated into portfolio construction because frequent rebalancing can materially reduce net performance.",
            "https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2025.1585187/full",
        ),
        (
            "AQR",
            "Hold the Dip",
            "2025",
            "Testing many drawdown/dip variants creates data-mining risk; guard variants should be preregistered and judged conservatively.",
            "https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/AQR-Alternative-Thinking---Hold-the-Dip.pdf?sc_lang=en",
        ),
        (
            "Transaction-cost-aware Factors",
            "Transaction-cost-aware factor construction",
            "2024",
            "Gross returns can favor high-turnover or costly trades; net cost-aware decision rules are more relevant.",
            "https://afajof.org/management/viewp.php?n=135184",
        ),
    ]
    return [
        {
            "task_id": "Task2521",
            "source_context_id": f"KISGUARDSRC2521-{idx:04d}",
            "source_name": source,
            "title": title,
            "date_basis": date_basis,
            "lesson_for_guard": lesson,
            "url": url,
            "used_as_source_of_truth_for_pnl": "0",
            "used_as_design_context_only": "1",
            "authority": AUTHORITY,
        }
        for idx, (source, title, date_basis, lesson, url) in enumerate(sources, start=1)
    ]


def expert_review_rows() -> list[dict[str, object]]:
    reviews = [
        (
            "risk_parity_portfolio_construction_reviewer",
            "Drawdown control can improve ride quality, but expecting no return cost is too strong. Require non-inferior CAGR, not guaranteed improvement.",
            "Use portfolio-drawdown state and cost-adjusted edge, not symbol-specific hindsight.",
        ),
        (
            "systematic_execution_cost_reviewer",
            "The guard must separate commission drag from SEC fee and should avoid high-turnover thin-edge exposure during stress.",
            "Apply only predeclared budget multipliers; never remove losers by name.",
        ),
        (
            "overfit_governance_reviewer",
            "Because the problematic window is known, any successful variant is diagnostic until OOS/PIT gates are rerun.",
            "Report feasibility, not acceptance.",
        ),
    ]
    return [
        {
            "task_id": "Task2522",
            "expert_review_id": f"KISGUARDEXPERT2522-{idx:04d}",
            "expert_role": role,
            "feedback": feedback,
            "implementation_constraint": constraint,
            "gpt_or_expert_review_only": "1",
            "source_of_truth_for_pnl": "0",
            "authority": AUTHORITY,
        }
        for idx, (role, feedback, constraint) in enumerate(reviews, start=1)
    ]


def guard_variant_rows() -> list[dict[str, object]]:
    variants = [
        (
            "kis_guard_none_baseline_v1",
            "baseline",
            "No guard; reproduce Task2501 KIS-cost path.",
            0.0,
            1.0,
            "none",
        ),
        (
            "kis_guard_drawdown20_monthly_overtrade_cap_v1",
            "lagged_drawdown_trade_intensity_cap",
            "When prior portfolio drawdown <= -20% and same-month trade count is above 2, cap all same-cohort intents at 60%.",
            -0.20,
            0.60,
            "monthly_trade_count_over_2",
        ),
        (
            "kis_guard_drawdown20_monthly_costrate_cap_v1",
            "lagged_drawdown_monthly_cost_budget_cap",
            "When prior portfolio drawdown <= -20% and same-month KIS cost rate is above 0.55%, cap all same-cohort intents at 65%.",
            -0.20,
            0.65,
            "monthly_cost_rate_over_0p0055",
        ),
        (
            "kis_guard_drawdown20_trade_costrate_cap_v1",
            "lagged_drawdown_trade_cost_budget_cap",
            "When prior portfolio drawdown <= -20% and trade KIS cost rate is above 0.60%, cap that intent at 50%.",
            -0.20,
            0.50,
            "trade_cost_rate_over_0p0060",
        ),
        (
            "kis_guard_drawdown25_cost_intensity_cap_v1",
            "lagged_drawdown_combined_cost_intensity_cap",
            "When prior portfolio drawdown <= -25% and same-month trade count or cost rate is high, cap affected intents at 60%.",
            -0.25,
            0.60,
            "monthly_trade_count_over_2_or_monthly_cost_rate_over_0p0055",
        ),
        (
            "kis_guard_drawdown15_portfolio_stress_cap90_v1",
            "lagged_drawdown_portfolio_stress_cap",
            "When prior portfolio drawdown <= -15%, cap all same-cohort intents at 90%.",
            -0.15,
            0.90,
            "portfolio_stress_all_intents",
        ),
        (
            "kis_guard_drawdown20_portfolio_stress_cap80_v1",
            "lagged_drawdown_portfolio_stress_cap",
            "When prior portfolio drawdown <= -20%, cap all same-cohort intents at 80%.",
            -0.20,
            0.80,
            "portfolio_stress_all_intents",
        ),
        (
            "kis_guard_drawdown25_portfolio_stress_cap80_v1",
            "lagged_drawdown_portfolio_stress_cap",
            "When prior portfolio drawdown <= -25%, cap all same-cohort intents at 80%.",
            -0.25,
            0.80,
            "portfolio_stress_all_intents",
        ),
    ]
    return [
        {
            "task_id": "Task2523",
            "guard_variant_id": variant,
            "guard_family": family,
            "preregistered_rule": rule,
            "prior_drawdown_trigger": trigger,
            "budget_multiplier_when_triggered": multiplier,
            "eligible_condition": condition,
            "uses_symbol_specific_hindsight": "0",
            "uses_future_outcome_for_assignment": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
        for variant, family, rule, trigger, multiplier, condition in variants
    ]


def cost_rate(row: dict[str, str]) -> float:
    notional = f(row.get("entry_notional"))
    return f(row.get("kis_total_cost")) / notional if notional else 0.0


def month_stats(rows: list[dict[str, str]]) -> dict[str, float]:
    cost = sum(f(row.get("kis_total_cost")) for row in rows)
    notional = sum(f(row.get("entry_notional")) for row in rows)
    return {
        "monthly_trade_count": float(len(rows)),
        "monthly_kis_cost": cost,
        "monthly_entry_notional": notional,
        "monthly_cost_rate": cost / notional if notional else 0.0,
    }


def condition_pass(row: dict[str, str], stats: dict[str, float], condition: str) -> bool:
    if condition == "none":
        return False
    if condition == "monthly_trade_count_over_2":
        return stats["monthly_trade_count"] > 2
    if condition == "monthly_cost_rate_over_0p0055":
        return stats["monthly_cost_rate"] > 0.0055
    if condition == "trade_cost_rate_over_0p0060":
        return cost_rate(row) > 0.0060
    if condition == "monthly_trade_count_over_2_or_monthly_cost_rate_over_0p0055":
        return stats["monthly_trade_count"] > 2 or stats["monthly_cost_rate"] > 0.0055
    if condition == "portfolio_stress_all_intents":
        return True
    return False


def replay_variant(trades: list[dict[str, str]], variant: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    equity = INITIAL_CAPITAL
    peak = equity
    guard_rows: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in trades:
        grouped[row["decision_asof_ts"]].append(row)
    for idx, ts in enumerate(sorted(grouped, key=parse_ts), start=1):
        prior_drawdown = equity / peak - 1.0 if peak else 0.0
        period_pnl = 0.0
        allocated = 0
        stats = month_stats(grouped[ts])
        for trade in grouped[ts]:
            triggered = (
                str(variant["guard_variant_id"]) != "kis_guard_none_baseline_v1"
                and prior_drawdown <= f(variant["prior_drawdown_trigger"])
                and condition_pass(trade, stats, str(variant["eligible_condition"]))
            )
            multiplier = f(variant["budget_multiplier_when_triggered"]) if triggered else 1.0
            adjusted_pnl = f(trade.get("kis_pnl")) * multiplier
            adjusted_cost = f(trade.get("kis_total_cost")) * multiplier
            period_pnl += adjusted_pnl
            allocated += 1
            guard_rows.append(
                {
                    "task_id": "Task2524",
                    "guard_row_id": f"KISGUARDROW2524-{len(guard_rows)+1:05d}",
                    "guard_variant_id": variant["guard_variant_id"],
                    "trade_spec_id": trade.get("trade_spec_id", ""),
                    "symbol": trade.get("symbol", ""),
                    "decision_asof_ts": ts,
                    "prior_portfolio_drawdown": round(prior_drawdown, 8),
                    "guard_triggered": "1" if triggered else "0",
                    "eligible_condition": variant["eligible_condition"],
                    "budget_multiplier": multiplier,
                    "original_kis_pnl": trade.get("kis_pnl", ""),
                    "adjusted_kis_pnl": round(adjusted_pnl, 6),
                    "original_kis_cost": trade.get("kis_total_cost", ""),
                    "adjusted_kis_cost": round(adjusted_cost, 6),
                    "trade_cost_rate": round(cost_rate(trade), 8),
                    "monthly_trade_count": int(stats["monthly_trade_count"]),
                    "monthly_kis_cost": round(stats["monthly_kis_cost"], 6),
                    "monthly_entry_notional": round(stats["monthly_entry_notional"], 6),
                    "monthly_cost_rate": round(stats["monthly_cost_rate"], 8),
                    "winner_defense_bucket": trade.get("source_winner_defense_bucket", ""),
                    "runtime_action": trade.get("source_runtime_action", ""),
                    "volatility_cause": trade.get("source_volatility_cause", ""),
                    "outcome_used_for_audit_only": "1",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
        equity += period_pnl
        peak = max(peak, equity)
        equity_rows.append(
            {
                "task_id": "Task2525",
                "equity_row_id": f"KISGUARDEQ2525-{str(variant['guard_variant_id'])}-{idx:04d}",
                "guard_variant_id": variant["guard_variant_id"],
                "decision_asof_ts": ts,
                "equity": round(equity, 6),
                "period_pnl": round(period_pnl, 6),
                "portfolio_drawdown_after_period": round(equity / peak - 1.0 if peak else 0.0, 8),
                "allocated_count": allocated,
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return guard_rows, equity_rows


def metrics_for_variant(variant_id: str, equity_rows: list[dict[str, object]], guard_rows: list[dict[str, object]]) -> dict[str, object]:
    final_equity = f(equity_rows[-1]["equity"]) if equity_rows else INITIAL_CAPITAL
    start = parse_ts(str(equity_rows[0]["decision_asof_ts"])) if equity_rows else datetime(2021, 1, 1)
    end = parse_ts(str(equity_rows[-1]["decision_asof_ts"])) if equity_rows else datetime(2026, 3, 31)
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = (final_equity / INITIAL_CAPITAL) ** (1 / years) - 1.0 if final_equity > 0 else -1.0
    peak = INITIAL_CAPITAL
    mdd = 0.0
    for row in equity_rows:
        eq = f(row["equity"])
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1.0 if peak else 0.0)
    triggered = [row for row in guard_rows if row["guard_variant_id"] == variant_id and row["guard_triggered"] == "1"]
    return {
        "task_id": "Task2526",
        "guard_variant_id": variant_id,
        "final_equity": round(final_equity, 6),
        "cagr": round(cagr, 8),
        "max_drawdown": round(mdd, 8),
        "guard_triggered_rows": len(triggered),
        "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
        "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
        "noninferior_final_vs_kis_baseline": "",
        "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 else "0",
        "outcome_used_for_audit_only": "1",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }


def run_guard_tests(trades: list[dict[str, str]], variants: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    all_guard_rows: list[dict[str, object]] = []
    all_equity_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    for variant in variants:
        guard_rows, equity_rows = replay_variant(trades, variant)
        all_guard_rows.extend(guard_rows)
        all_equity_rows.extend(equity_rows)
        metric_rows.append(metrics_for_variant(str(variant["guard_variant_id"]), equity_rows, guard_rows))
    baseline_final = next(row for row in metric_rows if row["guard_variant_id"] == "kis_guard_none_baseline_v1")["final_equity"]
    for row in metric_rows:
        row["noninferior_final_vs_kis_baseline"] = "1" if f(row["final_equity"]) >= f(baseline_final) else "0"
        row["return_preserving_mdd_success"] = (
            "1"
            if row["guard_variant_id"] != "kis_guard_none_baseline_v1"
            and f(row["final_equity"]) >= f(baseline_final)
            and f(row["max_drawdown"]) >= -0.30
            else "0"
        )
    return all_guard_rows, all_equity_rows, metric_rows


def feasibility_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    baseline = next(row for row in metrics if row["guard_variant_id"] == "kis_guard_none_baseline_v1")
    for idx, row in enumerate(metrics, start=1):
        if row["guard_variant_id"] == "kis_guard_none_baseline_v1":
            verdict = "baseline_reference"
        elif row["return_preserving_mdd_success"] == "1":
            verdict = "feasible_in_diagnostic_replay"
        elif f(row["max_drawdown"]) >= -0.30:
            verdict = "mdd_fixed_but_return_reduced"
        elif f(row["final_equity"]) >= f(baseline["final_equity"]):
            verdict = "return_preserved_but_mdd_not_fixed"
        else:
            verdict = "not_feasible"
        rows.append(
            {
                "task_id": "Task2527",
                "feasibility_id": f"KISFEAS2527-{idx:04d}",
                "guard_variant_id": row["guard_variant_id"],
                "verdict": verdict,
                "final_equity_delta_vs_baseline": round(f(row["final_equity"]) - f(baseline["final_equity"]), 6),
                "mdd_delta_vs_baseline": round(f(row["max_drawdown"]) - f(baseline["max_drawdown"]), 8),
                "cagr_delta_vs_baseline": round(f(row["cagr"]) - f(baseline["cagr"]), 8),
                "guard_triggered_rows": row["guard_triggered_rows"],
                "diagnostic_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def acceptance_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    feasible = any(row.get("return_preserving_mdd_success") == "1" for row in metrics)
    checks = [
        ("preregistered_variants_only", "1", "All variants are declared before replay inside Task2523."),
        ("no_symbol_specific_hindsight", "1", "No guard condition keys on CC/AVGO/CBT or other symbol names."),
        ("return_preserving_mdd_candidate_exists", "1" if feasible else "0", "At least one non-baseline variant must preserve final equity and bring MDD inside -30%."),
        ("diagnostic_only_status_preserved", "1", "No acceptance/deployment/real-capital status changes."),
    ]
    return [
        {
            "task_id": "Task2528",
            "acceptance_check_id": f"KISGUARDACCEPT2528-{idx:04d}",
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


def closeout_rows(metrics: list[dict[str, object]], feasibility: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates = [row for row in metrics if row.get("return_preserving_mdd_success") == "1"]
    if candidates:
        best = max(candidates, key=lambda row: f(row["final_equity"]))
        verdict = "return_preserving_mdd_repair_possible_in_diagnostic_replay"
    else:
        best = max(metrics, key=lambda row: (f(row["max_drawdown"]) >= -0.30, f(row["final_equity"])))
        verdict = "return_preserving_mdd_repair_not_found_in_preregistered_variants"
    return [
        {
            "task_id": "Task2530",
            "verdict": verdict,
            "best_guard_variant_id": best["guard_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "best_guard_triggered_rows": best["guard_triggered_rows"],
            "return_preserving_mdd_success": best.get("return_preserving_mdd_success", "0"),
            "strategy_tuning_performed": "0",
            "selector_changed": "0",
            "diagnostic_only": "1",
            "next_action": "Task2531+ must run PIT/as-of and OOS guard validation before any paper candidate generation.",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], sources: list[dict[str, object]], experts: list[dict[str, object]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['guard_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, triggered {row['guard_triggered_rows']}, success {row['return_preserving_mdd_success']}."
        for row in metrics
    )
    source_lines = "\n".join(f"- {row['source_name']} ({row['date_basis']}): {row['lesson_for_guard']}" for row in sources)
    expert_lines = "\n".join(f"- `{row['expert_role']}`: {row['feedback']}" for row in experts)
    success = str(closeout["return_preserving_mdd_success"]) == "1"
    plain_conclusion = (
        "Conclusion first: yes, in this diagnostic replay it appears possible to bring MDD back inside -30% without reducing final return."
        if success
        else "Conclusion first: no return-preserving MDD repair was found among the preregistered diagnostic guards."
    )
    plain_next = (
        "The successful guard still needs PIT/as-of, OOS guard validation, and paper-mode observation before it can affect real decisions."
        if success
        else "The tested guards either did not trigger or reduced return while improving drawdown. The next repair should improve selection quality or add a true ex-ante bad-trade filter, not simply de-risk the whole book."
    )
    REPORT.write_text(
        f"""# Task2521-2530 KIS Cost-Aware Guard Feasibility

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Best guard: `{closeout['best_guard_variant_id']}`.
- Best final equity: {closeout['best_final_equity']}.
- Best CAGR: {closeout['best_cagr']}.
- Best MDD: {closeout['best_max_drawdown']}.
- Return-preserving MDD success: `{closeout['return_preserving_mdd_success']}`.
- Selector changed: `0`.
- Strategy tuning performed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Recent source context:

{source_lines}

Expert review summary:

{expert_lines}

Guard replay metrics:

{metric_lines}

This is a diagnostic feasibility test. It does not prove deployability because PIT/as-of source certification and forward paper-trading evidence are still missing.

## No-Background Decision-Maker Report

{plain_conclusion}

But this is not approval. {plain_next}

## Artifact Manifest

- Artifacts: `data/artifacts/task_2521_2530_kis_cost_aware_guard_feasibility/`.
- Validator: `python scripts/trader_brain_2521_2530_kis_cost_aware_guard_feasibility_validate.py`.

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
    for task_no in range(2521, 2531):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"KIS Cost-Aware Drawdown Guard Feasibility Step {task_no}",
                "owner_team": "Backtest & Simulation Infra / Execution & Risk / Research Governance",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "kis-cost-aware-guard-feasibility-diagnostic-only",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2521_2530_kis_cost_aware_guard_feasibility/task_2521_2530_kis_cost_aware_guard_feasibility.md",
                "key_decision": "docs/reports/task_2521_2530_kis_cost_aware_guard_feasibility/task_2530_decision.csv",
                "key_artifacts": "data/artifacts/task_2521_2530_kis_cost_aware_guard_feasibility",
                "validation_command": "python scripts/trader_brain_2521_2530_kis_cost_aware_guard_feasibility_validate.py",
                "notes": "Tests preregistered KIS-cost-aware drawdown guard variants without changing selector.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    corrected_121 = (
        "121. Task2511-Task2520 decomposed the KIS-cost MDD failure: base MDD -0.28210924, KIS MDD -0.30814728, "
        "window 2022-01-31T21:00:00+00:00 to 2022-08-31T21:00:00+00:00, window trades 14, negative trades 11, "
        "cost 61.798787; no strategy tuning was performed. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN."
    )
    lines = text.rstrip().splitlines()
    lines = [corrected_121 if line.startswith("121. Task2511-Task2520") else line for line in lines]
    line_122 = (
        "122. Task2521-Task2530 tested preregistered KIS-cost-aware drawdown guard feasibility without selector changes: "
        f"best `{closeout['best_guard_variant_id']}` final {closeout['best_final_equity']} CAGR {closeout['best_cagr']} "
        f"MDD {closeout['best_max_drawdown']}, return-preserving MDD success {closeout['return_preserving_mdd_success']}. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN."
    )
    replaced_122 = False
    next_lines = []
    for line in lines:
        if line.startswith("122. Task2521-Task2530"):
            next_lines.append(line_122)
            replaced_122 = True
        else:
            next_lines.append(line)
    if not replaced_122:
        next_lines.append(line_122)
    lines = next_lines
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    sources = source_context_rows()
    experts = expert_review_rows()
    variants = guard_variant_rows()
    guard_rows, equity_rows, metrics = run_guard_tests(inputs["trades"], variants)
    feasibility = feasibility_rows(metrics)
    acceptance = acceptance_rows(metrics)
    closeout = closeout_rows(metrics, feasibility)

    outputs = [
        ("task2521_recent_source_context.csv", sources),
        ("task2522_expert_review_feedback.csv", experts),
        ("task2523_preregistered_guard_variants.csv", variants),
        ("task2524_guard_trade_rows.csv", guard_rows),
        ("task2525_guard_equity_paths.csv", equity_rows),
        ("task2526_guard_metrics.csv", metrics),
        ("task2527_feasibility_matrix.csv", feasibility),
        ("task2528_acceptance_checks.csv", acceptance),
        ("task2530_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2530_closeout.json", closeout[0])
    write_report(closeout[0], metrics, sources, experts)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2521_2530_KIS_COST_AWARE_GUARD_FEASIBILITY_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
