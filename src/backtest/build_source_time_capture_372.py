from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _prepare_corrected_entry_master
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH
from src.backtest.build_source_truth_lineage_368 import (
    SourceTruthLineageArtifacts,
    build_source_truth_lineage_dataset,
)
from src.state.store import (
    delete_continuation_capture_batch,
    initialize_store,
    insert_continuation_lifecycle,
    insert_continuation_snapshot,
    insert_continuation_source_event,
    insert_or_ignore_continuation_setup,
    list_continuation_lifecycles,
    list_continuation_setups,
    list_continuation_snapshots,
    list_continuation_source_events,
    summarize_continuation_capture_coverage_filtered,
    summarize_continuation_lifecycle_completeness_filtered,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_372_historical_source_backfill")
HISTORICAL_CAPTURE_MODE = "historical_backfill"
HISTORICAL_DATASET_VERSION = "task372-v1"
HISTORICAL_ID_PREFIX = "hist372"


@dataclass(frozen=True)
class SourceTimeCapture372Artifacts:
    historical_source_event_dataset: pd.DataFrame
    historical_lifecycle_identity: pd.DataFrame
    historical_setup_identity: pd.DataFrame
    historical_snapshot_dataset: pd.DataFrame
    lifecycle_backtest_panel: pd.DataFrame
    effect_summary: pd.DataFrame
    scope_comparison: pd.DataFrame
    backfill_coverage_summary: pd.DataFrame


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
    return float(numeric)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return int(default)
    return int(numeric)


def _coalesce_timestamp(*values: Any) -> pd.Timestamp:
    for value in values:
        stamp = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.notna(stamp):
            return stamp
    return pd.NaT


def _details_field(details_json: Any, key: str) -> str:
    text = _safe_text(details_json)
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    return _safe_text(payload.get(key))


def _historical_setup_id(setup_id: Any, capture_batch_id: str) -> str:
    return f"{HISTORICAL_ID_PREFIX}|{_safe_text(capture_batch_id, 'batch')}|setup|{_safe_text(setup_id, 'unknown_setup')}"


def _historical_lifecycle_id(continuation_id: Any, capture_batch_id: str) -> str:
    return f"{HISTORICAL_ID_PREFIX}|{_safe_text(capture_batch_id, 'batch')}|life|{_safe_text(continuation_id, 'unknown_continuation')}"


def _historical_source_event_id(continuation_id: Any, event_index: Any, event_id: Any, capture_batch_id: str) -> str:
    ordinal = _safe_int(event_index, 0)
    base = _safe_text(event_id)
    suffix = f"|{base}" if base else ""
    return f"{_historical_lifecycle_id(continuation_id, capture_batch_id)}|evt_{ordinal:03d}{suffix}"


def _event_source(row: pd.Series) -> str:
    linkage_source = _safe_text(row.get("linkage_source"))
    event_type = _safe_text(row.get("lineage_event_type", row.get("event_type")))
    if linkage_source in {"replay_continuity_fallback", "unmatched_synthetic"}:
        return "REPLAY_DERIVED"
    if event_type in {"PERSISTENCE_CONFIRMED", "FRAGILITY_WARNING", "REDUCTION_TRIGGER"}:
        return "SESSION_DERIVED"
    if event_type == "SETUP_DETECTED" and pd.notna(_coalesce_timestamp(row.get("setup_timestamp"), row.get("breakout_timestamp"))):
        return "SOURCE_CAPTURED"
    if event_type == "PROBE_ENTRY" and pd.notna(_coalesce_timestamp(row.get("entry_ts"), row.get("timestamp"))):
        return "SOURCE_CAPTURED"
    if event_type == "EXIT_TRIGGER" and pd.notna(_coalesce_timestamp(row.get("exit_ts"), row.get("timestamp"))):
        return "SOURCE_CAPTURED"
    if bool(row.get("source_linked_flag")):
        return "SOURCE_CAPTURED"
    return "SESSION_DERIVED"


def _identity_origin(group: pd.DataFrame) -> tuple[str, float]:
    setup_origin = set(group.get("setup_origin_type", pd.Series(dtype=str)).astype(str))
    event_sources = set(group["event_source"].astype(str))
    if setup_origin & {"explicit_breakout_setup", "explicit_entry_setup"}:
        return "explicit_setup_identity", 1.00
    if set(group.get("linkage_source", pd.Series(dtype=str)).astype(str)) & {"trade_id_master_match"}:
        return "explicit_trade_identity", 0.90
    if "SOURCE_CAPTURED" in event_sources:
        return "explicit_session_identity", 0.80
    if "SESSION_DERIVED" in event_sources:
        return "derived_session_continuity", 0.60
    return "replay_fallback_identity", 0.35


def _prepare_upstream_frames(
    *,
    source_truth_replay_dataset_df: pd.DataFrame | None,
    lineage_rows_df: pd.DataFrame | None,
    lineage_summary_df: pd.DataFrame | None,
    add_scale_evolution_df: pd.DataFrame | None,
    persistence_summary_df: pd.DataFrame | None,
    setup_identity_df: pd.DataFrame | None,
    corrected_master_df: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    corrected_master = corrected_master_df.copy() if corrected_master_df is not None else _prepare_corrected_entry_master().copy()
    if source_truth_replay_dataset_df is not None:
        dataset = source_truth_replay_dataset_df.copy()
        lineage_rows = lineage_rows_df.copy() if lineage_rows_df is not None else pd.DataFrame()
        lineage_summary = lineage_summary_df.copy() if lineage_summary_df is not None else pd.DataFrame()
        add_scale = add_scale_evolution_df.copy() if add_scale_evolution_df is not None else pd.DataFrame()
        persistence_summary = persistence_summary_df.copy() if persistence_summary_df is not None else pd.DataFrame()
        setup_identity = setup_identity_df.copy() if setup_identity_df is not None else pd.DataFrame()
        return dataset, lineage_rows, lineage_summary, add_scale, persistence_summary, setup_identity, corrected_master

    artifacts: SourceTruthLineageArtifacts = build_source_truth_lineage_dataset(
        corrected_master_df=corrected_master,
    )
    return (
        artifacts.source_truth_replay_dataset.copy(),
        artifacts.lineage_rows.copy(),
        artifacts.lineage_summary.copy(),
        artifacts.add_scale_evolution.copy(),
        artifacts.persistence_summary.copy(),
        artifacts.setup_identity.copy(),
        corrected_master,
    )


def _build_historical_event_frame(
    dataset: pd.DataFrame,
    lineage_rows: pd.DataFrame,
    add_scale: pd.DataFrame,
    persistence_summary: pd.DataFrame,
    setup_identity: pd.DataFrame,
    capture_batch_id: str,
) -> pd.DataFrame:
    frame = dataset.copy()
    for column in ("timestamp", "setup_timestamp", "entry_ts", "exit_ts", "breakout_timestamp"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)
    if not lineage_rows.empty:
        row_cols = ["continuation_id", "event_id", "lineage_event_type"]
        for optional in ("setup_origin_type", "event_source", "source_truth_flag"):
            if optional in lineage_rows.columns:
                row_cols.append(optional)
        frame = frame.merge(
            lineage_rows[row_cols].drop_duplicates(subset=["continuation_id", "event_id"], keep="first"),
            on=["continuation_id", "event_id"],
            how="left",
        )
    if "lineage_event_type" not in frame.columns:
        frame["lineage_event_type"] = frame["event_type"].astype(str)
    if not add_scale.empty:
        frame = frame.merge(
            add_scale[
                [
                    "continuation_id",
                    "event_id",
                    "add_depth",
                    "scale_depth",
                    "cumulative_size_multiplier",
                    "has_add_attempt",
                    "has_add_confirmed",
                    "has_scale_up",
                ]
            ].drop_duplicates(subset=["continuation_id", "event_id"], keep="first"),
            on=["continuation_id", "event_id"],
            how="left",
        )
    if not persistence_summary.empty:
        frame = frame.merge(
            persistence_summary[
                [
                    "continuation_id",
                    "setup_id",
                    "persistence_duration_minutes",
                    "persistence_depth",
                    "fragility_transition_depth",
                    "invalidation_depth",
                ]
            ].drop_duplicates(subset=["continuation_id", "setup_id"], keep="first"),
            on=["continuation_id", "setup_id"],
            how="left",
        )
    if not setup_identity.empty:
        frame = frame.merge(
            setup_identity[["setup_id", "symbol", "session_date", "setup_origin_type", "setup_confidence"]].drop_duplicates(),
            on=["setup_id", "symbol", "session_date"],
            how="left",
            suffixes=("", "_setup"),
        )
        if "setup_origin_type_setup" in frame.columns:
            frame["setup_origin_type"] = frame["setup_origin_type"].fillna(frame["setup_origin_type_setup"])
            frame = frame.drop(columns=["setup_origin_type_setup"])

    frame["hist_setup_id"] = frame["setup_id"].map(lambda value: _historical_setup_id(value, capture_batch_id))
    frame["hist_lifecycle_id"] = frame["continuation_id"].map(lambda value: _historical_lifecycle_id(value, capture_batch_id))
    frame["source_event_id"] = [
        _historical_source_event_id(cont_id, event_index, event_id, capture_batch_id)
        for cont_id, event_index, event_id in zip(frame["continuation_id"], frame["event_index"], frame["event_id"])
    ]
    frame["event_source"] = frame.apply(_event_source, axis=1)
    frame["source_dataset_version"] = HISTORICAL_DATASET_VERSION
    frame = frame.sort_values(["symbol", "session_date", "timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
    return frame


def _parent_linkage_map(frame: pd.DataFrame) -> dict[str, str | None]:
    rows: dict[str, str | None] = {}
    if frame.empty:
        return rows
    grouped = (
        frame.groupby(["hist_setup_id", "hist_lifecycle_id", "symbol", "session_date"], dropna=False)
        .agg(first_timestamp=("timestamp", "min"))
        .reset_index()
        .sort_values(["hist_setup_id", "first_timestamp", "hist_lifecycle_id"], kind="stable")
    )
    for _, setup_group in grouped.groupby("hist_setup_id", dropna=False, sort=False):
        previous: str | None = None
        for _, row in setup_group.iterrows():
            lifecycle_id = _safe_text(row["hist_lifecycle_id"])
            rows[lifecycle_id] = previous
            previous = lifecycle_id
    return rows


def _insert_backfill_rows(
    db_path: str,
    frame: pd.DataFrame,
    *,
    capture_batch_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    initialize_store(db_path)
    delete_continuation_capture_batch(
        db_path,
        capture_mode=HISTORICAL_CAPTURE_MODE,
        capture_batch_id=capture_batch_id,
    )
    parent_map = _parent_linkage_map(frame)
    lifecycle_rows: list[dict[str, Any]] = []
    setup_rows: list[dict[str, Any]] = []
    snapshot_rows: list[dict[str, Any]] = []

    for (hist_setup_id, symbol, session_date), setup_group in frame.groupby(["hist_setup_id", "symbol", "session_date"], dropna=False, sort=False):
        first_row = setup_group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").iloc[0]
        setup_timestamp = _coalesce_timestamp(first_row.get("setup_timestamp"), first_row.get("breakout_timestamp"), first_row.get("timestamp"))
        insert_or_ignore_continuation_setup(
            db_path,
            setup_id=_safe_text(hist_setup_id),
            symbol=_safe_text(symbol, "UNKNOWN"),
            session_date=_safe_text(session_date, "unknown_session"),
            setup_timestamp=setup_timestamp.isoformat() if pd.notna(setup_timestamp) else "",
            setup_origin=_safe_text(first_row.get("setup_origin_type"), "historical_backfill"),
            signal_event_id=_safe_text(first_row.get("raw_signal_id")) or None,
            risk_decision_id=None,
            capture_mode=HISTORICAL_CAPTURE_MODE,
            capture_batch_id=capture_batch_id,
            source_dataset_version=HISTORICAL_DATASET_VERSION,
            created_at=(setup_timestamp.isoformat() if pd.notna(setup_timestamp) else ""),
        )
        setup_rows.append(
            {
                "setup_id": _safe_text(hist_setup_id),
                "symbol": _safe_text(symbol, "UNKNOWN"),
                "session_date": _safe_text(session_date, "unknown_session"),
                "setup_timestamp": setup_timestamp,
                "setup_origin": _safe_text(first_row.get("setup_origin_type"), "historical_backfill"),
                "capture_mode": HISTORICAL_CAPTURE_MODE,
                "capture_batch_id": capture_batch_id,
                "source_dataset_version": HISTORICAL_DATASET_VERSION,
            }
        )

    for lifecycle_id, lifecycle_group in frame.groupby("hist_lifecycle_id", dropna=False, sort=False):
        ordered = lifecycle_group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        first_row = ordered.iloc[0]
        origin, confidence = _identity_origin(ordered)
        started_at = _coalesce_timestamp(first_row.get("timestamp"), first_row.get("entry_ts"), first_row.get("setup_timestamp"))
        insert_continuation_lifecycle(
            db_path,
            lifecycle_id=_safe_text(lifecycle_id),
            setup_id=_safe_text(first_row.get("hist_setup_id")),
            parent_lifecycle_id=parent_map.get(_safe_text(lifecycle_id)),
            symbol=_safe_text(first_row.get("symbol"), "UNKNOWN"),
            session_date=_safe_text(first_row.get("session_date"), "unknown_session"),
            started_at=started_at.isoformat() if pd.notna(started_at) else "",
            identity_origin=origin,
            identity_confidence=confidence,
            capture_mode=HISTORICAL_CAPTURE_MODE,
            capture_batch_id=capture_batch_id,
            source_dataset_version=HISTORICAL_DATASET_VERSION,
            created_at=(started_at.isoformat() if pd.notna(started_at) else ""),
        )
        lifecycle_rows.append(
            {
                "lifecycle_id": _safe_text(lifecycle_id),
                "setup_id": _safe_text(first_row.get("hist_setup_id")),
                "parent_lifecycle_id": parent_map.get(_safe_text(lifecycle_id)),
                "symbol": _safe_text(first_row.get("symbol"), "UNKNOWN"),
                "session_date": _safe_text(first_row.get("session_date"), "unknown_session"),
                "started_at": started_at,
                "identity_origin": origin,
                "identity_confidence": confidence,
                "capture_mode": HISTORICAL_CAPTURE_MODE,
                "capture_batch_id": capture_batch_id,
                "source_dataset_version": HISTORICAL_DATASET_VERSION,
            }
        )
        weakening_seen = False
        invalidated_seen = False
        persistence_depth_running = 0
        for _, row in ordered.iterrows():
            timestamp = _coalesce_timestamp(row.get("timestamp"), row.get("entry_ts"), row.get("setup_timestamp"))
            event_type = _safe_text(row.get("lineage_event_type", row.get("event_type")), "UNKNOWN")
            if event_type == "PERSISTENCE_CONFIRMED":
                persistence_depth_running += 1
            weakening_seen = weakening_seen or event_type in {"FRAGILITY_WARNING", "REDUCTION_TRIGGER"}
            invalidated_seen = invalidated_seen or event_type == "INVALIDATION"
            details = {
                "raw_trade_id": _safe_text(row.get("raw_trade_id")),
                "raw_signal_id": _safe_text(row.get("raw_signal_id")),
                "linkage_source": _safe_text(row.get("linkage_source")),
                "lineage_quality": _safe_text(row.get("lineage_quality")),
                "transition_reason": _safe_text(row.get("transition_reason")),
                "intraday_match_status": _safe_text(row.get("intraday_match_status")),
            }
            insert_continuation_source_event(
                db_path,
                source_event_id=_safe_text(row.get("source_event_id")),
                lifecycle_id=_safe_text(lifecycle_id),
                setup_id=_safe_text(row.get("hist_setup_id")),
                parent_lifecycle_id=parent_map.get(_safe_text(lifecycle_id)),
                signal_event_id=_safe_text(row.get("raw_signal_id")) or None,
                risk_decision_id=None,
                order_intent_id=None,
                order_id=None,
                fill_id=None,
                reconciliation_id=None,
                trade_run_id=None,
                symbol=_safe_text(row.get("symbol"), "UNKNOWN"),
                session_date=_safe_text(row.get("session_date"), "unknown_session"),
                event_type=event_type,
                event_source=_safe_text(row.get("event_source"), "SESSION_DERIVED"),
                event_timestamp=timestamp.isoformat() if pd.notna(timestamp) else "",
                state_label=_safe_text(row.get("state_label")) or None,
                participation_quality_label=_safe_text(row.get("participation_quality_label")) or None,
                expansion_score=_safe_float(row.get("expansion_score"), 0.0),
                fragility_score=_safe_float(row.get("fragility_score"), 0.0),
                continuation_risk_score=_safe_float(row.get("continuation_risk_score"), 0.0),
                size_multiplier=_safe_float(row.get("current_size_multiplier", row.get("size_multiplier")), 1.0),
                add_depth=_safe_int(row.get("add_depth", row.get("cumulative_add_count", 0)), 0),
                scale_depth=_safe_int(row.get("scale_depth", 0), 0),
                persistence_depth=persistence_depth_running,
                capture_mode=HISTORICAL_CAPTURE_MODE,
                capture_batch_id=capture_batch_id,
                source_dataset_version=HISTORICAL_DATASET_VERSION,
                details_json=pd.Series(details).to_json(force_ascii=True),
                created_at=(timestamp.isoformat() if pd.notna(timestamp) else ""),
            )
            snapshot_id = f"{_safe_text(row.get('source_event_id'))}|snapshot"
            insert_continuation_snapshot(
                db_path,
                snapshot_id=snapshot_id,
                lifecycle_id=_safe_text(lifecycle_id),
                setup_id=_safe_text(row.get("hist_setup_id")),
                event_id=_safe_text(row.get("source_event_id")),
                snapshot_timestamp=timestamp.isoformat() if pd.notna(timestamp) else "",
                replay_state=_safe_text(row.get("replay_state"), "UNKNOWN"),
                size_multiplier=_safe_float(row.get("current_size_multiplier", row.get("size_multiplier")), 1.0),
                add_depth=_safe_int(row.get("add_depth", row.get("cumulative_add_count", 0)), 0),
                scale_depth=_safe_int(row.get("scale_depth", 0), 0),
                persistence_depth=persistence_depth_running,
                weakening_flag=weakening_seen,
                invalidated_flag=invalidated_seen,
                capture_mode=HISTORICAL_CAPTURE_MODE,
                capture_batch_id=capture_batch_id,
                source_dataset_version=HISTORICAL_DATASET_VERSION,
                created_at=(timestamp.isoformat() if pd.notna(timestamp) else ""),
            )
            snapshot_rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "lifecycle_id": _safe_text(lifecycle_id),
                    "setup_id": _safe_text(row.get("hist_setup_id")),
                    "event_id": _safe_text(row.get("source_event_id")),
                    "snapshot_timestamp": timestamp,
                    "replay_state": _safe_text(row.get("replay_state"), "UNKNOWN"),
                    "size_multiplier": _safe_float(row.get("current_size_multiplier", row.get("size_multiplier")), 1.0),
                    "add_depth": _safe_int(row.get("add_depth", row.get("cumulative_add_count", 0)), 0),
                    "scale_depth": _safe_int(row.get("scale_depth", 0), 0),
                    "persistence_depth": persistence_depth_running,
                    "weakening_flag": weakening_seen,
                    "invalidated_flag": invalidated_seen,
                    "capture_mode": HISTORICAL_CAPTURE_MODE,
                    "capture_batch_id": capture_batch_id,
                    "source_dataset_version": HISTORICAL_DATASET_VERSION,
                }
            )
    return pd.DataFrame(setup_rows), pd.DataFrame(lifecycle_rows), pd.DataFrame(snapshot_rows)


def _build_lifecycle_backtest_panel(
    events_df: pd.DataFrame,
    lifecycle_df: pd.DataFrame,
    corrected_master: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if events_df.empty or lifecycle_df.empty:
        empty = pd.DataFrame()
        return empty, empty, pd.DataFrame(columns=["metric_name", "metric_value"])

    frame = events_df.copy()
    if "event_timestamp" in frame.columns:
        frame["event_timestamp"] = pd.to_datetime(frame["event_timestamp"], errors="coerce", utc=True)
    master = corrected_master.copy()
    master["trade_id"] = master["trade_id"].astype(str)

    details = frame.get("details_json", pd.Series("", index=frame.index)).fillna("").astype(str)
    frame["raw_trade_id"] = details.map(lambda text: _details_field(text, "raw_trade_id"))

    lifecycle_panel = (
        frame.groupby(["lifecycle_id", "setup_id", "symbol", "session_date"], dropna=False)
        .agg(
            event_count=("source_event_id", "count"),
            persistence_depth=("persistence_depth", "max"),
            add_depth=("add_depth", "max"),
            scale_depth=("scale_depth", "max"),
            participation_quality_start=("participation_quality_label", "first"),
            participation_quality_final=("participation_quality_label", "last"),
            expansion_score_start=("expansion_score", "first"),
            expansion_score_final=("expansion_score", "last"),
            fragility_score_start=("fragility_score", "first"),
            fragility_score_final=("fragility_score", "last"),
            max_size_multiplier=("size_multiplier", "max"),
            avg_size_multiplier=("size_multiplier", "mean"),
            source_linked_flag=("event_source", lambda values: int(any(str(v) == "SOURCE_CAPTURED" for v in values))),
            replay_derived_only=("event_source", lambda values: int(all(str(v) == "REPLAY_DERIVED" for v in values))),
            fragile_transition_flag=("event_type", lambda values: int(any(str(v) in {"FRAGILITY_WARNING", "REDUCTION_TRIGGER"} for v in values))),
            invalidated_flag=("event_type", lambda values: int(any(str(v) == "INVALIDATION" for v in values))),
            add_confirmed_flag=("event_type", lambda values: int(any(str(v) == "ADD_CONFIRMED" for v in values))),
            scale_up_flag=("event_type", lambda values: int(any(str(v) == "SIZE_INCREASE" for v in values))),
            persistence_confirmed_flag=("event_type", lambda values: int(any(str(v) == "PERSISTENCE_CONFIRMED" for v in values))),
            start_event_timestamp=("event_timestamp", "min"),
            end_event_timestamp=("event_timestamp", "max"),
            raw_trade_id=("raw_trade_id", "first"),
        )
        .reset_index()
    )
    lifecycle_panel = lifecycle_panel.merge(
        lifecycle_df[
            [
                "lifecycle_id",
                "parent_lifecycle_id",
                "identity_origin",
                "identity_confidence",
                "capture_mode",
                "capture_batch_id",
                "source_dataset_version",
            ]
        ],
        on="lifecycle_id",
        how="left",
    )
    master_cols = ["trade_id", "current_split", "realized_R"]
    for optional in ("proxy_pnl", "mfe", "mae", "mfe_5d_pct", "mae_5d_pct"):
        if optional in master.columns:
            master_cols.append(optional)
    master_join = (
        master[master_cols]
        .drop_duplicates(subset=["trade_id"], keep="first")
        .rename(columns={"trade_id": "raw_trade_id"})
        .reset_index(drop=True)
    )
    lifecycle_panel = lifecycle_panel.merge(
        master_join,
        on="raw_trade_id",
        how="left",
    )
    lifecycle_panel["current_split"] = lifecycle_panel["current_split"].fillna("full_period")
    lifecycle_panel["healthy_start_flag"] = lifecycle_panel["participation_quality_start"].astype(str).eq("HEALTHY_EXPANSION").astype(int)
    lifecycle_panel["lineage_quality"] = np.where(
        lifecycle_panel["source_linked_flag"].astype(int) > 0,
        "source_linked",
        np.where(lifecycle_panel["replay_derived_only"].astype(int) > 0, "replay_derived", "session_derived"),
    )
    lifecycle_panel["persistence_duration_minutes"] = (
        (lifecycle_panel["end_event_timestamp"] - lifecycle_panel["start_event_timestamp"]).dt.total_seconds().div(60.0).fillna(0.0)
    )

    scoped_frames = [lifecycle_panel.assign(evaluation_scope="full_period")]
    anchored = lifecycle_panel[lifecycle_panel["current_split"].astype(str) == "anchored_oos"].copy()
    if not anchored.empty:
        scoped_frames.append(anchored.assign(evaluation_scope="anchored_oos"))
    scoped_panel = pd.concat(scoped_frames, ignore_index=True)

    effect_rows: list[dict[str, Any]] = []
    cuts = {
        "healthy_start": scoped_panel["healthy_start_flag"].astype(int) > 0,
        "add_confirmed": scoped_panel["add_confirmed_flag"].astype(int) > 0,
        "scale_up": scoped_panel["scale_up_flag"].astype(int) > 0,
        "persistence_confirmed": scoped_panel["persistence_confirmed_flag"].astype(int) > 0,
        "fragile_transition": scoped_panel["fragile_transition_flag"].astype(int) > 0,
        "invalidated": scoped_panel["invalidated_flag"].astype(int) > 0,
        "source_linked": scoped_panel["source_linked_flag"].astype(int) > 0,
    }
    for scope, scope_df in scoped_panel.groupby("evaluation_scope", dropna=False, sort=False):
        for cut_name, mask in cuts.items():
            scoped_mask = mask.loc[scope_df.index]
            for bucket_name, bucket_df in (("selected", scope_df[scoped_mask]), ("other", scope_df[~scoped_mask])):
                realized = pd.to_numeric(bucket_df["realized_R"], errors="coerce")
                effect_rows.append(
                    {
                        "evaluation_scope": _safe_text(scope),
                        "cut_name": cut_name,
                        "bucket_name": bucket_name,
                        "lifecycle_count": int(len(bucket_df)),
                        "win_rate": round(float((realized > 0).mean()), 6) if not bucket_df.empty else 0.0,
                        "avg_realized_R": round(float(realized.mean()), 6) if not bucket_df.empty else 0.0,
                        "total_realized_R": round(float(realized.sum()), 6) if not bucket_df.empty else 0.0,
                    }
                )
    effect_summary = pd.DataFrame(effect_rows)

    scope_rows: list[dict[str, Any]] = []
    for scope, scope_df in scoped_panel.groupby("evaluation_scope", dropna=False, sort=False):
        realized = pd.to_numeric(scope_df["realized_R"], errors="coerce")
        scope_rows.append(
            {
                "evaluation_scope": _safe_text(scope),
                "lifecycle_count": int(len(scope_df)),
                "source_linked_share": round(float(scope_df["source_linked_flag"].astype(int).mean()), 6) if not scope_df.empty else 0.0,
                "add_confirmed_share": round(float(scope_df["add_confirmed_flag"].astype(int).mean()), 6) if not scope_df.empty else 0.0,
                "scale_up_share": round(float(scope_df["scale_up_flag"].astype(int).mean()), 6) if not scope_df.empty else 0.0,
                "persistence_confirmed_share": round(float(scope_df["persistence_confirmed_flag"].astype(int).mean()), 6) if not scope_df.empty else 0.0,
                "fragile_transition_share": round(float(scope_df["fragile_transition_flag"].astype(int).mean()), 6) if not scope_df.empty else 0.0,
                "avg_realized_R": round(float(realized.mean()), 6) if not scope_df.empty else 0.0,
                "total_realized_R": round(float(realized.sum()), 6) if not scope_df.empty else 0.0,
            }
        )
    scope_comparison = pd.DataFrame(scope_rows)

    return scoped_panel, effect_summary, scope_comparison


def build_source_time_capture_372(
    *,
    db_path: str = str(DB_PATH),
    capture_batch_id: str,
    reuse_existing_batch: bool = False,
    source_truth_replay_dataset_df: pd.DataFrame | None = None,
    lineage_rows_df: pd.DataFrame | None = None,
    lineage_summary_df: pd.DataFrame | None = None,
    add_scale_evolution_df: pd.DataFrame | None = None,
    persistence_summary_df: pd.DataFrame | None = None,
    setup_identity_df: pd.DataFrame | None = None,
    corrected_master_df: pd.DataFrame | None = None,
) -> SourceTimeCapture372Artifacts:
    if not str(capture_batch_id).strip():
        raise ValueError("capture_batch_id is required")
    corrected_master = corrected_master_df.copy() if corrected_master_df is not None else _prepare_corrected_entry_master().copy()
    if not reuse_existing_batch:
        dataset, lineage_rows, lineage_summary, add_scale, persistence_summary, setup_identity, corrected_master = _prepare_upstream_frames(
            source_truth_replay_dataset_df=source_truth_replay_dataset_df,
            lineage_rows_df=lineage_rows_df,
            lineage_summary_df=lineage_summary_df,
            add_scale_evolution_df=add_scale_evolution_df,
            persistence_summary_df=persistence_summary_df,
            setup_identity_df=setup_identity_df,
            corrected_master_df=corrected_master,
        )
        hist_frame = _build_historical_event_frame(
            dataset,
            lineage_rows,
            add_scale,
            persistence_summary,
            setup_identity,
            capture_batch_id,
        )
        _insert_backfill_rows(
            db_path,
            hist_frame,
            capture_batch_id=capture_batch_id,
        )
    historical_events = pd.DataFrame(
        list_continuation_source_events(
            db_path,
            capture_mode=HISTORICAL_CAPTURE_MODE,
            capture_batch_id=capture_batch_id,
            limit=200000,
        )
    )
    lifecycle_identity = pd.DataFrame(
        list_continuation_lifecycles(
            db_path,
            capture_mode=HISTORICAL_CAPTURE_MODE,
            capture_batch_id=capture_batch_id,
            limit=200000,
        )
    )
    setup_identity_rows = pd.DataFrame(
        list_continuation_setups(
            db_path,
            capture_mode=HISTORICAL_CAPTURE_MODE,
            capture_batch_id=capture_batch_id,
            limit=200000,
        )
    )
    snapshot_rows = pd.DataFrame(
        list_continuation_snapshots(
            db_path,
            capture_mode=HISTORICAL_CAPTURE_MODE,
            capture_batch_id=capture_batch_id,
            limit=200000,
        )
    )
    lifecycle_panel, effect_summary, scope_comparison = _build_lifecycle_backtest_panel(
        historical_events,
        lifecycle_identity,
        corrected_master,
    )
    coverage_metrics = summarize_continuation_capture_coverage_filtered(
        db_path,
        capture_mode=HISTORICAL_CAPTURE_MODE,
        capture_batch_id=capture_batch_id,
    )
    completeness_rows = summarize_continuation_lifecycle_completeness_filtered(
        db_path,
        capture_mode=HISTORICAL_CAPTURE_MODE,
        capture_batch_id=capture_batch_id,
        limit=200000,
    )
    backfill_coverage = pd.DataFrame(
        [{"metric_name": name, "metric_value": round(float(value), 6)} for name, value in coverage_metrics.items()]
        + [{"metric_name": "lifecycle_completeness_rows", "metric_value": float(len(completeness_rows))}]
    )
    return SourceTimeCapture372Artifacts(
        historical_source_event_dataset=historical_events,
        historical_lifecycle_identity=lifecycle_identity,
        historical_setup_identity=setup_identity_rows,
        historical_snapshot_dataset=snapshot_rows,
        lifecycle_backtest_panel=lifecycle_panel,
        effect_summary=effect_summary,
        scope_comparison=scope_comparison,
        backfill_coverage_summary=backfill_coverage,
    )


def write_source_time_capture_372(
    artifacts: SourceTimeCapture372Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.historical_source_event_dataset.to_csv(out_dir / "task_372_historical_source_event_dataset.csv", index=False)
    artifacts.historical_lifecycle_identity.to_csv(out_dir / "task_372_historical_lifecycle_identity.csv", index=False)
    artifacts.historical_setup_identity.to_csv(out_dir / "task_372_historical_setup_identity.csv", index=False)
    artifacts.historical_snapshot_dataset.to_csv(out_dir / "task_372_historical_snapshot_dataset.csv", index=False)
    artifacts.lifecycle_backtest_panel.to_csv(out_dir / "task_372_lifecycle_backtest_panel.csv", index=False)
    artifacts.effect_summary.to_csv(out_dir / "task_372_effect_summary.csv", index=False)
    artifacts.scope_comparison.to_csv(out_dir / "task_372_scope_comparison.csv", index=False)
    artifacts.backfill_coverage_summary.to_csv(out_dir / "task_372_backfill_coverage_summary.csv", index=False)
