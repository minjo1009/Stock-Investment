from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4126"
SLUG = "task_4126_l0_stage_6_full_backfill_l1_quality_coverage_reaudit"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "stage6_full_backfill_l1_quality_coverage_summary.json"
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
        REPORT_DIR / "task_4126_raw_hash_audit.csv",
        REPORT_DIR / "task_4126_mapping_audit.csv",
        REPORT_DIR / "task_4126_source_time_audit.csv",
        REPORT_DIR / "task_4126_coverage_audit.csv",
        REPORT_DIR / "task_4126_l2_handoff_decision.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors

    summary = read_json(SUMMARY_PATH)
    if summary.get("task_id") != TASK_ID:
        errors.append("summary task_id must be TASK-4126")
    if summary.get("stage5_task_id") != "TASK-4125":
        errors.append("summary stage5_task_id must be TASK-4125")
    if summary.get("stage6_status") != "L1_QUALITY_COVERAGE_REAUDIT_COMPLETE_L2_HANDOFF_BLOCKED":
        errors.append(f"unexpected Stage 6 status: {summary.get('stage6_status')}")
    if int(summary.get("coverage_complete_count", 0) or 0) != int(summary.get("coverage_source_count", -1) or -1):
        errors.append("full backfill coverage must be complete for all audited sources")
    if int(summary.get("raw_integrity_failure_count", 1)) != 0:
        errors.append("raw integrity failures must be 0")
    if int(summary.get("mapping_blocker_rows", 1)) != 0:
        errors.append("mapping blocker rows must be 0")
    if summary.get("l2_handoff_decision") != "BLOCKED":
        errors.append("L2 handoff must remain BLOCKED until feature admission gates open")
    blockers = str(summary.get("l2_handoff_blockers", ""))
    if "feature_admission_gate_closed" not in blockers:
        errors.append("handoff blockers must include feature_admission_gate_closed")
    if int(summary.get("strict_gate_rows", 1)) != 0:
        errors.append("strict_gate_rows must be 0")
    if int(summary.get("proxy_feature_rows_allowed", 1)) != 0:
        errors.append("proxy_feature_rows_allowed must be 0")
    if int(summary.get("missing_source_is_negative", 1)) != 0:
        errors.append("missing source must not be negative")
    if int(summary.get("assignment_uses_future_outcome", 1)) != 0:
        errors.append("future outcome assignment must remain 0")
    if int(summary.get("outcome_used_for_assignment", 1)) != 0:
        errors.append("outcome assignment must remain 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    raw_rows = read_csv(REPORT_DIR / "task_4126_raw_hash_audit.csv")
    for row in raw_rows:
        if row.get("hash_match") != "1" or row.get("secret_scan_pass") != "1" or row.get("raw_exists") != "1":
            errors.append(f"raw audit failed: {row.get('raw_path')}")
            break

    coverage_rows = read_csv(REPORT_DIR / "task_4126_coverage_audit.csv")
    if not coverage_rows:
        errors.append("coverage audit must not be empty")
    for row in coverage_rows:
        if row.get("coverage_status") != "PASS" or row.get("pending_units") != "0":
            errors.append(f"coverage audit failed: {row.get('source_key')}")
            break

    handoff = read_csv(REPORT_DIR / "task_4126_l2_handoff_decision.csv")
    if not handoff or handoff[0].get("l2_handoff_decision") != "BLOCKED":
        errors.append("handoff decision row must be BLOCKED")
    if handoff and handoff[0].get("missing_source_is_negative") != "0":
        errors.append("missing source must not be negative in handoff row")

    scheduler = read_json(SCHEDULER_PATH)
    stages = scheduler.get("management_plan", {}).get("stages", [])
    stage5 = next((stage for stage in stages if stage.get("stage") == 5), {})
    stage6 = next((stage for stage in stages if stage.get("stage") == 6), {})
    if int(stage5.get("full_2016_to_present_run_completed", 0) or 0) != 1:
        errors.append("scheduler Stage 5 full completion flag must be 1")
    if stage6.get("status") != "COMPLETE_AUDIT_L2_HANDOFF_BLOCKED":
        errors.append("scheduler Stage 6 must remain COMPLETE_AUDIT_L2_HANDOFF_BLOCKED")
    if stage6.get("audit_task") != TASK_ID:
        errors.append("scheduler Stage 6 audit_task must be TASK-4126")
    if stage6.get("l2_handoff_decision") != "BLOCKED":
        errors.append("scheduler Stage 6 L2 handoff decision must be BLOCKED")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE6_FULL_BACKFILL_REAUDIT_ERROR] {error}")
        return 1
    print("[L0_STAGE6_FULL_BACKFILL_REAUDIT_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
