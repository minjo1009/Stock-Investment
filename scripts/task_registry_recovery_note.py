"""Build Task3855 read-only task registry recovery note artifacts."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3855_task_registry_recovery_note"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID
REGISTRY_PATH = Path("tasks/task_registry.csv")

RECOVERY_PATH = ARTIFACT_DIR / "task_registry_recovery_observations.csv"
STATE_PATH = ARTIFACT_DIR / "task_registry_recovery_note_state.json"
REPORT_PATH = REPORT_DIR / "task_registry_recovery_note.md"
MANIFEST_PATH = REPORT_DIR / "artifact_manifest.csv"

HARD_STATE = {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git_status_for(path: str) -> str:
    completed = subprocess.run(["git", "status", "--short", "--", path], check=True, capture_output=True, text=True)
    return completed.stdout.strip() or "clean"


def read_registry_tail(limit: int = 10) -> list[str]:
    if not REGISTRY_PATH.exists():
        return []
    lines = REGISTRY_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-limit:]


def build_observations() -> list[dict[str, str]]:
    exists = REGISTRY_PATH.exists()
    status = git_status_for(str(REGISTRY_PATH))
    tail = read_registry_tail()
    return [
        {
            "observation_id": "registry_recovery_001",
            "area": "registry_file",
            "evidence": f"exists={str(exists).lower()} status={status}",
            "current_status": "UNKNOWN/BLOCKER" if status != "clean" else "PRESENT",
            "recommended_action": "DO_NOT_AUTO_MERGE_DIRTY_REGISTRY",
            "notes": "Registry changes require a focused recovery task because unrelated local edits are present.",
        },
        {
            "observation_id": "registry_recovery_002",
            "area": "registry_tail",
            "evidence": f"tail_line_count={len(tail)}",
            "current_status": "DIAGNOSTIC_ONLY",
            "recommended_action": "REVIEW_TAIL_BEFORE_CANONICAL_ROWS",
            "notes": "Tail was read only to support recovery planning; no row was added.",
        },
        {
            "observation_id": "registry_recovery_003",
            "area": "new_task_rows",
            "evidence": "tasks_3846_3855_reports_generated_as_isolated_artifacts",
            "current_status": "UNKNOWN/BLOCKER",
            "recommended_action": "ADD_ROWS_AFTER_REGISTRY_CLEANUP",
            "notes": "Current run avoids mutating the registry while it is already dirty.",
        },
    ]


def build_manifest() -> list[dict[str, str]]:
    return [
        {"artifact_path": str(RECOVERY_PATH), "artifact_type": "csv", "authority": "diagnostic", "status": "generated", "notes": "read-only registry recovery observations"},
        {"artifact_path": str(STATE_PATH), "artifact_type": "json", "authority": "diagnostic", "status": "generated", "notes": "hard-state guardrail summary"},
        {"artifact_path": str(REPORT_PATH), "artifact_type": "markdown", "authority": "diagnostic", "status": "generated", "notes": "task recovery note"},
    ]


def write_report(state: dict[str, Any], observations: list[dict[str, str]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task3855 Task Registry Recovery Note",
        "",
        "## Summary",
        "- [actual] This task generated a read-only registry recovery note.",
        "- [actual] It does not edit tasks/task_registry.csv because the file has unrelated local state.",
        "- [actual] Registry continuity remains UNKNOWN/BLOCKER until a focused recovery task reconciles rows.",
        "",
        "## Hard State",
        f"- Strategy: {state['strategy']}",
        f"- Deployment: {state['deployment']}",
        f"- Real capital: {state['real_capital']}",
        "",
        "## Observations",
    ]
    lines.extend(f"- {row['observation_id']}: {row['current_status']} / {row['recommended_action']}" for row in observations)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    observations = build_observations()
    state = {
        "task_id": TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_REGISTRY_RECOVERY_NOTE_COMPLETE_WITH_BLOCKERS",
        "observation_row_count": len(observations),
        "registry_file_edited": False,
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }
    write_csv(RECOVERY_PATH, observations, ["observation_id", "area", "evidence", "current_status", "recommended_action", "notes"])
    write_json(STATE_PATH, state)
    write_report(state, observations)
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
