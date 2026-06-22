from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH
from src.state.store import (
    initialize_store,
    list_continuation_lifecycles,
    list_continuation_setups,
    list_continuation_snapshots,
    list_continuation_source_events,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_370_source_time_capture")


@dataclass(frozen=True)
class SourceTimeCaptureArtifacts:
    source_event_dataset: pd.DataFrame
    lifecycle_identity: pd.DataFrame
    setup_summary: pd.DataFrame
    persistence_summary: pd.DataFrame
    add_scale_summary: pd.DataFrame
    capture_fidelity: pd.DataFrame


def _events_df(db_path: str) -> pd.DataFrame:
    return pd.DataFrame(list_continuation_source_events(db_path, limit=100000))


def _lifecycles_df(db_path: str) -> pd.DataFrame:
    return pd.DataFrame(list_continuation_lifecycles(db_path, limit=100000))


def _setups_df(db_path: str) -> pd.DataFrame:
    return pd.DataFrame(list_continuation_setups(db_path, limit=100000))


def _snapshots_df(db_path: str) -> pd.DataFrame:
    return pd.DataFrame(list_continuation_snapshots(db_path, limit=100000))


def build_source_time_capture(db_path: str = str(DB_PATH)) -> SourceTimeCaptureArtifacts:
    initialize_store(db_path)
    events_df = _events_df(db_path)
    lifecycle_df = _lifecycles_df(db_path)
    setup_df = _setups_df(db_path)
    snapshot_df = _snapshots_df(db_path)

    if not events_df.empty:
        events_df["event_timestamp"] = pd.to_datetime(events_df["event_timestamp"], errors="coerce", utc=True)
        events_df = events_df.sort_values(["event_timestamp", "source_event_id"], kind="stable").reset_index(drop=True)
    if not lifecycle_df.empty:
        lifecycle_df["started_at"] = pd.to_datetime(lifecycle_df["started_at"], errors="coerce", utc=True)
        lifecycle_df["ended_at"] = pd.to_datetime(lifecycle_df["ended_at"], errors="coerce", utc=True)
    if not setup_df.empty:
        setup_df["setup_timestamp"] = pd.to_datetime(setup_df["setup_timestamp"], errors="coerce", utc=True)
    if not snapshot_df.empty:
        snapshot_df["snapshot_timestamp"] = pd.to_datetime(snapshot_df["snapshot_timestamp"], errors="coerce", utc=True)

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

    persistence_summary = (
        snapshot_df.groupby("lifecycle_id", dropna=False)
        .agg(
            setup_id=("setup_id", "first"),
            persistence_depth=("persistence_depth", "max"),
            weakening_seen=("weakening_flag", lambda values: bool(pd.Series(values).fillna(0).astype(int).max())),
            invalidated_seen=("invalidated_flag", lambda values: bool(pd.Series(values).fillna(0).astype(int).max())),
            first_snapshot=("snapshot_timestamp", "min"),
            last_snapshot=("snapshot_timestamp", "max"),
        )
        .reset_index()
        .assign(
            persistence_duration_minutes=lambda df: (
                (df["last_snapshot"] - df["first_snapshot"]).dt.total_seconds().fillna(0.0) / 60.0
            )
        )
        .sort_values(["persistence_depth", "lifecycle_id"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
        if not snapshot_df.empty
        else pd.DataFrame(
            columns=[
                "lifecycle_id",
                "setup_id",
                "persistence_depth",
                "weakening_seen",
                "invalidated_seen",
                "first_snapshot",
                "last_snapshot",
                "persistence_duration_minutes",
            ]
        )
    )

    add_scale_summary = (
        events_df.groupby("lifecycle_id", dropna=False)
        .agg(
            setup_id=("setup_id", "first"),
            add_depth=("add_depth", "max"),
            scale_depth=("scale_depth", "max"),
            max_size_multiplier=("size_multiplier", "max"),
            add_confirm_count=("event_type", lambda values: int(pd.Series(values).astype(str).eq("ADD_CONFIRMED").sum())),
            scale_up_count=("event_type", lambda values: int(pd.Series(values).astype(str).eq("SIZE_INCREASE").sum())),
        )
        .reset_index()
        .sort_values(["scale_depth", "add_depth", "lifecycle_id"], ascending=[False, False, True], kind="stable")
        .reset_index(drop=True)
        if not events_df.empty
        else pd.DataFrame(
            columns=[
                "lifecycle_id",
                "setup_id",
                "add_depth",
                "scale_depth",
                "max_size_multiplier",
                "add_confirm_count",
                "scale_up_count",
            ]
        )
    )

    lifecycle_count = max(len(lifecycle_df), 1)
    event_count = max(len(events_df), 1)
    explicit_setup_identity_share = float(
        setup_df["setup_origin"].astype(str).eq("explicit_signal_identity").sum() / max(len(setup_df), 1)
    ) if not setup_df.empty else 0.0
    explicit_lifecycle_identity_share = float(
        lifecycle_df["identity_origin"].astype(str).isin(
            {"explicit_signal_identity", "explicit_risk_identity", "explicit_order_fill_identity"}
        ).sum()
        / lifecycle_count
    ) if not lifecycle_df.empty else 0.0
    parent_linkage_share = float(
        lifecycle_df["parent_lifecycle_id"].fillna("").astype(str).ne("").sum() / lifecycle_count
    ) if not lifecycle_df.empty else 0.0
    add_confirm_share = float(
        events_df["event_type"].astype(str).eq("ADD_CONFIRMED").sum() / lifecycle_count
    ) if not events_df.empty else 0.0
    scale_up_share = float(
        events_df["event_type"].astype(str).eq("SIZE_INCREASE").sum() / lifecycle_count
    ) if not events_df.empty else 0.0
    persistence_confirm_share = float(
        events_df["event_type"].astype(str).eq("PERSISTENCE_CONFIRMED").sum() / lifecycle_count
    ) if not events_df.empty else 0.0
    terminal_invalidation_share = float(
        events_df["event_type"].astype(str).eq("INVALIDATION").sum() / lifecycle_count
    ) if not events_df.empty else 0.0
    source_captured_share = float(events_df["event_source"].astype(str).eq("SOURCE_CAPTURED").sum() / event_count) if not events_df.empty else 0.0
    derived_share = float(
        events_df["event_source"].astype(str).isin({"SESSION_DERIVED", "REPLAY_DERIVED"}).sum() / event_count
    ) if not events_df.empty else 0.0

    capture_fidelity = pd.DataFrame(
        [
            {"metric_name": "explicit_setup_identity_share", "metric_value": round(explicit_setup_identity_share, 6)},
            {"metric_name": "explicit_lifecycle_identity_share", "metric_value": round(explicit_lifecycle_identity_share, 6)},
            {"metric_name": "parent_linkage_share", "metric_value": round(parent_linkage_share, 6)},
            {"metric_name": "add_confirm_share", "metric_value": round(add_confirm_share, 6)},
            {"metric_name": "scale_up_share", "metric_value": round(scale_up_share, 6)},
            {"metric_name": "persistence_confirm_share", "metric_value": round(persistence_confirm_share, 6)},
            {"metric_name": "terminal_invalidation_share", "metric_value": round(terminal_invalidation_share, 6)},
            {"metric_name": "source_captured_share", "metric_value": round(source_captured_share, 6)},
            {"metric_name": "derived_share", "metric_value": round(derived_share, 6)},
        ]
    )

    return SourceTimeCaptureArtifacts(
        source_event_dataset=events_df,
        lifecycle_identity=lifecycle_df,
        setup_summary=setup_summary,
        persistence_summary=persistence_summary,
        add_scale_summary=add_scale_summary,
        capture_fidelity=capture_fidelity,
    )


def write_source_time_capture(artifacts: SourceTimeCaptureArtifacts, out_dir: Path = DEFAULT_OUT_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.source_event_dataset.to_csv(out_dir / "task_370_source_event_dataset.csv", index=False)
    artifacts.lifecycle_identity.to_csv(out_dir / "task_370_lifecycle_identity.csv", index=False)
    artifacts.setup_summary.to_csv(out_dir / "task_370_setup_summary.csv", index=False)
    artifacts.persistence_summary.to_csv(out_dir / "task_370_persistence_summary.csv", index=False)
    artifacts.add_scale_summary.to_csv(out_dir / "task_370_add_scale_summary.csv", index=False)
    artifacts.capture_fidelity.to_csv(out_dir / "task_370_capture_fidelity.csv", index=False)
