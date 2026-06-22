from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.backtest.analysis_structural_breakout_source_time_capture_370 import main as report_main
from src.backtest.build_source_time_capture_370 import build_source_time_capture, write_source_time_capture
from src.app.continuation_runtime_capture_370 import emit_continuation_capture_event
from src.state.continuation_capture import (
    capture_add_confirmed_only,
    capture_persistence_if_due,
    capture_probe_entry,
    capture_setup_detected,
    capture_signal_risk_stage,
    capture_size_increase_only,
    capture_terminal_stage,
    capture_weakening_stage,
)
from src.state.store import (
    get_active_continuation_lifecycle,
    initialize_store,
    list_continuation_lifecycles,
    list_continuation_snapshots,
    list_continuation_source_events,
)


class TestSourceTimeCapture370(unittest.TestCase):
    def _db_path(self) -> tuple[tempfile.TemporaryDirectory[str], str]:
        td = tempfile.TemporaryDirectory()
        db_path = str(Path(td.name) / "state.db")
        initialize_store(db_path)
        return td, db_path

    def test_initialize_store_creates_capture_tables(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        con = sqlite3.connect(db_path)
        try:
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        finally:
            con.close()
        self.assertIn("continuation_setups", tables)
        self.assertIn("continuation_lifecycles", tables)
        self.assertIn("continuation_source_events", tables)
        self.assertIn("continuation_snapshots", tables)

    def test_signal_identity_and_prefix_stability(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        capture_setup_detected(
            db_path,
            symbol="AAPL",
            event_timestamp="2026-01-01T14:30:00Z",
            signal_event_id="sig-1",
            risk_decision_id="risk-1",
            state_label="SETUP",
            participation_quality_label="UNKNOWN",
            expansion_score=0.0,
            fragility_score=0.0,
            continuation_risk_score=0.0,
        )
        capture_probe_entry(
            db_path,
            symbol="AAPL",
            event_timestamp="2026-01-01T14:31:00Z",
            signal_event_id="sig-1",
            risk_decision_id="risk-1",
            state_label="PROBE",
            participation_quality_label="UNKNOWN",
            expansion_score=0.0,
            fragility_score=0.0,
            continuation_risk_score=0.0,
            size_multiplier=1.0,
        )
        first_rows = list_continuation_source_events(db_path, symbol="AAPL", limit=100)
        capture_persistence_if_due(
            db_path,
            symbol="AAPL",
            event_timestamp="2026-01-01T14:50:00Z",
            signal_event_id="sig-1",
            risk_decision_id="risk-1",
            state_label="PERSIST",
            participation_quality_label="UNKNOWN",
            expansion_score=0.0,
            fragility_score=0.0,
            continuation_risk_score=0.0,
            size_multiplier=1.0,
        )
        second_rows = list_continuation_source_events(db_path, symbol="AAPL", limit=100)
        self.assertEqual(first_rows[0]["source_event_id"], second_rows[0]["source_event_id"])
        self.assertEqual(first_rows[1]["source_event_id"], second_rows[1]["source_event_id"])

    def test_restart_parent_linkage_after_terminal(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        capture_signal_risk_stage(
            db_path,
            symbol="AAPL",
            event_timestamp="2026-01-01T14:30:00Z",
            signal_event_id="sig-2",
            risk_decision_id="risk-2",
            actionable=False,
            state_label="BLOCK",
            participation_quality_label="UNKNOWN",
            expansion_score=0.0,
            fragility_score=1.0,
            continuation_risk_score=1.0,
        )
        capture_probe_entry(
            db_path,
            symbol="AAPL",
            event_timestamp="2026-01-01T15:00:00Z",
            signal_event_id="sig-2",
            risk_decision_id="risk-2",
            state_label="RESTART",
            participation_quality_label="UNKNOWN",
            expansion_score=0.0,
            fragility_score=0.0,
            continuation_risk_score=0.0,
            size_multiplier=1.0,
        )
        lifecycles = list_continuation_lifecycles(db_path, setup_id="AAPL|2026-01-01|sig-2", symbol="AAPL", limit=100)
        self.assertEqual(len(lifecycles), 2)
        self.assertEqual(lifecycles[1]["parent_lifecycle_id"], lifecycles[0]["lifecycle_id"])

    def test_add_scale_persistence_and_weakening_deterministic(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        capture_setup_detected(
            db_path,
            symbol="MSFT",
            event_timestamp="2026-01-02T14:30:00Z",
            signal_event_id="sig-3",
            risk_decision_id="risk-3",
            state_label="SETUP",
            participation_quality_label="HEALTHY_EXPANSION",
            expansion_score=0.8,
            fragility_score=0.1,
            continuation_risk_score=0.1,
        )
        capture_probe_entry(
            db_path,
            symbol="MSFT",
            event_timestamp="2026-01-02T14:31:00Z",
            signal_event_id="sig-3",
            risk_decision_id="risk-3",
            state_label="PROBE",
            participation_quality_label="HEALTHY_EXPANSION",
            expansion_score=0.8,
            fragility_score=0.1,
            continuation_risk_score=0.1,
            size_multiplier=1.0,
        )
        emit_continuation_capture_event(
            db_path=db_path,
            environment="paper",
            run_id="run-370-a",
            event_type="ADD_ATTEMPT",
            symbol="MSFT",
            side="BUY",
            payload={"event_timestamp": "2026-01-02T14:32:00Z", "signal_event_id": "sig-3", "risk_decision_id": "risk-3", "position_quantity_before": 1.0, "size_multiplier": 1.0},
        )
        capture_add_confirmed_only(
            db_path,
            symbol="MSFT",
            event_timestamp="2026-01-02T14:33:00Z",
            signal_event_id="sig-3",
            risk_decision_id="risk-3",
            order_id="ord-1",
            fill_id="fill-1",
            state_label="ADD",
            participation_quality_label="HEALTHY_EXPANSION",
            expansion_score=0.8,
            fragility_score=0.1,
            continuation_risk_score=0.1,
            size_multiplier=2.0,
        )
        capture_size_increase_only(
            db_path,
            symbol="MSFT",
            event_timestamp="2026-01-02T14:34:00Z",
            signal_event_id="sig-3",
            risk_decision_id="risk-3",
            order_id="ord-1",
            fill_id="fill-1",
            state_label="SCALE",
            participation_quality_label="HEALTHY_EXPANSION",
            expansion_score=0.8,
            fragility_score=0.1,
            continuation_risk_score=0.1,
            size_multiplier=3.0,
        )
        capture_persistence_if_due(
            db_path,
            symbol="MSFT",
            event_timestamp="2026-01-02T14:55:00Z",
            signal_event_id="sig-3",
            risk_decision_id="risk-3",
            state_label="PERSIST",
            participation_quality_label="HEALTHY_EXPANSION",
            expansion_score=0.8,
            fragility_score=0.1,
            continuation_risk_score=0.1,
            size_multiplier=3.0,
        )
        capture_weakening_stage(
            db_path,
            symbol="MSFT",
            event_timestamp="2026-01-02T15:00:00Z",
            signal_event_id="sig-3",
            risk_decision_id="risk-3",
            state_label="WEAKEN",
            participation_quality_label="FRAGILE_CROWDING",
            expansion_score=0.3,
            fragility_score=0.8,
            continuation_risk_score=0.8,
            size_multiplier=2.0,
        )
        capture_weakening_stage(
            db_path,
            symbol="MSFT",
            event_timestamp="2026-01-02T15:01:00Z",
            signal_event_id="sig-3",
            risk_decision_id="risk-3",
            state_label="REDUCE",
            participation_quality_label="FRAGILE_CROWDING",
            expansion_score=0.2,
            fragility_score=0.9,
            continuation_risk_score=0.9,
            size_multiplier=1.0,
        )
        rows = list_continuation_source_events(db_path, symbol="MSFT", limit=100)
        snapshots = list_continuation_snapshots(db_path, lifecycle_id=rows[0]["lifecycle_id"], limit=100)
        event_types = [row["event_type"] for row in rows]
        self.assertIn("ADD_CONFIRMED", event_types)
        self.assertIn("SIZE_INCREASE", event_types)
        self.assertIn("PERSISTENCE_CONFIRMED", event_types)
        self.assertIn("FRAGILITY_WARNING", event_types)
        self.assertIn("REDUCTION_TRIGGER", event_types)
        self.assertEqual(max(int(row["add_depth"]) for row in rows), 1)
        self.assertEqual(max(int(row["scale_depth"]) for row in rows), 1)
        self.assertEqual(max(int(row["persistence_depth"]) for row in rows), 1)
        self.assertTrue(any(int(row["weakening_flag"]) == 1 for row in snapshots))

    def test_terminal_closure_marks_lifecycle_closed(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        capture_probe_entry(
            db_path,
            symbol="NVDA",
            event_timestamp="2026-01-03T14:30:00Z",
            signal_event_id="sig-4",
            risk_decision_id="risk-4",
            state_label="PROBE",
            participation_quality_label="UNKNOWN",
            expansion_score=0.0,
            fragility_score=0.0,
            continuation_risk_score=0.0,
            size_multiplier=1.0,
        )
        capture_terminal_stage(
            db_path,
            symbol="NVDA",
            event_timestamp="2026-01-03T14:35:00Z",
            signal_event_id="sig-4",
            risk_decision_id="risk-4",
            event_type="INVALIDATION",
            state_label="EXITED",
            participation_quality_label="FRAGILE_CROWDING",
            expansion_score=0.0,
            fragility_score=1.0,
            continuation_risk_score=1.0,
            size_multiplier=0.0,
            replay_state="EXITED",
            details={"reason": "test_terminal"},
        )
        active = get_active_continuation_lifecycle(db_path, setup_id="NVDA|2026-01-03|sig-4", symbol="NVDA", session_date="2026-01-03")
        self.assertIsNone(active)

    def test_report_artifacts_generated(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        capture_signal_risk_stage(
            db_path,
            symbol="TSLA",
            event_timestamp="2026-01-04T14:30:00Z",
            signal_event_id="sig-5",
            risk_decision_id="risk-5",
            actionable=True,
            state_label="SETUP",
            participation_quality_label="UNKNOWN",
            expansion_score=0.0,
            fragility_score=0.0,
            continuation_risk_score=0.0,
            size_multiplier=1.0,
        )
        with tempfile.TemporaryDirectory() as out_td:
            artifacts = build_source_time_capture(db_path)
            write_source_time_capture(artifacts, Path(out_td))
            self.assertTrue((Path(out_td) / "task_370_source_event_dataset.csv").exists())
            self.assertTrue((Path(out_td) / "task_370_capture_fidelity.csv").exists())
        with tempfile.TemporaryDirectory() as out_td, patch("sys.argv", ["task370", "--db-path", db_path, "--out-dir", out_td]):
            report_main()
            self.assertTrue((Path(out_td) / "task_370_source_time_capture.md").exists())


if __name__ == "__main__":
    unittest.main()
