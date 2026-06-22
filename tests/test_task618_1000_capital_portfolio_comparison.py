from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task618_1000_capital_portfolio_comparison import (
    build_task618_1000_capital_portfolio_comparison,
)


class Task618CapitalPortfolioComparisonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task618_1000_capital_portfolio_comparison()

    def test_compares_same_1000_starting_capital(self) -> None:
        summary = self.artifacts["task_618_1000_capital_portfolio_summary"]

        self.assertEqual(set(summary["initial_capital_usd"].round(2).unique()), {1000.0})
        self.assertEqual(set(summary["max_positions"].astype(int).unique()), {5, 10, 20, 50})
        self.assertEqual(set(summary["universe"].astype(str).unique()), {"all_candidates", "turboquant"})
        self.assertTrue((summary["final_capital_usd"] > 0).all())

    def test_turboquant_wins_same_capital_capacity_grid(self) -> None:
        winner = self.artifacts["task_618_capacity_winner_summary"]
        winners = {int(row.max_positions): str(row.winner_universe) for row in winner.itertuples()}

        self.assertEqual(winners[5], "turboquant")
        self.assertEqual(winners[10], "turboquant")
        self.assertEqual(winners[20], "turboquant")
        self.assertEqual(winners[50], "turboquant")

    def test_decision_blocks_trading_promotion(self) -> None:
        decision = self.artifacts["task_618_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_TURBOQUANT_1000_CAPITAL_ALL_CAPACITY_DIAGNOSTIC")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["raw_unlimited_total_return_is_not_account_return_flag"]), 1)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task618_1000_capital_portfolio_comparison(out_dir=out_dir)

            self.assertTrue((out_dir / "task_618_1000_capital_portfolio_comparison.md").exists())
            self.assertTrue((out_dir / "task_618_1000_capital_portfolio_summary.csv").exists())
            self.assertTrue((out_dir / "task_618_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertEqual(len(artifacts["task_618_1000_capital_portfolio_summary"]), 8)


if __name__ == "__main__":
    unittest.main()
