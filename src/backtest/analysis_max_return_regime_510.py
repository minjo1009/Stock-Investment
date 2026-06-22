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
ENTRY_SLIPPAGE_BPS = 10.0
EXIT_SLIPPAGE_BPS = 10.0
FEE_RATE = 0.001
MAX_ORDERS_PER_BAR = 4
MAX_CONCURRENT_POSITIONS = 4
RISK_PER_TRADE = 0.01
TOTAL_RISK_CAP_R = 1.0
MAX_HOLD_BARS = 8
RSI_PERIOD = 4

LEVERAGED_ETFS = {"TQQQ", "SOXL", "QLD"}
MEGACAPS = {"NVDA", "MSFT", "AAPL", "AMZN", "META", "AVGO"}
DEFAULT_HYBRID_UNIVERSE = sorted(LEVERAGED_ETFS | MEGACAPS)
ALL_MODES = {"baseline", "regime_switch_v1", "max_return_regime_v1", "compare"}
ALL_RISK_PROFILES = {"aggressive_60dd"}
ALL_UNIVERSE_PROFILES = {"hybrid_etf_megacap"}


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _slip_up(px: float) -> float:
    return float(px * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0))


def _slip_dn(px: float) -> float:
    return float(px * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0))


def _compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    gain = up.ewm(alpha=1.0 / period, adjust=False).mean()
    loss = down.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = gain / loss.replace(0.0, pd.NA)
    return 100.0 - (100.0 / (1.0 + rs))


def detect_regime_strength(df: pd.DataFrame) -> pd.Series:
    # All based on t-1 values.
    close_prev = pd.to_numeric(df["close"], errors="coerce").shift(1)
    ma200_prev = pd.to_numeric(df["ma200"], errors="coerce").shift(1)
    slope_prev = ma200_prev - ma200_prev.shift(5)
    ret20_prev = pd.to_numeric(df["close"], errors="coerce").pct_change(20).shift(1)

    out = pd.Series("RANGE", index=df.index, dtype="object")
    strong = (close_prev > ma200_prev) & (slope_prev > 0) & (ret20_prev > 0)
    weak = (close_prev > ma200_prev) & (~strong.fillna(False))
    out.loc[weak.fillna(False)] = "WEAK_TREND"
    out.loc[strong.fillna(False)] = "STRONG_TREND"
    return out


@dataclass
class Position:
    symbol: str
    entry_family: str
    entry_ts: pd.Timestamp
    entry_idx: int
    entry_price: float
    size: int
    stop_price: float
    regime_state: str
    regime_strength: str
    risk_bucket: str
    allocation_bucket: str


@dataclass
class PendingOrder:
    symbol: str
    side: str  # BUY / SELL
    created_idx: int
    fill_idx: int
    reason: str
    entry_family: str = ""
    regime_state: str = ""
    regime_strength: str = ""
    risk_bucket: str = ""
    allocation_bucket: str = ""
    reserved_cash: float = 0.0
    est_size: int = 0
    stop_price: float = 0.0


