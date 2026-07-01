from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = os.environ.get("L0_BACKFILL_GUARD_TASK_ID", "TASK-4193")
SLUG = os.environ.get("L0_BACKFILL_GUARD_SLUG", "task_4193_l0_overnight_backfill_completion_run")
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
RUNTIME_LOG_DIR = ARTIFACT_DIR / "runtime_logs"
STATUS_PATH = ARTIFACT_DIR / "supervisor_status.json"
EVENT_PATH = ARTIFACT_DIR / "supervisor_events.jsonl"
SNAPSHOT_DIR = ARTIFACT_DIR / "progress_snapshots"
BACKGROUND_PROCESS_PATH = ARTIFACT_DIR / "background_process.json"

NEWSWIRE_AGGREGATE_PATH = ROOT / "data" / "artifacts" / "l0_public_newswire_backfill_shards" / "aggregate_progress.json"
NEWSWIRE_BACKGROUND_PATH = ROOT / "data" / "artifacts" / "l0_public_newswire_backfill_shards" / "background_process.json"
NEWSWIRE_STOP_PATH = ROOT / "data" / "artifacts" / "l0_public_newswire_backfill_shards" / "STOP"

MARKET_BACKGROUND_PATH = ROOT / "data" / "artifacts" / "l0_public_market_macro_news_backfill" / "background_process.json"
MARKET_PROGRESS_PATH = ROOT / "data" / "artifacts" / "l0_public_market_macro_news_backfill" / "collector_progress.json"
MARKET_STOP_PATH = ROOT / "data" / "artifacts" / "l0_public_market_macro_news_backfill" / "STOP"

