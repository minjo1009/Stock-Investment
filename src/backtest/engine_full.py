from __future__ import annotations

import argparse
import math
import statistics
from dataclasses import dataclass
from datetime import datetime
from math import floor
from pathlib import Path

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, REQUIRED_COLUMNS, Bar, load_daily_bars, load_universe_daily_bars
from backtest.models import TradeResult


STRATEGY_ID = "us_swing_breakout_v0"

# Fixed strategy parameters (do not tune in this task).
BREAKOUT_WINDOW = 20
MA_FAST = 20
MA_SLOW = 50
MA_REGIME = 200
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
MIN_YEARS = 5
# Five-year daily bars from free sources are often around ~1250 rows.
MIN_BARS_5Y = 1200


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


@dataclass(frozen=True)
class FullTradeResult:
    trade: TradeResult
    cost: float
    net_pnl: float
    regime: str


@dataclass(frozen=True)
class FullSummary:
    total_pnl: float
    net_pnl: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    trade_count: int


def run_full_backtest(
    bars: list[Bar],
    *,
    symbol: str,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
) -> list[FullTradeResult]:
    if len(bars) < max(MA_REGIME, MA_SLOW) + 5:
        return []

    equity = initial_equity
    results: list[FullTradeResult] = []
    position: OpenPosition | None = None

    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    opens = [bar.open for bar in bars]
    volumes = [bar.volume for bar in bars]

    start_index = max(MA_REGIME, MA_SLOW, BREAKOUT_WINDOW, ATR_PERIOD + 1)
    if start_index >= len(bars) - 1:
        return []

    for i in range(start_index, len(bars) - 1):
        if position is not None:
            exit_reason = _exit_reason(i=i, closes=closes, lows=lows, position=position)
            if exit_reason is not None:
                exit_signal_price = closes[i]
                raw_exit_open = opens[i + 1]
                exit_fill_price = raw_exit_open * (1 - slippage_rate)
                exit_time = bars[i + 1].timestamp

                expected_pnl = (exit_signal_price - position.entry_price) * position.quantity
                gross_actual_pnl = (exit_fill_price - position.entry_fill_price) * position.quantity
                notional_entry = position.entry_fill_price * position.quantity
                notional_exit = exit_fill_price * position.quantity
                total_cost = (notional_entry + notional_exit) * fee_rate
                net_pnl = gross_actual_pnl - total_cost

                trade = TradeResult(
                    trade_id=f"full-{symbol}-{len(results) + 1:04d}",
                    strategy_id=STRATEGY_ID,
                    symbol=position.symbol,
                    entry_time=position.entry_time,
                    entry_price=position.entry_price,
                    entry_fill_price=position.entry_fill_price,
                    exit_time=exit_time,
                    exit_price=exit_signal_price,
                    exit_fill_price=exit_fill_price,
                    quantity=position.quantity,
                    expected_pnl=expected_pnl,
                    actual_pnl=gross_actual_pnl,
                    slippage=position.entry_fill_price - position.entry_price,
                    holding_time=float((exit_time - position.entry_time).total_seconds()),
                )
                results.append(
                    FullTradeResult(
                        trade=trade,
                        cost=total_cost,
                        net_pnl=net_pnl,
                        regime=position.regime,
                    )
                )
                equity += net_pnl
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

            entry_fill_price = next_open * (1 + slippage_rate)
            regime = _regime_label(closes=closes, i=i)
            position = OpenPosition(
                symbol=symbol,
                quantity=float(quantity),
                entry_index=i + 1,
                entry_time=bars[i + 1].timestamp,
                entry_price=reference_price,
                entry_fill_price=entry_fill_price,
                breakout_level=breakout_level,
                stop_price=reference_price - ATR_MULT * atr_value,
                reason="ENTRY_BREAKOUT",
                regime=regime,
            )

    return results


