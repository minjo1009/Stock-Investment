from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task504_multiday_entry_cell_portfolio import build_task504_multiday_entry_cell_portfolio


class Task504MultiDayEntryCellPortfolioTest(unittest.TestCase):
    def test_cell_portfolio_selects_goal_quality_cells(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = []
            for idx in range(320):
                rows.append(
                    {
                        "lifecycle_id": f"L{idx}",
                        "theme_id": "power_grid_electrification",
                        "symbol_multiday_setup_state": "trend_persistence_near_high",
                        "timing_state": "midday_continuation",
                        "net_return_from_entry": 0.08 if idx % 5 else -0.03,
                        "win_flag": int(idx % 5 != 0),
                        "add_scale_success_flag": int(idx % 5 != 0),
                        "entry_reduce_failure_flag": int(idx % 5 == 0),
                        "false_positive_flag": int(idx % 5 == 0),
                        "holding_days": 20.0,
                        "same_day_exit_flag": 0,
                        "split_name": "recent_oos" if idx > 250 else "train_design",
                        "quarter": "2026Q1",
                    }
                )
            panel_path = root / "panel.csv"
            pd.DataFrame(rows).to_csv(panel_path, index=False)
            artifacts = build_task504_multiday_entry_cell_portfolio(task503_panel_path=panel_path, out_dir=root / "out")
            decision = artifacts["task_504_decision"].iloc[0]
            self.assertEqual(int(decision["goal_achieved_flag"]), 1)
            self.assertEqual(int(decision["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertTrue((root / "out" / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
