from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

import pandas as pd


ContinuationEventType = Literal[
    "SETUP",
    "PROBE_ENTRY",
    "ADD",
    "SCALE_UP",
    "PERSIST",
    "REDUCE",
    "EXIT",
    "INVALIDATE",
]


@dataclass(frozen=True)
class ContinuationEventIdentityConfig:
    timestamp_column: str = "timestamp"
    symbol_column: str = "symbol"
    trade_id_column: str = "trade_id"
    signal_id_column: str = "signal_id"
    session_date_column: str = "session_date"


@dataclass(frozen=True)
class ContinuationEvent:
    continuation_id: str
    symbol: str
    session_date: str
    event_index: int
    event_type: str
    timestamp: pd.Timestamp | None
    trade_id: str
    signal_id: str | None
    replay_state: str
    participation_quality_label: str
    state_label: str
    size_multiplier: float
    add_activated: bool
    transition_reason: str


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


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _ordered_columns(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in frame.columns]


def _normalize_replay_inputs(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if replay_trace_df.empty:
        return pd.DataFrame()

    frame = replay_trace_df.copy()
    if lifecycle_rows_df is not None and not lifecycle_rows_df.empty:
        merge_columns = [
            "lifecycle_id",
            "trade_id",
            "signal_id",
            "timestamp",
            "symbol",
            "session_date",
            "sequence_in_lifecycle",
            "expansion_score",
            "fragility_score",
            "confidence",
            "factor_budget_allowed",
            "exposure_allow_add",
            "staged_gate_stage",
            "staged_add_allowed",
            "final_add_allowed",
        ]
        available_merge = _ordered_columns(lifecycle_rows_df, merge_columns)
        extra_columns = [
            column
            for column in available_merge
            if column not in {"lifecycle_id", "trade_id"} and column not in frame.columns
        ]
        if extra_columns:
            frame = frame.merge(
                lifecycle_rows_df[["lifecycle_id", "trade_id", *extra_columns]].drop_duplicates(
                    subset=["lifecycle_id", "trade_id"]
                ),
                on=["lifecycle_id", "trade_id"],
                how="left",
            )

    frame["timestamp"] = pd.to_datetime(frame.get("timestamp"), errors="coerce", utc=True)
    if "session_date" not in frame.columns:
        frame["session_date"] = frame["timestamp"].dt.strftime("%Y-%m-%d").fillna("unknown_date")
    frame["session_date"] = frame["session_date"].astype(str)
    if "signal_id" not in frame.columns:
        frame["signal_id"] = None
    frame = frame.sort_values(
        _ordered_columns(frame, ["lifecycle_id", "timestamp", "trade_id", "signal_id"]),
        kind="stable",
    ).reset_index(drop=True)
    return frame


def _classify_event_type(row: pd.Series, previous_row: pd.Series | None) -> str:
    replay_state = _safe_text(row.get("replay_state"), "UNKNOWN")
    previous_state = _safe_text(row.get("previous_replay_state"), "UNKNOWN")
    transition_reason = _safe_text(row.get("transition_reason"))
    add_activated = _safe_bool(row.get("add_activated"))
    size_increased = _safe_bool(row.get("size_increased_vs_prev"))
    size_multiplier = _safe_float(row.get("size_multiplier"), 0.0)
    event_index = int(_safe_float(row.get("event_index"), 0.0))
    prior_was_live = previous_row is not None and _safe_bool(previous_row.get("is_live_position"))

    if replay_state == "EXITED" and (
        event_index == 1 or previous_state == "IDLE"
    ) and transition_reason in {"dislocation_exit", "size_to_zero", "no_live_position"}:
        return "INVALIDATE"
    if replay_state == "EXITED":
        return "EXIT"
    if replay_state == "REDUCING":
        return "REDUCE"
    if add_activated and previous_state == "PROBE" and replay_state == "BUILDING":
        return "ADD"
    if add_activated and size_increased and prior_was_live:
        return "SCALE_UP"
    if replay_state == "PERSISTING":
        return "PERSIST"
    if replay_state == "PROBE":
        return "PROBE_ENTRY"
    if event_index == 1 and size_multiplier > 0.0:
        return "SETUP"
    return "SETUP"


def build_continuation_events(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame,
    config: ContinuationEventIdentityConfig = ContinuationEventIdentityConfig(),
) -> tuple[ContinuationEvent, ...]:
    frame = _normalize_replay_inputs(replay_trace_df, lifecycle_rows_df)
    if frame.empty:
        return ()

    events: list[ContinuationEvent] = []
    for continuation_id, group in frame.groupby("lifecycle_id", dropna=False, sort=False):
        group = group.sort_values(
            _ordered_columns(group, [config.timestamp_column, config.trade_id_column, config.signal_id_column]),
            kind="stable",
        ).reset_index(drop=True)
        previous_row: pd.Series | None = None
        for position, (_, raw_row) in enumerate(group.iterrows(), start=1):
            row = raw_row.copy()
            row["event_index"] = position
            event_type = _classify_event_type(row, previous_row)
            events.append(
                ContinuationEvent(
                    continuation_id=_safe_text(continuation_id, "unknown_continuation"),
                    symbol=_safe_text(row.get(config.symbol_column), "unknown_symbol"),
                    session_date=_safe_text(row.get(config.session_date_column), "unknown_date"),
                    event_index=position,
                    event_type=event_type,
                    timestamp=row.get(config.timestamp_column),
                    trade_id=_safe_text(row.get(config.trade_id_column), "unknown_trade"),
                    signal_id=(_safe_text(row.get(config.signal_id_column)) or None),
                    replay_state=_safe_text(row.get("replay_state"), "UNKNOWN"),
                    participation_quality_label=_safe_text(row.get("participation_quality_label"), "UNKNOWN"),
                    state_label=_safe_text(row.get("state_label"), "UNKNOWN"),
                    size_multiplier=_safe_float(row.get("size_multiplier"), 0.0),
                    add_activated=_safe_bool(row.get("add_activated")),
                    transition_reason=_safe_text(row.get("transition_reason")),
                )
            )
            previous_row = row
    return tuple(events)


def normalize_continuation_event_rows(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frame = _normalize_replay_inputs(replay_trace_df, lifecycle_rows_df)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "continuation_id",
                "symbol",
                "session_date",
                "event_index",
                "event_id",
                "event_type",
                "timestamp",
                "trade_id",
                "signal_id",
                "replay_state",
                "previous_replay_state",
                "participation_quality_label",
                "state_label",
                "size_multiplier",
                "add_activated",
                "transition_reason",
            ]
        )

    rows: list[dict[str, Any]] = []
    for continuation_id, group in frame.groupby("lifecycle_id", dropna=False, sort=False):
        group = group.sort_values(
            _ordered_columns(group, ["timestamp", "trade_id", "signal_id"]),
            kind="stable",
        ).reset_index(drop=True)
        previous_row: pd.Series | None = None
        for position, (_, raw_row) in enumerate(group.iterrows(), start=1):
            row = raw_row.copy()
            row["event_index"] = position
            event_type = _classify_event_type(row, previous_row)
            event_id = f"{_safe_text(continuation_id, 'unknown_continuation')}|{position:03d}|{event_type.lower()}"
            rows.append(
                {
                    "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                    "symbol": _safe_text(row.get("symbol"), "unknown_symbol"),
                    "session_date": _safe_text(row.get("session_date"), "unknown_date"),
                    "event_index": position,
                    "event_id": event_id,
                    "event_type": event_type,
                    "timestamp": row.get("timestamp"),
                    "trade_id": _safe_text(row.get("trade_id"), "unknown_trade"),
                    "signal_id": (_safe_text(row.get("signal_id")) or None),
                    "replay_state": _safe_text(row.get("replay_state"), "UNKNOWN"),
                    "previous_replay_state": _safe_text(row.get("previous_replay_state"), "UNKNOWN"),
                    "participation_quality_label": _safe_text(row.get("participation_quality_label"), "UNKNOWN"),
                    "state_label": _safe_text(row.get("state_label"), "UNKNOWN"),
                    "size_multiplier": _safe_float(row.get("size_multiplier"), 0.0),
                    "add_activated": _safe_bool(row.get("add_activated")),
                    "transition_reason": _safe_text(row.get("transition_reason")),
                }
            )
            previous_row = row
    return pd.DataFrame(rows)


def build_continuation_event_type_summary(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df.empty:
        return pd.DataFrame(columns=["event_type", "event_count", "add_activation_count", "avg_size_multiplier"])
    summary = (
        event_df.groupby("event_type", dropna=False)
        .agg(
            event_count=("event_type", "size"),
            add_activation_count=("add_activated", "sum"),
            avg_size_multiplier=("size_multiplier", "mean"),
        )
        .reset_index()
    )
    summary["avg_size_multiplier"] = pd.to_numeric(summary["avg_size_multiplier"], errors="coerce").fillna(0.0).round(6)
    summary["add_activation_count"] = pd.to_numeric(summary["add_activation_count"], errors="coerce").fillna(0).astype(int)
    summary["event_count"] = pd.to_numeric(summary["event_count"], errors="coerce").fillna(0).astype(int)
    return summary.sort_values(["event_count", "event_type"], ascending=[False, True], kind="stable").reset_index(drop=True)


def build_continuation_event_identity(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_df = normalize_continuation_event_rows(replay_trace_df, lifecycle_rows_df)
    return event_df, build_continuation_event_type_summary(event_df)


def events_to_frame(events: tuple[ContinuationEvent, ...]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame()
    return pd.DataFrame([asdict(event) for event in events])
