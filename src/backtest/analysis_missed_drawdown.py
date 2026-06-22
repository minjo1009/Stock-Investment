from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backtest import engine
from backtest.analysis_sector import SYMBOL_TO_SECTOR
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars


BIG_MISS_THRESHOLD = 0.05


@dataclass(frozen=True)
class MissedTrade:
    symbol: str
    signal_index: int
    signal_time: pd.Timestamp
    breakout_level: float
    quantity: float
    regime: str
    wait_bars: int
    max_future_return: float
    bucket: str
    est_missed_pnl: float


def _load_realistic_trades(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("trades", [])
    df = pd.DataFrame(rows)
    for col in ("entry_time", "exit_time", "signal_bar_time", "exit_signal_bar_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    for col in ("actual_pnl", "expected_pnl", "quantity", "entry_price", "breakout_level"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df, payload


def _compute_missed_bucket(ret: float) -> str:
    if ret >= BIG_MISS_THRESHOLD:
        return "BIG_MISS"
    if ret > 0:
        return "SMALL_MISS"
    return "NO_MOVE"


def _simulate_missed_trades(symbol: str, *, base_dir: Path) -> tuple[list[MissedTrade], int, int]:
    frame = load_daily_bars(symbol, base_dir=base_dir)
    bars = engine._bars_from_dataframe(frame)
    if len(bars) < engine.MA_SLOW + 5:
        return [], 0, 0

    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    opens = [bar.open for bar in bars]
    cond = engine.prepare_condition_frame(
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
    start_index = max(engine.MA_SLOW, engine.BREAKOUT_WINDOW, engine.ATR_PERIOD + 1)
    if start_index >= len(bars) - 1:
        return [], 0, 0

    equity = 100_000.0
    position: engine.OpenPosition | None = None
    pending_entry: engine.PendingEntryOrder | None = None
    pending_exit: engine.PendingExitOrder | None = None
    missed: list[MissedTrade] = []
    submitted = 0
    filled = 0

    for i in range(start_index, len(bars) - 1):
        if position is None and pending_entry is not None and i >= pending_entry.start_index:
            if lows[i] <= pending_entry.limit_price <= highs[i]:
                filled += 1
                position = engine.OpenPosition(
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
                )
                pending_entry = None
            else:
                wait_bars = i - pending_entry.signal_index
                if wait_bars >= engine.MAX_WAIT_BARS:
                    horizon_end = min(len(highs) - 1, pending_entry.signal_index + engine.MAX_HOLDING_DAYS)
                    future_high = max(highs[pending_entry.signal_index + 1 : horizon_end + 1]) if horizon_end > pending_entry.signal_index else pending_entry.breakout_level
                    max_future_return = (future_high - pending_entry.breakout_level) / pending_entry.breakout_level
                    bucket = _compute_missed_bucket(max_future_return)
                    est_missed_pnl = max_future_return * pending_entry.breakout_level * pending_entry.quantity
                    missed.append(
                        MissedTrade(
                            symbol=symbol,
                            signal_index=pending_entry.signal_index,
                            signal_time=pd.Timestamp(pending_entry.signal_time),
                            breakout_level=pending_entry.breakout_level,
                            quantity=pending_entry.quantity,
                            regime=pending_entry.regime,
                            wait_bars=wait_bars,
                            max_future_return=max_future_return,
                            bucket=bucket,
                            est_missed_pnl=est_missed_pnl,
                        )
                    )
                    pending_entry = None

        if position is None and pending_entry is None:
            entry = engine._entry_signal(i=i, frame=cond, equity=equity)
            if entry is not None:
                breakout_level, atr, reference_price, breakout_flag, ma_flag = entry
                gap_pct = (opens[i + 1] - closes[i]) / closes[i]
                if gap_pct <= engine.GAP_FILTER_MAX:
                    limit_price = reference_price * (1 + engine.ENTRY_LIMIT_BUFFER)
                    qty = int((equity * engine.MAX_POSITION_WEIGHT) // limit_price)
                    if qty >= 1:
                        submitted += 1
                        regime = engine._regime_label(frame=cond, i=i)
                        pending_entry = engine.PendingEntryOrder(
                            symbol=symbol,
                            signal_index=i,
                            signal_time=bars[i].timestamp,
                            start_index=i + 1,
                            limit_price=limit_price,
                            quantity=float(qty),
                            breakout_level=breakout_level,
                            stop_price=reference_price - engine.ATR_MULT * atr,
                            regime=regime,
                            breakout_flag=breakout_flag,
                            ma_trend_flag=ma_flag,
                        )

        if position is not None:
            if lows[i] <= position.stop_price:
                exit_fill = position.stop_price
                pnl = (exit_fill - position.entry_fill_price) * position.quantity
                equity += pnl
                position = None
                pending_exit = None
                continue

            if pending_exit is None:
                reason = engine._exit_reason(i=i, frame=cond, lows=lows, position=position)
                if reason is not None:
                    pending_exit = engine.PendingExitOrder(
                        signal_index=i,
                        signal_time=bars[i].timestamp,
                        start_index=i + 1,
                        limit_price=opens[i + 1],
                        exit_rule="TREND_BREAK_2BAR" if reason == "EXIT_TREND_BREAK" else "TIME_EXIT",
                    )

            if pending_exit is not None and i >= pending_exit.start_index:
                if lows[i] <= pending_exit.limit_price <= highs[i]:
                    pnl = (pending_exit.limit_price - position.entry_fill_price) * position.quantity
                    equity += pnl
                    position = None
                    pending_exit = None
                else:
                    wait = i - pending_exit.signal_index
                    if wait >= engine.MAX_WAIT_BARS:
                        pending_exit = None

    return missed, submitted, filled


def _drawdown_segments(trades: pd.DataFrame, top_n: int = 3) -> list[dict[str, Any]]:
    if trades.empty:
        return []
    frame = trades.sort_values("exit_time").copy()
    frame["actual_pnl"] = pd.to_numeric(frame["actual_pnl"], errors="coerce").fillna(0.0)
    frame["equity"] = frame["actual_pnl"].cumsum()
    frame["peak"] = frame["equity"].cummax()
    frame["drawdown"] = frame["peak"] - frame["equity"]
    troughs = frame.nlargest(top_n, "drawdown")
    segments: list[dict[str, Any]] = []
    for row in troughs.itertuples(index=False):
        trough_time = row.exit_time
        peak_subset = frame[frame["exit_time"] <= trough_time]
        peak_idx = peak_subset["equity"].idxmax()
        peak_time = frame.loc[peak_idx, "exit_time"]
        seg = frame[(frame["exit_time"] >= peak_time) & (frame["exit_time"] <= trough_time)].copy()
        if seg.empty:
            continue
        symbol_loss = (
            seg.groupby("symbol", as_index=False)["actual_pnl"]
            .sum()
            .sort_values("actual_pnl")
            .head(3)
        )
        exit_loss = (
            seg.groupby("exit_rule", as_index=False)["actual_pnl"]
            .sum()
            .sort_values("actual_pnl")
        )
        regime_loss = (
            seg.groupby("regime", as_index=False)["actual_pnl"]
            .sum()
            .sort_values("actual_pnl")
        )
        segments.append(
            {
                "peak_time": peak_time,
                "trough_time": trough_time,
                "drawdown": float(row.drawdown),
                "trade_count": int(len(seg)),
                "top_symbol_losses": symbol_loss.to_dict(orient="records"),
                "exit_loss": exit_loss.to_dict(orient="records"),
                "regime_loss": regime_loss.to_dict(orient="records"),
            }
        )
    return segments


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 064: Missed Trade / Drawdown Attribution")
    parser.add_argument("--trades", type=str, default="data/backtest/trades.json")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    args = parser.parse_args()

    realistic, payload = _load_realistic_trades(args.trades)
    realistic["exit_rule"] = realistic.get("exit_rule", pd.Series(dtype=str)).fillna("UNKNOWN")
    realistic["regime"] = realistic.get("regime", pd.Series(dtype=str)).fillna("UNKNOWN")
    realistic["sector"] = realistic.get("sector", pd.Series(dtype=str))
    realistic["sector"] = realistic["sector"].fillna(realistic.get("symbol", "").map(lambda s: SYMBOL_TO_SECTOR.get(str(s), "UNMAPPED")))

    filled = realistic.copy()
    filled["bucket"] = filled["actual_pnl"].map(lambda v: "FILLED_WIN" if float(v) > 0 else "FILLED_LOSS")
    filled_win = int((filled["bucket"] == "FILLED_WIN").sum())
    filled_loss = int((filled["bucket"] == "FILLED_LOSS").sum())

    all_missed: list[MissedTrade] = []
    total_signals = 0
    filled_signals = 0
    for symbol in args.symbols:
        missed, submitted, filled_count = _simulate_missed_trades(str(symbol).upper(), base_dir=Path(args.data_dir))
        all_missed.extend(missed)
        total_signals += submitted
        filled_signals += filled_count

    missed_df = pd.DataFrame([m.__dict__ for m in all_missed]) if all_missed else pd.DataFrame()
    missed_count = int(len(missed_df))
    big_miss_rate = float((missed_df["bucket"] == "BIG_MISS").mean() * 100.0) if not missed_df.empty else 0.0
    missed_avg_potential = float(missed_df["max_future_return"].mean() * 100.0) if not missed_df.empty else 0.0
    missed_profit_est = float(missed_df["est_missed_pnl"].sum()) if not missed_df.empty else 0.0

    win_rate = float((filled["actual_pnl"] > 0).mean() * 100.0) if not filled.empty else 0.0
    avg_holding_return = float(((filled["exit_fill_price"] - filled["entry_fill_price"]) / filled["entry_fill_price"]).mean() * 100.0) if not filled.empty else 0.0
    avg_pnl = float(filled["actual_pnl"].mean()) if not filled.empty else 0.0

    dd_segments = _drawdown_segments(filled, top_n=3)

    missed_signals = max(0, total_signals - filled_signals)
    fill_rate = (filled_signals / total_signals * 100.0) if total_signals > 0 else 0.0

    top_profit_symbols = (
        filled.groupby("symbol", as_index=False)["actual_pnl"]
        .sum()
        .sort_values("actual_pnl", ascending=False)
        .head(5)
        .to_dict(orient="records")
    )
    top_loss_symbols = (
        filled.groupby("symbol", as_index=False)["actual_pnl"]
        .sum()
        .sort_values("actual_pnl", ascending=True)
        .head(5)
        .to_dict(orient="records")
    )
    regime_loss = (
        filled.groupby("regime", as_index=False)["actual_pnl"]
        .sum()
        .sort_values("actual_pnl")
        .to_dict(orient="records")
    )

    report = {
        "trade_breakdown": {
            "filled_win": filled_win,
            "filled_loss": filled_loss,
            "missed_trade": missed_count,
        },
        "missed_trade_analysis": {
            "missed_trades": missed_count,
            "big_miss_rate_pct": big_miss_rate,
            "avg_potential_return_pct": missed_avg_potential,
            "missed_profit_estimate": missed_profit_est,
            "bucket_counts": missed_df["bucket"].value_counts(dropna=False).to_dict() if not missed_df.empty else {},
        },
        "filled_trade_analysis": {
            "filled_trades": int(len(filled)),
            "win_rate_pct": win_rate,
            "avg_holding_return_pct": avg_holding_return,
            "avg_pnl": avg_pnl,
        },
        "drawdown_attribution": dd_segments,
        "signal_vs_execution_gap": {
            "total_signals": total_signals,
            "filled_signals": filled_signals,
            "missed_signals": missed_signals,
            "fill_rate_pct": fill_rate,
            "missed_profit_estimate": missed_profit_est,
            "execution_stats": payload.get("execution_stats"),
        },
        "concentration": {
            "top_profit_symbols": top_profit_symbols,
            "top_loss_symbols": top_loss_symbols,
            "regime_loss": regime_loss,
        },
    }
    print(json.dumps(report, ensure_ascii=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

