from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1121_1130_pit_nonsec_repair_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1121_1130_pit_nonsec_repair"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11211130PitNonsecRepairTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_pit_repair_gate_blocks_current_static_universe(self) -> None:
        membership = rows("task1123_pit_membership_validation_panel.csv")
        join = rows("task1124_trade_spec_pit_join_audit.csv")
        self.assertEqual(4410, len(membership))
        self.assertEqual(3689, len(join))
        self.assertEqual({"0"}, {row["pit_membership_pass"] for row in membership})
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in join})

    def test_nonsec_candidates_are_normalized_but_not_allowed(self) -> None:
        candidates = rows("task1126_nonsec_normalized_event_candidates.csv")
        validation = rows("task1127_nonsec_event_validation_panel.csv")
        self.assertGreater(len(candidates), 1000)
        self.assertEqual(len(candidates), len(validation))
        self.assertIn("macro_fred", {row["source_family"] for row in candidates})
        self.assertIn("task_636_content_source_text", {row["source_family"] for row in candidates})
        self.assertNotIn("sec_company_submissions", {row["source_name"] for row in candidates})
        self.assertEqual({"0"}, {row["dynamic_use_allowed"] for row in validation})

    def test_reentry_boundary_separates_fresh_from_exposure(self) -> None:
        fresh = rows("task1128_fresh_entry_candidate_ledger.csv")
        exposure = rows("task1128_continuous_exposure_episode_ledger.csv")
        self.assertEqual(135, len(fresh))
        self.assertEqual(6, sum(1 for row in fresh if row["fresh_entry_candidate_flag"] == "1"))
        self.assertEqual(6, len(exposure))
        self.assertEqual({"0"}, {row["entry_counting_allowed"] for row in exposure})

    def test_closeout_preserves_no_replay_status(self) -> None:
        closeout = json.loads((ART / "task1130_pit_nonsec_repair_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("blocked_continue_source_repair", closeout["verdict"])
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
