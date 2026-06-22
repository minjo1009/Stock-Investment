from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_event_capture_369 import _write_report, main as task_369_main
from src.backtest.build_continuation_event_capture_369 import (
    build_continuation_event_capture,
    write_continuation_event_capture,
)
from src.backtest.build_multi_event_replay_dataset_366 import MultiEventReplayDatasetArtifacts


class TestEventCapture369(unittest.TestCase):
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
        base = {
            "session_date": "2026-01-03",
            "expansion_score": 0.8,
            "fragility_score": 0.2,
            "continuation_risk_score": 0.25,
            "state_label": "NORMAL",
        }
        rows = [
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e1",
                "event_index": 1,
                "event_type": "SETUP",
                "timestamp": "2026-01-03T14:25:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1",
                "symbol": "NVDA",
                "participation_quality_label": "HEALTHY_EXPANSION",
                "transition_reason": "",
                "replay_state": "PROBE",
                "current_size_multiplier": 0.0,
                "size_multiplier": 0.2,
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e2",
                "event_index": 2,
                "event_type": "PROBE_ENTRY",
                "timestamp": "2026-01-03T14:30:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1",
                "symbol": "NVDA",
                "participation_quality_label": "HEALTHY_EXPANSION",
                "transition_reason": "",
                "replay_state": "PROBE",
                "current_size_multiplier": 0.2,
                "size_multiplier": 0.2,
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e3",
                "event_index": 3,
                "event_type": "ADD_CONFIRMED",
                "timestamp": "2026-01-03T14:35:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1",
                "symbol": "NVDA",
                "participation_quality_label": "HEALTHY_EXPANSION",
                "transition_reason": "",
                "replay_state": "BUILDING",
                "current_size_multiplier": 0.45,
                "size_multiplier": 0.45,
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e4",
                "event_index": 4,
                "event_type": "SIZE_INCREASE",
                "timestamp": "2026-01-03T14:40:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1",
                "symbol": "NVDA",
                "participation_quality_label": "HEALTHY_EXPANSION",
                "transition_reason": "",
                "replay_state": "BUILDING",
                "current_size_multiplier": 0.75,
                "size_multiplier": 0.75,
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e5",
                "event_index": 5,
                "event_type": "PERSISTENCE_CONFIRMED",
                "timestamp": "2026-01-03T14:50:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1",
                "symbol": "NVDA",
                "participation_quality_label": "HEALTHY_EXPANSION",
                "transition_reason": "",
                "replay_state": "PERSISTING",
                "current_size_multiplier": 0.75,
                "size_multiplier": 0.75,
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e6",
                "event_index": 6,
                "event_type": "REDUCTION_TRIGGER",
                "timestamp": "2026-01-03T14:53:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1",
                "symbol": "NVDA",
                "participation_quality_label": "FRAGILE_CROWDING",
                "transition_reason": "fragile_exit",
                "replay_state": "REDUCING",
                "current_size_multiplier": 0.4,
                "size_multiplier": 0.4,
                "fragility_score": 0.7,
                "state_label": "DISLOCATION",
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e6b",
                "event_index": 7,
                "event_type": "EXIT_TRIGGER",
                "timestamp": "2026-01-03T14:55:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1",
                "symbol": "NVDA",
                "participation_quality_label": "FRAGILE_CROWDING",
                "transition_reason": "dislocation_exit",
                "replay_state": "EXITED",
                "current_size_multiplier": 0.0,
                "size_multiplier": 0.0,
                "fragility_score": 0.7,
                "state_label": "DISLOCATION",
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_002",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e7",
                "event_index": 1,
                "event_type": "SETUP",
                "timestamp": "2026-01-03T15:05:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1b",
                "symbol": "NVDA",
                "participation_quality_label": "NEUTRAL_PARTICIPATION",
                "transition_reason": "",
                "replay_state": "PROBE",
                "current_size_multiplier": 0.0,
                "size_multiplier": 0.1,
                "expansion_score": 0.45,
                "fragility_score": 0.35,
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_002",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e8",
                "event_index": 2,
                "event_type": "PROBE_ENTRY",
                "timestamp": "2026-01-03T15:10:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1b",
                "symbol": "NVDA",
                "participation_quality_label": "NEUTRAL_PARTICIPATION",
                "transition_reason": "",
                "replay_state": "PROBE",
                "current_size_multiplier": 0.1,
                "size_multiplier": 0.1,
                "expansion_score": 0.45,
                "fragility_score": 0.35,
            },
            {
                **base,
                "continuation_id": "NVDA|2026-01-03|setup_001|cont_002",
                "setup_id": "NVDA|2026-01-03|setup_001",
                "event_id": "raw_e9",
                "event_index": 3,
                "event_type": "INVALIDATION",
                "timestamp": "2026-01-03T15:15:00Z",
                "raw_trade_id": "t1",
                "raw_signal_id": "s1b",
                "symbol": "NVDA",
                "participation_quality_label": "FRAGILE_CROWDING",
                "transition_reason": "dislocation_exit",
                "replay_state": "EXITED",
                "current_size_multiplier": 0.0,
                "size_multiplier": 0.0,
                "fragility_score": 0.8,
                "state_label": "DISLOCATION",
            },
            {
                **base,
                "continuation_id": "META|2026-01-03|setup_001|cont_001",
                "setup_id": "META|2026-01-03|setup_001",
                "event_id": "raw_e10",
                "event_index": 1,
                "event_type": "SETUP",
                "timestamp": "2026-01-03T16:00:00Z",
                "raw_trade_id": "x1",
                "raw_signal_id": "sx1",
                "symbol": "META",
                "participation_quality_label": "NEUTRAL_PARTICIPATION",
                "transition_reason": "",
                "replay_state": "PROBE",
                "current_size_multiplier": 0.0,
                "size_multiplier": 0.1,
                "expansion_score": 0.4,
                "fragility_score": 0.4,
            },
            {
                **base,
                "continuation_id": "META|2026-01-03|setup_001|cont_001",
                "setup_id": "META|2026-01-03|setup_001",
                "event_id": "raw_e11",
                "event_index": 2,
                "event_type": "PROBE_ENTRY",
                "timestamp": "2026-01-03T16:05:00Z",
                "raw_trade_id": "x1",
                "raw_signal_id": "sx1",
                "symbol": "META",
                "participation_quality_label": "NEUTRAL_PARTICIPATION",
                "transition_reason": "",
                "replay_state": "PROBE",
                "current_size_multiplier": 0.1,
                "size_multiplier": 0.1,
                "expansion_score": 0.4,
                "fragility_score": 0.4,
            },
            {
                **base,
                "continuation_id": "AMD|2026-01-03|setup_001|cont_001",
                "setup_id": "AMD|2026-01-03|setup_001",
                "event_id": "raw_e12",
                "event_index": 1,
                "event_type": "SETUP",
                "timestamp": "2026-01-03T14:35:00Z",
                "raw_trade_id": "u1",
                "raw_signal_id": "su1",
                "symbol": "AMD",
                "participation_quality_label": "FRAGILE_CROWDING",
                "transition_reason": "dislocation_exit",
                "replay_state": "EXITED",
                "current_size_multiplier": 0.0,
                "size_multiplier": 0.0,
                "expansion_score": 0.2,
                "fragility_score": 0.9,
                "state_label": "DISLOCATION",
            },
            {
                **base,
                "continuation_id": "AMD|2026-01-03|setup_001|cont_001",
                "setup_id": "AMD|2026-01-03|setup_001",
                "event_id": "raw_e13",
                "event_index": 2,
                "event_type": "INVALIDATION",
                "timestamp": "2026-01-03T14:35:00Z",
                "raw_trade_id": "u1",
                "raw_signal_id": "su1",
                "symbol": "AMD",
                "participation_quality_label": "FRAGILE_CROWDING",
                "transition_reason": "dislocation_exit",
                "replay_state": "EXITED",
                "current_size_multiplier": 0.0,
                "size_multiplier": 0.0,
                "expansion_score": 0.2,
                "fragility_score": 0.9,
                "state_label": "DISLOCATION",
            },
        ]
        return pd.DataFrame(rows)

    def _corrected_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"trade_id": "t1", "symbol": "NVDA", "entry_date": "2026-01-03"},
            ]
        )

    def _intraday_bars(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"symbol": "NVDA", "bar_date": "2026-01-03", "bar_start_ts": "2026-01-03T14:25:00Z", "bar_end_ts": "2026-01-03T14:30:00Z"},
            ]
        )

    def _artifacts_366(self) -> MultiEventReplayDatasetArtifacts:
        return MultiEventReplayDatasetArtifacts(
            multi_event_replay_dataset=self._multi_event_dataset().copy(),
            event_timelines=pd.DataFrame(),
            exposure_evolution=pd.DataFrame(),
            setup_identity_summary=pd.DataFrame(),
            intraday_event_summary=pd.DataFrame(),
            setup_frame=self._setup_frame().copy(),
            lifecycle_rows=pd.DataFrame(),
            replay_trace=pd.DataFrame(),
        )

    def test_canonical_ids_and_event_types_deterministic(self) -> None:
        first = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        second = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        pd.testing.assert_frame_equal(first.canonical_events, second.canonical_events)
        self.assertTrue(first.canonical_events["event_id"].astype(str).str.contains(r"\|evt_").all())
        self.assertIn("FRAGILITY_WARNING", first.canonical_events["event_type"].tolist())

    def test_lifecycle_and_parent_linkage_deterministic(self) -> None:
        artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        lifecycle_df = artifacts.lifecycle_identity
        child = lifecycle_df[lifecycle_df["lifecycle_id"].astype(str).eq("NVDA|2026-01-03|setup_001|cont_002")].iloc[0]
        self.assertEqual(str(child["parent_lifecycle_id"]), "NVDA|2026-01-03|setup_001|cont_001")
        root = lifecycle_df[lifecycle_df["lifecycle_id"].astype(str).eq("NVDA|2026-01-03|setup_001|cont_001")].iloc[0]
        self.assertTrue(bool(root["is_root_lifecycle"]))

    def test_event_source_mapping_deterministic(self) -> None:
        artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        canonical = artifacts.canonical_events
        source_map = canonical.groupby("lifecycle_id", dropna=False)["event_source"].agg(lambda values: set(values.astype(str)))
        self.assertEqual(source_map["NVDA|2026-01-03|setup_001|cont_001"], {"SOURCE_CAPTURED"})
        self.assertEqual(source_map["META|2026-01-03|setup_001|cont_001"], {"SESSION_DERIVED"})
        self.assertEqual(source_map["AMD|2026-01-03|setup_001|cont_001"], {"REPLAY_DERIVED"})

    def test_lifecycle_snapshots_and_depths_deterministic(self) -> None:
        artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        snaps = artifacts.lifecycle_snapshots
        nvda = snaps[snaps["lifecycle_id"].astype(str).eq("NVDA|2026-01-03|setup_001|cont_001")]
        self.assertEqual(int(nvda["add_depth"].max()), 1)
        self.assertEqual(int(nvda["scale_depth"].max()), 1)
        self.assertEqual(int(nvda["persistence_depth"].max()), 1)
        child = snaps[snaps["lifecycle_id"].astype(str).eq("NVDA|2026-01-03|setup_001|cont_002")]
        self.assertTrue(child["invalidated_flag"].any())
        msft = snaps[snaps["lifecycle_id"].astype(str).eq("META|2026-01-03|setup_001|cont_001")]
        self.assertFalse(msft["weakening_flag"].any())

    def test_capture_fidelity_metrics_deterministic(self) -> None:
        artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        metric_map = dict(zip(artifacts.capture_fidelity["metric_name"], artifacts.capture_fidelity["metric_value"]))
        self.assertIn("explicit_event_capture_share", metric_map)
        self.assertIn("parent_linkage_share", metric_map)
        self.assertIn("capture_fidelity_score", metric_map)
        self.assertGreaterEqual(float(metric_map["capture_fidelity_score"]), 0.0)

    def test_no_future_leakage(self) -> None:
        full_df = self._multi_event_dataset().copy()
        full_df["timestamp"] = pd.to_datetime(full_df["timestamp"], errors="coerce", utc=True)
        cutoff = pd.Timestamp("2026-01-03T14:40:00Z")
        prefix_df = full_df[full_df["timestamp"].le(cutoff)].copy()
        full_artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        prefix_366 = MultiEventReplayDatasetArtifacts(
            multi_event_replay_dataset=prefix_df,
            event_timelines=pd.DataFrame(),
            exposure_evolution=pd.DataFrame(),
            setup_identity_summary=pd.DataFrame(),
            intraday_event_summary=pd.DataFrame(),
            setup_frame=self._setup_frame().copy(),
            lifecycle_rows=pd.DataFrame(),
            replay_trace=pd.DataFrame(),
        )
        prefix_artifacts = build_continuation_event_capture(
            multi_event_artifacts=prefix_366,
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        compare_cols = [
            "event_id",
            "raw_event_id",
            "setup_id",
            "lifecycle_id",
            "parent_lifecycle_id",
            "event_source",
            "add_depth",
            "scale_depth",
        ]
        prefix_raw_event_ids = set(prefix_df["event_id"].astype(str))
        full_prefix = (
            full_artifacts.canonical_events[
                full_artifacts.canonical_events["raw_event_id"].astype(str).isin(prefix_raw_event_ids)
            ][compare_cols]
            .sort_values(["lifecycle_id", "raw_event_id"], kind="stable")
            .reset_index(drop=True)
        )
        prefix_only = (
            prefix_artifacts.canonical_events[compare_cols]
            .sort_values(["lifecycle_id", "raw_event_id"], kind="stable")
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(full_prefix, prefix_only)
        full_snapshots = (
            full_artifacts.lifecycle_snapshots[
                full_artifacts.lifecycle_snapshots["event_id"].astype(str).isin(prefix_artifacts.lifecycle_snapshots["event_id"].astype(str))
            ]["persistence_depth"]
            .reset_index(drop=True)
        )
        prefix_snapshots = prefix_artifacts.lifecycle_snapshots["persistence_depth"].reset_index(drop=True)
        pd.testing.assert_series_equal(full_snapshots, prefix_snapshots, check_names=False)

    def test_appending_later_event_preserves_existing_canonical_rows(self) -> None:
        base_df = self._multi_event_dataset().copy()
        base_artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        appended_df = pd.concat(
            [
                base_df,
                pd.DataFrame(
                    [
                        {
                            "session_date": "2026-01-03",
                            "expansion_score": 0.82,
                            "fragility_score": 0.22,
                            "continuation_risk_score": 0.2,
                            "state_label": "NORMAL",
                            "continuation_id": "NVDA|2026-01-03|setup_001|cont_001",
                            "setup_id": "NVDA|2026-01-03|setup_001",
                            "event_id": "raw_e14",
                            "event_index": 8,
                            "event_type": "PERSISTENCE_CONFIRMED",
                            "timestamp": "2026-01-03T15:20:00Z",
                            "raw_trade_id": "t1",
                            "raw_signal_id": "s1c",
                            "symbol": "NVDA",
                            "participation_quality_label": "HEALTHY_EXPANSION",
                            "transition_reason": "",
                            "replay_state": "PERSISTING",
                            "current_size_multiplier": 0.75,
                            "size_multiplier": 0.75,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        appended_366 = MultiEventReplayDatasetArtifacts(
            multi_event_replay_dataset=appended_df,
            event_timelines=pd.DataFrame(),
            exposure_evolution=pd.DataFrame(),
            setup_identity_summary=pd.DataFrame(),
            intraday_event_summary=pd.DataFrame(),
            setup_frame=self._setup_frame().copy(),
            lifecycle_rows=pd.DataFrame(),
            replay_trace=pd.DataFrame(),
        )
        appended_artifacts = build_continuation_event_capture(
            multi_event_artifacts=appended_366,
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        compare_cols = [
            "event_id",
            "raw_event_id",
            "setup_id",
            "lifecycle_id",
            "parent_lifecycle_id",
            "event_source",
            "add_depth",
            "scale_depth",
            "size_multiplier",
        ]
        original_raw_ids = set(base_df["event_id"].astype(str))
        base_rows = (
            base_artifacts.canonical_events[compare_cols]
            .sort_values(["lifecycle_id", "raw_event_id"], kind="stable")
            .reset_index(drop=True)
        )
        appended_existing_rows = (
            appended_artifacts.canonical_events[
                appended_artifacts.canonical_events["raw_event_id"].astype(str).isin(original_raw_ids)
            ][compare_cols]
            .sort_values(["lifecycle_id", "raw_event_id"], kind="stable")
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(base_rows, appended_existing_rows)
        new_row = appended_artifacts.canonical_events[
            appended_artifacts.canonical_events["raw_event_id"].astype(str).eq("raw_e14")
        ]
        self.assertEqual(len(new_row), 1)
        self.assertEqual(str(new_row.iloc[0]["event_type"]), "PERSISTENCE_CONFIRMED")

    def test_report_artifacts_generated(self) -> None:
        artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            write_continuation_event_capture(artifacts, out_dir)
            expected = {
                "task_369_canonical_events.csv",
                "task_369_lifecycle_identity.csv",
                "task_369_lifecycle_snapshots.csv",
                "task_369_event_source_summary.csv",
                "task_369_identity_origin_summary.csv",
                "task_369_capture_fidelity.csv",
            }
            self.assertTrue(expected.issubset({path.name for path in out_dir.iterdir()}))

        with tempfile.TemporaryDirectory() as td, patch(
            "src.backtest.analysis_structural_breakout_event_capture_369.build_continuation_event_capture",
            return_value=artifacts,
        ), patch("sys.argv", ["task369", "--out-dir", td]):
            task_369_main()
            self.assertTrue((Path(td) / "task_369_event_capture.md").exists())

    def test_report_artifact_content_is_deterministic_across_rewrites(self) -> None:
        artifacts = build_continuation_event_capture(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            write_continuation_event_capture(artifacts, out_dir)
            _write_report(out_dir, artifacts)
            first_report = (out_dir / "task_369_event_capture.md").read_text(encoding="utf-8")
            self.assertIn("## Capture Fidelity", first_report)
            self.assertIn("## Canonical Events", first_report)
            self.assertIn("NVDA|2026-01-03|setup_001|cont_001", first_report)

            write_continuation_event_capture(artifacts, out_dir)
            _write_report(out_dir, artifacts)
            second_report = (out_dir / "task_369_event_capture.md").read_text(encoding="utf-8")
            self.assertEqual(first_report, second_report)

    def test_no_broker_live_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel_path in (
            root / "src" / "backtest" / "continuation_event_schema.py",
            root / "src" / "backtest" / "continuation_lifecycle_identity.py",
            root / "src" / "backtest" / "build_continuation_event_capture_369.py",
            root / "src" / "backtest" / "analysis_structural_breakout_event_capture_369.py",
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
