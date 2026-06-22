from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "reports" / "task_3422_3430_backend_runtime_professional_audit" / "task_3422_3430_backend_runtime_professional_audit.md"
DECISION = ROOT / "docs" / "reports" / "task_3422_3430_backend_runtime_professional_audit" / "task_3430_decision.csv"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3422_3430_backend_runtime_professional_audit"
FINDINGS = ARTIFACT_DIR / "audit_findings.csv"
REVIEWS = ARTIFACT_DIR / "review_evidence.csv"
MANIFEST = ARTIFACT_DIR / "artifact_manifest.md"
REGISTRY = ROOT / "tasks" / "task_registry.csv"
OPERATING_STATE = ROOT / "docs" / "operating_system" / "project_operating_state.md"


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
    registry = _read(REGISTRY)
    operating_state = _read(OPERATING_STATE)

    required_report_terms = [
        "BLOCK_RUNTIME_PROMOTION_UNTIL_P0_P1_CLOSED",
        "Task588 PowerShell parse passed: 0/1",
        "`run_trade_once` can allow execution when DB/control_state is missing",
        "Alternate execution plane",
        "Orchestration not wired",
        "Real-capital reachability",
        "GPT/Chrome and subagents were review-only",
        "Strategy: `NOT_ACCEPTED`",
        "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital: `FORBIDDEN`",
    ]
    for term in required_report_terms:
        if term not in report:
            raise AssertionError(f"missing report term: {term}")

    decision_rows = _rows(DECISION)
    if len(decision_rows) != 1:
        raise AssertionError(f"expected 1 decision row, got {len(decision_rows)}")
    decision = decision_rows[0]
    if decision.get("decision") != "BLOCK_RUNTIME_PROMOTION_UNTIL_P0_P1_CLOSED":
        raise AssertionError("decision row does not block runtime promotion")
    if decision.get("real_capital") != "FORBIDDEN":
        raise AssertionError("real capital boundary missing from decision")

    finding_rows = _rows(FINDINGS)
    if len(finding_rows) != 12:
        raise AssertionError(f"expected 12 finding rows, got {len(finding_rows)}")
    if not any(row["severity"] == "P0" and row["area"] == "Runtime fail-closed" for row in finding_rows):
        raise AssertionError("missing P0 runtime fail-closed finding")
    if not any(row["severity"] == "P0" and row["area"] == "Task588 supervisor" for row in finding_rows):
        raise AssertionError("missing P0 Task588 supervisor parse finding")
    if not any(row["severity"] == "P1" and row["area"] == "Runtime ledger" for row in finding_rows):
        raise AssertionError("missing P1 runtime ledger finding")

    review_rows = _rows(REVIEWS)
    if len(review_rows) != 6:
        raise AssertionError(f"expected 6 review evidence rows, got {len(review_rows)}")
    if not any(row["reviewer"] == "GPT_Chrome" and row["authority"] == "review_only_not_source_of_truth" for row in review_rows):
        raise AssertionError("missing GPT/Chrome review-only evidence")
    if not any(row["type"] == "local_command" and row["outcome"].startswith("FAIL") for row in review_rows):
        raise AssertionError("missing local command failure evidence")

    for term in [
        "audit findings: 12",
        "review evidence: 6",
        "Strategy: `NOT_ACCEPTED`",
        "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital: `FORBIDDEN`",
    ]:
        if term not in manifest:
            raise AssertionError(f"missing manifest term: {term}")

    if "Task3422" not in registry or "Task3430" not in registry:
        raise AssertionError("missing Task3422/Task3430 registry rows")
    if "Task3422-Task3430" not in operating_state:
        raise AssertionError("missing operating state closeout")

    print("[TASK3422_3430_OK] Backend runtime professional audit artifacts validated")


if __name__ == "__main__":
    main()
