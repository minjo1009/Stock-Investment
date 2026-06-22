from __future__ import annotations

import unittest

from src.backtest.build_task496_500_goal_revalidation import build_goal_revalidation
from tests.task496_500_fixture import fixture_panel


class Task499RegimeIntradayContinuationGridTest(unittest.TestCase):
    def test_grid_generates_holding_and_exact_lifecycle_metrics(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "panel.csv"
            fixture_panel().to_csv(panel_path, index=False)
            artifacts = build_goal_revalidation(
                task493_panel_path=panel_path,
                task489_market_path=root / "missing.csv",
                task496_out=root / "496",
                task497_out=root / "497",
                task498_out=root / "498",
                task499_out=root / "499",
                task500_out=root / "500",
            )
            decision = artifacts["task_499_decision"].iloc[0]
            self.assertEqual(int(decision["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertIn("same_day_exit_share", artifacts["selected_goal_portfolio_quality"].columns)


if __name__ == "__main__":
    unittest.main()
