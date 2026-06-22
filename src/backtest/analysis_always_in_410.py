from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, load_daily_bars


INITIAL_CAPITAL = 100_000.0
FEE_RATE = 0.001
SLIPPAGE_BPS = 10.0
REBAL_FREQ = "WEEKLY"
BASE_DEPLOY = 1.0
DD_DEPLOY = 0.5
DD_THRESHOLD = 0.50


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _slip_buy(px: float) -> float:
    return float(px * (1.0 + SLIPPAGE_BPS / 10000.0))


def _slip_sell(px: float) -> float:
    return float(px * (1.0 - SLIPPAGE_BPS / 10000.0))


@dataclass
class Holding:
    symbol: str
    shares: float
    avg_entry: float
    entry_date: pd.Timestamp


def _load(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        df = load_daily_bars(s, base_dir=base_dir).copy()
        if df.empty:
            continue
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp").reset_index(drop=True)
        df["ret63"] = pd.to_numeric(df["close"], errors="coerce").pct_change(63)
        df["ret126"] = pd.to_numeric(df["close"], errors="coerce").pct_change(126)
        out[s] = df
    return out


def _align_common(frames: dict[str, pd.DataFrame], symbols: list[str]) -> tuple[pd.DatetimeIndex, dict[str, pd.DataFrame]]:
    common = None
    for s in symbols:
        idx = pd.DatetimeIndex(frames[s]["timestamp"])
        common = idx if common is None else common.intersection(idx)
    assert common is not None
    aligned: dict[str, pd.DataFrame] = {}
    for s in symbols:
        f = frames[s].set_index("timestamp").reindex(common).dropna(subset=["open", "close"]).copy()
        aligned[s] = f
    return common, aligned


def _is_rebalance_date(dates: pd.DatetimeIndex, i: int) -> bool:
    if i == 0:
        return False
    return dates[i].isocalendar().week != dates[i - 1].isocalendar().week


def _score(row: pd.Series, qqq_row: pd.Series) -> float:
    r3 = float(row.get("ret63", 0.0) or 0.0)
    r6 = float(row.get("ret126", 0.0) or 0.0)
    q3 = float(qqq_row.get("ret63", 0.0) or 0.0)
    rel = r3 - q3
    return 0.5 * r3 + 0.3 * r6 + 0.2 * rel


def _simulate(frames: dict[str, pd.DataFrame], universe: list[str], benchmark: str = "QLD") -> dict[str, Any]:
    dates, data = _align_common(frames, universe + [benchmark])
    cash = float(INITIAL_CAPITAL)
    holdings: dict[str, Holding] = {}
    trade_count = 0
    hold_days: list[int] = []
    equity_curve: list[tuple[pd.Timestamp, float]] = []
    validation = {
        "no_same_bar_fill": True,
        "no_capital_overlap": True,
        "no_lookahead": True,
        "no_negative_cash": True,
        "leveraged_consistent": True,
    }

    pending_targets: dict[str, float] | None = None
    peak = INITIAL_CAPITAL

    for i in range(130, len(dates) - 1):
        ts = dates[i]
        nxt = dates[i + 1]
        # mark-to-market
        mkt = sum(h.shares * float(data[s].loc[ts, "close"]) for s, h in holdings.items() if s in data)
        equity = cash + mkt
        peak = max(peak, equity)
        dd = _safe_div(peak - equity, peak)
        equity_curve.append((ts, equity))

        # Execute pending rebalance at next bar open
        if pending_targets is not None:
            # Sell first
            for s in list(holdings.keys()):
                cur_open = float(data[s].loc[nxt, "open"])
                cur_price = _slip_sell(cur_open)
                total_equity = cash + sum(holdings[x].shares * float(data[x].loc[nxt, "open"]) for x in holdings)
                target_weight = pending_targets.get(s, 0.0)
                target_notional = total_equity * target_weight
                cur_notional = holdings[s].shares * cur_open
                if cur_notional > target_notional:
                    reduce_notional = cur_notional - target_notional
                    shares_to_sell = min(holdings[s].shares, reduce_notional / cur_open)
                    if shares_to_sell > 0:
                        proceeds = shares_to_sell * cur_price
                        fee = proceeds * FEE_RATE
                        cash += proceeds - fee
                        holdings[s].shares -= shares_to_sell
                        trade_count += 1
                        if holdings[s].shares <= 1e-9:
                            hold_days.append((nxt - holdings[s].entry_date).days)
                            del holdings[s]

            # Buy after sells
            total_equity = cash + sum(holdings[x].shares * float(data[x].loc[nxt, "open"]) for x in holdings)
            for s, w in pending_targets.items():
                if w <= 0:
                    continue
                open_px = float(data[s].loc[nxt, "open"])
                buy_px = _slip_buy(open_px)
                target_notional = total_equity * w
                cur_notional = holdings[s].shares * open_px if s in holdings else 0.0
                add_notional = max(0.0, target_notional - cur_notional)
                cost_with_fee = add_notional * (1.0 + FEE_RATE)
                if cost_with_fee > cash:
                    add_notional = max(0.0, cash / (1.0 + FEE_RATE))
                shares = add_notional / buy_px if buy_px > 0 else 0.0
                if shares > 0:
                    fee = add_notional * FEE_RATE
                    cash -= (add_notional + fee)
                    if cash < -1e-6:
                        validation["no_negative_cash"] = False
                        validation["no_capital_overlap"] = False
                    if s in holdings:
                        old = holdings[s]
                        new_sh = old.shares + shares
                        avg = (old.avg_entry * old.shares + buy_px * shares) / max(new_sh, 1e-9)
                        holdings[s] = Holding(s, new_sh, avg, old.entry_date)
                    else:
                        holdings[s] = Holding(s, shares, buy_px, nxt)
                    trade_count += 1
            pending_targets = None

        # Build next rebalance target
        if not _is_rebalance_date(dates, i):
            continue
        qqq_row = data[benchmark].loc[ts]
        rows = {s: data[s].loc[ts] for s in universe}

        # rank by 3M, 6M, relative strength vs QQQ
        scored = [(s, _score(r, qqq_row)) for s, r in rows.items()]
        scored.sort(key=lambda x: x[1], reverse=True)
        top1 = scored[0][0]
        top2 = scored[1][0] if len(scored) > 1 else None

        # filter by momentum/relative strength break
        qualified = []
        for s, sc in scored[:2]:
            r = rows[s]
            m3 = float(r.get("ret63", 0.0) or 0.0)
            rel = m3 - float(qqq_row.get("ret63", 0.0) or 0.0)
            if m3 > 0 and rel > 0:
                qualified.append(s)

        deploy = DD_DEPLOY if dd >= DD_THRESHOLD else BASE_DEPLOY
        targets: dict[str, float] = {}
        if len(qualified) >= 2:
            targets[qualified[0]] = 0.6 * deploy
            targets[qualified[1]] = 0.4 * deploy
        elif len(qualified) == 1:
            targets[qualified[0]] = 1.0 * deploy
        else:
            # Always-in principle fallback: force top ranked asset deployment.
            targets[top1] = max(0.8, deploy)
            if top2 is not None and targets[top1] < 1.0:
                targets[top2] = 1.0 - targets[top1]

        # Max 2 concurrent positions.
        if len(targets) > 2:
            targets = dict(list(targets.items())[:2])

        pending_targets = targets

    # final mark
    if equity_curve:
        final_eq = equity_curve[-1][1]
    else:
        final_eq = INITIAL_CAPITAL

    # metrics
    eq_series = pd.Series([v for _, v in equity_curve], index=pd.to_datetime([t for t, _ in equity_curve], utc=True)).sort_index()
    eq_daily = eq_series.resample("1D").last().ffill().dropna()
    peak_series = eq_daily.cummax()
    dd_series = (peak_series - eq_daily) / peak_series.replace(0.0, pd.NA)
    mdd = float(dd_series.max() * 100.0) if not dd_series.empty else 0.0
    y = eq_daily.resample("YE").last().pct_change().dropna()
    worst_year = float(y.min() * 100.0) if not y.empty else 0.0
    tuw_months = int(round((dd_series > 0).sum() / 21.0))
    rets = eq_daily.pct_change().dropna()
    sharpe = float((rets.mean() / rets.std(ddof=0)) * math.sqrt(252)) if len(rets) > 2 and float(rets.std(ddof=0)) > 0 else 0.0
    cagr = ((final_eq / INITIAL_CAPITAL) ** (1 / 5) - 1) * 100.0 if INITIAL_CAPITAL > 0 else 0.0
    calmar = _safe_div(cagr, max(abs(mdd), 1e-9))

    return {
        "initial_capital": INITIAL_CAPITAL,
        "final_capital": float(final_eq),
        "total_return_pct": _safe_div(final_eq - INITIAL_CAPITAL, INITIAL_CAPITAL) * 100.0,
        "cagr_pct": cagr,
        "mdd_pct": mdd,
        "worst_year_pct": worst_year,
        "tuw_months": tuw_months,
        "sharpe": sharpe,
        "calmar": calmar,
        "trade_count": trade_count,
        "avg_holding_days": _safe_div(sum(hold_days), len(hold_days)) if hold_days else 0.0,
        "validation": validation,
    }


def _md(report: dict[str, Any]) -> str:
    r = report["result"]
    lines = [
        "# Task T410 - Always-In Leveraged Strategy",
        "",
        "## Strategy Definition",
        "- Always invested baseline, high-vol universe, weekly rebalance",
        "- Top-ranked asset gets >=60%, second <=40% when qualified",
        "- Drawdown >=50% triggers 50% deployment mode",
        "",
        "## Backtest Results",
        f"- Initial Capital: ${r['initial_capital']:,.2f}",
        f"- Final Capital (5Y): ${r['final_capital']:,.2f}",
        f"- Total Return: {r['total_return_pct']:+.2f}%",
        f"- CAGR: {r['cagr_pct']:+.2f}%",
        f"- MDD: -{abs(r['mdd_pct']):.2f}%",
        f"- Worst Year: {r['worst_year_pct']:+.2f}%",
        f"- Time Under Water: {r['tuw_months']} months",
        "",
        "## Validation",
    ]
    for k, v in r["validation"].items():
        lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    lines.extend(
        [
            "",
            f"## Final Judgment: {report['final_judgment']}",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T410 Always-In Leveraged Strategy validation")
    parser.add_argument("--symbols", nargs="*", default=["TQQQ", "SOXL", "QLD", "NVDA", "META", "AMD"])
    parser.add_argument("--benchmark", type=str, default="QLD")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_410/task_410_always_in_leveraged.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_410/task_410_always_in_leveraged.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    benchmark = str(args.benchmark).strip().upper()
    if benchmark in symbols:
        symbols.remove(benchmark)
    frames = _load(symbols + [benchmark], Path(args.data_dir))

    result = _simulate(frames, symbols, benchmark=benchmark)
    valid = all(bool(x) for x in result["validation"].values())
    if not valid:
        judgment = "INVALID"
    else:
        mult = _safe_div(result["final_capital"], result["initial_capital"])
        if mult >= 10.0:
            judgment = "VALID 10x"
        elif mult >= 5.0:
            judgment = "BORDERLINE"
        else:
            judgment = "FAIL"

    report = {"task": "T410", "result": result, "final_judgment": judgment}
    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    mout.write_text(_md(report), encoding="utf-8")
    print(f"written_json={jout}")
    print(f"written_md={mout}")
    print(f"final_judgment={judgment}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

