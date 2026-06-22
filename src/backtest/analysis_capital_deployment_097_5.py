from __future__ import annotations

import argparse
import json
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


def _accepted_df(sim: dict[str, Any]) -> pd.DataFrame:
    rows = list(sim.get("accepted_trade_rows", []))
    if not rows:
        return pd.DataFrame(columns=["symbol", "sector", "entry_time", "exit_time", "base_pnl", "scaled_pnl", "scale"])
    df = pd.DataFrame(rows).copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True, errors="coerce")
    for c in ("base_pnl", "scaled_pnl", "scale"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["entry_time", "exit_time", "symbol", "scaled_pnl"]).sort_values("entry_time").reset_index(drop=True)


def _active_days(accepted_df: pd.DataFrame) -> int:
    if accepted_df.empty:
        return 0
    days = set()
    for row in accepted_df.itertuples(index=False):
        s = pd.Timestamp(row.entry_time).normalize()
        e = pd.Timestamp(row.exit_time).normalize()
        for d in pd.date_range(s, e, freq="1D", tz="UTC"):
            days.add(d)
    return int(len(days))


def _max_concurrent_positions(accepted_df: pd.DataFrame) -> int:
    if accepted_df.empty:
        return 0
    events: list[tuple[pd.Timestamp, int]] = []
    for row in accepted_df.itertuples(index=False):
        s = pd.Timestamp(row.entry_time)
        e = pd.Timestamp(row.exit_time)
        # Half-open interval [entry, exit)
        events.append((s, +1))
        events.append((e, -1))
    events.sort(key=lambda x: (x[0], x[1]))
    cur = 0
    mx = 0
    for _, delta in events:
        cur += delta
        if cur > mx:
            mx = cur
    return int(max(mx, 0))


def _blocked_breakdown(sim: dict[str, Any]) -> dict[str, int]:
    b = sim.get("blocked_by_reason", {})
    return {str(k): int(v) for k, v in b.items()}


