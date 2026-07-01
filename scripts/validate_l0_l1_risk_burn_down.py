from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4129"
SLUG = "task_4129_l0_l1_risk_burn_down_wikimedia_trading_scheduler_validator_chrome_mapping"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "l0_l1_risk_burn_down_summary.json"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def required_paths() -> list[Path]:
    names = [
        "report.md",
        "artifact_manifest.csv",
        "validation_results.md",
        "l0_l1_risk_burn_down_summary.json",
        "task_4129_wikimedia_noon_policy.csv",
        "task_4129_trading_feature_admission_criteria.csv",
        "task_4129_scheduler_execution_qa.csv",
        "task_4129_validator_split_audit.csv",
        "task_4129_chrome_crawl_posture.csv",
        "task_4129_mapping_hardening_audit.csv",
    ]
    return [REPORT_DIR / name for name in names]


def validate_summary(errors: list[str]) -> None:
    summary = read_json(SUMMARY_PATH)
    if summary.get("task_id") != TASK_ID:
        errors.append("summary task_id must be TASK-4129")
    if summary.get("risk_burn_down_status") != "COMPLETE_CONTEXT_POLICY_AND_VALIDATOR_GATES_INSTALLED":
        errors.append("unexpected risk burn-down status")
    if int(summary.get("wikimedia_total_rows", 0) or 0) != 19492:
        errors.append("Wikimedia total rows must remain 19,492")
    if int(summary.get("wikimedia_noon_context_rows", 0) or 0) != 19492:
        errors.append("Wikimedia noon context rows must be 19,492")
    if int(summary.get("previous_l2_context_rows", 0) or 0) != 478890:
        errors.append("previous L2 context rows must remain 478,890")
    if int(summary.get("l2_context_rows_after_noon_policy", 0) or 0) != 498382:
        errors.append("L2 context rows after noon policy must be 498,382")
    if int(summary.get("stage5_total_event_rows", 0) or 0) != 498382:
        errors.append("Stage 5 total event rows must be 498,382")
    if int(summary.get("trading_feature_criteria_defined", 0) or 0) != 1:
        errors.append("trading feature criteria must be defined")
    for field in ["trading_feature_opened", "strict_gate_pass_rows", "trade_feature_allowed_rows"]:
        if int(summary.get(field, 0) or 0) != 0:
            errors.append(f"{field} must remain 0")
    if summary.get("scheduler_qa_status") != "PROOF_VALIDATED_NOT_ACTIVATED":
        errors.append("scheduler status must be proof validated but not activated")
    if summary.get("validator_split_status") != "COMPLETE":
        errors.append("validator split status must be COMPLETE")
    if summary.get("chrome_crawl_status") != "SMOKE_ONLY_ADDED_NOT_RUNTIME_COLLECTION":
        errors.append("Chrome crawl status must be smoke-only")
    if summary.get("mapping_hardening_status") != "POLICY_DEFINED_AUDIT_READY":
        errors.append("mapping hardening status must be policy-defined/audit-ready")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")
    for field in ["missing_source_is_negative", "assignment_uses_future_outcome", "outcome_used_for_assignment"]:
        if int(summary.get(field, 0) or 0) != 0:
            errors.append(f"{field} must remain 0")


