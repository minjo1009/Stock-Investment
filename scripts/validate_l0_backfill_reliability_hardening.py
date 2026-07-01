from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4132"
SLUG = "task_4132_l0_backfill_stall_detection_supervisor_hardening"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
ARTIFACT_DIR = ROOT / "data/artifacts/l0_backfill_orchestration"
ENHANCED_SUMMARY = ARTIFACT_DIR / "enhanced_latest_summary.json"
CURRENT_ALERTS_JSON = ARTIFACT_DIR / "current_alerts.json"
CURRENT_ALERTS_MD = ARTIFACT_DIR / "current_alerts.md"
LANE_CSV = ARTIFACT_DIR / "lane_reliability.csv"
SOURCE_FAILURE_CSV = ARTIFACT_DIR / "source_failure_summary.csv"
RAW_AUDIT_CSV = ARTIFACT_DIR / "raw_cache_source_time_audit.csv"
FIVE_MIN_CHECKPOINT_JSON = ARTIFACT_DIR / "five_min_checkpoint_summary.json"
SUPERVISOR_RECOMMENDATIONS = ARTIFACT_DIR / "supervisor_recommendations.json"
HOURLY_LATEST = ARTIFACT_DIR / "hourly/latest_summary.json"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_reliability() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "scripts/run_l0_backfill_reliability_audit.py", "--write"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
    )
    return proc.returncode, proc.stdout + proc.stderr


def manifest_rows() -> list[dict[str, Any]]:
    rows = [
        {"path": "ops/task_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4132 registered and closed out", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "ops/doc_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4132 artifacts registered", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/CURRENT_TASKS.md", "type": "SSOT", "purpose": "TASK-4132 closeout recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/PROJECT_STATUS.md", "type": "SSOT", "purpose": "L0 reliability posture recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/ACTIVE_SSOT_INDEX.md", "type": "SSOT", "purpose": "TASK-4132 report indexed", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/architecture/l0_source_acquisition_project_management_plan.md", "type": "CANONICAL_DOC", "purpose": "L0 reliability hardening posture recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "scripts/report_l0_backfill_hourly_status.ps1", "type": "SCRIPT", "purpose": "Hourly reporter now emits TASK-4132 reliability evidence", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "scripts/run_l0_backfill_reliability_audit.py", "type": "SCRIPT", "purpose": "Stall, alert, source failure, raw audit, and 5m checkpoint builder", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/run_l0_backfill_supervisor.ps1", "type": "SCRIPT", "purpose": "Restart stopped incomplete lanes only", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/validate_l0_backfill_reliability_hardening.py", "type": "VALIDATOR", "purpose": "TASK-4132 validator", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/enhanced_latest_summary.json", "type": "REFERENCE", "purpose": "Latest reliability summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/current_alerts.json", "type": "REFERENCE", "purpose": "Machine-readable current alerts", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/current_alerts.md", "type": "REFERENCE", "purpose": "Human-readable current alerts", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/lane_reliability.csv", "type": "REFERENCE", "purpose": "Lane-level running, delta, event freshness, and stall status", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/source_failure_summary.csv", "type": "REFERENCE", "purpose": "Source-level failure and pending-unit summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/raw_cache_source_time_audit.csv", "type": "REFERENCE", "purpose": "Bounded raw/cache/source-time audit sample", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/five_min_checkpoint_summary.json", "type": "REFERENCE", "purpose": "5m checkpoint visibility", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/supervisor_recommendations.json", "type": "REFERENCE", "purpose": "Stopped-lane restart recommendations", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/report.md", "type": "TASK_REPORT", "purpose": "TASK-4132 report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/artifact_manifest.csv", "type": "ARTIFACT_MANIFEST", "purpose": "TASK-4132 artifact manifest", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/validation_results.md", "type": "VALIDATION_REPORT", "purpose": "TASK-4132 validation results", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/l0_backfill_reliability_summary.json", "type": "REFERENCE", "purpose": "TASK-4132 closeout summary", "created_or_modified": "created", "task_id": TASK_ID},
    ]
    return rows


