from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1021_1030_l1_l4_institutional_upgrade_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1021_1030_l1_l4_institutional_upgrade"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain10211030L1L4InstitutionalUpgradeTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_catalog_is_broad_and_research_only(self) -> None:
        catalog = rows("task1021_institutional_source_catalog.csv")
        self.assertGreaterEqual(len(catalog), 40)
        self.assertGreaterEqual(sum(1 for row in catalog if row["download_state"].startswith("downloaded")), 30)
        self.assertEqual({"0"}, {row["selection_use_allowed"] for row in catalog})
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in catalog})

    def test_l2_l3_l4_contracts_exist(self) -> None:
        self.assertGreaterEqual(len(rows("task1024_l2_primitive_schema.csv")), 7)
        self.assertGreaterEqual(len(rows("task1025_l3_relation_mechanism_schema.csv")), 8)
        l4_fields = {row["field"] for row in rows("task1026_l4_thesis_card_schema.csv")}
        self.assertIn("exposure_chain", l4_fields)
        self.assertIn("invalidation_path", l4_fields)

    def test_next_tasks_block_replay(self) -> None:
        backlog = rows("task1029_next_task_backlog.csv")
        self.assertEqual(10, len(backlog))
        self.assertEqual({"1"}, {row["blocked_replay_until_done"] for row in backlog})

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task1021_1030_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("0", summary["replay_executed"])
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
