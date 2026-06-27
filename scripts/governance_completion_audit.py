from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.codeowners_coverage_validate import validate as validate_codeowners
from scripts.active_task_registry_validate import validate_active_registry
from scripts.operating_closeout_validate import validate as validate_operating_closeout
from scripts.task_registry_validate import validate_registry
from validate_readiness_registry import validate as validate_readiness_registry


REQUIRED_FILES = [
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/research_task.yml",
    ".github/ISSUE_TEMPLATE/data_source_task.yml",
    ".github/ISSUE_TEMPLATE/data_integrity_bug.yml",
    ".github/ISSUE_TEMPLATE/refactor_infra_task.yml",
    "docs/ownership/team_charter.md",
    "docs/ownership/current_operating_model.md",
    "docs/ownership/readiness_registry.yaml",
    "docs/ownership/subagent_packet_standard.md",
    "docs/acceptance/strategy_acceptance_contract.md",
    "docs/acceptance/deployment_acceptance_contract.md",
    "docs/operating_system/goal_operating_cycle.md",
    "docs/operating_system/work_closeout_protocol.md",
    "docs/active/README_ACTIVE.md",
    "docs/active/PROJECT_STATUS.md",
    "docs/active/ACTIVE_SSOT_INDEX.md",
    "docs/active/CODEX_READ_SCOPE.md",
    "docs/active/CURRENT_TASKS.md",
    "docs/artifact_policy.md",
    "docs/report_standard.md",
    "docs/frontend_data_contract.md",
    "docs/architecture/github_project_operating_model.md",
    "tasks/task_registry.csv",
    "tasks/active_task_registry.csv",
    "tasks/archive_candidate_registry.csv",
    "validate_readiness_registry.py",
]

CANONICAL_MANIFEST_TASKS = [
    "task_493_microstructure_enhanced_continuation_grid",
    "task_495_microstructure_live_source_readiness",
]


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    for file_name in REQUIRED_FILES:
        if not (root / file_name).exists():
            errors.append(f"missing required governance file: {file_name}")
    errors.extend(validate_registry(root / "tasks" / "task_registry.csv", root=root))
    errors.extend(validate_active_registry(root / "tasks" / "active_task_registry.csv", root=root))
    errors.extend(validate_codeowners(root / ".github" / "CODEOWNERS"))
    errors.extend(validate_operating_closeout(root))
    errors.extend(validate_readiness_registry(root / "docs" / "ownership" / "readiness_registry.yaml"))
    for task in CANONICAL_MANIFEST_TASKS:
        manifest = root / "docs" / "reports" / task / "artifact_manifest.csv"
        if not manifest.exists():
            errors.append(f"missing canonical artifact manifest: {manifest}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = audit(args.root)
    if errors:
        for error in errors:
            print(f"[GOVERNANCE_ERROR] {error}")
        sys.exit(1)
    print("[GOVERNANCE_COMPLETE]")


if __name__ == "__main__":
    main()
