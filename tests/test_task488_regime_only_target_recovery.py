from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task488_regime_only_target_recovery import (
    build_task488_regime_only_target_recovery,
)


class Task488RegimeOnlyTargetRecoveryTest(unittest.TestCase):
    def test_regime_only_search_finds_target_and_keeps_assignment_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "task487_panel.csv"
            out_dir = root / "out"
            rows = []
            for idx in range(900):
                rows.append(
                    {
                        "lifecycle_id": f"L{idx}",
                        "entry_ts": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx % 300),
                        "exact_regime_join_flag": 1,
                        "payoff_market_score": 32.0 + (idx % 4),
                        "payoff_market_stress_score": 58.0 + (idx % 5),
                        "payoff_theme_score": 48.0 + (idx % 3),
                        "payoff_theme_stress_score": 61.0 + (idx % 4),
                        "net_return_from_entry": 0.006 if idx % 2 else 0.004,
                        "win_flag": 1,
                        "add_scale_success_flag": 1 if idx % 3 == 0 else 0,
                        "entry_reduce_failure_flag": 1 if idx % 5 == 0 else 0,
                        "false_positive_flag": 1 if idx % 5 == 0 else 0,
                        "quarter": "2024Q1",
                        "theme_id": "theme_a",
                    }
                )
            for idx in range(400):
                rows.append(
                    {
                        "lifecycle_id": f"B{idx}",
                        "entry_ts": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx % 300),
                        "exact_regime_join_flag": 1,
                        "payoff_market_score": 72.0 + (idx % 4),
                        "payoff_market_stress_score": 28.0 + (idx % 5),
                        "payoff_theme_score": 68.0 + (idx % 3),
                        "payoff_theme_stress_score": 33.0 + (idx % 4),
                        "net_return_from_entry": -0.004,
                        "win_flag": 0,
                        "add_scale_success_flag": 0,
                        "entry_reduce_failure_flag": 1,
                        "false_positive_flag": 1,
                        "quarter": "2024Q1",
                        "theme_id": "theme_b",
                    }
                )
            pd.DataFrame(rows).to_csv(panel_path, index=False)

            artifacts = build_task488_regime_only_target_recovery(task487_panel_path=panel_path, out_dir=out_dir)

            decision = artifacts.task_488_decision.iloc[0]
            self.assertEqual(int(decision["goal_achieved_full_sample_flag"]), 1)
            self.assertGreaterEqual(float(decision["selected_candidate_avg_net_pct"]), 0.35)
            self.assertGreaterEqual(float(decision["selected_candidate_win_rate"]), 0.50)
            self.assertLessEqual(float(decision["selected_candidate_entry_reduce_rate"]), 0.27)
            leakage = artifacts.target_recovered_leakage_audit.iloc[0]
            self.assertEqual(int(leakage["label_used_in_assignment_flag"]), 0)
            self.assertEqual(int(leakage["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertTrue((out_dir / "task_488_regime_only_target_recovery.md").exists())


if __name__ == "__main__":
    unittest.main()
