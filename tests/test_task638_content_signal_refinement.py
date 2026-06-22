from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_638_content_signal_refinement")


class Task638ContentSignalRefinementTest(unittest.TestCase):
    def test_all_requested_refinement_axes_are_tested(self) -> None:
        source = pd.read_csv(REPORT_DIR / "task_638_source_audit.csv").iloc[0]
        account = pd.read_csv(REPORT_DIR / "task_638_refinement_account_grid.csv")

        self.assertGreaterEqual(int(source["timing_mode_count"]), 6)
        self.assertGreaterEqual(int(source["exit_mode_count"]), 6)
        self.assertEqual(set(account["sizing_mode"].unique()), {"equal_max5", "dynamic_10_20_30", "dynamic_10_20_40"})
        self.assertEqual(int(source["presence_field_used_for_assignment_flag"]), 0)
        self.assertEqual(int(source["label_used_in_assignment_flag"]), 0)

    def test_refinement_improves_return_but_is_not_accepted(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_638_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "PASS_RETURN_IMPROVEMENT_FAILS_SAME_RULE_VALIDATION_NOT_ACCEPTED")
        self.assertGreater(float(decision["best_50bp_final_capital_usd"]), float(decision["task637_best_50bp_final_capital_usd"]))
        self.assertGreater(float(decision["risk_controlled_50bp_final_capital_usd"]), float(decision["task637_best_50bp_final_capital_usd"]))
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_same_rule_validation_failure_is_explicit(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_638_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(gates["risk_controlled_50bp_beats_task637"], 1)
        self.assertEqual(gates["same_rule_validation_oos_beats_qqq"], 0)
        self.assertEqual(gates["same_rule_recent_oos_beats_qqq"], 1)
        self.assertEqual(gates["trading_promotion"], 0)


if __name__ == "__main__":
    unittest.main()
