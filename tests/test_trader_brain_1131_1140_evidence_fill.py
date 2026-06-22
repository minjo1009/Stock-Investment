from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1131_1140_evidence_fill_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1131_1140_evidence_fill"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11311140EvidenceFillTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_pit_remains_blocked_without_true_membership_source(self) -> None:
        pit = rows("task1134_pit_membership_pass_recheck.csv")
        self.assertEqual(3689, len(pit))
        self.assertEqual({"0"}, {row["pit_membership_pass"] for row in pit})
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in pit})

    def test_nonsec_source_time_complete_but_not_historical_dynamic(self) -> None:
        asof = rows("task1137_nonsec_asof_event_panel.csv")
        self.assertGreater(sum(1 for row in asof if row["source_time_complete_flag"] == "1"), 1000)
        self.assertEqual({"0"}, {row["historical_dynamic_use_allowed"] for row in asof})
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in asof})

    def test_policy_preregistration_remains_blocked(self) -> None:
        readiness = rows("task1139_policy_preregistration_readiness.csv")[0]
        self.assertEqual("0", readiness["policy_preregistration_allowed"])
        self.assertEqual("0", readiness["replay_executed"])
        self.assertEqual("0", readiness["selection_promoted"])

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1140_evidence_fill_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("blocked_continue_source_repair", closeout["verdict"])
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
