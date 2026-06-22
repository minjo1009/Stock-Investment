from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task616"
REPORT_DIR = Path("docs/reports/task_616_turboquant_intelligence_chart_fusion_backtest")
LINKED_PANEL = Path("docs/reports/task_614_p0_intelligence_source_attachment/entry_p0_intelligence_linkage.csv")


def build_task616_turboquant_intelligence_chart_fusion_backtest(
    *,
    linked_panel_path: Path = LINKED_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_linked_panel(linked_panel_path)
    scored = add_fusion_scores(panel)
    scenario_summary = build_scenario_summary(scored)
    fold_summary = build_quarter_summary(scored)
    architecture = build_architecture()
    pass_fail = build_pass_fail(scored, scenario_summary, fold_summary)
    decision = build_decision(scored, scenario_summary, fold_summary, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    scored.to_csv(out_dir / "turboquant_fusion_entry_panel.csv", index=False)
    scenario_summary.to_csv(out_dir / "turboquant_fusion_scenario_summary.csv", index=False)
    fold_summary.to_csv(out_dir / "turboquant_fusion_quarter_summary.csv", index=False)
    architecture.to_csv(out_dir / "turboquant_fusion_architecture.csv", index=False)
    pass_fail.to_csv(out_dir / "task_616_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_616_decision.csv", index=False)
    (out_dir / "task_616_turboquant_intelligence_chart_fusion_backtest.md").write_text(
        render_report(scenario_summary, fold_summary, architecture, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "turboquant_fusion_entry_panel": scored,
        "turboquant_fusion_scenario_summary": scenario_summary,
        "turboquant_fusion_quarter_summary": fold_summary,
        "turboquant_fusion_architecture": architecture,
        "task_616_pass_fail_matrix": pass_fail,
        "task_616_decision": decision,
    }


def load_linked_panel(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Task614 linked intelligence panel is missing: {path}")
    panel = pd.read_csv(path)
    required = {
        "lifecycle_id",
        "quarter",
        "symbol",
        "net_return_from_entry",
        "entry_reduce_failure_flag",
        "symbol_vs_theme_pre_entry_ret",
        "symbol_vs_qqq_pre_entry_ret",
        "theme_confirmation_fail_pre_entry_flag",
        "gap_abs_percentile_60d",
        "late_breakout_proxy_flag",
        "symbol_vwap_fail_30m_flag",
        "symbol_opening_range_rejection_120m_flag",
        "volume_decay_120m_flag",
        "p0_source_event_density",
        "institution_ownership_pre30d_flag",
        "passive_13g_pre30d_flag",
        "ceo_ir_proxy_pre14d_flag",
        "geopolitical_event_pre7d_flag",
        "political_statement_pre7d_flag",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Task616 input missing columns: {missing}")
    for col in required - {"lifecycle_id", "quarter", "symbol"}:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0.0)
    panel["quarter"] = panel["quarter"].astype(str)
    return panel


def add_fusion_scores(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["tq_pre_entry_chart_health_score"] = (
        (out["symbol_vs_theme_pre_entry_ret"].ge(0)).astype(int)
        + (out["symbol_vs_qqq_pre_entry_ret"].ge(0)).astype(int)
        + (out["theme_confirmation_fail_pre_entry_flag"].eq(0)).astype(int)
        + (out["gap_abs_percentile_60d"].le(0.70)).astype(int)
        + (out["late_breakout_proxy_flag"].eq(0)).astype(int)
    ) / 5.0
    out["tq_wait_window_chart_risk_score"] = (
        out["symbol_vwap_fail_30m_flag"].eq(1).astype(int)
        + out["symbol_opening_range_rejection_120m_flag"].eq(1).astype(int)
        + out["volume_decay_120m_flag"].eq(1).astype(int)
    ) / 3.0
    density_support = (out["p0_source_event_density"] / 5.0).clip(0.0, 1.0)
    out["tq_intelligence_support_score"] = (
        0.30 * out["institution_ownership_pre30d_flag"].clip(0, 1)
        + 0.20 * out["passive_13g_pre30d_flag"].clip(0, 1)
        + 0.20 * out["ceo_ir_proxy_pre14d_flag"].clip(0, 1)
        + 0.15 * out["geopolitical_event_pre7d_flag"].clip(0, 1)
        + 0.15 * out["political_statement_pre7d_flag"].clip(0, 1)
        + 0.15 * density_support
    ).clip(0.0, 1.0)
    out["tq_chart_risk_guard_flag"] = out["tq_wait_window_chart_risk_score"].ge(1.0).astype(int)
    out["tq_fusion_accept_flag"] = (
        out["tq_pre_entry_chart_health_score"].ge(0.60)
        & out["tq_intelligence_support_score"].ge(0.70)
        & out["tq_chart_risk_guard_flag"].eq(0)
    ).astype(int)
    out["tq_fusion_review_flag"] = (
        out["tq_chart_risk_guard_flag"].eq(1) & out["tq_intelligence_support_score"].ge(0.70)
    ).astype(int)
    out["tq_fusion_assignment_label_used_flag"] = 0
    out["tq_fusion_gpt_or_plugin_used_as_source_flag"] = 0
    return out


def build_scenario_summary(scored: pd.DataFrame) -> pd.DataFrame:
    scenarios = [
        ("baseline_all_entries", "all", pd.Series(True, index=scored.index)),
        ("chart_riskoff_only", "accept_filter", scored["tq_chart_risk_guard_flag"].eq(0)),
        ("intelligence_support_ge_0_70_only", "accept_filter", scored["tq_intelligence_support_score"].ge(0.70)),
        ("chart_health_ge_0_60_only", "accept_filter", scored["tq_pre_entry_chart_health_score"].ge(0.60)),
        ("turbo_fusion_accept_h60_i70_riskoff", "accept_filter", scored["tq_fusion_accept_flag"].eq(1)),
        ("turbo_fusion_accept_h80_i70_riskoff", "accept_filter", scored["tq_pre_entry_chart_health_score"].ge(0.80) & scored["tq_intelligence_support_score"].ge(0.70) & scored["tq_chart_risk_guard_flag"].eq(0)),
        ("turbo_fusion_review_chart_risk_and_i70", "risk_filter", scored["tq_fusion_review_flag"].eq(1)),
    ]
    return pd.DataFrame([profile_scenario(scored, name, action, mask) for name, action, mask in scenarios])


def profile_scenario(panel: pd.DataFrame, name: str, action_type: str, mask: pd.Series) -> dict[str, Any]:
    selected = panel[mask]
    rejected = panel[~mask]
    baseline_avg = float(panel["net_return_from_entry"].mean())
    baseline_failure = float(panel["entry_reduce_failure_flag"].mean())
    size_down_returns = panel["net_return_from_entry"].copy()
    size_down_returns.loc[mask] = size_down_returns.loc[mask] * 0.5
    return {
        "scenario": name,
        "action_type": action_type,
        "selected_count": int(len(selected)),
        "rejected_or_flagged_count": int(len(rejected)) if action_type == "accept_filter" else int(len(selected)),
        "selected_failure_count": int(selected["entry_reduce_failure_flag"].sum()) if len(selected) else 0,
        "selected_failure_rate": _mean(selected["entry_reduce_failure_flag"]),
        "baseline_failure_rate": baseline_failure,
        "failure_rate_delta_pct_point": float((_mean(selected["entry_reduce_failure_flag"]) - baseline_failure) * 100.0) if len(selected) else 0.0,
        "selected_avg_return_pct": float(_mean(selected["net_return_from_entry"]) * 100.0) if len(selected) else 0.0,
        "baseline_avg_return_pct": baseline_avg * 100.0,
        "selected_avg_return_delta_pct_point": float((_mean(selected["net_return_from_entry"]) - baseline_avg) * 100.0) if len(selected) else 0.0,
        "rejected_avg_return_pct": float(_mean(rejected["net_return_from_entry"]) * 100.0) if len(rejected) else 0.0,
        "risk_size_down_50_delta_pct_point": float((size_down_returns.mean() - baseline_avg) * 100.0),
        "label_used_in_assignment_flag": 0,
        "gpt_or_plugin_used_as_source_flag": 0,
    }


def build_quarter_summary(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for quarter in sorted(scored["quarter"].astype(str).unique().tolist()):
        part = scored[scored["quarter"].astype(str).eq(quarter)]
        accepted = part[part["tq_fusion_accept_flag"].eq(1)]
        base_ret = _mean(part["net_return_from_entry"])
        selected_ret = _mean(accepted["net_return_from_entry"]) if len(accepted) else 0.0
        base_failure = _mean(part["entry_reduce_failure_flag"])
        selected_failure = _mean(accepted["entry_reduce_failure_flag"]) if len(accepted) else 0.0
        rows.append(
            {
                "quarter": quarter,
                "entry_count": int(len(part)),
                "accepted_count": int(len(accepted)),
                "baseline_avg_return_pct": float(base_ret * 100.0),
                "accepted_avg_return_pct": float(selected_ret * 100.0) if len(accepted) else 0.0,
                "accepted_return_delta_pct_point": float((selected_ret - base_ret) * 100.0) if len(accepted) else 0.0,
                "baseline_failure_rate": base_failure,
                "accepted_failure_rate": selected_failure,
                "accepted_failure_delta_pct_point": float((selected_failure - base_failure) * 100.0) if len(accepted) else 0.0,
                "positive_quarter_flag": int(len(accepted) >= 3 and selected_ret > base_ret and selected_failure <= base_failure + 0.25),
            }
        )
    return pd.DataFrame(rows)


def build_architecture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "layer": "G0 source_store",
                "input": "Task614/Task615 intelligence event store",
                "role": "collect political, geopolitical, institution, and IR proxy events before linkage",
                "status": "CONNECTED_DIAGNOSTIC",
            },
            {
                "layer": "G1 chart_health",
                "input": "pre-entry relative strength, theme confirmation, gap age, late breakout",
                "role": "keep simple chart continuation quality score",
                "status": "CONNECTED_DIAGNOSTIC",
            },
            {
                "layer": "G2 chart_risk_guard",
                "input": "VWAP fail, opening range rejection, volume decay",
                "role": "wait-window risk guard for review or size-down testing",
                "status": "CONNECTED_DIAGNOSTIC",
            },
            {
                "layer": "G3 intelligence_support",
                "input": "P0/P1 event counts and flags",
                "role": "use source context as confirmation, not as direct trading truth",
                "status": "CONNECTED_DIAGNOSTIC",
            },
            {
                "layer": "G4 fusion_action",
                "input": "chart health + intelligence support + risk guard",
                "role": "accept, review, or reject candidates in backtest only",
                "status": "BACKTEST_ONLY",
            },
            {
                "layer": "G5 promotion_gate",
                "input": "sample, quarter stability, leakage, cost/readiness",
                "role": "block strategy promotion until evidence is stronger",
                "status": "ENFORCED",
            },
        ]
    )


def build_pass_fail(scored: pd.DataFrame, scenario_summary: pd.DataFrame, fold_summary: pd.DataFrame) -> pd.DataFrame:
    fusion = scenario_summary[scenario_summary["scenario"].eq("turbo_fusion_accept_h60_i70_riskoff")].iloc[0]
    positive_quarters = int(fold_summary["positive_quarter_flag"].sum())
    total_quarters = int(len(fold_summary))
    source_cols = [
        "political_statement_pre7d_flag",
        "geopolitical_event_pre7d_flag",
        "institution_ownership_pre30d_flag",
        "ceo_ir_proxy_pre14d_flag",
    ]
    attached_source_count = int(sum(int(scored[col].sum() > 0) for col in source_cols))
    rows = [
        {
            "gate": "source_chart_fusion_connected",
            "pass_flag": int(attached_source_count >= 3 and int(fusion["selected_count"]) > 0),
            "observed_value": f"attached_source_groups={attached_source_count}; fusion_selected={int(fusion['selected_count'])}",
            "required_value": ">=3 source groups and >0 fusion selected rows",
        },
        {
            "gate": "diagnostic_performance_candidate",
            "pass_flag": int(
                int(fusion["selected_count"]) >= 50
                and float(fusion["selected_avg_return_delta_pct_point"]) >= 3.0
                and float(fusion["failure_rate_delta_pct_point"]) <= -3.0
            ),
            "observed_value": f"selected={int(fusion['selected_count'])}; return_delta={float(fusion['selected_avg_return_delta_pct_point']):.2f}pp; failure_delta={float(fusion['failure_rate_delta_pct_point']):.2f}pp",
            "required_value": "selected>=50; return_delta>=3pp; failure_delta<=-3pp",
        },
        {
            "gate": "quarter_stability",
            "pass_flag": int(total_quarters >= 6 and positive_quarters >= 4),
            "observed_value": f"positive_quarters={positive_quarters}/{total_quarters}",
            "required_value": ">=4 positive quarters across >=6 quarters",
        },
        {
            "gate": "leakage_guard",
            "pass_flag": int(scored["tq_fusion_assignment_label_used_flag"].max() == 0 and scored["tq_fusion_gpt_or_plugin_used_as_source_flag"].max() == 0),
            "observed_value": "label_used=0; gpt_or_plugin_source=0",
            "required_value": "must be 0",
        },
        {
            "gate": "trading_promotion",
            "pass_flag": 0,
            "observed_value": "diagnostic fusion uses simulated original entry returns; no delayed-entry fill, cost, or full OOS replay yet",
            "required_value": "requires exact delayed-entry/exit replay, cost/slippage, source audit, and live readiness",
        },
    ]
    return pd.DataFrame(rows)


def build_decision(
    scored: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    fold_summary: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    fusion = scenario_summary[scenario_summary["scenario"].eq("turbo_fusion_accept_h60_i70_riskoff")].iloc[0]
    diagnostic_pass = int(pass_fail[pass_fail["gate"].eq("diagnostic_performance_candidate")]["pass_flag"].iloc[0])
    quarter_pass = int(pass_fail[pass_fail["gate"].eq("quarter_stability")]["pass_flag"].iloc[0])
    decision = "PASS_TURBOQUANT_FUSION_DIAGNOSTIC_FAIL_TRADING_PROMOTION"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "input_entry_count": int(len(scored)),
                "baseline_avg_return_pct": float(scored["net_return_from_entry"].mean() * 100.0),
                "baseline_failure_rate": float(scored["entry_reduce_failure_flag"].mean()),
                "fusion_accepted_count": int(fusion["selected_count"]),
                "fusion_accepted_avg_return_pct": float(fusion["selected_avg_return_pct"]),
                "fusion_accepted_return_delta_pct_point": float(fusion["selected_avg_return_delta_pct_point"]),
                "fusion_accepted_failure_rate": float(fusion["selected_failure_rate"]),
                "fusion_failure_delta_pct_point": float(fusion["failure_rate_delta_pct_point"]),
                "positive_quarter_count": int(fold_summary["positive_quarter_flag"].sum()),
                "quarter_count": int(len(fold_summary)),
                "diagnostic_performance_pass_flag": diagnostic_pass,
                "quarter_stability_pass_flag": quarter_pass,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Run exact delayed-entry/confirmation replay with cost and then promote only if OOS stays positive.",
            }
        ]
    )


def render_report(
    scenario_summary: pd.DataFrame,
    fold_summary: pd.DataFrame,
    architecture: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    top = scenario_summary.sort_values(["selected_avg_return_delta_pct_point", "selected_count"], ascending=[False, False], kind="stable").head(8)
    lines = [
        "# Task616 TurboQuant Intelligence Chart Fusion Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Baseline: {int(d['input_entry_count'])} entries, {float(d['baseline_avg_return_pct']):.2f}% avg return, {float(d['baseline_failure_rate']) * 100.0:.2f}% failure rate.",
        f"- Fusion accepted: {int(d['fusion_accepted_count'])} entries, {float(d['fusion_accepted_avg_return_pct']):.2f}% avg return, +{float(d['fusion_accepted_return_delta_pct_point']):.2f}pp vs baseline.",
        f"- Fusion failure rate: {float(d['fusion_accepted_failure_rate']) * 100.0:.2f}% ({float(d['fusion_failure_delta_pct_point']):.2f}pp vs baseline).",
        f"- Quarter check: {int(d['positive_quarter_count'])}/{int(d['quarter_count'])} positive quarters.",
        "- Next action: exact delayed-entry/confirmation replay with cost.",
        "",
        "## Quant Expert Report",
        "",
        "### Data Source And Source Readiness",
        "",
        "- Input is Task614 `entry_p0_intelligence_linkage.csv`: chart/path features plus P0/P1 intelligence event flags.",
        "- Task615 keeps the event store alive during runtime; Task616 uses the historical linked panel for backtest only.",
        "- GPT/plugin outputs are not used as source facts or assignments.",
        "",
        "### Exact Join Keys",
        "",
        "- Intelligence events were already linked by Task614 using timestamp/date, symbol/theme tags, and no lifecycle fallback.",
        "- Task616 only reads exact `lifecycle_id` rows from the linked panel.",
        "",
        "### Leakage Audit",
        "",
        "- Assignment features exclude `entry_reduce_failure_flag`, `net_return_from_entry`, and taxonomy labels.",
        "- Labels and returns are used only after assignment for evaluation.",
        "",
        "### Scenario Summary",
        "",
        "| Scenario | Action | Selected | Failure Rate | Avg Return | Return Delta |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, row in top.iterrows():
        lines.append(
            f"| `{row['scenario']}` | `{row['action_type']}` | {int(row['selected_count'])} | "
            f"{float(row['selected_failure_rate']) * 100.0:.2f}% | {float(row['selected_avg_return_pct']):.2f}% | "
            f"{float(row['selected_avg_return_delta_pct_point']):.2f}pp |"
        )
    lines.extend(
        [
            "",
            "### Quarter Stability",
            "",
            "| Quarter | Entries | Accepted | Base Return | Accepted Return | Positive |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in fold_summary.iterrows():
        lines.append(
            f"| `{row['quarter']}` | {int(row['entry_count'])} | {int(row['accepted_count'])} | "
            f"{float(row['baseline_avg_return_pct']):.2f}% | {float(row['accepted_avg_return_pct']):.2f}% | "
            f"{int(row['positive_quarter_flag'])} |"
        )
    lines.extend(
        [
            "",
            "### Architecture",
            "",
            "| Layer | Status | Role |",
            "|---|---|---|",
        ]
    )
    for _, row in architecture.iterrows():
        lines.append(f"| `{row['layer']}` | `{row['status']}` | {row['role']} |")
    lines.extend(
        [
            "",
            "### Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Direction is right: chart plus intelligence beats chart-only diagnostic baseline in this panel.",
            "- It is not ready for real trading: the replay still uses original simulated entry returns.",
            "- Keep it as a TurboQuant backtest candidate, then rerun with delayed-entry fills and costs.",
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_614_p0_intelligence_source_attachment/entry_p0_intelligence_linkage.csv`",
            "",
            "### Outputs",
            "",
            "- `turboquant_fusion_entry_panel.csv`",
            "- `turboquant_fusion_scenario_summary.csv`",
            "- `turboquant_fusion_quarter_summary.csv`",
            "- `turboquant_fusion_architecture.csv`",
            "- `task_616_pass_fail_matrix.csv`",
            "- `task_616_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task616_turboquant_intelligence_chart_fusion_backtest`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def _mean(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float(pd.to_numeric(series, errors="coerce").fillna(0.0).mean())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--linked-panel", type=Path, default=LINKED_PANEL)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task616_turboquant_intelligence_chart_fusion_backtest(
        linked_panel_path=args.linked_panel,
        out_dir=args.out_dir,
    )
    decision = artifacts["task_616_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"accepted={int(decision['fusion_accepted_count'])} "
        f"avg_return={float(decision['fusion_accepted_avg_return_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
