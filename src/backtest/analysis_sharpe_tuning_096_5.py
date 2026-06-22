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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cagr(initial_capital: float, final_capital: float, start: pd.Timestamp, end: pd.Timestamp) -> float:
    if initial_capital <= 0 or final_capital <= 0:
        return -100.0
    years = max((end - start).days / 365.25, 1.0 / 365.25)
    return float(((final_capital / initial_capital) ** (1.0 / years) - 1.0) * 100.0)


def _calmar(cagr: float, mdd_pct: float) -> float:
    return _safe_div(cagr, max(mdd_pct, 1e-9))


def _apply_symbol_scaling(
    pnls: list[float],
    accepted_rows: list[dict[str, Any]],
    symbol_scale: dict[str, float],
) -> tuple[list[float], float]:
    if not pnls or not accepted_rows:
        return pnls, 1.0
    out: list[float] = []
    weighted_scale_sum = 0.0
    for i, pnl in enumerate(pnls):
        row = accepted_rows[i] if i < len(accepted_rows) else {}
        symbol = str(row.get("symbol", ""))
        s = float(symbol_scale.get(symbol, 1.0))
        out.append(float(pnl) * s)
        weighted_scale_sum += s
    avg_scale = weighted_scale_sum / max(len(out), 1)
    return out, float(avg_scale)


