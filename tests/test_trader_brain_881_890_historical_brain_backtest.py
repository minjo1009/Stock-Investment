from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_881_890_historical_brain_backtest_validate import validate


ROOT = Path(__file__).resolve().parents[1]


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain881890HistoricalBrainBacktestTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_program_has_10_tasks(self) -> None:
        step_rows = rows("docs/reports/task_881_historical_trader_brain_backtest_program/task_881_890_program_steps.csv")
        self.assertEqual(10, len(step_rows))
        self.assertEqual({f"Task{task_id}" for task_id in range(881, 891)}, {row["task_id"] for row in step_rows})

    def test_period_and_universe_are_fixed(self) -> None:
        contract = rows("docs/reports/task_882_period_split_universe_contract/period_split_universe_contract.csv")
        values = {(row["field"], row["value"]) for row in contract}
        self.assertIn(("start_date", "2021-01-01"), values)
        self.assertIn(("end_date", "2026-03-31"), values)
        self.assertIn(("universe", "data/raw/theme_universe_10x7.csv"), values)
        self.assertIn(("universe_authority", "fixed_research_universe_diagnostic_only"), values)
        self.assertIn(("benchmark", "QQQ"), values)

    def test_first_real_replay_is_no_go(self) -> None:
        matrix = rows("docs/reports/task_890_leakage_oos_cost_go_no_go/go_no_go_matrix.csv")
        self.assertTrue(any(row["gate"] == "first_real_historical_brain_replay" and row["current_status"] == "no_go" for row in matrix))
        self.assertIn("negative_fixture_leakage_guard", {row["gate"] for row in matrix})

    def test_prep_validator_passes_when_artifacts_exist(self) -> None:
        from scripts.trader_brain_881_890_historical_brain_backtest_prep_validate import validate as validate_prep

        self.assertEqual([], validate_prep())


if __name__ == "__main__":
    unittest.main()
