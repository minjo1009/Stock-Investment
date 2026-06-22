from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_source_time_capture_372 import (
    DEFAULT_OUT_DIR,
    SourceTimeCapture372Artifacts,
    build_source_time_capture_372,
    write_source_time_capture_372,
)


def _metric_map(metrics_df: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["metric_name"]): float(pd.to_numeric(pd.Series([row["metric_value"]]), errors="coerce").fillna(0.0).iloc[0])
        for _, row in metrics_df.iterrows()
    }


def _effect_delta(effect_df: pd.DataFrame, scope: str, cut_name: str) -> tuple[float, float]:
    scoped = effect_df[(effect_df["evaluation_scope"].astype(str) == scope) & (effect_df["cut_name"].astype(str) == cut_name)].copy()
    if scoped.empty:
        return 0.0, 0.0
    selected = scoped[scoped["bucket_name"].astype(str) == "selected"]
    other = scoped[scoped["bucket_name"].astype(str) == "other"]
    if selected.empty or other.empty:
        return 0.0, 0.0
    selected_avg = float(pd.to_numeric(selected.iloc[0]["avg_realized_R"], errors="coerce"))
    other_avg = float(pd.to_numeric(other.iloc[0]["avg_realized_R"], errors="coerce"))
    selected_total = float(pd.to_numeric(selected.iloc[0]["total_realized_R"], errors="coerce"))
    other_total = float(pd.to_numeric(other.iloc[0]["total_realized_R"], errors="coerce"))
    return round(selected_avg - other_avg, 6), round(selected_total - other_total, 6)


def _write_report(out_dir: Path, artifacts: SourceTimeCapture372Artifacts) -> None:
    metrics = _metric_map(artifacts.backfill_coverage_summary)
    panel = artifacts.lifecycle_backtest_panel.copy()
    full_scope = artifacts.scope_comparison[artifacts.scope_comparison["evaluation_scope"].astype(str) == "full_period"].copy()
    anchored_scope = artifacts.scope_comparison[artifacts.scope_comparison["evaluation_scope"].astype(str) == "anchored_oos"].copy()
    full_lifecycle_share = (
        float(metrics.get("full_lifecycle_sample_count", 0.0)) / max(float(metrics.get("lifecycles_recorded", 0.0)), 1.0)
        if metrics.get("lifecycles_recorded", 0.0) > 0
        else 0.0
    )
    anchored_add_delta, anchored_add_total_delta = _effect_delta(artifacts.effect_summary, "anchored_oos", "add_confirmed")
    anchored_fragile_delta, anchored_fragile_total_delta = _effect_delta(artifacts.effect_summary, "anchored_oos", "fragile_transition")
    anchored_healthy_delta, _ = _effect_delta(artifacts.effect_summary, "anchored_oos", "healthy_start")
    full_source_linked_delta, _ = _effect_delta(artifacts.effect_summary, "full_period", "source_linked")
    row_level_changed = abs(anchored_add_delta - full_source_linked_delta) > 1e-9

    lines = [
        "# Task 372 - Historical Source-Event Backfill & Lifecycle Backtest",
        "",
        "## Core Findings",
        f"- historical_backfill_rows: {int(metrics.get('source_rows_recorded', 0.0))}",
        f"- lifecycles_generated: {int(metrics.get('lifecycles_recorded', 0.0))}",
        f"- full_lifecycle_sample_share: {round(full_lifecycle_share, 6)}",
        f"- anchored_oos_add_expectancy_delta: {anchored_add_delta}",
        f"- anchored_oos_add_total_r_delta: {anchored_add_total_delta}",
        f"- anchored_oos_fragile_expectancy_delta: {anchored_fragile_delta}",
        f"- anchored_oos_fragile_total_r_delta: {anchored_fragile_total_delta}",
        f"- anchored_oos_healthy_start_expectancy_delta: {anchored_healthy_delta}",
        f"- full_period_source_linked_expectancy_delta: {full_source_linked_delta}",
        "",
        "## Required Answers",
        f"- Q1 historical backfill rows generated: `{int(metrics.get('source_rows_recorded', 0.0))}`",
        f"- Q2 lifecycles under source-time schema: `{int(metrics.get('lifecycles_recorded', 0.0))}`",
        f"- Q3 full lifecycle sample share: `{round(full_lifecycle_share, 6)}`",
        f"- Q4 add/scale effect improves returns: `{'YES' if anchored_add_delta > 0 or anchored_add_total_delta > 0 else 'NO'}`",
        f"- Q5 fragile transition detection reduces loss: `{'YES' if anchored_fragile_delta > 0 or anchored_fragile_total_delta > 0 else 'NO'}`",
        f"- Q6 suppression/gate/state effect holds lifecycle-wise: `{'YES' if anchored_healthy_delta > 0 else 'NO'}`",
        f"- Q7 row-level and lifecycle-level conclusions differ: `{'YES' if row_level_changed else 'NO'}`",
        "",
        "## Backfill Coverage",
        *(_markdown_table(artifacts.backfill_coverage_summary)),
        "",
        "## Scope Comparison",
        *(_markdown_table(artifacts.scope_comparison)),
        "",
        "## Effect Summary",
        *(_markdown_table(artifacts.effect_summary.head(40))),
        "",
        "## Lifecycle Panel Sample",
        *(_markdown_table(panel.head(30))),
        "",
        "## Historical Event Sample",
        *(_markdown_table(artifacts.historical_source_event_dataset.head(30))),
    ]
    if not anchored_scope.empty:
        lines.extend(["", "## Anchored OOS Comparison", *(_markdown_table(anchored_scope))])
    if not full_scope.empty:
        lines.extend(["", "## Full Period Comparison", *(_markdown_table(full_scope))])
    (out_dir / "task_372_historical_source_backfill.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 372 historical source-event backfill & lifecycle backtest")
    parser.add_argument("--db-path", type=str, default="trading.db")
    parser.add_argument("--capture-batch-id", type=str, default="task372_default")
    parser.add_argument("--reuse-existing-batch", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_source_time_capture_372(
        db_path=args.db_path,
        capture_batch_id=args.capture_batch_id,
        reuse_existing_batch=args.reuse_existing_batch,
    )
    write_source_time_capture_372(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