def _case_metrics(
    positions: pd.DataFrame,
    *,
    initial_capital: float,
    enable_loss_breaker: bool,
    enable_decorrelation: bool,
    loss_streak_threshold: int,
    cooldown_trades: int,
    max_concurrent_positions: int,
    sector_cap_ratio: float,
    symbol_scale: dict[str, float] | None = None,
) -> dict[str, Any]:
    sim = _simulate_risk_architecture(
        positions,
        initial_capital=initial_capital,
        enable_loss_breaker=enable_loss_breaker,
        enable_regime_throttle=False,
        enable_decorrelation=enable_decorrelation,
        enable_adaptive_exposure=False,
        loss_streak_threshold=loss_streak_threshold,
        cooldown_trades=cooldown_trades,
        max_concurrent_positions=max_concurrent_positions,
        sector_cap_ratio=sector_cap_ratio,
    )
    scaled_pnls = list(sim["scaled_trade_pnls"])
    util_after = float(sim["utilization_after"])
    if symbol_scale:
        scaled_pnls, avg_scale = _apply_symbol_scaling(
            scaled_pnls,
            list(sim.get("accepted_trade_rows", [])),
            symbol_scale,
        )
        util_after = util_after * avg_scale

    met = _metrics_from_trade_pnl(
        pnls=scaled_pnls,
        exit_times=list(sim["scaled_exit_times"]),
        initial_capital=initial_capital,
    )
    return {
        "metrics": met,
        "simulation": sim,
        "capital_utilization": _f(util_after),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T096.5 - Sharpe Gap Closure")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- target_sharpe: {report['target_sharpe']}")
    lines.append(f"- baseline_sharpe: {report['baseline_sharpe']}")
    lines.append(f"- best_sharpe: {report['best_sharpe']}")
    lines.append(f"- gap_closed: {report['gap_closed']}")
    lines.append(f"- status: {report['status']}")
    lines.append("")
    lines.append("## 2. Scenario Comparison")
    lines.append("| Case | Sharpe | Return | MDD | Utilization |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in report["comparison"]:
        lines.append(
            f"| {row['case']} | {row['sharpe']} | {row['return_pct']} | {row['mdd_pct']} | {row['capital_utilization']} |"
        )
    lines.append("")
    lines.append("## 3. Sharpe Gap Analysis")
    lines.append(f"- gap_before: {report['target_sharpe'] - report['baseline_sharpe']:.4f}")
    lines.append(f"- gap_after: {report['target_sharpe'] - report['best_sharpe']:.4f}")
    lines.append(f"- gap_closed: {report['gap_closed']}")
    lines.append("")
    lines.append("## 4. Trade-off")
    lines.append(f"- selected_case: {report['selected_case']}")
    lines.append(f"- return: {report['return']}")
    lines.append(f"- mdd: {report['mdd']}")
    lines.append(f"- utilization: {report['utilization']}")
    lines.append("")
    lines.append("## 5. Selected Adjustment")
    lines.append(f"- {report['selected_adjustment']}")
    lines.append("")
    lines.append("## 6. Decision")
    lines.append(f"- {report['status']}")
    lines.append("")
    lines.append("## 7. Final Answer")
    lines.append(f"Was Sharpe gap successfully closed without damaging risk profile? {report['answer']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T096.5: Sharpe gap closure by risk overlay micro-tuning")
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--input-t095", type=str, default="docs/reports/task_095/task_095_risk_adoption.json")
    parser.add_argument("--input-t096", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument("--input-t096-review", type=str, default="docs/reports/task_096_review/task_096_review_sharpe_gap.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_096_5/task_096_5_sharpe_tuning.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_096_5/task_096_5_sharpe_tuning.md")
    args = parser.parse_args(argv)

    t093 = _load_json(Path(args.input_t093))
    t095 = _load_json(Path(args.input_t095))
    t096 = _load_json(Path(args.input_t096))
    _ = _load_json(Path(args.input_t096_review))

    scenario_name = str(t096.get("baseline_scenario", t093.get("primary_scenario", "A_BASE_10K_HIGH_COST")))
    scenario = t093["scenarios"][scenario_name]
    initial_capital = float(scenario["initial_capital"])
    positions = _positions_df(scenario.get("closed_positions", []))
    if positions.empty:
        raise SystemExit("No closed positions available for T096.5.")

    start_ts = pd.Timestamp(positions["entry_time"].min())
    end_ts = pd.Timestamp(positions["exit_time"].max())
    target_sharpe = 0.7

    cases = [
        {
            "case": "CURRENT_BASELINE",
            "params": {
                "enable_loss_breaker": True,
                "enable_decorrelation": True,
                "loss_streak_threshold": 4,
                "cooldown_trades": 1,
                "max_concurrent_positions": 3,
                "sector_cap_ratio": 0.6,
                "symbol_scale": {},
            },
            "adjustment": "DECORRELATION + LIGHT_LOSS_BREAKER (current T096).",
        },
        {
            "case": "LIGHT_DECORRELATION",
            "params": {
                "enable_loss_breaker": True,
                "enable_decorrelation": True,
                "loss_streak_threshold": 4,
                "cooldown_trades": 1,
                "max_concurrent_positions": 4,
                "sector_cap_ratio": 0.75,
                "symbol_scale": {},
            },
            "adjustment": "Relax decorrelation: concurrent positions +1 and sector cap ratio 0.60->0.75.",
        },
        {
            "case": "LIGHT_LOSS_BREAKER",
            "params": {
                "enable_loss_breaker": True,
                "enable_decorrelation": True,
                "loss_streak_threshold": 5,
                "cooldown_trades": 1,
                "max_concurrent_positions": 3,
                "sector_cap_ratio": 0.6,
                "symbol_scale": {},
            },
            "adjustment": "Loosen loss breaker: threshold 4->5 with same cooldown 1 trade.",
        },
        {
            "case": "COMBINED_LIGHT",
            "params": {
                "enable_loss_breaker": True,
                "enable_decorrelation": True,
                "loss_streak_threshold": 5,
                "cooldown_trades": 1,
                "max_concurrent_positions": 4,
                "sector_cap_ratio": 0.75,
                "symbol_scale": {"NVDA": 0.85, "MSFT": 0.9, "AMD": 0.85},
            },
            "adjustment": (
                "Relax decorrelation + loosen loss breaker + symbol scaling "
                "(NVDA/MSFT/AMD => 0.85/0.90/0.85)."
            ),
        },
    ]

    rows: list[dict[str, Any]] = []
    case_details: dict[str, Any] = {}
    for c in cases:
        out = _case_metrics(positions, initial_capital=initial_capital, **c["params"])
        met = out["metrics"]
        cagr = _cagr(initial_capital, float(met["final_capital"]), start_ts, end_ts)
        calmar = _calmar(cagr, float(met["mdd_pct"]))
        row = {
            "case": c["case"],
            "sharpe": _f(float(met["sharpe"])),
            "return_pct": _f(float(met["return_pct"])),
            "mdd_pct": _f(float(met["mdd_pct"])),
            "calmar": _f(calmar),
            "loss_streak_max": int(met["max_loss_streak"]),
            "capital_utilization": _f(float(out["capital_utilization"])),
            "trade_count": int(met["trade_count"]),
        }
        rows.append(row)
        case_details[c["case"]] = {
            "adjustment": c["adjustment"],
            "params": c["params"],
            "simulation": out["simulation"],
            "metrics": row,
        }

    baseline = next(r for r in rows if r["case"] == "CURRENT_BASELINE")
    t092_alignment_ok = str(t096.get("consistency", {}).get("t092_status", "FAIL")).upper() == "PASS"

    def meets_pass(r: dict[str, Any]) -> bool:
        return (
            r["sharpe"] >= target_sharpe
            and r["mdd_pct"] <= (baseline["mdd_pct"] + 0.3)
            and r["return_pct"] >= (baseline["return_pct"] * 0.95)
            and t092_alignment_ok
        )

    pass_candidates = [r for r in rows if meets_pass(r)]
    best_row = max(rows, key=lambda x: x["sharpe"])
    selected = max(pass_candidates, key=lambda x: x["sharpe"]) if pass_candidates else best_row

    if pass_candidates:
        status = "PASS"
        answer = "YES"
    elif 0.68 <= float(selected["sharpe"]) < 0.70:
        status = "WARNING"
        answer = "NO"
    else:
        status = "FAIL"
        answer = "NO"

    gap_closed = bool(selected["sharpe"] >= target_sharpe)
    report = {
        "status": status,
        "baseline_sharpe": _f(float(baseline["sharpe"]), 4),
        "best_sharpe": _f(float(selected["sharpe"]), 6),
        "selected_case": selected["case"],
        "return": _f(float(selected["return_pct"])),
        "mdd": _f(float(selected["mdd_pct"])),
        "utilization": _f(float(selected["capital_utilization"])),
        "gap_closed": gap_closed,
        "target_sharpe": target_sharpe,
        "comparison": rows,
        "selected_adjustment": case_details[selected["case"]]["adjustment"],
        "acceptance_check": {
            "sharpe_gte_0_70": bool(selected["sharpe"] >= target_sharpe),
            "mdd_within_baseline_plus_0_3": bool(selected["mdd_pct"] <= (baseline["mdd_pct"] + 0.3)),
            "return_gte_95pct_baseline": bool(selected["return_pct"] >= (baseline["return_pct"] * 0.95)),
            "t092_alignment_maintained": bool(t092_alignment_ok),
        },
        "answer": answer,
        "notes": {
            "fixed_context_pack_only": [
                "src/backtest/analysis_revalidation_096.py",
                "src/backtest/analysis_risk_adoption_095.py",
                "src/backtest/analysis_drawdown_control_094.py",
                "docs/reports/task_096/task_096_revalidation.json",
                "docs/reports/task_096_review/task_096_review_sharpe_gap.json",
                "docs/reports/task_095/task_095_risk_adoption.json",
            ],
            "selected_overlay_input": t095.get("selected_overlay"),
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
    print(f"status={status}")
    print(f"selected_case={selected['case']}")
    print(f"best_sharpe={report['best_sharpe']}")
    print(f"gap_closed={gap_closed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

