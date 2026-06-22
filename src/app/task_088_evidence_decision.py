from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MIN_SAMPLE = {
    "minimum_trading_days": 5,
    "minimum_order_attempts": 10,
    "minimum_filled_orders": 5,
    "minimum_cancel_events": 1,
    "minimum_eod_reviews": 5,
    "minimum_reconciliation_checks": 5,
}

FAIL_REASONS = {
    "UNKNOWN_ORDER_EXISTS",
    "RECONCILIATION_CRITICAL_EXISTS",
    "UNRESOLVED_LATE_FILL",
    "CANCEL_LOOP_UNKNOWN_ESCALATION",
    "BROKER_LOCAL_POSITION_MISMATCH",
    "MARKET_ORDER_PATH_TRIGGERED",
    "LIVE_ENVIRONMENT_DETECTED",
    "RISK_GUARD_BREACH",
}


def _safe_ratio(num: float, den: float) -> float:
    return (num / den) if den else 0.0


def _load_evidence(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


def _evidence_complete(row: dict[str, Any]) -> bool:
    required = {
        "run_id",
        "started_at",
        "ended_at",
        "status",
        "order_attempts",
        "filled_orders",
        "cancelled_orders",
        "unknown_events",
        "reconciliation_checks",
        "reconciliation_critical_count",
    }
    return required.issubset(set(row.keys()))


def evaluate_aggregate_status(summary: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    if summary["unknown_events"] > 0:
        failures.append("UNKNOWN_EVENT_DETECTED")
    if summary["reconciliation_critical_count"] > 0:
        failures.append("RECONCILIATION_CRITICAL_DETECTED")
    if summary["unresolved_late_fill"] > 0:
        failures.append("UNRESOLVED_LATE_FILL_DETECTED")
    if summary["market_order_path_count"] > 0:
        failures.append("MARKET_ORDER_PATH_DETECTED")
    if summary["risk_guard_breach_count"] > 0:
        failures.append("RISK_GUARD_BREACH_DETECTED")
    if summary["live_env_count"] > 0:
        failures.append("LIVE_ENV_DETECTED")

    sample_met = (
        summary["trading_days_observed"] >= MIN_SAMPLE["minimum_trading_days"]
        and summary["order_attempts"] >= MIN_SAMPLE["minimum_order_attempts"]
        and summary["filled_orders"] >= MIN_SAMPLE["minimum_filled_orders"]
        and summary["cancelled_orders"] >= MIN_SAMPLE["minimum_cancel_events"]
        and summary["eod_reviews_completed"] >= MIN_SAMPLE["minimum_eod_reviews"]
        and summary["reconciliation_checks"] >= MIN_SAMPLE["minimum_reconciliation_checks"]
    )
    if not sample_met:
        warnings.append("MINIMUM_SAMPLE_NOT_MET")
    if summary["cancelled_orders"] == 0:
        warnings.append("NO_CANCEL_SAMPLE")
    if summary["order_attempts"] == 0:
        warnings.append("NO_ORDER_SAMPLE")
    if summary["slippage_drift_flag"]:
        warnings.append("SLIPPAGE_DRIFT")
    if float(summary.get("data_fresh_ratio", 0.0)) < 0.8:
        warnings.append("LOW_DATA_FRESHNESS")
    if float(summary.get("missing_bar_ratio", 1.0)) > 0.4:
        warnings.append("HIGH_MISSING_BAR_RATIO")

    if failures:
        return "FAIL", sorted(set(failures)), sorted(set(warnings))
    if not sample_met:
        return "WARNING", sorted(set(failures)), sorted(set(warnings))
    if summary["cancel_success_rate"] < 1.0 and summary["cancelled_orders"] > 0:
        warnings.append("CANCEL_SUCCESS_NOT_100")
        return "WARNING", sorted(set(failures)), sorted(set(warnings))
    return "PASS", sorted(set(failures)), sorted(set(warnings))


def _to_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 088 - Evidence Aggregation & Decision Engine")
    lines.append("")
    lines.append(f"- final_status: {report['final_decision']['status']}")
    lines.append(f"- total_runs: {report['aggregate_metrics']['total_runs']}")
    lines.append(f"- trading_days_observed: {report['aggregate_metrics']['trading_days_observed']}")
    lines.append("")
    lines.append("## Aggregate Metrics")
    for key, value in report["aggregate_metrics"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Minimum Sample Criteria")
    for key, value in report["minimum_sample_criteria"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Decision")
    lines.append(f"- status: {report['final_decision']['status']}")
    for reason in report["final_decision"]["failure_reasons"]:
        lines.append(f"- failure_reason: {reason}")
    for reason in report["final_decision"]["warnings"]:
        lines.append(f"- warning: {reason}")
    lines.append("")
    lines.append("## Notes")
    for note in report["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 088: aggregate Task 087 evidence and decide PASS/WARNING/FAIL")
    parser.add_argument("--runs-dir", type=str, default="docs/reports/task_087/runs")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_088/task_088_evidence_summary.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_088/task_088_evidence_summary.md")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    files = sorted(runs_dir.glob("*.json"))
    evidences: list[dict[str, Any]] = []
    ignored_files: list[str] = []
    for path in files:
        row = _load_evidence(path)
        if row is None:
            ignored_files.append(str(path))
            continue
        evidences.append(row)

    trading_days = {
        str(row.get("started_at", ""))[:10]
        for row in evidences
        if str(row.get("started_at", ""))[:10]
    }
    valid_count = sum(1 for row in evidences if _evidence_complete(row))
    completeness = _safe_ratio(valid_count, len(evidences)) if evidences else 0.0

    total_realized_pnl = sum(float(row.get("realized_pnl") or 0.0) for row in evidences)
    pnl_seq = [float(row.get("realized_pnl") or 0.0) for row in evidences]
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    for pnl in pnl_seq:
        cum += pnl
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
        if pnl > 0:
            gross_profit += pnl
        elif pnl < 0:
            gross_loss += abs(pnl)
    paper_pf = (gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

    agg = {
        "trading_days_observed": len(trading_days),
        "total_runs": len(evidences),
        "order_attempts": int(sum(int(row.get("order_attempts") or 0) for row in evidences)),
        "submitted_orders": int(sum(int(row.get("submitted_orders") or 0) for row in evidences)),
        "filled_orders": int(sum(int(row.get("filled_orders") or 0) for row in evidences)),
        "cancelled_orders": int(sum(int(row.get("cancelled_orders") or 0) for row in evidences)),
        "partial_fills": int(sum(int(row.get("partial_fills") or 0) for row in evidences)),
        "late_fills": int(sum(int(row.get("late_fills") or 0) for row in evidences)),
        "timeout_events": int(sum(int(row.get("timeout_events") or 0) for row in evidences)),
        "unknown_events": int(sum(int(row.get("unknown_events") or 0) for row in evidences)),
        "reconciliation_checks": int(sum(int(row.get("reconciliation_checks") or 0) for row in evidences)),
        "reconciliation_critical_count": int(sum(int(row.get("reconciliation_critical_count") or 0) for row in evidences)),
        "fill_rate": round(_safe_ratio(sum(int(row.get("filled_orders") or 0) for row in evidences), max(sum(int(row.get("order_attempts") or 0) for row in evidences), 1)), 6),
        "cancel_success_rate": round(
            _safe_ratio(
                sum(int(row.get("cancelled_orders") or 0) for row in evidences),
                max(sum(int(row.get("cancelled_orders") or 0) + int(row.get("timeout_events") or 0) for row in evidences), 1),
            ),
            6,
        ),
        "timeout_rate": round(_safe_ratio(sum(int(row.get("timeout_events") or 0) for row in evidences), max(sum(int(row.get("order_attempts") or 0) for row in evidences), 1)), 6),
        "average_slippage": round(_safe_ratio(sum(float(row.get("average_slippage") or 0.0) for row in evidences), max(len(evidences), 1)), 6),
        "max_slippage": round(max([float(row.get("max_slippage") or 0.0) for row in evidences], default=0.0), 6),
        "realized_pnl": round(total_realized_pnl, 6),
        "paper_pf": round(paper_pf, 6) if paper_pf != float("inf") else "INF",
        "paper_mdd": round(max_dd, 6),
        "evidence_completeness": round(completeness, 6),
        "eod_reviews_completed": int(sum(1 for row in evidences if bool(row.get("eod_review_completed")))),
        "unresolved_late_fill": int(sum(int(row.get("unresolved_late_fill_count") or 0) for row in evidences)),
        "market_order_path_count": int(sum(1 for row in evidences if bool(row.get("market_order_attempted")))),
        "risk_guard_breach_count": int(sum(1 for row in evidences if "RISK_GUARD_BREACH" in (row.get("failure_reasons") or []))),
        "live_env_count": int(sum(1 for row in evidences if str(row.get("environment") or "").lower() not in {"paper", ""})),
        "slippage_drift_flag": any(abs(float(row.get("average_slippage") or 0.0)) > 0.02 for row in evidences),
        "data_fresh_ratio": round(_safe_ratio(sum(float(row.get("data_fresh_ratio") or 0.0) for row in evidences), max(len(evidences), 1)), 6),
        "missing_bar_ratio": round(_safe_ratio(sum(float(row.get("missing_bar_ratio") or 1.0) for row in evidences), max(len(evidences), 1)), 6),
        "signal_generated_runs": int(sum(int(row.get("signal_generated_run") or 0) for row in evidences)),
    }

    status, failure_reasons, warnings = evaluate_aggregate_status(agg)
    notes: list[str] = []
    if not evidences:
        notes.append("No evidence files found. Status remains WARNING until samples are collected.")
    if ignored_files:
        notes.append(f"Ignored malformed evidence files: {len(ignored_files)}")
    if status == "WARNING" and "MINIMUM_SAMPLE_NOT_MET" in warnings:
        notes.append("Current status remains WARNING because minimum sample criteria are not met.")
    notes.append("Critical rule applied: before minimum sample is met, PASS is not allowed.")

    report = {
        "minimum_sample_criteria": MIN_SAMPLE,
        "aggregate_metrics": agg,
        "final_decision": {
            "status": status,
            "failure_reasons": failure_reasons,
            "warnings": warnings,
        },
        "evidence_files": [str(p) for p in files],
        "ignored_files": ignored_files,
        "notes": notes,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    out_json = Path(args.json_out)
    out_md = Path(args.md_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    out_md.write_text(_to_markdown(report), encoding="utf-8")

    print(f"written_json={out_json}")
    print(f"written_md={out_md}")
    print(f"final_status={status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
