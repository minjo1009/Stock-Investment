from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from scripts.trader_brain_relationship_graph_packet_validate import validate_graph_dir
from scripts.trader_brain_attention_packet_validate import validate_packet_file


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def valid_nodes() -> list[dict[str, str]]:
    base = {
        "source_artifact": "docs/reports/task_773_attention_budget_contract",
        "source_event_id": "src_evt_1",
        "evidence_id": "ev_1",
        "uncertainty_cap": "none",
        "forbidden_output_audit": "no buy sell rank score sizing backtest eligibility",
        "mechanism_id": "mech_ai_capex",
        "predecessor_node_id": "",
        "edge_evidence_id": "edge_ev_1",
        "review_owner": "Research Governance",
    }
    return [
        {
            **base,
            "info_node_id": "node_l1",
            "node_type": "attention_packet",
            "asof_ts": "2026-06-01T10:00:00+00:00",
            "layer": "L1",
            "review_state": "enough_for_review",
        },
        {
            **base,
            "info_node_id": "node_l2",
            "node_type": "salience",
            "asof_ts": "2026-06-01T10:01:00+00:00",
            "layer": "L2",
            "review_state": "enough_for_review",
            "predecessor_node_id": "node_l1",
        },
        {
            **base,
            "info_node_id": "node_l3",
            "node_type": "mechanism",
            "asof_ts": "2026-06-01T10:02:00+00:00",
            "layer": "L3",
            "review_state": "cap",
            "predecessor_node_id": "node_l2",
        },
    ]


def valid_edges() -> list[dict[str, str]]:
    return [
        {
            "edge_id": "edge_1",
            "from_node_id": "node_l1",
            "to_node_id": "node_l2",
            "edge_type": "sequences",
            "required_evidence": "predecessor_node_id and exact asof_ts",
            "edge_evidence_id": "edge_ev_1",
            "asof_ts": "2026-06-01T10:01:00+00:00",
            "review_owner": "Backtest & Simulation Infra",
            "mechanism_id": "",
            "predecessor_node_id": "node_l1",
            "affected_node_id": "",
            "missing_source_family": "",
        },
        {
            "edge_id": "edge_2",
            "from_node_id": "node_l2",
            "to_node_id": "node_l3",
            "edge_type": "explains",
            "required_evidence": "mechanism_id and source family",
            "edge_evidence_id": "edge_ev_2",
            "asof_ts": "2026-06-01T10:02:00+00:00",
            "review_owner": "Regime Research",
            "mechanism_id": "mech_ai_capex",
            "predecessor_node_id": "",
            "affected_node_id": "",
            "missing_source_family": "",
        },
    ]


def valid_transitions() -> list[dict[str, str]]:
    return [
        {
            "from_node_id": "node_l1",
            "to_node_id": "node_l2",
            "from_layer": "L1",
            "to_layer": "L2",
            "required_intermediate": "attention_packet_id",
            "intermediate_ref": "pkt_1",
        },
        {
            "from_node_id": "node_l2",
            "to_node_id": "node_l3",
            "from_layer": "L2",
            "to_layer": "L3",
            "required_intermediate": "salience_class",
            "intermediate_ref": "mechanism_core",
        },
    ]


def valid_attention_rows() -> list[dict[str, str]]:
    return [
        {
            "attention_packet_id": "pkt_1",
            "asof_ts": "2026-06-01T10:00:00+00:00",
            "source_event_id": "src_evt_1",
            "evidence_id": "ev_1",
            "source_family": "filing",
            "thesis_question": "does capex mechanism matter",
            "minimal_fact": "source-backed AI capex mechanism",
            "uncertainty_cap": "none",
            "sufficiency_state": "enough_for_review",
            "owner_next_check": "none",
            "forbidden_output_audit": "no buy sell rank score sizing backtest eligibility",
        }
    ]


class RelationshipGraphPacketValidatorTest(unittest.TestCase):
    def write_graph(self, root: Path, *, nodes=None, edges=None, transitions=None) -> None:
        write_csv(root / "nodes.csv", nodes or valid_nodes())
        write_csv(root / "edges.csv", edges or valid_edges())
        write_csv(root / "transitions.csv", transitions or valid_transitions())

    def test_valid_graph_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_graph(root)
            self.assertEqual([], validate_graph_dir(root))

    def test_negative_edge_without_required_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            edges = valid_edges()
            edges[0]["required_evidence"] = ""
            self.write_graph(root, edges=edges)
            self.assertTrue(any("missing required_evidence" in error for error in validate_graph_dir(root)))

    def test_negative_node_without_asof_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nodes = valid_nodes()
            nodes[0]["asof_ts"] = ""
            self.write_graph(root, nodes=nodes)
            self.assertTrue(any("missing asof_ts" in error for error in validate_graph_dir(root)))

    def test_negative_sequence_without_predecessor_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            edges = valid_edges()
            edges[0]["predecessor_node_id"] = ""
            self.write_graph(root, edges=edges)
            self.assertTrue(any("temporal_identity_missing" in error for error in validate_graph_dir(root)))

    def test_negative_source_gap_to_negative_fails_attention_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "attention_packets.csv"
            rows = valid_attention_rows()
            rows[0]["sufficiency_state"] = "source_gap"
            rows[0]["minimal_fact"] = "negative label because source missing"
            write_csv(path, rows)
            self.assertTrue(any("missing_to_negative_detected" in error for error in validate_packet_file(path)))

    def test_negative_expert_opinion_to_signal_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            edges = valid_edges()
            edges[1]["required_evidence"] = "expert_opinion_to_signal buy_signal"
            self.write_graph(root, edges=edges)
            self.assertTrue(any("forbidden output marker buy_signal" in error for error in validate_graph_dir(root)))

    def test_negative_mechanism_without_mechanism_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            edges = valid_edges()
            edges[1]["mechanism_id"] = ""
            self.write_graph(root, edges=edges)
            self.assertTrue(any("mechanism_identity_missing" in error for error in validate_graph_dir(root)))

    def test_negative_cross_layer_jump_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transitions = valid_transitions()
            transitions[0]["to_layer"] = "L7"
            self.write_graph(root, transitions=transitions)
            self.assertTrue(any("cross_layer_jump_detected" in error for error in validate_graph_dir(root)))

    def test_valid_attention_packet_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "attention_packets.csv"
            write_csv(path, valid_attention_rows())
            self.assertEqual([], validate_packet_file(path))


if __name__ == "__main__":
    unittest.main()
