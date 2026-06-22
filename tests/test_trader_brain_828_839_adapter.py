from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from scripts.trader_brain_828_839_program_validate import validate as validate_program
from scripts.trader_brain_adapter_eligibility_validate import validate_bundles
from scripts.trader_brain_adapter_input_builder import build_adapter_inputs


ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / "docs/reports/task_833_candidate_bundle_expansion_pack/expanded_candidate_bundles.csv"
NEGATIVE = ROOT / "docs/reports/task_834_negative_adapter_fixture_pack/negative_adapter_bundles.csv"
GRAPH_MANIFEST = ROOT / "docs/reports/task_831_source_time_namespace_contract/graph_packet_manifest.csv"
ADAPTER_INPUTS = ROOT / "docs/reports/task_836_controlled_adapter_input_builder/adapter_inputs.csv"
AUDIT = ROOT / "docs/reports/task_837_adapter_output_audit_report/adapter_eligibility_audit.csv"
SUMMARY = ROOT / "docs/reports/task_838_adapter_dry_run_governance_gate/adapter_dry_run_gate_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain828839AdapterTest(unittest.TestCase):
    def test_eligibility_validator_allows_only_clean_research_bundles(self) -> None:
        audit_rows, errors = validate_bundles(BUNDLES, GRAPH_MANIFEST)
        self.assertEqual([], errors)
        self.assertEqual(2, sum(1 for row in audit_rows if row["eligibility_state"] == "eligible"))
        self.assertEqual(10, sum(1 for row in audit_rows if row["eligibility_state"] == "blocked"))

    def test_negative_adapter_fixtures_fail(self) -> None:
        _audit_rows, errors = validate_bundles(NEGATIVE, GRAPH_MANIFEST)
        joined = "\n".join(errors)
        for expected in ["future_edge_leakage", "unknown_graph_id", "forbidden_output_marker", "source_gap_to_eligible", "unknown_node_id", "unknown_edge_id"]:
            self.assertIn(expected, joined)

    def test_builder_outputs_only_two_dry_adapter_rows(self) -> None:
        adapter_rows, audit_rows, errors = build_adapter_inputs(BUNDLES, GRAPH_MANIFEST)
        self.assertEqual([], errors)
        self.assertEqual(2, len(adapter_rows))
        self.assertEqual(12, len(audit_rows))
        self.assertTrue(all(row["adapter_input_state"] == "dry_adapter_input" for row in adapter_rows))

    def test_generated_adapter_outputs_match_contract(self) -> None:
        adapter_rows = read_csv(ADAPTER_INPUTS)
        audit_rows = read_csv(AUDIT)
        self.assertEqual(2, len(adapter_rows))
        self.assertEqual(12, len(audit_rows))
        forbidden_fields = {"buy_signal", "sell_signal", "alpha_score", "position_sizing", "backtest_eligibility"}
        combined = "\n".join(",".join(row.values()).lower() for row in adapter_rows)
        self.assertTrue(all(marker not in combined for marker in forbidden_fields))

    def test_gate_summary_is_diagnostic_only(self) -> None:
        row = read_csv(SUMMARY)[0]
        self.assertEqual("diagnostic_only_pass", row["gate_status"])
        self.assertEqual("NOT_ACCEPTED", row["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", row["deployment_status"])
        self.assertEqual("FORBIDDEN", row["real_capital"])
        self.assertEqual("2", row["adapter_input_count"])

    def test_program_validator_passes(self) -> None:
        self.assertEqual([], validate_program())

    def test_future_leakage_mutation_fails(self) -> None:
        rows = read_csv(BUNDLES)
        rows[0]["asof_ts"] = "2026-06-01T13:00:30+00:00"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundles.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            _audit_rows, errors = validate_bundles(path, GRAPH_MANIFEST)
        self.assertTrue(any("future_" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
