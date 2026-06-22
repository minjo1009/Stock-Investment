from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_forward_persistence_375 import (
    DEFAULT_OUT_DIR,
    ForwardPersistence375Artifacts,
    build_forward_persistence_375,
    write_forward_persistence_375,
)


def _summary_lookup(summary: pd.DataFrame, scope: str, cut: str, column: str) -> float:
    scoped = summary[
        summary["evaluation_scope"].astype(str).eq(scope)
        & summary["evaluation_cut"].astype(str).eq(cut)
    ].copy()
    if scoped.empty or column not in scoped.columns:
        return 0.0
    return float(pd.to_numeric(scoped.iloc[0][column], errors="coerce"))


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: ForwardPersistence375Artifacts) -> None:
    prediction = artifacts.forward_persistence_prediction_frame
    labels = artifacts.forward_persistence_labels
    training = artifacts.forward_persistence_training_frame
    evaluation = artifacts.forward_persistence_evaluation_panel
    leakage = artifacts.persistence_leakage_audit
    summary = artifacts.persistence_target_summary

    forbidden = {
        "forward_persistence_target",
        "target_reason",
        "excluded_from_training",
        "exclusion_reason",
        "realized_R",
        "invalidated_flag",
        "add_confirmed_flag",
        "scale_up_flag",
        "persistence_confirmed_flag",
        "persistence_duration_minutes",
        "event_count",
        "lineage_quality",
    }
    prediction_boundary_clean = not any(column in prediction.columns for column in forbidden)
    target_count = int(pd.to_numeric(labels.get("forward_persistence_target"), errors="coerce").fillna(0).sum()) if not labels.empty else 0
    exclusion_count = int(pd.to_numeric(labels.get("excluded_from_training"), errors="coerce").fillna(0).sum()) if not labels.empty else 0
    blocked_count = int((~leakage["allowed_for_prediction"].astype(bool)).sum()) if not leakage.empty else 0

    full_high_rate = _summary_lookup(summary, "full_period", "forward_high_quality", "target_rate")
    full_pred_rate = _summary_lookup(summary, "full_period", "predicted_expandable", "target_rate")
    lift = _summary_lookup(summary, "meta", "prediction_lift", "target_rate")
    anchored_pred_count = int(_summary_lookup(summary, "anchored_oos", "predicted_expandable", "trade_count"))
    anchored_pred_rate = _summary_lookup(summary, "anchored_oos", "predicted_expandable", "target_rate")

    checklist = {
        "prediction_boundary_clean": prediction_boundary_clean,
        "target_non_empty": len(labels) > 0,
        "positive_target_available": target_count > 0,
        "training_frame_available": len(training) > 0,
        "leakage_audit_blocks_outcomes": blocked_count >= 7,
    }
    complete_pass = all(checklist.values())

    lines = [
        "# Task 375 - Forward Persistence-Or-Add Prediction",
        "",
        "## Core Findings",
        f"- prediction_candidate_count: {len(prediction)}",
        f"- labeled_candidate_count: {len(labels)}",
        f"- training_candidate_count: {len(training)}",
        f"- positive_target_count: {target_count}",
        f"- immediate_invalidation_exclusion_count: {exclusion_count}",
        f"- outcome_or_lifecycle_blocked_feature_count: {blocked_count}",
        f"- full_period_high_quality_target_rate: {round(full_high_rate, 6)}",
        f"- full_period_predicted_expandable_target_rate: {round(full_pred_rate, 6)}",
        f"- full_period_prediction_lift_vs_high_quality: {round(lift, 6)}",
        f"- anchored_oos_predicted_expandable_count: {anchored_pred_count}",
        f"- anchored_oos_predicted_expandable_target_rate: {round(anchored_pred_rate, 6)}",
        "",
        "## Required Answers",
        "- Q1 target definition: `persistence_confirmed_flag OR add_confirmed_flag OR scale_up_flag`, with immediate invalidation excluded from supervised training",
        "- Q2 prediction boundary: `forward_persistence_prediction_frame` contains no realized, lifecycle, target, or exclusion columns",
        "- Q3 is this a finished alpha ranking model: `NO`, this is a forward-clean persistence-or-add diagnostic layer",
        f"- Q4 is there enough clean target signal to continue analysis: `{'YES' if target_count > 0 else 'NO'}`",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Prediction boundary clean", checklist["prediction_boundary_clean"], f"forbidden_columns_present={not prediction_boundary_clean}"),
        _checklist_row("Target labels generated", checklist["target_non_empty"], f"label_rows={len(labels)}"),
        _checklist_row("Positive target available", checklist["positive_target_available"], f"positive_target_count={target_count}"),
        _checklist_row("Training frame available", checklist["training_frame_available"], f"training_rows={len(training)}"),
        _checklist_row("Leakage audit blocks outcomes", checklist["leakage_audit_blocks_outcomes"], f"blocked_count={blocked_count}"),
        "- [INFO] Bucket monotonicity: diagnostic_only until min_30_per_bucket_and_min_120_total_bucketed",
        f"- Final Task 375 verdict: `{'COMPLETE_PASS' if complete_pass else 'NOT_YET'}`",
        "",
        "## Immediate invalidation exclusions",
        *(_markdown_table(labels[labels["excluded_from_training"].astype(int).gt(0)].head(30))),
        "",
        "## Target Summary",
        *(_markdown_table(summary)),
        "",
        "## Leakage Audit",
        *(_markdown_table(leakage)),
        "",
        "## Prediction Frame Sample",
        *(_markdown_table(prediction.head(30))),
        "",
        "## Evaluation Panel Sample",
        *(_markdown_table(evaluation.head(30))),
    ]
    (out_dir / "task_375_forward_persistence.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 375 forward persistence-or-add prediction")
    parser.add_argument("--db-path", type=str, default="trading.db")
    parser.add_argument("--capture-batch-id", type=str, default="task374_default")
    parser.add_argument("--reuse-existing-batch", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_forward_persistence_375(
        db_path=args.db_path,
        capture_batch_id=args.capture_batch_id,
        reuse_existing_batch=args.reuse_existing_batch,
    )
    write_forward_persistence_375(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
