from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from backtest.engine_full import FullTradeResult, run_full_backtest_universe_with_stats
from strategy.conditions import prepare_condition_frame


ENTRY_POLICY = "LIMITED_CHASE"
FEE_RATE = 0.0025
SLIPPAGE_RATE = 0.0010


def _load_price_frames(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        raw = load_daily_bars(symbol, base_dir=base_dir)
        frames[symbol] = prepare_condition_frame(raw)
    return frames


def _frame_index_at_or_before(frame: pd.DataFrame, timestamp: Any) -> int | None:
    if frame.empty or "timestamp" not in frame.columns or timestamp is None:
        return None
    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    matches = frame.index[frame["timestamp"] <= ts]
    if len(matches) == 0:
        return None
    return int(matches[-1])


def _safe_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _pct(value: float | None) -> float | None:
    return None if value is None else value * 100.0


def _classify_stop(mfe: float | None, mae: float | None, bars_to_stop: int | None) -> str:
    if mfe is None:
        return "UNKNOWN"
    if mfe > 0.03:
        return "GOOD_THEN_STOP"
    if mfe <= 0.005 and bars_to_stop is not None and bars_to_stop <= 3:
        return "FAKE_BREAKOUT"
    if mfe <= 0.01:
        return "BAD_IMMEDIATE_STOP"
    return "WEAK_THEN_STOP"


def _twenty_day_vol(frame: pd.DataFrame, idx: int) -> float | None:
    if "close" not in frame.columns or idx <= 0:
        return None
    start = max(0, idx - 20)
    returns = frame["close"].iloc[start : idx + 1].pct_change().dropna()
    if returns.empty:
        return None
    return float(returns.std())


def _trade_rows(results: list[FullTradeResult], frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in results:
        trade = item.trade
        meta = dict(item.metadata or {})
        symbol = trade.symbol
        frame = frames.get(symbol)
        if frame is None or frame.empty:
            continue

        entry_idx = _frame_index_at_or_before(frame, trade.entry_time)
        exit_idx = _frame_index_at_or_before(frame, trade.exit_time)
        signal_idx = meta.get("signal_bar_index")
        if not isinstance(signal_idx, int):
            signal_idx = _frame_index_at_or_before(frame, meta.get("signal_bar_time"))

        entry_ref = _safe_float(trade.entry_fill_price) or _safe_float(trade.entry_price)
        if entry_idx is None or exit_idx is None or entry_ref is None or exit_idx < entry_idx:
            mfe = None
            mae = None
            bars_to_stop = None
        else:
            trade_window = frame.iloc[entry_idx : exit_idx + 1]
            max_high = float(trade_window["high"].max())
            min_low = float(trade_window["low"].min())
            mfe = (max_high - entry_ref) / entry_ref
            mae = (min_low - entry_ref) / entry_ref
            bars_to_stop = int(exit_idx - entry_idx + 1)

        atr = _safe_float(frame.iloc[signal_idx]["atr14"]) if isinstance(signal_idx, int) and 0 <= signal_idx < len(frame) and "atr14" in frame.columns else None
        atr_pct = (atr / entry_ref) if atr is not None and entry_ref else None
        vol20 = _twenty_day_vol(frame, signal_idx) if isinstance(signal_idx, int) and signal_idx >= 0 else None

        rows.append(
            {
                "trade_id": trade.trade_id,
                "symbol": symbol,
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "entry_price": float(trade.entry_price),
                "entry_fill_price": float(trade.entry_fill_price or trade.entry_price),
                "exit_fill_price": float(trade.exit_fill_price or 0.0),
                "net_pnl": float(item.net_pnl),
                "gross_pnl": float(trade.actual_pnl or 0.0),
                "holding_seconds": float(trade.holding_time or 0.0),
                "bars_to_exit": bars_to_stop,
                "mfe_pct": _pct(mfe),
                "mae_pct": _pct(mae),
                "atr_pct": _pct(atr_pct),
                "vol20_pct": _pct(vol20),
                "regime": str(item.regime),
                "exit_rule": str(meta.get("exit_rule", "UNKNOWN")),
                "stop_hit_flag": bool(meta.get("stop_hit_flag") is True),
                "stop_price": _safe_float(meta.get("stop_price")),
                "classification": _classify_stop(mfe, mae, bars_to_stop) if meta.get("stop_hit_flag") is True else "NON_STOP",
            }
        )
    return pd.DataFrame(rows)


def _summary(all_trades: pd.DataFrame, stops: pd.DataFrame) -> dict[str, Any]:
    total = int(len(all_trades))
    stop_count = int(len(stops))
    loss_pct = ((stops["exit_fill_price"] - stops["entry_fill_price"]) / stops["entry_fill_price"]) * 100.0 if not stops.empty else pd.Series(dtype=float)
    return {
        "stop_trades": stop_count,
        "total_trades": total,
        "stop_trade_ratio_pct": float(stop_count / total * 100.0) if total else 0.0,
        "avg_stop_loss_pct": float(loss_pct.mean()) if not loss_pct.empty else 0.0,
        "avg_holding_days": float((stops["holding_seconds"] / 86400.0).mean()) if not stops.empty else 0.0,
        "max_stop_loss_pct": float(loss_pct.min()) if not loss_pct.empty else 0.0,
        "stop_net_pnl": float(stops["net_pnl"].sum()) if not stops.empty else 0.0,
        "total_net_pnl": float(all_trades["net_pnl"].sum()) if not all_trades.empty else 0.0,
    }


def _value_counts_pct(frame: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    if frame.empty or column not in frame.columns:
        return []
    counts = frame[column].value_counts(dropna=False)
    total = float(counts.sum())
    return [
        {"bucket": str(idx), "count": int(count), "ratio_pct": float(count / total * 100.0)}
        for idx, count in counts.items()
    ]


def _timing(stops: pd.DataFrame) -> dict[str, Any]:
    if stops.empty:
        return {}
    bars = pd.to_numeric(stops["bars_to_exit"], errors="coerce")
    return {
        "avg_bars_to_stop": float(bars.mean()),
        "median_bars_to_stop": float(bars.median()),
        "stop_within_1_3_bars_pct": float((bars <= 3).mean() * 100.0),
        "stop_after_5_bars_pct": float((bars >= 5).mean() * 100.0),
        "bucket_counts": {
            "1_3_bars": int((bars <= 3).sum()),
            "4_bars": int((bars == 4).sum()),
            "5_plus_bars": int((bars >= 5).sum()),
        },
    }


def _environment(stops: pd.DataFrame) -> dict[str, Any]:
    if stops.empty:
        return {}
    return {
        "avg_atr_pct": float(pd.to_numeric(stops["atr_pct"], errors="coerce").mean()),
        "avg_vol20_pct": float(pd.to_numeric(stops["vol20_pct"], errors="coerce").mean()),
        "regime": _group(stops, "regime", "net_pnl", ascending=True, limit=10),
        "regime_counts": _value_counts_pct(stops, "regime"),
        "classification_by_regime": _classification_by(stops, "regime"),
    }


def _symbol_analysis(all_trades: pd.DataFrame, stops: pd.DataFrame) -> dict[str, Any]:
    if all_trades.empty:
        return {"stop_loss_contribution": [], "stop_rate": []}
    stop_counts = stops.groupby("symbol").size().rename("stop_count") if not stops.empty else pd.Series(dtype=int)
    total_counts = all_trades.groupby("symbol").size().rename("trade_count")
    joined = pd.concat([total_counts, stop_counts], axis=1).fillna(0).reset_index()
    joined["stop_rate_pct"] = joined["stop_count"] / joined["trade_count"] * 100.0
    return {
        "stop_loss_contribution": _group(stops, "symbol", "net_pnl", ascending=True, limit=12),
        "stop_rate": joined.sort_values(["stop_rate_pct", "stop_count"], ascending=[False, False]).to_dict(orient="records"),
    }


def _drawdown_relation(all_trades: pd.DataFrame, stops: pd.DataFrame) -> dict[str, Any]:
    if all_trades.empty:
        return {}
    ordered = all_trades.sort_values("exit_time").copy()
    ordered["exit_time"] = pd.to_datetime(ordered["exit_time"], utc=True, errors="coerce")
    ordered["equity"] = ordered["net_pnl"].cumsum()
    ordered["peak"] = ordered["equity"].cummax()
    ordered["drawdown"] = ordered["peak"] - ordered["equity"]
    trough = ordered.loc[ordered["drawdown"].idxmax()]
    subset = ordered[ordered["exit_time"] <= trough["exit_time"]]
    peak_idx = subset["equity"].idxmax()
    peak_time = ordered.loc[peak_idx, "exit_time"]
    trough_time = trough["exit_time"]
    segment = ordered[(ordered["exit_time"] >= peak_time) & (ordered["exit_time"] <= trough_time)].copy()
    segment_stops = segment[segment["stop_hit_flag"] == True]
    return {
        "peak_time": str(peak_time),
        "trough_time": str(trough_time),
        "drawdown": float(trough["drawdown"]),
        "dd_trade_count": int(len(segment)),
        "dd_stop_count": int(len(segment_stops)),
        "dd_stop_ratio_pct": float(len(segment_stops) / len(segment) * 100.0) if len(segment) else 0.0,
        "dd_stop_net_pnl": float(segment_stops["net_pnl"].sum()) if not segment_stops.empty else 0.0,
        "dd_total_net_pnl": float(segment["net_pnl"].sum()) if not segment.empty else 0.0,
        "dd_stop_symbol_losses": _group(segment_stops, "symbol", "net_pnl", ascending=True, limit=8),
    }


def _classification_by(frame: pd.DataFrame, by: str) -> list[dict[str, Any]]:
    if frame.empty or by not in frame.columns:
        return []
    grouped = frame.groupby([by, "classification"], as_index=False).agg(count=("trade_id", "count"), net_pnl=("net_pnl", "sum"))
    return grouped.sort_values([by, "count"], ascending=[True, False]).to_dict(orient="records")


def _group(frame: pd.DataFrame, by: str, value: str, *, ascending: bool, limit: int) -> list[dict[str, Any]]:
    if frame.empty or by not in frame.columns or value not in frame.columns:
        return []
    grouped = frame.groupby(by, as_index=False)[value].sum().sort_values(value, ascending=ascending).head(limit)
    return grouped.to_dict(orient="records")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 067: STOP Loss Structure Analysis")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=args.initial_equity,
        fee_rate=FEE_RATE,
        slippage_rate=SLIPPAGE_RATE,
        entry_policy=ENTRY_POLICY,
    )
    frames = _load_price_frames(symbols, base_dir)
    all_trades = _trade_rows(results, frames)
    stops = all_trades[all_trades["stop_hit_flag"] == True].copy()

    report = {
        "setup": {
            "entry_policy": ENTRY_POLICY,
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "symbols": symbols,
            "execution_stats": {
                "total_signals": stats.total_signals,
                "fill_rate": stats.fill_rate,
                "expired_rate": stats.expired_rate,
                "big_miss": stats.big_miss_count,
            },
        },
        "stop_summary": _summary(all_trades, stops),
        "structure_analysis": {
            "classification": _value_counts_pct(stops, "classification"),
            "avg_mfe_pct": float(pd.to_numeric(stops["mfe_pct"], errors="coerce").mean()) if not stops.empty else 0.0,
            "avg_mae_pct": float(pd.to_numeric(stops["mae_pct"], errors="coerce").mean()) if not stops.empty else 0.0,
            "median_mfe_pct": float(pd.to_numeric(stops["mfe_pct"], errors="coerce").median()) if not stops.empty else 0.0,
            "median_mae_pct": float(pd.to_numeric(stops["mae_pct"], errors="coerce").median()) if not stops.empty else 0.0,
        },
        "timing_analysis": _timing(stops),
        "environment_analysis": _environment(stops),
        "symbol_analysis": _symbol_analysis(all_trades, stops),
        "dd_relation": _drawdown_relation(all_trades, stops),
    }
    out = json.dumps(report, ensure_ascii=True, indent=2, default=str)
    print(out)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
