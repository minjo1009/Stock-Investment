"""Validate Task3851 read-only kill-switch clearance checklist artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3851_kill_switch_clearance_checklist"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "kill_switch_clearance_checklist.csv",
    ARTIFACT_DIR / "kill_switch_blocker_trace.csv",
    ARTIFACT_DIR / "kill_switch_clearance_checklist_state.json",
    REPORT_DIR / "kill_switch_clearance_checklist_report.md",
    REPORT_DIR / "artifact_manifest.csv",
]

FORBIDDEN_TOKENS = ["insert into", "update ", "delete from", "submit_order", "broker.submit"]


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
    checklist_rows = read_csv(ARTIFACT_DIR / "kill_switch_clearance_checklist.csv")
    trace_rows = read_csv(ARTIFACT_DIR / "kill_switch_blocker_trace.csv")
    if not checklist_rows:
        failures.append("checklist rows are empty")
    if not trace_rows:
        failures.append("trace rows are empty")
    if any(row.get("clearance_allowed_now") != "false" for row in checklist_rows + trace_rows):
        failures.append("clearance must be false for every row")
    if any(row.get("control_state_mutation_allowed") != "false" for row in checklist_rows):
        failures.append("control state mutation must be false for every checklist row")

    state = json.loads((ARTIFACT_DIR / "kill_switch_clearance_checklist_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_KILL_SWITCH_CHECKLIST_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")

    report = (REPORT_DIR / "kill_switch_clearance_checklist_report.md").read_text(encoding="utf-8")
    for phrase in ["does not clear", "Kill switch remains uncleared", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/kill_switch_clearance_checklist.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden token: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Kill-switch clearance checklist validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
