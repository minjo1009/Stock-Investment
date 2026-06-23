"""Validate Task3855 read-only task registry recovery note artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3855_task_registry_recovery_note"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "task_registry_recovery_observations.csv",
    ARTIFACT_DIR / "task_registry_recovery_note_state.json",
    REPORT_DIR / "task_registry_recovery_note.md",
    REPORT_DIR / "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"missing file: {path}")
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    rows = read_csv(ARTIFACT_DIR / "task_registry_recovery_observations.csv")
    if len(rows) < 3:
        failures.append("registry recovery observations must include at least three rows")
    if not any(row.get("current_status") == "UNKNOWN/BLOCKER" for row in rows):
        failures.append("registry recovery note must preserve UNKNOWN/BLOCKER")

    state = json.loads((ARTIFACT_DIR / "task_registry_recovery_note_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_REGISTRY_RECOVERY_NOTE_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["registry_file_edited", "source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")

    report = (REPORT_DIR / "task_registry_recovery_note.md").read_text(encoding="utf-8")
    for phrase in ["does not edit tasks/task_registry.csv", "UNKNOWN/BLOCKER", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Task registry recovery note validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
