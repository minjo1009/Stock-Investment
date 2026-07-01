from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4165"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGGREGATE = Path("data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json")
DEFAULT_OUT_DIR = Path("data/artifacts/task_4165_l0_newswire_failed_recovery_runtime_cutover")


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=False)
        return result.returncode == 0 and str(pid) in result.stdout and "No tasks are running" not in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def month_window(shard_key: str) -> tuple[str, str]:
    year, month = [int(part) for part in shard_key.split("-", 1)]
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    start = datetime(year, month, 1, tzinfo=timezone.utc).date()
    next_start = datetime(next_year, next_month, 1, tzinfo=timezone.utc).date()
    end = next_start.fromordinal(next_start.toordinal() - 1)
    return start.isoformat(), end.isoformat()


def shard_paths(source: str, shard_key: str) -> dict[str, Path]:
    artifact_dir = Path("data/artifacts/l0_public_newswire_backfill_shards") / source / shard_key
    raw_dir = Path("data/raw/l0_public_newswire_backfill_shards") / source / shard_key
    return {
        "artifact_dir": artifact_dir,
        "raw_dir": raw_dir,
        "state_path": artifact_dir / "collector_state.json",
        "event_path": artifact_dir / "collector_events.jsonl",
        "progress_path": artifact_dir / "collector_progress.json",
        "plan_path": artifact_dir / "collection_plan.json",
        "lock_path": artifact_dir / "worker.lock.json",
        "worker_progress_path": artifact_dir / "worker_progress.json",
    }


def progress_status(source: str, shard_key: str, returncode: int) -> tuple[str, dict[str, Any]]:
    paths = shard_paths(source, shard_key)
    progress = load_json(paths["progress_path"])
    source_state = progress.get("backfill", {}).get(source, {}) if isinstance(progress.get("backfill"), dict) else {}
    offsets = source_state.get("archive_entry_offsets", {}) if isinstance(source_state.get("archive_entry_offsets"), dict) else {}
    completed = len(source_state.get("completed_archive_urls", []) or [])
    total = int(source_state.get("total_archive_urls", 1) or 1)
    last_status = str(progress.get("last_status", ""))
    if total and completed >= total and not offsets:
        status = "COMPLETED" if returncode == 0 else "COMPLETED_WITH_NONZERO_EXIT"
    elif returncode != 0 or last_status == "FAILED_RETRYABLE":
        status = "FAILED_RETRYABLE" if last_status == "FAILED_RETRYABLE" else "FAILED"
    else:
        status = "PARTIAL"
    cycles = progress.get("source_cycles", {}) if isinstance(progress.get("source_cycles"), dict) else {}
    cycle = cycles.get(source, {}) if isinstance(cycles.get(source, {}), dict) else {}
    current_archive_url = sorted(offsets)[0] if offsets else ""
    snapshot = {
        "completed_units": completed,
        "total_units": total,
        "pending_units": max(total - completed, 0),
        "active_archive_offsets": offsets,
        "current_archive_url": current_archive_url,
        "active_archive_offset": int(offsets.get(current_archive_url, 0) or 0) if current_archive_url else 0,
        "row_count": int(cycle.get("rows", 0) or 0),
        "last_status": last_status,
        "last_successful_fetch_at": cycle.get("last_updated_at") or "",
    }
    return status, snapshot


