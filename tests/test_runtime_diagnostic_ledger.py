from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.brain.diagnostic_orchestration import (
    DiagnosticHeartbeatCadence,
    L0L6DiagnosticRuntimeState,
    build_diagnostic_orchestration_decision,
)
from src.state.store import (
    get_latest_diagnostic_state_hash,
    initialize_store,
    list_runtime_operating_metrics,
    record_order,
    record_diagnostic_runtime_heartbeat,
    record_reconciliation_run,
    record_trade_run_start,
)


class RuntimeDiagnosticLedgerTest(unittest.TestCase):
    def test_diagnostic_heartbeat_state_hash_persists_for_duplicate_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            state = L0L6DiagnosticRuntimeState(
                cadence=DiagnosticHeartbeatCadence.SAFETY_5_MIN,
                heartbeat_bucket_ts="2026-06-20T10:00:00Z",
                market_session_id="nasdaq-2026-06-20",
                market_data_asof_ts="2026-06-20T10:00:00Z",
                account_state_ref="paper-account:unverified",
                source_receipt_ids=(),
                primitive_batch_ids=(),
                meaning_ids=(),
                thesis_ids=(),
                policy_action_ids=(),
                runtime_decision_ids=("runtime-review-state",),
                order_state_refs=("orders:none",),
                changed_candidate_ids=(),
                validation_refs=("unit-test",),
            )
            decision = build_diagnostic_orchestration_decision(state)
            inserted = record_diagnostic_runtime_heartbeat(
                db_path,
                idempotency_key=decision.idempotency_key,
                cadence=decision.cadence.value,
                heartbeat_bucket_ts=state.heartbeat_bucket_ts,
                state_hash=decision.state_hash,
                status=decision.status.value,
                should_execute=decision.should_execute,
                reason_codes=decision.reason_codes,
                allowed_operations=decision.allowed_operations,
                forbidden_operations=decision.forbidden_operations,
                created_at="2026-06-20T10:00:01Z",
            )
            self.assertTrue(inserted)
            previous_hash = get_latest_diagnostic_state_hash(
                db_path,
                cadence=DiagnosticHeartbeatCadence.SAFETY_5_MIN.value,
                heartbeat_bucket_ts=state.heartbeat_bucket_ts,
            )
            self.assertEqual(previous_hash, decision.state_hash)
            duplicate = build_diagnostic_orchestration_decision(state, previous_state_hash=previous_hash)
            self.assertFalse(duplicate.should_execute)

    def test_runtime_operating_metrics_surface_unknown_orders_and_reconciliation_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AMD",
                side="BUY",
                requested_quantity=1,
                started_at="2026-06-20T10:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="unknown-1",
                run_id=run_id,
                symbol="AMD",
                side="BUY",
                quantity=1,
                submitted_at="2026-06-20T10:00:00Z",
                status="UNKNOWN",
                environment="paper",
                raw_status="ORDER_NOT_FOUND",
            )
            record_reconciliation_run(
                db_path,
                run_id=run_id,
                started_at="2026-06-20T10:01:00Z",
                finished_at="2026-06-20T10:02:00Z",
                status="BLOCKING",
                max_severity="ERROR",
                block_new_orders=True,
                summary_text="unknown order blocks retry",
            )
            metrics = list_runtime_operating_metrics(db_path, now_iso="2026-06-20T10:30:00Z")
            self.assertEqual(metrics["unknown_order_count"], 1)
            self.assertGreaterEqual(metrics["oldest_unknown_order_age_minutes"], 30.0)
            self.assertEqual(metrics["reconciliation_block_count"], 1)


if __name__ == "__main__":
    unittest.main()
