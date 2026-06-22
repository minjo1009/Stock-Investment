from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_source_time_capture_370 import (
    DEFAULT_OUT_DIR,
    SourceTimeCaptureArtifacts,
    build_source_time_capture,
    write_source_time_capture,
)


def _metric_map(metrics_df: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["metric_name"]): float(pd.to_numeric(pd.Series([row["metric_value"]]), errors="coerce").fillna(0.0).iloc[0])
        for _, row in metrics_df.iterrows()
    }


def _write_report(out_dir: Path, artifacts: SourceTimeCaptureArtifacts) -> None:
    metric_map = _metric_map(artifacts.capture_fidelity)
    lines = [
        "# Task 370 - Source-Time Continuation Lifecycle Capture",
        "",
        "## Core Findings",
        f"- explicit_setup_identity_share: {round(metric_map.get('explicit_setup_identity_share', 0.0), 6)}",
        f"- explicit_lifecycle_identity_share: {round(metric_map.get('explicit_lifecycle_identity_share', 0.0), 6)}",
        f"- parent_linkage_share: {round(metric_map.get('parent_linkage_share', 0.0), 6)}",
        f"- add_confirm_share: {round(metric_map.get('add_confirm_share', 0.0), 6)}",
        f"- scale_up_share: {round(metric_map.get('scale_up_share', 0.0), 6)}",
        f"- persistence_confirm_share: {round(metric_map.get('persistence_confirm_share', 0.0), 6)}",
        f"- terminal_invalidation_share: {round(metric_map.get('terminal_invalidation_share', 0.0), 6)}",
        f"- source_captured_share: {round(metric_map.get('source_captured_share', 0.0), 6)}",
        f"- derived_share: {round(metric_map.get('derived_share', 0.0), 6)}",
        "",
        "## Capture Fidelity",
        *(_markdown_table(artifacts.capture_fidelity)),
        "",
        "## Setup Summary",
        *(_markdown_table(artifacts.setup_summary)),
        "",
        "## Persistence Summary",
        *(_markdown_table(artifacts.persistence_summary.head(25))),
        "",
        "## Add Scale Summary",
        *(_markdown_table(artifacts.add_scale_summary.head(25))),
        "",
        "## Source Event Sample",
        *(_markdown_table(artifacts.source_event_dataset.head(25))),
    ]
    (out_dir / "task_370_source_time_capture.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 370 source-time continuation lifecycle capture")
    parser.add_argument("--db-path", type=str, default="trading.db")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_source_time_capture(args.db_path)
    write_source_time_capture(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
