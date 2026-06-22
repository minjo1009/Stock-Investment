from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_portfolio_path_equity_curve_simulation_398 import (
    build_portfolio_path_equity_curve_simulation_398,
)


class TestPortfolioPathEquityCurve398(unittest.TestCase):
    def test_builds_equity_curve_and_drawdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "cost_panel.csv"
            rows = []
            for idx, ret in enumerate([0.02, -0.01, 0.03]):
                rows.append(
                    {
                        "policy_name": "cost_constrained_forward_live_strict",
                        "policy_accepted_lifecycle_flag": 1,
                        "lifecycle_id": f"L{idx}",
                        "entry_ts": f"2026-01-0{idx + 1}T14:30:00Z",
                        "exit_ts": f"2026-01-0{idx + 1}T18:30:00Z",
                        "net_return_from_entry": ret,
                        "estimated_total_cost": 0.003,
                        "anchored_split": "validation",
                    }
                )
            pd.DataFrame(rows).to_csv(panel, index=False, encoding="utf-8-sig")
            artifacts = build_portfolio_path_equity_curve_simulation_398(task396_panel_path=panel, out_dir=root / "out")
            self.assertEqual(len(artifacts.portfolio_equity_curve), 3)
            self.assertTrue((root / "out" / "task_398_portfolio_path_equity_curve_simulation.md").exists())


if __name__ == "__main__":
    unittest.main()
