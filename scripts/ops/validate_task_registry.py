from __future__ import annotations

import sys
import re

from ops_common import load_yaml, print_result


REQUIRED_FIELDS = {
    "task_id",
    "title",
    "status",
    "priority",
    "task_type",
    "profile",
    "allowed_paths",
    "forbidden_paths",
    "required_artifacts",
    "required_validators",
}

STATUS_ENUM = {"BACKLOG", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE", "CANCELLED"}
PRIORITY_ENUM = {"P0", "P1", "P2", "P3"}


def task_number(task_id: str) -> int:
    match = re.search(r"(\d+)$", task_id or "")
    return int(match.group(1)) if match else -1


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        registry = load_yaml("ops/task_registry.yaml")
        profiles = load_yaml("ops/task_profiles.yaml").get("profiles", {})
    except Exception as exc:
        return print_result("TASK REGISTRY VALIDATION", [], [], [str(exc)])

    for key in ["version", "updated_at", "tasks"]:
        if key not in registry:
            failures.append(f"missing root key: {key}")
    tasks = registry.get("tasks", [])
    if not isinstance(tasks, list):
        failures.append("tasks must be a list")
        tasks = []
    else:
        passes.append(f"tasks: {len(tasks)}")

    seen: set[str] = set()
    resolved = 0
    for idx, task in enumerate(tasks):
        label = task.get("task_id") or f"index {idx}"
        missing = sorted(REQUIRED_FIELDS - set(task.keys()))
        if missing:
            failures.append(f"{label} missing fields: {', '.join(missing)}")
        task_id = task.get("task_id")
        if task_id in seen:
            failures.append(f"duplicate task_id: {task_id}")
        if task_id:
            seen.add(task_id)
        if task.get("status") not in STATUS_ENUM:
            failures.append(f"{label} invalid status: {task.get('status')}")
        if task.get("priority") not in PRIORITY_ENUM:
            failures.append(f"{label} invalid priority: {task.get('priority')}")
        profile = task.get("profile")
        if profile not in profiles:
            failures.append(f"{label} unknown profile: {profile}")
        else:
            resolved += 1
        for list_key in ["allowed_paths", "forbidden_paths", "required_artifacts", "required_validators"]:
            if list_key in task and not isinstance(task.get(list_key), list):
                failures.append(f"{label} {list_key} must be a list")

    prime_config = registry.get("prime_contract_enforcement") or {}
    if prime_config.get("enabled") is True:
        threshold = task_number(prime_config.get("enabled_from_task_id") or "TASK-4172")
        for task in tasks:
            task_id = task.get("task_id") or ""
            if task_number(task_id) < threshold:
                continue
            artifacts = task.get("required_artifacts") or []
            validators = task.get("required_validators") or []
            if not any(str(path).replace("\\", "/").endswith("task_result_contract.yaml") for path in artifacts):
                failures.append(f"{task_id} missing Prime task_result_contract.yaml required artifact")
            expected_validator = f"python scripts/ops/validate_prime_task_contracts.py --task {task_id}"
            if expected_validator not in validators:
                failures.append(f"{task_id} missing Prime contract validator: {expected_validator}")

    if "TASK-4100" not in seen:
        failures.append("TASK-4100 missing")
    else:
        passes.append("TASK-4100 exists")
    passes.append(f"profiles_resolved: {resolved}")
    if not any("missing fields" in failure for failure in failures):
        passes.append("required_fields")

    return print_result("TASK REGISTRY VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
