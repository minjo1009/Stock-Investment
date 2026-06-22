from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_656_macro_pragmatic_policy")


class Task656MacroPragmaticPolicyTest(unittest.TestCase):
    def test_vintage_is_deferred_not_claimed(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_656_decision.csv").iloc[0]

        self.assertEqual(int(decision["vintage_asof_required_flag"]), 0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")

    def test_task639_has_pragmatic_macro_coverage(self) -> None:
        coverage = pd.read_csv(REPORT_DIR / "task_656_pragmatic_coverage.csv")
        task639 = coverage[coverage["scope"].eq("task639_core_delay1d_existing")].iloc[0]

        self.assertGreaterEqual(float(task639["pragmatic_macro_eligible_rate"]), 0.95)
        self.assertEqual(int(task639["strict_vintage_required_flag"]), 0)
        self.assertEqual(task639["macro_usage_permission"], "soft_modifier_allowed")

    def test_macro_permission_blocks_strong_actions(self) -> None:
        permissions = pd.read_csv(REPORT_DIR / "task_656_relation_permission_matrix.csv")
        blocked = set(permissions[permissions["permission"].eq("BLOCKED")]["relation_use"])

        self.assertIn("standalone_entry", blocked)
        self.assertIn("full_entry_promotion", blocked)
        self.assertIn("hard_block", blocked)
        self.assertIn("size_boost", blocked)

    def test_pass_fail_policy_gates(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_656_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(gates["release_time_required"], 1)
        self.assertEqual(gates["vintage_requirement_deferred"], 1)
        self.assertEqual(gates["task639_pragmatic_macro_coverage"], 1)
        self.assertEqual(gates["strict_assignment_not_claimed"], 1)
        self.assertEqual(gates["trading_promotion"], 0)


if __name__ == "__main__":
    unittest.main()