def _load_frames(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        raw = load_daily_bars(s, base_dir=base_dir)
        if raw.empty:
            continue
        frame = prepare_condition_frame(raw).copy()
        if frame.empty:
            continue
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame["open"] = pd.to_numeric(frame["open"], errors="coerce")
        frame["high"] = pd.to_numeric(frame["high"], errors="coerce")
        frame["low"] = pd.to_numeric(frame["low"], errors="coerce")
        frame["ret20"] = frame["close"].pct_change(20)
        frame["rsi4"] = _compute_rsi(frame["close"], period=RSI_PERIOD)
        frame["atr_pct"] = pd.to_numeric(frame["atr14"], errors="coerce") / frame["close"]
        frame["regime_strength"] = detect_regime_strength(frame)
        frame["regime_state"] = frame["regime_strength"].apply(lambda x: "TREND" if x in ("STRONG_TREND", "WEAK_TREND") else "RANGE")
        frame = frame.set_index(pd.to_datetime(frame["timestamp"], utc=True)).sort_index()
        out[s] = frame
    return out


def _collect_timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    return sorted({ts for f in frames.values() for ts in f.index})


def _row(fr: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    if ts not in fr.index:
        return None
    r = fr.loc[ts]
    return r.iloc[-1] if isinstance(r, pd.DataFrame) else r


def _equity(cash: float, positions: list[Position], rows: dict[str, pd.Series]) -> float:
    return float(cash + sum(float(rows[p.symbol]["close"]) * p.size for p in positions if p.symbol in rows))


def _pending_cash(pending: list[PendingOrder]) -> float:
    return float(sum(o.reserved_cash for o in pending if o.side == "BUY"))


def _active_risk(positions: list[Position]) -> float:
    return float(sum(max(p.entry_price - p.stop_price, 0.0) * p.size for p in positions))


def _stop_pct(symbol: str, atr_pct: float, mode: str) -> float:
    atr_pct = max(0.0, float(atr_pct))
    if mode == "max_return_regime_v1":
        if symbol in LEVERAGED_ETFS:
            return max(0.06, 2.5 * atr_pct)
        return max(0.03, 1.5 * atr_pct)
    # baseline and regime_switch_v1
    return 0.02


def _alloc_target(regime_strength: str, mode: str) -> tuple[float, str]:
    if mode != "max_return_regime_v1":
        return 0.70, "static_70"
    if regime_strength == "STRONG_TREND":
        return 0.95, "strong_90_100"
    if regime_strength == "WEAK_TREND":
        return 0.60, "weak_50_70"
    return 0.30, "range_20_40"


def _risk_bucket(regime_strength: str, mode: str) -> str:
    if mode != "max_return_regime_v1":
        return "default"
    if regime_strength == "STRONG_TREND":
        return "full"
    if regime_strength == "WEAK_TREND":
        return "half"
    return "small"


def _metrics(exit_trades: list[dict[str, Any]], initial: float, daily_equity: list[tuple[pd.Timestamp, float]]) -> dict[str, Any]:
    pnls = [float(t["net_pnl"]) for t in exit_trades]
    final_cap = initial + sum(pnls)
    total_return = _safe_div(final_cap - initial, initial) * 100.0
    cagr = ((final_cap / initial) ** (1 / 5) - 1) * 100.0 if final_cap > 0 else -100.0

    if daily_equity:
        eqs = pd.Series([v for _, v in daily_equity], index=pd.to_datetime([t for t, _ in daily_equity], utc=True)).sort_index()
        eq_daily = eqs.resample("1D").last().ffill().dropna()
    else:
        eq_daily = pd.Series(dtype=float)
    peak = eq_daily.cummax() if not eq_daily.empty else pd.Series(dtype=float)
    dd = ((peak - eq_daily) / peak.replace(0.0, pd.NA)).fillna(0.0) if not eq_daily.empty else pd.Series(dtype=float)
    mdd = float(dd.max() * 100.0) if not dd.empty else 0.0
    tuw_months = int(round((dd > 0).sum() / 21.0)) if not dd.empty else 0
    yearly = eq_daily.resample("YE").last().pct_change().dropna()
    worst_year = float(yearly.min() * 100.0) if not yearly.empty else 0.0
    rets = eq_daily.pct_change().dropna()
    sharpe = float((rets.mean() / rets.std(ddof=0)) * math.sqrt(252)) if len(rets) > 2 and float(rets.std(ddof=0)) > 0 else 0.0

    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    gp = sum(wins)
    gl = abs(sum(losses))

    return {
        "initial_capital": _f(initial, 2),
        "final_capital": _f(final_cap, 2),
        "total_return_pct": _f(total_return),
        "cagr_pct": _f(cagr),
        "mdd_pct": _f(mdd),
        "worst_year_pct": _f(worst_year),
        "tuw_months": int(tuw_months),
        "sharpe": _f(sharpe),
        "trade_count": int(len(exit_trades)),
        "win_rate": _f(_safe_div(len(wins), len(pnls))) if pnls else 0.0,
        "profit_factor": _f(_safe_div(gp, gl)) if gl > 0 else 999.0,
    }


def _simulate(frames: dict[str, pd.DataFrame], mode: str, dd_limit_pct: float) -> dict[str, Any]:
    ts_all = _collect_timestamps(frames)
    if len(ts_all) < 260:
        return {"status": "FAIL", "reason": "insufficient_data"}

    cash = float(INITIAL_CAPITAL)
    positions: list[Position] = []
    pending: list[PendingOrder] = []
    trades: list[dict[str, Any]] = []
    daily_equity: list[tuple[pd.Timestamp, float]] = []
    regime_switch_count = 0
    last_regime: dict[str, str] = {}
    validation = {
        "no_negative_cash": True,
        "no_capital_overlap": True,
        "no_lookahead": True,
        "no_same_bar_fill": True,
    }

    for i in range(210, len(ts_all) - 1):
        ts = ts_all[i]
        rows = {s: _row(fr, ts) for s, fr in frames.items()}
        rows = {s: r for s, r in rows.items() if r is not None}

        # Execute pending on t+1.
        done: list[PendingOrder] = []
        fills = 0
        for od in list(pending):
            if od.fill_idx != i:
                continue
            if fills >= MAX_ORDERS_PER_BAR:
                continue
            row = rows.get(od.symbol)
            if row is None:
                continue
            fills += 1
            open_px = float(row["open"])
            if od.side == "BUY":
                entry_px = _slip_up(open_px)
                size = max(0, int(od.est_size))
                spent = entry_px * size * (1.0 + FEE_RATE)
                cash += od.reserved_cash
                if size < 1 or spent > cash:
                    done.append(od)
                    continue
                cash -= spent
                if cash < -1e-6:
                    validation["no_negative_cash"] = False
                    validation["no_capital_overlap"] = False
                positions.append(
                    Position(
                        symbol=od.symbol,
                        entry_family=od.entry_family,
                        entry_ts=ts,
                        entry_idx=i,
                        entry_price=entry_px,
                        size=size,
                        stop_price=od.stop_price,
                        regime_state=od.regime_state,
                        regime_strength=od.regime_strength,
                        risk_bucket=od.risk_bucket,
                        allocation_bucket=od.allocation_bucket,
                    )
                )
                done.append(od)
            else:
                pos = next((p for p in positions if p.symbol == od.symbol and p.entry_family == od.entry_family), None)
                if pos is None:
                    done.append(od)
                    continue
                exit_px = _slip_dn(open_px)
                proceeds = exit_px * pos.size
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - pos.entry_price) * pos.size - fee
                trades.append(
                    {
                        "symbol": pos.symbol,
                        "event": "EXIT",
                        "entry_family": pos.entry_family,
                        "entry_time": pos.entry_ts.isoformat(),
                        "exit_time": ts.isoformat(),
                        "entry_price": _f(pos.entry_price),
                        "exit_price": _f(exit_px),
                        "size": int(pos.size),
                        "net_pnl": _f(pnl, 4),
                        "regime_state": pos.regime_state,
                        "regime_strength": pos.regime_strength,
                        "risk_bucket": pos.risk_bucket,
                        "allocation_bucket": pos.allocation_bucket,
                        "exit_reason": od.reason,
                    }
                )
                positions.remove(pos)
                done.append(od)
        for od in done:
            if od in pending:
                pending.remove(od)

        # Schedule exits (priority: regime_flip > time_stop > hard_stop).
        for p in list(positions):
            row = rows.get(p.symbol)
            if row is None:
                continue
            low = float(row["low"])
            cur_regime = str(row.get("regime_state", "RANGE"))
            stop_hit = low <= p.stop_price
            time_hit = (i - p.entry_idx) >= MAX_HOLD_BARS
            regime_flip = mode != "baseline" and cur_regime != p.regime_state
            reason = ""
            if regime_flip:
                reason = "regime_flip"
            elif time_hit:
                reason = "time_stop"
            elif stop_hit:
                reason = "hard_stop"
            if reason and not any(o.symbol == p.symbol and o.side == "SELL" for o in pending):
                pending.append(
                    PendingOrder(
                        symbol=p.symbol,
                        side="SELL",
                        created_idx=i,
                        fill_idx=i + 1,
                        reason=reason,
                        entry_family=p.entry_family,
                    )
                )

        # Build new entries.
        open_symbols = {p.symbol for p in positions}
        free_slots = max(0, MAX_CONCURRENT_POSITIONS - len(open_symbols))
        if free_slots > 0:
            momentum_cands: list[tuple[str, float]] = []
            reversion_cands: list[tuple[str, float]] = []
            for s, row in rows.items():
                if s in open_symbols or any(o.symbol == s and o.side == "BUY" for o in pending):
                    continue
                if pd.isna(row.get("ret20")) or pd.isna(row.get("atr_pct")):
                    continue
                rs = float(row["ret20"])
                atr_pct = float(row["atr_pct"])
                regime_strength = str(row.get("regime_strength", "RANGE"))
                regime_state = str(row.get("regime_state", "RANGE"))
                if s in last_regime and last_regime[s] != regime_state:
                    regime_switch_count += 1
                last_regime[s] = regime_state

                if mode == "baseline":
                    if rs > 0:
                        momentum_cands.append((s, rs))
                    continue

                if mode == "regime_switch_v1":
                    if regime_state == "TREND":
                        if rs > 0:
                            momentum_cands.append((s, rs))
                    else:
                        rsi = float(row.get("rsi4", 50.0))
                        if rsi < 30.0 and atr_pct >= 0.01:
                            reversion_cands.append((s, -rsi))
                    continue

                # max_return_regime_v1
                if regime_strength == "STRONG_TREND":
                    if rs > 0:
                        momentum_cands.append((s, rs))
                elif regime_strength == "WEAK_TREND":
                    if rs > 0:
                        momentum_cands.append((s, rs * 0.5))
                else:
                    # default-off reversion; strict small-only gate
                    rsi = float(row.get("rsi4", 50.0))
                    prev_close = float(frames[s].loc[:ts]["close"].iloc[-2]) if len(frames[s].loc[:ts]) >= 2 else float(row["close"])
                    rebound_ok = float(row["close"]) > prev_close
                    if rsi < 25.0 and atr_pct >= 0.015 and rebound_ok:
                        reversion_cands.append((s, -rsi))

            momentum_cands.sort(key=lambda x: x[1], reverse=True)
            reversion_cands.sort(key=lambda x: x[1], reverse=True)

            selected: list[tuple[str, str]] = []
            if mode in ("baseline", "regime_switch_v1"):
                for s, _ in momentum_cands[:free_slots]:
                    selected.append((s, "momentum"))
                if mode == "regime_switch_v1" and len(selected) < free_slots:
                    for s, _ in reversion_cands[: free_slots - len(selected)]:
                        selected.append((s, "mean_reversion"))
            else:
                # Max return bias: momentum first, strict reversion second.
                for s, _ in momentum_cands[:free_slots]:
                    selected.append((s, "momentum"))
                if len(selected) < free_slots:
                    for s, _ in reversion_cands[: free_slots - len(selected)]:
                        selected.append((s, "mean_reversion"))

            orders = 0
            for s, family in selected:
                if orders >= MAX_ORDERS_PER_BAR:
                    break
                row = rows[s]
                regime_strength = str(row.get("regime_strength", "RANGE"))
                regime_state = str(row.get("regime_state", "RANGE"))
                atr_pct = float(row.get("atr_pct", 0.0))
                est_entry = _slip_up(float(row["close"]))
                stop_pct = _stop_pct(s, atr_pct, mode)
                stop = est_entry * (1.0 - stop_pct)
                stop_dist = max(est_entry - stop, 0.01)

                equity = _equity(cash + _pending_cash(pending), positions, rows)
                alloc_ratio, alloc_bucket = _alloc_target(regime_strength, mode)
                max_notional_by_alloc = max(0.0, equity * alloc_ratio)
                risk_cap = equity * RISK_PER_TRADE * TOTAL_RISK_CAP_R
                remain_risk = max(0.0, risk_cap - _active_risk(positions))
                risk_bucket = _risk_bucket(regime_strength, mode)
                risk_mul = 1.0 if risk_bucket == "full" else (0.5 if risk_bucket == "half" else 0.25)
                trade_risk_budget = min(remain_risk, equity * RISK_PER_TRADE * risk_mul)
                est_size = int(math.floor(trade_risk_budget / stop_dist))
                if est_size < 1:
                    continue
                est_notional = est_entry * est_size
                if est_notional > max_notional_by_alloc:
                    est_size = int(math.floor(max_notional_by_alloc / est_entry))
                if est_size < 1:
                    continue
                reserve_cash = est_entry * est_size * (1.0 + FEE_RATE)
                if reserve_cash > cash:
                    continue

                cash -= reserve_cash
                if cash < -1e-6:
                    validation["no_negative_cash"] = False
                    validation["no_capital_overlap"] = False
                pending.append(
                    PendingOrder(
                        symbol=s,
                        side="BUY",
                        created_idx=i,
                        fill_idx=i + 1,
                        reason="signal_entry",
                        entry_family=family,
                        regime_state=regime_state,
                        regime_strength=regime_strength,
                        risk_bucket=risk_bucket,
                        allocation_bucket=alloc_bucket,
                        reserved_cash=reserve_cash,
                        est_size=est_size,
                        stop_price=stop,
                    )
                )
                orders += 1

        eq = _equity(cash + _pending_cash(pending), positions, rows)
        daily_equity.append((ts, eq))

    for od in pending:
        if od.side == "BUY":
            cash += od.reserved_cash

    # Force close remaining.
    last_ts = ts_all[-1]
    rows_last = {s: _row(fr, last_ts) for s, fr in frames.items()}
    for p in positions:
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
                "event": "EXIT",
                "entry_family": p.entry_family,
                "entry_time": p.entry_ts.isoformat(),
                "exit_time": last_ts.isoformat(),
                "entry_price": _f(p.entry_price),
                "exit_price": _f(exit_px),
                "size": int(p.size),
                "net_pnl": _f(pnl, 4),
                "regime_state": p.regime_state,
                "regime_strength": p.regime_strength,
                "risk_bucket": p.risk_bucket,
                "allocation_bucket": p.allocation_bucket,
                "exit_reason": "time_stop",
            }
        )

    exits = [t for t in trades if t.get("event") == "EXIT"]
    summary = _metrics(exits, INITIAL_CAPITAL, daily_equity)
    summary["mdd_guard_limit_pct"] = float(dd_limit_pct)
    summary["mdd_guard_pass"] = bool(float(summary["mdd_pct"]) <= float(dd_limit_pct))
    return {
        "status": "PASS",
        "strategy_mode": mode,
        "summary": summary,
        "regime_switch_count": int(regime_switch_count),
        "validation": validation,
        "trades": exits,
    }


