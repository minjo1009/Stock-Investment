from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

import pandas as pd


def _f(value: float, digits: int = 6) -> float:
    return float(round(float(value), digits))


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return float(a / b)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _positions_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "symbol",
                "sector",
                "entry_time",
                "exit_time",
                "net_pnl",
                "notional",
                "return_pct",
                "exit_rule",
            ]
        )
    df = pd.DataFrame(rows).copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True, errors="coerce")
    for col in ["net_pnl", "notional", "return_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["entry_time", "exit_time", "net_pnl", "notional"]).sort_values("entry_time").reset_index(drop=True)
    return df


def _metrics_from_trade_pnl(
    pnls: list[float],
    exit_times: list[pd.Timestamp],
    initial_capital: float,
) -> dict[str, Any]:
    if not pnls:
        return {
            "final_capital": initial_capital,
            "return_pct": 0.0,
            "mdd_pct": 0.0,
            "sharpe": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "trade_count": 0,
            "avg_trade_return_pct": 0.0,
            "max_loss_streak": 0,
            "equity_curve_trade": [],
            "equity_curve_daily": [],
        }
    equity = initial_capital
    peak = initial_capital
    max_dd = 0.0
    win_count = 0
    losses: list[float] = []
    wins: list[float] = []
    trade_curve: list[dict[str, Any]] = []
    streak = 0
    best_streak = 0
    rets: list[float] = []
    for pnl, ts in zip(pnls, exit_times):
        equity += pnl
        rets.append(_safe_div(pnl, max(equity - pnl, 1e-9)))
        peak = max(peak, equity)
        dd = _safe_div(peak - equity, peak)
        max_dd = max(max_dd, dd)
        if pnl > 0:
            wins.append(pnl)
            win_count += 1
            streak = 0
        elif pnl < 0:
            losses.append(pnl)
            streak += 1
            best_streak = max(best_streak, streak)
        trade_curve.append({"ts": str(ts.isoformat()), "equity": _f(equity)})

    pf = float(sum(wins) / abs(sum(losses))) if losses else float("inf")
    win_rate = _safe_div(win_count, len(pnls)) * 100.0
    avg_trade_return = statistics.fmean(rets) * 100.0 if rets else 0.0

    curve_df = pd.DataFrame(trade_curve)
    curve_df["ts"] = pd.to_datetime(curve_df["ts"], utc=True, errors="coerce")
    curve_df = curve_df.dropna(subset=["ts"]).set_index("ts").sort_index()
    daily = curve_df["equity"].resample("1D").last().ffill()
    daily_rets = daily.pct_change().dropna()
    if len(daily_rets) >= 2:
        std = float(daily_rets.std(ddof=0))
        sharpe = float((daily_rets.mean() / std) * math.sqrt(252)) if std > 0 else 0.0
    else:
        sharpe = 0.0
    daily_curve = [{"ts": str(ts.isoformat()), "equity": _f(v)} for ts, v in daily.items()]
    return {
        "final_capital": _f(equity, 4),
        "return_pct": _f(_safe_div(equity - initial_capital, initial_capital) * 100.0),
        "mdd_pct": _f(max_dd * 100.0),
        "sharpe": _f(sharpe),
        "profit_factor": _f(pf),
        "win_rate": _f(win_rate),
        "trade_count": int(len(pnls)),
        "avg_trade_return_pct": _f(avg_trade_return),
        "max_loss_streak": int(best_streak),
        "equity_curve_trade": trade_curve,
        "equity_curve_daily": daily_curve,
    }


def _simulate_risk_architecture(
    df: pd.DataFrame,
    *,
    initial_capital: float,
    loss_streak_threshold: int = 3,
    cooldown_trades: int = 2,
    rolling_window: int = 5,
    max_concurrent_positions: int = 3,
    sector_cap_ratio: float = 0.6,
    enable_loss_breaker: bool = True,
    enable_regime_throttle: bool = True,
    enable_decorrelation: bool = True,
    enable_adaptive_exposure: bool = True,
) -> dict[str, Any]:
    if df.empty:
        return {
            "scaled_trade_pnls": [],
            "scaled_exit_times": [],
            "blocked_entries_count": 0,
            "blocked_by_reason": {},
            "avg_position_reduction": 0.0,
            "cooldown_duration_effect": 0,
            "loss_streak_after": 0,
            "utilization_after": 0.0,
            "max_exposure_after": 0.0,
            "accepted_trade_rows": [],
        }

    work = df.sort_values("entry_time").reset_index(drop=True)
    active: list[dict[str, Any]] = []
    rolling: list[float] = []
    peak_equity = float(initial_capital)
    equity = float(initial_capital)
    loss_streak = 0
    cooldown_left = 0

    scaled_pnls: list[float] = []
    scaled_exit_times: list[pd.Timestamp] = []
    reductions: list[float] = []
    blocked = 0
    blocked_reason: dict[str, int] = {}
    accepted_rows: list[dict[str, Any]] = []
    exposure_samples: list[float] = []

    def block(reason: str) -> None:
        nonlocal blocked
        blocked += 1
        blocked_reason[reason] = blocked_reason.get(reason, 0) + 1

    for row in work.itertuples(index=False):
        entry_ts = pd.Timestamp(row.entry_time)
        exit_ts = pd.Timestamp(row.exit_time)
        # clear expired active positions
        active = [p for p in active if p["exit_time"] > entry_ts]

        if enable_loss_breaker and cooldown_left > 0:
            cooldown_left -= 1
            block("LOSS_CLUSTER_BREAKER")
            continue

        if enable_decorrelation and len(active) >= max_concurrent_positions:
            block("MAX_CONCURRENT_CAP")
            continue

        current_open_notional = sum(p["notional"] for p in active)
        sector_open_notional = sum(p["notional"] for p in active if p["sector"] == row.sector)
        if current_open_notional > equity:
            current_open_notional = equity
        if sector_open_notional > equity:
            sector_open_notional = equity

        # regime-aware throttle by rolling pnl
        throttle = 1.0
        if enable_regime_throttle and rolling:
            roll_sum = float(sum(rolling[-rolling_window:]))
            if roll_sum < -0.02 * max(equity, 1e-9):
                throttle = 0.25
            elif roll_sum < 0:
                throttle = 0.5

        # adaptive exposure by current DD
        dd = _safe_div(peak_equity - equity, peak_equity)
        exposure_mult = 1.0
        if enable_adaptive_exposure:
            if dd > 0.20:
                exposure_mult = 0.5
            elif dd > 0.10:
                exposure_mult = 0.7

        # portfolio de-correlation proxy:
        # if same sector already active, throttle harder
        decor_mult = 1.0
        if enable_decorrelation and any(p["sector"] == row.sector for p in active):
            decor_mult = 0.6

        raw_scale = throttle * exposure_mult * decor_mult
        # sector cap constraint
        max_sector_notional = sector_cap_ratio * equity if enable_decorrelation else equity
        allowed_for_sector = max(max_sector_notional - sector_open_notional, 0.0)
        sector_scale = _safe_div(allowed_for_sector, float(row.notional)) if float(row.notional) > 0 else 0.0
        # portfolio cap from remaining cash-equity proxy
        allowed_total = max(equity - current_open_notional, 0.0)
        total_scale = _safe_div(allowed_total, float(row.notional)) if float(row.notional) > 0 else 0.0
        scale = max(0.0, min(raw_scale, sector_scale, total_scale, 1.0))

        if scale <= 0.0:
            block("EXPOSURE_OR_SECTOR_CAP")
            continue

        scaled_pnl = float(row.net_pnl) * scale
        equity += scaled_pnl
        peak_equity = max(peak_equity, equity)
        rolling.append(scaled_pnl)
        if len(rolling) > rolling_window:
            rolling = rolling[-rolling_window:]

        if scaled_pnl < 0:
            loss_streak += 1
            if enable_loss_breaker and loss_streak >= loss_streak_threshold:
                cooldown_left = cooldown_trades
                loss_streak = 0
        else:
            loss_streak = 0

        reductions.append(1.0 - scale)
        scaled_pnls.append(scaled_pnl)
        scaled_exit_times.append(exit_ts)
        active.append({"exit_time": exit_ts, "notional": float(row.notional) * scale, "sector": row.sector})
        exposure_samples.append(_safe_div(sum(p["notional"] for p in active), max(equity, 1e-9)))
        accepted_rows.append(
            {
                "symbol": row.symbol,
                "sector": row.sector,
                "entry_time": str(entry_ts.isoformat()),
                "exit_time": str(exit_ts.isoformat()),
                "base_pnl": _f(row.net_pnl),
                "scaled_pnl": _f(scaled_pnl),
                "scale": _f(scale),
                "throttle": _f(throttle),
                "exposure_mult": _f(exposure_mult),
                "decor_mult": _f(decor_mult),
            }
        )

    loss_streak_after = 0
    streak = 0
    for p in scaled_pnls:
        if p < 0:
            streak += 1
            loss_streak_after = max(loss_streak_after, streak)
        else:
            streak = 0

    return {
        "scaled_trade_pnls": scaled_pnls,
        "scaled_exit_times": scaled_exit_times,
        "blocked_entries_count": int(blocked),
        "blocked_by_reason": dict(sorted(blocked_reason.items())),
        "avg_position_reduction": _f(statistics.fmean(reductions) if reductions else 0.0),
        "cooldown_duration_effect": int(blocked_reason.get("LOSS_CLUSTER_BREAKER", 0)),
        "loss_streak_after": int(loss_streak_after),
        "utilization_after": _f(statistics.fmean(exposure_samples) if exposure_samples else 0.0),
        "max_exposure_after": _f(max(exposure_samples) if exposure_samples else 0.0),
        "accepted_trade_rows": accepted_rows,
    }


def _status(baseline: dict[str, Any], improved: dict[str, Any]) -> str:
    mdd_reduction = _safe_div(float(baseline["mdd_pct"]) - float(improved["mdd_pct"]), max(float(baseline["mdd_pct"]), 1e-9)) * 100.0
    if mdd_reduction >= 20.0 and float(improved["sharpe"]) >= 0.8:
        return "PASS"
    if mdd_reduction > 0 or float(improved["sharpe"]) > float(baseline["sharpe"]):
        return "WARNING"
    return "FAIL"


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T094 - Risk Architecture")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- core_effect: {report['core_effect']}")
    lines.append("")
    lines.append("## 2. Baseline vs Improved")
    lines.append("| Metric | Before | After | Delta |")
    lines.append("|---|---:|---:|---:|")
    for row in report["comparison_rows"]:
        lines.append(f"| {row['metric']} | {row['before']} | {row['after']} | {row['delta']} |")
    lines.append("")
    lines.append("## 3. Loss Cluster Impact")
    lines.append(f"- loss_streak_before: {report['loss_cluster_impact']['loss_streak_before']}")
    lines.append(f"- loss_streak_after: {report['loss_cluster_impact']['loss_streak_after']}")
    lines.append(f"- blocked_entries_count: {report['loss_cluster_impact']['blocked_entries_count']}")
    lines.append(f"- blocked_by_reason: {report['loss_cluster_impact']['blocked_by_reason']}")
    lines.append("")
    lines.append("## 4. Drawdown Reduction")
    lines.append(f"- mdd_before_pct: {report['drawdown_reduction']['before']}")
    lines.append(f"- mdd_after_pct: {report['drawdown_reduction']['after']}")
    lines.append(f"- mdd_reduction_pct: {report['drawdown_reduction']['reduction_pct']}")
    lines.append("")
    lines.append("## 5. Sharpe Improvement")
    lines.append(f"- sharpe_before: {report['sharpe_improvement']['before']}")
    lines.append(f"- sharpe_after: {report['sharpe_improvement']['after']}")
    lines.append(f"- sharpe_delta: {report['sharpe_improvement']['delta']}")
    lines.append("")
    lines.append("## 6. Trade Impact")
    lines.append(f"- trade_count_before: {report['trade_impact']['before']}")
    lines.append(f"- trade_count_after: {report['trade_impact']['after']}")
    lines.append(f"- trade_count_change_pct: {report['trade_impact']['change_pct']}")
    lines.append("")
    lines.append("## 7. Side Effects")
    lines.append(f"- return_change_pct: {report['side_effects']['return_change_pct']}")
    lines.append(f"- avg_position_reduction: {report['side_effects']['avg_position_reduction']}")
    lines.append(f"- utilization_before: {report['side_effects']['utilization_before']}")
    lines.append(f"- utilization_after: {report['side_effects']['utilization_after']}")
    lines.append("")
    lines.append("## 8. Decision")
    lines.append(f"- {report['status']}")
    lines.append("")
    lines.append("## 9. Final Answer")
    lines.append(f"Does risk architecture reduce drawdown clustering without killing returns? {report['answer']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T094: Drawdown control architecture simulation")
    parser.add_argument(
        "--input-json",
        type=str,
        default="docs/reports/task_093/task_093_capital_backtest.json",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_094/task_094_risk_architecture.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_094/task_094_risk_architecture.md",
    )
    args = parser.parse_args(argv)

    payload = _load_json(Path(args.input_json))
    scenario = str(payload.get("primary_scenario", "A_BASE_10K_HIGH_COST"))
    metrics = payload["scenarios"][scenario]
    initial_capital = float(metrics["initial_capital"])
    positions = _positions_df(metrics.get("closed_positions", []))

    baseline = _metrics_from_trade_pnl(
        pnls=positions["net_pnl"].tolist() if not positions.empty else [],
        exit_times=positions["exit_time"].tolist() if not positions.empty else [],
        initial_capital=initial_capital,
    )

    sim = _simulate_risk_architecture(positions, initial_capital=initial_capital)
    improved = _metrics_from_trade_pnl(
        pnls=sim["scaled_trade_pnls"],
        exit_times=sim["scaled_exit_times"],
        initial_capital=initial_capital,
    )

    mdd_reduction_pct = _safe_div(float(baseline["mdd_pct"]) - float(improved["mdd_pct"]), max(float(baseline["mdd_pct"]), 1e-9)) * 100.0
    sharpe_improvement = float(improved["sharpe"]) - float(baseline["sharpe"])
    return_change = float(improved["return_pct"]) - float(baseline["return_pct"])
    loss_streak_reduction = int(baseline["max_loss_streak"]) - int(sim["loss_streak_after"])
    trade_count_change = int(improved["trade_count"]) - int(baseline["trade_count"])

    status = _status(baseline, improved)
    answer = "YES" if status in {"PASS", "WARNING"} and mdd_reduction_pct > 0 else "NO"

    comparison_rows = [
        {"metric": "Return %", "before": _f(baseline["return_pct"]), "after": _f(improved["return_pct"]), "delta": _f(return_change)},
        {"metric": "MDD %", "before": _f(baseline["mdd_pct"]), "after": _f(improved["mdd_pct"]), "delta": _f(-1.0 * mdd_reduction_pct)},
        {"metric": "Sharpe", "before": _f(baseline["sharpe"]), "after": _f(improved["sharpe"]), "delta": _f(sharpe_improvement)},
        {"metric": "Trade Count", "before": int(baseline["trade_count"]), "after": int(improved["trade_count"]), "delta": int(trade_count_change)},
    ]

    report = {
        "task": "T094",
        "status": status,
        "answer": answer,
        "scenario": scenario,
        "config": {
            "loss_cluster_breaker": {"threshold": 3, "cooldown_trades": 2},
            "regime_throttle": {"rolling_window_trades": 5, "negative": 0.5, "deep_negative": 0.25},
            "portfolio_decorrelation": {"max_concurrent_positions": 3, "sector_cap_ratio": 0.6, "same_sector_throttle": 0.6},
            "adaptive_exposure_control": {"dd_gt_10pct": 0.7, "dd_gt_20pct": 0.5},
        },
        "baseline": baseline,
        "improved": improved,
        "comparison_rows": comparison_rows,
        "loss_cluster_impact": {
            "loss_streak_before": int(baseline["max_loss_streak"]),
            "loss_streak_after": int(sim["loss_streak_after"]),
            "loss_streak_reduction": int(loss_streak_reduction),
            "blocked_entries_count": int(sim["blocked_entries_count"]),
            "cooldown_duration_effect": int(sim["cooldown_duration_effect"]),
            "blocked_by_reason": sim["blocked_by_reason"],
        },
        "drawdown_reduction": {
            "before": _f(baseline["mdd_pct"]),
            "after": _f(improved["mdd_pct"]),
            "reduction_pct": _f(mdd_reduction_pct),
        },
        "sharpe_improvement": {
            "before": _f(baseline["sharpe"]),
            "after": _f(improved["sharpe"]),
            "delta": _f(sharpe_improvement),
        },
        "trade_impact": {
            "before": int(baseline["trade_count"]),
            "after": int(improved["trade_count"]),
            "change": int(trade_count_change),
            "change_pct": _f(_safe_div(trade_count_change, max(int(baseline["trade_count"]), 1)) * 100.0),
        },
        "side_effects": {
            "return_change_pct": _f(return_change),
            "avg_position_reduction": _f(sim["avg_position_reduction"]),
            "utilization_before": _f(float(metrics.get("capital_utilization", 0.0))),
            "utilization_after": _f(sim["utilization_after"]),
            "max_exposure_after": _f(sim["max_exposure_after"]),
        },
        "mdd_reduction_pct": _f(mdd_reduction_pct),
        "sharpe_improvement_value": _f(sharpe_improvement),
        "return_change": _f(return_change),
        "loss_streak_reduction": int(loss_streak_reduction),
        "trade_count_change": int(trade_count_change),
        "core_effect": "Risk layer reduces temporal loss clustering via cooldown+throttle and controls drawdown path without alpha logic changes.",
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
    print(f"answer={answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
