"""Validate Task3853 read-only native iOS operator evidence checklist artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3853_native_ios_operator_evidence_checklist"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "native_ios_operator_evidence_checklist.csv",
    ARTIFACT_DIR / "native_ios_evidence_trace.csv",
    ARTIFACT_DIR / "native_ios_operator_evidence_checklist_state.json",
    REPORT_DIR / "native_ios_operator_evidence_checklist_report.md",
    REPORT_DIR / "artifact_manifest.csv",
]

FORBIDDEN_TOKENS = ["eas build", "expo run:ios", "xcrun", "simctl install", "submit_order", "broker.submit", "insert into", "delete from"]


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

    checklist = read_csv(ARTIFACT_DIR / "native_ios_operator_evidence_checklist.csv")
    if len(checklist) < 5:
        failures.append("checklist must include at least five evidence rows")
    if any(row.get("current_status") != "UNKNOWN/BLOCKER" for row in checklist):
        failures.append("all checklist rows must remain UNKNOWN/BLOCKER")
    if any(row.get("permission_granted") != "false" for row in checklist):
        failures.append("permission_granted must be false")

    state = json.loads((ARTIFACT_DIR / "native_ios_operator_evidence_checklist_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_NATIVE_IOS_OPERATOR_EVIDENCE_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["ios_build_run", "device_install_run", "source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")

    report = (REPORT_DIR / "native_ios_operator_evidence_checklist_report.md").read_text(encoding="utf-8")
    for phrase in ["UNKNOWN/BLOCKER", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/native_ios_operator_evidence_checklist.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden runtime token: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Native iOS operator evidence checklist validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
