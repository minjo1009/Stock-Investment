from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task740_engineering_high_resolver_completion import build_task740
from src.backtest.engineering_high_semantic_completion import (
    complete_engineering_high_requirement,
    extract_financing_primitives,
    extract_form4_primitives,
    extract_generic_8k_primitives,
)


class Task740EngineeringHighResolverCompletionTest(unittest.TestCase):
    def test_form4_extractor_splits_transaction_code_and_role(self) -> None:
        text = """
        <span class="FormData">X</span> Director
        <transactionCode>P</transactionCode>
        <transactionShares><value>1200</value></transactionShares>
        <sharesOwnedFollowingTransaction><value>5000</value></sharesOwnedFollowingTransaction>
        12/04/2023
        """
        primitives = extract_form4_primitives(text)

        self.assertEqual(primitives["primary_transaction_code"], "P")
        self.assertEqual(primitives["open_market_buy_flag"], 1)
        self.assertEqual(primitives["insider_director_flag"], 1)
        self.assertEqual(primitives["shares_changed_present_flag"], 1)

    def test_financing_extractor_keeps_terms_review_not_trade_ready(self) -> None:
        text = "The Company entered into a Credit Agreement for $500 million. Loans bear interest at SOFR. Proceeds may be used for working capital and general corporate purposes."
        primitives = extract_financing_primitives(text)

        self.assertEqual(primitives["instrument_credit_agreement_flag"], 1)
        self.assertEqual(primitives["principal_amount_present_flag"], 1)
        self.assertEqual(primitives["coupon_or_interest_language_present_flag"], 1)
        self.assertEqual(primitives["liquidity_rescue_language_flag"], 1)

    def test_generic_8k_item101_does_not_create_operating_supported(self) -> None:
        text = "Item 1.01 Entry into a Material Definitive Agreement. The Company entered into a credit agreement."
        primitives = extract_generic_8k_primitives(text)

        self.assertEqual(primitives["item_101_flag"], 1)
        self.assertEqual(primitives["financing_flag"], 1)
        self.assertEqual(primitives["operating_supported_flag"], 0)

    def test_requirement_completion_outputs_review_only_flags(self) -> None:
        row = pd.Series(
            {
                "lifecycle_id": "L1",
                "bundle_id": "bundle::L1",
                "source_event_id": "E1",
                "symbol": "TEST",
                "source_circuit": "credit_financing",
                "requirement_family": "financing_terms_enrichment",
            }
        )
        event = pd.Series(
            {
                "raw_text_path": "",
                "content_interpretation_evidence_span": "The Company entered into a convertible note purchase agreement with warrants for $100 million proceeds.",
            }
        )

        primitive, resolver, blockers = complete_engineering_high_requirement(row, event)

        self.assertEqual(primitive["research_only_flag"], 1)
        self.assertEqual(resolver["buy_sell_signal_created_flag"], 0)
        self.assertEqual(resolver["backtest_eligible_flag"], 0)
        self.assertEqual(resolver["resolver_state"], "dilution_overhang_review")
        self.assertTrue(blockers)

    def test_task740_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task740(out_dir=out_dir)

            for filename in [
                "task740_extracted_primitives.csv",
                "task740_extracted_primitives.jsonl",
                "task740_resolver_outputs.csv",
                "task740_resolver_outputs.jsonl",
                "task740_unresolved_join_blockers.csv",
                "task740_unresolved_join_blockers.jsonl",
                "task740_quality_metrics.csv",
                "task740_resolver_distribution.csv",
                "task740_completion_distribution.csv",
                "task740_coverage_report.csv",
                "task740_guardrail.csv",
                "task740_gpt_review_summary.csv",
                "task_740_decision.csv",
                "task_740_pass_fail_matrix.csv",
                "task_740_engineering_high_resolver_completion.md",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            self.assertEqual(len(artifacts["high_trace"]), 3443)
            self.assertEqual(len(artifacts["primitives"]), 3443)
            self.assertEqual(len(artifacts["resolvers"]), 3443)
            self.assertGreater(len(artifacts["blockers"]), 0)
            self.assertEqual(int(artifacts["guardrail"]["pass_flag"].min()), 1)
            self.assertEqual(artifacts["decision"].iloc[0]["backtest_permission"], "FAIL")


if __name__ == "__main__":
    unittest.main()
