from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_canonical_continuation_quality_386 import _write_report
from src.backtest.build_canonical_continuation_quality_386 import (
    build_canonical_continuation_quality_386,
    write_canonical_continuation_quality_386,
)


class TestCanonicalContinuationQuality386(unittest.TestCase):
    def test_builds_path_transition_and_bucket_quality_from_canonical_stream_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            event_log = root / "events.csv"
            summary = root / "summary.csv"
            replay = root / "replay.csv"
            revalidation = root / "revalidation.csv"
            _write_fixture(event_log, summary, replay, revalidation)

            artifacts = build_canonical_continuation_quality_386(
                event_log_path=event_log,
                lifecycle_summary_path=summary,
                replay_panel_path=replay,
                revalidation_panel_path=revalidation,
            )
            decision = artifacts.task_386_decision.iloc[0]
            paths = set(artifacts.canonical_path_quality_audit["path_type"].astype(str))
            transitions = set(artifacts.canonical_transition_quality_audit["transition"].astype(str))
            bucket = artifacts.canonical_bucket_quality_audit

            self.assertEqual(str(decision["task_386_verdict"]), "COMPLETE_PASS")
            self.assertEqual(int(decision["add_scale_quality_measurable_flag"]), 1)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertIn("ENTRY_ADD_SCALE_EXIT", paths)
            self.assertIn("ENTRY_REDUCE_EXIT", paths)
            self.assertIn("ENTRY->ADD", transitions)
            self.assertIn("REDUCE->EXIT", transitions)
            core = bucket[bucket["persistence_universe_bucket"].astype(str).eq("persistence_core")].iloc[0]
            self.assertEqual(int(core["lifecycle_count"]), 1)
            self.assertGreater(float(core["avg_return"]), 0.0)

    def test_report_and_csv_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = root / "out"
            event_log = root / "events.csv"
            summary = root / "summary.csv"
            replay = root / "replay.csv"
            revalidation = root / "revalidation.csv"
            _write_fixture(event_log, summary, replay, revalidation)
            artifacts = build_canonical_continuation_quality_386(
                event_log_path=event_log,
                lifecycle_summary_path=summary,
                replay_panel_path=replay,
                revalidation_panel_path=revalidation,
            )
            write_canonical_continuation_quality_386(artifacts, out)
            _write_report(out, artifacts)
            expected = [
                "canonical_lifecycle_quality_panel.csv",
                "canonical_path_quality_audit.csv",
                "canonical_transition_quality_audit.csv",
                "canonical_bucket_quality_audit.csv",
                "canonical_quality_boundary_audit.csv",
                "task_386_decision.csv",
                "task_386_canonical_continuation_quality.md",
            ]
            for name in expected:
                self.assertTrue((out / name).exists(), name)


def _write_fixture(event_log: Path, summary: Path, replay: Path, revalidation: Path) -> None:
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "symbol": "AMD", "event_type": "ENTRY", "event_timestamp": "2026-01-01T14:30:00Z", "price": 100, "size_multiplier": 0.5},
            {"lifecycle_id": "L1", "symbol": "AMD", "event_type": "ADD", "event_timestamp": "2026-01-02T14:30:00Z", "price": 104, "size_multiplier": 0.75},
            {"lifecycle_id": "L1", "symbol": "AMD", "event_type": "SCALE", "event_timestamp": "2026-01-03T14:30:00Z", "price": 108, "size_multiplier": 1.0},
            {"lifecycle_id": "L1", "symbol": "AMD", "event_type": "EXIT", "event_timestamp": "2026-01-04T14:30:00Z", "price": 110, "size_multiplier": 0.0},
            {"lifecycle_id": "L2", "symbol": "NVDA", "event_type": "ENTRY", "event_timestamp": "2026-01-01T14:30:00Z", "price": 100, "size_multiplier": 0.5},
            {"lifecycle_id": "L2", "symbol": "NVDA", "event_type": "REDUCE", "event_timestamp": "2026-01-02T14:30:00Z", "price": 96, "size_multiplier": 0.5},
            {"lifecycle_id": "L2", "symbol": "NVDA", "event_type": "EXIT", "event_timestamp": "2026-01-03T14:30:00Z", "price": 94, "size_multiplier": 0.0},
        ]
    ).to_csv(event_log, index=False)
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "symbol": "AMD", "entry_ts": "2026-01-01T14:30:00Z", "exit_ts": "2026-01-04T14:30:00Z", "bars_held": 3, "add_flag": 1, "scale_flag": 1, "reduce_flag": 0, "exit_reason": "time_exit", "return_from_entry": 0.10},
            {"lifecycle_id": "L2", "symbol": "NVDA", "entry_ts": "2026-01-01T14:30:00Z", "exit_ts": "2026-01-03T14:30:00Z", "bars_held": 2, "add_flag": 0, "scale_flag": 0, "reduce_flag": 1, "exit_reason": "drawdown_exit", "return_from_entry": -0.06},
        ]
    ).to_csv(summary, index=False)
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "event_count": 4, "add_event_count": 1, "scale_event_count": 1, "reduce_event_count": 0, "exit_event_count": 1, "canonical_sequence_valid_flag": 1, "canonical_persistence_quality_flag": 1, "continuation_duration_minutes": 4320},
            {"lifecycle_id": "L2", "event_count": 3, "add_event_count": 0, "scale_event_count": 0, "reduce_event_count": 1, "exit_event_count": 1, "canonical_sequence_valid_flag": 1, "canonical_persistence_quality_flag": 0, "continuation_duration_minutes": 2880},
        ]
    ).to_csv(replay, index=False)
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "persistence_universe_bucket": "persistence_core", "current_split": "test"},
            {"lifecycle_id": "L2", "persistence_universe_bucket": "suppressed_crowding_risk", "current_split": "test"},
        ]
    ).to_csv(revalidation, index=False)


if __name__ == "__main__":
    unittest.main()
