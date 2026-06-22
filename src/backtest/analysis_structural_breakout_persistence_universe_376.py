from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_persistence_universe_376 import (
    DEFAULT_OUT_DIR,
    PersistenceUniverse376Artifacts,
    build_persistence_universe_376,
    write_persistence_universe_376,
)


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: PersistenceUniverse376Artifacts) -> None:
    prediction = artifacts.persistence_universe_prediction_frame
    labels = artifacts.stateful_persistence_labels
    evaluation = artifacts.persistence_universe_evaluation_panel
    bucket_audit = artifacts.persistence_universe_bucket_audit
    leakage = artifacts.persistence_universe_leakage_audit
    sample_audit = artifacts.persistence_universe_sample_adequacy_audit
    decision = artifacts.persistence_universe_decision

    decision_row = decision.iloc[0].to_dict() if not decision.empty else {}
    verdict = str(decision_row.get("task_376_verdict", "NOT_YET"))
    acceptance = str(decision_row.get("acceptance_decision", "INSUFFICIENT_EVIDENCE"))
    anchored = sample_audit[sample_audit["evaluation_scope"].astype(str).eq("anchored_oos")].copy()
    anchored_status = str(anchored.iloc[0]["gate_status"]) if not anchored.empty else "diagnostic_only"
    full_scope = sample_audit[sample_audit["evaluation_scope"].astype(str).eq("full_period")].copy()
    full_status = str(full_scope.iloc[0]["gate_status"]) if not full_scope.empty else "diagnostic_only"
    labeled_count = int(pd.to_numeric(labels.get("lifecycle_coverage_flag"), errors="coerce").fillna(0).sum()) if not labels.empty else 0
    missing_count = int((pd.to_numeric(labels.get("lifecycle_coverage_flag"), errors="coerce").fillna(0) == 0).sum()) if not labels.empty else 0
    eligible_count = int(pd.to_numeric(labels.get("label_eligible_flag"), errors="coerce").fillna(0).sum()) if not labels.empty else 0
    positive_count = int(pd.to_numeric(labels.get("stateful_persistence_target_v1"), errors="coerce").fillna(0).sum()) if not labels.empty else 0
    blocked_count = int((~leakage["allowed_for_prediction"].astype(bool)).sum()) if not leakage.empty else 0

    checklist = {
        "prediction_boundary_clean": bool(decision_row.get("prediction_boundary_clean", False)),
        "labels_present": bool(decision_row.get("labels_present", False)),
        "lifecycle_coverage_present": bool(decision_row.get("lifecycle_coverage_present", False)),
        "sample_adequacy_present": bool(decision_row.get("sample_adequacy_present", False)),
        "leakage_audit_blocks_outcomes": blocked_count >= 10,
    }

    lines = [
        "# Task 376 - Persistence Universe Rebuild",
        "",
        "## Core Findings",
        f"- prediction_candidate_count: {len(prediction)}",
        f"- lifecycle_covered_count: {labeled_count}",
        f"- lifecycle_missing_count: {missing_count}",
        f"- label_eligible_count: {eligible_count}",
        f"- stateful_persistence_positive_count: {positive_count}",
        f"- outcome_or_lifecycle_blocked_feature_count: {blocked_count}",
        f"- full_period_gate_status: {full_status}",
        f"- anchored_oos_gate_status: {anchored_status}",
        f"- acceptance_decision: {acceptance}",
        "",
        "## Required Answers",
        "- Q1 base universe: `Task 374 forward_pure_breakout_candidates`, one row per `trade_id`",
        "- Q2 lifecycle missing treatment: `coverage_missing`, low confidence, unlabeled for supervised acceptance metrics",
        "- Q3 theme role: diagnostic prior only; it cannot override failed data/risk gates",
        "- Q4 anchored OOS claim: diagnostic-only until sample thresholds are met",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Prediction boundary clean", checklist["prediction_boundary_clean"], "prediction frame excludes outcome, target, lifecycle, and exclusion columns"),
        _checklist_row("Labels generated", checklist["labels_present"], f"label_rows={len(labels)}"),
        _checklist_row("Lifecycle coverage present", checklist["lifecycle_coverage_present"], f"covered_rows={labeled_count}"),
        _checklist_row("Sample adequacy audit generated", checklist["sample_adequacy_present"], f"sample_rows={len(sample_audit)}"),
        _checklist_row("Leakage audit blocks outcomes", checklist["leakage_audit_blocks_outcomes"], f"blocked_count={blocked_count}"),
        "- [INFO] Anchored OOS is reported as diagnostic_only because sample adequacy thresholds are not met; it can guide sample expansion but cannot independently validate acceptance.",
        f"- Final Task 376 verdict: `{verdict}`",
        "",
        "## Strategy Acceptance",
        *(_markdown_table(decision)),
        "",
        "## Sample Adequacy Audit",
        *(_markdown_table(sample_audit)),
        "",
        "## Universe Bucket Audit",
        *(_markdown_table(bucket_audit)),
        "",
        "## Leakage Audit",
        *(_markdown_table(leakage)),
        "",
        "## Coverage Missing Sample",
        *(_markdown_table(labels[labels["lifecycle_coverage_flag"].astype(int).eq(0)].head(30))),
        "",
        "## Prediction Frame Sample",
        *(_markdown_table(prediction.head(30))),
        "",
        "## Evaluation Panel Sample",
        *(_markdown_table(evaluation.head(30))),
    ]
    (out_dir / "task_376_persistence_universe_rebuild.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 376 persistence universe rebuild")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_persistence_universe_376()
    write_persistence_universe_376(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
