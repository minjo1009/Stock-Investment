from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_source_truth_replay_dataset_367 import (
    DEFAULT_OUT_DIR,
    SourceTruthReplayArtifacts,
    build_source_truth_replay_dataset,
    write_source_truth_replay_dataset,
)


def _metric_map(metrics_df: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["metric_name"]): float(pd.to_numeric(pd.Series([row["metric_value"]]), errors="coerce").fillna(0.0).iloc[0])
        for _, row in metrics_df.iterrows()
    }


def _ordered_sequence_count(dataset_df: pd.DataFrame, required: list[str], lineage_quality_allowed: set[str]) -> int:
    count = 0
    for _, group in dataset_df.groupby("continuation_id", dropna=False, sort=False):
        quality = str(group["lineage_quality"].iloc[0]) if "lineage_quality" in group.columns and not group.empty else ""
        if quality not in lineage_quality_allowed:
            continue
        ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable")
        event_types = ordered["event_type"].astype(str).tolist()
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


def _healthy_depth_summary(dataset_df: pd.DataFrame) -> tuple[float, float, float, float]:
    setup_rows = dataset_df[dataset_df["event_type"].astype(str).eq("SETUP")].copy()
    healthy_ids = set(
        setup_rows.loc[setup_rows["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION"), "continuation_id"].astype(str)
    )
    if not healthy_ids:
        return 0.0, 0.0, 0.0, 0.0

    scoped = dataset_df[dataset_df["continuation_id"].astype(str).isin(healthy_ids)].copy()
    depth_by_id = scoped.groupby("continuation_id", dropna=False)["event_id"].size()
    event_sets = scoped.groupby("continuation_id", dropna=False)["event_type"].agg(lambda values: set(values.astype(str)))
    denominator = max(len(healthy_ids), 1)
    return (
        float(depth_by_id.max()) if not depth_by_id.empty else 0.0,
        float(sum("ADD_CONFIRMED" in events for events in event_sets) / denominator),
        float(sum("SIZE_INCREASE" in events for events in event_sets) / denominator),
        float(sum("PERSISTENCE_CONFIRMED" in events for events in event_sets) / denominator),
    )


def _answers(artifacts: SourceTruthReplayArtifacts) -> tuple[str, str, str, str, str]:
    metric_map = _metric_map(artifacts.replay_fidelity)
    dataset_df = artifacts.source_truth_replay_dataset
    source_linked_share = metric_map.get("source_linked_continuation_share", 0.0)
    q1 = str(round(source_linked_share, 6))
    q2 = "YES" if _ordered_sequence_count(
        dataset_df,
        ["PROBE_ENTRY", "ADD_CONFIRMED"],
        {"source_truth", "mixed"},
    ) > 0 else "NO"

    max_depth, add_share, scale_share, persist_share = _healthy_depth_summary(dataset_df)
    q3 = f"max_depth={round(max_depth, 6)}, add={round(add_share, 6)}, scale={round(scale_share, 6)}, persist={round(persist_share, 6)}"

    probe_to_add = _ordered_sequence_count(dataset_df, ["PROBE_ENTRY", "ADD_CONFIRMED"], {"source_truth", "mixed"})
    probe_to_add_to_scale = _ordered_sequence_count(dataset_df, ["PROBE_ENTRY", "ADD_CONFIRMED", "SIZE_INCREASE"], {"source_truth", "mixed"})
    probe_to_add_to_scale_to_persist = _ordered_sequence_count(
        dataset_df,
        ["PROBE_ENTRY", "ADD_CONFIRMED", "SIZE_INCREASE", "PERSISTENCE_CONFIRMED"],
        {"source_truth", "mixed"},
    )
    q4 = (
        f"probe_add={probe_to_add}, "
        f"probe_add_scale={probe_to_add_to_scale}, "
        f"probe_add_scale_persist={probe_to_add_to_scale_to_persist}"
    )

    if source_linked_share < 0.5:
        q5 = "explicit multi-event setup identity from source"
    elif probe_to_add_to_scale_to_persist <= 0:
        q5 = "finer intraday add timestamps"
    elif metric_map.get("multi_stage_continuation_share", 0.0) < 0.5:
        q5 = "event-level liquidity/persistence features"
    else:
        q5 = "dynamic exposure snapshots from true execution state and an execution-timeline simulator"
    return q1, q2, q3, q4, q5


def _write_report(out_dir: Path, artifacts: SourceTruthReplayArtifacts) -> None:
    q1, q2, q3, q4, q5 = _answers(artifacts)
    lines = [
        "# Task 367 - Source-Truth Continuation Event Reconstruction",
        "",
        "## Core Answers",
        f"1. How much replay continuity is now source-linked rather than synthetic? {q1}",
        f"2. Can continuation now be reconstructed as true multi-stage event evolution? {q2}",
        f"3. How deep do healthy continuation sequences actually become? {q3}",
        f"4. How often does PROBE -> ADD -> SCALE -> PERSIST actually occur? {q4}",
        f"5. What is still missing before realistic continuation compounding research becomes possible? {q5}",
        "",
        "## Replay Fidelity",
        *(_markdown_table(artifacts.replay_fidelity)),
        "",
        "## Continuation Depth",
        *(_markdown_table(artifacts.continuation_depth)),
        "",
        "## Continuation Lineage",
        *(_markdown_table(artifacts.continuation_lineage.head(25))),
        "",
        "## Event Lineage",
        *(_markdown_table(artifacts.event_lineage.head(25))),
    ]
    (out_dir / "task_367_source_truth_replay.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 367: source-truth continuation replay")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_source_truth_replay_dataset()
    out_dir = args.out_dir
    write_source_truth_replay_dataset(artifacts, out_dir)
    _write_report(out_dir, artifacts)


if __name__ == "__main__":
    main()
