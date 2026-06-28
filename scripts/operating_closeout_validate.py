from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_FILES = [
    "docs/ownership/current_operating_model.md",
    "docs/ownership/readiness_registry.yaml",
    "docs/ownership/team_charter.md",
    "docs/ownership/module_ownership_map.md",
    "docs/acceptance/strategy_acceptance_contract.md",
    "docs/acceptance/deployment_acceptance_contract.md",
    "docs/operating_system/goal_operating_cycle.md",
    "docs/operating_system/work_closeout_protocol.md",
    "docs/graphify/graphify_cleanup_plan.md",
    "docs/INDEX.md",
    "validate_readiness_registry.py",
]

REQUIRED_CONTENT = {
    "docs/ownership/current_operating_model.md": [
        "Last updated:",
        "Strategy acceptance",
        "Paper operation",
        "Deployment readiness",
        "Every blocker must have an owner",
        "Graphify outputs in this repository were last generated",
        "Next Governance Action",
        "readiness_registry.yaml",
        "Task599",
    ],
    "docs/ownership/readiness_registry.yaml": [
        "program: T599_Strategy_Acceptance_Program",
        "status: READY_FOR_CONTROLLED_PAPER_RUN",
        "status: NOT_ACCEPTED",
        "target_status: ACCEPTANCE_REVIEW",
        "status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "blockers:",
        "program_level_acceptance_review:",
    ],
    "docs/ownership/team_charter.md": [
        "current_operating_model.md",
        "Named Leads",
        "Current Paper-Ops Standing",
        "Graphify outputs are discovery aids only",
    ],
    "docs/ownership/module_ownership_map.md": [
        "current_operating_model.md",
        "Current Operating Source",
        "주은 - Execution & Risk",
    ],
    "docs/acceptance/strategy_acceptance_contract.md": [
        "NOT_ACCEPTED",
        "ACCEPTANCE_REVIEW",
        "validate_readiness_registry.py",
        "Acceptance Review Entry Conditions",
        "Forbidden Claims",
    ],
    "docs/acceptance/deployment_acceptance_contract.md": [
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "Required Deployment Gates",
        "Immediate Deployment Fail Conditions",
        "validate_readiness_registry.py",
    ],
    "docs/operating_system/goal_operating_cycle.md": [
        "current_operating_model.md",
        "work_closeout_protocol.md",
        "validate_readiness_registry.py",
        "Do not infer a missing lead from team name alone",
    ],
    "docs/operating_system/work_closeout_protocol.md": [
        "Mandatory Closeout Checks",
        "Required Final Response Shape",
        "Minimum Validation",
        "python validate_readiness_registry.py",
        "python scripts/operating_closeout_validate.py",
    ],
    "docs/graphify/graphify_cleanup_plan.md": [
        "Current Validity",
        "stale for current paper-ops governance",
        "current_operating_model.md",
    ],
    "docs/INDEX.md": [
        "Read First",
        "Current operating model",
        "Readiness registry",
        "Strategy acceptance contract",
        "work_closeout_protocol.md",
        "Current Graphify outputs were generated on 2026-04-25",
    ],
    "validate_readiness_registry.py": [
        "REQUIRED_BLOCKER_FIELDS",
        "REQUIRED_ACCEPTANCE_GATES",
        "[READINESS_REGISTRY_OK]",
    ],
}


def _read(root: Path, relative_path: str) -> str:
    path = root / relative_path
    return path.read_text(encoding="utf-8")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if not path.exists():
            errors.append(f"missing required operating file: {relative_path}")
            continue
        text = _read(root, relative_path)
        for required in REQUIRED_CONTENT.get(relative_path, []):
            if required not in text:
                errors.append(f"{relative_path}: missing required text: {required}")
    cache_dir = root / "graphify-out" / "cache"
    if cache_dir.exists():
        stale_cache_count = sum(1 for item in cache_dir.iterdir() if item.is_file())
        if stale_cache_count:
            errors.append(
                "graphify-out/cache contains generated files; regenerate Graphify or clear stale cache"
            )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"[OPERATING_CLOSEOUT_ERROR] {error}")
        sys.exit(1)
    print("[OPERATING_CLOSEOUT_OK]")


if __name__ == "__main__":
    main()
