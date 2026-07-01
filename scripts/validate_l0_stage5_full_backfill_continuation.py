from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4125"
SLUG = "task_4125_l0_stage_5_full_2016_to_present_backfill_continuation"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
RAW_DIR = ROOT / f"data/raw/{SLUG}"
ARTIFACT_DIR = ROOT / f"data/artifacts/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "stage5_full_backfill_continuation_summary.json"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def secret_like(path: Path) -> bool:
    if path.suffix.lower() not in {".json", ".jsonl", ".csv", ".txt", ".log"}:
        return False
    text = path.read_text(encoding="utf-8-sig", errors="ignore")[:200_000]
    patterns = [
        r"(?i)\bAuthorization\s*[:=]",
        r"(?i)\bBearer\s+[A-Za-z0-9._-]{10,}",
        r"(?i)\b(api[_-]?key|apikey|token|secret)\s*[:=]\s*[A-Za-z0-9._-]{12,}",
        r"\bsk-[A-Za-z0-9_-]{12,}",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def validate() -> list[str]:
    errors: list[str] = []
    required = [
        SUMMARY_PATH,
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "validation_results.md",
        REPORT_DIR / "task_4125_scope_freeze.csv",
        REPORT_DIR / "task_4125_source_family_plan.csv",
        REPORT_DIR / "task_4125_api_or_raw_call_ledger.csv",
        REPORT_DIR / "task_4125_raw_response_classification.csv",
        REPORT_DIR / "task_4125_normalized_source_packets.csv",
        REPORT_DIR / "task_4125_decision_asof_coverage.csv",
        REPORT_DIR / "task_4125_feature_admission_gate.csv",
        REPORT_DIR / "task_4125_source_gap_ledger.csv",
        REPORT_DIR / "task_4125_progress_ledger.csv",
        REPORT_DIR / "task_4125_coverage_progress.csv",
        REPORT_DIR / "task_4125_command_ledger.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors

    summary = read_json(SUMMARY_PATH)
    if summary.get("stage5_status") not in {"FULL_2016_TO_PRESENT_BACKFILL_CONTINUATION_IN_PROGRESS", "FULL_2016_TO_PRESENT_BACKFILL_COMPLETE"}:
        errors.append(f"unexpected stage5 status: {summary.get('stage5_status')}")
    if int(summary.get("persistent_process_left_running", 1)) != 0:
        errors.append("persistent_process_left_running must be 0")
    for field in ["db_mutation_made", "broker_mutation_permitted", "paper_promotion_permitted", "live_order_enabled"]:
        if int(summary.get(field, 1)) != 0:
            errors.append(f"summary {field} must be 0")
    if int(summary.get("failed_command_count", 1)) != 0:
        errors.append("Stage 5 continuation command failures must be 0")
    if int(summary.get("secret_failure_count", 1)) != 0:
        errors.append("secret failures must be 0")
    if int(summary.get("event_count", 0)) < 2:
        errors.append("expected at least two source event rows")
    if int(summary.get("raw_file_count", 0)) < 2:
        errors.append("expected at least two raw files")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    scope_rows = read_csv(REPORT_DIR / "task_4125_scope_freeze.csv")
    if not scope_rows or scope_rows[0].get("backfill_start_date") != "2016-01-01":
        errors.append("scope must freeze 2016-01-01 start date")
    if scope_rows and scope_rows[0].get("persistent_process_left_running") != "0":
        errors.append("scope must disclose no persistent process left running")

    api_rows = read_csv(REPORT_DIR / "task_4125_api_or_raw_call_ledger.csv")
    for row in api_rows:
        if row.get("missing_source_is_negative") != "0":
            errors.append(f"{row.get('source_id')} missing source must not be negative")
        raw_path = row.get("raw_path", "")
        if raw_path:
            path = ROOT / raw_path
            if not path.exists():
                errors.append(f"raw path missing: {raw_path}")
            elif sha256_file(path) != row.get("raw_sha256"):
                errors.append(f"raw sha mismatch: {raw_path}")

    raw_rows = read_csv(REPORT_DIR / "task_4125_raw_response_classification.csv")
    for row in raw_rows:
        if row.get("secret_scan_status") != "PASS":
            errors.append(f"raw secret scan failed: {row.get('raw_path')}")
        if row.get("strict_gate_opened") != "0":
            errors.append(f"strict gate opened for raw: {row.get('raw_path')}")
    for path in list(RAW_DIR.rglob("*")) + list(ARTIFACT_DIR.rglob("*")):
        if path.is_file() and secret_like(path):
            errors.append(f"secret-like value in artifact: {path.relative_to(ROOT)}")

    progress_rows = read_csv(REPORT_DIR / "task_4125_progress_ledger.csv")
    for row in progress_rows:
        if row.get("diagnostic_only_flag") != "1":
            errors.append(f"{row.get('job_name')} diagnostic_only_flag must be 1")
        for field in ["trade_authority_flag", "broker_mutation_permitted_flag", "real_capital_permitted_flag"]:
            if row.get(field) != "0":
                errors.append(f"{row.get('job_name')} {field} must be 0")

    gate_rows = read_csv(REPORT_DIR / "task_4125_feature_admission_gate.csv")
    for row in gate_rows:
        for field in ["strict_gate_pass", "proxy_feature_allowed", "feature_builder_enabled", "l2_handoff_allowed"]:
            if row.get(field) != "0":
                errors.append(f"feature gate {field} must be 0")

    coverage_rows = read_csv(REPORT_DIR / "task_4125_coverage_progress.csv")
    if not coverage_rows:
        errors.append("coverage progress rows are required")
    if int(summary.get("full_2016_to_present_run_completed", 0)) == 0:
        gap_rows = read_csv(REPORT_DIR / "task_4125_source_gap_ledger.csv")
        if not any(row.get("gap") == "full_2016_to_present_background_run_not_completed" for row in gap_rows):
            errors.append("incomplete full run must be disclosed in source gap ledger")

    scheduler = read_json(SCHEDULER_PATH)
    stages = scheduler.get("management_plan", {}).get("stages", [])
    stage5 = next((stage for stage in stages if stage.get("stage") == 5), {})
    stage6 = next((stage for stage in stages if stage.get("stage") == 6), {})
    if stage5.get("continuation_task") != TASK_ID:
        errors.append("scheduler Stage 5 continuation_task must be TASK-4125")
    if int(stage5.get("full_2016_to_present_run_completed", 1)) != int(summary.get("full_2016_to_present_run_completed", 0)):
        errors.append("scheduler Stage 5 full completion flag must match TASK-4125 summary")
    if stage6.get("l2_handoff_decision") != "BLOCKED":
        errors.append("Stage 6 L2 handoff must remain blocked until coverage completes and reaudit passes")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE5_FULL_BACKFILL_CONTINUATION_ERROR] {error}")
        return 1
    print("[L0_STAGE5_FULL_BACKFILL_CONTINUATION_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
