from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task608"
REPORT_DIR = Path("docs/reports/task_608_strategy_backtest_firm_grade_review")
TASK505_DECISION = Path("docs/reports/task_505_two_year_pnl_grid/task_505_decision.csv")
TASK505_QUARTER = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_quarterly_quality.csv")
TASK505_CONCENTRATION = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_concentration_audit.csv")
TASK508_COST = Path("docs/reports/task_508_cost_stress_validation/cost_stress_quality.csv")
TASK509_DECISION = Path("docs/reports/task_509_walk_forward_oos_validation/task_509_decision.csv")
TASK509_QUALITY = Path("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_quality.csv")
TASK512_OVERFIT = Path("docs/reports/task_512_backtest_correctness_overfit_audit/overfit_risk_audit.csv")
TASK512_DECISION = Path("docs/reports/task_512_backtest_correctness_overfit_audit/task_512_decision.csv")


def build_task608_strategy_backtest_firm_grade_review(*, out_dir: Path = REPORT_DIR) -> dict[str, pd.DataFrame]:
    metrics = collect_metric_snapshot()
    gpt_notes = build_gpt_review_notes(metrics)
    backlog = build_upgrade_backlog(metrics)
    decision = build_decision(metrics)

    out_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out_dir / "strategy_backtest_metric_snapshot.csv", index=False)
    gpt_notes.to_csv(out_dir / "gpt_strategy_review_notes.csv", index=False)
    backlog.to_csv(out_dir / "firm_grade_strategy_upgrade_backlog.csv", index=False)
    decision.to_csv(out_dir / "task_608_decision.csv", index=False)
    (out_dir / "gpt_strategy_review_notes.md").write_text(render_gpt_notes(gpt_notes), encoding="utf-8")
    (out_dir / "task_608_strategy_backtest_firm_grade_review.md").write_text(
        render_report(metrics.iloc[0].to_dict(), gpt_notes, backlog, decision.iloc[0].to_dict()),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "strategy_backtest_metric_snapshot": metrics,
        "gpt_strategy_review_notes": gpt_notes,
        "firm_grade_strategy_upgrade_backlog": backlog,
        "task_608_decision": decision,
    }


def collect_metric_snapshot() -> pd.DataFrame:
    t505 = _read_one(TASK505_DECISION)
    t509 = _read_one(TASK509_DECISION)
    t512 = _read_one(TASK512_OVERFIT)
    t512_decision = _read_one(TASK512_DECISION)
    concentration = _read_one(TASK505_CONCENTRATION)
    quarter = _read(TASK505_QUARTER)
    cost = _read(TASK508_COST)
    wf = _read(TASK509_QUALITY)

    cost100 = _row_where(cost, "cost_stress_name", "roundtrip_100bp")
    cost200 = _row_where(cost, "cost_stress_name", "roundtrip_200bp")
    worst_wf = wf.sort_values("test_two_year_capital_pnl_pct").head(1) if not wf.empty else pd.DataFrame()
    weak_quarters = int(
        (
            quarter["win_rate"].astype(float).lt(0.50)
            | quarter["entry_reduce_failure_rate"].astype(float).ge(0.50)
            | quarter["avg_net_return_pct"].astype(float).lt(1.0)
        ).sum()
        if not quarter.empty
        else 0
    )
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "selected_strategy_name": t505.get("best_strategy_name", ""),
                "selected_count": _int(t505.get("selected_count")),
                "selected_avg_net_pct": _float(t505.get("selected_avg_net_pct")),
                "selected_win_rate": _float(t505.get("selected_win_rate")),
                "selected_entry_reduce_rate": _float(t505.get("selected_entry_reduce_rate")),
                "two_year_capital_pnl_pct": _float(t505.get("two_year_capital_pnl_pct")),
                "max_drawdown_pct": _float(t505.get("max_drawdown_pct")),
                "max_positions": _int(t505.get("max_positions")),
                "roundtrip_100bp_pnl_pct": _float(cost100.get("two_year_capital_pnl_pct")),
                "roundtrip_200bp_pnl_pct": _float(cost200.get("two_year_capital_pnl_pct")),
                "walk_forward_fold_count": _int(t509.get("walk_forward_fold_count")),
                "walk_forward_total_count": _int(t509.get("walk_forward_total_count")),
                "walk_forward_avg_net_pct": _float(t509.get("walk_forward_avg_net_pct")),
                "walk_forward_win_rate": _float(t509.get("walk_forward_win_rate")),
                "walk_forward_entry_reduce_rate": _float(t509.get("walk_forward_entry_reduce_rate")),
                "worst_walk_forward_quarter": worst_wf.iloc[0].get("test_quarter", "") if not worst_wf.empty else "",
                "worst_walk_forward_capital_pnl_pct": _float(
                    worst_wf.iloc[0].get("test_two_year_capital_pnl_pct") if not worst_wf.empty else None
                ),
                "avg_degradation_ratio": _float(t512.get("avg_degradation_ratio")),
                "weak_or_collapse_quarter_count": _int(t512.get("negative_or_weak_quarter_count")) or weak_quarters,
                "top_theme_share": _float(concentration.get("top_theme_share")),
                "top_symbol_share": _float(concentration.get("top_symbol_share")),
                "theme_count": _int(concentration.get("theme_count")),
                "symbol_count": _int(concentration.get("symbol_count")),
                "concentration_risk_flag": _int(concentration.get("concentration_risk_flag")),
                "overfit_risk_level": t512.get("overfit_risk_level", ""),
                "firm_grade_pass_flag": _int(t512_decision.get("firm_grade_pass_flag")),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "gpt_review_role": "REVIEW_NOT_SOURCE_OF_TRUTH",
            }
        ]
    )


