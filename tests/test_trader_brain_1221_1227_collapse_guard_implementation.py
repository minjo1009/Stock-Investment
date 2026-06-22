from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1221_1227_collapse_guard_implementation_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1221_1227_collapse_guard_implementation"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain12211227CollapseGuardImplementationTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_product_sleeve_allows_but_routes_leverage(self) -> None:
        product = rows("task1223_product_structure_classifier.csv")
        complex_rows = [row for row in product if row["product_sleeve"] == "leveraged_or_complex_product"]
        self.assertGreaterEqual(len(complex_rows), 1)
        self.assertEqual({"1"}, {row["leverage_allowed"] for row in complex_rows})
        self.assertEqual({"0"}, {row["ordinary_equity_ranking_allowed"] for row in complex_rows})

    def test_assignment_flags_are_no_future(self) -> None:
        specs = rows("task1226_l5_collapse_guard_trade_specs.csv")
        self.assertEqual({"0"}, {row["assignment_uses_future_outcome"] for row in specs})
        self.assertEqual({"1"}, {row["exit_uses_post_entry_price_path"] for row in specs})

    def test_guard_reduces_drawdown_but_does_not_accept_strategy(self) -> None:
        metric = rows("task1227_collapse_guard_metrics.csv")[0]
        self.assertLess(float(metric["max_drawdown"]), -0.30)
        self.assertEqual("0", metric["beats_base_slot5"])
        self.assertEqual("NOT_ACCEPTED", metric["strategy_acceptance"])

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1227_collapse_guard_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("1", closeout["replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
