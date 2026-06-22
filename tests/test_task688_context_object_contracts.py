from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK688_DIR = Path("docs/reports/task_688_context_object_contracts")
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


class Task688ContextObjectContractsTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task688_evidence_objects.csv",
            "task688_economic_interpretation_objects.csv",
            "task688_state_graph_edges.csv",
            "task688_candidate_context_bundles.csv",
            "task688_slot_decision_explanations.csv",
            "task688_contract_integrity_audit.csv",
            "task_688_decision.csv",
            "task_688_pass_fail_matrix.csv",
            "task_688_context_object_contracts.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK688_DIR / name).exists(), name)

    def test_candidate_level_layers_match_lifecycle_count(self) -> None:
        bundles = pd.read_csv(TASK688_DIR / "task688_candidate_context_bundles.csv")
        slot = pd.read_csv(TASK688_DIR / "task688_slot_decision_explanations.csv")

        self.assertEqual(len(bundles), len(slot))
        self.assertEqual(bundles["lifecycle_id"].nunique(), len(bundles))
        self.assertEqual(slot["lifecycle_id"].nunique(), len(slot))

    def test_no_outcome_columns_in_object_layers(self) -> None:
        for name in [
            "task688_evidence_objects.csv",
            "task688_economic_interpretation_objects.csv",
            "task688_state_graph_edges.csv",
            "task688_candidate_context_bundles.csv",
            "task688_slot_decision_explanations.csv",
        ]:
            frame = pd.read_csv(TASK688_DIR / name, nrows=1)
            self.assertFalse(FORBIDDEN_COLUMNS.intersection(frame.columns), name)

    def test_macro_edges_are_diagnostic_only(self) -> None:
        edges = pd.read_csv(TASK688_DIR / "task688_state_graph_edges.csv")
        macro = edges[edges["from_node"].eq("macro_context")]

        self.assertGreater(len(macro), 0)
        self.assertEqual(int(macro["eligible_for_slot_assignment_flag"].sum()), 0)
        self.assertTrue(macro["authority_scope"].eq("diagnostic_only").all())

    def test_contract_integrity_and_decision_status(self) -> None:
        audit = pd.read_csv(TASK688_DIR / "task688_contract_integrity_audit.csv")
        decision = pd.read_csv(TASK688_DIR / "task_688_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
