from __future__ import annotations

import argparse
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from math import floor
from pathlib import Path

import pandas as pd

from analytics.metrics import FullSummary as MetricsSummary
from analytics.metrics import analyze_regime_performance, analyze_yearly_performance, summarize_full_results
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, REQUIRED_COLUMNS, Bar, load_daily_bars, load_universe_daily_bars
from backtest.entry_gates import EntryGateConfig, evaluate_entry_gate, prepare_entry_gate_frame
from backtest.models import TradeResult
from execution.policies import ENTRY_POLICIES, estimate_missed_trade_potential, get_entry_policy, resolve_entry_fill_price
from portfolio.allocator import AllocationConfig, allocate_equal_weight
from risk.policies import RISK_MFE_TRIGGER, RISK_POLICIES, evaluate_risk_exit, get_risk_policy, position_mfe
from sector.sector_model import map_symbol_to_sector
from strategy.conditions import (
    breakout_column_for_mode,
    breakout_window_for_mode,
    is_breakout,
    is_exit_condition,
    is_ma_trend,
    prepare_condition_frame,
)
from strategy.validator import validate_trade_alignment
from universe.ranking import rank_universe
from universe.universe_selector import build_universe_snapshot, filter_universe_snapshot


STRATEGY_ID = "us_swing_breakout_v0"

# Fixed strategy parameters (do not tune in this task).
BREAKOUT_WINDOW = 20
MA_FAST = 20
MA_SLOW = 50
MA_REGIME = 200
ATR_PERIOD = 14
ATR_MULT = 2.0
MAX_HOLDING_DAYS = 20
MAX_WAIT_BARS = 3
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
    had_exit_expired: bool = False
    max_high_since_entry: float = 0.0
    risk_layer_armed: bool = False


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
    chase_bps: float = 0.0
    market_like: bool = False
    wait_bars: int = 0
    status: str = "PENDING"


@dataclass
class PendingExitOrder:
    signal_index: int
    signal_time: datetime
    start_index: int
    limit_price: float
    exit_rule: str
    wait_bars: int = 0
    status: str = "PENDING"


@dataclass(frozen=True)
class FullTradeResult:
    trade: TradeResult
    cost: float
    net_pnl: float
    regime: str
    metadata: dict[str, object] = field(default_factory=dict)


FullSummary = MetricsSummary


@dataclass(frozen=True)
class EntryExecutionStats:
    total_signals: int
    entry_filled: int
    entry_expired: int
    fill_rate: float
    expired_rate: float
    missed_trades: int
    big_miss_count: int
    missed_potential_return_sum: float
    missed_profit_estimate: float
    skipped_by_gate: int
    skipped_by_gate_reason_breakdown: dict[str, int] = field(default_factory=dict)
    skipped_by_gate_estimated_pnls: tuple[float, ...] = ()
    skipped_by_gate_winner_count: int = 0

    @property
    def skipped_by_gate_avg_estimated_pnl(self) -> float:
        if not self.skipped_by_gate_estimated_pnls:
            return 0.0
        return float(sum(self.skipped_by_gate_estimated_pnls) / len(self.skipped_by_gate_estimated_pnls))

    @property
    def skipped_by_gate_median_estimated_pnl(self) -> float:
        if not self.skipped_by_gate_estimated_pnls:
            return 0.0
        values = sorted(self.skipped_by_gate_estimated_pnls)
        mid = len(values) // 2
        if len(values) % 2 == 1:
            return float(values[mid])
        return float((values[mid - 1] + values[mid]) / 2.0)

    @property
    def skipped_by_gate_winner_ratio(self) -> float:
        if self.skipped_by_gate <= 0:
            return 0.0
        return float(self.skipped_by_gate_winner_count / self.skipped_by_gate)


def run_full_backtest(
    bars: list[Bar],
    *,
    symbol: str,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
    risk_policy: str = "BASELINE",
    breakout_mode: str = "BASELINE",
    entry_gate_config: EntryGateConfig | None = None,
) -> list[FullTradeResult]:
    results, _stats = run_full_backtest_with_stats(
        bars,
        symbol=symbol,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        risk_policy=risk_policy,
        breakout_mode=breakout_mode,
        entry_gate_config=entry_gate_config,
    )
    return results


