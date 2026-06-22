from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_951_960_conviction_risk_filter_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_951_960_conviction_risk_filter_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain951960ConvictionRiskFilterReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_features_are_prior_session_only(self) -> None:
        features = rows("task952_conviction_price_context_panel.csv")
        self.assertTrue(features)
        self.assertEqual({"uses_prior_session_only_no_future_price"}, {row["price_context_rule"] for row in features})

    def test_open_positions_do_not_exceed_active_cap(self) -> None:
        for row in rows("task958_conviction_risk_equity_curves.csv"):
            self.assertLessEqual(int(row["open_positions"]), 10)
            if int(row["open_positions"]) > int(row["active_slot_cap"]):
                self.assertEqual(0, int(row["entries_selected"]))

    def test_best_policy_did_not_beat_baseline_is_recorded(self) -> None:
        closeout = rows("task960_conviction_risk_governance_closeout.csv")[0]
        self.assertEqual("0", closeout["best_policy_beats_baseline_slot10"])

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task951_960_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
