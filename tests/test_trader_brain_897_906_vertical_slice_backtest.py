from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_897_906_vertical_slice_backtest_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_897_906_vertical_slice_backtest"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain897906VerticalSliceBacktestTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_source_admission_blocks_l2_to_l5_outputs(self) -> None:
        admission = rows("task897_source_admission_audit.csv")
        self.assertEqual(69, len(admission))
        self.assertEqual({"0"}, {row["can_enter_l2"] for row in admission})
        self.assertEqual(0, len(rows("task897_primitive_fact_seed_panel.csv")))
        self.assertEqual(0, len(rows("task898_economic_meaning_seed_panel.csv")))
        self.assertEqual(0, len(rows("task899_relation_snapshot_panel.csv")))
        self.assertEqual(0, len(rows("task900_candidate_thesis_packets.csv")))
        self.assertEqual(0, len(rows("task901_dry_trader_decisions.csv")))

    def test_raw_source_gap_stops_replay(self) -> None:
        front_gates = {row["gate"]: row["status"] for row in rows("task897_906_front_gate_status.csv")}
        self.assertEqual("fail", front_gates["raw_external_source_attached_for_l2"])
        self.assertEqual("invalidated", front_gates["previous_replay_result_validity"])
        gates = {row["gate"]: row["status"] for row in rows("task897_906_stop_gate_status.csv")}
        self.assertEqual("fail_front_gate_no_go", gates["source_admission_for_l2"])
        self.assertEqual("not_run_front_gate_no_go", gates["diagnostic_replay_allowed"])
        self.assertEqual(0, len(rows("task906_diagnostic_trade_specs.csv")))
        self.assertEqual(0, len(rows("task906_diagnostic_replay_trades.csv")))

    def test_no_go_has_no_acceptance_claim(self) -> None:
        summary = json.loads((ART / "task897_906_vertical_slice_backtest_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("no_go_missing_raw_external_source", summary["front_gate_status"])
        self.assertEqual("not_run_front_gate_no_go", summary["replay_status"])
        self.assertTrue(summary["invalidated_previous_replay_result"])
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
