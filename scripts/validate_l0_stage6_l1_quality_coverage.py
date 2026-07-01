from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4124"
SLUG = "task_4124_l0_stage_6_l1_quality_coverage_audit_l2_handoff"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "stage6_l1_quality_coverage_summary.json"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    required = [
        SUMMARY_PATH,
        REPORT_DIR / "task_4124_raw_hash_audit.csv",
        REPORT_DIR / "task_4124_mapping_audit.csv",
        REPORT_DIR / "task_4124_source_time_audit.csv",
        REPORT_DIR / "task_4124_coverage_audit.csv",
        REPORT_DIR / "task_4124_l2_handoff_decision.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors
    summary = read_json(SUMMARY_PATH)
    if summary.get("stage6_status") != "L1_QUALITY_COVERAGE_AUDIT_COMPLETE_L2_HANDOFF_BLOCKED":
        errors.append(f"unexpected Stage 6 status: {summary.get('stage6_status')}")
    if summary.get("l2_handoff_decision") != "BLOCKED":
        errors.append("L2 handoff must remain BLOCKED")
    for field in ["strict_gate_rows", "proxy_feature_rows_allowed"]:
        if int(summary.get(field, 1)) != 0:
            errors.append(f"{field} must be 0")
    if int(summary.get("raw_integrity_failure_count", 1)) != 0:
        errors.append("raw integrity failures must be 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    raw_rows = read_csv(REPORT_DIR / "task_4124_raw_hash_audit.csv")
    for row in raw_rows:
        if row.get("hash_match") != "1" or row.get("secret_scan_pass") != "1" or row.get("raw_exists") != "1":
            errors.append(f"raw audit failed: {row.get('raw_path')}")
    handoff = read_csv(REPORT_DIR / "task_4124_l2_handoff_decision.csv")
    if not handoff or handoff[0].get("l2_handoff_decision") != "BLOCKED":
        errors.append("handoff decision row must be BLOCKED")
    if "coverage_blocker" not in handoff[0].get("blockers", ""):
        errors.append("handoff blockers must include coverage_blocker")
    if handoff[0].get("missing_source_is_negative") != "0":
        errors.append("missing source must not be negative")
    if handoff[0].get("assignment_uses_future_outcome") != "0":
        errors.append("future outcome assignment must remain 0")

    scheduler = read_json(SCHEDULER_PATH)
    stages = scheduler.get("management_plan", {}).get("stages", [])
    stage6 = next((stage for stage in stages if stage.get("stage") == 6), {})
    next_stages = [stage for stage in stages if str(stage.get("status", "")).upper() == "NEXT"]
    if stage6.get("status") != "COMPLETE_AUDIT_L2_HANDOFF_BLOCKED":
        errors.append("Stage 6 must be COMPLETE_AUDIT_L2_HANDOFF_BLOCKED")
    if stage6.get("audit_task") != TASK_ID:
        errors.append("Stage 6 audit_task must be TASK-4124")
    if next_stages:
        errors.append("no NEXT stage should remain after Stage 6 audit closeout")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE6_AUDIT_ERROR] {error}")
        return 1
    print("[L0_STAGE6_AUDIT_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
