from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.db.source_acquisition.public_newswire_shards import (
    DEFAULT_SHARD_ARTIFACT_ROOT,
    DEFAULT_SHARD_RAW_ROOT,
    atomic_write_json,
    build_inventory,
    load_json,
    now_z,
    seed_shard_state,
)


DEFAULT_LEGACY_STATE = Path("data/artifacts/l0_public_newswire_backfill/collector_state.json")
DEFAULT_LEGACY_PROGRESS = Path("data/artifacts/l0_public_newswire_backfill/collector_progress.json")


MODE_DEFAULTS = {
    "smoke": {"max_fetches_per_source": 12, "max_items_per_source": 50, "request_sleep_seconds": 1.0},
    "stable": {"max_fetches_per_source": 400, "max_items_per_source": 200, "request_sleep_seconds": 1.0},
    "aggressive": {"max_fetches_per_source": 400, "max_items_per_source": 200, "request_sleep_seconds": 0.5},
}


def parse_sources(value: str) -> list[str]:
    allowed = {"businesswire", "globenewswire", "prnewswire"}
    sources = [item.strip() for item in value.split(",") if item.strip()]
    unknown = sorted(set(sources) - allowed)
    if unknown:
        raise ValueError(f"unknown sources: {unknown}")
    return sources


def parse_source_ints(value: str, sources: list[str], *, field_name: str) -> dict[str, int]:
    if not value.strip():
        return {}
    values: dict[str, int] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"{field_name} must be SOURCE=COUNT: {item}")
        source, count = item.split("=", 1)
        source = source.strip()
        if source not in sources:
            raise ValueError(f"{field_name} references disabled source: {source}")
        values[source] = max(0, int(count.strip()))
    return values


def parse_source_floats(value: str, sources: list[str], *, field_name: str) -> dict[str, float]:
    if not value.strip():
        return {}
    values: dict[str, float] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"{field_name} must be SOURCE=VALUE: {item}")
        source, count = item.split("=", 1)
        source = source.strip()
        if source not in sources:
            raise ValueError(f"{field_name} references disabled source: {source}")
        values[source] = max(0.0, float(count.strip()))
    return values


def parse_source_lanes(value: str, sources: list[str], concurrency: int) -> dict[str, int]:
    lanes = parse_source_ints(value, sources, field_name="source lane")
    if sum(lanes.values()) > concurrency:
        raise ValueError(f"source lanes exceed concurrency: lanes={lanes} concurrency={concurrency}")
    return lanes


def default_source_base_lanes(sources: list[str]) -> dict[str, int]:
    defaults = {"businesswire": 2, "globenewswire": 1, "prnewswire": 1}
    return {source: defaults.get(source, 1) for source in sources}


def default_source_lane_caps(sources: list[str]) -> dict[str, int]:
    defaults = {"businesswire": 4, "globenewswire": 1, "prnewswire": 1}
    return {source: defaults.get(source, 1) for source in sources}


def source_int(value_by_source: dict[str, int], source: str, fallback: int) -> int:
    return int(value_by_source.get(source, fallback) or fallback)


def source_float(value_by_source: dict[str, float], source: str, fallback: float) -> float:
    return float(value_by_source.get(source, fallback))


def lock_path_for(shard: dict[str, Any]) -> Path:
    return Path(shard["artifact_dir"]) / "worker.lock.json"


def progress_path_for(shard: dict[str, Any]) -> Path:
    return Path(shard["artifact_dir"]) / "worker_progress.json"


