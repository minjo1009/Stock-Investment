from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class AddScaleEvolution:
    continuation_id: str
    timestamp: pd.Timestamp | None
    add_depth: int
    scale_depth: int
    cumulative_size_multiplier: float
    replay_state: str


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


def build_add_scale_lineage(lineage_row_df: pd.DataFrame) -> pd.DataFrame:
    if lineage_row_df.empty:
        return pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "timestamp",
                "event_id",
                "lineage_event_type",
                "add_depth",
                "scale_depth",
                "cumulative_size_multiplier",
                "replay_state",
                "has_add_attempt",
                "has_add_confirmed",
                "has_scale_up",
                "add_linked_to_setup",
                "scale_linked_to_add",
            ]
        )

    rows: list[dict[str, Any]] = []
    for continuation_id, group in lineage_row_df.groupby("continuation_id", dropna=False, sort=False):
        ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        add_depth = 0
        scale_depth = 0
        seen_add_attempt = False
        seen_add_confirmed = False
        for _, row in ordered.iterrows():
            event_type = _safe_text(row.get("lineage_event_type"))
            if event_type == "ADD_ATTEMPT":
                seen_add_attempt = True
            if event_type == "ADD_CONFIRMED":
                add_depth += 1
                seen_add_confirmed = True
            if event_type == "SIZE_INCREASE":
                scale_depth += 1
            rows.append(
                {
                    "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                    "setup_id": _safe_text(row.get("setup_id"), "unknown_setup"),
                    "timestamp": pd.to_datetime(row.get("timestamp"), errors="coerce", utc=True),
                    "event_id": _safe_text(row.get("event_id"), "unknown_event"),
                    "lineage_event_type": event_type,
                    "add_depth": add_depth,
                    "scale_depth": scale_depth,
                    "cumulative_size_multiplier": _safe_float(
                        row.get("current_size_multiplier", row.get("size_multiplier")),
                        0.0,
                    ),
                    "replay_state": _safe_text(row.get("replay_state"), "UNKNOWN"),
                    "has_add_attempt": seen_add_attempt,
                    "has_add_confirmed": seen_add_confirmed,
                    "has_scale_up": scale_depth > 0,
                    "add_linked_to_setup": add_depth > 0 and bool(_safe_text(row.get("setup_id"))),
                    "scale_linked_to_add": scale_depth > 0 and add_depth > 0,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["continuation_id", "timestamp", "event_id"],
        kind="stable",
    ).reset_index(drop=True)
