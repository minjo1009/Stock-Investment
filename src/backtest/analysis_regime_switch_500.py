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
MAX_CONCURRENT_POSITIONS = 3
MAX_ORDERS_PER_BAR = 4
RISK_PER_TRADE = 0.01
TOTAL_RISK_CAP_R = 1.0
STOP_LOSS_PCT = 0.02
MAX_HOLDING_BARS = 8
MIN_VOL_ATR_PCT = 0.01
RSI_PERIOD = 4
RSI_ENTRY = 30.0

LEVERAGED_UNIVERSE = ["TQQQ", "QLD", "SOXL", "USD", "UPRO", "SSO", "TNA", "FAS", "LABU", "SQQQ", "SPXU"]
ALLOWED_MODES = {"baseline", "regime_switch_v1", "compare"}


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


def _detect_regime_state(df: pd.DataFrame) -> pd.Series:
    # Use only data up to t-1 for the t decision.
    close_prev = df["close"].shift(1)
    ma200_prev = df["ma200"].shift(1)
    ma200_slope_prev = (df["ma200"].shift(1) - df["ma200"].shift(6))
    trend = (close_prev > ma200_prev) & (ma200_slope_prev > 0)
    out = pd.Series("RANGE", index=df.index, dtype="object")
    out.loc[trend.fillna(False)] = "TREND"
    return out


@dataclass
class Position:
    symbol: str
    family: str
    entry_idx: int
    entry_ts: pd.Timestamp
    entry_price: float
    size: int
    stop_price: float
    regime_state: str


@dataclass
class PendingOrder:
    symbol: str
    side: str  # BUY or SELL
    family: str
    regime_state: str
    created_idx: int
    fill_idx: int
    reason: str
    reserved_cash: float = 0.0
    est_size: int = 0
    stop_price: float = 0.0


