from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_canonical_lifecycle_replay_revalidation_382 import (
    DEFAULT_DB_PATH,
    DEFAULT_OUT_DIR,
    TASK_376_EVALUATION_PATH,
    CanonicalLifecycleReplay382Artifacts,
    build_canonical_lifecycle_replay_revalidation_382,
    write_canonical_lifecycle_replay_revalidation_382,
)


def _write_report(out_dir: Path, artifacts: CanonicalLifecycleReplay382Artifacts) -> None:
    stream = artifacts.canonical_lifecycle_event_stream
    replay = artifacts.canonical_lifecycle_replay_panel
    panel = artifacts.canonical_persistence_revalidation_panel
    bucket = artifacts.canonical_persistence_bucket_audit
    readiness = artifacts.canonical_revalidation_readiness_audit
    decision = artifacts.task_382_decision
    decision_row = decision.iloc[0].to_dict() if not decision.empty else {}
    readiness_row = readiness.iloc[0].to_dict() if not readiness.empty else {}

    lines = [
        "# Task 382 - Canonical Lifecycle Replay & Persistence Revalidation",
        "",
        "## Required Answers",
        "- Did Task 382 overwrite labels? `NO`",
        "- Did Task 382 use symbol/session recovery matching? `NO`",
        "- Did Task 382 relax Task 376 ontology? `NO`",
        "- Did Task 382 promote AMD/semis by theme? `NO`",
        f"- canonical_event_count: {len(stream)}",
        f"- canonical_lifecycle_count: {len(replay)}",
        f"- explicit_task376_join_available: `{bool(readiness_row.get('explicit_join_available_flag', 0))}`",
        f"- joined_task376_lifecycle_count: {int(readiness_row.get('joined_lifecycle_count', 0) or 0)}",
        f"- persistence_revalidation_ready: `{decision_row.get('persistence_revalidation_ready', 'NO')}`",
        "",
        "## Interpretation Boundary",
        "Task 382 replays only explicitly recorded canonical lifecycle events. It does not infer that two rows are the same lifecycle from symbol, date, timestamp proximity, price proximity, theme, or recovery confidence.",
        "",
        "## Decision",
        *(_markdown_table(decision)),
        "",
        "## Readiness Audit",
        *(_markdown_table(readiness)),
        "",
        "## Canonical Bucket Audit",
        *(_markdown_table(bucket)),
        "",
        "## Replay Panel Sample",
        *(_markdown_table(replay.head(30))),
        "",
        "## Revalidation Panel Sample",
        *(_markdown_table(panel.head(30))),
        "",
        "## Canonical Event Stream Sample",
        *(_markdown_table(stream.head(50))),
    ]
    (out_dir / "task_382_canonical_lifecycle_replay_revalidation.md").write_text(
        "\n".join(lines),
        encoding="utf-8-sig",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 382 canonical lifecycle replay revalidation")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--task376-evaluation-path", type=Path, default=TASK_376_EVALUATION_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_canonical_lifecycle_replay_revalidation_382(
        db_path=args.db_path,
        task376_evaluation_path=args.task376_evaluation_path,
    )
    write_canonical_lifecycle_replay_revalidation_382(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
