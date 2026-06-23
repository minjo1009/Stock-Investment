"""Validate Task3856-3865 read-only diagnostic loop artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASKS = [
    "task_3856_task_registry_formal_recovery_plan",
    "task_3857_missing_loop_ledger_recovery",
    "task_3858_cleanup_candidate_decision_review",
    "task_3859_source_authority_proof_requirements_v2",
    "task_3860_freshness_proof_chain_audit",
    "task_3861_sec_user_agent_operator_evidence_plan",
    "task_3862_runtime_broker_safety_proof_v2",
    "task_3863_paper_gate_dependency_proof",
    "task_3864_native_ios_evidence_collection_runbook",
    "task_3865_next10_closeout_decision_pack",
]

REQUIRED_REGISTRY_COLUMNS = {
    "task_id",
    "title",
    "owner_team",
    "status",
    "canonical_state",
    "strategy_acceptance",
    "data_readiness",
    "parent_task",
    "key_report",
    "key_decision",
    "key_artifacts",
    "validation_command",
    "notes",
}

FORBIDDEN_SCRIPT_TOKENS = [
    "insert into",
    "update ",
    "delete from",
    "submit_order",
    "cancel_order",
    "replace_order",
    "broker.submit",
    "os.remove",
    "unlink(",
    "shutil.move",
]

FORBIDDEN_ARTIFACT_CLAIMS = [
    "PASS_AUTHORITY",
    "PAPER_ELIGIBLE",
    "STRATEGY_ACCEPTED",
    "REAL_CAPITAL_ALLOWED",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_state_file(artifact_dir: Path) -> Path | None:
    candidates = list(artifact_dir.glob("*_state.json"))
    return candidates[0] if candidates else None


def main() -> int:
    failures: list[str] = []
    for task_id in TASKS:
        artifact_dir = Path("data/artifacts") / task_id
        report_dir = Path("docs/reports") / task_id
        if not artifact_dir.exists():
            failures.append(f"missing artifact dir: {artifact_dir}")
            continue
        if not report_dir.exists():
            failures.append(f"missing report dir: {report_dir}")
            continue
        state_file = find_state_file(artifact_dir)
        if state_file is None:
            failures.append(f"missing state json for {task_id}")
            continue
        state = json.loads(state_file.read_text(encoding="utf-8"))
        for key, expected in {
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }.items():
            if state.get(key) != expected:
                failures.append(f"{task_id}: unexpected {key}: {state.get(key)}")
        for key in ["source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted", "destructive_action_run"]:
            if state.get(key) is not False:
                failures.append(f"{task_id}: {key} must be false")
        report_text = "\n".join(path.read_text(encoding="utf-8") for path in report_dir.glob("*.md"))
        for phrase in ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN", "UNKNOWN/BLOCKER"]:
            if phrase not in report_text:
                failures.append(f"{task_id}: report missing {phrase}")

    proposed = Path("data/artifacts/task_3856_task_registry_formal_recovery_plan/proposed_task_registry_rows.csv")
    if not proposed.exists():
        failures.append("missing proposed task registry rows")
    else:
        rows = read_csv(proposed)
        if len(rows) != 10:
            failures.append(f"expected 10 proposed registry rows, got {len(rows)}")
        columns = set(rows[0].keys()) if rows else set()
        missing = REQUIRED_REGISTRY_COLUMNS - columns
        if missing:
            failures.append(f"proposed registry rows missing columns: {sorted(missing)}")
        required_ids = {f"Task{task_num}" for task_num in range(3846, 3856)}
        found_ids = {row.get("task_id", "") for row in rows}
        if required_ids - found_ids:
            failures.append(f"proposed registry rows missing ids: {sorted(required_ids - found_ids)}")
        for row in rows:
            row_text = json.dumps(row, ensure_ascii=False).lower()
            for token in ["strategy_accepted", "deployment-ready", "paper-live-allowed", "real-capital-allowed", "broker-mutation-allowed"]:
                if token in row_text:
                    failures.append(f"proposed row contains forbidden permission wording: {token}")

    ledger = Path("docs/reports/task_3856_3865_gpt_next10_loop_run/loop_ledger.csv")
    if not ledger.exists():
        failures.append("missing run loop ledger")
    else:
        ledger_rows = read_csv(ledger)
        if len(ledger_rows) != 10:
            failures.append(f"expected 10 loop ledger rows, got {len(ledger_rows)}")

    script_text = Path("scripts/diagnostic_next10_loop_run.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_SCRIPT_TOKENS:
        if token in script_text:
            failures.append(f"generator contains forbidden token: {token}")

    artifact_text = ""
    for task_id in TASKS:
        for path in (Path("data/artifacts") / task_id).glob("*"):
            if path.is_file() and path.suffix in {".csv", ".json", ".md"}:
                artifact_text += path.read_text(encoding="utf-8", errors="replace")
    for token in FORBIDDEN_ARTIFACT_CLAIMS:
        if token in artifact_text:
            failures.append(f"generated artifacts contain forbidden claim: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Task3856-3865 diagnostic next10 loop validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
