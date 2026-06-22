from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import FullTradeResult, run_full_backtest_universe_with_stats, summarize


ENTRY_POLICY = "LIMITED_CHASE"

SCENARIOS = [
    ("S1_ZERO_COST", 0.0, 0.0),
    ("S2_LOW_COST", 0.0005, 0.0005),
    ("S3_MEDIUM_COST", 0.0010, 0.0005),
    ("S4_KIS_REALISTIC", 0.0025, 0.0010),
    ("S5_KIS_STRESS_20", 0.0025, 0.0020),
    ("S6_KIS_STRESS_30", 0.0025, 0.0030),
]


def _scenario_result(
    *,
    name: str,
    fee_rate: float,
    slippage_rate: float,
    symbols: list[str],
    base_dir: Path,
    initial_equity: float,
) -> tuple[dict[str, Any], list[FullTradeResult]]:
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        entry_policy=ENTRY_POLICY,
    )
    summary = summarize(results, initial_equity=initial_equity)
    row = {
        "scenario": name,
        "fee_rate": fee_rate,
        "slippage_rate": slippage_rate,
        "total_pnl": float(summary.total_pnl),
        "net_pnl": float(summary.net_pnl),
        "trades": int(summary.trade_count),
        "win_rate": float(summary.win_rate),
        "profit_factor": float(summary.profit_factor),
        "max_drawdown": float(summary.max_drawdown),
        "sharpe": float(summary.sharpe_ratio),
        "fill_rate": float(stats.fill_rate),
        "expired_rate": float(stats.expired_rate),
        "big_miss": int(stats.big_miss_count),
        "missed_trades": int(stats.missed_trades),
    }
    return row, results


