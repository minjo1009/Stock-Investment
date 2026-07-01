from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4199"
ARTIFACT = ROOT / "data/artifacts/task_4199_l0_scheduler_deletion_and_l0_l5_integration_audit"
STATE_PATH = ARTIFACT / "l3_l4_refresh_state.json"
RUN_STATUS = ARTIFACT / "l3_l4_refresh_last_run.json"
LOCK_PATH = ARTIFACT / "l3_l4_refresh.lock.json"


INPUTS = [
    ROOT / "data/artifacts/l0_operating_status/current_l0_status.json",
    ROOT / "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l1_article_packets.csv",
    ROOT / "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l2_diagnostic_feature_rows.csv",
    ROOT / "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l1_wide_normalized_source_packets.csv",
    ROOT / "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l2_feature_materialization_candidates.csv",
    ROOT / "configs/l3_diagnostic_strategy_view_bootstrap_4150.json",
    ROOT / "configs/l3_relation_graph_v2_4152.json",
    ROOT / "configs/l3_relation_graph_quality_guard_4154.json",
    ROOT / "configs/l4_thesis_bundle_4156.json",
]


COMMANDS = [
    ["python", "scripts/build_l3_diagnostic_strategy_view_4150.py", "--config", "configs/l3_diagnostic_strategy_view_bootstrap_4150.json"],
    ["python", "scripts/build_l3_relation_graph_v2_4152.py", "--config", "configs/l3_relation_graph_v2_4152.json"],
    ["python", "scripts/build_l3_relation_graph_quality_guard_4154.py", "--config", "configs/l3_relation_graph_quality_guard_4154.json"],
    ["python", "scripts/build_l4_thesis_bundles.py", "--config", "configs/l4_thesis_bundle_4156.json"],
    ["python", "scripts/build_task4199_layer_refresh_chain.py"],
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def input_watermark() -> dict[str, Any]:
    rows = [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256_file(path)} for path in INPUTS]
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"digest": digest, "inputs": rows}


def pid_alive(pid: Any) -> bool:
    try:
        pid_int = int(pid)
    except Exception:
        return False
    if pid_int <= 0:
        return False
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"if(Get-Process -Id {pid_int} -ErrorAction SilentlyContinue){{'1'}}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() == "1"


def acquire_lock() -> bool:
    lock = read_json(LOCK_PATH)
    if lock and pid_alive(lock.get("pid")):
        return False
    write_json(LOCK_PATH, {"task_id": TASK_ID, "pid": os.getpid(), "started_at": now_iso()})
    return True


def release_lock() -> None:
    try:
        LOCK_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def run_command(cmd: list[str], timeout_seconds: int) -> dict[str, Any]:
    started = now_iso()
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )
    return {
        "command": " ".join(cmd),
        "started_at": started,
        "ended_at": now_iso(),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()

    if not acquire_lock():
        write_json(RUN_STATUS, {"task_id": TASK_ID, "status": "SKIPPED_LOCKED", "generated_at": now_iso()})
        return 0
    try:
        current = input_watermark()
        previous = read_json(STATE_PATH)
        commands: list[dict[str, Any]] = []
        should_run = args.force or previous.get("digest") != current["digest"]
        status = "NOOP_INPUT_WATERMARK_UNCHANGED"
        if should_run:
            status = "REFRESHED"
            for cmd in COMMANDS:
                result = run_command(cmd, args.timeout_seconds)
                commands.append(result)
                if result["returncode"] != 0:
                    status = "FAILED"
                    break
            if status == "REFRESHED":
                write_json(STATE_PATH, {**current, "updated_at": now_iso()})
        else:
            result = run_command(["python", "scripts/build_task4199_layer_refresh_chain.py"], args.timeout_seconds)
            commands.append(result)
            if result["returncode"] != 0:
                status = "FAILED"

        run_status = {
            "task_id": TASK_ID,
            "generated_at": now_iso(),
            "status": status,
            "input_digest": current["digest"],
            "commands": commands,
            "authority": {
                "diagnostic_only": True,
                "broker_mutation": 0,
                "live_order": 0,
                "paper_promotion": 0,
                "trading_authority": 0,
            },
        }
        write_json(RUN_STATUS, run_status)
        return 0 if status in {"REFRESHED", "NOOP_INPUT_WATERMARK_UNCHANGED"} else 1
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
