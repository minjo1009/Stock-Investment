from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_665_priority_mdd_attribution")


class Task665PriorityMddAttributionTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_665_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_mdd_penalty_is_explicit(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_665_decision.csv").iloc[0]

        self.assertLess(float(decision["priority_mdd_penalty_pct_point"]), 0.0)
        self.assertGreater(float(decision["priority_final_capital_delta_usd"]), 0.0)

    def test_delta_and_displacement_artifacts_exist(self) -> None:
        delta = pd.read_csv(REPORT_DIR / "accepted_trade_delta.csv")
        displacement = pd.read_csv(REPORT_DIR / "slot_displacement_pairs.csv")

        self.assertIn("added_by_priority", set(delta["delta_class"].astype(str)))
        self.assertIn("removed_by_priority", set(delta["delta_class"].astype(str)))
        self.assertGreater(len(displacement), 0)
        self.assertIn("pair_return_delta_pct_point", set(displacement.columns))

    def test_active_inventory_exists(self) -> None:
        active = pd.read_csv(REPORT_DIR / "priority_mdd_active_trade_inventory.csv")

        self.assertGreater(len(active), 0)
        self.assertTrue(pd.to_numeric(active["active_during_priority_mdd_interval_flag"], errors="coerce").eq(1).all())

    def test_drawdown_gate_blocks_promotion(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_665_pass_fail_matrix.csv")
        drawdown_gate = pass_fail[pass_fail["gate"].eq("drawdown_not_worse")].iloc[0]

        self.assertEqual(int(drawdown_gate["pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
