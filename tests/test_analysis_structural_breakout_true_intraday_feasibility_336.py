from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import (
    ENTRY_ONLY,
    IMMEDIATE_POST_BREAK,
    FORBIDDEN_FUTURE_COLUMNS,
    INTRADAY_D_IMMEDIATE,
    _coverage_row,
    _extract_intraday_features,
    _feature_set_features,
    _final_decision,
)


class TestAnalysisStructuralBreakoutTrueIntradayFeasibility336(unittest.TestCase):
    def _session(self) -> pd.DataFrame:
        rows = []
        base_ts = pd.Timestamp("2026-04-24T15:30:00Z")
        prices = [
            (99.0, 99.5, 98.8, 99.2, 10.0),
            (99.2, 99.7, 99.0, 99.4, 11.0),
            (99.4, 99.9, 99.1, 99.6, 12.0),
            (99.6, 100.4, 99.5, 100.2, 30.0),
            (100.2, 100.8, 100.0, 100.6, 18.0),
            (100.6, 101.0, 100.3, 100.9, 16.0),
            (100.9, 101.1, 100.5, 100.7, 14.0),
            (100.7, 100.9, 100.2, 100.3, 13.0),
            (100.3, 100.5, 99.9, 100.0, 12.0),
        ]
        for idx, (opn, high, low, close, volume) in enumerate(prices):
            start = base_ts + pd.Timedelta(minutes=5 * idx)
            end = start + pd.Timedelta(minutes=4, seconds=59)
            rows.append(
                {
                    "symbol": "AAPL",
                    "bar_start_ts": start,
                    "bar_end_ts": end,
                    "open": opn,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "bar_date": start.strftime("%Y-%m-%d"),
                }
            )
        return pd.DataFrame(rows)

    def test_breakout_timestamp_extraction_is_deterministic(self) -> None:
        intraday = self._session()
        trade = pd.Series({"symbol": "AAPL", "entry_date": "2026-04-24", "breakout_level": 100.0})
        row1 = _coverage_row(trade, intraday)
        row2 = _coverage_row(trade, intraday)
        self.assertEqual(row1["breakout_bar_index"], 3)
        self.assertEqual(row1["breakout_timestamp"], row2["breakout_timestamp"])

    def test_entry_only_feature_extraction_uses_no_post_break_values(self) -> None:
        session = self._session()
        features = _extract_intraday_features(session, 3, 100.0, ENTRY_ONLY)
        self.assertTrue(pd.isna(features["return_next_3bars"]))
        self.assertTrue(pd.isna(features["volume_persistence_3bars"]))
        self.assertTrue(pd.isna(features["breakout_hold_duration_bars"]))

    def test_immediate_post_break_respects_allowed_horizon(self) -> None:
        session = self._session()
        features = _extract_intraday_features(session, 3, 100.0, IMMEDIATE_POST_BREAK)
        self.assertFalse(pd.isna(features["return_next_3bars"]))
        self.assertFalse(pd.isna(features["return_next_5bars"]))
        self.assertFalse(pd.isna(features["breakout_hold_duration_bars"]))

    def test_coverage_status_handles_missing_symbol_and_missing_date(self) -> None:
        intraday = self._session()
        missing_symbol = pd.Series({"symbol": "MSFT", "entry_date": "2026-04-24", "breakout_level": 100.0})
        missing_date = pd.Series({"symbol": "AAPL", "entry_date": "2026-04-25", "breakout_level": 100.0})
        self.assertEqual(_coverage_row(missing_symbol, intraday)["coverage_status"], "missing_symbol")
        self.assertEqual(_coverage_row(missing_date, intraday)["coverage_status"], "missing_date")

    def test_feature_set_definitions_do_not_use_post_entry_targets(self) -> None:
        all_sets = {
            "entry": _feature_set_features(ENTRY_ONLY, "all_combined_entry_only"),
            "post": _feature_set_features(IMMEDIATE_POST_BREAK, "all_combined_immediate_post_break"),
        }
        for features in all_sets.values():
            self.assertTrue(set(features).isdisjoint(FORBIDDEN_FUTURE_COLUMNS))

    def test_immediate_only_family_not_available_in_entry_mode(self) -> None:
        self.assertEqual(_feature_set_features(ENTRY_ONLY, "intraday_only_immediate_post_break"), [])
        self.assertTrue(set(INTRADAY_D_IMMEDIATE).issubset(set(_feature_set_features(IMMEDIATE_POST_BREAK, "all_combined_immediate_post_break"))))

    def test_final_decision_returns_no_edge_when_coverage_zero(self) -> None:
        prediction_df = pd.DataFrame()
        holdout_df = pd.DataFrame()
        economic_df = pd.DataFrame()
        coverage_df = pd.DataFrame([{"coverage_status": "missing_date"}, {"coverage_status": "missing_symbol"}])
        decision = _final_decision(prediction_df, holdout_df, economic_df, coverage_df)
        self.assertEqual(str(decision.iloc[0]["decision"]), "NO_INTRADAY_EDGE")


if __name__ == "__main__":
    unittest.main()
