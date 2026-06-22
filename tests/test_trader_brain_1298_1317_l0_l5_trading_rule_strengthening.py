from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1298_1317_l0_l5_trading_rule_strengthening"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class Task1298To1317L0L5TradingRuleStrengtheningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [sys.executable, "scripts/trader_brain_1298_1317_l0_l5_trading_rule_strengthening.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_layer_outputs_have_expected_shape(self) -> None:
        self.assertEqual(310, len(read_csv(OUT_DIR / "task1300_l0_coverage_gate.csv")))
        self.assertEqual(310, len(read_csv(OUT_DIR / "task1301_l1_signal_quality_scores.csv")))
        self.assertEqual(310, len(read_csv(OUT_DIR / "task1302_l2_trading_judgment_scores.csv")))
        self.assertEqual(1860, len(read_csv(OUT_DIR / "task1303_l3_rule_action_edges.csv")))
        self.assertEqual(310, len(read_csv(OUT_DIR / "task1304_l4_rank_route_panel.csv")))

    def test_policy_replay_outputs_have_expected_shape(self) -> None:
        self.assertEqual(1240, len(read_csv(OUT_DIR / "task1305_l5_rule_policy_specs.csv")))
        self.assertEqual(1240, len(read_csv(OUT_DIR / "task1306_replay_trades.csv")))
        self.assertEqual(248, len(read_csv(OUT_DIR / "task1307_replay_equity.csv")))
        self.assertEqual(4, len(read_csv(OUT_DIR / "task1308_replay_metrics.csv")))

    def test_no_future_assignment_and_no_acceptance_overclaim(self) -> None:
        for name in [
            "task1302_l2_trading_judgment_scores.csv",
            "task1304_l4_rank_route_panel.csv",
            "task1305_l5_rule_policy_specs.csv",
            "task1306_replay_trades.csv",
        ]:
            rows = read_csv(OUT_DIR / name)
            self.assertTrue(all(row["assignment_uses_future_outcome"] == "0" for row in rows))
        gate = read_csv(OUT_DIR / "task1310_acceptance_gate.csv")[0]
        self.assertEqual("NOT_ACCEPTED", gate["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", gate["deployment_readiness"])
        self.assertEqual("FORBIDDEN", gate["real_capital"])


if __name__ == "__main__":
    unittest.main()
