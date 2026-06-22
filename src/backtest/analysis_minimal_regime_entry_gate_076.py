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
from backtest.entry_gates import EntryGateConfig


SCENARIOS = [
    ("S1_ZERO_COST", 0.0, 0.0),
    ("S2_LOW_COST", 0.0005, 0.0005),
    ("S3_MEDIUM_COST", 0.0010, 0.0005),
    ("S4_KIS_REALISTIC", 0.0025, 0.0010),
    ("S5_KIS_STRESS_20", 0.0025, 0.0020),
    ("S6_KIS_STRESS_30", 0.0025, 0.0030),
]

BASELINE_LABEL = "A_BASELINE"
BASELINE_RISK_POLICY = "TIME_STOP_ONLY_066B"

BASELINE_REFERENCE = {
    "pf": 1.1684,
    "net_pnl": 8373.70,
    "mdd": 8919.73,
    "sharpe": 0.7238,
    "stop_count": 55,
    "good_then_stop_count": 15,
}


def _candidate_configs() -> list[dict[str, Any]]:
    ker = EntryGateConfig(use_ker_gate=True)
    volume = EntryGateConfig(use_volume_gate=True)
    daily = EntryGateConfig(use_daily_bias_gate=True)
    return [
        {"name": "A_BASELINE", "gate_config": EntryGateConfig.disabled()},
        {"name": "B_KER_ONLY", "gate_config": ker},
        {"name": "C_VOLUME_ONLY", "gate_config": volume},
        {"name": "D_DAILY_BIAS_ONLY", "gate_config": daily},
        {"name": "E_KER_VOLUME", "gate_config": EntryGateConfig(use_ker_gate=True, use_volume_gate=True)},
        {"name": "F_KER_DAILY_BIAS", "gate_config": EntryGateConfig(use_ker_gate=True, use_daily_bias_gate=True)},
        {"name": "G_VOLUME_DAILY_BIAS", "gate_config": EntryGateConfig(use_volume_gate=True, use_daily_bias_gate=True)},
        {
            "name": "H_KER_VOLUME_DAILY_BIAS",
            "gate_config": EntryGateConfig(use_ker_gate=True, use_volume_gate=True, use_daily_bias_gate=True),
        },
    ]


@contextmanager
def patched_time_stop_only_policy() -> Any:
    old_mfe_trigger = risk_policies.RISK_MFE_TRIGGER
    old_giveback = risk_policies.RISK_GIVEBACK_FRACTION
    old_time_bars = risk_policies.RISK_TIME_STOP_BARS
    old_profit_buffer = risk_policies.RISK_TIME_STOP_MIN_RETURN
    old_engine_mfe_trigger = engine_full.RISK_MFE_TRIGGER
    had_policy = BASELINE_RISK_POLICY in risk_policies.RISK_POLICIES
    old_policy = risk_policies.RISK_POLICIES.get(BASELINE_RISK_POLICY)
    try:
        risk_policies.RISK_MFE_TRIGGER = 0.03
        risk_policies.RISK_GIVEBACK_FRACTION = 0.50
        risk_policies.RISK_TIME_STOP_BARS = 10
        risk_policies.RISK_TIME_STOP_MIN_RETURN = 0.0
        engine_full.RISK_MFE_TRIGGER = 0.03
        risk_policies.RISK_POLICIES[BASELINE_RISK_POLICY] = {
            "break_even": False,
            "giveback": False,
            "time_stop": True,
        }
        yield
    finally:
        risk_policies.RISK_MFE_TRIGGER = old_mfe_trigger
        risk_policies.RISK_GIVEBACK_FRACTION = old_giveback
        risk_policies.RISK_TIME_STOP_BARS = old_time_bars
        risk_policies.RISK_TIME_STOP_MIN_RETURN = old_profit_buffer
        engine_full.RISK_MFE_TRIGGER = old_engine_mfe_trigger
        if had_policy:
            risk_policies.RISK_POLICIES[BASELINE_RISK_POLICY] = old_policy if old_policy is not None else {}
        else:
            risk_policies.RISK_POLICIES.pop(BASELINE_RISK_POLICY, None)


