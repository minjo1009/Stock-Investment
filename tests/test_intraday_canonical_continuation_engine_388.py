from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.intraday_canonical_continuation_engine_388 import (
    run_intraday_canonical_continuation_engine_388,
)


class TestIntradayCanonicalContinuationEngine388(unittest.TestCase):
    def test_intraday_fixture_generates_ordered_canonical_events(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intraday_dir = root / "intraday"
            intraday_dir.mkdir()
            _write_intraday_fixture(intraday_dir / "AMD.csv")
            artifacts = run_intraday_canonical_continuation_engine_388(
                symbols=["AMD"],
                intraday_dir=intraday_dir,
                db_path=root / "task388.db",
                out_dir=root / "out",
            )
            decision = artifacts.task_388_decision.iloc[0]
            ordering = artifacts.intraday_event_ordering_audit.iloc[0]

            self.assertEqual(str(decision["intraday_engine_status"]), "INTRADAY_CANONICAL_STREAM_READY")
            self.assertGreater(int(decision["canonical_event_count"]), 0)
            self.assertGreater(int(decision["add_count"]), 0)
            self.assertGreater(int(decision["scale_count"]), 0)
            self.assertGreater(int(decision["exit_count"]), 0)
            self.assertEqual(int(ordering["same_timestamp_multiple_events"]), 0)
            self.assertEqual(int(ordering["transition_after_exit"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)

    def test_missing_intraday_data_reports_data_required(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifacts = run_intraday_canonical_continuation_engine_388(
                symbols=["AMD"],
                intraday_dir=root / "missing",
                db_path=root / "task388.db",
                out_dir=root / "out",
            )
            decision = artifacts.task_388_decision.iloc[0]
            availability = artifacts.intraday_data_availability_audit.iloc[0]
            self.assertEqual(str(decision["intraday_engine_status"]), "INTRADAY_DATA_REQUIRED")
            self.assertEqual(int(availability["available_flag"]), 0)


def _write_intraday_fixture(path: Path) -> None:
    rows = []
    start = pd.Timestamp("2026-01-02T14:30:00Z")
    prices = [
        100.0,
        100.1,
        100.2,
        100.3,
        100.4,
        100.5,
        100.6,
        100.7,
        100.8,
        101.2,
        102.5,
        103.8,
        102.0,
        100.8,
    ]
    for i, close in enumerate(prices):
        ts = start + pd.Timedelta(minutes=15 * i)
        rows.append(
            {
                "timestamp": ts.isoformat().replace("+00:00", "Z"),
                "open": close - 0.1,
                "high": close + 0.2,
                "low": close - 0.2,
                "close": close,
                "volume": 100000 + i,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


if __name__ == "__main__":
    unittest.main()
