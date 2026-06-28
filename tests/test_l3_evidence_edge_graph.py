from __future__ import annotations

import unittest

from src.brain.contracts import MeaningDirection
from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3EconomicMeaningV2, L3EvidenceEdgeState, L3RelationGraphState
from src.brain.l3.evidence_edge import build_evidence_edge
from src.brain.l3.graph_aggregator import aggregate_evidence_graph
from src.l2.runtime_context import HISTORICAL_RESEARCH


def _meaning(
    meaning_id: str,
    direction: MeaningDirection,
    *,
    uncertainty_flags: tuple[str, ...] = (),
    authority_class: str = "official_primary",
) -> L3EconomicMeaningV2:
    return L3EconomicMeaningV2(
        meaning_id=meaning_id,
        asof_ts="2026-06-01T10:00:00Z",
        symbol="AAPL",
        l2_primitive_ids=("l2-" + meaning_id,),
        source_receipt_ids=("receipt-" + meaning_id,),
        source_family="sec_event",
        provider="sec",
        authority_class=authority_class,
        runtime_context=HISTORICAL_RESEARCH,
        source_time_certified=True,
        freshness_status="FRESH",
        event_type="guidance_raise_with_margin_language",
        economic_dimension="REVENUE",
        direction=direction,
        confidence=build_static_l3_confidence("medium"),
        uncertainty_flags=uncertainty_flags,
        reason_codes=("UNIT_TEST",),
    )


class L3EvidenceEdgeGraphTest(unittest.TestCase):
    def test_supportive_plus_noncritical_not_ready_does_not_block_graph(self) -> None:
        support = build_evidence_edge(_meaning("support", MeaningDirection.SUPPORTIVE))
        not_ready = build_evidence_edge(
            _meaning("gap", MeaningDirection.UNKNOWN, uncertainty_flags=("not_ready_confirmation",))
        )
        graph = aggregate_evidence_graph(
            (support, not_ready),
            relation_graph_id="graph-1",
            symbol="AAPL",
            decision_asof_ts="2026-06-01T10:00:00Z",
            expected_edges=2,
        )
        self.assertNotEqual(graph.graph_state, L3RelationGraphState.BLOCKED_CRITICAL)
        self.assertEqual(graph.graph_state, L3RelationGraphState.SUPPORT_DOMINANT_REVIEW)
        self.assertIn("MISSING_CONFIRMATION", graph.noncritical_gap_flags)

    def test_critical_missing_raw_source_blocks_graph(self) -> None:
        blocked = build_evidence_edge(
            _meaning("blocked", MeaningDirection.SUPPORTIVE, uncertainty_flags=("missing_raw_source",))
        )
        graph = aggregate_evidence_graph(
            (blocked,),
            relation_graph_id="graph-2",
            symbol="AAPL",
            decision_asof_ts="2026-06-01T10:00:00Z",
            expected_edges=1,
        )
        self.assertEqual(blocked.edge_state, L3EvidenceEdgeState.CRITICAL_BLOCKED)
        self.assertEqual(graph.graph_state, L3RelationGraphState.BLOCKED_CRITICAL)
        self.assertIn("MISSING_RAW_SOURCE", graph.critical_blocker_flags)

    def test_graph_outputs_review_states_only_and_no_trade_flags(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        self.assertEqual(meaning.trade_output_flag, 0)
        self.assertEqual(meaning.score_output_flag, 0)
        self.assertEqual(meaning.order_intent_flag, 0)
        edge = build_evidence_edge(meaning)
        graph = aggregate_evidence_graph(
            (edge,),
            relation_graph_id="graph-3",
            symbol="AAPL",
            decision_asof_ts="2026-06-01T10:00:00Z",
            expected_edges=1,
        )
        self.assertTrue(graph.graph_state.value.endswith("_REVIEW"))


if __name__ == "__main__":
    unittest.main()
