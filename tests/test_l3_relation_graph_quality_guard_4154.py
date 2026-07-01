from __future__ import annotations

import unittest

from src.brain.l3_relation_graph_quality_guard_4154.builder import (
    build_coverage_gap_summary,
    build_event_cluster_limitations,
    build_graph_quality_summary,
    build_handoff_manifest,
)


class L3RelationGraphQualityGuardTests(unittest.TestCase):
    def test_graph_quality_summary_reports_singletons(self) -> None:
        graphs = [
            {"graph_family": "ENTITY_EVENT", "edge_count": "1"},
            {"graph_family": "ENTITY_EVENT", "edge_count": "2"},
        ]
        edges = [
            {"graph_family": "ENTITY_EVENT", "l1_packet_id": "l1", "l2_row_id": "l2", "source_node_id": "SYMBOL:AAPL", "target_node_id": "EVENT_CLUSTER:c1", "source_family": "public_context_news_feeds"},
            {"graph_family": "ENTITY_EVENT", "l1_packet_id": "l1b", "l2_row_id": "l2b", "source_node_id": "SYMBOL:MSFT", "target_node_id": "EVENT_CLUSTER:c2", "source_family": "public_context_news_feeds"},
            {"graph_family": "ENTITY_EVENT", "l1_packet_id": "l1c", "l2_row_id": "l2c", "source_node_id": "SYMBOL:MSFT", "target_node_id": "EVENT_CLUSTER:c2", "source_family": "public_newswire_feeds"},
        ]
        rows = build_graph_quality_summary(graphs, edges, [])
        self.assertEqual(rows[0]["graph_count"], 2)
        self.assertEqual(rows[0]["edge_count"], 3)
        self.assertEqual(rows[0]["singleton_graph_count"], 1)
        self.assertEqual(rows[0]["distinct_entity_count"], 2)

    def test_event_cluster_limitations_mark_proto_bucket(self) -> None:
        clusters = [{"event_cluster_key": "c1", "cluster_basis": "", "event_domain": "NEWS"}]
        edges = [{"target_node_id": "EVENT_CLUSTER:c1", "source_node_id": "SYMBOL:AAPL", "source_family": "public_context_news_feeds"}]
        rows = build_event_cluster_limitations(clusters, edges)
        self.assertEqual(rows[0]["event_identity_status"], "PROTO_BUCKET")
        self.assertEqual(rows[0]["same_event_assertion"], "false")
        self.assertEqual(rows[0]["edge_count"], 1)

    def test_coverage_gap_summary_preserves_non_negative_gap(self) -> None:
        gaps = [
            {"reason_code": "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE", "source_family": "public_newswire_feeds", "time_bucket": "2026-W27", "source_row_id": "m1", "l1_packet_id": "l1"}
        ]
        rows = build_coverage_gap_summary(gaps)
        self.assertEqual(rows[0]["gap_count"], 1)
        self.assertEqual(rows[0]["negative_evidence_allowed"], 0)

    def test_handoff_manifest_keeps_hard_boundaries(self) -> None:
        manifest = build_handoff_manifest(
            source_manifest={"inputs": [], "output_counts": {"l3_relation_graphs": 1}},
            quality_rows=[],
            edges=[],
            graphs=[],
            gaps=[],
            unsupported_rows=[],
        )
        self.assertTrue(manifest["diagnostic_only"])
        self.assertEqual(manifest["strategy_status"], "NOT_ACCEPTED")
        self.assertEqual(manifest["deployment_status"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(manifest["real_capital"], "FORBIDDEN")
        self.assertFalse(manifest["same_event_assertion"])


if __name__ == "__main__":
    unittest.main()

