from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "reports" / "task_3486_3500_runtime_idempotency_authority_observability"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3486_3500_runtime_idempotency_authority_observability"
REPORT = REPORT_DIR / "task_3486_3500_runtime_idempotency_authority_observability.md"
DECISION = REPORT_DIR / "task_3500_decision.csv"
MANIFEST = ARTIFACT_DIR / "artifact_manifest.md"
GPT_FINDINGS = ARTIFACT_DIR / "gpt_review_findings.csv"
STORE = ROOT / "src" / "state" / "store.py"
CONTRACTS = ROOT / "src" / "brain" / "contracts.py"
AUTHORITY = ROOT / "src" / "brain" / "runtime_authority.py"
KIS = ROOT / "src" / "integration" / "kis_client.py"
TASK585 = ROOT / "src" / "app" / "task_585_kis_paper_order_execution.py"
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
    contracts = _read(CONTRACTS)
    authority = _read(AUTHORITY)
    kis = _read(KIS)
    task585 = _read(TASK585)
    registry = _read(REGISTRY)
    operating_state = _read(OPERATING_STATE)
    llm_realtime = _read(LLM_REALTIME)
    validation_map = _read(VALIDATION_MAP)

    for term in [
        "RUNTIME_SAFETY_CONNECTIONS_IMPLEMENTED_PROMOTION_STILL_BLOCKED",
        "targeted runtime safety tests: 41",
        "GPT/Chrome review-only",
        "broker calls: 0",
        "paper orders: 0",
        "live orders: 0",
        "Strategy: `NOT_ACCEPTED`",
        "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital: `FORBIDDEN`",
    ]:
        if term not in report:
            raise AssertionError(f"missing report term: {term}")

    decision_rows = _rows(DECISION)
    if len(decision_rows) != 1:
        raise AssertionError(f"expected 1 decision row, got {len(decision_rows)}")
    if decision_rows[0].get("decision") != "RUNTIME_SAFETY_CONNECTIONS_IMPLEMENTED_PROMOTION_STILL_BLOCKED":
        raise AssertionError("unexpected decision")
    if decision_rows[0].get("real_capital") != "FORBIDDEN":
        raise AssertionError("real capital boundary missing")

    finding_rows = _rows(GPT_FINDINGS)
    if len(finding_rows) != 10:
        raise AssertionError(f"expected 10 GPT review findings, got {len(finding_rows)}")
    if sum(1 for row in finding_rows if row["severity"] == "P0") != 3:
        raise AssertionError("expected 3 GPT P0 findings")

    for term in [
        "CREATE TABLE IF NOT EXISTS paper_order_intents",
        "CREATE TABLE IF NOT EXISTS runtime_authority_evidence_ledger",
        "validate_scheduler_lease_token",
        "record_runtime_authority_evidence",
        "resolve_paper_order_intent_after_reconciliation",
        "list_runtime_operating_metrics",
    ]:
        if term not in store:
            raise AssertionError(f"missing store term: {term}")

    for term in ["valid_from", "valid_until", "snapshot_refs", "lineage_hash"]:
        if term not in contracts:
            raise AssertionError(f"missing RuntimeDecision field: {term}")

    for term in ["REQUIRED_PAPER_ELIGIBILITY_EVIDENCE", "validate_runtime_authority", "BROKER_TRUTH_REVIEWED"]:
        if term not in authority:
            raise AssertionError(f"missing authority term: {term}")

    for term in [
        "supports_client_order_id",
        "KIS_CLIENT_ORDER_ID_UNSUPPORTED",
        "idempotency_key",
        "_local_idempotency_key",
        "reconciliation_before_retry_required",
    ]:
        if term not in kis:
            raise AssertionError(f"missing KIS idempotency term: {term}")

    for term in [
        "create_paper_order_intent",
        "transition_paper_order_intent",
        "LOCAL_RECORD_FAILED_AFTER_BROKER_SUBMIT",
        "DUPLICATE_INTENT_REQUIRES_RECONCILIATION_BEFORE_RETRY",
        '{"SUBMITTED", "PENDING", "PARTIAL", "UNKNOWN"}',
    ]:
        if term not in task585:
            raise AssertionError(f"missing Task585 runtime term: {term}")

    for term in ["targeted runtime safety tests: 41", "GPT review-only findings: 10"]:
        if term not in manifest:
            raise AssertionError(f"missing manifest term: {term}")
    if "Task3486" not in registry or "Task3500" not in registry:
        raise AssertionError("missing registry rows")
    if "Task3486-Task3500" not in operating_state:
        raise AssertionError("missing operating state entry")
    if "Task3486-Task3500" not in llm_realtime:
        raise AssertionError("missing LLM wiki entry")
    if "Task3486-Task3500 adds the runtime safety connection validation lane" not in validation_map:
        raise AssertionError("missing validation map entry")

    print("[TASK3486_3500_OK] Runtime idempotency authority observability validated")


if __name__ == "__main__":
    main()
