from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task732_source_circuit_interpreters import build_task732
from src.backtest.source_circuit_interpreters import interpret_source_event


class Task732SourceCircuitInterpretersTest(unittest.TestCase):
    def test_form4_builds_context_without_operating_fact(self) -> None:
        row = pd.Series(
            {
                "event_id": "E1",
                "lifecycle_id": "L1",
                "symbol": "TEST",
                "theme_id": "theme",
                "entry_ts": "2024-01-02T14:30:00Z",
                "split_name": "unit",
                "source_form_family": "form4_insider",
                "content_interpretation_evidence_span": "FORM 4 director transactionCode P common stock",
            }
        )
        context, edge = interpret_source_event(row)

        self.assertEqual(context["context_type"], "InsiderBehaviorContext")
        self.assertIn("insider_open_market_buy_observed", context["interpretation_states"])
        self.assertEqual(context["operating_primitive_created_flag"], 0)
        self.assertEqual(context["source_is_discarded_flag"], 0)
        self.assertEqual(edge["rule_id"], "INSIDER_CONTEXT_MODIFIES_ONLY_IF_OPERATING_PATH_EXISTS")
        self.assertEqual(edge["backtest_eligible_flag"], 0)

    def test_financing_context_splits_growth_and_dilution(self) -> None:
        row = pd.Series(
            {
                "event_id": "E2",
                "lifecycle_id": "L2",
                "symbol": "TEST",
                "theme_id": "theme",
                "entry_ts": "2024-01-02T14:30:00Z",
                "split_name": "unit",
                "source_form_family": "financing_8k",
                "content_interpretation_evidence_span": "$185.0 million convertible notes with warrants for manufacturing capacity expansion",
            }
        )
        context, edge = interpret_source_event(row)

        self.assertEqual(context["context_type"], "CreditFinancingContext")
        self.assertIn("growth_funding_possible", context["interpretation_states"])
        self.assertIn("dilution_overhang_present", context["interpretation_states"])
        self.assertEqual(context["operating_primitive_created_flag"], 0)
        self.assertEqual(edge["relation_type"], "offsetting_or_reinforcing")

    def test_macro_without_company_link_stays_context(self) -> None:
        row = pd.Series(
            {
                "event_id": "E3",
                "lifecycle_id": "L3",
                "symbol": "GEV",
                "theme_id": "power_grid_electrification",
                "entry_ts": "2024-01-02T14:30:00Z",
                "split_name": "unit",
                "source_form_family": "macro_policy_or_geopolitical_source",
                "content_interpretation_evidence_span": "Federal budget funding supports power grid demand",
            }
        )
        context, edge = interpret_source_event(row)

        self.assertEqual(context["context_type"], "MacroPolicyTransmissionContext")
        self.assertIn("single_name_link_missing", context["interpretation_states"])
        self.assertEqual(context["operating_primitive_created_flag"], 0)
        self.assertEqual(edge["rule_id"], "MACRO_POLICY_REQUIRES_COMPANY_LINK_FOR_SINGLE_NAME")

    def test_task732_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task732(out_dir=out_dir)

            for filename in [
                "task732_circuit_contexts.csv",
                "task732_context_edges.csv",
                "task732_circuit_coverage_report.csv",
                "task732_forbidden_fact_guardrail.csv",
                "task732_alive_review_states_report.csv",
                "task732_gpt_review_summary.csv",
                "task_732_decision.csv",
                "task_732_pass_fail_matrix.csv",
                "task_732_source_circuit_interpreters.md",
                "task732_circuit_contexts.jsonl",
                "task732_context_edges.jsonl",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            contexts = artifacts["contexts"]
            edges = artifacts["edges"]
            guardrail = artifacts["guardrail"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(len(contexts), 5302)
            self.assertEqual(len(edges), 5302)
            self.assertEqual(contexts["source_form_family"].nunique(), 7)
            self.assertEqual(int(contexts["source_is_discarded_flag"].sum()), 0)
            self.assertEqual(int(contexts["operating_primitive_created_flag"].sum()), 0)
            self.assertEqual(int(contexts["backtest_eligible_flag"].sum()), 0)
            self.assertEqual(int(guardrail["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")


if __name__ == "__main__":
    unittest.main()
