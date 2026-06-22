from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1141_1150_external_source_acquisition_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1141_1150_external_source_acquisition"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11411150ExternalSourceAcquisitionTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_official_sources_were_actually_downloaded(self) -> None:
        catalog = rows("task1141_external_source_catalog.csv")
        downloaded = [row for row in catalog if row["download_status"] == "downloaded"]
        self.assertGreaterEqual(len(downloaded), 3)
        self.assertTrue(all(row["source_hash"] for row in downloaded))

    def test_sec_source_time_improved_but_pit_not_solved(self) -> None:
        submissions = rows("task1143_sec_submission_download_panel.csv")
        self.assertEqual(70, len(submissions))
        accepted_rows = sum(int(row["accepted_datetime_rows_2021_2026q1"]) for row in submissions)
        self.assertGreater(accepted_rows, 100)
        pit = rows("task1147_pit_universe_resolution_matrix.csv")
        self.assertEqual({"0"}, {row["pit_membership_pass"] for row in pit})
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in pit})

    def test_policy_archives_do_not_unlock_replay(self) -> None:
        fr = rows("task1145_federal_register_policy_archive_panel.csv")
        self.assertEqual(10, len(fr))
        self.assertGreater(sum(int(row["result_count"]) for row in fr), 0)
        self.assertEqual({"0"}, {row["dynamic_replay_use_allowed"] for row in fr})

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1150_external_source_acquisition_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual(0, closeout["pit_membership_pass_rows"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