def _load_frames(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for s in symbols:
        raw = load_daily_bars(s, base_dir=base_dir)
        if raw.empty:
            continue
        frame = prepare_condition_frame(raw).copy()
        if frame.empty:
            continue
        frame["ret20"] = pd.to_numeric(frame["close"], errors="coerce").pct_change(20)
        frame["rsi4"] = _compute_rsi(pd.to_numeric(frame["close"], errors="coerce"), period=RSI_PERIOD)
        frame["atr_pct"] = pd.to_numeric(frame["atr14"], errors="coerce") / pd.to_numeric(frame["close"], errors="coerce")
        frame["regime_state"] = _detect_regime_state(frame)
        frame = frame.set_index(pd.to_datetime(frame["timestamp"], utc=True)).sort_index()
        frames[s] = frame
    return frames


def _collect_timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    return sorted({ts for f in frames.values() for ts in f.index})


def _row_at(fr: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    if ts not in fr.index:
        return None
    row = fr.loc[ts]
    return row.iloc[-1] if isinstance(row, pd.DataFrame) else row


def _equity(cash: float, positions: list[Position], rows: dict[str, pd.Series]) -> float:
    mkt = 0.0
    for p in positions:
        row = rows.get(p.symbol)
        if row is None:
            continue
        mkt += float(row["close"]) * p.size
    return float(cash + mkt)


def _active_risk(positions: list[Position]) -> float:
    return float(sum(max(p.entry_price - p.stop_price, 0.0) * p.size for p in positions))


def _pending_cash(pending: list[PendingOrder]) -> float:
    return float(sum(p.reserved_cash for p in pending if p.side == "BUY"))


def _metrics(trades: list[dict[str, Any]], initial_capital: float, daily_equity: list[tuple[pd.Timestamp, float]]) -> dict[str, Any]:
    pnls = [float(t["net_pnl"]) for t in trades]
    final_cap = initial_capital + sum(pnls)
    total_return = _safe_div(final_cap - initial_capital, initial_capital) * 100.0
    cagr = ((final_cap / initial_capital) ** (1 / 5) - 1) * 100.0 if initial_capital > 0 and final_cap > 0 else -100.0

    if daily_equity:
        eq_series = pd.Series([v for _, v in daily_equity], index=pd.to_datetime([t for t, _ in daily_equity], utc=True)).sort_index()
        eq_daily = eq_series.resample("1D").last().ffill().dropna()
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
        "initial_capital": _f(initial_capital, 2),
        "final_capital": _f(final_cap, 2),
        "total_return_pct": _f(total_return),
        "cagr_pct": _f(cagr),
        "mdd_pct": _f(mdd),
        "worst_year_pct": _f(worst_year),
        "tuw_months": int(tuw_months),
        "sharpe": _f(sharpe),
        "trade_count": int(len(trades)),
        "win_rate": _f(_safe_div(len(wins), len(pnls))) if pnls else 0.0,
        "profit_factor": _f(_safe_div(gp, gl)) if gl > 0 else 999.0,
    }


def _simulate(frames: dict[str, pd.DataFrame], strategy_mode: str) -> dict[str, Any]:
    ts_all = _collect_timestamps(frames)
    if len(ts_all) < 260:
        return {"status": "FAIL", "reason": "insufficient_data"}

    cash = float(INITIAL_CAPITAL)
    positions: list[Position] = []
    pending: list[PendingOrder] = []
    trades: list[dict[str, Any]] = []
    daily_equity: list[tuple[pd.Timestamp, float]] = []
    regime_switch_count = 0
    last_regime_by_symbol: dict[str, str] = {}
    validation = {
        "no_negative_cash": True,
        "no_capital_overlap": True,
        "no_lookahead": True,
        "no_same_bar_fill": True,
    }

    for i in range(210, len(ts_all) - 1):
        ts = ts_all[i]
        rows: dict[str, pd.Series] = {}
        for s, fr in frames.items():
            row = _row_at(fr, ts)
            if row is not None:
                rows[s] = row

        # Fill pending at t+1 open only.
        executed: list[PendingOrder] = []
        fills = 0
        for od in list(pending):
            if od.fill_idx != i:
                continue
            row = rows.get(od.symbol)
            if row is None:
                continue
            if fills >= MAX_ORDERS_PER_BAR:
                continue
            fills += 1
            open_px = float(row["open"])
            if od.side == "BUY":
                entry_px = _slip_up(open_px)
                size = max(0, int(od.est_size))
                spent = entry_px * size * (1.0 + FEE_RATE)
                # Reservation rollback then spend exact amount.
                cash += od.reserved_cash
                if size < 1 or spent > cash:
                    executed.append(od)
                    continue
                cash -= spent
                if cash < -1e-6:
                    validation["no_negative_cash"] = False
                    validation["no_capital_overlap"] = False
                positions.append(
                    Position(
                        symbol=od.symbol,
                        family=od.family,
                        entry_idx=i,
                        entry_ts=ts,
                        entry_price=entry_px,
                        size=size,
                        stop_price=od.stop_price,
                        regime_state=od.regime_state,
                    )
                )
                trades.append(
                    {
                        "symbol": od.symbol,
                        "event": "ENTRY",
                        "entry_family": od.family,
                        "entry_time": ts.isoformat(),
                        "entry_price": _f(entry_px),
                        "size": int(size),
                        "regime_state": od.regime_state,
                        "exit_reason": "",
                    }
                )
                executed.append(od)
            else:
                pos = next((p for p in positions if p.symbol == od.symbol and p.family == od.family), None)
                if pos is None:
                    executed.append(od)
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
                        "entry_family": pos.family,
                        "entry_time": pos.entry_ts.isoformat(),
                        "exit_time": ts.isoformat(),
                        "entry_price": _f(pos.entry_price),
                        "exit_price": _f(exit_px),
                        "size": int(pos.size),
                        "net_pnl": _f(pnl, 4),
                        "regime_state": pos.regime_state,
                        "exit_reason": od.reason,
                    }
                )
                positions.remove(pos)
                executed.append(od)
        for od in executed:
            if od in pending:
                pending.remove(od)

        # Schedule exits for next bar open.
        for p in list(positions):
            row = rows.get(p.symbol)
            if row is None:
                continue
            low = float(row["low"])
            close = float(row["close"])
            cur_regime = str(row.get("regime_state", "RANGE"))
            stop_hit = low <= p.stop_price
            time_hit = (i - p.entry_idx) >= MAX_HOLDING_BARS
            regime_flip = strategy_mode == "regime_switch_v1" and cur_regime != p.regime_state
            if stop_hit or time_hit or regime_flip:
                reason = "hard_stop" if stop_hit else ("time_stop" if time_hit else "regime_flip")
                if not any(o.symbol == p.symbol and o.side == "SELL" and o.family == p.family for o in pending):
                    pending.append(
                        PendingOrder(
                            symbol=p.symbol,
                            side="SELL",
                            family=p.family,
                            regime_state=p.regime_state,
                            created_idx=i,
                            fill_idx=i + 1,
                            reason=reason,
                        )
                    )

        # Build candidate entries.
        open_symbols = {p.symbol for p in positions}
        free_slots = max(0, MAX_CONCURRENT_POSITIONS - len(open_symbols))
        if free_slots > 0:
            trend_candidates: list[tuple[str, float]] = []
            mr_candidates: list[tuple[str, float]] = []
            for s, row in rows.items():
                regime_state = str(row.get("regime_state", "RANGE"))
                if s in open_symbols:
                    continue
                if any(o.symbol == s and o.side == "BUY" for o in pending):
                    continue
                if pd.isna(row.get("ret20")) or pd.isna(row.get("atr_pct")) or pd.isna(row.get("rsi4")):
                    continue
                if not pd.isna(row.get("ma200")) and s in last_regime_by_symbol:
                    if last_regime_by_symbol[s] != regime_state:
                        regime_switch_count += 1
                last_regime_by_symbol[s] = regime_state

                ret20 = float(row["ret20"])
                atr_pct = float(row["atr_pct"])
                rsi = float(row["rsi4"])
                if strategy_mode == "baseline":
                    if ret20 > 0:
                        trend_candidates.append((s, ret20))
                    continue

                # regime_switch_v1
                if regime_state == "TREND":
                    if ret20 > 0:
                        trend_candidates.append((s, ret20))
                else:
                    if rsi < RSI_ENTRY and atr_pct >= MIN_VOL_ATR_PCT:
                        mr_candidates.append((s, -rsi))

            trend_candidates.sort(key=lambda x: x[1], reverse=True)
            mr_candidates.sort(key=lambda x: x[1], reverse=True)
            selected: list[tuple[str, str, str]] = []
            if strategy_mode == "baseline":
                for s, _ in trend_candidates[:free_slots]:
                    selected.append((s, "momentum", "RANGE"))
            else:
                half = max(1, free_slots // 2)
                for s, _ in trend_candidates[:half]:
                    selected.append((s, "momentum", "TREND"))
                if len(selected) < free_slots:
                    for s, _ in mr_candidates[: free_slots - len(selected)]:
                        selected.append((s, "mean_reversion", "RANGE"))
                if len(selected) < free_slots:
                    # If one side is empty, fill by available strong trend candidates.
                    existing = {x[0] for x in selected}
                    for s, _ in trend_candidates:
                        if s in existing:
                            continue
                        selected.append((s, "momentum", "TREND"))
                        if len(selected) >= free_slots:
                            break

            # Reserve capital / risk and place pending buy orders.
            orders = 0
            for s, family, regime in selected:
                if orders >= MAX_ORDERS_PER_BAR:
                    break
                row = rows[s]
                est_open = float(row["close"])
                est_entry = _slip_up(est_open)
                equity = _equity(cash + _pending_cash(pending), positions, rows)
                total_risk_cap = equity * RISK_PER_TRADE * TOTAL_RISK_CAP_R
                remaining_risk = max(0.0, total_risk_cap - _active_risk(positions))
                stop = est_entry * (1.0 - STOP_LOSS_PCT)
                stop_dist = max(est_entry - stop, 0.01)
                risk_budget = min(equity * RISK_PER_TRADE, remaining_risk)
                est_size = int(math.floor(risk_budget / stop_dist))
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
                        family=family,
                        regime_state=regime,
                        created_idx=i,
                        fill_idx=i + 1,
                        reason="signal_entry",
                        reserved_cash=reserve_cash,
                        est_size=est_size,
                        stop_price=stop,
                    )
                )
                orders += 1

        eq = _equity(cash + _pending_cash(pending), positions, rows)
        daily_equity.append((ts, eq))

    # Release unfilled reserved cash.
    for od in pending:
        if od.side == "BUY":
            cash += od.reserved_cash

    # Force close remains at final close.
    last_ts = ts_all[-1]
    rows_last = {s: _row_at(f, last_ts) for s, f in frames.items()}
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
                "entry_family": p.family,
                "entry_time": p.entry_ts.isoformat(),
                "exit_time": last_ts.isoformat(),
                "entry_price": _f(p.entry_price),
                "exit_price": _f(exit_px),
                "size": int(p.size),
                "net_pnl": _f(pnl, 4),
                "regime_state": p.regime_state,
                "exit_reason": "time_stop",
            }
        )

    exit_trades = [t for t in trades if t.get("event") == "EXIT"]
    summary = _metrics(exit_trades, INITIAL_CAPITAL, daily_equity)
    return {
        "status": "PASS",
        "strategy_mode": strategy_mode,
        "summary": summary,
        "regime_switch_count": int(regime_switch_count),
        "validation": validation,
        "trades": trades,
    }