def build_gpt_review_notes(metrics: pd.DataFrame) -> pd.DataFrame:
    row = metrics.iloc[0].to_dict()
    return pd.DataFrame(
        [
            {
                "priority": "P0",
                "finding": "research_candidate_not_deployment_candidate",
                "review_note": "GPT review classified the strategy as a research candidate with possible signal, but the selected rulebook is materially over-optimized for the current sample.",
                "repo_evidence": f"avg_degradation_ratio={row['avg_degradation_ratio']}; overfit_risk_level={row['overfit_risk_level']}",
            },
            {
                "priority": "P0",
                "finding": "theme_dependency_must_be_tested",
                "review_note": "Run leave-one-theme-out because only four themes are active and top_theme_share is high.",
                "repo_evidence": f"top_theme_share={row['top_theme_share']}; theme_count={row['theme_count']}",
            },
            {
                "priority": "P0",
                "finding": "symbol_dependency_must_be_tested",
                "review_note": "Run leave-top-symbols-out to prove this is not a small set of lucky names.",
                "repo_evidence": f"top_symbol_share={row['top_symbol_share']}; symbol_count={row['symbol_count']}",
            },
            {
                "priority": "P0",
                "finding": "parameter_neighborhood_stability_required",
                "review_note": "A single best grid cell is not enough. Neighboring cells must mostly remain positive OOS.",
                "repo_evidence": f"selected_strategy={row['selected_strategy_name']}",
            },
            {
                "priority": "P1",
                "finding": "entry_reduce_failure_is_too_high",
                "review_note": "Entry-reduce failure around the selected and walk-forward samples is high enough to require attribution before any refinement claim.",
                "repo_evidence": f"selected_entry_reduce={row['selected_entry_reduce_rate']}; walk_forward_entry_reduce={row['walk_forward_entry_reduce_rate']}",
            },
            {
                "priority": "P1",
                "finding": "regime_failure_map_required",
                "review_note": "Failing folds should be mapped as failure environments, not used to invent new hindsight rules.",
                "repo_evidence": f"worst_fold={row['worst_walk_forward_quarter']}; worst_capital_pnl={row['worst_walk_forward_capital_pnl_pct']}",
            },
        ]
    )


