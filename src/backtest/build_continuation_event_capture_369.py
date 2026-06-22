from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _prepare_corrected_entry_master
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH, _load_intraday_bars
from src.backtest.build_multi_event_replay_dataset_366 import (
    MultiEventReplayDatasetArtifacts,
    build_multi_event_replay_dataset,
)
from src.backtest.build_source_truth_lineage_368 import (
    SourceTruthLineageArtifacts,
    build_source_truth_lineage_dataset,
)
from src.backtest.build_source_truth_replay_dataset_367 import SourceTruthReplayArtifacts, build_source_truth_replay_dataset
from src.backtest.continuation_event_schema import EVENT_SOURCE_TYPES
from src.backtest.continuation_lifecycle_identity import build_continuation_lifecycle_identity


DEFAULT_OUT_DIR = Path("docs/reports/task_369_event_capture")


@dataclass(frozen=True)
class ContinuationEventCaptureArtifacts:
    canonical_events: pd.DataFrame
    lifecycle_identity: pd.DataFrame
    lifecycle_snapshots: pd.DataFrame
    event_source_summary: pd.DataFrame
    identity_origin_summary: pd.DataFrame
    capture_fidelity: pd.DataFrame
    upstream_368: SourceTruthLineageArtifacts
    upstream_367: SourceTruthReplayArtifacts
    upstream_366: MultiEventReplayDatasetArtifacts


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(numeric):
        return float(default)
    return numeric


def _canonical_event_source(lineage_event_source: str, identity_origin: str, lineage_quality: str) -> str:
    if identity_origin in {"explicit_setup_identity", "explicit_trade_identity", "explicit_session_identity"} and lineage_event_source == "SOURCE_TRUTH":
        return "SOURCE_CAPTURED"
    if identity_origin == "derived_session_continuity" or lineage_event_source == "SHADOW_INFERRED" or lineage_quality == "mixed":
        return "SESSION_DERIVED"
    return "REPLAY_DERIVED"


def _build_canonical_events(
    lineage_rows_df: pd.DataFrame,
    add_scale_evolution_df: pd.DataFrame,
    lifecycle_identity_df: pd.DataFrame,
    event_identity_df: pd.DataFrame,
) -> pd.DataFrame:
    frame = lineage_rows_df.copy()
    if frame.empty:
        return pd.DataFrame()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.sort_values(
        ["symbol", "session_date", "timestamp", "event_index", "event_id"],
        kind="stable",
    ).reset_index(drop=True)
    frame["event_rank_within_lifecycle"] = frame.groupby("continuation_id", dropna=False).cumcount() + 1
    frame = frame.merge(
        add_scale_evolution_df[
            [
                "continuation_id",
                "event_id",
                "add_depth",
                "scale_depth",
                "cumulative_size_multiplier",
            ]
        ],
        on=["continuation_id", "event_id"],
        how="left",
        suffixes=("", "_addscale"),
    ).merge(
        lifecycle_identity_df[
            [
                "lifecycle_id",
                "identity_origin",
                "identity_confidence",
                "parent_lifecycle_id",
                "setup_id",
            ]
        ],
        left_on="continuation_id",
        right_on="lifecycle_id",
        how="left",
        suffixes=("", "_identity"),
    ).merge(
        event_identity_df[
            [
                "continuation_id",
                "canonical_event_id",
                "event_rank_within_lifecycle",
            ]
        ],
        on=["continuation_id", "event_rank_within_lifecycle"],
        how="left",
    )

    frame["canonical_event_rank"] = frame.groupby("lifecycle_id", dropna=False).cumcount() + 1
    frame["canonical_event_id"] = frame["canonical_event_id"].where(
        frame["canonical_event_id"].notna(),
        frame.apply(
            lambda row: f"{_safe_text(row.get('lifecycle_id'), 'unknown_lifecycle')}|evt_{int(_safe_float(row.get('canonical_event_rank'), 1)):03d}",
            axis=1,
        ),
    )
    frame["event_source"] = frame.apply(
        lambda row: _canonical_event_source(
            _safe_text(row.get("event_source"), "REPLAY_INFERRED"),
            _safe_text(row.get("identity_origin"), "replay_fallback_identity"),
            _safe_text(row.get("lineage_quality"), "synthetic_only"),
        ),
        axis=1,
    )
    if "setup_id_identity" in frame.columns:
        frame["setup_id"] = frame["setup_id_identity"].where(frame["setup_id_identity"].notna(), frame["setup_id"])
    frame["size_multiplier_canonical"] = pd.to_numeric(
        frame.get("cumulative_size_multiplier", frame.get("current_size_multiplier", frame.get("size_multiplier"))),
        errors="coerce",
    ).fillna(pd.to_numeric(frame.get("current_size_multiplier", frame.get("size_multiplier")), errors="coerce")).fillna(0.0)

    canonical = frame[
        [
            "canonical_event_id",
            "setup_id",
            "lifecycle_id",
            "parent_lifecycle_id",
            "symbol",
            "session_date",
            "timestamp",
            "lineage_event_type",
            "event_source",
            "state_label",
            "participation_quality_label",
            "expansion_score",
            "fragility_score",
            "continuation_risk_score",
            "size_multiplier_canonical",
            "add_depth",
            "scale_depth",
            "replay_state",
            "event_index",
            "event_id",
            "identity_origin",
            "identity_confidence",
        ]
    ].rename(
        columns={
            "canonical_event_id": "event_id",
            "lineage_event_type": "event_type",
            "size_multiplier_canonical": "size_multiplier",
            "event_id": "raw_event_id",
        }
    )
    return canonical.sort_values(
        ["symbol", "session_date", "timestamp", "event_index", "event_id"],
        kind="stable",
    ).reset_index(drop=True)


