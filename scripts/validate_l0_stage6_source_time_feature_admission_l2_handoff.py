from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4127"
SLUG = "task_4127_l0_stage_6_source_time_feature_admission_l2_context_handoff"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "stage6_source_time_feature_admission_l2_handoff_summary.json"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    required = [
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "validation_results.md",
        SUMMARY_PATH,
        REPORT_DIR / "task_4127_source_family_admission.csv",
        REPORT_DIR / "task_4127_blocked_source_rows.csv",
        REPORT_DIR / "task_4127_feature_admission_gate.csv",
        REPORT_DIR / "task_4127_l2_context_handoff_manifest.csv",
        REPORT_DIR / "task_4127_l2_handoff_decision.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors

    summary = read_json(SUMMARY_PATH)
    if summary.get("task_id") != TASK_ID:
        errors.append("summary task_id must be TASK-4127")
    if summary.get("stage5_task_id") != "TASK-4125":
        errors.append("stage5_task_id must be TASK-4125")
    if summary.get("stage6_reaudit_task_id") != "TASK-4126":
        errors.append("stage6_reaudit_task_id must be TASK-4126")
    if summary.get("stage6_status") != "SOURCE_TIME_FEATURE_ADMISSION_COMPLETE_PARTIAL_L2_CONTEXT_HANDOFF_READY":
        errors.append(f"unexpected status: {summary.get('stage6_status')}")
    if summary.get("l2_handoff_decision") != "PARTIAL_CONTEXT_ONLY_HANDOFF_READY":
        errors.append("L2 handoff decision must be PARTIAL_CONTEXT_ONLY_HANDOFF_READY")
    admitted = int(summary.get("l2_context_admitted_rows", 0) or 0)
    blocked = int(summary.get("blocked_rows", 0) or 0)
    certified = int(summary.get("source_time_certified_rows", 0) or 0)
    uncertified = int(summary.get("source_time_uncertified_rows", 0) or 0)
    headline_rows = int(summary.get("headline_rows", 0) or 0)
    if admitted <= 0:
        errors.append("L2 context admitted rows must be positive")
    if blocked <= 0:
        errors.append("blocked rows must remain positive for Wikimedia current events")
    if admitted != certified:
        errors.append("admitted rows must equal source-time certified rows")
    if blocked != uncertified:
        errors.append("blocked rows must equal source-time uncertified rows")
    if admitted + blocked != headline_rows:
        errors.append("admitted plus blocked rows must equal headline rows")
    if int(summary.get("strict_gate_pass_rows", 1)) != 0:
        errors.append("strict_gate_pass_rows must remain 0")
    if int(summary.get("trade_feature_allowed_rows", 1)) != 0:
        errors.append("trade_feature_allowed_rows must remain 0")
    if int(summary.get("proxy_feature_allowed_rows", 0) or 0) != admitted:
        errors.append("proxy_feature_allowed_rows must equal admitted rows")
    if int(summary.get("missing_source_is_negative", 1)) != 0:
        errors.append("missing_source_is_negative must be 0")
    if int(summary.get("assignment_uses_future_outcome", 1)) != 0:
        errors.append("assignment_uses_future_outcome must be 0")
    if int(summary.get("outcome_used_for_assignment", 1)) != 0:
        errors.append("outcome_used_for_assignment must be 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    family_rows = read_csv(REPORT_DIR / "task_4127_source_family_admission.csv")
    if len(family_rows) != int(summary.get("source_family_count", -1) or -1):
        errors.append("source family count mismatch")
    wikimedia = [row for row in family_rows if row.get("source_key") == "wikimedia_current_events"]
    if not wikimedia:
        errors.append("wikimedia_current_events row must be present")
    elif wikimedia[0].get("admission_status") != "BLOCKED":
        errors.append("wikimedia_current_events must remain BLOCKED")

    blocked_rows = read_csv(REPORT_DIR / "task_4127_blocked_source_rows.csv")
    if not any(row.get("source_key") == "wikimedia_current_events" and "source_time_uncertified" in row.get("blocker", "") for row in blocked_rows):
        errors.append("blocked ledger must include wikimedia_current_events source_time_uncertified")

    gate = read_csv(REPORT_DIR / "task_4127_feature_admission_gate.csv")
    if not gate:
        errors.append("feature admission gate row missing")
    else:
        row = gate[0]
        if row.get("strict_gate_pass_rows") != "0" or row.get("trade_feature_allowed_rows") != "0":
            errors.append("feature gate must keep strict/trade rows at 0")
        if int(row.get("proxy_feature_allowed_rows", 0) or 0) != admitted:
            errors.append("feature gate proxy count mismatch")
        if row.get("l2_trading_handoff_allowed") != "0":
            errors.append("l2_trading_handoff_allowed must be 0")

    handoff = read_csv(REPORT_DIR / "task_4127_l2_handoff_decision.csv")
    if not handoff or handoff[0].get("l2_handoff_decision") != "PARTIAL_CONTEXT_ONLY_HANDOFF_READY":
        errors.append("handoff decision row must be partial context-only ready")
    if handoff and handoff[0].get("missing_source_is_negative") != "0":
        errors.append("handoff missing_source_is_negative must be 0")

    scheduler = read_json(SCHEDULER_PATH)
    stages = scheduler.get("management_plan", {}).get("stages", [])
    stage6 = next((stage for stage in stages if stage.get("stage") == 6), {})
    if stage6.get("audit_task") != TASK_ID:
        errors.append("scheduler Stage 6 audit_task must be TASK-4127")
    if stage6.get("l2_handoff_decision") != "PARTIAL_CONTEXT_ONLY_HANDOFF_READY":
        errors.append("scheduler Stage 6 L2 handoff decision must be partial context-only ready")
    if stage6.get("l2_trading_handoff_allowed") not in {0, "0"}:
        errors.append("scheduler Stage 6 trading handoff must remain 0")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE6_SOURCE_TIME_FEATURE_ADMISSION_ERROR] {error}")
        return 1
    print("[L0_STAGE6_SOURCE_TIME_FEATURE_ADMISSION_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
