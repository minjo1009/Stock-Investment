from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, Bar, load_daily_bars
from backtest.engine_full import run_full_backtest_universe_with_stats, summarize
from strategy.conditions import prepare_condition_frame


ENTRY_POLICY = "LIMITED_CHASE"
RISK_POLICY = "TIME_STOP_ONLY"
FEE_RATE = 0.0025
SLIPPAGE_RATE = 0.0010
INITIAL_EQUITY = 100_000.0
RISK_PER_TRADE = 0.01

TRANCHE_R = {"E1": 0.3, "E2": 0.3, "E3": 0.4}
MAX_ENTRIES = 3
MAX_HOLDING_BARS = 20
COOLDOWN_BARS = 5


@dataclass
class Tranche:
    entry_type: str
    entry_index: int
    entry_time: datetime
    entry_price: float
    breakout_level: float
    atr_at_entry: float
    size: int
    stop_price: float
    active: bool = True
    partial_taken: bool = False


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _bars_from_df(df: pd.DataFrame) -> list[Bar]:
    out: list[Bar] = []
    for row in df.itertuples(index=False):
        ts = row.timestamp.to_pydatetime() if hasattr(row.timestamp, "to_pydatetime") else row.timestamp
        out.append(Bar(timestamp=ts, open=float(row.open), high=float(row.high), low=float(row.low), close=float(row.close), volume=float(row.volume)))
    return out