DAILY_PROGRESS_PATH = ROOT / "data" / "artifacts" / "l0_bar_daily_full_backfill" / "collector_progress.json"
FIVE_MIN_BACKGROUND_PATH = ROOT / "data" / "artifacts" / "l0_bar_full_backfill" / "background_process_5m.json"
FIVE_MIN_STATE_PATH = ROOT / "data" / "artifacts" / "l0_bar_full_backfill" / "collector_state.json"
FIVE_MIN_PROGRESS_PATH = ROOT / "data" / "artifacts" / "l0_bar_full_backfill" / "collector_progress.json"
FIVE_MIN_EVENT_PATH = ROOT / "data" / "artifacts" / "l0_bar_full_backfill" / "collector_events.jsonl"
FIVE_MIN_STOP_PATH = ROOT / "data" / "artifacts" / "l0_bar_full_backfill" / "STOP"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        try:
            cleaned = path.read_bytes().replace(b"\x00", b"")
            if not cleaned.strip():
                return default
            return json.loads(cleaned.decode("utf-8-sig", errors="replace"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    tmp.replace(path)


def append_event(event_type: str, payload: dict[str, Any]) -> None:
    EVENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": utc_now(), "event_type": event_type, **payload}
    with EVENT_PATH.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def elapsed_seconds_since(value: Any) -> int:
    if not value:
        return 0
    try:
        then = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return 0
    return max(0, int((datetime.now(timezone.utc) - then).total_seconds()))


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"$p=Get-Process -Id {pid} -ErrorAction SilentlyContinue; if ($p) {{ '1' }} else {{ '0' }}",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    return result.stdout.strip().endswith("1")


def terminate_pid(pid: int, *, reason: str) -> dict[str, Any]:
    if pid <= 0:
        return {"pid": pid, "terminated": 0, "reason": reason, "status": "NO_PID"}
    if not pid_alive(pid):
        return {"pid": pid, "terminated": 0, "reason": reason, "status": "NOT_RUNNING"}
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue",
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    payload = {
        "pid": pid,
        "terminated": int(result.returncode == 0),
        "reason": reason,
        "status": "TERMINATED" if result.returncode == 0 else "TERMINATE_FAILED",
        "stderr_tail": result.stderr[-500:],
    }
    append_event("PID_TERMINATION", payload)
    return payload


def commandline_contains(pid: int, expected: str) -> bool:
    if pid <= 0:
        return False
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                f"$p=Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\";"
                "if ($p) { $p.CommandLine }"
            ),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    return expected.lower() in result.stdout.lower()


def remove_stop_file(path: Path) -> None:
    if path.exists():
        path.unlink()
        append_event("STOP_FILE_REMOVED", {"path": rel(path)})


def current_newswire_launcher_config_is_current() -> bool:
    bg = read_json(NEWSWIRE_BACKGROUND_PATH, {})
    if not isinstance(bg, dict):
        return False
    return (
        bg.get("businesswire_shard_granularity") == "day"
        and bg.get("source_max_worker_seconds") == "businesswire=14400,prnewswire=21600"
        and bg.get("source_stale_progress_seconds") == "businesswire=1200,prnewswire=1800"
    )


def restart_newswire_for_current_config() -> dict[str, Any]:
    bg = read_json(NEWSWIRE_BACKGROUND_PATH, {})
    agg = read_json(NEWSWIRE_AGGREGATE_PATH, {})
    NEWSWIRE_STOP_PATH.parent.mkdir(parents=True, exist_ok=True)
    NEWSWIRE_STOP_PATH.write_text("TASK-4200 current config restart\n", encoding="utf-8")
    terminated: list[dict[str, Any]] = []
    if isinstance(bg, dict):
        terminated.append(terminate_pid(as_int(bg.get("pid")), reason="TASK_4200_CURRENT_CONFIG_RESTART_LAUNCHER"))
    if isinstance(agg, dict):
        for worker in agg.get("active_workers", []) or []:
            if isinstance(worker, dict):
                terminated.append(terminate_pid(as_int(worker.get("pid") or worker.get("worker_pid")), reason="TASK_4200_CURRENT_CONFIG_RESTART_WORKER"))
                source = str(worker.get("source") or "")
                shard_key = str(worker.get("shard_key") or "")
                if source and shard_key:
                    artifact_dir = NEWSWIRE_AGGREGATE_PATH.parent / source / shard_key
                    lock_path = artifact_dir / "worker.lock.json"
                    progress_path = artifact_dir / "worker_progress.json"
                    lock = read_json(lock_path, {})
                    if isinstance(lock, dict) and lock.get("status") == "RUNNING":
                        lock["status"] = "CURRENT_CONFIG_RESTARTED"
                        lock["returncode"] = -9
                        lock["finished_at"] = utc_now()
                        lock["stale_recovery_reason"] = "TASK_4200_CURRENT_CONFIG_RESTART"
                        write_json(lock_path, lock)
                    progress = read_json(progress_path, {})
                    if isinstance(progress, dict):
                        progress["status"] = "CURRENT_CONFIG_RESTARTED"
                        progress["limit_hit_reason"] = "TASK_4200_CURRENT_CONFIG_RESTART"
                        progress["updated_at"] = utc_now()
                        write_json(progress_path, progress)
    time.sleep(3)
    remove_stop_file(NEWSWIRE_STOP_PATH)
    launched = start_newswire_launcher()
    return {"terminated": terminated, "launched": launched}


def current_five_min_config_is_current() -> bool:
    bg = read_json(FIVE_MIN_BACKGROUND_PATH, {})
    progress = read_json(FIVE_MIN_PROGRESS_PATH, {})
    if not isinstance(bg, dict):
        return False
    progress_pacing = progress.get("request_pacing_mode") if isinstance(progress, dict) else ""
    return (
        as_int(bg.get("requests_per_minute")) == 120
        and bg.get("request_pacing_mode") == "request_start_interval_cap"
        and progress_pacing in {"", None, "request_start_interval_cap"}
    )


def restart_five_min_for_current_config() -> dict[str, Any]:
    bg = read_json(FIVE_MIN_BACKGROUND_PATH, {})
    FIVE_MIN_STOP_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIVE_MIN_STOP_PATH.write_text("TASK-4201 current 5m pacing restart\n", encoding="utf-8")
    terminated: list[dict[str, Any]] = []
    if isinstance(bg, dict):
        terminated.append(terminate_pid(as_int(bg.get("pid")), reason="TASK_4201_CURRENT_5M_PACING_RESTART"))
    time.sleep(3)
    remove_stop_file(FIVE_MIN_STOP_PATH)
    launched = start_five_min()
    return {"terminated": terminated, "launched": launched}


def is_nul_corrupted(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    data = path.read_bytes()
    return bool(data) and data.count(b"\x00") == len(data)


def backup_file(path: Path, *, reason: str) -> str:
    if not path.exists():
        return ""
    backup_dir = ARTIFACT_DIR / "corrupt_checkpoint_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"{path.name}.{stamp}.{reason}.bak"
    backup_path.write_bytes(path.read_bytes())
    append_event("CHECKPOINT_BACKED_UP", {"path": rel(path), "backup_path": rel(backup_path), "reason": reason})
    return rel(backup_path)


def recover_five_min_checkpoint_if_needed() -> dict[str, Any]:
    corrupted = [path for path in [FIVE_MIN_STATE_PATH, FIVE_MIN_PROGRESS_PATH] if is_nul_corrupted(path)]
    if not corrupted:
        return {"recovered": 0, "reason": "not_corrupted"}

    from tools.db.source_acquisition.bar_full_backfill import (  # noqa: PLC0415
        DEFAULT_FIVE_MIN_CHUNK_DAYS,
        DEFAULT_START_DATE,
        calendar_date_blocks,
        latest_complete_market_date,
        load_universe,
        now_z,
    )

    symbols = load_universe()
    blocks = calendar_date_blocks(DEFAULT_START_DATE, latest_complete_market_date(), max_span_days=DEFAULT_FIVE_MIN_CHUNK_DAYS)
    symbol_to_index = {symbol: idx for idx, symbol in enumerate(symbols)}
    block_start_to_index = {str(start): idx for idx, (start, _end) in enumerate(blocks)}
    last_event: dict[str, Any] | None = None
    counters = {
        "processed_events": 0,
        "exported_events": 0,
        "empty_events": 0,
        "skipped_events": 0,
        "failed_events": 0,
        "rate_limited_events": 0,
        "five_min_rows_written": 0,
    }
    if FIVE_MIN_EVENT_PATH.exists():
        with FIVE_MIN_EVENT_PATH.open("r", encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                if '"lane": "5m"' not in line and '"lane":"5m"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                last_event = row
                counters["processed_events"] += 1
                status = str(row.get("status") or "")
                if status == "EXPORTED":
                    counters["exported_events"] += 1
                    counters["five_min_rows_written"] += as_int(row.get("row_count"))
                elif status == "EMPTY_PROVIDER_RESPONSE":
                    counters["empty_events"] += 1
                elif status.startswith("SKIPPED"):
                    counters["skipped_events"] += 1
                elif status == "RATE_LIMITED":
                    counters["rate_limited_events"] += 1
                else:
                    counters["failed_events"] += 1

    if not last_event:
        return {"recovered": 0, "reason": "no_5m_events_for_cursor_recovery", "corrupted": [rel(path) for path in corrupted]}

    symbol = str(last_event.get("symbol") or "").strip().upper()
    source_id = str(last_event.get("source_id") or "")
    parts = source_id.split(":")
    block_start = parts[2] if len(parts) >= 4 else ""
    symbol_index = symbol_to_index.get(symbol)
    block_index = block_start_to_index.get(block_start)
    if symbol_index is None or block_index is None:
        return {
            "recovered": 0,
            "reason": "last_event_cursor_not_resolvable",
            "symbol": symbol,
            "block_start": block_start,
            "corrupted": [rel(path) for path in corrupted],
        }

    if str(last_event.get("status") or "") == "RATE_LIMITED":
        next_symbol_index = symbol_index
        next_block_index = block_index
    else:
        next_block_index = block_index + 1
        next_symbol_index = symbol_index
        if next_block_index >= len(blocks):
            next_symbol_index += 1
            next_block_index = 0

    backups = [backup_file(path, reason="nul_corrupt") for path in corrupted]
    state = {
        "schema_version": 1,
        "start_date": DEFAULT_START_DATE,
        "end_date": latest_complete_market_date(),
        "lanes": ["5m"],
        "universe_count": len(symbols),
        "five_min_blocks_per_symbol": len(blocks),
        "lane_cursor_index": 0,
        "daily_symbol_index": 0,
        "five_min_symbol_index": next_symbol_index,
        "five_min_block_index": next_block_index,
        "daily_rows_written": 0,
        "updated_at": now_z(),
        **counters,
    }
    write_json(FIVE_MIN_STATE_PATH, state)
    done = min(next_symbol_index * len(blocks) + next_block_index, len(symbols) * len(blocks))
    total = len(symbols) * len(blocks)
    progress = {
        **state,
        "status": "RECOVERED_FROM_EVENT_LOG",
        "last_status": "RECOVERED_FROM_EVENT_LOG",
        "daily_progress_pct": 100.0,
        "five_min_progress_pct": round(done / total * 100.0, 4) if total else 100.0,
        "overall_progress_pct": round(done / total * 100.0, 4) if total else 100.0,
        "remaining_request_units": max(total - done, 0),
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
        "updated_at": now_z(),
    }
    write_json(FIVE_MIN_PROGRESS_PATH, progress)
    payload = {
        "recovered": 1,
        "reason": "nul_corrupt_checkpoint",
        "backups": backups,
        "last_event_symbol": symbol,
        "last_event_source_id": source_id,
        "next_symbol_index": next_symbol_index,
        "next_block_index": next_block_index,
        "five_min_progress_pct": progress["five_min_progress_pct"],
    }
    append_event("FIVE_MIN_CHECKPOINT_RECOVERED", payload)
    return payload


def aggregate_newswire() -> dict[str, Any]:
    script = ROOT / "scripts" / "aggregate_l0_public_newswire_shards.py"
    if not script.exists():
        return {"returncode": "MISSING", "stdout_tail": "", "stderr_tail": "aggregate script missing"}
    result = subprocess.run(
        [sys.executable, str(script), "--skip-raw-dedupe"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    return {
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-1000:],
        "stderr_tail": result.stderr[-1000:],
    }


def build_l0_status() -> dict[str, Any]:
    script = ROOT / "scripts" / "build_l0_operating_status_4190.py"
    if not script.exists():
        return {"returncode": "MISSING", "stdout_tail": "", "stderr_tail": "status builder missing"}
    result = subprocess.run(
        [sys.executable, str(script), "--contract", "ops/l0_operating_contract.yaml"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    return {
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-1000:],
        "stderr_tail": result.stderr[-1000:],
    }


def start_newswire_launcher() -> dict[str, Any]:
    remove_stop_file(NEWSWIRE_STOP_PATH)
    RUNTIME_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stdout_path = RUNTIME_LOG_DIR / f"public_newswire_{stamp}.stdout.log"
    stderr_path = RUNTIME_LOG_DIR / f"public_newswire_{stamp}.stderr.log"
    args = [
        sys.executable,
        "scripts/run_l0_public_newswire_sharded_backfill.py",
        "--start-month",
        "2016-01",
        "--end-month",
        "2026-06",
        "--sources",
        "businesswire,prnewswire",
        "--mode",
        "stable",
        "--concurrency",
        "5",
        "--schedule-strategy",
        "source_round_robin",
        "--source-base-lanes",
        "businesswire=4,prnewswire=1",
        "--source-lane-caps",
        "businesswire=4,prnewswire=1",
        "--rebalance-priority",
        "businesswire,prnewswire",
        "--businesswire-shard-granularity",
        "day",
        "--source-max-fetches",
        "businesswire=200,prnewswire=220",
        "--source-max-items",
        "businesswire=250,prnewswire=250",
        "--source-request-sleep-seconds",
        "businesswire=1.0,prnewswire=1.0",
        "--source-max-worker-seconds",
        "businesswire=14400,prnewswire=21600",
        "--source-stale-progress-seconds",
        "businesswire=1200,prnewswire=1800",
        "--max-recycles-per-shard",
        "6",
        "--poll-seconds",
        "5",
    ]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
        process = subprocess.Popen(args, cwd=ROOT, stdout=stdout, stderr=stderr, creationflags=flags)
    payload = {
        "schema_version": "task4193_l0_public_newswire_sharded_launcher_process_v1",
        "task_id": TASK_ID,
        "pid": process.pid,
        "started_at": utc_now(),
        "provider": "public_newswire_feeds",
        "launcher": "scripts/run_l0_public_newswire_sharded_backfill.py",
        "aggregate_progress_path": rel(NEWSWIRE_AGGREGATE_PATH),
        "stop_path": rel(NEWSWIRE_STOP_PATH),
        "mode": "stable",
        "concurrency": 5,
        "source_base_lanes": "businesswire=4,prnewswire=1",
        "source_lane_caps": "businesswire=4,prnewswire=1",
        "businesswire_shard_granularity": "day",
        "source_max_fetches": "businesswire=200,prnewswire=220",
        "source_max_items": "businesswire=250,prnewswire=250",
        "source_max_worker_seconds": "businesswire=14400,prnewswire=21600",
        "source_stale_progress_seconds": "businesswire=1200,prnewswire=1800",
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    write_json(NEWSWIRE_BACKGROUND_PATH, payload)
    append_event("NEWSWIRE_LAUNCHER_STARTED", {"pid": process.pid, "stdout_path": rel(stdout_path), "stderr_path": rel(stderr_path)})
    return payload


def run_powershell_start(script: str, args: list[str], event_type: str) -> dict[str, Any]:
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, *args]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90,
    )
    payload = {
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-1000:],
        "stderr_tail": result.stderr[-1000:],
    }
    append_event(event_type, payload)
    return payload


def start_market_macro() -> dict[str, Any]:
    remove_stop_file(MARKET_STOP_PATH)
    return run_powershell_start(
        "scripts/start_l0_public_market_macro_news_backfill.ps1",
        [
            "-MaxItemsPerSource",
            "1000",
            "-MaxFetchesPerSource",
            "48",
            "-CycleSleepSeconds",
            "120",
            "-RequestSleepSeconds",
            "1.0",
        ],
        "MARKET_MACRO_STARTED",
    )


def start_five_min() -> dict[str, Any]:
    remove_stop_file(FIVE_MIN_STOP_PATH)
    recovery = recover_five_min_checkpoint_if_needed()
    if recovery.get("recovered"):
        append_event("FIVE_MIN_PRESTART_CHECKPOINT_RECOVERY", recovery)
    return run_powershell_start(
        "scripts/start_l0_bar_full_backfill.ps1",
        [
            "-Lanes",
            "5m",
            "-FiveMinChunkDays",
            "120",
            "-RequestsPerMinute",
            "120",
            "-RetryLimit",
            "3",
            "-StatusPath",
            "data/artifacts/l0_bar_full_backfill/background_process_5m.json",
            "-MaxRuntimeMinutes",
            "0",
        ],
        "FIVE_MIN_STARTED",
    )


def newswire_snapshot() -> dict[str, Any]:
    bg = read_json(NEWSWIRE_BACKGROUND_PATH, {})
    agg = read_json(NEWSWIRE_AGGREGATE_PATH, {})
    pid = as_int(bg.get("pid")) if isinstance(bg, dict) else 0
    by_source = agg.get("by_source", {}) if isinstance(agg, dict) else {}
    return {
        "status": agg.get("status") if isinstance(agg, dict) else "",
        "progress_pct": as_float(agg.get("progress_pct")) if isinstance(agg, dict) else 0.0,
        "completed_units": as_int(agg.get("completed_units")) if isinstance(agg, dict) else 0,
        "pending_units": as_int(agg.get("pending_units")) if isinstance(agg, dict) else 0,
        "partial_units": as_int(agg.get("partial_units")) if isinstance(agg, dict) else 0,
        "failed_units": as_int(agg.get("failed_units")) if isinstance(agg, dict) else 0,
        "total_units": as_int(agg.get("total_units")) if isinstance(agg, dict) else 0,
        "long_tail_eta_hours": as_float(agg.get("long_tail_eta_hours_by_source_unit_velocity")) if isinstance(agg, dict) else 0.0,
        "pid": pid,
        "pid_alive": int(pid_alive(pid)),
        "pid_owner_verified": int(commandline_contains(pid, "run_l0_public_newswire_sharded_backfill.py")),
        "by_source": by_source,
    }


def market_snapshot() -> dict[str, Any]:
    bg = read_json(MARKET_BACKGROUND_PATH, {})
    progress = read_json(MARKET_PROGRESS_PATH, {})
    pid = as_int(bg.get("pid")) if isinstance(bg, dict) else 0
    backfill = progress.get("backfill", {}) if isinstance(progress, dict) else {}
    pending = 0
    total = 0
    if isinstance(backfill, dict):
        for row in backfill.values():
            if isinstance(row, dict):
                pending += as_int(row.get("pending_units"))
                total += as_int(row.get("total_units"))
    return {
        "last_status": progress.get("last_status") if isinstance(progress, dict) else "",
        "processed_events": as_int(progress.get("processed_events")) if isinstance(progress, dict) else 0,
        "exported_events": as_int(progress.get("exported_events")) if isinstance(progress, dict) else 0,
        "failed_events": as_int(progress.get("failed_events")) if isinstance(progress, dict) else 0,
        "pending_units": pending,
        "total_units": total,
        "updated_at": progress.get("updated_at") if isinstance(progress, dict) else "",
        "pid": pid,
        "pid_alive": int(pid_alive(pid)),
        "pid_owner_verified": int(commandline_contains(pid, "run_l0_public_market_macro_news_collector.py")),
    }


def bar_snapshot() -> dict[str, Any]:
    daily = read_json(DAILY_PROGRESS_PATH, {})
    five_bg = read_json(FIVE_MIN_BACKGROUND_PATH, {})
    five = read_json(FIVE_MIN_PROGRESS_PATH, {})
    five_pid = as_int(five_bg.get("pid")) if isinstance(five_bg, dict) else 0
    return {
        "daily_status": daily.get("status") if isinstance(daily, dict) else "",
        "daily_progress_pct": as_float(daily.get("daily_progress_pct")) if isinstance(daily, dict) else 0.0,
        "daily_rows_written": as_int(daily.get("daily_rows_written")) if isinstance(daily, dict) else 0,
        "five_min_status": five.get("status") if isinstance(five, dict) else "",
        "five_min_progress_pct": as_float(five.get("five_min_progress_pct")) if isinstance(five, dict) else 0.0,
        "five_min_rows_written": as_int(five.get("five_min_rows_written")) if isinstance(five, dict) else 0,
        "five_min_pid": five_pid,
        "five_min_pid_alive": int(pid_alive(five_pid)),
        "five_min_pid_owner_verified": int(commandline_contains(five_pid, "run_l0_bar_full_backfill.py")),
    }


def write_snapshot(payload: dict[str, Any]) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    write_json(SNAPSHOT_DIR / f"{stamp}.json", payload)


def one_cycle() -> dict[str, Any]:
    previous_status = read_json(STATUS_PATH, {})
    previous_newswire = previous_status.get("public_newswire", {}) if isinstance(previous_status, dict) else {}
    aggregate_result = aggregate_newswire()
    before_newswire = newswire_snapshot()
    before_market = market_snapshot()
    before_bar = bar_snapshot()
    actions: list[dict[str, Any]] = []

    newswire_config_stale = before_newswire["pending_units"] > 0 and before_newswire["pid_alive"] == 1 and before_newswire["pid_owner_verified"] == 1 and not current_newswire_launcher_config_is_current()
    if newswire_config_stale:
        actions.append({"target": "public_newswire", "action": "restart_current_config", "result": restart_newswire_for_current_config()})
    elif before_newswire["pending_units"] > 0 and (before_newswire["pid_alive"] == 0 or before_newswire["pid_owner_verified"] == 0):
        actions.append({"target": "public_newswire", "action": "restart", "result": start_newswire_launcher()})

    market_incomplete = before_market["pending_units"] > 0 or str(before_market["last_status"]).upper() == "FAILED_RETRYABLE"
    if market_incomplete and (before_market["pid_alive"] == 0 or before_market["pid_owner_verified"] == 0):
        actions.append({"target": "public_market_macro_news", "action": "restart", "result": start_market_macro()})

    five_incomplete = before_bar["five_min_progress_pct"] < 100.0
    five_min_config_stale = five_incomplete and before_bar["five_min_pid_alive"] == 1 and before_bar["five_min_pid_owner_verified"] == 1 and not current_five_min_config_is_current()
    if five_min_config_stale:
        actions.append({"target": "five_min_bars", "action": "restart_current_pacing_config", "result": restart_five_min_for_current_config()})
    elif five_incomplete and (before_bar["five_min_pid_alive"] == 0 or before_bar["five_min_pid_owner_verified"] == 0):
        actions.append({"target": "five_min_bars", "action": "restart", "result": start_five_min()})

    time.sleep(5 if actions else 0)
    build_status_result = build_l0_status()
    after_newswire = newswire_snapshot()
    previous_completed = as_int(previous_newswire.get("completed_units")) if isinstance(previous_newswire, dict) else 0
    completed_delta = after_newswire["completed_units"] - previous_completed
    generated_at_previous = previous_status.get("generated_at", "") if isinstance(previous_status, dict) else ""
    seconds_since_previous = elapsed_seconds_since(generated_at_previous)
    newswire_progress_health = {
        "previous_generated_at": generated_at_previous,
        "seconds_since_previous_cycle": seconds_since_previous,
        "previous_completed_units": previous_completed,
        "completed_units_delta_since_previous_cycle": completed_delta,
        "stalled_completed_units": int(after_newswire["pending_units"] > 0 and previous_completed > 0 and completed_delta <= 0 and seconds_since_previous >= 1800),
        "stall_threshold_seconds": 1800,
        "active_worker_count": len((read_json(NEWSWIRE_AGGREGATE_PATH, {}) or {}).get("active_workers", []) or []),
    }
    if newswire_progress_health["stalled_completed_units"]:
        append_event(
            "NEWSWIRE_COMPLETED_UNIT_STALL",
            {
                "pending_units": after_newswire["pending_units"],
                "completed_units": after_newswire["completed_units"],
                "previous_completed_units": previous_completed,
                "pid": after_newswire["pid"],
            },
        )
    after = {
        "generated_at": utc_now(),
        "task_id": TASK_ID,
        "aggregate_result": aggregate_result,
        "build_l0_status_result": build_status_result,
        "actions": actions,
        "public_newswire": after_newswire,
        "public_newswire_progress_health": newswire_progress_health,
        "public_market_macro_news": market_snapshot(),
        "bars": bar_snapshot(),
        "safety": {
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "live_order_permitted_flag": 0,
            "paper_promotion_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        },
    }
    write_json(STATUS_PATH, after)
    write_snapshot(after)
    append_event("SUPERVISOR_CYCLE", {"actions": [row["target"] for row in actions], "newswire_pending": after["public_newswire"]["pending_units"], "market_pending": after["public_market_macro_news"]["pending_units"]})
    return after


def install_self_background() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = RUNTIME_LOG_DIR / "supervisor.stdout.log"
    stderr_path = RUNTIME_LOG_DIR / "supervisor.stderr.log"
    args = [
        sys.executable,
        "scripts/run_task4193_l0_overnight_backfill_supervisor.py",
        "--loop",
        "--sleep-seconds",
        "300",
        "--max-hours",
        "12",
    ]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
        process = subprocess.Popen(args, cwd=ROOT, stdout=stdout, stderr=stderr, creationflags=flags)
    payload = {
        "schema_version": "task4193_l0_overnight_supervisor_process_v1",
        "task_id": TASK_ID,
        "pid": process.pid,
        "started_at": utc_now(),
        "script": "scripts/run_task4193_l0_overnight_backfill_supervisor.py",
        "mode": "loop",
        "sleep_seconds": 300,
        "max_hours": 12,
        "status_path": rel(STATUS_PATH),
        "event_path": rel(EVENT_PATH),
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "live_order_permitted_flag": 0,
        "paper_promotion_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    write_json(BACKGROUND_PROCESS_PATH, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--sleep-seconds", type=int, default=300)
    parser.add_argument("--max-hours", type=float, default=12)
    parser.add_argument("--install-background", action="store_true")
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if args.install_background:
        payload = install_self_background()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    end_at = time.time() + max(args.max_hours, 0.1) * 3600
    cycle = 0
    while True:
        cycle += 1
        payload = one_cycle()
        print(json.dumps({"cycle": cycle, "generated_at": payload["generated_at"], "actions": payload["actions"]}, ensure_ascii=False))
        if not args.loop or time.time() >= end_at:
            break
        time.sleep(max(args.sleep_seconds, 30))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
