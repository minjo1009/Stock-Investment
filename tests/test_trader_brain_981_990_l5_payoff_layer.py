from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_981_990_l5_payoff_layer_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_981_990_l5_payoff_layer"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain981990L5PayoffLayerTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_source_context_covers_l5_layers(self) -> None:
        layers = {row["layer_id"] for row in rows("task981_l5_source_context_manifest.csv")}
        self.assertTrue({"L5-A", "L5-B", "L5-C", "L5-D", "L5-E", "L5-V"} <= layers)

    def test_feature_time_uses_prior_prices_only(self) -> None:
        guard = rows("task988_l5v_validation_guard_panel.csv")
        self.assertTrue(guard)
        for row in guard:
            if row["feature_time_state"] == "pass":
                self.assertLess(row["max_price_timestamp_used"], row["entry_date"])

    def test_feature_panels_are_not_selection_inputs(self) -> None:
        guard = rows("task988_l5v_validation_guard_panel.csv")
        self.assertEqual({"0"}, {row["selection_use_allowed"] for row in guard})
        self.assertEqual({"0"}, {row["replay_executed"] for row in guard})

    def test_gap_pnl_is_evaluation_only(self) -> None:
        gap = rows("task989_baseline_shadow_gap_evaluation_only.csv")
        self.assertTrue(gap)
        self.assertEqual(
            {"post_replay_failure_decomposition_only_never_selection_input"},
            {row["evaluation_use_mode"] for row in gap},
        )

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task981_990_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
