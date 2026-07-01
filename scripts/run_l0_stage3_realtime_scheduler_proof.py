from __future__ import annotations

import argparse
import copy
import csv
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4121"
DEFAULT_OUT_DIR = ROOT / "docs/reports/task_4121_l0_stage_3_realtime_scheduler_setup_and_execution"
SCHEDULER_CONFIG = ROOT / "configs/db_source_acquisition_scheduler.json"
REALTIME_JOBS = {
    "official_news_sources_15m",
    "gdelt_news_discovery_15m",
    "marketaux_news_free_30m",
}

sys.path.append(str(ROOT))
from tools.db.source_acquisition.scheduler_override import load_effective_scheduler_config  # noqa: E402


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_scheduler() -> dict[str, Any]:
    return json.loads(SCHEDULER_CONFIG.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
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


def clean_generated_dirs(out_dir: Path) -> None:
    for directory in [out_dir / "scheduler_runtime_artifacts", out_dir / "scheduler_logs"]:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()


def force_permissions_closed(config: dict[str, Any]) -> None:
    permissions = config.setdefault("permissions", {})
    permissions["diagnostic_only"] = True
    for field in [
        "execution_permitted",
        "broker_mutation_permitted",
        "paper_promotion_permitted",
        "real_capital_permitted",
        "live_order_enabled",
        "replay_permission_granted",
        "buy_sell_signal_generation_permitted",
    ]:
        permissions[field] = 0
    for job in config.get("jobs", []):
        if not isinstance(job, dict):
            continue
        job["diagnostic_only"] = True
        for field in [
            "execution_permitted",
            "broker_mutation_permitted",
            "paper_promotion_permitted",
            "real_capital_permitted",
            "live_order_enabled",
            "replay_permission_granted",
            "buy_sell_signal_generation_permitted",
        ]:
            job[field] = 0
        if "feature_builder_enabled" in job:
            job["feature_builder_enabled"] = False


def task_override_payload(base: dict[str, Any]) -> dict[str, Any]:
    jobs = {job.get("name"): job for job in base.get("jobs", []) if isinstance(job, dict)}
    payload_jobs: list[dict[str, Any]] = []
    for name in sorted(REALTIME_JOBS):
        job = jobs[name]
        item: dict[str, Any] = {
            "name": name,
            "enabled": True,
            "allow_network": False,
            "interval_minutes": int(job.get("interval_minutes", 15) or 15),
            "symbols": list(job.get("symbols", [])),
            "macro_series": list(job.get("macro_series", [])),
            "mode": "stage3_scheduler_proof",
            "diagnostic_only": True,
        }
        if name == "marketaux_news_free_30m":
            item["interval_minutes"] = 16
            item["articles_per_request"] = int(job.get("articles_per_request", 3) or 3)
            item["daily_request_cap"] = int(job.get("daily_request_cap", 95) or 95)
        payload_jobs.append(item)
    return {
        "posture": "task_4121_stage3_scheduler_proof",
        "permissions": {"diagnostic_only": True},
        "jobs": payload_jobs,
    }


def proof_config(base: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    config = copy.deepcopy(base)
    config["posture"] = "task_4121_stage3_scheduler_proof"
    config["artifact_dir"] = rel(out_dir / "scheduler_runtime_artifacts")
    config["registered_loop_enabled"] = False
    config["default_allow_network"] = False
    for job in config.get("jobs", []):
        if not isinstance(job, dict):
            continue
        name = str(job.get("name"))
        job["enabled"] = name in REALTIME_JOBS
        job["allow_network"] = False
        if name == "marketaux_news_free_30m":
            job["interval_minutes"] = 16
        if name in REALTIME_JOBS:
            job["mode"] = "stage3_scheduler_proof"
    force_permissions_closed(config)
    return config


def setup_plan_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for job in config.get("jobs", []):
        if not isinstance(job, dict) or not bool(job.get("enabled")):
            continue
        interval = int(job.get("interval_minutes", 0) or 0)
        rows.append(
            {
                "task_id": TASK_ID,
                "job_name": job.get("name", ""),
                "source_families": "|".join(str(item) for item in job.get("families", [])),
                "enabled_in_task_proof": int(bool(job.get("enabled"))),
                "allow_network": int(bool(job.get("allow_network"))),
                "interval_minutes": interval,
                "scheduled_requests_per_day": int((1440 + interval - 1) / interval) if interval else 0,
                "mode": job.get("mode", ""),
                "diagnostic_only": int(bool(job.get("diagnostic_only"))),
                "execution_permitted": int(bool(job.get("execution_permitted", 0))),
                "broker_mutation_permitted": int(bool(job.get("broker_mutation_permitted", 0))),
                "real_capital_permitted": int(bool(job.get("real_capital_permitted", 0))),
                "proof_note": "task-local forced-due recurrence proof; provider network disabled",
            }
        )
    return rows


def run_scheduler(proof_config_path: Path, out_dir: Path) -> dict[str, Any]:
    log_dir = out_dir / "scheduler_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT / "scripts/run_db_source_acquisition_scheduler.ps1"),
        "-Config",
        str(proof_config_path),
        "-IntervalSeconds",
        "1",
        "-MaxRuns",
        "2",
        "-ForceDue",
        "-LogDir",
        str(log_dir),
    ]
    proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "log_dir": rel(log_dir),
    }


