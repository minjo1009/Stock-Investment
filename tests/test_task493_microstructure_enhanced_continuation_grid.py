from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task493_microstructure_enhanced_continuation_grid import (
    build_task493_microstructure_enhanced_continuation_grid,
)


class Task493MicrostructureEnhancedContinuationGridTest(unittest.TestCase):
    def test_microstructure_grid_uses_exact_lifecycle_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "panel.csv"
            market_path = root / "market.csv"
            cells_path = root / "cells.csv"
            micro_path = root / "micro.csv"
            out_dir = root / "out"
            dates = pd.date_range("2024-01-01", periods=80).strftime("%Y-%m-%d")
            pd.DataFrame({"score_date": dates, "broad_market_score": [40 + i % 5 for i in range(80)], "broad_market_stress": [20 + i % 5 for i in range(80)]}).to_csv(market_path, index=False)
            pd.DataFrame({"cell_dims": ["broad_market_score"] * 5, "cell_values": [str(i) for i in range(5)]}).to_csv(cells_path, index=False)
            rows = []
            micro = []
            for idx in range(120):
                good = idx % 10 != 0
                lifecycle_id = f"L{idx}"
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
                        "lifecycle_id": lifecycle_id,
                        "symbol": f"S{idx % 8}",
                        "theme_id": "theme_a",
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
                        "net_return_from_entry": 0.03 if good else -0.01,
                        "win_flag": int(good),
                        "add_scale_success_flag": int(good),
                        "entry_reduce_failure_flag": int(not good),
                        "false_positive_flag": int(not good),
                        "quarter": "2024Q1",
                    }
                )
                micro.append(
                    {
                        "lifecycle_id": lifecycle_id,
                        "spread_state": "tight_spread",
                        "quote_freshness_state": "fresh_quote",
                        "nbbo_size_state": "thick_nbbo",
                        "microstructure_tradability_state": "micro_clean",
                        "spread_bps": 2.0,
                        "quote_age_seconds": 1.0,
                        "nbbo_size_dollar": 100000,
                        "microstructure_feature_available_flag": 1,
                    }
                )
            pd.DataFrame(rows).to_csv(panel_path, index=False)
            pd.DataFrame(micro).to_csv(micro_path, index=False)
            artifacts = build_task493_microstructure_enhanced_continuation_grid(
                task487_panel_path=panel_path,
                task489_selected_cells_path=cells_path,
                micro_feature_panel_path=micro_path,
                broad_market_cache=market_path,
                broad_daily_dir=root / "missing",
                out_dir=out_dir,
            )
            self.assertTrue((out_dir / "task_493_microstructure_enhanced_continuation_grid.md").exists())
            self.assertGreater(len(artifacts.microstructure_grid_candidate_pool), 0)
            self.assertEqual(int(artifacts.microstructure_grid_leakage_audit.iloc[0]["leakage_pass_flag"]), 1)
            self.assertEqual(int(artifacts.task_493_decision.iloc[0]["raw_receive_timestamp_available_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
