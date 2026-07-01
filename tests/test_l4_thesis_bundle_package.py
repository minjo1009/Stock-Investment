from __future__ import annotations

import json
import tempfile
import unittest
import hashlib
from pathlib import Path

from src.brain.l4_thesis_bundle.builder import (
    build_bundle,
    build_evidence_links_for_graph,
    stable_id,
)
from src.validation.l4_thesis_bundle_validator import validate_l4_package


class L4ThesisBundlePackageTests(unittest.TestCase):
    def test_bundle_preserves_hard_boundaries(self) -> None:
        graph = sample_graph("ENTITY_EVENT")
        evidence = build_evidence_links_for_graph("b1", graph, [sample_edge()], {"l1": {"source_url": "u"}}, {"l2": {"feature_namespace": "REGULATORY"}}, {}, {})
        bundle = build_bundle(graph, [sample_edge()], [], {}, "b1", "2026-06-30T00:00:00Z", evidence, [], {})
        self.assertTrue(bundle["diagnostic_only"])
        self.assertEqual(bundle["strategy_status"], "NOT_ACCEPTED")
        self.assertEqual(bundle["deployment_status"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(bundle["real_capital"], "FORBIDDEN")
        self.assertFalse(bundle["same_event_assertion"])

    def test_source_event_cluster_stays_proto(self) -> None:
        graph = sample_graph("SOURCE_EVENT_CLUSTER")
        evidence = build_evidence_links_for_graph("b1", graph, [sample_edge()], {"l1": {}}, {"l2": {}}, {}, {})
        bundle = build_bundle(graph, [sample_edge()], [], {}, "b1", "2026-06-30T00:00:00Z", evidence, [], {})
        self.assertEqual(bundle["event_identity_status"], "PROTO_BUCKET")
        self.assertFalse(bundle["same_event_assertion"])

    def test_raw_only_supporting_evidence_is_blocked(self) -> None:
        graph = sample_graph("ENTITY_EVENT")
        edge = sample_edge()
        edge["l1_packet_id"] = ""
        edge["l2_row_id"] = ""
        evidence = build_evidence_links_for_graph("b1", graph, [edge], {}, {}, {}, {})
        self.assertEqual(evidence[0]["lineage_status"], "BLOCKED")
        self.assertEqual(evidence[0]["evidence_quality_flag"], "BLOCKED")

    def test_stable_ids_are_deterministic(self) -> None:
        self.assertEqual(stable_id("x", "a", "b"), stable_id("x", "a", "b"))
        self.assertNotEqual(stable_id("x", "a", "b"), stable_id("x", "a", "c"))

    def test_validator_rejects_forbidden_authority_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_package(out, extra_bundle_field={"order_intent": "BUY"})
            result = validate_l4_package(out)
            self.assertEqual(result["status"], "FAIL")

    def test_validator_accepts_blocked_mixed_diagnostic_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_package(out)
            result = validate_l4_package(out)
            self.assertEqual(result["status"], "PASS")

    def test_contradiction_not_scanned_rejects_complete_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_package(out, extra_bundle_field={"coverage_status": "COMPLETE"})
            result = validate_l4_package(out)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("CONTRADICTION_NOT_SCANNED" in failure or "L0 is incomplete" in failure for failure in result["failures"]))

    def test_manifest_source_inputs_require_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_package(out)
            manifest_path = out / "l4_run_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source_inputs"][0]["sha256"] = ""
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = validate_l4_package(out)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("sha256 missing" in failure for failure in result["failures"]))


def sample_graph(family: str) -> dict[str, str]:
    return {
        "graph_key": f"g:{family}",
        "graph_family": family,
        "target_type": "SYMBOL",
        "target_key": "AAPL",
        "economic_dimension": "REGULATORY",
        "source_scope": "public_context_news_feeds",
        "time_bucket": "2026-W26",
        "window_start": "2026-W26",
        "window_end": "2026-W26",
        "edge_count": "1",
        "coverage_state": "LINEAGED",
        "lineage_complete": "1",
    }


def sample_edge() -> dict[str, str]:
    return {
        "edge_id": "e1",
        "graph_key": "g:ENTITY_EVENT",
        "graph_family": "ENTITY_EVENT",
        "source_node_id": "SYMBOL:AAPL",
        "target_node_id": "EVENT_CLUSTER:c1",
        "edge_type": "entity_to_event_cluster",
        "source_artifact": "artifact",
        "source_row_id": "src1",
        "l1_packet_id": "l1",
        "l2_row_id": "l2",
        "source_family": "public_context_news_feeds",
        "source_provider": "public_context_news_feeds",
        "mapping_status": "HIGH_CONFIDENCE_DETERMINISTIC",
        "admission_status": "READY",
        "economic_dimension": "REGULATORY",
        "direction_review": "RISK_REVIEW",
        "evidence_time": "2026-06-30T00:00:00Z",
    }


