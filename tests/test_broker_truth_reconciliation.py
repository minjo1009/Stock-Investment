from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.app.broker_truth_reconciliation import run_broker_truth_reconciliation
from src.state.store import (
    create_paper_order_intent,
    get_paper_order_intent,
    initialize_store,
    list_recent_reconciliation_runs,
    record_order,
    transition_paper_order_intent,
)


class BrokerTruthReconciliationTest(unittest.TestCase):
    def test_clean_broker_truth_records_reconciliation_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            record_order(
                db_path,
                order_id="order-1",
                run_id="run-1",
                symbol="AMD",
                side="BUY",
                quantity=1,
                submitted_at="2026-06-20T10:00:00Z",
                status="SUBMITTED",
                raw_status="SUBMITTED",
                environment="paper",
            )
            result = run_broker_truth_reconciliation(
                db_path=db_path,
                broker_orders=[
                    {
                        "source": "fixture",
                        "order_id": "order-1",
                        "symbol": "AMD",
                        "mapped_status": "SUBMITTED",
                        "raw_status": "SUBMITTED",
                        "order_qty": 1,
                        "filled_qty": 0,
                    }
                ],
                now="2026-06-20T10:01:00Z",
            )
            self.assertEqual(result.status, "CLEAN")
            self.assertFalse(result.block_new_orders)
            self.assertTrue(result.broker_truth_ref.startswith("broker-truth:"))
            self.assertEqual(list_recent_reconciliation_runs(db_path, limit=1)[0]["status"], "CLEAN")

    def test_missing_broker_truth_blocks_new_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            record_order(
                db_path,
                order_id="order-1",
                run_id="run-1",
                symbol="AMD",
                side="BUY",
                quantity=1,
                submitted_at="2026-06-20T10:00:00Z",
                status="SUBMITTED",
                raw_status="SUBMITTED",
                environment="paper",
            )
            result = run_broker_truth_reconciliation(
                db_path=db_path,
                broker_orders=[],
                now="2026-06-20T10:01:00Z",
            )
            self.assertEqual(result.status, "MISMATCH")
            self.assertEqual(result.max_severity, "CRITICAL")
            self.assertTrue(result.block_new_orders)
            self.assertEqual(result.event_count, 1)

    def test_unknown_intent_resolves_from_broker_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            create_paper_order_intent(
                db_path,
                intent_id="intent-1",
                idempotency_key="intent-1",
                runtime_decision_id="runtime-1",
                authority_id="authority-1",
                lineage_hash="lineage-1",
                scheduler_lease_token="lease-1",
                symbol="AMD",
                side="BUY",
                quantity=1,
                limit_price=100.0,
                broker_supports_client_order_id=False,
                broker_client_order_id=None,
                created_at="2026-06-20T10:00:00Z",
            )
            transition_paper_order_intent(
                db_path,
                idempotency_key="intent-1",
                from_state="CREATED",
                to_state="SUBMITTING",
                updated_at="2026-06-20T10:00:01Z",
            )
            transition_paper_order_intent(
                db_path,
                idempotency_key="intent-1",
                from_state="SUBMITTING",
                to_state="UNKNOWN",
                updated_at="2026-06-20T10:00:02Z",
                broker_order_id="order-1",
            )
            result = run_broker_truth_reconciliation(
                db_path=db_path,
                broker_orders=[
                    {
                        "source": "fixture",
                        "order_id": "order-1",
                        "symbol": "AMD",
                        "mapped_status": "SUBMITTED",
                        "raw_status": "SUBMITTED",
                        "order_qty": 1,
                        "filled_qty": 0,
                    }
                ],
                now="2026-06-20T10:01:00Z",
            )
            self.assertEqual(result.resolved_intents[0]["resolution"], "RECONCILED")
            self.assertEqual(get_paper_order_intent(db_path, idempotency_key="intent-1")["state"], "RECONCILED")


if __name__ == "__main__":
    unittest.main()
