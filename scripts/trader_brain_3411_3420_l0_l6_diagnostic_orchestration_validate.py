from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REPORT_DIR = ROOT / "docs" / "reports" / "task_3411_3420_l0_l6_diagnostic_orchestration"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3411_3420_l0_l6_diagnostic_orchestration"


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise AssertionError(f"no rows to write: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _base_state(**overrides):
    from brain.diagnostic_orchestration import DiagnosticHeartbeatCadence, L0L6DiagnosticRuntimeState

    fields = {
        "cadence": DiagnosticHeartbeatCadence.BRAIN_10_MIN,
        "heartbeat_bucket_ts": "2026-06-20T14:40:00+09:00",
        "market_session_id": "NASDAQ-2026-06-19-REGULAR",
        "market_data_asof_ts": "2026-06-20T14:39:30+09:00",
        "account_state_ref": "account-state:shadow:20260620T1440",
        "source_receipt_ids": ("source-receipt-2", "source-receipt-1"),
        "primitive_batch_ids": ("primitive-batch-1",),
        "meaning_ids": ("meaning-2", "meaning-1"),
        "thesis_ids": ("thesis-1",),
        "policy_action_ids": ("policy-action-1",),
        "runtime_decision_ids": ("runtime-decision-1",),
        "order_state_refs": ("order-state:shadow:none",),
        "changed_candidate_ids": ("candidate-1",),
        "validation_refs": ("python scripts/task_registry_validate.py",),
    }
    fields.update(overrides)
    return L0L6DiagnosticRuntimeState(**fields)


def _run_unit_tests() -> None:
    cmd = [sys.executable, "-m", "unittest", "tests.test_brain_diagnostic_orchestration"]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        raise AssertionError(f"unit test failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")


def main() -> None:
    from brain.diagnostic_orchestration import (
        DiagnosticHeartbeatCadence,
        build_diagnostic_orchestration_decision,
    )

    _run_unit_tests()

    brain_state = _base_state()
    brain_decision = build_diagnostic_orchestration_decision(brain_state)
    duplicate_decision = build_diagnostic_orchestration_decision(brain_state, previous_state_hash=brain_decision.state_hash)
    no_change_decision = build_diagnostic_orchestration_decision(_base_state(changed_candidate_ids=()))
    safety_decision = build_diagnostic_orchestration_decision(
        _base_state(
            cadence=DiagnosticHeartbeatCadence.SAFETY_5_MIN,
            heartbeat_bucket_ts="2026-06-20T14:35:00+09:00",
            primitive_batch_ids=(),
            meaning_ids=(),
            thesis_ids=(),
            policy_action_ids=(),
            changed_candidate_ids=(),
            runtime_decision_ids=("runtime-decision-existing-1",),
        )
    )

    decisions = [brain_decision, duplicate_decision, no_change_decision, safety_decision]
    _write_rows(
        ARTIFACT_DIR / "heartbeat_decisions.csv",
        [
            {
                "row": idx + 1,
                "cadence": decision.cadence.value,
                "status": decision.status.value,
                "should_execute": int(decision.should_execute),
                "state_hash": decision.state_hash,
                "idempotency_key": decision.idempotency_key,
                "allowed_operations": "|".join(decision.allowed_operations),
                "forbidden_operations": "|".join(decision.forbidden_operations),
                "reason_codes": "|".join(decision.reason_codes),
            }
            for idx, decision in enumerate(decisions)
        ],
    )
    _write_rows(
        ARTIFACT_DIR / "idempotency_audit.csv",
        [
            {
                "check": "same_state_same_hash",
                "passed": int(brain_decision.state_hash == duplicate_decision.state_hash),
                "detail": "duplicate heartbeat preserved state hash",
            },
            {
                "check": "same_state_same_idempotency_key",
                "passed": int(brain_decision.idempotency_key == duplicate_decision.idempotency_key),
                "detail": "duplicate heartbeat preserved idempotency key",
            },
            {
                "check": "duplicate_skipped",
                "passed": int((not duplicate_decision.should_execute) and duplicate_decision.status.value == "DUPLICATE_STATE_SKIPPED"),
                "detail": "previous hash matched current hash",
            },
        ],
    )

    report = _read(REPORT_DIR / "task_3411_3420_l0_l6_diagnostic_orchestration.md")
    decision_rows = _rows(REPORT_DIR / "task_3420_decision.csv")
    heartbeat_rows = _rows(ARTIFACT_DIR / "heartbeat_decisions.csv")
    idempotency_rows = _rows(ARTIFACT_DIR / "idempotency_audit.csv")
    manifest_rows = _rows(ARTIFACT_DIR / "artifact_manifest.csv")

    for phrase in [
        "l0_l6_diagnostic_orchestration_state_hash_idempotency_guard_implemented",
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "5-minute safety heartbeat rejects changed-candidate brain work",
        "10-minute brain heartbeat with changed candidates requires L6 runtime decision references",
    ]:
        if phrase not in report:
            raise AssertionError(f"report missing phrase: {phrase}")

    if len(decision_rows) != 1:
        raise AssertionError("decision CSV must contain one row")
    decision_row = decision_rows[0]
    if decision_row["strategy"] != "NOT_ACCEPTED" or decision_row["deployment"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        raise AssertionError("decision status boundary changed")
    if decision_row["real_capital"] != "FORBIDDEN":
        raise AssertionError("real capital boundary changed")

    if len(heartbeat_rows) != 4:
        raise AssertionError("heartbeat decision artifact row count changed")
    if len(idempotency_rows) != 3 or any(row["passed"] != "1" for row in idempotency_rows):
        raise AssertionError("idempotency audit did not fully pass")
    if len(manifest_rows) != 4:
        raise AssertionError("artifact manifest row count changed")

    combined = "\n".join(
        [
            _read(ROOT / "src" / "brain" / "diagnostic_orchestration.py"),
            _read(ROOT / "src" / "brain" / "__init__.py"),
            _read(ROOT / "tests" / "test_brain_diagnostic_orchestration.py"),
        ]
    )
    for forbidden in ["submit_order(", "place_order(", "kis_client.", "run_backtest("]:
        if forbidden in combined:
            raise AssertionError(f"forbidden execution/replay call found: {forbidden}")

    print("[TASK3411_3420_OK] L0-L6 diagnostic orchestration state hash and idempotency guard checks passed")


if __name__ == "__main__":
    main()
