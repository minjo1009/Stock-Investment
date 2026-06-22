from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import run_full_backtest_universe_with_stats, summarize


ENTRY_POLICY = "LIMITED_CHASE"
RISK_POLICY = "TIME_STOP_ONLY"
MODE = "portfolio"
MAX_POSITIONS = 3
INITIAL_EQUITY = 100_000.0
FEE_RATE = 0.0025
SLIPPAGE_RATE = 0.0010


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _calc_mdd_pct(results: list[Any], initial_equity: float) -> float:
    equity = float(initial_equity)
    peak = equity
    max_dd = 0.0
    ordered = sorted(results, key=lambda x: x.trade.exit_time or x.trade.entry_time)
    for row in ordered:
        equity += float(row.net_pnl)
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    return float(max_dd * 100.0)


def _metrics(results: list[Any], stats: Any, initial_equity: float) -> dict[str, float]:
    summary = summarize(results, initial_equity=initial_equity)
    net_pnls = [float(r.net_pnl) for r in results]
    wins = [p for p in net_pnls if p > 0]
    losses = [p for p in net_pnls if p < 0]
    gross_profit = sum(wins)
    gross_loss_abs = abs(sum(losses))
    expectancy = _safe_div(sum(net_pnls), len(net_pnls))
    return {
        "sharpe": _f(summary.sharpe_ratio),
        "mdd_pct": _f(_calc_mdd_pct(results, initial_equity)),
        "trade_count": int(summary.trade_count),
        "win_rate": _f(summary.win_rate),
        "expectancy": _f(expectancy, 4),
        "profit_factor": _f(gross_profit / gross_loss_abs) if gross_loss_abs > 0 else 999.0,
        "fill_rate": _f(float(stats.fill_rate)),
    }