def build_upgrade_backlog(metrics: pd.DataFrame) -> pd.DataFrame:
    row = metrics.iloc[0].to_dict()
    return pd.DataFrame(
        [
            _task("Task608A", "P0", "Theme Dependency Audit", "Regime Research", "Backtest & Simulation Infra", "leave-one-theme-out across selected rulebook themes", "all leave-one-theme-out OOS runs positive and worst degradation < 40%", "any theme removal makes OOS expectancy negative", row),
            _task("Task608B", "P0", "Symbol Dependency Audit", "Intraday Continuation Research", "Backtest & Simulation Infra", "leave-top1 top3 top5 symbols out of the selected strategy", "OOS avg return remains > 50% of baseline and max drawdown does not worsen materially", "top symbols removal collapses OOS return below costs", row),
            _task("Task608C", "P0", "Parameter Neighborhood Stability", "Backtest & Simulation Infra", "Research Governance", "evaluate neighboring Task505 cells around avg12 win55 er45 pos10", ">= 70% neighboring cells positive OOS and degradation < 50%", "selected rule is an isolated parameter spike", row),
            _task("Task608D", "P1", "Regime Failure Map", "Regime Research", "Backtest & Simulation Infra", "explain 2025Q1 2026Q1 2026Q2 weak folds using pre-existing regime fields", "failure regimes are identifiable without new labels or hindsight assignment", "weak folds have no coherent repeatable environment", row),
            _task("Task608E", "P1", "Entry Reduce Attribution", "Intraday Continuation Research", "Research Governance", "separate clean-entry and entry-reduce-failure cohorts", "alpha primarily comes from clean entries and entry_reduce_failure falls below 30%", "alpha is dominated by failed-entry cohort", row),
            _task("Task608F", "P1", "Ensemble Rulebook Validation", "Backtest & Simulation Infra", "Regime Research", "replace single best cell with neighboring-cell ensemble vote", "OOS degradation < 50%, weak/collapse quarters <= 1, concentration_risk_flag = 0", "ensemble does not improve stability versus selected single cell", row),
        ]
    )


def build_decision(metrics: pd.DataFrame) -> pd.DataFrame:
    row = metrics.iloc[0].to_dict()
    pass_flag = int(
        row["firm_grade_pass_flag"] == 1
        and row["avg_degradation_ratio"] < 0.50
        and row["concentration_risk_flag"] == 0
        and row["walk_forward_entry_reduce_rate"] <= 0.30
    )
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "RESEARCH_CANDIDATE_NOT_FIRM_GRADE" if not pass_flag else "FIRM_GRADE_REVIEW_CANDIDATE",
                "firm_grade_pass_flag": pass_flag,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_action": "Run Task608A Theme Dependency Audit and Task608B Symbol Dependency Audit before any new alpha experiment.",
            }
        ]
    )


