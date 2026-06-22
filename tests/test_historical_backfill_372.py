from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.analysis_structural_breakout_source_time_capture_372 import main as report_main
from backtest.build_source_time_capture_372 import build_source_time_capture_372, write_source_time_capture_372
from state.store import (
    initialize_store,
    insert_continuation_lifecycle,
    insert_continuation_snapshot,
    insert_continuation_source_event,
    insert_or_ignore_continuation_setup,
    list_continuation_lifecycles,
    list_continuation_setups,
    list_continuation_snapshots,
    list_continuation_source_events,
    summarize_continuation_capture_coverage_filtered,
    summarize_continuation_lifecycle_completeness_filtered,
)


def _fixture_event_rows() -> pd.DataFrame:
    rows = [
        {
            "setup_id": "setup_a",
            "continuation_id": "cont_a",
            "symbol": "AAPL",
            "timestamp": "2026-01-05T14:30:00Z",
            "event_type": "PROBE_ENTRY",
            "replay_state": "PROBE",
            "participation_quality_label": "HEALTHY_EXPANSION",
            "expansion_score": 0.8,
            "fragility_score": 0.1,
            "continuation_risk_score": 0.1,
            "size_multiplier": 1.0,
            "allow_add": True,
            "event_index": 1,
            "event_id": "evt_a_001",
            "raw_trade_id": "trade_a",
            "raw_signal_id": "sig_a",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-05T14:25:00Z",
            "entry_ts": "2026-01-05T14:30:00Z",
            "exit_ts": "2026-01-05T15:30:00Z",
            "breakout_timestamp": "2026-01-05T14:25:00Z",
            "session_date": "2026-01-05",
            "transition_reason": "probe",
            "state_label": "PROBE",
            "current_size_multiplier": 1.0,
            "cumulative_add_count": 0,
            "persistence_duration_minutes": 0.0,
            "linkage_source": "trade_id_master_match",
            "lineage_confidence": 1.0,
            "lineage_quality": "source_truth",
            "lineage_break_reason": "none",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_a",
            "continuation_id": "cont_a",
            "symbol": "AAPL",
            "timestamp": "2026-01-05T14:35:00Z",
            "event_type": "ADD_CONFIRMED",
            "replay_state": "ADD",
            "participation_quality_label": "HEALTHY_EXPANSION",
            "expansion_score": 0.85,
            "fragility_score": 0.1,
            "continuation_risk_score": 0.1,
            "size_multiplier": 2.0,
            "allow_add": True,
            "event_index": 2,
            "event_id": "evt_a_002",
            "raw_trade_id": "trade_a",
            "raw_signal_id": "sig_a",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-05T14:25:00Z",
            "entry_ts": "2026-01-05T14:30:00Z",
            "exit_ts": "2026-01-05T15:30:00Z",
            "breakout_timestamp": "2026-01-05T14:25:00Z",
            "session_date": "2026-01-05",
            "transition_reason": "add",
            "state_label": "ADD",
            "current_size_multiplier": 2.0,
            "cumulative_add_count": 1,
            "persistence_duration_minutes": 0.0,
            "linkage_source": "trade_id_master_match",
            "lineage_confidence": 1.0,
            "lineage_quality": "source_truth",
            "lineage_break_reason": "none",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_a",
            "continuation_id": "cont_a",
            "symbol": "AAPL",
            "timestamp": "2026-01-05T14:36:00Z",
            "event_type": "SIZE_INCREASE",
            "replay_state": "ADD",
            "participation_quality_label": "HEALTHY_EXPANSION",
            "expansion_score": 0.86,
            "fragility_score": 0.1,
            "continuation_risk_score": 0.1,
            "size_multiplier": 2.0,
            "allow_add": True,
            "event_index": 3,
            "event_id": "evt_a_003",
            "raw_trade_id": "trade_a",
            "raw_signal_id": "sig_a",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-05T14:25:00Z",
            "entry_ts": "2026-01-05T14:30:00Z",
            "exit_ts": "2026-01-05T15:30:00Z",
            "breakout_timestamp": "2026-01-05T14:25:00Z",
            "session_date": "2026-01-05",
            "transition_reason": "scale",
            "state_label": "ADD",
            "current_size_multiplier": 2.0,
            "cumulative_add_count": 1,
            "persistence_duration_minutes": 0.0,
            "linkage_source": "trade_id_master_match",
            "lineage_confidence": 1.0,
            "lineage_quality": "source_truth",
            "lineage_break_reason": "none",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_a",
            "continuation_id": "cont_a",
            "symbol": "AAPL",
            "timestamp": "2026-01-05T14:50:00Z",
            "event_type": "PERSISTENCE_CONFIRMED",
            "replay_state": "PERSIST",
            "participation_quality_label": "HEALTHY_EXPANSION",
            "expansion_score": 0.78,
            "fragility_score": 0.2,
            "continuation_risk_score": 0.2,
            "size_multiplier": 2.0,
            "allow_add": True,
            "event_index": 4,
            "event_id": "evt_a_004",
            "raw_trade_id": "trade_a",
            "raw_signal_id": "sig_a",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-05T14:25:00Z",
            "entry_ts": "2026-01-05T14:30:00Z",
            "exit_ts": "2026-01-05T15:30:00Z",
            "breakout_timestamp": "2026-01-05T14:25:00Z",
            "session_date": "2026-01-05",
            "transition_reason": "persist",
            "state_label": "PERSIST",
            "current_size_multiplier": 2.0,
            "cumulative_add_count": 1,
            "persistence_duration_minutes": 20.0,
            "linkage_source": "trade_id_master_match",
            "lineage_confidence": 1.0,
            "lineage_quality": "source_truth",
            "lineage_break_reason": "none",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_a",
            "continuation_id": "cont_a",
            "symbol": "AAPL",
            "timestamp": "2026-01-05T15:00:00Z",
            "event_type": "REDUCTION_TRIGGER",
            "replay_state": "FRAGILE",
            "participation_quality_label": "FRAGILE",
            "expansion_score": 0.4,
            "fragility_score": 0.8,
            "continuation_risk_score": 0.7,
            "size_multiplier": 1.5,
            "allow_add": False,
            "event_index": 5,
            "event_id": "evt_a_005",
            "raw_trade_id": "trade_a",
            "raw_signal_id": "sig_a",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-05T14:25:00Z",
            "entry_ts": "2026-01-05T14:30:00Z",
            "exit_ts": "2026-01-05T15:30:00Z",
            "breakout_timestamp": "2026-01-05T14:25:00Z",
            "session_date": "2026-01-05",
            "transition_reason": "fragile_exit",
            "state_label": "FRAGILE",
            "current_size_multiplier": 1.5,
            "cumulative_add_count": 1,
            "persistence_duration_minutes": 30.0,
            "linkage_source": "trade_id_master_match",
            "lineage_confidence": 1.0,
            "lineage_quality": "source_truth",
            "lineage_break_reason": "terminal_replay_break",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_a",
            "continuation_id": "cont_a",
            "symbol": "AAPL",
            "timestamp": "2026-01-05T15:30:00Z",
            "event_type": "EXIT_TRIGGER",
            "replay_state": "EXIT",
            "participation_quality_label": "FRAGILE",
            "expansion_score": 0.3,
            "fragility_score": 0.9,
            "continuation_risk_score": 0.8,
            "size_multiplier": 0.0,
            "allow_add": False,
            "event_index": 6,
            "event_id": "evt_a_006",
            "raw_trade_id": "trade_a",
            "raw_signal_id": "sig_a",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-05T14:25:00Z",
            "entry_ts": "2026-01-05T14:30:00Z",
            "exit_ts": "2026-01-05T15:30:00Z",
            "breakout_timestamp": "2026-01-05T14:25:00Z",
            "session_date": "2026-01-05",
            "transition_reason": "size_to_zero",
            "state_label": "EXIT",
            "current_size_multiplier": 0.0,
            "cumulative_add_count": 1,
            "persistence_duration_minutes": 60.0,
            "linkage_source": "trade_id_master_match",
            "lineage_confidence": 1.0,
            "lineage_quality": "source_truth",
            "lineage_break_reason": "terminal_replay_break",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_b",
            "continuation_id": "cont_b",
            "symbol": "MSFT",
            "timestamp": "2026-01-06T14:10:00Z",
            "event_type": "INVALIDATION",
            "replay_state": "BLOCK",
            "participation_quality_label": "NEUTRAL",
            "expansion_score": 0.1,
            "fragility_score": 0.6,
            "continuation_risk_score": 0.7,
            "size_multiplier": 0.0,
            "allow_add": False,
            "event_index": 1,
            "event_id": "evt_b_001",
            "raw_trade_id": "trade_b",
            "raw_signal_id": "sig_b",
            "intraday_match_status": "missing_intraday_session",
            "setup_timestamp": "2026-01-06T14:05:00Z",
            "entry_ts": "",
            "exit_ts": "2026-01-06T14:10:00Z",
            "breakout_timestamp": "2026-01-06T14:05:00Z",
            "session_date": "2026-01-06",
            "transition_reason": "blocked",
            "state_label": "BLOCK",
            "current_size_multiplier": 0.0,
            "cumulative_add_count": 0,
            "persistence_duration_minutes": 0.0,
            "linkage_source": "replay_continuity_fallback",
            "lineage_confidence": 0.35,
            "lineage_quality": "synthetic_only",
            "lineage_break_reason": "missing_setup_link",
            "source_linked_flag": False,
        },
        {
            "setup_id": "setup_c",
            "continuation_id": "cont_c1",
            "symbol": "NVDA",
            "timestamp": "2026-01-07T14:20:00Z",
            "event_type": "PROBE_ENTRY",
            "replay_state": "PROBE",
            "participation_quality_label": "HEALTHY_EXPANSION",
            "expansion_score": 0.7,
            "fragility_score": 0.2,
            "continuation_risk_score": 0.2,
            "size_multiplier": 1.0,
            "allow_add": True,
            "event_index": 1,
            "event_id": "evt_c1_001",
            "raw_trade_id": "trade_c",
            "raw_signal_id": "sig_c",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-07T14:15:00Z",
            "entry_ts": "2026-01-07T14:20:00Z",
            "exit_ts": "2026-01-07T14:40:00Z",
            "breakout_timestamp": "2026-01-07T14:15:00Z",
            "session_date": "2026-01-07",
            "transition_reason": "probe",
            "state_label": "PROBE",
            "current_size_multiplier": 1.0,
            "cumulative_add_count": 0,
            "persistence_duration_minutes": 0.0,
            "linkage_source": "entry_bar_match",
            "lineage_confidence": 0.8,
            "lineage_quality": "mixed",
            "lineage_break_reason": "none",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_c",
            "continuation_id": "cont_c1",
            "symbol": "NVDA",
            "timestamp": "2026-01-07T14:40:00Z",
            "event_type": "EXIT_TRIGGER",
            "replay_state": "EXIT",
            "participation_quality_label": "NEUTRAL",
            "expansion_score": 0.2,
            "fragility_score": 0.5,
            "continuation_risk_score": 0.6,
            "size_multiplier": 0.0,
            "allow_add": False,
            "event_index": 2,
            "event_id": "evt_c1_002",
            "raw_trade_id": "trade_c",
            "raw_signal_id": "sig_c",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-07T14:15:00Z",
            "entry_ts": "2026-01-07T14:20:00Z",
            "exit_ts": "2026-01-07T14:40:00Z",
            "breakout_timestamp": "2026-01-07T14:15:00Z",
            "session_date": "2026-01-07",
            "transition_reason": "exit",
            "state_label": "EXIT",
            "current_size_multiplier": 0.0,
            "cumulative_add_count": 0,
            "persistence_duration_minutes": 20.0,
            "linkage_source": "entry_bar_match",
            "lineage_confidence": 0.8,
            "lineage_quality": "mixed",
            "lineage_break_reason": "none",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_c",
            "continuation_id": "cont_c2",
            "symbol": "NVDA",
            "timestamp": "2026-01-07T15:10:00Z",
            "event_type": "PROBE_ENTRY",
            "replay_state": "PROBE",
            "participation_quality_label": "HEALTHY_EXPANSION",
            "expansion_score": 0.75,
            "fragility_score": 0.15,
            "continuation_risk_score": 0.15,
            "size_multiplier": 1.0,
            "allow_add": True,
            "event_index": 1,
            "event_id": "evt_c2_001",
            "raw_trade_id": "trade_c",
            "raw_signal_id": "sig_c",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-07T14:15:00Z",
            "entry_ts": "2026-01-07T15:10:00Z",
            "exit_ts": "2026-01-07T15:20:00Z",
            "breakout_timestamp": "2026-01-07T14:15:00Z",
            "session_date": "2026-01-07",
            "transition_reason": "restart",
            "state_label": "PROBE",
            "current_size_multiplier": 1.0,
            "cumulative_add_count": 0,
            "persistence_duration_minutes": 0.0,
            "linkage_source": "entry_bar_match",
            "lineage_confidence": 0.8,
            "lineage_quality": "mixed",
            "lineage_break_reason": "timestamp_gap_break",
            "source_linked_flag": True,
        },
        {
            "setup_id": "setup_c",
            "continuation_id": "cont_c2",
            "symbol": "NVDA",
            "timestamp": "2026-01-07T15:20:00Z",
            "event_type": "INVALIDATION",
            "replay_state": "INVALIDATE",
            "participation_quality_label": "FRAGILE",
            "expansion_score": 0.2,
            "fragility_score": 0.7,
            "continuation_risk_score": 0.8,
            "size_multiplier": 0.0,
            "allow_add": False,
            "event_index": 2,
            "event_id": "evt_c2_002",
            "raw_trade_id": "trade_c",
            "raw_signal_id": "sig_c",
            "intraday_match_status": "matched",
            "setup_timestamp": "2026-01-07T14:15:00Z",
            "entry_ts": "2026-01-07T15:10:00Z",
            "exit_ts": "2026-01-07T15:20:00Z",
            "breakout_timestamp": "2026-01-07T14:15:00Z",
            "session_date": "2026-01-07",
            "transition_reason": "blocked",
            "state_label": "INVALIDATE",
            "current_size_multiplier": 0.0,
            "cumulative_add_count": 0,
            "persistence_duration_minutes": 10.0,
            "linkage_source": "entry_bar_match",
            "lineage_confidence": 0.8,
            "lineage_quality": "mixed",
            "lineage_break_reason": "timestamp_gap_break",
            "source_linked_flag": True,
        },
    ]
    return pd.DataFrame(rows)