def run_full_backtest_with_stats(
    bars: list[Bar],
    *,
    symbol: str,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
    entry_policy: str = "BASELINE",
    risk_policy: str = "BASELINE",
    breakout_mode: str = "BASELINE",
    entry_gate_config: EntryGateConfig | None = None,
) -> tuple[list[FullTradeResult], EntryExecutionStats]:
    policy = _entry_policy(entry_policy)
    risk = _risk_policy(risk_policy)
    gate_config = entry_gate_config if entry_gate_config is not None else EntryGateConfig.disabled()
    if len(bars) < max(MA_REGIME, MA_SLOW) + 5:
        return [], EntryExecutionStats(0, 0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0)

    equity = initial_equity
    results: list[FullTradeResult] = []
    position: OpenPosition | None = None
    pending_entry: PendingEntryOrder | None = None
    pending_exit: PendingExitOrder | None = None

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
    frame = prepare_entry_gate_frame(frame, gate_config)

    start_index = max(MA_REGIME, MA_SLOW, breakout_window_for_mode(breakout_mode), ATR_PERIOD + 1)
    if start_index >= len(bars) - 1:
        return [], EntryExecutionStats(0, 0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0)

    total_signals = 0
    entry_filled = 0
    entry_expired = 0
    missed_potential_return_sum = 0.0
    missed_profit_estimate = 0.0
    big_miss_count = 0
    skipped_by_gate = 0
    skipped_by_gate_reason_breakdown: dict[str, int] = {}
    skipped_by_gate_estimated_pnls: list[float] = []
    skipped_by_gate_winner_count = 0
    for i in range(start_index, len(bars) - 1):
        if position is None and pending_entry is not None and i >= pending_entry.start_index:
            can_fill, fill_px = _entry_fill_price(
                low=lows[i],
                high=highs[i],
                open_px=opens[i],
                pending=pending_entry,
            )
            if can_fill and fill_px is not None:
                entry_filled += 1
                pending_entry.status = "FILLED"
                entry_fill_price = fill_px * (1 + slippage_rate)
                position = OpenPosition(
                    symbol=symbol,
                    quantity=pending_entry.quantity,
                    entry_index=i,
                    entry_time=bars[i].timestamp,
                    entry_price=pending_entry.breakout_level,
                    entry_fill_price=entry_fill_price,
                    breakout_level=pending_entry.breakout_level,
                    stop_price=pending_entry.stop_price,
                    reason="ENTRY_BREAKOUT",
                    regime=pending_entry.regime,
                    signal_index=pending_entry.signal_index,
                    signal_time=pending_entry.signal_time,
                    breakout_flag=pending_entry.breakout_flag,
                    ma_trend_flag=pending_entry.ma_trend_flag,
                    max_high_since_entry=highs[i],
                )
                pending_entry = None
            else:
                pending_entry.wait_bars = i - pending_entry.signal_index
                if pending_entry.wait_bars >= policy["wait_bars"]:
                    pending_entry.status = "EXPIRED"
                    entry_expired += 1
                    max_ret, est_pnl = _missed_trade_potential(
                        highs=highs,
                        breakout_level=pending_entry.breakout_level,
                        quantity=pending_entry.quantity,
                        signal_index=pending_entry.signal_index,
                    )
                    missed_potential_return_sum += max_ret
                    missed_profit_estimate += est_pnl
                    if max_ret >= 0.05:
                        big_miss_count += 1
                    pending_entry = None

        if position is None and pending_entry is None:
            entry_signal = _entry_signal(i=i, frame=frame, equity=equity, breakout_mode=breakout_mode)
            if entry_signal is not None:
                total_signals += 1
                breakout_level, atr_value, reference_price, breakout_flag, ma_trend_flag = entry_signal
                next_open = opens[i + 1]
                close_now = closes[i]
                gap_pct = (next_open - close_now) / close_now
                if gap_pct <= GAP_FILTER_MAX:
                    entry_limit_price = reference_price * policy["limit_mult"]
                    position_cap = equity * MAX_POSITION_WEIGHT
                    quantity = floor(position_cap / entry_limit_price)
                    if quantity >= 1:
                        gate_decision = evaluate_entry_gate(frame=frame, idx=i, config=gate_config)
                        if not gate_decision.passed:
                            skipped_by_gate += 1
                            for reason in gate_decision.failed_reasons:
                                skipped_by_gate_reason_breakdown[reason] = skipped_by_gate_reason_breakdown.get(reason, 0) + 1
                            max_ret, est_pnl = _missed_trade_potential(
                                highs=highs,
                                breakout_level=breakout_level,
                                quantity=float(quantity),
                                signal_index=i,
                            )
                            _ = max_ret
                            skipped_by_gate_estimated_pnls.append(float(est_pnl))
                            if est_pnl > 0:
                                skipped_by_gate_winner_count += 1
                            continue
                        regime = _regime_label(frame=frame, i=i)
                        pending_entry = PendingEntryOrder(
                            symbol=symbol,
                            signal_index=i,
                            signal_time=bars[i].timestamp,
                            start_index=i + 1,
                            limit_price=entry_limit_price,
                            quantity=float(quantity),
                            breakout_level=breakout_level,
                            stop_price=reference_price - ATR_MULT * atr_value,
                            regime=regime,
                            breakout_flag=breakout_flag,
                            ma_trend_flag=ma_trend_flag,
                            chase_bps=policy["chase_bps"],
                            market_like=policy["market_like"],
                        )

        if position is not None:
            position.max_high_since_entry = max(position.max_high_since_entry, highs[i])
            mfe = _position_mfe(position)
            if mfe >= RISK_MFE_TRIGGER:
                position.risk_layer_armed = True

            risk_exit = _risk_exit(
                i=i,
                close=closes[i],
                low=lows[i],
                position=position,
                risk_policy=risk,
            )
            active_stop_price = risk_exit["stop_price"] if risk_exit is not None and risk_exit["kind"] == "stop" else position.stop_price
            if lows[i] <= active_stop_price:
                exit_signal_price = active_stop_price
                exit_fill_price = active_stop_price
                exit_time = bars[i].timestamp
                exit_signal_time = bars[i].timestamp
                stop_hit_flag = active_stop_price <= position.stop_price
                trend_break_2bar_flag = False
                exit_rule = "STOP" if stop_hit_flag else "RISK_BREAK_EVEN_STOP"
                entry_order_status = "FILLED"
                exit_order_status = "FILLED"
                entry_wait_bars = max(0, position.entry_index - position.signal_index)
                exit_wait_bars = 0
            elif risk_exit is not None and risk_exit["kind"] == "exit":
                exit_signal_price = float(risk_exit["price"])
                exit_fill_price = float(risk_exit["price"]) * (1 - slippage_rate)
                exit_time = bars[i].timestamp
                exit_signal_time = bars[i].timestamp
                stop_hit_flag = False
                trend_break_2bar_flag = False
                exit_rule = str(risk_exit["rule"])
                entry_order_status = "FILLED"
                exit_order_status = "FILLED"
                entry_wait_bars = max(0, position.entry_index - position.signal_index)
                exit_wait_bars = 0
            else:
                if pending_exit is None:
                    exit_reason = _exit_reason(i=i, frame=frame, lows=lows, position=position)
                    if exit_reason is not None:
                        pending_exit = PendingExitOrder(
                            signal_index=i,
                            signal_time=bars[i].timestamp,
                            start_index=i + 1,
                            limit_price=opens[i + 1],
                            exit_rule=("TREND_BREAK_2BAR" if exit_reason == "EXIT_TREND_BREAK" else "TIME_EXIT"),
                        )
                if pending_exit is not None and i >= pending_exit.start_index:
                    if lows[i] <= pending_exit.limit_price <= highs[i]:
                        pending_exit.status = "FILLED"
                        exit_signal_price = closes[pending_exit.signal_index]
                        exit_fill_price = pending_exit.limit_price * (1 - slippage_rate)
                        exit_time = bars[i].timestamp
                        exit_signal_time = pending_exit.signal_time
                        stop_hit_flag = False
                        trend_break_2bar_flag = pending_exit.exit_rule == "TREND_BREAK_2BAR"
                        exit_rule = pending_exit.exit_rule
                        entry_order_status = "FILLED"
                        exit_order_status = "FILLED"
                        entry_wait_bars = max(0, position.entry_index - position.signal_index)
                        exit_wait_bars = max(0, i - pending_exit.signal_index)
                        pending_exit = None
                    else:
                        pending_exit.wait_bars = i - pending_exit.signal_index
                        if pending_exit.wait_bars >= MAX_WAIT_BARS:
                            pending_exit.status = "EXPIRED"
                            pending_exit = None
                            position.had_exit_expired = True
                        continue
                else:
                    continue

            expected_pnl = (exit_signal_price - position.entry_price) * position.quantity
            gross_actual_pnl = (exit_fill_price - position.entry_fill_price) * position.quantity
            notional_entry = position.entry_fill_price * position.quantity
            notional_exit = exit_fill_price * position.quantity
            total_cost = (notional_entry + notional_exit) * fee_rate
            net_pnl = gross_actual_pnl - total_cost

            trade_id = f"full-{symbol}-{len(results) + 1:04d}"
            trade = TradeResult(
                trade_id=trade_id,
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
            metadata: dict[str, object] = {
                "signal_bar_index": position.signal_index,
                "signal_bar_time": position.signal_time.isoformat(),
                "entry_fill_bar_time": position.entry_time.isoformat(),
                "exit_signal_bar_time": exit_signal_time.isoformat(),
                "exit_fill_bar_time": exit_time.isoformat(),
                "entry_rule": "BREAKOUT + MA_TREND",
                "exit_rule": exit_rule,
                "risk_policy": str(risk_policy).strip().upper(),
                "breakout_level": float(position.breakout_level),
                "stop_price": float(position.stop_price),
                "max_mfe_pct": float(_position_mfe(position) * 100.0),
                "risk_layer_armed": bool(position.risk_layer_armed),
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
                "sector": map_symbol_to_sector(symbol),
                "reason": "ENTRY_BREAKOUT",
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
            results.append(
                FullTradeResult(
                    trade=trade,
                    cost=total_cost,
                    net_pnl=net_pnl,
                    regime=position.regime,
                    metadata=metadata,
                )
            )
            equity += net_pnl
            position = None

    fill_rate = (entry_filled / total_signals * 100.0) if total_signals > 0 else 0.0
    expired_rate = (entry_expired / total_signals * 100.0) if total_signals > 0 else 0.0
    stats = EntryExecutionStats(
        total_signals=total_signals,
        entry_filled=entry_filled,
        entry_expired=entry_expired,
        fill_rate=fill_rate,
        expired_rate=expired_rate,
        missed_trades=entry_expired,
        big_miss_count=big_miss_count,
        missed_potential_return_sum=missed_potential_return_sum,
        missed_profit_estimate=missed_profit_estimate,
        skipped_by_gate=skipped_by_gate,
        skipped_by_gate_reason_breakdown=dict(sorted(skipped_by_gate_reason_breakdown.items())),
        skipped_by_gate_estimated_pnls=tuple(skipped_by_gate_estimated_pnls),
        skipped_by_gate_winner_count=skipped_by_gate_winner_count,
    )
    return results, stats


def run_full_backtest_universe(
    *,
    symbols: list[str],
    base_dir: str | Path,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
    entry_policy: str = "BASELINE",
    risk_policy: str = "BASELINE",
    breakout_mode: str = "BASELINE",
    entry_gate_config: EntryGateConfig | None = None,
    mode: str = "single_symbol",
    max_positions: int = 3,
) -> list[FullTradeResult]:
    results, _stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        entry_policy=entry_policy,
        risk_policy=risk_policy,
        breakout_mode=breakout_mode,
        entry_gate_config=entry_gate_config,
        mode=mode,
        max_positions=max_positions,
    )
    return results


def run_full_backtest_universe_with_stats(
    *,
    symbols: list[str],
    base_dir: str | Path,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
    entry_policy: str = "BASELINE",
    risk_policy: str = "BASELINE",
    breakout_mode: str = "BASELINE",
    entry_gate_config: EntryGateConfig | None = None,
    mode: str = "single_symbol",
    max_positions: int = 3,
) -> tuple[list[FullTradeResult], EntryExecutionStats]:
    frames = load_universe_daily_bars(symbols, base_dir=base_dir)
    out: list[FullTradeResult] = []
    total_signals = 0
    entry_filled = 0
    entry_expired = 0
    big_miss_count = 0
    missed_potential_return_sum = 0.0
    missed_profit_estimate = 0.0
    skipped_by_gate = 0
    skipped_by_gate_reason_breakdown: dict[str, int] = {}
    skipped_by_gate_estimated_pnls: list[float] = []
    skipped_by_gate_winner_count = 0
    normalized_mode = str(mode).strip().lower()
    run_symbols = sorted(frames.keys())
    allocation_by_symbol = {symbol: 1.0 for symbol in run_symbols}
    if normalized_mode == "portfolio":
        snapshot = build_universe_snapshot(frames)
        filtered = filter_universe_snapshot(snapshot)
        ranked = rank_universe(filtered)
        portfolio_symbols = ranked["symbol"].head(max(1, int(max_positions))).tolist() if not ranked.empty else []
        if not portfolio_symbols:
            portfolio_symbols = run_symbols[: max(1, int(max_positions))]
        allocations = allocate_equal_weight(
            portfolio_symbols,
            config=AllocationConfig(max_positions=max_positions, max_exposure_per_symbol=1.0),
        )
        allocation_by_symbol = {str(item["symbol"]): float(item["allocation_pct"]) for item in allocations}
        run_symbols = sorted(allocation_by_symbol.keys())

    for symbol in run_symbols:
        bars = _bars_from_dataframe(frames[symbol])
        symbol_equity = initial_equity * float(allocation_by_symbol.get(symbol, 1.0))
        results, stats = run_full_backtest_with_stats(
            bars,
            symbol=symbol,
            initial_equity=symbol_equity,
            fee_rate=fee_rate,
            slippage_rate=slippage_rate,
            entry_policy=entry_policy,
            risk_policy=risk_policy,
            breakout_mode=breakout_mode,
            entry_gate_config=entry_gate_config,
        )
        out.extend(results)
        total_signals += stats.total_signals
        entry_filled += stats.entry_filled
        entry_expired += stats.entry_expired
        big_miss_count += stats.big_miss_count
        missed_potential_return_sum += stats.missed_potential_return_sum
        missed_profit_estimate += stats.missed_profit_estimate
        skipped_by_gate += stats.skipped_by_gate
        for reason, count in stats.skipped_by_gate_reason_breakdown.items():
            skipped_by_gate_reason_breakdown[reason] = skipped_by_gate_reason_breakdown.get(reason, 0) + int(count)
        skipped_by_gate_estimated_pnls.extend(stats.skipped_by_gate_estimated_pnls)
        skipped_by_gate_winner_count += stats.skipped_by_gate_winner_count
    fill_rate = (entry_filled / total_signals * 100.0) if total_signals > 0 else 0.0
    expired_rate = (entry_expired / total_signals * 100.0) if total_signals > 0 else 0.0
    agg_stats = EntryExecutionStats(
        total_signals=total_signals,
        entry_filled=entry_filled,
        entry_expired=entry_expired,
        fill_rate=fill_rate,
        expired_rate=expired_rate,
        missed_trades=entry_expired,
        big_miss_count=big_miss_count,
        missed_potential_return_sum=missed_potential_return_sum,
        missed_profit_estimate=missed_profit_estimate,
        skipped_by_gate=skipped_by_gate,
        skipped_by_gate_reason_breakdown=dict(sorted(skipped_by_gate_reason_breakdown.items())),
        skipped_by_gate_estimated_pnls=tuple(skipped_by_gate_estimated_pnls),
        skipped_by_gate_winner_count=skipped_by_gate_winner_count,
    )
    return sorted(out, key=lambda x: x.trade.entry_time), agg_stats


def summarize(results: list[FullTradeResult], *, initial_equity: float) -> FullSummary:
    return summarize_full_results(results, initial_equity=initial_equity)


def analyze_yearly(results: list[FullTradeResult]) -> pd.DataFrame:
    return analyze_yearly_performance(results)


def analyze_regime(results: list[FullTradeResult]) -> pd.DataFrame:
    return analyze_regime_performance(results)


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
    frame: pd.DataFrame,
    equity: float,
    breakout_mode: str = "BASELINE",
) -> tuple[float, float, float, bool, bool] | None:
    close_now = _frame_value(frame, i, "close")
    if close_now is None or close_now < MIN_CLOSE:
        return None

    max_affordable_price = equity * MAX_POSITION_WEIGHT
    if close_now > max_affordable_price:
        return None

    breakout_flag = bool(is_breakout(frame, i, breakout_mode=breakout_mode) is True)
    ma_trend_flag = bool(is_ma_trend(frame, i) is True)
    if not breakout_flag or not ma_trend_flag:
        return None

    avg_volume20 = _frame_value(frame, i, "avg_volume_20")
    avg_turnover20 = _frame_value(frame, i, "avg_turnover_20")
    if avg_volume20 is None or avg_turnover20 is None:
        return None
    if avg_volume20 < MIN_AVG_VOLUME or avg_turnover20 < MIN_AVG_TURNOVER:
        return None

    breakout_level = _frame_value(frame, i, breakout_column_for_mode(breakout_mode))
    atr = _frame_value(frame, i, "atr14")
    if atr is None or atr <= 0:
        return None

    return breakout_level, atr, breakout_level, breakout_flag, ma_trend_flag


