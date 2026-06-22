from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_canonical_lifecycle_capture_expansion_383 import (
    DEFAULT_DB_PATH,
    DEFAULT_OUT_DIR,
    TASK_376_EVALUATION_PATH,
    TASK_376_PREDICTION_PATH,
    CanonicalLifecycleCaptureExpansion383Artifacts,
    build_canonical_lifecycle_capture_expansion_383,
    write_canonical_lifecycle_capture_expansion_383,
)


def _write_report(out_dir: Path, artifacts: CanonicalLifecycleCaptureExpansion383Artifacts) -> None:
    stream = artifacts.canonical_capture_event_stream
    lifecycle = artifacts.canonical_capture_lifecycle_panel
    mapping = artifacts.task376_canonical_capture_mapping_audit
    readiness = artifacts.canonical_capture_readiness_audit
    decision = artifacts.task_383_decision
    decision_row = decision.iloc[0].to_dict() if not decision.empty else {}

    lines = [
        "# Task 383 - Canonical Lifecycle Capture Expansion",
        "",
        "## Required Answers",
        "- Did Task 383 infer lifecycle identity from symbol/session? `NO`",
        "- Did Task 383 use recovery scoring? `NO`",
        "- Did Task 383 overwrite labels? `NO`",
        "- Did Task 383 relax Task 376 ontology? `NO`",
        f"- canonical_event_count: {len(stream)}",
        f"- canonical_lifecycle_count: {len(lifecycle)}",
        f"- task382_revalidation_ready: `{decision_row.get('task382_revalidation_ready', 'NO')}`",
        f"- next_priority: `{decision_row.get('next_priority', '')}`",
        "",
        "## Boundary",
        "Task 383 expands capture infrastructure. It does not validate alpha. Task 376 rows become capture-ready only when they carry explicit `lifecycle_id` and usable intraday ENTRY timestamps.",
        "",
        "## Decision",
        *(_markdown_table(decision)),
        "",
        "## Capture Readiness Audit",
        *(_markdown_table(readiness)),
        "",
        "## Task 376 Mapping Audit",
        *(_markdown_table(mapping)),
        "",
        "## Canonical Lifecycle Panel Sample",
        *(_markdown_table(lifecycle.head(30))),
        "",
        "## Canonical Event Stream Sample",
        *(_markdown_table(stream.head(50))),
    ]
    (out_dir / "task_383_canonical_lifecycle_capture_expansion.md").write_text(
        "\n".join(lines),
        encoding="utf-8-sig",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 383 canonical lifecycle capture expansion")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--task376-prediction-path", type=Path, default=TASK_376_PREDICTION_PATH)
    parser.add_argument("--task376-evaluation-path", type=Path, default=TASK_376_EVALUATION_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_canonical_lifecycle_capture_expansion_383(
        db_path=args.db_path,
        task376_prediction_path=args.task376_prediction_path,
        task376_evaluation_path=args.task376_evaluation_path,
    )
    write_canonical_lifecycle_capture_expansion_383(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
