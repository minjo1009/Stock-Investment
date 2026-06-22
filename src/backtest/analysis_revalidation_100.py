from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backtest.analysis_drawdown_control_094 import _positions_df, _simulate_risk_architecture
from backtest.analysis_revalidation_096 import _overlay_flags


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _f(value: float, digits: int = 6) -> float:
    return float(round(float(value), digits))


def _run_python(script: str, args: list[str]) -> dict[str, Any]:
    cmd = [sys.executable, script, *args]
    env = dict(**__import__("os").environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC_DIR) if not existing else f"{SRC_DIR};{existing}"
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    return {
        "cmd": " ".join(cmd),
        "stdout": proc.stdout.strip(),
    }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _row_key(row: dict[str, Any]) -> tuple[str, str, str, float]:
    return (
        str(row.get("symbol", "")),
        str(row.get("entry_time", "")),
        str(row.get("exit_time", "")),
        _f(_safe_float(row.get("net_pnl", 0.0)), 4),
    )


def _markdown(report: dict[str, Any]) -> str:
    c = report["capital_metrics"]
    lines: list[str] = []
    lines.append("# Task T100 - A_10 Full Revalidation")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- adopted_breakout: {report['adopted_breakout']}")
    lines.append(f"- alignment_major_mismatch_count: {report['alignment']['major_mismatch_count']}")
    lines.append("")
    lines.append("## 2. Capital Metrics (A_BASE_10K_HIGH_COST)")
    lines.append(f"- sharpe: {c['sharpe']}")
    lines.append(f"- return_pct: {c['return_pct']}")
    lines.append(f"- mdd_pct: {c['max_drawdown_pct']}")
    lines.append(f"- profit_factor: {c['profit_factor']}")
    lines.append(f"- win_rate: {c['win_rate']}")
    lines.append(f"- trade_count: {c['trade_count']}")
    lines.append("")
    lines.append("## 3. Signal Density")
    lines.append(f"- baseline_generated_signals: {report['signal_density']['baseline_generated_signals']}")
    lines.append(f"- a10_generated_signals: {report['signal_density']['new_generated_signals']}")
    lines.append(f"- delta_generated_signals: {report['signal_density']['delta_generated_signals']}")
    lines.append("")
    lines.append("## 4. Risk Overlay Interaction")
    lines.append(f"- blocked_count: {report['risk_overlay_interaction']['blocked_count']}")
    lines.append(f"- blocked_winners: {report['risk_overlay_interaction']['blocked_winners']}")
    lines.append(f"- blocked_losers: {report['risk_overlay_interaction']['blocked_losers']}")
    lines.append(f"- blocked_by_reason: {report['risk_overlay_interaction']['blocked_by_reason']}")
    lines.append("")
    lines.append("## 5. Stability")
    lines.append(f"- capital_utilization: {report['stability']['capital_utilization']}")
    lines.append(f"- max_loss_streak: {report['stability']['max_loss_streak']}")
    lines.append(f"- avg_trade_return_pct: {report['stability']['avg_trade_return_pct']}")
    lines.append(f"- baseline_sharpe_t099: {report['stability']['baseline_sharpe_t099']}")
    lines.append(f"- sharpe_delta_vs_t099_baseline: {report['stability']['sharpe_delta_vs_t099_baseline']}")
    lines.append("")
    lines.append("## 6. Commands")
    for row in report["commands"]:
        lines.append(f"- `{row['cmd']}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T100: A_10 full-system revalidation")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_100/task_100_full_revalidation.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_100/task_100_full_revalidation.md")
    args = parser.parse_args(argv)

    task100_dir = Path(args.json_out).resolve().parent
    task100_dir.mkdir(parents=True, exist_ok=True)

    t089_json = task100_dir / "_task_089_market_signal_refresh.json"
    t089_md = task100_dir / "_task_089_market_signal_refresh.md"
    t092_json = task100_dir / "_task_092_signal_alignment.json"
    t092_md = task100_dir / "_task_092_signal_alignment.md"
    t093_json = task100_dir / "_task_093_capital_backtest.json"
    t093_md = task100_dir / "_task_093_capital_backtest.md"
    t099_json = task100_dir / "_task_099_a_family.json"
    t099_md = task100_dir / "_task_099_a_family.md"

    commands: list[dict[str, Any]] = []
    commands.append(
        _run_python(
            "src/app/task_089_market_data_signal_refresh.py",
            ["--json-out", str(t089_json), "--md-out", str(t089_md)],
        )
    )
    commands.append(
        _run_python(
            "src/app/task_092_signal_alignment_audit.py",
            ["--json-out", str(t092_json), "--md-out", str(t092_md)],
        )
    )
    commands.append(
        _run_python(
            "src/backtest/analysis_capital_backtest_093.py",
            ["--json-out", str(t093_json), "--md-out", str(t093_md)],
        )
    )
    commands.append(
        _run_python(
            "src/backtest/analysis_breakout_sensitivity_099.py",
            ["--family", "A", "--json-out", str(t099_json), "--md-out", str(t099_md)],
        )
    )

    t092 = _load_json(t092_json)
    t093 = _load_json(t093_json)
    t099 = _load_json(t099_json)
    t099_review = _load_json(Path("docs/reports/task_099_review/task_099_review_breakout_decision.json"))
    t095 = _load_json(Path("docs/reports/task_095/task_095_risk_adoption.json"))

    scenario_name = str(t093.get("primary_scenario", "A_BASE_10K_HIGH_COST"))
    scenario = t093["scenarios"][scenario_name]

    runs = {str(r["run_id"]): r for r in t099.get("runs", [])}
    baseline_run = runs.get("BASELINE", {})
    a10_run = runs.get("A_10", {})

    baseline_generated = _safe_int(t099_review.get("baseline_snapshot", {}).get("generated_signals", 39), 39)
    a10_generated = _safe_int(a10_run.get("signal_density", {}).get("generated_signals", 0))

    positions = _positions_df(scenario.get("closed_positions", []))
    overlay = str(t095.get("selected_overlay", "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER"))
    flags, overrides = _overlay_flags(overlay)
    sim = _simulate_risk_architecture(positions, initial_capital=_safe_float(scenario.get("initial_capital", 10_000.0)), **flags, **overrides)
    risk_overlay_row = a10_run.get("filtered_quality", {}).get("RISK_OVERLAY", {})
    if isinstance(risk_overlay_row, dict) and _safe_int(risk_overlay_row.get("count", 0)) > 0:
        blocked_winners = _safe_int(risk_overlay_row.get("winners_20", 0))
        blocked_losers = _safe_int(risk_overlay_row.get("losers_20", 0))
    else:
        accepted_keys = {_row_key(r) for r in sim.get("accepted_trade_rows", [])}
        blocked_rows = [row for row in scenario.get("closed_positions", []) if _row_key(row) not in accepted_keys]
        blocked_winners = sum(1 for row in blocked_rows if _safe_float(row.get("net_pnl", 0.0)) > 0)
        blocked_losers = sum(1 for row in blocked_rows if _safe_float(row.get("net_pnl", 0.0)) < 0)

    alignment_major = _safe_int(t092.get("major_diff_count", 0))
    status = "PASS" if alignment_major == 0 else "FAIL"
    status = "WARNING" if status == "PASS" and a10_generated <= 0 else status

    report = {
        "task": "T100",
        "status": status,
        "adopted_breakout": "A_10",
        "decision_source": "docs/reports/task_099_review/task_099_review_breakout_decision.json",
        "alignment": {
            "status": t092.get("status", "FAIL"),
            "major_mismatch_count": alignment_major,
            "minor_mismatch_count": _safe_int(t092.get("minor_diff_count", 0)),
            "match_count": _safe_int(t092.get("match_count", 0)),
            "total_cases": _safe_int(t092.get("total_cases", 0)),
        },
        "capital_metrics": {
            "scenario": scenario_name,
            "sharpe": _f(_safe_float(scenario.get("sharpe", 0.0))),
            "return_pct": _f(_safe_float(scenario.get("total_return_pct", 0.0))),
            "max_drawdown_pct": _f(_safe_float(scenario.get("max_drawdown_pct", 0.0))),
            "profit_factor": _f(_safe_float(scenario.get("profit_factor", 0.0))),
            "win_rate": _f(_safe_float(scenario.get("win_rate", 0.0))),
            "trade_count": _safe_int(scenario.get("trade_count", 0)),
        },
        "signal_density": {
            "baseline_generated_signals": baseline_generated,
            "new_generated_signals": a10_generated,
            "delta_generated_signals": a10_generated - baseline_generated,
            "baseline_executed_signals": _safe_int(baseline_run.get("signal_density", {}).get("executed_signals", 0)),
            "new_executed_signals": _safe_int(a10_run.get("signal_density", {}).get("executed_signals", 0)),
        },
        "risk_overlay_interaction": {
            "overlay": overlay,
            "blocked_count": _safe_int(sim.get("blocked_entries_count", 0)),
            "blocked_winners": blocked_winners,
            "blocked_losers": blocked_losers,
            "blocked_by_reason": sim.get("blocked_by_reason", {}),
        },
        "stability": {
            "capital_utilization": _f(_safe_float(scenario.get("capital_utilization", 0.0))),
            "max_loss_streak": _safe_int(scenario.get("max_loss_streak", 0)),
            "avg_trade_return_pct": _f(_safe_float(scenario.get("avg_trade_return_pct", 0.0))),
            "baseline_sharpe_t099": _f(_safe_float(baseline_run.get("portfolio_metrics", {}).get("sharpe", 0.0))),
            "sharpe_delta_vs_t099_baseline": _f(
                _safe_float(scenario.get("sharpe", 0.0)) - _safe_float(baseline_run.get("portfolio_metrics", {}).get("sharpe", 0.0))
            ),
            "a10_sharpe_t099": _f(_safe_float(a10_run.get("portfolio_metrics", {}).get("sharpe", 0.0))),
        },
        "commands": commands,
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
    print(f"a10_generated_signals={a10_generated}")
    print(f"alignment_major_mismatch_count={alignment_major}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
