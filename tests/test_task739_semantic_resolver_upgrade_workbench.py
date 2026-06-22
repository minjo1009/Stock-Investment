from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task739_semantic_resolver_upgrade_workbench import build_task739
from src.backtest.semantic_resolver_upgrade_workbench import build_workbench


class Task739SemanticResolverUpgradeWorkbenchTest(unittest.TestCase):
    def test_workbench_creates_extractor_and_resolver_orders(self) -> None:
        requirements = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L1",
                    "bundle_id": "bundle::L1",
                    "source_event_id": "E1",
                    "symbol": "TEST",
                    "theme_id": "theme",
                    "entry_ts": "2024-01-02T14:30:00Z",
                    "requirement_family": "form4_plan_pattern_enrichment",
                    "circuit_type": "form4_insider_behavior",
                    "resolver_target_state": "insider_pattern_needed",
                    "missing_primitive_fields": "insider_role|shares_sold|percent_of_holdings",
                    "required_denominators": "insider_total_holdings|market_cap",
                    "required_comparators": "prior_90d_insider_sales",
                    "required_timing_checks": "transaction_date|filing_date",
                    "required_interaction_fields": "financing_or_liquidity_context",
                    "can_affect_confidence": 0,
                    "can_affect_risk": 1,
                    "can_affect_slot": 0,
                }
            ]
        )

        workbench = build_workbench(requirements)

        extractor = workbench["extractor_orders"].iloc[0]
        resolver = workbench["resolver_orders"].iloc[0]
        trace = workbench["trace"].iloc[0]

        self.assertEqual(extractor["target_extractor"], "form4_insider_pattern_extractor")
        self.assertEqual(extractor["engineering_lane"], "engineering_high")
        self.assertIn("NO_BUY_SELL_ACTIONABILITY", extractor["guardrail_ids"])
        self.assertEqual(resolver["target_resolver"], "form4_insider_behavior_resolver")
        self.assertIn("form4_plan_pattern_resolved", resolver["allowed_output_states"])
        self.assertIn("buy_signal", resolver["forbidden_output_states"])
        self.assertEqual(trace["extractor_work_order_id"], extractor["work_order_id"])
        self.assertEqual(trace["resolver_work_order_id"], resolver["work_order_id"])

    def test_allowed_taxonomy_keeps_financing_as_review_not_trade_ready(self) -> None:
        requirements = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L2",
                    "bundle_id": "bundle::L2",
                    "source_event_id": "E2",
                    "symbol": "TEST",
                    "theme_id": "theme",
                    "entry_ts": "2024-01-02T14:30:00Z",
                    "requirement_family": "financing_terms_enrichment",
                    "circuit_type": "credit_financing",
                    "resolver_target_state": "financing_terms_needed",
                    "missing_primitive_fields": "instrument|use_of_proceeds",
                    "required_denominators": "cash|debt|market_cap",
                    "required_comparators": "prior_liquidity",
                    "required_timing_checks": "announcement_date|closing_date",
                    "required_interaction_fields": "operating_catalyst_alignment|dilution_overhang",
                    "can_affect_confidence": 0,
                    "can_affect_risk": 1,
                    "can_affect_slot": 0,
                }
            ]
        )

        resolver = build_workbench(requirements)["resolver_orders"].iloc[0]

        self.assertIn("growth_funding_review", resolver["allowed_output_states"])
        self.assertIn("trade_ready", resolver["forbidden_output_states"])
        self.assertNotIn("bullish_financing", resolver["allowed_output_states"])
        self.assertEqual(int(resolver["research_only_flag"]), 1)

    def test_task739_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task739(out_dir=out_dir)

            for filename in [
                "task739_extractor_work_orders.csv",
                "task739_extractor_work_orders.jsonl",
                "task739_resolver_work_orders.csv",
                "task739_resolver_work_orders.jsonl",
                "task739_work_order_requirement_trace.csv",
                "task739_work_order_requirement_trace.jsonl",
                "task739_allowed_resolver_states.csv",
                "task739_allowed_resolver_states.jsonl",
                "task739_engineering_lane_summary.csv",
                "task739_denominator_join_contracts.csv",
                "task739_denominator_join_contracts.yaml",
                "task739_comparator_join_contracts.csv",
                "task739_comparator_join_contracts.yaml",
                "task739_timing_asof_contracts.csv",
                "task739_timing_asof_contracts.yaml",
                "task739_coverage_report.csv",
                "task739_guardrail.csv",
                "task739_gpt_review_summary.csv",
                "task_739_decision.csv",
                "task_739_pass_fail_matrix.csv",
                "task_739_semantic_resolver_upgrade_workbench.md",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            requirements = artifacts["requirements"]
            extractor_orders = artifacts["extractor_orders"]
            resolver_orders = artifacts["resolver_orders"]
            trace = artifacts["trace"]
            guardrail = artifacts["guardrail"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(len(extractor_orders), requirements["requirement_family"].nunique())
            self.assertEqual(len(resolver_orders), requirements["requirement_family"].nunique())
            self.assertEqual(len(trace), len(requirements))
            self.assertEqual(len(trace), 4101)
            self.assertEqual(int(guardrail["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertGreater(int(decision["engineering_high_work_order_count"]), 0)


if __name__ == "__main__":
    unittest.main()
