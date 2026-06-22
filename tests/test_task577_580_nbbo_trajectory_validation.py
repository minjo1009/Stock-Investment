from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task577_580_nbbo_trajectory_validation import (
    build_task577,
    build_task578,
    build_task579,
    build_task580,
)


class Task577580NbboTrajectoryValidationTest(unittest.TestCase):
    def test_trajectory_uses_only_pre_entry_quotes_and_blocks_live_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quote_dir = root / "quotes"
            quote_dir.mkdir()
            panel_path = root / "panel.csv"
            pd.DataFrame(
                [
                    {
                        "symbol": "AAPL",
                        "entry_ts": "2026-05-18T14:31:00Z",
                        "lifecycle_id": "L1",
                        "pullback_sleeve_v1": "controlled_pullback_only",
                        "capital_flow_regime_v6": "capital_flow_expansion",
                        "net_return_from_entry": 0.04,
                        "win_flag": 1,
                        "entry_reduce_failure_flag": 0,
                        "add_scale_success_flag": 1,
                        "split_name": "validation",
                        "quarter": "2026Q2",
                    }
                ]
            ).to_csv(panel_path, index=False)
            pd.DataFrame(
                [
                    {"symbol": "AAPL", "quote_ts": "2026-05-18T14:30:10Z", "bid": 100.0, "ask": 100.1, "bid_size": 10, "ask_size": 10, "mid": 100.05, "spread_bps": 10.0, "nbbo_size_dollar": 200100.0, "nbbo_imbalance": 0.0},
                    {"symbol": "AAPL", "quote_ts": "2026-05-18T14:30:50Z", "bid": 100.2, "ask": 100.25, "bid_size": 25, "ask_size": 12, "mid": 100.225, "spread_bps": 5.0, "nbbo_size_dollar": 370832.5, "nbbo_imbalance": 0.35},
                    {"symbol": "AAPL", "quote_ts": "2026-05-18T14:31:05Z", "bid": 99.0, "ask": 101.0, "bid_size": 1, "ask_size": 1, "mid": 100.0, "spread_bps": 200.0, "nbbo_size_dollar": 20000.0, "nbbo_imbalance": 0.0},
                ]
            ).to_csv(quote_dir / "AAPL.csv", index=False)
            old_panel = __import__("src.backtest.build_task577_580_nbbo_trajectory_validation", fromlist=["TASK573_PANEL"])
            old_panel.TASK573_PANEL = panel_path
            old_panel.TASK576_PANEL = Path("__missing__")
            old_panel.QUOTE_DIR = quote_dir
            artifacts = build_task577()
            panel = artifacts["nbbo_trajectory_feature_panel.csv"]
            self.assertEqual(int(panel["future_quote_used_flag"].max()), 0)
            self.assertEqual(int(panel["receive_ts_live_ready_flag"].max()), 0)
            self.assertGreater(int(panel["q60_quote_count"].iloc[0]), 0)
            self.assertLess(float(panel["q60_spread_delta"].iloc[0]), 0)

    def test_backtest_and_gate_are_generated(self) -> None:
        panel = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L1",
                    "symbol": "AAPL",
                    "entry_ts": "2026-05-18T14:31:00Z",
                    "capital_flow_regime_v6": "capital_flow_expansion",
                    "pullback_sleeve_v1": "controlled_pullback_only",
                    "spread_trajectory_state": "spread_tightening",
                    "book_pressure_state": "bid_support_persistent",
                    "quote_activity_state": "active_quote_stream",
                    "nbbo_trajectory_state_v1": "spread_tightening|bid_support_persistent|active_quote_stream",
                    "q30_quote_count": 40,
                    "net_return_from_entry": 0.04,
                    "win_flag": 1,
                    "entry_reduce_failure_flag": 0,
                    "add_scale_success_flag": 1,
                    "split_name": "validation",
                    "quarter": "2026Q2",
                }
            ]
        )
        task578 = build_task578(panel)
        task579 = build_task579()
        task577 = {
            "task_577_decision.csv": pd.DataFrame(
                [{"strategy_acceptance_status": "DIAGNOSTIC_PASS_NBBO_TRAJECTORY_BUILT"}]
            )
        }
        task580 = build_task580(task577, task578, task579)
        self.assertEqual(task578["task_578_decision.csv"].iloc[0]["strategy_acceptance_status"], "DIAGNOSTIC_PASS_TRAJECTORY_BACKTESTED")
        self.assertIn(task580["task_580_decision.csv"].iloc[0]["strategy_acceptance_status"], {"CONTINUE_WITH_NBBO_TRAJECTORY_AND_LIVE_CAPTURE", "DIAGNOSTIC_ONLY_TRAJECTORY_NOT_SUFFICIENT_YET"})


if __name__ == "__main__":
    unittest.main()
