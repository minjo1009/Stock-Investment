from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_continuation_event_capture_369 import (
    DEFAULT_OUT_DIR,
    ContinuationEventCaptureArtifacts,
    build_continuation_event_capture,
    write_continuation_event_capture,
)


def _metric_map(metrics_df: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["metric_name"]): float(pd.to_numeric(pd.Series([row["metric_value"]]), errors="coerce").fillna(0.0).iloc[0])
        for _, row in metrics_df.iterrows()
    }


def _answers(artifacts: ContinuationEventCaptureArtifacts) -> tuple[str, str, str, str, str]:
    metric_map = _metric_map(artifacts.capture_fidelity)
    q1 = str(round(metric_map.get("explicit_event_capture_share", 0.0), 6))

    canonical = artifacts.canonical_events
    q2 = "YES" if (
        not canonical.empty
        and canonical["event_id"].astype(str).ne("").all()
        and canonical["setup_id"].astype(str).ne("").all()
        and canonical["lifecycle_id"].astype(str).ne("").all()
    ) else "NO"

    q3 = "YES" if (
        not canonical.empty
        and canonical["event_type"].astype(str).isin({"ADD_CONFIRMED", "SIZE_INCREASE", "PERSISTENCE_CONFIRMED"}).any()
        and pd.to_numeric(canonical["add_depth"], errors="coerce").fillna(0.0).gt(0).any()
        and pd.to_numeric(canonical["scale_depth"], errors="coerce").fillna(0.0).gt(0).any()
        and canonical["setup_id"].astype(str).ne("").all()
    ) else "NO"

    snapshots = artifacts.lifecycle_snapshots
    q4 = (
        f"derived={round(metric_map.get('derived_event_capture_share', 0.0), 6)}, "
        f"replay_fallback={round(metric_map.get('replay_fallback_share', 0.0), 6)}, "
        f"explicit_lifecycle_identity={round(metric_map.get('explicit_lifecycle_identity_share', 0.0), 6)}"
    )

    if metric_map.get("explicit_setup_identity_share", 0.0) < 0.5:
        q5 = "explicit setup identity from raw source data"
    elif metric_map.get("multi_stage_capture_share", 0.0) <= 0:
        q5 = "finer intraday add timestamps"
    elif not snapshots.empty and not snapshots["persistence_depth"].fillna(0).gt(0).any():
        q5 = "event-level liquidity/persistence features"
    else:
        q5 = "dynamic exposure snapshots from true execution state and an execution-timeline simulator"
    return q1, q2, q3, q4, q5


def _write_report(out_dir: Path, artifacts: ContinuationEventCaptureArtifacts) -> None:
    q1, q2, q3, q4, q5 = _answers(artifacts)
    lines = [
        "# Task 369 - Explicit Continuation Event Capture Architecture",
        "",
        "## Core Answers",
        f"1. How much continuation lifecycle is now explicitly capturable rather than reconstructed? {q1}",
        f"2. Can the system now represent continuation as explicit lifecycle events with stable ids? {q2}",
        f"3. Can add/scale/persistence now be attached to explicit lifecycle identity? {q3}",
        f"4. How much of the current architecture still depends on derived or replay fallback identity? {q4}",
        f"5. What is still missing before true real-time continuation compounding research becomes possible? {q5}",
        "",
        "## Capture Fidelity",
        *(_markdown_table(artifacts.capture_fidelity)),
        "",
        "## Event Source Summary",
        *(_markdown_table(artifacts.event_source_summary)),
        "",
        "## Identity Origin Summary",
        *(_markdown_table(artifacts.identity_origin_summary)),
        "",
        "## Canonical Events",
        *(_markdown_table(artifacts.canonical_events.head(25))),
        "",
        "## Lifecycle Identity",
        *(_markdown_table(artifacts.lifecycle_identity.head(25))),
        "",
        "## Lifecycle Snapshots",
        *(_markdown_table(artifacts.lifecycle_snapshots.head(25))),
    ]
    (out_dir / "task_369_event_capture.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 369: explicit continuation event capture")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_continuation_event_capture()
    out_dir = args.out_dir
    write_continuation_event_capture(artifacts, out_dir)
    _write_report(out_dir, artifacts)


if __name__ == "__main__":
    main()
