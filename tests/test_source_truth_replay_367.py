from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_source_truth_replay_367 import main as task_367_main
from src.backtest.build_multi_event_replay_dataset_366 import MultiEventReplayDatasetArtifacts
from src.backtest.build_source_truth_replay_dataset_367 import (
    build_source_truth_replay_dataset,
    write_source_truth_replay_dataset,
)
from src.backtest.continuation_event_lineage import build_continuation_event_lineage
from src.backtest.source_truth_continuation_identity import build_source_truth_continuation_identity


class TestSourceTruthReplay367(unittest.TestCase):
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
                    "breakout_timestamp": None,
                    "entry_ts": "2026-01-03T15:00:00Z",
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
                    "breakout_timestamp": None,
                    "entry_ts": None,
                },
                {
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "trade_id": "m1",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "setup_session_date": "2026-01-03",
                    "setup_type": "breakout_timestamp",
                    "intraday_match_status": "matched_session_bars",
                    "master_match": True,
                    "breakout_timestamp": "2026-01-03T13:55:00Z",
                    "entry_ts": "2026-01-03T14:00:00Z",
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
                    "intraday_match_status": "missing_intraday_session",
                },
                {
                    "continuation_id": "AMD|2026-01-03|setup_001|cont_001",
                    "setup_id": "AMD|2026-01-03|setup_001",
                    "event_id": "e9",
                    "event_index": 1,
                    "event_type": "INVALIDATION",
                    "timestamp": "2026-01-03T14:35:00Z",
                    "raw_trade_id": "u1",
                    "raw_signal_id": "su1",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "transition_reason": "dislocation_exit",
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e10",
                    "event_index": 1,
                    "event_type": "SETUP",
                    "timestamp": "2026-01-03T14:00:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "transition_reason": "",
                },
                {
                    "continuation_id": "MSFT|2026-01-03|setup_001|cont_001",
                    "setup_id": "MSFT|2026-01-03|setup_001",
                    "event_id": "e11",
                    "event_index": 2,
                    "event_type": "EXIT_TRIGGER",
                    "timestamp": "2026-01-03T14:45:00Z",
                    "raw_trade_id": "m1",
                    "raw_signal_id": "sm1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "transition_reason": "dislocation_exit",
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
                {"symbol": "MSFT", "bar_date": "2026-01-03", "bar_start_ts": "2026-01-03T14:00:00Z", "bar_end_ts": "2026-01-03T14:05:00Z"},
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

    def test_continuation_identities_deterministic(self) -> None:
        args = (
            self._multi_event_dataset(),
            self._setup_frame(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        first_row, first_cont = build_source_truth_continuation_identity(*args)
        second_row, second_cont = build_source_truth_continuation_identity(*args)
        pd.testing.assert_frame_equal(first_row, second_row)
        pd.testing.assert_frame_equal(first_cont, second_cont)

    def test_lineage_ordering_preserved(self) -> None:
        row_identity_df, continuation_identity_df = build_source_truth_continuation_identity(
            self._multi_event_dataset(),
            self._setup_frame(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        lineage_row_df, _cont_df, _depth_df, _fidelity_df = build_continuation_event_lineage(
            self._multi_event_dataset(),
            row_identity_df,
            continuation_identity_df,
        )
        for _, group in lineage_row_df.groupby("continuation_id"):
            ordered_ids = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable")["event_id"].tolist()
            self.assertEqual(ordered_ids, group["event_id"].tolist())

    def test_source_linked_continuation_recognized(self) -> None:
        row_identity_df, continuation_identity_df = build_source_truth_continuation_identity(
            self._multi_event_dataset(),
            self._setup_frame(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        source_row = row_identity_df[row_identity_df["continuation_id"].astype(str).eq("NVDA|2026-01-03|setup_001|cont_001")]
        self.assertTrue(source_row["source_linked_flag"].all())
        source_cont = continuation_identity_df[continuation_identity_df["continuation_id"].astype(str).eq("NVDA|2026-01-03|setup_001|cont_001")].iloc[0]
        self.assertEqual(str(source_cont["linkage_source"]), "trade_id_master_match")

    def test_replay_only_continuation_is_synthetic_only(self) -> None:
        row_identity_df, continuation_identity_df = build_source_truth_continuation_identity(
            self._multi_event_dataset(),
            self._setup_frame(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        lineage_row_df, continuation_lineage_df, _depth_df, _fidelity_df = build_continuation_event_lineage(
            self._multi_event_dataset(),
            row_identity_df,
            continuation_identity_df,
        )
        amd = continuation_lineage_df[continuation_lineage_df["continuation_id"].astype(str).eq("AMD|2026-01-03|setup_001|cont_001")].iloc[0]
        self.assertEqual(str(amd["lineage_quality"]), "synthetic_only")
        self.assertEqual(str(amd["lineage_break_reason"]), "missing_master_match")

    def test_lineage_confidence_follows_priority(self) -> None:
        row_identity_df, _continuation_identity_df = build_source_truth_continuation_identity(
            self._multi_event_dataset(),
            self._setup_frame(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        mapping = dict(zip(row_identity_df["event_id"], row_identity_df["lineage_confidence"]))
        self.assertEqual(mapping["e1"], 1.0)
        self.assertEqual(mapping["e6"], 1.0)
        self.assertEqual(mapping["e9"], 0.1)

    def test_lineage_break_reason_is_deterministic(self) -> None:
        dataset = self._multi_event_dataset().copy()
        row_identity_df, continuation_identity_df = build_source_truth_continuation_identity(
            dataset,
            self._setup_frame(),
            self._corrected_master(),
            self._intraday_bars(),
        )
        lineage_row_df, continuation_lineage_df, _depth_df, _fidelity_df = build_continuation_event_lineage(
            dataset,
            row_identity_df,
            continuation_identity_df,
        )
        mixed = continuation_lineage_df[continuation_lineage_df["continuation_id"].astype(str).eq("NVDA|2026-01-03|setup_002|cont_001")].iloc[0]
        terminal = continuation_lineage_df[continuation_lineage_df["continuation_id"].astype(str).eq("MSFT|2026-01-03|setup_001|cont_001")].iloc[0]
        self.assertEqual(str(mixed["lineage_break_reason"]), "missing_intraday_session")
        self.assertEqual(str(terminal["lineage_break_reason"]), "terminal_replay_break")
        self.assertTrue(lineage_row_df["lineage_break_reason"].notna().all())

    def test_replay_fidelity_metrics_deterministic(self) -> None:
        artifacts = build_source_truth_replay_dataset(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        metric_map = dict(zip(artifacts.replay_fidelity["metric_name"], artifacts.replay_fidelity["metric_value"]))
        self.assertIn("source_linked_continuation_share", metric_map)
        self.assertIn("replay_fidelity_score", metric_map)
        self.assertGreaterEqual(float(metric_map["replay_fidelity_score"]), 0.0)

    def test_no_future_leakage(self) -> None:
        full_dataset = self._multi_event_dataset()
        prefix_dataset = full_dataset[full_dataset["event_index"].astype(int) <= 2].copy()
        args = (self._setup_frame(), self._corrected_master(), self._intraday_bars())
        full_row, _ = build_source_truth_continuation_identity(full_dataset, *args)
        prefix_row, _ = build_source_truth_continuation_identity(prefix_dataset, *args)
        full_prefix = full_row[full_row["event_id"].astype(str).isin(prefix_row["event_id"].astype(str))].reset_index(drop=True)
        pd.testing.assert_series_equal(full_prefix["linkage_source"], prefix_row["linkage_source"], check_names=False)
        pd.testing.assert_series_equal(full_prefix["lineage_confidence"], prefix_row["lineage_confidence"], check_names=False)

    def test_report_artifacts_generated(self) -> None:
        artifacts = build_source_truth_replay_dataset(
            multi_event_artifacts=self._artifacts_366(),
            corrected_master_df=self._corrected_master(),
            intraday_bars_df=self._intraday_bars(),
        )
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            write_source_truth_replay_dataset(artifacts, out_dir)
            expected = {
                "task_367_source_truth_replay_dataset.csv",
                "task_367_event_lineage.csv",
                "task_367_continuation_depth.csv",
                "task_367_replay_fidelity.csv",
            }
            self.assertTrue(expected.issubset({path.name for path in out_dir.iterdir()}))

        with tempfile.TemporaryDirectory() as td, patch(
            "src.backtest.analysis_structural_breakout_source_truth_replay_367.build_source_truth_replay_dataset",
            return_value=artifacts,
        ), patch("sys.argv", ["task367", "--out-dir", td]):
            task_367_main()
            self.assertTrue((Path(td) / "task_367_source_truth_replay.md").exists())

    def test_no_broker_live_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel_path in (
            root / "src" / "backtest" / "source_truth_continuation_identity.py",
            root / "src" / "backtest" / "continuation_event_lineage.py",
            root / "src" / "backtest" / "build_source_truth_replay_dataset_367.py",
            root / "src" / "backtest" / "analysis_structural_breakout_source_truth_replay_367.py",
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
