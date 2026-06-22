from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_canonical_lifecycle_stream_accumulation_384 import (
    DEFAULT_DB_PATH,
    DEFAULT_OUT_DIR,
    TASK_376_EVALUATION_PATH,
    TASK_376_PREDICTION_PATH,
    TASK_384_SOURCE_EVENTS_PATH,
    CanonicalLifecycleStreamAccumulation384Artifacts,
    build_canonical_lifecycle_stream_accumulation_384,
    write_canonical_lifecycle_stream_accumulation_384,
)


def _write_report(out_dir: Path, artifacts: CanonicalLifecycleStreamAccumulation384Artifacts) -> None:
    source = artifacts.canonical_accumulation_source_events
    audit = artifacts.canonical_accumulation_event_audit
    stream = artifacts.canonical_accumulation_event_stream
    lifecycle = artifacts.canonical_accumulation_lifecycle_panel
    success = artifacts.canonical_accumulation_success_audit
    task376 = artifacts.task376_canonical_capture_mapping_audit
    decision = artifacts.task_384_decision
    decision_row = decision.iloc[0].to_dict() if not decision.empty else {}

    lines = [
        "# Task 384 - Canonical Lifecycle Stream Accumulation",
        "",
        "## Required Answers",
        "- Did Task 384 optimize strategy thresholds? `NO`",
        "- Did Task 384 use symbol/session matching? `NO`",
        "- Did Task 384 use recovery scoring? `NO`",
        "- Did Task 384 allow post-entry events without explicit lifecycle_id? `NO`",
        f"- canonical_event_count: {len(stream)}",
        f"- canonical_lifecycle_count: {len(lifecycle)}",
        f"- task382_canonical_stream_only_ready: `{decision_row.get('task382_canonical_stream_only_ready', 'NO')}`",
        "",
        "## Boundary",
        "Task 384 accumulates canonical ENTRY/ADD/SCALE/REDUCE/EXIT streams. It does not infer lifecycle identity and does not validate alpha.",
        "",
        "## Decision",
        *(_markdown_table(decision)),
        "",
        "## Success Audit",
        *(_markdown_table(success)),
        "",
        "## Task 376 Capture Mapping Audit",
        *(_markdown_table(task376)),
        "",
        "## Source Event Audit",
        *(_markdown_table(audit.head(50))),
        "",
        "## Lifecycle Panel Sample",
        *(_markdown_table(lifecycle.head(30))),
        "",
        "## Event Stream Sample",
        *(_markdown_table(stream.head(80))),
        "",
        "## Source Events Sample",
        *(_markdown_table(source.head(50))),
    ]
    (out_dir / "task_384_canonical_lifecycle_stream_accumulation.md").write_text(
        "\n".join(lines),
        encoding="utf-8-sig",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 384 canonical lifecycle stream accumulation")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--source-events-path", type=Path, default=TASK_384_SOURCE_EVENTS_PATH)
    parser.add_argument("--task376-prediction-path", type=Path, default=TASK_376_PREDICTION_PATH)
    parser.add_argument("--task376-evaluation-path", type=Path, default=TASK_376_EVALUATION_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--no-execute", action="store_true")
    args = parser.parse_args()

    artifacts = build_canonical_lifecycle_stream_accumulation_384(
        db_path=args.db_path,
        source_events_path=args.source_events_path,
        task376_prediction_path=args.task376_prediction_path,
        task376_evaluation_path=args.task376_evaluation_path,
        execute_accumulation=not args.no_execute,
    )
    write_canonical_lifecycle_stream_accumulation_384(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
