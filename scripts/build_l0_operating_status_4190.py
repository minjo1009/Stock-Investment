from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - environment guard
    print(f"FAIL PyYAML is required: {exc}")
    sys.exit(2)


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4195"
DEFAULT_CONTRACT = ROOT / "ops/l0_operating_contract.yaml"
DEFAULT_OUT_ROOT = ROOT / "data/artifacts/l0_operating_status"


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(ROOT)
        except ValueError:
            return p.as_posix()
    return p.as_posix()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    last_exc: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le"):
        try:
            with path.open("r", encoding=encoding) as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            last_exc = exc
    raise ValueError(f"could not decode JSON {path}: {last_exc}")


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process_info(pid: Any) -> dict[str, Any]:
    if not pid:
        return {"pid": None, "alive": False, "command_line": None, "process_name": None}
    try:
        pid_int = int(pid)
    except Exception:
        return {"pid": pid, "alive": False, "command_line": None, "process_name": None}

    ps = (
        "Get-CimInstance Win32_Process -Filter \"ProcessId = "
        + str(pid_int)
        + "\" | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    text = proc.stdout.strip()
    if not text:
        return {"pid": pid_int, "alive": False, "command_line": None, "process_name": None}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"pid": pid_int, "alive": True, "command_line": None, "process_name": None}
    if isinstance(data, list):
        data = data[0] if data else {}
    return {
        "pid": pid_int,
        "alive": bool(data),
        "command_line": data.get("CommandLine"),
        "process_name": data.get("Name"),
    }


def scheduler_task(name: str) -> dict[str, Any]:
    escaped_name = name.replace("'", "''")
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                f"$task=Get-ScheduledTask -TaskName '{escaped_name}' -ErrorAction SilentlyContinue;"
                "if ($task) {"
                f"$info=Get-ScheduledTaskInfo -TaskName '{escaped_name}';"
                "$action=$task.Actions | Select-Object -First 1;"
                "[pscustomobject]@{"
                "TaskName=$task.TaskName;"
                "State=$task.State.ToString();"
                "NextRunTime=if($info.NextRunTime){$info.NextRunTime.ToString('o')}else{''};"
                "LastRunTime=if($info.LastRunTime){$info.LastRunTime.ToString('o')}else{''};"
                "LastTaskResult=[string]$info.LastTaskResult;"
                "TaskToRun=if($action){(($action.Execute + ' ' + $action.Arguments).Trim())}else{''}"
                "} | ConvertTo-Json -Compress"
                "}"
            ),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "name": name,
            "exists": False,
            "query_returncode": proc.returncode,
            "status": "MISSING",
            "last_result": None,
            "last_result_status": "MISSING",
            "task_to_run": None,
            "raw_error": proc.stderr.strip(),
        }
    if not (proc.stdout or "").strip():
        return {
            "name": name,
            "exists": False,
            "query_returncode": proc.returncode,
            "status": "MISSING",
            "last_result": None,
            "last_result_status": "MISSING",
            "task_to_run": None,
            "raw_error": proc.stderr.strip(),
        }
    try:
        row = json.loads(proc.stdout)
    except json.JSONDecodeError:
        row = {}

    last_result = str(row.get("LastTaskResult") or "")
    status = str(row.get("State") or "")
    result_status = classify_scheduler_result(last_result, status)
    return {
        "name": name,
        "exists": True,
        "query_returncode": proc.returncode,
        "task_name": row.get("TaskName"),
        "status": status,
        "next_run_time": row.get("NextRunTime"),
        "last_run_time": row.get("LastRunTime"),
        "last_result": last_result,
        "last_result_status": result_status,
        "task_to_run": row.get("TaskToRun"),
    }


def classify_scheduler_result(last_result: str | None, status: str | None) -> str:
    if last_result is None:
        return "UNKNOWN"
    value = str(last_result).strip()
    if (status or "").strip().lower() == "running":
        return "RUNNING"
    if value in {"0", "0x0"}:
        return "SUCCESS"
    if value in {"", "N/A"}:
        return "UNKNOWN"
    return "FAILED"


