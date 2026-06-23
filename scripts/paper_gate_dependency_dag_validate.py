"""Validate Task3852 read-only paper gate dependency DAG artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3852_paper_gate_dependency_dag"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "paper_gate_dependency_nodes.csv",
    ARTIFACT_DIR / "paper_gate_dependency_edges.csv",
    ARTIFACT_DIR / "paper_gate_dependency_dag_state.json",
    REPORT_DIR / "paper_gate_dependency_dag_report.md",
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
    nodes = read_csv(ARTIFACT_DIR / "paper_gate_dependency_nodes.csv")
    edges = read_csv(ARTIFACT_DIR / "paper_gate_dependency_edges.csv")
    if not any(row.get("node_id") == "paper_gate_root" and row.get("status") == "BLOCKED" for row in nodes):
        failures.append("paper gate root must remain blocked")
    if any(row.get("permission_granted") != "false" for row in nodes):
        failures.append("permission granted must be false for every node")
    if any(row.get("inference_allowed") != "false" for row in edges):
        failures.append("inference must be false for every edge")
    if any(row.get("weakest_link_blocks_root") != "true" for row in edges):
        failures.append("every edge must block the root")

    state = json.loads((ARTIFACT_DIR / "paper_gate_dependency_dag_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_PAPER_GATE_DAG_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")

    report = (REPORT_DIR / "paper_gate_dependency_dag_report.md").read_text(encoding="utf-8")
    for phrase in ["does not grant paper/live permission", "UNKNOWN/BLOCKER", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/paper_gate_dependency_dag.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden token: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Paper gate dependency DAG validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