def render_gpt_notes(notes: pd.DataFrame) -> str:
    lines = [
        "# GPT Strategy Review Notes",
        "",
        "These are external review notes only. They are not source-of-truth and do not change strategy acceptance.",
        "",
    ]
    for item in notes.to_dict(orient="records"):
        lines.extend(
            [
                f"## {item['priority']} - {item['finding']}",
                "",
                f"- Review note: {item['review_note']}",
                f"- Repo evidence: {item['repo_evidence']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_report(metrics: dict[str, Any], notes: pd.DataFrame, backlog: pd.DataFrame, decision: dict[str, Any]) -> str:
    backlog_lines = [
        f"- {row['priority']} {row['proposed_task_id']}: {row['title']} - pass: {row['pass_criteria']}"
        for row in backlog.to_dict(orient="records")
    ]
    note_lines = [
        f"- {row['priority']} {row['finding']}: {row['review_note']}"
        for row in notes.to_dict(orient="records")
    ]
    return "\n".join(
        [
            "# Task608 Strategy Backtest Firm-Grade Review",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {decision['decision']}",
            f"- Strategy acceptance status: {decision['strategy_acceptance_status']}",
            f"- Two-year PnL: {metrics['two_year_capital_pnl_pct']:.2f}%",
            f"- Walk-forward avg net: {metrics['walk_forward_avg_net_pct']:.2f}%",
            f"- OOS degradation: {metrics['avg_degradation_ratio']:.3f}",
            f"- Concentration risk flag: {metrics['concentration_risk_flag']}",
            f"- What changed: Task505/508/509/512 were rerun and GPT review notes were converted into repo-native diagnostics/backlog.",
            f"- Next action: {decision['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            f"- Data source and source readiness: uses existing Task503/505/508/509/512 artifacts; GPT is review-only and not a data source.",
            "- Exact join keys: inherited from Task503/505 lifecycle rows; inferred lifecycle matching remains 0.",
            "- Leakage audit: label/outcome fields are not allowed in assignment. New backlog items are diagnostics or robustness controls, not new alpha labels.",
            f"- Split/OOS metrics: walk-forward folds={metrics['walk_forward_fold_count']}, trades={metrics['walk_forward_total_count']}, avg={metrics['walk_forward_avg_net_pct']:.2f}%, win={metrics['walk_forward_win_rate']:.2%}, entry_reduce={metrics['walk_forward_entry_reduce_rate']:.2%}.",
            f"- Failure decomposition: worst walk-forward fold={metrics['worst_walk_forward_quarter']} at {metrics['worst_walk_forward_capital_pnl_pct']:.2f}% capital PnL; weak/collapse quarters={metrics['weak_or_collapse_quarter_count']}.",
            f"- Cost/slippage stress: 100bp={metrics['roundtrip_100bp_pnl_pct']:.2f}%, 200bp={metrics['roundtrip_200bp_pnl_pct']:.2f}%; cost is not the main current blocker.",
            "- Remaining blockers: concentration, OOS degradation, entry-reduce failure, weak-fold map, and parameter-neighborhood stability.",
            "",
            "### GPT Review Notes",
            "",
            *note_lines,
            "",
            "### Repo-Native Backlog",
            "",
            *backlog_lines,
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: the backtest still looks interesting, but the professional review says it is not sturdy enough yet.",
            "- Why it matters: big headline PnL is less important than whether it survives OOS, theme removal, symbol removal, and nearby parameter tests.",
            "- Whether this changes capital/deployment readiness: no. Strategy remains NOT_ACCEPTED and deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
            "- Plain-language next step: prove the edge is not coming from one theme, a few symbols, or one lucky parameter cell.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def _task(
    task_id: str,
    priority: str,
    title: str,
    owner: str,
    reviewer: str,
    objective: str,
    pass_criteria: str,
    fail_criteria: str,
    metrics: dict[str, Any],
) -> dict[str, object]:
    return {
        "priority": priority,
        "proposed_task_id": task_id,
        "title": title,
        "owner_team": owner,
        "reviewer_team": reviewer,
        "objective": objective,
        "input_baseline": metrics.get("selected_strategy_name", ""),
        "pass_criteria": pass_criteria,
        "fail_criteria": fail_criteria,
        "status": "accepted_to_backlog",
    }


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _read_one(path: Path) -> dict[str, Any]:
    frame = _read(path)
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _row_where(frame: pd.DataFrame, column: str, value: str) -> dict[str, Any]:
    if frame.empty or column not in frame.columns:
        return {}
    matched = frame[frame[column].astype(str).eq(value)]
    return matched.iloc[0].to_dict() if not matched.empty else {}


def _float(value: object) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _int(value: object) -> int:
    try:
        if value is None or pd.isna(value):
            return 0
        return int(float(value))
    except Exception:
        return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608_strategy_backtest_firm_grade_review(out_dir=args.out_dir)
    row = artifacts["task_608_decision"].iloc[0]
    metrics = artifacts["strategy_backtest_metric_snapshot"].iloc[0]
    print(
        "[TASK608] "
        f"decision={row['decision']} pnl={float(metrics['two_year_capital_pnl_pct']):.2f}% "
        f"wf_avg={float(metrics['walk_forward_avg_net_pct']):.2f}% "
        f"degradation={float(metrics['avg_degradation_ratio']):.3f}"
    )


if __name__ == "__main__":
    main()
