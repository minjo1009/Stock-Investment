from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK706_DIR = Path("docs/reports/task_706_candidate_context_bundle_v2")


class Task706CandidateContextBundleV2Test(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task706_candidate_context_bundle_v2.csv",
            "task706_context_coverage_audit.csv",
            "task_706_decision.csv",
            "task_706_pass_fail_matrix.csv",
            "task_706_candidate_context_bundle_v2.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK706_DIR / name).exists(), name)

    def test_bundle_scope_and_context(self) -> None:
        bundle = pd.read_csv(TASK706_DIR / "task706_candidate_context_bundle_v2.csv")

        self.assertEqual(len(bundle), 5265)
        self.assertEqual(int(bundle["source_event_available_flag"].sum()), 2445)
        self.assertEqual(int(bundle["price_context_available_flag"].sum()), 5265)
        self.assertEqual(int(bundle["context_bundle_available_flag"].sum()), 5265)
        self.assertEqual(int(bundle["macro_assignment_authority"].sum()), 0)
        for col in [
            "candidate_context_bundle_id",
            "context_reason_codes",
            "relation_transmission_state",
            "weakest_layer",
            "price_chart_acceptance_state",
        ]:
            self.assertIn(col, bundle.columns)

    def test_decision_and_pass_fail(self) -> None:
        decision = pd.read_csv(TASK706_DIR / "task_706_decision.csv").iloc[0]
        pass_fail = pd.read_csv(TASK706_DIR / "task_706_pass_fail_matrix.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
