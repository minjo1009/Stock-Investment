from __future__ import annotations

import unittest

from src.brain.contracts import RuntimeDecision, RuntimeGate
from src.brain.runtime_authority import (
    BrokerSubmitIdempotencyPlan,
    REQUIRED_KILL_SWITCH_LEVELS,
    REQUIRED_PAPER_ELIGIBILITY_EVIDENCE,
    RuntimeAuthorityCandidate,
    RuntimeAuthorityGate,
    RuntimeAuthorityEvidence,
    RuntimeLineageHashes,
    RuntimeSnapshotRefs,
    authorize_latest_runtime_decision,
    validate_runtime_authority,
)


def _runtime(gate: RuntimeGate = RuntimeGate.SHADOW_ONLY, *, paper_allowed: bool = False) -> RuntimeDecision:
    kwargs = {}
    if gate == RuntimeGate.PAPER_ELIGIBLE or paper_allowed:
        kwargs = {
            "valid_from": "2026-06-20T10:00:00Z",
            "valid_until": "2026-06-20T10:10:00Z",
            "snapshot_refs": ("market-v1", "economic-v1", "universe-v1", "policy-v1"),
            "lineage_hash": "l3-l4-l5-l6-hash",
        }
    return RuntimeDecision(
        runtime_decision_id="runtime-1",
        policy_action_id="policy-action-1",
        gate=gate,
        blocker_flags=() if gate == RuntimeGate.PAPER_ELIGIBLE else ("REVIEW_ONLY",),
        validation_refs=("python scripts/task_registry_validate.py",),
        paper_order_intent_allowed=paper_allowed,
        **kwargs,
    )


def _evidence(**overrides) -> RuntimeAuthorityEvidence:
    payload = {
        "authority_id": "authority-1",
        "runtime_decision_id": "runtime-1",
        "lineage": RuntimeLineageHashes(
            economic_meaning_hash="l3-hash",
            thesis_bundle_hash="l4-hash",
            policy_action_hash="l5-hash",
            runtime_decision_hash="l6-hash",
        ),
        "snapshots": RuntimeSnapshotRefs(
            market_data_version="market-v1",
            economic_data_version="economic-v1",
            universe_version="universe-v1",
            policy_version="policy-v1",
            source_receipt_ids=("source-receipt-1",),
        ),
        "valid_from": "2026-06-20T10:00:00Z",
        "valid_until": "2026-06-20T10:10:00Z",
        "kill_switch_levels_checked": REQUIRED_KILL_SWITCH_LEVELS,
    }
    payload.update(overrides)
    return RuntimeAuthorityEvidence(**payload)


