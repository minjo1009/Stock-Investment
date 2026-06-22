from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task487_regime_phase_target_validation import (
    build_task487_regime_phase_target_validation,
)


class TestTask487RegimePhaseTargetValidation(unittest.TestCase):
    def test_regime_phase_validation_uses_daily_regime_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            symbols = ["AAA", "BBB", "CCC", "DDD", "SPY", "QQQ", "IWM", "XLK", "SMH", "IGV", "HACK", "IBB", "XLI", "XLE", "XLU"]
            for idx, symbol in enumerate(symbols):
                rows = []
                price = 100 + idx
                for day in range(1, 80):
                    price *= 1.002 if idx % 2 == 0 else 0.999
                    for bar in range(26):
                        hour = 13 + ((bar + 2) // 4)
                        minute = ((bar + 2) % 4) * 15
                        close = price + bar * 0.01
                        rows.append(
                            {
                                "timestamp": f"2026-01-{day:02d}T{hour:02d}:{minute:02d}:00Z",
                                "open": close - 0.02,
                                "high": close + 0.03,
                                "low": close - 0.03,
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
                        "entry_ts": "2026-02-20T15:00:00Z",
                        "symbol": "AAA",
                        "net_return_from_entry": 0.02,
                        "lifecycle_outcome_class": "add_scale_success",
                    },
                    {
                        "lifecycle_id": "L2",
                        "entry_ts": "2026-02-21T15:00:00Z",
                        "symbol": "CCC",
                        "net_return_from_entry": -0.01,
                        "lifecycle_outcome_class": "entry_reduce_failure",
                    },
                ]
            ).to_csv(snapshot, index=False)

            artifacts = build_task487_regime_phase_target_validation(
                intraday_dir=raw,
                theme_universe_path=theme,
                task480_snapshot_path=snapshot,
                out_dir=root / "out",
                symbols=symbols,
            )

            self.assertIn("refined_market_phase", artifacts.refined_market_phase_panel.columns)
            self.assertIn("refined_theme_phase", artifacts.refined_theme_phase_panel.columns)
            leakage = artifacts.regime_phase_leakage_audit
            self.assertTrue(leakage["status"].eq("PASS").all())
            decision = artifacts.task_487_decision.iloc[0]
            self.assertEqual(int(decision["leakage_pass_flag"]), 1)
            self.assertTrue((root / "out" / "task_487_regime_only_phase_target_validation.md").exists())


if __name__ == "__main__":
    unittest.main()
