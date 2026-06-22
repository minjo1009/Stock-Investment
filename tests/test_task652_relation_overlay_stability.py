from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_652_relation_overlay_stability")


class Task652RelationOverlayStabilityTest(unittest.TestCase):
    def test_no_relation_overlay_beats_task639(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_652_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "NO_RELATION_OVERLAY_BEATS_TASK639_KEEP_BASELINE_DIAGNOSTIC_ONLY")
        self.assertEqual(int(decision["relation_overlay_promotion_candidate_count"]), 0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_baseline_remains_top_candidate(self) -> None:
        grid = pd.read_csv(REPORT_DIR / "task_652_candidate_account_grid.csv")
        top = grid.sort_values("final_capital_usd", ascending=False).iloc[0]
        baseline = grid[grid["candidate_name"].eq("baseline_task639_core")].iloc[0]

        self.assertEqual(top["candidate_name"], "baseline_task639_core")
        self.assertGreater(float(baseline["final_capital_usd"]), float(baseline["qqq_final_capital_usd"]))

    def test_gpt_not_used_as_source(self) -> None:
        status = pd.read_csv(REPORT_DIR / "task_652_gpt_review_status.csv").iloc[0]

        self.assertEqual(int(status["used_as_source_flag"]), 0)
        self.assertEqual(int(status["captured_flag"]), 0)
        self.assertEqual(status["status"], "ATTEMPTED_BUT_CHROME_TIMEOUT")

    def test_pass_fail_blocks_promotion(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_652_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(gates["baseline_beats_qqq"], 1)
        self.assertEqual(gates["best_overlay_beats_task639"], 0)
        self.assertEqual(gates["overlay_promotion_candidate"], 0)
        self.assertEqual(gates["trading_promotion"], 0)


if __name__ == "__main__":
    unittest.main()
