from __future__ import annotations

import unittest

from src.brain.l3_relation_graph_v2_4152.builder import (
    bucket_time,
    coverage_graph_key,
    is_newswire_unknown_collapse,
    relation_edges_for_meaning,
)
from src.brain.l3_relation_graph_v2_4152.contracts import GraphFamily


class L3RelationGraphV2Tests(unittest.TestCase):
    def test_bucket_time_uses_iso_week(self) -> None:
        self.assertEqual(bucket_time("2026-06-30T10:00:00Z"), "2026-W27")

    def test_newswire_unknown_collapse_detected(self) -> None:
        row = {
            "source_family": "public_newswire_feeds",
            "target_node_type": "SOURCE_FAMILY",
            "target_node_key": "public_newswire_feeds",
            "economic_dimension": "UNKNOWN",
        }
        self.assertTrue(is_newswire_unknown_collapse(row))

    def test_entity_symbol_creates_event_and_dimension_edges(self) -> None:
        meaning = {
            "l3_meaning_id": "m1",
            "l1_packet_id": "l1",
            "l2_row_id": "l2",
            "source_family": "public_context_news_feeds",
            "provider": "public_context_news_feeds",
            "target_node_type": "SYMBOL",
            "target_node_key": "AAPL",
            "economic_dimension": "REGULATORY",
            "direction_review": "RISK_REVIEW",
            "event_time": "2026-06-30",
        }
        context = {"source_artifact": "l3_meanings.jsonl", "mapping_status": "HIGH_CONFIDENCE", "admission_status": "READY"}
        edges = relation_edges_for_meaning(meaning, context, "event_cluster:abc", "2026-W27")
        families = {edge.graph_family for edge in edges}
        self.assertIn(GraphFamily.SOURCE_EVENT_CLUSTER, families)
        self.assertIn(GraphFamily.ENTITY_EVENT, families)
        self.assertIn(GraphFamily.ENTITY_DIMENSION, families)
        self.assertTrue(all(not edge.raw_l0_read for edge in edges))
        self.assertTrue(all(edge.l1_packet_id and edge.l2_row_id for edge in edges))

    def test_coverage_gap_key_is_stable(self) -> None:
        left = coverage_graph_key("NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE", "public_newswire_feeds", "2026-W27")
        right = coverage_graph_key("NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE", "public_newswire_feeds", "2026-W27")
        self.assertEqual(left, right)
        self.assertIn("coverage_gap", left)


if __name__ == "__main__":
    unittest.main()

