from __future__ import annotations

from typing import Any

import pandas as pd


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def build_persistence_lineage_timeline(lineage_row_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if lineage_row_df.empty:
        empty_row = pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "timestamp",
                "lineage_event_type",
                "birth_timestamp",
                "last_timestamp",
                "persistence_duration_minutes",
                "persistence_depth",
                "fragility_transition_depth",
                "invalidation_depth",
            ]
        )
        empty_summary = pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "birth_timestamp",
                "last_timestamp",
                "persistence_duration_minutes",
                "persistence_depth",
                "fragility_transition_depth",
                "invalidation_depth",
            ]
        )
        return empty_row, empty_summary

    row_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    for continuation_id, group in lineage_row_df.groupby("continuation_id", dropna=False, sort=False):
        ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        birth_candidates = ordered.loc[
            ordered["lineage_event_type"].astype(str).isin({"PROBE_ENTRY", "SETUP_DETECTED"}),
            "timestamp",
        ]
        birth_timestamp = pd.to_datetime(birth_candidates.iloc[0], errors="coerce", utc=True) if not birth_candidates.empty else pd.NaT
        last_timestamp = pd.to_datetime(ordered["timestamp"], errors="coerce", utc=True).max()
        persistence_depth = 0
        fragility_transition_depth = 0
        invalidation_depth = 0
        timeline_rows: list[dict[str, Any]] = []
        for depth_index, (_, row) in enumerate(ordered.iterrows(), start=1):
            event_type = _safe_text(row.get("lineage_event_type"))
            if event_type == "PERSISTENCE_CONFIRMED":
                persistence_depth += 1
            if fragility_transition_depth == 0 and event_type in {"FRAGILITY_WARNING", "REDUCTION_TRIGGER"}:
                fragility_transition_depth = depth_index
            if invalidation_depth == 0 and event_type == "INVALIDATION":
                invalidation_depth = depth_index
            timestamp = pd.to_datetime(row.get("timestamp"), errors="coerce", utc=True)
            duration = 0.0
            if pd.notna(timestamp) and pd.notna(birth_timestamp):
                duration = max((timestamp - birth_timestamp).total_seconds() / 60.0, 0.0)
            timeline_rows.append(
                {
                    "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                    "setup_id": _safe_text(row.get("setup_id"), "unknown_setup"),
                    "timestamp": timestamp,
                    "lineage_event_type": event_type,
                    "birth_timestamp": birth_timestamp,
                    "last_timestamp": last_timestamp,
                    "persistence_duration_minutes": round(duration, 6),
                    "persistence_depth": persistence_depth,
                    "fragility_transition_depth": fragility_transition_depth,
                    "invalidation_depth": invalidation_depth,
                }
            )
        row_frames.append(pd.DataFrame(timeline_rows))
        final_duration = 0.0
        if pd.notna(last_timestamp) and pd.notna(birth_timestamp):
            final_duration = max((last_timestamp - birth_timestamp).total_seconds() / 60.0, 0.0)
        summary_rows.append(
            {
                "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                "setup_id": _safe_text(ordered.iloc[0].get("setup_id"), "unknown_setup"),
                "birth_timestamp": birth_timestamp,
                "last_timestamp": last_timestamp,
                "persistence_duration_minutes": round(final_duration, 6),
                "persistence_depth": persistence_depth,
                "fragility_transition_depth": fragility_transition_depth,
                "invalidation_depth": invalidation_depth,
            }
        )
    row_df = pd.concat(row_frames, ignore_index=True).sort_values(
        ["continuation_id", "timestamp", "lineage_event_type"],
        kind="stable",
    ).reset_index(drop=True)
    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["persistence_duration_minutes", "continuation_id"],
        ascending=[False, True],
        kind="stable",
    ).reset_index(drop=True)
    return row_df, summary_df
