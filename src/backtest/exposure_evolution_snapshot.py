from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ExposureEvolutionSnapshot:
    continuation_id: str
    timestamp: pd.Timestamp | None
    replay_state: str
    current_size_multiplier: float
    cumulative_add_count: int
    persistence_duration_minutes: float
    participation_quality_label: str
    expansion_score: float
    fragility_score: float


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


def build_exposure_evolution_snapshots(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "timestamp",
                "replay_state",
                "current_size_multiplier",
                "cumulative_add_count",
                "persistence_duration_minutes",
                "participation_quality_label",
                "expansion_score",
                "fragility_score",
                "event_type",
                "event_id",
            ]
        )

    frame = events_df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.sort_values(
        ["continuation_id", "timestamp", "event_index", "event_id"],
        kind="stable",
    ).reset_index(drop=True)

    snapshots: list[dict[str, Any]] = []
    for continuation_id, group in frame.groupby("continuation_id", dropna=False, sort=False):
        group = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        final_row_size = _safe_float(group["size_multiplier"].iloc[-1], 0.0)
        has_later_add = bool(group["event_type"].astype(str).isin({"ADD_CONFIRMED", "SIZE_INCREASE"}).any())
        current_size = 0.0
        cumulative_add_count = 0
        first_probe_ts = pd.NaT

        for _, row in group.iterrows():
            event_type = _safe_text(row.get("event_type"), "UNKNOWN")
            timestamp = row.get("timestamp")
            if event_type == "SETUP":
                current_size = 0.0
            elif event_type == "PROBE_ENTRY":
                current_size = min(final_row_size, 0.25) if has_later_add else final_row_size
                if pd.isna(first_probe_ts):
                    first_probe_ts = timestamp
            elif event_type == "ADD_CONFIRMED":
                current_size = max(current_size, final_row_size * 0.6)
                cumulative_add_count += 1
            elif event_type == "SIZE_INCREASE":
                current_size = final_row_size
            elif event_type == "PERSISTENCE_CONFIRMED":
                current_size = current_size
            elif event_type == "REDUCTION_TRIGGER":
                current_size = current_size * 0.5
            elif event_type in {"EXIT_TRIGGER", "INVALIDATION"}:
                current_size = 0.0

            quality_label = _safe_text(row.get("participation_quality_label"), "UNKNOWN")
            state_label = _safe_text(row.get("state_label"), "UNKNOWN")
            if event_type == "REDUCTION_TRIGGER" and quality_label == "HEALTHY_EXPANSION":
                quality_label = "NEUTRAL_PARTICIPATION"
            if event_type in {"EXIT_TRIGGER", "INVALIDATION"} and (
                state_label == "DISLOCATION" or quality_label == "FRAGILE_CROWDING"
            ):
                quality_label = "FRAGILE_CROWDING"

            if pd.notna(first_probe_ts) and pd.notna(timestamp):
                persistence_minutes = max(float((pd.Timestamp(timestamp) - pd.Timestamp(first_probe_ts)).total_seconds() / 60.0), 0.0)
            else:
                persistence_minutes = 0.0

            snapshots.append(
                {
                    "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                    "setup_id": _safe_text(row.get("setup_id"), "unknown_setup"),
                    "timestamp": timestamp,
                    "replay_state": _safe_text(row.get("replay_state"), "UNKNOWN"),
                    "current_size_multiplier": round(float(current_size), 6),
                    "cumulative_add_count": int(cumulative_add_count),
                    "persistence_duration_minutes": round(float(persistence_minutes), 6),
                    "participation_quality_label": quality_label,
                    "expansion_score": _safe_float(row.get("expansion_score"), 0.0),
                    "fragility_score": _safe_float(row.get("fragility_score"), 0.0),
                    "event_type": event_type,
                    "event_id": _safe_text(row.get("event_id"), "unknown_event"),
                }
            )

    return pd.DataFrame(snapshots).sort_values(
        ["continuation_id", "timestamp", "event_id"],
        kind="stable",
    ).reset_index(drop=True)
