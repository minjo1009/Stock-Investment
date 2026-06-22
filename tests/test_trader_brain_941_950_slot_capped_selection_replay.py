from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_941_950_slot_capped_selection_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain941950SlotCappedSelectionReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_slot_caps_are_enforced(self) -> None:
        equity = rows("task944_slot_capped_equity_curves.csv")
        for row in equity:
            self.assertLessEqual(int(row["open_positions"]), int(row["slot_cap"]))

    def test_summary_contains_three_five_ten(self) -> None:
        summary = rows("task946_slot_capped_summary.csv")
        self.assertEqual({3, 5, 10}, {int(row["slot_cap"]) for row in summary})

    def test_selection_features_do_not_use_future_outcomes(self) -> None:
        features = rows("task941_selection_feature_panel.csv")
        self.assertTrue(features)
        for row in features[:50]:
            self.assertIn("future_return", row["does_not_use"])
            self.assertIn("realized_return", row["does_not_use"])
            self.assertIn("pnl", row["does_not_use"])

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task941_950_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