def _build_lifecycle_snapshots(canonical_events_df: pd.DataFrame) -> pd.DataFrame:
    if canonical_events_df.empty:
        return pd.DataFrame(
            columns=[
                "lifecycle_id",
                "timestamp",
                "replay_state",
                "size_multiplier",
                "add_depth",
                "scale_depth",
                "persistence_depth",
                "weakening_flag",
                "invalidated_flag",
                "event_id",
            ]
        )

    snapshot_rows: list[dict[str, Any]] = []
    for lifecycle_id, group in canonical_events_df.groupby("lifecycle_id", dropna=False, sort=False):
        ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        persistence_depth = 0
        weakening_flag = False
        invalidated_flag = False
        for _, row in ordered.iterrows():
            event_type = _safe_text(row.get("event_type"))
            if event_type == "PERSISTENCE_CONFIRMED":
                persistence_depth += 1
            if event_type == "FRAGILITY_WARNING":
                weakening_flag = True
            if event_type == "INVALIDATION":
                invalidated_flag = True
            snapshot_rows.append(
                {
                    "lifecycle_id": _safe_text(lifecycle_id, "unknown_lifecycle"),
                    "timestamp": pd.to_datetime(row.get("timestamp"), errors="coerce", utc=True),
                    "replay_state": _safe_text(row.get("replay_state"), "UNKNOWN"),
                    "size_multiplier": round(_safe_float(row.get("size_multiplier"), 0.0), 6),
                    "add_depth": int(_safe_float(row.get("add_depth"), 0.0)),
                    "scale_depth": int(_safe_float(row.get("scale_depth"), 0.0)),
                    "persistence_depth": persistence_depth,
                    "weakening_flag": weakening_flag,
                    "invalidated_flag": invalidated_flag,
                    "event_id": _safe_text(row.get("event_id"), "unknown_event"),
                }
            )
    return pd.DataFrame(snapshot_rows).sort_values(
        ["lifecycle_id", "timestamp", "event_id"],
        kind="stable",
    ).reset_index(drop=True)


