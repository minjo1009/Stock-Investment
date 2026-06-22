from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backtest.analysis_stop_loss_structure import _load_price_frames, _trade_rows
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import run_full_backtest_universe_with_stats, summarize


ENTRY_POLICY = "LIMITED_CHASE"
FEE_RATE = 0.0025
SLIPPAGE_RATE = 0.0010

POLICIES = [
    ("BASELINE", "current STOP only"),
    ("BREAK_EVEN_STOP", "if MFE >= +3%, lift stop to entry fill"),
    ("MFE_GIVEBACK_50", "if MFE >= +3%, exit after giving back 50% of max profit"),
    ("TIME_STOP", "after 10 bars, exit if profit is below +1%"),
    ("HYBRID", "break-even stop + MFE giveback + time stop"),
]


def _policy_result(
    *,
    policy: str,
    symbols: list[str],
    base_dir: Path,
    initial_equity: float,
) -> dict[str, Any]:
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=FEE_RATE,
        slippage_rate=SLIPPAGE_RATE,
        entry_policy=ENTRY_POLICY,
        risk_policy=policy,
    )
    summary = summarize(results, initial_equity=initial_equity)
    frames = _load_price_frames(symbols, base_dir)
    trades = _trade_rows(results, frames)
    stops = trades[trades["stop_hit_flag"] == True].copy() if not trades.empty else trades
    good_then_stop = int((stops["classification"] == "GOOD_THEN_STOP").sum()) if not stops.empty else 0
    stop_count = int(len(stops))
    exit_rule_counts = trades["exit_rule"].value_counts(dropna=False).to_dict() if not trades.empty else {}
    return {
        "policy": policy,
        "trade_count": int(summary.trade_count),
        "win_rate": float(summary.win_rate),
        "profit_factor": float(summary.profit_factor),
        "net_pnl": float(summary.net_pnl),
        "max_drawdown": float(summary.max_drawdown),
        "sharpe": float(summary.sharpe_ratio),
        "stop_count": stop_count,
        "good_then_stop": good_then_stop,
        "fill_rate": float(stats.fill_rate),
        "expired_rate": float(stats.expired_rate),
        "exit_rule_counts": {str(k): int(v) for k, v in exit_rule_counts.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 068: Risk Model Layer Experiment")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)

    rows = [
        _policy_result(
            policy=policy,
            symbols=symbols,
            base_dir=base_dir,
            initial_equity=args.initial_equity,
        )
        for policy, _desc in POLICIES
    ]

    baseline = next(row for row in rows if row["policy"] == "BASELINE")
    for row in rows:
        row["net_pnl_delta_vs_baseline"] = row["net_pnl"] - baseline["net_pnl"]
        row["pf_delta_vs_baseline"] = row["profit_factor"] - baseline["profit_factor"]
        row["mdd_delta_vs_baseline"] = row["max_drawdown"] - baseline["max_drawdown"]
        row["stop_reduction_vs_baseline"] = baseline["stop_count"] - row["stop_count"]
        row["good_then_stop_reduction_vs_baseline"] = baseline["good_then_stop"] - row["good_then_stop"]

    candidates = [
        row
        for row in rows
        if row["policy"] != "BASELINE"
        and row["profit_factor"] >= 1.2
        and row["net_pnl"] > baseline["net_pnl"]
        and row["max_drawdown"] < baseline["max_drawdown"]
        and row["good_then_stop"] < baseline["good_then_stop"]
    ]
    best = max(candidates, key=lambda row: (row["profit_factor"], row["net_pnl"], -row["max_drawdown"])) if candidates else None

    report = {
        "experiment_setup": {
            "entry_policy": ENTRY_POLICY,
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "symbols": symbols,
            "policies": [{"name": policy, "description": desc} for policy, desc in POLICIES],
        },
        "results": rows,
        "best_policy": best,
    }
    out = json.dumps(report, ensure_ascii=True, indent=2, default=str)
    print(out)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
