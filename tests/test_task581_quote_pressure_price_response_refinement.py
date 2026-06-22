from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task581_quote_pressure_price_response_refinement import build_task581


class Task581QuotePressurePriceResponseTest(unittest.TestCase):
    def test_price_response_uses_entry_safe_sources_and_keeps_missing_trade_unapproximated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "panel.csv"
            quote_dir = root / "quotes"
            trade_dir = root / "trades"
            quote_dir.mkdir()
            trade_dir.mkdir()

            pd.DataFrame(
                [
                    {
                        "symbol": "AAA",
                        "entry_ts": "2026-01-02T15:00:30Z",
                        "lifecycle_id": "L1",
                        "capital_flow_regime_v6": "capital_flow_expansion",
                        "pullback_sleeve_v1": "controlled_pullback_only",
                        "split_name": "validation",
                        "quarter": "2026Q1",
                        "net_return_from_entry": 0.05,
                        "win_flag": 1,
                        "entry_reduce_failure_flag": 0,
                        "add_scale_success_flag": 1,
                        "false_positive_flag": 0,
                        "holding_days": 4,
                    },
                    {
                        "symbol": "BBB",
                        "entry_ts": "2026-01-02T15:00:30Z",
                        "lifecycle_id": "L2",
                        "capital_flow_regime_v6": "capital_flow_expansion",
                        "pullback_sleeve_v1": "controlled_pullback_only",
                        "split_name": "validation",
                        "quarter": "2026Q1",
                        "net_return_from_entry": -0.02,
                        "win_flag": 0,
                        "entry_reduce_failure_flag": 1,
                        "add_scale_success_flag": 0,
                        "false_positive_flag": 1,
                        "holding_days": 1,
                    },
                ]
            ).to_csv(panel_path, index=False)

            pd.DataFrame(
                [
                    {
                        "symbol": "AAA",
                        "quote_ts": "2026-01-02T15:00:01Z",
                        "bid": 100.0,
                        "ask": 100.02,
                        "bid_size": 100,
                        "ask_size": 40,
                        "mid": 100.01,
                        "spread_bps": 2.0,
                        "nbbo_imbalance": 0.43,
                    },
                    {
                        "symbol": "AAA",
                        "quote_ts": "2026-01-02T15:00:29Z",
                        "bid": 100.2,
                        "ask": 100.22,
                        "bid_size": 120,
                        "ask_size": 40,
                        "mid": 100.21,
                        "spread_bps": 2.0,
                        "nbbo_imbalance": 0.5,
                    },
                    {
                        "symbol": "AAA",
                        "quote_ts": "2026-01-02T15:00:40Z",
                        "bid": 99.0,
                        "ask": 99.1,
                        "bid_size": 1,
                        "ask_size": 1,
                        "mid": 99.05,
                        "spread_bps": 10.0,
                        "nbbo_imbalance": 0.0,
                    },
                ]
                * 20
            ).to_csv(quote_dir / "AAA.csv", index=False)
            pd.DataFrame(
                [
                    {"symbol": "AAA", "trade_ts": "2026-01-02T15:00:01Z", "price": 100.02, "size": 10},
                    {"symbol": "AAA", "trade_ts": "2026-01-02T15:00:29Z", "price": 100.25, "size": 20},
                ]
            ).to_csv(trade_dir / "AAA.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "symbol": "BBB",
                        "quote_ts": "2026-01-02T15:00:01Z",
                        "bid": 50.0,
                        "ask": 50.1,
                        "bid_size": 5,
                        "ask_size": 50,
                        "mid": 50.05,
                        "spread_bps": 20.0,
                        "nbbo_imbalance": -0.82,
                    }
                ]
            ).to_csv(quote_dir / "BBB.csv", index=False)

            artifacts = build_task581(panel_path=panel_path, quote_dir=quote_dir, trade_dir=trade_dir)
            out = artifacts["quote_pressure_price_response_panel.csv"]
            aaa = out[out["symbol"].eq("AAA")].iloc[0]
            bbb = out[out["symbol"].eq("BBB")].iloc[0]

            self.assertEqual(int(aaa["future_market_data_used_flag"]), 0)
            self.assertEqual(int(aaa["label_used_in_assignment_flag_task581"]), 0)
            self.assertEqual(int(aaa["missing_source_approximated_flag_task581"]), 0)
            self.assertEqual(aaa["quote_pressure_price_response_state_v1"], "bid_support_price_acceptance")
            self.assertEqual(int(bbb["trade_response_source_available_flag"]), 0)
            self.assertEqual(int(bbb["missing_source_approximated_flag_task581"]), 0)

            leakage = artifacts["quote_pressure_price_response_leakage_audit.csv"]
            self.assertTrue((leakage["status"] == "PASS").all())


if __name__ == "__main__":
    unittest.main()
