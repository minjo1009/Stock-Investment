from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task731_source_information_router import build_task731
from src.backtest.source_information_router import route_source_event


class Task731SourceInformationRouterTest(unittest.TestCase):
    def test_form4_is_routed_not_discarded(self) -> None:
        routed = route_source_event(pd.Series({"source_form_family": "form4_insider"}))

        self.assertEqual(routed["source_route_state"], "insider_behavior_route")
        self.assertEqual(routed["route_circuit"], "insider_behavior_circuit")
        self.assertEqual(routed["source_is_discarded_flag"], 0)
        self.assertEqual(routed["operating_extractor_permission_state"], "denied_non_operating_source")
        self.assertIn("revenue", routed["forbidden_fact_families"])
        self.assertEqual(routed["backtest_eligible_flag"], 0)

    def test_financing_is_routed_to_credit_circuit(self) -> None:
        routed = route_source_event(pd.Series({"source_form_family": "financing_8k"}))

        self.assertEqual(routed["source_route_state"], "financing_credit_route")
        self.assertEqual(routed["route_circuit"], "credit_financing_circuit")
        self.assertIn("use_of_proceeds", routed["allowed_fact_families"])
        self.assertEqual(routed["source_is_discarded_flag"], 0)
        self.assertEqual(routed["backtest_eligible_flag"], 0)

    def test_task731_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task731(out_dir=out_dir)

            for filename in [
                "task731_source_route_map.csv",
                "task731_allowed_fact_family_matrix.csv",
                "task731_source_routed_events.csv",
                "task731_operating_extractor_permission.csv",
                "task731_non_operating_context_facts.csv",
                "task731_cross_circuit_edges.csv",
                "task731_pollution_guardrail.csv",
                "task731_gpt_institutional_review_summary.csv",
                "task_731_decision.csv",
                "task_731_pass_fail_matrix.csv",
                "task_731_source_information_router.md",
                "task731_source_routed_events.jsonl",
                "task731_cross_circuit_edges.jsonl",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            routed_events = artifacts["routed_events"]
            cross_edges = artifacts["cross_edges"]
            guardrail = artifacts["pollution_guardrail"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(len(routed_events), 5302)
            self.assertEqual(len(cross_edges), 5302)
            self.assertEqual(int(routed_events["source_is_discarded_flag"].sum()), 0)
            self.assertEqual(int(routed_events["backtest_eligible_flag"].sum()), 0)
            self.assertEqual(int(guardrail["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertEqual(decision["discarded_source_count"], 0)


if __name__ == "__main__":
    unittest.main()
