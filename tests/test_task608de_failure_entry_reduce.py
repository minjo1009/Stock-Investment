from __future__ import annotations

import unittest

from src.backtest.build_task608de_failure_entry_reduce import (
    build_entry_reduce_attribution,
    build_quarter_failure_map,
    build_task608de_failure_entry_reduce,
    load_oos_panel,
    summarize_panel,
)


class Task608DEFailureEntryReduceTest(unittest.TestCase):
    def test_entry_reduce_failure_is_material_in_oos_panel(self) -> None:
        panel = load_oos_panel("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_assignment_panel.csv")
        baseline = summarize_panel(panel, label="baseline_oos")
        quarter_map = build_quarter_failure_map(panel, baseline)
        attribution = build_entry_reduce_attribution(panel, quarter_map)

        clean = attribution[attribution["entry_reduce_failure_flag"].eq(0)].iloc[0]
        failed = attribution[attribution["entry_reduce_failure_flag"].eq(1)].iloc[0]

        self.assertGreater(float(clean["avg_net_return_pct"]), 0.0)
        self.assertLess(float(failed["avg_net_return_pct"]), 0.0)
        self.assertEqual(float(failed["win_rate"]), 0.0)
        self.assertGreater(float(baseline["entry_reduce_failure_rate"]), 0.30)

    def test_failure_map_identifies_2025q1_and_decisions(self) -> None:
        artifacts = build_task608de_failure_entry_reduce()
        quarter_map = artifacts["quarter_failure_map"]
        decisions = artifacts["task_608de_decision"]

        q1_2025 = quarter_map[quarter_map["quarter"].eq("2025Q1")].iloc[0]

        self.assertEqual(int(q1_2025["hard_break_flag"]), 1)
        self.assertEqual(int(q1_2025["weak_quarter_flag"]), 1)
        self.assertIn("Task608D", set(decisions["task_id"]))
        self.assertIn("Task608E", set(decisions["task_id"]))
        self.assertEqual(
            decisions[decisions["task_id"].eq("Task608E")]["decision"].iloc[0],
            "FAIL_ENTRY_REDUCE_FAILURE_MATERIAL",
        )


if __name__ == "__main__":
    unittest.main()
