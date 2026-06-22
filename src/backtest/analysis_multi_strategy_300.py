from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from strategy.conditions import prepare_condition_frame


INITIAL_CAPITAL = 100_000.0
RISK_PER_TRADE = 0.01
MAX_CONCURRENT_POSITIONS = 8
MAX_ORDERS_PER_BAR = 8
ENTRY_SLIPPAGE_BPS = 10.0
EXIT_SLIPPAGE_BPS = 10.0
FEE_RATE = 0.001


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _slip_up(px: float) -> float:
    return float(px * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0))


def _slip_dn(px: float) -> float:
    return float(px * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0))


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    gain = up.ewm(alpha=1.0 / period, adjust=False).mean()
    loss = down.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = gain / loss.replace(0.0, pd.NA)
    return 100.0 - (100.0 / (1.0 + rs))


@dataclass
class Position:
    symbol: str
    strategy: str
    entry_ts: pd.Timestamp
    entry_idx: int
    entry_price: float
    size: int
    stop_price: float
    entry_signal: str
    max_holding_days: int


@dataclass
class PendingOrder:
    symbol: str
    side: str  # BUY / SELL
    strategy: str
    created_idx: int
    fill_idx: int
    reason: str
    reserved_cash: float = 0.0
    est_size: int = 0
    stop_price: float = 0.0
    max_holding_days: int = 0