def _entry_policy(name: str) -> dict[str, float | bool]:
    return get_entry_policy(name)


def _risk_policy(name: str) -> dict[str, bool]:
    return get_risk_policy(name)


def _entry_fill_price(*, low: float, high: float, open_px: float, pending: PendingEntryOrder) -> tuple[bool, float | None]:
    return resolve_entry_fill_price(low=low, high=high, open_px=open_px, pending=pending)


def _position_mfe(position: OpenPosition) -> float:
    return position_mfe(position)


def _risk_exit(
    *,
    i: int,
    close: float,
    low: float,
    position: OpenPosition,
    risk_policy: dict[str, bool],
) -> dict[str, float | str] | None:
    return evaluate_risk_exit(i=i, close=close, low=low, position=position, risk_policy=risk_policy)


def _missed_trade_potential(
    *,
    highs: list[float],
    breakout_level: float,
    quantity: float,
    signal_index: int,
    horizon_bars: int = MAX_HOLDING_DAYS,
) -> tuple[float, float]:
    return estimate_missed_trade_potential(
        highs=highs,
        breakout_level=breakout_level,
        quantity=quantity,
        signal_index=signal_index,
        horizon_bars=horizon_bars,
    )


def _exit_reason(*, i: int, frame: pd.DataFrame, lows: list[float], position: OpenPosition) -> str | None:
    if lows[i] <= position.stop_price:
        return "EXIT_STOP"
    if is_exit_condition(frame, i) is True:
        return "EXIT_TREND_BREAK"
    holding_days = i - position.entry_index + 1
    if holding_days > MAX_HOLDING_DAYS:
        return "EXIT_TIME"
    return None


