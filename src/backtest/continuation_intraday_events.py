from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


EVENT_TYPES = (
    "SETUP",
    "PROBE_ENTRY",
    "ADD_ATTEMPT",
    "ADD_CONFIRMED",
    "SIZE_INCREASE",
    "PERSISTENCE_CONFIRMED",
    "REDUCTION_TRIGGER",
    "EXIT_TRIGGER",
    "INVALIDATION",
)


@dataclass(frozen=True)
class ContinuationIntradayEvent:
    setup_id: str
    continuation_id: str
    symbol: str
    timestamp: pd.Timestamp | None
    event_type: str
    replay_state: str
    participation_quality_label: str
    expansion_score: float
    fragility_score: float
    continuation_risk_score: float
    size_multiplier: float
    allow_add: bool


@dataclass(frozen=True)
class ContinuationIntradayEventConfig:
    persistence_minutes: int = 15


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


def _normalize_intraday_bars(intraday_bars_df: pd.DataFrame) -> pd.DataFrame:
    if intraday_bars_df.empty:
        return pd.DataFrame(
            columns=["symbol", "bar_start_ts", "bar_end_ts", "bar_date", "open", "high", "low", "close", "volume"]
        )
    frame = intraday_bars_df.copy()
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    frame["bar_start_ts"] = pd.to_datetime(frame["bar_start_ts"], errors="coerce", utc=True)
    frame["bar_end_ts"] = pd.to_datetime(frame.get("bar_end_ts"), errors="coerce", utc=True)
    if "bar_date" not in frame.columns:
        frame["bar_date"] = frame["bar_start_ts"].dt.strftime("%Y-%m-%d")
    frame["bar_date"] = frame["bar_date"].astype(str)
    return frame.sort_values(["symbol", "bar_date", "bar_start_ts"], kind="stable").reset_index(drop=True)


def _session_bars(intraday_bars_df: pd.DataFrame, symbol: str, session_date: str) -> pd.DataFrame:
    if intraday_bars_df.empty:
        return intraday_bars_df.copy()
    scoped = intraday_bars_df[
        intraday_bars_df["symbol"].astype(str).eq(str(symbol).upper())
        & intraday_bars_df["bar_date"].astype(str).eq(str(session_date))
    ].copy()
    return scoped.sort_values("bar_start_ts", kind="stable").reset_index(drop=True)


def _bar_at_or_after(session: pd.DataFrame, target_ts: pd.Timestamp | None) -> pd.Timestamp | None:
    if session.empty or target_ts is None or pd.isna(target_ts):
        return pd.NaT
    timestamp = pd.Timestamp(target_ts)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    contains = session[
        (session["bar_start_ts"] <= timestamp)
        & ((session["bar_end_ts"] > timestamp) | session["bar_end_ts"].isna())
    ]
    if not contains.empty:
        return pd.Timestamp(contains.iloc[0]["bar_start_ts"])
    after = session[session["bar_start_ts"] >= timestamp]
    if not after.empty:
        return pd.Timestamp(after.iloc[0]["bar_start_ts"])
    return pd.NaT


def _next_bar(session: pd.DataFrame, anchor_ts: pd.Timestamp | None, offset: int = 1) -> pd.Timestamp | None:
    if session.empty or anchor_ts is None or pd.isna(anchor_ts):
        return pd.NaT
    rows = session[session["bar_start_ts"] >= pd.Timestamp(anchor_ts)].reset_index(drop=True)
    if rows.empty:
        return pd.NaT
    idx = min(max(offset, 0), len(rows) - 1)
    return pd.Timestamp(rows.iloc[idx]["bar_start_ts"])


def _timestamp_plus_minutes(session: pd.DataFrame, anchor_ts: pd.Timestamp | None, minutes: int) -> pd.Timestamp | None:
    if session.empty or anchor_ts is None or pd.isna(anchor_ts):
        return pd.NaT
    target = pd.Timestamp(anchor_ts) + pd.Timedelta(minutes=minutes)
    return _bar_at_or_after(session, target)


def _terminal_like(row: pd.Series) -> bool:
    replay_state = _safe_text(row.get("replay_state"), "UNKNOWN")
    transition_reason = _safe_text(row.get("transition_reason"))
    size_multiplier = _safe_float(row.get("size_multiplier"), 0.0)
    state_label = _safe_text(row.get("state_label"), "UNKNOWN")
    return (
        replay_state == "EXITED"
        or transition_reason in {"dislocation_exit", "size_to_zero", "no_live_position", "fragile_exit"}
        or size_multiplier <= 0.0
        or state_label == "DISLOCATION"
    )


