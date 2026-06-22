from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_991_1000_l5_policy_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_991_1000_l5_policy_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain9911000L5PolicyReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_policy_is_pre_registered(self) -> None:
        policy = rows("task992_pre_registered_l5_policy.csv")
        self.assertEqual(1, len(policy))
        self.assertEqual("1", policy[0]["pre_registered_before_replay"])

    def test_selection_ledger_has_no_outcome_columns(self) -> None:
        selection = rows("task993_l5_policy_selection_ledger.csv")
        forbidden = {"pnl", "return_pct", "future_return", "realized_return", "outcome_rank", "exit_price"}
        self.assertFalse(forbidden & set(selection[0].keys()))

    def test_slot_cap_preselection(self) -> None:
        counts: dict[str, int] = {}
        for row in rows("task993_l5_policy_selection_ledger.csv"):
            if row["selection_state"] == "selected":
                counts[row["entry_date"]] = counts.get(row["entry_date"], 0) + 1
        self.assertTrue(counts)
        self.assertLessEqual(max(counts.values()), 10)

    def test_failure_decomposition_is_evaluation_only(self) -> None:
        for name in ["task999_l5_bucket_attribution_evaluation_only.csv", "task999_l5_tail_trades_evaluation_only.csv"]:
            self.assertEqual(
                {"post_replay_failure_decomposition_only_never_selection_input"},
                {row["evaluation_use_mode"] for row in rows(name)},
            )

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task991_1000_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
