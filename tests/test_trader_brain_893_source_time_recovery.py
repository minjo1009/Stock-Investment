from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_893_source_time_recovery_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_893_source_time_recovery"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain893SourceTimeRecoveryTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_recovered_rows_are_internal_event_only(self) -> None:
        recovered = rows("recovered_source_time_panel.csv")
        self.assertGreater(len(recovered), 0)
        authorities = {row["bridge_authority"] for row in recovered}
        gaps = {row["source_gap_flag"] for row in recovered}
        files = {row["source_url_or_file"] for row in recovered}
        self.assertEqual({"diagnostic_recovered_internal_event_only"}, authorities)
        self.assertEqual({"raw_external_document_missing"}, gaps)
        self.assertEqual({"docs/reports/task_372_historical_source_backfill/task_372_historical_source_event_dataset.csv"}, files)

    def test_rejected_rows_keep_derived_events_out(self) -> None:
        rejected = rows("rejected_event_source_rows.csv")
        reasons = {row["rejection_reason"] for row in rejected}
        self.assertIn("derived_or_session_event_not_source_capture", reasons)
        self.assertIn("harness_fixture_not_historical_backtest_evidence", reasons)


if __name__ == "__main__":
    unittest.main()