def _fixture_lineage_rows(events: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "evt_a_001": "PROBE_ENTRY",
        "evt_a_002": "ADD_CONFIRMED",
        "evt_a_003": "SIZE_INCREASE",
        "evt_a_004": "PERSISTENCE_CONFIRMED",
        "evt_a_005": "FRAGILITY_WARNING",
        "evt_a_006": "EXIT_TRIGGER",
        "evt_b_001": "INVALIDATION",
        "evt_c1_001": "PROBE_ENTRY",
        "evt_c1_002": "EXIT_TRIGGER",
        "evt_c2_001": "PROBE_ENTRY",
        "evt_c2_002": "INVALIDATION",
    }
    setup_origin = {"setup_a": "explicit_breakout_setup", "setup_b": "replay_linked_setup", "setup_c": "explicit_entry_setup"}
    rows = []
    for _, row in events.iterrows():
        rows.append(
            {
                "continuation_id": row["continuation_id"],
                "setup_id": row["setup_id"],
                "event_id": row["event_id"],
                "timestamp": row["timestamp"],
                "event_index": row["event_index"],
                "symbol": row["symbol"],
                "lineage_event_type": mapping[row["event_id"]],
                "setup_origin_type": setup_origin[row["setup_id"]],
                "event_source": "SOURCE_TRUTH" if row["source_linked_flag"] else "REPLAY_INFERRED",
                "source_truth_flag": bool(row["source_linked_flag"]),
            }
        )
    return pd.DataFrame(rows)