def build_report(summary: dict[str, Any], lane_rows: list[dict[str, str]], errors: list[str]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(REPORT_DIR / "artifact_manifest.csv", manifest_rows())
    closeout = {
        "task_id": TASK_ID,
        "lane_count": len(summary.get("lanes", {})),
        "alert_count": len(summary.get("alerts", [])),
        "p0_alert_count": sum(1 for item in summary.get("alerts", []) if item.get("severity") == "P0"),
        "supervisor_recommendation_count": len(summary.get("supervisor_recommendations", [])),
        "raw_audit": summary.get("raw_audit", {}),
        "five_min_checkpoint": summary.get("five_min_checkpoint", {}),
        "seven_steps": {
            "backfill_completion_and_stall_monitoring": "IMPLEMENTED",
            "long_run_stability_visibility": "IMPLEMENTED",
            "five_min_checkpoint_visibility": "IMPLEMENTED",
            "source_failure_summary": "IMPLEMENTED",
            "restart_supervisor": "IMPLEMENTED_STOPPED_INCOMPLETE_ONLY",
            "actionable_alert_summary": "IMPLEMENTED",
            "raw_cache_source_time_audit": "IMPLEMENTED_BOUNDED_SAMPLE",
        },
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    write_json(REPORT_DIR / "l0_backfill_reliability_summary.json", closeout)
    lines = [
        "# TASK-4132 L0 Backfill Stall Detection And Supervisor Hardening",
        "",
        "## Result",
        "",
        f"- Lane count: `{closeout['lane_count']}`.",
        f"- Alert count: `{closeout['alert_count']}`.",
        f"- P0 alert count: `{closeout['p0_alert_count']}`.",
        f"- Supervisor recommendations: `{closeout['supervisor_recommendation_count']}`.",
        f"- 5m progress: `{closeout['five_min_checkpoint'].get('progress_pct')}`.",
        "",
        "## Lane Health",
        "",
    ]
    for row in lane_rows:
        lines.append(
            f"- `{row.get('lane')}`: {row.get('health')}, running={row.get('running')}, "
            f"progress={row.get('progress_pct')}, delta={row.get('metric_delta_since_last_audit')}, "
            f"last_event_age_min={row.get('last_event_age_minutes')}"
        )
    lines.extend(
        [
            "",
            "## Scope Boundary",
            "",
            "TASK-4132 hardens L0 collection reliability only. It does not evaluate trading usefulness, feature quality, L2/L3 semantic value, broker truth, replay validity, strategy acceptance, deployment readiness, or real capital.",
            "",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ]
    )
    (REPORT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    validation_lines = ["# TASK-4132 Validation Results", "", f"Result: {'FAIL' if errors else 'PASS'}.", ""]
    if errors:
        validation_lines.extend(["## Errors", ""])
        validation_lines.extend(f"- {error}" for error in errors)
        validation_lines.append("")
    validation_lines.extend(
        [
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ]
    )
    (REPORT_DIR / "validation_results.md").write_text("\n".join(validation_lines) + "\n", encoding="utf-8")


def validate() -> list[str]:
    errors: list[str] = []
    code, output = run_reliability()
    if code != 0:
        errors.append(f"reliability audit command failed: {output.strip()}")
    required = [
        ENHANCED_SUMMARY,
        CURRENT_ALERTS_JSON,
        CURRENT_ALERTS_MD,
        LANE_CSV,
        SOURCE_FAILURE_CSV,
        RAW_AUDIT_CSV,
        FIVE_MIN_CHECKPOINT_JSON,
        SUPERVISOR_RECOMMENDATIONS,
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required artifact: {rel(path)}")
    summary = read_json(ENHANCED_SUMMARY) if ENHANCED_SUMMARY.exists() else {}
    lane_rows = read_csv(LANE_CSV) if LANE_CSV.exists() else []
    if summary.get("task_id") != TASK_ID:
        errors.append("enhanced summary task_id must be TASK-4132")
    if len(summary.get("lanes", {})) < 5:
        errors.append("enhanced summary must include at least five lanes")
    if len(lane_rows) < 5:
        errors.append("lane reliability CSV must include at least five lanes")
    for row in lane_rows:
        if row.get("diagnostic_only_flag") != "1":
            errors.append(f"lane {row.get('lane')} diagnostic_only_flag must be 1")
        for field in ["trade_authority_flag", "broker_mutation_permitted_flag", "real_capital_permitted_flag"]:
            if row.get(field) != "0":
                errors.append(f"lane {row.get('lane')} {field} must remain 0")
    raw_rows = read_csv(RAW_AUDIT_CSV) if RAW_AUDIT_CSV.exists() else []
    if not raw_rows:
        errors.append("raw/cache/source-time audit must contain bounded sample rows")
    for row in raw_rows:
        for field in ["missing_source_is_negative", "assignment_uses_future_outcome", "outcome_used_for_assignment"]:
            if row.get(field) not in {"", "0"}:
                errors.append(f"raw audit row has forbidden assignment flag {field}=1")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")
    if int(summary.get("trade_authority_flag", 0) or 0) != 0:
        errors.append("trade authority flag must remain 0")
    if int(summary.get("broker_mutation_permitted_flag", 0) or 0) != 0:
        errors.append("broker mutation flag must remain 0")
    if int(summary.get("real_capital_permitted_flag", 0) or 0) != 0:
        errors.append("real capital flag must remain 0")
    if HOURLY_LATEST.exists():
        hourly = read_json(HOURLY_LATEST)
        if hourly.get("task_id") not in {"TASK-4131", TASK_ID}:
            errors.append("hourly latest summary has unexpected task_id")
    build_report(summary, lane_rows, errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_BACKFILL_RELIABILITY_ERROR] {error}")
        return 1
    print("[L0_BACKFILL_RELIABILITY_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
