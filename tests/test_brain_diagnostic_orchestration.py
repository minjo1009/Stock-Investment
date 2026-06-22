from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainDiagnosticOrchestration(unittest.TestCase):
    def _state(self, **overrides):
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

    def test_state_hash_is_stable_for_reordered_ids(self) -> None:
        first = self._state()
        second = self._state(
            source_receipt_ids=("source-receipt-1", "source-receipt-2"),
            meaning_ids=("meaning-1", "meaning-2"),
        )

        self.assertEqual(first.state_hash(), second.state_hash())

    def test_changed_candidate_changes_state_hash(self) -> None:
        first = self._state()
        second = self._state(changed_candidate_ids=("candidate-2",))

        self.assertNotEqual(first.state_hash(), second.state_hash())

    def test_first_10_min_brain_heartbeat_executes(self) -> None:
        from brain.diagnostic_orchestration import (
            DiagnosticOrchestrationStatus,
            build_diagnostic_orchestration_decision,
        )

        decision = build_diagnostic_orchestration_decision(self._state())

        self.assertEqual(decision.status, DiagnosticOrchestrationStatus.DIAGNOSTIC_RUN_REQUIRED)
        self.assertTrue(decision.should_execute)
        self.assertIn("validate_l3_l6_review_chain", decision.allowed_operations)
        self.assertIn("submit_live_order", decision.forbidden_operations)
        self.assertIn("permit_real_capital", decision.forbidden_operations)

    def test_duplicate_state_hash_skips_idempotently(self) -> None:
        from brain.diagnostic_orchestration import (
            DiagnosticOrchestrationStatus,
            build_diagnostic_orchestration_decision,
        )

        state = self._state()
        first = build_diagnostic_orchestration_decision(state)
        second = build_diagnostic_orchestration_decision(state, previous_state_hash=first.state_hash)

        self.assertEqual(second.status, DiagnosticOrchestrationStatus.DUPLICATE_STATE_SKIPPED)
        self.assertFalse(second.should_execute)
        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertIn("STATE_HASH_UNCHANGED", second.reason_codes)

    def test_10_min_brain_without_changed_candidates_skips_without_error(self) -> None:
        from brain.diagnostic_orchestration import (
            DiagnosticOrchestrationStatus,
            build_diagnostic_orchestration_decision,
        )

        decision = build_diagnostic_orchestration_decision(self._state(changed_candidate_ids=()))

        self.assertEqual(decision.status, DiagnosticOrchestrationStatus.NO_CHANGED_CANDIDATES_SKIPPED)
        self.assertFalse(decision.should_execute)

    def test_5_min_safety_heartbeat_rejects_brain_work(self) -> None:
        from brain.diagnostic_orchestration import DiagnosticHeartbeatCadence

        with self.assertRaises(ValueError):
            self._state(cadence=DiagnosticHeartbeatCadence.SAFETY_5_MIN)

    def test_valid_5_min_safety_heartbeat_has_safety_ops_only(self) -> None:
        from brain.diagnostic_orchestration import DiagnosticHeartbeatCadence, build_diagnostic_orchestration_decision

        state = self._state(
            cadence=DiagnosticHeartbeatCadence.SAFETY_5_MIN,
            changed_candidate_ids=(),
            primitive_batch_ids=(),
            meaning_ids=(),
            thesis_ids=(),
            policy_action_ids=(),
            runtime_decision_ids=("runtime-decision-existing-1",),
        )
        decision = build_diagnostic_orchestration_decision(state)

        self.assertIn("check_existing_l6_runtime_state", decision.allowed_operations)
        self.assertNotIn("validate_l3_l6_review_chain", decision.allowed_operations)
        self.assertTrue(decision.should_execute)

    def test_rejects_paper_or_live_order_counts(self) -> None:
        with self.assertRaises(ValueError):
            self._state(paper_order_intent_count=1)
        with self.assertRaises(ValueError):
            self._state(live_order_count=1)

    def test_rejects_status_boundary_change(self) -> None:
        with self.assertRaises(ValueError):
            self._state(strategy_status="ACCEPTED")
        with self.assertRaises(ValueError):
            self._state(deployment_status="DEPLOYMENT_READY")
        with self.assertRaises(ValueError):
            self._state(real_capital_status="ALLOWED")

    def test_30_min_heavy_source_requires_source_receipts(self) -> None:
        from brain.diagnostic_orchestration import DiagnosticHeartbeatCadence

        with self.assertRaises(ValueError):
            self._state(cadence=DiagnosticHeartbeatCadence.HEAVY_SOURCE_30_MIN, source_receipt_ids=())

    def test_package_exports_diagnostic_orchestration_surface(self) -> None:
        import brain

        expected_exports = {
            "DiagnosticHeartbeatCadence",
            "DiagnosticOrchestrationDecision",
            "DiagnosticOrchestrationStatus",
            "L0L6DiagnosticRuntimeState",
            "build_diagnostic_orchestration_decision",
            "build_idempotency_key",
        }

        self.assertTrue(expected_exports.issubset(set(brain.__all__)))
        for export_name in expected_exports:
            self.assertTrue(hasattr(brain, export_name), export_name)


if __name__ == "__main__":
    unittest.main()