def _add_attempt_open(row: pd.Series) -> bool:
    return (
        _safe_bool(row.get("exposure_allow_add"))
        or _safe_text(row.get("staged_gate_stage")) == "stage_2_add"
        or _safe_bool(row.get("quality_aware_add_allowed"))
    )


def _add_confirmed(row: pd.Series) -> bool:
    return _safe_bool(row.get("final_add_allowed")) or _safe_bool(row.get("add_activated"))


def _build_event_record(
    row: pd.Series,
    continuation_id: str,
    event_index: int,
    event_type: str,
    timestamp: pd.Timestamp | None,
    intraday_match_status: str,
) -> dict[str, Any]:
    return {
        "setup_id": _safe_text(row.get("setup_id"), "unknown_setup"),
        "continuation_id": continuation_id,
        "symbol": _safe_text(row.get("symbol"), "UNKNOWN"),
        "timestamp": timestamp,
        "event_type": event_type,
        "replay_state": _safe_text(row.get("replay_state"), "UNKNOWN"),
        "participation_quality_label": _safe_text(row.get("participation_quality_label"), "UNKNOWN"),
        "expansion_score": _safe_float(row.get("expansion_score"), 0.0),
        "fragility_score": _safe_float(row.get("fragility_score"), 0.0),
        "continuation_risk_score": _safe_float(row.get("continuation_risk_score"), 0.0),
        "size_multiplier": _safe_float(row.get("size_multiplier"), 0.0),
        "allow_add": _safe_bool(row.get("final_add_allowed")),
        "event_index": event_index,
        "event_id": f"{continuation_id}|event_{event_index:03d}",
        "raw_trade_id": _safe_text(row.get("raw_trade_id") or row.get("trade_id"), "unknown_trade"),
        "raw_signal_id": (_safe_text(row.get("raw_signal_id") or row.get("signal_id")) or None),
        "intraday_match_status": intraday_match_status,
        "setup_timestamp": row.get("setup_timestamp"),
        "entry_ts": row.get("entry_ts"),
        "exit_ts": row.get("exit_ts"),
        "breakout_timestamp": row.get("breakout_timestamp"),
        "session_date": _safe_text(row.get("setup_session_date") or row.get("session_date"), "unknown_date"),
        "transition_reason": _safe_text(row.get("transition_reason")),
        "state_label": _safe_text(row.get("state_label"), "UNKNOWN"),
    }


