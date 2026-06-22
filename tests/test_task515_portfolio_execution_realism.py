from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task512_516_firm_grade_validation import build_task515_portfolio_execution_realism
from tests.task512_516_fixture import write_firm_grade_fixture


class Task515PortfolioExecutionRealismTest(unittest.TestCase):
    def test_execution_realism_keeps_broker_truth_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_firm_grade_fixture(root, rows=40)
            artifacts = build_task515_portfolio_execution_realism(task505_panel_path=panel, out_dir=root / "out")
            quality = artifacts["execution_realism_scenario_quality"]
            self.assertIn("pos10_100bp", set(quality["execution_scenario"]))
            self.assertEqual(int(artifacts["task_515_decision"].iloc[0]["broker_truth_fill_available_flag"]), 0)
            self.assertTrue((root / "out" / "capital_path_with_execution_cost.csv").exists())


if __name__ == "__main__":
    unittest.main()
