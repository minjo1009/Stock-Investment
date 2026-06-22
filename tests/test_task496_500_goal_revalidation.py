from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task496_500_goal_revalidation import build_goal_revalidation


def _fixture_panel() -> pd.DataFrame:
    rows = []
    for idx in range(40):
        good = idx % 4 != 0
        entry = pd.Timestamp("2025-01-01", tz="UTC") + pd.Timedelta(days=idx)
        rows.append(
            {
                "decision_id": f"D{idx}",
                "candidate_id": f"C{idx}",
                "lifecycle_id": f"L{idx}",
                "symbol": f"S{idx % 5}",
                "theme_id": "ai_semiconductors" if idx % 2 == 0 else "cloud_ai_platforms",
                "session_date_et": entry.strftime("%Y-%m-%d"),
                "entry_ts": entry,
                "exit_ts": entry + pd.Timedelta(days=5 if good else 0),
                "net_return_from_entry": 0.05 if good else -0.03,
                "win_flag": int(good),
                "add_scale_success_flag": int(good),
                "entry_reduce_failure_flag": int(not good),
                "false_positive_flag": int(not good),
                "quarter": "2025Q1",
                "split_name": "train_design" if idx < 20 else ("validation" if idx < 30 else "recent_oos"),
                "broad_market_score": 4 if good else 2,
                "broad_market_stress": 1 if good else 4,
                "payoff_theme_score": 4 if good else 2,
                "payoff_theme_stress_score": 1 if good else 4,
                "forward_live_theme_breadth_positive_rate": 0.8 if good else 0.3,
                "forward_live_theme_return": 0.02 if good else -0.01,
                "forward_live_theme_rank": 1 if good else 5,
                "vwap_acceptance_state": "above_vwap" if good else "below_vwap",
                "timing_state": "midday_continuation" if good else "late_day",
                "close_location": 0.85 if good else 0.35,
                "upper_wick_pct": 0.1 if good else 0.55,
                "range_pos": 0.8 if good else 0.95,
                "entry_extension_atr": 1.0 if good else 2.5,
                "volume_ratio_20": 2.2 if good else 0.7,
                "vwap_deviation": 0.01 if good else -0.01,
                "spread_state": "tight_spread" if good else "wide_spread",
                "quote_freshness_state": "fresh_quote" if good else "stale_quote",
                "nbbo_size_state": "thick_nbbo" if good else "thin_nbbo",
                "microstructure_feature_available_flag": 1,
            }
        )
    return pd.DataFrame(rows)


class Task496500GoalRevalidationTest(unittest.TestCase):
    def test_goal_revalidation_outputs_exact_lifecycle_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "task493.csv"
            market_path = root / "market.csv"
            _fixture_panel().to_csv(panel_path, index=False)
            pd.DataFrame({"score_date": pd.date_range("2025-01-01", periods=40).strftime("%Y-%m-%d"), "broad_market_score": [4] * 40}).to_csv(market_path, index=False)

            artifacts = build_goal_revalidation(
                task493_panel_path=panel_path,
                task489_market_path=market_path,
                task496_out=root / "task496",
                task497_out=root / "task497",
                task498_out=root / "task498",
                task499_out=root / "task499",
                task500_out=root / "task500",
            )

            regime = artifacts["multi_day_regime_v4_panel"]
            intraday = artifacts["intraday_continuation_state_panel"]
            decision = artifacts["task_499_decision"].iloc[0]

            self.assertIn("persistent_broad_risk_on", set(regime["multi_day_market_state_v4"]))
            self.assertIn("volume_climax_continuation", set(intraday["intraday_entry_state_v4"]))
            self.assertEqual(int(regime["lifecycle_outcome_used_for_regime_flag"].max()), 0)
            self.assertEqual(int(intraday["label_used_in_intraday_assignment_flag"].max()), 0)
            self.assertEqual(int(decision["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertIn("median_holding_days", artifacts["selected_goal_portfolio_quality"].columns)
            self.assertTrue((root / "task499" / "artifact_manifest.csv").exists())
            self.assertTrue((root / "task500" / "task_500_goal_loop_synthesis.md").exists())


if __name__ == "__main__":
    unittest.main()
