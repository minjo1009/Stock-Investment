from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4123"
SLUG = "task_4123_l0_stage_5_background_historical_backfill_from_2016"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
RAW_DIR = ROOT / f"data/raw/{SLUG}"
ARTIFACT_DIR = ROOT / f"data/artifacts/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "stage5_background_backfill_summary.json"
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
        REPORT_DIR / "task_4123_scope_freeze.csv",
        REPORT_DIR / "task_4123_source_family_plan.csv",
        REPORT_DIR / "task_4123_api_or_raw_call_ledger.csv",
        REPORT_DIR / "task_4123_raw_response_classification.csv",
        REPORT_DIR / "task_4123_normalized_source_packets.csv",
        REPORT_DIR / "task_4123_decision_asof_coverage.csv",
        REPORT_DIR / "task_4123_feature_admission_gate.csv",
        REPORT_DIR / "task_4123_source_gap_ledger.csv",
        REPORT_DIR / "task_4123_progress_ledger.csv",
        REPORT_DIR / "task_4123_command_ledger.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors

    summary = read_json(SUMMARY_PATH)
    if summary.get("stage5_status") != "BACKGROUND_HISTORICAL_BACKFILL_BOUNDED_PROOF_EXECUTED":
        errors.append(f"unexpected stage5 status: {summary.get('stage5_status')}")
    if int(summary.get("bounded_background_collection_started", 0)) != 1:
        errors.append("bounded background collection must be started")
    for field in ["persistent_process_left_running", "db_mutation_made", "broker_mutation_permitted", "paper_promotion_permitted", "live_order_enabled"]:
        if int(summary.get(field, 1)) != 0:
            errors.append(f"summary {field} must be 0")
    if int(summary.get("failed_command_count", 1)) != 0:
        errors.append("Stage 5 command failures must be 0")
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

    api_rows = read_csv(REPORT_DIR / "task_4123_api_or_raw_call_ledger.csv")
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

    raw_rows = read_csv(REPORT_DIR / "task_4123_raw_response_classification.csv")
    for row in raw_rows:
        if row.get("secret_scan_status") != "PASS":
            errors.append(f"raw secret scan failed: {row.get('raw_path')}")
        if row.get("strict_gate_opened") != "0":
            errors.append(f"strict gate opened for raw: {row.get('raw_path')}")
    for path in list(RAW_DIR.rglob("*")) + list(ARTIFACT_DIR.rglob("*")):
        if path.is_file() and secret_like(path):
            errors.append(f"secret-like value in artifact: {path.relative_to(ROOT)}")

    progress_rows = read_csv(REPORT_DIR / "task_4123_progress_ledger.csv")
    for row in progress_rows:
        if row.get("diagnostic_only_flag") != "1":
            errors.append(f"{row.get('job_name')} diagnostic_only_flag must be 1")
        for field in ["trade_authority_flag", "broker_mutation_permitted_flag", "real_capital_permitted_flag"]:
            if row.get(field) != "0":
                errors.append(f"{row.get('job_name')} {field} must be 0")

    gate_rows = read_csv(REPORT_DIR / "task_4123_feature_admission_gate.csv")
    for row in gate_rows:
        for field in ["strict_gate_pass", "proxy_feature_allowed", "feature_builder_enabled", "l2_handoff_allowed"]:
            if row.get(field) != "0":
                errors.append(f"feature gate {field} must be 0")

    scheduler = read_json(SCHEDULER_PATH)
    stages = scheduler.get("management_plan", {}).get("stages", [])
    stage5 = next((stage for stage in stages if stage.get("stage") == 5), {})
    stage6 = next((stage for stage in stages if stage.get("stage") == 6), {})
    next_stages = [stage for stage in stages if str(stage.get("status", "")).upper() == "NEXT"]
    if stage5.get("status") != "COMPLETE_BACKGROUND_BACKFILL_BOUNDED_PROOF_EXECUTED":
        errors.append("Stage 5 must be COMPLETE_BACKGROUND_BACKFILL_BOUNDED_PROOF_EXECUTED")
    if stage5.get("backfill_task") != TASK_ID:
        errors.append("Stage 5 backfill_task must be TASK-4123")
    if int(stage5.get("full_2016_to_present_run_completed", 1)) != 0:
        errors.append("Stage 5 must disclose full 2016-to-present run is not complete")
    if stage6.get("status") != "NEXT":
        errors.append("Stage 6 must be NEXT after Stage 5 proof")
    if len(next_stages) != 1 or next_stages[0].get("stage") != 6:
        errors.append("management plan must have Stage 6 as the single NEXT stage")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE5_BACKFILL_ERROR] {error}")
        return 1
    print("[L0_STAGE5_BACKFILL_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
