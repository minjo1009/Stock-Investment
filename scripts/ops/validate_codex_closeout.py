from __future__ import annotations

import argparse
import shlex
import sys
import shutil

from ops_common import ROOT, context_config, get_task, print_result, run_command


MANAGED_CACHE_ROOTS = [
    ".codex",
    "apps",
    "configs",
    "docs",
    "frontend",
    "ops",
    "schemas",
    "scripts",
    "src",
    "tasks",
    "tests",
    "tools",
]


def has_context_bundle(task_id: str) -> bool:
    try:
        return any(bundle.get("task_id") == task_id for bundle in context_config().get("bundles", {}).values())
    except Exception:
        return False


def remove_managed_pycache() -> None:
    for root_name in MANAGED_CACHE_ROOTS:
        scan_root = ROOT / root_name
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("__pycache__"), key=lambda item: len(item.parts), reverse=True):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    try:
        task = get_task(args.task)
    except Exception as exc:
        return print_result("CODEX CLOSEOUT VALIDATION", [], [], [str(exc)])

    commands = [
        "python scripts/ops/validate_task_registry.py",
        "python scripts/ops/validate_doc_registry.py --soft",
        "python scripts/ops/validate_project_hygiene.py",
        "python scripts/ops/validate_project_structure_policy.py",
        "python scripts/ops/validate_knowledge_surfaces.py",
        "python scripts/ops/validate_internal_cleanliness.py",
        f"python scripts/ops/validate_prime_task_contracts.py --task {args.task}",
        f"python scripts/ops/validate_task_scope.py --task {args.task}",
        f"python scripts/ops/validate_required_artifacts.py --task {args.task}",
    ]
    if has_context_bundle(args.task):
        commands.insert(2, f"python scripts/ops/validate_context_bundle.py --task {args.task}")
    for command in task.get("required_validators", []):
        normalized = command.strip()
        if normalized.startswith("python scripts/ops/validate_codex_closeout.py"):
            continue
        if command not in commands:
            commands.append(command)
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    for command in commands:
        if "validate_internal_cleanliness.py" in command:
            remove_managed_pycache()
        code, output = run_command(shlex.split(command))
        if code == 0:
            if "RESULT: PASS_WITH_WARNINGS" in output:
                warnings.append(f"{command}: PASS_WITH_WARNINGS")
            else:
                passes.append(f"{command}: PASS")
        else:
            failures.append(f"{command}: FAIL\n{output.strip()}")

    closeout = task.get("closeout", {})
    required_flags = [
        "registry_updated",
        "doc_registry_updated",
        "validators_passed",
        "artifact_manifest_exists",
        "forbidden_paths_clean",
    ]
    for flag in required_flags:
        if closeout.get(flag) is True:
            passes.append(f"closeout.{flag}: true")
        else:
            failures.append(f"closeout.{flag} is not true")

    if task.get("status") == "DONE" and failures:
        failures.append("task is DONE but closeout conditions failed")

    return print_result("CODEX CLOSEOUT VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
