from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1181_1190_l0_l3_strengthening_plan_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1181_1190_l0_l3_strengthening_plan"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11811190L0L3StrengtheningPlanTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_sources_and_expert_packets_exist(self) -> None:
        downloads = rows("task1181_download_ledger.csv")
        downloaded = [row for row in downloads if row["download_status"] in {"downloaded", "already_downloaded"}]
        self.assertGreaterEqual(len(downloaded), 15)
        experts = rows("task1183_expert_roster.csv")
        self.assertEqual(14, len(experts))

    def test_current_failure_context_is_recorded(self) -> None:
        context = rows("task1182_project_context_packet.csv")
        self.assertTrue(any("Task1171-1180" in row["current_state"] for row in context))
        self.assertTrue(any("355.68" in row["current_state"] for row in context))

    def test_plan_covers_l0_to_l3_and_next_tasks(self) -> None:
        gaps = rows("task1184_l0_l3_gap_matrix.csv")
        self.assertTrue({"L0", "L1", "L2", "L3"}.issubset({row["layer"] for row in gaps}))
        plan = rows("task1185_l0_l3_strengthening_plan.csv")
        self.assertEqual({f"Task{idx}" for idx in range(1191, 1201)}, {row["task_id"] for row in plan})

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1190_l0_l3_plan_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
