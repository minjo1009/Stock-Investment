from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_backfill_scope_337 import (
    build_required_symbol_dates,
    build_symbol_summary,
)


class IntradayBackfillScope337Tests(unittest.TestCase):
    def test_scope_extraction_full_period_dedupes_symbol_dates_deterministically(self) -> None:
        df = pd.DataFrame(
            [
                {"symbol": "aapl", "entry_date": "2025-01-02", "scope": "full_period", "scenario": "s2", "trade_id": "t2"},
                {"symbol": "AAPL", "entry_date": "2025-01-02", "scope": "full_period", "scenario": "s1", "trade_id": "t1"},
                {"symbol": "MSFT", "entry_date": "2025-01-03", "scope": "full_period", "scenario": "m1", "trade_id": "t3"},
            ]
        )
        required = build_required_symbol_dates(df)
        self.assertEqual(
            required.to_dict("records"),
            [
                {
                    "symbol": "AAPL",
                    "trade_date": "2025-01-02",
                    "scope": "full_period",
                    "scenario": "s1|s2",
                    "trade_count_on_date": 2,
                },
                {
                    "symbol": "MSFT",
                    "trade_date": "2025-01-03",
                    "scope": "full_period",
                    "scenario": "m1",
                    "trade_count_on_date": 1,
                },
            ],
        )

    def test_symbol_summary_has_expected_min_max_and_counts(self) -> None:
        required = pd.DataFrame(
            [
                {"symbol": "AAPL", "trade_date": "2025-01-02", "trade_count_on_date": 2},
                {"symbol": "AAPL", "trade_date": "2025-01-04", "trade_count_on_date": 1},
                {"symbol": "MSFT", "trade_date": "2025-01-03", "trade_count_on_date": 1},
            ]
        )
        summary = build_symbol_summary(required)
        self.assertEqual(
            summary.to_dict("records"),
            [
                {
                    "symbol": "AAPL",
                    "required_trade_dates": 2,
                    "earliest_trade_date": "2025-01-02",
                    "latest_trade_date": "2025-01-04",
                    "total_trade_count": 3,
                },
                {
                    "symbol": "MSFT",
                    "required_trade_dates": 1,
                    "earliest_trade_date": "2025-01-03",
                    "latest_trade_date": "2025-01-03",
                    "total_trade_count": 1,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
