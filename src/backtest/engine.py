from __future__ import annotations

import argparse
import json
import logging
import statistics
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from math import floor
from pathlib import Path

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, REQUIRED_COLUMNS, Bar, load_daily_bars, load_universe_daily_bars
from backtest.models import TradeResult
from backtest.analysis_sector import SYMBOL_TO_SECTOR
from strategy.conditions import is_breakout, is_exit_condition, is_ma_trend, prepare_condition_frame
from strategy.validator import validate_trade_alignment


STRATEGY_ID = "us_swing_breakout_v0"

# Fixed parameters from docs/strategy_spec_us_swing_breakout_v0.md
BREAKOUT_WINDOW = 20
MA_FAST = 20
MA_SLOW = 50
ATR_PERIOD = 14
ATR_MULT = 2.0
MAX_HOLDING_DAYS = 20
MAX_WAIT_BARS = 3
GAP_FILTER_MAX = 0.03
ENTRY_LIMIT_BUFFER = 0.001
NEXT_BAR_EXECUTION_CONVENTION = (
    "Signals are detected after bar i close. Entry gap checks and non-stop order "
    "execution are evaluated on bar i+1 when that bar is available."
)

MIN_CLOSE = 5.0
MIN_AVG_VOLUME = 1_000_000.0
MIN_AVG_TURNOVER = 20_000_000.0
MAX_POSITION_WEIGHT = 0.10
MIN_UNIVERSE_SIZE = 10

logger = logging.getLogger(__name__)


@dataclass
class OpenPosition:
    symbol: str
    quantity: float
    entry_index: int
    entry_time: datetime
    entry_price: float
    entry_fill_price: float
    breakout_level: float
    stop_price: float
    reason: str
    regime: str
    signal_index: int
    signal_time: datetime
    breakout_flag: bool
    ma_trend_flag: bool
    canonical_lifecycle_id: str | None = None
    had_exit_expired: bool = False


@dataclass
class PendingEntryOrder:
    symbol: str
    signal_index: int
    signal_time: datetime
    start_index: int
    limit_price: float
    quantity: float
    breakout_level: float
    stop_price: float
    regime: str
    breakout_flag: bool
    ma_trend_flag: bool
    signal_close: float
    wait_bars: int = 0
    status: str = "PENDING"


@dataclass
class PendingExitOrder:
    signal_index: int
    signal_time: datetime
    start_index: int
    limit_price: float | None
    exit_rule: str
    wait_bars: int = 0
    status: str = "PENDING"


@dataclass(frozen=True)
class BacktestSummary:
    total_pnl: float
    win_rate: float
    number_of_trades: int
    average_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float


@dataclass(frozen=True)
class ExecutionStats:
    entry_submitted: int
    entry_filled: int
    entry_expired: int
    exit_submitted: int
    exit_filled: int
    exit_expired: int


def run_quick_backtest(
    bars: list[Bar],
    *,
    symbol: str,
    initial_equity: float = 100_000.0,
) -> list[TradeResult]:
    trades, _metadata, _stats = _run_quick_backtest_with_metadata(
        bars,
        symbol=symbol,
        initial_equity=initial_equity,
    )
    return trades


