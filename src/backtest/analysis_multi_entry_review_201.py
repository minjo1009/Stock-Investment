from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T201-REVIEW - Realism Audit")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- decision: {report['decision']}")
    lines.append(f"- annualized_trade_events: {report['trade_frequency']['annualized_trade_events']}")
    lines.append(f"- annualized_roundtrip_estimate: {report['trade_frequency']['annualized_roundtrip_estimate']}")
    lines.append("")
    lines.append("## 2. Trade Frequency")
    lines.append(f"- total_events_5y: {report['trade_frequency']['total_events_5y']}")
    lines.append(f"- annualized_events: {report['trade_frequency']['annualized_trade_events']}")
    lines.append(f"- estimated_roundtrips_annualized: {report['trade_frequency']['annualized_roundtrip_estimate']}")
    lines.append(f"- below_50_per_year_roundtrip: {report['trade_frequency']['below_50_per_year_roundtrip']}")
    lines.append("")
    lines.append("## 3. Realism Checks")
    lines.append("| Check | Result | Evidence |")
    lines.append("|---|---|---|")
    for c in report["realism_checks"]:
        lines.append(f"| {c['name']} | {c['result']} | {c['evidence']} |")
    lines.append("")
    lines.append("## 4. Risk Notes")
    for n in report["risk_notes"]:
        lines.append(f"- {n}")
    lines.append("")
    lines.append("## 5. Final Verdict")
    lines.append(report["final_answer"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T201 review: realism audit only")
    parser.add_argument(
        "--input-json",
        type=str,
        default="docs/reports/task_201/task_201_multi_entry_v1.json",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_201_review/task_201_review_realism.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_201_review/task_201_review_realism.md",
    )
    args = parser.parse_args(argv)

    src = _load_json(Path(args.input_json))
    total_events = int(src.get("multi_entry_v1", {}).get("trades", 0))
    annualized_events = _safe_div(total_events, 5.0)
    # Conservative proxy: event-based count includes partial/time/stop fragments,
    # so roundtrip count is likely lower than half the event count.
    annualized_roundtrip_est = _safe_div(total_events * 0.4, 5.0)
    below_50 = annualized_roundtrip_est < 50.0

    realism_checks = [
        {
            "name": "Portfolio Capital Constraint",
            "result": "FAIL",
            "evidence": "Per-symbol simulation runs independently; shared capital pool is not enforced across symbols.",
        },
        {
            "name": "Execution Cost Completeness",
            "result": "FAIL",
            "evidence": "Event-level PnL lacks baseline-equivalent explicit roundtrip fee/slippage accounting path.",
        },
        {
            "name": "Global Risk Cap",
            "result": "FAIL",
            "evidence": "Tranche R is bounded per symbol lifecycle, but cross-symbol concurrent risk cap is not enforced.",
        },
        {
            "name": "Intrabar Fill Ordering",
            "result": "WARNING",
            "evidence": "Same-bar high/low usage for partial/stop can introduce optimistic sequencing bias.",
        },
        {
            "name": "Trade Frequency Practicality",
            "result": "WARNING" if below_50 else "PASS",
            "evidence": f"Estimated annualized roundtrip frequency is {annualized_roundtrip_est:.2f} (threshold: 50).",
        },
    ]

    fail_count = sum(1 for x in realism_checks if x["result"] == "FAIL")
    warning_count = sum(1 for x in realism_checks if x["result"] == "WARNING")
    status = "FAIL" if fail_count > 0 else ("WARNING" if warning_count > 0 else "PASS")
    decision = "NOT_PRODUCTION_READY" if status in {"FAIL", "WARNING"} else "PRODUCTION_CANDIDATE"

    report = {
        "task": "T201-REVIEW",
        "status": status,
        "decision": decision,
        "trade_frequency": {
            "total_events_5y": total_events,
            "annualized_trade_events": _f(annualized_events),
            "annualized_roundtrip_estimate": _f(annualized_roundtrip_est),
            "below_50_per_year_roundtrip": bool(below_50),
            "note": "Roundtrip estimate uses conservative event-to-roundtrip compression factor.",
        },
        "realism_checks": realism_checks,
        "risk_notes": [
            "Directionality improvement is acknowledged, but profit magnitude is likely inflated by simulation artifacts.",
            "This review does not modify strategy logic; it only audits operational realism.",
        ],
        "final_answer": "MULTI_ENTRY_V1 shows directional promise, but current backtest realism is insufficient for production adoption.",
    }

    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    mout.write_text(_markdown(report), encoding="utf-8")
    print(f"written_json={jout}")
    print(f"written_md={mout}")
    print(f"status={status}")
    print(f"decision={decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

