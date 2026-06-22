from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1111_1120_pre_replay_audit_program_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1111_1120_pre_replay_audit_program"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11111120PreReplayAuditProgramTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_pit_universe_blocks_all_trade_specs(self) -> None:
        join = rows("task1113_trade_spec_pit_join_audit.csv")
        blocks = rows("task1114_pit_block_ledger.csv")
        self.assertEqual(3689, len(join))
        self.assertEqual(len(join), len(blocks))
        self.assertEqual({"0"}, {row["pit_universe_pass"] for row in join})

    def test_reentry_audit_detects_stale_static_thesis(self) -> None:
        reentries = rows("task1115_reentry_freshness_ledger.csv")
        stale = [row for row in reentries if row["stale_reentry_flag"] == "1"]
        self.assertEqual(135, len(reentries))
        self.assertGreaterEqual(len(stale), 120)
        self.assertEqual({"0"}, {row["reentry_selection_use_allowed"] for row in reentries})

    def test_exposure_chains_are_separated_from_new_decisions(self) -> None:
        exposures = rows("task1116_continuous_thesis_exposure_ledger.csv")
        self.assertEqual(6, len(exposures))
        self.assertEqual({"1"}, {row["continuous_thesis_exposure_flag"] for row in exposures})
        self.assertTrue(all(row["exposure_type"] == "structural_hold_candidate" for row in exposures))

    def test_non_sec_dynamic_sources_are_inventory_only(self) -> None:
        non_sec = rows("task1118_non_sec_source_time_panel.csv")
        shadow = rows("task1119_dynamic_event_shadow_ranking.csv")
        self.assertGreaterEqual(len(non_sec), 5)
        self.assertEqual({"0"}, {row["dynamic_use_allowed"] for row in non_sec})
        self.assertEqual({"0"}, {row["shadow_ranking_use_allowed"] for row in shadow})

    def test_statuses_and_replay_remain_blocked(self) -> None:
        closeout = json.loads((ART / "task1120_external_audit_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
