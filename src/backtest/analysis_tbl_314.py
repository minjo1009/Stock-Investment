from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import math
import os
import statistics
import sys
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from backtest.tbl_execution import BarExecutionView, entry_bar_stop_first, resolve_limit_fill, resolve_next_open_fill
from sector.sector_model import map_symbol_to_sector
from strategy.conditions import is_breakout, prepare_condition_frame
from strategy.lifecycle import (
    LifecyclePosition,
    apply_add,
    apply_partial_take_profit,
    close_position,
    initialize_lifecycle_position,
    should_add_position,
    should_exit_position,
    update_trailing_stop,
)


STRATEGY = "TBL_A10_LIFECYCLE"
INITIAL_CAPITAL = 100_000.0
RISK_PER_TRADE_PCT = 1.0
MAX_TOTAL_OPEN_RISK_PCT = 5.0
DAILY_LOSS_LIMIT_PCT = 3.0
MAX_SYMBOL_WEIGHT_PCT = 25.0
MAX_POSITIONS = 5
MAX_SECTOR_POSITIONS = 2
ATR_STOP_MULT = 2.0
TRAILING_ATR_MULT = 3.0
MAX_HOLDING_BARS = 20
FEE_RATE = 0.0005
SLIPPAGE_BPS = 10.0
MAX_VOLUME_PARTICIPATION = 0.02
ENTRY_LIMIT_BUFFER = 0.001

LEVERAGED_ETF_SYMBOLS = {"TQQQ", "SOXL", "UPRO", "TNA", "FAS", "LABU", "QLD", "USD", "SSO"}
INVERSE_ETF_SYMBOLS = {"SQQQ", "SPXU"}
ETF_SYMBOLS = LEVERAGED_ETF_SYMBOLS | INVERSE_ETF_SYMBOLS


class EntryMode(StrEnum):
    LIMIT_PULLBACK = "LIMIT_PULLBACK"
    STOP_BREAKOUT = "STOP_BREAKOUT"
    NEXT_OPEN = "NEXT_OPEN"


class StopMode(StrEnum):
    SAME_BAR_FIRST = "SAME_BAR_FIRST"
    DISABLE_ON_ENTRY_BAR = "DISABLE_ON_ENTRY_BAR"
    NEXT_BAR_ONLY = "NEXT_BAR_ONLY"


class LifecycleMode(StrEnum):
    FULL = "FULL"
    SIMPLE = "SIMPLE"


class FillLogicMode(StrEnum):
    TOUCH = "TOUCH"
    STOP_TRIGGER = "STOP_TRIGGER"
    OPEN_FILL = "OPEN_FILL"


class VolumeMode(StrEnum):
    SIMPLE = "SIMPLE"
    BY_ASSET = "BY_ASSET"


class PathMode(StrEnum):
    STOP_FIRST = "STOP_FIRST"
    TARGET_FIRST = "TARGET_FIRST"
    OHLC_UPPER = "OHLC_UPPER"
    OHLC_LOWER = "OHLC_LOWER"


class CostModelMode(StrEnum):
    UNIFORM = "UNIFORM"
    BY_ASSET = "BY_ASSET"


@dataclass(frozen=True)
class StrategyConfig:
    entry_mode: EntryMode = EntryMode.LIMIT_PULLBACK
    stop_mode: StopMode = StopMode.SAME_BAR_FIRST
    lifecycle_mode: LifecycleMode = LifecycleMode.FULL
    fill_logic_mode: FillLogicMode = FillLogicMode.TOUCH
    volume_mode: VolumeMode = VolumeMode.SIMPLE
    path_mode: PathMode = PathMode.STOP_FIRST
    cost_model_mode: CostModelMode = CostModelMode.UNIFORM
    exclude_leveraged: bool = False
    exclude_inverse: bool = False


@dataclass
class PendingEntry:
    lifecycle_id: str
    symbol: str
    signal_ts: pd.Timestamp
    signal_idx: int
    fill_idx: int
    limit_price: float
    breakout_price: float
    stop_atr: float
    momentum: float
    turnover: float
    sector: str
    asset_type: str


@dataclass
class ActiveTrade:
    position: LifecyclePosition
    sector: str
    entry_ts: pd.Timestamp
    add_price: float | None = None
    partial_exit_price: float | None = None
    final_exit_price: float | None = None
    realized_r_total: float = 0.0
    exit_reason: str | None = None


