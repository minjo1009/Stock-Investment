from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task501_multiday_continuation_policy_rebuild import build_task501_multiday_continuation_policy_rebuild
from tests.task496_500_fixture import fixture_panel


class Task501MultiDayContinuationPolicyRebuildTest(unittest.TestCase):
    def test_multiday_policy_uses_exact_entry_rows_and_daily_raw(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = fixture_panel()
            panel["multi_day_market_state_v4"] = "persistent_broad_risk_on"
            panel["theme_regime_state_v4"] = "persistent_theme_leader"
            panel["intraday_entry_state_v4"] = "upper_range_hold"
            panel["microstructure_state_v4"] = "microstructure_clean"
            panel["entry_price"] = 100.0
            panel_path = root / "state.csv"
            panel.to_csv(panel_path, index=False)
            daily_dir = root / "daily"
            daily_dir.mkdir()
            for symbol in panel["symbol"].unique():
                dates = pd.date_range("2024-12-31", periods=90, freq="D", tz="UTC")
                prices = [100 + i for i in range(len(dates))]
                pd.DataFrame(
                    {
                        "timestamp": dates,
                        "open": prices,
                        "high": [p * 1.01 for p in prices],
                        "low": [p * 0.99 for p in prices],
                        "close": prices,
                        "volume": [1000] * len(dates),
                    }
                ).to_csv(daily_dir / f"{symbol}.csv", index=False)
            artifacts = build_task501_multiday_continuation_policy_rebuild(
                intraday_state_panel_path=panel_path,
                daily_dir=daily_dir,
                out_dir=root / "out",
            )
            decision = artifacts.task_501_decision.iloc[0]
            self.assertEqual(int(decision["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertGreater(float(decision["median_holding_days"]), 3.0)
            self.assertTrue((root / "out" / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
