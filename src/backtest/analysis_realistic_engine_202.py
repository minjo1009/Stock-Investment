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


INITIAL_CASH = 100_000.0
RISK_PER_TRADE = 0.01
GLOBAL_RISK_CAP_R = 1.0
ENTRY_SLIPPAGE_BPS = 10.0
EXIT_SLIPPAGE_BPS = 10.0
FEE_RATE = 0.001
MAX_CONCURRENT_POSITIONS = 8
MAX_ORDERS_PER_BAR = 8
MAX_HOLDING_BARS = 20
COOLDOWN_BARS = 5

TRANCHE_R = {"E1": 0.3, "E2": 0.3, "E3": 0.4}


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _slip_up(px: float, bps: float) -> float:
    return float(px * (1.0 + bps / 10000.0))


def _slip_dn(px: float, bps: float) -> float:
    return float(px * (1.0 - bps / 10000.0))


@dataclass
class Position:
    symbol: str
    entry_type: str
    entry_idx: int
    entry_ts: pd.Timestamp
    entry_price: float
    size: int
    stop_price: float
    init_risk_per_share: float
    breakout_level: float
    atr_at_entry: float
    highest_close: float
    partial_taken: bool = False
    closed: bool = False


@dataclass
class PendingOrder:
    symbol: str
    kind: str  # E1/E2/E3
    created_idx: int
    fill_idx: int
    stop_price: float
    breakout_level: float
    atr_value: float
    tranche_r: float


def _load_frames(symbols: list[str], base_dir: Path) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        raw = load_daily_bars(s, base_dir=base_dir)
        frame = prepare_condition_frame(raw)
        if frame.empty:
            continue
        frame = frame.set_index(pd.to_datetime(frame["timestamp"], utc=True)).sort_index()
        out[s] = frame
    return out


