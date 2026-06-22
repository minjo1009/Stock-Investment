from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from strategy.conditions import condition_snapshot, find_last_index_at_or_before, find_last_index_before, prepare_condition_frame


MAX_HOLDING_DAYS = 20


@dataclass(frozen=True)
class TradeAlignmentResult:
    is_aligned: bool
    alignment_result: str
    mismatch_reasons: list[str]
    breakout_condition: bool | None
    ma_condition: bool | None
    exit_condition: bool | None
    entry_signal_index: int | None
    exit_signal_index: int | None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_timestamp(value: Any) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _frame_value(frame: pd.DataFrame, idx: int | None, column: str) -> float | None:
    if idx is None or column not in frame.columns or not (0 <= idx < len(frame)):
        return None
    value = frame.iloc[idx][column]
    if pd.isna(value):
        return None
    return float(value)


def validate_trade_alignment(trade: Any, df: pd.DataFrame) -> TradeAlignmentResult:
    frame = prepare_condition_frame(df)
    entry_time = _safe_timestamp(getattr(trade, "get", lambda _k, _d=None: _d)("entry_time"))
    exit_time = _safe_timestamp(getattr(trade, "get", lambda _k, _d=None: _d)("exit_time"))
    signal_bar_time = _safe_timestamp(getattr(trade, "get", lambda _k, _d=None: _d)("signal_bar_time"))
    exit_signal_bar_time = _safe_timestamp(getattr(trade, "get", lambda _k, _d=None: _d)("exit_signal_bar_time"))
    signal_bar_index_raw = getattr(trade, "get", lambda _k, _d=None: _d)("signal_bar_index")
    signal_reason = str(getattr(trade, "get", lambda _k, _d=None: _d)("reason", "") or "").upper().strip()
    entry_rule = str(getattr(trade, "get", lambda _k, _d=None: _d)("entry_rule", "") or "").upper().strip()
    exit_rule = str(getattr(trade, "get", lambda _k, _d=None: _d)("exit_rule", "") or "").upper().strip()
    stop_price = _safe_float(getattr(trade, "get", lambda _k, _d=None: _d)("stop_price"))
    exit_price = _safe_float(getattr(trade, "get", lambda _k, _d=None: _d)("exit_price"))
    holding_time = _safe_float(getattr(trade, "get", lambda _k, _d=None: _d)("holding_time"))
    stop_hit_flag = getattr(trade, "get", lambda _k, _d=None: _d)("stop_hit_flag")
    trend_break_2bar_flag = getattr(trade, "get", lambda _k, _d=None: _d)("trend_break_2bar_flag")

    try:
        signal_bar_index = int(signal_bar_index_raw) if signal_bar_index_raw is not None else None
    except Exception:
        signal_bar_index = None

    entry_signal_index = signal_bar_index
    if entry_signal_index is None:
        if signal_bar_time is not None:
            entry_signal_index = find_last_index_at_or_before(frame, signal_bar_time)
        elif entry_time is not None:
            entry_signal_index = find_last_index_before(frame, entry_time)

    if exit_signal_bar_time is not None:
        exit_signal_index = find_last_index_at_or_before(frame, exit_signal_bar_time)
    else:
        exit_signal_index = find_last_index_before(frame, exit_time)
    entry_snapshot = condition_snapshot(frame, entry_signal_index)
    exit_snapshot = condition_snapshot(frame, exit_signal_index)

    breakout_condition = entry_snapshot["breakout_condition"]
    ma_condition = entry_snapshot["ma_condition"]
    exit_condition = exit_snapshot["exit_condition"]

    mismatch_reasons: list[str] = []
    if entry_signal_index is None:
        mismatch_reasons.append("missing entry signal bar")
    if exit_time is not None and exit_signal_index is None:
        mismatch_reasons.append("missing exit signal bar")

    if "BREAKOUT" in signal_reason or "BREAKOUT" in entry_rule:
        if breakout_condition is not True:
            mismatch_reasons.append("entry breakout condition is not true on signal bar")
        if ma_condition is not True:
            mismatch_reasons.append("entry MA condition is not true on signal bar")

    if exit_time is not None:
        if str(stop_hit_flag).lower() == "true" or "STOP" in exit_rule:
            inferred_stop_exit = True
        else:
            exit_low = _frame_value(frame, exit_signal_index, "low")
            inferred_stop_exit = (
                stop_price is not None
                and exit_low is not None
                and exit_low <= stop_price
            )
        if str(trend_break_2bar_flag).lower() == "true" or "TREND_BREAK_2BAR" in exit_rule:
            inferred_trend_break = True
        else:
            inferred_trend_break = exit_condition is True
        if "TIME_EXIT" in exit_rule:
            inferred_time_exit = True
        else:
            inferred_time_exit = holding_time is not None and holding_time > (MAX_HOLDING_DAYS * 86400)

        if not inferred_stop_exit and not inferred_time_exit and not inferred_trend_break:
            mismatch_reasons.append("exit trend-break condition is not true on exit signal bar")

    if entry_signal_index is None:
        alignment_result = "UNKNOWN"
    elif mismatch_reasons:
        alignment_result = "MISMATCH"
    else:
        alignment_result = "MATCH"

    return TradeAlignmentResult(
        is_aligned=alignment_result == "MATCH",
        alignment_result=alignment_result,
        mismatch_reasons=mismatch_reasons,
        breakout_condition=breakout_condition,
        ma_condition=ma_condition,
        exit_condition=exit_condition,
        entry_signal_index=entry_signal_index,
        exit_signal_index=exit_signal_index,
    )