class RuntimeAuthorityContractTest(unittest.TestCase):
    def test_shadow_runtime_never_grants_paper_order_intent(self) -> None:
        result = validate_runtime_authority(
            _runtime(),
            _evidence(),
            now="2026-06-20T10:05:00Z",
        )
        self.assertEqual(result.gate, RuntimeAuthorityGate.SHADOW_ONLY)
        self.assertFalse(result.paper_order_intent_allowed)
        self.assertIn("SHADOW_ONLY_NO_ORDER_PERMISSION", result.reason_codes)

    def test_expired_runtime_decision_blocks(self) -> None:
        result = validate_runtime_authority(
            _runtime(),
            _evidence(),
            now="2026-06-20T10:10:00Z",
        )
        self.assertEqual(result.gate, RuntimeAuthorityGate.BLOCKED)
        self.assertIn("RUNTIME_DECISION_EXPIRED", result.reason_codes)

    def test_paper_eligible_requires_complete_evidence(self) -> None:
        result = validate_runtime_authority(
            _runtime(RuntimeGate.PAPER_ELIGIBLE, paper_allowed=True),
            _evidence(paper_eligibility_evidence=("SOURCE_FRESHNESS_OK",)),
            now="2026-06-20T10:05:00Z",
        )
        self.assertEqual(result.gate, RuntimeAuthorityGate.BLOCKED)
        self.assertFalse(result.paper_order_intent_allowed)
        self.assertIn("PAPER_ELIGIBILITY_EVIDENCE_INCOMPLETE", result.reason_codes)

    def test_runtime_decision_rejects_paper_eligible_without_authority_fields(self) -> None:
        with self.assertRaises(ValueError):
            RuntimeDecision(
                runtime_decision_id="runtime-no-authority-fields",
                policy_action_id="policy-action-1",
                gate=RuntimeGate.PAPER_ELIGIBLE,
                blocker_flags=(),
                validation_refs=("python scripts/task_registry_validate.py",),
                paper_order_intent_allowed=True,
            )

    def test_paper_eligible_can_pass_only_with_full_lineage_snapshot_and_broker_truth_refs(self) -> None:
        result = validate_runtime_authority(
            _runtime(RuntimeGate.PAPER_ELIGIBLE, paper_allowed=True),
            _evidence(
                paper_eligibility_evidence=REQUIRED_PAPER_ELIGIBILITY_EVIDENCE,
                broker_truth_refs=("broker-truth-fill-ledger-v1",),
                source_quality_refs=("source-quality-ok-v1",),
            ),
            now="2026-06-20T10:05:00Z",
        )
        self.assertEqual(result.gate, RuntimeAuthorityGate.PAPER_ELIGIBLE)
        self.assertTrue(result.paper_order_intent_allowed)
        self.assertIn("PAPER_ELIGIBILITY_EVIDENCE_COMPLETE", result.reason_codes)

    def test_all_kill_switch_levels_are_required(self) -> None:
        with self.assertRaises(ValueError):
            _evidence(kill_switch_levels_checked=("GLOBAL_BLOCK",))

    def test_broker_without_client_order_id_requires_reconciliation_before_retry(self) -> None:
        with self.assertRaises(ValueError):
            BrokerSubmitIdempotencyPlan(
                local_intent_id="intent-1",
                idempotency_key="idem-1",
                scheduler_lease_token="lease-1",
                broker_supports_client_order_id=False,
                reconciliation_before_retry_required=False,
            )

    def test_broker_client_order_id_must_equal_idempotency_key_when_supported(self) -> None:
        with self.assertRaises(ValueError):
            BrokerSubmitIdempotencyPlan(
                local_intent_id="intent-1",
                idempotency_key="idem-1",
                scheduler_lease_token="lease-1",
                broker_supports_client_order_id=True,
                broker_client_order_id="different",
            )

    def test_single_latest_authority_selects_latest_runtime_decision(self) -> None:
        older = RuntimeAuthorityCandidate(
            runtime=_runtime(),
            evidence=_evidence(authority_id="authority-old", valid_from="2026-06-20T09:00:00Z", valid_until="2026-06-20T09:10:00Z"),
        )
        latest_runtime = RuntimeDecision(
            runtime_decision_id="runtime-2",
            policy_action_id="policy-action-2",
            gate=RuntimeGate.SHADOW_ONLY,
            blocker_flags=("REVIEW_ONLY",),
            validation_refs=("python scripts/task_registry_validate.py",),
        )
        latest = RuntimeAuthorityCandidate(
            runtime=latest_runtime,
            evidence=_evidence(
                authority_id="authority-latest",
                runtime_decision_id="runtime-2",
                valid_from="2026-06-20T10:00:00Z",
                valid_until="2026-06-20T10:10:00Z",
            ),
        )
        decision = authorize_latest_runtime_decision((older, latest), now="2026-06-20T10:05:00Z")
        self.assertEqual(decision.selected_runtime_decision_id, "runtime-2")
        self.assertEqual(decision.result.gate, RuntimeAuthorityGate.SHADOW_ONLY)
        self.assertIn("SINGLE_LATEST_L6_AUTHORITY", decision.result.reason_codes)

    def test_single_latest_authority_rejects_tied_latest_decisions(self) -> None:
        runtime_2 = RuntimeDecision(
            runtime_decision_id="runtime-2",
            policy_action_id="policy-action-2",
            gate=RuntimeGate.SHADOW_ONLY,
            blocker_flags=("REVIEW_ONLY",),
            validation_refs=("python scripts/task_registry_validate.py",),
        )
        with self.assertRaises(ValueError):
            authorize_latest_runtime_decision(
                (
                    RuntimeAuthorityCandidate(runtime=_runtime(), evidence=_evidence()),
                    RuntimeAuthorityCandidate(runtime=runtime_2, evidence=_evidence(runtime_decision_id="runtime-2")),
                ),
                now="2026-06-20T10:05:00Z",
            )


if __name__ == "__main__":
    unittest.main()
