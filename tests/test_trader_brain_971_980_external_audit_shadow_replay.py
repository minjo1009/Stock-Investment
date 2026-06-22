from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_971_980_external_audit_shadow_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_971_980_external_audit_shadow_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain971980ExternalAuditShadowReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_policy_is_pre_registered(self) -> None:
        policy = rows("task972_pre_registered_policy.csv")[0]
        self.assertEqual("slot10_external_audit_shadow_rank_v1", policy["policy_id"])
        self.assertEqual("1", policy["pre_registered_before_replay"])

    def test_preselected_and_entered_are_separated(self) -> None:
        summary = rows("task978_replay_summary.csv")[0]
        self.assertEqual("630", summary["policy_preselected_entries"])
        self.assertEqual("450", summary["selected_entries"])
        self.assertEqual("180", summary["deferred_by_live_slot_cap"])

    def test_trade_ids_match_entered_ids(self) -> None:
        entered = {row["trade_spec_id"] for row in rows("task974_replay_entry_decision_ledger.csv") if row["entry_decision_state"] == "entered"}
        traded = {row["trade_spec_id"] for row in rows("task975_replay_trades.csv")}
        self.assertEqual(entered, traded)

    def test_equity_constraints_hold(self) -> None:
        for row in rows("task976_replay_equity.csv"):
            self.assertLessEqual(int(row["open_positions"]), 10)
            self.assertGreaterEqual(float(row["cash"]), -0.0001)
            self.assertAlmostEqual(float(row["equity"]), float(row["cash"]) + float(row["open_market_value"]), places=2)

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task971_980_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
