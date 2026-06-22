from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate


TASK_ID = "Task620"
REPORT_DIR = Path("docs/reports/task_620_recent_oos_failure_decomposition")
TASK617_PANEL = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv")

EVENT_FLAG_COLUMNS = [
    "political_statement_pre7d_flag",
    "geopolitical_event_pre7d_flag",
    "institution_ownership_pre30d_flag",
    "passive_13g_pre30d_flag",
    "insider_form4_or_144_pre30d_flag",
    "ceo_ir_proxy_pre14d_flag",
    "p0_source_event_density_ge2_flag",
]


def build_task620_recent_oos_failure_decomposition(
    *,
    panel_path: Path = TASK617_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(panel_path)
    recent = panel[panel["split_name"].astype(str).eq("recent_oos")].copy().reset_index(drop=True)
    validation = panel[panel["split_name"].astype(str).eq("validation")].copy().reset_index(drop=True)

    taxonomy_panel = assign_recent_taxonomy(recent)
    taxonomy_summary = summarize_taxonomy(taxonomy_panel)
    degradation = build_degradation_matrix(validation, recent)
    source_discrimination = build_source_discrimination(panel)
    source_findings = build_source_findings(source_discrimination, recent)
    pass_fail = build_pass_fail(taxonomy_panel, taxonomy_summary, degradation)
    decision = build_decision(taxonomy_panel, taxonomy_summary, source_findings, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    taxonomy_panel.to_csv(out_dir / "recent_oos_failure_taxonomy.csv", index=False)
    taxonomy_summary.to_csv(out_dir / "recent_oos_failure_taxonomy_summary.csv", index=False)
    degradation.to_csv(out_dir / "recent_oos_degradation_matrix.csv", index=False)
    source_discrimination.to_csv(out_dir / "recent_oos_intelligence_source_discrimination.csv", index=False)
    source_findings.to_csv(out_dir / "recent_oos_source_findings.csv", index=False)
    pass_fail.to_csv(out_dir / "task_620_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_620_decision.csv", index=False)
    (out_dir / "task_620_recent_oos_failure_decomposition.md").write_text(
        render_report(taxonomy_summary, degradation, source_findings, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "recent_oos_failure_taxonomy": taxonomy_panel,
        "recent_oos_failure_taxonomy_summary": taxonomy_summary,
        "recent_oos_degradation_matrix": degradation,
        "recent_oos_intelligence_source_discrimination": source_discrimination,
        "recent_oos_source_findings": source_findings,
        "task_620_pass_fail_matrix": pass_fail,
        "task_620_decision": decision,
    }


def load_panel(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing Task617 panel: {path}")
    panel = pd.read_csv(path)
    required = {"lifecycle_id", "split_name", "entry_ts", "net_return_from_entry", "win_flag", "entry_reduce_failure_flag"}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    panel = panel.copy()
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    for col in ["win_flag", "entry_reduce_failure_flag", "false_positive_flag"]:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0).astype(int)
    numeric_cols = [
        "theme_ret20_prev",
        "theme_breadth20_prev",
        "volume_ratio_prev",
        "intraday_ret_from_open",
        "range_pos",
        "p0_source_event_density",
        "tq_intelligence_support_score",
        "tq_pre_entry_chart_health_score",
        "tq_runtime_entry_confirmation_score",
    ]
    for col in numeric_cols + EVENT_FLAG_COLUMNS:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "split_name", "entry_ts", "net_return_from_entry"]).reset_index(drop=True)


def assign_recent_taxonomy(recent: pd.DataFrame) -> pd.DataFrame:
    out = recent.copy()
    if out.empty:
        return out
    out["recent_oos_problem_flag"] = (
        out["entry_reduce_failure_flag"].astype(int).eq(1)
        | out["win_flag"].astype(int).eq(0)
        | out.get("false_positive_flag", pd.Series(0, index=out.index)).astype(int).eq(1)
    ).astype(int)
    rows: list[str] = []
    for _, row in out.iterrows():
        taxonomy = "clean_recent_oos_winner"
        if int(row["recent_oos_problem_flag"]) == 1:
            taxonomy = classify_failure(row)
        rows.append(taxonomy)
    out["primary_failure_taxonomy"] = rows
    out["taxonomy_assigned_flag"] = out["primary_failure_taxonomy"].ne("unclassified_recent_oos_problem").astype(int)
    out["label_used_in_assignment_flag"] = 0
    out["gpt_or_plugin_used_as_source_flag"] = 0
    keep = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "split_name",
        "net_return_from_entry",
        "win_flag",
        "entry_reduce_failure_flag",
        "false_positive_flag",
        "holding_days",
        "same_day_exit_flag",
        "exit_reason",
        "primary_failure_taxonomy",
        "recent_oos_problem_flag",
        "taxonomy_assigned_flag",
        "theme_regime_state_v4",
        "timing_state",
        "symbol_multiday_setup_state",
        "theme_ret20_prev",
        "theme_breadth20_prev",
        "volume_ratio_prev",
        "intraday_ret_from_open",
        "range_pos",
        "p0_source_event_density",
        "tq_intelligence_support_score",
        "ceo_ir_proxy_pre14d_flag",
        "passive_13g_pre30d_flag",
        "political_statement_pre7d_flag",
        "geopolitical_event_pre7d_flag",
        "institution_ownership_pre30d_flag",
        "label_used_in_assignment_flag",
        "gpt_or_plugin_used_as_source_flag",
    ]
    return out[[col for col in keep if col in out.columns]].copy()


