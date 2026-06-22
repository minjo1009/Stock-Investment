from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK707_DIR = Path("docs/reports/task_707_tiered_action_logic")


class Task707TieredActionLogicTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task707_tiered_action_panel.csv",
            "task707_action_transition_matrix.csv",
            "task707_block_reason_audit.csv",
            "task_707_decision.csv",
            "task_707_pass_fail_matrix.csv",
            "task_707_tiered_action_logic.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK707_DIR / name).exists(), name)

    def test_action_tiers_and_no_hard_block_only(self) -> None:
        panel = pd.read_csv(TASK707_DIR / "task707_tiered_action_panel.csv")

        self.assertEqual(len(panel), 5265)
        self.assertEqual(int(panel["source_event_available_flag"].sum()), 2445)
        self.assertEqual(set(panel["task707_action_tier"]), {
            "PRIORITY_ELIGIBLE",
            "NORMAL_ELIGIBLE",
            "LOW_PRIORITY_ALIVE",
            "CONFIRMATION_REQUIRED",
            "RESEARCH_ONLY",
            "TRUE_REJECT",
        })
        self.assertGreater(int(panel["task707_trade_candidate_flag"].sum()), int(panel["full_event_axis_eligible_flag"].sum()))
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)

    def test_transition_and_decision(self) -> None:
        transition = pd.read_csv(TASK707_DIR / "task707_action_transition_matrix.csv")
        decision = pd.read_csv(TASK707_DIR / "task_707_decision.csv").iloc[0]
        pass_fail = pd.read_csv(TASK707_DIR / "task_707_pass_fail_matrix.csv")

        self.assertGreater(len(transition), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