def _load_frames(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for s in symbols:
        raw = load_daily_bars(s, base_dir=base_dir)
        f = prepare_condition_frame(raw).copy()
        if f.empty:
            continue
        f["ret20"] = f["close"].pct_change(20)
        f["rsi14"] = _compute_rsi(pd.to_numeric(f["close"], errors="coerce"), period=14)
        f["avg_turnover20"] = pd.to_numeric(f["avg_turnover_20"], errors="coerce")
        f = f.set_index(pd.to_datetime(f["timestamp"], utc=True)).sort_index()
        frames[s] = f
    return frames


def _collect_timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    return sorted({ts for f in frames.values() for ts in f.index})


def _row_at(fr: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    if ts not in fr.index:
        return None
    r = fr.loc[ts]
    return r.iloc[-1] if isinstance(r, pd.DataFrame) else r


def _equity(cash: float, positions: list[Position], rows_now: dict[str, pd.Series]) -> float:
    mkt = 0.0
    for p in positions:
        row = rows_now.get(p.symbol)
        if row is None:
            continue
        mkt += float(row["close"]) * p.size
    return float(cash + mkt)


def _metrics(trades: list[dict[str, Any]], initial: float, daily_equity: list[tuple[pd.Timestamp, float]]) -> dict[str, Any]:
    pnls = [float(t["net_pnl"]) for t in trades]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    gp = sum(wins)
    gl = abs(sum(losses))
    final_cap = initial + sum(pnls)

    # MDD / Sharpe from daily equity
    if daily_equity:
        eq_series = pd.Series([v for _, v in daily_equity], index=pd.to_datetime([t for t, _ in daily_equity], utc=True)).sort_index()
        eq_daily = eq_series.resample("1D").last().ffill().dropna()
    else:
        eq_daily = pd.Series(dtype=float)
    peak = -1e18
    max_dd = 0.0
    for v in eq_daily.tolist():
        peak = max(peak, v)
        if peak > 0:
            max_dd = max(max_dd, (peak - v) / peak)
    rets = eq_daily.pct_change().dropna()
    sharpe = 0.0
    if len(rets) > 2 and float(rets.std(ddof=0)) > 0:
        sharpe = float((rets.mean() / rets.std(ddof=0)) * math.sqrt(252))

    return {
        "initial_capital": _f(initial, 2),
        "final_capital": _f(final_cap, 2),
        "total_return_pct": _f(_safe_div(final_cap - initial, initial) * 100.0),
        "sharpe": _f(sharpe),
        "mdd_pct": _f(max_dd * 100.0),
        "trade_count": int(len(trades)),
        "win_rate": _f(_safe_div(len(wins), len(pnls))) if pnls else 0.0,
        "avg_win": _f(_safe_div(gp, len(wins)), 4) if wins else 0.0,
        "avg_loss": _f(_safe_div(sum(losses), len(losses)), 4) if losses else 0.0,
        "expectancy": _f(_safe_div(sum(pnls), len(pnls)), 4) if pnls else 0.0,
    }


def _simulate(frames: dict[str, pd.DataFrame], mode: str) -> dict[str, Any]:
    ts_all = _collect_timestamps(frames)
    cash = float(INITIAL_CAPITAL)
    positions: list[Position] = []
    pending: list[PendingOrder] = []
    trades: list[dict[str, Any]] = []
    daily_equity: list[tuple[pd.Timestamp, float]] = []
    cooldown_until: dict[str, int] = {}

    for i in range(210, len(ts_all) - 1):
        ts = ts_all[i]
        rows_now: dict[str, pd.Series] = {}
        for s, fr in frames.items():
            row = _row_at(fr, ts)
            if row is not None:
                rows_now[s] = row

        # 1) execute pending
        filled_or_cancelled: list[PendingOrder] = []
        fills_this_bar = 0
        for od in list(pending):
            if od.fill_idx != i:
                continue
            row = rows_now.get(od.symbol)
            if row is None:
                continue
            if fills_this_bar >= MAX_ORDERS_PER_BAR:
                continue
            fills_this_bar += 1
            open_px = float(row["open"])
            if od.side == "BUY":
                entry_px = _slip_up(open_px)
                size = od.est_size
                spent = entry_px * size * (1.0 + FEE_RATE)
                cash += od.reserved_cash
                if spent > cash or size < 1:
                    filled_or_cancelled.append(od)
                    continue
                cash -= spent
                positions.append(
                    Position(
                        symbol=od.symbol,
                        strategy=od.strategy,
                        entry_ts=ts,
                        entry_idx=i,
                        entry_price=entry_px,
                        size=size,
                        stop_price=od.stop_price,
                        entry_signal=od.reason,
                        max_holding_days=od.max_holding_days,
                    )
                )
                filled_or_cancelled.append(od)
            else:
                # SELL close
                pos = next((p for p in positions if p.symbol == od.symbol and p.strategy == od.strategy), None)
                if pos is None:
                    filled_or_cancelled.append(od)
                    continue
                exit_px = _slip_dn(open_px)
                proceeds = exit_px * pos.size
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - pos.entry_price) * pos.size - fee
                trades.append(
                    {
                        "symbol": pos.symbol,
                        "strategy": pos.strategy,
                        "entry_time": pos.entry_ts.isoformat(),
                        "exit_time": ts.isoformat(),
                        "entry_price": _f(pos.entry_price),
                        "exit_price": _f(exit_px),
                        "size": int(pos.size),
                        "net_pnl": _f(pnl, 4),
                        "reason": od.reason,
                    }
                )
                positions.remove(pos)
                filled_or_cancelled.append(od)
        for od in filled_or_cancelled:
            if od in pending:
                pending.remove(od)

        # 2) stops/time exits -> schedule sell next bar
        for p in list(positions):
            row = rows_now.get(p.symbol)
            if row is None:
                continue
            low = float(row["low"])
            if low <= p.stop_price:
                if not any(o.symbol == p.symbol and o.side == "SELL" for o in pending):
                    pending.append(PendingOrder(p.symbol, "SELL", p.strategy, i, i + 1, "STOP"))
                cooldown_until[p.symbol] = i + 3
                continue
            if i - p.entry_idx >= p.max_holding_days:
                if not any(o.symbol == p.symbol and o.side == "SELL" for o in pending):
                    pending.append(PendingOrder(p.symbol, "SELL", p.strategy, i, i + 1, "TIME_EXIT"))

        # 3) generate new entries (no same-bar fill)
        # liquidity filter
        liquid = []
        for s, r in rows_now.items():
            turn = r.get("avg_turnover20")
            if pd.notna(turn):
                liquid.append((s, float(turn)))
        liquid = sorted(liquid, key=lambda x: x[1], reverse=True)[:10]
        liquid_symbols = {s for s, _ in liquid}

        open_symbols = {p.symbol for p in positions}
        pending_buy_symbols = {o.symbol for o in pending if o.side == "BUY"}
        equity_now = _equity(cash, positions, rows_now)
        free_slots = max(0, MAX_CONCURRENT_POSITIONS - len(open_symbols))
        orders_created = 0

        def try_buy(symbol: str, reason: str, max_hold: int) -> None:
            nonlocal cash, orders_created, free_slots
            if orders_created >= MAX_ORDERS_PER_BAR or free_slots <= 0:
                return
            if symbol in open_symbols or symbol in pending_buy_symbols:
                return
            if i <= cooldown_until.get(symbol, -1):
                return
            r = rows_now.get(symbol)
            if r is None or pd.isna(r.get("atr14")) or float(r["atr14"]) <= 0:
                return
            est_entry = _slip_up(float(r["close"]))
            stop = est_entry - max(float(r["atr14"]) * 1.5, est_entry * 0.01)
            stop_dist = max(est_entry - stop, 0.01)
            risk_budget = equity_now * RISK_PER_TRADE
            size = int(math.floor(risk_budget / stop_dist))
            if size < 1:
                return
            reserve = est_entry * size * (1.0 + FEE_RATE)
            if reserve > cash:
                return
            cash -= reserve
            pending.append(PendingOrder(symbol, "BUY", mode, i, i + 1, reason, reserve, size, stop, max_hold))
            pending_buy_symbols.add(symbol)
            orders_created += 1
            free_slots -= 1

        # Strategy rules
        if mode == "MOMENTUM":
            if i % 5 == 0:
                ranked = []
                for s in liquid_symbols:
                    rr = rows_now[s].get("ret20")
                    if pd.notna(rr):
                        ranked.append((s, float(rr)))
                ranked.sort(key=lambda x: x[1], reverse=True)
                top = [s for s, _ in ranked[:5]]
                # exit non-top momentum holdings
                for p in list(positions):
                    if p.strategy == "MOMENTUM" and p.symbol not in top and not any(o.symbol == p.symbol and o.side == "SELL" for o in pending):
                        pending.append(PendingOrder(p.symbol, "SELL", p.strategy, i, i + 1, "REBALANCE_EXIT"))
                for s in top:
                    try_buy(s, "MOMENTUM_TOP_RET20", 10)

        elif mode == "MEAN_REVERSION":
            for s in liquid_symbols:
                rsi = rows_now[s].get("rsi14")
                if pd.notna(rsi) and float(rsi) < 30.0:
                    try_buy(s, "RSI_OVERSOLD", 3)
            # exit signal
            for p in list(positions):
                if p.strategy != "MEAN_REVERSION":
                    continue
                rsi = rows_now.get(p.symbol, {}).get("rsi14") if isinstance(rows_now.get(p.symbol), dict) else rows_now[p.symbol].get("rsi14")
                if pd.notna(rsi) and float(rsi) > 50.0 and not any(o.symbol == p.symbol and o.side == "SELL" for o in pending):
                    pending.append(PendingOrder(p.symbol, "SELL", p.strategy, i, i + 1, "RSI_REVERT_EXIT"))

        else:  # REGIME_SWITCH
            # Trend regime -> momentum rebalance weekly
            if i % 5 == 0:
                trend_rank = []
                for s in liquid_symbols:
                    row = rows_now[s]
                    if pd.notna(row.get("ma50")) and float(row["close"]) > float(row["ma50"]) and pd.notna(row.get("ret20")):
                        trend_rank.append((s, float(row["ret20"])))
                trend_rank.sort(key=lambda x: x[1], reverse=True)
                top = [s for s, _ in trend_rank[:4]]
                for p in list(positions):
                    if p.strategy == "REGIME_SWITCH" and p.symbol not in top and not any(o.symbol == p.symbol and o.side == "SELL" for o in pending):
                        pending.append(PendingOrder(p.symbol, "SELL", p.strategy, i, i + 1, "REGIME_REBALANCE_EXIT"))
                for s in top:
                    try_buy(s, "REGIME_TREND_MOM", 10)
            # Range regime -> mean reversion entries
            for s in liquid_symbols:
                row = rows_now[s]
                rsi = row.get("rsi14")
                if pd.notna(row.get("ma50")) and float(row["close"]) <= float(row["ma50"]) and pd.notna(rsi) and float(rsi) < 30.0:
                    try_buy(s, "REGIME_RANGE_MR", 3)

        # Daily equity snapshot
        daily_equity.append((ts, _equity(cash, positions, rows_now)))

    # force liquidate
    if ts_all:
        last_ts = ts_all[-1]
        rows_last = {s: _row_at(fr, last_ts) for s, fr in frames.items()}
        for p in list(positions):
            row = rows_last.get(p.symbol)
            if row is None:
                continue
            exit_px = _slip_dn(float(row["close"]))
            proceeds = exit_px * p.size
            fee = proceeds * FEE_RATE
            cash += proceeds - fee
            pnl = (exit_px - p.entry_price) * p.size - fee
            trades.append(
                {
                    "symbol": p.symbol,
                    "strategy": p.strategy,
                    "entry_time": p.entry_ts.isoformat(),
                    "exit_time": last_ts.isoformat(),
                    "entry_price": _f(p.entry_price),
                    "exit_price": _f(exit_px),
                    "size": int(p.size),
                    "net_pnl": _f(pnl, 4),
                    "reason": "FORCE_CLOSE",
                }
            )
            positions.remove(p)
        if pending:
            # release remaining reservations
            cash += sum(o.reserved_cash for o in pending if o.side == "BUY")
            pending.clear()

    return {"summary": _metrics(trades, INITIAL_CAPITAL, daily_equity), "trades": trades}


def _report_block(name: str, s: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": name,
        "initial_capital": s["initial_capital"],
        "final_capital": s["final_capital"],
        "total_return_pct": s["total_return_pct"],
        "sharpe": s["sharpe"],
        "mdd_pct": s["mdd_pct"],
        "trade_count": s["trade_count"],
        "win_rate": s["win_rate"],
        "avg_win": s["avg_win"],
        "avg_loss": s["avg_loss"],
        "expectancy": s["expectancy"],
    }


def _markdown(out: dict[str, Any]) -> str:
    lines = ["# Task T300 - Multi-Strategy Backtest", ""]
    for x in out["results"]:
        lines.append(f"## {x['strategy']}")
        lines.append(f"- Initial Capital: ${x['initial_capital']:,.2f}")
        lines.append(f"- Final Capital (5Y): ${x['final_capital']:,.2f}")
        lines.append(f"- Total Return: {x['total_return_pct']:+.2f}%")
        lines.append(f"- Sharpe: {x['sharpe']}")
        lines.append(f"- MDD: {x['mdd_pct']}%")
        lines.append("")
    lines.append("## Comparison")
    lines.append("| Strategy | Initial | Final | Return | Sharpe | MDD |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for x in out["results"]:
        lines.append(
            f"| {x['strategy']} | ${x['initial_capital']:,.2f} | ${x['final_capital']:,.2f} | {x['total_return_pct']:+.2f}% | {x['sharpe']:.4f} | {x['mdd_pct']:.2f}% |"
        )
    lines.append("")
    lines.append("## Final Analysis")
    lines.append(f"- Which strategy actually makes money? {out['analysis']['money_maker']}")
    lines.append(f"- Best risk-adjusted return? {out['analysis']['best_risk_adjusted']}")
    lines.append(f"- Most scalable for automation? {out['analysis']['most_scalable']}")
    lines.append(f"- Develop further: {out['analysis']['develop_further']}")
    if out["analysis"]["no_meaningful_edge"]:
        lines.append('- NO STRATEGY HAS MEANINGFUL EDGE')
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T300 multi-strategy backtest under realistic constraints")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_300/task_300_multi_strategy.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_300/task_300_multi_strategy.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    frames = _load_frames(symbols, Path(args.data_dir))

    mom = _simulate(frames, "MOMENTUM")["summary"]
    mr = _simulate(frames, "MEAN_REVERSION")["summary"]
    rs = _simulate(frames, "REGIME_SWITCH")["summary"]

    results = [
        _report_block("Cross-sectional Momentum", mom),
        _report_block("Short-term Mean Reversion", mr),
        _report_block("Regime Switch", rs),
    ]

    profitable = [r for r in results if r["final_capital"] > r["initial_capital"]]
    best_sharpe = max(results, key=lambda r: float(r["sharpe"]))
    best_return = max(results, key=lambda r: float(r["total_return_pct"]))
    no_edge = all((float(r["sharpe"]) < 0.7 or float(r["total_return_pct"]) < 5.0) for r in results)

    analysis = {
        "money_maker": best_return["strategy"] if profitable else "None",
        "best_risk_adjusted": best_sharpe["strategy"],
        "most_scalable": "Cross-sectional Momentum",
        "develop_further": best_sharpe["strategy"],
        "no_meaningful_edge": bool(no_edge),
    }

    out = {"task": "T300", "results": results, "analysis": analysis}

    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    mout.write_text(_markdown(out), encoding="utf-8")
    print(f"written_json={jout}")
    print(f"written_md={mout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

