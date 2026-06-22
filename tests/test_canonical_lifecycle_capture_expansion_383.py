from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.continuation_runtime_capture_370 import emit_continuation_capture_event
from backtest.analysis_structural_breakout_canonical_lifecycle_capture_expansion_383 import _write_report
from backtest.build_canonical_lifecycle_capture_expansion_383 import (
    build_canonical_lifecycle_capture_expansion_383,
    write_canonical_lifecycle_capture_expansion_383,
)
from backtest.canonical_position_lifecycle_event_sourcing import list_canonical_position_events
from state.store import initialize_store


class TestCanonicalLifecycleCaptureExpansion383(unittest.TestCase):
    def test_runtime_probe_entry_creates_canonical_entry_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            capture_path = Path(td) / "capture.jsonl"
            initialize_store(str(db_path))

            old_capture = _set_env("TRADING_CONTINUATION_CAPTURE_PATH", str(capture_path))
            try:
                emit_continuation_capture_event(
                    db_path=str(db_path),
                    environment="paper",
                    run_id="run-1",
                    event_type="PROBE_ENTRY",
                    symbol="AMD",
                    side="BUY",
                    reason="order_submitted",
                    order_id="ORD-1",
                    payload={
                        "event_timestamp": "2026-05-08T13:31:00Z",
                        "canonical_lifecycle_id": "LIFECYCLE|AMD|2026-05-08|ORD-1",
                        "limit_price": 164.25,
                        "trade_run_id": "run-1",
                    },
                )
            finally:
                _restore_env("TRADING_CONTINUATION_CAPTURE_PATH", old_capture)

            events = list_canonical_position_events(str(db_path), lifecycle_id="LIFECYCLE|AMD|2026-05-08|ORD-1")
            self.assertEqual([event["canonical_event_type"] for event in events], ["ENTRY"])
            record = json.loads(capture_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["payload"]["canonical_capture_status"], "canonical_entry_recorded")

    def test_runtime_add_requires_explicit_lifecycle_id_for_canonical_capture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            capture_path = Path(td) / "capture.jsonl"
            initialize_store(str(db_path))
            old_capture = _set_env("TRADING_CONTINUATION_CAPTURE_PATH", str(capture_path))
            try:
                emit_continuation_capture_event(
                    db_path=str(db_path),
                    environment="paper",
                    run_id="run-1",
                    event_type="PROBE_ENTRY",
                    symbol="NVDA",
                    side="BUY",
                    order_id="ORD-1",
                    payload={
                        "event_timestamp": "2026-05-08T13:31:00Z",
                        "canonical_lifecycle_id": "LIFECYCLE|NVDA|2026-05-08|ORD-1",
                    },
                )
                emit_continuation_capture_event(
                    db_path=str(db_path),
                    environment="paper",
                    run_id="run-1",
                    event_type="ADD_CONFIRMED",
                    symbol="NVDA",
                    side="BUY",
                    order_id="ORD-2",
                    payload={"event_timestamp": "2026-05-08T13:40:00Z"},
                )
                emit_continuation_capture_event(
                    db_path=str(db_path),
                    environment="paper",
                    run_id="run-1",
                    event_type="ADD_CONFIRMED",
                    symbol="NVDA",
                    side="BUY",
                    order_id="ORD-3",
                    payload={
                        "event_timestamp": "2026-05-08T13:45:00Z",
                        "canonical_lifecycle_id": "LIFECYCLE|NVDA|2026-05-08|ORD-1",
                    },
                )
            finally:
                _restore_env("TRADING_CONTINUATION_CAPTURE_PATH", old_capture)

            events = list_canonical_position_events(str(db_path), lifecycle_id="LIFECYCLE|NVDA|2026-05-08|ORD-1")
            self.assertEqual([event["canonical_event_type"] for event in events], ["ENTRY", "ADD"])
            statuses = [
                json.loads(line)["payload"]["canonical_capture_status"]
                for line in capture_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertIn("missing_explicit_lifecycle_id", statuses)
            self.assertIn("canonical_add_recorded", statuses)

    def test_runtime_cancel_confirms_exit_for_explicit_lifecycle_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            initialize_store(str(db_path))
            emit_continuation_capture_event(
                db_path=str(db_path),
                environment="paper",
                run_id="run-1",
                event_type="PROBE_ENTRY",
                symbol="AAPL",
                side="BUY",
                order_id="ORD-1",
                payload={
                    "event_timestamp": "2026-05-08T13:31:00Z",
                    "canonical_lifecycle_id": "LIFECYCLE|AAPL|2026-05-08|ORD-1",
                },
            )
            emit_continuation_capture_event(
                db_path=str(db_path),
                environment="paper",
                run_id="run-1",
                event_type="CANCEL_CONFIRMED",
                symbol="AAPL",
                side="BUY",
                order_id="ORD-1",
                payload={
                    "event_timestamp": "2026-05-08T13:45:00Z",
                    "canonical_lifecycle_id": "LIFECYCLE|AAPL|2026-05-08|ORD-1",
                },
            )

            events = list_canonical_position_events(str(db_path), lifecycle_id="LIFECYCLE|AAPL|2026-05-08|ORD-1")
            self.assertEqual([event["canonical_event_type"] for event in events], ["ENTRY", "EXIT"])

    def test_task376_rows_without_explicit_lifecycle_id_are_not_capture_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            pd.DataFrame(
                {
                    "trade_id": ["same-looking-row"],
                    "symbol": ["AMD"],
                    "entry_ts": ["2026-05-08T13:31:00Z"],
                }
            ).to_csv(task376_path, index=False)

            artifacts = build_canonical_lifecycle_capture_expansion_383(
                db_path=db_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            audit = artifacts.task376_canonical_capture_mapping_audit.iloc[0]
            decision = artifacts.task_383_decision.iloc[0]
            self.assertEqual(str(audit["mapping_status"]), "explicit_lifecycle_id_missing")
            self.assertEqual(int(audit["capture_ready_row_count"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)

    def test_explicit_lifecycle_id_and_intraday_entry_ts_are_capture_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            pd.DataFrame(
                {
                    "trade_id": ["trade-1"],
                    "lifecycle_id": ["LIFECYCLE|MSFT|2026-05-08|ORD-1"],
                    "symbol": ["MSFT"],
                    "entry_ts": ["2026-05-08T13:31:00Z"],
                }
            ).to_csv(task376_path, index=False)

            artifacts = build_canonical_lifecycle_capture_expansion_383(
                db_path=db_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            audit = artifacts.task376_canonical_capture_mapping_audit.iloc[0]
            self.assertEqual(str(audit["mapping_status"]), "capture_ready_explicit_lifecycle_rows_available")
            self.assertEqual(int(audit["capture_ready_row_count"]), 1)

    def test_date_only_or_midnight_entry_ts_is_not_capture_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            pd.DataFrame(
                {
                    "trade_id": ["trade-1"],
                    "lifecycle_id": ["LIFECYCLE|AMZN|2026-05-08|ORD-1"],
                    "symbol": ["AMZN"],
                    "entry_ts": ["2026-05-08 00:00:00+00:00"],
                }
            ).to_csv(task376_path, index=False)

            artifacts = build_canonical_lifecycle_capture_expansion_383(
                db_path=db_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            audit = artifacts.task376_canonical_capture_mapping_audit.iloc[0]
            self.assertEqual(str(audit["mapping_status"]), "explicit_lifecycle_id_present_but_entry_ts_not_capture_ready")
            self.assertEqual(int(audit["capture_ready_row_count"]), 0)

    def test_report_and_csv_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            out_dir = Path(td) / "out"
            pd.DataFrame({"trade_id": ["t1"], "symbol": ["AAPL"], "entry_ts": ["2026-05-08"]}).to_csv(task376_path, index=False)

            artifacts = build_canonical_lifecycle_capture_expansion_383(
                db_path=db_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            write_canonical_lifecycle_capture_expansion_383(artifacts, out_dir)
            _write_report(out_dir, artifacts)
            expected = [
                "canonical_capture_event_stream.csv",
                "canonical_capture_lifecycle_panel.csv",
                "task376_canonical_capture_mapping_audit.csv",
                "canonical_capture_readiness_audit.csv",
                "task_383_decision.csv",
                "task_383_canonical_lifecycle_capture_expansion.md",
            ]
            for name in expected:
                self.assertTrue((out_dir / name).exists(), name)


def _set_env(key: str, value: str) -> str | None:
    import os

    old = os.environ.get(key)
    os.environ[key] = value
    return old


def _restore_env(key: str, old: str | None) -> None:
    import os

    if old is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = old


if __name__ == "__main__":
    unittest.main()
