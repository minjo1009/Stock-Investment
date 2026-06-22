from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK709_DIR = Path("docs/reports/task_709_subtype_attribution")


class Task709SubtypeAttributionTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task709_subtype_performance.csv",
            "task709_mdd_subtype_exposure.csv",
            "task709_winner_loser_examples.csv",
            "task_709_decision.csv",
            "task_709_pass_fail_matrix.csv",
            "task_709_subtype_attribution.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK709_DIR / name).exists(), name)

    def test_diagnostic_outputs(self) -> None:
        performance = pd.read_csv(TASK709_DIR / "task709_subtype_performance.csv")
        exposure = pd.read_csv(TASK709_DIR / "task709_mdd_subtype_exposure.csv")
        examples = pd.read_csv(TASK709_DIR / "task709_winner_loser_examples.csv")

        self.assertGreater(len(performance), 0)
        self.assertGreater(len(exposure), 0)
        self.assertGreater(len(examples), 0)
        self.assertEqual(int(performance["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(set(performance["outcome_used_for_evaluation_flag"]), {1})

    def test_decision_and_pass_fail(self) -> None:
        decision = pd.read_csv(TASK709_DIR / "task_709_decision.csv").iloc[0]
        pass_fail = pd.read_csv(TASK709_DIR / "task_709_pass_fail_matrix.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