def run_full_backtest_universe(
    *,
    symbols: list[str],
    base_dir: str | Path,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
) -> list[FullTradeResult]:
    frames = load_universe_daily_bars(symbols, base_dir=base_dir)
    out: list[FullTradeResult] = []
    for symbol in sorted(frames.keys()):
        bars = _bars_from_dataframe(frames[symbol])
        out.extend(
            run_full_backtest(
                bars,
                symbol=symbol,
                initial_equity=initial_equity,
                fee_rate=fee_rate,
                slippage_rate=slippage_rate,
            )
        )
    return sorted(out, key=lambda x: x.trade.entry_time)


def summarize(results: list[FullTradeResult], *, initial_equity: float) -> FullSummary:
    if not results:
        return FullSummary(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    gross = [item.trade.actual_pnl for item in results if item.trade.actual_pnl is not None]
    net = [item.net_pnl for item in results]
    wins = [value for value in net if value > 0]
    losses = [value for value in net if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    returns = [value / initial_equity for value in net]
    sharpe_ratio = _simple_sharpe(returns)

    return FullSummary(
        total_pnl=sum(gross),
        net_pnl=sum(net),
        win_rate=(len(wins) / len(net)) * 100.0,
        profit_factor=profit_factor,
        max_drawdown=_max_drawdown(net),
        sharpe_ratio=sharpe_ratio,
        trade_count=len(results),
    )


def analyze_yearly(results: list[FullTradeResult]) -> pd.DataFrame:
    if not results:
        return pd.DataFrame(columns=["year", "total_pnl", "net_pnl", "trade_count", "win_rate"])
    rows = []
    for item in results:
        rows.append(
            {
                "year": item.trade.entry_time.year,
                "gross_pnl": item.trade.actual_pnl if item.trade.actual_pnl is not None else 0.0,
                "net_pnl": item.net_pnl,
                "win": 1 if item.net_pnl > 0 else 0,
            }
        )
    df = pd.DataFrame(rows)
    grouped = (
        df.groupby("year", as_index=False)
        .agg(total_pnl=("gross_pnl", "sum"), net_pnl=("net_pnl", "sum"), trade_count=("net_pnl", "count"), wins=("win", "sum"))
        .sort_values("year")
    )
    grouped["win_rate"] = (grouped["wins"] / grouped["trade_count"]) * 100.0
    return grouped[["year", "total_pnl", "net_pnl", "trade_count", "win_rate"]]


def analyze_regime(results: list[FullTradeResult]) -> pd.DataFrame:
    if not results:
        return pd.DataFrame(columns=["regime", "total_pnl", "net_pnl", "trade_count", "win_rate"])
    rows = []
    for item in results:
        rows.append(
            {
                "regime": item.regime,
                "gross_pnl": item.trade.actual_pnl if item.trade.actual_pnl is not None else 0.0,
                "net_pnl": item.net_pnl,
                "win": 1 if item.net_pnl > 0 else 0,
            }
        )
    df = pd.DataFrame(rows)
    grouped = (
        df.groupby("regime", as_index=False)
        .agg(total_pnl=("gross_pnl", "sum"), net_pnl=("net_pnl", "sum"), trade_count=("net_pnl", "count"), wins=("win", "sum"))
        .sort_values("regime")
    )
    grouped["win_rate"] = (grouped["wins"] / grouped["trade_count"]) * 100.0
    return grouped[["regime", "total_pnl", "net_pnl", "trade_count", "win_rate"]]


def _validate_preconditions(symbols: list[str], *, base_dir: Path) -> None:
    if len(symbols) < MIN_UNIVERSE_SIZE:
        raise SystemExit(f"precondition failed: need at least {MIN_UNIVERSE_SIZE} symbols, got {len(symbols)}")
    if not base_dir.exists():
        raise SystemExit(f"precondition failed: missing data directory: {base_dir}")

    missing = [sym for sym in symbols if not (base_dir / f"{sym}.csv").exists()]
    if missing:
        raise SystemExit("precondition failed: missing CSV files for symbols: " + ", ".join(missing))

    bad: list[str] = []
    for symbol in symbols:
        try:
            frame = load_daily_bars(symbol, base_dir=base_dir)
        except Exception:
            bad.append(symbol)
            continue
        if frame.empty:
            bad.append(symbol)
            continue
        if any(col not in frame.columns for col in REQUIRED_COLUMNS):
            bad.append(symbol)
            continue
        if not frame["timestamp"].is_monotonic_increasing:
            bad.append(symbol)
            continue
        if len(frame) < MIN_BARS_5Y:
            bad.append(symbol)
            continue
        span_days = int((frame["timestamp"].max() - frame["timestamp"].min()).days)
        if span_days < (365 * MIN_YEARS - 40):
            bad.append(symbol)
    if bad:
        raise SystemExit("precondition failed: data does not satisfy 5y/full schema for: " + ", ".join(bad))


def _bars_from_dataframe(frame: pd.DataFrame) -> list[Bar]:
    rows: list[Bar] = []
    for row in frame.itertuples(index=False):
        ts = row.timestamp.to_pydatetime() if hasattr(row.timestamp, "to_pydatetime") else row.timestamp
        rows.append(
            Bar(
                timestamp=ts,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )
        )
    return rows


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
    if not (close_now > sma50 and sma20 > sma50):
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

    atr = _atr(bars, i, ATR_PERIOD)
    if atr is None or atr <= 0:
        return None

    return breakout_level, atr, breakout_level


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


def _regime_label(*, closes: list[float], i: int) -> str:
    ma200 = _sma(closes, i, MA_REGIME)
    if ma200 is None:
        return "BEAR"
    return "BULL" if closes[i] >= ma200 else "BEAR"


def _avg(series: list[float], i: int, window: int) -> float | None:
    start = i - window + 1
    if start < 0:
        return None
    return sum(series[start : i + 1]) / float(window)


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
    tr_values: list[float] = []
    for idx in range(start, i + 1):
        high = bars[idx].high
        low = bars[idx].low
        prev_close = bars[idx - 1].close
        tr_values.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    if not tr_values:
        return None
    return sum(tr_values) / float(period)


def _max_drawdown(net_pnls: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in net_pnls:
        equity += pnl
        if equity > peak:
            peak = equity
        drawdown = peak - equity
        if drawdown > max_dd:
            max_dd = drawdown
    return max_dd


def _simple_sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = statistics.fmean(returns)
    std_r = statistics.pstdev(returns)
    if std_r == 0:
        return 0.0
    return (mean_r / std_r) * math.sqrt(len(returns))


def _print_df(df: pd.DataFrame) -> None:
    if df.empty:
        print("(no rows)")
    else:
        print(df.to_string(index=False))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Full Backtest (5y+) for US Swing Breakout v0")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE), help="Universe symbols")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR), help="Daily CSV directory")
    parser.add_argument("--initial-equity", type=float, default=100_000.0, help="Per-symbol base equity")
    parser.add_argument("--fee-rate", type=float, default=0.0005, help="Fee rate per side (default 0.05%)")
    parser.add_argument("--slippage-rate", type=float, default=0.0005, help="Slippage rate per side (default 0.05%)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    data_dir = Path(args.data_dir)

    _validate_preconditions(symbols, base_dir=data_dir)
    results = run_full_backtest_universe(
        symbols=symbols,
        base_dir=data_dir,
        initial_equity=args.initial_equity,
        fee_rate=args.fee_rate,
        slippage_rate=args.slippage_rate,
    )
    summary = summarize(results, initial_equity=args.initial_equity)
    yearly = analyze_yearly(results)
    regime = analyze_regime(results)

    print("=== OVERALL PERFORMANCE ===")
    print(f"TOTAL PNL: {summary.total_pnl:.4f}")
    print(f"NET PNL: {summary.net_pnl:.4f}")
    print(f"WIN RATE: {summary.win_rate:.2f}%")
    pf_text = "inf" if summary.profit_factor == float("inf") else f"{summary.profit_factor:.4f}"
    print(f"PROFIT FACTOR: {pf_text}")
    print(f"MAX DD: {summary.max_drawdown:.4f}")
    print(f"SHARPE: {summary.sharpe_ratio:.4f}")
    print(f"TRADES: {summary.trade_count}")
    print()

    print("=== YEARLY PERFORMANCE ===")
    _print_df(yearly)
    print()

    print("=== REGIME PERFORMANCE ===")
    _print_df(regime)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
