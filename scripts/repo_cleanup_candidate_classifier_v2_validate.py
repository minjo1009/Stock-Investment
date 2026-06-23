"""Validate Task3854 read-only repo cleanup candidate classifier artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3854_repo_cleanup_candidate_classifier_v2"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "repo_cleanup_candidate_classifier_v2.csv",
    ARTIFACT_DIR / "repo_cleanup_candidate_summary.csv",
    ARTIFACT_DIR / "repo_cleanup_candidate_classifier_v2_state.json",
    REPORT_DIR / "repo_cleanup_candidate_classifier_v2_report.md",
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

    rows = read_csv(ARTIFACT_DIR / "repo_cleanup_candidate_classifier_v2.csv")
    summary = read_csv(ARTIFACT_DIR / "repo_cleanup_candidate_summary.csv")
    if not rows:
        failures.append("classifier rows are empty")
    if not summary:
        failures.append("summary rows are empty")
    if any(row.get("destructive_action_permitted") != "false" for row in rows + summary):
        failures.append("destructive action must not be permitted")

    state = json.loads((ARTIFACT_DIR / "repo_cleanup_candidate_classifier_v2_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_REPO_CLEANUP_CLASSIFIER_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")
    if state.get("destructive_action_rows") != 0:
        failures.append("destructive_action_rows must be zero")

    report = (REPORT_DIR / "repo_cleanup_candidate_classifier_v2_report.md").read_text(encoding="utf-8")
    for phrase in ["no destructive action", "UNKNOWN/BLOCKER", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Repo cleanup candidate classifier v2 validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
