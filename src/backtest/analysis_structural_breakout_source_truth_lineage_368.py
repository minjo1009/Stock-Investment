from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_source_truth_lineage_368 import (
    DEFAULT_OUT_DIR,
    SourceTruthLineageArtifacts,
    build_source_truth_lineage_dataset,
    write_source_truth_lineage_dataset,
)


def _metric_map(metrics_df: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["metric_name"]): float(pd.to_numeric(pd.Series([row["metric_value"]]), errors="coerce").fillna(0.0).iloc[0])
        for _, row in metrics_df.iterrows()
    }


def _ordered_sequence_count(lineage_rows_df: pd.DataFrame, required: list[str], allowed_quality: set[str]) -> int:
    count = 0
    for _, group in lineage_rows_df.groupby("continuation_id", dropna=False, sort=False):
        quality = str(group["lineage_quality"].iloc[0]) if not group.empty else ""
        if quality not in allowed_quality:
            continue
        event_types = group.sort_values(["timestamp", "event_id"], kind="stable")["lineage_event_type"].astype(str).tolist()
        cursor = 0
        matched = True
        for needle in required:
            try:
                cursor = event_types.index(needle, cursor) + 1
            except ValueError:
                matched = False
                break
        if matched:
            count += 1
    return count


def _answers(artifacts: SourceTruthLineageArtifacts) -> tuple[str, str, str, str, str]:
    metric_map = _metric_map(artifacts.replay_fidelity)
    q1 = str(round(metric_map.get("source_truth_lineage_share", 0.0), 6))
    q2 = "YES" if _ordered_sequence_count(
        artifacts.lineage_rows,
        ["SETUP_DETECTED", "PROBE_ENTRY", "ADD_CONFIRMED"],
        {"source_truth", "mixed"},
    ) > 0 else "NO"

    add_scale_summary = artifacts.lineage_summary.copy()
    q3 = "YES" if (
        pd.to_numeric(add_scale_summary.get("final_add_depth"), errors="coerce").fillna(0.0).gt(0).any()
        and pd.to_numeric(add_scale_summary.get("final_scale_depth"), errors="coerce").fillna(0.0).gt(0).any()
        and add_scale_summary["setup_id"].astype(str).ne("").any()
    ) else "NO"

    q4 = "YES" if (
        pd.to_numeric(artifacts.persistence_summary.get("persistence_duration_minutes"), errors="coerce").fillna(0.0).gt(0.0).any()
        and pd.to_numeric(artifacts.persistence_summary.get("persistence_depth"), errors="coerce").fillna(0.0).gt(0.0).any()
    ) else "NO"

    if metric_map.get("source_truth_lineage_share", 0.0) < 0.5:
        q5 = "explicit setup identity from raw source data"
    elif not q3 == "YES":
        q5 = "finer intraday add timestamps"
    elif metric_map.get("multi_stage_lineage_share", 0.0) < 0.5:
        q5 = "event-level liquidity/persistence features"
    else:
        q5 = "dynamic exposure snapshots from true execution state and an execution-timeline simulator"
    return q1, q2, q3, q4, q5


def _write_report(out_dir: Path, artifacts: SourceTruthLineageArtifacts) -> None:
    q1, q2, q3, q4, q5 = _answers(artifacts)
    lines = [
        "# Task 368 - Source-Truth Continuation Lineage Reconstruction",
        "",
        "## Core Answers",
        f"1. How much continuation replay is now explicitly source-linked? {q1}",
        f"2. Can continuation now be reconstructed as true multi-stage lineage? {q2}",
        f"3. Can add/scale progression now be linked to explicit setup lineage? {q3}",
        f"4. Can continuation persistence now be measured as true lineage evolution? {q4}",
        f"5. What is still missing before realistic continuation compounding research becomes possible? {q5}",
        "",
        "## Replay Fidelity",
        *(_markdown_table(artifacts.replay_fidelity)),
        "",
        "## Setup Identity Summary",
        *(_markdown_table(artifacts.setup_identity_summary)),
        "",
        "## Lineage Summary",
        *(_markdown_table(artifacts.lineage_summary.head(25))),
        "",
        "## Add/Scale Evolution",
        *(_markdown_table(artifacts.add_scale_evolution.head(25))),
        "",
        "## Persistence Timeline",
        *(_markdown_table(artifacts.persistence_timeline.head(25))),
    ]
    (out_dir / "task_368_source_truth_lineage.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 368: source-truth continuation lineage")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_source_truth_lineage_dataset()
    out_dir = args.out_dir
    write_source_truth_lineage_dataset(artifacts, out_dir)
    _write_report(out_dir, artifacts)


if __name__ == "__main__":
    main()
