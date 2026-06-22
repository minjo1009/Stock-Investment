from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_canonical_continuation_quality_386 import (
    DEFAULT_OUT_DIR,
    TASK_382_REPLAY_PANEL_PATH,
    TASK_382_REVALIDATION_PANEL_PATH,
    TASK_385_EVENT_LOG_PATH,
    TASK_385_LIFECYCLE_SUMMARY_PATH,
    CanonicalContinuationQuality386Artifacts,
    build_canonical_continuation_quality_386,
    write_canonical_continuation_quality_386,
)


def _write_report(out_dir: Path, artifacts: CanonicalContinuationQuality386Artifacts) -> None:
    decision = artifacts.task_386_decision
    panel = artifacts.canonical_lifecycle_quality_panel
    path = artifacts.canonical_path_quality_audit
    transition = artifacts.canonical_transition_quality_audit
    bucket = artifacts.canonical_bucket_quality_audit
    boundary = artifacts.canonical_quality_boundary_audit
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    lines = [
        "# Task 386 - Canonical Continuation Quality Evaluation",
        "",
        "## Required Answers",
        "- Did Task 386 use reconstruction/recovery? `NO`",
        "- Did Task 386 use symbol/session matching? `NO`",
        "- Did Task 386 relax thresholds or optimize strategy? `NO`",
        f"- canonical_lifecycle_count: {len(panel)}",
        f"- add_scale_quality_measurable: `{bool(row.get('add_scale_quality_measurable_flag', 0))}`",
        f"- transition_quality_measurable: `{bool(row.get('transition_quality_measurable_flag', 0))}`",
        f"- bucket_quality_measurable: `{bool(row.get('bucket_quality_measurable_flag', 0))}`",
        "",
        "## Decision",
        *(_markdown_table(decision)),
        "",
        "## Boundary Audit",
        *(_markdown_table(boundary)),
        "",
        "## Path Quality",
        *(_markdown_table(path)),
        "",
        "## Transition Quality",
        *(_markdown_table(transition)),
        "",
        "## Bucket Quality",
        *(_markdown_table(bucket)),
        "",
        "## Lifecycle Quality Sample",
        *(_markdown_table(panel.head(50))),
    ]
    (out_dir / "task_386_canonical_continuation_quality.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 386 canonical continuation quality evaluation")
    parser.add_argument("--event-log-path", type=Path, default=TASK_385_EVENT_LOG_PATH)
    parser.add_argument("--lifecycle-summary-path", type=Path, default=TASK_385_LIFECYCLE_SUMMARY_PATH)
    parser.add_argument("--replay-panel-path", type=Path, default=TASK_382_REPLAY_PANEL_PATH)
    parser.add_argument("--revalidation-panel-path", type=Path, default=TASK_382_REVALIDATION_PANEL_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_canonical_continuation_quality_386(
        event_log_path=args.event_log_path,
        lifecycle_summary_path=args.lifecycle_summary_path,
        replay_panel_path=args.replay_panel_path,
        revalidation_panel_path=args.revalidation_panel_path,
    )
    write_canonical_continuation_quality_386(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
