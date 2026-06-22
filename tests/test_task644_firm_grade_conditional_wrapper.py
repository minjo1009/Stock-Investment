from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_644_firm_grade_conditional_wrapper")


class Task644FirmGradeConditionalWrapperTest(unittest.TestCase):
    def test_decision_keeps_task639_as_best(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_644_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "FAIL_NO_FIRM_GRADE_CONDITIONAL_WRAPPER_OVER_TASK639")
        self.assertEqual(decision["best_entry_wrapper"], "base")
        self.assertEqual(decision["best_exit_wrapper"], "existing")
        self.assertEqual(decision["best_sizing_wrapper"], "equal")
        self.assertAlmostEqual(float(decision["best_final_capital_usd"]), float(decision["task639_final_capital_usd"]), places=2)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_conditional_wrappers_do_not_beat_return_and_drawdown_together(self) -> None:
        grid = pd.read_csv(REPORT_DIR / "task_644_account_grid.csv")
        decision = pd.read_csv(REPORT_DIR / "task_644_decision.csv").iloc[0]
        base_final = float(decision["task639_final_capital_usd"])
        base_dd = float(decision["task639_max_drawdown_pct"])

        both = grid[(grid["final_capital_usd"] > base_final + 0.01) & (grid["max_drawdown_pct"] > base_dd + 0.01)]
        self.assertTrue(both.empty)

    def test_gpt_design_and_result_reviews_were_captured(self) -> None:
        design = REPORT_DIR / "task_644_gpt_design_response.md"
        result = REPORT_DIR / "task_644_gpt_result_response.md"

        self.assertTrue(design.exists())
        self.assertTrue(result.exists())
        self.assertIn("conditional", design.read_text(encoding="utf-8").lower())
        self.assertIn("microstructure", result.read_text(encoding="utf-8").lower())

    def test_no_shortcut_gates_pass_and_promotion_stays_blocked(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_644_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(gates["gpt_design_captured"], 1)
        self.assertEqual(gates["no_shortcut_blacklist_or_label"], 1)
        self.assertEqual(gates["trading_promotion"], 0)


if __name__ == "__main__":
    unittest.main()
