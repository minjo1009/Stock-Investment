from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4130"
SLUG = "task_4130_l0_public_page_collection_effective_hardening"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "l0_public_page_collection_effective_hardening_summary.json"
COLLECTOR_PATH = ROOT / "tools/db/source_acquisition/public_newswire_collector.py"
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
        "l0_public_page_collection_effective_hardening_summary.json",
        "task_4130_priority_effectiveness.csv",
        "task_4130_fallback_order.csv",
        "task_4130_failure_reason_matrix.csv",
        "task_4130_mapping_hint_fixture.csv",
    ]
    return [REPORT_DIR / name for name in names]


def validate_summary(errors: list[str]) -> None:
    summary = read_json(SUMMARY_PATH)
    if summary.get("task_id") != TASK_ID:
        errors.append("summary task_id must be TASK-4130")
    if summary.get("hardening_status") != "COMPLETE_EFFECTIVE_COLLECTOR_HARDENING_NO_TRADING_GATES":
        errors.append("unexpected hardening status")
    if int(summary.get("static_html_fallback_configured", 0) or 0) != 1:
        errors.append("static HTML fallback must be configured")
    if int(summary.get("fallback_stage_count", 0) or 0) < 5:
        errors.append("fallback stage count must be at least 5")
    if int(summary.get("failure_reason_pass_count", 0) or 0) != int(summary.get("failure_reason_check_count", -1) or -1):
        errors.append("all failure reason fixture checks must pass")
    if int(summary.get("fixture_public_page_rows", 0) or 0) < 2:
        errors.append("fixture public page parser must produce at least two rows")
    if int(summary.get("candidate_hint_rows", 0) or 0) < 2:
        errors.append("candidate hint fixture must produce at least two hinted rows")
    if int(summary.get("candidate_hints_are_authority", 0) or 0) != 0:
        errors.append("candidate hints must remain non-authority")
    if int(summary.get("chrome_smoke_only_configured", 0) or 0) != 1:
        errors.append("Chrome smoke-only lane must be configured")
    if int(summary.get("chrome_job_enabled", 0) or 0) != 0:
        errors.append("Chrome smoke job must remain disabled")
    if int(summary.get("chrome_job_allow_network", 0) or 0) != 0:
        errors.append("Chrome smoke job allow_network must remain false")
    for field in ["strict_gate_pass_rows", "trade_feature_allowed_rows", "missing_source_is_negative", "assignment_uses_future_outcome", "outcome_used_for_assignment"]:
        if int(summary.get(field, 0) or 0) != 0:
            errors.append(f"{field} must remain 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")


def validate_csvs(errors: list[str]) -> None:
    priority_rows = read_csv(REPORT_DIR / "task_4130_priority_effectiveness.csv")
    expected_priorities = {
        "public_page_fallback",
        "failure_reason_recording",
        "source_fallback_order",
        "ticker_entity_candidate_hints",
        "chrome_selector_drift_smoke",
    }
    actual_priorities = {row.get("priority_item", "") for row in priority_rows}
    if actual_priorities != expected_priorities:
        errors.append("priority effectiveness CSV must contain the five agreed items")
    for row in priority_rows:
        if row.get("implemented") != "1":
            errors.append(f"priority not implemented: {row.get('priority_item')}")
        if row.get("opened_trading_gate") != "0":
            errors.append(f"priority opened trading gate: {row.get('priority_item')}")

    fallback_rows = read_csv(REPORT_DIR / "task_4130_fallback_order.csv")
    stages = [row.get("fallback_stage") for row in fallback_rows]
    for stage in ["rss_or_feed", "sitemap", "robots_sitemap", "static_html_probe", "static_html_base"]:
        if stage not in stages:
            errors.append(f"fallback stage missing: {stage}")

    failure_rows = read_csv(REPORT_DIR / "task_4130_failure_reason_matrix.csv")
    for row in failure_rows:
        if row.get("pass") != "1":
            errors.append(f"failure reason case failed: {row.get('case_id')}")

    mapping_rows = read_csv(REPORT_DIR / "task_4130_mapping_hint_fixture.csv")
    if not mapping_rows:
        errors.append("mapping hint fixture is empty")
    hinted = [row for row in mapping_rows if int(row.get("candidate_hint_count", 0) or 0) > 0]
    if len(hinted) < 2:
        errors.append("mapping hint fixture must have at least two hinted rows")
    for row in mapping_rows:
        if row.get("candidate_hints_are_authority") != "0":
            errors.append("candidate hints must not be authority")
        if row.get("trade_authority_flag") != "0":
            errors.append("trade authority flag must remain 0 in mapping hint fixture")


def validate_code_markers(errors: list[str]) -> None:
    text = COLLECTOR_PATH.read_text(encoding="utf-8-sig")
    markers = [
        "COLLECTOR_VERSION = \"public_newswire_collector.v0.1.5\"",
        "CANDIDATE_HINT_VERSION",
        "def classify_fetch_failure",
        "def build_collection_candidates",
        "static_html_probe",
        "static_html_base",
        "entity_candidate_hints",
        "entity_candidate_hints_are_authority",
        "chrome_smoke_role",
    ]
    for marker in markers:
        if marker not in text:
            errors.append(f"collector missing marker: {marker}")


def validate_scheduler(errors: list[str]) -> None:
    scheduler = read_json(SCHEDULER_PATH)
    if scheduler.get("strategy") != "NOT_ACCEPTED":
        errors.append("scheduler strategy changed")
    if scheduler.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("scheduler deployment changed")
    if scheduler.get("real_capital") != "FORBIDDEN":
        errors.append("scheduler real_capital changed")
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
    jobs = scheduler.get("jobs", [])
    for job in jobs:
        if bool(job.get("enabled")):
            errors.append(f"base scheduler job must remain disabled: {job.get('name')}")
        if bool(job.get("allow_network")):
            errors.append(f"base scheduler job allow_network must remain false: {job.get('name')}")
    chrome_job = next((job for job in jobs if job.get("name") == "chrome_public_page_snapshot_smoke"), {})
    if chrome_job.get("runtime_collection_authority") not in {0, "0", False}:
        errors.append("Chrome smoke job must have no runtime collection authority")
    if chrome_job.get("purpose") != "selector_drift_and_public_page_availability_diagnostics_only":
        errors.append("Chrome smoke job purpose must be selector drift/public page diagnostics only")


def write_validation_results(errors: list[str]) -> None:
    result = "FAIL" if errors else "PASS"
    lines = [
        "# TASK-4130 Validation Results",
        "",
        f"Result: {result}.",
        "",
        "## Commands",
        "",
        "- `python scripts/audit_l0_public_page_collection_effective_hardening.py`",
        "- `python scripts/validate_l0_public_page_collection_effective_hardening.py`",
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
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
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
    validate_code_markers(errors)
    validate_scheduler(errors)
    return errors


def main() -> int:
    errors = validate()
    write_validation_results(errors)
    if errors:
        for error in errors:
            print(f"[L0_PUBLIC_PAGE_EFFECTIVE_HARDENING_ERROR] {error}")
        return 1
    print("[L0_PUBLIC_PAGE_EFFECTIVE_HARDENING_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
