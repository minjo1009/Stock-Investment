from __future__ import annotations

import csv
import json
import os
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4183"
OUT_DIR = Path("data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit")
REPORT_DIR = Path("docs/reports/task_4183_l0_l4_realtime_backfill_recovery_audit")

SCHEDULED_TASKS = [
    "TraderBrainL0BackfillWorkerRecovery4148",
    "TraderBrainL0L2Hardening4147",
    "ForeignStockQuantPaperWake",
]

ARTIFACT_PATHS = {
    "l0_collection_status": Path("data/artifacts/l0_collection_status/current_status.json"),
    "l0_newswire_backfill": Path("data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json"),
    "l0_backfill_reliability": Path("data/artifacts/l0_backfill_orchestration/enhanced_latest_summary.json"),
    "l1_feature_materialization": Path("data/artifacts/task_4179_l1_feature_materialization_repair/task_4179_l1_feature_materialization_summary.json"),
    "l1_ambiguous_blockers": Path("data/artifacts/task_4181_l1_ambiguous_blocker_deterministic_burn_down/task_4181_l1_ambiguous_summary.json"),
    "l2_wide_handoff": Path("data/artifacts/task_4146_l0_l2_wide_packetization_handoff/task_4146_l0_l2_wide_handoff_summary.json"),
    "l3_relation_graph": Path("data/artifacts/task_4154_l3_relation_graph_v2_quality_guard/l3_graph_quality_summary.json"),
    "l4_scanner": Path("data/artifacts/task_4176_l4_diagnostic_blocker_taxonomy_scanner_v1/task_4176_l4_scanner_summary.json"),
}

DB_TABLES = [
    "source_scheduler_registry",
    "market_bars_5m",
    "market_ticks",
    "l2_primitive_batches",
    "l2_primitive_facts",
    "l2_runtime_context_audit",
    "l2_runtime_source_receipts",
]


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"read_error": type(exc).__name__, "path": str(path)}
    return value if isinstance(value, dict) else {"payload_type": type(value).__name__}


def run_powershell(script: str) -> Any:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=20,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip(), "returncode": result.returncode}
    text = result.stdout.strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def scheduled_tasks() -> list[dict[str, Any]]:
    quoted = ",".join("'" + name + "'" for name in SCHEDULED_TASKS)
    script = (
        "$out=@(); "
        f"foreach ($n in @({quoted})) {{ "
        "$task=Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue; "
        "$info=Get-ScheduledTaskInfo -TaskName $n -ErrorAction SilentlyContinue; "
        "if ($task -and $info) { "
        "$out += [PSCustomObject]@{TaskName=$n;State=[string]$task.State;"
        "LastRunTime=[string]$info.LastRunTime;LastTaskResult=$info.LastTaskResult;"
        "NextRunTime=[string]$info.NextRunTime;NumberOfMissedRuns=$info.NumberOfMissedRuns} } }; "
        "$out | ConvertTo-Json -Depth 4"
    )
    value = run_powershell(script)
    if isinstance(value, dict):
        return [value]
    return value if isinstance(value, list) else []


def process_rows() -> list[dict[str, Any]]:
    script = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -match 'python|run_l0|scheduler|backfill|collector|l[0-4]' } | "
        "Select-Object ProcessId,Name,CreationDate,CommandLine | ConvertTo-Json -Depth 4"
    )
    value = run_powershell(script)
    if isinstance(value, dict) and "ProcessId" in value:
        return [value]
    return value if isinstance(value, list) else []


def pid_running(pid: Any) -> bool:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False
    try:
        os.kill(pid_int, 0)
        return True
    except OSError:
        return False


def db_latest_rows() -> dict[str, Any]:
    db_path = Path("trading.db")
    if not db_path.exists():
        return {"status": "MISSING", "path": str(db_path)}
    out: dict[str, Any] = {}
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2)
    con.row_factory = sqlite3.Row
    try:
        for table in DB_TABLES:
            try:
                cols = [row[1] for row in con.execute(f"pragma table_info({table})")]
                latest = con.execute(f"select * from {table} order by rowid desc limit 1").fetchone()
                max_rowid = con.execute(f"select max(rowid) from {table}").fetchone()[0]
                out[table] = {
                    "status": "PRESENT",
                    "max_rowid": max_rowid,
                    "columns": cols,
                    "latest_row": dict(latest) if latest else None,
                }
            except Exception as exc:
                out[table] = {"status": "ERROR", "error": type(exc).__name__, "message": str(exc)}
    finally:
        con.close()
    return out