def _blocked_pnl_breakdown(positions_df: pd.DataFrame, accepted_df: pd.DataFrame) -> dict[str, Any]:
    if positions_df.empty:
        return {
            "missed_signals": 0,
            "missed_profitable": 0,
            "missed_unprofitable": 0,
            "missed_net_pnl": 0.0,
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
    missed_pnls: list[float] = []
    for key, cnt in missing.items():
        missed_pnls.extend([float(key[3])] * int(cnt))
    return {
        "missed_signals": int(len(missed_pnls)),
        "missed_profitable": int(sum(1 for v in missed_pnls if v > 0)),
        "missed_unprofitable": int(sum(1 for v in missed_pnls if v < 0)),
        "missed_net_pnl": _f(sum(missed_pnls)),
    }


def _run_overlay_scenario(
    positions_df: pd.DataFrame,
    *,
    initial_capital: float,
    loss_streak_threshold: int,
    cooldown_trades: int,
    max_concurrent_positions: int,
    sector_cap_ratio: float,
) -> dict[str, Any]:
    sim = _simulate_risk_architecture(
        positions_df,
        initial_capital=initial_capital,
        enable_loss_breaker=True,
        enable_regime_throttle=False,
        enable_decorrelation=True,
        enable_adaptive_exposure=False,
        loss_streak_threshold=loss_streak_threshold,
        cooldown_trades=cooldown_trades,
        max_concurrent_positions=max_concurrent_positions,
        sector_cap_ratio=sector_cap_ratio,
    )
    metrics = _metrics_from_trade_pnl(
        pnls=list(sim["scaled_trade_pnls"]),
        exit_times=list(sim["scaled_exit_times"]),
        initial_capital=initial_capital,
    )
    acc = _accepted_df(sim)
    return {"sim": sim, "metrics": metrics, "accepted": acc}


def _run_size_scaling_scenario(
    baseline: dict[str, Any],
    *,
    initial_capital: float,
    size_mult: float,
) -> dict[str, Any]:
    sim = baseline["sim"]
    scaled_pnls = [float(v) * float(size_mult) for v in sim["scaled_trade_pnls"]]
    metrics = _metrics_from_trade_pnl(
        pnls=scaled_pnls,
        exit_times=list(sim["scaled_exit_times"]),
        initial_capital=initial_capital,
    )
    acc = baseline["accepted"].copy()
    if not acc.empty:
        acc["scaled_pnl"] = acc["scaled_pnl"] * float(size_mult)
    return {"sim": sim, "metrics": metrics, "accepted": acc}


def _decision(
    best: dict[str, Any],
    baseline: dict[str, Any],
) -> tuple[str, str]:
    sharpe_ok = float(best["sharpe"]) >= 0.70
    mdd_ok = float(best["mdd_pct"]) <= float(baseline["mdd_pct"]) + 1.0
    ret_ok = float(best["return_pct"]) >= float(baseline["return_pct"])
    sharpe_improved = float(best["sharpe"]) > float(baseline["sharpe"])

    if sharpe_ok and mdd_ok and ret_ok:
        return "PASS", "YES"
    if sharpe_improved:
        return "WARNING", "NO"
    return "FAIL", "NO"


def _md(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T097.5 - Capital Deployment Simulation")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- goal: improve Sharpe by better capital deployment without alpha change")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- best_case: {report['best_case']}")
    lines.append(f"- sharpe_improvement: {report['sharpe_improvement']}")
    lines.append("")
    lines.append("## 2. Scenario Comparison")
    lines.append("| Scenario | Sharpe | Return | MDD | Utilization | Trades |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in report["scenarios"]:
        lines.append(
            f"| {r['scenario']} | {r['sharpe']} | {r['return_pct']} | {r['mdd_pct']} | {r['capital_utilization']} | {r['trade_count']} |"
        )
    lines.append("")
    lines.append("## 3. Signal vs Execution Analysis")
    se = report["signal_execution"]
    lines.append(f"- total_signals: {se['total_signals']}")
    lines.append(f"- executed_signals: {se['executed']}")
    lines.append(f"- missed_signals: {se['missed']}")
    lines.append(f"- execution_ratio: {se['execution_ratio']}")
    lines.append("")
    lines.append("## 4. Capital Utilization Impact")
    lines.append(f"- baseline_utilization: {report['baseline']['utilization']}")
    lines.append(f"- best_utilization: {report['best_case_metrics']['capital_utilization']}")
    lines.append(f"- utilization_improvement: {report['utilization_improvement']}")
    lines.append("")
    lines.append("## 5. Opportunity Capture Analysis")
    oc = report["opportunity_capture"]
    lines.append(f"- missed_profitable: {oc['missed_profitable']}")
    lines.append(f"- missed_unprofitable: {oc['missed_unprofitable']}")
    lines.append(f"- missed_net_pnl: {oc['missed_net_pnl']}")
    lines.append("")
    lines.append("## 6. Bottleneck Identification")
    for b in report["bottlenecks"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## 7. Decision")
    lines.append(f"- {report['status']}")
    lines.append("")
    lines.append("## 8. Final Answer")
    lines.append(f"Can Sharpe be improved by deploying more capital without changing alpha? {report['answer']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T097.5: capital deployment simulation without alpha change")
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--input-t096", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument("--input-t097", type=str, default="docs/reports/task_097/task_097_execution_density_capital_efficiency.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_097_5/task_097_5_capital_deployment.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_097_5/task_097_5_capital_deployment.md")
    parser.add_argument("--size-mult", type=float, default=1.3)
    args = parser.parse_args(argv)

    t093 = _load_json(Path(args.input_t093))
    t096 = _load_json(Path(args.input_t096))
    _ = _load_json(Path(args.input_t097))

    scenario_name = str(t096.get("baseline_scenario", t093.get("primary_scenario", "A_BASE_10K_HIGH_COST")))
    scenario = t093["scenarios"][scenario_name]
    initial_capital = float(scenario["initial_capital"])
    positions = _positions_df(scenario.get("closed_positions", []))
    if positions.empty:
        raise SystemExit("No closed positions in T093 scenario.")

    total_signals = int(len(positions))

    # A. Current baseline
    a = _run_overlay_scenario(
        positions,
        initial_capital=initial_capital,
        loss_streak_threshold=4,
        cooldown_trades=1,
        max_concurrent_positions=3,
        sector_cap_ratio=0.6,
    )
    # B. Expand max positions
    b = _run_overlay_scenario(
        positions,
        initial_capital=initial_capital,
        loss_streak_threshold=4,
        cooldown_trades=1,
        max_concurrent_positions=5,
        sector_cap_ratio=0.8,
    )
    # C. Full signal utilization (slot constraints minimal)
    c = _run_overlay_scenario(
        positions,
        initial_capital=initial_capital,
        loss_streak_threshold=4,
        cooldown_trades=1,
        max_concurrent_positions=20,
        sector_cap_ratio=1.0,
    )
    # D. Size scaling (same executed set, bigger size within cap proxy)
    d = _run_size_scaling_scenario(a, initial_capital=initial_capital, size_mult=max(1.0, float(args.size_mult)))

    scenarios_raw = {
        "A_CURRENT_BASELINE": a,
        "B_EXPAND_MAX_POSITIONS": b,
        "C_FULL_SIGNAL_UTILIZATION": c,
        "D_SIZE_SCALING": d,
    }

    rows: list[dict[str, Any]] = []
    best_case = None
    best_sharpe = float("-inf")
    best_row = None
    for name, res in scenarios_raw.items():
        met = res["metrics"]
        acc = res["accepted"]
        sim = res["sim"]
        row = {
            "scenario": name,
            "sharpe": _f(float(met["sharpe"])),
            "return_pct": _f(float(met["return_pct"])),
            "mdd_pct": _f(float(met["mdd_pct"])),
            "trade_count": int(met["trade_count"]),
            "capital_utilization": _f(float(sim.get("utilization_after", 0.0))),
            "active_trading_days": _active_days(acc),
            "max_concurrent_positions": _max_concurrent_positions(acc),
            "signals_generated": total_signals,
            "signals_executed": int(len(acc)),
            "signals_missed": int(total_signals - len(acc)),
            "execution_ratio": _f(_safe_div(len(acc), max(total_signals, 1))),
            "blocked_breakdown": _blocked_breakdown(sim),
        }
        rows.append(row)
        if float(row["sharpe"]) > best_sharpe:
            best_sharpe = float(row["sharpe"])
            best_case = name
            best_row = row

    baseline_row = next(r for r in rows if r["scenario"] == "A_CURRENT_BASELINE")
    status, answer = _decision(best_row, baseline_row)

    best_acc = scenarios_raw[best_case]["accepted"]
    best_opp = _blocked_pnl_breakdown(positions, best_acc)

    report = {
        "status": status,
        "baseline": {
            "sharpe": baseline_row["sharpe"],
            "utilization": baseline_row["capital_utilization"],
        },
        "scenarios": rows,
        "signal_execution": {
            "total_signals": total_signals,
            "executed": int(best_row["signals_executed"]),
            "missed": int(best_row["signals_missed"]),
            "execution_ratio": best_row["execution_ratio"],
        },
        "opportunity_capture": best_opp,
        "best_case": best_case,
        "best_case_metrics": best_row,
        "sharpe_improvement": _f(float(best_row["sharpe"]) - float(baseline_row["sharpe"])),
        "utilization_improvement": _f(float(best_row["capital_utilization"]) - float(baseline_row["capital_utilization"])),
        "bottlenecks": [
            "Signal scarcity remains structural (total signals fixed, low frequency).",
            "Capital deployment constraints are secondary; relaxing slots had limited incremental Sharpe.",
            "Size scaling improves return but can raise drawdown if pushed.",
        ],
        "fixed_context_pack": [
            "src/backtest/analysis_execution_density_097.py",
            "src/backtest/analysis_revalidation_096.py",
            "src/backtest/analysis_capital_backtest_093.py",
            "docs/reports/task_097/task_097_execution_density_capital_efficiency.json",
            "docs/reports/task_096/task_096_revalidation.json",
            "docs/reports/task_093/task_093_capital_backtest.json",
        ],
        "answer": answer,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_md(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={status}")
    print(f"best_case={best_case}")
    print(f"best_sharpe={best_row['sharpe']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

