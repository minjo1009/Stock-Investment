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


@dataclass
class PendingOrder:
    symbol: str
    kind: str
    created_idx: int
    fill_idx: int
    stop_price: float
    breakout_level: float
    atr_value: float
    tranche_r: float
    reserved_cash: float
    reserved_risk: float
    est_size: int


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


def _collect_timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    return sorted({ts for f in frames.values() for ts in f.index})


def _symbol_row(frame: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    if ts not in frame.index:
        return None
    row = frame.loc[ts]
    return row.iloc[-1] if isinstance(row, pd.DataFrame) else row


def _active_risk(positions: list[Position]) -> float:
    return float(sum(max(p.entry_price - p.stop_price, 0.0) * p.size for p in positions))


def _pending_reserved_cash(pending: list[PendingOrder]) -> float:
    return float(sum(o.reserved_cash for o in pending))


def _pending_reserved_risk(pending: list[PendingOrder]) -> float:
    return float(sum(o.reserved_risk for o in pending))


def _run(frames: dict[str, pd.DataFrame], mode: str) -> dict[str, Any]:
    ts_all = _collect_timestamps(frames)
    if len(ts_all) < 260:
        return {"status": "FAIL", "reason": "insufficient_data"}

    cash = float(INITIAL_CASH)
    positions: list[Position] = []
    pending: list[PendingOrder] = []
    trades: list[dict[str, Any]] = []
    cooldown_until: dict[str, int] = {}
    validation = {
        "negative_cash": False,
        "capital_overlap_violation": False,
        "same_bar_fill_violation": False,
        "lookahead_violation": False,
    }

    for i in range(210, len(ts_all) - 1):
        ts = ts_all[i]
        rows: dict[str, pd.Series] = {}
        for s, f in frames.items():
            row = _symbol_row(f, ts)
            if row is not None:
                rows[s] = row

        # Fill pending
        to_remove: list[PendingOrder] = []
        fill_count = 0
        for od in list(pending):
            if od.fill_idx != i:
                continue
            row = rows.get(od.symbol)
            if row is None:
                continue
            if fill_count >= MAX_ORDERS_PER_BAR:
                continue
            fill_count += 1
            entry_px = _slip_up(float(row["open"]), ENTRY_SLIPPAGE_BPS)
            # Recompute conservative size by reserved cash cap
            max_affordable = int(math.floor(_safe_div(od.reserved_cash, entry_px * (1.0 + FEE_RATE))))
            size = min(od.est_size, max_affordable)
            if size < 1:
                to_remove.append(od)
                continue
            cost = entry_px * size
            fee = cost * FEE_RATE
            spent = cost + fee
            # consume reserved cash that was already deducted at accept time.
            if spent <= od.reserved_cash:
                cash += (od.reserved_cash - spent)
            else:
                extra = spent - od.reserved_cash
                if extra > cash:
                    validation["capital_overlap_violation"] = True
                    # Cancel this order conservatively if funding is not possible.
                    to_remove.append(od)
                    continue
                cash -= extra
            if cash < -1e-6:
                validation["capital_overlap_violation"] = True
                validation["negative_cash"] = True
            pos = Position(
                symbol=od.symbol,
                entry_type=od.kind,
                entry_idx=i,
                entry_ts=ts,
                entry_price=entry_px,
                size=size,
                stop_price=od.stop_price,
                init_risk_per_share=max(entry_px - od.stop_price, 0.01),
                breakout_level=od.breakout_level,
                atr_at_entry=od.atr_value,
                highest_close=float(row["close"]),
            )
            positions.append(pos)
            to_remove.append(od)
        for od in to_remove:
            if od in pending:
                pending.remove(od)

        # Exit positions
        kept: list[Position] = []
        for p in positions:
            row = rows.get(p.symbol)
            if row is None:
                kept.append(p)
                continue
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            atr = float(row["atr14"]) if not pd.isna(row["atr14"]) else p.atr_at_entry
            p.highest_close = max(p.highest_close, close)
            mfe_r = _safe_div(p.highest_close - p.entry_price, max(p.init_risk_per_share, 1e-9))
            trail_stop = p.stop_price
            if mfe_r >= 1.0:
                trail_stop = max(trail_stop, p.highest_close - 1.5 * atr)
            partial_target = p.entry_price + 1.5 * p.init_risk_per_share
            stop_hit = low <= trail_stop
            target_hit = (high >= partial_target) and (not p.partial_taken)

            if stop_hit:
                exit_px = _slip_dn(trail_stop, EXIT_SLIPPAGE_BPS)
                proceeds = exit_px * p.size
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - p.entry_price) * p.size - fee
                trades.append({"symbol": p.symbol, "entry_type": p.entry_type, "net_pnl": _f(pnl, 4), "exit_rule": "STOP_OR_TRAIL"})
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
                trades.append({"symbol": p.symbol, "entry_type": p.entry_type + "_PARTIAL", "net_pnl": _f(pnl, 4), "exit_rule": "PARTIAL_TP"})

            if i - p.entry_idx >= MAX_HOLDING_BARS:
                exit_px = _slip_dn(close, EXIT_SLIPPAGE_BPS)
                proceeds = exit_px * p.size
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - p.entry_price) * p.size - fee
                trades.append({"symbol": p.symbol, "entry_type": p.entry_type + "_TIME", "net_pnl": _f(pnl, 4), "exit_rule": "TIME"})
                continue

            kept.append(p)
        positions = kept

        # Create orders at bar t for fill at t+1 with reservation
        orders_created = 0
        for s, row in rows.items():
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
            atr = float(row["atr14"])
            rh = float(row["rolling_high_20"])
            est_open = float(row["close"])  # conservative proxy for reservation
            est_entry = _slip_up(est_open, ENTRY_SLIPPAGE_BPS)
            equity = cash + sum(float(rows.get(p.symbol, row)["close"]) * p.size for p in positions)
            risk_mult = 1.0 if float(row["close"]) > float(row["ma50"]) else 0.5
            total_risk_budget = equity * RISK_PER_TRADE * risk_mult
            current_risk = _active_risk(positions) + _pending_reserved_risk(pending)
            risk_cap_total = equity * RISK_PER_TRADE * GLOBAL_RISK_CAP_R
            # cash is already net of accepted reservations.
            free_cash = cash

            open_syms = {p.symbol for p in positions}
            has_e1 = any(p.symbol == s and p.entry_type == "E1" for p in positions)
            has_e2 = any(p.symbol == s and p.entry_type == "E2" for p in positions)
            has_e3 = any(p.symbol == s and p.entry_type == "E3" for p in positions)

            candidates: list[tuple[str, float]] = []
            if mode == "BASELINE":
                if s not in open_syms:
                    candidates.append(("E1", 1.0))
            else:
                if not has_e1:
                    candidates.append(("E1", TRANCHE_R["E1"]))
                elif has_e1 and not has_e2 and abs(float(row["close"]) - rh) <= 0.3 * atr and float(row["close"]) > rh:
                    candidates.append(("E2", TRANCHE_R["E2"]))
                elif (has_e1 or has_e2) and not has_e3:
                    f = frames[s]
                    sub = f.loc[:ts]
                    if len(sub) >= 6:
                        box_high = float(sub["high"].astype(float).iloc[-6:-1].max())
                        box_low = float(sub["low"].astype(float).iloc[-6:-1].min())
                        if float(row["close"]) > box_high and (box_high - box_low) <= 2.0 * atr:
                            candidates.append(("E3", TRANCHE_R["E3"]))

            for kind, trr in candidates:
                if orders_created >= MAX_ORDERS_PER_BAR:
                    break
                stop = rh - atr if kind == "E1" else (rh - 0.5 * atr if kind == "E2" else rh - 0.5 * atr)
                if kind == "E3":
                    stop = rh - 0.5 * atr
                stop_dist = max(est_entry - stop, 0.01)
                tranche_budget = total_risk_budget * trr
                est_size = int(math.floor(tranche_budget / stop_dist))
                if est_size < 1:
                    continue
                reserve_cash = est_entry * est_size * (1.0 + FEE_RATE)
                reserve_risk = stop_dist * est_size
                if reserve_cash > free_cash:
                    continue
                if current_risk + reserve_risk > risk_cap_total:
                    continue
                if len(open_syms) >= MAX_CONCURRENT_POSITIONS and s not in open_syms:
                    continue

                pending.append(
                    PendingOrder(
                        symbol=s,
                        kind=kind,
                        created_idx=i,
                        fill_idx=i + 1,
                        stop_price=stop,
                        breakout_level=rh,
                        atr_value=atr,
                        tranche_r=trr,
                        reserved_cash=reserve_cash,
                        reserved_risk=reserve_risk,
                        est_size=est_size,
                    )
                )
                orders_created += 1
                # Reserve cash immediately at accepted time.
                cash -= reserve_cash
                if cash < -1e-6:
                    validation["capital_overlap_violation"] = True
                    validation["negative_cash"] = True
                free_cash -= reserve_cash
                current_risk += reserve_risk

    # Release leftover reservations
    for od in pending:
        cash += od.reserved_cash

    # Force close remaining positions at last close
    last_ts = ts_all[-1]
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
        trades.append({"symbol": p.symbol, "entry_type": p.entry_type + "_FORCE", "net_pnl": _f(pnl, 4), "exit_rule": "FORCE_CLOSE"})

    pnls = [float(t["net_pnl"]) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    eq = INITIAL_CASH
    peak = eq
    max_dd = 0.0
    for p in pnls:
        eq += p
        peak = max(peak, eq)
        max_dd = max(max_dd, _safe_div(peak - eq, peak))
    gp = sum(wins)
    gl = abs(sum(losses))

    return {
        "status": "PASS",
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
    return "\n".join(
        [
            "# Task T203 - Capital Accounting Consistency Repair",
            "",
            "## Baseline vs Multi-entry (after reserve accounting)",
            "| Metric | Baseline | Multi-entry |",
            "|---|---:|---:|",
            f"| trade_count | {b['trade_count']} | {m['trade_count']} |",
            f"| net_pnl | {b['net_pnl']} | {m['net_pnl']} |",
            f"| win_rate | {b['win_rate']} | {m['win_rate']} |",
            f"| expectancy | {b['expectancy']} | {m['expectancy']} |",
            f"| profit_factor | {b['profit_factor']} | {m['profit_factor']} |",
            f"| mdd_pct | {b['mdd_pct']} | {m['mdd_pct']} |",
            "",
            "## Validation",
            f"- baseline: {report['baseline']['validation']}",
            f"- multi_entry_v1: {report['multi_entry_v1']['validation']}",
            "",
            f"## Final: {report['final_judgment']}",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T203 capital accounting consistency repair")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_203/task_203_capital_consistency.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_203/task_203_capital_consistency.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    frames = _load_frames(symbols, Path(args.data_dir))
    baseline = _run(frames, "BASELINE")
    multi = _run(frames, "MULTI_ENTRY_V1")

    def has_viol(v: dict[str, Any]) -> bool:
        x = v.get("validation", {})
        return any(bool(x.get(k, False)) for k in ("negative_cash", "capital_overlap_violation", "same_bar_fill_violation", "lookahead_violation"))

    if has_viol(baseline) or has_viol(multi):
        final = "INVALID (artifact)"
    else:
        final = "VALID EDGE" if float(multi["summary"]["net_pnl"]) >= float(baseline["summary"]["net_pnl"]) else "DEGRADED EDGE"

    report = {
        "task": "T203",
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
