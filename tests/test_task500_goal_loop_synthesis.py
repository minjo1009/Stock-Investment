from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task496_500_goal_revalidation import build_task500


class Task500GoalLoopSynthesisTest(unittest.TestCase):
    def test_goal_failure_generates_next_iteration_actions(self) -> None:
        decision = pd.DataFrame(
            [
                {
                    "goal_achieved_flag": 0,
                    "selected_count": 327,
                    "selected_avg_net_pct": 0.9,
                    "selected_win_rate": 0.62,
                    "selected_entry_reduce_rate": 0.21,
                    "median_holding_days": 0.98,
                    "same_day_exit_share": 0.82,
                }
            ]
        )
        synthesis, task_decision = build_task500(decision, pd.DataFrame(), pd.DataFrame())
        self.assertGreater(len(synthesis), 0)
        self.assertIn("holding_shortfall_remove_scalp_like_lifecycles", set(synthesis["next_iteration_action"]))
        self.assertEqual(int(task_decision.iloc[0]["goal_achieved_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
