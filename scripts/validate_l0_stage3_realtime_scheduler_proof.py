from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs/reports/task_4121_l0_stage_3_realtime_scheduler_setup_and_execution"
SUMMARY_PATH = REPORT_DIR / "stage3_scheduler_summary.json"
SETUP_PLAN_PATH = REPORT_DIR / "task_4121_scheduler_setup_plan.csv"
EXECUTION_LEDGER_PATH = REPORT_DIR / "task_4121_scheduler_execution_ledger.csv"
OVERRIDE_PATH = REPORT_DIR / "stage3_scheduler_proof_override.json"
AUDIT_PATH = REPORT_DIR / "effective_scheduler_config_audit.json"
COMMAND_RESULT_PATH = REPORT_DIR / "stage3_scheduler_command_result.json"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"
RUNNER_PATH = ROOT / "tools/db/run_source_acquisition_once.py"
POWERSHELL_SCHEDULER = ROOT / "scripts/run_db_source_acquisition_scheduler.ps1"

REALTIME_JOBS = {
    "official_news_sources_15m",
    "gdelt_news_discovery_15m",
    "marketaux_news_free_30m",
}

FORBIDDEN_TRUE_FIELDS = [
    "execution_permitted",
    "broker_mutation_permitted",
    "paper_promotion_permitted",
    "real_capital_permitted",
    "live_order_enabled",
]