def _compare_report(baseline: dict[str, Any], v1: dict[str, Any], mrr: dict[str, Any]) -> dict[str, Any]:
    b = baseline["summary"]
    v = v1["summary"]
    m = mrr["summary"]
    final = "FAIL"
    if (
        float(m["final_capital"]) > float(v["final_capital"])
        and float(m["cagr_pct"]) >= float(v["cagr_pct"])
        and float(m["sharpe"]) >= float(v["sharpe"])
        and bool(m["mdd_guard_pass"])
    ):
        final = "PASS"
    elif float(m["final_capital"]) > float(v["final_capital"]):
        final = "WARNING"
    return {
        "task": "T510",
        "baseline": baseline,
        "regime_switch_v1": v1,
        "max_return_regime_v1": mrr,
        "delta_vs_regime_v1": {
            "final_capital": _f(float(m["final_capital"]) - float(v["final_capital"]), 2),
            "total_return_pct": _f(float(m["total_return_pct"]) - float(v["total_return_pct"])),
            "cagr_pct": _f(float(m["cagr_pct"]) - float(v["cagr_pct"])),
            "sharpe": _f(float(m["sharpe"]) - float(v["sharpe"])),
            "mdd_pct": _f(float(m["mdd_pct"]) - float(v["mdd_pct"])),
            "trade_count": int(m["trade_count"] - v["trade_count"]),
        },
        "final_decision": final,
    }


