from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from src.backtest.continuation_intraday_events import ContinuationIntradayEvent


@dataclass(frozen=True)
class ContinuationTimeline:
    continuation_id: str
    setup_id: str
    symbol: str
    ordered_events: tuple[ContinuationIntradayEvent, ...]
    first_timestamp: pd.Timestamp | None
    last_timestamp: pd.Timestamp | None
    persistence_duration_minutes: float


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


def _events_to_frame(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return events_df.copy()
    frame = events_df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    return frame.sort_values(
        ["setup_id", "continuation_id", "timestamp", "event_index", "event_id"],
        kind="stable",
    ).reset_index(drop=True)


def build_continuation_timelines(events_df: pd.DataFrame) -> tuple[ContinuationTimeline, ...]:
    frame = _events_to_frame(events_df)
    if frame.empty:
        return ()

    timelines: list[ContinuationTimeline] = []
    for continuation_id, group in frame.groupby("continuation_id", dropna=False, sort=False):
        group = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        records = [
            ContinuationIntradayEvent(
                setup_id=_safe_text(row.get("setup_id"), "unknown_setup"),
                continuation_id=_safe_text(row.get("continuation_id"), "unknown_continuation"),
                symbol=_safe_text(row.get("symbol"), "UNKNOWN"),
                timestamp=row.get("timestamp"),
                event_type=_safe_text(row.get("event_type"), "UNKNOWN"),
                replay_state=_safe_text(row.get("replay_state"), "UNKNOWN"),
                participation_quality_label=_safe_text(row.get("participation_quality_label"), "UNKNOWN"),
                expansion_score=_safe_float(row.get("expansion_score"), 0.0),
                fragility_score=_safe_float(row.get("fragility_score"), 0.0),
                continuation_risk_score=_safe_float(row.get("continuation_risk_score"), 0.0),
                size_multiplier=_safe_float(row.get("size_multiplier"), 0.0),
                allow_add=bool(row.get("allow_add")),
            )
            for _, row in group.iterrows()
        ]
        probe_rows = group[group["event_type"].astype(str).eq("PROBE_ENTRY")]
        first_probe = pd.Timestamp(probe_rows["timestamp"].iloc[0]) if not probe_rows.empty else pd.NaT
        first_ts = pd.Timestamp(group["timestamp"].iloc[0]) if group["timestamp"].notna().any() else pd.NaT
        last_ts = pd.Timestamp(group["timestamp"].iloc[-1]) if group["timestamp"].notna().any() else pd.NaT
        if pd.notna(first_probe) and pd.notna(last_ts):
            persistence_minutes = max(float((last_ts - first_probe).total_seconds() / 60.0), 0.0)
        else:
            persistence_minutes = 0.0
        timelines.append(
            ContinuationTimeline(
                continuation_id=_safe_text(continuation_id, "unknown_continuation"),
                setup_id=_safe_text(group["setup_id"].iloc[0], "unknown_setup"),
                symbol=_safe_text(group["symbol"].iloc[0], "UNKNOWN"),
                ordered_events=tuple(records),
                first_timestamp=first_ts if pd.notna(first_ts) else pd.NaT,
                last_timestamp=last_ts if pd.notna(last_ts) else pd.NaT,
                persistence_duration_minutes=round(persistence_minutes, 6),
            )
        )
    return tuple(timelines)


def build_event_timelines_dataframe(events_df: pd.DataFrame) -> pd.DataFrame:
    timelines = build_continuation_timelines(events_df)
    if not timelines:
        return pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "symbol",
                "first_timestamp",
                "last_timestamp",
                "persistence_duration_minutes",
                "event_count",
                "event_types",
            ]
        )
    rows = []
    for timeline in timelines:
        rows.append(
            {
                "continuation_id": timeline.continuation_id,
                "setup_id": timeline.setup_id,
                "symbol": timeline.symbol,
                "first_timestamp": timeline.first_timestamp,
                "last_timestamp": timeline.last_timestamp,
                "persistence_duration_minutes": timeline.persistence_duration_minutes,
                "event_count": len(timeline.ordered_events),
                "event_types": "|".join(event.event_type for event in timeline.ordered_events),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["symbol", "first_timestamp", "continuation_id"],
        kind="stable",
    ).reset_index(drop=True)
