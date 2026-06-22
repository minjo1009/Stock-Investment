from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainFrontendReadModelAdapter(unittest.TestCase):
    def _runtime(self, **overrides):
        from brain.contracts import RuntimeDecision, RuntimeGate

        fields = {
            "runtime_decision_id": "runtime-1",
            "policy_action_id": "action-1",
            "gate": RuntimeGate.SHADOW_ONLY,
            "blocker_flags": ("L6_REVIEW_ONLY_NOT_PAPER_ELIGIBLE",),
            "validation_refs": ("python scripts/task_registry_validate.py",),
            "paper_order_intent_allowed": False,
            "live_order_allowed": False,
        }
        fields.update(overrides)
        return RuntimeDecision(**fields)

    def test_shadow_only_runtime_becomes_read_only_frontend_model(self) -> None:
        from brain.frontend_read_model_adapter import build_frontend_read_model_from_runtime_decision_review

        read_model = build_frontend_read_model_from_runtime_decision_review(
            self._runtime(),
            provenance_paths=("docs/reports/example.md",),
        )

        self.assertEqual(read_model.display_status, "review_shadow_only")
        self.assertEqual(read_model.runtime_decision_id, "runtime-1")
        self.assertTrue(read_model.read_only)
        self.assertIn("L6_REVIEW_ONLY_NOT_PAPER_ELIGIBLE", read_model.blocker_flags)

    def test_blocked_runtime_becomes_blocked_frontend_model(self) -> None:
        from brain.contracts import RuntimeGate
        from brain.frontend_read_model_adapter import build_frontend_read_model_from_runtime_decision_review

        read_model = build_frontend_read_model_from_runtime_decision_review(
            self._runtime(gate=RuntimeGate.BLOCKED, blocker_flags=("L5_SKIP_ACTION_BLOCKED",)),
            provenance_paths=("docs/reports/example.md",),
        )

        self.assertEqual(read_model.display_status, "review_blocked")
        self.assertIn("L5_SKIP_ACTION_BLOCKED", read_model.blocker_flags)

    def test_frontend_adapter_rejects_paper_eligible_runtime(self) -> None:
        from brain.contracts import RuntimeDecision, RuntimeGate
        from brain.frontend_read_model_adapter import build_frontend_read_model_from_runtime_decision_review

        runtime = RuntimeDecision(
            runtime_decision_id="runtime-1",
            policy_action_id="action-1",
            gate=RuntimeGate.PAPER_ELIGIBLE,
            blocker_flags=(),
            validation_refs=("python scripts/task_registry_validate.py",),
        )

        with self.assertRaises(ValueError):
            build_frontend_read_model_from_runtime_decision_review(runtime, provenance_paths=("docs/reports/example.md",))

    def test_frontend_adapter_requires_provenance_paths(self) -> None:
        from brain.frontend_read_model_adapter import build_frontend_read_model_from_runtime_decision_review

        with self.assertRaises(ValueError):
            build_frontend_read_model_from_runtime_decision_review(self._runtime(), provenance_paths=())

    def test_review_chain_rejects_writable_read_model(self) -> None:
        from brain.contracts import FrontendReadModel
        from brain.frontend_read_model_adapter import assert_runtime_frontend_read_model_review_chain

        runtime = self._runtime()
        read_model = FrontendReadModel(
            read_model_id="read-model-1",
            runtime_decision_id=runtime.runtime_decision_id,
            source_tier="brain_runtime_review",
            display_status="review_shadow_only",
            provenance_paths=("docs/reports/example.md",),
            blocker_flags=runtime.blocker_flags,
            read_only=True,
        )

        assert_runtime_frontend_read_model_review_chain(runtime, read_model)

    def test_package_exports_frontend_read_model_adapter(self) -> None:
        import brain

        expected_exports = {
            "build_frontend_read_model_from_runtime_decision_review",
            "assert_runtime_frontend_read_model_review_chain",
        }

        self.assertTrue(expected_exports.issubset(set(brain.__all__)))
        for export_name in expected_exports:
            self.assertTrue(hasattr(brain, export_name), export_name)


if __name__ == "__main__":
    unittest.main()
