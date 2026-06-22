from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_891_as_is_to_be_gap_diagnosis_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_891_as_is_to_be_gap_diagnosis"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain891GapDiagnosisTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_gap_matrix_keeps_source_time_not_ready(self) -> None:
        gap = rows("as_is_to_be_gap_matrix.csv")
        source_gap = [row for row in gap if row["area"] == "historical_source_time_panel"][0]
        self.assertEqual("not_ready", source_gap["status"])

    def test_inventory_has_source_candidates(self) -> None:
        inventory = rows("repo_source_evidence_inventory.csv")
        self.assertGreater(len(inventory), 0)
        self.assertTrue(any("source" in row["relative_path"].lower() or "evidence" in row["relative_path"].lower() for row in inventory))

    def test_backlog_names_task883_first(self) -> None:
        backlog = rows("to_be_requirement_backlog.csv")
        self.assertEqual("1", backlog[0]["priority"])
        self.assertIn("Task883", backlog[0]["requirement"])


if __name__ == "__main__":
    unittest.main()