def _run_quick_backtest_with_metadata(
    bars: list[Bar],
    *,
    symbol: str,
    initial_equity: float = 100_000.0,
    canonical_db_path: str | Path | None = None,
) -> tuple[list[TradeResult], dict[str, dict[str, object]], ExecutionStats]:
    if len(bars) < MA_SLOW + 5:
        return [], {}, ExecutionStats(0, 0, 0, 0, 0, 0)

    equity = initial_equity
    trades: list[TradeResult] = []
    metadata_by_trade_id: dict[str, dict[str, object]] = {}
    position: OpenPosition | None = None
    pending_entry: PendingEntryOrder | None = None
    pending_exit: PendingExitOrder | None = None
    entry_submitted = 0
    entry_filled = 0
    entry_expired = 0
    exit_submitted = 0
    exit_filled = 0
    exit_expired = 0

    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    opens = [bar.open for bar in bars]
    frame = prepare_condition_frame(
        pd.DataFrame(
            {
                "timestamp": [bar.timestamp for bar in bars],
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": [bar.volume for bar in bars],
            }
        )
    )

    start_index = max(MA_SLOW, BREAKOUT_WINDOW, ATR_PERIOD + 1)
    if start_index >= len(bars) - 1:
        return [], {}, ExecutionStats(0, 0, 0, 0, 0, 0)

    for i in range(start_index, len(bars) - 1):
        # 1) Entry pending order execution.
        if position is None and pending_entry is not None and i >= pending_entry.start_index:
            gap_pct = _entry_execution_gap_pct(open_price=opens[i], signal_close=pending_entry.signal_close)
            if gap_pct > GAP_FILTER_MAX:
                entry_expired += 1
                pending_entry.status = "EXPIRED"
                pending_entry = None
            elif lows[i] <= pending_entry.limit_price <= highs[i]:
                entry_filled += 1
                pending_entry.status = "FILLED"
                canonical_lifecycle_id = None
                if canonical_db_path is not None:
                    (
                        build_canonical_lifecycle_id,
                        start_canonical_position_lifecycle,
                        _append_canonical_position_event,
                    ) = _load_canonical_lifecycle_writers()
                    entry_ts = _canonical_backtest_event_timestamp(bars[i].timestamp)
                    canonical_lifecycle_id = build_canonical_lifecycle_id(
                        symbol=symbol,
                        entry_timestamp=entry_ts,
                        entry_order_id=f"bt-entry|{symbol}|{pending_entry.signal_index}|{i}",
                        trade_run_id=f"offline_backtest|{symbol}",
                    )
                    start_canonical_position_lifecycle(
                        str(canonical_db_path),
                        lifecycle_id=canonical_lifecycle_id,
                        symbol=symbol,
                        entry_timestamp=entry_ts,
                        entry_order_id=f"bt-entry|{symbol}|{pending_entry.signal_index}|{i}",
                        trade_run_id=f"offline_backtest|{symbol}",
                        quantity=float(pending_entry.quantity),
                        price=float(pending_entry.limit_price),
                        size_multiplier=1.0,
                        capture_mode="historical_backfill",
                        capture_batch_id="engine_quick_backtest",
                        details={
                            "capture_expansion_task": "384",
                            "emission_mode": "engine_event_time",
                            "source_engine": "backtest.engine",
                            "signal_index": pending_entry.signal_index,
                            "entry_index": i,
                        },
                    )
                position = OpenPosition(
                    symbol=symbol,
                    quantity=pending_entry.quantity,
                    entry_index=i,
                    entry_time=bars[i].timestamp,
                    entry_price=pending_entry.breakout_level,
                    entry_fill_price=pending_entry.limit_price,
                    breakout_level=pending_entry.breakout_level,
                    stop_price=pending_entry.stop_price,
                    reason="ENTRY_BREAKOUT",
                    regime=pending_entry.regime,
                    signal_index=pending_entry.signal_index,
                    signal_time=pending_entry.signal_time,
                    breakout_flag=pending_entry.breakout_flag,
                    ma_trend_flag=pending_entry.ma_trend_flag,
                    canonical_lifecycle_id=canonical_lifecycle_id,
                )
                pending_entry = None
            else:
                pending_entry.wait_bars = i - pending_entry.signal_index
                if pending_entry.wait_bars >= MAX_WAIT_BARS:
                    entry_expired += 1
                    pending_entry.status = "EXPIRED"
                    pending_entry = None

        # 2) Generate entry signal only when flat and no pending order.
        if position is None and pending_entry is None:
            entry_signal = _entry_signal(i=i, frame=frame, equity=equity)
            if entry_signal is not None:
                breakout_level, atr_value, reference_price, breakout_flag, ma_trend_flag = entry_signal
                close_now = closes[i]
                limit_price = reference_price * (1 + ENTRY_LIMIT_BUFFER)
                position_cap = equity * MAX_POSITION_WEIGHT
                quantity = floor(position_cap / limit_price)
                if quantity >= 1:
                    entry_submitted += 1
                    regime = _regime_label(frame=frame, i=i)
                    pending_entry = PendingEntryOrder(
                        symbol=symbol,
                        signal_index=i,
                        signal_time=bars[i].timestamp,
                        start_index=i + 1,
                        limit_price=limit_price,
                        quantity=float(quantity),
                        breakout_level=breakout_level,
                        stop_price=reference_price - ATR_MULT * atr_value,
                        regime=regime,
                        breakout_flag=breakout_flag,
                        ma_trend_flag=ma_trend_flag,
                        signal_close=close_now,
                    )

        # 3) Exit pending order execution and stop handling.
        if position is not None:
            if lows[i] <= position.stop_price:
                exit_submitted += 1
                exit_filled += 1
                exit_signal_price = position.stop_price
                exit_fill_price = position.stop_price
                exit_time = bars[i].timestamp
                stop_hit_flag = True
                trend_break_2bar_flag = False
                exit_rule = "STOP"
                exit_signal_time = bars[i].timestamp
                entry_wait_bars = max(0, position.entry_index - position.signal_index)
                exit_wait_bars = 0
                entry_order_status = "FILLED"
                exit_order_status = "FILLED"
            else:
                if pending_exit is None:
                    exit_reason = _exit_reason(i=i, frame=frame, lows=lows, position=position)
                    if exit_reason is not None:
                        exit_submitted += 1
                        pending_exit = PendingExitOrder(
                            signal_index=i,
                            signal_time=bars[i].timestamp,
                            start_index=i + 1,
                            limit_price=None,
                            exit_rule=("TREND_BREAK_2BAR" if exit_reason == "EXIT_TREND_BREAK" else "TIME_EXIT"),
                        )

                if pending_exit is not None and i >= pending_exit.start_index:
                    exit_execution_price = _pending_exit_execution_price(pending_exit=pending_exit, open_price=opens[i])
                    if lows[i] <= exit_execution_price <= highs[i]:
                        exit_filled += 1
                        pending_exit.status = "FILLED"
                        exit_signal_price = closes[pending_exit.signal_index]
                        exit_fill_price = exit_execution_price
                        exit_time = bars[i].timestamp
                        stop_hit_flag = False
                        trend_break_2bar_flag = pending_exit.exit_rule == "TREND_BREAK_2BAR"
                        exit_rule = pending_exit.exit_rule
                        exit_signal_time = pending_exit.signal_time
                        entry_wait_bars = max(0, position.entry_index - position.signal_index)
                        exit_wait_bars = max(0, i - pending_exit.signal_index)
                        entry_order_status = "FILLED"
                        exit_order_status = "FILLED"
                        pending_exit = None
                    else:
                        pending_exit.wait_bars = i - pending_exit.signal_index
                        if pending_exit.wait_bars >= MAX_WAIT_BARS:
                            exit_expired += 1
                            pending_exit.status = "EXPIRED"
                            pending_exit = None
                            position.had_exit_expired = True
                        continue
                else:
                    continue

            expected_pnl = (exit_signal_price - position.entry_price) * position.quantity
            actual_pnl = (exit_fill_price - position.entry_fill_price) * position.quantity
            holding_time = float((exit_time - position.entry_time).total_seconds())
            trade_id = f"bt-{symbol}-{len(trades) + 1:04d}"
            trade = TradeResult(
                trade_id=trade_id,
                strategy_id=STRATEGY_ID,
                symbol=symbol,
                entry_time=position.entry_time,
                entry_price=position.entry_price,
                entry_fill_price=position.entry_fill_price,
                exit_time=exit_time,
                exit_price=exit_signal_price,
                exit_fill_price=exit_fill_price,
                quantity=position.quantity,
                expected_pnl=expected_pnl,
                actual_pnl=actual_pnl,
                slippage=position.entry_fill_price - position.entry_price,
                holding_time=holding_time,
            )
            trades.append(trade)
            if canonical_db_path is not None and position.canonical_lifecycle_id is not None:
                (
                    _build_canonical_lifecycle_id,
                    _start_canonical_position_lifecycle,
                    append_canonical_position_event,
                ) = _load_canonical_lifecycle_writers()
                append_canonical_position_event(
                    str(canonical_db_path),
                    lifecycle_id=position.canonical_lifecycle_id,
                    event_type="EXIT",
                    event_timestamp=_canonical_backtest_event_timestamp(exit_time),
                    order_id=f"{trade_id}|EXIT",
                    trade_run_id=trade_id,
                    quantity=-float(position.quantity),
                    price=float(exit_fill_price),
                    size_multiplier=0.0,
                    capture_mode="historical_backfill",
                    capture_batch_id="engine_quick_backtest",
                    details={
                        "capture_expansion_task": "384",
                        "emission_mode": "engine_event_time",
                        "source_engine": "backtest.engine",
                        "exit_rule": exit_rule,
                    },
                )
            metadata: dict[str, object] = {
                "signal_bar_index": position.signal_index,
                "signal_bar_time": position.signal_time.isoformat(),
                "entry_fill_bar_time": position.entry_time.isoformat(),
                "exit_signal_bar_time": exit_signal_time.isoformat(),
                "exit_fill_bar_time": exit_time.isoformat(),
                "entry_rule": "BREAKOUT + MA_TREND",
                "exit_rule": exit_rule,
                "breakout_level": float(position.breakout_level),
                "stop_price": float(position.stop_price),
                "target_price": None,
                "breakout_flag": bool(position.breakout_flag),
                "ma_trend_flag": bool(position.ma_trend_flag),
                "trend_break_2bar_flag": trend_break_2bar_flag,
                "stop_hit_flag": stop_hit_flag,
                "entry_order_status": entry_order_status,
                "exit_order_status": exit_order_status,
                "entry_wait_bars": entry_wait_bars,
                "exit_wait_bars": exit_wait_bars,
                "unfilled_flag": bool(position.had_exit_expired),
                "expired_flag": bool(position.had_exit_expired),
                "regime": position.regime,
                "sector": SYMBOL_TO_SECTOR.get(symbol, "UNMAPPED"),
                "reason": "ENTRY_BREAKOUT",
                "lifecycle_id": position.canonical_lifecycle_id,
            }
            validation = validate_trade_alignment(asdict(trade) | metadata, frame)
            if validation.alignment_result != "MATCH":
                metadata["validation_error"] = ", ".join(validation.mismatch_reasons) if validation.mismatch_reasons else "alignment mismatch"
                logger.warning(
                    "alignment mismatch trade_id=%s symbol=%s reasons=%s",
                    trade_id,
                    symbol,
                    metadata["validation_error"],
                )
            else:
                metadata["validation_error"] = None
            metadata_by_trade_id[trade_id] = metadata
            equity += actual_pnl
            position = None

    return trades, metadata_by_trade_id, ExecutionStats(
        entry_submitted=entry_submitted,
        entry_filled=entry_filled,
        entry_expired=entry_expired,
        exit_submitted=exit_submitted,
        exit_filled=exit_filled,
        exit_expired=exit_expired,
    )


