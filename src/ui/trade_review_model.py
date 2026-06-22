from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.analysis_sector import SYMBOL_TO_SECTOR
from backtest.data_loader import DEFAULT_BASE_DIR, load_daily_bars
from strategy.conditions import find_last_index_before, prepare_condition_frame


@dataclass(frozen=True)
class TradeReviewRecord:
    trade_id: str
    symbol: str
    strategy_id: str
    sector: str
    regime: str
    signal_bar_index: int | None
    signal_bar_time: pd.Timestamp | None
    entry_fill_bar_time: pd.Timestamp | None
    exit_signal_bar_time: pd.Timestamp | None
    exit_fill_bar_time: pd.Timestamp | None
    entry_rule: str
    exit_rule: str
    entry_time: pd.Timestamp
    entry_price: float
    entry_fill_price: float
    exit_time: pd.Timestamp
    exit_price: float
    exit_fill_price: float
    breakout_level: float
    stop_price: float
    target_price: float | None
    breakout_flag: bool | None
    ma_trend_flag: bool | None
    trend_break_2bar_flag: bool | None
    stop_hit_flag: bool | None
    entry_order_status: str
    exit_order_status: str
    entry_wait_bars: int | None
    exit_wait_bars: int | None
    unfilled_flag: bool | None
    expired_flag: bool | None
    validation_error: str | None
    expected_pnl: float
    actual_pnl: float
    slippage: float
    holding_time: float
    reason: str
    source: str


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return int(value)
    except Exception:
        return None


def _safe_timestamp(value: Any) -> pd.Timestamp:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return pd.Timestamp("1970-01-01T00:00:00Z")
    return ts


def _safe_optional_timestamp(value: Any) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _safe_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _infer_regime(entry_time: pd.Timestamp, condition_df: pd.DataFrame) -> str:
    if condition_df.empty or "close" not in condition_df.columns:
        return "UNKNOWN"
    idx = find_last_index_before(condition_df, entry_time)
    if idx is None:
        return "UNKNOWN"
    row = condition_df.iloc[idx]
    ma200 = row.get("ma200")
    if pd.isna(ma200):
        return "UNKNOWN"
    return "BULL" if float(row["close"]) >= float(ma200) else "BEAR"


def _infer_breakout_stop(entry_time: pd.Timestamp, condition_df: pd.DataFrame) -> tuple[float, float]:
    if condition_df.empty:
        return 0.0, 0.0
    idx = find_last_index_before(condition_df, entry_time)
    if idx is None:
        return 0.0, 0.0
    row = condition_df.iloc[idx]
    breakout_level = float(row["rolling_high_20"]) if pd.notna(row.get("rolling_high_20")) else float(row["close"])
    atr = float(row["atr14"]) if pd.notna(row.get("atr14")) else 0.0
    stop_price = breakout_level - (2.0 * atr) if atr > 0 else breakout_level
    return breakout_level, stop_price


