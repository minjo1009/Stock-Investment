from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH
from src.state.store import (
    initialize_store,
    list_continuation_lifecycles,
    list_continuation_setups,
    list_continuation_source_events,
    summarize_continuation_capture_coverage,
    summarize_continuation_lifecycle_completeness,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_371_source_time_capture")


@dataclass(frozen=True)
class SourceTimeCapture371Artifacts:
    source_event_dataset: pd.DataFrame
    lifecycle_identity: pd.DataFrame
    recent_source_event_runs: pd.DataFrame
    lifecycle_completeness: pd.DataFrame
    identifier_linkage: pd.DataFrame
    capture_coverage_gap: pd.DataFrame
    capture_fidelity: pd.DataFrame
    setup_summary: pd.DataFrame


def build_source_time_capture_371(db_path: str = str(DB_PATH)) -> SourceTimeCapture371Artifacts:
    initialize_store(db_path)
    events_df = pd.DataFrame(list_continuation_source_events(db_path, limit=100000))
    lifecycle_df = pd.DataFrame(list_continuation_lifecycles(db_path, limit=100000))
    setup_df = pd.DataFrame(list_continuation_setups(db_path, limit=100000))
    lifecycle_completeness = pd.DataFrame(summarize_continuation_lifecycle_completeness(db_path, limit=100000))
    coverage_metrics = summarize_continuation_capture_coverage(db_path)

    if not events_df.empty:
        events_df["event_timestamp"] = pd.to_datetime(events_df["event_timestamp"], errors="coerce", utc=True)
        events_df = events_df.sort_values(["event_timestamp", "source_event_id"], kind="stable").reset_index(drop=True)
    if not lifecycle_df.empty:
        lifecycle_df["started_at"] = pd.to_datetime(lifecycle_df["started_at"], errors="coerce", utc=True)
        lifecycle_df["ended_at"] = pd.to_datetime(lifecycle_df["ended_at"], errors="coerce", utc=True)
    if not setup_df.empty:
        setup_df["setup_timestamp"] = pd.to_datetime(setup_df["setup_timestamp"], errors="coerce", utc=True)

    recent_source_event_runs = (
        events_df.groupby("trade_run_id", dropna=False)
        .agg(
            event_count=("source_event_id", "count"),
            lifecycle_count=("lifecycle_id", "nunique"),
            symbol_count=("symbol", "nunique"),
            first_timestamp=("event_timestamp", "min"),
            last_timestamp=("event_timestamp", "max"),
        )
        .reset_index()
        .sort_values(["last_timestamp", "trade_run_id"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
        if not events_df.empty
        else pd.DataFrame(columns=["trade_run_id", "event_count", "lifecycle_count", "symbol_count", "first_timestamp", "last_timestamp"])
    )

    identifier_linkage_rows: list[dict[str, object]] = []
    for field_name in (
        "signal_event_id",
        "risk_decision_id",
        "order_intent_id",
        "order_id",
        "fill_id",
        "reconciliation_id",
        "trade_run_id",
    ):
        if events_df.empty:
            completeness = 0.0
            non_null = 0
            total = 0
        else:
            series = events_df[field_name].fillna("").astype(str).str.strip()
            non_null = int(series.ne("").sum())
            total = int(len(series))
            completeness = float(non_null / total) if total else 0.0
        identifier_linkage_rows.append(
            {
                "field_name": field_name,
                "non_null_count": non_null,
                "row_count": total,
                "completeness": round(completeness, 6),
            }
        )
    identifier_linkage = pd.DataFrame(identifier_linkage_rows)

    capture_gap_rows = [
        {
            "gap_name": "missing_source_rows",
            "gap_flag": int(coverage_metrics["source_rows_recorded"] <= 0),
            "observed_value": coverage_metrics["source_rows_recorded"],
        },
        {
            "gap_name": "missing_full_lifecycle_sample",
            "gap_flag": int(coverage_metrics["full_lifecycle_sample_count"] <= 0),
            "observed_value": coverage_metrics["full_lifecycle_sample_count"],
        },
        {
            "gap_name": "missing_persistence_sample",
            "gap_flag": int(coverage_metrics["persistence_sample_count"] <= 0),
            "observed_value": coverage_metrics["persistence_sample_count"],
        },
        {
            "gap_name": "missing_weakening_sample",
            "gap_flag": int(coverage_metrics["weakening_sample_count"] <= 0),
            "observed_value": coverage_metrics["weakening_sample_count"],
        },
        {
            "gap_name": "missing_terminal_sample",
            "gap_flag": int(coverage_metrics["terminal_sample_count"] <= 0),
            "observed_value": coverage_metrics["terminal_sample_count"],
        },
    ]
    capture_coverage_gap = pd.DataFrame(capture_gap_rows)

    capture_fidelity = pd.DataFrame(
        [
            {"metric_name": name, "metric_value": round(float(value), 6)}
            for name, value in coverage_metrics.items()
        ]
    )

    setup_summary = (
        setup_df.groupby("setup_origin", dropna=False)
        .agg(
            setup_count=("setup_id", "nunique"),
            symbol_count=("symbol", "nunique"),
            explicit_signal_count=("signal_event_id", lambda values: int(pd.Series(values).fillna("").astype(str).ne("").sum())),
        )
        .reset_index()
        .sort_values(["setup_count", "setup_origin"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
        if not setup_df.empty
        else pd.DataFrame(columns=["setup_origin", "setup_count", "symbol_count", "explicit_signal_count"])
    )

    return SourceTimeCapture371Artifacts(
        source_event_dataset=events_df,
        lifecycle_identity=lifecycle_df,
        recent_source_event_runs=recent_source_event_runs,
        lifecycle_completeness=lifecycle_completeness,
        identifier_linkage=identifier_linkage,
        capture_coverage_gap=capture_coverage_gap,
        capture_fidelity=capture_fidelity,
        setup_summary=setup_summary,
    )


def write_source_time_capture_371(artifacts: SourceTimeCapture371Artifacts, out_dir: Path = DEFAULT_OUT_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.source_event_dataset.to_csv(out_dir / "task_371_source_event_dataset.csv", index=False)
    artifacts.lifecycle_identity.to_csv(out_dir / "task_371_lifecycle_identity.csv", index=False)
    artifacts.recent_source_event_runs.to_csv(out_dir / "task_371_recent_source_event_runs.csv", index=False)
    artifacts.lifecycle_completeness.to_csv(out_dir / "task_371_lifecycle_completeness.csv", index=False)
    artifacts.identifier_linkage.to_csv(out_dir / "task_371_identifier_linkage.csv", index=False)
    artifacts.capture_coverage_gap.to_csv(out_dir / "task_371_capture_coverage_gap.csv", index=False)
    artifacts.capture_fidelity.to_csv(out_dir / "task_371_capture_fidelity.csv", index=False)
    artifacts.setup_summary.to_csv(out_dir / "task_371_setup_summary.csv", index=False)