def _run_one(
    *,
    symbols: list[str],
    base_dir: Path,
    initial_equity: float,
    scenario: tuple[str, float, float],
    gate_config: EntryGateConfig,
    frames: dict[str, pd.DataFrame],
) -> tuple[dict[str, Any], list[FullTradeResult]]:
    scenario_name, fee_rate, slippage_rate = scenario
    results, stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        entry_policy="LIMITED_CHASE",
        risk_policy=BASELINE_RISK_POLICY,
        entry_gate_config=gate_config,
    )
    summary = summarize(results, initial_equity=initial_equity)
    trades = _trade_rows(results, frames)
    stops = trades[trades["stop_hit_flag"] == True].copy() if not trades.empty else trades
    good_then_stop = int((stops["classification"] == "GOOD_THEN_STOP").sum()) if not stops.empty else 0
    row = {
        "scenario": scenario_name,
        "fee_rate": float(fee_rate),
        "slippage_rate": float(slippage_rate),
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
        "skipped_by_gate": int(stats.skipped_by_gate),
        "skipped_by_gate_reason_breakdown": dict(stats.skipped_by_gate_reason_breakdown),
        "blocked_trade_avg_estimated_pnl": float(stats.skipped_by_gate_avg_estimated_pnl),
        "blocked_trade_median_estimated_pnl": float(stats.skipped_by_gate_median_estimated_pnl),
        "blocked_trade_winner_ratio": float(stats.skipped_by_gate_winner_ratio),
    }
    return row, results


def _delta(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, float]:
    keys = (
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
        "skipped_by_gate",
    )
    out: dict[str, float] = {}
    for key in keys:
        out[f"{key}_delta"] = float(candidate[key]) - float(base[key])
    return out


