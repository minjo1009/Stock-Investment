from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task484_continuation_payoff_regime_engine import (
    build_task484_continuation_payoff_regime_engine,
)


class TestTask484ContinuationPayoffRegimeEngine(unittest.TestCase):
    def test_payoff_regime_audits_missing_benchmarks_and_avoids_outcome_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            symbols = ["AAA", "BBB", "CCC", "DDD"]
            for idx, symbol in enumerate(symbols):
                rows = []
                price = 100 + idx * 5
                for day in range(1, 80):
                    price *= 1.002 if idx < 2 else 0.999
                    for bar in range(26):
                        hour = 13 + ((bar + 2) // 4)
                        minute = ((bar + 2) % 4) * 15
                        close = price + bar * 0.02
                        rows.append(
                            {
                                "timestamp": f"2026-01-{day:02d}T{hour:02d}:{minute:02d}:00Z",
                                "open": close - 0.02,
                                "high": close + 0.04,
                                "low": close - 0.04,
                                "close": close,
                                "volume": 1000 + day * 20 + idx,
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

            artifacts = build_task484_continuation_payoff_regime_engine(
                intraday_dir=raw,
                theme_universe_path=theme,
                task480_snapshot_path=snapshot,
                out_dir=root / "out",
                symbols=symbols,
            )

            self.assertTrue((artifacts.benchmark_source_audit["status"] == "collectable_but_missing").any())
            decision = artifacts.task_484_decision.iloc[0]
            self.assertEqual(int(decision["benchmark_data_gap_blocks_deployment_flag"]), 1)
            self.assertEqual(int(decision["d_minus_1_daily_only_flag"]), 1)
            self.assertEqual(int(decision["intraday_confirmation_used_for_regime_flag"]), 0)
            self.assertEqual(int(decision["symbol_continuation_used_for_regime_flag"]), 0)
            self.assertEqual(int(decision["lifecycle_outcome_used_for_state_flag"]), 0)
            self.assertTrue((root / "out" / "task_484_continuation_payoff_regime_engine.md").exists())
            self.assertIn("payoff_market_regime_state", artifacts.payoff_market_regime_state_panel.columns)
            self.assertIn("payoff_theme_regime_state", artifacts.payoff_theme_regime_state_panel.columns)
            self.assertIn("benchmark_trend_score", artifacts.payoff_market_regime_state_panel.columns)
            self.assertIn("risk_appetite_confirmation_score", artifacts.payoff_market_regime_state_panel.columns)


if __name__ == "__main__":
    unittest.main()
