from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainRuntimeContracts(unittest.TestCase):
    def _valid_chain(self):
        from brain.contracts import (
            EconomicMeaning,
            FrontendReadModel,
            MeaningDirection,
            PolicyAction,
            PolicyActionType,
            RuntimeDecision,
            RuntimeGate,
            SizingDirective,
            SourceGap,
            ThesisBundle,
            ThesisInvalidationState,
        )

        meaning = EconomicMeaning(
            meaning_id="meaning-1",
            asof_ts="2026-06-20T00:00:00Z",
            symbol="TEST",
            direction=MeaningDirection.SUPPORTIVE,
            confidence=0.7,
            uncertainty_flags=("SOURCE_PARTIAL",),
            source_packet_ids=("source-packet-1",),
            relation_readiness="REVIEW_READY",
        )
        thesis = ThesisBundle(
            thesis_id="thesis-1",
            trade_spec_id="trade-spec-1",
            symbol="TEST",
            decision_asof_ts="2026-06-20T00:00:00Z",
            meaning_ids=("meaning-1",),
            catalyst_summary="source-backed catalyst under review",
            invalidation_state=ThesisInvalidationState.WATCH,
            blocker_flags=("STRICT_ASOF_INCOMPLETE",),
            source_gaps=(SourceGap.MISSING_ASOF_TIMESTAMP,),
        )
        action = PolicyAction(
            action_id="action-1",
            policy_id="policy-1",
            thesis_id="thesis-1",
            action=PolicyActionType.REDUCE,
            sizing_directive=SizingDirective.REDUCE_ONLY,
            reason_codes=("DRAWDOWN_CAUSE_UNCONFIRMED",),
            evidence_paths=("docs/reports/example.md",),
        )
        runtime = RuntimeDecision(
            runtime_decision_id="runtime-1",
            policy_action_id="action-1",
            gate=RuntimeGate.BLOCKED,
            blocker_flags=("BROKER_TRUTH_SELL_MISSING",),
            validation_refs=("python scripts/task_registry_validate.py",),
        )
        read_model = FrontendReadModel(
            read_model_id="read-model-1",
            runtime_decision_id="runtime-1",
            source_tier="diagnostic",
            display_status="blocked",
            provenance_paths=("docs/reports/example.md",),
            blocker_flags=("BROKER_TRUTH_SELL_MISSING",),
        )
        return meaning, thesis, action, runtime, read_model

    def test_valid_contract_chain_has_no_assignment_leakage(self) -> None:
        from brain.contracts import assert_no_assignment_leakage

        assert_no_assignment_leakage(*self._valid_chain())

    def test_l3_rejects_outcome_assignment(self) -> None:
        from brain.contracts import EconomicMeaning, MeaningDirection

        with self.assertRaises(ValueError):
            EconomicMeaning(
                meaning_id="meaning-1",
                asof_ts="2026-06-20T00:00:00Z",
                symbol="TEST",
                direction=MeaningDirection.RISK,
                confidence=0.5,
                uncertainty_flags=(),
                source_packet_ids=("source-packet-1",),
                relation_readiness="REVIEW_READY",
                outcome_used_for_assignment=True,
            )

    def test_l5_cannot_create_order_intent(self) -> None:
        from brain.contracts import PolicyAction, PolicyActionType, SizingDirective

        with self.assertRaises(ValueError):
            PolicyAction(
                action_id="action-1",
                policy_id="policy-1",
                thesis_id="thesis-1",
                action=PolicyActionType.HOLD,
                sizing_directive=SizingDirective.UNCHANGED,
                reason_codes=("THESIS_SURVIVES",),
                evidence_paths=("docs/reports/example.md",),
                creates_order_intent=True,
            )

    def test_source_gap_none_cannot_be_combined(self) -> None:
        from brain.contracts import SourceGap, ThesisBundle, ThesisInvalidationState

        with self.assertRaises(ValueError):
            ThesisBundle(
                thesis_id="thesis-1",
                trade_spec_id="trade-spec-1",
                symbol="TEST",
                decision_asof_ts="2026-06-20T00:00:00Z",
                meaning_ids=("meaning-1",),
                catalyst_summary="source-backed catalyst under review",
                invalidation_state=ThesisInvalidationState.WATCH,
                blocker_flags=(),
                source_gaps=(SourceGap.NONE, SourceGap.MISSING_RAW_SOURCE),
            )

    def test_l6_forbids_live_order_permission(self) -> None:
        from brain.contracts import RuntimeDecision, RuntimeGate

        with self.assertRaises(ValueError):
            RuntimeDecision(
                runtime_decision_id="runtime-1",
                policy_action_id="action-1",
                gate=RuntimeGate.PAPER_ELIGIBLE,
                blocker_flags=(),
                validation_refs=("python scripts/task_registry_validate.py",),
                paper_order_intent_allowed=True,
                live_order_allowed=True,
            )

    def test_l6_paper_eligible_cannot_carry_blockers(self) -> None:
        from brain.contracts import RuntimeDecision, RuntimeGate

        with self.assertRaises(ValueError):
            RuntimeDecision(
                runtime_decision_id="runtime-1",
                policy_action_id="action-1",
                gate=RuntimeGate.PAPER_ELIGIBLE,
                blocker_flags=("STRICT_ASOF_BLOCKED",),
                validation_refs=("python scripts/task_registry_validate.py",),
                paper_order_intent_allowed=True,
            )

    def test_frontend_read_model_must_be_read_only(self) -> None:
        from brain.contracts import FrontendReadModel

        with self.assertRaises(ValueError):
            FrontendReadModel(
                read_model_id="read-model-1",
                runtime_decision_id="runtime-1",
                source_tier="diagnostic",
                display_status="blocked",
                provenance_paths=("docs/reports/example.md",),
                blocker_flags=(),
                read_only=False,
            )

    def test_frontend_read_model_cannot_claim_deployment_or_acceptance(self) -> None:
        from brain.contracts import FrontendReadModel

        with self.assertRaises(ValueError):
            FrontendReadModel(
                read_model_id="read-model-1",
                runtime_decision_id="runtime-1",
                source_tier="diagnostic",
                display_status="deployment_ready",
                provenance_paths=("docs/reports/example.md",),
                blocker_flags=(),
            )

    def test_contract_chain_rejects_symbol_mismatch(self) -> None:
        from brain.contracts import ThesisBundle, assert_no_assignment_leakage

        meaning, thesis, action, runtime, read_model = self._valid_chain()
        bad_thesis = ThesisBundle(
            thesis_id=thesis.thesis_id,
            trade_spec_id=thesis.trade_spec_id,
            symbol="OTHER",
            decision_asof_ts=thesis.decision_asof_ts,
            meaning_ids=thesis.meaning_ids,
            catalyst_summary=thesis.catalyst_summary,
            invalidation_state=thesis.invalidation_state,
            blocker_flags=thesis.blocker_flags,
            source_gaps=thesis.source_gaps,
        )

        with self.assertRaises(ValueError):
            assert_no_assignment_leakage(meaning, bad_thesis, action, runtime, read_model)

    def test_contract_chain_rejects_future_meaning_asof(self) -> None:
        from brain.contracts import EconomicMeaning, assert_no_assignment_leakage

        meaning, thesis, action, runtime, read_model = self._valid_chain()
        future_meaning = EconomicMeaning(
            meaning_id=meaning.meaning_id,
            asof_ts="2026-06-21T00:00:00Z",
            symbol=meaning.symbol,
            direction=meaning.direction,
            confidence=meaning.confidence,
            uncertainty_flags=meaning.uncertainty_flags,
            source_packet_ids=meaning.source_packet_ids,
            relation_readiness=meaning.relation_readiness,
        )

        with self.assertRaises(ValueError):
            assert_no_assignment_leakage(future_meaning, thesis, action, runtime, read_model)

    def test_package_exports_contract_surface(self) -> None:
        import brain

        expected_exports = {
            "EconomicMeaning",
            "MeaningRelationEdge",
            "RelationEdgeType",
            "ThesisBundle",
            "PolicyAction",
            "RuntimeDecision",
            "FrontendReadModel",
            "assert_no_assignment_leakage",
            "assert_relation_edge_thesis_chain",
            "assert_thesis_policy_action_review_chain",
            "assert_policy_action_runtime_review_chain",
            "assert_runtime_frontend_read_model_review_chain",
            "build_meaning_relation_edge",
            "build_policy_action_review_from_thesis",
            "build_frontend_read_model_from_runtime_decision_review",
            "build_runtime_decision_from_policy_action_review",
            "build_thesis_bundle_from_relation_edge",
            "task742_row_to_economic_meaning",
            "task742_rows_to_economic_meanings",
            "build_frontend_read_model_from_paper_ops_catalog",
            "PAPER_OPS_RUNTIME_CONTRACT_VERSION",
        }

        self.assertTrue(expected_exports.issubset(set(brain.__all__)))
        for export_name in expected_exports:
            self.assertTrue(hasattr(brain, export_name), export_name)


if __name__ == "__main__":
    unittest.main()
