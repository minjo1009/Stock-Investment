from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1228_1237_volatility_terminal_discriminator_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain12281237VolatilityTerminalDiscriminatorTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_high_vol_upside_is_not_penalized(self) -> None:
        specs = rows("task1233_policy_specs.csv")
        high_vol = [row for row in specs if row["volatility_terminal_route"] == "high_vol_upside"]
        self.assertGreater(len(high_vol), 0)
        self.assertEqual({"1.0"}, {row["position_multiplier"] for row in high_vol})
        self.assertEqual({"scheduled_preserve_upside"}, {row["exit_reason"] for row in high_vol})

    def test_terminal_discriminator_does_not_use_outcomes(self) -> None:
        disc = rows("task1231_l2_volatility_terminal_discriminator.csv")
        self.assertEqual({"0"}, {row["outcome_used_for_assignment"] for row in disc})
        self.assertEqual({"1"}, {row["volatility_not_penalized_alone"] for row in disc})

    def test_policy_beats_base_but_not_acceptance_targets(self) -> None:
        metric = rows("task1234_replay_metrics.csv")[0]
        gate = rows("task1236_acceptance_gate.csv")[0]
        self.assertEqual("1", metric["beats_base_slot5"])
        self.assertEqual("1", metric["beats_benchmark"])
        self.assertEqual("0", gate["target_cagr_30pct_pass"])
        self.assertEqual("0", gate["target_mdd_minus30pct_pass"])

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1237_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("1", closeout["replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
