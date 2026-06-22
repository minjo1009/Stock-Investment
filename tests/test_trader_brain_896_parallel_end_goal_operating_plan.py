from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_896_parallel_end_goal_operating_plan_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_896_parallel_end_goal_operating_plan"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain896ParallelEndGoalOperatingPlanTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_plan_has_parallel_lanes(self) -> None:
        plan = rows("parallel_execution_plan_task897_906.csv")
        lane_counts: dict[str, int] = {}
        for row in plan:
            lane_counts[row["lane"]] = lane_counts.get(row["lane"], 0) + 1
        self.assertEqual(5, lane_counts["vertical_slice"])
        self.assertEqual(4, lane_counts["data_corpus"])
        self.assertEqual(1, lane_counts["integration"])

    def test_scorecard_covers_end_goal_chain(self) -> None:
        stages = {row["stage"] for row in rows("end_goal_progress_scorecard.csv")}
        self.assertIn("1_l1_source_evidence", stages)
        self.assertIn("6_backtest_paper_live_gate", stages)

    def test_stop_rules_prevent_drift(self) -> None:
        rules = " ".join(row["rule"] for row in rows("stop_doing_rules.csv"))
        self.assertIn("Do not create another pure diagnosis task", rules)
        self.assertIn("Do not broad-download sources", rules)
        self.assertIn("80 percent", rules)
        self.assertIn("95 percent", rules)

    def test_external_gpt_review_changes_plan(self) -> None:
        review = rows("external_gpt_review_synthesis.csv")
        self.assertGreaterEqual(len(review), 8)
        plan = {row["task_id"]: row for row in rows("parallel_execution_plan_task897_906.csv")}
        self.assertEqual("Task897;Task903", plan["Task898"]["blocked_by"])
        self.assertIn("source span", plan["Task897"]["success_criteria"])


if __name__ == "__main__":
    unittest.main()
