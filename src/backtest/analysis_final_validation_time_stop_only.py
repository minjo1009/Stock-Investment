from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

import backtest.engine_full as engine_full
import risk.policies as risk_policies
from backtest.analysis_stop_loss_structure import _load_price_frames, _trade_rows
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import FullTradeResult, run_full_backtest_universe_with_stats, summarize


BASELINE_POLICY = {"entry_policy": "LIMITED_CHASE", "risk_policy": "BASELINE", "label": "LIMITED_CHASE"}
CANDIDATE_POLICY = {
    "entry_policy": "LIMITED_CHASE",
    "risk_policy": "TIME_STOP_ONLY_066B",
    "label": "TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0)",
}

SCENARIOS = [
    ("S1_ZERO_COST", 0.0, 0.0),
    ("S2_LOW_COST", 0.0005, 0.0005),
    ("S3_MEDIUM_COST", 0.0010, 0.0005),
    ("S4_KIS_REALISTIC", 0.0025, 0.0010),
    ("S5_KIS_STRESS_20", 0.0025, 0.0020),
    ("S6_KIS_STRESS_30", 0.0025, 0.0030),
]


@contextmanager
def patched_time_stop_only_policy() -> Any:
    old_mfe_trigger = risk_policies.RISK_MFE_TRIGGER
    old_giveback = risk_policies.RISK_GIVEBACK_FRACTION
    old_time_bars = risk_policies.RISK_TIME_STOP_BARS
    old_profit_buffer = risk_policies.RISK_TIME_STOP_MIN_RETURN
    old_engine_mfe_trigger = engine_full.RISK_MFE_TRIGGER
    had_policy = "TIME_STOP_ONLY_066B" in risk_policies.RISK_POLICIES
    old_policy = risk_policies.RISK_POLICIES.get("TIME_STOP_ONLY_066B")
    try:
        risk_policies.RISK_MFE_TRIGGER = 0.03
        risk_policies.RISK_GIVEBACK_FRACTION = 0.50
        risk_policies.RISK_TIME_STOP_BARS = 10
        risk_policies.RISK_TIME_STOP_MIN_RETURN = 0.0
        engine_full.RISK_MFE_TRIGGER = 0.03
        risk_policies.RISK_POLICIES["TIME_STOP_ONLY_066B"] = {"break_even": False, "giveback": False, "time_stop": True}
        yield
    finally:
        risk_policies.RISK_MFE_TRIGGER = old_mfe_trigger
        risk_policies.RISK_GIVEBACK_FRACTION = old_giveback
        risk_policies.RISK_TIME_STOP_BARS = old_time_bars
        risk_policies.RISK_TIME_STOP_MIN_RETURN = old_profit_buffer
        engine_full.RISK_MFE_TRIGGER = old_engine_mfe_trigger
        if had_policy:
            risk_policies.RISK_POLICIES["TIME_STOP_ONLY_066B"] = old_policy if old_policy is not None else {}
        else:
            risk_policies.RISK_POLICIES.pop("TIME_STOP_ONLY_066B", None)


def _run_policy_scenario(
    *,
    policy: dict[str, str],
    scenario: tuple[str, float, float],
    symbols: list[str],
    base_dir: Path,
    initial_equity: float,
    frames: dict[str, pd.DataFrame],
) -> tuple[dict[str, Any], list[FullTradeResult]]:
    scenario_name, fee_rate, slippage_rate = scenario
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        entry_policy=policy["entry_policy"],
        risk_policy=policy["risk_policy"],
    )
    summary = summarize(results, initial_equity=initial_equity)
    trades = _trade_rows(results, frames)
    stops = trades[trades["stop_hit_flag"] == True].copy() if not trades.empty else trades
    good_then_stop = int((stops["classification"] == "GOOD_THEN_STOP").sum()) if not stops.empty else 0

    row = {
        "policy": policy["label"],
        "scenario": scenario_name,
        "fee_rate": fee_rate,
        "slippage_rate": slippage_rate,
        "trades": int(summary.trade_count),
        "win_rate": float(summary.win_rate),
        "profit_factor": float(summary.profit_factor),
        "net_pnl": float(summary.net_pnl),
        "max_drawdown": float(summary.max_drawdown),
        "sharpe": float(summary.sharpe_ratio),
        "fill_rate": float(stats.fill_rate),
        "stop_count": int(len(stops)),
        "good_then_stop_count": good_then_stop,
        "big_miss_count": int(stats.big_miss_count),
    }
    return row, results


