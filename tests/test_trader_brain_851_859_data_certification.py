from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_851_859_data_certification_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data/artifacts/task_850_859_data_certification"


def rows(name: str) -> list[dict[str, str]]:
    with (ARTIFACT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain851859DataCertificationTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_gate_remains_no_replay(self) -> None:
        decisions = rows("certification_decision.csv")
        self.assertTrue(
            any(
                row["decision_area"] == "market_data_gate_handoff"
                and row["status"] == "MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY"
                for row in decisions
            )
        )

    def test_intraday_mixed_schema_detected(self) -> None:
        schemas = rows("schema_fingerprint_inventory.csv")
        intraday = [row for row in schemas if row["dataset_id"] == "us_intraday"]
        self.assertGreaterEqual(len(intraday), 2)
        self.assertTrue(any(row["certification_status"] == "blocked_mixed_schema" for row in intraday))

    def test_no_full_certification_claim(self) -> None:
        manifest = rows("canonical_data_manifest.csv")
        forbidden = {"certified", "certified_for_controlled_replay"}
        self.assertFalse(any(row["certification_status"] in forbidden for row in manifest))


if __name__ == "__main__":
    unittest.main()
