from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task503_multiday_entry_population_rebuild import build_task503_multiday_entry_population_rebuild


class Task503MultiDayEntryPopulationRebuildTest(unittest.TestCase):
    def test_entry_population_is_generated_from_raw_daily_and_intraday(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            theme = pd.DataFrame([{"theme": "theme_a", "symbol": "AAA", "role": "leader"}])
            theme_path = root / "theme.csv"
            theme.to_csv(theme_path, index=False)
            daily_dir = root / "daily"
            intraday_dir = root / "intra"
            daily_dir.mkdir()
            intraday_dir.mkdir()
            dates = pd.date_range("2025-01-01 05:00:00", periods=100, freq="D", tz="UTC")
            prices = [100 + i * 0.5 for i in range(100)]
            pd.DataFrame(
                {
                    "timestamp": dates,
                    "open": prices,
                    "high": [p * 1.01 for p in prices],
                    "low": [p * 0.99 for p in prices],
                    "close": prices,
                    "volume": [1000 + i * 10 for i in range(100)],
                }
            ).to_csv(daily_dir / "AAA.csv", index=False)
            bars = []
            for date in pd.date_range("2025-01-01", periods=100, freq="D", tz="UTC"):
                for hour in [14, 15, 16, 17, 18]:
                    ts = pd.Timestamp(year=date.year, month=date.month, day=date.day, hour=hour, tz="UTC")
                    bars.append({"timestamp": ts, "open": 120, "high": 125, "low": 119, "close": 124.5, "volume": 2000, "vwap": 121})
            pd.DataFrame(bars).to_csv(intraday_dir / "AAA.csv", index=False)
            market = pd.DataFrame(
                {
                    "score_date": pd.date_range("2025-01-01", periods=100, freq="D").strftime("%Y-%m-%d"),
                    "broad_market_score": [4] * 100,
                    "broad_market_stress": [1] * 100,
                    "breadth_20d": [0.7] * 100,
                    "market_ret_20d": [0.1] * 100,
                    "liquidity_ratio": [1.2] * 100,
                    "vol_ratio": [0.8] * 100,
                }
            )
            market_path = root / "market.csv"
            market.to_csv(market_path, index=False)
            artifacts = build_task503_multiday_entry_population_rebuild(
                theme_map_path=theme_path,
                daily_dir=daily_dir,
                intraday_dir=intraday_dir,
                market_panel_path=market_path,
                out_dir=root / "out",
            )
            self.assertGreater(len(artifacts.multiday_entry_candidate_panel), 0)
            self.assertEqual(int(artifacts.task_503_decision.iloc[0]["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertEqual(int(artifacts.task_503_decision.iloc[0]["label_used_in_assignment_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
