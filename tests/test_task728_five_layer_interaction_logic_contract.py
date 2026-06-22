from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task728_five_layer_interaction_logic_contract import build_task728


class Task728FiveLayerInteractionLogicContractTest(unittest.TestCase):
    def test_task728_builds_five_layer_interaction_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task728(out_dir=out_dir)

            expected_files = [
                "task728_layer_state_inventory.csv",
                "task728_corrected_five_layer_contract.csv",
                "task728_interaction_rule_family_catalog.csv",
                "task728_observed_five_layer_interaction_cells.csv",
                "task728_rule_candidate_assignments.csv",
                "task728_rule_coverage_audit.csv",
                "task728_gpt_institutional_review_packet.csv",
                "task_728_decision.csv",
                "task_728_pass_fail_matrix.csv",
                "task_728_five_layer_interaction_logic_contract.md",
                "artifact_manifest.csv",
            ]
            for filename in expected_files:
                self.assertTrue((out_dir / filename).exists(), filename)

            layer_contract = artifacts["layer_contract"]
            self.assertEqual(set(layer_contract["layer"]), {"L1_Evidence", "L2_Economic", "L3_Price", "L4_Portfolio", "L5_Risk"})
            self.assertTrue((layer_contract["standalone_trade_signal_allowed_flag"] == 0).all())

            rule_families = artifacts["rule_families"]
            self.assertGreaterEqual(len(rule_families), 25)
            for relation in ["reinforcing", "offsetting", "prerequisite", "blocker", "confidence_cap", "invalidation", "sizing_modifier"]:
                self.assertIn(relation, set(rule_families["relation_type"]))

            observed_cells = artifacts["observed_cells"]
            rule_candidates = artifacts["rule_candidates"]
            self.assertGreaterEqual(len(observed_cells), 100)
            self.assertEqual(len(observed_cells), len(rule_candidates))
            self.assertGreaterEqual(rule_candidates["relation_type"].nunique(), 5)
            self.assertTrue((rule_candidates["assignment_allowed_flag"] == 0).all())
            self.assertTrue((rule_candidates["backtest_allowed_flag"] == 0).all())

            review = artifacts["gpt_packet"]
            self.assertEqual(len(review), 5)
            self.assertTrue((review["gpt_response_status"] == "CAPTURED_IN_CHROME").all())

            decision = artifacts["decision"].iloc[0]
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
            self.assertEqual(decision["real_capital_status"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