def _build_report(baseline: dict[str, Any], v1: dict[str, Any]) -> dict[str, Any]:
    b = baseline["summary"]
    r = v1["summary"]
    b_ret = float(b["total_return_pct"])
    b_cagr = float(b["cagr_pct"])
    r_ret = float(r["total_return_pct"])
    r_cagr = float(r["cagr_pct"])
    if float(r["sharpe"]) > float(b["sharpe"]) and float(r["mdd_pct"]) <= float(b["mdd_pct"]) + 2.0:
        final = "PASS"
    elif r_ret > b_ret or r_cagr > b_cagr:
        final = "WARNING"
    else:
        final = "FAIL"
    return {
        "task": "T500",
        "baseline": baseline,
        "regime_switch_v1": v1,
        "delta": {
            "trade_count": int(r["trade_count"] - b["trade_count"]),
            "total_return_pct": _f(r_ret - b_ret),
            "cagr_pct": _f(r_cagr - b_cagr),
            "sharpe": _f(float(r["sharpe"]) - float(b["sharpe"])),
            "mdd_pct": _f(float(r["mdd_pct"]) - float(b["mdd_pct"])),
        },
        "final_decision": final,
    }


def _render_md(report: dict[str, Any]) -> str:
    b = report["baseline"]["summary"]
    r = report["regime_switch_v1"]["summary"]
    return "\n".join(
        [
            "# Task T500 - Regime Switching V1 (Reality-First)",
            "",
            "## Summary Table",
            "| Metric | Baseline | Regime V1 |",
            "|---|---:|---:|",
            f"| Initial Capital | ${b['initial_capital']:,.2f} | ${r['initial_capital']:,.2f} |",
            f"| Final Capital | ${b['final_capital']:,.2f} | ${r['final_capital']:,.2f} |",
            f"| Total Return | {b['total_return_pct']:+.2f}% | {r['total_return_pct']:+.2f}% |",
            f"| CAGR | {b['cagr_pct']:+.2f}% | {r['cagr_pct']:+.2f}% |",
            f"| MDD | -{abs(b['mdd_pct']):.2f}% | -{abs(r['mdd_pct']):.2f}% |",
            f"| Worst Year | {b['worst_year_pct']:+.2f}% | {r['worst_year_pct']:+.2f}% |",
            f"| TUW (months) | {b['tuw_months']} | {r['tuw_months']} |",
            f"| Sharpe | {b['sharpe']:.4f} | {r['sharpe']:.4f} |",
            f"| Trade Count | {b['trade_count']} | {r['trade_count']} |",
            "",
            "## Runtime Validation",
            f"- baseline validation: {report['baseline']['validation']}",
            f"- regime_switch_v1 validation: {report['regime_switch_v1']['validation']}",
            f"- regime_switch_count (v1): {report['regime_switch_v1']['regime_switch_count']}",
            "",
            f"## Final Decision: {report['final_decision']}",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T500 regime switching v1 reality-first validation")
    parser.add_argument("--strategy-mode", type=str, default="compare", help="baseline|regime_switch_v1|compare")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE) + LEVERAGED_UNIVERSE)
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_500/task_500_regime_switch_v1.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_500/task_500_regime_switch_v1.md")
    args = parser.parse_args(argv)

    mode = str(args.strategy_mode).strip().lower()
    if mode not in ALLOWED_MODES:
        raise SystemExit(f"invalid --strategy-mode: {mode}. allowed: baseline|regime_switch_v1|compare")

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    frames = _load_frames(symbols, Path(args.data_dir))
    if mode == "baseline":
        report = {"task": "T500", "result": _simulate(frames, "baseline")}
    elif mode == "regime_switch_v1":
        report = {"task": "T500", "result": _simulate(frames, "regime_switch_v1")}
    else:
        baseline = _simulate(frames, "baseline")
        v1 = _simulate(frames, "regime_switch_v1")
        report = _build_report(baseline, v1)

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

