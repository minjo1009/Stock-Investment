from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task401_exact_label_generation_404 import build_task401_exact_label_generation_404


class TestTask401ExactLabelGeneration404(unittest.TestCase):
    def test_exact_lifecycle_labels_and_non_lifecycle_candidates_are_separated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidates = root / "candidates.csv"
            events = root / "events.csv"
            pd.DataFrame(
                [
                    _candidate("D1", "L1", "ALLOW"),
                    _candidate("D2", "L2", "ALLOW"),
                    _candidate("D3", "", "WATCH"),
                    _candidate("D4", "", "REJECT"),
                ]
            ).to_csv(candidates, index=False, encoding="utf-8-sig")
            pd.DataFrame(
                [
                    _event("L1", "ENTRY", "2026-01-01T15:00:00Z", 100.0),
                    _event("L1", "ADD", "2026-01-01T15:15:00Z", 101.0),
                    _event("L1", "SCALE", "2026-01-01T15:30:00Z", 102.0),
                    _event("L1", "EXIT", "2026-01-01T16:00:00Z", 103.0),
                    _event("L2", "ENTRY", "2026-01-01T15:00:00Z", 100.0),
                ]
            ).to_csv(events, index=False, encoding="utf-8-sig")

            artifacts = build_task401_exact_label_generation_404(
                task401_entry_candidates_path=candidates,
                task401_event_log_path=events,
                out_dir=root / "out",
            )

            labels = artifacts.task401_exact_lifecycle_labels
            self.assertEqual(labels[labels["lifecycle_id"].eq("L1")]["lifecycle_outcome_class"].iloc[0], "add_scale_success")
            self.assertEqual(labels[labels["lifecycle_id"].eq("L2")]["lifecycle_outcome_class"].iloc[0], "unlabeled_open_or_incomplete")
            coverage = artifacts.task401_label_coverage_audit
            watch = coverage[coverage["bucket"].eq("WATCH")].iloc[0]
            self.assertEqual(int(watch["non_lifecycle_candidate_count"]), 1)
            self.assertEqual(int(coverage["unlabeled_treated_as_negative_flag"].max()), 0)
            self.assertEqual(int(coverage["symbol_date_price_time_fallback_used_flag"].max()), 0)
            self.assertTrue((root / "out" / "task_404_task401_exact_label_generation.md").exists())


def _candidate(decision_id: str, lifecycle_id: str, bucket: str) -> dict:
    return {
        "decision_id": decision_id,
        "lifecycle_id": lifecycle_id,
        "bucket": bucket,
        "symbol": "AAA",
        "decision_ts_utc": "2026-01-01T15:00:00Z",
    }


def _event(lifecycle_id: str, event_type: str, ts: str, price: float) -> dict:
    return {
        "lifecycle_id": lifecycle_id,
        "symbol": "AAA",
        "event_type": event_type,
        "event_timestamp": ts,
        "price": price,
        "size_multiplier": 1.0,
        "decision_id": "D1" if event_type == "ENTRY" else "",
    }


if __name__ == "__main__":
    unittest.main()
