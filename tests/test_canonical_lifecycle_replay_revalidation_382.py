from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_canonical_lifecycle_replay_revalidation_382 import _write_report
from src.backtest.build_canonical_lifecycle_replay_revalidation_382 import (
    build_canonical_lifecycle_replay_revalidation_382,
    write_canonical_lifecycle_replay_revalidation_382,
)
from src.backtest.canonical_position_lifecycle_event_sourcing import (
    append_canonical_position_event,
    start_canonical_position_lifecycle,
)


class TestCanonicalLifecycleReplayRevalidation382(unittest.TestCase):
    def test_replays_explicit_canonical_lifecycle_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            pd.DataFrame({"trade_id": ["t1"], "symbol": ["NVDA"]}).to_csv(task376_path, index=False)

            start = start_canonical_position_lifecycle(
                str(db_path),
                lifecycle_id="LIFECYCLE|NVDA|2026-05-08|ORD-1",
                symbol="NVDA",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-1",
                size_multiplier=0.5,
            )
            append_canonical_position_event(
                str(db_path),
                lifecycle_id=start.lifecycle_id,
                event_type="ADD",
                event_timestamp="2026-05-08T13:40:00Z",
                size_multiplier=0.8,
            )
            append_canonical_position_event(
                str(db_path),
                lifecycle_id=start.lifecycle_id,
                event_type="SCALE",
                event_timestamp="2026-05-08T14:05:00Z",
                size_multiplier=1.0,
            )

            artifacts = build_canonical_lifecycle_replay_revalidation_382(
                db_path=db_path,
                task376_evaluation_path=task376_path,
            )
            replay = artifacts.canonical_lifecycle_replay_panel
            self.assertEqual(len(replay), 1)
            self.assertEqual(int(replay.iloc[0]["add_event_count"]), 1)
            self.assertEqual(int(replay.iloc[0]["scale_event_count"]), 1)
            self.assertEqual(int(replay.iloc[0]["canonical_sequence_valid_flag"]), 1)
            self.assertEqual(int(replay.iloc[0]["canonical_persistence_quality_flag"]), 1)

    def test_task376_without_explicit_lifecycle_id_is_not_joined_by_symbol_or_date(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            pd.DataFrame(
                {
                    "trade_id": ["looks-same-but-not-explicit"],
                    "symbol": ["AMD"],
                    "entry_ts": ["2026-05-08T13:31:00Z"],
                    "persistence_universe_bucket": ["persistence_core"],
                }
            ).to_csv(task376_path, index=False)

            start_canonical_position_lifecycle(
                str(db_path),
                lifecycle_id="LIFECYCLE|AMD|2026-05-08|ORD-2",
                symbol="AMD",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-2",
            )

            artifacts = build_canonical_lifecycle_replay_revalidation_382(
                db_path=db_path,
                task376_evaluation_path=task376_path,
            )
            readiness = artifacts.canonical_revalidation_readiness_audit.iloc[0]
            decision = artifacts.task_382_decision.iloc[0]
            panel = artifacts.canonical_persistence_revalidation_panel
            self.assertEqual(int(readiness["explicit_join_available_flag"]), 0)
            self.assertEqual(str(readiness["readiness_reason"]), "task376_lacks_explicit_lifecycle_id")
            self.assertEqual(str(panel.iloc[0]["persistence_universe_bucket"]), "unmapped_no_explicit_lifecycle_id")
            self.assertEqual(str(decision["persistence_revalidation_ready"]), "NO_CANONICAL_MAPPING_REQUIRED")
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)

    def test_explicit_lifecycle_id_join_builds_bucket_audit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            lifecycle_id = "LIFECYCLE|MSFT|2026-05-08|ORD-3"
            pd.DataFrame(
                {
                    "lifecycle_id": [lifecycle_id],
                    "trade_id": ["trade-explicit"],
                    "current_split": ["anchored_oos"],
                    "persistence_universe_bucket": ["persistence_core"],
                }
            ).to_csv(task376_path, index=False)

            start = start_canonical_position_lifecycle(
                str(db_path),
                lifecycle_id=lifecycle_id,
                symbol="MSFT",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-3",
            )
            append_canonical_position_event(
                str(db_path),
                lifecycle_id=start.lifecycle_id,
                event_type="ADD",
                event_timestamp="2026-05-08T13:45:00Z",
            )

            artifacts = build_canonical_lifecycle_replay_revalidation_382(
                db_path=db_path,
                task376_evaluation_path=task376_path,
            )
            readiness = artifacts.canonical_revalidation_readiness_audit.iloc[0]
            decision = artifacts.task_382_decision.iloc[0]
            audit = artifacts.canonical_persistence_bucket_audit
            self.assertEqual(int(readiness["explicit_join_available_flag"]), 1)
            self.assertEqual(int(readiness["joined_lifecycle_count"]), 1)
            self.assertEqual(str(decision["persistence_revalidation_ready"]), "YES_CANONICAL_EXPLICIT_LAYER_ONLY")
            self.assertEqual(str(audit.iloc[0]["persistence_universe_bucket"]), "persistence_core")
            self.assertEqual(float(audit.iloc[0]["canonical_quality_rate"]), 1.0)

    def test_report_and_csv_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            task376_path = Path(td) / "task376.csv"
            out_dir = Path(td) / "out"
            pd.DataFrame({"trade_id": ["t1"], "symbol": ["AAPL"]}).to_csv(task376_path, index=False)
            start_canonical_position_lifecycle(
                str(db_path),
                lifecycle_id="LIFECYCLE|AAPL|2026-05-08|ORD-4",
                symbol="AAPL",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-4",
            )

            artifacts = build_canonical_lifecycle_replay_revalidation_382(
                db_path=db_path,
                task376_evaluation_path=task376_path,
            )
            write_canonical_lifecycle_replay_revalidation_382(artifacts, out_dir)
            _write_report(out_dir, artifacts)

            expected = [
                "canonical_lifecycle_event_stream.csv",
                "canonical_lifecycle_replay_panel.csv",
                "canonical_persistence_revalidation_panel.csv",
                "canonical_persistence_bucket_audit.csv",
                "canonical_revalidation_readiness_audit.csv",
                "task_382_decision.csv",
                "task_382_canonical_lifecycle_replay_revalidation.md",
            ]
            for name in expected:
                self.assertTrue((out_dir / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