def load_optional_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        failures.append(f"missing json: {rel(path)}")
        return {}
    try:
        return read_json(path)
    except Exception as exc:
        failures.append(f"invalid json {rel(path)}: {exc}")
        return {}


def lane_completed(lane_name: str) -> bool:
    progress_by_lane = {
        "daily_bars_backfill": ROOT / "data/artifacts/l0_bar_daily_full_backfill/collector_progress.json",
        "five_min_bars_backfill": ROOT / "data/artifacts/l0_bar_full_backfill/collector_progress.json",
    }
    progress_path = progress_by_lane.get(lane_name)
    if not progress_path or not progress_path.exists():
        return False
    try:
        progress = read_json(progress_path)
    except Exception:
        return False
    status = str(progress.get("status") or progress.get("last_status") or "").upper()
    overall = float(progress.get("overall_progress_pct") or 0)
    daily = float(progress.get("daily_progress_pct") or 0)
    five_min = float(progress.get("five_min_progress_pct") or 0)
    remaining = int(progress.get("remaining_request_units") or 0)
    return status in {"EXHAUSTED", "COMPLETE", "COMPLETED"} and max(overall, daily, five_min) >= 100 and remaining == 0


def by_source_summary(aggregate: dict[str, Any]) -> dict[str, Any]:
    source = aggregate.get("by_source") or {}
    out: dict[str, Any] = {}
    for key in ["businesswire", "globenewswire", "prnewswire"]:
        row = source.get(key) or {}
        completed = int(row.get("completed_units") or 0)
        pending = int(row.get("pending_units") or 0)
        partial = int(row.get("partial_units") or 0)
        failed = int(row.get("failed_units") or 0)
        out[key] = {
            "completed_units": completed,
            "pending_units": pending,
            "partial_units": partial,
            "failed_units": failed,
            "row_count": row.get("row_count"),
            "unit_velocity_per_hour": row.get("unit_velocity_per_hour"),
            "status": "COMPLETE" if pending == 0 and partial == 0 and failed == 0 else "INCOMPLETE",
        }
    return out


