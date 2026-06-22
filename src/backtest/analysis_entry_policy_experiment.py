from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import run_full_backtest_universe_with_stats, summarize


POLICIES = [
    ("BASELINE", "limit=breakout*1.001, wait=3, no-chase"),
    ("STRICT_LIMIT", "limit=breakout, wait=3, no-chase"),
    ("AGGRESSIVE_LIMIT", "limit=breakout*1.002, wait=3, no-chase"),
    ("EXTENDED_WAIT", "limit=breakout*1.001, wait=5, no-chase"),
    ("LIMITED_CHASE", "limit=breakout, wait=3, chase<=+0.3%"),
    ("MARKET_LIKE", "next-open market proxy, always filled"),
]


def _policy_result(
    *,
    policy: str,
    symbols: list[str],
    base_dir: Path,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
) -> dict[str, Any]:
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        entry_policy=policy,
    )
    summary = summarize(results, initial_equity=initial_equity)
    return {
        "policy": policy,
        "trade_count": int(summary.trade_count),
        "fill_rate": float(stats.fill_rate),
        "expired_rate": float(stats.expired_rate),
        "profit_factor": float(summary.profit_factor),
        "net_pnl": float(summary.net_pnl),
        "win_rate": float(summary.win_rate),
        "max_drawdown": float(summary.max_drawdown),
        "sharpe": float(summary.sharpe_ratio),
        "missed_trades": int(stats.missed_trades),
        "big_miss": int(stats.big_miss_count),
        "missed_profit_estimate": float(stats.missed_profit_estimate),
        "total_signals": int(stats.total_signals),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 065: Entry Execution Policy Experiment")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--fee-rate", type=float, default=0.0005)
    parser.add_argument("--slippage-rate", type=float, default=0.0005)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)
    setup = {
        "symbols": symbols,
        "data_dir": str(base_dir),
        "initial_equity": args.initial_equity,
        "fee_rate": args.fee_rate,
        "slippage_rate": args.slippage_rate,
        "policies": [{"name": k, "description": v} for k, v in POLICIES],
    }

    rows: list[dict[str, Any]] = []
    for policy, _desc in POLICIES:
        rows.append(
            _policy_result(
                policy=policy,
                symbols=symbols,
                base_dir=base_dir,
                initial_equity=args.initial_equity,
                fee_rate=args.fee_rate,
                slippage_rate=args.slippage_rate,
            )
        )

    baseline = next(row for row in rows if row["policy"] == "BASELINE")
    for row in rows:
        row["net_pnl_delta_vs_baseline"] = row["net_pnl"] - baseline["net_pnl"]
        row["fill_rate_delta_vs_baseline"] = row["fill_rate"] - baseline["fill_rate"]
        row["pf_delta_vs_baseline"] = row["profit_factor"] - baseline["profit_factor"]
        row["big_miss_reduction_vs_baseline"] = baseline["big_miss"] - row["big_miss"]
        row["missed_profit_reduction_vs_baseline"] = baseline["missed_profit_estimate"] - row["missed_profit_estimate"]

    feasible = [
        row
        for row in rows
        if row["profit_factor"] >= 1.1
        and row["net_pnl"] >= baseline["net_pnl"]
        and row["fill_rate"] >= baseline["fill_rate"]
        and row["big_miss"] <= baseline["big_miss"]
    ]
    best_policy = max(feasible, key=lambda x: (x["profit_factor"], x["net_pnl"])) if feasible else None

    report = {
        "experiment_setup": setup,
        "results": rows,
        "best_policy": best_policy,
    }
    out = json.dumps(report, ensure_ascii=True, indent=2)
    print(out)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

