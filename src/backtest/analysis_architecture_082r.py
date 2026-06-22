from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analytics.metrics import summarize_portfolio_results
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_universe_daily_bars
from backtest.engine_full import run_full_backtest_universe_with_stats, summarize
from portfolio.allocator import AllocationConfig, allocate_equal_weight
from sector.sector_model import build_sector_snapshot
from universe.ranking import rank_universe
from universe.universe_selector import build_universe_snapshot, filter_universe_snapshot


def _round(value: float, digits: int = 6) -> float:
    return float(round(float(value), digits))


def _summary_dict(summary: Any) -> dict[str, float | int]:
    return {
        "trade_count": int(summary.trade_count),
        "total_pnl": _round(summary.total_pnl),
        "net_pnl": _round(summary.net_pnl),
        "win_rate": _round(summary.win_rate),
        "profit_factor": _round(summary.profit_factor),
        "max_drawdown": _round(summary.max_drawdown),
        "sharpe_ratio": _round(summary.sharpe_ratio),
    }


def _stats_dict(stats: Any) -> dict[str, float | int]:
    return {
        "total_signals": int(stats.total_signals),
        "entry_filled": int(stats.entry_filled),
        "entry_expired": int(stats.entry_expired),
        "fill_rate": _round(stats.fill_rate),
        "expired_rate": _round(stats.expired_rate),
        "missed_trades": int(stats.missed_trades),
        "big_miss_count": int(stats.big_miss_count),
        "skipped_by_gate": int(stats.skipped_by_gate),
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 082-R - Research Platform Re-baseline")
    lines.append("")
    lines.append("## Universe Snapshot")
    lines.append("| Symbol | AvgDollarVolume | Volatility | Momentum20d |")
    lines.append("|---|---:|---:|---:|")
    for row in payload["universe_snapshot"]:
        lines.append(
            f"| {row['symbol']} | {row['avg_dollar_volume']:.2f} | {row['volatility']:.6f} | {row['momentum']:.6f} |"
        )

    lines.append("")
    lines.append("## Sector Strength")
    lines.append("| Sector | Strength | Rank | Momentum20d | Volatility |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in payload["sector_strength"]:
        lines.append(
            f"| {row['sector']} | {row['strength_score']:.6f} | {row['sector_strength_rank']} | "
            f"{row['sector_return_20d']:.6f} | {row['sector_volatility']:.6f} |"
        )

    lines.append("")
    lines.append("## Ranked Symbols")
    lines.append("| Rank | Symbol | Score | MomentumRank | VolumeRank | VolPenalty |")
    lines.append("|---:|---|---:|---:|---:|---:|")
    for idx, row in enumerate(payload["ranking"], start=1):
        lines.append(
            f"| {idx} | {row['symbol']} | {row['score']:.6f} | {row['momentum_rank']:.4f} | "
            f"{row['volume_rank']:.4f} | {row['volatility_penalty']:.4f} |"
        )

    lines.append("")
    lines.append("## Portfolio Allocation Example")
    lines.append("| Symbol | AllocationPct |")
    lines.append("|---|---:|")
    for row in payload["portfolio_allocation"]:
        lines.append(f"| {row['symbol']} | {row['allocation_pct']:.4f} |")

    lines.append("")
    lines.append("## Backtest Comparison (S4)")
    lines.append("| Mode | Trades | PF | NetPnL | MDD | Sharpe | FillRate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in payload["comparison"]:
        lines.append(
            f"| {row['mode']} | {row['trade_count']} | {row['profit_factor']:.6f} | {row['net_pnl']:.4f} | "
            f"{row['max_drawdown']:.4f} | {row['sharpe_ratio']:.6f} | {row['fill_rate']:.4f} |"
        )

    lines.append("")
    lines.append("## Validation")
    for item in payload["validation"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(f"**Critical Answer:** {payload['critical_answer']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task 082-R architecture baseline report")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--fee-rate", type=float, default=0.0025)
    parser.add_argument("--slippage-rate", type=float, default=0.0010)
    parser.add_argument("--entry-policy", type=str, default="LIMITED_CHASE")
    parser.add_argument("--risk-policy", type=str, default="TIME_STOP")
    parser.add_argument("--max-positions", type=int, default=3)
    parser.add_argument("--json-out", type=str, default="docs/reports/task_082R/task_082R_architecture.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_082R/task_082R_architecture.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    frames = load_universe_daily_bars(symbols, base_dir=args.data_dir)
    universe_snapshot_df = build_universe_snapshot(frames)
    filtered_df = filter_universe_snapshot(universe_snapshot_df)
    ranked_df = rank_universe(filtered_df)
    top_symbols = ranked_df["symbol"].head(max(1, int(args.max_positions))).tolist() if not ranked_df.empty else symbols[: args.max_positions]
    allocation = allocate_equal_weight(top_symbols, config=AllocationConfig(max_positions=args.max_positions))

    sector_snapshot = build_sector_snapshot(frames)
    sector_rows = []
    for sector, values in sorted(
        sector_snapshot.items(),
        key=lambda item: (int(item[1].get("sector_strength_rank", 999)), item[0]),
    ):
        sector_rows.append({"sector": sector, **values})

    risk_policy = "TIME_STOP" if str(args.risk_policy).strip().upper() == "TIME_STOP_ONLY" else str(args.risk_policy).strip().upper()

    single_results, single_stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=args.data_dir,
        initial_equity=args.initial_equity,
        fee_rate=args.fee_rate,
        slippage_rate=args.slippage_rate,
        entry_policy=args.entry_policy,
        risk_policy=risk_policy,
        mode="single_symbol",
        max_positions=args.max_positions,
    )
    portfolio_results, portfolio_stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=args.data_dir,
        initial_equity=args.initial_equity,
        fee_rate=args.fee_rate,
        slippage_rate=args.slippage_rate,
        entry_policy=args.entry_policy,
        risk_policy=risk_policy,
        mode="portfolio",
        max_positions=args.max_positions,
    )

    single_summary = summarize(single_results, initial_equity=args.initial_equity)
    portfolio_summary = summarize(portfolio_results, initial_equity=args.initial_equity)
    portfolio_metrics = summarize_portfolio_results(
        portfolio_results,
        initial_equity=args.initial_equity,
        max_positions=args.max_positions,
    )

    comparison = [
        {**_summary_dict(single_summary), "mode": "single_symbol", "fill_rate": _round(single_stats.fill_rate)},
        {**_summary_dict(portfolio_summary), "mode": "portfolio", "fill_rate": _round(portfolio_stats.fill_rate)},
    ]

    validation = [
        f"single_mode_trade_count={single_summary.trade_count}",
        f"portfolio_mode_trade_count={portfolio_summary.trade_count}",
        f"portfolio_mode_has_position={'yes' if portfolio_summary.trade_count > 0 else 'no'}",
    ]
    critical_answer = "YES" if portfolio_summary.trade_count > 0 else "NO"

    payload: dict[str, Any] = {
        "task": "082-R",
        "objective": "Research Platform Re-baseline (Universe/Sector/Portfolio Layer)",
        "inputs": {
            "symbols": symbols,
            "data_dir": str(args.data_dir),
            "entry_policy": args.entry_policy,
            "risk_policy": risk_policy,
            "fee_rate": args.fee_rate,
            "slippage_rate": args.slippage_rate,
            "max_positions": args.max_positions,
        },
        "universe_snapshot": universe_snapshot_df.to_dict(orient="records"),
        "sector_strength": sector_rows,
        "ranking": ranked_df.to_dict(orient="records"),
        "portfolio_allocation": allocation,
        "comparison": comparison,
        "portfolio_metrics": {
            "capital_utilization": _round(portfolio_metrics.capital_utilization),
            "max_exposure": _round(portfolio_metrics.max_exposure),
            "trade_count": int(portfolio_metrics.trade_count),
            "net_pnl": _round(portfolio_metrics.net_pnl),
            "max_drawdown": _round(portfolio_metrics.max_drawdown),
            "sharpe_ratio": _round(portfolio_metrics.sharpe_ratio),
        },
        "execution_stats": {
            "single_symbol": _stats_dict(single_stats),
            "portfolio": _stats_dict(portfolio_stats),
        },
        "validation": validation,
        "critical_answer": critical_answer,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(payload), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"critical_answer={critical_answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
