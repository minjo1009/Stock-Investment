from __future__ import annotations

import argparse
import json
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


def _cagr(initial_capital: float, final_capital: float, start: pd.Timestamp, end: pd.Timestamp) -> float:
    if initial_capital <= 0 or final_capital <= 0:
        return -100.0
    years = max((end - start).days / 365.25, 1.0 / 365.25)
    return float(((final_capital / initial_capital) ** (1.0 / years) - 1.0) * 100.0)


def _case_score(m: dict[str, Any]) -> float:
    return float(
        (float(m["sharpe"]) * 2.0)
        - (float(m["max_drawdown_pct"]) * 0.05)
        + (float(m["total_return_pct"]) * 0.5)
        - (float(m["loss_streak_max"]) * 0.5)
    )


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T095 - Risk Overlay Adoption")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- selected_overlay: {report['selected_overlay']}")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- reason: {report['reason']}")
    lines.append("")
    lines.append("## 2. Scenario Comparison")
    lines.append("| Case | Return | MDD | Sharpe | Calmar | Score |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in report["comparison"]:
        lines.append(
            f"| {row['case']} | {row['total_return_pct']:.4f} | {row['max_drawdown_pct']:.4f} | "
            f"{row['sharpe']:.6f} | {row['calmar_ratio']:.6f} | {row['score']:.6f} |"
        )
    lines.append("")
    lines.append("## 3. Trade-off Analysis")
    lines.append("- Return vs Risk summary:")
    for row in report["comparison"]:
        lines.append(
            f"  - {row['case']}: return={row['total_return_pct']:.4f}%, mdd={row['max_drawdown_pct']:.4f}%, sharpe={row['sharpe']:.6f}"
        )
    lines.append("")
    lines.append("## 4. Stability Analysis")
    for row in report["comparison"]:
        lines.append(
            f"- {row['case']}: loss_streak_max={row['loss_streak_max']}, trade_count={row['trade_count']}, win_rate={row['win_rate']:.4f}%"
        )
    lines.append("")
    lines.append("## 5. Capital Efficiency")
    for row in report["comparison"]:
        lines.append(f"- {row['case']}: capital_utilization={row['capital_utilization']:.6f}")
    lines.append("")
    lines.append("## 6. Rejected Candidates")
    for row in report["rejected"]:
        lines.append(f"- {row['case']}: {row['reason']}")
    lines.append("")
    lines.append("## 7. Selected Overlay")
    lines.append(f"- {report['selected_overlay']}")
    lines.append(f"- components: {report['selected_components']}")
    lines.append("")
    lines.append("## 8. Decision")
    lines.append(f"- {report['status']}")
    lines.append("")
    lines.append("## 9. Final Answer")
    lines.append("Which risk overlay should be deployed in production?")
    lines.append(f"- {report['selected_overlay']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T095: Risk overlay adoption test")
    parser.add_argument(
        "--input-json",
        type=str,
        default="docs/reports/task_093/task_093_capital_backtest.json",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_095/task_095_risk_adoption.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_095/task_095_risk_adoption.md",
    )
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    scenario = str(payload.get("primary_scenario", "A_BASE_10K_HIGH_COST"))
    scenario_metrics = payload["scenarios"][scenario]
    initial_capital = float(scenario_metrics["initial_capital"])
    positions = _positions_df(scenario_metrics.get("closed_positions", []))
    if positions.empty:
        raise SystemExit("No closed_positions found in T093 input.")

    start_ts = pd.Timestamp(positions["entry_time"].min())
    end_ts = pd.Timestamp(positions["exit_time"].max())

    baseline_return = float(scenario_metrics.get("total_return_pct", 0.0))

    cases: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
        (
            "BASELINE",
            {
                "enable_loss_breaker": False,
                "enable_regime_throttle": False,
                "enable_decorrelation": False,
                "enable_adaptive_exposure": False,
            },
            {},
        ),
        (
            "DECORRELATION_ONLY",
            {
                "enable_loss_breaker": False,
                "enable_regime_throttle": False,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": False,
            },
            {},
        ),
        (
            "FULL_COMBINED",
            {
                "enable_loss_breaker": True,
                "enable_regime_throttle": True,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": True,
            },
            {},
        ),
        (
            "DECORRELATION_PLUS_POSITION_THROTTLE",
            {
                "enable_loss_breaker": False,
                "enable_regime_throttle": True,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": False,
            },
            {},
        ),
        (
            "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER",
            {
                "enable_loss_breaker": True,
                "enable_regime_throttle": False,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": False,
            },
            {"loss_streak_threshold": 4, "cooldown_trades": 1},
        ),
    ]

    comparison: list[dict[str, Any]] = []
    baseline_metrics: dict[str, Any] | None = None
    for case_name, flags, overrides in cases:
        sim = _simulate_risk_architecture(
            positions,
            initial_capital=initial_capital,
            **flags,
            **overrides,
        )
        met = _metrics_from_trade_pnl(
            pnls=sim["scaled_trade_pnls"],
            exit_times=sim["scaled_exit_times"],
            initial_capital=initial_capital,
        )
        total_return_pct = float(met["return_pct"])
        max_drawdown_pct = float(met["mdd_pct"])
        sharpe = float(met["sharpe"])
        cagr = _cagr(initial_capital, float(met["final_capital"]), start_ts, end_ts)
        calmar = _safe_div(cagr, max_drawdown_pct)
        row = {
            "case": case_name,
            "total_return_pct": _f(total_return_pct),
            "cagr": _f(cagr),
            "max_drawdown_pct": _f(max_drawdown_pct),
            "sharpe": _f(sharpe),
            "calmar_ratio": _f(calmar),
            "profit_factor": _f(float(met["profit_factor"])),
            "win_rate": _f(float(met["win_rate"])),
            "loss_streak_max": int(met["max_loss_streak"]),
            "trade_count": int(met["trade_count"]),
            "capital_utilization": _f(float(sim["utilization_after"])),
            "blocked_entries_count": int(sim["blocked_entries_count"]),
        }
        row["score"] = _f(_case_score(row))
        comparison.append(row)
        if case_name == "BASELINE":
            baseline_metrics = row

    if baseline_metrics is None:
        raise SystemExit("Baseline case missing.")

    for row in comparison:
        row["return_change_vs_baseline"] = _f(float(row["total_return_pct"]) - float(baseline_metrics["total_return_pct"]))
        row["mdd_change_vs_baseline"] = _f(float(row["max_drawdown_pct"]) - float(baseline_metrics["max_drawdown_pct"]))
        row["sharpe_change_vs_baseline"] = _f(float(row["sharpe"]) - float(baseline_metrics["sharpe"]))

    ranked = sorted(comparison, key=lambda r: r["score"], reverse=True)
    winner = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None

    pass_like = []
    for row in comparison:
        return_drop_pct = _safe_div((float(row["total_return_pct"]) - baseline_return), max(abs(baseline_return), 1e-9)) * 100.0
        criteria = (
            float(row["max_drawdown_pct"]) < 25.0
            and float(row["sharpe"]) >= 0.8
            and return_drop_pct >= -20.0
            and int(row["loss_streak_max"]) < int(baseline_metrics["loss_streak_max"])
        )
        if criteria:
            pass_like.append(row["case"])

    if len(pass_like) == 1:
        status = "PASS"
    elif len(pass_like) > 1:
        status = "WARNING"
    else:
        # No strict pass: still choose best trade-off case by score
        status = "WARNING" if winner["score"] > 0 else "FAIL"

    selected_overlay = str(winner["case"])
    selected_components_map = {
        "BASELINE": [],
        "DECORRELATION_ONLY": ["DECORRELATION"],
        "FULL_COMBINED": ["DECORRELATION", "POSITION_THROTTLE", "LOSS_CLUSTER_BREAKER", "ADAPTIVE_EXPOSURE"],
        "DECORRELATION_PLUS_POSITION_THROTTLE": ["DECORRELATION", "POSITION_THROTTLE"],
        "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER": ["DECORRELATION", "LIGHT_LOSS_BREAKER"],
    }
    selected_components = selected_components_map.get(selected_overlay, [])

    rejected: list[dict[str, Any]] = []
    for row in comparison:
        if row["case"] == selected_overlay:
            continue
        reasons: list[str] = []
        if float(row["max_drawdown_pct"]) >= float(winner["max_drawdown_pct"]):
            reasons.append("Higher or equal drawdown versus selected overlay.")
        if float(row["sharpe"]) <= float(winner["sharpe"]):
            reasons.append("Lower or equal Sharpe versus selected overlay.")
        if float(row["score"]) < float(winner["score"]):
            reasons.append("Lower composite score.")
        if not reasons:
            reasons.append("Dominated by selected overlay on risk-return balance.")
        rejected.append({"case": row["case"], "reason": " ".join(reasons)})

    reason = (
        f"Selected {selected_overlay} as best score={winner['score']}, balancing return={winner['total_return_pct']}%, "
        f"MDD={winner['max_drawdown_pct']}%, Sharpe={winner['sharpe']}."
    )
    if second is not None and abs(float(winner["score"]) - float(second["score"])) < 0.25:
        status = "WARNING"
        reason += f" Competition remains close with {second['case']}."

    report = {
        "status": status,
        "selected_overlay": selected_overlay,
        "selected_components": selected_components,
        "metrics": {
            "return": winner["total_return_pct"],
            "mdd": winner["max_drawdown_pct"],
            "sharpe": winner["sharpe"],
            "calmar": winner["calmar_ratio"],
        },
        "comparison": comparison,
        "rejected": rejected,
        "reason": reason,
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
    print(f"selected_overlay={selected_overlay}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
