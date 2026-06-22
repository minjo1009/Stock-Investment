from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from scripts.trader_brain_attention_packet_validate import validate_packet_file
from scripts.trader_brain_graph_batch_validate import build_report_rows
from scripts.trader_brain_provenance_manifest_linker_validate import validate_graph_provenance
from scripts.trader_brain_relationship_graph_governance_gate import FOOTER
from scripts.trader_brain_relationship_graph_packet_validate import validate_graph_dir


ROOT = Path(__file__).resolve().parents[1]
AI_GRAPH = ROOT / "docs/reports/task_813_golden_graph_fixture_pack/fixtures/ai_capex_mechanism_graph"
MACRO_GRAPH = ROOT / "docs/reports/task_813_golden_graph_fixture_pack/fixtures/macro_policy_source_gap_graph"
ATTENTION = ROOT / "docs/reports/task_815_attention_packet_fixture_corpus/fixtures/attention_packets.csv"
BATCH_MANIFEST = ROOT / "docs/reports/task_814_graph_batch_runner_contract/batch_manifest.csv"
PROVENANCE = ROOT / "docs/reports/task_816_provenance_manifest_linker_contract/provenance_manifest.csv"
GOVERNANCE_SUMMARY = ROOT / "docs/reports/task_818_ci_governance_gate_contract/governance_gate_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrainNext8OperationalHardeningTest(unittest.TestCase):
    def test_task813_golden_graph_fixtures_pass(self) -> None:
        self.assertEqual([], validate_graph_dir(AI_GRAPH))
        self.assertEqual([], validate_graph_dir(MACRO_GRAPH))

    def test_task815_attention_corpus_passes_and_preserves_states(self) -> None:
        self.assertEqual([], validate_packet_file(ATTENTION))
        states = {row["sufficiency_state"] for row in read_csv(ATTENTION)}
        self.assertEqual({"enough_for_review", "defer", "source_gap", "block", "noise"}, states)

    def test_task814_batch_runner_reports_expected_failure(self) -> None:
        rows, all_expected = build_report_rows(BATCH_MANIFEST)
        self.assertTrue(all_expected)
        failure_rows = [row for row in rows if row["observed_status"] == "fail"]
        self.assertEqual(1, len(failure_rows))
        self.assertEqual("missing_required_evidence", failure_rows[0]["failure_class"])

    def test_task816_provenance_linker_passes_golden_graphs(self) -> None:
        self.assertEqual([], validate_graph_provenance(AI_GRAPH, PROVENANCE))
        self.assertEqual([], validate_graph_provenance(MACRO_GRAPH, PROVENANCE))

    def test_task816_provenance_linker_detects_orphan_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "provenance_manifest.csv"
            rows = [row for row in read_csv(PROVENANCE) if row["evidence_id"] != "edge_ev_ai_explains_001"]
            with manifest.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            errors = validate_graph_provenance(AI_GRAPH, manifest)
            self.assertTrue(any("manifest_orphan" in error for error in errors))

    def test_task818_governance_summary_is_diagnostic_only(self) -> None:
        rows = read_csv(GOVERNANCE_SUMMARY)
        self.assertEqual("diagnostic_only_pass", rows[0]["gate_status"])
        self.assertEqual("NOT_ACCEPTED", rows[0]["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", rows[0]["deployment_status"])
        self.assertEqual("FORBIDDEN", rows[0]["real_capital"])
        self.assertEqual(FOOTER, rows[0]["footer"])


if __name__ == "__main__":
    unittest.main()
