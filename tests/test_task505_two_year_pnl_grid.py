from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task505_two_year_pnl_grid import build_task505_two_year_pnl_grid


class Task505TwoYearPnlGridTest(unittest.TestCase):
    def test_two_year_pnl_grid_uses_exact_lifecycle_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = []
            for idx in range(80):
                entry_ts = pd.Timestamp("2025-01-01", tz="UTC") + pd.Timedelta(days=idx * 3)
                rows.append(
                    {
                        "lifecycle_id": f"L{idx}",
                        "entry_ts": entry_ts.isoformat(),
                        "simulated_exit_ts": (entry_ts + pd.Timedelta(days=20)).isoformat(),
                        "net_return_from_entry": 0.08 if idx % 5 else -0.02,
                        "win_flag": int(idx % 5 != 0),
                        "add_scale_success_flag": int(idx % 5 != 0),
                        "entry_reduce_failure_flag": int(idx % 5 == 0),
                        "false_positive_flag": int(idx % 5 == 0),
                        "holding_days": 20.0,
                        "same_day_exit_flag": 0,
                        "theme_id": "power_grid_electrification",
                        "symbol": f"SYM{idx % 4}",
                        "symbol_multiday_setup_state": "trend_persistence_near_high",
                        "timing_state": "midday_continuation",
                        "quarter": "2025Q1",
                    }
                )
            panel_path = root / "panel.csv"
            pd.DataFrame(rows).to_csv(panel_path, index=False)

            artifacts = build_task505_two_year_pnl_grid(task503_panel_path=panel_path, out_dir=root / "out")
            decision = artifacts.task_505_decision.iloc[0]

            self.assertEqual(int(decision["two_year_pnl_grid_complete_flag"]), 1)
            self.assertEqual(int(decision["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)
            self.assertGreater(float(decision["two_year_capital_pnl_pct"]), 0.0)
            self.assertTrue((root / "out" / "selected_two_year_pnl_equity_curve.csv").exists())
            self.assertTrue((root / "out" / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