def build_continuation_intraday_events(
    setup_frame: pd.DataFrame,
    intraday_bars_df: pd.DataFrame,
    config: ContinuationIntradayEventConfig = ContinuationIntradayEventConfig(),
) -> pd.DataFrame:
    if setup_frame.empty:
        return pd.DataFrame(
            columns=[
                "setup_id",
                "continuation_id",
                "symbol",
                "timestamp",
                "event_type",
                "replay_state",
                "participation_quality_label",
                "expansion_score",
                "fragility_score",
                "continuation_risk_score",
                "size_multiplier",
                "allow_add",
                "event_index",
                "event_id",
                "raw_trade_id",
                "raw_signal_id",
                "intraday_match_status",
                "setup_timestamp",
                "entry_ts",
                "exit_ts",
                "breakout_timestamp",
                "session_date",
                "transition_reason",
                "state_label",
            ]
        )

    intraday = _normalize_intraday_bars(intraday_bars_df)
    frame = setup_frame.copy()
    for column in ("setup_timestamp", "entry_ts", "exit_ts", "breakout_timestamp", "timestamp"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)

    all_events: list[dict[str, Any]] = []
    for setup_id, group in frame.groupby("setup_id", dropna=False, sort=False):
        group = group.sort_values(["setup_member_index", "setup_timestamp", "trade_id"], kind="stable").reset_index(drop=True)
        for member_ordinal, (_, row) in enumerate(group.iterrows(), start=1):
            continuation_id = f"{_safe_text(setup_id, 'unknown_setup')}|cont_{member_ordinal:03d}"
            session = _session_bars(
                intraday,
                _safe_text(row.get("symbol"), "UNKNOWN"),
                _safe_text(row.get("setup_session_date") or row.get("session_date"), "unknown_date"),
            )
            intraday_match_status = _safe_text(row.get("intraday_match_status"), "unmatched_shadow_only")
            if intraday_match_status == "matched_master_pending_bars":
                intraday_match_status = "matched_session_bars" if not session.empty else "missing_intraday_session"

            setup_ts = _bar_at_or_after(session, row.get("breakout_timestamp"))
            if pd.isna(setup_ts):
                setup_ts = _bar_at_or_after(session, row.get("setup_timestamp"))
            if pd.isna(setup_ts):
                setup_ts = row.get("setup_timestamp")
            entry_ts = _bar_at_or_after(session, row.get("entry_ts"))
            if pd.isna(entry_ts):
                entry_ts = _bar_at_or_after(session, row.get("timestamp"))
            exit_ts = _bar_at_or_after(session, row.get("exit_ts"))

            event_index = 1
            events_for_row: list[dict[str, Any]] = []
            events_for_row.append(
                _build_event_record(row, continuation_id, event_index, "SETUP", setup_ts, intraday_match_status)
            )
            event_index += 1

            immediate_invalid = _terminal_like(row)
            live_position = _safe_float(row.get("size_multiplier"), 0.0) > 0.0 and not immediate_invalid
            probe_ts = entry_ts if not pd.isna(entry_ts) else setup_ts

            if live_position:
                events_for_row.append(
                    _build_event_record(row, continuation_id, event_index, "PROBE_ENTRY", probe_ts, intraday_match_status)
                )
                event_index += 1

                if _add_attempt_open(row):
                    attempt_ts = _next_bar(session, probe_ts, offset=1)
                    if pd.isna(attempt_ts):
                        attempt_ts = probe_ts
                    events_for_row.append(
                        _build_event_record(row, continuation_id, event_index, "ADD_ATTEMPT", attempt_ts, intraday_match_status)
                    )
                    event_index += 1

                    if _add_confirmed(row):
                        confirm_ts = _next_bar(session, attempt_ts, offset=1)
                        if pd.isna(confirm_ts):
                            confirm_ts = attempt_ts
                        events_for_row.append(
                            _build_event_record(row, continuation_id, event_index, "ADD_CONFIRMED", confirm_ts, intraday_match_status)
                        )
                        event_index += 1

                        size_ts = _next_bar(session, confirm_ts, offset=1)
                        if pd.isna(size_ts):
                            size_ts = confirm_ts
                        events_for_row.append(
                            _build_event_record(row, continuation_id, event_index, "SIZE_INCREASE", size_ts, intraday_match_status)
                        )
                        event_index += 1

                if not _safe_text(row.get("replay_state")) == "REDUCING":
                    persist_ts = _timestamp_plus_minutes(session, probe_ts, config.persistence_minutes)
                    if pd.isna(persist_ts):
                        persist_ts = _next_bar(session, probe_ts, offset=1)
                    if not pd.isna(persist_ts):
                        events_for_row.append(
                            _build_event_record(
                                row,
                                continuation_id,
                                event_index,
                                "PERSISTENCE_CONFIRMED",
                                persist_ts,
                                intraday_match_status,
                            )
                        )
                        event_index += 1

                if _safe_text(row.get("replay_state")) == "REDUCING" or _safe_text(row.get("state_label")) == "DISLOCATION":
                    reduction_anchor = exit_ts if not pd.isna(exit_ts) else _next_bar(session, probe_ts, offset=2)
                    if pd.isna(reduction_anchor):
                        reduction_anchor = probe_ts
                    events_for_row.append(
                        _build_event_record(
                            row,
                            continuation_id,
                            event_index,
                            "REDUCTION_TRIGGER",
                            reduction_anchor,
                            intraday_match_status,
                        )
                    )
                    event_index += 1

                if _safe_text(row.get("replay_state")) == "EXITED" or _safe_text(row.get("state_label")) == "DISLOCATION":
                    trigger_ts = exit_ts
                    if pd.isna(trigger_ts):
                        trigger_ts = _next_bar(session, probe_ts, offset=3)
                    if pd.isna(trigger_ts):
                        trigger_ts = probe_ts
                    events_for_row.append(
                        _build_event_record(
                            row,
                            continuation_id,
                            event_index,
                            "EXIT_TRIGGER",
                            trigger_ts,
                            intraday_match_status,
                        )
                    )
            else:
                invalid_ts = entry_ts if not pd.isna(entry_ts) else setup_ts
                events_for_row.append(
                    _build_event_record(
                        row,
                        continuation_id,
                        event_index,
                        "INVALIDATION",
                        invalid_ts,
                        intraday_match_status,
                    )
                )

            all_events.extend(events_for_row)

    events_df = pd.DataFrame(all_events)
    if events_df.empty:
        return events_df
    events_df["timestamp"] = pd.to_datetime(events_df["timestamp"], errors="coerce", utc=True)
    return events_df.sort_values(
        ["setup_id", "continuation_id", "timestamp", "event_index", "event_id"],
        kind="stable",
    ).reset_index(drop=True)


def build_intraday_event_summary(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(columns=["event_type", "intraday_match_status", "event_count", "continuation_count"])
    summary = (
        events_df.groupby(["event_type", "intraday_match_status"], dropna=False)
        .agg(
            event_count=("event_id", "size"),
            continuation_count=("continuation_id", "nunique"),
        )
        .reset_index()
    )
    return summary.sort_values(
        ["event_count", "continuation_count", "event_type"],
        ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)
