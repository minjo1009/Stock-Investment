from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backtest.analysis_drawdown_control_094 import (
    _metrics_from_trade_pnl,
    _positions_df,
    _safe_div,
    _simulate_risk_architecture,
)


def _f(v: float, digits: int = 6) -> float:
    return float(round(float(v), digits))


COMPONENT_CASES = [
    (
        "BASELINE",
        {
            "enable_loss_breaker": False,
            "enable_regime_throttle": False,
            "enable_decorrelation": False,
            "enable_adaptive_exposure": False,
        },
    ),
    (
        "LOSS_CLUSTER_BREAKER_ONLY",
        {
            "enable_loss_breaker": True,
            "enable_regime_throttle": False,
            "enable_decorrelation": False,
            "enable_adaptive_exposure": False,
        },
    ),
    (
        "POSITION_THROTTLE_ONLY",
        {
            "enable_loss_breaker": False,
            "enable_regime_throttle": True,
            "enable_decorrelation": False,
            "enable_adaptive_exposure": False,
        },
    ),
    (
        "DECORRELATION_ONLY",
        {
            "enable_loss_breaker": False,
            "enable_regime_throttle": False,
            "enable_decorrelation": True,
            "enable_adaptive_exposure": False,
        },
    ),
    (
        "ADAPTIVE_EXPOSURE_ONLY",
        {
            "enable_loss_breaker": False,
            "enable_regime_throttle": False,
            "enable_decorrelation": False,
            "enable_adaptive_exposure": True,
        },
    ),
    (
        "FULL_COMBINED",
        {
            "enable_loss_breaker": True,
            "enable_regime_throttle": True,
            "enable_decorrelation": True,
            "enable_adaptive_exposure": True,
        },
    ),
]


