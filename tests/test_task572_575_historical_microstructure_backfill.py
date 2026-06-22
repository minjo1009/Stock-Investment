from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task572_575_historical_microstructure_backfill import (
    build_task572,
    build_task573,
    build_task574,
    build_task575,
)


class Task572575HistoricalMicrostructureBackfillTest(unittest.TestCase):
    def _write_candidate(self, root: Path) -> Path:
        path = root / "candidate.csv"
        pd.DataFrame(
            [
                {
                    "symbol": "AAPL",
                    "entry_ts": "2026-05-15T14:35:00Z",
                    "lifecycle_id": "L1",
                    "range_pos": 0.8,
                    "vwap_acceptance_state_v3": "below_vwap_controlled_pullback",
                    "net_return_from_entry": 0.03,
                    "win_flag": 1,
                    "entry_reduce_failure_flag": 0,
                    "add_scale_success_flag": 1,
                },
                {
                    "symbol": "AAPL",
                    "entry_ts": "2026-05-15T14:45:00Z",
                    "lifecycle_id": "L2",
                    "range_pos": 0.3,
                    "vwap_acceptance_state_v3": "late_chase_above_vwap",
                    "net_return_from_entry": -0.02,
                    "win_flag": 0,
                    "entry_reduce_failure_flag": 1,
                    "add_scale_success_flag": 0,
                },
            ]
        ).to_csv(path, index=False)
        return path

    def _write_quotes(self, root: Path) -> None:
        out = root / "feed=sip" / "quotes"
        out.mkdir(parents=True)
        pd.DataFrame(
            [
                {
                    "symbol": "AAPL",
                    "quote_ts": "2026-05-15T14:34:58Z",
                    "bid": 100.0,
                    "ask": 100.04,
                    "bid_size": 20,
                    "ask_size": 18,
                    "mid": 100.02,
                    "spread_bps": 3.9992,
                    "nbbo_size_dollar": 380076.0,
                    "nbbo_imbalance": 0.0526,
                    "source": "ALPACA_HISTORICAL_QUOTES",
                    "recv_ts_utc": "",
                    "receive_ts_available_flag": 0,
                },
                {
                    "symbol": "AAPL",
                    "quote_ts": "2026-05-15T14:44:58Z",
                    "bid": 101.0,
                    "ask": 101.7,
                    "bid_size": 3,
                    "ask_size": 30,
                    "mid": 101.35,
                    "spread_bps": 69.0686,
                    "nbbo_size_dollar": 334455.0,
                    "nbbo_imbalance": -0.8181,
                    "source": "ALPACA_HISTORICAL_QUOTES",
                    "recv_ts_utc": "",
                    "receive_ts_available_flag": 0,
                },
            ]
        ).to_csv(out / "AAPL.csv", index=False)

    def test_missing_quotes_are_reported_as_blocker_not_approximated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self._write_candidate(root)
            task572 = build_task572(raw_dir=root / "missing", candidate_path=candidate)
            decision = task572["task_572_decision.csv"].iloc[0]
            self.assertEqual(decision["strategy_acceptance_status"], "DATA_BLOCKED_HISTORICAL_QUOTES_MISSING")
            self.assertEqual(int(decision["missing_source_approximated_flag"]), 0)
            commands = task572["historical_microstructure_download_command_contract.csv"]
            self.assertTrue(commands["command"].str.contains("--entry-panel", regex=False).all())
            self.assertTrue(commands["download_scope"].eq("entry_window_targeted_not_full_range").all())

    def test_historical_quote_features_are_entry_safe_and_not_live_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self._write_candidate(root)
            raw_dir = root / "raw"
            self._write_quotes(raw_dir)
            task573 = build_task573(raw_dir=raw_dir, candidate_path=candidate)
            features = task573["historical_nbbo_feature_panel.csv"]
            self.assertEqual(int(features["quote_match_available_flag"].sum()), 2)
            self.assertEqual(int(features["historical_quote_used_as_live_ready_flag"].max()), 0)
            self.assertEqual(int(features["inferred_lifecycle_matching_used_flag_micro"].max()), 0)
            self.assertEqual(int(features["symbol_date_price_time_fallback_used_flag"].max()), 0)
            self.assertIn("spread_bps", features.columns)

    def test_failure_separation_and_gate_are_generated_when_quotes_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self._write_candidate(root)
            raw_dir = root / "raw"
            self._write_quotes(raw_dir)
            task572 = build_task572(raw_dir=raw_dir, candidate_path=candidate)
            task573 = build_task573(raw_dir=raw_dir, candidate_path=candidate)
            task574 = build_task574(feature_panel=task573["historical_nbbo_feature_panel.csv"])
            task575 = build_task575(task572, task573, task574)
            self.assertGreater(len(task574["historical_microstructure_bucket_quality.csv"]), 0)
            self.assertEqual(task574["task_574_decision.csv"].iloc[0]["strategy_acceptance_status"], "DIAGNOSTIC_PASS_HISTORICAL_MICROSTRUCTURE_TESTED")
            self.assertEqual(task575["task_575_decision.csv"].iloc[0]["strategy_acceptance_status"], "HISTORICAL_MICROSTRUCTURE_DIAGNOSTIC_READY_NOT_LIVE_READY")


if __name__ == "__main__":
    unittest.main()
