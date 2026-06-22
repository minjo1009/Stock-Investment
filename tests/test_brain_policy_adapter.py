from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainPolicyAdapter(unittest.TestCase):
    def _thesis(self, **overrides):
        from brain.contracts import SourceGap, ThesisBundle, ThesisInvalidationState

        fields = {
            "thesis_id": "thesis-1",
            "trade_spec_id": "trade-spec-1",
            "symbol": "TEST",
            "decision_asof_ts": "2026-06-20T00:00:00Z",
            "meaning_ids": ("meaning-1",),
            "catalyst_summary": "review-only thesis",
            "invalidation_state": ThesisInvalidationState.NONE,
            "blocker_flags": ("MIXED_RELATION_CONTEXT",),
            "source_gaps": (SourceGap.NONE,),
        }
        fields.update(overrides)
        return ThesisBundle(**fields)

    def test_mixed_context_thesis_becomes_watch_review_action(self) -> None:
        from brain.contracts import PolicyActionType, SizingDirective
        from brain.policy_adapter import build_policy_action_review_from_thesis

        action = build_policy_action_review_from_thesis(
            self._thesis(),
            policy_id="review-policy-v1",
            evidence_paths=("docs/reports/example.md",),
        )

        self.assertEqual(action.action, PolicyActionType.WATCH)
        self.assertEqual(action.sizing_directive, SizingDirective.NONE)
        self.assertFalse(action.creates_order_intent)
        self.assertIn("L5_REVIEW_ONLY", action.reason_codes)

    def test_source_gap_thesis_becomes_skip_review_action(self) -> None:
        from brain.contracts import PolicyActionType, SourceGap
        from brain.policy_adapter import build_policy_action_review_from_thesis

        action = build_policy_action_review_from_thesis(
            self._thesis(blocker_flags=("SOURCE_GAP_FLAGS_PRESENT",), source_gaps=(SourceGap.MISSING_RAW_SOURCE,)),
            policy_id="review-policy-v1",
            evidence_paths=("docs/reports/example.md",),
        )

        self.assertEqual(action.action, PolicyActionType.SKIP)
        self.assertIn("SOURCE_GAP_MISSING_RAW_SOURCE", action.reason_codes)

    def test_unknown_invalidation_thesis_becomes_skip_review_action(self) -> None:
        from brain.contracts import PolicyActionType, ThesisInvalidationState
        from brain.policy_adapter import build_policy_action_review_from_thesis

        action = build_policy_action_review_from_thesis(
            self._thesis(invalidation_state=ThesisInvalidationState.UNKNOWN, blocker_flags=("RELATION_NOT_READY",)),
            policy_id="review-policy-v1",
            evidence_paths=("docs/reports/example.md",),
        )

        self.assertEqual(action.action, PolicyActionType.SKIP)
        self.assertIn("RELATION_NOT_READY", action.reason_codes)

    def test_review_action_requires_evidence_paths(self) -> None:
        from brain.policy_adapter import build_policy_action_review_from_thesis

        with self.assertRaises(ValueError):
            build_policy_action_review_from_thesis(self._thesis(), policy_id="review-policy-v1", evidence_paths=())

    def test_review_chain_rejects_non_review_action(self) -> None:
        from brain.contracts import PolicyAction, PolicyActionType, SizingDirective
        from brain.policy_adapter import assert_thesis_policy_action_review_chain

        thesis = self._thesis()
        action = PolicyAction(
            action_id="action-1",
            policy_id="review-policy-v1",
            thesis_id=thesis.thesis_id,
            action=PolicyActionType.REDUCE,
            sizing_directive=SizingDirective.REDUCE_ONLY,
            reason_codes=("manual-test",),
            evidence_paths=("docs/reports/example.md",),
        )

        with self.assertRaises(ValueError):
            assert_thesis_policy_action_review_chain(thesis, action)

    def test_package_exports_policy_adapter(self) -> None:
        import brain

        expected_exports = {
            "build_policy_action_review_from_thesis",
            "assert_thesis_policy_action_review_chain",
        }

        self.assertTrue(expected_exports.issubset(set(brain.__all__)))
        for export_name in expected_exports:
            self.assertTrue(hasattr(brain, export_name), export_name)


if __name__ == "__main__":
    unittest.main()
