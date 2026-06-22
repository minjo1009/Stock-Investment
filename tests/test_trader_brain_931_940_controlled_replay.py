from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_931_940_controlled_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_931_940_controlled_brain_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain931940ControlledReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_replay_has_strategy_and_qqq_results(self) -> None:
        summary = json.loads((ART / "task936_controlled_replay_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(1000.0, summary["initial_capital"])
        self.assertGreater(summary["strategy_final_equity"], 0)
        self.assertGreater(summary["qqq_final_equity"], 0)
        self.assertEqual("QQQ", summary["benchmark_symbol"])

    def test_replay_remains_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task936_controlled_replay_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])
        closeout = rows("task940_governance_closeout.csv")[0]
        self.assertEqual("DIAGNOSTIC_CONTROLLED_BRAIN_REPLAY_ONLY", closeout["authority"])

    def test_trade_rows_have_lineage_and_no_short(self) -> None:
        trades = rows("task931_controlled_replay_trades.csv")
        self.assertTrue(trades)
        self.assertEqual({"long"}, {row["side"] for row in trades})
        self.assertTrue(all(row["adapter_input_id"] and row["candidate_bundle_id"] and row["source_graph_id"] for row in trades))

    def test_split_and_theme_summaries_exist(self) -> None:
        self.assertEqual({"development_2021_2024", "oos_1_2025", "oos_2_2026_q1"}, {row["split_id"] for row in rows("task933_controlled_replay_by_split.csv")})
        self.assertEqual(10, len(rows("task934_controlled_replay_by_theme.csv")))


if __name__ == "__main__":
    unittest.main()
