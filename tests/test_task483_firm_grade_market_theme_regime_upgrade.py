from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task483_firm_grade_market_theme_regime_upgrade import (
    build_task483_firm_grade_market_theme_regime_upgrade,
)


class TestTask483FirmGradeMarketThemeRegimeUpgrade(unittest.TestCase):
    def test_firm_grade_regime_is_daily_only_and_smoothed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            symbols = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
            for idx, symbol in enumerate(symbols):
                rows = []
                price = 80 + idx * 8
                for day in range(1, 80):
                    drift = 1.003 if idx < 3 else 0.999
                    price *= drift
                    for bar in range(26):
                        hour = 13 + ((bar + 2) // 4)
                        minute = ((bar + 2) % 4) * 15
                        close = price + bar * 0.02
                        rows.append(
                            {
                                "timestamp": f"2026-01-{day:02d}T{hour:02d}:{minute:02d}:00Z",
                                "open": close - 0.03,
                                "high": close + 0.05,
                                "low": close - 0.05,
                                "close": close,
                                "volume": 1000 + day * 20 + idx * 10,
                            }
                        )
                pd.DataFrame(rows).to_csv(raw / f"{symbol}.csv", index=False)
            theme = root / "theme.csv"
            pd.DataFrame(
                [
                    {"symbol": "AAA", "theme": "theme_one", "role": "leader"},
                    {"symbol": "BBB", "theme": "theme_one", "role": "member"},
                    {"symbol": "CCC", "theme": "theme_one", "role": "member"},
                    {"symbol": "DDD", "theme": "theme_two", "role": "leader"},
                    {"symbol": "EEE", "theme": "theme_two", "role": "member"},
                    {"symbol": "FFF", "theme": "theme_two", "role": "member"},
                ]
            ).to_csv(theme, index=False)
            snapshot = root / "snapshot.csv"
            pd.DataFrame(
                [
                    {
                        "lifecycle_id": "L1",
                        "entry_ts": "2026-02-20T15:00:00Z",
                        "symbol": "AAA",
                        "theme_id": "theme_one",
                        "net_return_from_entry": 0.02,
                        "lifecycle_outcome_class": "add_scale_success",
                    },
                    {
                        "lifecycle_id": "L2",
                        "entry_ts": "2026-02-21T15:00:00Z",
                        "symbol": "DDD",
                        "theme_id": "theme_two",
                        "net_return_from_entry": -0.01,
                        "lifecycle_outcome_class": "entry_reduce_failure",
                    },
                ]
            ).to_csv(snapshot, index=False)

            artifacts = build_task483_firm_grade_market_theme_regime_upgrade(
                intraday_dir=raw,
                theme_universe_path=theme,
                task480_snapshot_path=snapshot,
                out_dir=root / "out",
                symbols=symbols,
            )

            decision = artifacts.firm_regime_upgrade_decision.iloc[0]
            self.assertEqual(int(decision["d_minus_1_daily_only_flag"]), 1)
            self.assertEqual(int(decision["continuous_weighted_score_flag"]), 1)
            self.assertEqual(int(decision["smoothed_score_flag"]), 1)
            self.assertEqual(int(decision["three_day_hysteresis_flag"]), 1)
            self.assertEqual(int(decision["intraday_confirmation_used_for_regime_flag"]), 0)
            self.assertEqual(int(decision["symbol_continuation_used_for_regime_flag"]), 0)
            self.assertIn("firm_market_regime_score", artifacts.firm_market_regime_state_panel.columns)
            self.assertIn("firm_theme_regime_score", artifacts.firm_theme_regime_state_panel.columns)
            self.assertTrue((root / "out" / "task_483_firm_grade_market_theme_regime_upgrade.md").exists())
            self.assertTrue((root / "out" / "firm_regime_v1_comparison.csv").exists())


if __name__ == "__main__":
    unittest.main()