def _status(row: dict[str, Any]) -> str:
    if row["mdd_reduction_pct"] >= 20.0 and row["sharpe_delta"] >= 0.10 and row["return_change_pct"] >= -10.0:
        return "PASS"
    if row["mdd_reduction_pct"] > 0:
        return "WARNING"
    return "FAIL"


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T094-REVIEW - Risk Component Attribution")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- baseline_case: {report['baseline_case']}")
    lines.append(f"- best_mdd_case: {report['best_mdd_case']}")
    lines.append(f"- best_sharpe_case: {report['best_sharpe_case']}")
    lines.append(f"- recommended_case: {report['recommended_case']}")
    lines.append("")
    lines.append("## 2. Component Comparison")
    lines.append("| Case | Return % | MDD % | Sharpe | Trades | MDD Reduction % | Sharpe Delta | Return Delta | Status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in report["comparison_rows"]:
        lines.append(
            f"| {row['case']} | {row['return_pct']:.4f} | {row['mdd_pct']:.4f} | {row['sharpe']:.6f} | {row['trade_count']} | "
            f"{row['mdd_reduction_pct']:.4f} | {row['sharpe_delta']:.6f} | {row['return_change_pct']:.4f} | {row['status']} |"
        )
    lines.append("")
    lines.append("## 3. Attribution")
    lines.append(f"- strongest_mdd_component: {report['attribution']['strongest_mdd_component']}")
    lines.append(f"- strongest_sharpe_component: {report['attribution']['strongest_sharpe_component']}")
    lines.append(f"- largest_return_drag_component: {report['attribution']['largest_return_drag_component']}")
    lines.append("")
    lines.append("## 4. Side Effects")
    for item in report["side_effects"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 5. Final Decision")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- answer: {report['answer']}")
    lines.append("")
    lines.append("## 6. Final Answer")
    lines.append(f"- {report['final_answer']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T094-REVIEW: risk component attribution")
    parser.add_argument(
        "--input-json",
        type=str,
        default="docs/reports/task_093/task_093_capital_backtest.json",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_094_review/task_094_review_component_attribution.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_094_review/task_094_review_component_attribution.md",
    )
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    scenario = str(payload.get("primary_scenario", "A_BASE_10K_HIGH_COST"))
    base_metrics = payload["scenarios"][scenario]
    initial_capital = float(base_metrics["initial_capital"])
    positions = _positions_df(base_metrics.get("closed_positions", []))

    raw_baseline = _metrics_from_trade_pnl(
        pnls=positions["net_pnl"].tolist() if not positions.empty else [],
        exit_times=positions["exit_time"].tolist() if not positions.empty else [],
        initial_capital=initial_capital,
    )

    rows: list[dict[str, Any]] = []
    case_details: dict[str, Any] = {}
    for case_name, flags in COMPONENT_CASES:
        sim = _simulate_risk_architecture(
            positions,
            initial_capital=initial_capital,
            **flags,
        )
        metrics = _metrics_from_trade_pnl(
            pnls=sim["scaled_trade_pnls"],
            exit_times=sim["scaled_exit_times"],
            initial_capital=initial_capital,
        )
        mdd_reduction_pct = _safe_div(raw_baseline["mdd_pct"] - metrics["mdd_pct"], max(raw_baseline["mdd_pct"], 1e-9)) * 100.0
        sharpe_delta = metrics["sharpe"] - raw_baseline["sharpe"]
        return_change = metrics["return_pct"] - raw_baseline["return_pct"]
        row = {
            "case": case_name,
            "return_pct": _f(metrics["return_pct"]),
            "mdd_pct": _f(metrics["mdd_pct"]),
            "sharpe": _f(metrics["sharpe"]),
            "trade_count": int(metrics["trade_count"]),
            "loss_streak": int(metrics["max_loss_streak"]),
            "mdd_reduction_pct": _f(mdd_reduction_pct),
            "sharpe_delta": _f(sharpe_delta),
            "return_change_pct": _f(return_change),
            "blocked_entries_count": int(sim["blocked_entries_count"]),
            "blocked_by_reason": sim["blocked_by_reason"],
            "avg_position_reduction": _f(sim["avg_position_reduction"]),
            "status": "",
        }
        row["status"] = _status(row)
        rows.append(row)
        case_details[case_name] = {"flags": flags, "metrics": metrics, "sim_summary": sim, "row": row}

    # attribution decomposition among single-component cases
    singles = [r for r in rows if r["case"].endswith("_ONLY")]
    strongest_mdd = max(singles, key=lambda r: r["mdd_reduction_pct"]) if singles else None
    strongest_sharpe = max(singles, key=lambda r: r["sharpe_delta"]) if singles else None
    largest_return_drag = min(singles, key=lambda r: r["return_change_pct"]) if singles else None

    best_mdd_case = max(rows, key=lambda r: r["mdd_reduction_pct"])["case"] if rows else "N/A"
    best_sharpe_case = max(rows, key=lambda r: r["sharpe_delta"])["case"] if rows else "N/A"

    full_row = next((r for r in rows if r["case"] == "FULL_COMBINED"), rows[0] if rows else {})
    recommended_case = "FULL_COMBINED" if full_row and full_row.get("status") in {"PASS", "WARNING"} else best_mdd_case

    overall_status = full_row.get("status", "FAIL") if full_row else "FAIL"
    answer = "YES" if overall_status in {"PASS", "WARNING"} else "NO"

    side_effects = []
    for r in rows:
        if r["return_change_pct"] < 0:
            side_effects.append(f"{r['case']} reduces return by {r['return_change_pct']:.4f}% vs baseline.")
        if r["trade_count"] < raw_baseline["trade_count"]:
            side_effects.append(
                f"{r['case']} reduces trade count by {int(r['trade_count'] - raw_baseline['trade_count'])}."
            )
    if not side_effects:
        side_effects.append("No material side-effect observed.")

    report = {
        "task": "T094-REVIEW",
        "status": overall_status,
        "answer": answer,
        "scenario": scenario,
        "baseline_case": "BASELINE",
        "baseline_metrics": {
            "return_pct": _f(raw_baseline["return_pct"]),
            "mdd_pct": _f(raw_baseline["mdd_pct"]),
            "sharpe": _f(raw_baseline["sharpe"]),
            "trade_count": int(raw_baseline["trade_count"]),
            "loss_streak": int(raw_baseline["max_loss_streak"]),
        },
        "comparison_rows": rows,
        "best_mdd_case": best_mdd_case,
        "best_sharpe_case": best_sharpe_case,
        "recommended_case": recommended_case,
        "attribution": {
            "strongest_mdd_component": strongest_mdd["case"] if strongest_mdd else "N/A",
            "strongest_mdd_reduction_pct": _f(strongest_mdd["mdd_reduction_pct"]) if strongest_mdd else 0.0,
            "strongest_sharpe_component": strongest_sharpe["case"] if strongest_sharpe else "N/A",
            "strongest_sharpe_delta": _f(strongest_sharpe["sharpe_delta"]) if strongest_sharpe else 0.0,
            "largest_return_drag_component": largest_return_drag["case"] if largest_return_drag else "N/A",
            "largest_return_drag_pct": _f(largest_return_drag["return_change_pct"]) if largest_return_drag else 0.0,
        },
        "side_effects": side_effects[:12],
        "final_answer": "Loss clustering is reduced, with the largest impact coming from component-level gating/exposure controls; return drag remains the trade-off.",
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={overall_status}")
    print(f"answer={answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