def write_package(out: Path, extra_bundle_field: dict[str, object] | None = None) -> None:
    bundle = {
        "schema_version": "l4_thesis_bundle.v0.1",
        "task_id": "TASK-4156",
        "bundle_id": "b1",
        "created_at_utc": "2026-06-30T00:00:00Z",
        "diagnostic_only": True,
        "strategy_status": "NOT_ACCEPTED",
        "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "no_broker_mutation": True,
        "no_live_order": True,
        "no_paper_promotion": True,
        "bundle_status": "DRAFT_MIXED",
        "institutional_quality_status": "MIXED",
        "thesis_type": "ENTITY_EVENT",
        "thesis_statement": "Review only.",
        "thesis_scope": "single_entity",
        "primary_symbols": ["AAPL"],
        "primary_entity_ids": [],
        "source_lanes": ["public_context_news_feeds"],
        "time_window_start_utc": "2026-W26",
        "time_window_end_utc": "2026-W26",
        "l3_graph_ids": ["g1"],
        "l3_graph_families": ["ENTITY_EVENT"],
        "l3_event_cluster_ids": ["c1"],
        "event_identity_status": "GRAPH_RELATION_CANDIDATE",
        "same_event_assertion": False,
        "supporting_evidence_count": 1,
        "context_evidence_count": 0,
        "contradicting_evidence_count": 0,
        "coverage_gap_count": 0,
        "lineage_status": "OK",
        "source_access_status": "OK",
        "coverage_status": "INCOMPLETE",
        "contradiction_status": "NOT_SCANNED_BLOCKER",
        "relation_quality_status": "MIXED",
        "thesis_specificity_score": 80,
        "evidence_linkage_score": 100,
        "source_traceability_score": 100,
        "contradiction_handling_score": None,
        "institutional_quality_score": None,
        "block_reasons": ["CONTRADICTION_NOT_SCANNED"],
        "warnings": ["CONTRADICTION_NOT_SCANNED"],
    }
    if extra_bundle_field:
        bundle.update(extra_bundle_field)
    evidence = {
        "schema_version": "l4_evidence_link.v0.1",
        "bundle_id": "b1",
        "evidence_link_id": "ev1",
        "evidence_role": "supporting",
        "evidence_claim": "diagnostic only",
        "source_lane": "public_context_news_feeds",
        "source_id": "src1",
        "source_url_or_path": "path",
        "publisher_or_origin": "origin",
        "source_time_utc": "2026-06-30T00:00:00Z",
        "ingested_at_utc": "2026-06-30T00:00:00Z",
        "l1_packet_id": "l1",
        "l1_mapping_status": "READY",
        "l2_feature_id": "l2",
        "l2_feature_family": "REGULATORY",
        "l3_edge_id": "e1",
        "l3_graph_id": "g1",
        "l3_graph_family": "ENTITY_EVENT",
        "lineage_status": "OK",
        "source_access_status": "OK",
        "mapping_confidence": "HIGH",
        "evidence_quality_flag": "USABLE_DIAGNOSTIC",
        "negative_evidence_allowed": "False",
    }
    blocker = {
        "schema_version": "l4_blocker.v0.1",
        "bundle_id": "b1",
        "blocker_id": "blk1",
        "blocker_type": "CONTRADICTION_NOT_SCANNED",
        "severity": "P0",
        "source_layer": "L3",
        "related_artifact_id": "g1",
        "reason": "not scanned",
        "required_action": "IMPLEMENT_CONTRADICTION_SCAN",
        "is_hard_blocker": "True",
        "negative_evidence_allowed": "False",
    }
    source_path = out / "fixture_source.csv"
    source_path.write_text("id\n1\n", encoding="utf-8")
    manifest = {
        "schema_version": "l4_run_manifest.v0.1",
        "task_id": "TASK-4156",
        "created_at_utc": "2026-06-30T00:00:00Z",
        "diagnostic_only": True,
        "hard_boundaries": {
            "strategy_status": "NOT_ACCEPTED",
            "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "no_broker_mutation": True,
            "no_live_order": True,
            "no_paper_promotion": True,
        },
        "input_artifacts": [{"role": "fixture_source", "path": str(source_path), "exists": True}],
        "source_inputs": [
            {
                "role": "fixture_source",
                "path": str(source_path),
                "exists": True,
                "row_count": 1,
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "mtime_utc": "2026-06-30T00:00:00Z",
            }
        ],
        "l0_coverage_state": {"public_context_news_feeds": {"incomplete": True}},
        "bundle_count": 1,
        "evidence_link_count": 1,
        "blocker_count": 1,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "l4_thesis_bundles.jsonl").write_text(json.dumps(bundle) + "\n", encoding="utf-8")
    write_csv(out / "l4_thesis_evidence_links.csv", [evidence])
    write_csv(out / "l4_thesis_blockers.csv", [blocker])
    (out / "l4_run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    import csv

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