def _run_multi_entry_symbol(df: pd.DataFrame, *, symbol: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frame = prepare_condition_frame(df)
    if frame.empty:
        return [], {"E1": 0, "E2": 0, "E3": 0, "E1_hit": 0, "E2_hit": 0, "E3_hit": 0}

    closes = frame["close"].astype(float).tolist()
    highs = frame["high"].astype(float).tolist()
    lows = frame["low"].astype(float).tolist()
    opens = frame["open"].astype(float).tolist()
    ma50 = pd.to_numeric(frame["ma50"], errors="coerce").tolist()
    rolling_high = pd.to_numeric(frame["rolling_high_20"], errors="coerce").tolist()
    atr14 = pd.to_numeric(frame["atr14"], errors="coerce").tolist()

    trades: list[dict[str, Any]] = []
    entry_counts = {"E1": 0, "E2": 0, "E3": 0, "E1_hit": 0, "E2_hit": 0, "E3_hit": 0}
    active: list[Tranche] = []
    cooldown_until = -1
    session_breakout: float | None = None
    entry_anchor: float | None = None
    highest_close = -1.0
    regime_full = True

    for i in range(210, len(frame) - 1):
        atr = atr14[i]
        if pd.isna(atr) or atr <= 0:
            continue
        if i <= cooldown_until:
            continue

        close_now = closes[i]
        high_now = highs[i]
        low_now = lows[i]
        next_open = opens[i + 1]
        rh = rolling_high[i]
        if pd.isna(rh):
            continue
        regime_full = bool(not pd.isna(ma50[i]) and close_now > float(ma50[i]))
        risk_mult = 1.0 if regime_full else 0.5
        total_risk_budget = INITIAL_EQUITY * RISK_PER_TRADE * risk_mult

        # trailing state
        if active:
            highest_close = max(highest_close, close_now)
        hard_stop_hit = False
        remaining: list[Tranche] = []
        for tr in active:
            stop = tr.stop_price
            mfe_r = _safe_div(highest_close - tr.entry_price, max(tr.entry_price - stop, 1e-9))
            if mfe_r >= 1.0:
                stop = max(stop, highest_close - 1.5 * atr)
            if low_now <= stop:
                exit_px = stop * (1 - SLIPPAGE_RATE)
                pnl = (exit_px - tr.entry_price) * tr.size
                trades.append(
                    {
                        "symbol": symbol,
                        "entry_type": tr.entry_type,
                        "entry_time": tr.entry_time.isoformat(),
                        "exit_time": frame.iloc[i]["timestamp"].isoformat(),
                        "entry_price": _f(tr.entry_price),
                        "exit_price": _f(exit_px),
                        "size": int(tr.size),
                        "net_pnl": _f(pnl),
                        "stop_price": _f(tr.stop_price),
                        "atr_at_entry": _f(tr.atr_at_entry),
                    }
                )
                hard_stop_hit = True
            else:
                tr.stop_price = stop
                # optional partial TP at +1.5R
                if (not tr.partial_taken) and _safe_div(high_now - tr.entry_price, max(tr.entry_price - tr.stop_price, 1e-9)) >= 1.5 and tr.size > 1:
                    part = max(1, int(math.floor(tr.size * 0.3)))
                    exit_px = close_now * (1 - SLIPPAGE_RATE)
                    pnl = (exit_px - tr.entry_price) * part
                    trades.append(
                        {
                            "symbol": symbol,
                            "entry_type": tr.entry_type + "_PARTIAL",
                            "entry_time": tr.entry_time.isoformat(),
                            "exit_time": frame.iloc[i]["timestamp"].isoformat(),
                            "entry_price": _f(tr.entry_price),
                            "exit_price": _f(exit_px),
                            "size": int(part),
                            "net_pnl": _f(pnl),
                            "stop_price": _f(tr.stop_price),
                            "atr_at_entry": _f(tr.atr_at_entry),
                        }
                    )
                    tr.size -= part
                    tr.partial_taken = True
                remaining.append(tr)
        active = [t for t in remaining if t.size > 0]
        if hard_stop_hit and not active:
            cooldown_until = i + COOLDOWN_BARS
            session_breakout = None
            entry_anchor = None
            highest_close = -1.0
            continue

        # time exit
        timed_out: list[Tranche] = []
        keep: list[Tranche] = []
        for tr in active:
            if i - tr.entry_index >= MAX_HOLDING_BARS:
                timed_out.append(tr)
            else:
                keep.append(tr)
        active = keep
        for tr in timed_out:
            exit_px = close_now * (1 - SLIPPAGE_RATE)
            pnl = (exit_px - tr.entry_price) * tr.size
            trades.append(
                {
                    "symbol": symbol,
                    "entry_type": tr.entry_type + "_TIME",
                    "entry_time": tr.entry_time.isoformat(),
                    "exit_time": frame.iloc[i]["timestamp"].isoformat(),
                    "entry_price": _f(tr.entry_price),
                    "exit_price": _f(exit_px),
                    "size": int(tr.size),
                    "net_pnl": _f(pnl),
                    "stop_price": _f(tr.stop_price),
                    "atr_at_entry": _f(tr.atr_at_entry),
                }
            )

        if len(active) >= MAX_ENTRIES:
            continue

        # E1: breakout
        breakout = close_now > float(rh)
        if breakout and session_breakout is None:
            stop = float(rh) - 1.0 * float(atr)
            stop_dist = max(next_open - stop, 0.01)
            tranche_budget = total_risk_budget * TRANCHE_R["E1"]
            shares = int(math.floor(tranche_budget / stop_dist))
            if shares >= 1:
                ep = next_open * (1 + SLIPPAGE_RATE)
                t = Tranche("E1", i + 1, frame.iloc[i + 1]["timestamp"].to_pydatetime(), ep, float(rh), float(atr), shares, stop)
                active.append(t)
                session_breakout = float(rh)
                entry_anchor = ep
                highest_close = close_now
                entry_counts["E1"] += 1
                entry_counts["E1_hit"] += 1
                continue

        # E2: pullback re-entry
        if session_breakout is not None and any(t.entry_type == "E1" for t in active) and not any(t.entry_type == "E2" for t in active):
            pullback_zone = abs(close_now - session_breakout) <= (0.3 * float(atr))
            hold = close_now > session_breakout
            if pullback_zone and hold:
                stop = session_breakout - 0.5 * float(atr)
                stop_dist = max(next_open - stop, 0.01)
                tranche_budget = total_risk_budget * TRANCHE_R["E2"]
                shares = int(math.floor(tranche_budget / stop_dist))
                if shares >= 1:
                    ep = next_open * (1 + SLIPPAGE_RATE)
                    active.append(Tranche("E2", i + 1, frame.iloc[i + 1]["timestamp"].to_pydatetime(), ep, session_breakout, float(atr), shares, stop))
                    entry_counts["E2"] += 1
                    entry_counts["E2_hit"] += 1
                    continue

        # E3: continuation add-on (5 bar box breakout)
        if session_breakout is not None and any(t.entry_type in {"E1", "E2"} for t in active) and not any(t.entry_type == "E3" for t in active):
            if i >= 5:
                box_high = max(highs[i - 5 : i])
                box_low = min(lows[i - 5 : i])
                if close_now > box_high and (box_high - box_low) <= 2.0 * float(atr):
                    stop = (box_high + box_low) / 2.0
                    stop_dist = max(next_open - stop, 0.01)
                    tranche_budget = total_risk_budget * TRANCHE_R["E3"]
                    shares = int(math.floor(tranche_budget / stop_dist))
                    if shares >= 1:
                        ep = next_open * (1 + SLIPPAGE_RATE)
                        active.append(Tranche("E3", i + 1, frame.iloc[i + 1]["timestamp"].to_pydatetime(), ep, box_high, float(atr), shares, stop))
                        entry_counts["E3"] += 1
                        entry_counts["E3_hit"] += 1

    return trades, entry_counts


def _summary_from_trades(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {"trades": 0, "net_pnl": 0.0, "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0, "expectancy": 0.0, "pf": 0.0}
    pnls = [float(r["net_pnl"]) for r in rows]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gp = sum(wins)
    gl = abs(sum(losses))
    return {
        "trades": int(len(rows)),
        "net_pnl": _f(sum(pnls), 4),
        "win_rate": _f(_safe_div(len(wins), len(pnls))),
        "avg_win": _f(_safe_div(gp, len(wins)), 4) if wins else 0.0,
        "avg_loss": _f(_safe_div(sum(losses), len(losses)), 4) if losses else 0.0,
        "expectancy": _f(_safe_div(sum(pnls), len(pnls)), 4),
        "pf": _f(_safe_div(gp, gl)) if gl > 0 else 999.0,
    }


def _md(report: dict[str, Any]) -> str:
    b = report["baseline"]
    m = report["multi_entry_v1"]
    lines = [
        "# Task T201 - Multi-Entry Lifecycle Implementation",
        "",
        "## Metrics",
        "| Metric | Baseline | MULTI_ENTRY_V1 |",
        "|---|---:|---:|",
        f"| trades | {b['trades']} | {m['trades']} |",
        f"| net_pnl | {b['net_pnl']} | {m['net_pnl']} |",
        f"| win_rate | {b['win_rate']} | {m['win_rate']} |",
        f"| avg_win | {b['avg_win']} | {m['avg_win']} |",
        f"| avg_loss | {b['avg_loss']} | {m['avg_loss']} |",
        f"| expectancy | {b['expectancy']} | {m['expectancy']} |",
        f"| profit_factor | {b['pf']} | {m['pf']} |",
        "",
        "## Tranche Stats",
        f"- E1 hits: {report['tranche_stats']['E1_hit']}",
        f"- E2 hits: {report['tranche_stats']['E2_hit']}",
        f"- E3 hits: {report['tranche_stats']['E3_hit']}",
        "",
        "## Notes",
        "- R is risk budget: 1R = equity * risk_per_trade",
        "- shares = tranche_risk_budget / stop_distance",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T201 multi-entry lifecycle implementation (experimental)")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_201/task_201_multi_entry_v1.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_201/task_201_multi_entry_v1.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    base_dir = Path(args.data_dir)

    baseline_results, _stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=INITIAL_EQUITY,
        fee_rate=FEE_RATE,
        slippage_rate=SLIPPAGE_RATE,
        entry_policy=ENTRY_POLICY,
        risk_policy=RISK_POLICY,
        breakout_mode="BASELINE",
        mode="portfolio",
        max_positions=3,
    )
    baseline_summary = summarize(baseline_results, initial_equity=INITIAL_EQUITY)
    baseline_rows = [{"net_pnl": float(x.net_pnl)} for x in baseline_results]

    multi_rows: list[dict[str, Any]] = []
    tranche_stats = {"E1": 0, "E2": 0, "E3": 0, "E1_hit": 0, "E2_hit": 0, "E3_hit": 0}
    for symbol in symbols:
        df = load_daily_bars(symbol, base_dir=base_dir)
        rows, counts = _run_multi_entry_symbol(df, symbol=symbol)
        multi_rows.extend(rows)
        for k in tranche_stats:
            tranche_stats[k] += int(counts.get(k, 0))

    report = {
        "task": "T201",
        "mode": "MULTI_ENTRY_V1",
        "config": {
            "risk_per_trade": RISK_PER_TRADE,
            "R_definition": "1R = account_equity * risk_per_trade (risk budget)",
            "tranche_r": TRANCHE_R,
            "max_entries_per_symbol": MAX_ENTRIES,
            "cooldown_bars": COOLDOWN_BARS,
        },
        "baseline": {
            **_summary_from_trades(baseline_rows),
            "sharpe": _f(float(baseline_summary.sharpe_ratio)),
            "mdd": _f(float(baseline_summary.max_drawdown)),
        },
        "multi_entry_v1": _summary_from_trades(multi_rows),
        "tranche_stats": tranche_stats,
        "hit_ratio": {
            "E1": _f(_safe_div(tranche_stats["E1_hit"], max(tranche_stats["E1"], 1))),
            "E2": _f(_safe_div(tranche_stats["E2_hit"], max(tranche_stats["E2"], 1))),
            "E3": _f(_safe_div(tranche_stats["E3_hit"], max(tranche_stats["E3"], 1))),
        },
    }

    j = Path(args.json_out)
    m = Path(args.md_out)
    j.parent.mkdir(parents=True, exist_ok=True)
    m.parent.mkdir(parents=True, exist_ok=True)
    j.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    m.write_text(_md(report), encoding="utf-8")
    print(f"written_json={j}")
    print(f"written_md={m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

