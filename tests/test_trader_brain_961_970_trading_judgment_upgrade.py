from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_961_970_trading_judgment_upgrade_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_961_970_trading_judgment_upgrade"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain961970TradingJudgmentUpgradeTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_no_future_evidence_enters_freshness_panel(self) -> None:
        freshness = rows("task962_thesis_freshness_panel.csv")
        self.assertTrue(freshness)
        self.assertEqual({"pass"}, {row["leakage_state"] for row in freshness})

    def test_duplicate_cluster_controls_are_recorded(self) -> None:
        duplicate = rows("task963_duplicate_thesis_clusters.csv")
        self.assertTrue(duplicate)
        self.assertIn("thesis_cluster_key", duplicate[0])
        self.assertIn("duplicate_cluster_prior_selected_count", duplicate[0])

    def test_equity_constraints_hold(self) -> None:
        for row in rows("task969_fresh_duplicate_replay_equity.csv"):
            self.assertLessEqual(int(row["open_positions"]), 10)
            self.assertGreaterEqual(float(row["cash"]), -0.0001)
            self.assertAlmostEqual(
                float(row["equity"]),
                float(row["cash"]) + float(row["open_market_value"]),
                places=2,
            )

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task961_970_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])

    def test_upgraded_replay_did_not_beat_baseline_is_recorded(self) -> None:
        closeout = rows("task970_governance_closeout.csv")[0]
        self.assertEqual("0", closeout["beats_baseline_slot10"])


if __name__ == "__main__":
    unittest.main()
