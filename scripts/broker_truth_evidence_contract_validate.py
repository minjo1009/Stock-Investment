"""Validate Task3850 read-only broker truth evidence contract artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3850_broker_truth_evidence_contract"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "broker_truth_evidence_contract.csv",
    ARTIFACT_DIR / "broker_truth_gap_trace.csv",
    ARTIFACT_DIR / "broker_truth_evidence_contract_state.json",
    REPORT_DIR / "broker_truth_evidence_contract_report.md",
    REPORT_DIR / "artifact_manifest.csv",
]

FORBIDDEN_TOKENS = ["insert into", "update ", "delete from", "submit_order", "cancel_order", "replace_order", "broker.submit"]


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
    contract_rows = read_csv(ARTIFACT_DIR / "broker_truth_evidence_contract.csv")
    gap_rows = read_csv(ARTIFACT_DIR / "broker_truth_gap_trace.csv")
    if len(contract_rows) < 5:
        failures.append("contract must contain at least five evidence domains")
    if not gap_rows:
        failures.append("gap trace must not be empty")
    if any(row.get("broker_call_allowed") != "false" for row in contract_rows):
        failures.append("broker call must be false for every contract row")
    if any(row.get("authority_claim_allowed") != "false" for row in contract_rows):
        failures.append("authority claim must be false for every contract row")
    if any(row.get("blocked_for_paper") != "true" for row in gap_rows):
        failures.append("gap trace rows must remain blocked for paper")

    state = json.loads((ARTIFACT_DIR / "broker_truth_evidence_contract_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_BROKER_TRUTH_CONTRACT_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")

    report = (REPORT_DIR / "broker_truth_evidence_contract_report.md").read_text(encoding="utf-8")
    for phrase in ["No broker API call", "No local order rows", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/broker_truth_evidence_contract.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden token: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Broker truth evidence contract validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
