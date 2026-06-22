from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK705_DIR = Path("docs/reports/task_705_source_risk_subtaxonomy")


class Task705SourceRiskSubtaxonomyTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task705_source_risk_taxonomy_panel.csv",
            "task705_subtype_summary.csv",
            "task_705_decision.csv",
            "task_705_pass_fail_matrix.csv",
            "task_705_source_risk_subtaxonomy.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK705_DIR / name).exists(), name)

    def test_scope_axes_and_no_leakage(self) -> None:
        panel = pd.read_csv(TASK705_DIR / "task705_source_risk_taxonomy_panel.csv")

        self.assertEqual(len(panel), 5265)
        self.assertEqual(int(panel["source_event_available_flag"].sum()), 2445)
        for col in [
            "high_noise_subtype",
            "low_novelty_subtype",
            "financing_subtype",
            "source_risk_reason_codes",
            "source_risk_assignment_ready_flag",
        ]:
            self.assertIn(col, panel.columns)
        self.assertGreater(panel[["high_noise_subtype", "low_novelty_subtype", "financing_subtype"]].nunique().sum(), 5)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["missing_source_used_as_negative_flag"].sum()), 0)

    def test_decision_and_pass_fail(self) -> None:
        decision = pd.read_csv(TASK705_DIR / "task_705_decision.csv").iloc[0]
        pass_fail = pd.read_csv(TASK705_DIR / "task_705_pass_fail_matrix.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
