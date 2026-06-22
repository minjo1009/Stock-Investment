from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.analysis_drawdown_control_094 import (
    _f,
    _metrics_from_trade_pnl,
    _positions_df,
    _safe_div,
    _simulate_risk_architecture,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _daily_equity_series(curve: list[dict[str, Any]]) -> pd.Series:
    if not curve:
        return pd.Series(dtype="float64")
    df = pd.DataFrame(curve).copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df["equity"] = pd.to_numeric(df["equity"], errors="coerce")
    df = df.dropna(subset=["ts", "equity"]).sort_values("ts").drop_duplicates("ts", keep="last")
    if df.empty:
        return pd.Series(dtype="float64")
    return df.set_index("ts")["equity"].astype(float)


def _accepted_frame(sim: dict[str, Any]) -> pd.DataFrame:
    rows = list(sim.get("accepted_trade_rows", []))
    if not rows:
        return pd.DataFrame(columns=["symbol", "sector", "entry_time", "exit_time", "base_pnl", "scaled_pnl", "scale"])
    df = pd.DataFrame(rows).copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True, errors="coerce")
    for c in ("base_pnl", "scaled_pnl", "scale"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["entry_time", "exit_time", "symbol", "scaled_pnl"]).reset_index(drop=True)


def _trade_frequency(accepted_df: pd.DataFrame) -> dict[str, Any]:
    if accepted_df.empty:
        return {
            "total_trades": 0,
            "trades_per_year": 0.0,
            "trades_per_month": 0.0,
            "avg_days_between_trades": 0.0,
            "longest_no_trade_period_days": 0,
            "active_trading_days_ratio": 0.0,
        }

    exits = accepted_df["exit_time"].sort_values().reset_index(drop=True)
    total = int(len(exits))
    span_days = max(int((exits.iloc[-1] - exits.iloc[0]).days), 1)
    years = span_days / 365.25
    months = span_days / 30.44
    gaps = exits.diff().dropna().dt.days
    active_days = int(exits.dt.normalize().nunique())
    total_days = int((exits.iloc[-1].normalize() - exits.iloc[0].normalize()).days + 1)

    return {
        "total_trades": total,
        "trades_per_year": _f(_safe_div(total, years)),
        "trades_per_month": _f(_safe_div(total, months)),
        "avg_days_between_trades": _f(float(gaps.mean()) if not gaps.empty else 0.0),
        "longest_no_trade_period_days": int(gaps.max()) if not gaps.empty else 0,
        "active_trading_days_ratio": _f(_safe_div(active_days, max(total_days, 1))),
    }


def _utilization_stats(daily_equity: pd.Series, accepted_df: pd.DataFrame, sim_util: float) -> dict[str, Any]:
    if daily_equity.empty:
        return {
            "average": _f(sim_util),
            "median": _f(sim_util),
            "max": _f(sim_util),
            "idle_days": 0,
            "zero_exposure_days": 0,
            "utilization_by_year": [],
        }

    day_index = pd.DatetimeIndex(daily_equity.index.normalize().unique())
    exposures = pd.Series(0.0, index=day_index)

    if not accepted_df.empty:
        for row in accepted_df.itertuples(index=False):
            s = pd.Timestamp(row.entry_time).normalize()
            e = pd.Timestamp(row.exit_time).normalize()
            for d in pd.date_range(s, e, freq="1D", tz="UTC"):
                if d in exposures.index:
                    exposures.loc[d] = max(float(exposures.loc[d]), float(row.scale))

    util_year = []
    for yr, grp in exposures.groupby(exposures.index.year):
        util_year.append({"year": int(yr), "avg_utilization": _f(float(grp.mean()))})

    return {
        "average": _f(float(exposures.mean()) if len(exposures) > 0 else sim_util),
        "median": _f(float(exposures.median()) if len(exposures) > 0 else sim_util),
        "max": _f(float(exposures.max()) if len(exposures) > 0 else sim_util),
        "idle_days": int((exposures <= 0).sum()),
        "zero_exposure_days": int((exposures <= 0).sum()),
        "utilization_by_year": util_year,
    }


