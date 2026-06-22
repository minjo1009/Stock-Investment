from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_multi_event_dataset_366 import main as task_366_main
from src.backtest.build_multi_event_replay_dataset_366 import (
    build_multi_event_replay_dataset,
    write_multi_event_replay_dataset,
)
from src.backtest.continuation_intraday_events import build_continuation_intraday_events
from src.backtest.continuation_lifecycle_replay import run_lifecycle_replay
from src.backtest.continuation_setup_identity import build_setup_identity_frame
from src.backtest.continuation_timeline_builder import build_event_timelines_dataframe
from src.backtest.exposure_evolution_snapshot import build_exposure_evolution_snapshots


class TestMultiEventDataset366(unittest.TestCase):
    def _sample_shadow_log(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "timestamp": "2026-01-03T14:30:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t1",
                    "signal_id": "s1",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.82,
                    "participation_fragility_score": 0.18,
                    "participation_confidence": 0.90,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.22,
                    "factor_exposure_violated": False,
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "PROBE_ONLY",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "NO_CHANGE",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.20,
                    "baseline_realized_R": 0.40,
                    "shadow_realized_R_proxy": 0.08,
                    "quality_aware_realized_R_proxy": 0.10,
                    "healthy_aggressive_realized_R_proxy": 0.08,
                    "day_key": "2026-01-03",
                },
                {
                    "timestamp": "2026-01-03T14:31:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t2",
                    "signal_id": "s2",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.86,
                    "participation_fragility_score": 0.16,
                    "participation_confidence": 0.91,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.18,
                    "factor_exposure_violated": False,
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "quality_aware_policy_stage": "ADD_ALLOWED",
                    "quality_aware_add_allowed": True,
                    "healthy_aggressive_policy_label": "RELAX_SIZE_AND_ADD",
                    "healthy_aggressive_final_add_allowed": True,
                    "healthy_aggressive_final_size_multiplier": 0.60,
                    "baseline_realized_R": 0.70,
                    "shadow_realized_R_proxy": 0.30,
                    "quality_aware_realized_R_proxy": 0.42,
                    "healthy_aggressive_realized_R_proxy": 0.50,
                    "day_key": "2026-01-03",
                },
                {
                    "timestamp": "2026-01-03T14:32:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t3",
                    "signal_id": "s3",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.84,
                    "participation_fragility_score": 0.20,
                    "participation_confidence": 0.90,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.20,
                    "factor_exposure_violated": False,
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "PROBE_ONLY",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "NO_CHANGE",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.60,
                    "baseline_realized_R": 0.20,
                    "shadow_realized_R_proxy": 0.10,
                    "quality_aware_realized_R_proxy": 0.10,
                    "healthy_aggressive_realized_R_proxy": 0.10,
                    "day_key": "2026-01-03",
                },
                {
                    "timestamp": "2026-01-03T14:50:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t4",
                    "signal_id": "s4",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.62,
                    "participation_fragility_score": 0.45,
                    "participation_confidence": 0.87,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.35,
                    "factor_exposure_violated": False,
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "PROBE_ONLY",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "NO_CHANGE",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.20,
                    "baseline_realized_R": -0.20,
                    "shadow_realized_R_proxy": -0.04,
                    "quality_aware_realized_R_proxy": -0.04,
                    "healthy_aggressive_realized_R_proxy": -0.04,
                    "day_key": "2026-01-03",
                },
                {
                    "timestamp": "2026-01-03T15:20:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t5",
                    "signal_id": "s5",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.88,
                    "participation_fragility_score": 0.15,
                    "participation_confidence": 0.93,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.17,
                    "factor_exposure_violated": False,
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "quality_aware_policy_stage": "ADD_ALLOWED",
                    "quality_aware_add_allowed": True,
                    "healthy_aggressive_policy_label": "RELAX_SIZE_AND_ADD",
                    "healthy_aggressive_final_add_allowed": True,
                    "healthy_aggressive_final_size_multiplier": 0.50,
                    "baseline_realized_R": 0.55,
                    "shadow_realized_R_proxy": 0.27,
                    "quality_aware_realized_R_proxy": 0.35,
                    "healthy_aggressive_realized_R_proxy": 0.42,
                    "day_key": "2026-01-03",
                },
                {
                    "timestamp": "2026-01-03T14:35:00Z",
                    "symbol": "AMD",
                    "trade_id": "u1",
                    "signal_id": "su1",
                    "strategy_id": "continuation",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "participation_expansion_score": 0.10,
                    "participation_fragility_score": 0.90,
                    "participation_confidence": 0.95,
                    "state_label": "DISLOCATION",
                    "continuation_risk_score": 0.95,
                    "factor_exposure_violated": False,
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "BLOCK",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.00,
                    "baseline_realized_R": -1.00,
                    "shadow_realized_R_proxy": 0.00,
                    "quality_aware_realized_R_proxy": 0.00,
                    "healthy_aggressive_realized_R_proxy": 0.00,
                    "day_key": "2026-01-03",
                },
            ]
        )

    def _corrected_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "trade_id": "t1",
                    "symbol": "NVDA",
                    "entry_date": "2026-01-03",
                    "entry_ts": "2026-01-03T14:30:00Z",
                    "exit_ts": "2026-01-03T15:00:00Z",
                    "breakout_timestamp": "2026-01-03T14:25:00Z",
                    "realized_R": 0.4,
                },
                {
                    "trade_id": "t2",
                    "symbol": "NVDA",
                    "entry_date": "2026-01-03",
                    "entry_ts": "2026-01-03T14:31:00Z",
                    "exit_ts": "2026-01-03T15:05:00Z",
                    "breakout_timestamp": "2026-01-03T14:26:00Z",
                    "realized_R": 0.7,
                },
                {
                    "trade_id": "t3",
                    "symbol": "NVDA",
                    "entry_date": "2026-01-03",
                    "entry_ts": "2026-01-03T14:32:00Z",
                    "exit_ts": "2026-01-03T15:10:00Z",
                    "breakout_timestamp": "2026-01-03T14:27:00Z",
                    "realized_R": 0.2,
                },
                {
                    "trade_id": "t4",
                    "symbol": "NVDA",
                    "entry_date": "2026-01-03",
                    "entry_ts": "2026-01-03T14:50:00Z",
                    "exit_ts": "2026-01-03T15:12:00Z",
                    "breakout_timestamp": "2026-01-03T14:45:00Z",
                    "realized_R": -0.2,
                },
                {
                    "trade_id": "t5",
                    "symbol": "NVDA",
                    "entry_date": "2026-01-03",
                    "entry_ts": "2026-01-03T15:20:00Z",
                    "exit_ts": "2026-01-03T15:40:00Z",
                    "breakout_timestamp": "2026-01-03T15:15:00Z",
                    "realized_R": 0.55,
                },
            ]
        )

    def _intraday_bars(self) -> pd.DataFrame:
        rows = []
        start = pd.Timestamp("2026-01-03T14:20:00Z")
        for index in range(18):
            bar_start = start + pd.Timedelta(minutes=5 * index)
            rows.append(
                {
                    "symbol": "NVDA",
                    "bar_start_ts": bar_start,
                    "bar_end_ts": bar_start + pd.Timedelta(minutes=5),
                    "open": 100.0 + index,
                    "high": 100.5 + index,
                    "low": 99.5 + index,
                    "close": 100.2 + index,
                    "volume": 1000 + 10 * index,
                    "bar_date": "2026-01-03",
                }
            )
        return pd.DataFrame(rows)

    def _setup_frame(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        shadow_log = self._sample_shadow_log()
        lifecycle_rows_df, replay_trace_df, _tm, _ls = run_lifecycle_replay(shadow_log)
        setup_frame = build_setup_identity_frame(
            shadow_log,
            replay_trace_df,
            lifecycle_rows_df,
            self._corrected_master(),
        )
        return setup_frame, lifecycle_rows_df, replay_trace_df

    def test_setup_identities_deterministic(self) -> None:
        first, _, _ = self._setup_frame()
        second, _, _ = self._setup_frame()
        pd.testing.assert_series_equal(first["setup_id"], second["setup_id"])

    def test_anchor_gap_splits_repeated_setup_ids(self) -> None:
        setup_frame, _, _ = self._setup_frame()
        nvda_ids = setup_frame.loc[setup_frame["symbol"].eq("NVDA"), "setup_id"].tolist()
        self.assertEqual(nvda_ids[:4], ["NVDA|2026-01-03|setup_001"] * 4)
        self.assertEqual(nvda_ids[4], "NVDA|2026-01-03|setup_002")

    def test_unmatched_shadow_rows_retained(self) -> None:
        setup_frame, _, _ = self._setup_frame()
        unmatched = setup_frame[setup_frame["trade_id"].astype(str).eq("u1")].iloc[0]
        self.assertEqual(str(unmatched["setup_type"]), "unmatched_shadow_only")

    def test_intraday_events_assigned_chronologically(self) -> None:
        setup_frame, _, _ = self._setup_frame()
        events_df = build_continuation_intraday_events(setup_frame, self._intraday_bars())
        for continuation_id, group in events_df.groupby("continuation_id"):
            self.assertEqual(
                group.sort_values(["timestamp", "event_index"], kind="stable")["event_index"].tolist(),
                group["event_index"].tolist(),
            )

    def test_invalidation_emitted_for_immediate_dislocation(self) -> None:
        setup_frame, _, _ = self._setup_frame()
        events_df = build_continuation_intraday_events(setup_frame, self._intraday_bars())
        amd_events = events_df[events_df["raw_trade_id"].astype(str).eq("u1")]
        self.assertTrue(amd_events["event_type"].astype(str).eq("INVALIDATION").any())

    def test_add_attempt_and_confirmed_are_distinct(self) -> None:
        setup_frame, _, _ = self._setup_frame()
        events_df = build_continuation_intraday_events(setup_frame, self._intraday_bars())
        t2_events = events_df[events_df["raw_trade_id"].astype(str).eq("t2")]
        self.assertIn("ADD_ATTEMPT", t2_events["event_type"].tolist())
        self.assertIn("ADD_CONFIRMED", t2_events["event_type"].tolist())

    def test_persistence_duration_is_deterministic(self) -> None:
        artifacts = build_multi_event_replay_dataset(
            self._sample_shadow_log(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        timelines_df = artifacts.event_timelines
        self.assertTrue(pd.to_numeric(timelines_df["persistence_duration_minutes"], errors="coerce").fillna(0.0).ge(0.0).all())
        first = build_event_timelines_dataframe(artifacts.multi_event_replay_dataset)
        second = build_event_timelines_dataframe(artifacts.multi_event_replay_dataset)
        pd.testing.assert_frame_equal(first, second)

    def test_exposure_snapshots_increment_only_on_confirmed_adds(self) -> None:
        artifacts = build_multi_event_replay_dataset(
            self._sample_shadow_log(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        exposure_df = artifacts.exposure_evolution
        add_rows = exposure_df[exposure_df["event_type"].astype(str).eq("ADD_CONFIRMED")]
        self.assertTrue(pd.to_numeric(add_rows["cumulative_add_count"], errors="coerce").fillna(0.0).ge(1).all())
        non_add_rows = exposure_df[~exposure_df["event_type"].astype(str).eq("ADD_CONFIRMED")]
        self.assertTrue(pd.to_numeric(non_add_rows["cumulative_add_count"], errors="coerce").fillna(0.0).ge(0).all())

    def test_quality_transitions_tracked_correctly(self) -> None:
        artifacts = build_multi_event_replay_dataset(
            self._sample_shadow_log(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        exposure_df = artifacts.exposure_evolution
        reduction_rows = exposure_df[exposure_df["event_type"].astype(str).eq("REDUCTION_TRIGGER")]
        self.assertTrue(reduction_rows["participation_quality_label"].astype(str).eq("NEUTRAL_PARTICIPATION").any())

    def test_no_future_leakage_in_setup_identity(self) -> None:
        shadow_log = self._sample_shadow_log()
        full_lifecycle_rows_df, full_replay_trace_df, _tm, _ls = run_lifecycle_replay(shadow_log)
        prefix_shadow_log = shadow_log.iloc[:4].copy()
        prefix_lifecycle_rows_df, prefix_replay_trace_df, _tm2, _ls2 = run_lifecycle_replay(prefix_shadow_log)
        full_setup = build_setup_identity_frame(
            shadow_log,
            full_replay_trace_df,
            full_lifecycle_rows_df,
            self._corrected_master(),
        )
        prefix_setup = build_setup_identity_frame(
            prefix_shadow_log,
            prefix_replay_trace_df,
            prefix_lifecycle_rows_df,
            self._corrected_master(),
        )
        full_subset = full_setup[full_setup["trade_id"].astype(str).isin(["t1", "t2", "t3", "t4"])].reset_index(drop=True)
        pd.testing.assert_series_equal(
            full_subset["setup_id"].reset_index(drop=True),
            prefix_setup["setup_id"].reset_index(drop=True),
        )

    def test_dataset_writer_and_report_artifacts_generated(self) -> None:
        artifacts = build_multi_event_replay_dataset(
            self._sample_shadow_log(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            write_multi_event_replay_dataset(artifacts, out_dir)
            expected_csvs = {
                "task_366_multi_event_replay_dataset.csv",
                "task_366_event_timelines.csv",
                "task_366_exposure_evolution.csv",
                "task_366_setup_identity_summary.csv",
                "task_366_intraday_event_summary.csv",
            }
            actual = {path.name for path in out_dir.iterdir()}
            self.assertTrue(expected_csvs.issubset(actual))

        with tempfile.TemporaryDirectory() as td, patch(
            "src.backtest.analysis_structural_breakout_multi_event_dataset_366.build_multi_event_replay_dataset",
            return_value=artifacts,
        ), patch("sys.argv", ["task366", "--out-dir", td]):
            task_366_main()
            self.assertTrue((Path(td) / "task_366_multi_event_dataset.md").exists())

    def test_no_broker_live_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel_path in (
            root / "src" / "backtest" / "continuation_setup_identity.py",
            root / "src" / "backtest" / "continuation_intraday_events.py",
            root / "src" / "backtest" / "continuation_timeline_builder.py",
            root / "src" / "backtest" / "exposure_evolution_snapshot.py",
            root / "src" / "backtest" / "build_multi_event_replay_dataset_366.py",
            root / "src" / "backtest" / "analysis_structural_breakout_multi_event_dataset_366.py",
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