def _drawdown_stop_view(results: list[FullTradeResult]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in results:
        trade = item.trade
        meta = dict(item.metadata or {})
        rows.append(
            {
                "exit_time": trade.exit_time,
                "net_pnl": float(item.net_pnl),
                "stop_hit_flag": bool(meta.get("stop_hit_flag") is True),
                "symbol": trade.symbol,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return {"drawdown": 0.0, "dd_stop_ratio_pct": 0.0, "dd_stop_net_pnl": 0.0}
    frame["exit_time"] = pd.to_datetime(frame["exit_time"], utc=True, errors="coerce")
    frame = frame.sort_values("exit_time").reset_index(drop=True)
    frame["equity"] = frame["net_pnl"].cumsum()
    frame["peak"] = frame["equity"].cummax()
    frame["drawdown"] = frame["peak"] - frame["equity"]
    trough_idx = int(frame["drawdown"].idxmax())
    trough = frame.loc[trough_idx]
    peak_idx = int(frame.loc[:trough_idx, "equity"].idxmax())
    segment = frame.loc[peak_idx:trough_idx].copy()
    segment_stops = segment[segment["stop_hit_flag"] == True]
    return {
        "drawdown": float(trough["drawdown"]),
        "dd_trade_count": int(len(segment)),
        "dd_stop_count": int(len(segment_stops)),
        "dd_stop_ratio_pct": float(len(segment_stops) / len(segment) * 100.0) if len(segment) else 0.0,
        "dd_stop_net_pnl": float(segment_stops["net_pnl"].sum()) if not segment_stops.empty else 0.0,
    }


def _gate(metrics: dict[str, Any]) -> dict[str, Any]:
    pf = float(metrics["profit_factor"])
    net = float(metrics["net_pnl"])
    sharpe = float(metrics["sharpe"])
    mdd = float(metrics["max_drawdown"])

    if pf < 1.0 or net <= 0.0:
        status = "FAIL"
    elif pf >= 1.2 and sharpe >= 1.0 and mdd <= net * 0.40:
        status = "PASS"
    else:
        status = "WARNING"
    return {
        "status": status,
        "pf_ok": pf >= 1.2,
        "net_pnl_ok": net > 0.0,
        "sharpe_ok": sharpe >= 1.0,
        "mdd_ok": (mdd <= net * 0.40) if net > 0 else False,
        "mdd_to_net_pnl_pct": (mdd / net * 100.0) if net > 0 else None,
    }


def _scenario_delta(base: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "trades",
        "win_rate",
        "profit_factor",
        "net_pnl",
        "max_drawdown",
        "sharpe",
        "fill_rate",
        "stop_count",
        "good_then_stop_count",
        "big_miss_count",
    )
    out: dict[str, Any] = {}
    for key in fields:
        out[f"{key}_delta"] = float(cand[key]) - float(base[key])
    return out


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 066-B Final Validation (TIME_STOP_ONLY)")
    lines.append("")
    lines.append("## Comparison Setup")
    lines.append(f"- Baseline: {report['comparison_setup']['baseline']}")
    lines.append(f"- Candidate: {report['comparison_setup']['candidate']}")
    lines.append("")
    lines.append("## Results Table")
    lines.append("")
    lines.append("| Scenario | Policy | Trades | WinRate | PF | NetPnL | MDD | Sharpe | FillRate | STOP | GOOD->STOP | BIG_MISS |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for scenario in SCENARIOS:
        name = scenario[0]
        for policy_label in (BASELINE_POLICY["label"], CANDIDATE_POLICY["label"]):
            row = report["results"][policy_label][name]
            lines.append(
                f"| {name} | {policy_label} | {row['trades']} | {row['win_rate']:.2f}% | {row['profit_factor']:.4f} | "
                f"{row['net_pnl']:.2f} | {row['max_drawdown']:.2f} | {row['sharpe']:.4f} | {row['fill_rate']:.2f}% | "
                f"{row['stop_count']} | {row['good_then_stop_count']} | {row['big_miss_count']} |"
            )
    lines.append("")
    s4 = report["s4_detailed_comparison"]
    lines.append("## S4 Detailed Comparison")
    lines.append("")
    lines.append(f"- Baseline PF/Net/MDD/Sharpe: {s4['baseline']['profit_factor']:.4f} / {s4['baseline']['net_pnl']:.2f} / {s4['baseline']['max_drawdown']:.2f} / {s4['baseline']['sharpe']:.4f}")
    lines.append(f"- Candidate PF/Net/MDD/Sharpe: {s4['candidate']['profit_factor']:.4f} / {s4['candidate']['net_pnl']:.2f} / {s4['candidate']['max_drawdown']:.2f} / {s4['candidate']['sharpe']:.4f}")
    lines.append(f"- Delta (candidate-baseline): PF {s4['delta']['profit_factor_delta']:.4f}, Net {s4['delta']['net_pnl_delta']:.2f}, MDD {s4['delta']['max_drawdown_delta']:.2f}, Sharpe {s4['delta']['sharpe_delta']:.4f}")
    lines.append("")
    risk = report["risk_comparison"]
    lines.append("## Risk Comparison")
    lines.append("")
    lines.append(f"- STOP-driven DD ratio: baseline {risk['baseline_dd']['dd_stop_ratio_pct']:.2f}% -> candidate {risk['candidate_dd']['dd_stop_ratio_pct']:.2f}%")
    lines.append(f"- STOP count delta (S4): {s4['delta']['stop_count_delta']:+.0f}")
    lines.append(f"- GOOD_THEN_STOP delta (S4): {s4['delta']['good_then_stop_count_delta']:+.0f}")
    lines.append("")
    gate = report["kpi_gate_result"]
    lines.append("## KPI Gate Result")
    lines.append("")
    lines.append(f"- Status: {gate['status']}")
    lines.append(f"- PF>=1.2: {gate['pf_ok']}")
    lines.append(f"- NetPnL>0: {gate['net_pnl_ok']}")
    lines.append(f"- Sharpe>=1.0: {gate['sharpe_ok']}")
    lines.append(f"- MDD<=40% of NetPnL: {gate['mdd_ok']}")
    lines.append("")
    final_decision = report["final_decision"]
    lines.append("## Final Decision")
    lines.append("")
    lines.append(f"- Pilot Decision: {final_decision['pilot_decision']}")
    lines.append(f"- Reason: {final_decision['reason']}")
    lines.append("")
    lines.append("## Next Actions")
    for action in report["next_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 066-B: Final Validation Re-run for TIME_STOP_ONLY")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--json-out", type=str, default="docs/task_066B_final_validation_time_stop_only.json")
    parser.add_argument("--md-out", type=str, default="docs/task_066B_final_validation_time_stop_only.md")
    args = parser.parse_args()

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)
    frames = _load_price_frames(symbols, base_dir)

    baseline_rows: dict[str, Any] = {}
    baseline_s4_results: list[FullTradeResult] = []
    for scenario in SCENARIOS:
        row, results = _run_policy_scenario(
            policy=BASELINE_POLICY,
            scenario=scenario,
            symbols=symbols,
            base_dir=base_dir,
            initial_equity=args.initial_equity,
            frames=frames,
        )
        baseline_rows[scenario[0]] = row
        if scenario[0] == "S4_KIS_REALISTIC":
            baseline_s4_results = results

    candidate_rows: dict[str, Any] = {}
    candidate_s4_results: list[FullTradeResult] = []
    with patched_time_stop_only_policy():
        for scenario in SCENARIOS:
            row, results = _run_policy_scenario(
                policy=CANDIDATE_POLICY,
                scenario=scenario,
                symbols=symbols,
                base_dir=base_dir,
                initial_equity=args.initial_equity,
                frames=frames,
            )
            candidate_rows[scenario[0]] = row
            if scenario[0] == "S4_KIS_REALISTIC":
                candidate_s4_results = results

    by_scenario_delta = {
        name: _scenario_delta(baseline_rows[name], candidate_rows[name]) for name, _fee, _slip in SCENARIOS
    }
    s4_baseline = baseline_rows["S4_KIS_REALISTIC"]
    s4_candidate = candidate_rows["S4_KIS_REALISTIC"]
    s4_delta = by_scenario_delta["S4_KIS_REALISTIC"]

    gate = _gate(s4_candidate)
    if gate["status"] == "PASS":
        pilot_decision = "YES"
        reason = "KPI gate passed on S4 with positive returns and acceptable risk."
    elif gate["status"] == "WARNING":
        pilot_decision = "WARNING"
        reason = "Positive PF/Net on S4 but full gate not satisfied (Sharpe or MDD constraint)."
    else:
        pilot_decision = "NO"
        reason = "Candidate fails minimum viability gate on S4."

    report = {
        "comparison_setup": {
            "baseline": BASELINE_POLICY["label"],
            "candidate": CANDIDATE_POLICY["label"],
            "symbols": symbols,
            "data_dir": str(base_dir),
            "initial_equity": float(args.initial_equity),
            "scenarios": [
                {"name": name, "fee_rate": fee, "slippage_rate": slip} for name, fee, slip in SCENARIOS
            ],
        },
        "results": {
            BASELINE_POLICY["label"]: baseline_rows,
            CANDIDATE_POLICY["label"]: candidate_rows,
        },
        "scenario_deltas_candidate_minus_baseline": by_scenario_delta,
        "s4_detailed_comparison": {
            "baseline": s4_baseline,
            "candidate": s4_candidate,
            "delta": s4_delta,
        },
        "risk_comparison": {
            "baseline_dd": _drawdown_stop_view(baseline_s4_results),
            "candidate_dd": _drawdown_stop_view(candidate_s4_results),
            "stop_driven_dd_reduced": _drawdown_stop_view(candidate_s4_results)["dd_stop_ratio_pct"]
            < _drawdown_stop_view(baseline_s4_results)["dd_stop_ratio_pct"],
            "sharpe_improved_s4": float(s4_delta["sharpe_delta"]) > 0.0,
            "mdd_improved_s4": float(s4_delta["max_drawdown_delta"]) < 0.0,
            "good_then_stop_reduced_s4": float(s4_delta["good_then_stop_count_delta"]) < 0.0,
        },
        "kpi_gate_result": gate,
        "final_decision": {"pilot_decision": pilot_decision, "reason": reason},
        "next_actions": [
            "If WARNING, run ultra-small pilot with strict daily loss cap and UNKNOWN-order halt.",
            "Track S4-equivalent live slippage and fill-rate drift against backtest deltas.",
            "If S4 live metrics degrade for 2 consecutive weeks, rollback to baseline policy.",
        ],
    }

    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_path}")
    print(f"written_md={md_path}")
    print(f"kpi_status={gate['status']}")
    print(f"pilot_decision={pilot_decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
