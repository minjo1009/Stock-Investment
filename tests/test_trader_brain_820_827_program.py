from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from scripts.trader_brain_820_827_program_validate import validate as validate_program
from scripts.trader_brain_candidate_bundle_validate import validate_candidate_bundles
from scripts.trader_brain_provenance_coverage_audit import audit_graph
from scripts.trader_brain_relationship_graph_packet_validate import validate_graph_dir


ROOT = Path(__file__).resolve().parents[1]
SEMI_GRAPH = ROOT / "docs/reports/task_821_graph_fixture_corpus_expansion/fixtures/semiconductor_export_control_graph"
SPACE_GRAPH = ROOT / "docs/reports/task_821_graph_fixture_corpus_expansion/fixtures/space_defense_policy_graph"
PROVENANCE = ROOT / "docs/reports/task_816_provenance_manifest_linker_contract/provenance_manifest.csv"
BUNDLES = ROOT / "docs/reports/task_823_candidate_bundle_adapter_contract/candidate_bundles.csv"
READINESS = ROOT / "docs/reports/task_826_backtest_adapter_readiness_checklist/backtest_adapter_readiness_checklist.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain820827ProgramTest(unittest.TestCase):
    def test_task821_expanded_graph_fixtures_pass(self) -> None:
        self.assertEqual([], validate_graph_dir(SEMI_GRAPH))
        self.assertEqual([], validate_graph_dir(SPACE_GRAPH))

    def test_task822_provenance_coverage_has_no_orphans(self) -> None:
        rows = audit_graph(SEMI_GRAPH, PROVENANCE) + audit_graph(SPACE_GRAPH, PROVENANCE)
        self.assertTrue(rows)
        self.assertTrue(all(row["coverage_state"] == "covered" for row in rows))

    def test_task823_candidate_bundles_validate(self) -> None:
        self.assertEqual([], validate_candidate_bundles(BUNDLES))
        states = {row["bundle_state"] for row in read_csv(BUNDLES)}
        self.assertIn("blocked_by_contradiction", states)
        self.assertIn("blocked_by_gap", states)

    def test_task823_candidate_bundle_blocks_forbidden_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate_bundles.csv"
            rows = read_csv(BUNDLES)
            rows[0]["thesis_question"] = "buy_signal should never appear here"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            self.assertTrue(any("forbidden output marker buy_signal" in error for error in validate_candidate_bundles(path)))

    def test_task826_backtest_adapter_readiness_is_not_ready(self) -> None:
        rows = read_csv(READINESS)
        self.assertTrue(rows)
        self.assertTrue(all(row["status"] == "not_ready" for row in rows))

    def test_task820_827_program_validator_passes(self) -> None:
        self.assertEqual([], validate_program())


if __name__ == "__main__":
    unittest.main()
