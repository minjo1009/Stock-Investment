from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainRuntimeDecisionAdapter(unittest.TestCase):
    def _action(self, **overrides):
        from brain.contracts import PolicyAction, PolicyActionType, SizingDirective

        fields = {
            "action_id": "action-1",
            "policy_id": "review-policy-v1",
            "thesis_id": "thesis-1",
            "action": PolicyActionType.WATCH,
            "sizing_directive": SizingDirective.NONE,
            "reason_codes": ("L5_REVIEW_ONLY", "MIXED_RELATION_CONTEXT"),
            "evidence_paths": ("docs/reports/example.md",),
            "creates_order_intent": False,
        }
        fields.update(overrides)
        return PolicyAction(**fields)

    def test_watch_review_action_becomes_shadow_only_runtime_decision(self) -> None:
        from brain.contracts import RuntimeGate
        from brain.runtime_decision_adapter import build_runtime_decision_from_policy_action_review

        runtime = build_runtime_decision_from_policy_action_review(
            self._action(),
            validation_refs=("python scripts/task_registry_validate.py",),
        )

        self.assertEqual(runtime.gate, RuntimeGate.SHADOW_ONLY)
        self.assertFalse(runtime.paper_order_intent_allowed)
        self.assertFalse(runtime.live_order_allowed)
        self.assertIn("L6_REVIEW_ONLY_NOT_PAPER_ELIGIBLE", runtime.blocker_flags)

    def test_skip_review_action_becomes_blocked_runtime_decision(self) -> None:
        from brain.contracts import PolicyActionType, RuntimeGate
        from brain.runtime_decision_adapter import build_runtime_decision_from_policy_action_review

        runtime = build_runtime_decision_from_policy_action_review(
            self._action(action=PolicyActionType.SKIP, reason_codes=("L5_REVIEW_ONLY", "RELATION_NOT_READY")),
            validation_refs=("python scripts/task_registry_validate.py",),
        )

        self.assertEqual(runtime.gate, RuntimeGate.BLOCKED)
        self.assertIn("L5_SKIP_ACTION_BLOCKED", runtime.blocker_flags)
        self.assertFalse(runtime.paper_order_intent_allowed)

    def test_runtime_adapter_requires_validation_refs(self) -> None:
        from brain.runtime_decision_adapter import build_runtime_decision_from_policy_action_review

        with self.assertRaises(ValueError):
            build_runtime_decision_from_policy_action_review(self._action(), validation_refs=())

    def test_runtime_adapter_rejects_non_review_action(self) -> None:
        from brain.contracts import PolicyActionType, SizingDirective
        from brain.runtime_decision_adapter import build_runtime_decision_from_policy_action_review

        with self.assertRaises(ValueError):
            build_runtime_decision_from_policy_action_review(
                self._action(action=PolicyActionType.REDUCE, sizing_directive=SizingDirective.REDUCE_ONLY),
                validation_refs=("python scripts/task_registry_validate.py",),
            )

    def test_review_chain_rejects_paper_eligible_runtime(self) -> None:
        from brain.contracts import RuntimeDecision, RuntimeGate
        from brain.runtime_decision_adapter import assert_policy_action_runtime_review_chain

        action = self._action()
        runtime = RuntimeDecision(
            runtime_decision_id="runtime-1",
            policy_action_id=action.action_id,
            gate=RuntimeGate.PAPER_ELIGIBLE,
            blocker_flags=(),
            validation_refs=("python scripts/task_registry_validate.py",),
            paper_order_intent_allowed=True,
            valid_from="2026-06-20T10:00:00Z",
            valid_until="2026-06-20T10:10:00Z",
            snapshot_refs=("market-v1", "economic-v1", "universe-v1", "policy-v1"),
            lineage_hash="l3-l4-l5-l6-hash",
        )

        with self.assertRaises(ValueError):
            assert_policy_action_runtime_review_chain(action, runtime)

    def test_package_exports_runtime_decision_adapter(self) -> None:
        import brain

        expected_exports = {
            "build_runtime_decision_from_policy_action_review",
            "assert_policy_action_runtime_review_chain",
        }

        self.assertTrue(expected_exports.issubset(set(brain.__all__)))
        for export_name in expected_exports:
            self.assertTrue(hasattr(brain, export_name), export_name)


if __name__ == "__main__":
    unittest.main()
