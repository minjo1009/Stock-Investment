from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_860_869_backtest_cycle_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data/artifacts/task_860_869_backtest_cycle"


def read_rows(name: str) -> list[dict[str, str]]:
    with (ARTIFACT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain860869BacktestCycleTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_strategy_attempts_are_not_executed(self) -> None:
        attempts = read_rows("controlled_replay_attempts.csv")
        self.assertEqual(2, len(attempts))
        self.assertTrue(all(row["strategy_replay_decision"] == "not_executed" for row in attempts))
        self.assertTrue(all(row["trade_row_count"] == "0" for row in attempts))

    def test_qqq_reference_exists(self) -> None:
        qqq = read_rows("qqq_benchmark_reference.csv")
        self.assertEqual("QQQ", qqq[0]["symbol"])
        self.assertEqual("1000.0", qqq[0]["initial_capital"])


if __name__ == "__main__":
    unittest.main()
