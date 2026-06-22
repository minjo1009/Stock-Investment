#!/usr/bin/env python
"""Validate the Task3181-3190 brain/code operating loop surfaces.

This is a governance/package/reporting surface check. It does not run replay,
submit orders, acquire sources, or mutate broker/runtime state.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3181_3190_brain_code_operating_loop"


REQUIRED_FILES = [
    "docs/operating_system/brain_code_operating_loop.md",
    "docs/contracts/brain_runtime_contract.md",
    "src/brain/__init__.py",
    "src/brain/contracts.py",
    "src/brain/runtime_catalog.py",
    "tests/test_brain_runtime_contracts.py",
    "tests/test_brain_runtime_catalog_adapter.py",
    "scripts/trader_brain_3164_runtime_catalog_adapter_validate.py",
    "docs/reports/task_3181_3190_brain_code_operating_loop/task_3181_3190_brain_code_operating_loop.md",
    "docs/reports/task_3181_3190_brain_code_operating_loop/artifact_manifest.csv",
]

LOOP_TASKS = [f"Task{task_id}" for task_id in range(3181, 3191)]

FORBIDDEN_STATUS_CLAIMS = [
    "strategy accepted",
    "deployment ready",
    "real capital allowed",
    "broker truth complete",
]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _exists(relative_path: str) -> bool:
    return (ROOT / relative_path).exists()


def _contains(relative_path: str, needle: str) -> bool:
    path = ROOT / relative_path
    return path.exists() and needle in path.read_text(encoding="utf-8")


def build_checks() -> list[dict[str, str | int]]:
    registry = _read("tasks/task_registry.csv")
    operating_state = _read("docs/operating_system/project_operating_state.md")
    runbook = _read("docs/operating_system/brain_code_operating_loop.md")
    brain_init = _read("src/brain/__init__.py")
    contracts = _read("src/brain/contracts.py")
    adapter = _read("src/brain/runtime_catalog.py")
    llm_wiki = _read("docs/llm_wiki/README.md")
    obsidian_home = _read("docs/obsidian/Vault Home.md")

    checks: list[dict[str, str | int]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "pass": int(passed), "detail": detail})

    add(
        "required_files_present",
        all(_exists(path) for path in REQUIRED_FILES),
        f"required_files={len(REQUIRED_FILES)}",
    )
    add(
        "ten_loop_tasks_registered",
        all(task_id in registry for task_id in LOOP_TASKS),
        "|".join(LOOP_TASKS),
    )
    add(
        "ten_loop_tasks_in_operating_state",
        "Task3181-Task3190" in operating_state,
        "Task3181-Task3190 operating state entry",
    )
    add(
        "runbook_preserves_status_boundaries",
        all(term in runbook for term in ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]),
        "standing boundaries",
    )
    add(
        "brain_exports_are_contract_only",
        "build_frontend_read_model_from_paper_ops_catalog" in brain_init
        and "submit_order" not in brain_init
        and "run_replay" not in brain_init,
        "src/brain/__init__.py",
    )
    add(
        "contracts_forbid_assignment_and_order_leakage",
        "outcome fields are forbidden" in contracts
        and "cannot create order intent directly" in contracts
        and "live order permission is forbidden" in contracts,
        "src/brain/contracts.py",
    )
    add(
        "runtime_adapter_is_read_only",
        "does not call the catalog builder" in adapter
        and "read_only=True" in adapter
        and "deployment claims" in adapter,
        "src/brain/runtime_catalog.py",
    )
    add(
        "navigation_layers_link_runbook",
        "brain_code_operating_loop.md" in llm_wiki and "brain_code_operating_loop.md" in obsidian_home,
        "LLM wiki and Obsidian navigation",
    )
    add(
        "registry_rows_keep_diagnostic_status",
        all(
            f"{task_id},Brain Code Operating Loop" in registry
            and f"{task_id},Brain Code Operating Loop" in registry
            for task_id in LOOP_TASKS
        )
        and registry.count("brain-code-operating-loop-no-trading-logic-change") >= 10,
        "diagnostic rows for Task3181-Task3190",
    )
    lowered = "\n".join([runbook, registry, operating_state]).lower()
    add(
        "no_forbidden_status_claims",
        not any(claim in lowered for claim in FORBIDDEN_STATUS_CLAIMS),
        "no acceptance/deployment/real-capital overclaim",
    )

    return checks


def main() -> int:
    checks = build_checks()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ARTIFACT_DIR / "brain_code_operating_loop_validation.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_name", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3181_3190_ERROR] {row['check_name']}: {row['detail']}")
        return 1

    print(f"[TASK3181_3190_OK] checks={len(checks)} output={output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