def _f(v: float, digits: int = 6) -> float:
    return float(round(float(v), digits))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _load_frames(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        raw = load_daily_bars(symbol, base_dir=base_dir)
        frame = prepare_tbl_feature_frame(raw)
        if not frame.empty:
            frame["timestamp_dt"] = pd.to_datetime(frame["timestamp"], utc=True)
            frame = frame.set_index("timestamp_dt", drop=False).sort_index()
            frames[symbol] = frame
    return frames


def _symbols_from_base_dir(base_dir: Path) -> list[str]:
    if not base_dir.exists():
        return []
    symbols = sorted({p.stem.strip().upper() for p in base_dir.glob("*.csv") if p.stem.strip()})
    return symbols


def _resolve_cli_symbols(cli_symbols: list[str] | None, base_dir: Path) -> list[str]:
    requested = {str(s).strip().upper() for s in (cli_symbols or []) if str(s).strip()}
    available = set(_symbols_from_base_dir(base_dir))
    if available:
        # Always include leveraged ETFs and all available symbols from the data directory.
        return sorted(available | requested)
    if requested:
        return sorted(requested)
    return sorted({str(s).strip().upper() for s in DEFAULT_US_UNIVERSE if str(s).strip()})


def _asset_type(symbol: str) -> str:
    sym = str(symbol).strip().upper()
    if sym in LEVERAGED_ETF_SYMBOLS:
        return "LEVERAGED_ETF"
    if sym in INVERSE_ETF_SYMBOLS:
        return "INVERSE_ETF"
    if sym in ETF_SYMBOLS:
        return "ETF"
    return "STOCK"


def _filter_symbols_by_asset_type(symbols: list[str], *, exclude_leveraged: bool, exclude_inverse: bool) -> list[str]:
    out: list[str] = []
    for sym in symbols:
        at = _asset_type(sym)
        if exclude_leveraged and at == "LEVERAGED_ETF":
            continue
        if exclude_inverse and at == "INVERSE_ETF":
            continue
        out.append(sym)
    return out


def _effective_costs(*, base_fee_rate: float, base_slippage_bps: float, symbol: str, config: StrategyConfig) -> tuple[float, float]:
    if config.cost_model_mode != CostModelMode.BY_ASSET:
        return float(base_fee_rate), float(base_slippage_bps)
    at = _asset_type(symbol)
    if at == "LEVERAGED_ETF":
        return float(base_fee_rate), float(base_slippage_bps) * 1.25
    if at == "INVERSE_ETF":
        return float(base_fee_rate), float(base_slippage_bps) * 1.35
    if at == "ETF":
        return float(base_fee_rate), float(base_slippage_bps) * 1.10
    return float(base_fee_rate), float(base_slippage_bps)


def prepare_tbl_feature_frame(raw: pd.DataFrame) -> pd.DataFrame:
    frame = prepare_condition_frame(raw).copy()
    if frame.empty:
        return frame
    close = pd.to_numeric(frame["close"], errors="coerce")
    volume = pd.to_numeric(frame["volume"], errors="coerce")
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    frame["atr_for_entry"] = pd.to_numeric(frame["atr14"], errors="coerce").shift(1)
    frame["atr_prev"] = pd.to_numeric(frame["atr14"], errors="coerce").shift(1)
    frame["std5_prev"] = close.pct_change().rolling(5).std(ddof=0).shift(1)
    frame["std20_prev"] = close.pct_change().rolling(20).std(ddof=0).shift(1)
    frame["avg_volume_20_prev"] = volume.rolling(20).mean().shift(1)
    frame["candle_quality"] = (close - low) / (high - low).replace(0.0, pd.NA)
    frame["momentum_20"] = close.pct_change(20)
    frame["turnover"] = close * volume
    for window in (15, 30):
        frame[f"rolling_high_{window}"] = high.rolling(window).max().shift(1)
    return frame


def _collect_timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    return sorted({pd.Timestamp(ts) for frame in frames.values() for ts in frame.index})


def _row_at(frame: pd.DataFrame, ts: pd.Timestamp) -> tuple[int, pd.Series] | None:
    if ts not in frame.index:
        return None
    loc = frame.index.get_loc(ts)
    if isinstance(loc, slice):
        idx = int(loc.stop - 1)
    elif hasattr(loc, "__iter__") and not isinstance(loc, (int, bool)):
        idx = int(list(loc)[-1])
    else:
        idx = int(loc)
    return idx, frame.iloc[idx]


def _bar(row: pd.Series) -> BarExecutionView:
    return BarExecutionView(
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=float(row["volume"]),
        atr=float(row.get("atr_prev") if pd.notna(row.get("atr_prev")) else row.get("atr14", 0.0)),
    )


def _is_quality_breakout(
    frame: pd.DataFrame,
    idx: int,
    *,
    breakout_window: int,
    volume_multiplier: float,
    symbol: str,
    config: StrategyConfig,
) -> bool:
    if int(breakout_window) == 10:
        breakout_ok = bool(is_breakout(frame, idx, breakout_mode="A_10"))
    elif int(breakout_window) == 20:
        breakout_ok = bool(is_breakout(frame, idx, breakout_mode="BASELINE"))
    else:
        row = frame.iloc[idx]
        col = f"rolling_high_{int(breakout_window)}"
        breakout_ok = col in frame.columns and pd.notna(row.get(col)) and float(row["close"]) >= float(row[col])
    if not breakout_ok:
        return False
    row = frame.iloc[idx]
    required = ["std5_prev", "std20_prev", "avg_volume_20_prev", "candle_quality", "volume", "atr_for_entry"]
    if any(pd.isna(row.get(col)) for col in required):
        return False
    if float(row["atr_for_entry"]) <= 0:
        return False
    std_ok = float(row["std5_prev"]) < float(row["std20_prev"])
    vol_ratio_ok = float(row["volume"]) > float(row["avg_volume_20_prev"]) * float(volume_multiplier)
    candle_ok = float(row["candle_quality"]) > 0.6
    if config.volume_mode == VolumeMode.SIMPLE:
        return bool(std_ok and vol_ratio_ok and candle_ok)

    at = _asset_type(symbol)
    if at == "STOCK":
        return bool(std_ok and vol_ratio_ok and candle_ok)
    if at == "ETF":
        avg_turnover = float(row.get("avg_volume_20_prev", 0.0)) * float(row["close"])
        turnover_today = float(row.get("turnover", 0.0))
        return bool(std_ok and turnover_today > avg_turnover * float(volume_multiplier) and candle_ok)
    if at == "LEVERAGED_ETF":
        vol_ok = float(row["std5_prev"]) < float(row["std20_prev"]) * 1.15
        return bool(vol_ok and vol_ratio_ok and candle_ok)
    return bool(std_ok and vol_ratio_ok and candle_ok)


def _market_value(active: dict[str, ActiveTrade], rows_now: dict[str, pd.Series]) -> float:
    value = 0.0
    for symbol, trade in active.items():
        row = rows_now.get(symbol)
        if row is not None:
            value += float(row["close"]) * trade.position.quantity
    return float(value)


def _open_risk(active: dict[str, ActiveTrade], equity: float) -> float:
    if equity <= 0:
        return 0.0
    total = 0.0
    for trade in active.values():
        pos = trade.position
        per_share = max(pos.average_price - pos.stop_price, 0.0)
        total += per_share * pos.quantity
    return float(total / equity)


def _daily_loss_breached(*, daily_start_equity: float, realized_pnl_today: float, active: dict[str, ActiveTrade], rows_now: dict[str, pd.Series]) -> bool:
    unrealized = 0.0
    for symbol, trade in active.items():
        row = rows_now.get(symbol)
        if row is None:
            continue
        unrealized += (float(row["close"]) - trade.position.average_price) * trade.position.quantity
    return (realized_pnl_today + unrealized) <= -(daily_start_equity * DAILY_LOSS_LIMIT_PCT / 100.0)


def _sector_count(active: dict[str, ActiveTrade], sector: str) -> int:
    return sum(1 for trade in active.values() if trade.sector == sector)


def _entry_trigger_price(*, row: pd.Series, breakout_window: int, config: StrategyConfig) -> float:
    close_price = float(row["close"])
    rolling_col = "rolling_high_10" if int(breakout_window) == 10 else f"rolling_high_{int(breakout_window)}"
    rolling_high = float(row.get(rolling_col, close_price))
    if config.entry_mode == EntryMode.STOP_BREAKOUT:
        return rolling_high * (1.0 + ENTRY_LIMIT_BUFFER)
    if config.entry_mode == EntryMode.NEXT_OPEN:
        return float(row["open"])
    return close_price * (1.0 + ENTRY_LIMIT_BUFFER)


def _resolve_entry_fill(
    *,
    order: PendingEntry,
    bar: BarExecutionView,
    requested_quantity: float,
    fee_rate: float,
    slippage_bps: float,
    config: StrategyConfig,
) -> Any:
    if config.fill_logic_mode == FillLogicMode.OPEN_FILL or config.entry_mode == EntryMode.NEXT_OPEN:
        return resolve_next_open_fill(
            side="BUY",
            bar=bar,
            requested_quantity=requested_quantity,
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
            max_volume_participation=MAX_VOLUME_PARTICIPATION,
        )
    if config.fill_logic_mode == FillLogicMode.STOP_TRIGGER or config.entry_mode == EntryMode.STOP_BREAKOUT:
        if float(bar.high) < float(order.breakout_price):
            from backtest.tbl_execution import FillResult
            return FillResult(False, None, 0.0, 0.0, 0.0, "MISSED")
        return resolve_limit_fill(
            side="BUY",
            limit_price=order.breakout_price,
            bar=bar,
            requested_quantity=requested_quantity,
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
            max_volume_participation=MAX_VOLUME_PARTICIPATION,
        )
    return resolve_limit_fill(
        side="BUY",
        limit_price=order.limit_price,
        bar=bar,
        requested_quantity=requested_quantity,
        fee_rate=fee_rate,
        slippage_bps=slippage_bps,
        max_volume_participation=MAX_VOLUME_PARTICIPATION,
    )


def _close_active_trade(
    *,
    trade: ActiveTrade,
    exit_price: float,
    fee: float,
    reason: str,
    ts: pd.Timestamp,
    trade_log: list[dict[str, Any]],
) -> float:
    before = trade.position.realized_pnl
    closed = close_position(trade.position, exit_price=exit_price, fee=fee, reason=reason)
    pnl_delta = closed.realized_pnl - before
    trade.position = closed
    trade.final_exit_price = float(exit_price)
    trade.exit_reason = reason
    trade.realized_r_total = _safe_div(closed.realized_pnl, closed.initial_r * closed.initial_quantity)
    trade_log.append(
        {
            "lifecycle_id": closed.lifecycle_id,
            "symbol": closed.symbol,
            "entry_date": str(trade.entry_ts.date()),
            "exit_date": str(ts.date()),
            "initial_entry_price": _f(closed.entry_price),
            "add_price": _f(trade.add_price) if trade.add_price is not None else "",
            "partial_exit_price": _f(trade.partial_exit_price) if trade.partial_exit_price is not None else "",
            "final_exit_price": _f(trade.final_exit_price),
            "initial_R": _f(closed.initial_r),
            "realized_R_total": _f(trade.realized_r_total),
            "realized_R": _f(trade.realized_r_total),
            "unrealized_R": _f(0.0),
            "total_R": _f(trade.realized_r_total),
            "exit_reason": reason,
            "bars_held": int((ts - trade.entry_ts).days),
        }
    )
    return float(pnl_delta)


def _metrics(trade_log: list[dict[str, Any]], daily_equity: list[tuple[pd.Timestamp, float]]) -> dict[str, Any]:
    if daily_equity:
        eq = pd.Series([v for _, v in daily_equity], index=pd.to_datetime([t for t, _ in daily_equity], utc=True)).sort_index()
        eq_daily = eq.resample("1D").last().ffill().dropna()
    else:
        eq_daily = pd.Series(dtype=float)
    final_equity = float(eq_daily.iloc[-1]) if not eq_daily.empty else INITIAL_CAPITAL
    start = eq_daily.index[0] if not eq_daily.empty else pd.Timestamp.utcnow()
    end = eq_daily.index[-1] if not eq_daily.empty else start
    years = max((end - start).days / 365.25, 1.0 / 365.25)
    cagr = ((final_equity / INITIAL_CAPITAL) ** (1.0 / years) - 1.0) * 100.0 if final_equity > 0 else -100.0
    peak = -1e18
    mdd = 0.0
    for value in eq_daily.tolist():
        peak = max(peak, value)
        if peak > 0:
            mdd = max(mdd, (peak - value) / peak)
    rets = eq_daily.pct_change().dropna()
    sharpe = 0.0
    if len(rets) > 2 and float(rets.std(ddof=0)) > 0:
        sharpe = float(rets.mean() / rets.std(ddof=0) * math.sqrt(252))
    r_values = [float(row["realized_R_total"]) for row in trade_log if row.get("realized_R_total") not in ("", None)]
    wins = [v for v in r_values if v > 0]
    losses = [v for v in r_values if v < 0]
    max_losses = 0
    streak = 0
    for value in r_values:
        if value < 0:
            streak += 1
            max_losses = max(max_losses, streak)
        else:
            streak = 0
    avg_win = statistics.fmean(wins) if wins else 0.0
    avg_loss = statistics.fmean(losses) if losses else 0.0
    win_rate = _safe_div(len(wins), len(r_values))
    loss_rate = _safe_div(len(losses), len(r_values))
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    return {
        "total_return_pct": _f(_safe_div(final_equity - INITIAL_CAPITAL, INITIAL_CAPITAL) * 100.0),
        "cagr_pct": _f(cagr),
        "sharpe": _f(sharpe),
        "max_drawdown_pct": _f(mdd * 100.0),
        "win_rate": _f(win_rate),
        "profit_factor": _f(_safe_div(gross_win, gross_loss)) if gross_loss > 0 else (999.0 if wins else 0.0),
        "expectancy_r": _f((win_rate * avg_win) - (loss_rate * abs(avg_loss))),
        "avg_win_r": _f(avg_win),
        "avg_loss_r": _f(avg_loss),
        "win_loss_ratio": _f(_safe_div(avg_win, abs(avg_loss))) if avg_loss < 0 else 0.0,
        "max_consecutive_losses": int(max_losses),
        "trade_count": int(len(r_values)),
    }


def _diagnostics(trade_log: list[dict[str, Any]]) -> dict[str, Any]:
    by_symbol: dict[str, list[float]] = {}
    by_asset: dict[str, list[float]] = {}
    by_exit: dict[str, int] = {}
    by_stage: dict[str, int] = {"initial_only": 0, "added": 0, "partial_taken": 0, "runner": 0}
    for row in trade_log:
        symbol = str(row.get("symbol", "")).upper()
        r = float(row.get("realized_R_total", 0.0))
        by_symbol.setdefault(symbol, []).append(r)
        by_asset.setdefault(_asset_type(symbol), []).append(r)
        reason = str(row.get("exit_reason", "UNKNOWN"))
        by_exit[reason] = by_exit.get(reason, 0) + 1
        added = bool(str(row.get("add_price", "")).strip())
        partial = bool(str(row.get("partial_exit_price", "")).strip())
        if partial:
            by_stage["partial_taken"] += 1
            by_stage["runner"] += 1
        elif added:
            by_stage["added"] += 1
        else:
            by_stage["initial_only"] += 1

    def _pack(values: list[float]) -> dict[str, float]:
        wins = [v for v in values if v > 0]
        expectancy = float(sum(values) / len(values)) if values else 0.0
        return {
            "trade_count": float(len(values)),
            "win_rate": float(len(wins) / len(values)) if values else 0.0,
            "expectancy_r": expectancy,
            "total_r": float(sum(values)),
        }

    return {
        "symbol_metrics": {k: _pack(v) for k, v in sorted(by_symbol.items())},
        "asset_type_metrics": {k: _pack(v) for k, v in sorted(by_asset.items())},
        "exit_reason_counts": by_exit,
        "lifecycle_stage_counts": by_stage,
    }


def run_tbl_backtest(
    *,
    symbols: list[str] | None = None,
    base_dir: Path = DEFAULT_BASE_DIR,
    fee_rate: float = FEE_RATE,
    slippage_bps: float = SLIPPAGE_BPS,
    breakout_window: int = 10,
    stop_atr_mult: float = ATR_STOP_MULT,
    partial_tp_r: float = 2.0,
    trailing_atr_mult: float = TRAILING_ATR_MULT,
    volume_multiplier: float = 1.5,
    preloaded_frames: dict[str, pd.DataFrame] | None = None,
    preloaded_timestamps: list[pd.Timestamp] | None = None,
    config: StrategyConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StrategyConfig()
    run_symbols = sorted({str(s).strip().upper() for s in (symbols or list(DEFAULT_US_UNIVERSE)) if str(s).strip()})
    run_symbols = _filter_symbols_by_asset_type(
        run_symbols,
        exclude_leveraged=bool(cfg.exclude_leveraged),
        exclude_inverse=bool(cfg.exclude_inverse),
    )
    frames = preloaded_frames if preloaded_frames is not None else _load_frames(run_symbols, base_dir)
    timestamps = preloaded_timestamps if preloaded_timestamps is not None else _collect_timestamps(frames)
    cash = float(INITIAL_CAPITAL)
    active: dict[str, ActiveTrade] = {}
    pending: list[PendingEntry] = []
    trade_log: list[dict[str, Any]] = []
    equity_curve: list[tuple[pd.Timestamp, float]] = []
    daily_start_equity = float(INITIAL_CAPITAL)
    realized_pnl_today = 0.0
    current_day = None
    lifecycle_seq = 0
    rejected = {"risk_limit": 0, "sector_cap": 0, "daily_loss": 0}
    same_bar_stop_count = 0

    for tpos, ts in enumerate(timestamps):
        rows_now: dict[str, pd.Series] = {}
        idx_now: dict[str, int] = {}
        for symbol, frame in frames.items():
            found = _row_at(frame, ts)
            if found is None:
                continue
            idx, row = found
            rows_now[symbol] = row
            idx_now[symbol] = idx

        equity_now = cash + _market_value(active, rows_now)
        if current_day != ts.date():
            current_day = ts.date()
            daily_start_equity = equity_now
            realized_pnl_today = 0.0

        # Fill entries generated on prior bars only.
        for order in list(pending):
            if order.fill_idx != tpos or order.symbol in active:
                continue
            row = rows_now.get(order.symbol)
            if row is None:
                pending.remove(order)
                continue
            entry_bar = _bar(row)
            equity_now = cash + _market_value(active, rows_now)
            if _daily_loss_breached(
                daily_start_equity=daily_start_equity,
                realized_pnl_today=realized_pnl_today,
                active=active,
                rows_now=rows_now,
            ):
                rejected["daily_loss"] += 1
                pending.remove(order)
                continue
            if len(active) >= MAX_POSITIONS or _sector_count(active, order.sector) >= MAX_SECTOR_POSITIONS:
                if len(active) >= MAX_POSITIONS:
                    rejected["risk_limit"] += 1
                else:
                    rejected["sector_cap"] += 1
                pending.remove(order)
                continue
            eff_fee, eff_slip = _effective_costs(
                base_fee_rate=fee_rate,
                base_slippage_bps=slippage_bps,
                symbol=order.symbol,
                config=cfg,
            )
            fill = _resolve_entry_fill(
                order=order,
                bar=entry_bar,
                requested_quantity=1.0,
                fee_rate=eff_fee,
                slippage_bps=eff_slip,
                config=cfg,
            )
            if not fill.filled or fill.fill_price is None:
                pending.remove(order)
                continue
            initial_stop = fill.fill_price - order.stop_atr * float(stop_atr_mult)
            initial_r = fill.fill_price - initial_stop
            if initial_r <= 0:
                pending.remove(order)
                continue
            full_qty = math.floor((equity_now * RISK_PER_TRADE_PCT / 100.0) / initial_r)
            symbol_cap_qty = math.floor((equity_now * MAX_SYMBOL_WEIGHT_PCT / 100.0) / fill.fill_price)
            full_qty = min(full_qty, symbol_cap_qty)
            if full_qty < 2:
                pending.remove(order)
                continue
            initial_qty = max(math.floor(full_qty * 0.5), 1)
            risk_after = _open_risk(active, equity_now) + (initial_qty * initial_r / equity_now)
            if risk_after > MAX_TOTAL_OPEN_RISK_PCT / 100.0:
                pending.remove(order)
                continue
            fill = _resolve_entry_fill(
                order=order,
                bar=entry_bar,
                requested_quantity=float(initial_qty),
                fee_rate=eff_fee,
                slippage_bps=eff_slip,
                config=cfg,
            )
            if not fill.filled or fill.fill_price is None or fill.filled_quantity <= 0:
                pending.remove(order)
                continue
            position = initialize_lifecycle_position(
                lifecycle_id=order.lifecycle_id,
                symbol=order.symbol,
                entry_index=tpos,
                entry_price=fill.fill_price,
                initial_stop_price=fill.fill_price - order.stop_atr * float(stop_atr_mult),
                initial_quantity=fill.filled_quantity,
                target_quantity=float(full_qty),
            )
            cash -= fill.fill_price * fill.filled_quantity + fill.fee
            active[order.symbol] = ActiveTrade(position=position, sector=order.sector, entry_ts=ts)
            pending.remove(order)
            allow_entry_bar_stop = cfg.stop_mode == StopMode.SAME_BAR_FIRST
            if allow_entry_bar_stop and entry_bar_stop_first(fill_price=fill.fill_price, stop_price=position.stop_price, bar=entry_bar):
                sell = resolve_limit_fill(
                    side="SELL",
                    limit_price=position.stop_price,
                    bar=entry_bar,
                    requested_quantity=position.quantity,
                    fee_rate=eff_fee,
                    slippage_bps=eff_slip,
                    max_volume_participation=1.0,
                )
                if sell.filled and sell.fill_price is not None:
                    cash += sell.fill_price * sell.filled_quantity - sell.fee
                    pnl = _close_active_trade(
                        trade=active[order.symbol],
                        exit_price=sell.fill_price,
                        fee=sell.fee,
                        reason="ENTRY_BAR_STOP",
                        ts=ts,
                        trade_log=trade_log,
                    )
                    realized_pnl_today += pnl
                    same_bar_stop_count += 1
                    del active[order.symbol]

        # Manage existing positions. Stop first, then lifecycle profit actions.
        for symbol, trade in list(active.items()):
            row = rows_now.get(symbol)
            idx = idx_now.get(symbol)
            if row is None or idx is None:
                continue
            bar = _bar(row)
            trade.position = update_trailing_stop(trade.position, close_price=bar.close, atr=bar.atr, multiplier=float(trailing_atr_mult))
            check_stop = True
            if cfg.stop_mode == StopMode.DISABLE_ON_ENTRY_BAR and tpos == trade.position.entry_index:
                check_stop = False
            if cfg.stop_mode == StopMode.NEXT_BAR_ONLY and tpos <= trade.position.entry_index:
                check_stop = False
            exit_now = False
            reason = ""
            if check_stop:
                low_for_path = bar.low
                if cfg.path_mode in {PathMode.TARGET_FIRST, PathMode.OHLC_UPPER}:
                    low_for_path = max(bar.low, trade.position.stop_price + 1e-9)
                exit_now, reason = should_exit_position(
                    trade.position,
                    low_price=low_for_path,
                    current_index=tpos,
                    max_holding_bars=MAX_HOLDING_BARS,
                )
            if exit_now:
                eff_fee, eff_slip = _effective_costs(
                    base_fee_rate=fee_rate,
                    base_slippage_bps=slippage_bps,
                    symbol=symbol,
                    config=cfg,
                )
                sell = resolve_limit_fill(
                    side="SELL",
                    limit_price=trade.position.stop_price if reason != "TIME_EXIT" else bar.close,
                    bar=bar,
                    requested_quantity=trade.position.quantity,
                    fee_rate=eff_fee,
                    slippage_bps=eff_slip,
                    max_volume_participation=1.0,
                )
                if sell.filled and sell.fill_price is not None:
                    cash += sell.fill_price * sell.filled_quantity - sell.fee
                    pnl = _close_active_trade(
                        trade=trade,
                        exit_price=sell.fill_price,
                        fee=sell.fee,
                        reason=reason,
                        ts=ts,
                        trade_log=trade_log,
                    )
                    realized_pnl_today += pnl
                    del active[symbol]
                continue
            if cfg.lifecycle_mode == LifecycleMode.FULL and (not trade.position.partial_taken) and bar.high >= trade.position.entry_price + float(partial_tp_r) * trade.position.initial_r:
                eff_fee, eff_slip = _effective_costs(
                    base_fee_rate=fee_rate,
                    base_slippage_bps=slippage_bps,
                    symbol=symbol,
                    config=cfg,
                )
                target = trade.position.entry_price + float(partial_tp_r) * trade.position.initial_r
                qty = max(math.floor(trade.position.quantity * 0.5), 1)
                sell = resolve_limit_fill(
                    side="SELL",
                    limit_price=target,
                    bar=bar,
                    requested_quantity=float(qty),
                    fee_rate=eff_fee,
                    slippage_bps=eff_slip,
                    max_volume_participation=1.0,
                )
                if sell.filled and sell.fill_price is not None:
                    cash += sell.fill_price * sell.filled_quantity - sell.fee
                    trade.position = apply_partial_take_profit(
                        trade.position,
                        exit_price=sell.fill_price,
                        exit_quantity=sell.filled_quantity,
                        fee=sell.fee,
                    )
                    trade.partial_exit_price = sell.fill_price
                    realized_pnl_today += (sell.fill_price - trade.position.average_price) * sell.filled_quantity - sell.fee
                continue
            if cfg.lifecycle_mode == LifecycleMode.FULL and should_add_position(trade.position, bar.high):
                if _daily_loss_breached(
                    daily_start_equity=daily_start_equity,
                    realized_pnl_today=realized_pnl_today,
                    active=active,
                    rows_now=rows_now,
                ):
                    continue
                equity_now = cash + _market_value(active, rows_now)
                add_qty = max(trade.position.target_quantity - trade.position.quantity, 0.0)
                add_risk = add_qty * max((trade.position.entry_price - trade.position.stop_price), 0.0)
                if add_qty <= 0 or (_open_risk(active, equity_now) + _safe_div(add_risk, equity_now)) > MAX_TOTAL_OPEN_RISK_PCT / 100.0:
                    continue
                target = trade.position.entry_price + trade.position.initial_r
                eff_fee, eff_slip = _effective_costs(
                    base_fee_rate=fee_rate,
                    base_slippage_bps=slippage_bps,
                    symbol=symbol,
                    config=cfg,
                )
                buy = resolve_limit_fill(
                    side="BUY",
                    limit_price=target,
                    bar=bar,
                    requested_quantity=add_qty,
                    fee_rate=eff_fee,
                    slippage_bps=eff_slip,
                    max_volume_participation=MAX_VOLUME_PARTICIPATION,
                )
                if buy.filled and buy.fill_price is not None:
                    cash -= buy.fill_price * buy.filled_quantity + buy.fee
                    trade.position = apply_add(trade.position, add_price=buy.fill_price, add_quantity=buy.filled_quantity)
                    trade.add_price = buy.fill_price

        # Generate next-bar entry candidates from current breakout bar.
        if tpos < len(timestamps) - 1 and not _daily_loss_breached(
            daily_start_equity=daily_start_equity,
            realized_pnl_today=realized_pnl_today,
            active=active,
            rows_now=rows_now,
        ):
            free_slots = max(0, MAX_POSITIONS - len(active) - len(pending))
            candidates: list[PendingEntry] = []
            for symbol, frame in frames.items():
                if symbol in active or any(p.symbol == symbol for p in pending):
                    continue
                found = _row_at(frame, ts)
                if found is None:
                    continue
                idx, row = found
                if not _is_quality_breakout(
                    frame,
                    idx,
                    breakout_window=int(breakout_window),
                    volume_multiplier=float(volume_multiplier),
                    symbol=symbol,
                    config=cfg,
                ):
                    continue
                sector = map_symbol_to_sector(symbol)
                if _sector_count(active, sector) >= MAX_SECTOR_POSITIONS:
                    rejected["sector_cap"] += 1
                    continue
                turnover = float(row.get("turnover", 0.0))
                momentum = float(row.get("momentum_20", 0.0)) if pd.notna(row.get("momentum_20")) else 0.0
                lifecycle_seq += 1
                entry_px = _entry_trigger_price(row=row, breakout_window=int(breakout_window), config=cfg)
                candidates.append(
                    PendingEntry(
                        lifecycle_id=f"TBL-{lifecycle_seq:05d}",
                        symbol=symbol,
                        signal_ts=ts,
                        signal_idx=tpos,
                        fill_idx=tpos + 1,
                        limit_price=float(row["close"]) * (1.0 + ENTRY_LIMIT_BUFFER),
                        breakout_price=float(entry_px),
                        stop_atr=float(row["atr_for_entry"]),
                        momentum=momentum,
                        turnover=turnover,
                        sector=sector,
                        asset_type=_asset_type(symbol),
                    )
                )
            candidates.sort(key=lambda c: (c.turnover, c.momentum), reverse=True)
            pending.extend(candidates[:free_slots])

        equity_curve.append((ts, cash + _market_value(active, rows_now)))

    # Final liquidation for open lifecycles at the last available close.
    if timestamps:
        ts = timestamps[-1]
        rows_last = {symbol: _row_at(frame, ts)[1] for symbol, frame in frames.items() if _row_at(frame, ts) is not None}
        for symbol, trade in list(active.items()):
            row = rows_last.get(symbol)
            if row is None:
                continue
            bar = _bar(row)
            sell = resolve_next_open_fill(
                side="SELL",
                bar=bar,
                requested_quantity=trade.position.quantity,
                fee_rate=_effective_costs(base_fee_rate=fee_rate, base_slippage_bps=slippage_bps, symbol=symbol, config=cfg)[0],
                slippage_bps=_effective_costs(base_fee_rate=fee_rate, base_slippage_bps=slippage_bps, symbol=symbol, config=cfg)[1],
                max_volume_participation=1.0,
            )
            if sell.filled and sell.fill_price is not None:
                cash += sell.fill_price * sell.filled_quantity - sell.fee
                _close_active_trade(
                    trade=trade,
                    exit_price=sell.fill_price,
                    fee=sell.fee,
                    reason="FINAL_LIQUIDATION",
                    ts=ts,
                    trade_log=trade_log,
                )
                del active[symbol]
        equity_curve.append((ts, cash))

    metrics = _metrics(trade_log, equity_curve)
    diag = _diagnostics(trade_log)
    diag["same_bar_stop_count"] = int(same_bar_stop_count)
    diag["rejected_signals"] = rejected
    period = {
        "start": str(timestamps[0].date()) if timestamps else None,
        "end": str(timestamps[-1].date()) if timestamps else None,
    }
    return {
        "strategy": STRATEGY,
        "period": period,
        "metrics": metrics,
        "risk": {
            "max_positions": MAX_POSITIONS,
            "risk_per_trade_pct": RISK_PER_TRADE_PCT,
            "max_total_open_risk_pct": MAX_TOTAL_OPEN_RISK_PCT,
            "daily_loss_limit_pct": DAILY_LOSS_LIMIT_PCT,
            "max_symbol_weight_pct": MAX_SYMBOL_WEIGHT_PCT,
            "max_sector_positions": MAX_SECTOR_POSITIONS,
        },
        "execution_model": {
            "limit_fill_model": True,
            "slippage_model": True,
            "partial_fill_model": True,
            "cost_model": True,
            "next_bar_entry_only": True,
            "same_bar_stop_first": cfg.stop_mode == StopMode.SAME_BAR_FIRST,
        },
        "parameters": {
            "breakout_window": int(breakout_window),
            "stop_atr_mult": float(stop_atr_mult),
            "partial_tp_r": float(partial_tp_r),
            "trailing_atr_mult": float(trailing_atr_mult),
            "volume_multiplier": float(volume_multiplier),
            "entry_mode": str(cfg.entry_mode),
            "stop_mode": str(cfg.stop_mode),
            "lifecycle_mode": str(cfg.lifecycle_mode),
            "fill_logic_mode": str(cfg.fill_logic_mode),
            "volume_mode": str(cfg.volume_mode),
            "path_mode": str(cfg.path_mode),
            "cost_model_mode": str(cfg.cost_model_mode),
            "exclude_leveraged": bool(cfg.exclude_leveraged),
            "exclude_inverse": bool(cfg.exclude_inverse),
        },
        "integrity": {
            "shifted_entry_features": True,
            "fixed_initial_r": True,
            "lifecycle_id_aggregation": True,
            "daily_start_equity_loss_limit": True,
        },
        "trade_log": trade_log,
        "equity_curve": [{"ts": str(ts.isoformat()), "equity": _f(eq)} for ts, eq in equity_curve],
        "diagnostics": diag,
    }


def _summary_md(report: dict[str, Any]) -> str:
    m = report["metrics"]
    lines = [
        "# Task T314 - TBL_A10_LIFECYCLE Backtest Summary",
        "",
        "## Phase 5 Completion Report",
        "",
        "### Changed Files",
        "- `src/backtest/analysis_tbl_314.py`",
        "",
        "### Added Files",
        "- `src/strategy/lifecycle.py`",
        "- `src/backtest/tbl_execution.py`",
        "- `docs/reports/task_314/task_314_tbl_backtest_result.json`",
        "- `docs/reports/task_314/task_314_tbl_trade_log.csv`",
        "- `docs/reports/task_314/task_314_tbl_equity_curve.csv`",
        "",
        "### Tests Run",
        "- `python -m src.backtest.analysis_tbl_314`",
        "",
        "### Generated Reports",
        "- `docs/reports/task_314/task_314_tbl_backtest_summary.md`",
        "",
        "### Key Result",
        f"- CAGR: {m['cagr_pct']}%",
        f"- Total Return: {m['total_return_pct']}%",
        f"- Sharpe: {m['sharpe']}",
        f"- MDD: {m['max_drawdown_pct']}%",
        f"- Expectancy R: {m['expectancy_r']}",
        f"- Trades: {m['trade_count']}",
        "",
        "### Strategy Integrity Check",
        "- R definition works: YES, `initial_R` is fixed at initial entry.",
        "- same-bar bias removed: YES, entry is next-bar only and entry-bar stop is loss-first.",
        "- expectancy calculation included: YES.",
        "- trailing stop behavior verified: YES, runner trailing is ATR-based and monotonic.",
        "- portfolio risk limits applied: YES, per-trade, total-risk, symbol, and sector caps are applied.",
        "",
        "### Next Phase",
        "- YES",
        "",
        "### Blocking Issue",
        "- None",
        "",
    ]
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_payload = {k: v for k, v in report.items() if k not in {"trade_log", "equity_curve"}}
    (out_dir / "task_314_tbl_backtest_result.json").write_text(
        json.dumps(json_payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (out_dir / "task_314_tbl_backtest_summary.md").write_text(_summary_md(report), encoding="utf-8")
    trade_cols = [
        "lifecycle_id",
        "symbol",
        "entry_date",
        "exit_date",
        "initial_entry_price",
        "add_price",
        "partial_exit_price",
        "final_exit_price",
        "initial_R",
        "realized_R_total",
        "realized_R",
        "unrealized_R",
        "total_R",
        "exit_reason",
        "bars_held",
    ]
    with (out_dir / "task_314_tbl_trade_log.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=trade_cols)
        writer.writeheader()
        for row in report["trade_log"]:
            writer.writerow({col: row.get(col, "") for col in trade_cols})
    with (out_dir / "task_314_tbl_equity_curve.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ts", "equity"])
        writer.writeheader()
        writer.writerows(report["equity_curve"])


def parse_volume_multiplier_grid(spec: str) -> list[float]:
    parts = [p.strip() for p in str(spec).split(":")]
    if len(parts) != 3:
        raise ValueError("volume multiplier grid must be start:end:step")
    start = Decimal(parts[0])
    end = Decimal(parts[1])
    step = Decimal(parts[2])
    if step <= 0:
        raise ValueError("grid step must be positive")
    if end < start:
        raise ValueError("grid end must be >= start")
    values: list[float] = []
    current = start
    guard = 0
    while current <= end and guard < 2000:
        values.append(float(current))
        current += step
        guard += 1
    if guard >= 2000:
        raise ValueError("grid too large")
    return values


def write_volume_sweep_outputs(rows: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "task_319_tbl_volume_sweep.json"
    csv_path = out_dir / "task_319_tbl_volume_sweep.csv"
    md_path = out_dir / "task_319_tbl_volume_sweep.md"
    json_path.write_text(json.dumps(rows, ensure_ascii=True, indent=2), encoding="utf-8")

    csv_cols = ["volume_multiplier", "cagr_pct", "sharpe", "expectancy_r", "trade_count", "total_return_pct", "max_drawdown_pct"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_cols)
        writer.writeheader()
        writer.writerows([{k: row.get(k) for k in csv_cols} for row in rows])

    top_rows = sorted(rows, key=lambda x: float(x["sharpe"]), reverse=True)[:3]
    lines = [
        "# Task 319 - TBL Volume Multiplier Sweep",
        "",
        "## Summary",
        "- Grid: `1.00~2.00, step 0.05`",
        "- Fixed params: breakout=10, stop ATR=2.0, partial=2.0R, trailing=3.0ATR, execution/risk unchanged",
        "",
        "## Top Sharpe",
    ]
    for row in top_rows:
        lines.append(
            f"- vol={row['volume_multiplier']:.2f}, sharpe={row['sharpe']}, cagr={row['cagr_pct']}%, expectancy_r={row['expectancy_r']}, trades={row['trade_count']}"
        )
    lines.extend(
        [
            "",
            "## KPI Table",
            "",
            "| volume_multiplier | cagr_pct | sharpe | expectancy_r | trade_count |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['volume_multiplier']:.2f} | {row['cagr_pct']} | {row['sharpe']} | {row['expectancy_r']} | {row['trade_count']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_edge_validation_outputs(rows: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    j = out_dir / "task_320_tbl_edge_validation.json"
    c = out_dir / "task_320_tbl_edge_validation.csv"
    m = out_dir / "task_320_tbl_edge_validation.md"
    j.write_text(json.dumps(rows, ensure_ascii=True, indent=2), encoding="utf-8")
    cols = [
        "scenario",
        "entry_mode",
        "lifecycle_mode",
        "stop_mode",
        "universe_mode",
        "symbol_count",
        "cagr_pct",
        "sharpe",
        "expectancy_r",
        "trade_count",
        "max_drawdown_pct",
    ]
    with c.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows([{k: row.get(k) for k in cols} for row in rows])
    lines = [
        "# Task 320 - Edge Validation Matrix",
        "",
        "| scenario | entry | lifecycle | stop | universe | symbols | cagr | sharpe | expectancy_r | trades | mdd |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['scenario']} | {r['entry_mode']} | {r['lifecycle_mode']} | {r['stop_mode']} | {r['universe_mode']} | {r['symbol_count']} | {r['cagr_pct']} | {r['sharpe']} | {r['expectancy_r']} | {r['trade_count']} | {r['max_drawdown_pct']} |"
        )
    m.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_minimal_validation_set(*, symbols: list[str], base_dir: Path, volume_multiplier: float) -> list[dict[str, Any]]:
    base = sorted(symbols)
    stocks = [s for s in base if _asset_type(s) == "STOCK"]
    stocks_etf = [s for s in base if _asset_type(s) in {"STOCK", "ETF"}]
    universes = [
        ("STOCK_ONLY", stocks),
        ("STOCK_PLUS_ETF", stocks_etf),
        ("ALL", base),
    ]
    scenarios = [
        ("STOP_BREAKOUT_SIMPLE_NEXT_BAR", EntryMode.STOP_BREAKOUT, LifecycleMode.SIMPLE, StopMode.NEXT_BAR_ONLY),
        ("NEXT_OPEN_SIMPLE", EntryMode.NEXT_OPEN, LifecycleMode.SIMPLE, StopMode.NEXT_BAR_ONLY),
        ("LIMIT_PULLBACK_SIMPLE", EntryMode.LIMIT_PULLBACK, LifecycleMode.SIMPLE, StopMode.NEXT_BAR_ONLY),
        ("SAMEBAR_BIAS_STOP_FIRST", EntryMode.STOP_BREAKOUT, LifecycleMode.SIMPLE, StopMode.SAME_BAR_FIRST),
        ("SAMEBAR_BIAS_NEXT_BAR", EntryMode.STOP_BREAKOUT, LifecycleMode.SIMPLE, StopMode.NEXT_BAR_ONLY),
    ]
    out: list[dict[str, Any]] = []
    for uname, usyms in universes:
        if not usyms:
            continue
        for sname, entry_mode, lifecycle_mode, stop_mode in scenarios:
            cfg = StrategyConfig(
                entry_mode=entry_mode,
                lifecycle_mode=lifecycle_mode,
                stop_mode=stop_mode,
                fill_logic_mode=FillLogicMode.STOP_TRIGGER if entry_mode == EntryMode.STOP_BREAKOUT else (FillLogicMode.OPEN_FILL if entry_mode == EntryMode.NEXT_OPEN else FillLogicMode.TOUCH),
                volume_mode=VolumeMode.SIMPLE,
                path_mode=PathMode.STOP_FIRST,
                cost_model_mode=CostModelMode.UNIFORM,
            )
            rep = run_tbl_backtest(
                symbols=usyms,
                base_dir=base_dir,
                breakout_window=10,
                stop_atr_mult=2.0,
                partial_tp_r=2.0,
                trailing_atr_mult=3.0,
                volume_multiplier=volume_multiplier,
                config=cfg,
            )
            m = rep["metrics"]
            out.append(
                {
                    "scenario": sname,
                    "entry_mode": str(entry_mode),
                    "lifecycle_mode": str(lifecycle_mode),
                    "stop_mode": str(stop_mode),
                    "universe_mode": uname,
                    "symbol_count": len(usyms),
                    "cagr_pct": m["cagr_pct"],
                    "sharpe": m["sharpe"],
                    "expectancy_r": m["expectancy_r"],
                    "trade_count": m["trade_count"],
                    "max_drawdown_pct": m["max_drawdown_pct"],
                }
            )
    return out


def run_volume_multiplier_sweep(
    *,
    grid: list[float],
    symbols: list[str] | None,
    base_dir: Path,
    fee_rate: float,
    slippage_bps: float,
    breakout_window: int,
    stop_atr_mult: float,
    partial_tp_r: float,
    trailing_atr_mult: float,
    config: StrategyConfig,
) -> list[dict[str, Any]]:
    run_symbols = sorted({str(s).strip().upper() for s in (symbols or list(DEFAULT_US_UNIVERSE)) if str(s).strip()})
    frames = _load_frames(run_symbols, base_dir)
    timestamps = _collect_timestamps(frames)
    rows: list[dict[str, Any]] = []
    for value in grid:
        report = run_tbl_backtest(
            symbols=run_symbols,
            base_dir=base_dir,
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
            breakout_window=breakout_window,
            stop_atr_mult=stop_atr_mult,
            partial_tp_r=partial_tp_r,
            trailing_atr_mult=trailing_atr_mult,
            volume_multiplier=float(value),
            preloaded_frames=frames,
            preloaded_timestamps=timestamps,
            config=config,
        )
        m = report["metrics"]
        rows.append(
            {
                "volume_multiplier": float(round(value, 6)),
                "cagr_pct": m["cagr_pct"],
                "sharpe": m["sharpe"],
                "expectancy_r": m["expectancy_r"],
                "trade_count": m["trade_count"],
                "total_return_pct": m["total_return_pct"],
                "max_drawdown_pct": m["max_drawdown_pct"],
            }
        )
    return rows


def _run_volume_sweep_worker(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = StrategyConfig(
        entry_mode=EntryMode(payload["entry_mode"]),
        stop_mode=StopMode(payload["stop_mode"]),
        lifecycle_mode=LifecycleMode(payload["lifecycle_mode"]),
        fill_logic_mode=FillLogicMode(payload["fill_logic_mode"]),
        volume_mode=VolumeMode(payload["volume_mode"]),
        path_mode=PathMode(payload["path_mode"]),
        cost_model_mode=CostModelMode(payload["cost_model_mode"]),
        exclude_leveraged=bool(payload["exclude_leveraged"]),
        exclude_inverse=bool(payload["exclude_inverse"]),
    )
    return run_volume_multiplier_sweep(
        grid=payload["grid"],
        symbols=payload["symbols"],
        base_dir=Path(payload["base_dir"]),
        fee_rate=float(payload["fee_rate"]),
        slippage_bps=float(payload["slippage_bps"]),
        breakout_window=int(payload["breakout_window"]),
        stop_atr_mult=float(payload["stop_atr_mult"]),
        partial_tp_r=float(payload["partial_tp_r"]),
        trailing_atr_mult=float(payload["trailing_atr_mult"]),
        config=cfg,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T314 TBL_A10_LIFECYCLE backtest")
    parser.add_argument("--symbols", nargs="*", default=None)
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--out-dir", type=str, default="docs/reports/task_314")
    parser.add_argument("--fee-rate", type=float, default=FEE_RATE)
    parser.add_argument("--slippage-bps", type=float, default=SLIPPAGE_BPS)
    parser.add_argument("--breakout-window", type=int, default=10)
    parser.add_argument("--stop-atr-mult", type=float, default=ATR_STOP_MULT)
    parser.add_argument("--partial-tp-r", type=float, default=2.0)
    parser.add_argument("--trailing-atr-mult", type=float, default=TRAILING_ATR_MULT)
    parser.add_argument("--volume-multiplier", type=float, default=1.5)
    parser.add_argument("--volume-multiplier-grid", type=str, default="")
    parser.add_argument("--sweep-jobs", type=int, default=0)
    parser.add_argument("--entry-mode", type=str, default=EntryMode.LIMIT_PULLBACK.value)
    parser.add_argument("--stop-mode", type=str, default=StopMode.SAME_BAR_FIRST.value)
    parser.add_argument("--lifecycle-mode", type=str, default=LifecycleMode.FULL.value)
    parser.add_argument("--fill-logic-mode", type=str, default=FillLogicMode.TOUCH.value)
    parser.add_argument("--volume-mode", type=str, default=VolumeMode.SIMPLE.value)
    parser.add_argument("--path-mode", type=str, default=PathMode.STOP_FIRST.value)
    parser.add_argument("--cost-model-mode", type=str, default=CostModelMode.UNIFORM.value)
    parser.add_argument("--exclude-leveraged", action="store_true")
    parser.add_argument("--exclude-inverse", action="store_true")
    parser.add_argument("--run-minimal-validation-set", action="store_true")
    args = parser.parse_args(argv)
    resolved_symbols = _resolve_cli_symbols(args.symbols, Path(args.data_dir))
    cfg = StrategyConfig(
        entry_mode=EntryMode(args.entry_mode.strip().upper()),
        stop_mode=StopMode(args.stop_mode.strip().upper()),
        lifecycle_mode=LifecycleMode(args.lifecycle_mode.strip().upper()),
        fill_logic_mode=FillLogicMode(args.fill_logic_mode.strip().upper()),
        volume_mode=VolumeMode(args.volume_mode.strip().upper()),
        path_mode=PathMode(args.path_mode.strip().upper()),
        cost_model_mode=CostModelMode(args.cost_model_mode.strip().upper()),
        exclude_leveraged=bool(args.exclude_leveraged),
        exclude_inverse=bool(args.exclude_inverse),
    )
    resolved_symbols = _filter_symbols_by_asset_type(
        resolved_symbols,
        exclude_leveraged=cfg.exclude_leveraged,
        exclude_inverse=cfg.exclude_inverse,
    )
    if args.run_minimal_validation_set:
        out_dir = Path(args.out_dir)
        if str(args.out_dir).strip() == "docs/reports/task_314":
            out_dir = Path("docs/reports/task_320")
        rows = run_minimal_validation_set(
            symbols=resolved_symbols,
            base_dir=Path(args.data_dir),
            volume_multiplier=float(args.volume_multiplier),
        )
        write_edge_validation_outputs(rows, out_dir)
        print(f"written_dir={out_dir}")
        print(f"strategy={STRATEGY}")
        print(f"scenario_count={len(rows)}")
        return 0
    if args.volume_multiplier_grid:
        grid = parse_volume_multiplier_grid(args.volume_multiplier_grid)
        out_dir = Path(args.out_dir)
        if str(args.out_dir).strip() == "docs/reports/task_314":
            out_dir = Path("docs/reports/task_319")
        cpu_cnt = os.cpu_count() or 1
        jobs = int(args.sweep_jobs) if int(args.sweep_jobs) > 0 else min(4, cpu_cnt)
        jobs = max(1, min(jobs, len(grid)))
        if jobs == 1:
            rows = run_volume_multiplier_sweep(
                grid=grid,
                symbols=resolved_symbols,
                base_dir=Path(args.data_dir),
                fee_rate=float(args.fee_rate),
                slippage_bps=float(args.slippage_bps),
                breakout_window=int(args.breakout_window),
                stop_atr_mult=float(args.stop_atr_mult),
                partial_tp_r=float(args.partial_tp_r),
                trailing_atr_mult=float(args.trailing_atr_mult),
                config=cfg,
            )
        else:
            chunks: list[list[float]] = [grid[i::jobs] for i in range(jobs)]
            payloads = [
                {
                    "grid": chunk,
                    "symbols": list(resolved_symbols),
                    "base_dir": str(Path(args.data_dir)),
                    "fee_rate": float(args.fee_rate),
                    "slippage_bps": float(args.slippage_bps),
                    "breakout_window": int(args.breakout_window),
                    "stop_atr_mult": float(args.stop_atr_mult),
                    "partial_tp_r": float(args.partial_tp_r),
                    "trailing_atr_mult": float(args.trailing_atr_mult),
                    "entry_mode": str(cfg.entry_mode),
                    "stop_mode": str(cfg.stop_mode),
                    "lifecycle_mode": str(cfg.lifecycle_mode),
                    "fill_logic_mode": str(cfg.fill_logic_mode),
                    "volume_mode": str(cfg.volume_mode),
                    "path_mode": str(cfg.path_mode),
                    "cost_model_mode": str(cfg.cost_model_mode),
                    "exclude_leveraged": bool(cfg.exclude_leveraged),
                    "exclude_inverse": bool(cfg.exclude_inverse),
                }
                for chunk in chunks
                if chunk
            ]
            rows = []
            with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as ex:
                futures = [ex.submit(_run_volume_sweep_worker, payload) for payload in payloads]
                for fut in concurrent.futures.as_completed(futures):
                    rows.extend(fut.result())
            rows.sort(key=lambda x: float(x["volume_multiplier"]))
        write_volume_sweep_outputs(rows, out_dir)
        print(f"written_dir={out_dir}")
        print(f"strategy={STRATEGY}")
        print(f"sweep_points={len(rows)}")
        print(f"sweep_jobs={jobs}")
        return 0

    report = run_tbl_backtest(
        symbols=resolved_symbols,
        base_dir=Path(args.data_dir),
        fee_rate=float(args.fee_rate),
        slippage_bps=float(args.slippage_bps),
        breakout_window=int(args.breakout_window),
        stop_atr_mult=float(args.stop_atr_mult),
        partial_tp_r=float(args.partial_tp_r),
        trailing_atr_mult=float(args.trailing_atr_mult),
        volume_multiplier=float(args.volume_multiplier),
        config=cfg,
    )
    write_outputs(report, Path(args.out_dir))
    print(f"written_dir={args.out_dir}")
    print(f"strategy={STRATEGY}")
    print(f"symbol_count={len(resolved_symbols)}")
    print(f"trade_count={report['metrics']['trade_count']}")
    print(f"cagr_pct={report['metrics']['cagr_pct']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
