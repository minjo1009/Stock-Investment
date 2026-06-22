from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1211_1220_collapse_guard_development_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1211_1220_collapse_guard_development"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain12111220CollapseGuardDevelopmentTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_leverage_is_allowed_but_routed(self) -> None:
        leverage = rows("task1218_leverage_handling_policy.csv")
        self.assertIn("allowed", {row["policy_clause"] for row in leverage})
        self.assertIn("must_route", {row["policy_clause"] for row in leverage})

    def test_collapse_cases_are_eval_only(self) -> None:
        cases = rows("task1213_collapse_tail_diagnostic_eval_only.csv")
        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual({"0"}, {row["outcome_used_for_assignment"] for row in cases})
        self.assertEqual({"1"}, {row["diagnostic_only"] for row in cases})

    def test_l5_has_exit_sizing_and_reentry_rules(self) -> None:
        l5 = rows("task1217_l5_trade_action_policy.csv")
        names = {row["rule_name"] for row in l5}
        self.assertIn("hard_event_exit", names)
        self.assertIn("risk_bucket_sizing", names)
        self.assertIn("reentry_cooling", names)

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1220_collapse_guard_development_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
