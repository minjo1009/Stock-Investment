from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_canonical_continuation_oos_overlay_387 import (
    ANCHOR_DATE,
    DEFAULT_OUT_DIR,
    TASK_385_EVENT_LOG_PATH,
    TASK_386_QUALITY_PANEL_PATH,
    CanonicalContinuationOosOverlay387Artifacts,
    build_canonical_continuation_oos_overlay_387,
    write_canonical_continuation_oos_overlay_387,
)


def _write_report(out_dir: Path, artifacts: CanonicalContinuationOosOverlay387Artifacts) -> None:
    decision = artifacts.task_387_decision
    panel = artifacts.canonical_oos_quality_panel
    path = artifacts.canonical_oos_path_quality_audit
    transition = artifacts.canonical_oos_transition_quality_audit
    bucket = artifacts.canonical_oos_bucket_overlay_audit
    sample = artifacts.canonical_oos_sample_adequacy_audit
    anomaly = artifacts.canonical_sequence_anomaly_audit
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    lines = [
        "# Task 387 - Canonical Continuation OOS Split & Universe Overlay Validation",
        "",
        "## Required Answers",
        "- Did Task 387 use canonical stream only? `YES`",
        "- Did Task 387 use symbol/session recovery? `NO`",
        "- Did Task 387 relax thresholds or optimize strategy? `NO`",
        f"- anchor_date: `{row.get('anchor_date', ANCHOR_DATE)}`",
        f"- anchored_oos_lifecycle_count: {row.get('anchored_oos_lifecycle_count', 0)}",
        f"- anchored_oos_sample_gate: `{row.get('anchored_oos_sample_gate', 'diagnostic_only')}`",
        f"- sequence_anomaly_count: {row.get('sequence_anomaly_count', 0)}",
        "",
        "## Decision",
        *(_markdown_table(decision)),
        "",
        "## Sample Adequacy",
        *(_markdown_table(sample)),
        "",
        "## Sequence Anomaly Audit",
        *(_markdown_table(anomaly)),
        "",
        "## OOS Path Quality",
        *(_markdown_table(path)),
        "",
        "## OOS Transition Quality",
        *(_markdown_table(transition)),
        "",
        "## Bucket Overlay Quality",
        *(_markdown_table(bucket)),
        "",
        "## OOS Panel Sample",
        *(_markdown_table(panel.head(50))),
    ]
    (out_dir / "task_387_canonical_continuation_oos_overlay.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 387 canonical continuation OOS overlay")
    parser.add_argument("--quality-panel-path", type=Path, default=TASK_386_QUALITY_PANEL_PATH)
    parser.add_argument("--event-log-path", type=Path, default=TASK_385_EVENT_LOG_PATH)
    parser.add_argument("--anchor-date", type=str, default=ANCHOR_DATE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_canonical_continuation_oos_overlay_387(
        quality_panel_path=args.quality_panel_path,
        event_log_path=args.event_log_path,
        anchor_date=args.anchor_date,
    )
    write_canonical_continuation_oos_overlay_387(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
