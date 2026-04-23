from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from math import floor
from pathlib import Path

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, REQUIRED_COLUMNS, Bar, load_daily_bars, load_universe_daily_bars
from backtest.models import TradeResult


STRATEGY_ID = "us_swing_breakout_v0"

# Fixed parameters from docs/strategy_spec_us_swing_breakout_v0.md
BREAKOUT_WINDOW = 20
MA_FAST = 20
MA_SLOW = 50
ATR_PERIOD = 14
ATR_MULT = 2.0
MAX_HOLDING_DAYS = 20
GAP_FILTER_MAX = 0.03
ENTRY_LIMIT_BUFFER = 0.001

MIN_CLOSE = 5.0
MIN_AVG_VOLUME = 1_000_000.0
MIN_AVG_TURNOVER = 20_000_000.0
MAX_POSITION_WEIGHT = 0.10
MIN_UNIVERSE_SIZE = 10


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


def run_quick_backtest(
    bars: list[Bar],
    *,
    symbol: str,
    initial_equity: float = 100_000.0,
) -> list[TradeResult]:
    if len(bars) < MA_SLOW + 5:
        return []

    equity = initial_equity
    trades: list[TradeResult] = []
    position: OpenPosition | None = None

    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    opens = [bar.open for bar in bars]
    volumes = [bar.volume for bar in bars]

    start_index = max(MA_SLOW, BREAKOUT_WINDOW, ATR_PERIOD + 1)
    if start_index >= len(bars) - 1:
        return []

    for i in range(start_index, len(bars) - 1):
        if position is not None:
            exit_reason = _exit_reason(i=i, closes=closes, lows=lows, position=position)
            if exit_reason is not None:
                exit_signal_price = closes[i]
                exit_fill_price = opens[i + 1]
                exit_time = bars[i + 1].timestamp
                expected_pnl = (exit_signal_price - position.entry_price) * position.quantity
                actual_pnl = (exit_fill_price - position.entry_fill_price) * position.quantity
                holding_time = float((exit_time - position.entry_time).total_seconds())

                trades.append(
                    TradeResult(
                        trade_id=f"bt-{symbol}-{len(trades) + 1:04d}",
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
                )
                equity += actual_pnl
                position = None
                continue

        if position is None:
            entry_signal = _entry_signal(
                i=i,
                bars=bars,
                closes=closes,
                highs=highs,
                volumes=volumes,
                equity=equity,
            )
            if entry_signal is None:
                continue

            breakout_level, atr_value, reference_price = entry_signal
            next_open = opens[i + 1]
            close_now = closes[i]
            gap_pct = (next_open - close_now) / close_now
            if gap_pct > GAP_FILTER_MAX:
                continue

            entry_limit_price = reference_price * (1 + ENTRY_LIMIT_BUFFER)
            position_cap = equity * MAX_POSITION_WEIGHT
            quantity = floor(position_cap / entry_limit_price)
            if quantity < 1:
                continue

            position = OpenPosition(
                symbol=symbol,
                quantity=float(quantity),
                entry_index=i + 1,
                entry_time=bars[i + 1].timestamp,
                entry_price=reference_price,
                entry_fill_price=next_open,
                breakout_level=breakout_level,
                stop_price=reference_price - ATR_MULT * atr_value,
                reason="ENTRY_BREAKOUT",
            )

    return trades


def run_quick_backtest_universe(
    *,
    symbols: list[str],
    base_dir: str | Path = DEFAULT_BASE_DIR,
    initial_equity: float = 100_000.0,
) -> list[TradeResult]:
    frames = load_universe_daily_bars(symbols, base_dir=base_dir)
    all_trades: list[TradeResult] = []
    for symbol in sorted(frames.keys()):
        bars = _bars_from_dataframe(frames[symbol])
        symbol_trades = run_quick_backtest(bars, symbol=symbol, initial_equity=initial_equity)
        all_trades.extend(symbol_trades)
    return sorted(all_trades, key=lambda trade: trade.entry_time)


def save_trades(
    trades: list[TradeResult],
    *,
    path: str | Path = "data/backtest/trades.json",
    default_reason: str = "ENTRY_BREAKOUT",
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

        # Keep model contract intact while exporting optional UI hints.
        item["breakout_level"] = None
        item["stop_price"] = None
        item["reason"] = default_reason
        rows.append(item)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "strategy_id": STRATEGY_ID,
        "count": len(rows),
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


def _entry_signal(
    *,
    i: int,
    bars: list[Bar],
    closes: list[float],
    highs: list[float],
    volumes: list[float],
    equity: float,
) -> tuple[float, float, float] | None:
    close_now = closes[i]
    if close_now < MIN_CLOSE:
        return None

    max_affordable_price = equity * MAX_POSITION_WEIGHT
    if close_now > max_affordable_price:
        return None

    sma20 = _sma(closes, i, MA_FAST)
    sma50 = _sma(closes, i, MA_SLOW)
    if sma20 is None or sma50 is None:
        return None

    trend_ok = close_now > sma50 and sma20 > sma50
    if not trend_ok:
        return None

    avg_volume20 = _avg(volumes, i, 20)
    turnover = [bar.close * bar.volume for bar in bars]
    avg_turnover20 = _avg(turnover, i, 20)
    if avg_volume20 is None or avg_turnover20 is None:
        return None
    if avg_volume20 < MIN_AVG_VOLUME or avg_turnover20 < MIN_AVG_TURNOVER:
        return None

    breakout_level = _highest_prev(highs, i, BREAKOUT_WINDOW)
    if breakout_level is None or close_now < breakout_level:
        return None

    atr_value = _atr(bars, i, ATR_PERIOD)
    if atr_value is None or atr_value <= 0:
        return None

    reference_price = breakout_level
    return breakout_level, atr_value, reference_price


def _exit_reason(*, i: int, closes: list[float], lows: list[float], position: OpenPosition) -> str | None:
    if lows[i] <= position.stop_price:
        return "EXIT_STOP"

    sma20_now = _sma(closes, i, MA_FAST)
    if sma20_now is not None and closes[i] < sma20_now:
        return "EXIT_TREND_BREAK"

    holding_days = i - position.entry_index + 1
    if holding_days > MAX_HOLDING_DAYS:
        return "EXIT_TIME"

    return None


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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    symbols = sorted({str(symbol).strip().upper() for symbol in args.symbols if str(symbol).strip()})
    data_dir = Path(args.data_dir)

    _validate_preconditions(symbols, base_dir=data_dir)

    trades = run_quick_backtest_universe(symbols=symbols, base_dir=data_dir, initial_equity=args.initial_equity)
    summary = summarize(trades)

    print(f"[INPUT] data_dir={data_dir} symbols={len(symbols)}")
    _print_summary(summary)
    _print_trade_samples(trades, max_rows=max(1, args.print_trades))
    output_path = save_trades(trades, path=args.output)
    print(f"[EXPORT] trades_json={output_path} count={len(trades)}")

    if not trades:
        print("[WARN] no trades generated for the selected universe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
