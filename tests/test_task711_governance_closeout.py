from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK711_DIR = Path("docs/reports/task_711_governance_closeout")


class Task711GovernanceCloseoutTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task711_acceptance_matrix.csv",
            "task_711_decision.csv",
            "task_711_pass_fail_matrix.csv",
            "task_711_governance_closeout.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK711_DIR / name).exists(), name)

    def test_acceptance_matrix_and_decision(self) -> None:
        acceptance = pd.read_csv(TASK711_DIR / "task711_acceptance_matrix.csv")
        decision = pd.read_csv(TASK711_DIR / "task_711_decision.csv").iloc[0]
        pass_fail = pd.read_csv(TASK711_DIR / "task_711_pass_fail_matrix.csv")

        self.assertEqual(int(acceptance["pass_flag"].min()), 1)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertIn("real_capital_forbidden", set(acceptance["gate_name"]))
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
