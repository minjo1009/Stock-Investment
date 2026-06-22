from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_892_repo_source_time_bridge_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_892_repo_source_time_bridge"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain892SourceBridgeTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_accepted_panel_is_empty_but_schema_exists(self) -> None:
        accepted = rows("accepted_source_time_panel.csv")
        self.assertEqual([], accepted)
        header = (ART / "accepted_source_time_panel.csv").read_text(encoding="utf-8").splitlines()[0]
        self.assertIn("available_to_brain_ts", header)

    def test_rejection_ledger_exists(self) -> None:
        rejected = rows("rejected_source_artifact_ledger.csv")
        self.assertGreater(len(rejected), 0)
        self.assertIn("rejection_reason", rejected[0])


if __name__ == "__main__":
    unittest.main()