def _regime_label(*, frame: pd.DataFrame, i: int) -> str:
    ma200 = _frame_value(frame, i, "ma200")
    close_now = _frame_value(frame, i, "close")
    if ma200 is None or close_now is None:
        return "BEAR"
    return "BULL" if close_now >= ma200 else "BEAR"


def _frame_value(frame: pd.DataFrame, i: int, column: str) -> float | None:
    if column not in frame.columns or not (0 <= i < len(frame)):
        return None
    value = frame.iloc[i][column]
    if pd.isna(value):
        return None
    return float(value)


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
    parser.add_argument("--entry-policy", type=str, default="BASELINE", help=f"Entry policy: {', '.join(sorted(ENTRY_POLICIES.keys()))}")
    parser.add_argument("--risk-policy", type=str, default="BASELINE", help=f"Risk policy: {', '.join(sorted(RISK_POLICIES.keys()))}")
    parser.add_argument("--breakout-mode", type=str, default="BASELINE", choices=["BASELINE", "A_10", "CRB"], help="Breakout mode")
    parser.add_argument("--mode", type=str, default="single_symbol", choices=["single_symbol", "portfolio"], help="Backtest mode")
    parser.add_argument("--max-positions", type=int, default=3, help="Max positions for portfolio mode")
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
        entry_policy=args.entry_policy,
        risk_policy=args.risk_policy,
        breakout_mode=args.breakout_mode,
        mode=args.mode,
        max_positions=args.max_positions,
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
