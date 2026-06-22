from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1201_1210_l0_l3_controlled_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain12011210L0L3ControlledReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_replay_preserves_no_future_assignment_flags(self) -> None:
        cards = rows("task1202_l4_candidate_cards.csv")
        specs = rows("task1203_l5_trade_specs.csv")
        selections = rows("task1205_slot_selections.csv")
        self.assertEqual({"0"}, {row["assignment_uses_future_outcome"] for row in cards})
        self.assertEqual({"0"}, {row["assignment_uses_future_outcome"] for row in specs})
        self.assertEqual({"0"}, {row["assignment_uses_future_outcome"] for row in selections})

    def test_slot_metrics_are_diagnostic_and_not_accepted(self) -> None:
        metrics = rows("task1207_replay_metrics.csv")
        self.assertEqual(3, len(metrics))
        self.assertEqual({"NOT_ACCEPTED"}, {row["strategy_acceptance"] for row in metrics})
        self.assertEqual({"DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"}, {row["deployment_readiness"] for row in metrics})
        self.assertEqual({"FORBIDDEN"}, {row["real_capital"] for row in metrics})

    def test_current_best_beats_qqq_but_fails_targets(self) -> None:
        acceptance = rows("task1209_acceptance_gate.csv")[0]
        self.assertEqual("l0_l3_slot5_v1", acceptance["best_variant"])
        self.assertEqual("1", acceptance["benchmark_pass"])
        self.assertEqual("0", acceptance["target_cagr_30pct_pass"])
        self.assertEqual("0", acceptance["target_mdd_minus30pct_pass"])

    def test_trade_attribution_is_preserved(self) -> None:
        trades = rows("task1206_replay_trades.csv")
        self.assertGreater(len(trades), 0)
        self.assertTrue(all(row["trade_spec_id"] for row in trades))
        self.assertTrue(all(row["derived_theme"] for row in trades))

    def test_cost_sensitivity_exists_and_preserves_status(self) -> None:
        costs = rows("task1207_cost_sensitivity.csv")
        self.assertEqual(12, len(costs))
        self.assertEqual({"0.0", "20.0", "50.0", "100.0"}, {row["round_trip_cost_bps"] for row in costs})
        self.assertEqual({"NOT_ACCEPTED"}, {row["strategy_acceptance"] for row in costs})

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1210_l0_l3_controlled_replay_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("1", closeout["diagnostic_replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