def validate_csvs(errors: list[str]) -> None:
    wikimedia_rows = read_csv(REPORT_DIR / "task_4129_wikimedia_noon_policy.csv")
    if not wikimedia_rows:
        errors.append("Wikimedia noon policy CSV is empty")
    if sum(int(row.get("known_day_rows", 0) or 0) for row in wikimedia_rows) != 19492:
        errors.append("Wikimedia noon policy known_day_rows must total 19,492")
    for row in wikimedia_rows:
        if row.get("derived_source_ts_policy") != "YYYY_MM_DD_DAY_HEADING_TO_12_00_00Z":
            errors.append("Wikimedia noon policy marker missing")
        if int(row.get("strict_gate_pass_rows", 0) or 0) != 0:
            errors.append("Wikimedia strict gate rows must remain 0")
        if int(row.get("trade_feature_allowed_rows", 0) or 0) != 0:
            errors.append("Wikimedia trade feature rows must remain 0")

    feature_rows = read_csv(REPORT_DIR / "task_4129_trading_feature_admission_criteria.csv")
    if len(feature_rows) < 8:
        errors.append("trading feature admission criteria must have at least eight checks")
    for row in feature_rows:
        if row.get("current_status") != "DEFINED_NOT_OPENED":
            errors.append(f"trading feature criterion not closed: {row.get('criterion')}")
        if row.get("current_pass_for_trading_feature") != "0":
            errors.append(f"trading feature criterion unexpectedly open: {row.get('criterion')}")

    scheduler_rows = read_csv(REPORT_DIR / "task_4129_scheduler_execution_qa.csv")
    for row in scheduler_rows:
        if row.get("pass") != "1":
            errors.append(f"scheduler QA check failed: {row.get('check')}")

    split_rows = read_csv(REPORT_DIR / "task_4129_validator_split_audit.csv")
    for row in split_rows:
        if row.get("marker_present") != "1":
            errors.append(f"validator split marker missing: {row.get('validator')}")

    chrome_rows = read_csv(REPORT_DIR / "task_4129_chrome_crawl_posture.csv")
    if not any(row.get("item") == "chrome_public_page_snapshot_smoke_lane" and row.get("configured") == "1" for row in chrome_rows):
        errors.append("Chrome public page snapshot smoke lane must be configured")
    for row in chrome_rows:
        if row.get("job_enabled") != "0" or row.get("allow_network") != "0":
            errors.append(f"Chrome posture must remain disabled/no-network: {row.get('item')}")

    mapping_rows = read_csv(REPORT_DIR / "task_4129_mapping_hardening_audit.csv")
    if len(mapping_rows) < 5:
        errors.append("mapping hardening audit must have at least five checks")
    for row in mapping_rows:
        if row.get("current_pass_for_l2_context") != "1":
            errors.append(f"mapping check must pass for L2 context: {row.get('mapping_check')}")
        if row.get("current_pass_for_trading_feature") != "0":
            errors.append(f"mapping check must not pass for trading feature: {row.get('mapping_check')}")


def validate_scheduler_config(errors: list[str]) -> None:
    scheduler = read_json(SCHEDULER_PATH)
    if scheduler.get("strategy") != "NOT_ACCEPTED":
        errors.append("scheduler strategy changed")
    if scheduler.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("scheduler deployment changed")
    if scheduler.get("real_capital") != "FORBIDDEN":
        errors.append("scheduler real_capital changed")
    if bool(scheduler.get("registered_loop_enabled")):
        errors.append("registered loop must remain disabled")
    permissions = scheduler.get("permissions", {})
    for field in [
        "execution_permitted",
        "broker_mutation_permitted",
        "paper_promotion_permitted",
        "real_capital_permitted",
        "live_order_enabled",
        "replay_permission_granted",
        "buy_sell_signal_generation_permitted",
    ]:
        if int(permissions.get(field, 0) or 0) != 0:
            errors.append(f"scheduler permissions.{field} must remain 0")
    modes = scheduler.get("management_plan", {}).get("implementation_modes", {})
    if "chrome_public_page_snapshot_smoke" not in modes.get("chrome_smoke_only", []):
        errors.append("chrome_public_page_snapshot_smoke must be in chrome_smoke_only")
    if modes.get("codex_gpt_role") != "planning_review_recovery_only_not_runtime_collection":
        errors.append("Codex/GPT role must remain planning/review/recovery only")
    jobs = scheduler.get("jobs", [])
    for job in jobs:
        if bool(job.get("enabled")):
            errors.append(f"base scheduler job must remain disabled: {job.get('name')}")
        if bool(job.get("allow_network")):
            errors.append(f"base scheduler job allow_network must remain false: {job.get('name')}")
    chrome_job = next((job for job in jobs if job.get("name") == "chrome_public_page_snapshot_smoke"), None)
    if chrome_job is None:
        errors.append("missing chrome_public_page_snapshot_smoke job")
    elif chrome_job.get("mode") != "smoke":
        errors.append("chrome_public_page_snapshot_smoke job must be smoke mode")


def write_validation_results(errors: list[str]) -> None:
    result = "FAIL" if errors else "PASS"
    lines = [
        "# TASK-4129 Validation Results",
        "",
        f"Result: {result}.",
        "",
        "## Commands",
        "",
        "- `python scripts/audit_l0_l1_risk_burn_down.py`",
        "- `python scripts/validate_l0_l1_risk_burn_down.py`",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.append("")
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    lines.extend(
        [
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ]
    )
    (REPORT_DIR / "validation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate() -> list[str]:
    errors: list[str] = []
    for path in required_paths():
        if not path.exists():
            errors.append(f"missing artifact: {rel(path)}")
    if errors:
        return errors
    validate_summary(errors)
    validate_csvs(errors)
    validate_scheduler_config(errors)
    return errors


def main() -> int:
    errors = validate()
    write_validation_results(errors)
    if errors:
        for error in errors:
            print(f"[L0_L1_RISK_BURN_DOWN_ERROR] {error}")
        return 1
    print("[L0_L1_RISK_BURN_DOWN_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