def _symbol_row(frame: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    if ts not in frame.index:
        return None
    row = frame.loc[ts]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[-1]
    return row


def _account_equity(cash: float, positions: list[Position], rows_by_symbol: dict[str, pd.Series]) -> float:
    mkt = 0.0
    for p in positions:
        row = rows_by_symbol.get(p.symbol)
        if row is None:
            continue
        mkt += float(row["close"]) * p.size
    return float(cash + mkt)


def _active_risk(positions: list[Position]) -> float:
    total = 0.0
    for p in positions:
        total += max(p.entry_price - p.stop_price, 0.0) * p.size
    return float(total)


def _collect_timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    all_ts = sorted({ts for f in frames.values() for ts in f.index})
    return all_ts


def _run_simulation(frames: dict[str, pd.DataFrame], mode: str) -> dict[str, Any]:
    timestamps = _collect_timestamps(frames)
    if len(timestamps) < 260:
        return {"status": "FAIL", "reason": "insufficient timestamps", "trades": []}

    start_idx = 210
    cash = float(INITIAL_CASH)
    positions: list[Position] = []
    pending: list[PendingOrder] = []
    trades: list[dict[str, Any]] = []
    cooldown_until: dict[str, int] = {}
    symbol_e1_open: dict[str, bool] = {}
    validation = {
        "negative_cash": False,
        "capital_overlap_violation": False,
        "same_bar_fill_violation": False,
        "lookahead_violation": False,
    }

    for i in range(start_idx, len(timestamps) - 1):
        ts = timestamps[i]
        next_ts = timestamps[i + 1]
        rows_now: dict[str, pd.Series] = {}
        for s, f in frames.items():
            row = _symbol_row(f, ts)
            if row is not None:
                rows_now[s] = row

        # 1) Fill pending orders scheduled for this bar (t+1 fill discipline).
        filled_pending: list[PendingOrder] = []
        orders_filled_this_bar = 0
        for od in list(pending):
            if od.fill_idx != i:
                continue
            row = rows_now.get(od.symbol)
            if row is None:
                continue
            if orders_filled_this_bar >= MAX_ORDERS_PER_BAR:
                continue

            entry_px = _slip_up(float(row["open"]), ENTRY_SLIPPAGE_BPS)
            stop_dist = max(entry_px - od.stop_price, 0.01)
            equity = _account_equity(cash, positions, rows_now)
            trade_risk_budget = equity * RISK_PER_TRADE * od.tranche_r
            shares = int(math.floor(trade_risk_budget / stop_dist))
            notional = entry_px * shares
            fee = notional * FEE_RATE
            cash_needed = notional + fee
            new_risk = stop_dist * shares
            total_risk_cap = equity * RISK_PER_TRADE * GLOBAL_RISK_CAP_R

            if shares < 1:
                continue
            if cash_needed > cash:
                validation["capital_overlap_violation"] = True
                continue
            if _active_risk(positions) + new_risk > total_risk_cap:
                continue
            if len({p.symbol for p in positions}) >= MAX_CONCURRENT_POSITIONS and od.symbol not in {p.symbol for p in positions}:
                continue

            cash -= cash_needed
            if cash < 0:
                validation["negative_cash"] = True
            pos = Position(
                symbol=od.symbol,
                entry_type=od.kind,
                entry_idx=i,
                entry_ts=ts,
                entry_price=entry_px,
                size=shares,
                stop_price=od.stop_price,
                init_risk_per_share=stop_dist,
                breakout_level=od.breakout_level,
                atr_at_entry=od.atr_value,
                highest_close=float(row["close"]),
            )
            positions.append(pos)
            orders_filled_this_bar += 1
            filled_pending.append(od)
            if od.kind == "E1":
                symbol_e1_open[od.symbol] = True
        for od in filled_pending:
            pending.remove(od)

        # 2) Exit logic with conservative intrabar rule (worst outcome first).
        kept: list[Position] = []
        for p in positions:
            row = rows_now.get(p.symbol)
            if row is None:
                kept.append(p)
                continue
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            atr = float(row["atr14"]) if not pd.isna(row["atr14"]) else p.atr_at_entry
            p.highest_close = max(p.highest_close, close)

            # trailing activation after +1R
            mfe_r = _safe_div(p.highest_close - p.entry_price, max(p.init_risk_per_share, 1e-9))
            trail_stop = p.stop_price
            if mfe_r >= 1.0:
                trail_stop = max(trail_stop, p.highest_close - 1.5 * atr)

            partial_target = p.entry_price + 1.5 * p.init_risk_per_share
            stop_hit = low <= trail_stop
            target_hit = high >= partial_target and (not p.partial_taken)

            # Conservative same-bar conflict: stop first for long.
            if stop_hit:
                exit_px = _slip_dn(trail_stop, EXIT_SLIPPAGE_BPS)
                proceeds = exit_px * p.size
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - p.entry_price) * p.size - fee
                trades.append(
                    {
                        "symbol": p.symbol,
                        "entry_type": p.entry_type,
                        "entry_time": p.entry_ts.isoformat(),
                        "exit_time": ts.isoformat(),
                        "size": int(p.size),
                        "entry_price": _f(p.entry_price),
                        "exit_price": _f(exit_px),
                        "net_pnl": _f(pnl, 4),
                        "exit_rule": "STOP_OR_TRAIL",
                    }
                )
                symbol_e1_open[p.symbol] = False
                cooldown_until[p.symbol] = i + COOLDOWN_BARS
                continue

            if target_hit and p.size > 1:
                part = max(1, int(math.floor(p.size * 0.3)))
                exit_px = _slip_dn(partial_target, EXIT_SLIPPAGE_BPS)
                proceeds = exit_px * part
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - p.entry_price) * part - fee
                p.size -= part
                p.partial_taken = True
                trades.append(
                    {
                        "symbol": p.symbol,
                        "entry_type": p.entry_type + "_PARTIAL",
                        "entry_time": p.entry_ts.isoformat(),
                        "exit_time": ts.isoformat(),
                        "size": int(part),
                        "entry_price": _f(p.entry_price),
                        "exit_price": _f(exit_px),
                        "net_pnl": _f(pnl, 4),
                        "exit_rule": "PARTIAL_TP",
                    }
                )

            if i - p.entry_idx >= MAX_HOLDING_BARS:
                exit_px = _slip_dn(close, EXIT_SLIPPAGE_BPS)
                proceeds = exit_px * p.size
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - p.entry_price) * p.size - fee
                trades.append(
                    {
                        "symbol": p.symbol,
                        "entry_type": p.entry_type + "_TIME",
                        "entry_time": p.entry_ts.isoformat(),
                        "exit_time": ts.isoformat(),
                        "size": int(p.size),
                        "entry_price": _f(p.entry_price),
                        "exit_price": _f(exit_px),
                        "net_pnl": _f(pnl, 4),
                        "exit_rule": "TIME",
                    }
                )
                symbol_e1_open[p.symbol] = False
                continue

            kept.append(p)
        positions = kept

        # 3) Signal generation at bar t, orders placed for t+1 only.
        orders_created = 0
        for s, row in rows_now.items():
            if orders_created >= MAX_ORDERS_PER_BAR:
                break
            if i <= cooldown_until.get(s, -1):
                continue
            if pd.isna(row.get("rolling_high_20")) or pd.isna(row.get("atr14")):
                continue
            breakout = float(row["close"]) > float(row["rolling_high_20"])
            ma_ok = (not pd.isna(row.get("ma20"))) and (not pd.isna(row.get("ma50"))) and float(row["ma20"]) > float(row["ma50"])
            if not (breakout and ma_ok):
                continue
            if next_ts <= ts:
                validation["lookahead_violation"] = True
                continue

            open_symbols = {p.symbol for p in positions}
            has_e1 = any(p.symbol == s and p.entry_type == "E1" for p in positions)
            has_e2 = any(p.symbol == s and p.entry_type == "E2" for p in positions)
            has_e3 = any(p.symbol == s and p.entry_type == "E3" for p in positions)
            atr = float(row["atr14"])
            rh = float(row["rolling_high_20"])

            # baseline: only E1 once per symbol while flat
            if mode == "BASELINE":
                if s in open_symbols:
                    continue
                stop = rh - 1.0 * atr
                pending.append(PendingOrder(s, "E1", i, i + 1, stop, rh, atr, 1.0))
                orders_created += 1
                continue

            # MULTI_ENTRY_V1
            if not has_e1:
                stop = rh - 1.0 * atr
                pending.append(PendingOrder(s, "E1", i, i + 1, stop, rh, atr, TRANCHE_R["E1"]))
                orders_created += 1
                continue

            # E2 pullback
            if has_e1 and (not has_e2):
                pullback_zone = abs(float(row["close"]) - rh) <= (0.3 * atr)
                hold = float(row["close"]) > rh
                if pullback_zone and hold:
                    stop = rh - 0.5 * atr
                    pending.append(PendingOrder(s, "E2", i, i + 1, stop, rh, atr, TRANCHE_R["E2"]))
                    orders_created += 1
                    continue

            # E3 continuation
            if (has_e1 or has_e2) and (not has_e3):
                f = frames[s]
                sub = f.loc[:ts]
                if len(sub) >= 6:
                    highs = sub["high"].astype(float).iloc[-6:-1]
                    lows = sub["low"].astype(float).iloc[-6:-1]
                    box_high = float(highs.max())
                    box_low = float(lows.min())
                    if float(row["close"]) > box_high and (box_high - box_low) <= 2.0 * atr:
                        stop = (box_high + box_low) / 2.0
                        pending.append(PendingOrder(s, "E3", i, i + 1, stop, box_high, atr, TRANCHE_R["E3"]))
                        orders_created += 1

    # Close remaining at last close
    last_ts = timestamps[-1]
    rows_last = {s: _symbol_row(f, last_ts) for s, f in frames.items()}
    for p in positions:
        row = rows_last.get(p.symbol)
        if row is None:
            continue
        exit_px = _slip_dn(float(row["close"]), EXIT_SLIPPAGE_BPS)
        proceeds = exit_px * p.size
        fee = proceeds * FEE_RATE
        cash += proceeds - fee
        pnl = (exit_px - p.entry_price) * p.size - fee
        trades.append(
            {
                "symbol": p.symbol,
                "entry_type": p.entry_type + "_FORCE",
                "entry_time": p.entry_ts.isoformat(),
                "exit_time": last_ts.isoformat(),
                "size": int(p.size),
                "entry_price": _f(p.entry_price),
                "exit_price": _f(exit_px),
                "net_pnl": _f(pnl, 4),
                "exit_rule": "FORCE_CLOSE",
            }
        )

    eq = INITIAL_CASH
    peak = eq
    max_dd = 0.0
    pnls = []
    for t in sorted(trades, key=lambda x: x["exit_time"]):
        pnl = float(t["net_pnl"])
        pnls.append(pnl)
        eq += pnl
        peak = max(peak, eq)
        max_dd = max(max_dd, _safe_div(peak - eq, peak))
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    gp = sum(wins)
    gl = abs(sum(losses))

    return {
        "status": "PASS",
        "trades": trades,
        "summary": {
            "trade_count": int(len(trades)),
            "net_pnl": _f(sum(pnls), 4),
            "win_rate": _f(_safe_div(len(wins), len(pnls))),
            "avg_win": _f(_safe_div(gp, len(wins)), 4) if wins else 0.0,
            "avg_loss": _f(_safe_div(sum(losses), len(losses)), 4) if losses else 0.0,
            "expectancy": _f(_safe_div(sum(pnls), len(pnls)), 4),
            "profit_factor": _f(_safe_div(gp, gl)) if gl > 0 else 999.0,
            "mdd_pct": _f(max_dd * 100.0),
            "final_cash": _f(cash, 4),
        },
        "validation": validation,
    }