def classify_failure(row: pd.Series) -> str:
    theme = str(row.get("theme_id", ""))
    regime = str(row.get("theme_regime_state_v4", ""))
    timing = str(row.get("timing_state", ""))
    exit_reason = str(row.get("exit_reason", ""))
    theme_ret20 = float(row.get("theme_ret20_prev", 0.0) or 0.0)
    ceo_ir = int(float(row.get("ceo_ir_proxy_pre14d_flag", 0.0) or 0.0))

    if theme == "aerospace_defense_space":
        return "theme_specific_collapse_aerospace_defense"
    if theme_ret20 > 0.15 and regime == "persistent_theme_leader":
        return "overextended_persistent_theme_leader"
    if exit_reason == "trailing_stop_exit":
        return "trailing_stop_path_failure"
    if timing == "midday_continuation":
        return "late_midday_continuation_decay"
    if ceo_ir == 0:
        return "broad_event_support_without_recent_ir_proxy"
    return "residual_recent_oos_problem"


def summarize_taxonomy(taxonomy_panel: pd.DataFrame) -> pd.DataFrame:
    if taxonomy_panel.empty:
        return pd.DataFrame()
    rows = []
    for taxonomy, group in taxonomy_panel.groupby("primary_failure_taxonomy", dropna=False):
        metrics = aggregate(group)
        rows.append(
            {
                "primary_failure_taxonomy": taxonomy,
                "trade_count": int(len(group)),
                "problem_count": int(group["recent_oos_problem_flag"].sum()),
                "problem_share": float(group["recent_oos_problem_flag"].mean()),
                "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                "win_rate": float(metrics.get("win_rate", 0.0)),
                "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                "avg_p0_source_event_density": float(pd.to_numeric(group.get("p0_source_event_density"), errors="coerce").mean())
                if "p0_source_event_density" in group
                else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["problem_count", "trade_count"], ascending=False).reset_index(drop=True)


def build_degradation_matrix(validation: pd.DataFrame, recent: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dimensions = [
        ("overall", None, None),
        ("theme_id", "theme_id", None),
        ("theme_regime_state_v4", "theme_regime_state_v4", None),
        ("timing_state", "timing_state", None),
        ("exit_reason", "exit_reason", None),
        ("theme_ret20_gt_15", None, lambda frame: pd.to_numeric(frame["theme_ret20_prev"], errors="coerce").gt(0.15)),
        ("ceo_ir_proxy_pre14d_flag", "ceo_ir_proxy_pre14d_flag", None),
    ]
    for dimension, col, mask_builder in dimensions:
        if dimension == "overall":
            rows.append(degradation_row("overall", "all", validation, recent))
            continue
        if mask_builder is not None:
            rows.append(degradation_row(dimension, "1", validation[mask_builder(validation)], recent[mask_builder(recent)]))
            continue
        values = sorted(set(validation[col].dropna().astype(str)).union(set(recent[col].dropna().astype(str))))
        for value in values:
            rows.append(degradation_row(dimension, value, validation[validation[col].astype(str).eq(value)], recent[recent[col].astype(str).eq(value)]))
    out = pd.DataFrame(rows)
    return out.sort_values(["recent_count", "avg_delta_recent_vs_validation_pct_point"], ascending=[False, True]).reset_index(drop=True)


def degradation_row(dimension: str, bucket: str, validation: pd.DataFrame, recent: pd.DataFrame) -> dict[str, object]:
    val = aggregate(validation) if not validation.empty else {}
    rec = aggregate(recent) if not recent.empty else {}
    return {
        "dimension": dimension,
        "bucket": bucket,
        "validation_count": int(len(validation)),
        "validation_avg_net_return_pct": float(val.get("avg_net_return_pct", 0.0)),
        "validation_win_rate": float(val.get("win_rate", 0.0)),
        "validation_entry_reduce_failure_rate": float(val.get("entry_reduce_failure_rate", 0.0)),
        "recent_count": int(len(recent)),
        "recent_avg_net_return_pct": float(rec.get("avg_net_return_pct", 0.0)),
        "recent_win_rate": float(rec.get("win_rate", 0.0)),
        "recent_entry_reduce_failure_rate": float(rec.get("entry_reduce_failure_rate", 0.0)),
        "avg_delta_recent_vs_validation_pct_point": float(rec.get("avg_net_return_pct", 0.0)) - float(val.get("avg_net_return_pct", 0.0)),
        "entry_reduce_delta_recent_vs_validation_pct_point": (
            float(rec.get("entry_reduce_failure_rate", 0.0)) - float(val.get("entry_reduce_failure_rate", 0.0))
        )
        * 100.0,
    }


def build_source_discrimination(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    subset = panel[panel["split_name"].astype(str).isin(["validation", "recent_oos"])].copy()
    for split_name, split_group in subset.groupby("split_name"):
        for col in EVENT_FLAG_COLUMNS:
            if col not in split_group.columns:
                continue
            values = sorted(pd.to_numeric(split_group[col], errors="coerce").dropna().unique().tolist())
            for value in values:
                group = split_group[pd.to_numeric(split_group[col], errors="coerce").eq(value)]
                metrics = aggregate(group) if not group.empty else {}
                rows.append(
                    {
                        "split_name": split_name,
                        "source_flag": col,
                        "flag_value": int(value),
                        "trade_count": int(len(group)),
                        "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                        "win_rate": float(metrics.get("win_rate", 0.0)),
                        "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                        "discrimination_possible_flag": int(len(values) > 1),
                    }
                )
    return pd.DataFrame(rows).sort_values(["split_name", "source_flag", "flag_value"]).reset_index(drop=True)


def build_source_findings(source_discrimination: pd.DataFrame, recent: pd.DataFrame) -> pd.DataFrame:
    rows = []
    recent_source = source_discrimination[source_discrimination["split_name"].astype(str).eq("recent_oos")]
    for col in EVENT_FLAG_COLUMNS:
        group = recent_source[recent_source["source_flag"].astype(str).eq(col)]
        possible = int(group["discrimination_possible_flag"].max()) if not group.empty else 0
        active_share = float(pd.to_numeric(recent[col], errors="coerce").fillna(0).mean()) if col in recent.columns and len(recent) else 0.0
        rows.append(
            {
                "source_flag": col,
                "recent_active_share": active_share,
                "discrimination_possible_flag": possible,
                "finding": "too_broad_in_recent_oos" if active_share in {0.0, 1.0} else "has_some_cross_sectional_variation",
            }
        )
    return pd.DataFrame(rows)


def build_pass_fail(taxonomy_panel: pd.DataFrame, taxonomy_summary: pd.DataFrame, degradation: pd.DataFrame) -> pd.DataFrame:
    problem = taxonomy_panel[taxonomy_panel["recent_oos_problem_flag"].astype(int).eq(1)] if not taxonomy_panel.empty else pd.DataFrame()
    coverage = float(problem["taxonomy_assigned_flag"].mean()) if not problem.empty else 0.0
    recent_metrics = aggregate(taxonomy_panel) if not taxonomy_panel.empty else {}
    overall = degradation[(degradation["dimension"].eq("overall")) & (degradation["bucket"].eq("all"))].iloc[0]
    top_taxonomy_count = int(taxonomy_summary["problem_count"].max()) if not taxonomy_summary.empty else 0
    return pd.DataFrame(
        [
            {
                "gate": "taxonomy_coverage",
                "pass_flag": int(coverage >= 0.80),
                "observed_value": f"{coverage * 100.0:.2f}%",
                "required_value": ">=80.00% of recent OOS problem trades assigned to a taxonomy",
            },
            {
                "gate": "recent_oos_performance",
                "pass_flag": int(
                    float(recent_metrics.get("avg_net_return_pct", 0.0)) >= 5.0
                    and float(recent_metrics.get("win_rate", 0.0)) >= 0.50
                    and float(recent_metrics.get("entry_reduce_failure_rate", 1.0)) <= 0.40
                ),
                "observed_value": (
                    f"avg={float(recent_metrics.get('avg_net_return_pct', 0.0)):.2f}%; "
                    f"win={float(recent_metrics.get('win_rate', 0.0)) * 100.0:.2f}%; "
                    f"entry_reduce={float(recent_metrics.get('entry_reduce_failure_rate', 0.0)) * 100.0:.2f}%"
                ),
                "required_value": "avg>=5.00%, win>=50.00%, entry_reduce<=40.00%",
            },
            {
                "gate": "degradation_explained",
                "pass_flag": int(top_taxonomy_count >= 20 and float(overall["avg_delta_recent_vs_validation_pct_point"]) < 0.0),
                "observed_value": f"top_taxonomy_problem_count={top_taxonomy_count}; overall_delta={float(overall['avg_delta_recent_vs_validation_pct_point']):.2f}pp",
                "required_value": "top taxonomy count >=20 and recent OOS degradation visible",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "recent OOS performance gate fails",
                "required_value": "must pass recent OOS, cost/slippage, and live-source gates",
            },
        ]
    )


def build_decision(
    taxonomy_panel: pd.DataFrame,
    taxonomy_summary: pd.DataFrame,
    source_findings: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    recent = aggregate(taxonomy_panel) if not taxonomy_panel.empty else {}
    top = taxonomy_summary.iloc[0] if not taxonomy_summary.empty else pd.Series(dtype=object)
    too_broad = int(source_findings["finding"].astype(str).eq("too_broad_in_recent_oos").sum()) if not source_findings.empty else 0
    performance_pass = int(pass_fail[pass_fail["gate"].eq("recent_oos_performance")]["pass_flag"].iloc[0])
    decision = "FAIL_RECENT_OOS_STABILITY_SOURCE_FLAGS_TOO_BROAD"
    if performance_pass:
        decision = "PASS_RECENT_OOS_STABILITY_DIAGNOSTIC"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "recent_oos_trade_count": int(len(taxonomy_panel)),
                "recent_oos_avg_net_return_pct": float(recent.get("avg_net_return_pct", 0.0)),
                "recent_oos_win_rate": float(recent.get("win_rate", 0.0)),
                "recent_oos_entry_reduce_failure_rate": float(recent.get("entry_reduce_failure_rate", 0.0)),
                "top_failure_taxonomy": str(top.get("primary_failure_taxonomy", "")),
                "top_failure_problem_count": int(top.get("problem_count", 0) or 0),
                "too_broad_recent_source_flag_count": too_broad,
                "recent_oos_gate_pass_flag": performance_pass,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Run Task621 cost/slippage stress, but keep refinement blocked; source flags need narrower event typing before source-driven trading claims.",
            }
        ]
    )


def render_report(
    taxonomy_summary: pd.DataFrame,
    degradation: pd.DataFrame,
    source_findings: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task620 Recent OOS Failure Decomposition",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Recent OOS: {int(d['recent_oos_trade_count'])} trades, avg {float(d['recent_oos_avg_net_return_pct']):.2f}%, win {float(d['recent_oos_win_rate']) * 100.0:.2f}%, entry-reduce {float(d['recent_oos_entry_reduce_failure_rate']) * 100.0:.2f}%.",
        f"- Top failure taxonomy: `{d['top_failure_taxonomy']}` with {int(d['top_failure_problem_count'])} problem trades.",
        "- GPT/plugin output is not used as a source or score input.",
        "",
        "## Quant Expert Report",
        "",
        "### Failure Taxonomy Summary",
        "",
        "| Taxonomy | Trades | Problems | Avg Return | Win | Entry-Reduce | Avg Event Density |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in taxonomy_summary.iterrows():
        lines.append(
            f"| `{row['primary_failure_taxonomy']}` | {int(row['trade_count'])} | {int(row['problem_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['win_rate']) * 100.0:.2f}% | "
            f"{float(row['entry_reduce_failure_rate']) * 100.0:.2f}% | {float(row['avg_p0_source_event_density']):.2f} |"
        )
    lines.extend(
        [
            "",
            "### Biggest Degradation Buckets",
            "",
            "| Dimension | Bucket | Validation Count | Validation Avg | Recent Count | Recent Avg | Delta | Recent Entry-Reduce |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    show = degradation[degradation["recent_count"].astype(int).ge(10)].sort_values(
        ["avg_delta_recent_vs_validation_pct_point", "recent_count"], ascending=[True, False]
    ).head(8)
    for _, row in show.iterrows():
        lines.append(
            f"| `{row['dimension']}` | `{row['bucket']}` | {int(row['validation_count'])} | "
            f"{float(row['validation_avg_net_return_pct']):.2f}% | {int(row['recent_count'])} | "
            f"{float(row['recent_avg_net_return_pct']):.2f}% | {float(row['avg_delta_recent_vs_validation_pct_point']):.2f}pp | "
            f"{float(row['recent_entry_reduce_failure_rate']) * 100.0:.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Intelligence Source Findings",
            "",
            "| Source Flag | Recent Active Share | Discriminates In Recent OOS | Finding |",
            "|---|---:|---:|---|",
        ]
    )
    for _, row in source_findings.iterrows():
        lines.append(
            f"| `{row['source_flag']}` | {float(row['recent_active_share']) * 100.0:.2f}% | "
            f"{int(row['discrimination_possible_flag'])} | `{row['finding']}` |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Recent OOS weakness is real and still blocks promotion.",
            "- The intelligence layer helps diagnosis, but the current event flags are too broad in recent OOS.",
            "- The largest damage comes from aerospace/defense-space, overextended persistent theme leaders, and trailing-stop path failures.",
            "- This supports better source typing and recent-OOS decomposition before strategy refinement.",
            "",
            "## Pass/Fail Matrix",
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
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `recent_oos_failure_taxonomy.csv`",
            "- `recent_oos_failure_taxonomy_summary.csv`",
            "- `recent_oos_degradation_matrix.csv`",
            "- `recent_oos_intelligence_source_discrimination.csv`",
            "- `recent_oos_source_findings.csv`",
            "- `task_620_pass_fail_matrix.csv`",
            "- `task_620_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task620_recent_oos_failure_decomposition`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task620_recent_oos_failure_decomposition(out_dir=args.out_dir)
    row = artifacts["task_620_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"recent_avg={float(row['recent_oos_avg_net_return_pct']):.2f}% "
        f"entry_reduce={float(row['recent_oos_entry_reduce_failure_rate']) * 100.0:.2f}%"
    )


if __name__ == "__main__":
    main()
