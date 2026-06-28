from __future__ import annotations

import unittest

from src.brain.contracts import MeaningDirection
from src.brain.l3.canonical_diagnostic_engine import (
    adapt_canonical_source_event_to_l3_meaning,
    build_canonical_evidence_edge,
    build_canonical_l3_objects,
)
from src.brain.l3.contracts import L3EvidenceEdgeState, L3RelationGraphState


class L3CanonicalDiagnosticEngineTest(unittest.TestCase):
    def test_canonical_source_event_adapter_is_context_only_not_task742_replay(self) -> None:
        meaning = adapt_canonical_source_event_to_l3_meaning(
            {
                "source_event_id": "CANONICAL|LIFECYCLE|AAPL|2021-01-01|CONT-0001|000001|ENTRY",
                "lifecycle_id": "LIFECYCLE|AAPL|2021-01-01|CONT-0001",
                "symbol": "AAPL",
                "event_timestamp": "2021-01-01T14:30:00+00:00",
                "canonical_event_type": "ENTRY",
            }
        )
        self.assertEqual(meaning.direction, MeaningDirection.NEUTRAL)
        self.assertEqual(meaning.provider, "canonical_source_event_rebuild")
        self.assertIn("NOT_TASK742_GOLDEN_REPLAY", meaning.reason_codes)
        self.assertEqual(meaning.trade_output_flag, 0)
        self.assertEqual(meaning.score_output_flag, 0)
        self.assertEqual(meaning.order_intent_flag, 0)

    def test_canonical_evidence_edge_remains_context(self) -> None:
        meaning = adapt_canonical_source_event_to_l3_meaning(
            {
                "source_event_id": "event-1",
                "lifecycle_id": "life-1",
                "symbol": "AAPL",
                "event_timestamp": "2021-01-01T14:30:00+00:00",
                "canonical_event_type": "ADD",
            }
        )
        edge = build_canonical_evidence_edge(meaning)
        self.assertEqual(edge.direction, MeaningDirection.NEUTRAL)
        self.assertEqual(edge.edge_state, L3EvidenceEdgeState.CONTEXT)
        self.assertGreater(edge.edge_weight, 0.0)
        self.assertIn("NOT_TASK742_GOLDEN_REPLAY", edge.reason_codes)

    def test_canonical_rebuild_groups_relation_graph_by_lifecycle(self) -> None:
        meanings, edges, graphs = build_canonical_l3_objects(
            (
                {
                    "source_event_id": "event-1",
                    "lifecycle_id": "life-1",
                    "symbol": "AAPL",
                    "event_timestamp": "2021-01-01T14:30:00+00:00",
                    "canonical_event_type": "ENTRY",
                },
                {
                    "source_event_id": "event-2",
                    "lifecycle_id": "life-1",
                    "symbol": "AAPL",
                    "event_timestamp": "2021-01-02T14:30:00+00:00",
                    "canonical_event_type": "EXIT",
                },
            )
        )
        self.assertEqual(len(meanings), 2)
        self.assertEqual(len(edges), 2)
        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].graph_state, L3RelationGraphState.CONTEXT_ONLY)


if __name__ == "__main__":
    unittest.main()
