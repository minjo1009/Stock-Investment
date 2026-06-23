"""Validate Task3847 read-only source freshness blocker taxonomy artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3847_source_freshness_blocker_taxonomy"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "freshness_blocker_taxonomy.csv",
    ARTIFACT_DIR / "strict_proxy_gate_matrix.csv",
    ARTIFACT_DIR / "source_family_blocker_summary.csv",
    ARTIFACT_DIR / "source_freshness_blocker_taxonomy_state.json",
    REPORT_DIR / "source_freshness_blocker_taxonomy_report.md",
    REPORT_DIR / "artifact_manifest.csv",
]

FORBIDDEN_TOKENS = [
    "insert into",
    "update ",
    "delete from",
    "submit_order",
    "cancel_order",
    "replace_order",
    "broker.submit",
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

    taxonomy_rows = read_csv(ARTIFACT_DIR / "freshness_blocker_taxonomy.csv")
    gate_rows = read_csv(ARTIFACT_DIR / "strict_proxy_gate_matrix.csv")
    summary_rows = read_csv(ARTIFACT_DIR / "source_family_blocker_summary.csv")
    if len(taxonomy_rows) != 12:
        failures.append("taxonomy must contain the 12 Task3845 source families")
    if len(gate_rows) != 24:
        failures.append("gate matrix must contain strict and proxy rows for each source family")
    if not summary_rows:
        failures.append("summary rows are empty")
    if any(row.get("permission_inference_allowed") != "false" for row in gate_rows):
        failures.append("permission inference must be false for every gate row")
    if not any(row.get("severity") == "P0_BLOCKER" for row in taxonomy_rows):
        failures.append("taxonomy must preserve P0 blocker rows")
    if any(row.get("current_decision") != "BLOCKED_DIAGNOSTIC_ONLY" for row in summary_rows):
        failures.append("source family decisions must remain blocked diagnostic only")

    state = json.loads((ARTIFACT_DIR / "source_freshness_blocker_taxonomy_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_FRESHNESS_TAXONOMY_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in [
        "source_acquisition_run",
        "scheduler_run",
        "db_mutation",
        "broker_mutation_added",
        "paper_live_permission_granted",
        "real_capital_permission_granted",
    ]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")

    report = (REPORT_DIR / "source_freshness_blocker_taxonomy_report.md").read_text(encoding="utf-8")
    for phrase in [
        "UNKNOWN/BLOCKER",
        "No strict/proxy gate is opened",
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
    ]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/source_freshness_blocker_taxonomy.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden token: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Source freshness blocker taxonomy validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
