from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_canonical_continuation_oos_overlay_387 import _write_report
from src.backtest.build_canonical_continuation_oos_overlay_387 import (
    build_canonical_continuation_oos_overlay_387,
    write_canonical_continuation_oos_overlay_387,
)


class TestCanonicalContinuationOosOverlay387(unittest.TestCase):
    def test_oos_split_path_quality_and_transition_anomaly_audit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            quality = root / "quality.csv"
            events = root / "events.csv"
            _write_fixture(quality, events)

            artifacts = build_canonical_continuation_oos_overlay_387(
                quality_panel_path=quality,
                event_log_path=events,
                anchor_date="2025-01-01",
            )
            decision = artifacts.task_387_decision.iloc[0]
            oos_paths = artifacts.canonical_oos_path_quality_audit
            anomaly = artifacts.canonical_sequence_anomaly_audit

            self.assertEqual(str(decision["task_387_verdict"]), "COMPLETE_PASS")
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertEqual(int(decision["anchored_oos_lifecycle_count"]), 2)
            self.assertIn("anchored_oos", set(oos_paths["canonical_split"].astype(str)))
            self.assertTrue(anomaly["anomaly_type"].astype(str).eq("transition_after_exit").any())
            self.assertGreaterEqual(int(decision["sequence_anomaly_count"]), 1)

    def test_report_and_csv_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            quality = root / "quality.csv"
            events = root / "events.csv"
            out = root / "out"
            _write_fixture(quality, events)
            artifacts = build_canonical_continuation_oos_overlay_387(
                quality_panel_path=quality,
                event_log_path=events,
                anchor_date="2025-01-01",
            )
            write_canonical_continuation_oos_overlay_387(artifacts, out)
            _write_report(out, artifacts)
            expected = [
                "canonical_oos_quality_panel.csv",
                "canonical_oos_path_quality_audit.csv",
                "canonical_oos_transition_quality_audit.csv",
                "canonical_oos_bucket_overlay_audit.csv",
                "canonical_oos_sample_adequacy_audit.csv",
                "canonical_sequence_anomaly_audit.csv",
                "task_387_decision.csv",
                "task_387_canonical_continuation_oos_overlay.md",
            ]
            for name in expected:
                self.assertTrue((out / name).exists(), name)


def _write_fixture(quality: Path, events: Path) -> None:
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "entry_ts": "2024-01-01T14:30:00Z", "path_type": "ENTRY_ADD_SCALE_EXIT", "return_from_entry": 0.10, "positive_return_flag": 1, "strong_return_flag": 1, "loss_flag": 0, "add_event_count": 1, "scale_event_count": 1, "reduce_event_count": 0, "persistence_universe_bucket": "persistence_core"},
            {"lifecycle_id": "L2", "entry_ts": "2025-02-01T14:30:00Z", "path_type": "ENTRY_ADD_SCALE_EXIT", "return_from_entry": 0.08, "positive_return_flag": 1, "strong_return_flag": 1, "loss_flag": 0, "add_event_count": 1, "scale_event_count": 1, "reduce_event_count": 0, "persistence_universe_bucket": "persistence_core"},
            {"lifecycle_id": "L3", "entry_ts": "2025-03-01T14:30:00Z", "path_type": "ENTRY_REDUCE_EXIT", "return_from_entry": -0.05, "positive_return_flag": 0, "strong_return_flag": 0, "loss_flag": 1, "add_event_count": 0, "scale_event_count": 0, "reduce_event_count": 1, "persistence_universe_bucket": "suppressed_crowding_risk"},
        ]
    ).to_csv(quality, index=False)
    pd.DataFrame(
        [
            {"lifecycle_id": "L2", "event_type": "ENTRY", "event_timestamp": "2025-02-01T14:30:00Z"},
            {"lifecycle_id": "L2", "event_type": "ADD", "event_timestamp": "2025-02-02T14:30:00Z"},
            {"lifecycle_id": "L2", "event_type": "SCALE", "event_timestamp": "2025-02-03T14:30:00Z"},
            {"lifecycle_id": "L2", "event_type": "EXIT", "event_timestamp": "2025-02-04T14:30:00Z"},
            {"lifecycle_id": "L3", "event_type": "ENTRY", "event_timestamp": "2025-03-01T14:30:00Z"},
            {"lifecycle_id": "L3", "event_type": "EXIT", "event_timestamp": "2025-03-02T14:30:00Z"},
            {"lifecycle_id": "L3", "event_type": "REDUCE", "event_timestamp": "2025-03-03T14:30:00Z"},
        ]
    ).to_csv(events, index=False)


if __name__ == "__main__":
    unittest.main()
