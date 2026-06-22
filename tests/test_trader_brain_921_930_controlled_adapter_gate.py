from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_921_930_controlled_adapter_gate_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain921930ControlledAdapterGateTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_eligibility_blocks_and_passes_rows(self) -> None:
        eligibility = rows("task921_adapter_eligibility_ledger.csv")
        states = {row["eligibility_state"] for row in eligibility}
        self.assertIn("eligible_controlled_adapter_candidate", states)
        self.assertIn("blocked_before_adapter_policy", states)
        for row in eligibility:
            if row["eligibility_state"] == "eligible_controlled_adapter_candidate":
                self.assertEqual("1", row["has_symbol"])
                self.assertEqual("1", row["symbol_in_universe"])
                self.assertEqual("no_direct_contradiction", row["contradiction_state"])

    def test_trade_specs_are_lineaged_and_not_results(self) -> None:
        specs = rows("task929_controlled_trade_specs.csv")
        self.assertTrue(specs)
        forbidden = {"entry_price", "exit_price", "shares", "final_capital", "return_pct", "pnl"}
        self.assertFalse(forbidden & set(specs[0]))
        self.assertEqual({"long"}, {row["side"] for row in specs})
        self.assertEqual({"ready_for_controlled_replay_plan"}, {row["trade_spec_state"] for row in specs})
        self.assertTrue(all(row["adapter_input_id"] and row["candidate_bundle_id"] and row["source_graph_id"] for row in specs))

    def test_gate_does_not_run_replay_or_change_status(self) -> None:
        gate = rows("task930_first_controlled_replay_gate.csv")[0]
        self.assertEqual("not_run_trade_spec_gate_only", gate["diagnostic_replay_status"])
        self.assertEqual("0", gate["price_lookup_count"])
        self.assertEqual("0", gate["trade_execution_count"])
        self.assertEqual("0", gate["pnl_count"])
        self.assertEqual("0", gate["engine_call_count"])
        self.assertEqual("NOT_ACCEPTED", gate["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", gate["deployment_readiness"])
        self.assertEqual("FORBIDDEN", gate["real_capital"])

    def test_summary_matches_expected_gate_shape(self) -> None:
        summary = json.loads((ART / "task921_930_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(4461, summary["input_adapter_rows"])
        self.assertGreater(summary["eligible_adapter_rows"], 0)
        self.assertEqual(summary["eligible_adapter_rows"], summary["trade_specs_ready"])
        self.assertEqual("go_for_first_controlled_replay_execution_next", summary["controlled_replay_gate_status"])


if __name__ == "__main__":
    unittest.main()
