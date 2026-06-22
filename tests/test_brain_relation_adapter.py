from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainRelationAdapter(unittest.TestCase):
    def _meaning(self, meaning_id: str = "meaning-1", **overrides):
        from brain.contracts import EconomicMeaning, MeaningDirection

        fields = {
            "meaning_id": meaning_id,
            "asof_ts": "2026-06-20T00:00:00Z",
            "symbol": "TEST",
            "direction": MeaningDirection.SUPPORTIVE,
            "confidence": 0.7,
            "uncertainty_flags": (),
            "source_packet_ids": (f"source-{meaning_id}",),
            "relation_readiness": "directional",
        }
        fields.update(overrides)
        return EconomicMeaning(**fields)

    def test_directional_meanings_build_supportive_edge_and_thesis(self) -> None:
        from brain.contracts import RelationEdgeType, SourceGap, ThesisInvalidationState
        from brain.relation_adapter import build_meaning_relation_edge, build_thesis_bundle_from_relation_edge

        edge = build_meaning_relation_edge(
            [self._meaning("meaning-1"), self._meaning("meaning-2", confidence=0.5)],
            relation_edge_id="edge-1",
        )
        thesis = build_thesis_bundle_from_relation_edge(edge, trade_spec_id="trade-spec-1")

        self.assertEqual(edge.edge_type, RelationEdgeType.SUPPORTS_THESIS)
        self.assertEqual(edge.confidence_floor, 0.5)
        self.assertEqual(edge.source_gaps, (SourceGap.NONE,))
        self.assertEqual(thesis.thesis_id, "thesis:edge-1")
        self.assertEqual(thesis.meaning_ids, edge.meaning_ids)
        self.assertEqual(thesis.invalidation_state, ThesisInvalidationState.NONE)

    def test_context_only_meanings_do_not_create_directional_edge(self) -> None:
        from brain.contracts import MeaningDirection, RelationEdgeType
        from brain.relation_adapter import build_meaning_relation_edge

        edge = build_meaning_relation_edge(
            [
                self._meaning("meaning-1", direction=MeaningDirection.NEUTRAL, relation_readiness="context_only"),
                self._meaning("meaning-2", direction=MeaningDirection.UNKNOWN, relation_readiness="context_only"),
            ],
            relation_edge_id="edge-1",
        )

        self.assertEqual(edge.edge_type, RelationEdgeType.CONTEXT_ONLY)
        self.assertIn("CONTEXT_ONLY_NOT_DIRECTIONAL", edge.blocker_flags)

    def test_not_ready_meaning_blocks_relation_edge(self) -> None:
        from brain.contracts import RelationEdgeType
        from brain.relation_adapter import build_meaning_relation_edge

        edge = build_meaning_relation_edge(
            [self._meaning(relation_readiness="not_ready", uncertainty_flags=("prior_context_missing",))],
            relation_edge_id="edge-1",
        )

        self.assertEqual(edge.edge_type, RelationEdgeType.BLOCKED_NOT_READY)
        self.assertIn("RELATION_NOT_READY", edge.blocker_flags)
        self.assertIn("SOURCE_GAP_FLAGS_PRESENT", edge.blocker_flags)

    def test_relation_edge_rejects_symbol_mismatch(self) -> None:
        from brain.relation_adapter import build_meaning_relation_edge

        with self.assertRaises(ValueError):
            build_meaning_relation_edge(
                [self._meaning("meaning-1"), self._meaning("meaning-2", symbol="OTHER")],
                relation_edge_id="edge-1",
            )

    def test_relation_edge_rejects_future_meaning_asof(self) -> None:
        from brain.relation_adapter import build_meaning_relation_edge

        with self.assertRaises(ValueError):
            build_meaning_relation_edge(
                [self._meaning(asof_ts="2026-06-21T00:00:00Z")],
                relation_edge_id="edge-1",
                decision_asof_ts="2026-06-20T00:00:00Z",
            )

    def test_package_exports_relation_adapter(self) -> None:
        import brain

        expected_exports = {
            "MeaningRelationEdge",
            "RelationEdgeType",
            "build_meaning_relation_edge",
            "build_thesis_bundle_from_relation_edge",
            "assert_relation_edge_thesis_chain",
        }

        self.assertTrue(expected_exports.issubset(set(brain.__all__)))
        for export_name in expected_exports:
            self.assertTrue(hasattr(brain, export_name), export_name)


if __name__ == "__main__":
    unittest.main()
