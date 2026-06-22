from __future__ import annotations

import sqlite3
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.app.task_337_historical_intraday_backfill import _build_plan
from src.data.intraday_backfill import (
    AlpacaHistoricalBarsProvider,
    ensure_market_bars_table,
    split_contiguous_date_blocks,
    upsert_market_bars,
)


class HistoricalIntradayBackfill337Tests(unittest.TestCase):
    def test_alpaca_normalization_enforces_schema_and_utc_strings(self) -> None:
        raw = [
            {"t": "2025-01-02T14:30:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 10, "n": 4},
        ]
        df = AlpacaHistoricalBarsProvider._normalize_rows("AAPL", raw)
        self.assertEqual(
            list(df.columns),
            [
                "symbol",
                "bar_start_ts",
                "bar_end_ts",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "tick_count",
                "source",
            ],
        )
        self.assertEqual(df.iloc[0]["bar_start_ts"], "2025-01-02T14:30:00Z")
        self.assertEqual(df.iloc[0]["bar_end_ts"], "2025-01-02T14:34:59Z")
        self.assertEqual(df.iloc[0]["source"], "ALPACA_HISTORICAL_5M")

    def test_upsert_replaces_existing_bar_without_duplication(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            ensure_market_bars_table(db_path)
            frame1 = pd.DataFrame(
                [
                    {
                        "symbol": "AAPL",
                        "bar_start_ts": "2025-01-02T14:30:00Z",
                        "bar_end_ts": "2025-01-02T14:34:59Z",
                        "open": 1.0,
                        "high": 2.0,
                        "low": 0.5,
                        "close": 1.5,
                        "volume": 10.0,
                        "tick_count": 1,
                        "source": "ALPACA_HISTORICAL_5M",
                    }
                ]
            )
            frame2 = frame1.copy()
            frame2.loc[0, "close"] = 9.0
            upsert_market_bars(db_path, frame1)
            upsert_market_bars(db_path, frame2)

            con = sqlite3.connect(db_path)
            try:
                count = con.execute("SELECT COUNT(*) FROM market_bars_5m").fetchone()[0]
                close = con.execute("SELECT close FROM market_bars_5m").fetchone()[0]
            finally:
                con.close()
            self.assertEqual(count, 1)
            self.assertEqual(close, 9.0)

    def test_skip_existing_plan_ignores_dates_with_full_session_coverage(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            ensure_market_bars_table(db_path)
            bars = []
            for idx in range(60):
                hh = 14 + ((30 + idx * 5) // 60)
                mm = (30 + idx * 5) % 60
                start = f"2025-01-02T{hh:02d}:{mm:02d}:00Z"
                end = f"2025-01-02T{hh:02d}:{mm:02d}:59Z"
                bars.append(
                    {
                        "symbol": "AAPL",
                        "bar_start_ts": start,
                        "bar_end_ts": end,
                        "open": 1.0,
                        "high": 1.0,
                        "low": 1.0,
                        "close": 1.0,
                        "volume": 1.0,
                        "tick_count": 0,
                        "source": "ALPACA_HISTORICAL_5M",
                    }
                )
            upsert_market_bars(db_path, pd.DataFrame(bars))
            scope_df = pd.DataFrame(
                [
                    {"symbol": "AAPL", "trade_date": "2025-01-02"},
                    {"symbol": "AAPL", "trade_date": "2025-01-03"},
                ]
            )
            planned, summary = _build_plan(scope_df, db_path=db_path, chunk_days=20, skip_existing=True)
            self.assertEqual(summary["already_covered_dates"], 1)
            self.assertEqual(summary["missing_coverage_dates"], 1)
            self.assertEqual(
                planned,
                [{"symbol": "AAPL", "start_date": "2025-01-03", "end_date": "2025-01-03", "requested_trade_dates": 1}],
            )

    def test_split_contiguous_date_blocks_respects_max_span(self) -> None:
        blocks = split_contiguous_date_blocks(
            [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 10), date(2025, 1, 11), date(2025, 2, 1)],
            max_span_days=5,
        )
        self.assertEqual(
            blocks,
            [
                (date(2025, 1, 1), date(2025, 1, 2)),
                (date(2025, 1, 10), date(2025, 1, 11)),
                (date(2025, 2, 1), date(2025, 2, 1)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
