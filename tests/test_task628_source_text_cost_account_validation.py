from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task628_source_text_cost_account_validation import (
    build_task628_source_text_cost_account_validation,
)


class Task628SourceTextCostAccountValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task628_source_text_cost_account_validation()

    def test_cost_account_edge_fails(self) -> None:
        decision = self.artifacts["task_628_decision"].iloc[0]

        self.assertEqual(decision["decision"], "FAIL_SOURCE_TEXT_COST_ACCOUNT_EDGE_NOT_ACCEPTED")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["recent_oos_50bp_account_edge_pass_flag"]), 0)
        self.assertEqual(int(decision["full_panel_50bp_account_edge_pass_flag"]), 0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_recent_wins_only_two_capacities_at_50bp(self) -> None:
        decision = self.artifacts["task_628_decision"].iloc[0]
        pass_fail = self.artifacts["task_628_pass_fail_matrix"]
        recent_gate = pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_edge")].iloc[0]

        self.assertEqual(int(decision["recent_oos_50bp_hold_win_capacity_count"]), 2)
        self.assertEqual(int(recent_gate["pass_flag"]), 0)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task628_source_text_cost_account_validation(out_dir=out_dir)

            self.assertTrue((out_dir / "task_628_source_text_cost_account_validation.md").exists())
            self.assertTrue((out_dir / "task_628_cost_account_matrix.csv").exists())
            self.assertTrue((out_dir / "task_628_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_628_cost_account_matrix"]), 40)


if __name__ == "__main__":
    unittest.main()
