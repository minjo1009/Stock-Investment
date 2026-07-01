from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs/reports/task_4122_l0_stage_4_historical_backfill_optimization"
SUMMARY_PATH = REPORT_DIR / "stage4_backfill_optimization_summary.json"
PLAN_PATH = REPORT_DIR / "task_4122_backfill_optimization_plan.csv"
BLOCKER_PATH = REPORT_DIR / "task_4122_backfill_blocker_ledger.csv"
COVERAGE_PATH = REPORT_DIR / "task_4122_backfill_coverage_audit_plan.csv"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"
MICROSTRUCTURE_BACKFILL = ROOT / "scripts/run_task646_full_microstructure_backfill.py"

BACKFILL_JOBS = {
    "public_context_news_backfill",
    "public_market_macro_news_backfill",
    "microstructure_backfill_batch",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for path in [SUMMARY_PATH, PLAN_PATH, BLOCKER_PATH, COVERAGE_PATH]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors

    summary = read_json(SUMMARY_PATH)
    if summary.get("stage4_status") != "HISTORICAL_BACKFILL_OPTIMIZED_NOT_ACTIVATED":
        errors.append(f"unexpected stage4 status: {summary.get('stage4_status')}")
    for field in ["scheduler_activation_permitted", "background_collection_started", "network_calls_made", "db_mutation_made"]:
        if int(summary.get(field, 1)) != 0:
            errors.append(f"summary {field} must be 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    rows = read_csv(PLAN_PATH)
    jobs = {row.get("job_name") for row in rows}
    if jobs != BACKFILL_JOBS:
        errors.append(f"backfill plan jobs mismatch: {sorted(jobs)}")
    for row in rows:
        if row.get("optimization_status") != "OPTIMIZED_NOT_ACTIVATED":
            errors.append(f"{row.get('job_name')} must be optimized but not activated")
        if row.get("scheduler_activation_permitted") != "0":
            errors.append(f"{row.get('job_name')} scheduler activation must remain 0")
        if row.get("network_calls_made") != "0":
            errors.append(f"{row.get('job_name')} must not make network calls in Stage 4")
        if row.get("db_mutation_made") != "0":
            errors.append(f"{row.get('job_name')} must not mutate DB in Stage 4")

    coverage_rows = read_csv(COVERAGE_PATH)
    for row in coverage_rows:
        if row.get("feature_admission_allowed") != "0" or row.get("l2_handoff_allowed") != "0":
            errors.append(f"{row.get('job_name')} must keep feature/L2 gates closed")

    scheduler = read_json(SCHEDULER_PATH)
    stages = scheduler.get("management_plan", {}).get("stages", [])
    stage4 = next((stage for stage in stages if stage.get("stage") == 4), {})
    stage5 = next((stage for stage in stages if stage.get("stage") == 5), {})
    next_stages = [stage for stage in stages if str(stage.get("status", "")).upper() == "NEXT"]
    if stage4.get("status") != "COMPLETE_HISTORICAL_BACKFILL_OPTIMIZED_NOT_ACTIVATED":
        errors.append("Stage 4 must be COMPLETE_HISTORICAL_BACKFILL_OPTIMIZED_NOT_ACTIVATED")
    if stage4.get("backfill_task") != "TASK-4122":
        errors.append("Stage 4 backfill_task must be TASK-4122")
    stage5_status = stage5.get("status")
    stage5_already_completed = stage5_status == "COMPLETE_FULL_2016_TO_PRESENT_BACKFILL"
    stage5_is_next = stage5_status == "NEXT"
    if not (stage5_is_next or stage5_already_completed):
        errors.append("Stage 5 must be NEXT after Stage 4 closeout")
    if not ((len(next_stages) == 1 and next_stages[0].get("stage") == 5) or (stage5_already_completed and len(next_stages) == 0)):
        errors.append("scheduler management plan must have Stage 5 as the single NEXT stage")

    jobs_by_name = {job.get("name"): job for job in scheduler.get("jobs", []) if isinstance(job, dict)}
    for name in BACKFILL_JOBS:
        job = jobs_by_name.get(name, {})
        if bool(job.get("enabled")):
            errors.append(f"base backfill job must remain disabled: {name}")
        if bool(job.get("allow_network")):
            errors.append(f"base backfill job must keep allow_network=false: {name}")
        stage4_meta = job.get("stage4_backfill_optimization", {})
        if stage4_meta.get("optimization_status") != "OPTIMIZED_NOT_ACTIVATED":
            errors.append(f"{name} missing Stage 4 optimization metadata")
        if int(stage4_meta.get("scheduler_activation_permitted", 1)) != 0:
            errors.append(f"{name} stage4 scheduler_activation_permitted must be 0")

    backfill_text = MICROSTRUCTURE_BACKFILL.read_text(encoding="utf-8-sig")
    for needle in ["chunk_minutes", "--chunk-minutes", "timedelta(minutes=idx * max(int(chunk_minutes), 1))"]:
        if needle not in backfill_text:
            errors.append(f"microstructure backfill missing chunk_minutes support: {needle}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE4_BACKFILL_ERROR] {error}")
        return 1
    print("[L0_STAGE4_BACKFILL_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
