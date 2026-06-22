from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_shadow_integration_360 import generate_shadow_artifacts
from src.backtest.continuation_lifecycle_replay import (
    build_add_activation_summary,
    build_compounding_diagnostics,
    build_fragility_transition_summary,
    build_replay_state_distribution,
    replay_lifecycle,
    run_lifecycle_replay,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_364_lifecycle_replay")


def _transition_trace(shadow_log: pd.DataFrame) -> pd.DataFrame:
    from src.backtest.continuation_lifecycle_replay import build_continuation_lifecycles

    transition_frames: list[pd.DataFrame] = []
    for lifecycle in build_continuation_lifecycles(shadow_log):
        _replay_df, transition_df = replay_lifecycle(lifecycle)
        transition_frames.append(transition_df)
    return pd.concat(transition_frames, ignore_index=True) if transition_frames else pd.DataFrame()


def _answers(
    lifecycle_summary_df: pd.DataFrame,
    replay_trace_df: pd.DataFrame,
    fragility_transition_df: pd.DataFrame,
) -> tuple[str, str, str, str, str]:
    multi_row_exists = bool((pd.to_numeric(lifecycle_summary_df.get("row_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0) > 1).any())
    persisting_exists = bool(lifecycle_summary_df.get("has_persisting", pd.Series(dtype=bool)).fillna(False).astype(bool).any())
    q1 = "YES" if multi_row_exists and persisting_exists else "NO"

    healthy = replay_trace_df[replay_trace_df["participation_quality_label"].astype(str) == "HEALTHY_EXPANSION"].copy()
    healthy_states = set(healthy["replay_state"].astype(str).tolist())
    q2 = "YES" if {"PROBE", "BUILDING", "PERSISTING"}.issubset(healthy_states) else "NO"

    q3 = "YES" if multi_row_exists and not replay_trace_df[
        replay_trace_df["previous_replay_state"].astype(str).eq("PROBE")
        & replay_trace_df["replay_state"].astype(str).eq("BUILDING")
    ].empty else "NO"

    q4 = "YES" if not fragility_transition_df.empty else "NO"

    if not multi_row_exists:
        q5 = "explicit multi-event setup identity and intraday add timestamps"
    elif q2 == "NO":
        q5 = "richer persistence features and classifier expansion"
    elif q3 == "NO":
        q5 = "dynamic exposure state snapshots and add-timeline detail"
    else:
        q5 = "true execution-timeline simulator"
    return q1, q2, q3, q4, q5


def _report(
    out_dir: Path,
    state_distribution_df: pd.DataFrame,
    lifecycle_summary_df: pd.DataFrame,
    transition_matrix_df: pd.DataFrame,
    add_activation_df: pd.DataFrame,
    compounding_df: pd.DataFrame,
    fragility_transition_df: pd.DataFrame,
    replay_trace_df: pd.DataFrame,
) -> None:
    q1, q2, q3, q4, q5 = _answers(lifecycle_summary_df, replay_trace_df, fragility_transition_df)
    lines = [
        "# Task 364 - Real Lifecycle Replay & Healthy Continuation Compounding Engine Foundation",
        "",
        "## Core Answers",
        f"1. Does lifecycle replay reveal continuation persistence that row-level replay missed? {q1}",
        f"2. Can healthy continuation now transition through PROBE / BUILDING / PERSISTING states? {q2}",
        f"3. Does add activation now occur across replay sequences rather than isolated rows? {q3}",
        f"4. Is fragility transition observable over lifecycle evolution? {q4}",
        f"5. What is still missing before true continuation compounding can be realistically simulated? {q5}",
        "",
        "## Replay State Distribution",
        *(_markdown_table(state_distribution_df)),
        "",
        "## Lifecycle Summary",
        *(_markdown_table(lifecycle_summary_df.head(25))),
        "",
        "## Transition Matrix",
        *(_markdown_table(transition_matrix_df)),
        "",
        "## Add Activation",
        *(_markdown_table(add_activation_df)),
        "",
        "## Compounding Diagnostics",
        *(_markdown_table(compounding_df)),
        "",
        "## Fragility Transition",
        *(_markdown_table(fragility_transition_df)),
    ]
    (out_dir / "task_364_lifecycle_replay.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 364: lifecycle replay and healthy continuation compounding foundation")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = generate_shadow_artifacts(enable_shadow_state_engine=True)
    shadow_log = artifacts.shadow_log.copy()
    _lifecycle_rows_df, replay_trace_df, transition_matrix_df, lifecycle_summary_df = run_lifecycle_replay(shadow_log)
    transition_trace_df = _transition_trace(shadow_log)
    state_distribution_df = build_replay_state_distribution(replay_trace_df)
    add_activation_df = build_add_activation_summary(replay_trace_df)
    compounding_df = build_compounding_diagnostics(replay_trace_df, lifecycle_summary_df, transition_trace_df)
    fragility_transition_df = build_fragility_transition_summary(transition_trace_df)

    state_distribution_df.to_csv(out_dir / "task_364_replay_state_distribution.csv", index=False)
    lifecycle_summary_df.to_csv(out_dir / "task_364_lifecycle_summary.csv", index=False)
    transition_matrix_df.to_csv(out_dir / "task_364_transition_matrix.csv", index=False)
    add_activation_df.to_csv(out_dir / "task_364_add_activation.csv", index=False)
    compounding_df.to_csv(out_dir / "task_364_compounding_diagnostics.csv", index=False)
    fragility_transition_df.to_csv(out_dir / "task_364_fragility_transition.csv", index=False)
    _report(
        out_dir,
        state_distribution_df,
        lifecycle_summary_df,
        transition_matrix_df,
        add_activation_df,
        compounding_df,
        fragility_transition_df,
        replay_trace_df,
    )


if __name__ == "__main__":
    main()