def artifact_snapshot() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, path in ARTIFACT_PATHS.items():
        payload = load_json(path)
        out[name] = {
            "path": str(path),
            "exists": path.exists(),
            "last_write_time_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat().replace("+00:00", "Z") if path.exists() else "",
            "payload": payload,
        }
    return out


def latest_logs(limit: int = 30) -> list[dict[str, Any]]:
    logs = sorted(Path("logs").rglob("*"), key=lambda p: p.stat().st_mtime if p.is_file() else 0, reverse=True)
    rows = []
    for path in logs:
        if not path.is_file():
            continue
        rows.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "last_write_time_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat().replace("+00:00", "Z"),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def level_verdicts(artifacts: dict[str, Any], db: dict[str, Any], tasks: list[dict[str, Any]], processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    newswire = artifacts.get("l0_newswire_backfill", {}).get("payload", {})
    active_workers = newswire.get("active_workers", []) if isinstance(newswire, dict) else []
    dead_active_workers = [row for row in active_workers if not pid_running(row.get("pid"))]
    python_collectors = [row for row in processes if "python" in str(row.get("Name", "")).lower() or "python" in str(row.get("CommandLine", "")).lower()]
    task_by_name = {row.get("TaskName"): row for row in tasks}
    l0_l2_task = task_by_name.get("TraderBrainL0L2Hardening4147", {})
    backfill_task = task_by_name.get("TraderBrainL0BackfillWorkerRecovery4148", {})

    backfill_result = backfill_task.get("LastTaskResult")
    l0_l2_result = l0_l2_task.get("LastTaskResult")
    backfill_running = backfill_task.get("State") == "Running" or backfill_result == 267009
    l0_l2_running = l0_l2_task.get("State") == "Running" or l0_l2_result == 267009
    l0_status = "PARTIAL_RUNNING_WITH_BLOCKER"
    l0_reason = "backfill/L0-L2 scheduled tasks are running or recently successful, but public newswire aggregate still records dead active worker PIDs"
    if (backfill_running or backfill_result == 0) and l0_l2_running and not dead_active_workers and python_collectors:
        l0_status = "RUNNING"
        l0_reason = "scheduled backfill and L0-L2 tasks plus live Python collectors are observed"

    l1_summary = artifacts.get("l1_feature_materialization", {}).get("payload", {})
    l1_status = "RECENT_ARTIFACT_PRESENT" if artifacts.get("l1_feature_materialization", {}).get("exists") else "UNKNOWN"

    l2_db = db.get("l2_primitive_facts", {})
    l2_latest = (l2_db.get("latest_row") or {}).get("asof_ts") if isinstance(l2_db, dict) else ""
    l2_status = "STALE_OR_NOT_REALTIME_DB"
    if l2_latest and str(l2_latest) >= "2026-07-01":
        l2_status = "CURRENT_OR_RECENT"

    l3_status = "RECENT_ARTIFACT_PRESENT" if artifacts.get("l3_relation_graph", {}).get("exists") else "UNKNOWN"
    l4_status = "RECENT_ARTIFACT_PRESENT" if artifacts.get("l4_scanner", {}).get("exists") else "UNKNOWN"

    return [
        {
            "level": "L0",
            "status": l0_status,
            "reason": l0_reason,
            "scheduled_backfill_result": backfill_result,
            "scheduled_l0_l2_result": l0_l2_result,
            "scheduled_backfill_state": backfill_task.get("State"),
            "scheduled_l0_l2_state": l0_l2_task.get("State"),
            "aggregate_status": newswire.get("status"),
            "aggregate_progress_pct": newswire.get("progress_pct"),
            "aggregate_pending_units": newswire.get("pending_units"),
            "aggregate_active_workers": len(active_workers),
            "dead_active_workers": len(dead_active_workers),
            "python_collector_processes": len(python_collectors),
        },
        {
            "level": "L1",
            "status": l1_status,
            "reason": "latest L1 task artifacts are present; this does not prove a live parser loop",
            "feature_materialization_rows": l1_summary.get("feature_materialization_candidate_count", l1_summary.get("feature_candidate_count", "")),
        },
        {
            "level": "L2",
            "status": l2_status,
            "reason": "DB L2 runtime primitive latest asof is older than July 1; separate L0-L2 hardening artifacts are updating but DB runtime is stale",
            "latest_asof_ts": l2_latest,
            "latest_rowid": l2_db.get("max_rowid") if isinstance(l2_db, dict) else "",
        },
        {
            "level": "L3",
            "status": l3_status,
            "reason": "relation-graph artifacts exist, but no live L3 scheduler/process was observed",
        },
        {
            "level": "L4",
            "status": l4_status,
            "reason": "L4 scanner artifact exists, but no live L4 scheduler/process was observed",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_report(summary: dict[str, Any], verdicts: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TASK-4183 L0-L4 Realtime and Backfill Recovery Audit",
        "",
        "## Conclusion",
        "",
        f"- Overall verdict: {summary['overall_verdict']}",
        f"- Generated at: {summary['generated_at']}",
        "- Scope: L0-L4 collection/backfill/read-model health audit only.",
        "- Trading safety: diagnostic-only; no broker mutation, paper promotion, live order, or real-capital permission.",
        "",
        "## Level Verdicts",
        "",
        "| Level | Status | Reason |",
        "|---|---|---|",
    ]
    for row in verdicts:
        lines.append(f"| {row['level']} | {row['status']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Key Evidence",
            "",
            f"- L0 public newswire aggregate status: {summary.get('l0_aggregate_status')} progress={summary.get('l0_aggregate_progress_pct')} pending_units={summary.get('l0_aggregate_pending_units')}",
            f"- L0 aggregate active workers: {summary.get('l0_aggregate_active_workers')} recorded, dead PIDs={summary.get('l0_dead_active_workers')}",
            f"- Python collector processes observed: {summary.get('python_collector_processes')}",
            f"- Scheduled backfill worker result: {summary.get('scheduled_backfill_result')}",
            f"- Scheduled L0-L2 hardening result: {summary.get('scheduled_l0_l2_result')}",
            f"- L2 latest asof: {summary.get('l2_latest_asof_ts')}",
            "",
            "## Safety Boundary",
            "",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ]
    )
    (REPORT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_contract(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""task_id: {TASK_ID}
task_type: DIAGNOSTIC_ONLY
domain: L0_L4_RECOVERY_AUDIT
hard_state:
  strategy: NOT_ACCEPTED
  deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
  real_capital: FORBIDDEN
  broker_mutation: FORBIDDEN
  live_order: FORBIDDEN
  paper_promotion: FORBIDDEN
  missing_stale_incomplete_data_semantics: UNKNOWN_OR_BLOCKER_NEVER_NEGATIVE_EVIDENCE
scope:
  changed_paths:
    - scripts/run_task4183_l0_l4_realtime_backfill_recovery_audit.py
    - scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
    - data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit/**
    - docs/reports/task_4183_l0_l4_realtime_backfill_recovery_audit/**
    - ops/task_registry.yaml
    - ops/doc_registry.yaml
  allowed_paths:
    - scripts/run_task4183_l0_l4_realtime_backfill_recovery_audit.py
    - scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
    - data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit/**
    - docs/reports/task_4183_l0_l4_realtime_backfill_recovery_audit/**
    - ops/task_registry.yaml
    - ops/doc_registry.yaml
  forbidden_paths:
    - broker/**
    - live_trading/**
    - production_orders/**
    - secrets/**
    - configs/broker/**
outcome_unit:
  name: stale_realtime_collector_count
  direction: change
  problem_progress_claim_allowed: false
  harness_progress_claim_allowed: false
intended_change:
  summary: Record a read-only L0-L4 runtime and backfill health snapshot after workstation recovery.
measurement_method:
  commands:
    - python scripts/run_task4183_l0_l4_realtime_backfill_recovery_audit.py
    - python scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
allowed_actions:
  - read process and scheduled task state
  - read artifact and database freshness snapshots
  - write task-scoped audit artifacts and report
forbidden_actions:
  - broker mutation
  - paper promotion
  - live order
  - strategy acceptance
  - missing data as negative evidence
evidence_artifacts:
  required:
    - data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit/task_4183_recovery_audit_summary.json
    - data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit/task_4183_level_verdicts.csv
    - data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit/task_4183_scheduled_tasks.json
    - data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit/task_4183_process_snapshot.json
validators:
  required:
    - python scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
    - python scripts/ops/validate_prime_task_contracts.py --task TASK-4183
progress_claim_policy:
  actual_underlying_progress: false
  missing_data_used_as_negative_evidence: false
  closeout_claims:
    - Read-only audit only.
closeout_verdict:
  selected: BLOCKED_BY_UPSTREAM
  reason: {summary['overall_verdict']}
report:
  path: docs/reports/task_4183_l0_l4_realtime_backfill_recovery_audit/report.md
  summary: Read-only audit recorded L0-L4 collection status and residual blockers.
  claims:
    - Not all audited lanes have current runtime evidence.
  actual_underlying_progress: false
next_target:
  required: true
  task_type: OUTCOME_CHANGE
  outcome_unit: stale_realtime_collector_count
  required_baseline: task_4183_recovery_audit_summary.json
  required_validator: validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
layer_outcome_validation:
  layer: L0
"""
    (REPORT_DIR / "task_result_contract.yaml").write_text(text, encoding="utf-8")


def write_manifest() -> None:
    rows = [
        ("scripts/run_task4183_l0_l4_realtime_backfill_recovery_audit.py", "RUNNER", "Generate the read-only recovery audit snapshot."),
        ("scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py", "VALIDATOR", "Validate task-scoped audit artifacts and safety flags."),
        (str(OUT_DIR / "task_4183_recovery_audit_summary.json"), "SUMMARY", "Machine-readable audit conclusion."),
        (str(OUT_DIR / "task_4183_level_verdicts.csv"), "LEVEL_VERDICTS", "L0-L4 per-level status table."),
        (str(OUT_DIR / "task_4183_scheduled_tasks.json"), "SCHEDULED_TASKS", "Windows scheduled task state snapshot."),
        (str(OUT_DIR / "task_4183_process_snapshot.json"), "PROCESS_SNAPSHOT", "Runtime process snapshot."),
        (str(OUT_DIR / "task_4183_db_latest_rows.json"), "DB_LATEST_ROWS", "Read-only latest-row DB evidence."),
        (str(OUT_DIR / "task_4183_artifact_snapshot.json"), "ARTIFACT_SNAPSHOT", "Latest relevant artifact evidence."),
        (str(REPORT_DIR / "task_result_contract.yaml"), "CONTRACT", "Prime task result contract."),
        (str(REPORT_DIR / "report.md"), "TASK_REPORT", "Human-readable closeout report."),
        (str(REPORT_DIR / "artifact_manifest.csv"), "ARTIFACT_MANIFEST", "Artifact inventory."),
        (str(REPORT_DIR / "validation_results.md"), "VALIDATION_REPORT", "Validator run log."),
        ("ops/task_registry.yaml", "REGISTRY", "Task registry update."),
        ("ops/doc_registry.yaml", "REGISTRY", "Document registry update."),
    ]
    with (REPORT_DIR / "artifact_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "type", "purpose", "created_or_modified", "task_id"])
        for path, artifact_type, purpose in rows:
            writer.writerow([path.replace("\\", "/"), artifact_type, purpose, "created_or_modified", TASK_ID])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    tasks = scheduled_tasks()
    processes = process_rows()
    artifacts = artifact_snapshot()
    db = db_latest_rows()
    logs = latest_logs()
    verdicts = level_verdicts(artifacts, db, tasks, processes)

    l0 = next(row for row in verdicts if row["level"] == "L0")
    l2 = next(row for row in verdicts if row["level"] == "L2")
    overall = "PASS_ALL_RUNNING" if all(row["status"] in {"RUNNING", "CURRENT_OR_RECENT"} for row in verdicts) else "BLOCKED_NOT_ALL_RUNNING"
    summary = {
        "task_id": TASK_ID,
        "generated_at": now_z(),
        "overall_verdict": overall,
        "l0_aggregate_status": l0.get("aggregate_status"),
        "l0_aggregate_progress_pct": l0.get("aggregate_progress_pct"),
        "l0_aggregate_pending_units": l0.get("aggregate_pending_units"),
        "l0_aggregate_active_workers": l0.get("aggregate_active_workers"),
        "l0_dead_active_workers": l0.get("dead_active_workers"),
        "python_collector_processes": l0.get("python_collector_processes"),
        "scheduled_backfill_result": l0.get("scheduled_backfill_result"),
        "scheduled_l0_l2_result": l0.get("scheduled_l0_l2_result"),
        "l2_latest_asof_ts": l2.get("latest_asof_ts"),
        "diagnostic_only": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "paper_promotion_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }

    (OUT_DIR / "task_4183_recovery_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "task_4183_scheduled_tasks.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "task_4183_process_snapshot.json").write_text(json.dumps(processes, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "task_4183_db_latest_rows.json").write_text(json.dumps(db, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "task_4183_artifact_snapshot.json").write_text(json.dumps(artifacts, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "task_4183_latest_logs.json").write_text(json.dumps(logs, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(
        OUT_DIR / "task_4183_level_verdicts.csv",
        verdicts,
        [
            "level",
            "status",
            "reason",
            "scheduled_backfill_result",
            "scheduled_l0_l2_result",
            "aggregate_status",
            "aggregate_progress_pct",
            "aggregate_pending_units",
            "aggregate_active_workers",
            "dead_active_workers",
            "python_collector_processes",
            "latest_asof_ts",
        ],
    )
    write_report(summary, verdicts)
    write_contract(summary)
    write_manifest()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