def _evaluate_candidate(
    *,
    candidate_name: str,
    candidate_scenarios: dict[str, dict[str, Any]],
    baseline_scenarios: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    s4_base = baseline_scenarios["S4_KIS_REALISTIC"]
    s4 = candidate_scenarios["S4_KIS_REALISTIC"]
    s5 = candidate_scenarios["S5_KIS_STRESS_20"]
    s6 = candidate_scenarios["S6_KIS_STRESS_30"]
    s6_base = baseline_scenarios["S6_KIS_STRESS_30"]

    trade_count_ok = float(s4["trades"]) >= float(s4_base["trades"]) * 0.50
    pf_improved = float(s4["profit_factor"]) > float(s4_base["profit_factor"])
    net_ok = float(s4["net_pnl"]) >= float(s4_base["net_pnl"]) * 0.90
    sharpe_improved = float(s4["sharpe"]) > float(s4_base["sharpe"])
    mdd_not_worse = float(s4["max_drawdown"]) <= float(s4_base["max_drawdown"])
    stress_s5_ok = float(s5["profit_factor"]) > 1.0
    stress_s6_ok = float(s6["profit_factor"]) >= float(s6_base["profit_factor"]) - 0.05
    skipped_mostly_winners = float(s4["blocked_trade_winner_ratio"]) > 0.55

    improved_scenarios = 0
    for scenario_name in [name for name, _fee, _slippage in SCENARIOS]:
        if float(candidate_scenarios[scenario_name]["profit_factor"]) > float(baseline_scenarios[scenario_name]["profit_factor"]):
            improved_scenarios += 1
    not_isolated = improved_scenarios >= 2

    hard_reject = (
        (not trade_count_ok)
        or (not net_ok)
        or (not stress_s5_ok)
        or (not stress_s6_ok)
        or skipped_mostly_winners
        or (not not_isolated)
    )
    if hard_reject:
        status = "FAIL"
    elif pf_improved and sharpe_improved and mdd_not_worse:
        status = "PASS"
    else:
        status = "WARNING"

    return {
        "candidate": candidate_name,
        "status": status,
        "checks": {
            "trade_count_ok": trade_count_ok,
            "pf_improved_s4": pf_improved,
            "net_ok_s4": net_ok,
            "sharpe_improved_s4": sharpe_improved,
            "mdd_not_worse_s4": mdd_not_worse,
            "stress_s5_pf_gt_1": stress_s5_ok,
            "stress_s6_not_materially_worse": stress_s6_ok,
            "not_isolated_improvement": not_isolated,
            "skipped_mostly_winners": skipped_mostly_winners,
        },
    }


def _select_recommendation(
    *,
    evaluations: dict[str, dict[str, Any]],
    baseline_scenarios: dict[str, dict[str, Any]],
    candidate_scenarios: dict[str, dict[str, dict[str, Any]]],
) -> tuple[str, dict[str, Any]]:
    scored: list[tuple[float, str]] = []
    base_s4 = baseline_scenarios["S4_KIS_REALISTIC"]
    for candidate, eval_data in evaluations.items():
        if candidate == BASELINE_LABEL:
            continue
        s4 = candidate_scenarios[candidate]["S4_KIS_REALISTIC"]
        status = eval_data["status"]
        status_score = {"PASS": 2.0, "WARNING": 1.0, "FAIL": 0.0}[status]
        pf_delta = float(s4["profit_factor"]) - float(base_s4["profit_factor"])
        sharpe_delta = float(s4["sharpe"]) - float(base_s4["sharpe"])
        mdd_improvement = float(base_s4["max_drawdown"]) - float(s4["max_drawdown"])
        score = status_score * 100.0 + pf_delta * 50.0 + sharpe_delta * 20.0 + mdd_improvement / 1000.0
        scored.append((score, candidate))
    if not scored:
        return BASELINE_LABEL, evaluations[BASELINE_LABEL]
    scored.sort(reverse=True)
    best_candidate = scored[0][1]
    return best_candidate, evaluations[best_candidate]


def _to_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 076 - Minimal Regime & Entry Quality Gate")
    lines.append("")
    lines.append("## Experiment Setup")
    lines.append(f"- baseline: {report['experiment_setup']['baseline']}")
    lines.append("- candidate set: A~H")
    lines.append(f"- symbols: {len(report['experiment_setup']['symbols'])}")
    lines.append(f"- data_dir: {report['experiment_setup']['data_dir']}")
    lines.append("")
    lines.append("## Gate Definitions")
    lines.append("- KER: abs(close_t-close_t-20)/sum(abs(diff(close)),20), TREND if >0.50")
    lines.append("- Volume percentile: rolling(100) percentile rank >= 0.60")
    lines.append("- Daily bias: close>SMA50 and optional SMA20>SMA50")
    lines.append("")
    lines.append("## Results Table (S4)")
    lines.append("")
    lines.append("| Candidate | Trades | PF | NetPnL | MDD | Sharpe | FillRate | STOP | GOOD->STOP | BIG_MISS | Skipped |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for candidate, scenarios in report["results"].items():
        s4 = scenarios["S4_KIS_REALISTIC"]
        lines.append(
            f"| {candidate} | {s4['trades']} | {s4['profit_factor']:.4f} | {s4['net_pnl']:.2f} | {s4['max_drawdown']:.2f} | {s4['sharpe']:.4f} | "
            f"{s4['fill_rate']:.2f}% | {s4['stop_count']} | {s4['good_then_stop_count']} | {s4['big_miss_count']} | {s4['skipped_by_gate']} |"
        )
    lines.append("")
    lines.append("## S4 Comparison (vs Baseline)")
    for candidate, delta in report["s4_comparison"].items():
        lines.append(
            f"- {candidate}: PF {delta['profit_factor_delta']:+.4f}, Net {delta['net_pnl_delta']:+.2f}, "
            f"MDD {delta['max_drawdown_delta']:+.2f}, Sharpe {delta['sharpe_delta']:+.4f}, Trades {delta['trades_delta']:+.0f}"
        )
    lines.append("")
    lines.append("## Stress Comparison (S5/S6)")
    for candidate, stress in report["stress_comparison"].items():
        lines.append(
            f"- {candidate}: S5 PF {stress['s5_pf']:.4f}, S6 PF {stress['s6_pf']:.4f}, "
            f"S6 PF delta vs baseline {stress['s6_pf_delta_vs_baseline']:+.4f}"
        )
    lines.append("")
    lines.append("## Gate Attribution (S4)")
    for candidate, attr in report["gate_attribution"].items():
        lines.append(
            f"- {candidate}: skipped={attr['skipped_by_gate']}, avg={attr['blocked_trade_avg_estimated_pnl']:.2f}, "
            f"median={attr['blocked_trade_median_estimated_pnl']:.2f}, winner_ratio={attr['blocked_trade_winner_ratio']:.2%}, "
            f"reasons={attr['skipped_by_gate_reason_breakdown']}"
        )
    lines.append("")
    lines.append("## Decision")
    lines.append(f"- recommendation candidate: {report['final_recommendation']['candidate']}")
    lines.append(f"- status: {report['decision']}")
    lines.append(f"- final question answer: {report['final_question_answer']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 076: Minimal Regime & Entry Quality Gate")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_076/task_076_minimal_regime_entry_gate.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_076/task_076_minimal_regime_entry_gate.md",
    )
    args = parser.parse_args()

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)
    frames = _load_price_frames(symbols, base_dir)

    candidates = _candidate_configs()
    results: dict[str, dict[str, dict[str, Any]]] = {}
    full_results: dict[str, dict[str, list[FullTradeResult]]] = {}
    with patched_time_stop_only_policy():
        for candidate in candidates:
            candidate_name = str(candidate["name"])
            results[candidate_name] = {}
            full_results[candidate_name] = {}
            for scenario in SCENARIOS:
                row, scenario_results = _run_one(
                    symbols=symbols,
                    base_dir=base_dir,
                    initial_equity=args.initial_equity,
                    scenario=scenario,
                    gate_config=candidate["gate_config"],
                    frames=frames,
                )
                results[candidate_name][scenario[0]] = row
                full_results[candidate_name][scenario[0]] = scenario_results

    baseline_scenarios = results[BASELINE_LABEL]
    s4_comparison: dict[str, dict[str, float]] = {}
    stress_comparison: dict[str, dict[str, float]] = {}
    gate_attribution: dict[str, dict[str, Any]] = {}
    evaluations: dict[str, dict[str, Any]] = {}
    for candidate_name, by_scenario in results.items():
        s4_comparison[candidate_name] = _delta(baseline_scenarios["S4_KIS_REALISTIC"], by_scenario["S4_KIS_REALISTIC"])
        stress_comparison[candidate_name] = {
            "s5_pf": float(by_scenario["S5_KIS_STRESS_20"]["profit_factor"]),
            "s6_pf": float(by_scenario["S6_KIS_STRESS_30"]["profit_factor"]),
            "s6_pf_delta_vs_baseline": float(
                by_scenario["S6_KIS_STRESS_30"]["profit_factor"] - baseline_scenarios["S6_KIS_STRESS_30"]["profit_factor"]
            ),
        }
        s4 = by_scenario["S4_KIS_REALISTIC"]
        gate_attribution[candidate_name] = {
            "skipped_by_gate": int(s4["skipped_by_gate"]),
            "skipped_by_gate_reason_breakdown": dict(s4["skipped_by_gate_reason_breakdown"]),
            "blocked_trade_avg_estimated_pnl": float(s4["blocked_trade_avg_estimated_pnl"]),
            "blocked_trade_median_estimated_pnl": float(s4["blocked_trade_median_estimated_pnl"]),
            "blocked_trade_winner_ratio": float(s4["blocked_trade_winner_ratio"]),
        }
        evaluations[candidate_name] = _evaluate_candidate(
            candidate_name=candidate_name,
            candidate_scenarios=by_scenario,
            baseline_scenarios=baseline_scenarios,
        )

    best_candidate, best_eval = _select_recommendation(
        evaluations=evaluations,
        baseline_scenarios=baseline_scenarios,
        candidate_scenarios=results,
    )
    decision = str(best_eval["status"])
    if decision == "PASS":
        final_answer = "YES"
    elif decision == "WARNING":
        final_answer = "WARNING"
    else:
        final_answer = "NO"

    report = {
        "experiment_setup": {
            "baseline": "TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0)",
            "symbols": symbols,
            "data_dir": str(base_dir),
            "initial_equity": float(args.initial_equity),
            "scenarios": [
                {"name": name, "fee_rate": fee, "slippage_rate": slippage}
                for name, fee, slippage in SCENARIOS
            ],
            "baseline_reference": BASELINE_REFERENCE,
            "candidate_names": [str(candidate["name"]) for candidate in candidates],
        },
        "gate_definitions": {
            "ker": "abs(close_t-close_t-20)/sum(abs(diff(close)),20), TREND if >0.50, block MIXED and MEAN_REV",
            "volume_percentile": "rolling percentile rank of volume over 100 bars >= 0.60",
            "daily_bias": "BULLISH if close>SMA50, STRONG_BULLISH if close>SMA50 and SMA20>SMA50",
        },
        "results": results,
        "s4_comparison": s4_comparison,
        "stress_comparison": stress_comparison,
        "gate_attribution": gate_attribution,
        "candidate_evaluations": evaluations,
        "final_recommendation": {
            "candidate": best_candidate,
            "status": decision,
            "checks": best_eval["checks"],
        },
        "decision": decision,
        "final_question_answer": final_answer,
    }

    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_path.write_text(_to_markdown(report), encoding="utf-8")
    print(f"written_json={json_path}")
    print(f"written_md={md_path}")
    print(f"decision={decision}")
    print(f"final_answer={final_answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