PROTOCOL_TABLES = [
    "task_4121_scope_freeze.csv",
    "task_4121_source_family_plan.csv",
    "task_4121_api_or_raw_call_ledger.csv",
    "task_4121_raw_response_classification.csv",
    "task_4121_normalized_source_packets.csv",
    "task_4121_decision_asof_coverage.csv",
    "task_4121_feature_admission_gate.csv",
    "task_4121_source_gap_ledger.csv",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for path in [SUMMARY_PATH, SETUP_PLAN_PATH, EXECUTION_LEDGER_PATH, OVERRIDE_PATH, AUDIT_PATH, COMMAND_RESULT_PATH]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    for name in PROTOCOL_TABLES:
        if not (REPORT_DIR / name).exists():
            errors.append(f"missing protocol table: docs/reports/task_4121_l0_stage_3_realtime_scheduler_setup_and_execution/{name}")
    if errors:
        return errors

    summary = read_json(SUMMARY_PATH)
    if summary.get("stage3_status") != "REALTIME_SCHEDULER_PROOF_EXECUTED":
        errors.append(f"unexpected stage3_status: {summary.get('stage3_status')}")
    if int(summary.get("persistent_os_task_installed", 1)) != 0:
        errors.append("persistent OS task must not be installed by Stage 3 proof")
    if int(summary.get("network_calls_made", 1)) != 0:
        errors.append("Stage 3 proof must not make provider network calls")
    if int(summary.get("db_mutation_made", 1)) != 0:
        errors.append("Stage 3 proof must not mutate DB")
    for field in FORBIDDEN_TRUE_FIELDS:
        if int(summary.get(field, 0) or 0) != 0:
            errors.append(f"summary {field} must remain 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")
    if int(summary.get("execution_artifact_count", 0) or 0) < 6:
        errors.append("expected at least 6 scheduler execution artifacts for 3 jobs x 2 cycles")

    setup_rows = read_csv(SETUP_PLAN_PATH)
    setup_jobs = {row.get("job_name") for row in setup_rows}
    if setup_jobs != REALTIME_JOBS:
        errors.append(f"setup plan realtime jobs mismatch: {sorted(setup_jobs)}")
    for row in setup_rows:
        if row.get("allow_network") != "0":
            errors.append(f"{row.get('job_name')} must keep allow_network=0 in Stage 3 proof")
        if row.get("diagnostic_only") != "1":
            errors.append(f"{row.get('job_name')} must be diagnostic_only=1")
        for field in ["execution_permitted", "broker_mutation_permitted", "real_capital_permitted"]:
            if row.get(field) != "0":
                errors.append(f"{row.get('job_name')} {field} must remain 0")
        if row.get("job_name") == "marketaux_news_free_30m" and row.get("interval_minutes") != "16":
            errors.append("marketaux proof interval must remain 16")

    execution_rows = read_csv(EXECUTION_LEDGER_PATH)
    if len(execution_rows) < 6:
        errors.append("execution ledger must include at least six rows")
    for row in execution_rows:
        if row.get("requested_apply") != "1":
            errors.append(f"{row.get('artifact_path')} must show scheduler --apply compatibility")
        if row.get("allow_network_requested") != "0":
            errors.append(f"{row.get('artifact_path')} must not request network")
        if row.get("network_calls_made") != "0":
            errors.append(f"{row.get('artifact_path')} made network calls")
        if row.get("db_mutation_made") != "0":
            errors.append(f"{row.get('artifact_path')} mutated DB")
        if row.get("collection_apply_mode") != "AUDIT_ONLY_NO_PROVIDER_EXECUTION":
            errors.append(f"{row.get('artifact_path')} collection mode not guarded")
        for field in FORBIDDEN_TRUE_FIELDS:
            if row.get(field) != "0":
                errors.append(f"{row.get('artifact_path')} {field} must remain 0")

    audit = read_json(AUDIT_PATH)
    if not audit.get("permissions_closed"):
        errors.append("effective scheduler audit permissions_closed must be true")
    if not audit.get("status_preserved"):
        errors.append("effective scheduler audit status_preserved must be true")
    if not audit.get("secrets_detected_false"):
        errors.append("effective scheduler audit must not detect secrets")
    if set(audit.get("jobs_enabled", [])) != REALTIME_JOBS:
        errors.append(f"effective audit enabled jobs mismatch: {audit.get('jobs_enabled')}")

    command_result = read_json(COMMAND_RESULT_PATH)
    if int(command_result.get("returncode", 1)) != 0:
        errors.append(f"scheduler command failed: {command_result.get('returncode')}")

    scheduler = read_json(SCHEDULER_PATH)
    stages = scheduler.get("management_plan", {}).get("stages", [])
    stage3 = next((stage for stage in stages if stage.get("stage") == 3), {})
    stage4 = next((stage for stage in stages if stage.get("stage") == 4), {})
    next_stages = [stage for stage in stages if str(stage.get("status", "")).upper() == "NEXT"]
    if stage3.get("status") != "COMPLETE_REALTIME_SCHEDULER_PROOF_EXECUTED":
        errors.append("Stage 3 must be COMPLETE_REALTIME_SCHEDULER_PROOF_EXECUTED after closeout")
    if stage3.get("scheduler_task") != "TASK-4121":
        errors.append("Stage 3 scheduler_task must be TASK-4121")
    stage4_status = stage4.get("status")
    stage4_already_completed = stage4_status == "COMPLETE_HISTORICAL_BACKFILL_OPTIMIZED_NOT_ACTIVATED"
    stage4_is_next = stage4_status == "NEXT"
    if not (stage4_is_next or stage4_already_completed):
        errors.append("Stage 4 must be NEXT after Stage 3 closeout")
    if not ((len(next_stages) == 1 and next_stages[0].get("stage") == 4) or (stage4_already_completed and len(next_stages) == 0)):
        errors.append("scheduler management plan must have Stage 4 as the single NEXT stage")
    if bool(scheduler.get("registered_loop_enabled", False)):
        errors.append("base scheduler registered_loop_enabled must remain false unless module is restored")

    runner_text = RUNNER_PATH.read_text(encoding="utf-8-sig")
    for needle in ["--apply", "--bucket", "--json", "AUDIT_ONLY_NO_PROVIDER_EXECUTION"]:
        if needle not in runner_text:
            errors.append(f"run_source_acquisition_once missing scheduler compatibility marker: {needle}")
    ps_text = POWERSHELL_SCHEDULER.read_text(encoding="utf-8-sig")
    if "registered_loop_enabled" not in ps_text:
        errors.append("PowerShell scheduler must gate run_registered_loop_once behind registered_loop_enabled")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE3_SCHEDULER_ERROR] {error}")
        return 1
    print("[L0_STAGE3_SCHEDULER_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
