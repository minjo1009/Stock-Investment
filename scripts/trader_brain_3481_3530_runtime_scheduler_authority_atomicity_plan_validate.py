from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "reports" / "task_3481_3530_runtime_scheduler_authority_atomicity_plan"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3481_3530_runtime_scheduler_authority_atomicity_plan"
REPORT = REPORT_DIR / "task_3481_3530_runtime_scheduler_authority_atomicity_plan.md"
DECISION = REPORT_DIR / "task_3530_decision.csv"
LANES = ARTIFACT_DIR / "implementation_lanes.csv"
GPT_FINDINGS = ARTIFACT_DIR / "gpt_review_findings.csv"
MANIFEST = ARTIFACT_DIR / "artifact_manifest.md"
REGISTRY = ROOT / "tasks" / "task_registry.csv"
OPERATING_STATE = ROOT / "docs" / "operating_system" / "project_operating_state.md"
LLM_REALTIME = ROOT / "docs" / "llm_wiki" / "realtime_trading_operations.md"


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
    llm_realtime = _read(LLM_REALTIME)

    for term in [
        "PLAN_APPROVED_FOR_IMPLEMENTATION_NOT_PROMOTION",
        "global state-machine specification",
        "decision lineage immutability",
        "scheduler singleton/lease ownership",
        "runtime snapshot consistency/versioning",
        "kill-switch hierarchy",
        "reconciliation authority/conflict model",
        "Task3481-3500",
        "Task3501-3520",
        "Task3521-3530",
        "These findings are review-only and not source-of-truth.",
        "Strategy: `NOT_ACCEPTED`",
        "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital: `FORBIDDEN`",
    ]:
        if term not in report:
            raise AssertionError(f"missing report term: {term}")

    decision_rows = _rows(DECISION)
    if len(decision_rows) != 1:
        raise AssertionError(f"expected 1 decision row, got {len(decision_rows)}")
    if decision_rows[0].get("decision") != "PLAN_APPROVED_FOR_IMPLEMENTATION_NOT_PROMOTION":
        raise AssertionError("unexpected decision")
    if decision_rows[0].get("real_capital") != "FORBIDDEN":
        raise AssertionError("real capital boundary missing")

    lane_rows = _rows(LANES)
    if len(lane_rows) != 3:
        raise AssertionError(f"expected 3 implementation lanes, got {len(lane_rows)}")
    for lane in ["Full Diagnostic Scheduler", "Single Runtime Authority", "Broker Submit Atomicity"]:
        if not any(row["lane"] == lane for row in lane_rows):
            raise AssertionError(f"missing lane: {lane}")

    finding_rows = _rows(GPT_FINDINGS)
    if len(finding_rows) != 11:
        raise AssertionError(f"expected 11 GPT findings, got {len(finding_rows)}")
    if sum(1 for row in finding_rows if row["severity"] == "P0") != 6:
        raise AssertionError("expected 6 P0 GPT findings")
    if not all(row["authority"] == "review_only_not_source_of_truth" for row in finding_rows):
        raise AssertionError("GPT findings must remain review-only")

    for term in ["implementation lanes: 3", "GPT review findings: 11", "Strategy: `NOT_ACCEPTED`"]:
        if term not in manifest:
            raise AssertionError(f"missing manifest term: {term}")

    if "Task3481" not in registry or "Task3530" not in registry:
        raise AssertionError("missing Task3481/Task3530 registry rows")
    if "Task3481-Task3530" not in operating_state:
        raise AssertionError("missing operating state entry")
    if "Task3481-Task3530" not in llm_realtime and "Task3481-3530" not in llm_realtime:
        raise AssertionError("missing realtime LLM wiki update")

    print("[TASK3481_3530_PLAN_OK] Runtime scheduler authority atomicity plan validated")


if __name__ == "__main__":
    main()