def _fixture_add_scale() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"continuation_id": "cont_a", "event_id": "evt_a_001", "add_depth": 0, "scale_depth": 0, "cumulative_size_multiplier": 1.0, "has_add_attempt": False, "has_add_confirmed": False, "has_scale_up": False},
            {"continuation_id": "cont_a", "event_id": "evt_a_002", "add_depth": 1, "scale_depth": 0, "cumulative_size_multiplier": 2.0, "has_add_attempt": True, "has_add_confirmed": True, "has_scale_up": False},
            {"continuation_id": "cont_a", "event_id": "evt_a_003", "add_depth": 1, "scale_depth": 1, "cumulative_size_multiplier": 2.0, "has_add_attempt": True, "has_add_confirmed": True, "has_scale_up": True},
            {"continuation_id": "cont_a", "event_id": "evt_a_004", "add_depth": 1, "scale_depth": 1, "cumulative_size_multiplier": 2.0, "has_add_attempt": True, "has_add_confirmed": True, "has_scale_up": True},
            {"continuation_id": "cont_a", "event_id": "evt_a_005", "add_depth": 1, "scale_depth": 1, "cumulative_size_multiplier": 1.5, "has_add_attempt": True, "has_add_confirmed": True, "has_scale_up": True},
            {"continuation_id": "cont_a", "event_id": "evt_a_006", "add_depth": 1, "scale_depth": 1, "cumulative_size_multiplier": 0.0, "has_add_attempt": True, "has_add_confirmed": True, "has_scale_up": True},
        ]
    )