def recover_one(source: str, shard_key: str, args: argparse.Namespace) -> dict[str, Any]:
    paths = shard_paths(source, shard_key)
    lock = load_json(paths["lock_path"])
    if lock.get("status") == "RUNNING" and pid_alive(int(lock.get("pid", 0) or 0)):
        return {
            "task_id": TASK_ID,
            "source": source,
            "shard_key": shard_key,
            "status": "SKIPPED_LIVE_LOCK",
            "returncode": "",
            "log_path": "",
        }
    start_date, end_date = month_window(shard_key)
    max_fetches = args.prnewswire_max_fetches if source == "prnewswire" else args.globenewswire_max_fetches if source == "globenewswire" else args.businesswire_max_fetches
    max_items = args.prnewswire_max_items if source == "prnewswire" else args.globenewswire_max_items if source == "globenewswire" else args.businesswire_max_items
    max_bytes = args.prnewswire_max_bytes if source == "prnewswire" else args.max_bytes
    scope = "monthly" if source == "prnewswire" else "all"
    log_path = Path("logs") / f"l0_public_newswire_recovery_{TASK_ID}_{source}_{shard_key}.log"
    command = [
        sys.executable,
        "tools/db/source_acquisition/public_newswire_collector.py",
        "--mode",
        "backfill",
        "--sources",
        source,
        "--backfill-start-date",
        start_date,
        "--backfill-end-date",
        end_date,
        "--state-path",
        str(paths["state_path"]),
        "--event-path",
        str(paths["event_path"]),
        "--progress-path",
        str(paths["progress_path"]),
        "--plan-path",
        str(paths["plan_path"]),
        "--raw-dir",
        str(paths["raw_dir"]),
        "--stop-path",
        "data/artifacts/l0_public_newswire_backfill_shards/STOP",
        "--log-path",
        str(log_path),
        "--max-fetches-per-source",
        str(max_fetches),
        "--max-items-per-source",
        str(max_items),
        "--max-bytes",
        str(max_bytes),
        "--request-sleep-seconds",
        str(args.request_sleep_seconds),
        "--cycle-sleep-seconds",
        "1",
        "--prnewswire-archive-scope",
        scope,
        "--max-cycles",
        str(args.max_cycles),
        "--exit-when-complete",
    ]
    run_id = f"{TASK_ID}:{source}:{shard_key}:{int(time.time())}"
    atomic_write_json(
        paths["lock_path"],
        {
            "schema_version": "l0_public_newswire_shard_lock_v1",
            "task_id": TASK_ID,
            "run_id": run_id,
            "source": source,
            "shard_key": shard_key,
            "shard_id": f"{source}:{shard_key}",
            "status": "RUNNING",
            "started_at": now_z(),
            "pid": 0,
            "command": command,
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        },
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", errors="replace") as log_handle:
        log_handle.write(f"{now_z()} [TASK4165_RECOVERY_START] {' '.join(command)}\n")
        log_handle.flush()
        proc = subprocess.Popen(command, cwd=ROOT, stdout=log_handle, stderr=log_handle, text=True)
        lock_payload = load_json(paths["lock_path"])
        lock_payload["pid"] = proc.pid
        lock_payload["updated_at"] = now_z()
        atomic_write_json(paths["lock_path"], lock_payload)
        try:
            returncode = proc.wait(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
            returncode = -9
    status, snapshot = progress_status(source, shard_key, returncode)
    finished_at = now_z()
    lock_payload = load_json(paths["lock_path"])
    lock_payload.update({"status": status, "returncode": returncode, "finished_at": finished_at})
    atomic_write_json(paths["lock_path"], lock_payload)
    atomic_write_json(
        paths["worker_progress_path"],
        {
            "schema_version": "l0_public_newswire_sharded_worker_v1",
            "task_id": TASK_ID,
            "run_id": run_id,
            "source": source,
            "shard_key": shard_key,
            "shard_id": f"{source}:{shard_key}",
            "status": status,
            "pid": proc.pid,
            "worker_pid": proc.pid,
            "returncode": returncode,
            "last_progress_at": finished_at,
            "last_successful_fetch_at": snapshot.get("last_successful_fetch_at", ""),
            "current_archive_url": snapshot.get("current_archive_url", ""),
            "active_archive_offset": snapshot.get("active_archive_offset", 0),
            "processed_item_count": snapshot.get("row_count", 0),
            "estimated_total_item_count": None,
            "row_count": snapshot.get("row_count", 0),
            "raw_bytes": paths["event_path"].stat().st_size if paths["event_path"].exists() else 0,
            "limit_hit_reason": "" if returncode == 0 else "RECOVERY_RETURNED_NONZERO",
            "last_error_type": "",
            "last_error_message": "",
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
            "updated_at": finished_at,
        },
    )
    return {
        "task_id": TASK_ID,
        "source": source,
        "shard_key": shard_key,
        "status": status,
        "returncode": str(returncode),
        "completed_units": str(snapshot.get("completed_units", 0)),
        "pending_units": str(snapshot.get("pending_units", 0)),
        "active_archive_offset": str(snapshot.get("active_archive_offset", 0)),
        "row_count": str(snapshot.get("row_count", 0)),
        "log_path": str(log_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover represented failed L0 public newswire shards.")
    parser.add_argument("--aggregate-path", type=Path, default=DEFAULT_AGGREGATE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--only", action="append", default=[], help="Optional shard id like globenewswire:2024-11")
    parser.add_argument("--max-shards", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--max-cycles", type=int, default=3)
    parser.add_argument("--request-sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-bytes", type=int, default=25_000_000)
    parser.add_argument("--prnewswire-max-bytes", type=int, default=50_000_000)
    parser.add_argument("--globenewswire-max-fetches", type=int, default=800)
    parser.add_argument("--globenewswire-max-items", type=int, default=10000)
    parser.add_argument("--prnewswire-max-fetches", type=int, default=1200)
    parser.add_argument("--prnewswire-max-items", type=int, default=20000)
    parser.add_argument("--businesswire-max-fetches", type=int, default=240)
    parser.add_argument("--businesswire-max-items", type=int, default=1000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    aggregate = load_json(args.aggregate_path)
    shard_ids = list(args.only) if args.only else [str(item) for item in aggregate.get("failed_shards", [])]
    if args.max_shards > 0:
        shard_ids = shard_ids[: args.max_shards]
    rows: list[dict[str, Any]] = []
    for shard_id in shard_ids:
        if ":" not in shard_id:
            continue
        source, shard_key = shard_id.split(":", 1)
        if source not in {"businesswire", "globenewswire", "prnewswire"} or shard_key == "recent":
            continue
        rows.append(recover_one(source, shard_key, args))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = args.out_dir / "failed_shard_recovery_ledger.csv"
    fieldnames = ["task_id", "source", "shard_key", "status", "returncode", "completed_units", "pending_units", "active_archive_offset", "row_count", "log_path"]
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    atomic_write_json(
        args.out_dir / "failed_shard_recovery_summary.json",
        {
            "task_id": TASK_ID,
            "generated_at": now_z(),
            "ledger_path": str(ledger_path),
            "attempted_shards": len(rows),
            "status_counts": {status: sum(1 for row in rows if row.get("status") == status) for status in sorted({str(row.get("status", "")) for row in rows})},
            "rows": rows,
            "safety": {
                "broker_mutation_count": 0,
                "live_order_count": 0,
                "paper_promotion_count": 0,
                "real_capital_flag_count": 0,
            },
        },
    )
    print(json.dumps({"attempted_shards": len(rows), "out": str(ledger_path)}, indent=2, sort_keys=True))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
