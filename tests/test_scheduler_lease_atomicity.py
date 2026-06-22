from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.state.store import (
    acquire_scheduler_lease,
    create_paper_order_intent,
    get_paper_order_intent,
    get_scheduler_lease,
    get_runtime_authority_evidence,
    heartbeat_scheduler_lease,
    initialize_store,
    record_runtime_authority_evidence,
    release_scheduler_lease,
    resolve_paper_order_intent_after_reconciliation,
    transition_paper_order_intent,
    validate_scheduler_lease_token,
)


class SchedulerLeaseAtomicityTest(unittest.TestCase):
    def test_active_lease_blocks_second_owner_until_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            first = acquire_scheduler_lease(
                db_path,
                lease_key="5_min_safety:2026-06-20T10:00:00Z",
                cadence="5_min_safety",
                bucket_ts="2026-06-20T10:00:00Z",
                owner_id="owner-a",
                state_hash="hash-a",
                now="2026-06-20T10:00:01Z",
                ttl_seconds=60,
            )
            self.assertTrue(first["acquired"])
            second = acquire_scheduler_lease(
                db_path,
                lease_key="5_min_safety:2026-06-20T10:00:00Z",
                cadence="5_min_safety",
                bucket_ts="2026-06-20T10:00:00Z",
                owner_id="owner-b",
                state_hash="hash-b",
                now="2026-06-20T10:00:30Z",
                ttl_seconds=60,
            )
            self.assertFalse(second["acquired"])
            self.assertEqual(second["owner_id"], "owner-a")

            stolen = acquire_scheduler_lease(
                db_path,
                lease_key="5_min_safety:2026-06-20T10:00:00Z",
                cadence="5_min_safety",
                bucket_ts="2026-06-20T10:00:00Z",
                owner_id="owner-b",
                state_hash="hash-b",
                now="2026-06-20T10:02:01Z",
                ttl_seconds=60,
            )
            self.assertTrue(stolen["acquired"])
            self.assertEqual(stolen["owner_id"], "owner-b")
            lease = get_scheduler_lease(db_path, lease_key="5_min_safety:2026-06-20T10:00:00Z")
            self.assertEqual(lease["owner_id"], "owner-b")
            self.assertEqual(lease["status"], "ACTIVE")

    def test_heartbeat_and_release_require_matching_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            acquired = acquire_scheduler_lease(
                db_path,
                lease_key="10_min_brain:2026-06-20T10:00:00Z",
                cadence="10_min_brain",
                bucket_ts="2026-06-20T10:00:00Z",
                owner_id="brain-owner",
                state_hash="hash-brain",
                now="2026-06-20T10:00:01Z",
                ttl_seconds=60,
            )
            self.assertFalse(
                heartbeat_scheduler_lease(
                    db_path,
                    lease_key="10_min_brain:2026-06-20T10:00:00Z",
                    lease_token="wrong-token",
                    now="2026-06-20T10:00:10Z",
                    ttl_seconds=60,
                )
            )
            self.assertTrue(
                heartbeat_scheduler_lease(
                    db_path,
                    lease_key="10_min_brain:2026-06-20T10:00:00Z",
                    lease_token=str(acquired["lease_token"]),
                    now="2026-06-20T10:00:10Z",
                    ttl_seconds=60,
                )
            )
            self.assertFalse(
                release_scheduler_lease(
                    db_path,
                    lease_key="10_min_brain:2026-06-20T10:00:00Z",
                    lease_token="wrong-token",
                    released_at="2026-06-20T10:00:20Z",
                )
            )
            self.assertTrue(
                release_scheduler_lease(
                    db_path,
                    lease_key="10_min_brain:2026-06-20T10:00:00Z",
                    lease_token=str(acquired["lease_token"]),
                    released_at="2026-06-20T10:00:20Z",
                )
            )
            lease = get_scheduler_lease(db_path, lease_key="10_min_brain:2026-06-20T10:00:00Z")
            self.assertEqual(lease["status"], "RELEASED")

    def test_validate_scheduler_lease_token_rejects_stale_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            acquired = acquire_scheduler_lease(
                db_path,
                lease_key="5_min_safety:2026-06-20T10:00:00Z",
                cadence="5_min_safety",
                bucket_ts="2026-06-20T10:00:00Z",
                owner_id="owner-a",
                state_hash="hash-a",
                now="2026-06-20T10:00:01Z",
                ttl_seconds=60,
            )
            self.assertTrue(
                validate_scheduler_lease_token(
                    db_path,
                    lease_key="5_min_safety:2026-06-20T10:00:00Z",
                    lease_token=str(acquired["lease_token"]),
                    now="2026-06-20T10:00:30Z",
                )
            )
            self.assertFalse(
                validate_scheduler_lease_token(
                    db_path,
                    lease_key="5_min_safety:2026-06-20T10:00:00Z",
                    lease_token=str(acquired["lease_token"]),
                    now="2026-06-20T10:02:30Z",
                )
            )

    def test_paper_order_intent_state_machine_rejects_impossible_transition(self) -> None:
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
            self.assertTrue(
                transition_paper_order_intent(
                    db_path,
                    idempotency_key="intent-1",
                    from_state="CREATED",
                    to_state="SUBMITTING",
                    updated_at="2026-06-20T10:00:01Z",
                )
            )
            with self.assertRaises(ValueError):
                transition_paper_order_intent(
                    db_path,
                    idempotency_key="intent-1",
                    from_state="SUBMITTING",
                    to_state="CREATED",
                    updated_at="2026-06-20T10:00:02Z",
                )
            self.assertTrue(
                transition_paper_order_intent(
                    db_path,
                    idempotency_key="intent-1",
                    from_state="SUBMITTING",
                    to_state="UNKNOWN",
                    updated_at="2026-06-20T10:00:03Z",
                    broker_order_id="order-1",
                    raw_response={"ok": True},
                )
            )
            intent = get_paper_order_intent(db_path, idempotency_key="intent-1")
            self.assertEqual(intent["state"], "UNKNOWN")
            self.assertEqual(intent["broker_order_id"], "order-1")

    def test_unknown_intent_reconciles_or_blocks_deterministically(self) -> None:
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
            resolution = resolve_paper_order_intent_after_reconciliation(
                db_path,
                idempotency_key="intent-1",
                broker_state="SUBMITTED",
                local_state="UNKNOWN",
                updated_at="2026-06-20T10:01:00Z",
            )
            self.assertEqual(resolution, "RECONCILED")
            self.assertEqual(get_paper_order_intent(db_path, idempotency_key="intent-1")["state"], "RECONCILED")

    def test_authority_evidence_ledger_is_append_only_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            payload = {"runtime_decision_id": "runtime-1", "lineage_hash": "hash-1"}
            self.assertTrue(
                record_runtime_authority_evidence(
                    db_path,
                    authority_hash="authority-hash-1",
                    authority_id="authority-1",
                    runtime_decision_id="runtime-1",
                    payload=payload,
                    created_at="2026-06-20T10:00:00Z",
                )
            )
            self.assertFalse(
                record_runtime_authority_evidence(
                    db_path,
                    authority_hash="authority-hash-1",
                    authority_id="authority-1",
                    runtime_decision_id="runtime-1",
                    payload=payload,
                    created_at="2026-06-20T10:00:01Z",
                )
            )
            with self.assertRaises(ValueError):
                record_runtime_authority_evidence(
                    db_path,
                    authority_hash="authority-hash-1",
                    authority_id="authority-1",
                    runtime_decision_id="runtime-1",
                    payload={"runtime_decision_id": "runtime-1", "lineage_hash": "changed"},
                    created_at="2026-06-20T10:00:02Z",
                )
            self.assertEqual(
                get_runtime_authority_evidence(db_path, authority_hash="authority-hash-1")["payload"],
                payload,
            )


if __name__ == "__main__":
    unittest.main()