def _md(report: dict[str, Any]) -> str:
    b = report["baseline"]["summary"]
    m = report["multi_entry_v1"]["summary"]
    lines = [
        "# Task T202 - Realistic Lifecycle Backtest Engine",
        "",
        "## Engine Design Summary",
        "- deterministic t->t+1 execution",
        "- strict cash and global risk cap",
        "- conservative intrabar stop-first rule",
        "",
        "## Backtest Result (Baseline vs Multi-entry)",
        "| Metric | Baseline | Multi-entry V1 |",
        "|---|---:|---:|",
        f"| trade_count | {b['trade_count']} | {m['trade_count']} |",
        f"| net_pnl | {b['net_pnl']} | {m['net_pnl']} |",
        f"| win_rate | {b['win_rate']} | {m['win_rate']} |",
        f"| avg_win | {b['avg_win']} | {m['avg_win']} |",
        f"| avg_loss | {b['avg_loss']} | {m['avg_loss']} |",
        f"| expectancy | {b['expectancy']} | {m['expectancy']} |",
        f"| profit_factor | {b['profit_factor']} | {m['profit_factor']} |",
        f"| mdd_pct | {b['mdd_pct']} | {m['mdd_pct']} |",
        "",
        "## Validation Checklist",
        f"- baseline: {report['baseline']['validation']}",
        f"- multi_entry_v1: {report['multi_entry_v1']['validation']}",
        "",
        "## Final Judgment",
        f"- {report['final_judgment']}",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T202 realistic lifecycle backtest engine")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_202/task_202_realistic_engine.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_202/task_202_realistic_engine.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    frames = _load_frames(symbols, Path(args.data_dir))

    baseline = _run_simulation(frames, mode="BASELINE")
    multi = _run_simulation(frames, mode="MULTI_ENTRY_V1")

    def has_violation(x: dict[str, Any]) -> bool:
        v = x.get("validation", {})
        return any(bool(v.get(k, False)) for k in ("negative_cash", "capital_overlap_violation", "same_bar_fill_violation", "lookahead_violation"))

    if has_violation(multi) or has_violation(baseline):
        final = "INVALID (artifact)"
    else:
        bn = float(baseline["summary"]["net_pnl"])
        mn = float(multi["summary"]["net_pnl"])
        if mn >= bn:
            final = "VALID EDGE"
        else:
            final = "DEGRADED EDGE"

    report = {
        "task": "T202",
        "baseline": baseline,
        "multi_entry_v1": multi,
        "delta": {
            "trade_count": int(multi["summary"]["trade_count"] - baseline["summary"]["trade_count"]),
            "net_pnl": _f(float(multi["summary"]["net_pnl"]) - float(baseline["summary"]["net_pnl"]), 4),
            "expectancy": _f(float(multi["summary"]["expectancy"]) - float(baseline["summary"]["expectancy"]), 4),
            "mdd_pct": _f(float(multi["summary"]["mdd_pct"]) - float(baseline["summary"]["mdd_pct"])),
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

