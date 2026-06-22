from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_source_truth_lineage_368 import main as task_368_main
from src.backtest.build_multi_event_replay_dataset_366 import MultiEventReplayDatasetArtifacts
from src.backtest.build_source_truth_lineage_368 import (
    build_source_truth_lineage_dataset,
    write_source_truth_lineage_dataset,
)
from src.backtest.build_source_truth_replay_dataset_367 import build_source_truth_replay_dataset
from src.backtest.source_setup_identity import build_source_setup_identity
from src.backtest.source_truth_lineage import build_source_truth_lineage


class TestSourceTruthLineage368(unittest.TestCase):
    def _setup_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "setup_id": "NVDA|2026-01-03|setup_001",
                    "trade_id": "t1",
                    "raw_trade_id": "t1",
                    "raw_signal_id": "s1",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "setup_session_date": "2026-01-03",
                    "setup_type": "breakout_timestamp",
                    "intraday_match_status": "matched_session_bars",
                    "master_match": True,
                    "setup_timestamp": "2026-01-03T14:25:00Z",
                    "breakout_timestamp": "2026-01-03T14:25:00Z",
                    "entry_ts": "2026-01-03T14:30:00Z",
                },
                {
                    "setup_id": "NVDA|2026-01-03|setup_002",
                    "trade_id": "t2",
                    "raw_trade_id": "t2",
                    "raw_signal_id": "s2",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "setup_session_date": "2026-01-03",
                    "setup_type": "entry_timestamp_fallback",
                    "intraday_match_status": "matched_session_bars",
                    "master_match": True,
                    "setup_timestamp": "2026-01-03T15:00:00Z",
                    "breakout_timestamp": None,
                    "entry_ts": "2026-01-03T15:00:00Z",
                },
                {
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "trade_id": "m1",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "setup_session_date": "2026-01-03",
                    "setup_type": "entry_timestamp_fallback",
                    "intraday_match_status": "matched_master_pending_bars",
                    "master_match": True,
                    "setup_timestamp": "2026-01-03T13:55:00Z",
                    "breakout_timestamp": None,
                    "entry_ts": "2026-01-03T14:00:00Z",
                },
                {
                    "setup_id": "META|2026-01-03|setup_001",
                    "trade_id": "x1",
                    "raw_trade_id": "x1",
                    "raw_signal_id": "sx1",
                    "symbol": "META",
                    "session_date": "2026-01-03",
                    "setup_session_date": "2026-01-03",
                    "setup_type": "manual_replay",
                    "intraday_match_status": "matched_master_pending_bars",
                    "master_match": False,
                    "setup_timestamp": "2026-01-03T16:00:00Z",
                    "breakout_timestamp": None,
                    "entry_ts": None,
                },
                {
                    "setup_id": "AMD|2026-01-03|setup_001",
                    "trade_id": "u1",
                    "raw_trade_id": "u1",
                    "raw_signal_id": "su1",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "setup_session_date": "2026-01-03",
                    "setup_type": "unmatched_shadow_only",
                    "intraday_match_status": "unmatched_shadow_only",
                    "master_match": False,
                    "setup_timestamp": "2026-01-03T14:35:00Z",
                    "breakout_timestamp": None,
                    "entry_ts": None,
                },
            ]
        )

    def _multi_event_dataset(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_001",
                    "event_id": "e1",
                    "event_index": 1,
                    "event_type": "SETUP",
                    "timestamp": "2026-01-03T14:25:00Z",
                    "raw_trade_id": "t1",
                    "raw_signal_id": "s1",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.0,
                    "size_multiplier": 0.2,
                },
                {
                    "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_001",
                    "event_id": "e2",
                    "event_index": 2,
                    "event_type": "PROBE_ENTRY",
                    "timestamp": "2026-01-03T14:30:00Z",
                    "raw_trade_id": "t1",
                    "raw_signal_id": "s1",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.2,
                    "size_multiplier": 0.2,
                },
                {
                    "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_001",
                    "event_id": "e3",
                    "event_index": 3,
                    "event_type": "ADD_CONFIRMED",
                    "timestamp": "2026-01-03T14:35:00Z",
                    "raw_trade_id": "t1",
                    "raw_signal_id": "s1",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "BUILDING",
                    "current_size_multiplier": 0.45,
                    "size_multiplier": 0.45,
                },
                {
                    "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_001",
                    "event_id": "e4",
                    "event_index": 4,
                    "event_type": "SIZE_INCREASE",
                    "timestamp": "2026-01-03T14:40:00Z",
                    "raw_trade_id": "t1",
                    "raw_signal_id": "s1",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "BUILDING",
                    "current_size_multiplier": 0.75,
                    "size_multiplier": 0.75,
                },
                {
                    "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_001",
                    "event_id": "e5",
                    "event_index": 5,
                    "event_type": "PERSISTENCE_CONFIRMED",
                    "timestamp": "2026-01-03T14:50:00Z",
                    "raw_trade_id": "t1",
                    "raw_signal_id": "s1",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PERSISTING",
                    "current_size_multiplier": 0.75,
                    "size_multiplier": 0.75,
                },
                {
                    "continuation_id": "NVDA|2026-01-03|setup_002|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_002",
                    "event_id": "e6",
                    "event_index": 1,
                    "event_type": "SETUP",
                    "timestamp": "2026-01-03T15:00:00Z",
                    "raw_trade_id": "t2",
                    "raw_signal_id": "s2",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.0,
                    "size_multiplier": 0.2,
                    "intraday_match_status": "matched_session_bars",
                },
                {
                    "continuation_id": "NVDA|2026-01-03|setup_002|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_002",
                    "event_id": "e7",
                    "event_index": 2,
                    "event_type": "PROBE_ENTRY",
                    "timestamp": "2026-01-03T15:05:00Z",
                    "raw_trade_id": "t2",
                    "raw_signal_id": "s2",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.2,
                    "size_multiplier": 0.2,
                    "intraday_match_status": "missing_intraday_session",
                },
                {
                    "continuation_id": "NVDA|2026-01-03|setup_002|cont_001",
                    "setup_id": "NVDA|2026-01-03|setup_002",
                    "event_id": "e8",
                    "event_index": 3,
                    "event_type": "ADD_CONFIRMED",
                    "timestamp": "2026-01-03T15:10:00Z",
                    "raw_trade_id": "t2",
                    "raw_signal_id": "s2",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "BUILDING",
                    "current_size_multiplier": 0.45,
                    "size_multiplier": 0.45,
                    "intraday_match_status": "missing_intraday_session",
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e9",
                    "event_index": 1,
                    "event_type": "SETUP",
                    "timestamp": "2026-01-03T14:00:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.0,
                    "size_multiplier": 0.3,
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e10",
                    "event_index": 2,
                    "event_type": "PROBE_ENTRY",
                    "timestamp": "2026-01-03T14:05:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.3,
                    "size_multiplier": 0.3,
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e11",
                    "event_index": 3,
                    "event_type": "PERSISTENCE_CONFIRMED",
                    "timestamp": "2026-01-03T14:15:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                    "replay_state": "PERSISTING",
                    "current_size_multiplier": 0.3,
                    "size_multiplier": 0.3,
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e12",
                    "event_index": 4,
                    "event_type": "REDUCTION_TRIGGER",
                    "timestamp": "2026-01-03T14:20:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "transition_reason": "",
                    "replay_state": "REDUCING",
                    "current_size_multiplier": 0.15,
                    "size_multiplier": 0.15,
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e13",
                    "event_index": 5,
                    "event_type": "REDUCTION_TRIGGER",
                    "timestamp": "2026-01-03T14:25:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "transition_reason": "",
                    "replay_state": "REDUCING",
                    "current_size_multiplier": 0.10,
                    "size_multiplier": 0.10,
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e14",
                    "event_index": 6,
                    "event_type": "EXIT_TRIGGER",
                    "timestamp": "2026-01-03T14:30:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "transition_reason": "dislocation_exit",
                    "replay_state": "EXITED",
                    "current_size_multiplier": 0.0,
                    "size_multiplier": 0.0,
                },
                {
                    "continuation_id": "META|2026-01-03|setup_001|cont_001",
                    "setup_id": "META|2026-01-03|setup_001",
                    "event_id": "e15",
                    "event_index": 1,
                    "event_type": "SETUP",
                    "timestamp": "2026-01-03T16:00:00Z",
                    "raw_trade_id": "x1",
                    "raw_signal_id": "sx1",
                    "symbol": "META",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "NEUTRAL_PARTICIPATION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.0,
                    "size_multiplier": 0.1,
                },
                {
                    "continuation_id": "META|2026-01-03|setup_001|cont_001",
                    "setup_id": "META|2026-01-03|setup_001",
                    "event_id": "e16",
                    "event_index": 2,
                    "event_type": "PROBE_ENTRY",
                    "timestamp": "2026-01-03T16:05:00Z",
                    "raw_trade_id": "x1",
                    "raw_signal_id": "sx1",
                    "symbol": "META",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "NEUTRAL_PARTICIPATION",
                    "transition_reason": "",
                    "replay_state": "PROBE",
                    "current_size_multiplier": 0.1,
                    "size_multiplier": 0.1,
                },
                {
                    "continuation_id": "AMD|2026-01-03|setup_001|cont_001",
                    "setup_id": "AMD|2026-01-03|setup_001",
                    "event_id": "e17",
                    "event_index": 1,
                    "event_type": "SETUP",
                    "timestamp": "2026-01-03T14:35:00Z",
                    "raw_trade_id": "u1",
                    "raw_signal_id": "su1",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "transition_reason": "dislocation_exit",
                    "replay_state": "EXITED",
                    "current_size_multiplier": 0.0,
                    "size_multiplier": 0.0,
                },
                {
                    "continuation_id": "AMD|2026-01-03|setup_001|cont_001",
                    "setup_id": "AMD|2026-01-03|setup_001",
                    "event_id": "e18",
                    "event_index": 2,
                    "event_type": "INVALIDATION",
                    "timestamp": "2026-01-03T14:35:00Z",
                    "raw_trade_id": "u1",
                    "raw_signal_id": "su1",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "transition_reason": "dislocation_exit",
                    "replay_state": "EXITED",
                    "current_size_multiplier": 0.0,
                    "size_multiplier": 0.0,
                },
            ]
        )

    def _corrected_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"trade_id": "t1", "symbol": "NVDA", "entry_date": "2026-01-03"},
                {"trade_id": "t2", "symbol": "NVDA", "entry_date": "2026-01-03"},
                {"trade_id": "m1", "symbol": "MSFT", "entry_date": "2026-01-03"},
            ]
        )

    def _intraday_bars(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"symbol": "NVDA", "bar_date": "2026-01-03", "bar_start_ts": "2026-01-03T14:25:00Z", "bar_end_ts": "2026-01-03T14:30:00Z"},
            ]
        )

    def _artifacts_366(self) -> MultiEventReplayDatasetArtifacts:
        dataset = self._multi_event_dataset().copy()
        return MultiEventReplayDatasetArtifacts(
            multi_event_replay_dataset=dataset,
            event_timelines=pd.DataFrame(),
            exposure_evolution=pd.DataFrame(),
            setup_identity_summary=pd.DataFrame(),
            intraday_event_summary=pd.DataFrame(),
            setup_frame=self._setup_frame().copy(),
            lifecycle_rows=pd.DataFrame(),
            replay_trace=pd.DataFrame(),
        )

    def test_setup_identities_deterministic(self) -> None:
        args = (self._setup_frame(), self._multi_event_dataset(), self._corrected_master(), self._intraday_bars())
        first_df, _ = build_source_setup_identity(*args)
        second_df, _ = build_source_setup_identity(*args)
        pd.testing.assert_frame_equal(first_df, second_df)

    def test_setup_origin_priority(self) -> None:
        setup_df, _ = build_source_setup_identity(
            self._setup_frame(),
            self._multi_event_dataset(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        mapping = dict(zip(setup_df["setup_id"], setup_df["setup_origin_type"]))
        self.assertEqual(mapping["NVDA|2026-01-03|setup_001"], "explicit_breakout_setup")
        self.assertEqual(mapping["NVDA|2026-01-03|setup_002"], "explicit_entry_setup")
        self.assertEqual(mapping["MSFT|2026-01-03|setup_001"], "trade_linked_setup")
        self.assertEqual(mapping["META|2026-01-03|setup_001"], "chronology_linked_setup")
        self.assertEqual(mapping["AMD|2026-01-03|setup_001"], "unmatched_setup")

    def test_lineage_ordering_and_event_type_mapping_preserved(self) -> None:
        artifacts_367 = build_source_truth_replay_dataset(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        setup_df, _ = build_source_setup_identity(
            self._setup_frame(),
            self._multi_event_dataset(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        lineage_rows_df, _summary_df, _fidelity_df, _conf_df = build_source_truth_lineage(
            artifacts_367.source_truth_replay_dataset,
            setup_df,
        )
        for _, group in lineage_rows_df.groupby("continuation_id"):
            ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable")["event_id"].tolist()
            self.assertEqual(ordered, group["event_id"].tolist())
        msft_types = lineage_rows_df[lineage_rows_df["continuation_id"].astype(str).eq("MSFT|2026-01-03|setup_001|cont_001")]["lineage_event_type"].tolist()
        self.assertIn("FRAGILITY_WARNING", msft_types)
        self.assertIn("REDUCTION_TRIGGER", msft_types)

    def test_add_linkage_deterministic(self) -> None:
        artifacts = build_source_truth_lineage_dataset(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        nvda = artifacts.add_scale_evolution[artifacts.add_scale_evolution["continuation_id"].astype(str).eq("NVDA|2026-01-03|setup_001|cont_001")]
        self.assertEqual(int(nvda["add_depth"].max()), 1)
        self.assertEqual(int(nvda["scale_depth"].max()), 1)
        self.assertTrue(nvda["add_linked_to_setup"].any())
        self.assertTrue(nvda["scale_linked_to_add"].any())

    def test_persistence_timeline_deterministic(self) -> None:
        artifacts = build_source_truth_lineage_dataset(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        msft = artifacts.persistence_summary[artifacts.persistence_summary["continuation_id"].astype(str).eq("MSFT|2026-01-03|setup_001|cont_001")].iloc[0]
        self.assertGreater(float(msft["persistence_duration_minutes"]), 0.0)
        self.assertEqual(int(msft["persistence_depth"]), 1)
        self.assertGreater(int(msft["fragility_transition_depth"]), 0)

    def test_replay_fidelity_deterministic(self) -> None:
        artifacts = build_source_truth_lineage_dataset(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        metric_map = dict(zip(artifacts.replay_fidelity["metric_name"], artifacts.replay_fidelity["metric_value"]))
        self.assertIn("source_truth_lineage_share", metric_map)
        self.assertIn("replay_fidelity_score", metric_map)
        self.assertGreaterEqual(float(metric_map["replay_fidelity_score"]), 0.0)

    def test_no_future_leakage(self) -> None:
        full_dataset = self._multi_event_dataset()
        prefix_dataset = full_dataset[full_dataset["event_index"].astype(int) <= 2].copy()
        full_366 = self._artifacts_366()
        prefix_366 = MultiEventReplayDatasetArtifacts(
            multi_event_replay_dataset=prefix_dataset,
            event_timelines=pd.DataFrame(),
            exposure_evolution=pd.DataFrame(),
            setup_identity_summary=pd.DataFrame(),
            intraday_event_summary=pd.DataFrame(),
            setup_frame=self._setup_frame().copy(),
            lifecycle_rows=pd.DataFrame(),
            replay_trace=pd.DataFrame(),
        )
        full = build_source_truth_lineage_dataset(
            multi_event_artifacts=full_366,
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        prefix = build_source_truth_lineage_dataset(
            multi_event_artifacts=prefix_366,
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        full_prefix = full.add_scale_evolution[full.add_scale_evolution["event_id"].astype(str).isin(prefix.add_scale_evolution["event_id"].astype(str))].reset_index(drop=True)
        pd.testing.assert_series_equal(full_prefix["add_depth"], prefix.add_scale_evolution["add_depth"].reset_index(drop=True), check_names=False)
        pd.testing.assert_series_equal(full_prefix["scale_depth"], prefix.add_scale_evolution["scale_depth"].reset_index(drop=True), check_names=False)

    def test_report_artifacts_generated(self) -> None:
        artifacts = build_source_truth_lineage_dataset(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            write_source_truth_lineage_dataset(artifacts, out_dir)
            expected = {
                "task_368_lineage_summary.csv",
                "task_368_persistence_timeline.csv",
                "task_368_add_scale_evolution.csv",
                "task_368_replay_fidelity.csv",
                "task_368_lineage_confidence.csv",
            }
            self.assertTrue(expected.issubset({path.name for path in out_dir.iterdir()}))

        with tempfile.TemporaryDirectory() as td, patch(
            "src.backtest.analysis_structural_breakout_source_truth_lineage_368.build_source_truth_lineage_dataset",
            return_value=artifacts,
        ), patch("sys.argv", ["task368", "--out-dir", td]):
            task_368_main()
            self.assertTrue((Path(td) / "task_368_source_truth_lineage.md").exists())

    def test_no_broker_live_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel_path in (
            root / "src" / "backtest" / "source_setup_identity.py",
            root / "src" / "backtest" / "source_truth_lineage.py",
            root / "src" / "backtest" / "add_scale_lineage.py",
            root / "src" / "backtest" / "persistence_lineage_timeline.py",
            root / "src" / "backtest" / "build_source_truth_lineage_368.py",
            root / "src" / "backtest" / "analysis_structural_breakout_source_truth_lineage_368.py",
        ):
            tree = ast.parse(rel_path.read_text(encoding="utf-8"))
            imported: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            lowered = "|".join(name.lower() for name in imported)
            self.assertNotIn("broker", lowered)
            self.assertNotIn("live", lowered)


if __name__ == "__main__":
    unittest.main()
