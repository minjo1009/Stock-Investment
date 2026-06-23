"""Validate Task3846 read-only source authority cleanup planning artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3846_source_authority_cleanup_plan"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "cleanup_candidate_matrix.csv",
    ARTIFACT_DIR / "source_authority_gap_rank.csv",
    ARTIFACT_DIR / "non_destructive_next_actions.csv",
    ARTIFACT_DIR / "source_authority_cleanup_plan_state.json",
    REPORT_DIR / "source_authority_cleanup_plan_report.md",
    REPORT_DIR / "artifact_manifest.csv",
    REPORT_DIR / "registry_recovery_note.md",
]

FORBIDDEN_SCRIPT_TOKENS = [
    "insert into",
    "update ",
    "delete from",
    "submit_order",
    "cancel_order",
    "replace_order",
    "broker.submit",
    "shutil.move",
    "os.remove",
    "unlink(",
]

FORBIDDEN_CLAIMS = [
    "PASS_AUTHORITY",
    "PAPER_ELIGIBLE",
    "DEPLOYMENT_READY",
    "STRATEGY_ACCEPTED",
    "REAL_CAPITAL_ALLOWED",
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

    cleanup_rows = read_csv(ARTIFACT_DIR / "cleanup_candidate_matrix.csv")
    gap_rows = read_csv(ARTIFACT_DIR / "source_authority_gap_rank.csv")
    action_rows = read_csv(ARTIFACT_DIR / "non_destructive_next_actions.csv")
    if not cleanup_rows:
        failures.append("cleanup candidate matrix is empty")
    if not gap_rows:
        failures.append("gap rank is empty")
    if not action_rows:
        failures.append("next actions are empty")

    if any(row.get("destructive_action_required") != "false" for row in cleanup_rows):
        failures.append("all cleanup rows must mark destructive_action_required=false")
    if any(row.get("implement_now_allowed") != "true" for row in cleanup_rows):
        failures.append("all cleanup rows must be report/script/artifact-only implement-now rows")
    if any("UNKNOWN/BLOCKER" not in row.get("non_authority_notice", "") and "Diagnostic" not in row.get("non_authority_notice", "") for row in action_rows):
        failures.append("next actions must carry non-authority notices")

    state = json.loads((ARTIFACT_DIR / "source_authority_cleanup_plan_state.json").read_text(encoding="utf-8"))
    expected = {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_CLEANUP_PLAN_COMPLETE_WITH_BLOCKERS",
    }
    for key, value in expected.items():
        if state.get(key) != value:
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
    if state.get("destructive_action_rows") != 0:
        failures.append("destructive action rows must be zero")

    report = (REPORT_DIR / "source_authority_cleanup_plan_report.md").read_text(encoding="utf-8")
    for phrase in [
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "does not run source acquisition",
        "No source gates, broker gates, paper/live gates",
        "UNKNOWN/BLOCKER",
    ]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/source_authority_cleanup_plan.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_SCRIPT_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden token: {token}")

    generated_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in REQUIRED_FILES)
    generated_text_for_claims = generated_text.replace("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "")
    for claim in FORBIDDEN_CLAIMS:
        if claim in generated_text_for_claims:
            failures.append(f"generated artifact contains forbidden claim: {claim}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Source authority cleanup plan validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