def run_quick_backtest_universe(
    *,
    symbols: list[str],
    base_dir: str | Path = DEFAULT_BASE_DIR,
    initial_equity: float = 100_000.0,
) -> list[TradeResult]:
    trades, _metadata, _stats = run_quick_backtest_universe_with_metadata(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
    )
    return trades


def run_quick_backtest_universe_with_metadata(
    *,
    symbols: list[str],
    base_dir: str | Path = DEFAULT_BASE_DIR,
    initial_equity: float = 100_000.0,
    canonical_db_path: str | Path | None = None,
) -> tuple[list[TradeResult], dict[str, dict[str, object]], ExecutionStats]:
    frames = load_universe_daily_bars(symbols, base_dir=base_dir)
    all_trades: list[TradeResult] = []
    metadata_by_trade_id: dict[str, dict[str, object]] = {}
    entry_submitted = 0
    entry_filled = 0
    entry_expired = 0
    exit_submitted = 0
    exit_filled = 0
    exit_expired = 0
    for symbol in sorted(frames.keys()):
        bars = _bars_from_dataframe(frames[symbol])
        symbol_trades, symbol_metadata, stats = _run_quick_backtest_with_metadata(
            bars,
            symbol=symbol,
            initial_equity=initial_equity,
            canonical_db_path=canonical_db_path,
        )
        all_trades.extend(symbol_trades)
        metadata_by_trade_id.update(symbol_metadata)
        entry_submitted += stats.entry_submitted
        entry_filled += stats.entry_filled
        entry_expired += stats.entry_expired
        exit_submitted += stats.exit_submitted
        exit_filled += stats.exit_filled
        exit_expired += stats.exit_expired
    sorted_trades = sorted(all_trades, key=lambda trade: trade.entry_time)
    return sorted_trades, metadata_by_trade_id, ExecutionStats(
        entry_submitted=entry_submitted,
        entry_filled=entry_filled,
        entry_expired=entry_expired,
        exit_submitted=exit_submitted,
        exit_filled=exit_filled,
        exit_expired=exit_expired,
    )