def runtime_json_rows(out_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((out_dir / "scheduler_runtime_artifacts").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        rows.append(
            {
                "task_id": TASK_ID,
                "artifact_path": rel(path),
                "bucket": payload.get("bucket", ""),
                "requested_families": "|".join(payload.get("requested_families", [])),
                "requested_symbols": "|".join(payload.get("requested_symbols", [])),
                "requested_apply": int(bool(payload.get("requested_apply"))),
                "allow_network_requested": int(bool(payload.get("allow_network_requested"))),
                "network_calls_made": int(payload.get("network_calls_made", 0) or 0),
                "db_mutation_made": int(payload.get("db_mutation_made", 0) or 0),
                "collection_apply_mode": payload.get("collection_apply_mode", ""),
                "diagnostic_only": int(bool(payload.get("diagnostic_only"))),
                "execution_permitted": int(bool(payload.get("execution_permitted", 0))),
                "broker_mutation_permitted": int(bool(payload.get("broker_mutation_permitted", 0))),
                "paper_promotion_permitted": int(bool(payload.get("paper_promotion_permitted", 0))),
                "live_order_enabled": int(bool(payload.get("live_order_enabled", 0))),
                "real_capital_permitted": int(bool(payload.get("real_capital_permitted", 0))),
            }
        )
    return rows


def write_protocol_tables(out_dir: Path, setup_rows: list[dict[str, Any]], execution_rows: list[dict[str, Any]]) -> None:
    write_csv(
        out_dir / "task_4121_scope_freeze.csv",
        [
            {
                "task_id": TASK_ID,
                "scope_type": "stage3_realtime_scheduler_proof",
                "universe": "AAPL|MSFT|NVDA|AMD|QQQ plus macro release feeds from scheduler config",
                "decision_dates": "not_applicable_scheduler_recurrence_proof",
                "network_calls_allowed": 0,
                "persistent_os_task_installed": 0,
                "status": "FROZEN",
            }
        ],
    )
    write_csv(out_dir / "task_4121_source_family_plan.csv", setup_rows)
    write_csv(out_dir / "task_4121_scheduler_setup_plan.csv", setup_rows)
    write_csv(out_dir / "task_4121_scheduler_execution_ledger.csv", execution_rows)
    write_csv(
        out_dir / "task_4121_api_or_raw_call_ledger.csv",
        [
            {
                "task_id": TASK_ID,
                "artifact_path": row["artifact_path"],
                "provider_call_status": "NOT_CALLED_SCHEDULER_PROOF_ONLY",
                "network_calls_made": row["network_calls_made"],
                "db_mutation_made": row["db_mutation_made"],
                "raw_path": row["artifact_path"],
                "raw_sha256": "",
            }
            for row in execution_rows
        ],
    )
    write_csv(
        out_dir / "task_4121_raw_response_classification.csv",
        [
            {
                "task_id": TASK_ID,
                "artifact_path": row["artifact_path"],
                "classification": "SCHEDULER_EXECUTION_AUDIT_JSON",
                "provider_payload_present": 0,
                "secret_leak_detected": 0,
                "strict_gate_opened": 0,
            }
            for row in execution_rows
        ],
    )
    packet_fields = [
        "task_id",
        "source_packet_id",
        "candidate_id",
        "trade_spec_id",
        "symbol",
        "decision_asof_ts",
        "provider",
        "endpoint_or_source_family",
        "source_ts",
        "available_to_brain_ts",
        "source_time_basis",
        "source_time_certified",
        "raw_path",
        "raw_sha256",
        "strict_gate_pass",
        "proxy_feature_allowed",
        "missing_source_is_negative",
        "assignment_uses_future_outcome",
        "outcome_used_for_assignment",
        "authority",
    ]
    write_csv(out_dir / "task_4121_normalized_source_packets.csv", [], fieldnames=packet_fields)
    write_csv(
        out_dir / "task_4121_decision_asof_coverage.csv",
        [
            {
                "task_id": TASK_ID,
                "coverage_scope": "stage3_scheduler_proof",
                "decision_asof_applicable": 0,
                "coverage_status": "NOT_APPLICABLE_NO_SOURCE_ROWS_ADMITTED",
            }
        ],
    )
    write_csv(
        out_dir / "task_4121_feature_admission_gate.csv",
        [
            {
                "task_id": TASK_ID,
                "gate": "stage3_scheduler_proof",
                "strict_gate_pass": 0,
                "proxy_feature_allowed": 0,
                "feature_builder_enabled": 0,
                "l2_handoff_allowed": 0,
            }
        ],
    )
    write_csv(
        out_dir / "task_4121_source_gap_ledger.csv",
        [
            {
                "task_id": TASK_ID,
                "gap": "provider_collection_not_executed",
                "status": "INTENTIONAL_STAGE3_SCHEDULER_PROOF_ONLY",
                "missing_source_is_negative": 0,
            }
        ],
    )
    due_rows = []
    for index, row in enumerate(execution_rows, start=1):
        due_rows.append(
            {
                "task_id": TASK_ID,
                "execution_index": index,
                "bucket": row.get("bucket", ""),
                "artifact_path": row.get("artifact_path", ""),
                "force_due": 1,
                "status": "EXECUTED_AUDIT_ONLY",
            }
        )
    write_csv(out_dir / "task_4121_scheduler_due_cycle_ledger.csv", due_rows)


def run(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    clean_generated_dirs(out_dir)
    base = load_scheduler()
    override = task_override_payload(base)
    override_path = out_dir / "stage3_scheduler_proof_override.json"
    write_json(override_path, override)
    audit_path = out_dir / "effective_scheduler_config_audit.json"
    load_effective_scheduler_config(override_path=override_path, audit_path=audit_path)

    config = proof_config(base, out_dir)
    proof_config_path = out_dir / "stage3_scheduler_proof_config.json"
    write_json(proof_config_path, config)

    setup_rows = setup_plan_rows(config)
    scheduler_result = run_scheduler(proof_config_path, out_dir)
    write_json(out_dir / "stage3_scheduler_command_result.json", scheduler_result)

    execution_rows = runtime_json_rows(out_dir)
    write_protocol_tables(out_dir, setup_rows, execution_rows)

    expected_artifacts = len(setup_rows) * 2
    network_calls = sum(int(row.get("network_calls_made", 0) or 0) for row in execution_rows)
    db_mutations = sum(int(row.get("db_mutation_made", 0) or 0) for row in execution_rows)
    status = "REALTIME_SCHEDULER_PROOF_EXECUTED"
    if scheduler_result["returncode"] != 0 or len(execution_rows) < expected_artifacts:
        status = "REALTIME_SCHEDULER_PROOF_FAILED"
    summary = {
        "task_id": TASK_ID,
        "updated_at": now_z(),
        "stage3_status": status,
        "enabled_realtime_job_count": len(setup_rows),
        "expected_execution_artifact_count": expected_artifacts,
        "execution_artifact_count": len(execution_rows),
        "scheduler_returncode": scheduler_result["returncode"],
        "persistent_os_task_installed": 0,
        "network_calls_made": network_calls,
        "db_mutation_made": db_mutations,
        "registered_loop_enabled": 0,
        "collection_apply_mode": "AUDIT_ONLY_NO_PROVIDER_EXECUTION",
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "broker_mutation_permitted": 0,
        "paper_promotion_permitted": 0,
        "live_order_enabled": 0,
        "next_stage": "historical_backfill_optimization",
    }
    write_json(out_dir / "stage3_scheduler_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run L0 Stage 3 realtime scheduler setup and execution proof.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[L0_STAGE3_REALTIME_SCHEDULER_PROOF] "
        f"status={summary['stage3_status']} artifacts={summary['execution_artifact_count']}/"
        f"{summary['expected_execution_artifact_count']} network_calls_made={summary['network_calls_made']} "
        "persistent_os_task_installed=0 broker_mutation_permitted=0 real_capital_permitted=0"
    )
    return 0 if summary["stage3_status"] == "REALTIME_SCHEDULER_PROOF_EXECUTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
