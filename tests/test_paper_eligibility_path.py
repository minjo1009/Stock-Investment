from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.brain.contracts import RuntimeDecision, RuntimeGate
from src.brain.runtime_authority import (
    BrokerSubmitIdempotencyPlan,
    REQUIRED_KILL_SWITCH_LEVELS,
    REQUIRED_PAPER_ELIGIBILITY_EVIDENCE,
    RuntimeAuthorityCandidate,
    RuntimeAuthorityEvidence,
    RuntimeLineageHashes,
    RuntimeSnapshotRefs,
)
from src.execution.paper_eligibility_path import create_paper_intent_from_latest_authority
from src.state.store import get_runtime_authority_evidence, initialize_store


def _candidate(*, complete: bool = True) -> RuntimeAuthorityCandidate:
    runtime = RuntimeDecision(
        runtime_decision_id="runtime-paper-1",
        policy_action_id="policy-action-1",
        gate=RuntimeGate.PAPER_ELIGIBLE,
        blocker_flags=(),
        validation_refs=("python scripts/task_registry_validate.py",),
        paper_order_intent_allowed=True,
        valid_from="2026-06-20T10:00:00Z",
        valid_until="2026-06-20T10:10:00Z",
        snapshot_refs=("market-v1", "economic-v1", "universe-v1", "policy-v1"),
        lineage_hash="l3-l4-l5-l6-hash",
    )
    evidence = RuntimeAuthorityEvidence(
        authority_id="authority-paper-1",
        runtime_decision_id="runtime-paper-1",
        lineage=RuntimeLineageHashes(
            economic_meaning_hash="l3-hash",
            thesis_bundle_hash="l4-hash",
            policy_action_hash="l5-hash",
            runtime_decision_hash="l6-hash",
        ),
        snapshots=RuntimeSnapshotRefs(
            market_data_version="market-v1",
            economic_data_version="economic-v1",
            universe_version="universe-v1",
            policy_version="policy-v1",
            source_receipt_ids=("source-receipt-1",),
        ),
        valid_from="2026-06-20T10:00:00Z",
        valid_until="2026-06-20T10:10:00Z",
        kill_switch_levels_checked=REQUIRED_KILL_SWITCH_LEVELS,
        paper_eligibility_evidence=REQUIRED_PAPER_ELIGIBILITY_EVIDENCE if complete else ("SOURCE_FRESHNESS_OK",),
        broker_truth_refs=("broker-truth:fixture",) if complete else (),
        source_quality_refs=("source-quality:fixture",) if complete else (),
    )
    return RuntimeAuthorityCandidate(runtime=runtime, evidence=evidence)


class PaperEligibilityPathTest(unittest.TestCase):
    def test_full_evidence_paper_eligible_path_creates_local_intent_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            result = create_paper_intent_from_latest_authority(
                db_path,
                candidates=(_candidate(),),
                idempotency=BrokerSubmitIdempotencyPlan(
                    local_intent_id="intent-paper-1",
                    idempotency_key="intent-paper-1",
                    scheduler_lease_token="lease-1",
                    broker_supports_client_order_id=False,
                    reconciliation_before_retry_required=True,
                ),
                symbol="AMD",
                side="BUY",
                quantity=1,
                limit_price=100.0,
                now="2026-06-20T10:05:00Z",
                created_at="2026-06-20T10:05:00Z",
            )
            self.assertEqual(result.selected_runtime_decision_id, "runtime-paper-1")
            self.assertTrue(result.evidence_inserted)
            self.assertEqual(result.intent["state"], "CREATED")
            self.assertEqual(result.intent["broker_order_id"], None)
            self.assertEqual(
                get_runtime_authority_evidence(db_path, authority_hash=result.authority_hash)["runtime_decision_id"],
                "runtime-paper-1",
            )

    def test_incomplete_evidence_blocks_before_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            with self.assertRaises(RuntimeError):
                create_paper_intent_from_latest_authority(
                    db_path,
                    candidates=(_candidate(complete=False),),
                    idempotency=BrokerSubmitIdempotencyPlan(
                        local_intent_id="intent-paper-1",
                        idempotency_key="intent-paper-1",
                        scheduler_lease_token="lease-1",
                        broker_supports_client_order_id=False,
                        reconciliation_before_retry_required=True,
                    ),
                    symbol="AMD",
                    side="BUY",
                    quantity=1,
                    limit_price=100.0,
                    now="2026-06-20T10:05:00Z",
                    created_at="2026-06-20T10:05:00Z",
                )


if __name__ == "__main__":
    unittest.main()
