from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task489_broad_regime_cell_portfolio import build_task489_broad_regime_cell_portfolio


class Task489BroadRegimeCellPortfolioTest(unittest.TestCase):
    def test_broad_regime_cell_portfolio_uses_exact_regime_fields_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "panel.csv"
            cache_path = root / "broad_market.csv"
            out_dir = root / "out"
            market = pd.DataFrame(
                {
                    "score_date": pd.date_range("2024-01-01", periods=40).strftime("%Y-%m-%d"),
                    "broad_market_score": [40 + (i % 5) for i in range(40)],
                    "broad_market_stress": [30 + (i % 5) for i in range(40)],
                }
            )
            market.to_csv(cache_path, index=False)
            rows = []
            for idx in range(900):
                score_date = market["score_date"].iloc[idx % len(market)]
                raw = {
                    "forward_live_breadth_positive_rate": 0.60 + (idx % 5) * 0.01,
                    "forward_live_avg_symbol_return": 0.01,
                    "forward_live_liquidity_ratio": 1.0,
                    "forward_live_theme_breadth_positive_rate": 0.65,
                    "forward_live_theme_return": 0.01 + (idx % 5) * 0.001,
                    "forward_live_theme_rank": 2,
                }
                rows.append(
                    {
                        "lifecycle_id": f"L{idx}",
                        "entry_ts": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx % 280),
                        "score_date": score_date,
                        "exact_regime_join_flag": 1,
                        "raw_factors_json": json.dumps(raw),
                        "payoff_theme_score": 45 + (idx % 5),
                        "payoff_theme_stress_score": 35 + (idx % 5),
                        "net_return_from_entry": 0.006,
                        "win_flag": 1,
                        "add_scale_success_flag": 1,
                        "entry_reduce_failure_flag": 0,
                        "false_positive_flag": 0,
                        "quarter": "2024Q1",
                        "theme_id": "theme_a",
                    }
                )
            pd.DataFrame(rows).to_csv(panel_path, index=False)
            artifacts = build_task489_broad_regime_cell_portfolio(
                task487_panel_path=panel_path,
                broad_market_cache=cache_path,
                broad_daily_dir=root / "missing",
                out_dir=out_dir,
            )
            decision = artifacts.task_489_decision.iloc[0]
            self.assertEqual(int(decision["leakage_pass_flag"]), 1)
            self.assertEqual(int(artifacts.regime_cell_leakage_audit.iloc[0]["label_used_in_assignment_flag"]), 0)
            self.assertEqual(int(artifacts.regime_cell_leakage_audit.iloc[0]["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertTrue((out_dir / "task_489_broad_regime_cell_portfolio.md").exists())


if __name__ == "__main__":
    unittest.main()