def write_worker_progress(path: Path, payload: dict[str, Any]) -> None:
    base = {
        "schema_version": "l0_public_newswire_sharded_worker_v1",
        "updated_at": now_z(),
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    base.update(payload)
    atomic_write_json(path, base)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and str(pid) in result.stdout and "No tasks are running" not in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def create_lock(shard: dict[str, Any], command: list[str]) -> Path:
    path = lock_path_for(shard)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = load_json(path)
        if existing.get("status") == "RUNNING":
            pid = int(existing.get("pid", 0) or 0)
            if pid_alive(pid):
                raise RuntimeError(f"shard already locked: {shard['shard_id']}")
            existing["status"] = "STALE_DEAD_PID_RECOVERED"
            existing["returncode"] = -9
            existing["finished_at"] = now_z()
            existing["stale_recovery_reason"] = "dead_pid_before_launch"
            atomic_write_json(path, existing)
    atomic_write_json(
        path,
        {
            "schema_version": "l0_public_newswire_shard_lock_v1",
            "shard_id": shard["shard_id"],
            "source": shard["source"],
            "shard_key": shard["shard_key"],
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
    return path


def live_running_lock(shard: dict[str, Any]) -> dict[str, Any] | None:
    path = lock_path_for(shard)
    lock = load_json(path)
    if lock.get("status") != "RUNNING":
        return None
    pid = int(lock.get("pid", 0) or 0)
    if pid_alive(pid):
        return {"path": str(path), "pid": pid, "shard_id": shard["shard_id"]}
    return None


def recover_dead_running_locks(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    recovered: list[dict[str, Any]] = []
    for shard in inventory.get("shards", []):
        lock_path = lock_path_for(shard)
        lock = load_json(lock_path)
        if lock.get("status") != "RUNNING":
            continue
        pid = int(lock.get("pid", 0) or 0)
        if pid_alive(pid):
            continue
        lock["status"] = "STALE_DEAD_PID_RECOVERED"
        lock["returncode"] = -9
        lock["finished_at"] = now_z()
        lock["stale_recovery_reason"] = "dead_pid_before_launcher_loop"
        atomic_write_json(lock_path, lock)
        write_worker_progress(
            progress_path_for(shard),
            worker_progress_payload(
                shard,
                status="STALE_DEAD_PID_RECOVERED",
                pid=pid,
                limit_hit_reason="STALE_DEAD_PID_RECOVERED",
            ),
        )
        recovered.append({"shard_id": shard["shard_id"], "pid": pid})
    return recovered


def update_lock_pid(path: Path, pid: int) -> None:
    payload = load_json(path)
    payload["pid"] = pid
    payload["updated_at"] = now_z()
    atomic_write_json(path, payload)


def finish_lock(path: Path, status: str, returncode: int) -> None:
    payload = load_json(path)
    payload["status"] = status
    payload["returncode"] = returncode
    payload["finished_at"] = now_z()
    atomic_write_json(path, payload)


def worker_activity_time(shard: dict[str, Any], lock_path: Path) -> float:
    paths = [
        lock_path,
        Path(shard.get("progress_path", "")),
        Path(shard.get("event_path", "")),
        progress_path_for(shard),
        Path(shard.get("log_path", "")),
    ]
    newest = 0.0
    for path in paths:
        if path.exists():
            newest = max(newest, path.stat().st_mtime)
    return newest


def progress_snapshot(shard: dict[str, Any]) -> dict[str, Any]:
    progress = load_json(Path(shard.get("progress_path", "")))
    state = load_json(Path(shard.get("state_path", "")))
    source = shard.get("source", "")
    backfill = state.get("backfill", {}).get(source, {}) if isinstance(state.get("backfill"), dict) else {}
    progress_backfill = progress.get("backfill", {}).get(source, {}) if isinstance(progress.get("backfill"), dict) else {}
    if progress_backfill:
        backfill = {**backfill, **progress_backfill}
    offsets = backfill.get("archive_entry_offsets", {}) or {}
    cycles = progress.get("source_cycles", {}) if isinstance(progress.get("source_cycles"), dict) else {}
    cycle = cycles.get(source, {}) if isinstance(cycles.get(source, {}), dict) else {}
    current_archive_url = sorted(offsets)[0] if offsets else ""
    active_offset = int(offsets.get(current_archive_url, 0) or 0) if current_archive_url else 0
    event_path = Path(str(shard.get("event_path", "")))
    log_path = Path(str(shard.get("log_path", "")))
    event_size = event_path.stat().st_size if event_path.exists() else 0
    raw_bytes = event_size
    completed_units = len(backfill.get("completed_archive_urls", []) or [])
    processed_item_count = int(progress.get("processed_this_run", 0) or 0)
    row_count = int(cycle.get("rows", 0) or 0)
    newest_activity = worker_activity_time(shard, lock_path_for(shard))
    return {
        "completed_units": completed_units,
        "active_archive_offsets_count": len(offsets),
        "active_archive_offset_total": sum(int(value or 0) for value in offsets.values()),
        "current_archive_url": current_archive_url,
        "active_archive_offset": active_offset,
        "processed_item_count": processed_item_count,
        "estimated_total_item_count": None,
        "row_count": row_count,
        "raw_bytes": raw_bytes,
        "last_successful_fetch_at": cycle.get("last_updated_at") or "",
        "last_status": progress.get("last_status") or cycle.get("last_status") or "",
        "event_size": event_size,
        "event_mtime": event_path.stat().st_mtime if event_path.exists() else 0.0,
        "log_mtime": log_path.stat().st_mtime if log_path.exists() else 0.0,
        "newest_activity_mtime": newest_activity,
    }


def progress_signature(snapshot: dict[str, Any]) -> str:
    keys = [
        "completed_units",
        "active_archive_offsets_count",
        "active_archive_offset_total",
        "processed_item_count",
        "row_count",
        "raw_bytes",
        "last_successful_fetch_at",
        "event_size",
        "event_mtime",
        "log_mtime",
    ]
    return json.dumps({key: snapshot.get(key) for key in keys}, sort_keys=True)


def worker_progress_payload(
    shard: dict[str, Any],
    *,
    status: str,
    pid: int = 0,
    run_id: str = "",
    snapshot: dict[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    snapshot = snapshot or progress_snapshot(shard)
    payload = {
        "shard_id": shard["shard_id"],
        "source": shard["source"],
        "shard_key": shard["shard_key"],
        "worker_pid": pid,
        "pid": pid,
        "run_id": run_id,
        "status": status,
        "last_progress_at": now_z(),
        "last_successful_fetch_at": snapshot.get("last_successful_fetch_at") or "",
        "current_archive_url": snapshot.get("current_archive_url") or "",
        "active_archive_offset": int(snapshot.get("active_archive_offset", 0) or 0),
        "processed_item_count": int(snapshot.get("processed_item_count", 0) or 0),
        "estimated_total_item_count": snapshot.get("estimated_total_item_count"),
        "row_count": int(snapshot.get("row_count", 0) or 0),
        "raw_bytes": int(snapshot.get("raw_bytes", 0) or 0),
        "limit_hit_reason": None,
        "last_error_type": None,
        "last_error_message": None,
    }
    payload.update(extra)
    return payload


def stop_process(process: subprocess.Popen[str], *, graceful_seconds: int = 10) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=graceful_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=graceful_seconds)


def completed_status_for(shard: dict[str, Any], returncode: int) -> str:
    progress = load_json(Path(shard.get("progress_path", "")))
    if str(progress.get("last_status", "")) == "FAILED_RETRYABLE":
        return "FAILED_RETRYABLE"
    source = shard.get("source", "")
    source_state = progress.get("backfill", {}).get(source, {}) if isinstance(progress.get("backfill"), dict) else {}
    completed = len(source_state.get("completed_archive_urls", []) or [])
    total = int(shard.get("total_units", 0) or 0)
    offsets = source_state.get("archive_entry_offsets", {}) or {}
    if total and completed >= total and not offsets:
        return "COMPLETED" if returncode == 0 else "COMPLETED_WITH_NONZERO_EXIT"
    if returncode != 0:
        return "FAILED"
    return "PARTIAL"


def shard_command(shard: dict[str, Any], args: argparse.Namespace) -> list[str]:
    mode_defaults = MODE_DEFAULTS[args.mode]
    source = shard["source"]
    scope = "all"
    if source == "prnewswire":
        scope = "recent" if shard["shard_key"] == "recent" else "monthly"
    max_fetches = source_int(
        args.source_max_fetches,
        source,
        args.max_fetches_per_source or mode_defaults["max_fetches_per_source"],
    )
    max_items = source_int(
        args.source_max_items,
        source,
        args.max_items_per_source or mode_defaults["max_items_per_source"],
    )
    sleep_seconds = source_float(
        args.source_request_sleep_seconds,
        source,
        args.request_sleep_seconds if args.request_sleep_seconds is not None else mode_defaults["request_sleep_seconds"],
    )
    max_bytes = source_int(args.source_max_bytes, source, args.max_bytes)
    command = [
        sys.executable,
        "tools/db/source_acquisition/public_newswire_collector.py",
        "--mode",
        "backfill",
        "--sources",
        source,
        "--backfill-start-date",
        shard["start_date"],
        "--backfill-end-date",
        shard["end_date"],
        "--state-path",
        shard["state_path"],
        "--event-path",
        shard["event_path"],
        "--progress-path",
        shard["progress_path"],
        "--plan-path",
        shard["plan_path"],
        "--raw-dir",
        shard["raw_dir"],
        "--stop-path",
        shard["stop_path"],
        "--log-path",
        shard["log_path"],
        "--max-fetches-per-source",
        str(max_fetches),
        "--max-items-per-source",
        str(max_items),
        "--request-sleep-seconds",
        str(sleep_seconds),
        "--max-bytes",
        str(max_bytes),
        "--cycle-sleep-seconds",
        str(args.cycle_sleep_seconds),
        "--prnewswire-archive-scope",
        scope,
        "--exit-when-complete",
    ]
    if args.worker_max_cycles > 0:
        command.extend(["--max-cycles", str(args.worker_max_cycles)])
    return command


def source_round_robin(shards: list[dict[str, Any]], source_order: list[str]) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = {source: [] for source in source_order}
    for shard in shards:
        by_source.setdefault(shard["source"], []).append(shard)
    ordered: list[dict[str, Any]] = []
    while any(by_source.values()):
        for source in source_order:
            if by_source.get(source):
                ordered.append(by_source[source].pop(0))
    return ordered


def runnable_shards(
    inventory: dict[str, Any],
    *,
    max_shards: int,
    schedule_strategy: str,
    source_order: list[str],
) -> list[dict[str, Any]]:
    pending = [shard for shard in inventory["shards"] if int(shard.get("pending_units", 0)) > 0]
    if schedule_strategy == "source_round_robin":
        pending = source_round_robin(pending, source_order)
    return pending[:max_shards] if max_shards > 0 else pending


def running_source_counts(running: list[tuple[dict[str, Any], subprocess.Popen[str], Path, int, float, str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for shard, process, _lock_path, _retries, _last_progress_ts, _last_signature, _run_id in running:
        if process.poll() is None:
            counts[shard["source"]] = counts.get(shard["source"], 0) + 1
    return counts


def effective_source_lanes(
    queue: list[tuple[dict[str, Any], int]],
    *,
    running: list[tuple[dict[str, Any], subprocess.Popen[str], Path, int, float, str, str]],
    sources: list[str],
    source_base_lanes: dict[str, int],
    source_lane_caps: dict[str, int],
    concurrency: int,
    rebalance_priority: list[str],
) -> dict[str, int]:
    active_sources = {shard["source"] for shard, _retries in queue}
    active_sources.update(shard["source"] for shard, process, _lock, _retries, _last_ts, _sig, _run_id in running if process.poll() is None)
    lanes: dict[str, int] = {}
    remaining = max(int(concurrency), 0)
    for source in sources:
        if source not in active_sources or remaining <= 0:
            continue
        cap = max(int(source_lane_caps.get(source, concurrency) or 0), 0)
        base = min(max(int(source_base_lanes.get(source, 0) or 0), 0), cap)
        assigned = min(base, remaining)
        if assigned:
            lanes[source] = assigned
            remaining -= assigned
    for source in rebalance_priority:
        if source not in active_sources or remaining <= 0:
            continue
        cap = max(int(source_lane_caps.get(source, concurrency) or 0), 0)
        current = lanes.get(source, 0)
        extra = min(max(cap - current, 0), remaining)
        if extra:
            lanes[source] = current + extra
            remaining -= extra
    return lanes


def pop_next_runnable(
    queue: list[tuple[dict[str, Any], int]],
    *,
    running: list[tuple[dict[str, Any], subprocess.Popen[str], Path, int, float, str, str]],
    source_lanes: dict[str, int],
) -> tuple[dict[str, Any], int] | None:
    if not source_lanes:
        return queue.pop(0) if queue else None
    counts = running_source_counts(running)
    for idx, (shard, retries) in enumerate(queue):
        source = shard["source"]
        lane = source_lanes.get(source)
        if lane is None or counts.get(source, 0) < lane:
            return queue.pop(idx)
    return None


def write_inventory(path: Path, inventory: dict[str, Any]) -> None:
    atomic_write_json(path, inventory)


def run(args: argparse.Namespace) -> int:
    artifact_root = args.shard_artifact_root
    raw_root = args.shard_raw_root
    sources = parse_sources(args.sources)
    legacy_source_lanes = parse_source_lanes(args.source_lanes, sources, args.concurrency)
    source_base_lanes = (
        parse_source_ints(args.source_base_lanes, sources, field_name="source base lanes")
        or legacy_source_lanes
        or default_source_base_lanes(sources)
    )
    source_lane_caps = (
        parse_source_ints(args.source_lane_caps, sources, field_name="source lane caps")
        or legacy_source_lanes
        or default_source_lane_caps(sources)
    )
    source_max_fetches = parse_source_ints(args.source_max_fetches, sources, field_name="source max fetches")
    source_max_items = parse_source_ints(args.source_max_items, sources, field_name="source max items")
    source_max_bytes = parse_source_ints(args.source_max_bytes, sources, field_name="source max bytes")
    source_request_sleep_seconds = parse_source_floats(args.source_request_sleep_seconds, sources, field_name="source request sleep seconds")
    source_max_worker_seconds = parse_source_ints(args.source_max_worker_seconds, sources, field_name="source max worker seconds")
    source_stale_progress_seconds = parse_source_ints(args.source_stale_progress_seconds, sources, field_name="source stale progress seconds")
    args.source_max_fetches = source_max_fetches
    args.source_max_items = source_max_items
    args.source_max_bytes = source_max_bytes
    args.source_request_sleep_seconds = source_request_sleep_seconds
    legacy_state = load_json(args.legacy_state_path)
    inventory = build_inventory(
        start_month=args.start_month,
        end_month=args.end_month,
        sources=sources,
        artifact_root=artifact_root,
        raw_root=raw_root,
        legacy_state=legacy_state,
        businesswire_shard_granularity=args.businesswire_shard_granularity,
    )
    inventory_path = artifact_root / "shard_inventory.json"
    write_inventory(inventory_path, inventory)
    recovered_dead_locks: list[dict[str, Any]] = []
    if not args.dry_run:
        recovered_dead_locks = recover_dead_running_locks(inventory)
    shards = runnable_shards(
        inventory,
        max_shards=args.max_shards,
        schedule_strategy=args.schedule_strategy,
        source_order=sources,
    )
    summary = {
        "inventory_path": str(inventory_path),
        "total_units": inventory["total_units"],
        "legacy_completed_units": inventory["legacy_completed_units"],
        "pending_units": inventory["pending_units"],
        "scheduled_shards": len(shards),
        "schedule_strategy": args.schedule_strategy,
        "source_base_lanes": source_base_lanes,
        "source_lane_caps": source_lane_caps,
        "source_max_fetches": source_max_fetches,
        "source_max_items": source_max_items,
        "source_max_bytes": source_max_bytes,
        "source_request_sleep_seconds": source_request_sleep_seconds,
        "source_max_worker_seconds": source_max_worker_seconds,
        "source_stale_progress_seconds": source_stale_progress_seconds,
        "businesswire_shard_granularity": args.businesswire_shard_granularity,
        "recovered_dead_locks": recovered_dead_locks,
        "max_worker_seconds": args.max_worker_seconds,
        "stale_progress_seconds": args.stale_progress_seconds,
        "dry_run": bool(args.dry_run),
    }
    if args.dry_run:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.stop_file.exists():
        print(json.dumps({**summary, "status": "STOP_PRESENT_NO_SPAWN"}, indent=2, sort_keys=True))
        return 0

    running: list[tuple[dict[str, Any], subprocess.Popen[str], Path, int, float, str, str]] = []
    completed = 0
    failed = 0
    recycled = 0
    skipped_live_locks = 0
    queue: list[tuple[dict[str, Any], int]] = [(shard, 0) for shard in shards]
    while queue or running:
        while queue and len(running) < args.concurrency and not args.stop_file.exists():
            source_lanes = effective_source_lanes(
                queue,
                running=running,
                sources=sources,
                source_base_lanes=source_base_lanes,
                source_lane_caps=source_lane_caps,
                concurrency=args.concurrency,
                rebalance_priority=parse_sources(args.rebalance_priority),
            )
            item = pop_next_runnable(queue, running=running, source_lanes=source_lanes)
            if item is None:
                break
            shard, retries = item
            existing_live_lock = live_running_lock(shard)
            if existing_live_lock:
                skipped_live_locks += 1
                write_worker_progress(
                    progress_path_for(shard),
                    worker_progress_payload(
                        shard,
                        status="RUNNING_EXISTING_WORKER_SKIPPED",
                        pid=int(existing_live_lock["pid"]),
                        limit_hit_reason="LIVE_LOCK_ALREADY_RUNNING",
                        retry_count=retries,
                    ),
                )
                continue
            seed_shard_state(shard)
            command = shard_command(shard, args)
            lock_path = create_lock(shard, command)
            progress_path = progress_path_for(shard)
            run_id = f"{shard['shard_id']}:{int(time.time())}:{retries}"
            write_worker_progress(progress_path, worker_progress_payload(shard, status="STARTING", run_id=run_id, retry_count=retries))
            log_path = Path(str(shard.get("log_path", "")))
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8", errors="replace") as log_handle:
                log_handle.write(f"{now_z()} [L0_PUBLIC_NEWSWIRE_SHARD_COMMAND] {' '.join(command)}\n")
                log_handle.flush()
                process = subprocess.Popen(command, cwd=ROOT, stdout=log_handle, stderr=log_handle, text=True)
            update_lock_pid(lock_path, process.pid)
            snapshot = progress_snapshot(shard)
            write_worker_progress(progress_path, worker_progress_payload(shard, status="RUNNING", pid=process.pid, run_id=run_id, snapshot=snapshot, retry_count=retries, effective_source_lanes=source_lanes))
            running.append((shard, process, lock_path, retries, time.time(), progress_signature(snapshot), run_id))
        still_running: list[tuple[dict[str, Any], subprocess.Popen[str], Path, int, float, str, str]] = []
        now = time.time()
        for shard, process, lock_path, retries, last_progress_ts, last_signature, run_id in running:
            code = process.poll()
            if code is None:
                started_at = load_json(lock_path).get("started_at")
                runtime_seconds = 0.0
                if isinstance(started_at, str):
                    try:
                        runtime_seconds = now - datetime.fromisoformat(started_at.replace("Z", "+00:00")).timestamp()
                    except ValueError:
                        runtime_seconds = 0.0
                snapshot = progress_snapshot(shard)
                signature = progress_signature(snapshot)
                if signature != last_signature:
                    last_progress_ts = now
                    last_signature = signature
                    write_worker_progress(
                        progress_path_for(shard),
                        worker_progress_payload(
                            shard,
                            status="RUNNING",
                            pid=process.pid,
                            run_id=run_id,
                            snapshot=snapshot,
                            retry_count=retries,
                            runtime_seconds=round(runtime_seconds, 3),
                        ),
                    )
                idle_seconds = now - last_progress_ts
                max_worker_seconds = source_int(source_max_worker_seconds, shard["source"], args.max_worker_seconds)
                stale_progress_seconds = source_int(source_stale_progress_seconds, shard["source"], args.stale_progress_seconds)
                timed_out = max_worker_seconds > 0 and runtime_seconds >= max_worker_seconds
                stale = stale_progress_seconds > 0 and idle_seconds >= stale_progress_seconds
                if timed_out and not stale and stale_progress_seconds > 0:
                    write_worker_progress(
                        progress_path_for(shard),
                        worker_progress_payload(
                            shard,
                            status="RUNNING_MAX_RUNTIME_EXTENDED_PROGRESS_ACTIVE",
                            pid=process.pid,
                            run_id=run_id,
                            snapshot=snapshot,
                            runtime_seconds=round(runtime_seconds, 3),
                            idle_seconds=round(idle_seconds, 3),
                            retry_count=retries,
                            limit_hit_reason="MAX_RUNTIME_EXTENDED_PROGRESS_ACTIVE",
                        ),
                    )
                    still_running.append((shard, process, lock_path, retries, last_progress_ts, last_signature, run_id))
                    continue
                if timed_out or stale:
                    stop_process(process)
                    recycled += 1
                    reason = "STALE_PROGRESS_RECYCLED" if stale else "MAX_WORKER_SECONDS_RECYCLED"
                    finish_lock(lock_path, reason, -9)
                    write_worker_progress(
                        progress_path_for(shard),
                        worker_progress_payload(
                            shard,
                            status=reason,
                            pid=process.pid,
                            run_id=run_id,
                            snapshot=snapshot,
                            runtime_seconds=round(runtime_seconds, 3),
                            idle_seconds=round(idle_seconds, 3),
                            retry_count=retries,
                            limit_hit_reason=reason,
                        ),
                    )
                    if retries < args.max_recycles_per_shard and not args.stop_file.exists():
                        queue.append((shard, retries + 1))
                    else:
                        failed += 1
                    continue
                still_running.append((shard, process, lock_path, retries, last_progress_ts, last_signature, run_id))
                continue
            status = completed_status_for(shard, code)
            completed += int(status == "COMPLETED")
            failed += int(code != 0)
            finish_lock(lock_path, status, code)
            write_worker_progress(progress_path_for(shard), worker_progress_payload(shard, status=status, pid=process.pid, run_id=run_id, returncode=code))
        running = still_running
        if args.stop_file.exists() and not running:
            break
        time.sleep(max(args.poll_seconds, 1))
    result = {
        **summary,
        "status": "FINISHED",
        "completed_shards": completed,
        "failed_shards": failed,
        "recycled_shards": recycled,
        "skipped_live_locks": skipped_live_locks,
        "remaining_queue": len(queue),
    }
    atomic_write_json(artifact_root / "launcher_result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if failed == 0 else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run L0 public newswire sharded backfill workers.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default=None)
    parser.add_argument("--sources", default="businesswire,globenewswire,prnewswire")
    parser.add_argument("--mode", choices=["smoke", "stable", "aggressive"], default="smoke")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--schedule-strategy", choices=["inventory", "source_round_robin"], default="source_round_robin")
    parser.add_argument("--source-lanes", default="")
    parser.add_argument("--source-base-lanes", default="")
    parser.add_argument("--source-lane-caps", default="")
    parser.add_argument("--rebalance-priority", default="businesswire,prnewswire,globenewswire")
    parser.add_argument("--businesswire-shard-granularity", choices=["month", "day"], default="month")
    parser.add_argument("--max-shards", type=int, default=0)
    parser.add_argument("--max-fetches-per-source", type=int, default=0)
    parser.add_argument("--max-items-per-source", type=int, default=0)
    parser.add_argument("--request-sleep-seconds", type=float, default=None)
    parser.add_argument("--source-max-fetches", default="")
    parser.add_argument("--source-max-items", default="")
    parser.add_argument("--max-bytes", type=int, default=25_000_000)
    parser.add_argument("--source-max-bytes", default="")
    parser.add_argument("--source-request-sleep-seconds", default="")
    parser.add_argument("--source-max-worker-seconds", default="")
    parser.add_argument("--source-stale-progress-seconds", default="")
    parser.add_argument("--cycle-sleep-seconds", type=int, default=1)
    parser.add_argument("--worker-max-cycles", type=int, default=0)
    parser.add_argument("--max-worker-seconds", type=int, default=0)
    parser.add_argument("--stale-progress-seconds", type=int, default=0)
    parser.add_argument("--max-recycles-per-shard", type=int, default=2)
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--legacy-state-path", type=Path, default=DEFAULT_LEGACY_STATE)
    parser.add_argument("--legacy-progress-path", type=Path, default=DEFAULT_LEGACY_PROGRESS)
    parser.add_argument("--shard-artifact-root", type=Path, default=DEFAULT_SHARD_ARTIFACT_ROOT)
    parser.add_argument("--shard-raw-root", type=Path, default=DEFAULT_SHARD_RAW_ROOT)
    parser.add_argument("--stop-file", type=Path, default=DEFAULT_SHARD_ARTIFACT_ROOT / "STOP")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