def _decision(baseline: dict[str, float], crb: dict[str, float]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    sharpe_ok = crb["sharpe"] >= (baseline["sharpe"] - 0.02)
    trade_ok = crb["trade_count"] >= int(round(baseline["trade_count"] * 1.15))
    mdd_ok = crb["mdd_pct"] <= (baseline["mdd_pct"] + 2.0)
    expectancy_ok = crb["expectancy"] >= baseline["expectancy"]

    hard_fail = (
        crb["sharpe"] <= (baseline["sharpe"] - 0.10)
        or crb["mdd_pct"] >= (baseline["mdd_pct"] + 4.0)
        or crb["expectancy"] <= (baseline["expectancy"] * 0.7)
    )

    if not sharpe_ok:
        reasons.append("Sharpe guard failed")
    if not trade_ok:
        reasons.append("Trade-count uplift guard failed")
    if not mdd_ok:
        reasons.append("MDD guard failed")
    if not expectancy_ok:
        reasons.append("Expectancy guard failed")
    if hard_fail:
        reasons.append("Kill condition triggered")

    if hard_fail:
        return "FAIL", reasons
    if sharpe_ok and trade_ok and mdd_ok and expectancy_ok:
        return "PASS", reasons
    return "WARNING", reasons


def _markdown(report: dict[str, Any]) -> str:
    b = report["baseline"]
    c = report["crb"]
    d = report["delta"]
    lines: list[str] = []
    lines.append("# Task T101 - CRB Validation")
    lines.append("")
    lines.append("## 1. Metrics Table (Baseline vs CRB)")
    lines.append("| Metric | Baseline | CRB |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Sharpe | {b['sharpe']} | {c['sharpe']} |")
    lines.append(f"| MDD % | {b['mdd_pct']} | {c['mdd_pct']} |")
    lines.append(f"| Trade count | {b['trade_count']} | {c['trade_count']} |")
    lines.append(f"| Win rate % | {b['win_rate']} | {c['win_rate']} |")
    lines.append(f"| Expectancy | {b['expectancy']} | {c['expectancy']} |")
    lines.append(f"| Profit factor | {b['profit_factor']} | {c['profit_factor']} |")
    lines.append("")
    lines.append("## 2. Delta Summary")
    lines.append(f"- delta_sharpe: {d['sharpe']}")
    lines.append(f"- delta_mdd_pct: {d['mdd_pct']}")
    lines.append(f"- delta_trade_count: {d['trade_count']}")
    lines.append(f"- delta_expectancy: {d['expectancy']}")
    lines.append("")
    lines.append("## 3. Decision")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- answer: {report['answer']}")
    lines.append(f"- decision_reasons: {report['decision_reasons']}")
    lines.append("")
    lines.append("## 4. Implementation Check")
    for check in report["implementation_check"]:
        lines.append(f"- {check}")
    lines.append("")
    lines.append("## 5. Failure Diagnosis")
    for item in report["failure_diagnosis"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 6. Next Action")
    lines.append(f"- {report['next_action']}")
    lines.append("")
    lines.append("## Final")
    lines.append("Does compressed range breakout produce better risk-adjusted returns than pure breakout?")
    lines.append(f"- {report['answer']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T101: CRB validation")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_101/task_101_crb_validation.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_101/task_101_crb_validation.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(x).strip().upper() for x in args.symbols if str(x).strip()})
    data_dir = Path(args.data_dir)

    baseline_results, baseline_stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=data_dir,
        initial_equity=INITIAL_EQUITY,
        fee_rate=FEE_RATE,
        slippage_rate=SLIPPAGE_RATE,
        entry_policy=ENTRY_POLICY,
        risk_policy=RISK_POLICY,
        breakout_mode="BASELINE",
        mode=MODE,
        max_positions=MAX_POSITIONS,
    )
    crb_results, crb_stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=data_dir,
        initial_equity=INITIAL_EQUITY,
        fee_rate=FEE_RATE,
        slippage_rate=SLIPPAGE_RATE,
        entry_policy=ENTRY_POLICY,
        risk_policy=RISK_POLICY,
        breakout_mode="CRB",
        mode=MODE,
        max_positions=MAX_POSITIONS,
    )

    baseline = _metrics(baseline_results, baseline_stats, INITIAL_EQUITY)
    crb = _metrics(crb_results, crb_stats, INITIAL_EQUITY)
    delta = {
        "sharpe": _f(crb["sharpe"] - baseline["sharpe"]),
        "mdd_pct": _f(crb["mdd_pct"] - baseline["mdd_pct"]),
        "trade_count": int(crb["trade_count"] - baseline["trade_count"]),
        "expectancy": _f(crb["expectancy"] - baseline["expectancy"], 4),
    }
    status, reasons = _decision(baseline, crb)
    answer = "YES" if status == "PASS" else "NO"

    diagnosis: list[str] = []
    if status == "FAIL":
        if delta["trade_count"] > 0 and delta["sharpe"] < 0:
            diagnosis.append("False-breakout frequency increased faster than quality.")
        if crb["trade_count"] <= baseline["trade_count"]:
            diagnosis.append("Compression gate is too strict and did not improve density.")
        if delta["mdd_pct"] > 0:
            diagnosis.append("Range/compression condition did not control downside clustering.")
    if not diagnosis:
        diagnosis.append("No hard-fail signature detected; inspect regime-level behavior next.")

    report = {
        "task": "T101",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "config": {
            "entry_policy": ENTRY_POLICY,
            "risk_policy": RISK_POLICY,
            "mode": MODE,
            "max_positions": MAX_POSITIONS,
            "initial_equity": INITIAL_EQUITY,
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "crb_rule": {
                "N": 20,
                "max_range_pct": 0.10,
                "compression_ratio": 0.65,
                "touch_count": 2,
            },
        },
        "implementation_check": [
            "Range excludes current bar via shifted rolling high/low.",
            "Compression uses ATR5(t-1) / ATR20(t-6).",
            "All trigger inputs are computed from past bars only.",
            "Baseline and CRB run on identical universe/execution/risk/cost settings.",
        ],
        "baseline": baseline,
        "crb": crb,
        "delta": delta,
        "status": status,
        "answer": answer,
        "decision_reasons": reasons,
        "failure_diagnosis": diagnosis,
        "next_action": "T102 (parameter refinement)" if status == "PASS" else "T101-REV (structure revision)",
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={status}")
    print(f"answer={answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
