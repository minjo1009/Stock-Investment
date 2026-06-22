from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_source_time_capture_371 import (
    DEFAULT_OUT_DIR,
    SourceTimeCapture371Artifacts,
    build_source_time_capture_371,
    write_source_time_capture_371,
)


def _metric_map(metrics_df: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["metric_name"]): float(pd.to_numeric(pd.Series([row["metric_value"]]), errors="coerce").fillna(0.0).iloc[0])
        for _, row in metrics_df.iterrows()
    }


def _write_report(out_dir: Path, artifacts: SourceTimeCapture371Artifacts) -> None:
    metrics = _metric_map(artifacts.capture_fidelity)
    lines = [
        "# Task 371 - Paper Runtime Source Capture Rollout & Coverage Expansion",
        "",
        "## Core Findings",
        f"- source_rows_recorded: {int(metrics.get('source_rows_recorded', 0.0))}",
        f"- lifecycles_recorded: {int(metrics.get('lifecycles_recorded', 0.0))}",
        f"- full_lifecycle_sample_count: {int(metrics.get('full_lifecycle_sample_count', 0.0))}",
        f"- blocked_invalidation_sample_count: {int(metrics.get('blocked_invalidation_sample_count', 0.0))}",
        f"- filled_add_sample_count: {int(metrics.get('filled_add_sample_count', 0.0))}",
        f"- persistence_sample_count: {int(metrics.get('persistence_sample_count', 0.0))}",
        f"- weakening_sample_count: {int(metrics.get('weakening_sample_count', 0.0))}",
        f"- terminal_sample_count: {int(metrics.get('terminal_sample_count', 0.0))}",
        f"- identifier_linkage_completeness: {round(metrics.get('identifier_linkage_completeness', 0.0), 6)}",
        f"- source_captured_share: {round(metrics.get('source_captured_share', 0.0), 6)}",
        "",
        "## Capture Fidelity",
        *(_markdown_table(artifacts.capture_fidelity)),
        "",
        "## Setup Summary",
        *(_markdown_table(artifacts.setup_summary)),
        "",
        "## Recent Source Runs",
        *(_markdown_table(artifacts.recent_source_event_runs.head(25))),
        "",
        "## Lifecycle Completeness",
        *(_markdown_table(artifacts.lifecycle_completeness.head(25))),
        "",
        "## Identifier Linkage",
        *(_markdown_table(artifacts.identifier_linkage)),
        "",
        "## Coverage Gaps",
        *(_markdown_table(artifacts.capture_coverage_gap)),
        "",
        "## Source Event Sample",
        *(_markdown_table(artifacts.source_event_dataset.head(25))),
    ]
    (out_dir / "task_371_source_time_capture.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 371 paper runtime source capture rollout report")
    parser.add_argument("--db-path", type=str, default="trading.db")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_source_time_capture_371(args.db_path)
    write_source_time_capture_371(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
