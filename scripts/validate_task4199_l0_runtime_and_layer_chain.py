from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4199"
ARTIFACT = ROOT / "data/artifacts/task_4199_l0_scheduler_deletion_and_l0_l5_integration_audit"
EXPECTED_ACTIVE = {
    "TraderBrainL0ContinuousBackfillGuard4195": "PT5M",
    "TraderBrainL0L2Hardening4147": "PT15M",
}
DELETED_SCHEDULERS = {
    "TraderBrainL0BackfillWorkerRecovery4148",
    "Task3893OfficialBackfillAutoLoop",
    "Task3899FullOfficialBackfillWorker",
    "Task3899FullOfficialBackfillProgressReport",
}
DELETED_ENTRYPOINTS = [
    "scripts/start_l0_public_newswire_backfill.ps1",
    "scripts/start_l0_public_newswire_collector.ps1",
    "scripts/start_l0_prioritized_backfills.ps1",
    "scripts/run_l0_backfill_worker_recovery_4148.py",
    "scripts/run_l0_backfill_supervisor.ps1",
    "data/artifacts/l0_public_newswire_backfill/background_process.json",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def query_task(name: str) -> dict[str, Any]:
    script = (
        f"$task=Get-ScheduledTask -TaskName '{name}' -ErrorAction SilentlyContinue;"
        "if($task){"
        f"$info=Get-ScheduledTaskInfo -TaskName '{name}';"
        "$action=$task.Actions|Select-Object -First 1;"
        "$trigger=$task.Triggers|Select-Object -First 1;"
        "[pscustomobject]@{"
        "exists=$true;"
        "task_name=$task.TaskName;"
        "state=[string]$task.State;"
        "last_result=[string]$info.LastTaskResult;"
        "execute=[string]$action.Execute;"
        "arguments=[string]$action.Arguments;"
        "repetition_interval=if($trigger -and $trigger.Repetition){[string]$trigger.Repetition.Interval}else{''}"
        "}|ConvertTo-Json -Compress"
        "}else{[pscustomobject]@{exists=$false;task_name='"
        + name
        + "'}|ConvertTo-Json -Compress}"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return {"exists": False, "task_name": name, "error": proc.stderr.strip()}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"exists": False, "task_name": name, "error": str(exc)}
    return data if isinstance(data, dict) else {}


def fail_or_pass(condition: bool, message: str, passes: list[str], failures: list[str]) -> None:
    (passes if condition else failures).append(message)


def build_report() -> dict[str, Any]:
    passes: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []

    active_tasks = {name: query_task(name) for name in EXPECTED_ACTIVE}
    deleted_tasks = {name: query_task(name) for name in DELETED_SCHEDULERS}
    all_actions = " ".join(
        (str(row.get("execute") or "") + " " + str(row.get("arguments") or ""))
        for row in active_tasks.values()
    ).replace("\\", "/")

    for name, interval in EXPECTED_ACTIVE.items():
        row = active_tasks[name]
        fail_or_pass(bool(row.get("exists")), f"active scheduler exists: {name}", passes, failures)
        fail_or_pass(str(row.get("last_result")) == "0", f"active scheduler last result success: {name}", passes, failures)
        actual_interval = str(row.get("repetition_interval") or "")
        fail_or_pass(actual_interval == interval, f"active scheduler interval {name}={interval}", passes, failures)

    for name, row in deleted_tasks.items():
        fail_or_pass(not bool(row.get("exists")), f"legacy scheduler deleted: {name}", passes, failures)

    for path in DELETED_ENTRYPOINTS:
        exists = (ROOT / path).exists()
        fail_or_pass(not exists, f"deleted legacy entrypoint absent: {path}", passes, failures)
        fail_or_pass(path.replace("\\", "/") not in all_actions, f"active scheduler does not reference deleted entrypoint: {path}", passes, failures)

    fail_or_pass("configs/db_source_acquisition_scheduler.json" not in all_actions, "reference config is not directly scheduled", passes, failures)

    l0 = read_json(ROOT / "data/artifacts/l0_operating_status/current_l0_status.json")
    fail_or_pass(l0.get("task_id") == TASK_ID, "current L0 context task_id is TASK-4199", passes, failures)
    pn = l0.get("public_newswire") or {}
    partial = bool((pn.get("pending_units") or 0) or (pn.get("partial_units") or 0))
    if partial:
        fail_or_pass("L0_PUBLIC_NEWSWIRE_INCOMPLETE" in (l0.get("blockers") or []), "partial L0 is explicitly blocked", passes, failures)
    fail_or_pass((l0.get("historical_recycle_ledger") or {}).get("affects_active_health") is False, "stale workers are separated from active health", passes, failures)

    chain = read_json(ARTIFACT / "layer_watermarks/layer_refresh_chain.json")
    fail_or_pass(bool(chain), "layer_refresh_chain exists", passes, failures)
    fail_or_pass((chain.get("safety") or {}).get("broker_mutation") == 0, "chain broker mutation closed", passes, failures)
    fail_or_pass((chain.get("safety") or {}).get("live_order") == 0, "chain live order closed", passes, failures)
    fail_or_pass((chain.get("safety") or {}).get("paper_promotion") == 0, "chain paper promotion closed", passes, failures)

    l0_layer = next((row for row in chain.get("layers", []) if row.get("layer") == "L0"), {})
    if partial:
        fail_or_pass(l0_layer.get("status") == "PARTIAL_RUNNING", "L0 watermark is PARTIAL_RUNNING", passes, failures)
        for row in chain.get("layers", []):
            if row.get("layer") == "L0":
                continue
            fail_or_pass(
                row.get("status") in {"BLOCKED_BY_L0_INCOMPLETE", "STALE_VS_L0_WATERMARK"},
                f"{row.get('layer')} does not claim full freshness while L0 partial",
                passes,
                failures,
            )
            fail_or_pass(
                not bool((row.get("authority") or {}).get("complete_source_coverage_claim")),
                f"{row.get('layer')} complete source coverage claim closed",
                passes,
                failures,
            )

    report = {
        "task_id": TASK_ID,
        "status": "PASS" if not failures else "FAIL",
        "runtime_status": "L0_RUNTIME_CLEAN_WITH_PARTIAL_COLLECTION" if not failures and partial else "L0_RUNTIME_CLEAN",
        "passes": passes,
        "warnings": warnings,
        "failures": failures,
        "active_tasks": active_tasks,
        "deleted_tasks": deleted_tasks,
    }
    out_json = ARTIFACT / "runtime_and_layer_chain_validation.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report)
    return report


def write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# TASK-4199 Runtime And Layer Chain Validation",
        "",
        f"- Status: {report['status']}",
        f"- Runtime status: {report['runtime_status']}",
        "",
        "## Failures",
    ]
    lines.extend(f"- {item}" for item in report["failures"] or ["none"])
    lines.append("")
    lines.append("## Passes")
    lines.extend(f"- {item}" for item in report["passes"])
    lines.extend([
        "",
        "Strategy remains NOT_ACCEPTED.",
        "Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
        "Real capital remains FORBIDDEN.",
    ])
    (ARTIFACT / "runtime_and_layer_chain_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = build_report()
    print(json.dumps({"task_id": TASK_ID, "status": report["status"], "runtime_status": report["runtime_status"]}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