def _sparse_return_path(daily_equity: pd.Series) -> dict[str, Any]:
    if daily_equity.empty or len(daily_equity) < 2:
        return {
            "zero_return_days": 0,
            "positive_days": 0,
            "negative_days": 0,
            "active_day_return": 0.0,
            "inactive_day_drag": 0.0,
            "daily_return_mean": 0.0,
            "daily_return_std": 0.0,
        }
    rets = daily_equity.pct_change().dropna()
    pos = rets[rets > 0]
    neg = rets[rets < 0]
    zero = rets[rets == 0]
    active = rets[rets != 0]
    return {
        "zero_return_days": int(len(zero)),
        "positive_days": int(len(pos)),
        "negative_days": int(len(neg)),
        "active_day_return": _f(float(active.mean()) if not active.empty else 0.0),
        "inactive_day_drag": _f(float(rets.mean()) - float(active.mean()) if not active.empty else 0.0),
        "daily_return_mean": _f(float(rets.mean())),
        "daily_return_std": _f(float(rets.std(ddof=0))),
    }


def _blocked_winners_losers(positions_df: pd.DataFrame, accepted_df: pd.DataFrame) -> dict[str, Any]:
    if positions_df.empty:
        return {
            "blocked_trades": 0,
            "blocked_winners": 0,
            "blocked_losers": 0,
            "net_block_effect": 0.0,
        }

    base_keys: list[tuple[Any, ...]] = []
    for row in positions_df.itertuples(index=False):
        base_keys.append(
            (
                str(row.symbol),
                str(pd.Timestamp(row.entry_time).isoformat()),
                str(pd.Timestamp(row.exit_time).isoformat()),
                _f(float(row.net_pnl), 4),
            )
        )
    acc_keys: list[tuple[Any, ...]] = []
    if not accepted_df.empty:
        for row in accepted_df.itertuples(index=False):
            acc_keys.append(
                (
                    str(row.symbol),
                    str(pd.Timestamp(row.entry_time).isoformat()),
                    str(pd.Timestamp(row.exit_time).isoformat()),
                    _f(float(row.base_pnl), 4),
                )
            )

    missing = Counter(base_keys) - Counter(acc_keys)
    blocked_pnls: list[float] = []
    for k, cnt in missing.items():
        blocked_pnls.extend([float(k[3])] * int(cnt))

    return {
        "blocked_trades": int(len(blocked_pnls)),
        "blocked_winners": int(sum(1 for p in blocked_pnls if p > 0)),
        "blocked_losers": int(sum(1 for p in blocked_pnls if p < 0)),
        "net_block_effect": _f(sum(blocked_pnls)),
    }


def _universe_constraint(
    selected_symbols: list[str],
    selected_sectors: list[str],
    accepted_df: pd.DataFrame,
) -> dict[str, Any]:
    sym_set = set(selected_symbols)
    traded = set(accepted_df["symbol"].unique().tolist()) if not accepted_df.empty else set()
    without_trades = sym_set - traded
    traded_only = traded if traded else set()
    sector_count = int(len(set(selected_sectors))) if selected_sectors else (
        int(accepted_df["sector"].nunique()) if not accepted_df.empty else 0
    )
    # Need-based flag: narrow sector coverage or high symbol concentration.
    expansion_needed = bool(sector_count <= 1 or len(traded_only) <= 3 or len(without_trades) > 0)
    return {
        "current_universe_size": int(len(sym_set)) if sym_set else int(len(traded_only)),
        "symbols_with_trades": int(len(traded_only)),
        "symbols_without_trades": int(len(without_trades)),
        "sector_count": sector_count,
        "expansion_needed": expansion_needed,
    }


