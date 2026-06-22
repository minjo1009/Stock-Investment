from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from analytics.metrics import summarize_portfolio_results
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_universe_daily_bars
from backtest.engine_full import FullTradeResult, run_full_backtest_universe_with_stats, summarize
from sector.sector_model import build_sector_snapshot, map_symbol_to_sector


S4_FEE_RATE = 0.0025
S4_SLIPPAGE_RATE = 0.0010


def _float(v: float, digits: int = 6) -> float:
    return float(round(float(v), digits))


def _trades_frame(results: list[FullTradeResult]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in results:
        meta = item.metadata or {}
        exit_time = item.trade.exit_time or item.trade.entry_time
        rows.append(
            {
                "trade_id": item.trade.trade_id,
                "symbol": item.trade.symbol,
                "entry_time": item.trade.entry_time,
                "exit_time": exit_time,
                "net_pnl": float(item.net_pnl),
                "quantity": float(item.trade.quantity),
                "entry_fill_price": float(item.trade.entry_fill_price or item.trade.entry_price),
                "sector": str(meta.get("sector") or map_symbol_to_sector(item.trade.symbol)),
                "exit_rule": str(meta.get("exit_rule") or "UNKNOWN"),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=["trade_id", "symbol", "entry_time", "exit_time", "net_pnl", "quantity", "entry_fill_price", "sector", "exit_rule"]
        )
    return pd.DataFrame(rows).sort_values("exit_time").reset_index(drop=True)


def _compute_avg_concurrent_positions(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    events: list[tuple[pd.Timestamp, int]] = []
    for row in df.itertuples(index=False):
        entry_ts = pd.Timestamp(row.entry_time)
        exit_ts = pd.Timestamp(row.exit_time)
        events.append((entry_ts, +1))
        events.append((exit_ts, -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    running = 0
    samples: list[int] = []
    for _ts, delta in events:
        running += delta
        running = max(running, 0)
        samples.append(running)
    if not samples:
        return 0.0
    return float(statistics.fmean(samples))


def _compute_exposure_variance(df: pd.DataFrame, *, initial_equity: float, max_positions: int) -> float:
    if df.empty:
        return 0.0
    total_capital = float(initial_equity) * float(max(max_positions, 1))
    exposures = ((df["entry_fill_price"] * df["quantity"]) / total_capital).astype(float).tolist()
    if len(exposures) < 2:
        return 0.0
    return float(statistics.pvariance(exposures))


def _symbol_contribution(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"top": [], "worst": [], "distribution": []}
    grouped = (
        df.groupby("symbol", as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), trades=("trade_id", "count"))
        .sort_values("net_pnl", ascending=False)
        .reset_index(drop=True)
    )
    top = grouped.head(5).to_dict(orient="records")
    worst = grouped.tail(5).sort_values("net_pnl", ascending=True).to_dict(orient="records")
    distribution = grouped.sort_values("trades", ascending=False).to_dict(orient="records")
    return {"top": top, "worst": worst, "distribution": distribution}


def _sector_contribution(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    grouped = (
        df.groupby("sector", as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), trades=("trade_id", "count"))
        .sort_values("net_pnl", ascending=False)
        .reset_index(drop=True)
    )
    return grouped.to_dict(orient="records")


def _exit_type(rule: str) -> str:
    text = str(rule).upper()
    if "STOP" in text:
        return "STOP"
    if "TIME" in text:
        return "TIME"
    if "TREND" in text:
        return "TREND"
    return "OTHER"


def _drawdown_attribution(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "worst_period": None,
            "max_drawdown": 0.0,
            "top_symbol_losses": [],
            "exit_type_breakdown": [],
        }
    work = df.copy().sort_values("exit_time").reset_index(drop=True)
    work["equity"] = work["net_pnl"].cumsum()
    work["peak"] = work["equity"].cummax()
    work["drawdown"] = work["peak"] - work["equity"]
    trough_idx = int(work["drawdown"].idxmax())
    peak_val = float(work.loc[trough_idx, "peak"])
    prior = work.loc[:trough_idx]
    peak_idx = int(prior[prior["equity"] == peak_val].index[0]) if not prior.empty else 0
    segment = work.loc[peak_idx : trough_idx].copy()

    loss_contrib = (
        segment.groupby("symbol", as_index=False)["net_pnl"]
        .sum()
        .sort_values("net_pnl", ascending=True)
        .head(5)
        .to_dict(orient="records")
    )
    segment["exit_type"] = segment["exit_rule"].map(_exit_type)
    exit_breakdown = (
        segment.groupby("exit_type", as_index=False)
        .agg(trades=("trade_id", "count"), net_pnl=("net_pnl", "sum"))
        .sort_values("net_pnl", ascending=True)
        .to_dict(orient="records")
    )
    return {
        "worst_period": {
            "start": str(pd.Timestamp(work.loc[peak_idx, "exit_time"]).isoformat()),
            "end": str(pd.Timestamp(work.loc[trough_idx, "exit_time"]).isoformat()),
        },
        "max_drawdown": _float(work["drawdown"].max()),
        "top_symbol_losses": loss_contrib,
        "exit_type_breakdown": exit_breakdown,
    }


def _mode_status(*, baseline: dict[str, float], current: dict[str, float]) -> str:
    if (
        float(current["profit_factor"]) >= float(baseline["profit_factor"])
        and float(current["max_drawdown"]) <= float(baseline["max_drawdown"])
        and float(current["sharpe_ratio"]) >= float(baseline["sharpe_ratio"])
    ):
        return "PASS"
    if float(current["profit_factor"]) >= 1.0:
        return "WARNING"
    return "FAIL"


def _overall_answer(statuses: list[str]) -> str:
    if any(s == "PASS" for s in statuses):
        return "YES"
    if any(s == "WARNING" for s in statuses):
        return "WARNING"
    return "NO"


def _run_mode(
    *,
    mode_name: str,
    symbols: list[str],
    base_dir: str | Path,
    initial_equity: float,
    entry_policy: str,
    risk_policy: str,
    mode: str,
    max_positions: int,
) -> dict[str, Any]:
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=S4_FEE_RATE,
        slippage_rate=S4_SLIPPAGE_RATE,
        entry_policy=entry_policy,
        risk_policy=risk_policy,
        mode=mode,
        max_positions=max_positions,
    )
    summary = summarize(results, initial_equity=initial_equity)
    psummary = summarize_portfolio_results(results, initial_equity=initial_equity, max_positions=max_positions)
    df = _trades_frame(results)

    metrics = {
        "trade_count": int(summary.trade_count),
        "net_pnl": _float(summary.net_pnl),
        "profit_factor": _float(summary.profit_factor),
        "win_rate": _float(summary.win_rate),
        "max_drawdown": _float(summary.max_drawdown),
        "sharpe_ratio": _float(summary.sharpe_ratio),
        "capital_utilization": _float(psummary.capital_utilization),
        "average_concurrent_positions": _float(_compute_avg_concurrent_positions(df)),
        "exposure_variance": _float(_compute_exposure_variance(df, initial_equity=initial_equity, max_positions=max_positions)),
    }
    return {
        "mode_name": mode_name,
        "params": {"mode": mode, "max_positions": max_positions, "symbols": symbols},
        "metrics": metrics,
        "execution_stats": {
            "fill_rate": _float(stats.fill_rate),
            "expired_rate": _float(stats.expired_rate),
            "total_signals": int(stats.total_signals),
            "entry_filled": int(stats.entry_filled),
        },
        "symbol_contribution": _symbol_contribution(df),
        "sector_contribution": _sector_contribution(df),
        "drawdown_attribution": _drawdown_attribution(df),
    }


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 083 - Portfolio Mode Validation & Attribution")
    lines.append("")
    lines.append("## Summary Table")
    lines.append("| Mode | Trades | PF | NetPnL | MDD | Sharpe | WinRate | FillRate | CapUtil | AvgConcPos | ExpVar | Status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in payload["summary_table"]:
        lines.append(
            f"| {row['mode']} | {row['trade_count']} | {row['profit_factor']:.6f} | {row['net_pnl']:.4f} | "
            f"{row['max_drawdown']:.4f} | {row['sharpe_ratio']:.6f} | {row['win_rate']:.2f}% | "
            f"{row['fill_rate']:.2f}% | {row['capital_utilization']:.6f} | {row['average_concurrent_positions']:.6f} | "
            f"{row['exposure_variance']:.6f} | {row['status']} |"
        )

    lines.append("")
    lines.append("## Baseline vs Portfolio Comparison")
    for comp in payload["baseline_comparison"]:
        lines.append(
            f"- {comp['mode']}: PF {comp['pf_delta']:+.6f}, NetPnL {comp['net_pnl_delta']:+.4f}, "
            f"MDD {comp['mdd_delta']:+.4f}, Sharpe {comp['sharpe_delta']:+.6f}"
        )

    lines.append("")
    lines.append("## Symbol Contribution (Top/Worst)")
    for mode_name, data in payload["symbol_contribution"].items():
        lines.append(f"### {mode_name}")
        lines.append("- Top:")
        for row in data.get("top", []):
            lines.append(f"  - {row['symbol']}: net_pnl={row['net_pnl']:.4f}, trades={row['trades']}")
        lines.append("- Worst:")
        for row in data.get("worst", []):
            lines.append(f"  - {row['symbol']}: net_pnl={row['net_pnl']:.4f}, trades={row['trades']}")

    lines.append("")
    lines.append("## Sector Contribution")
    for mode_name, rows in payload["sector_contribution"].items():
        lines.append(f"### {mode_name}")
        for row in rows:
            lines.append(f"- {row['sector']}: net_pnl={row['net_pnl']:.4f}, trades={row['trades']}")

    lines.append("")
    lines.append("## Drawdown Attribution")
    for mode_name, dd in payload["drawdown_attribution"].items():
        lines.append(f"### {mode_name}")
        lines.append(f"- max_drawdown: {dd['max_drawdown']:.4f}")
        lines.append(f"- worst_period: {dd['worst_period']}")
        lines.append(f"- top_symbol_losses: {dd['top_symbol_losses']}")
        lines.append(f"- exit_type_breakdown: {dd['exit_type_breakdown']}")

    lines.append("")
    lines.append("## Capital Utilization")
    for row in payload["summary_table"]:
        lines.append(
            f"- {row['mode']}: utilization={row['capital_utilization']:.6f}, avg_concurrent={row['average_concurrent_positions']:.6f}"
        )

    lines.append("")
    lines.append("## Failure Analysis")
    for item in payload["failure_analysis"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Final Decision")
    lines.append(f"- overall: {payload['final_decision']}")
    lines.append(f"- critical answer: {payload['critical_answer']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task 083: Portfolio mode validation and attribution")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--entry-policy", type=str, default="LIMITED_CHASE")
    parser.add_argument("--risk-policy", type=str, default="TIME_STOP_ONLY")
    parser.add_argument("--top-sectors", type=int, default=2)
    parser.add_argument("--json-out", type=str, default="docs/reports/task_083/task_083_portfolio_validation.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_083/task_083_portfolio_validation.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    frames = load_universe_daily_bars(symbols, base_dir=args.data_dir)
    sector_snapshot = build_sector_snapshot(frames)
    ranked_sectors = sorted(
        sector_snapshot.items(),
        key=lambda item: float(item[1].get("strength_score", 0.0)),
        reverse=True,
    )
    allowed_sectors = {name for name, _ in ranked_sectors[: max(1, int(args.top_sectors))]}
    sector_symbols = [s for s in symbols if map_symbol_to_sector(s) in allowed_sectors]
    if not sector_symbols:
        sector_symbols = symbols

    modes = [
        ("A_BASELINE_SINGLE", "single_symbol", 1, symbols),
        ("B_PORTFOLIO_TOP3", "portfolio", 3, symbols),
        ("C_PORTFOLIO_TOP5", "portfolio", 5, symbols),
        ("D_PORTFOLIO_SECTOR_FILTER", "portfolio", 3, sector_symbols),
    ]
    outputs: dict[str, dict[str, Any]] = {}
    for mode_name, mode, max_positions, mode_symbols in modes:
        outputs[mode_name] = _run_mode(
            mode_name=mode_name,
            symbols=mode_symbols,
            base_dir=args.data_dir,
            initial_equity=args.initial_equity,
            entry_policy=args.entry_policy,
            risk_policy=args.risk_policy,
            mode=mode,
            max_positions=max_positions,
        )

    baseline_metrics = outputs["A_BASELINE_SINGLE"]["metrics"]
    summary_table: list[dict[str, Any]] = []
    baseline_comparison: list[dict[str, Any]] = []
    decisions: dict[str, str] = {}
    for mode_name, payload in outputs.items():
        metrics = payload["metrics"]
        status = _mode_status(baseline=baseline_metrics, current=metrics)
        decisions[mode_name] = status
        row = {
            "mode": mode_name,
            "status": status,
            **metrics,
            "fill_rate": payload["execution_stats"]["fill_rate"],
        }
        summary_table.append(row)
        if mode_name != "A_BASELINE_SINGLE":
            baseline_comparison.append(
                {
                    "mode": mode_name,
                    "pf_delta": _float(metrics["profit_factor"] - baseline_metrics["profit_factor"]),
                    "net_pnl_delta": _float(metrics["net_pnl"] - baseline_metrics["net_pnl"]),
                    "mdd_delta": _float(metrics["max_drawdown"] - baseline_metrics["max_drawdown"]),
                    "sharpe_delta": _float(metrics["sharpe_ratio"] - baseline_metrics["sharpe_ratio"]),
                }
            )

    failure_analysis: list[str] = []
    for item in baseline_comparison:
        mode = item["mode"]
        if item["pf_delta"] < 0:
            failure_analysis.append(f"{mode}: PF declined vs baseline; ranking/diversification may be diluting edge.")
        if item["net_pnl_delta"] < 0:
            failure_analysis.append(f"{mode}: NetPnL declined; capital spread likely reduced high-conviction exposure.")
        if item["mdd_delta"] > 0:
            failure_analysis.append(f"{mode}: MDD increased; diversification did not reduce drawdown in this config.")
        if item["sharpe_delta"] < 0:
            failure_analysis.append(f"{mode}: Sharpe declined; risk-adjusted return is weaker than baseline.")
    if not failure_analysis:
        failure_analysis.append("No dominant failure signal detected against baseline in configured modes.")

    statuses = [decisions[key] for key in decisions if key != "A_BASELINE_SINGLE"]
    final_decision = "PASS" if any(s == "PASS" for s in statuses) else ("WARNING" if any(s == "WARNING" for s in statuses) else "FAIL")
    critical_answer = _overall_answer(statuses)

    report = {
        "task": "083",
        "config": {
            "symbols": symbols,
            "data_dir": str(args.data_dir),
            "entry_policy": args.entry_policy,
            "risk_policy": args.risk_policy,
            "cost_scenario": "S4_KIS_REALISTIC",
            "fee_rate": S4_FEE_RATE,
            "slippage_rate": S4_SLIPPAGE_RATE,
            "top_sectors": int(args.top_sectors),
            "allowed_sectors_for_mode_d": sorted(allowed_sectors),
        },
        "summary_table": summary_table,
        "baseline_comparison": baseline_comparison,
        "symbol_contribution": {k: v["symbol_contribution"] for k, v in outputs.items()},
        "sector_contribution": {k: v["sector_contribution"] for k, v in outputs.items()},
        "drawdown_attribution": {k: v["drawdown_attribution"] for k, v in outputs.items()},
        "capital_utilization": {
            k: {
                "capital_utilization": v["metrics"]["capital_utilization"],
                "average_concurrent_positions": v["metrics"]["average_concurrent_positions"],
                "exposure_variance": v["metrics"]["exposure_variance"],
            }
            for k, v in outputs.items()
        },
        "failure_analysis": failure_analysis,
        "final_decision": final_decision,
        "mode_decisions": decisions,
        "critical_answer": critical_answer,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_to_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"final_decision={final_decision}")
    print(f"critical_answer={critical_answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
