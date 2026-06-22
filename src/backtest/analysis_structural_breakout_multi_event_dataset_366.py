from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_multi_event_replay_dataset_366 import (
    DEFAULT_OUT_DIR,
    MultiEventReplayDatasetArtifacts,
    build_multi_event_replay_dataset,
    write_multi_event_replay_dataset,
)


def _transition_count(exposure_df: pd.DataFrame, from_label: str, to_label: str) -> int:
    if exposure_df.empty:
        return 0
    scoped = exposure_df.sort_values(["continuation_id", "timestamp", "event_id"], kind="stable").copy()
    scoped["previous_quality_label"] = scoped.groupby("continuation_id")["participation_quality_label"].shift(1)
    return int(
        (
            scoped["previous_quality_label"].astype(str).eq(from_label)
            & scoped["participation_quality_label"].astype(str).eq(to_label)
        ).sum()
    )


def _core_metrics(artifacts: MultiEventReplayDatasetArtifacts) -> pd.DataFrame:
    events_df = artifacts.multi_event_replay_dataset
    timelines_df = artifacts.event_timelines
    exposure_df = artifacts.exposure_evolution

    healthy_start_ids = set(
        events_df[events_df["event_type"].astype(str).eq("SETUP")]
        .loc[lambda df: df["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION"), "continuation_id"]
        .astype(str)
    )
    scaled_ids = set(
        events_df[events_df["event_type"].astype(str).eq("SIZE_INCREASE")]["continuation_id"].astype(str)
    )

    metrics = [
        ("continuation_count", float(events_df["continuation_id"].astype(str).nunique()) if not events_df.empty else 0.0),
        ("multi_event_continuation_count", float(pd.to_numeric(timelines_df["event_count"], errors="coerce").fillna(0.0).gt(1).sum()) if not timelines_df.empty else 0.0),
        ("max_event_count", float(pd.to_numeric(timelines_df["event_count"], errors="coerce").fillna(0.0).max()) if not timelines_df.empty else 0.0),
        ("avg_event_count", float(pd.to_numeric(timelines_df["event_count"], errors="coerce").fillna(0.0).mean()) if not timelines_df.empty else 0.0),
        ("sequential_add_count", float(events_df["event_type"].astype(str).eq("ADD_CONFIRMED").sum()) if not events_df.empty else 0.0),
        ("scaling_progression_count", float(events_df["event_type"].astype(str).eq("SIZE_INCREASE").sum()) if not events_df.empty else 0.0),
        ("reduction_progression_count", float(events_df["event_type"].astype(str).eq("REDUCTION_TRIGGER").sum()) if not events_df.empty else 0.0),
        ("persist_duration_positive_count", float(pd.to_numeric(timelines_df["persistence_duration_minutes"], errors="coerce").fillna(0.0).gt(0).sum()) if not timelines_df.empty else 0.0),
        ("healthy_start_scale_rate", float(sum(1 for continuation_id in healthy_start_ids if continuation_id in scaled_ids) / max(len(healthy_start_ids), 1))),
        ("healthy_to_neutral_count", float(_transition_count(exposure_df, "HEALTHY_EXPANSION", "NEUTRAL_PARTICIPATION"))),
        ("healthy_to_fragile_count", float(_transition_count(exposure_df, "HEALTHY_EXPANSION", "FRAGILE_CROWDING"))),
        ("fragile_to_invalidation_count", float(events_df.loc[
            events_df["event_type"].astype(str).eq("INVALIDATION")
            & events_df["participation_quality_label"].astype(str).eq("FRAGILE_CROWDING")
        ].shape[0]) if not events_df.empty else 0.0),
        ("max_cumulative_add_count", float(pd.to_numeric(exposure_df["cumulative_add_count"], errors="coerce").fillna(0.0).max()) if not exposure_df.empty else 0.0),
    ]
    return pd.DataFrame([{"metric_name": name, "metric_value": round(value, 6)} for name, value in metrics])


def _answers(artifacts: MultiEventReplayDatasetArtifacts, metrics_df: pd.DataFrame) -> tuple[str, str, str, str, str]:
    metric_map = {
        str(row["metric_name"]): float(pd.to_numeric(pd.Series([row["metric_value"]]), errors="coerce").fillna(0.0).iloc[0])
        for _, row in metrics_df.iterrows()
    }
    q1 = "YES" if metric_map.get("multi_event_continuation_count", 0.0) > 0 else "NO"
    q2 = "YES" if metric_map.get("sequential_add_count", 0.0) > 0 and metric_map.get("persist_duration_positive_count", 0.0) > 0 else "NO"
    q3 = str(metric_map.get("healthy_start_scale_rate", 0.0))
    q4 = "YES" if (
        metric_map.get("healthy_to_neutral_count", 0.0) > 0
        or metric_map.get("healthy_to_fragile_count", 0.0) > 0
        or metric_map.get("fragile_to_invalidation_count", 0.0) > 0
    ) else "NO"

    unmatched_count = 0
    if not artifacts.setup_frame.empty and "setup_type" in artifacts.setup_frame.columns:
        unmatched_count = int(artifacts.setup_frame["setup_type"].astype(str).eq("unmatched_shadow_only").sum())
    if unmatched_count > 0:
        q5 = "explicit multi-event setup identity from source data"
    elif metric_map.get("sequential_add_count", 0.0) <= 0:
        q5 = "finer intraday add timestamps"
    elif metric_map.get("persist_duration_positive_count", 0.0) <= 0:
        q5 = "event-level liquidity/persistence features"
    else:
        q5 = "dynamic exposure snapshots from true execution state and an execution-timeline simulator"
    return q1, q2, q3, q4, q5


def _write_report(
    out_dir: Path,
    artifacts: MultiEventReplayDatasetArtifacts,
    metrics_df: pd.DataFrame,
) -> None:
    q1, q2, q3, q4, q5 = _answers(artifacts, metrics_df)
    lines = [
        "# Task 366 - Explicit Continuation Event Instrumentation & Multi-Event Replay Dataset",
        "",
        "## Core Answers",
        f"1. Can continuation now be represented as multi-event sequences? {q1}",
        f"2. Do event timelines now show persistence / sequential adds / scaling progression / reduction progression? {q2}",
        f"3. How often do HEALTHY_EXPANSION sequences survive long enough to scale? {q3}",
        f"4. Can continuation now evolve HEALTHY -> NEUTRAL / HEALTHY -> FRAGILE / FRAGILE -> INVALIDATE over time? {q4}",
        f"5. What data is still missing before realistic continuation compounding research becomes possible? {q5}",
        "",
        "## Core Metrics",
        *(_markdown_table(metrics_df)),
        "",
        "## Setup Identity Summary",
        *(_markdown_table(artifacts.setup_identity_summary)),
        "",
        "## Intraday Event Summary",
        *(_markdown_table(artifacts.intraday_event_summary)),
        "",
        "## Event Timelines",
        *(_markdown_table(artifacts.event_timelines.head(25))),
        "",
        "## Exposure Evolution",
        *(_markdown_table(artifacts.exposure_evolution.head(25))),
    ]
    (out_dir / "task_366_multi_event_dataset.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 366: multi-event continuation replay dataset")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_multi_event_replay_dataset()
    out_dir = args.out_dir
    write_multi_event_replay_dataset(artifacts, out_dir)
    metrics_df = _core_metrics(artifacts)
    _write_report(out_dir, artifacts, metrics_df)


if __name__ == "__main__":
    main()