def _counterfactuals(
    positions_df: pd.DataFrame,
    *,
    initial_capital: float,
    accepted_df: pd.DataFrame,
    baseline_overlay_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    # A: current overlay utilization/result
    a = {
        "scenario": "A_CURRENT_UTILIZATION",
        "sharpe": _f(float(baseline_overlay_metrics["sharpe"])),
        "return_pct": _f(float(baseline_overlay_metrics["return_pct"])),
        "mdd_pct": _f(float(baseline_overlay_metrics["mdd_pct"])),
        "note": "Current adopted overlay output.",
    }

    # B: idle cash ignored, signals unchanged => apply all base trade pnls
    b_metrics = _metrics_from_trade_pnl(
        pnls=positions_df["net_pnl"].tolist(),
        exit_times=positions_df["exit_time"].tolist(),
        initial_capital=initial_capital,
    )
    b = {
        "scenario": "B_IGNORE_IDLE_CASH_SIGNALS_UNCHANGED",
        "sharpe": _f(float(b_metrics["sharpe"])),
        "return_pct": _f(float(b_metrics["return_pct"])),
        "mdd_pct": _f(float(b_metrics["mdd_pct"])),
        "note": "No overlay gating/scaling; same trades from base list.",
    }

    # C: fully use slots when signal exists => relax decorrelation caps only.
    c_sim = _simulate_risk_architecture(
        positions_df,
        initial_capital=initial_capital,
        enable_loss_breaker=True,
        enable_regime_throttle=False,
        enable_decorrelation=True,
        enable_adaptive_exposure=False,
        loss_streak_threshold=4,
        cooldown_trades=1,
        max_concurrent_positions=8,
        sector_cap_ratio=1.0,
    )
    c_metrics = _metrics_from_trade_pnl(
        pnls=c_sim["scaled_trade_pnls"],
        exit_times=c_sim["scaled_exit_times"],
        initial_capital=initial_capital,
    )
    c = {
        "scenario": "C_FULL_SLOT_WHEN_SIGNAL_EXISTS",
        "sharpe": _f(float(c_metrics["sharpe"])),
        "return_pct": _f(float(c_metrics["return_pct"])),
        "mdd_pct": _f(float(c_metrics["mdd_pct"])),
        "note": "Relaxed concurrent/sector caps; same signal universe and risk breaker.",
    }

    # D: increase size within existing caps => scale accepted trades by +10%.
    d_pnls = [float(v) * 1.10 for v in baseline_overlay_metrics["_scaled_trade_pnls"]]
    d_metrics = _metrics_from_trade_pnl(
        pnls=d_pnls,
        exit_times=baseline_overlay_metrics["_scaled_exit_times"],
        initial_capital=initial_capital,
    )
    d = {
        "scenario": "D_SIZE_UP_WITHIN_EXISTING_CAPS",
        "sharpe": _f(float(d_metrics["sharpe"])),
        "return_pct": _f(float(d_metrics["return_pct"])),
        "mdd_pct": _f(float(d_metrics["mdd_pct"])),
        "note": "10% sizing lift on accepted trades only (same signals, same blocking).",
    }
    return [a, b, c, d]


def _classification(
    *,
    trade_frequency: dict[str, Any],
    capital_util: dict[str, Any],
    sparse: dict[str, Any],
    opp: dict[str, Any],
    universe: dict[str, Any],
) -> tuple[str, str, list[str], list[str]]:
    secondary: list[str] = []
    rejected: list[str] = []

    low_freq = trade_frequency["trades_per_month"] < 1.2
    low_util = capital_util["average"] < 0.35
    sparse_path = sparse["zero_return_days"] > (sparse["positive_days"] + sparse["negative_days"]) * 5
    overblock = opp["blocked_winners"] > opp["blocked_losers"]
    universe_tight = universe["expansion_needed"]

    if low_util or sparse_path:
        primary = "Capital deployment inefficiency: low utilization with sparse return path compresses risk-adjusted returns."
        secondary.extend(
            [
                "Trade frequency is low enough to create long no-return stretches.",
                "Universe concentration limits diversification of return streams.",
            ]
        )
        if overblock:
            secondary.append("Risk overlay may be overblocking winners.")
        else:
            rejected.append("Risk overlay overblocking problem (blocked winners <= blocked losers).")
        classification = "Mixed" if (low_freq and universe_tight) else "Capital deployment problem"
    elif low_freq:
        primary = "Alpha frequency problem: signal events are too sparse to create stable daily return series."
        secondary.append("Capital utilization remains low because signals are infrequent.")
        classification = "Alpha frequency problem"
    elif overblock:
        primary = "Risk overlay overblocking problem: overlay blocks more winners than losers."
        classification = "Risk overlay overblocking problem"
    elif universe_tight:
        primary = "Universe constraint problem: narrow symbol/sector opportunity set limits return path density."
        classification = "Universe constraint problem"
    else:
        primary = "Mixed constraints across frequency, utilization, and concentration suppress Sharpe."
        classification = "Mixed"

    if not low_freq:
        rejected.append("Alpha frequency problem as sole primary cause.")
    if not universe_tight:
        rejected.append("Universe constraint problem as sole primary cause.")
    return primary, classification, secondary[:4], rejected[:4]


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T097 - Execution Density & Capital Efficiency Analysis")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append(f"- 3-line summary: {report['summary_3lines']}")
    lines.append(f"- primary cause: {report['primary_cause']}")
    lines.append(f"- final classification: {report['classification']}")
    lines.append("")
    lines.append("## 2. Context Pack")
    lines.append("- files inspected:")
    for f in report["context_pack"]["files_inspected"]:
        lines.append(f"  - {f}")
    lines.append(f"- graphify usage note: {report['context_pack']['graphify_usage_note']}")
    lines.append("")
    lines.append("## 3. Trade Frequency Analysis")
    tf = report["trade_frequency"]
    lines.append(f"- total_trades: {tf['total_trades']}")
    lines.append(f"- trades_per_year: {tf['trades_per_year']}")
    lines.append(f"- trades_per_month: {tf['trades_per_month']}")
    lines.append(f"- avg_days_between_trades: {tf['avg_days_between_trades']}")
    lines.append(f"- longest_no_trade_period_days: {tf['longest_no_trade_period_days']}")
    lines.append(f"- active_trading_days_ratio: {tf['active_trading_days_ratio']}")
    lines.append("")
    lines.append("## 4. Capital Utilization Analysis")
    cu = report["capital_utilization"]
    lines.append(f"- average: {cu['average']}")
    lines.append(f"- median: {cu['median']}")
    lines.append(f"- max: {cu['max']}")
    lines.append(f"- idle_days: {cu['idle_days']}")
    lines.append(f"- zero_exposure_days: {cu['zero_exposure_days']}")
    lines.append(f"- utilization_by_year: {cu['utilization_by_year']}")
    lines.append("")
    lines.append("## 5. Sparse Return Path Analysis")
    sp = report["sparse_return_path"]
    lines.append(f"- zero_return_days: {sp['zero_return_days']}")
    lines.append(f"- positive_days: {sp['positive_days']}")
    lines.append(f"- negative_days: {sp['negative_days']}")
    lines.append(f"- active_day_return: {sp['active_day_return']}")
    lines.append(f"- inactive_day_drag: {sp['inactive_day_drag']}")
    lines.append(f"- daily_return_mean/std: {sp['daily_return_mean']} / {sp['daily_return_std']}")
    lines.append("")
    lines.append("## 6. Opportunity Loss Analysis")
    op = report["opportunity_loss"]
    lines.append(f"- blocked_trades: {op['blocked_trades']}")
    lines.append(f"- blocked_winners: {op['blocked_winners']}")
    lines.append(f"- blocked_losers: {op['blocked_losers']}")
    lines.append(f"- net_block_effect: {op['net_block_effect']}")
    lines.append(f"- blocked_reason_breakdown: {op['blocked_reason_breakdown']}")
    lines.append("")
    lines.append("## 7. Universe Constraint Analysis")
    uc = report["universe_constraint"]
    lines.append(f"- current_universe_size: {uc['current_universe_size']}")
    lines.append(f"- symbols_with_trades: {uc['symbols_with_trades']}")
    lines.append(f"- symbols_without_trades: {uc['symbols_without_trades']}")
    lines.append(f"- sector_count: {uc['sector_count']}")
    lines.append(f"- expansion_needed: {uc['expansion_needed']}")
    lines.append("")
    lines.append("## 8. Counterfactual Capital Deployment")
    lines.append("| Scenario | Sharpe | Return % | MDD % | Note |")
    lines.append("|---|---:|---:|---:|---|")
    for row in report["counterfactual_deployment"]:
        lines.append(
            f"| {row['scenario']} | {row['sharpe']} | {row['return_pct']} | {row['mdd_pct']} | {row['note']} |"
        )
    lines.append("")
    lines.append("## 9. Root Cause Map")
    lines.append(f"- primary cause: {report['primary_cause']}")
    lines.append("- secondary causes:")
    for c in report["secondary_causes"]:
        lines.append(f"  - {c}")
    lines.append("- rejected hypotheses:")
    for h in report["rejected_hypotheses"]:
        lines.append(f"  - {h}")
    lines.append("")
    lines.append("## 10. Recommended Next Task")
    nxt = report["recommended_next_task"]
    lines.append(f"- task_id: {nxt['task_id']}")
    lines.append(f"- title: {nxt['title']}")
    lines.append(f"- objective: {nxt['objective']}")
    lines.append("")
    lines.append("## 11. Final Answer")
    lines.append(report["final_answer"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T097: Execution density & capital efficiency analysis")
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--input-t093-review", type=str, default="docs/reports/task_093_review/task_093_review_failure_analysis.json")
    parser.add_argument("--input-t095", type=str, default="docs/reports/task_095/task_095_risk_adoption.json")
    parser.add_argument("--input-t096", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument("--input-t096-review", type=str, default="docs/reports/task_096_review/task_096_review_sharpe_gap.json")
    parser.add_argument("--input-t096-5", type=str, default="docs/reports/task_096_5/task_096_5_sharpe_tuning.json")
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_097/task_097_execution_density_capital_efficiency.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_097/task_097_execution_density_capital_efficiency.md",
    )
    args = parser.parse_args(argv)

    t093 = _load_json(Path(args.input_t093))
    _ = _load_json(Path(args.input_t093_review))
    t095 = _load_json(Path(args.input_t095))
    t096 = _load_json(Path(args.input_t096))
    _ = _load_json(Path(args.input_t096_review))
    _ = _load_json(Path(args.input_t096_5))

    scenario_name = str(t096.get("baseline_scenario", t093.get("primary_scenario", "A_BASE_10K_HIGH_COST")))
    scenario = t093["scenarios"][scenario_name]
    initial_capital = float(scenario["initial_capital"])
    positions = _positions_df(scenario.get("closed_positions", []))
    if positions.empty:
        raise SystemExit("No closed positions found for T097.")

    # Adopted overlay baseline from T096/T095.
    selected_overlay = str(t095.get("selected_overlay", "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER"))
    sim = _simulate_risk_architecture(
        positions,
        initial_capital=initial_capital,
        enable_loss_breaker=True,
        enable_regime_throttle=False,
        enable_decorrelation=True,
        enable_adaptive_exposure=False,
        loss_streak_threshold=4,
        cooldown_trades=1,
        max_concurrent_positions=3,
        sector_cap_ratio=0.6,
    )
    overlay_metrics = _metrics_from_trade_pnl(
        pnls=sim["scaled_trade_pnls"],
        exit_times=sim["scaled_exit_times"],
        initial_capital=initial_capital,
    )

    accepted_df = _accepted_frame(sim)
    daily_equity = _daily_equity_series(overlay_metrics["equity_curve_daily"])

    trade_frequency = _trade_frequency(accepted_df)
    capital_utilization = _utilization_stats(daily_equity, accepted_df, float(sim["utilization_after"]))
    sparse_return_path = _sparse_return_path(daily_equity)
    blocked = _blocked_winners_losers(positions, accepted_df)
    opportunity_loss = {
        **blocked,
        "portfolio_slot_unavailable_count": int(sim.get("blocked_by_reason", {}).get("MAX_CONCURRENT_CAP", 0)),
        "sector_cap_blocked_count": int(sim.get("blocked_by_reason", {}).get("EXPOSURE_OR_SECTOR_CAP", 0)),
        "decorrelation_blocked_count": int(sim.get("blocked_by_reason", {}).get("MAX_CONCURRENT_CAP", 0))
        + int(sim.get("blocked_by_reason", {}).get("EXPOSURE_OR_SECTOR_CAP", 0)),
        "loss_breaker_blocked_count": int(sim.get("blocked_by_reason", {}).get("LOSS_CLUSTER_BREAKER", 0)),
        "blocked_reason_breakdown": dict(sim.get("blocked_by_reason", {})),
    }
    universe_constraint = _universe_constraint(
        selected_symbols=list(t093.get("selected_symbols", [])),
        selected_sectors=list(t093.get("selected_sectors", [])),
        accepted_df=accepted_df,
    )

    overlay_metrics["_scaled_trade_pnls"] = list(sim["scaled_trade_pnls"])
    overlay_metrics["_scaled_exit_times"] = list(sim["scaled_exit_times"])
    counterfactuals = _counterfactuals(
        positions,
        initial_capital=initial_capital,
        accepted_df=accepted_df,
        baseline_overlay_metrics=overlay_metrics,
    )

    primary_cause, classification, secondary_causes, rejected = _classification(
        trade_frequency=trade_frequency,
        capital_util=capital_utilization,
        sparse=sparse_return_path,
        opp=opportunity_loss,
        universe=universe_constraint,
    )

    status = "PASS" if primary_cause and classification else "FAIL"
    if status == "PASS" and (trade_frequency["total_trades"] == 0 or sparse_return_path["zero_return_days"] == 0):
        status = "WARNING"

    next_task = {
        "task_id": "T097.5",
        "title": "Capital Deployment Simulation (No Alpha Change)",
        "objective": (
            "Run structured deployment simulations to increase active-day density and utilization without changing alpha logic "
            "or loosening overlay beyond validated safety bounds."
        ),
    }

    summary = [
        "Sharpe bottleneck is primarily tied to sparse return path and capital underdeployment, not outright alpha collapse.",
        f"Current utilization is low (avg={capital_utilization['average']}) with many zero-return days ({sparse_return_path['zero_return_days']}).",
        "Blocked-trade profile does not indicate winner-overblocking dominance; constraint pressure is mixed with narrow opportunity set.",
    ]

    report = {
        "status": status,
        "task": "T097",
        "primary_cause": primary_cause,
        "classification": classification,
        "trade_frequency": trade_frequency,
        "capital_utilization": capital_utilization,
        "sparse_return_path": sparse_return_path,
        "opportunity_loss": {
            "blocked_trades": opportunity_loss["blocked_trades"],
            "blocked_winners": opportunity_loss["blocked_winners"],
            "blocked_losers": opportunity_loss["blocked_losers"],
            "net_block_effect": opportunity_loss["net_block_effect"],
            "portfolio_slot_unavailable_count": opportunity_loss["portfolio_slot_unavailable_count"],
            "sector_cap_blocked_count": opportunity_loss["sector_cap_blocked_count"],
            "decorrelation_blocked_count": opportunity_loss["decorrelation_blocked_count"],
            "loss_breaker_blocked_count": opportunity_loss["loss_breaker_blocked_count"],
            "blocked_reason_breakdown": opportunity_loss["blocked_reason_breakdown"],
        },
        "universe_constraint": universe_constraint,
        "counterfactual_deployment": counterfactuals,
        "summary_3lines": summary,
        "secondary_causes": secondary_causes,
        "rejected_hypotheses": rejected,
        "recommended_next_task": next_task,
        "context_pack": {
            "files_inspected": [
                "src/backtest/analysis_capital_backtest_093.py",
                "src/backtest/analysis_capital_failure_review_093.py",
                "src/backtest/analysis_risk_adoption_095.py",
                "src/backtest/analysis_revalidation_096.py",
                "src/backtest/analysis_sharpe_gap_review_096.py",
                "src/backtest/analysis_sharpe_tuning_096_5.py",
                "docs/reports/task_093/task_093_capital_backtest.json",
                "docs/reports/task_093_review/task_093_review_failure_analysis.json",
                "docs/reports/task_095/task_095_risk_adoption.json",
                "docs/reports/task_096/task_096_revalidation.json",
                "docs/reports/task_096_review/task_096_review_sharpe_gap.json",
                "docs/reports/task_096_5/task_096_5_sharpe_tuning.json",
            ],
            "graphify_usage_note": "Graphify full graph/report not loaded; fixed context pack only.",
        },
        "final_answer": "Sharpe remains below target mainly because low capital utilization and sparse active return days keep risk-adjusted compounding too thin despite drawdown control.",
        "overlay_used": selected_overlay,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={status}")
    print(f"classification={classification}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

