from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from tools.db.source_acquisition.microstructure_background_collector import (
    chunk_raw_path,
    legacy_existing_source_symbols,
    session_chunks,
)
from tools.db.source_acquisition.microstructure_coverage import build_raw_catalog


class L0MicrostructureBackgroundCollectorTest(unittest.TestCase):
    def test_session_chunks_use_new_york_market_hours_with_dst(self) -> None:
        summer = session_chunks("2026-06-26", chunk_minutes=1)
        winter = session_chunks("2026-01-02", chunk_minutes=1)

        self.assertEqual(summer[0], ("2026-06-26T13:30:00Z", "2026-06-26T13:31:00Z"))
        self.assertEqual(summer[-1][1], "2026-06-26T20:00:00Z")
        self.assertEqual(winter[0], ("2026-01-02T14:30:00Z", "2026-01-02T14:31:00Z"))
        self.assertEqual(winter[-1][1], "2026-01-02T21:00:00Z")

    def test_session_chunks_support_accelerated_15_minute_windows(self) -> None:
        chunks = session_chunks("2026-06-26", chunk_minutes=15)

        self.assertEqual(len(chunks), 26)
        self.assertEqual(chunks[0], ("2026-06-26T13:30:00Z", "2026-06-26T13:45:00Z"))
        self.assertEqual(chunks[-1], ("2026-06-26T19:45:00Z", "2026-06-26T20:00:00Z"))

    def test_chunk_raw_path_does_not_overwrite_symbol_file(self) -> None:
        path = chunk_raw_path(
            Path("raw"),
            feed="iex",
            source_type="quotes",
            symbol="AAPL",
            session_date="2026-06-26",
            chunk_start_ts="2026-06-26T13:30:00Z",
            chunk_end_ts="2026-06-26T13:31:00Z",
        )

        self.assertEqual(
            path.as_posix(),
            "raw/feed=iex/source_type=quotes/symbol=AAPL/session_date=2026-06-26/chunk_start=20260626T133000Z_chunk_end=20260626T133100Z.csv",
        )

    def test_chunked_raw_catalog_uses_symbol_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = (
                root
                / "feed=iex"
                / "source_type=quotes"
                / "symbol=AAPL"
                / "session_date=2026-06-26"
                / "chunk_start=20260626T133000Z_chunk_end=20260626T133100Z.csv"
            )
            raw_path.parent.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "symbol": "AAPL",
                        "quote_ts": "2026-06-26T13:30:01Z",
                        "bid": 1.0,
                        "ask": 1.1,
                    }
                ]
            ).to_csv(raw_path, index=False)

            catalog = build_raw_catalog(root)

        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog.loc[0, "symbol"], "AAPL")
        self.assertEqual(catalog.loc[0, "source_type"], "quotes")
        self.assertEqual(catalog.loc[0, "session_date"], "2026-06-26")

    def test_legacy_existing_source_symbols_detects_held_raw(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = root / "feed=sip" / "trades" / "AAPL.csv"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_text("symbol,trade_ts\nAAPL,2026-06-26T13:30:00Z\n", encoding="utf-8")

            existing = legacy_existing_source_symbols([root])

        self.assertIn(("trades", "AAPL"), existing)

    def test_chunked_raw_does_not_mark_entire_symbol_as_held(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = (
                root
                / "feed=iex"
                / "source_type=trades"
                / "symbol=AAPL"
                / "session_date=2026-06-26"
                / "chunk_start=20260626T133000Z_chunk_end=20260626T133100Z.csv"
            )
            raw_path.parent.mkdir(parents=True)
            raw_path.write_text("symbol,trade_ts\nAAPL,2026-06-26T13:30:00Z\n", encoding="utf-8")

            existing = legacy_existing_source_symbols([root])

        self.assertNotIn(("trades", "AAPL"), existing)


if __name__ == "__main__":
    unittest.main()
