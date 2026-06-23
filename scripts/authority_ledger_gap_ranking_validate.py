"""Validate Task3849 read-only authority ledger gap ranking artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3849_authority_ledger_gap_ranking"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "authority_ledger_gap_rank.csv",
    ARTIFACT_DIR / "evidence_layer_separation_matrix.csv",
    ARTIFACT_DIR / "authority_ledger_gap_ranking_state.json",
    REPORT_DIR / "authority_ledger_gap_ranking_report.md",
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

    gap_rows = read_csv(ARTIFACT_DIR / "authority_ledger_gap_rank.csv")
    layer_rows = read_csv(ARTIFACT_DIR / "evidence_layer_separation_matrix.csv")
    if len(gap_rows) != 12:
        failures.append("gap rank must contain the 12 Task3845 source families")
    if len(layer_rows) != 72:
        failures.append("layer matrix must contain 6 layers for each source family")
    if any(row.get("authority_certification_allowed") != "false" for row in layer_rows):
        failures.append("authority certification must be false for every layer")
    if any(row.get("authority_status") != "BLOCKED_DIAGNOSTIC_ONLY" for row in gap_rows):
        failures.append("authority status must remain blocked diagnostic only")

    state = json.loads((ARTIFACT_DIR / "authority_ledger_gap_ranking_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_AUTHORITY_GAP_RANKING_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")
    if state.get("authority_certification_rows") != 0:
        failures.append("authority certification rows must be zero")

    report = (REPORT_DIR / "authority_ledger_gap_ranking_report.md").read_text(encoding="utf-8")
    for phrase in ["not authority certification", "UNKNOWN/BLOCKER", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/authority_ledger_gap_ranking.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden token: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Authority ledger gap ranking validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
