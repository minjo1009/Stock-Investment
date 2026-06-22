from __future__ import annotations

from typing import Any

import pandas as pd

from backtest.indicators import compute_indicators


BREAKOUT_WINDOW_BASELINE = 20
BREAKOUT_WINDOW_A10 = 10
BREAKOUT_WINDOW_CRB = 20
DEFAULT_BREAKOUT_MODE = "BASELINE"
MA_FAST = 20
MA_SLOW = 50
MA_REGIME = 200
ATR_PERIOD = 14
LIQUIDITY_WINDOW = 20


def prepare_condition_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Build the canonical strategy-condition frame.

    This is the single source of truth for:
    - breakout condition
    - MA trend condition
    - exit trend-break condition
    - shared support fields used by engine/UI review
    """
    if df.empty:
        return pd.DataFrame()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()

    out = compute_indicators(df.copy())
    if "timestamp" in out.columns:
        out = out.sort_values("timestamp").reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)

    for column in ("open", "high", "low", "close", "volume"):
        out[column] = pd.to_numeric(out[column], errors="coerce")

    close = out["close"]
    high = out["high"]
    low = out["low"]
    volume = out["volume"]

    out["ma20"] = close.rolling(MA_FAST).mean()
    out["ma50"] = close.rolling(MA_SLOW).mean()
    out["ma200"] = close.rolling(MA_REGIME).mean()

    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr14"] = true_range.rolling(ATR_PERIOD).mean()

    out["avg_volume_20"] = volume.rolling(LIQUIDITY_WINDOW).mean()
    out["avg_turnover_20"] = (close * volume).rolling(LIQUIDITY_WINDOW).mean()

    # Exclude the current bar high to avoid look-ahead.
    out["rolling_high_20"] = high.rolling(BREAKOUT_WINDOW_BASELINE).max().shift(1)
    out["rolling_high_10"] = high.rolling(BREAKOUT_WINDOW_A10).max().shift(1)
    out["rolling_low_20"] = low.rolling(BREAKOUT_WINDOW_CRB).min().shift(1)
    out["breakout_high_20"] = out["rolling_high_20"]

    # CRB (Compressed Range Breakout) support columns.
    out["atr5"] = true_range.rolling(5).mean()
    out["atr20"] = true_range.rolling(20).mean()
    out["crb_recent_vol"] = out["atr5"].shift(1)
    out["crb_past_vol"] = out["atr20"].shift(6)
    out["crb_range_pct"] = (out["rolling_high_20"] - out["rolling_low_20"]) / close.shift(1)
    near_high_level = out["rolling_high_20"] * 0.995
    out["crb_touch_count_5"] = (
        (high.shift(1) >= near_high_level).astype(int)
        + (high.shift(2) >= near_high_level).astype(int)
        + (high.shift(3) >= near_high_level).astype(int)
        + (high.shift(4) >= near_high_level).astype(int)
        + (high.shift(5) >= near_high_level).astype(int)
    )
    return out


def find_last_index_before(df: pd.DataFrame, timestamp: Any) -> int | None:
    if df.empty or "timestamp" not in df.columns or timestamp is None:
        return None
    ts = pd.Timestamp(timestamp)
    matches = df.index[df["timestamp"] < ts]
    if len(matches) == 0:
        return None
    return int(matches[-1])


def find_last_index_at_or_before(df: pd.DataFrame, timestamp: Any) -> int | None:
    if df.empty or "timestamp" not in df.columns or timestamp is None:
        return None
    ts = pd.Timestamp(timestamp)
    matches = df.index[df["timestamp"] <= ts]
    if len(matches) == 0:
        return None
    return int(matches[-1])


def _normalize_index(df: pd.DataFrame, idx: Any) -> int | None:
    if df.empty or idx is None:
        return None
    if isinstance(idx, int):
        if 0 <= idx < len(df):
            return idx
        return None
    if isinstance(idx, str):
        return find_last_index_at_or_before(df, idx)
    if isinstance(idx, pd.Timestamp):
        return find_last_index_at_or_before(df, idx)
    return None


def _safe_bool(value: Any) -> bool | None:
    if value is None or pd.isna(value):
        return None
    return bool(value)


def _numeric_at(df: pd.DataFrame, idx: Any, column: str) -> float | None:
    pos = _normalize_index(df, idx)
    if pos is None or column not in df.columns:
        return None
    value = df.iloc[pos][column]
    if pd.isna(value):
        return None
    return float(value)


def close_above_ma50(df: pd.DataFrame, idx: Any) -> bool | None:
    close_now = _numeric_at(df, idx, "close")
    ma50 = _numeric_at(df, idx, "ma50")
    if close_now is None or ma50 is None:
        return None
    return close_now > ma50


def fast_ma_above_slow(df: pd.DataFrame, idx: Any) -> bool | None:
    ma20 = _numeric_at(df, idx, "ma20")
    ma50 = _numeric_at(df, idx, "ma50")
    if ma20 is None or ma50 is None:
        return None
    return ma20 > ma50


def _normalize_breakout_mode(breakout_mode: str | None) -> str:
    mode = str(breakout_mode or DEFAULT_BREAKOUT_MODE).strip().upper()
    if mode == "A_10":
        return "A_10"
    if mode == "CRB":
        return "CRB"
    return "BASELINE"


def breakout_window_for_mode(breakout_mode: str | None) -> int:
    mode = _normalize_breakout_mode(breakout_mode)
    if mode == "A_10":
        return BREAKOUT_WINDOW_A10
    return BREAKOUT_WINDOW_BASELINE


def breakout_column_for_mode(breakout_mode: str | None) -> str:
    mode = _normalize_breakout_mode(breakout_mode)
    return "rolling_high_10" if mode == "A_10" else "rolling_high_20"


def _is_crb_breakout(df: pd.DataFrame, idx: Any) -> bool | None:
    close_now = _numeric_at(df, idx, "close")
    range_high = _numeric_at(df, idx, "rolling_high_20")
    range_pct = _numeric_at(df, idx, "crb_range_pct")
    recent_vol = _numeric_at(df, idx, "crb_recent_vol")
    past_vol = _numeric_at(df, idx, "crb_past_vol")
    touch_count = _numeric_at(df, idx, "crb_touch_count_5")
    if None in (close_now, range_high, range_pct, recent_vol, past_vol, touch_count):
        return None
    if past_vol <= 0:
        return None
    compressed = (recent_vol / past_vol) <= 0.65
    touch_ok = touch_count >= 2
    return bool(
        close_now > range_high
        and range_pct <= 0.10
        and compressed
        and touch_ok
    )


def is_breakout(df: pd.DataFrame, idx: Any, *, breakout_mode: str | None = None) -> bool | None:
    mode = _normalize_breakout_mode(breakout_mode)
    if mode == "CRB":
        return _is_crb_breakout(df, idx)
    close_now = _numeric_at(df, idx, "close")
    rolling_high = _numeric_at(df, idx, breakout_column_for_mode(mode))
    if close_now is None or rolling_high is None:
        return None
    return close_now >= rolling_high


def is_ma_trend(df: pd.DataFrame, idx: Any) -> bool | None:
    close_vs_ma50 = close_above_ma50(df, idx)
    fast_vs_slow = fast_ma_above_slow(df, idx)
    if close_vs_ma50 is None or fast_vs_slow is None:
        return None
    return close_vs_ma50 and fast_vs_slow


def is_exit_condition(df: pd.DataFrame, idx: Any) -> bool | None:
    pos = _normalize_index(df, idx)
    if pos is None or pos < 1:
        return None
    close_now = _numeric_at(df, pos, "close")
    close_prev = _numeric_at(df, pos - 1, "close")
    ma20_now = _numeric_at(df, pos, "ma20")
    ma20_prev = _numeric_at(df, pos - 1, "ma20")
    if None in (close_now, close_prev, ma20_now, ma20_prev):
        return None
    return bool(close_now < ma20_now and close_prev < ma20_prev)


def condition_snapshot(df: pd.DataFrame, idx: Any) -> dict[str, bool | None]:
    return {
        "breakout_condition": is_breakout(df, idx),
        "close_above_ma50": close_above_ma50(df, idx),
        "ma20_above_ma50": fast_ma_above_slow(df, idx),
        "ma_condition": is_ma_trend(df, idx),
        "exit_condition": is_exit_condition(df, idx),
    }