def _fixture_persistence_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"continuation_id": "cont_a", "setup_id": "setup_a", "persistence_duration_minutes": 60.0, "persistence_depth": 1, "fragility_transition_depth": 5, "invalidation_depth": 0},
            {"continuation_id": "cont_b", "setup_id": "setup_b", "persistence_duration_minutes": 0.0, "persistence_depth": 0, "fragility_transition_depth": 0, "invalidation_depth": 1},
            {"continuation_id": "cont_c1", "setup_id": "setup_c", "persistence_duration_minutes": 20.0, "persistence_depth": 0, "fragility_transition_depth": 0, "invalidation_depth": 0},
            {"continuation_id": "cont_c2", "setup_id": "setup_c", "persistence_duration_minutes": 10.0, "persistence_depth": 0, "fragility_transition_depth": 0, "invalidation_depth": 2},
        ]
    )


def _fixture_setup_identity() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"setup_id": "setup_a", "symbol": "AAPL", "session_date": "2026-01-05", "setup_origin_type": "explicit_breakout_setup", "setup_confidence": 1.0},
            {"setup_id": "setup_b", "symbol": "MSFT", "session_date": "2026-01-06", "setup_origin_type": "replay_linked_setup", "setup_confidence": 0.35},
            {"setup_id": "setup_c", "symbol": "NVDA", "session_date": "2026-01-07", "setup_origin_type": "explicit_entry_setup", "setup_confidence": 0.9},
        ]
    )