def build_trade_review(trade_result: dict[str, Any], price_df: pd.DataFrame) -> TradeReviewRecord:
    symbol = str(trade_result.get("symbol", "")).upper()
    trade_id = str(trade_result.get("trade_id", ""))
    strategy_id = str(trade_result.get("strategy_id", "us_swing_breakout_v0"))
    entry_time = _safe_timestamp(trade_result.get("entry_time"))
    exit_time = _safe_timestamp(trade_result.get("exit_time"))
    condition_df = prepare_condition_frame(price_df)

    breakout_level = _safe_float(trade_result.get("breakout_level"), default=float("nan"))
    stop_price = _safe_float(trade_result.get("stop_price"), default=float("nan"))
    if pd.isna(breakout_level) or pd.isna(stop_price):
        inferred_breakout, inferred_stop = _infer_breakout_stop(entry_time, condition_df)
        if pd.isna(breakout_level):
            breakout_level = inferred_breakout
        if pd.isna(stop_price):
            stop_price = inferred_stop

    regime_raw = str(trade_result.get("regime", "")).upper().strip()
    regime = regime_raw if regime_raw in {"BULL", "BEAR"} else _infer_regime(entry_time, condition_df)
    sector_raw = str(trade_result.get("sector", "")).upper().strip()
    sector = sector_raw if sector_raw else SYMBOL_TO_SECTOR.get(symbol, "UNMAPPED")

    source_raw = str(trade_result.get("source", "")).strip().lower()
    source = source_raw if source_raw else "backtest"

    expected_pnl = _safe_float(trade_result.get("expected_pnl"))
    actual_pnl = _safe_float(trade_result.get("actual_pnl"))
    slippage = _safe_float(trade_result.get("slippage"), default=_safe_float(trade_result.get("entry_fill_price")) - _safe_float(trade_result.get("entry_price")))
    holding_time = _safe_float(trade_result.get("holding_time"), default=max(0.0, float((exit_time - entry_time).total_seconds())))

    return TradeReviewRecord(
        trade_id=trade_id,
        symbol=symbol,
        strategy_id=strategy_id,
        sector=sector,
        regime=regime,
        signal_bar_index=_safe_int(trade_result.get("signal_bar_index")),
        signal_bar_time=_safe_optional_timestamp(trade_result.get("signal_bar_time")),
        entry_fill_bar_time=_safe_optional_timestamp(trade_result.get("entry_fill_bar_time")),
        exit_signal_bar_time=_safe_optional_timestamp(trade_result.get("exit_signal_bar_time")),
        exit_fill_bar_time=_safe_optional_timestamp(trade_result.get("exit_fill_bar_time")),
        entry_rule=str(trade_result.get("entry_rule", "BREAKOUT + MA_TREND")),
        exit_rule=str(trade_result.get("exit_rule", "")),
        entry_time=entry_time,
        entry_price=_safe_float(trade_result.get("entry_price")),
        entry_fill_price=_safe_float(trade_result.get("entry_fill_price")),
        exit_time=exit_time,
        exit_price=_safe_float(trade_result.get("exit_price")),
        exit_fill_price=_safe_float(trade_result.get("exit_fill_price")),
        breakout_level=_safe_float(breakout_level),
        stop_price=_safe_float(stop_price),
        target_price=trade_result.get("target_price", None),
        breakout_flag=_safe_bool(trade_result.get("breakout_flag")),
        ma_trend_flag=_safe_bool(trade_result.get("ma_trend_flag")),
        trend_break_2bar_flag=_safe_bool(trade_result.get("trend_break_2bar_flag")),
        stop_hit_flag=_safe_bool(trade_result.get("stop_hit_flag")),
        entry_order_status=str(trade_result.get("entry_order_status", "")),
        exit_order_status=str(trade_result.get("exit_order_status", "")),
        entry_wait_bars=_safe_int(trade_result.get("entry_wait_bars")),
        exit_wait_bars=_safe_int(trade_result.get("exit_wait_bars")),
        unfilled_flag=_safe_bool(trade_result.get("unfilled_flag")),
        expired_flag=_safe_bool(trade_result.get("expired_flag")),
        validation_error=(None if trade_result.get("validation_error") in (None, "") else str(trade_result.get("validation_error"))),
        expected_pnl=expected_pnl,
        actual_pnl=actual_pnl,
        slippage=slippage,
        holding_time=holding_time,
        reason=str(trade_result.get("reason", "UNKNOWN")),
        source=source,
    )


def load_trade_reviews(path: str | Path, *, data_dir: str | Path = DEFAULT_BASE_DIR) -> list[TradeReviewRecord]:
    json_path = Path(path)
    if not json_path.exists():
        return []

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    rows: list[dict[str, Any]]
    if isinstance(payload, dict):
        trades = payload.get("trades", [])
        rows = trades if isinstance(trades, list) else []
    elif isinstance(payload, list):
        rows = [row for row in payload if isinstance(row, dict)]
    else:
        rows = []

    if not rows:
        return []

    cache: dict[str, pd.DataFrame] = {}
    records: list[TradeReviewRecord] = []
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if not symbol:
            continue
        if symbol not in cache:
            try:
                cache[symbol] = load_daily_bars(symbol, base_dir=data_dir)
            except Exception:
                cache[symbol] = pd.DataFrame()
        record = build_trade_review(row, cache[symbol])
        records.append(record)

    return records


def to_dataframe(records: list[TradeReviewRecord]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame([asdict(item) for item in records])
