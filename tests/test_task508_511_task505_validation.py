from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task508_511_task505_validation import (
    build_task508_cost_stress_validation,
    build_task509_walk_forward_oos_validation,
    build_task510_entry_reduce_failure_decomposition,
    build_task511_live_source_feature_revalidation,
)


def _fixture(path: Path, n: int = 140) -> Path:
    rows = []
    start = pd.Timestamp("2024-01-02", tz="UTC")
    for idx in range(n):
        entry = start + pd.Timedelta(days=idx * 5)
        good = idx % 4 != 0
        rows.append(
            {
                "lifecycle_id": f"L{idx}",
                "entry_ts": entry.isoformat(),
                "simulated_exit_ts": (entry + pd.Timedelta(days=40)).isoformat(),
                "net_return_from_entry": 0.12 if good else -0.06,
                "win_flag": int(good),
                "add_scale_success_flag": int(good),
                "entry_reduce_failure_flag": int(not good),
                "false_positive_flag": int(not good),
                "holding_days": 40.0,
                "same_day_exit_flag": 0,
                "theme_id": "theme_a" if idx % 2 else "theme_b",
                "symbol": f"S{idx % 6}",
                "multi_day_market_state_v4": "constructive_risk_on",
                "theme_regime_state_v4": "persistent_theme_leader",
                "symbol_multiday_setup_state": "trend_persistence_near_high",
                "timing_state": "opening_drive",
                "exit_reason": "time_exit" if good else "trailing_stop_exit",
                "quarter": f"{entry.year}Q{((entry.month-1)//3)+1}",
            }
        )
    panel = path / "panel.csv"
    pd.DataFrame(rows).to_csv(panel, index=False)
    return panel


class Task508511Task505ValidationTest(unittest.TestCase):
    def test_cost_walk_forward_failure_and_live_source_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = _fixture(root)
            task508 = build_task508_cost_stress_validation(task505_panel_path=panel, out_dir=root / "508")
            self.assertIn("roundtrip_100bp", set(task508.cost_stress_quality["cost_stress_name"]))
            self.assertEqual(int(task508.task_508_decision.iloc[0]["explicit_cost_model_added_flag"]), 1)

            task509 = build_task509_walk_forward_oos_validation(task503_panel_path=panel, out_dir=root / "509")
            self.assertTrue((root / "509" / "walk_forward_oos_quality.csv").exists())
            self.assertEqual(int(task509["task_509_decision"].iloc[0]["hindsight_grid_selection_removed_flag"]), 1)

            task510 = build_task510_entry_reduce_failure_decomposition(task505_panel_path=panel, out_dir=root / "510")
            self.assertGreater(int(task510["task_510_decision"].iloc[0]["entry_reduce_count"]), 0)
            self.assertEqual(int(task510["task_510_decision"].iloc[0]["label_used_for_evaluation_only_flag"]), 1)

            (root / "raw" / "us_intraday").mkdir(parents=True)
            task511 = build_task511_live_source_feature_revalidation(data_raw=root / "raw", out_dir=root / "511")
            self.assertEqual(int(task511["task_511_decision"].iloc[0]["missing_sources_approximated_flag"]), 0)
            self.assertEqual(int(task511["task_511_decision"].iloc[0]["live_source_revalidation_ready_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
