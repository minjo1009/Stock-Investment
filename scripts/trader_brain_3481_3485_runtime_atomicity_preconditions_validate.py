from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "reports" / "task_3481_3485_runtime_atomicity_preconditions"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3481_3485_runtime_atomicity_preconditions"
REPORT = REPORT_DIR / "task_3481_3485_runtime_atomicity_preconditions.md"
DECISION = REPORT_DIR / "task_3485_decision.csv"
MANIFEST = ARTIFACT_DIR / "artifact_manifest.md"
STORE = ROOT / "src" / "state" / "store.py"
AUTHORITY = ROOT / "src" / "brain" / "runtime_authority.py"
BRAIN_INIT = ROOT / "src" / "brain" / "__init__.py"
LEASE_TEST = ROOT / "tests" / "test_scheduler_lease_atomicity.py"
AUTHORITY_TEST = ROOT / "tests" / "test_runtime_authority_contract.py"
REGISTRY = ROOT / "tasks" / "task_registry.csv"
OPERATING_STATE = ROOT / "docs" / "operating_system" / "project_operating_state.md"
LLM_REALTIME = ROOT / "docs" / "llm_wiki" / "realtime_trading_operations.md"
VALIDATION_MAP = ROOT / "docs" / "architecture" / "test_validation_canonicalization_map.md"


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    report = _read(REPORT)
    manifest = _read(MANIFEST)
    store = _read(STORE)
    authority = _read(AUTHORITY)
    brain_init = _read(BRAIN_INIT)
    lease_test = _read(LEASE_TEST)
    authority_test = _read(AUTHORITY_TEST)
    registry = _read(REGISTRY)
    operating_state = _read(OPERATING_STATE)
    llm_realtime = _read(LLM_REALTIME)
    validation_map = _read(VALIDATION_MAP)

    for term in [
        "PRECONDITIONS_IMPLEMENTED_PROMOTION_STILL_BLOCKED",
        "scheduler lease atomicity",
        "`RuntimeDecision` alone is not enough",
        "reconciliation before retry is mandatory",
        "Strategy: `NOT_ACCEPTED`",
        "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital: `FORBIDDEN`",
    ]:
        if term not in report:
            raise AssertionError(f"missing report term: {term}")

    rows = _rows(DECISION)
    if len(rows) != 1:
        raise AssertionError(f"expected 1 decision row, got {len(rows)}")
    if rows[0].get("decision") != "PRECONDITIONS_IMPLEMENTED_PROMOTION_STILL_BLOCKED":
        raise AssertionError("unexpected decision")
    if rows[0].get("real_capital") != "FORBIDDEN":
        raise AssertionError("real capital boundary missing")

    for term in [
        "CREATE TABLE IF NOT EXISTS scheduler_leases",
        "BEGIN IMMEDIATE",
        "acquire_scheduler_lease",
        "heartbeat_scheduler_lease",
        "release_scheduler_lease",
        "PRAGMA busy_timeout",
    ]:
        if term not in store:
            raise AssertionError(f"missing store contract: {term}")

    for term in [
        "RuntimeAuthorityEvidence",
        "RuntimeSnapshotRefs",
        "RuntimeLineageHashes",
        "BrokerSubmitIdempotencyPlan",
        "REQUIRED_PAPER_ELIGIBILITY_EVIDENCE",
        "validate_runtime_authority",
        "reconciliation_before_retry_required",
    ]:
        if term not in authority:
            raise AssertionError(f"missing authority contract: {term}")
        if term in {"RuntimeAuthorityEvidence", "BrokerSubmitIdempotencyPlan", "validate_runtime_authority"} and term not in brain_init:
            raise AssertionError(f"missing brain export: {term}")

    for term in ["active_lease_blocks_second_owner", "heartbeat_and_release_require_matching_token"]:
        if term not in lease_test:
            raise AssertionError(f"missing lease test: {term}")
    for term in [
        "paper_eligible_requires_complete_evidence",
        "broker_without_client_order_id_requires_reconciliation_before_retry",
        "all_kill_switch_levels_are_required",
    ]:
        if term not in authority_test:
            raise AssertionError(f"missing authority test: {term}")

    for term in [
        "scheduler lease tests: 2",
        "runtime authority tests: 7",
        "paper orders: 0",
        "live orders: 0",
    ]:
        if term not in manifest:
            raise AssertionError(f"missing manifest term: {term}")

    if "Task3485" not in registry:
        raise AssertionError("missing Task3485 registry row")
    if "Task3481-Task3485" not in operating_state:
        raise AssertionError("missing operating state entry")
    if "Task3481-Task3485" not in llm_realtime:
        raise AssertionError("missing LLM wiki entry")
    if "Task3481-Task3485 adds the runtime atomicity precondition validation lane" not in validation_map:
        raise AssertionError("missing validation map entry")

    print("[TASK3481_3485_OK] Runtime atomicity preconditions validated")


if __name__ == "__main__":
    main()
