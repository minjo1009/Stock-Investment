from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs/reports/task_4120_l0_stage_2_realtime_source_budget_optimization"
SUMMARY_PATH = REPORT_DIR / "stage2_realtime_budget_summary.json"
PLAN_PATH = REPORT_DIR / "task_4120_realtime_budget_plan.csv"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"
OVERRIDE_TEMPLATE = ROOT / "configs/local_templates/db_source_acquisition_scheduler.override.example.json"
MARKETAUX_REGISTRY = ROOT / "configs/source_registry/l0_marketaux_queries.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    scheduler = json.loads(SCHEDULER_PATH.read_text(encoding="utf-8-sig"))
    jobs = {job.get("name"): job for job in scheduler.get("jobs", []) if isinstance(job, dict)}
    marketaux = jobs.get("marketaux_news_free_30m", {})
    if not marketaux:
        errors.append("missing marketaux_news_free_30m job")
    if bool(marketaux.get("enabled")):
        errors.append("marketaux job must remain disabled in base config")
    if bool(marketaux.get("allow_network")):
        errors.append("marketaux job must keep allow_network=false in base config")
    interval = int(marketaux.get("interval_minutes", 0) or 0)
    cap = int(marketaux.get("daily_request_cap", 0) or 0)
    budget = int(marketaux.get("stage2_realtime_budget", {}).get("requests_per_day_budget", 0) or 0)
    if interval != 16:
        errors.append(f"marketaux interval must be 16m for 90/95 budget, got {interval}")
    if cap != 95:
        errors.append(f"marketaux daily cap must be 95, got {cap}")
    if budget != 90:
        errors.append(f"marketaux requests_per_day_budget must be 90, got {budget}")
    if budget > cap:
        errors.append("marketaux budget exceeds cap")
    utilization = budget / cap if cap else 0
    if not 0.90 <= utilization <= 0.95:
        errors.append(f"marketaux utilization outside target band: {utilization}")
    if int(marketaux.get("stage2_realtime_budget", {}).get("scheduler_activation_permitted", 1)) != 0:
        errors.append("Stage 2 must not permit scheduler activation")

    stages = scheduler.get("management_plan", {}).get("stages", [])
    next_stages = [stage for stage in stages if str(stage.get("status", "")).upper() == "NEXT"]
    stage3 = next((stage for stage in stages if stage.get("stage") == 3), {})
    stage3_already_completed = stage3.get("status") == "COMPLETE_REALTIME_SCHEDULER_PROOF_EXECUTED"
    stage3_is_next = len(next_stages) == 1 and next_stages[0].get("stage") == 3
    if not (stage3_is_next or stage3_already_completed):
        errors.append("scheduler management plan must have Stage 3 as the single NEXT stage after Stage 2 closeout")
    stage1 = next((stage for stage in stages if stage.get("stage") == 1), {})
    if stage1.get("status") != "COMPLETE_NETWORK_SMOKE_PASS":
        errors.append("Stage 1 must remain COMPLETE_NETWORK_SMOKE_PASS")
    stage2 = next((stage for stage in stages if stage.get("stage") == 2), {})
    if stage2.get("status") != "COMPLETE_REALTIME_BUDGET_OPTIMIZED":
        errors.append("Stage 2 must be COMPLETE_REALTIME_BUDGET_OPTIMIZED")

    override = json.loads(OVERRIDE_TEMPLATE.read_text(encoding="utf-8-sig"))
    override_jobs = {job.get("name"): job for job in override.get("jobs", []) if isinstance(job, dict)}
    if int(override_jobs.get("marketaux_news_free_30m", {}).get("interval_minutes", 0) or 0) != 16:
        errors.append("override template marketaux interval must be 16")
    registry = json.loads(MARKETAUX_REGISTRY.read_text(encoding="utf-8-sig"))
    if int(registry.get("preferred_operator_interval_minutes", 0) or 0) != 16:
        errors.append("marketaux registry preferred interval must be 16")

    if not SUMMARY_PATH.exists():
        errors.append(f"missing summary: {SUMMARY_PATH.relative_to(ROOT)}")
    else:
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8-sig"))
        if summary.get("stage2_status") != "REALTIME_BUDGET_OPTIMIZED":
            errors.append(f"unexpected stage2 status: {summary.get('stage2_status')}")
        if int(summary.get("scheduler_activation", 1)) != 0:
            errors.append("summary scheduler_activation must be 0")
        if int(summary.get("network_calls_made", 1)) != 0:
            errors.append("Stage 2 budget optimization must not make network calls")
        if summary.get("strategy") != "NOT_ACCEPTED":
            errors.append("strategy status changed")
        if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment status changed")
        if summary.get("real_capital") != "FORBIDDEN":
            errors.append("real capital status changed")

    if not PLAN_PATH.exists():
        errors.append(f"missing budget plan: {PLAN_PATH.relative_to(ROOT)}")
    else:
        rows = read_csv(PLAN_PATH)
        marketaux_rows = [row for row in rows if row.get("source_family") == "marketaux_news_free"]
        if not marketaux_rows:
            errors.append("budget plan missing marketaux row")
        elif marketaux_rows[0].get("budget_status") != "PASS":
            errors.append("marketaux budget plan row must pass")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE2_REALTIME_BUDGET_ERROR] {error}")
        return 1
    print("[L0_STAGE2_REALTIME_BUDGET_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
