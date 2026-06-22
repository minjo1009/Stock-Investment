from __future__ import annotations

import unittest

from src.backtest.build_task608h_no_label_reduce_exit_walk_forward import (
    build_task608h_no_label_reduce_exit_walk_forward,
    candidate_triggered,
)


class Task608HNoLabelReduceExitWalkForwardTest(unittest.TestCase):
    def test_candidate_trigger_uses_state_and_signal_without_label(self) -> None:
        row = {
            "symbol_multiday_setup_state": "trend_persistence_near_high",
            "early_adverse_60m_flag": 1,
            "entry_reduce_failure_flag": 0,
        }

        self.assertTrue(
            candidate_triggered(
                row,
                "symbol_multiday_setup_state=trend_persistence_near_high&early_adverse_60m_flag",
            )
        )
        self.assertFalse(
            candidate_triggered(
                row,
                "symbol_multiday_setup_state=volume_confirmed_reclaim&early_adverse_60m_flag",
            )
        )

    def test_walk_forward_reduce_simulation_does_not_accept_strategy(self) -> None:
        artifacts = build_task608h_no_label_reduce_exit_walk_forward()
        quality = artifacts["walk_forward_reduce_quality"]
        decisions = artifacts["task_608h_decision"]

        self.assertGreater(len(quality), 0)
        self.assertIn("delta_avg_net_return_pct", quality.columns)
        self.assertEqual(decisions["strategy_acceptance_status"].iloc[0], "NOT_ACCEPTED")
        self.assertEqual(decisions["deployment_status"].iloc[0], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(int(decisions["pass_flag"].iloc[0]), 0)


if __name__ == "__main__":
    unittest.main()