def build_status(contract_path: Path, out_root: Path) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    inputs: list[str] = [rel(contract_path)]
    generated_at = now_iso()

    if not contract_path.exists():
        blockers.append("L0_CONTRACT_MISSING")
        contract: dict[str, Any] = {}
    else:
        contract = read_yaml(contract_path)

    lanes = contract.get("active_lanes") or {}
    newswire_cfg = lanes.get("public_newswire_backfill") or {}
    realtime_cfg = lanes.get("realtime_hardening_loop") or {}
    recovery_cfg = lanes.get("backfill_recovery_loop") or {}

    aggregate_path = ROOT / (newswire_cfg.get("aggregate_progress") or "")
    background_path = ROOT / (newswire_cfg.get("background_process") or "")
    realtime_config_path = ROOT / (realtime_cfg.get("config") or "")
    inputs.extend(rel(p) for p in [aggregate_path, background_path, realtime_config_path] if str(p) != ".")

    load_failures: list[str] = []
    aggregate = load_optional_json(aggregate_path, load_failures)
    background = load_optional_json(background_path, load_failures)
    realtime_config = load_optional_json(realtime_config_path, load_failures)
    blockers.extend("L0_ACTIVE_ARTIFACT_MISSING" for _ in load_failures)

    launcher = process_info(background.get("pid"))
    expected_runner = newswire_cfg.get("runner")
    command_line = (launcher.get("command_line") or "").replace("\\", "/")
    command_matches = bool(expected_runner and expected_runner.replace("\\", "/") in command_line) if launcher.get("alive") else False

    active_workers = aggregate.get("active_workers") or []
    stale_workers = aggregate.get("stale_workers") or []
    active_worker_alive_count = 0
    active_worker_rows: list[dict[str, Any]] = []
    for worker in active_workers:
        if not isinstance(worker, dict):
            continue
        worker_pid = worker.get("worker_pid") or worker.get("pid")
        info = process_info(worker_pid)
        if info["alive"]:
            active_worker_alive_count += 1
        active_worker_rows.append({
            "source": worker.get("source"),
            "shard_key": worker.get("shard_key"),
            "worker_pid": worker_pid,
            "alive": info["alive"],
            "status": worker.get("status"),
            "last_progress_at": worker.get("last_progress_at"),
        })

    aggregate_status = aggregate.get("status")
    pending_units = int(aggregate.get("pending_units") or 0)
    partial_units = int(aggregate.get("partial_units") or 0)
    failed_units = int(aggregate.get("failed_units") or 0)

    derived_newswire_status = "UNKNOWN"
    if aggregate_status == "COMPLETED" and pending_units == 0 and partial_units == 0 and failed_units == 0:
        derived_newswire_status = "COMPLETE"
    elif aggregate_status == "RUNNING" and not launcher["alive"] and active_worker_alive_count == 0:
        derived_newswire_status = "BLOCKED_DEAD_PID"
        blockers.append("L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD")
    elif pending_units > 0 or partial_units > 0:
        derived_newswire_status = "RUNNING_INCOMPLETE" if launcher["alive"] else "BLOCKED_INCOMPLETE_NOT_RUNNING"
    if pending_units > 0 or partial_units > 0:
        blockers.append("L0_PUBLIC_NEWSWIRE_INCOMPLETE")
    if stale_workers:
        warnings.append("L0_STALE_WORKERS_PRESENT")
    if launcher["alive"] and not command_matches:
        warnings.append("L0_LAUNCHER_PID_COMMAND_UNVERIFIED")

    scheduler = scheduler_task(str(realtime_cfg.get("scheduler_task") or ""))
    recovery_scheduler = scheduler_task(str(recovery_cfg.get("scheduler_task") or ""))
    if not scheduler["exists"]:
        blockers.append("L0_REALTIME_SCHEDULER_MISSING")
    elif scheduler["last_result_status"] == "FAILED":
        blockers.append("L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED")
    elif scheduler["last_result_status"] == "RUNNING_PREVIOUS_NON_SUCCESS":
        warnings.append("L0_REALTIME_SCHEDULER_RUNNING_WITH_PREVIOUS_NON_SUCCESS_RESULT")

    if not recovery_scheduler["exists"]:
        blockers.append("L0_BACKFILL_GUARD_SCHEDULER_MISSING")
    elif recovery_scheduler["last_result_status"] == "FAILED":
        blockers.append("L0_BACKFILL_GUARD_SCHEDULER_LAST_RESULT_FAILED")
    elif recovery_scheduler["last_result_status"] == "RUNNING_PREVIOUS_NON_SUCCESS":
        warnings.append("L0_RECOVERY_TASK_RUNNING_WITH_PREVIOUS_NON_SUCCESS_RESULT")

    config_scheduler = (((realtime_config.get("runtime_boundary") or {}).get("scheduler_task_name")) if realtime_config else None)
    contract_scheduler = realtime_cfg.get("scheduler_task")
    config_alignment = {
        "realtime_config_path": rel(realtime_config_path),
        "config_scheduler_task": config_scheduler,
        "contract_scheduler_task": contract_scheduler,
        "aligned": bool(config_scheduler and contract_scheduler and config_scheduler == contract_scheduler),
    }
    if not config_alignment["aligned"]:
        blockers.append("L0_REALTIME_CONFIG_SCHEDULER_MISMATCH")

    lane_statuses: dict[str, Any] = {}
    for lane_name, lane in lanes.items():
        bg = lane.get("background_process")
        lane_row: dict[str, Any] = {"role": lane.get("role")}
        if bg:
            bg_path = ROOT / bg
            bg_data = load_optional_json(bg_path, [])
            info = process_info(bg_data.get("pid"))
            lane_row.update({"background_process": bg, "pid": bg_data.get("pid"), "pid_alive": info["alive"]})
            if lane_name not in {"public_newswire_backfill"} and bg_data.get("pid") and not info["alive"] and not lane_completed(lane_name):
                warnings.append(f"L0_BACKGROUND_PID_DEAD:{lane_name}")
        lane_statuses[lane_name] = lane_row

    legacy = []
    active_paths = {v for lane in lanes.values() if isinstance(lane, dict) for v in lane.values() if isinstance(v, str)}
    for entry in contract.get("legacy_runtime_entrypoints") or []:
        path = entry.get("path")
        if not path:
            continue
        exists = (ROOT / path).exists()
        if exists:
            warnings.append(f"L0_LEGACY_PATH_PRESENT:{path}")
        if path in active_paths:
            blockers.append(f"L0_LEGACY_PATH_TREATED_AS_CURRENT:{path}")
        legacy.append({"path": path, "exists": exists, "reason": entry.get("reason")})

    reference_configs = []
    for entry in contract.get("reference_configs") or []:
        path = entry.get("path")
        if not path:
            continue
        reference_configs.append({"path": path, "exists": (ROOT / path).exists(), "reason": entry.get("reason")})

    deleted_legacy_entrypoints = []
    for entry in contract.get("deleted_legacy_entrypoints") or []:
        path = entry.get("path")
        if not path:
            continue
        exists = (ROOT / path).exists()
        deleted_legacy_entrypoints.append(
            {
                "path": path,
                "exists": exists,
                "deleted": not exists,
                "reason": entry.get("reason"),
                "deleted_by_task": entry.get("deleted_by_task"),
            }
        )

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    verdict = "BLOCKED" if blockers else "PASS_WITH_WARNINGS" if warnings else "PASS"

    status = {
        "schema_version": "l0_operating_status_v1",
        "task_id": contract.get("task_id") or TASK_ID,
        "generated_at": generated_at,
        "contract_path": rel(contract_path),
        "overall_verdict": verdict,
        "blockers": blockers,
        "warnings": warnings,
        "hard_state": contract.get("hard_state") or {},
        "read_first_order": contract.get("read_first_order") or [],
        "public_newswire": {
            "aggregate_path": rel(aggregate_path),
            "background_process_path": rel(background_path),
            "aggregate_status": aggregate_status,
            "derived_runtime_status": derived_newswire_status,
            "progress_pct": aggregate.get("progress_pct"),
            "completed_units": aggregate.get("completed_units"),
            "pending_units": pending_units,
            "failed_units": failed_units,
            "partial_units": partial_units,
            "total_units": aggregate.get("total_units"),
            "launcher_pid": launcher.get("pid"),
            "launcher_pid_alive": launcher.get("alive"),
            "launcher_command_line_verified": command_matches,
            "active_worker_count": len(active_worker_rows),
            "active_worker_alive_count": active_worker_alive_count,
            "stale_worker_count": len(stale_workers),
            "by_source": by_source_summary(aggregate),
            "active_workers": active_worker_rows,
        },
        "active_worker_health": {
            "status": "PASS" if active_worker_alive_count > 0 or aggregate_status != "RUNNING" else "UNKNOWN_NO_ACTIVE_WORKER_ALIVE",
            "active_worker_count": len(active_worker_rows),
            "active_worker_alive_count": active_worker_alive_count,
            "affects_runtime_verdict": bool(aggregate_status == "RUNNING" and not launcher["alive"] and active_worker_alive_count == 0),
        },
        "historical_recycle_ledger": {
            "stale_workers_present": bool(stale_workers),
            "stale_worker_count": len(stale_workers),
            "affects_active_health": False,
        },
        "lanes": lane_statuses,
        "scheduler": {
            "realtime": scheduler,
            "backfill_recovery": recovery_scheduler,
        },
        "config_alignment": config_alignment,
        "reference_configs": reference_configs,
        "legacy_runtime_entrypoints": legacy,
        "deleted_legacy_entrypoints": deleted_legacy_entrypoints,
        "deleted_legacy_schedulers": contract.get("deleted_legacy_schedulers")
        or contract.get("superseded_schedulers")
        or [],
        "negative_evidence_conversion": 0,
        "broker_mutation_permitted_flag": 0,
        "live_order_permitted_flag": 0,
        "paper_promotion_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }

    out_root.mkdir(parents=True, exist_ok=True)
    status_path = out_root / "current_l0_status.json"
    context_path = out_root / "current_l0_context.md"
    manifest_path = out_root / "l0_operating_manifest.json"
    write_json(status_path, status)
    context_path.write_text(render_context(status), encoding="utf-8", newline="\n")
    manifest = {
        "schema_version": "l0_operating_manifest_v1",
        "task_id": contract.get("task_id") or TASK_ID,
        "generated_at": generated_at,
        "builder": rel(Path(__file__)),
        "validator": "scripts/validate_l0_operating_contract_4190.py",
        "inputs": sorted(set(inputs)),
        "outputs": [rel(status_path), rel(context_path), rel(manifest_path)],
        "overall_verdict": verdict,
        "blockers": blockers,
        "warnings": warnings,
    }
    write_json(manifest_path, manifest)
    return status


def render_context(status: dict[str, Any]) -> str:
    pn = status["public_newswire"]
    by_source = pn["by_source"]
    lines = [
        "# Current L0 Operating Context",
        "",
        f"- Generated at: {status['generated_at']}",
        f"- Task: {status['task_id']}",
        f"- Verdict: {status['overall_verdict']}",
        "- Strategy: NOT_ACCEPTED",
        "- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "- Real Capital: FORBIDDEN",
        "",
        "## Read This First",
    ]
    lines.extend(f"- {path}" for path in status.get("read_first_order", []))
    lines.extend([
        "",
        "## Public Newswire Backfill",
        f"- Aggregate status: {pn.get('aggregate_status')}",
        f"- Derived runtime status: {pn.get('derived_runtime_status')}",
        f"- Progress: {pn.get('progress_pct')}%",
        f"- Units: completed={pn.get('completed_units')} pending={pn.get('pending_units')} partial={pn.get('partial_units')} failed={pn.get('failed_units')} total={pn.get('total_units')}",
        f"- Launcher PID: {pn.get('launcher_pid')} alive={pn.get('launcher_pid_alive')} command_verified={pn.get('launcher_command_line_verified')}",
        f"- Active workers: recorded={pn.get('active_worker_count')} alive={pn.get('active_worker_alive_count')} stale={pn.get('stale_worker_count')}",
        "",
        "## Source Progress",
        "| source | status | completed | pending | partial | failed | rows |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for source, row in by_source.items():
        lines.append(
            f"| {source} | {row.get('status')} | {row.get('completed_units')} | {row.get('pending_units')} | "
            f"{row.get('partial_units')} | {row.get('failed_units')} | {row.get('row_count')} |"
        )
    lines.extend([
        "",
        "## Scheduler",
        f"- Realtime task: {status['scheduler']['realtime'].get('name')} exists={status['scheduler']['realtime'].get('exists')} status={status['scheduler']['realtime'].get('status')} last_result={status['scheduler']['realtime'].get('last_result')} classified={status['scheduler']['realtime'].get('last_result_status')}",
        f"- Continuous backfill guard: {status['scheduler']['backfill_recovery'].get('name')} exists={status['scheduler']['backfill_recovery'].get('exists')} status={status['scheduler']['backfill_recovery'].get('status')} last_result={status['scheduler']['backfill_recovery'].get('last_result')} classified={status['scheduler']['backfill_recovery'].get('last_result_status')}",
        "",
        "## Blockers",
    ])
    lines.extend(f"- {item}" for item in status.get("blockers", []) or ["none"])
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {item}" for item in status.get("warnings", []) or ["none"])
    lines.extend([
        "",
        "## Interpretation",
        "- aggregate_progress.json is progress evidence only. It is not runtime health by itself.",
        "- Missing or stale L0 data is UNKNOWN/BLOCKER, never negative evidence.",
        "- Deleted legacy entrypoints are intentionally absent; do not recreate or use them.",
        "- Reference configs may exist, but they are not current L0 runtime unless named under active_lanes.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    args = parser.parse_args()
    status = build_status(Path(args.contract), Path(args.out_root))
    print(json.dumps({
        "status_path": "data/artifacts/l0_operating_status/current_l0_status.json",
        "context_path": "data/artifacts/l0_operating_status/current_l0_context.md",
        "overall_verdict": status["overall_verdict"],
        "blockers": status["blockers"],
        "warnings": status["warnings"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
