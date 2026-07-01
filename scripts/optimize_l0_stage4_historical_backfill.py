from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4122"
DEFAULT_OUT_DIR = ROOT / "docs/reports/task_4122_l0_stage_4_historical_backfill_optimization"
SCHEDULER_CONFIG = ROOT / "configs/db_source_acquisition_scheduler.json"
BACKFILL_JOBS = [
    "public_context_news_backfill",
    "public_market_macro_news_backfill",
    "microstructure_backfill_batch",
]


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_scheduler() -> dict[str, Any]:
    return json.loads(SCHEDULER_CONFIG.read_text(encoding="utf-8-sig"))


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


def job_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {job.get("name"): job for job in config.get("jobs", []) if isinstance(job, dict)}


def optimization_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = job_map(config)
    rows: list[dict[str, Any]] = []
    for name in BACKFILL_JOBS:
        job = jobs.get(name, {})
        stage4 = job.get("stage4_backfill_optimization", {}) if isinstance(job, dict) else {}
        rows.append(
            {
                "task_id": TASK_ID,
                "job_name": name,
                "families": "|".join(str(item) for item in job.get("families", [])),
                "sources": "|".join(str(item) for item in job.get("sources", [])),
                "backfill_start_date": job.get("backfill_start_date", stage4.get("backfill_start_date", "")),
                "chunk_unit": stage4.get("chunk_unit", ""),
                "chunk_size": stage4.get("chunk_size", ""),
                "max_work_per_cycle": stage4.get("max_work_per_cycle", ""),
                "checkpoint_mode": stage4.get("checkpoint_mode", ""),
                "resume_mode": stage4.get("resume_mode", ""),
                "retry_policy": stage4.get("retry_policy", ""),
                "coverage_audit": int(bool(stage4.get("coverage_audit_required", False))),
                "materialization_status": stage4.get("materialization_status", "READY_FOR_OPERATOR_MATERIALIZATION_CHECK"),
                "scheduler_activation_permitted": int(stage4.get("scheduler_activation_permitted", 0) or 0),
                "network_calls_made": 0,
                "db_mutation_made": 0,
                "optimization_status": stage4.get("optimization_status", "MISSING_STAGE4_METADATA"),
            }
        )
    return rows


def blocker_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in rows:
        if row["optimization_status"] != "OPTIMIZED_NOT_ACTIVATED":
            blockers.append(
                {
                    "task_id": TASK_ID,
                    "job_name": row["job_name"],
                    "blocker": "stage4_metadata_not_optimized",
                    "status": row["optimization_status"],
                }
            )
        if "BLOCKED" in str(row["materialization_status"]):
            blockers.append(
                {
                    "task_id": TASK_ID,
                    "job_name": row["job_name"],
                    "blocker": "local_file_materialization",
                    "status": row["materialization_status"],
                }
            )
    return blockers


def coverage_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = job_map(config)
    rows: list[dict[str, Any]] = []
    for name in BACKFILL_JOBS:
        job = jobs.get(name, {})
        stage4 = job.get("stage4_backfill_optimization", {}) if isinstance(job, dict) else {}
        rows.append(
            {
                "task_id": TASK_ID,
                "job_name": name,
                "coverage_artifact_policy": stage4.get("coverage_artifact_policy", ""),
                "raw_ledger_required": 1,
                "checkpoint_required": 1,
                "source_time_required": 1,
                "feature_admission_allowed": 0,
                "l2_handoff_allowed": 0,
            }
        )
    return rows


def run(out_dir: Path) -> dict[str, Any]:
    config = load_scheduler()
    rows = optimization_rows(config)
    blockers = blocker_rows(rows)
    coverage = coverage_rows(config)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "task_4122_backfill_optimization_plan.csv", rows)
    write_csv(out_dir / "task_4122_backfill_blocker_ledger.csv", blockers)
    write_csv(out_dir / "task_4122_backfill_coverage_audit_plan.csv", coverage)
    summary = {
        "task_id": TASK_ID,
        "updated_at": now_z(),
        "stage4_status": "HISTORICAL_BACKFILL_OPTIMIZED_NOT_ACTIVATED" if not [b for b in blockers if b["blocker"] == "stage4_metadata_not_optimized"] else "HISTORICAL_BACKFILL_OPTIMIZATION_INCOMPLETE",
        "backfill_job_count": len(rows),
        "blocker_count": len(blockers),
        "scheduler_activation_permitted": 0,
        "background_collection_started": 0,
        "network_calls_made": 0,
        "db_mutation_made": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_stage": "background_historical_backfill_from_2016",
    }
    (out_dir / "stage4_backfill_optimization_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "[L0_STAGE4_BACKFILL_OPTIMIZATION] "
        f"status={summary['stage4_status']} jobs={summary['backfill_job_count']} "
        f"blockers={summary['blocker_count']} network_calls_made=0 background_collection_started=0"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize L0 Stage 4 historical backfill optimization plan.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    return 0 if summary["stage4_status"] == "HISTORICAL_BACKFILL_OPTIMIZED_NOT_ACTIVATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
