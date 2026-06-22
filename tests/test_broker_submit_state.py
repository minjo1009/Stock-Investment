from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.brain.runtime_authority import BrokerSubmitIdempotencyPlan, RuntimeAuthorityGate, RuntimeAuthorityResult
from src.execution.broker_submit_state import (
    PaperOrderIntentSpec,
    create_authorized_paper_order_intent,
    get_submit_state,
    mark_paper_order_intent_local_recorded,
    mark_paper_order_intent_submitting,
    mark_paper_order_intent_unknown_after_submit,
    reconcile_paper_order_intent,
)
from src.state.store import initialize_store


def _authority(allowed: bool = True) -> RuntimeAuthorityResult:
    return RuntimeAuthorityResult(
        authority_id="authority-1",
        gate=RuntimeAuthorityGate.PAPER_ELIGIBLE if allowed else RuntimeAuthorityGate.BLOCKED,
        authority_hash="authority-hash-1",
        reason_codes=("unit-test",),
        paper_order_intent_allowed=allowed,
    )


def _spec() -> PaperOrderIntentSpec:
    return PaperOrderIntentSpec(
        runtime_decision_id="runtime-1",
        authority=_authority(),
        idempotency=BrokerSubmitIdempotencyPlan(
            local_intent_id="intent-1",
            idempotency_key="intent-1",
            scheduler_lease_token="lease-1",
            broker_supports_client_order_id=False,
            reconciliation_before_retry_required=True,
        ),
        lineage_hash="lineage-1",
        symbol="AMD",
        side="BUY",
        quantity=1,
        limit_price=100.0,
    )


class BrokerSubmitStateTest(unittest.TestCase):
    def test_authorized_intent_lifecycle_reconciles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            created = create_authorized_paper_order_intent(
                db_path,
                spec=_spec(),
                created_at="2026-06-20T10:00:00Z",
            )
            self.assertEqual(created["state"], "CREATED")
            self.assertTrue(mark_paper_order_intent_submitting(db_path, idempotency_key="intent-1", updated_at="2026-06-20T10:00:01Z"))
            self.assertTrue(
                mark_paper_order_intent_local_recorded(
                    db_path,
                    idempotency_key="intent-1",
                    broker_order_id="order-1",
                    raw_response={"ok": True},
                    updated_at="2026-06-20T10:00:02Z",
                )
            )
            self.assertEqual(get_submit_state(db_path, idempotency_key="intent-1")["state"], "SUBMITTED_LOCAL_RECORDED")
            resolution = reconcile_paper_order_intent(
                db_path,
                idempotency_key="intent-1",
                broker_state="SUBMITTED",
                local_state="SUBMITTED",
                updated_at="2026-06-20T10:01:00Z",
            )
            self.assertEqual(resolution, "RECONCILED")
            self.assertEqual(get_submit_state(db_path, idempotency_key="intent-1")["state"], "RECONCILED")

    def test_unknown_after_submit_blocks_until_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            create_authorized_paper_order_intent(db_path, spec=_spec(), created_at="2026-06-20T10:00:00Z")
            self.assertTrue(mark_paper_order_intent_submitting(db_path, idempotency_key="intent-1", updated_at="2026-06-20T10:00:01Z"))
            self.assertTrue(
                mark_paper_order_intent_unknown_after_submit(
                    db_path,
                    idempotency_key="intent-1",
                    broker_order_id="order-1",
                    raw_response={"submit": "accepted", "local_write": "failed"},
                    updated_at="2026-06-20T10:00:02Z",
                )
            )
            self.assertEqual(get_submit_state(db_path, idempotency_key="intent-1")["state"], "UNKNOWN")
            resolution = reconcile_paper_order_intent(
                db_path,
                idempotency_key="intent-1",
                broker_state="ORDER_NOT_FOUND",
                local_state="UNKNOWN",
                updated_at="2026-06-20T10:01:00Z",
            )
            self.assertEqual(resolution, "BLOCKED")
            self.assertEqual(get_submit_state(db_path, idempotency_key="intent-1")["state"], "BLOCKED")

    def test_blocked_authority_cannot_create_intent_spec(self) -> None:
        with self.assertRaises(ValueError):
            PaperOrderIntentSpec(
                runtime_decision_id="runtime-1",
                authority=_authority(allowed=False),
                idempotency=BrokerSubmitIdempotencyPlan(
                    local_intent_id="intent-1",
                    idempotency_key="intent-1",
                    scheduler_lease_token="lease-1",
                    broker_supports_client_order_id=False,
                    reconciliation_before_retry_required=True,
                ),
                lineage_hash="lineage-1",
                symbol="AMD",
                side="BUY",
                quantity=1,
                limit_price=100.0,
            )


if __name__ == "__main__":
    unittest.main()