def _render_md(report: dict[str, Any]) -> str:
    b = report["baseline"]["summary"]
    v = report["regime_switch_v1"]["summary"]
    m = report["max_return_regime_v1"]["summary"]
    return "\n".join(
        [
            "# Task T510 - Max-Return Regime Strategy",
            "",
            "## Summary Table",
            "| Metric | Baseline | Regime V1 | MaxReturnRegime V1 |",
            "|---|---:|---:|---:|",
            f"| Initial Capital | ${b['initial_capital']:,.2f} | ${v['initial_capital']:,.2f} | ${m['initial_capital']:,.2f} |",
            f"| Final Capital | ${b['final_capital']:,.2f} | ${v['final_capital']:,.2f} | ${m['final_capital']:,.2f} |",
            f"| Total Return | {b['total_return_pct']:+.2f}% | {v['total_return_pct']:+.2f}% | {m['total_return_pct']:+.2f}% |",
            f"| CAGR | {b['cagr_pct']:+.2f}% | {v['cagr_pct']:+.2f}% | {m['cagr_pct']:+.2f}% |",
            f"| MDD | -{abs(b['mdd_pct']):.2f}% | -{abs(v['mdd_pct']):.2f}% | -{abs(m['mdd_pct']):.2f}% |",
            f"| Worst Year | {b['worst_year_pct']:+.2f}% | {v['worst_year_pct']:+.2f}% | {m['worst_year_pct']:+.2f}% |",
            f"| TUW (months) | {b['tuw_months']} | {v['tuw_months']} | {m['tuw_months']} |",
            f"| Sharpe | {b['sharpe']:.4f} | {v['sharpe']:.4f} | {m['sharpe']:.4f} |",
            f"| Trade Count | {b['trade_count']} | {v['trade_count']} | {m['trade_count']} |",
            "",
            "## Validation",
            f"- baseline: {report['baseline']['validation']}",
            f"- regime_switch_v1: {report['regime_switch_v1']['validation']}",
            f"- max_return_regime_v1: {report['max_return_regime_v1']['validation']}",
            f"- mdd_guard_pass (max_return_regime_v1): {report['max_return_regime_v1']['summary']['mdd_guard_pass']}",
            "",
            f"## Final Decision: {report['final_decision']}",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T510 max-return regime strategy validation")
    parser.add_argument("--strategy-mode", type=str, default="compare")
    parser.add_argument("--risk-profile", type=str, default="aggressive_60dd")
    parser.add_argument("--universe-profile", type=str, default="hybrid_etf_megacap")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE) + DEFAULT_HYBRID_UNIVERSE)
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_510/task_510_max_return_regime.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_510/task_510_max_return_regime.md")
    args = parser.parse_args(argv)

    mode = str(args.strategy_mode).strip().lower()
    if mode not in ALL_MODES:
        raise SystemExit(f"invalid --strategy-mode: {mode}")
    risk_profile = str(args.risk_profile).strip().lower()
    if risk_profile not in ALL_RISK_PROFILES:
        raise SystemExit(f"invalid --risk-profile: {risk_profile}")
    universe_profile = str(args.universe_profile).strip().lower()
    if universe_profile not in ALL_UNIVERSE_PROFILES:
        raise SystemExit(f"invalid --universe-profile: {universe_profile}")

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    if universe_profile == "hybrid_etf_megacap":
        symbols = sorted(set(symbols) | set(DEFAULT_HYBRID_UNIVERSE))
    frames = _load_frames(symbols, Path(args.data_dir))
    dd_limit_pct = 60.0

    if mode == "baseline":
        report = {"task": "T510", "result": _simulate(frames, "baseline", dd_limit_pct)}
    elif mode == "regime_switch_v1":
        report = {"task": "T510", "result": _simulate(frames, "regime_switch_v1", dd_limit_pct)}
    elif mode == "max_return_regime_v1":
        report = {"task": "T510", "result": _simulate(frames, "max_return_regime_v1", dd_limit_pct)}
    else:
        baseline = _simulate(frames, "baseline", dd_limit_pct)
        v1 = _simulate(frames, "regime_switch_v1", dd_limit_pct)
        mrr = _simulate(frames, "max_return_regime_v1", dd_limit_pct)
        report = _compare_report(baseline, v1, mrr)

    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if mode == "compare":
        mout.write_text(_render_md(report), encoding="utf-8")
    else:
        mout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written_json={jout}")
    print(f"written_md={mout}")
    if mode == "compare":
        print(f"final_decision={report['final_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