def _fixture_corrected_master() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_id": "trade_a", "current_split": "anchored_oos", "realized_R": 2.0},
            {"trade_id": "trade_b", "current_split": "full_period", "realized_R": -1.0},
            {"trade_id": "trade_c", "current_split": "anchored_oos", "realized_R": 0.5},
        ]
    )


class TestHistoricalBackfill372(unittest.TestCase):
    def _db_path(self) -> tuple[tempfile.TemporaryDirectory[str], str]:
        td = tempfile.TemporaryDirectory()
        db_path = str(Path(td.name) / "state.db")
        initialize_store(db_path)
        return td, db_path

    def _seed_paper_runtime_row(self, db_path: str) -> None:
        insert_or_ignore_continuation_setup(
            db_path,
            setup_id="paper_setup",
            symbol="PAPER",
            session_date="2026-01-01",
            setup_timestamp="2026-01-01T14:00:00Z",
            setup_origin="paper_runtime",
            signal_event_id="paper_sig",
            risk_decision_id="paper_risk",
            created_at="2026-01-01T14:00:00Z",
        )
        insert_continuation_lifecycle(
            db_path,
            lifecycle_id="paper_life",
            setup_id="paper_setup",
            parent_lifecycle_id=None,
            symbol="PAPER",
            session_date="2026-01-01",
            started_at="2026-01-01T14:00:00Z",
            identity_origin="explicit_signal_identity",
            identity_confidence=1.0,
            created_at="2026-01-01T14:00:00Z",
        )
        insert_continuation_source_event(
            db_path,
            source_event_id="paper_evt_001",
            lifecycle_id="paper_life",
            setup_id="paper_setup",
            parent_lifecycle_id=None,
            signal_event_id="paper_sig",
            risk_decision_id="paper_risk",
            order_intent_id="paper_intent",
            order_id=None,
            fill_id=None,
            reconciliation_id=None,
            trade_run_id="paper_run",
            symbol="PAPER",
            session_date="2026-01-01",
            event_type="PROBE_ENTRY",
            event_source="SOURCE_CAPTURED",
            event_timestamp="2026-01-01T14:00:00Z",
            state_label="PROBE",
            participation_quality_label="HEALTHY_EXPANSION",
            expansion_score=0.8,
            fragility_score=0.1,
            continuation_risk_score=0.1,
            size_multiplier=1.0,
            add_depth=0,
            scale_depth=0,
            persistence_depth=0,
            details_json="{}",
            created_at="2026-01-01T14:00:00Z",
        )
        insert_continuation_snapshot(
            db_path,
            snapshot_id="paper_snap_001",
            lifecycle_id="paper_life",
            setup_id="paper_setup",
            event_id="paper_evt_001",
            snapshot_timestamp="2026-01-01T14:00:00Z",
            replay_state="PROBE",
            size_multiplier=1.0,
            add_depth=0,
            scale_depth=0,
            persistence_depth=0,
            weakening_flag=False,
            invalidated_flag=False,
            created_at="2026-01-01T14:00:00Z",
        )

    def _build(self, db_path: str, batch_id: str):
        events = _fixture_event_rows()
        return build_source_time_capture_372(
            db_path=db_path,
            capture_batch_id=batch_id,
            source_truth_replay_dataset_df=events,
            lineage_rows_df=_fixture_lineage_rows(events),
            lineage_summary_df=pd.DataFrame(),
            add_scale_evolution_df=_fixture_add_scale(),
            persistence_summary_df=_fixture_persistence_summary(),
            setup_identity_df=_fixture_setup_identity(),
            corrected_master_df=_fixture_corrected_master(),
        )

    def test_backfill_coexists_with_paper_rows_and_filters_by_capture_mode(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        self._seed_paper_runtime_row(db_path)
        artifacts = self._build(db_path, "batch_a")
        self.assertFalse(artifacts.historical_source_event_dataset.empty)
        historical_rows = list_continuation_source_events(db_path, capture_mode="historical_backfill", limit=200)
        paper_rows = list_continuation_source_events(db_path, capture_mode="paper_runtime", limit=200)
        self.assertTrue(all(str(row["source_event_id"]).startswith("hist372|") for row in historical_rows))
        self.assertEqual(len(paper_rows), 1)
        self.assertEqual(len(list_continuation_setups(db_path, capture_mode="paper_runtime", limit=50)), 1)
        self.assertGreater(len(list_continuation_setups(db_path, capture_mode="historical_backfill", limit=50)), 0)

    def test_backfill_rerun_replaces_same_batch_only(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        first = self._build(db_path, "batch_same")
        count_first = len(first.historical_source_event_dataset)
        self._build(db_path, "batch_other")
        count_two_batches = len(list_continuation_source_events(db_path, capture_mode="historical_backfill", limit=500))
        self._build(db_path, "batch_same")
        rows_same = list_continuation_source_events(db_path, capture_mode="historical_backfill", capture_batch_id="batch_same", limit=500)
        rows_other = list_continuation_source_events(db_path, capture_mode="historical_backfill", capture_batch_id="batch_other", limit=500)
        self.assertEqual(len(rows_same), count_first)
        self.assertGreater(count_two_batches, len(rows_same))
        self.assertGreater(len(rows_other), 0)

    def test_deterministic_mapping_labels_parent_linkage_and_scope_outputs(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        artifacts = self._build(db_path, "batch_scope")
        events = artifacts.historical_source_event_dataset
        self.assertIn("SOURCE_CAPTURED", set(events["event_source"].astype(str)))
        self.assertIn("SESSION_DERIVED", set(events["event_source"].astype(str)))
        self.assertIn("REPLAY_DERIVED", set(events["event_source"].astype(str)))
        lifecycles = artifacts.historical_lifecycle_identity
        restart_row = lifecycles[lifecycles["lifecycle_id"].astype(str).str.contains("cont_c2")].iloc[0]
        self.assertTrue(str(restart_row["parent_lifecycle_id"]).strip())
        panel_scopes = set(artifacts.lifecycle_backtest_panel["evaluation_scope"].astype(str))
        self.assertIn("full_period", panel_scopes)
        self.assertIn("anchored_oos", panel_scopes)

    def test_coverage_and_report_artifacts_are_non_empty(self) -> None:
        td, db_path = self._db_path()
        self.addCleanup(td.cleanup)
        artifacts = self._build(db_path, "batch_report")
        completeness = summarize_continuation_lifecycle_completeness_filtered(
            db_path,
            capture_mode="historical_backfill",
            capture_batch_id="batch_report",
            limit=200,
        )
        coverage = summarize_continuation_capture_coverage_filtered(
            db_path,
            capture_mode="historical_backfill",
            capture_batch_id="batch_report",
        )
        self.assertGreater(len(completeness), 0)
        self.assertGreater(coverage["full_lifecycle_sample_count"], 0.0)
        with tempfile.TemporaryDirectory() as out_td:
            out_dir = Path(out_td)
            write_source_time_capture_372(artifacts, out_dir)
            self.assertTrue((out_dir / "task_372_lifecycle_backtest_panel.csv").exists())
            self.assertTrue((out_dir / "task_372_backfill_coverage_summary.csv").exists())
        with tempfile.TemporaryDirectory() as out_td, patch(
            "sys.argv",
            ["task372", "--db-path", db_path, "--capture-batch-id", "batch_report", "--reuse-existing-batch", "--out-dir", out_td],
        ):
            report_main()
            report_path = Path(out_td) / "task_372_historical_source_backfill.md"
            self.assertTrue(report_path.exists())
            self.assertIn("full_lifecycle_sample_share", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
