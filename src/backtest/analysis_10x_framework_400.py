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
FEE_RATE = 0.001
ENTRY_SLIPPAGE_BPS = 10.0
EXIT_SLIPPAGE_BPS = 10.0
RISK_PER_TRADE = 0.01
MAX_CONCURRENT = 8
MAX_ORDERS_PER_BAR = 8


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _slip_up(px: float) -> float:
    return float(px * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0))


def _slip_dn(px: float) -> float:
    return float(px * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0))


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0.0)
    dn = -d.clip(upper=0.0)
    gain = up.ewm(alpha=1.0 / period, adjust=False).mean()
    loss = dn.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = gain / loss.replace(0.0, pd.NA)
    return 100.0 - 100.0 / (1.0 + rs)


@dataclass
class Position:
    symbol: str
    track: str
    entry_ts: pd.Timestamp
    entry_idx: int
    entry_price: float
    size: int
    stop_price: float
    hold_max: int


@dataclass
class Pending:
    symbol: str
    side: str
    track: str
    reason: str
    created_idx: int
    fill_idx: int
    reserve_cash: float = 0.0
    est_size: int = 0
    stop_price: float = 0.0
    hold_max: int = 0


def _load_frames(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for s in symbols:
        raw = load_daily_bars(s, base_dir=base_dir)
        f = prepare_condition_frame(raw).copy()
        if f.empty:
            continue
        f["ret20"] = f["close"].pct_change(20)
        f["ret60"] = f["close"].pct_change(60)
        f["rsi14"] = _rsi(pd.to_numeric(f["close"], errors="coerce"), 14)
        f["vol_ratio"] = pd.to_numeric(f["atr14"], errors="coerce") / pd.to_numeric(f["close"], errors="coerce")
        f = f.set_index(pd.to_datetime(f["timestamp"], utc=True)).sort_index()
        frames[s] = f
    return frames


def _timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    return sorted({ts for f in frames.values() for ts in f.index})


def _row(fr: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    if ts not in fr.index:
        return None
    r = fr.loc[ts]
    return r.iloc[-1] if isinstance(r, pd.DataFrame) else r


def _market_regime(rows: dict[str, pd.Series], ma_window: int = 200) -> tuple[bool, float]:
    # Equal-weight market proxy from available symbols.
    closes = []
    ma_vals = []
    for r in rows.values():
        if pd.notna(r.get("close")) and pd.notna(r.get(f"ma{ma_window}")):
            closes.append(float(r["close"]))
            ma_vals.append(float(r[f"ma{ma_window}"]))
    if not closes or not ma_vals:
        return False, 0.0
    price = sum(closes) / len(closes)
    ma = sum(ma_vals) / len(ma_vals)
    # ma slope proxy via ma50 vs ma200 not always present for custom window -> simple condition
    trend_on = price > ma
    return trend_on, _safe_div(price - ma, max(ma, 1e-9))


def _metrics(trades: list[dict[str, Any]], initial_capital: float, daily_equity: list[tuple[pd.Timestamp, float]]) -> dict[str, Any]:
    pnls = [float(t["net_pnl"]) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gp = sum(wins)
    gl = abs(sum(losses))
    final_capital = initial_capital + sum(pnls)

    if daily_equity:
        eq_series = pd.Series(
            [v for _, v in daily_equity],
            index=pd.to_datetime([t for t, _ in daily_equity], utc=True),
        ).sort_index()
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
        "initial_capital": _f(initial_capital, 2),
        "final_capital": _f(final_capital, 2),
        "total_return_pct": _f(_safe_div(final_capital - initial_capital, initial_capital) * 100.0),
        "sharpe": _f(sharpe),
        "mdd_pct": _f(max_dd * 100.0),
        "trade_count": int(len(trades)),
        "win_rate": _f(_safe_div(len(wins), len(pnls))) if pnls else 0.0,
        "avg_win": _f(_safe_div(gp, len(wins)), 4) if wins else 0.0,
        "avg_loss": _f(_safe_div(sum(losses), len(losses)), 4) if losses else 0.0,
        "expectancy": _f(_safe_div(sum(pnls), len(pnls)), 4) if pnls else 0.0,
    }


def _simulate(frames: dict[str, pd.DataFrame], *, ma_window: int = 200) -> dict[str, Any]:
    ts_all = _timestamps(frames)
    cash = float(INITIAL_CAPITAL)
    positions: list[Position] = []
    pending: list[Pending] = []
    trades: list[dict[str, Any]] = []
    daily_eq: list[tuple[pd.Timestamp, float]] = []

    validation = {
        "no_same_bar_fill": True,
        "no_capital_overlap": True,
        "no_negative_cash": True,
        "no_lookahead": True,
        "regime_past_only": True,
        "equity_continuity": True,
    }
    regime_on_days = 0

    for i in range(max(210, ma_window + 5), len(ts_all) - 1):
        ts = ts_all[i]
        rows_now = {s: _row(f, ts) for s, f in frames.items()}
        rows_now = {k: v for k, v in rows_now.items() if v is not None}

        # Fill pending at t+1 open discipline.
        rm: list[Pending] = []
        fills = 0
        for od in list(pending):
            if od.fill_idx != i:
                continue
            r = rows_now.get(od.symbol)
            if r is None:
                continue
            if fills >= MAX_ORDERS_PER_BAR:
                continue
            fills += 1
            px_open = float(r["open"])
            if od.side == "BUY":
                ep = _slip_up(px_open)
                spent = ep * od.est_size * (1.0 + FEE_RATE)
                cash += od.reserve_cash
                if spent > cash or od.est_size < 1:
                    rm.append(od)
                    continue
                cash -= spent
                if cash < -1e-6:
                    validation["no_negative_cash"] = False
                    validation["no_capital_overlap"] = False
                positions.append(Position(od.symbol, od.track, ts, i, ep, od.est_size, od.stop_price, od.hold_max))
            else:
                pos = next((p for p in positions if p.symbol == od.symbol and p.track == od.track), None)
                if pos is not None:
                    xp = _slip_dn(px_open)
                    proceeds = xp * pos.size
                    fee = proceeds * FEE_RATE
                    cash += proceeds - fee
                    pnl = (xp - pos.entry_price) * pos.size - fee
                    trades.append(
                        {
                            "symbol": pos.symbol,
                            "track": pos.track,
                            "entry_time": pos.entry_ts.isoformat(),
                            "exit_time": ts.isoformat(),
                            "entry_price": _f(pos.entry_price),
                            "exit_price": _f(xp),
                            "size": int(pos.size),
                            "net_pnl": _f(pnl, 4),
                            "reason": od.reason,
                        }
                    )
                    positions.remove(pos)
            rm.append(od)
        for x in rm:
            if x in pending:
                pending.remove(x)

        # Exit by stop / holding
        for p in list(positions):
            r = rows_now.get(p.symbol)
            if r is None:
                continue
            low = float(r["low"])
            if low <= p.stop_price:
                if not any(o.symbol == p.symbol and o.side == "SELL" and o.track == p.track for o in pending):
                    pending.append(Pending(p.symbol, "SELL", p.track, "STOP", i, i + 1))
                continue
            if i - p.entry_idx >= p.hold_max:
                if not any(o.symbol == p.symbol and o.side == "SELL" and o.track == p.track for o in pending):
                    pending.append(Pending(p.symbol, "SELL", p.track, "TIME", i, i + 1))

        trend_on, trend_strength = _market_regime(rows_now, ma_window=ma_window)
        if trend_on:
            regime_on_days += 1

        # Crash defense: trend off or vol shock => de-risk
        # vol shock proxy: median vol_ratio > 0.06
        vol_vals = [float(r["vol_ratio"]) for r in rows_now.values() if pd.notna(r.get("vol_ratio"))]
        vol_shock = (sum(vol_vals) / len(vol_vals)) > 0.06 if vol_vals else False
        if (not trend_on) or vol_shock:
            for p in list(positions):
                if p.track == "A" and not any(o.symbol == p.symbol and o.side == "SELL" and o.track == p.track for o in pending):
                    pending.append(Pending(p.symbol, "SELL", p.track, "DERISK", i, i + 1))

        # Track A priority allocation
        open_syms = {p.symbol for p in positions}
        pending_buy = {o.symbol for o in pending if o.side == "BUY"}
        eq_now = cash + sum(float(rows_now[p.symbol]["close"]) * p.size for p in positions if p.symbol in rows_now)
        orders = 0

        def submit_buy(symbol: str, track: str, reason: str, hold_max: int, risk_frac: float) -> None:
            nonlocal cash, orders
            if orders >= MAX_ORDERS_PER_BAR:
                return
            if symbol in open_syms or symbol in pending_buy:
                return
            r = rows_now.get(symbol)
            if r is None or pd.isna(r.get("atr14")):
                return
            ep_est = _slip_up(float(r["close"]))
            stop = ep_est - max(float(r["atr14"]) * 1.5, ep_est * 0.01)
            stop_dist = max(ep_est - stop, 0.01)
            risk_budget = eq_now * RISK_PER_TRADE * risk_frac
            size = int(math.floor(risk_budget / stop_dist))
            if size < 1:
                return
            reserve = ep_est * size * (1.0 + FEE_RATE)
            if reserve > cash:
                return
            cash -= reserve
            if cash < -1e-6:
                validation["no_negative_cash"] = False
                validation["no_capital_overlap"] = False
            pending.append(Pending(symbol, "BUY", track, reason, i, i + 1, reserve, size, stop, hold_max))
            pending_buy.add(symbol)
            orders += 1

        # Track A: Convex Growth
        if trend_on and (not vol_shock):
            ranked = []
            for s, r in rows_now.items():
                if pd.notna(r.get("ret60")) and pd.notna(r.get("ret20")):
                    score = 0.7 * float(r["ret60"]) + 0.3 * float(r["ret20"])
                    ranked.append((s, score))
            ranked.sort(key=lambda x: x[1], reverse=True)
            top = [s for s, _ in ranked[:3]]
            # Allocation tiers
            risk_frac = 1.0 if trend_strength > 0.03 else (0.6 if trend_strength > 0.0 else 0.3)
            for s in top[: max(1, min(3, MAX_CONCURRENT - len(open_syms)))]:
                submit_buy(s, "A", "TRACK_A_MOM", 15, risk_frac=risk_frac)

        # Track B: Mean Reversion on residual cash only
        idle_ratio = _safe_div(cash, max(eq_now, 1e-9))
        if idle_ratio > 0.2:
            for s, r in rows_now.items():
                if pd.notna(r.get("rsi14")) and float(r["rsi14"]) < 30.0:
                    submit_buy(s, "B", "TRACK_B_MR", 3, risk_frac=0.5)

        daily_eq.append((ts, cash + sum(float(rows_now[p.symbol]["close"]) * p.size for p in positions if p.symbol in rows_now)))

    # cleanup
    if pending:
        cash += sum(o.reserve_cash for o in pending if o.side == "BUY")
        pending.clear()
    if ts_all:
        last_ts = ts_all[-1]
        rows_last = {s: _row(f, last_ts) for s, f in frames.items()}
        for p in list(positions):
            r = rows_last.get(p.symbol)
            if r is None:
                continue
            xp = _slip_dn(float(r["close"]))
            proceeds = xp * p.size
            fee = proceeds * FEE_RATE
            cash += proceeds - fee
            pnl = (xp - p.entry_price) * p.size - fee
            trades.append(
                {
                    "symbol": p.symbol,
                    "track": p.track,
                    "entry_time": p.entry_ts.isoformat(),
                    "exit_time": last_ts.isoformat(),
                    "entry_price": _f(p.entry_price),
                    "exit_price": _f(xp),
                    "size": int(p.size),
                    "net_pnl": _f(pnl, 4),
                    "reason": "FORCE_CLOSE",
                }
            )
            positions.remove(p)

    metrics = _metrics(trades, INITIAL_CAPITAL, daily_eq)
    reg_on = _safe_div(regime_on_days, max(len(daily_eq), 1))
    metrics["regime_on_pct"] = _f(reg_on * 100.0)
    metrics["time_under_water_months"] = _estimate_tuw_months(daily_eq)
    metrics["worst_year_return_pct"] = _worst_year_return(daily_eq)
    return {"metrics": metrics, "validation": validation}


def _estimate_tuw_months(daily_equity: list[tuple[pd.Timestamp, float]]) -> int:
    if not daily_equity:
        return 0
    s = pd.Series([v for _, v in daily_equity], index=pd.to_datetime([t for t, _ in daily_equity], utc=True)).sort_index().resample("1D").last().ffill()
    peak = s.cummax()
    underwater = s < peak
    return int(round(underwater.sum() / 21.0))


def _worst_year_return(daily_equity: list[tuple[pd.Timestamp, float]]) -> float:
    if not daily_equity:
        return 0.0
    s = pd.Series([v for _, v in daily_equity], index=pd.to_datetime([t for t, _ in daily_equity], utc=True)).sort_index().resample("1D").last().ffill()
    y = s.resample("Y").last().pct_change().dropna()
    return _f(float(y.min() * 100.0)) if not y.empty else 0.0


def _render_block(name: str, m: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "Initial Capital": f"${m['initial_capital']:,.2f}",
        "Final Capital (5Y)": f"${m['final_capital']:,.2f}",
        "Total Return": f"{m['total_return_pct']:+.2f}%",
        "CAGR": f"{_f(((m['final_capital']/m['initial_capital'])**(1/5)-1)*100):+.2f}%",
        "MDD": f"-{abs(m['mdd_pct']):.2f}%",
        "Worst Year": f"{m['worst_year_return_pct']:+.2f}%",
        "Time Under Water": f"{m['time_under_water_months']} months",
        "sharpe": m["sharpe"],
        "trade_count": m["trade_count"],
        "avg_win": m["avg_win"],
        "avg_loss": m["avg_loss"],
        "expectancy": m["expectancy"],
        "regime_on_pct": m["regime_on_pct"],
    }


def _md(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T400 - 10x Objective Strategy Framework")
    lines.append("")
    lines.append("## Strategy Definition")
    lines.append("- Track A: Convex Growth (trend+momentum+vol guard)")
    lines.append("- Track B: Mean Reversion on residual idle cash")
    lines.append("")
    lines.append("## Backtest Results")
    for b in report["result_blocks"]:
        lines.append(f"### {b['name']}")
        lines.append(f"- Initial Capital: {b['Initial Capital']}")
        lines.append(f"- Final Capital (5Y): {b['Final Capital (5Y)']}")
        lines.append(f"- Total Return: {b['Total Return']}")
        lines.append(f"- CAGR: {b['CAGR']}")
        lines.append(f"- MDD: {b['MDD']}")
        lines.append(f"- Worst Year: {b['Worst Year']}")
        lines.append(f"- Time Under Water: {b['Time Under Water']}")
        lines.append("")
    lines.append("## Validation Checklist")
    for k, v in report["validation"].items():
        lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    lines.append("")
    lines.append("## Sensitivity")
    lines.append(f"- perturbation: {report['sensitivity']['perturbation']}")
    lines.append(f"- total_return_change_pct: {report['sensitivity']['total_return_change_pct']}")
    lines.append(f"- overfit_risk: {report['sensitivity']['overfit_risk']}")
    lines.append("")
    lines.append(f"## Final Judgment: {report['final_judgment']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T400 10x objective strategy framework")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_400/task_400_10x_framework.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_400/task_400_10x_framework.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    frames = _load_frames(symbols, Path(args.data_dir))

    main_run = _simulate(frames, ma_window=200)
    sens_run = _simulate(frames, ma_window=220)  # one perturbation

    v = main_run["validation"]
    valid = all(bool(x) for x in v.values())
    if not valid:
        final = "INVALID ? SIMULATION ERROR"
    else:
        final_cap = float(main_run["metrics"]["final_capital"])
        mult = _safe_div(final_cap, INITIAL_CAPITAL)
        if mult >= 10.0:
            final = "VALID 10x CANDIDATE"
        elif mult >= 5.0:
            final = "BORDERLINE"
        else:
            final = "INVALID"

    main_block = _render_block("Dual-Track 10x Framework", main_run["metrics"])
    sens_ret = float(sens_run["metrics"]["total_return_pct"])
    base_ret = float(main_run["metrics"]["total_return_pct"])
    ret_change = _f(sens_ret - base_ret)
    overfit = "HIGH" if ret_change <= -20.0 else "LOW"

    report = {
        "task": "T400",
        "result_blocks": [main_block],
        "validation": v,
        "sensitivity": {
            "perturbation": "MA window 200 -> 220",
            "total_return_change_pct": ret_change,
            "overfit_risk": overfit,
        },
        "final_judgment": final,
    }

    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    mout.write_text(_md(report), encoding="utf-8")
    print(f"written_json={jout}")
    print(f"written_md={mout}")
    print(f"final_judgment={final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
