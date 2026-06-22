from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK689_DIR = Path("docs/reports/task_689_interpretation_edge_quality")
FORBIDDEN_COLUMNS = {
    "net_return_from_entry",
    "net_return_pct",
    "return_pct",
    "win_flag",
    "win_eval_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "simulated_exit_price",
    "simulated_exit_ts",
}


class Task689InterpretationEdgeQualityTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task689_sector_edge_rulebook.csv",
            "task689_interpretation_quality_panel.csv",
            "task689_edge_quality_panel.csv",
            "task689_candidate_weak_layer_audit.csv",
            "task689_integrity_audit.csv",
            "task_689_decision.csv",
            "task_689_pass_fail_matrix.csv",
            "task_689_interpretation_edge_quality.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK689_DIR / name).exists(), name)

    def test_quality_outputs_do_not_include_outcomes(self) -> None:
        for name in [
            "task689_interpretation_quality_panel.csv",
            "task689_edge_quality_panel.csv",
            "task689_candidate_weak_layer_audit.csv",
        ]:
            frame = pd.read_csv(TASK689_DIR / name, nrows=1)
            self.assertFalse(FORBIDDEN_COLUMNS.intersection(frame.columns), name)

    def test_sector_edge_rules_and_weak_layers_are_decomposed(self) -> None:
        rulebook = pd.read_csv(TASK689_DIR / "task689_sector_edge_rulebook.csv")
        weak = pd.read_csv(TASK689_DIR / "task689_candidate_weak_layer_audit.csv")
        edge = pd.read_csv(TASK689_DIR / "task689_edge_quality_panel.csv")

        self.assertGreaterEqual(rulebook["sector_family"].nunique(), 5)
        self.assertGreaterEqual(edge["sector_family"].nunique(), 5)
        self.assertGreaterEqual(weak["weakest_layer"].nunique(), 3)
        self.assertEqual(weak["lifecycle_id"].nunique(), len(weak))

    def test_macro_edges_remain_diagnostic_only(self) -> None:
        edge = pd.read_csv(TASK689_DIR / "task689_edge_quality_panel.csv")
        macro = edge[edge["from_node"].eq("macro_context")]

        self.assertGreater(len(macro), 0)
        self.assertEqual(int(macro["eligible_for_slot_assignment_flag"].sum()), 0)
        self.assertTrue(macro["refined_edge_type"].eq("diagnostic_context").all())

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK689_DIR / "task689_integrity_audit.csv")
        decision = pd.read_csv(TASK689_DIR / "task_689_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
