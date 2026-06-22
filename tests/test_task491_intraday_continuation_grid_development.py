from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task491_intraday_continuation_grid_development import (
    build_task491_intraday_continuation_grid_development,
)


class Task491IntradayContinuationGridDevelopmentTest(unittest.TestCase):
    def test_grid_development_generates_candidates_without_inferred_matching(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "panel.csv"
            market_path = root / "market.csv"
            selected_cells_path = root / "selected_cells.csv"
            out_dir = root / "out"
            dates = pd.date_range("2024-01-01", periods=80).strftime("%Y-%m-%d")
            pd.DataFrame(
                {
                    "score_date": dates,
                    "broad_market_score": [40 + idx % 5 for idx in range(80)],
                    "broad_market_stress": [20 + idx % 5 for idx in range(80)],
                }
            ).to_csv(market_path, index=False)
            pd.DataFrame(
                {
                    "cell_dims": ["broad_market_score"] * 5,
                    "cell_values": [str(idx) for idx in range(5)],
                }
            ).to_csv(selected_cells_path, index=False)
            rows = []
            for idx in range(180):
                good = idx % 5 != 0
                raw = {
                    "forward_live_breadth_positive_rate": 0.62,
                    "forward_live_avg_symbol_return": 0.01,
                    "forward_live_liquidity_ratio": 1.0,
                    "forward_live_theme_breadth_positive_rate": 0.70,
                    "forward_live_theme_return": 0.01,
                    "forward_live_theme_rank": 1,
                }
                rows.append(
                    {
                        "lifecycle_id": f"L{idx}",
                        "symbol": f"SYM{idx % 12}",
                        "theme_id": f"theme_{idx % 3}",
                        "entry_ts": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx),
                        "score_date": dates[idx % len(dates)],
                        "exact_regime_join_flag": 1,
                        "raw_factors_json": json.dumps(raw),
                        "payoff_theme_score": 50,
                        "payoff_theme_stress_score": 20,
                        "entry_bar_quality_state": "strong_close_acceptance",
                        "breakout_structure_state": "clean_breakout",
                        "momentum_structure_state": "steady_momentum",
                        "pullback_reclaim_state": "upper_range_hold",
                        "volatility_structure_state": "healthy_expansion",
                        "volume_confirmation_state": "confirmed_participation",
                        "vwap_acceptance_state": "above_vwap",
                        "timing_state": "midday_continuation",
                        "net_return_from_entry": 0.035 if good else -0.01,
                        "win_flag": int(good),
                        "add_scale_success_flag": int(good),
                        "entry_reduce_failure_flag": int(not good),
                        "false_positive_flag": int(not good),
                        "quarter": "2024Q1",
                    }
                )
            pd.DataFrame(rows).to_csv(panel_path, index=False)
            artifacts = build_task491_intraday_continuation_grid_development(
                task487_panel_path=panel_path,
                task489_selected_cells_path=selected_cells_path,
                broad_market_cache=market_path,
                broad_daily_dir=root / "missing",
                out_dir=out_dir,
            )
            self.assertTrue((out_dir / "task_491_intraday_continuation_grid_development.md").exists())
            self.assertGreater(len(artifacts.grid_portfolio_candidate_pool), 0)
            self.assertEqual(int(artifacts.grid_leakage_audit.iloc[0]["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertEqual(int(artifacts.grid_leakage_audit.iloc[0]["leakage_pass_flag"]), 1)
            self.assertIn("best_target_status", artifacts.grid_development_decision.columns)


if __name__ == "__main__":
    unittest.main()
