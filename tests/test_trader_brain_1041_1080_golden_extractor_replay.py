from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1041_1080_golden_extractor_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1041_1080_golden_extractor_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain10411080GoldenExtractorReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_extractor_and_stress_inputs_exist(self) -> None:
        self.assertEqual(10, len(rows("task1041_gpt_expert_plan_synthesis.csv")))
        self.assertEqual(20, len(rows("task1042_extractor_contract.csv")))
        self.assertEqual(20, len(rows("task1043_extractor_golden_match.csv")))
        self.assertEqual(200, len(rows("task1044_expanded_stress_input_set.csv")))

    def test_adapter_feature_panel_is_large_and_gap_marked(self) -> None:
        features = rows("task1045_golden_brain_adapter_feature_panel.csv")
        self.assertEqual(3689, len(features))
        self.assertEqual({"1"}, {row["historical_source_time_gap"] for row in features})

    def test_base_and_risk_overlay_backtests_ran(self) -> None:
        base = rows("task1050_golden_brain_backtest_summary.csv")
        risk = rows("task1055_golden_risk_overlay_summary.csv")
        self.assertEqual({"3", "5", "10"}, {row["slot_cap"] for row in base})
        self.assertEqual(8, len(risk))
        self.assertTrue(any(row["meets_cagr_30"] == "1" for row in base))
        self.assertTrue(any(row["meets_cagr_30"] == "1" for row in risk))

    def test_statuses_remain_diagnostic_only(self) -> None:
        closeout = json.loads((ART / "task1080_golden_extractor_replay_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])
        self.assertEqual("1", closeout["historical_source_time_gap"])


if __name__ == "__main__":
    unittest.main()
