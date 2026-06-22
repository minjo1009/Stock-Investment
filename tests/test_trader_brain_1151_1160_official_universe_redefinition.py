from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1151_1160_official_universe_redefinition_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1151_1160_official_universe_redefinition"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11511160OfficialUniverseRedefinitionTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_custom_theme_universe_is_not_selection_basis(self) -> None:
        basis = rows("task1151_universe_basis_decision.csv")[0]
        self.assertEqual("0", basis["custom_10x7_for_selection_allowed"])
        theme_policy = rows("task1157_theme_label_policy.csv")[0]
        self.assertIn("preselecting_candidate_symbols", theme_policy["forbidden_use"])

    def test_official_current_sec_universe_is_broad_but_not_pit(self) -> None:
        universe = rows("task1153_current_sec_exchange_universe.csv")
        self.assertGreaterEqual(len(universe), 9000)
        self.assertEqual({"0"}, {row["historical_listing_pit_pass"] for row in universe})

    def test_seed_panel_blocks_selection_until_asof_membership(self) -> None:
        calendar = rows("task1155_decision_calendar.csv")
        seed = rows("task1156_official_universe_seed_panel.csv")
        self.assertEqual(63, len(calendar))
        self.assertEqual(len(calendar) * 1000, len(seed))
        self.assertEqual({"0"}, {row["eligible_for_brain_selection"] for row in seed})
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in seed})

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1160_official_universe_redefinition_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("0", closeout["custom_10x7_selection_basis_allowed"])
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
