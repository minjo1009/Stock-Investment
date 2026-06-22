from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1171_1180_public_filer_proxy_backtest_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1171_1180_public_filer_proxy_backtest"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11711180PublicFilerProxyBacktestTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_price_and_feature_coverage_exist(self) -> None:
        coverage = rows("task1173_price_coverage_gate.csv")[0]
        self.assertEqual("1", coverage["price_coverage_pass"])
        features = rows("task1174_public_filer_proxy_feature_panel.csv")
        self.assertGreater(len(features), 1000)
        self.assertEqual({"0"}, {row["future_price_used"] for row in features[:500]})
        self.assertEqual({"0"}, {row["future_filing_used"] for row in features[:500]})

    def test_slot_variants_are_backtested(self) -> None:
        metrics = rows("task1177_proxy_backtest_metrics.csv")
        self.assertEqual(
            {"public_filer_proxy_slot3_v1", "public_filer_proxy_slot5_v1", "public_filer_proxy_slot10_v1"},
            {row["policy_variant_id"] for row in metrics},
        )
        self.assertTrue(all(row["strategy_acceptance"] == "NOT_ACCEPTED" for row in metrics))

    def test_benchmark_and_bad_strategy_result_are_recorded(self) -> None:
        metrics = rows("task1177_proxy_backtest_metrics.csv")
        best = max(metrics, key=lambda row: float(row["final_equity"]))
        self.assertEqual("public_filer_proxy_slot10_v1", best["policy_variant_id"])
        self.assertLess(float(best["final_equity"]), float(best["benchmark_final_equity"]))
        self.assertGreater(float(best["benchmark_final_equity"]), 1000)

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1180_public_filer_proxy_backtest_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("1", closeout["diagnostic_replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