def _to_trade_frame(results: list[FullTradeResult]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in results:
        trade = item.trade
        meta = dict(item.metadata or {})
        rows.append(
            {
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "gross_pnl": float(trade.actual_pnl or 0.0),
                "net_pnl": float(item.net_pnl),
                "regime": str(item.regime),
                "exit_rule": str(meta.get("exit_rule", "UNKNOWN")),
                "sector": str(meta.get("sector", "UNKNOWN")),
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["exit_time"] = pd.to_datetime(frame["exit_time"], utc=True, errors="coerce")
        frame = frame.sort_values("exit_time").reset_index(drop=True)
    return frame


def _drawdown_analysis(results: list[FullTradeResult], top_n: int = 3) -> dict[str, Any]:
    frame = _to_trade_frame(results)
    if frame.empty:
        return {"worst_segments": [], "symbol_contribution": [], "exit_rule_contribution": []}

    frame["equity"] = frame["net_pnl"].cumsum()
    frame["peak"] = frame["equity"].cummax()
    frame["drawdown"] = frame["peak"] - frame["equity"]

    segments: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in frame.nlargest(top_n * 2, "drawdown").itertuples(index=False):
        trough_time = row.exit_time
        subset = frame[frame["exit_time"] <= trough_time]
        if subset.empty:
            continue
        peak_idx = subset["equity"].idxmax()
        peak_time = frame.loc[peak_idx, "exit_time"]
        key = (str(peak_time), str(trough_time))
        if key in seen:
            continue
        seen.add(key)
        segment = frame[(frame["exit_time"] >= peak_time) & (frame["exit_time"] <= trough_time)]
        if segment.empty:
            continue
        segments.append(
            {
                "peak_time": str(peak_time),
                "trough_time": str(trough_time),
                "drawdown": float(row.drawdown),
                "trade_count": int(len(segment)),
                "top_symbol_losses": _group_sum(segment, "symbol", ascending=True, limit=5),
                "exit_rule_loss": _group_sum(segment, "exit_rule", ascending=True, limit=5),
                "regime_loss": _group_sum(segment, "regime", ascending=True, limit=5),
            }
        )
        if len(segments) >= top_n:
            break

    return {
        "worst_segments": segments,
        "symbol_contribution": _group_sum(frame, "symbol", ascending=True, limit=12),
        "exit_rule_contribution": _group_sum(frame, "exit_rule", ascending=True, limit=10),
        "regime_contribution": _group_sum(frame, "regime", ascending=True, limit=10),
    }


def _group_sum(frame: pd.DataFrame, column: str, *, ascending: bool, limit: int) -> list[dict[str, Any]]:
    if frame.empty or column not in frame.columns:
        return []
    grouped = (
        frame.groupby(column, as_index=False)["net_pnl"]
        .sum()
        .sort_values("net_pnl", ascending=ascending)
        .head(limit)
    )
    return grouped.to_dict(orient="records")


def _task_066_gate(row: dict[str, Any]) -> dict[str, Any]:
    net_pnl = float(row["net_pnl"])
    mdd = float(row["max_drawdown"])
    pf = float(row["profit_factor"])
    sharpe = float(row["sharpe"])

    hard_fail = pf < 1.0 or net_pnl < 0
    pass_gate = pf >= 1.2 and net_pnl > 0 and sharpe >= 1.0 and mdd <= net_pnl * 0.40
    if hard_fail:
        status = "FAIL"
    elif pass_gate:
        status = "PASS"
    else:
        status = "WARNING"
    return {
        "status": status,
        "pf_ok": pf >= 1.2,
        "net_pnl_ok": net_pnl > 0,
        "sharpe_ok": sharpe >= 1.0,
        "mdd_ok": mdd <= net_pnl * 0.40 if net_pnl > 0 else False,
        "mdd_to_net_pnl_pct": (mdd / net_pnl * 100.0) if net_pnl > 0 else None,
    }


def _pilot_doc_gate(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {row["scenario"]: row for row in scenarios}
    s4 = by_name["S4_KIS_REALISTIC"]
    s5 = by_name["S5_KIS_STRESS_20"]
    s6 = by_name["S6_KIS_STRESS_30"]
    checks = {
        "scenario_4_pf_1_25": s4["profit_factor"] >= 1.25,
        "scenario_4_net_positive": s4["net_pnl"] > 0,
        "scenario_4_sharpe_1": s4["sharpe"] >= 1.0,
        "scenario_5_pf_1_10": s5["profit_factor"] >= 1.10,
        "scenario_5_net_positive": s5["net_pnl"] > 0,
        "scenario_6_pf_1_05": s6["profit_factor"] >= 1.05,
        "scenario_4_mdd_40pct_net": s4["max_drawdown"] <= s4["net_pnl"] * 0.40 if s4["net_pnl"] > 0 else False,
    }
    if all(checks.values()):
        status = "PASS"
    elif s4["profit_factor"] >= 1.0 and s4["net_pnl"] > 0:
        status = "WARNING"
    else:
        status = "FAIL"
    return {"status": status, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 066: Final Validation for LIMITED_CHASE")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)

    scenario_rows: list[dict[str, Any]] = []
    kis_results: list[FullTradeResult] = []
    for name, fee_rate, slippage_rate in SCENARIOS:
        row, results = _scenario_result(
            name=name,
            fee_rate=fee_rate,
            slippage_rate=slippage_rate,
            symbols=symbols,
            base_dir=base_dir,
            initial_equity=args.initial_equity,
        )
        row["task_066_gate"] = _task_066_gate(row)
        scenario_rows.append(row)
        if name == "S4_KIS_REALISTIC":
            kis_results = results

    report = {
        "setup": {
            "entry_policy": ENTRY_POLICY,
            "symbols": symbols,
            "data_dir": str(base_dir),
            "initial_equity": args.initial_equity,
        },
        "final_results": next(row for row in scenario_rows if row["scenario"] == "S4_KIS_REALISTIC"),
        "cost_sensitivity": scenario_rows,
        "drawdown_analysis": _drawdown_analysis(kis_results),
        "kpi_gate_result": {
            "task_066": next(row for row in scenario_rows if row["scenario"] == "S4_KIS_REALISTIC")["task_066_gate"],
            "pilot_kpi_gate_doc": _pilot_doc_gate(scenario_rows),
        },
    }
    out = json.dumps(report, ensure_ascii=True, indent=2, default=str)
    print(out)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
