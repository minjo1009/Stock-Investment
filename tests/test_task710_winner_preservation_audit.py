from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK710_DIR = Path("docs/reports/task_710_winner_preservation_audit")


class Task710WinnerPreservationAuditTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task710_winner_preservation_audit.csv",
            "task710_symbol_theme_concentration_audit.csv",
            "task710_overfit_risk_matrix.csv",
            "task_710_decision.csv",
            "task_710_pass_fail_matrix.csv",
            "task_710_winner_preservation_audit.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK710_DIR / name).exists(), name)

    def test_winner_preservation_and_overfit_outputs(self) -> None:
        preservation = pd.read_csv(TASK710_DIR / "task710_winner_preservation_audit.csv")
        concentration = pd.read_csv(TASK710_DIR / "task710_symbol_theme_concentration_audit.csv")
        overfit = pd.read_csv(TASK710_DIR / "task710_overfit_risk_matrix.csv")

        self.assertEqual(set(preservation["sample"]), {"top_50_winners", "bottom_50_losers"})
        self.assertTrue(preservation["preservation_rate"].between(0, 1).all())
        self.assertGreater(len(concentration), 0)
        self.assertGreater(len(overfit), 0)
        self.assertIn("winner_preservation_low", set(overfit["risk_name"]))

    def test_decision_and_pass_fail(self) -> None:
        decision = pd.read_csv(TASK710_DIR / "task_710_decision.csv").iloc[0]
        pass_fail = pd.read_csv(TASK710_DIR / "task_710_pass_fail_matrix.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
