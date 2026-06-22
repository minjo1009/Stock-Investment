from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_shadow_integration_360 import generate_shadow_artifacts
from src.backtest.continuation_event_chain import (
    build_chain_summary_metrics,
    build_continuation_event_chains,
    build_continuation_evolution_snapshots,
    build_event_transition_summary,
    build_exit_reason_summary,
    build_quality_evolution_summary,
    build_size_evolution_summary,
    summarize_event_chains,
)
from src.backtest.continuation_event_identity import build_continuation_events, events_to_frame
from src.backtest.continuation_lifecycle_replay import run_lifecycle_replay


DEFAULT_OUT_DIR = Path("docs/reports/task_365_event_lifecycle")


def _metric_value(metrics_df: pd.DataFrame, metric_name: str, default: float = 0.0) -> float:
    scoped = metrics_df[metrics_df["metric_name"].astype(str) == metric_name]
    if scoped.empty:
        return default
    return float(pd.to_numeric(scoped["metric_value"], errors="coerce").fillna(default).iloc[0])


def _answers(event_chains_df: pd.DataFrame, chain_summary_df: pd.DataFrame, evolution_df: pd.DataFrame, metrics_df: pd.DataFrame) -> tuple[str, str, str, str, str]:
    q1 = "YES" if not chain_summary_df.empty and int(pd.to_numeric(chain_summary_df["event_count"], errors="coerce").fillna(0.0).max()) > 1 else "NO"
    probe_ids = set(evolution_df[evolution_df["event_type"].astype(str).eq("PROBE_ENTRY")]["continuation_id"].astype(str))
    progressed_ids = set(
        evolution_df[evolution_df["event_type"].astype(str).isin({"ADD", "SCALE_UP", "PERSIST"})]["continuation_id"].astype(str)
    )
    q2 = "YES" if any(continuation_id in progressed_ids for continuation_id in probe_ids) else "NO"
    q3 = str(_metric_value(metrics_df, "healthy_to_fragile_transition_rate", 0.0))
    q4 = "YES" if not chain_summary_df.empty and bool(pd.to_numeric(chain_summary_df["persistence_duration_events"], errors="coerce").fillna(0.0).gt(0).any()) else "NO"
    if q1 == "NO" or event_chains_df.empty:
        q5 = "explicit multi-event setup identity"
    elif q4 == "NO":
        q5 = "intraday add timestamps and event-level liquidity/persistence fields"
    else:
        q5 = "dynamic exposure snapshots and execution-timeline simulator"
    return q1, q2, q3, q4, q5


def _report(
    out_dir: Path,
    event_chains_df: pd.DataFrame,
    transitions_df: pd.DataFrame,
    quality_df: pd.DataFrame,
    size_df: pd.DataFrame,
    exit_df: pd.DataFrame,
    chain_summary_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
) -> None:
    evolution_df = quality_df.merge(
        size_df[["continuation_id", "event_index", "event_type"]],
        on=["continuation_id", "event_index"],
        how="left",
    )
    q1, q2, q3, q4, q5 = _answers(event_chains_df, chain_summary_df, evolution_df, metrics_df)
    lines = [
        "# Task 365 - Event-Level Continuation Lifecycle Enrichment",
        "",
        "## Core Answers",
        f"1. Can continuation now be represented as linked event chains rather than isolated rows? {q1}",
        f"2. Do healthy continuation sequences now show probe / add / persistence / scale behavior? {q2}",
        f"3. How often does HEALTHY_EXPANSION evolve into FRAGILE_CROWDING? {q3}",
        f"4. Can continuation persistence now be measured across time? {q4}",
        f"5. What data is still missing before realistic continuation compounding research becomes possible? {q5}",
        "",
        "## Chain Summary Metrics",
        *(_markdown_table(metrics_df)),
        "",
        "## Event Chains",
        *(_markdown_table(event_chains_df.head(25))),
        "",
        "## Event Transitions",
        *(_markdown_table(transitions_df.head(25))),
        "",
        "## Quality Evolution",
        *(_markdown_table(quality_df.head(25))),
        "",
        "## Size Evolution",
        *(_markdown_table(size_df.head(25))),
        "",
        "## Exit Reasons",
        *(_markdown_table(exit_df)),
        "",
        "## Chain Summary",
        *(_markdown_table(chain_summary_df.head(25))),
    ]
    (out_dir / "task_365_event_lifecycle.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 365: event-level continuation lifecycle enrichment")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = generate_shadow_artifacts(enable_shadow_state_engine=True)
    shadow_log = artifacts.shadow_log.copy()
    lifecycle_rows_df, replay_trace_df, _transition_matrix_df, _lifecycle_summary_df = run_lifecycle_replay(shadow_log)
    events = build_continuation_events(replay_trace_df, lifecycle_rows_df)
    event_chains = build_continuation_event_chains(events, replay_trace_df, lifecycle_rows_df)
    evolution_df = build_continuation_evolution_snapshots(replay_trace_df, lifecycle_rows_df)
    chain_summary_df = summarize_event_chains(event_chains, evolution_df)
    transitions_df = build_event_transition_summary(evolution_df)
    quality_df = build_quality_evolution_summary(evolution_df)
    size_df = build_size_evolution_summary(evolution_df)
    exit_df = build_exit_reason_summary(chain_summary_df)
    metrics_df = build_chain_summary_metrics(chain_summary_df, evolution_df)
    event_chains_df = events_to_frame(events).sort_values(["continuation_id", "event_index"], kind="stable").reset_index(drop=True)

    event_chains_df.to_csv(out_dir / "task_365_event_chains.csv", index=False)
    transitions_df.to_csv(out_dir / "task_365_event_transitions.csv", index=False)
    quality_df.to_csv(out_dir / "task_365_quality_evolution.csv", index=False)
    size_df.to_csv(out_dir / "task_365_size_evolution.csv", index=False)
    exit_df.to_csv(out_dir / "task_365_exit_reasons.csv", index=False)
    chain_summary_df.to_csv(out_dir / "task_365_chain_summary.csv", index=False)
    _report(out_dir, event_chains_df, transitions_df, quality_df, size_df, exit_df, chain_summary_df, metrics_df)


if __name__ == "__main__":
    main()
