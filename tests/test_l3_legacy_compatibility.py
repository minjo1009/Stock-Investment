from __future__ import annotations

import unittest

from src.brain.contracts import MeaningDirection, MeaningRelationEdgeType
from src.brain.meaning_adapter import adapt_task742_row_to_economic_meaning
from src.brain.relation_adapter import build_legacy_relation_edge
from src.brain.l3.adapters.task742_legacy_adapter import adapt_task742_row_to_l3_v2
from src.brain.l3.contracts import L3CalibrationStatus


class L3LegacyCompatibilityTest(unittest.TestCase):
    def test_task742_adapter_preserves_static_mapping(self) -> None:
        meaning = adapt_task742_row_to_economic_meaning(
            {
                "meaning_id": "m1",
                "asof_ts": "2026-06-01T10:00:00Z",
                "symbol": "AAPL",
                "lifecycle_id": "life-1",
                "economic_direction_hint": "positive",
                "confidence_band": "medium",
                "relation_readiness": "directional",
                "source_packet_ids": "p1,p2",
            }
        )
        self.assertEqual(meaning.direction, MeaningDirection.SUPPORTIVE)
        self.assertEqual(meaning.confidence, 0.60)
        edge = build_legacy_relation_edge((meaning,))
        self.assertEqual(edge.edge_type, MeaningRelationEdgeType.SUPPORTS_THESIS)

    def test_legacy_not_ready_still_blocks_legacy_edge(self) -> None:
        ready = adapt_task742_row_to_economic_meaning(
            {
                "meaning_id": "m1",
                "asof_ts": "2026-06-01T10:00:00Z",
                "symbol": "AAPL",
                "lifecycle_id": "life-1",
                "economic_direction_hint": "positive",
                "confidence_band": "medium",
                "relation_readiness": "directional",
            }
        )
        not_ready = adapt_task742_row_to_economic_meaning(
            {
                "meaning_id": "m2",
                "asof_ts": "2026-06-01T10:00:00Z",
                "symbol": "AAPL",
                "lifecycle_id": "life-1",
                "economic_direction_hint": "neutral",
                "confidence_band": "low",
                "relation_readiness": "not_ready",
            }
        )
        edge = build_legacy_relation_edge((ready, not_ready))
        self.assertEqual(edge.edge_type, MeaningRelationEdgeType.BLOCKED_NOT_READY)

    def test_task742_l3_v2_wrapper_is_not_calibrated(self) -> None:
        meaning = adapt_task742_row_to_l3_v2(
            {
                "meaning_id": "m1",
                "asof_ts": "2026-06-01T10:00:00Z",
                "symbol": "AAPL",
                "lifecycle_id": "life-1",
                "economic_direction_hint": "positive",
                "confidence_band": "medium",
                "relation_readiness": "directional",
            }
        )
        self.assertEqual(meaning.runtime_context, "HISTORICAL_RESEARCH")
        self.assertFalse(meaning.source_time_certified)
        self.assertEqual(meaning.confidence.calibration_status, L3CalibrationStatus.NOT_CALIBRATED)
        self.assertIsNone(meaning.confidence.calibrated_probability)


if __name__ == "__main__":
    unittest.main()
