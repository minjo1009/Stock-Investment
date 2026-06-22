from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_canonical_lifecycle_stream_accumulation_384 import _write_report
from src.backtest.build_canonical_lifecycle_replay_revalidation_382 import (
    build_canonical_lifecycle_replay_revalidation_382,
)
from src.backtest.build_canonical_lifecycle_stream_accumulation_384 import (
    build_canonical_lifecycle_stream_accumulation_384,
    write_canonical_lifecycle_stream_accumulation_384,
)


class TestCanonicalLifecycleStreamAccumulation384(unittest.TestCase):
    def test_accumulates_entry_add_scale_and_entry_reduce_exit_lifecycles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            source_path = Path(td) / "source.csv"
            task376_path = Path(td) / "task376.csv"
            _write_source_events(source_path)
            _write_task376(task376_path)

            artifacts = build_canonical_lifecycle_stream_accumulation_384(
                db_path=db_path,
                source_events_path=source_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            success = artifacts.canonical_accumulation_success_audit.iloc[0]
            decision = artifacts.task_384_decision.iloc[0]
            lifecycle = artifacts.canonical_accumulation_lifecycle_panel

            self.assertEqual(int(success["canonical_event_count"]), 6)
            self.assertEqual(int(success["canonical_lifecycle_count"]), 2)
            self.assertEqual(int(success["has_entry_add_or_scale_lifecycle_flag"]), 1)
            self.assertEqual(int(success["has_entry_reduce_exit_lifecycle_flag"]), 1)
            self.assertEqual(str(decision["task382_canonical_stream_only_ready"]), "YES")
            self.assertEqual(set(lifecycle["sequence_status"].astype(str)), {"valid"})

    def test_rejects_post_entry_event_without_explicit_lifecycle_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            source_path = Path(td) / "source.csv"
            task376_path = Path(td) / "task376.csv"
            pd.DataFrame(
                [
                    {
                        "lifecycle_id": "LIFECYCLE|AMD|2026-05-08|ORD-1",
                        "event_type": "ENTRY",
                        "symbol": "AMD",
                        "event_timestamp": "2026-05-08T13:31:00Z",
                    },
                    {
                        "lifecycle_id": "",
                        "event_type": "ADD",
                        "symbol": "AMD",
                        "event_timestamp": "2026-05-08T13:40:00Z",
                    },
                ]
            ).to_csv(source_path, index=False)
            _write_task376(task376_path)

            artifacts = build_canonical_lifecycle_stream_accumulation_384(
                db_path=db_path,
                source_events_path=source_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            audit = artifacts.canonical_accumulation_event_audit
            success = artifacts.canonical_accumulation_success_audit.iloc[0]
            self.assertEqual(int(success["canonical_event_count"]), 1)
            self.assertTrue(audit["rejection_reason"].astype(str).str.contains("post-entry canonical event requires explicit lifecycle_id").any())
            self.assertEqual(int(success["symbol_session_inference_used_flag"]), 0)

    def test_task382_can_replay_accumulated_stream_in_canonical_only_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            source_path = Path(td) / "source.csv"
            task376_path = Path(td) / "task376.csv"
            _write_source_events(source_path)
            _write_task376(task376_path)

            build_canonical_lifecycle_stream_accumulation_384(
                db_path=db_path,
                source_events_path=source_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            replay = build_canonical_lifecycle_replay_revalidation_382(
                db_path=db_path,
                task376_evaluation_path=task376_path,
            )
            decision = replay.task_382_decision.iloc[0]
            bucket_audit = replay.canonical_persistence_bucket_audit
            self.assertEqual(str(decision["persistence_revalidation_ready"]), "YES_CANONICAL_EXPLICIT_LAYER_ONLY")
            self.assertEqual(int(decision["joined_task376_lifecycle_count"]), 2)
            self.assertIn("persistence_core", set(bucket_audit["persistence_universe_bucket"].astype(str)))

    def test_report_and_csv_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            source_path = Path(td) / "source.csv"
            task376_path = Path(td) / "task376.csv"
            out_dir = Path(td) / "out"
            _write_source_events(source_path)
            _write_task376(task376_path)

            artifacts = build_canonical_lifecycle_stream_accumulation_384(
                db_path=db_path,
                source_events_path=source_path,
                task376_prediction_path=task376_path,
                task376_evaluation_path=task376_path,
            )
            write_canonical_lifecycle_stream_accumulation_384(artifacts, out_dir)
            _write_report(out_dir, artifacts)
            expected = [
                "canonical_accumulation_source_events.csv",
                "canonical_accumulation_event_audit.csv",
                "canonical_accumulation_event_stream.csv",
                "canonical_accumulation_lifecycle_panel.csv",
                "canonical_accumulation_success_audit.csv",
                "task376_canonical_capture_mapping_audit.csv",
                "task_384_decision.csv",
                "task_384_canonical_lifecycle_stream_accumulation.md",
            ]
            for name in expected:
                self.assertTrue((out_dir / name).exists(), name)


def _write_source_events(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "lifecycle_id": "LIFECYCLE|AMD|2026-05-08|ORD-1",
                "event_type": "ENTRY",
                "symbol": "AMD",
                "event_timestamp": "2026-05-08T13:31:00Z",
                "order_id": "ORD-1",
                "trade_run_id": "run-1",
                "quantity": 10,
                "price": 164.0,
                "size_multiplier": 0.5,
            },
            {
                "lifecycle_id": "LIFECYCLE|AMD|2026-05-08|ORD-1",
                "event_type": "ADD",
                "symbol": "AMD",
                "event_timestamp": "2026-05-08T13:40:00Z",
                "order_id": "ORD-2",
                "trade_run_id": "run-1",
                "quantity": 5,
                "price": 166.0,
                "size_multiplier": 0.8,
            },
            {
                "lifecycle_id": "LIFECYCLE|AMD|2026-05-08|ORD-1",
                "event_type": "SCALE",
                "symbol": "AMD",
                "event_timestamp": "2026-05-08T13:55:00Z",
                "order_id": "ORD-3",
                "trade_run_id": "run-1",
                "quantity": 5,
                "price": 170.0,
                "size_multiplier": 1.0,
            },
            {
                "lifecycle_id": "LIFECYCLE|NVDA|2026-05-08|ORD-4",
                "event_type": "ENTRY",
                "symbol": "NVDA",
                "event_timestamp": "2026-05-08T14:00:00Z",
                "order_id": "ORD-4",
                "trade_run_id": "run-2",
                "quantity": 2,
                "price": 910.0,
                "size_multiplier": 0.5,
            },
            {
                "lifecycle_id": "LIFECYCLE|NVDA|2026-05-08|ORD-4",
                "event_type": "REDUCE",
                "symbol": "NVDA",
                "event_timestamp": "2026-05-08T14:20:00Z",
                "order_id": "ORD-5",
                "trade_run_id": "run-2",
                "quantity": -1,
                "price": 905.0,
                "size_multiplier": 0.25,
            },
            {
                "lifecycle_id": "LIFECYCLE|NVDA|2026-05-08|ORD-4",
                "event_type": "EXIT",
                "symbol": "NVDA",
                "event_timestamp": "2026-05-08T14:45:00Z",
                "order_id": "ORD-6",
                "trade_run_id": "run-2",
                "quantity": -1,
                "price": 900.0,
                "size_multiplier": 0.0,
            },
        ]
    ).to_csv(path, index=False)


def _write_task376(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "trade_id": "trade-amd",
                "lifecycle_id": "LIFECYCLE|AMD|2026-05-08|ORD-1",
                "current_split": "anchored_oos",
                "persistence_universe_bucket": "persistence_core",
                "entry_ts": "2026-05-08T13:31:00Z",
            },
            {
                "trade_id": "trade-nvda",
                "lifecycle_id": "LIFECYCLE|NVDA|2026-05-08|ORD-4",
                "current_split": "anchored_oos",
                "persistence_universe_bucket": "suppressed_crowding_risk",
                "entry_ts": "2026-05-08T14:00:00Z",
            },
        ]
    ).to_csv(path, index=False)


if __name__ == "__main__":
    unittest.main()
