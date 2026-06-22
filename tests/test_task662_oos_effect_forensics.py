from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_662_oos_effect_forensics")


class Task662OosEffectForensicsTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_662_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_oos_action_reach_identifies_signal_but_limited_acceptance(self) -> None:
        reach = pd.read_csv(REPORT_DIR / "task662_oos_action_reach.csv")
        recent = reach[reach["split_name"].eq("recent_oos")].iloc[0]

        self.assertGreater(int(recent["strength_hold_candidate_rows"]), 0)
        self.assertGreater(int(recent["accepted_trade_ids_with_action_count"]), 0)
        self.assertEqual(int(recent["reduce_duration_accepted"]), 0)

    def test_accepted_delta_explains_no_effect_and_winner_cuts(self) -> None:
        delta = pd.read_csv(REPORT_DIR / "task662_candidate_accepted_delta.csv")

        self.assertIn("no_accepted_trade_effect", set(delta["effect_summary"].astype(str)))
        self.assertIn("accepted_winners_cut_or_returns_reduced", set(delta["effect_summary"].astype(str)))

    def test_winner_cut_audit_has_negative_deltas(self) -> None:
        winner_cut = pd.read_csv(REPORT_DIR / "task662_winner_cut_audit.csv")

        self.assertGreater(len(winner_cut), 0)
        self.assertLess(float(winner_cut["return_delta_pct_point"].min()), 0.0)


if __name__ == "__main__":
    unittest.main()
