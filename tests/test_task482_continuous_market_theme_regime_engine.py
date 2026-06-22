from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task482_continuous_market_theme_regime_engine import (
    build_task482_continuous_market_theme_regime_engine,
)


class TestTask482ContinuousMarketThemeRegimeEngine(unittest.TestCase):
    def test_daily_only_continuous_weighted_regime_scores(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            symbols = ["AAA", "BBB", "CCC", "DDD"]
            for idx, symbol in enumerate(symbols):
                rows = []
                price = 100 + idx * 10
                for day in range(1, 46):
                    price *= 1.002 + idx * 0.0002
                    for bar in range(26):
                        ts_hour = 13 + ((bar + 2) // 4)
                        ts_min = ((bar + 2) % 4) * 15
                        close = price + bar * 0.01
                        rows.append(
                            {
                                "timestamp": f"2026-01-{day:02d}T{ts_hour:02d}:{ts_min:02d}:00Z",
                                "open": close - 0.02,
                                "high": close + 0.04,
                                "low": close - 0.05,
                                "close": close,
                                "volume": 1000 + day * 10 + idx,
                            }
                        )
                pd.DataFrame(rows).to_csv(raw / f"{symbol}.csv", index=False)
            theme = root / "theme.csv"
            pd.DataFrame(
                [
                    {"symbol": "AAA", "theme": "theme_one", "role": "leader"},
                    {"symbol": "BBB", "theme": "theme_one", "role": "member"},
                    {"symbol": "CCC", "theme": "theme_two", "role": "leader"},
                    {"symbol": "DDD", "theme": "theme_two", "role": "member"},
                ]
            ).to_csv(theme, index=False)
            snapshot = root / "snapshot.csv"
            pd.DataFrame(
                [
                    {
                        "lifecycle_id": "L1",
                        "entry_ts": "2026-01-20T15:00:00Z",
                        "theme_id": "theme_one",
                        "net_return_from_entry": 0.02,
                        "lifecycle_outcome_class": "add_scale_success",
                    }
                ]
            ).to_csv(snapshot, index=False)

            artifacts = build_task482_continuous_market_theme_regime_engine(
                intraday_dir=raw,
                theme_universe_path=theme,
                task480_snapshot_path=snapshot,
                out_dir=root / "out",
                symbols=symbols,
            )

            self.assertGreater(len(artifacts.daily_market_regime_component_scores), 0)
            self.assertGreater(len(artifacts.daily_theme_regime_component_scores), 0)
            decision = artifacts.task_482_decision.iloc[0]
            self.assertEqual(int(decision["d_minus_1_daily_only_flag"]), 1)
            self.assertEqual(int(decision["continuous_weighted_score_flag"]), 1)
            self.assertEqual(int(decision["intraday_confirmation_used_for_regime_flag"]), 0)
            self.assertEqual(int(decision["symbol_continuation_used_for_regime_flag"]), 0)
            market = artifacts.daily_market_regime_state_panel
            self.assertTrue((pd.to_datetime(market["score_date"]) > pd.to_datetime(market["asof_date"])).all())
            self.assertIn("market_regime_score", market.columns)
            self.assertTrue((root / "out" / "task_482_continuous_market_theme_regime_engine.md").exists())


if __name__ == "__main__":
    unittest.main()