def _event_source_summary(canonical_events_df: pd.DataFrame) -> pd.DataFrame:
    if canonical_events_df.empty:
        return pd.DataFrame(columns=["event_source", "event_count", "lifecycle_count", "event_share"])
    total_events = max(len(canonical_events_df), 1)
    return (
        canonical_events_df.groupby("event_source", dropna=False)
        .agg(
            event_count=("event_id", "size"),
            lifecycle_count=("lifecycle_id", "nunique"),
        )
        .reset_index()
        .assign(event_share=lambda df: df["event_count"] / total_events)
        .sort_values(["event_count", "event_source"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )


def _capture_fidelity(
    canonical_events_df: pd.DataFrame,
    lifecycle_identity_df: pd.DataFrame,
) -> pd.DataFrame:
    if canonical_events_df.empty or lifecycle_identity_df.empty:
        return pd.DataFrame(columns=["metric_name", "metric_value"])

    event_count = max(len(canonical_events_df), 1)
    lifecycle_count = max(len(lifecycle_identity_df), 1)
    explicit_event_capture_share = float(canonical_events_df["event_source"].astype(str).eq("SOURCE_CAPTURED").sum() / event_count)
    derived_event_capture_share = float(canonical_events_df["event_source"].astype(str).eq("SESSION_DERIVED").sum() / event_count)
    replay_fallback_share = float(canonical_events_df["event_source"].astype(str).eq("REPLAY_DERIVED").sum() / event_count)
    explicit_setup_identity_share = float(lifecycle_identity_df["identity_origin"].astype(str).eq("explicit_setup_identity").sum() / lifecycle_count)
    explicit_lifecycle_identity_share = float(
        lifecycle_identity_df["identity_origin"].astype(str).isin(
            {"explicit_setup_identity", "explicit_trade_identity", "explicit_session_identity"}
        ).sum()
        / lifecycle_count
    )

    non_root = lifecycle_identity_df[~lifecycle_identity_df["is_root_lifecycle"].fillna(False).astype(bool)]
    parent_linkage_share = float(
        non_root["parent_lifecycle_id"].notna().sum() / len(non_root)
    ) if not non_root.empty else 0.0

    multi_stage_count = 0
    for _, group in canonical_events_df.groupby("lifecycle_id", dropna=False, sort=False):
        ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable")
        event_types = ordered["event_type"].astype(str).tolist()
        if "PROBE_ENTRY" not in event_types:
            continue
        probe_idx = event_types.index("PROBE_ENTRY")
        later = set(event_types[probe_idx + 1 :])
        if {"ADD_CONFIRMED", "SIZE_INCREASE", "PERSISTENCE_CONFIRMED"} & later:
            multi_stage_count += 1
    multi_stage_capture_share = float(multi_stage_count / lifecycle_count)

    capture_fidelity_score = (
        0.25 * explicit_event_capture_share
        + 0.20 * explicit_setup_identity_share
        + 0.15 * explicit_lifecycle_identity_share
        + 0.15 * parent_linkage_share
        + 0.25 * multi_stage_capture_share
    )

    metrics = [
        ("explicit_event_capture_share", explicit_event_capture_share),
        ("derived_event_capture_share", derived_event_capture_share),
        ("replay_fallback_share", replay_fallback_share),
        ("explicit_setup_identity_share", explicit_setup_identity_share),
        ("explicit_lifecycle_identity_share", explicit_lifecycle_identity_share),
        ("parent_linkage_share", parent_linkage_share),
        ("multi_stage_capture_share", multi_stage_capture_share),
        ("capture_fidelity_score", capture_fidelity_score),
    ]
    return pd.DataFrame(
        [{"metric_name": name, "metric_value": round(value, 6)} for name, value in metrics]
    )


def build_continuation_event_capture(
    source_truth_lineage_artifacts: SourceTruthLineageArtifacts | None = None,
    source_truth_replay_artifacts: SourceTruthReplayArtifacts | None = None,
    multi_event_artifacts: MultiEventReplayDatasetArtifacts | None = None,
    corrected_master_df: pd.DataFrame | None = None,
    intraday_bars_df: pd.DataFrame | None = None,
) -> ContinuationEventCaptureArtifacts:
    upstream_366 = multi_event_artifacts if multi_event_artifacts is not None else build_multi_event_replay_dataset()
    upstream_367 = source_truth_replay_artifacts if source_truth_replay_artifacts is not None else build_source_truth_replay_dataset(
        multi_event_artifacts=upstream_366,
        corrected_master_df=corrected_master_df,
        intraday_bars_df=intraday_bars_df,
    )
    upstream_368 = source_truth_lineage_artifacts if source_truth_lineage_artifacts is not None else build_source_truth_lineage_dataset(
        source_truth_artifacts=upstream_367,
        multi_event_artifacts=upstream_366,
        corrected_master_df=corrected_master_df,
        intraday_bars_df=intraday_bars_df,
    )

    corrected_master = corrected_master_df.copy() if corrected_master_df is not None else _prepare_corrected_entry_master().copy()
    intraday_bars = intraday_bars_df.copy() if intraday_bars_df is not None else _load_intraday_bars(DB_PATH).copy()
    _ = corrected_master
    _ = intraday_bars

    lifecycle_identity_df, event_identity_df, identity_origin_summary_df = build_continuation_lifecycle_identity(
        upstream_366.setup_frame,
        upstream_366.multi_event_replay_dataset,
        upstream_367.source_truth_replay_dataset,
        upstream_368.setup_identity,
        upstream_368.lineage_rows,
    )
    canonical_events_df = _build_canonical_events(
        upstream_368.lineage_rows,
        upstream_368.add_scale_evolution,
        lifecycle_identity_df,
        event_identity_df,
    )
    lifecycle_snapshots_df = _build_lifecycle_snapshots(canonical_events_df)
    event_source_summary_df = _event_source_summary(canonical_events_df)
    capture_fidelity_df = _capture_fidelity(canonical_events_df, lifecycle_identity_df)

    return ContinuationEventCaptureArtifacts(
        canonical_events=canonical_events_df,
        lifecycle_identity=lifecycle_identity_df,
        lifecycle_snapshots=lifecycle_snapshots_df,
        event_source_summary=event_source_summary_df,
        identity_origin_summary=identity_origin_summary_df,
        capture_fidelity=capture_fidelity_df,
        upstream_368=upstream_368,
        upstream_367=upstream_367,
        upstream_366=upstream_366,
    )


def write_continuation_event_capture(
    artifacts: ContinuationEventCaptureArtifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.canonical_events.to_csv(out_dir / "task_369_canonical_events.csv", index=False)
    artifacts.lifecycle_identity.to_csv(out_dir / "task_369_lifecycle_identity.csv", index=False)
    artifacts.lifecycle_snapshots.to_csv(out_dir / "task_369_lifecycle_snapshots.csv", index=False)
    artifacts.event_source_summary.to_csv(out_dir / "task_369_event_source_summary.csv", index=False)
    artifacts.identity_origin_summary.to_csv(out_dir / "task_369_identity_origin_summary.csv", index=False)
    artifacts.capture_fidelity.to_csv(out_dir / "task_369_capture_fidelity.csv", index=False)
