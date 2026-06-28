from __future__ import annotations

import json
import sqlite3
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from tools.db.source_acquisition.bar_full_backfill import (
    BarFullBackfillConfig,
    calendar_date_blocks,
    daily_loader_frame,
    load_universe,
    run_bar_full_backfill,
)


class FakeBarsProvider:
    def fetch_bars(self, symbol: str, start_date: date, end_date: date, interval: str = "5m") -> pd.DataFrame:
        if interval == "1d":
            return pd.DataFrame(
                [
                    {
                        "symbol": symbol,
                        "bar_start_ts": f"{start_date.isoformat()}T00:00:00Z",
                        "bar_end_ts": f"{start_date.isoformat()}T23:59:59Z",
                        "open": 1.0,
                        "high": 2.0,
                        "low": 0.5,
                        "close": 1.5,
                        "volume": 10.0,
                        "tick_count": 1,
                        "source": "FAKE_1D",
                    }
                ]
            )
        return pd.DataFrame(
            [
                {
                    "symbol": symbol,
                    "bar_start_ts": f"{start_date.isoformat()}T14:30:00Z",
                    "bar_end_ts": f"{start_date.isoformat()}T14:34:59Z",
                    "open": 1.0,
                    "high": 2.0,
                    "low": 0.5,
                    "close": 1.5,
                    "volume": 10.0,
                    "tick_count": 1,
                    "source": "FAKE_5M",
                }
            ]
        )


class L0BarFullBackfillTests(unittest.TestCase):
    def test_calendar_blocks_use_large_windows(self) -> None:
        blocks = calendar_date_blocks("2025-01-01", "2025-04-30", max_span_days=120)
        self.assertEqual(blocks, [(date(2025, 1, 1), date(2025, 4, 30))])

    def test_daily_loader_frame_matches_l1_schema(self) -> None:
        bars = pd.DataFrame(
            [
                {
                    "symbol": "aapl",
                    "bar_start_ts": "2025-01-02T00:00:00Z",
                    "bar_end_ts": "2025-01-02T23:59:59Z",
                    "open": 1,
                    "high": 2,
                    "low": 0.5,
                    "close": 1.5,
                    "volume": 10,
                    "tick_count": 1,
                    "source": "FAKE",
                }
            ]
        )
        out = daily_loader_frame(bars, symbol="AAPL")
        self.assertEqual(list(out.columns), ["timestamp", "open", "high", "low", "close", "volume", "symbol"])
        self.assertEqual(out.iloc[0]["symbol"], "AAPL")

    def test_load_universe_supports_offset_stride_shards(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "universe.csv"
            path.write_text(
                "symbol,status,tradable\nA,active,True\nB,active,True\nC,active,True\nD,active,True\n",
                encoding="utf-8",
            )
            self.assertEqual(load_universe(path, offset=1, stride=2), ["B", "D"])

    def test_smoke_backfill_writes_daily_csv_and_5m_db(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            universe_path = root / "universe.csv"
            universe_path.write_text("symbol,status,tradable\nAAPL,active,True\n", encoding="utf-8")
            config = BarFullBackfillConfig(
                universe_path=universe_path,
                daily_raw_dir=root / "daily",
                db_path=root / "trading.db",
                state_path=root / "artifacts" / "state.json",
                event_path=root / "artifacts" / "events.jsonl",
                progress_path=root / "artifacts" / "progress.json",
                stop_path=root / "artifacts" / "STOP",
                plan_path=root / "artifacts" / "plan.json",
                contract_path=root / "artifacts" / "contract.json",
                log_path=root / "logs" / "collector.log",
                start_date="2025-01-02",
                end_date="2025-01-02",
                lanes=("daily", "5m"),
                max_requests=2,
            )
            result = run_bar_full_backfill(config, provider=FakeBarsProvider(), smoke=False)
            self.assertEqual(result["status"], "MAX_REQUESTS_REACHED")
            self.assertTrue((root / "daily" / "AAPL.csv").exists())
            con = sqlite3.connect(root / "trading.db")
            try:
                count = con.execute("SELECT COUNT(*) FROM market_bars_5m").fetchone()[0]
            finally:
                con.close()
            self.assertEqual(count, 1)
            progress = json.loads((root / "artifacts" / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(progress["trade_authority_flag"], 0)
            self.assertEqual(progress["broker_mutation_permitted_flag"], 0)


if __name__ == "__main__":
    unittest.main()
