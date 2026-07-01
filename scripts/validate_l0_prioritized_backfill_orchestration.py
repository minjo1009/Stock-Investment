from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4131"
SLUG = "task_4131_l0_prioritized_backfill_background_orchestration"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
ARTIFACT_DIR = ROOT / "data/artifacts/l0_backfill_orchestration"
SUMMARY_PATH = ARTIFACT_DIR / "orchestration_summary.json"
START_LEDGER_PATH = ARTIFACT_DIR / "start_ledger.json"
HOURLY_SUMMARY_PATH = ARTIFACT_DIR / "hourly/latest_summary.json"
SMOKE_PROGRESS_PATH = ROOT / "data/artifacts/l0_public_newswire_smoke_task_4131/collector_progress.json"
SCHEDULER_PATH = ROOT / "configs/db_source_acquisition_scheduler.json"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    fields = list(fieldnames or [])
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_optional_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return read_json(path)
    except json.JSONDecodeError:
        return None


def status_rows(start_ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in sorted(start_ledger, key=lambda row: int(row.get("priority", 99) or 99)):
        rows.append(
            {
                "task_id": TASK_ID,
                "priority": item.get("priority", ""),
                "lane": item.get("lane", ""),
                "status": item.get("status", ""),
                "started": int(bool(item.get("started"))),
                "already_running": int(bool(item.get("already_running"))),
                "status_path": item.get("status_path", ""),
                "reason": item.get("reason", ""),
            }
        )
    return rows


def build_report_files(summary: dict[str, Any], rows: list[dict[str, Any]], hourly: Any, smoke: Any, errors: list[str]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows = [
        {"path": "ops/task_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4131 task scope and closeout tracking", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "ops/doc_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4131 docs and artifacts registered", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/CURRENT_TASKS.md", "type": "SSOT", "purpose": "TASK-4131 closeout recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/PROJECT_STATUS.md", "type": "SSOT", "purpose": "Backfill orchestration state recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/ACTIVE_SSOT_INDEX.md", "type": "SSOT", "purpose": "TASK-4131 report registered as active evidence", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/architecture/l0_source_acquisition_project_management_plan.md", "type": "CANONICAL_DOC", "purpose": "Background backfill posture recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "scripts/start_l0_prioritized_backfills.ps1", "type": "SCRIPT", "purpose": "Priority backfill background starter", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/report_l0_backfill_hourly_status.ps1", "type": "SCRIPT", "purpose": "Hourly status snapshot and alert writer", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/validate_l0_prioritized_backfill_orchestration.py", "type": "VALIDATOR", "purpose": "TASK-4131 validator", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "tools/db/source_acquisition/bar_full_backfill.py", "type": "COLLECTOR", "purpose": "Keep bar backfill alive when log append fails on local OneDrive paths", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "tools/db/source_acquisition/public_context_news_collector.py", "type": "COLLECTOR", "purpose": "Keep context backfill alive when log append fails on local OneDrive paths", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/orchestration_summary.json", "type": "REFERENCE", "purpose": "Backfill start summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/start_ledger.json", "type": "REFERENCE", "purpose": "Backfill start ledger", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/hourly/latest_summary.json", "type": "REFERENCE", "purpose": "Latest hourly tracking summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_backfill_orchestration/log_write_failures.jsonl", "type": "REFERENCE", "purpose": "Fallback ledger for non-fatal log append failures", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "data/artifacts/l0_public_newswire_smoke_task_4131/collector_progress.json", "type": "REFERENCE", "purpose": "Real public newswire smoke progress", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/report.md", "type": "TASK_REPORT", "purpose": "TASK-4131 report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/artifact_manifest.csv", "type": "ARTIFACT_MANIFEST", "purpose": "TASK-4131 artifact manifest", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/validation_results.md", "type": "VALIDATION_REPORT", "purpose": "TASK-4131 validation report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/l0_backfill_orchestration_summary.json", "type": "REFERENCE", "purpose": "TASK-4131 closeout summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4131_backfill_start_ledger.csv", "type": "REFERENCE", "purpose": "Priority backfill start ledger", "created_or_modified": "created", "task_id": TASK_ID},
    ]
    write_csv(REPORT_DIR / "artifact_manifest.csv", manifest_rows)
    write_csv(REPORT_DIR / "task_4131_backfill_start_ledger.csv", rows)
    closeout = {
        "task_id": TASK_ID,
        "orchestration_status": summary.get("orchestration_status", ""),
        "started_count": int(summary.get("started_count", 0) or 0),
        "already_running_count": int(summary.get("already_running_count", 0) or 0),
        "lane_count": len(rows),
        "hourly_tracking_configured": int(isinstance(hourly, dict)),
        "latest_running": hourly.get("running", {}) if isinstance(hourly, dict) else {},
        "latest_progress": hourly.get("progress", {}) if isinstance(hourly, dict) else {},
        "newswire_smoke_status": smoke.get("status", "") if isinstance(smoke, dict) else "",
        "newswire_smoke_processed": int(smoke.get("processed_this_run", 0) or 0) if isinstance(smoke, dict) else 0,
        "log_append_failure_nonfatal_hardening": "ENABLED",
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    write_json(REPORT_DIR / "l0_backfill_orchestration_summary.json", closeout)
    report_lines = [
        "# TASK-4131 L0 Prioritized Backfill Background Orchestration",
        "",
        "## Result",
        "",
        f"- Orchestration status: `{closeout['orchestration_status']}`.",
        f"- Background lanes started this run: `{closeout['started_count']}`.",
        f"- Already-running lanes skipped: `{closeout['already_running_count']}`.",
        f"- Hourly tracking configured: `{closeout['hourly_tracking_configured']}`.",
        f"- Public newswire hardening smoke status: `{closeout['newswire_smoke_status']}`.",
        "- Daily/context log append failures are non-fatal and mirrored to the TASK-4131 fallback ledger when possible.",
        "",
        "## Priority Order",
        "",
    ]
    for row in rows:
        report_lines.append(f"- P{row['priority']} `{row['lane']}`: {row['status']} - {row['reason']}")
    report_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This starts or tracks diagnostic L0 collection only. It does not open trading, order, broker, strategy acceptance, deployment, or real-capital gates.",
            "",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ]
    )
    (REPORT_DIR / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    validation_lines = ["# TASK-4131 Validation Results", "", f"Result: {'FAIL' if errors else 'PASS'}.", ""]
    if errors:
        validation_lines.append("## Errors")
        validation_lines.append("")
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
    required = [SUMMARY_PATH, START_LEDGER_PATH, HOURLY_SUMMARY_PATH, SMOKE_PROGRESS_PATH]
    for path in required:
        if not path.exists():
            errors.append(f"missing required orchestration artifact: {rel(path)}")
    if errors:
        build_report_files({}, [], None, None, errors)
        return errors
    summary = read_json(SUMMARY_PATH)
    start_ledger = read_json(START_LEDGER_PATH)
    hourly = load_optional_json(HOURLY_SUMMARY_PATH)
    smoke = load_optional_json(SMOKE_PROGRESS_PATH)
    if summary.get("task_id") != TASK_ID:
        errors.append("orchestration summary task_id must be TASK-4131")
    if summary.get("orchestration_status") != "BACKGROUND_START_REQUESTED":
        errors.append("orchestration status must be BACKGROUND_START_REQUESTED")
    if not isinstance(start_ledger, list) or len(start_ledger) < 5:
        errors.append("start ledger must contain at least five lanes")
        start_ledger = []
    lane_names = {str(row.get("lane", "")) for row in start_ledger}
    expected = {
        "daily_bars_remaining",
        "public_context_news_backfill",
        "public_newswire_backfill",
        "public_market_macro_news_backfill",
        "five_min_bars_long_backfill",
        "hourly_status_reporter",
    }
    missing = expected - lane_names
    if missing:
        errors.append(f"start ledger missing lanes: {', '.join(sorted(missing))}")
    active = [row for row in start_ledger if bool(row.get("started")) or bool(row.get("already_running"))]
    if len(active) < 5:
        errors.append("at least five collection/reporting lanes must be started or already running")
    if not isinstance(hourly, dict):
        errors.append("hourly latest summary must be readable")
    else:
        running = hourly.get("running", {})
        required_running = {
            "daily",
            "five_min",
            "public_newswire_backfill",
            "public_context_news_backfill",
            "public_market_macro_news_backfill",
        }
        not_running = sorted(name for name in required_running if not bool(running.get(name)))
        if not_running:
            errors.append(f"latest hourly summary has non-running lanes: {', '.join(not_running)}")
    if not isinstance(smoke, dict):
        errors.append("public newswire smoke progress must be readable")
    elif int(smoke.get("processed_this_run", 0) or 0) <= 0:
        errors.append("public newswire smoke must process at least one source")
    scheduler = read_json(SCHEDULER_PATH)
    if scheduler.get("strategy") != "NOT_ACCEPTED":
        errors.append("scheduler strategy changed")
    if scheduler.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("scheduler deployment changed")
    if scheduler.get("real_capital") != "FORBIDDEN":
        errors.append("scheduler real capital changed")
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
    rows = status_rows(start_ledger)
    build_report_files(summary, rows, hourly, smoke, errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_BACKFILL_ORCHESTRATION_ERROR] {error}")
        return 1
    print("[L0_BACKFILL_ORCHESTRATION_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
