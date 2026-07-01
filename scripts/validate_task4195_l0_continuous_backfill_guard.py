from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_NAME = "TraderBrainL0ContinuousBackfillGuard4195"
SUPERSEDED_TASKS = [
    "TraderBrainL0BackfillWorkerRecovery4148",
    "Task3893OfficialBackfillAutoLoop",
    "Task3899FullOfficialBackfillWorker",
    "Task3899FullOfficialBackfillProgressReport",
]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_4195_l0_continuous_backfill_runtime_governance"
STATUS_PATH = ARTIFACT_DIR / "supervisor_status.json"
REGISTRATION_PATH = ARTIFACT_DIR / "windows_task_scheduler_registration.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return default


def as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def scheduler_query(name: str) -> dict[str, str]:
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", name, "/V", "/FO", "LIST"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if result.returncode != 0:
        return {"exists": "0", "stderr": result.stderr.strip()}
    row: dict[str, str] = {"exists": "1"}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        row[key.strip().lower().replace(" ", "_")] = value.strip()
    return row


def print_result(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    print("TASK-4195 CONTINUOUS L0 BACKFILL GUARD VALIDATION")
    for row in passes:
        print(f"PASS {row}")
    for row in warnings:
        print(f"WARN {row}")
    for row in failures:
        print(f"FAIL {row}")
    if failures:
        print("RESULT: FAIL")
        return 1
    if warnings:
        print("RESULT: PASS_WITH_WARNINGS")
    else:
        print("RESULT: PASS")
    return 0


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    registration = read_json(REGISTRATION_PATH, {})
    if as_int(registration.get("registered")) != 1:
        failures.append("TASK-4195 registration artifact does not prove scheduler registered")
    else:
        passes.append("registration artifact proves scheduler registered")

    scheduler = scheduler_query(TASK_NAME)
    if scheduler.get("exists") != "1":
        failures.append(f"{TASK_NAME} scheduler missing")
    else:
        passes.append(f"{TASK_NAME} scheduler exists")
        if scheduler.get("scheduled_task_state") != "Enabled":
            failures.append(f"{TASK_NAME} is not enabled: {scheduler.get('scheduled_task_state')}")
        else:
            passes.append(f"{TASK_NAME} enabled")
        last_result = scheduler.get("last_result")
        if last_result not in {"0", "267009"}:
            failures.append(f"{TASK_NAME} last result is not success/running: {last_result}")
        else:
            passes.append(f"{TASK_NAME} last_result acceptable: {last_result}")

    for task_name in SUPERSEDED_TASKS:
        superseded = scheduler_query(task_name)
        if superseded.get("exists") == "1" and superseded.get("scheduled_task_state") != "Disabled":
            warnings.append(f"{task_name} still exists and is not disabled")
        else:
            passes.append(f"{task_name} disabled_or_missing")

    status = read_json(STATUS_PATH, {})
    if not status:
        failures.append(f"missing continuous guard status: {STATUS_PATH}")
    else:
        passes.append("continuous guard status exists")
        for key in [
            ("public_newswire", "pid_alive"),
            ("public_market_macro_news", "pid_alive"),
            ("bars", "five_min_pid_alive"),
        ]:
            section, field = key
            value = as_int((status.get(section) or {}).get(field))
            if value != 1:
                failures.append(f"{section}.{field} is not alive")
            else:
                passes.append(f"{section}.{field}=1")
        safety = status.get("safety") or {}
        for field in [
            "trade_authority_flag",
            "broker_mutation_permitted_flag",
            "live_order_permitted_flag",
            "paper_promotion_permitted_flag",
            "real_capital_permitted_flag",
        ]:
            if as_int(safety.get(field)) != 0:
                failures.append(f"safety flag opened: {field}")
        if not any("safety flag opened" in item for item in failures):
            passes.append("safety flags closed")

    return print_result(passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())
