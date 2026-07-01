from __future__ import annotations

import argparse
import re
import sys

from ops_common import ROOT, artifact_manifest_files, get_task, load_yaml, print_result

sys.path.insert(0, str(ROOT))

from src.validation.prime_outcome_contract_validator import load_contract, validate_contract


DEFAULT_THRESHOLD = "TASK-4172"


def task_number(task_id: str) -> int:
    match = re.search(r"(\d+)$", task_id or "")
    return int(match.group(1)) if match else -1


def enforcement_threshold() -> int:
    registry = load_yaml("ops/task_registry.yaml")
    config = registry.get("prime_contract_enforcement") or {}
    return task_number(config.get("enabled_from_task_id") or DEFAULT_THRESHOLD)


def enforced(task: dict) -> bool:
    task_id = task.get("task_id") or ""
    return task_number(task_id) >= enforcement_threshold()


def contract_paths(task: dict) -> list[str]:
    return [
        path
        for path in task.get("required_artifacts", [])
        if path.replace("\\", "/").endswith("task_result_contract.yaml")
    ]


def validate_task(task: dict, passes: list[str], warnings: list[str], failures: list[str]) -> None:
    task_id = task.get("task_id")
    paths = contract_paths(task)
    if not paths:
        failures.append(f"{task_id} missing required task_result_contract.yaml artifact")
        return
    if len(paths) > 1:
        failures.append(f"{task_id} has multiple task_result_contract.yaml artifacts: {paths}")
        return

    contract_path = paths[0]
    full_path = ROOT / contract_path
    if not full_path.exists():
        failures.append(f"{task_id} contract file missing: {contract_path}")
        return

    manifest_files = artifact_manifest_files(task)
    if manifest_files and contract_path not in manifest_files:
        failures.append(f"{task_id} contract not listed in artifact_manifest.csv: {contract_path}")

    try:
        contract = load_contract(full_path)
    except Exception as exc:
        failures.append(f"{task_id} contract load failed: {exc}")
        return

    if contract.get("task_id") != task_id:
        failures.append(f"{task_id} contract.task_id mismatch: {contract.get('task_id')}")

    validation = validate_contract(contract)
    if validation["status"] != "PASS":
        failures.append(f"{task_id} contract validation failed: {validation['failures']}")
    else:
        passes.append(f"{task_id} prime contract valid: {contract_path}")
    warnings.extend(f"{task_id}: {warning}" for warning in validation.get("warnings", []))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    if args.task:
        try:
            tasks = [get_task(args.task)]
        except Exception as exc:
            return print_result("PRIME TASK CONTRACT VALIDATION", [], [], [str(exc)])
    else:
        tasks = load_yaml("ops/task_registry.yaml").get("tasks", [])

    checked = 0
    for task in tasks:
        if not enforced(task):
            continue
        checked += 1
        validate_task(task, passes, warnings, failures)

    passes.append(f"enforced_tasks_checked: {checked}")
    return print_result("PRIME TASK CONTRACT VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
