from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.continuation_runtime_capture_370 import emit_continuation_capture_event
from app.paper_capture_harness_371 import run_paper_capture_harness_371
import app.run_trade_loop as run_trade_loop
from backtest.analysis_structural_breakout_source_time_capture_371 import main as report_main
from backtest.build_source_time_capture_371 import build_source_time_capture_371, write_source_time_capture_371
from state.continuation_capture import capture_probe_entry
from state.store import (
    get_active_continuation_lifecycle_for_trade_run,
    get_latest_continuation_source_event_by_fill_id,
    get_latest_continuation_source_event_by_order_id,
    initialize_store,
    list_continuation_source_events,
)


class TestSourceTimeCapture371(unittest.TestCase):
    def _db_path(self) -> tuple[tempfile.TemporaryDirectory[str], str]:
        td = tempfile.TemporaryDirectory()
        db_path = str(Path(td.name) / "state.db")
        initialize_store(db_path)
        return td, db_path

    def test_runtime_event_lineage_is_stored_top_level(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        emit_continuation_capture_event(
            db_path=db_path,
            environment="paper",
            run_id="runtime-fill-run",
            event_type="FILL_CONFIRMED",
            symbol="AAPL",
            side="BUY",
            order_id="ord-371",
            payload={
                "event_timestamp": "2026-01-10T14:30:00Z",
                "signal_event_id": "sig-371",
                "risk_decision_id": "risk-371",
                "order_intent_id": "intent-371",
                "fill_id": "fill-371",
                "reconciliation_id": "recon-371",
                "trade_run_id": "runtime-fill-run",
                "position_quantity_before": 1.0,
                "position_quantity_after": 3.0,
                "prior_size_multiplier": 1.0,
                "next_size_multiplier": 3.0,
                "size_multiplier": 3.0,
            },
        )
        order_row = get_latest_continuation_source_event_by_order_id(db_path, "ord-371")
        fill_row = get_latest_continuation_source_event_by_fill_id(db_path, "fill-371")
        self.assertIsNotNone(order_row)
        self.assertIsNotNone(fill_row)
        self.assertEqual(str(order_row["trade_run_id"]), "runtime-fill-run")
        self.assertEqual(str(order_row["order_intent_id"]), "intent-371")
        self.assertEqual(str(fill_row["reconciliation_id"]), "recon-371")

    def test_run_loop_emits_persistence_for_open_lifecycle(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)

        def _executor() -> None:
            capture_probe_entry(
                db_path,
                symbol="MSFT",
                event_timestamp="2026-01-10T14:00:00Z",
                signal_event_id="loop-sig",
                risk_decision_id="loop-risk",
                state_label="PROBE",
                participation_quality_label="HEALTHY_EXPANSION",
                expansion_score=0.7,
                fragility_score=0.1,
                continuation_risk_score=0.1,
                size_multiplier=1.0,
                trade_run_id="loop-run-371",
            )

        old_db = os.environ.get("TRADING_DB_PATH")
        try:
            os.environ["TRADING_DB_PATH"] = db_path
            with patch.object(run_trade_loop, "_now_iso", return_value="2026-01-10T14:20:00Z"):
                exit_code = run_trade_loop.run_loop(max_runs=1, run_once_fn=_executor, sleep_fn=lambda _: None)
        finally:
            if old_db is None:
                os.environ.pop("TRADING_DB_PATH", None)
            else:
                os.environ["TRADING_DB_PATH"] = old_db
        self.assertEqual(exit_code, 0)
        rows = list_continuation_source_events(db_path, symbol="MSFT", limit=100)
        self.assertIn("PERSISTENCE_CONFIRMED", [str(row["event_type"]) for row in rows])

    def test_harness_generates_full_lifecycle_and_parent_linkage(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        summary = run_paper_capture_harness_371(db_path)
        self.assertGreater(summary["source_rows_recorded"], 0.0)
        self.assertGreater(summary["full_lifecycle_sample_count"], 0.0)
        self.assertGreater(summary["terminal_sample_count"], 0.0)
        self.assertGreater(summary["filled_add_sample_count"], 0.0)
        active = get_active_continuation_lifecycle_for_trade_run(db_path, trade_run_id="harness-run-restart-b", symbol="AMD")
        self.assertIsNone(active)
        rows = list_continuation_source_events(db_path, symbol="AMD", limit=100)
        self.assertTrue(any(str(row.get("parent_lifecycle_id") or "").strip() for row in rows))

    def test_report_artifacts_are_non_empty_after_harness(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        run_paper_capture_harness_371(db_path)
        artifacts = build_source_time_capture_371(db_path)
        self.assertFalse(artifacts.source_event_dataset.empty)
        self.assertFalse(artifacts.lifecycle_completeness.empty)
        with tempfile.TemporaryDirectory() as out_td:
            out_dir = Path(out_td)
            write_source_time_capture_371(artifacts, out_dir)
            self.assertTrue((out_dir / "task_371_source_event_dataset.csv").exists())
            self.assertTrue((out_dir / "task_371_lifecycle_completeness.csv").exists())
        with tempfile.TemporaryDirectory() as out_td, patch("sys.argv", ["task371", "--db-path", db_path, "--out-dir", out_td]):
            report_main()
            report_path = Path(out_td) / "task_371_source_time_capture.md"
            self.assertTrue(report_path.exists())
            self.assertIn("full_lifecycle_sample_count", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
