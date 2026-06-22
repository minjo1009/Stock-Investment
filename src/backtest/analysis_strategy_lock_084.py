from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

import pandas as pd

from analytics.metrics import summarize_portfolio_results
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_universe_daily_bars
from backtest.engine_full import FullTradeResult, run_full_backtest_universe_with_stats, summarize
from sector.sector_model import build_sector_snapshot, map_symbol_to_sector


SCENARIOS = [
    ("S1_ZERO_COST", 0.0, 0.0),
    ("S2_LOW_COST", 0.0005, 0.0005),
    ("S3_MEDIUM_COST", 0.0010, 0.0005),
    ("S4_KIS_REALISTIC", 0.0025, 0.0010),
    ("S5_KIS_STRESS_20", 0.0025, 0.0020),
    ("S6_KIS_STRESS_30", 0.0025, 0.0030),
]

STRATEGY_ID = "D_PORTFOLIO_SECTOR_FILTER"


def _f(value: float, digits: int = 6) -> float:
    return float(round(float(value), digits))


def _trade_frame(results: list[FullTradeResult]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in results:
        meta = item.metadata or {}
        rows.append(
            {
                "trade_id": item.trade.trade_id,
                "symbol": item.trade.symbol,
                "sector": str(meta.get("sector") or map_symbol_to_sector(item.trade.symbol)),
                "entry_time": pd.Timestamp(item.trade.entry_time),
                "exit_time": pd.Timestamp(item.trade.exit_time or item.trade.entry_time),
                "net_pnl": float(item.net_pnl),
                "slippage": float(item.trade.slippage) if item.trade.slippage is not None else 0.0,
                "entry_fill_price": float(item.trade.entry_fill_price or item.trade.entry_price),
                "quantity": float(item.trade.quantity),
                "exit_rule": str(meta.get("exit_rule", "UNKNOWN")),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "trade_id",
                "symbol",
                "sector",
                "entry_time",
                "exit_time",
                "net_pnl",
                "slippage",
                "entry_fill_price",
                "quantity",
                "exit_rule",
            ]
        )
    return pd.DataFrame(rows).sort_values("exit_time").reset_index(drop=True)


def _avg_concurrent_positions(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    events: list[tuple[pd.Timestamp, int]] = []
    for row in df.itertuples(index=False):
        events.append((pd.Timestamp(row.entry_time), +1))
        events.append((pd.Timestamp(row.exit_time), -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    running = 0
    values: list[int] = []
    for _ts, delta in events:
        running = max(0, running + delta)
        values.append(running)
    return float(statistics.fmean(values)) if values else 0.0


def _max_concurrent_positions(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    events: list[tuple[pd.Timestamp, int]] = []
    for row in df.itertuples(index=False):
        events.append((pd.Timestamp(row.entry_time), +1))
        events.append((pd.Timestamp(row.exit_time), -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    running = 0
    peak = 0
    for _ts, delta in events:
        running = max(0, running + delta)
        peak = max(peak, running)
    return int(peak)


def _exposure_variance(df: pd.DataFrame, *, initial_equity: float, max_positions: int) -> float:
    if df.empty:
        return 0.0
    total_capital = float(initial_equity) * float(max(max_positions, 1))
    exposures = ((df["entry_fill_price"] * df["quantity"]) / total_capital).astype(float).tolist()
    return float(statistics.pvariance(exposures)) if len(exposures) >= 2 else 0.0


def _symbol_contrib(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["symbol", "net_pnl", "trades"])
    return (
        df.groupby("symbol", as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), trades=("trade_id", "count"))
        .sort_values("net_pnl", ascending=False)
        .reset_index(drop=True)
    )


def _sector_contrib(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["sector", "net_pnl", "trades"])
    return (
        df.groupby("sector", as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), trades=("trade_id", "count"))
        .sort_values("net_pnl", ascending=False)
        .reset_index(drop=True)
    )


def _exit_type(exit_rule: str) -> str:
    t = str(exit_rule).upper()
    if "STOP" in t:
        return "STOP"
    if "TIME" in t:
        return "TIME"
    if "TREND" in t:
        return "TREND"
    return "OTHER"


def _drawdown_analysis(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "period": None,
            "drawdown": 0.0,
            "top_symbol_losses": [],
            "top_sector_losses": [],
            "exit_type_breakdown": [],
        }
    work = df.copy().sort_values("exit_time").reset_index(drop=True)
    work["equity"] = work["net_pnl"].cumsum()
    work["peak"] = work["equity"].cummax()
    work["drawdown"] = work["peak"] - work["equity"]
    trough_idx = int(work["drawdown"].idxmax())
    peak_val = float(work.loc[trough_idx, "peak"])
    peak_idx = int(work.loc[:trough_idx][work.loc[:trough_idx, "equity"] == peak_val].index[0])
    segment = work.loc[peak_idx:trough_idx].copy()
    segment["exit_type"] = segment["exit_rule"].map(_exit_type)

    sym = (
        segment.groupby("symbol", as_index=False)["net_pnl"]
        .sum()
        .sort_values("net_pnl", ascending=True)
        .head(5)
        .to_dict(orient="records")
    )
    sec = (
        segment.groupby("sector", as_index=False)["net_pnl"]
        .sum()
        .sort_values("net_pnl", ascending=True)
        .head(5)
        .to_dict(orient="records")
    )
    exit_breakdown = (
        segment.groupby("exit_type", as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), trades=("trade_id", "count"))
        .sort_values("net_pnl", ascending=True)
        .to_dict(orient="records")
    )
    return {
        "period": {
            "start": str(pd.Timestamp(work.loc[peak_idx, "exit_time"]).isoformat()),
            "end": str(pd.Timestamp(work.loc[trough_idx, "exit_time"]).isoformat()),
        },
        "drawdown": _f(work["drawdown"].max()),
        "top_symbol_losses": sym,
        "top_sector_losses": sec,
        "exit_type_breakdown": exit_breakdown,
    }


def _loss_streak(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    streak = 0
    best = 0
    for pnl in df.sort_values("exit_time")["net_pnl"].tolist():
        if pnl < 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return int(best)


def _worst_day_loss(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    work = df.copy()
    work["date"] = pd.to_datetime(work["exit_time"], utc=True, errors="coerce").dt.date
    daily = work.groupby("date", as_index=False)["net_pnl"].sum()
    return _f(daily["net_pnl"].min()) if not daily.empty else 0.0


def _concentration(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "top3_symbol_share_abs": 0.0,
            "top_sector_share_abs": 0.0,
            "symbol_risk": False,
            "sector_risk": False,
        }
    sym = _symbol_contrib(df)
    sec = _sector_contrib(df)
    abs_total = float(df["net_pnl"].abs().sum()) or 1.0
    top3_symbol_share = float(sym["net_pnl"].abs().head(3).sum() / abs_total)
    top_sector_share = float(sec["net_pnl"].abs().head(1).sum() / abs_total)
    return {
        "top3_symbol_share_abs": _f(top3_symbol_share),
        "top_sector_share_abs": _f(top_sector_share),
        "symbol_risk": top3_symbol_share > 0.40,
        "sector_risk": top_sector_share > 0.60,
    }


def _pilot_gate(s4: dict[str, Any], concentration: dict[str, Any]) -> dict[str, Any]:
    pf = float(s4["profit_factor"])
    sharpe = float(s4["sharpe"])
    net = float(s4["net_pnl"])
    mdd = float(s4["max_drawdown"])
    no_concentration = not bool(concentration["symbol_risk"] or concentration["sector_risk"])

    pass_cond = pf >= 1.2 and sharpe >= 1.0 and (mdd <= net * 0.60 if net > 0 else False) and no_concentration
    warn_cond = pf >= 1.0
    if pass_cond:
        status = "PASS"
    elif warn_cond:
        status = "WARNING"
    else:
        status = "FAIL"
    return {
        "status": status,
        "pf_ok": pf >= 1.2,
        "sharpe_ok": sharpe >= 1.0,
        "mdd_ok": (mdd <= net * 0.60) if net > 0 else False,
        "concentration_ok": no_concentration,
        "mdd_to_net_pct": _f((mdd / net) * 100.0) if net > 0 else None,
    }


def _failure_mode(
    *,
    scenarios: dict[str, dict[str, Any]],
    concentration: dict[str, Any],
    trade_quality_s4: dict[str, Any],
) -> dict[str, Any]:
    s4 = scenarios["S4_KIS_REALISTIC"]
    s6 = scenarios["S6_KIS_STRESS_30"]
    reasons: list[str] = []
    code = "B"
    label = "strategy weakness"

    if concentration["sector_risk"] or concentration["symbol_risk"]:
        code, label = "C", "sector concentration"
        reasons.append("Concentration threshold exceeded in symbol/sector attribution.")
    elif float(trade_quality_s4["fill_rate"]) < 50.0 or float(trade_quality_s4["missed_trade_ratio"]) > 45.0:
        code, label = "A", "execution failure"
        reasons.append("Low fill rate or high missed-trade ratio on S4.")
    elif float(s6["profit_factor"]) < 1.0 and float(s4["profit_factor"]) >= 1.0:
        code, label = "D", "volatility regime dependency"
        reasons.append("Performance deteriorates sharply in stress scenario S6.")
    elif int(s4["trades"]) > 220:
        code, label = "E", "overtrading"
        reasons.append("Trade count indicates potential overtrading pressure.")
    else:
        reasons.append("Primary weakness appears in baseline edge retention under costs.")

    return {"code": code, "label": label, "reasons": reasons}


def _pilot_conditions(status: str, s4: dict[str, Any]) -> dict[str, Any]:
    if status == "FAIL":
        return {"enabled": False, "reason": "Gate failed; pilot blocked."}
    net = max(float(s4["net_pnl"]), 1.0)
    return {
        "enabled": True,
        "max_positions": 3,
        "max_notional_per_trade": 0.30,
        "daily_loss_limit_pct": 0.75 if status == "PASS" else 0.50,
        "kill_switch": [
            "UNKNOWN order detected",
            "reconciliation critical mismatch",
            "consecutive cancel loop UNKNOWN",
        ],
        "stop_trading_conditions": [
            "realized day loss exceeds daily limit",
            "rolling PF below 1.0 for 20 trades",
            f"MDD exceeds { _f((float(s4['max_drawdown']) / net) * 100.0) }% of S4 net reference",
        ],
    }


def _run_scenario(
    *,
    symbols: list[str],
    data_dir: Path,
    initial_equity: float,
    entry_policy: str,
    risk_policy: str,
    max_positions: int,
    fee_rate: float,
    slippage_rate: float,
) -> tuple[dict[str, Any], list[FullTradeResult], Any]:
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=data_dir,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        entry_policy=entry_policy,
        risk_policy=risk_policy,
        mode="portfolio",
        max_positions=max_positions,
    )
    summary = summarize(results, initial_equity=initial_equity)
    return (
        {
            "trades": int(summary.trade_count),
            "profit_factor": _f(summary.profit_factor),
            "net_pnl": _f(summary.net_pnl),
            "max_drawdown": _f(summary.max_drawdown),
            "sharpe": _f(summary.sharpe_ratio),
            "win_rate": _f(summary.win_rate),
            "fill_rate": _f(stats.fill_rate),
            "expired_rate": _f(stats.expired_rate),
            "missed_trades": int(stats.missed_trades),
            "big_miss_count": int(stats.big_miss_count),
        },
        results,
        stats,
    )


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 084 - Portfolio Strategy Lock & Paper Pilot Readiness")
    lines.append("")
    lines.append("## 1. Strategy Summary")
    lines.append(f"- strategy_id: {report['strategy_summary']['strategy_id']}")
    lines.append(f"- execution: {report['strategy_summary']['execution_policy']}")
    lines.append(f"- risk: {report['strategy_summary']['risk_policy']}")
    lines.append(f"- max_positions: {report['strategy_summary']['max_positions']}")
    lines.append(f"- sector_filter: {', '.join(report['strategy_summary']['allowed_sectors'])}")
    lines.append("")
    lines.append("## 2. Cost Sensitivity Table (S1~S6)")
    lines.append("| Scenario | PF | NetPnL | MDD | Sharpe | Trades | FillRate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for name, _fee, _slip in SCENARIOS:
        row = report["cost_sensitivity"][name]
        lines.append(
            f"| {name} | {row['profit_factor']:.6f} | {row['net_pnl']:.4f} | {row['max_drawdown']:.4f} | "
            f"{row['sharpe']:.6f} | {row['trades']} | {row['fill_rate']:.2f}% |"
        )
    lines.append("")
    lines.append("## 3. Stability Analysis")
    for k, v in report["stability_analysis"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 4. Drawdown Attribution")
    dd = report["drawdown_attribution"]
    lines.append(f"- period: {dd['period']}")
    lines.append(f"- drawdown: {dd['drawdown']:.4f}")
    lines.append(f"- top_symbol_losses: {dd['top_symbol_losses']}")
    lines.append(f"- top_sector_losses: {dd['top_sector_losses']}")
    lines.append(f"- exit_type_breakdown: {dd['exit_type_breakdown']}")
    lines.append("")
    lines.append("## 5. Concentration Risk")
    for k, v in report["concentration_risk"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 6. Trade Quality")
    for k, v in report["trade_quality"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 7. Failure Mode")
    lines.append(f"- code: {report['failure_mode']['code']}")
    lines.append(f"- label: {report['failure_mode']['label']}")
    lines.append(f"- reasons: {report['failure_mode']['reasons']}")
    lines.append("")
    lines.append("## 8. Pilot Conditions")
    for k, v in report["pilot_conditions"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 9. Final Decision")
    lines.append(f"- gate_status: {report['final_decision']['gate_status']}")
    lines.append(f"- decision: {report['final_decision']['decision']}")
    lines.append(f"- answer_q1_real_money: {report['final_decision']['answer_q1_real_money']}")
    lines.append(f"- answer_q2_long_term: {report['final_decision']['answer_q2_long_term']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 084: Portfolio strategy lock & paper pilot readiness")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--entry-policy", type=str, default="LIMITED_CHASE")
    parser.add_argument("--risk-policy", type=str, default="TIME_STOP_ONLY")
    parser.add_argument("--max-positions", type=int, default=3)
    parser.add_argument("--top-sectors", type=int, default=2)
    parser.add_argument("--json-out", type=str, default="docs/reports/task_084/task_084_strategy_lock.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_084/task_084_strategy_lock.md")
    args = parser.parse_args()

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    data_dir = Path(args.data_dir)

    frames = load_universe_daily_bars(symbols, base_dir=data_dir)
    sector_snapshot = build_sector_snapshot(frames)
    ranked_sectors = sorted(sector_snapshot.items(), key=lambda item: float(item[1]["strength_score"]), reverse=True)
    allowed_sectors = {name for name, _ in ranked_sectors[: max(1, int(args.top_sectors))]}
    sector_symbols = [s for s in symbols if map_symbol_to_sector(s) in allowed_sectors]
    if not sector_symbols:
        sector_symbols = symbols

    scenario_metrics: dict[str, dict[str, Any]] = {}
    scenario_results: dict[str, list[FullTradeResult]] = {}
    scenario_stats: dict[str, Any] = {}
    for name, fee, slip in SCENARIOS:
        metrics, results, stats = _run_scenario(
            symbols=sector_symbols,
            data_dir=data_dir,
            initial_equity=args.initial_equity,
            entry_policy=args.entry_policy,
            risk_policy=args.risk_policy,
            max_positions=args.max_positions,
            fee_rate=fee,
            slippage_rate=slip,
        )
        scenario_metrics[name] = metrics
        scenario_results[name] = results
        scenario_stats[name] = stats

    s4 = scenario_metrics["S4_KIS_REALISTIC"]
    s5 = scenario_metrics["S5_KIS_STRESS_20"]
    s6 = scenario_metrics["S6_KIS_STRESS_30"]
    stability = {
        "pf_decay_s1_to_s6": _f(scenario_metrics["S1_ZERO_COST"]["profit_factor"] - s6["profit_factor"]),
        "s4_pf_ge_1_2": bool(float(s4["profit_factor"]) >= 1.2),
        "s5_pf_ge_1_0": bool(float(s5["profit_factor"]) >= 1.0),
        "s4_sharpe_ge_1_0": bool(float(s4["sharpe"]) >= 1.0),
        "pf_collapses_hard": bool(float(s6["profit_factor"]) < 0.85 * max(float(s4["profit_factor"]), 1e-9)),
    }

    s4_df = _trade_frame(scenario_results["S4_KIS_REALISTIC"])
    drawdown = _drawdown_analysis(s4_df)
    concentration = _concentration(s4_df)
    portfolio_metrics = summarize_portfolio_results(
        scenario_results["S4_KIS_REALISTIC"],
        initial_equity=args.initial_equity,
        max_positions=args.max_positions,
    )

    s4_stats = scenario_stats["S4_KIS_REALISTIC"]
    total_signals = int(s4_stats.total_signals)
    missed_ratio = (float(s4_stats.missed_trades) / total_signals * 100.0) if total_signals > 0 else 0.0
    big_miss_ratio = (float(s4_stats.big_miss_count) / max(float(s4_stats.missed_trades), 1.0) * 100.0) if s4_stats.missed_trades > 0 else 0.0
    trade_quality = {
        "fill_rate": _f(s4_stats.fill_rate),
        "missed_trade_ratio": _f(missed_ratio),
        "big_miss_ratio_of_missed": _f(big_miss_ratio),
        "avg_slippage": _f(float(s4_df["slippage"].mean()) if not s4_df.empty else 0.0),
        "missed_trades": int(s4_stats.missed_trades),
        "big_miss_count": int(s4_stats.big_miss_count),
    }

    portfolio_risk = {
        "max_concurrent_positions": _max_concurrent_positions(s4_df),
        "average_concurrent_positions": _f(_avg_concurrent_positions(s4_df)),
        "capital_utilization": _f(portfolio_metrics.capital_utilization),
        "exposure_variance": _f(_exposure_variance(s4_df, initial_equity=args.initial_equity, max_positions=args.max_positions)),
        "worst_day_loss": _worst_day_loss(s4_df),
        "loss_streak": _loss_streak(s4_df),
    }

    failure_mode = _failure_mode(scenarios=scenario_metrics, concentration=concentration, trade_quality_s4=trade_quality)
    gate = _pilot_gate(s4, concentration)
    decision_map = {"PASS": "PASS", "WARNING": "WARNING", "FAIL": "FAIL"}
    final_status = decision_map[gate["status"]]
    answer_q1 = "YES" if final_status == "PASS" else ("WARNING" if final_status == "WARNING" else "NO")
    answer_q2 = "YES" if (final_status == "PASS" and not stability["pf_collapses_hard"]) else ("WARNING" if final_status == "WARNING" else "NO")
    pilot_conditions = _pilot_conditions(final_status, s4)

    report = {
        "strategy_summary": {
            "strategy_id": STRATEGY_ID,
            "execution_policy": args.entry_policy,
            "risk_policy": args.risk_policy,
            "mode": "portfolio",
            "max_positions": int(args.max_positions),
            "allowed_sectors": sorted(allowed_sectors),
            "symbols_used": sector_symbols,
        },
        "cost_sensitivity": scenario_metrics,
        "stability_analysis": stability,
        "drawdown_attribution": drawdown,
        "concentration_risk": concentration,
        "portfolio_risk_validation": portfolio_risk,
        "trade_quality": trade_quality,
        "failure_mode": failure_mode,
        "pilot_gate": gate,
        "pilot_conditions": pilot_conditions,
        "final_decision": {
            "gate_status": final_status,
            "decision": (
                "PASS -> 즉시 Paper Pilot 가능"
                if final_status == "PASS"
                else ("WARNING -> 초소액 제한 Pilot만 가능" if final_status == "WARNING" else "FAIL -> 전략 폐기 또는 재설계 필요")
            ),
            "answer_q1_real_money": answer_q1,
            "answer_q2_long_term": answer_q2,
        },
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"final_status={final_status}")
    print(f"answer_q1={answer_q1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