def save_trades(
    trades: list[TradeResult],
    *,
    path: str | Path = "data/backtest/trades.json",
    default_reason: str = "ENTRY_BREAKOUT",
    metadata_by_trade_id: dict[str, dict[str, object]] | None = None,
    execution_stats: ExecutionStats | None = None,
) -> Path:
    """Persist trade results for UI consumption.

    Stored schema:
    - TradeResult core fields
    - lightweight extensions for UI overlays:
      - breakout_level (nullable)
      - stop_price (nullable)
      - reason
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for trade in trades:
        item = asdict(trade)
        for key in ("entry_time", "exit_time"):
            value = item.get(key)
            if isinstance(value, datetime):
                item[key] = value.isoformat()

        metadata = (metadata_by_trade_id or {}).get(trade.trade_id, {})
        item["signal_bar_index"] = metadata.get("signal_bar_index")
        item["signal_bar_time"] = metadata.get("signal_bar_time")
        item["entry_fill_bar_time"] = metadata.get("entry_fill_bar_time")
        item["exit_signal_bar_time"] = metadata.get("exit_signal_bar_time")
        item["exit_fill_bar_time"] = metadata.get("exit_fill_bar_time")
        item["entry_rule"] = metadata.get("entry_rule", "BREAKOUT + MA_TREND")
        item["exit_rule"] = metadata.get("exit_rule")
        item["breakout_level"] = metadata.get("breakout_level")
        item["stop_price"] = metadata.get("stop_price")
        item["target_price"] = metadata.get("target_price")
        item["breakout_flag"] = metadata.get("breakout_flag")
        item["ma_trend_flag"] = metadata.get("ma_trend_flag")
        item["trend_break_2bar_flag"] = metadata.get("trend_break_2bar_flag")
        item["stop_hit_flag"] = metadata.get("stop_hit_flag")
        item["entry_order_status"] = metadata.get("entry_order_status")
        item["exit_order_status"] = metadata.get("exit_order_status")
        item["entry_wait_bars"] = metadata.get("entry_wait_bars")
        item["exit_wait_bars"] = metadata.get("exit_wait_bars")
        item["unfilled_flag"] = metadata.get("unfilled_flag")
        item["expired_flag"] = metadata.get("expired_flag")
        item["regime"] = metadata.get("regime")
        item["sector"] = metadata.get("sector")
        item["reason"] = metadata.get("reason", default_reason)
        item["lifecycle_id"] = metadata.get("lifecycle_id")
        item["validation_error"] = metadata.get("validation_error")
        rows.append(item)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "strategy_id": STRATEGY_ID,
        "count": len(rows),
        "execution_stats": (
            {
                "entry_submitted": execution_stats.entry_submitted,
                "entry_filled": execution_stats.entry_filled,
                "entry_expired": execution_stats.entry_expired,
                "exit_submitted": execution_stats.exit_submitted,
                "exit_filled": execution_stats.exit_filled,
                "exit_expired": execution_stats.exit_expired,
            }
            if execution_stats is not None
            else None
        ),
        "trades": rows,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return output_path


def summarize(trades: list[TradeResult]) -> BacktestSummary:
    actual_pnls = [trade.actual_pnl for trade in trades if trade.actual_pnl is not None]
    if not actual_pnls:
        return BacktestSummary(
            total_pnl=0.0,
            win_rate=0.0,
            number_of_trades=0,
            average_pnl=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            max_drawdown=0.0,
        )

    wins = [value for value in actual_pnls if value > 0]
    losses = [value for value in actual_pnls if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    return BacktestSummary(
        total_pnl=sum(actual_pnls),
        win_rate=(len(wins) / len(actual_pnls)) * 100.0,
        number_of_trades=len(actual_pnls),
        average_pnl=statistics.fmean(actual_pnls),
        avg_win=statistics.fmean(wins) if wins else 0.0,
        avg_loss=statistics.fmean(losses) if losses else 0.0,
        profit_factor=profit_factor,
        max_drawdown=_max_drawdown_from_equity_curve(actual_pnls),
    )


def _validate_preconditions(symbols: list[str], *, base_dir: Path) -> None:
    if len(symbols) < MIN_UNIVERSE_SIZE:
        raise SystemExit(
            f"precondition failed: at least {MIN_UNIVERSE_SIZE} symbols are required, got {len(symbols)}"
        )

    if not base_dir.exists():
        raise SystemExit(f"precondition failed: data directory does not exist: {base_dir}")

    missing_files: list[str] = []
    for symbol in symbols:
        csv_path = base_dir / f"{symbol}.csv"
        if not csv_path.exists():
            missing_files.append(symbol)

    if missing_files:
        raise SystemExit(
            "precondition failed: missing CSV files for symbols: " + ", ".join(missing_files)
        )

    bad_schema: list[str] = []
    for symbol in symbols:
        try:
            # Explicitly validate schema/ordering via the loader.
            frame = load_daily_bars(symbol, base_dir=base_dir)
        except Exception:
            bad_schema.append(symbol)
            continue
        if frame.empty:
            bad_schema.append(symbol)
            continue
        if any(col not in frame.columns for col in REQUIRED_COLUMNS):
            bad_schema.append(symbol)
            continue
        if not frame["timestamp"].is_monotonic_increasing:
            bad_schema.append(symbol)

    if bad_schema:
        raise SystemExit(
            "precondition failed: invalid or unsorted daily data for symbols: " + ", ".join(bad_schema)
        )


def _bars_from_dataframe(frame: pd.DataFrame) -> list[Bar]:
    bars: list[Bar] = []
    for row in frame.itertuples(index=False):
        timestamp = row.timestamp.to_pydatetime() if hasattr(row.timestamp, "to_pydatetime") else row.timestamp
        bars.append(
            Bar(
                timestamp=timestamp,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )
        )
    return bars


def _entry_execution_gap_pct(*, open_price: float, signal_close: float) -> float:
    if signal_close <= 0:
        raise ValueError("signal_close must be positive")
    return (open_price - signal_close) / signal_close


def _pending_exit_execution_price(*, pending_exit: PendingExitOrder, open_price: float) -> float:
    return float(open_price) if pending_exit.limit_price is None else float(pending_exit.limit_price)


def _load_canonical_lifecycle_writers():
    from backtest.canonical_position_lifecycle_event_sourcing import (
        append_canonical_position_event,
        build_canonical_lifecycle_id,
        start_canonical_position_lifecycle,
    )

    return build_canonical_lifecycle_id, start_canonical_position_lifecycle, append_canonical_position_event


def _entry_signal(
    *,
    i: int,
    frame: pd.DataFrame,
    equity: float,
) -> tuple[float, float, float, bool, bool] | None:
    close_now = _frame_value(frame, i, "close")
    if close_now is None or close_now < MIN_CLOSE:
        return None

    max_affordable_price = equity * MAX_POSITION_WEIGHT
    if close_now > max_affordable_price:
        return None

    breakout_flag = bool(is_breakout(frame, i) is True)
    ma_trend_flag = bool(is_ma_trend(frame, i) is True)
    if not breakout_flag or not ma_trend_flag:
        return None

    avg_volume20 = _frame_value(frame, i, "avg_volume_20")
    avg_turnover20 = _frame_value(frame, i, "avg_turnover_20")
    if avg_volume20 is None or avg_turnover20 is None:
        return None
    if avg_volume20 < MIN_AVG_VOLUME or avg_turnover20 < MIN_AVG_TURNOVER:
        return None

    breakout_level = _frame_value(frame, i, "rolling_high_20")
    atr_value = _frame_value(frame, i, "atr14")
    if atr_value is None or atr_value <= 0:
        return None

    reference_price = breakout_level
    return breakout_level, atr_value, reference_price, breakout_flag, ma_trend_flag


def _exit_reason(*, i: int, frame: pd.DataFrame, lows: list[float], position: OpenPosition) -> str | None:
    if lows[i] <= position.stop_price:
        return "EXIT_STOP"

    if is_exit_condition(frame, i) is True:
        return "EXIT_TREND_BREAK"

    holding_days = i - position.entry_index + 1
    if holding_days > MAX_HOLDING_DAYS:
        return "EXIT_TIME"

    return None


def _frame_value(frame: pd.DataFrame, i: int, column: str) -> float | None:
    if column not in frame.columns or not (0 <= i < len(frame)):
        return None
    value = frame.iloc[i][column]
    if pd.isna(value):
        return None
    return float(value)


def _regime_label(*, frame: pd.DataFrame, i: int) -> str:
    close_now = _frame_value(frame, i, "close")
    ma200 = _frame_value(frame, i, "ma200")
    if close_now is None or ma200 is None:
        return "BEAR"
    return "BULL" if close_now >= ma200 else "BEAR"


def _avg(series: list[float], i: int, window: int) -> float | None:
    start = i - window + 1
    if start < 0:
        return None
    subset = series[start : i + 1]
    return sum(subset) / float(window)


def _sma(series: list[float], i: int, window: int) -> float | None:
    return _avg(series, i, window)


def _highest_prev(series: list[float], i: int, window: int) -> float | None:
    start = i - window
    if start < 0:
        return None
    return max(series[start:i])


def _atr(bars: list[Bar], i: int, period: int) -> float | None:
    start = i - period + 1
    if start < 1:
        return None
    true_ranges: list[float] = []
    for idx in range(start, i + 1):
        high = bars[idx].high
        low = bars[idx].low
        prev_close = bars[idx - 1].close
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    if not true_ranges:
        return None
    return sum(true_ranges) / float(period)


def _max_drawdown_from_equity_curve(pnls: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnls:
        equity += pnl
        if equity > peak:
            peak = equity
        drawdown = peak - equity
        if drawdown > max_dd:
            max_dd = drawdown
    return max_dd


def _print_summary(summary: BacktestSummary) -> None:
    print(f"TOTAL PNL: {summary.total_pnl:.4f}")
    print(f"WIN RATE: {summary.win_rate:.2f}%")
    print(f"TRADES: {summary.number_of_trades}")
    print(f"AVG PNL: {summary.average_pnl:.4f}")
    pf_text = "inf" if summary.profit_factor == float("inf") else f"{summary.profit_factor:.4f}"
    print(f"PROFIT FACTOR: {pf_text}")
    print(f"MAX DD: {summary.max_drawdown:.4f}")


def _print_trade_samples(trades: list[TradeResult], *, max_rows: int = 5) -> None:
    print("[TRADE SAMPLES]")
    if not trades:
        print("- no trades")
        return
    for trade in trades[:max_rows]:
        print(
            "- "
            f"trade_id={trade.trade_id} | symbol={trade.symbol} | "
            f"entry_time={trade.entry_time.isoformat()} | entry_price={trade.entry_price:.4f} | "
            f"entry_fill={trade.entry_fill_price if trade.entry_fill_price is not None else 'None'} | "
            f"exit_time={trade.exit_time.isoformat() if trade.exit_time is not None else 'None'} | "
            f"exit_fill={trade.exit_fill_price if trade.exit_fill_price is not None else 'None'} | "
            f"expected_pnl={trade.expected_pnl:.4f} | actual_pnl={trade.actual_pnl if trade.actual_pnl is not None else 'None'} | "
            f"holding_time_sec={trade.holding_time if trade.holding_time is not None else 'None'}"
        )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick Backtest Engine for US Swing Breakout v0")
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=list(DEFAULT_US_UNIVERSE),
        help=f"Symbols to backtest (minimum {MIN_UNIVERSE_SIZE})",
    )
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR), help="Daily CSV directory path")
    parser.add_argument("--print-trades", type=int, default=5, help="How many trade rows to print")
    parser.add_argument("--initial-equity", type=float, default=100_000.0, help="Per-symbol quick sizing equity")
    parser.add_argument("--output", type=str, default="data/backtest/trades.json", help="TradeResult export JSON path")
    parser.add_argument("--canonical-db", type=str, default="", help="Optional canonical lifecycle DB path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    symbols = sorted({str(symbol).strip().upper() for symbol in args.symbols if str(symbol).strip()})
    data_dir = Path(args.data_dir)

    _validate_preconditions(symbols, base_dir=data_dir)

    trades, metadata_by_trade_id, execution_stats = run_quick_backtest_universe_with_metadata(
        symbols=symbols,
        base_dir=data_dir,
        initial_equity=args.initial_equity,
        canonical_db_path=args.canonical_db or None,
    )
    summary = summarize(trades)

    print(f"[INPUT] data_dir={data_dir} symbols={len(symbols)}")
    _print_summary(summary)
    _print_trade_samples(trades, max_rows=max(1, args.print_trades))
    output_path = save_trades(
        trades,
        path=args.output,
        metadata_by_trade_id=metadata_by_trade_id,
        execution_stats=execution_stats,
    )
    print(f"[EXPORT] trades_json={output_path} count={len(trades)}")
    if execution_stats.entry_submitted > 0:
        entry_fill_rate = execution_stats.entry_filled / execution_stats.entry_submitted * 100.0
        entry_expired_rate = execution_stats.entry_expired / execution_stats.entry_submitted * 100.0
    else:
        entry_fill_rate = 0.0
        entry_expired_rate = 0.0
    if execution_stats.exit_submitted > 0:
        exit_fill_rate = execution_stats.exit_filled / execution_stats.exit_submitted * 100.0
        exit_expired_rate = execution_stats.exit_expired / execution_stats.exit_submitted * 100.0
    else:
        exit_fill_rate = 0.0
        exit_expired_rate = 0.0
    print(
        "[EXECUTION] "
        f"entry_submitted={execution_stats.entry_submitted} "
        f"entry_filled={execution_stats.entry_filled} "
        f"entry_expired={execution_stats.entry_expired} "
        f"entry_fill_rate={entry_fill_rate:.2f}% "
        f"entry_expired_rate={entry_expired_rate:.2f}%"
    )
    print(
        "[EXECUTION] "
        f"exit_submitted={execution_stats.exit_submitted} "
        f"exit_filled={execution_stats.exit_filled} "
        f"exit_expired={execution_stats.exit_expired} "
        f"exit_fill_rate={exit_fill_rate:.2f}% "
        f"exit_expired_rate={exit_expired_rate:.2f}%"
    )

    if not trades:
        print("[WARN] no trades generated for the selected universe.")
    return 0


def _canonical_backtest_event_timestamp(value: datetime) -> str:
    """Daily-bar offline convention: record generated events at US cash open proxy."""
    return value.date().isoformat() + "T14:30:00+00:00"


if __name__ == "__main__":
    raise SystemExit(main())
