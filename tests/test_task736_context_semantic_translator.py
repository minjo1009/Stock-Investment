from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task736_context_semantic_translator import build_task736
from src.backtest.context_semantic_translator import translate_context


def context_row(**overrides: object) -> pd.Series:
    row = {
        "event_id": "E1",
        "lifecycle_id": "L1",
        "symbol": "TEST",
        "theme_id": "theme",
        "entry_ts": "2024-01-02T14:30:00Z",
        "split_name": "unit",
        "source_form_family": "form4_insider",
        "context_type": "InsiderBehaviorContext",
        "primitive_fields_json": "{}",
        "interpretation_states": "",
    }
    row.update(overrides)
    return pd.Series(row)


class Task736ContextSemanticTranslatorTest(unittest.TestCase):
    def test_insider_open_market_buy_is_constructive_modifier_not_trade(self) -> None:
        result = translate_context(
            context_row(
                primitive_fields_json='{"open_market_buy_flag":1,"director_or_officer_language_present":1}',
                interpretation_states="insider_open_market_buy_observed|executive_or_director_signal_present",
            )
        )

        self.assertEqual(result["semantic_state"], "open_market_buy_constructive_modifier")
        self.assertEqual(result["semantic_polarity"], "constructive")
        self.assertEqual(result["edge_effect"], "confidence_modifier")
        self.assertEqual(result["buy_sell_signal_created_flag"], 0)
        self.assertEqual(result["backtest_eligible_flag"], 0)

    def test_financing_growth_with_dilution_is_mixed(self) -> None:
        result = translate_context(
            context_row(
                source_form_family="financing_8k",
                context_type="CreditFinancingContext",
                primitive_fields_json='{"growth_use_of_proceeds_flag":1,"conversion_feature_flag":1}',
                interpretation_states="growth_funding_possible|dilution_overhang_present|convertible_or_warrant_overhang_present",
            )
        )

        self.assertEqual(result["semantic_state"], "growth_funding_with_dilution_mixed")
        self.assertEqual(result["semantic_polarity"], "mixed")
        self.assertIn("dilution_overhang", result["transmission_channel"])
        self.assertEqual(result["operating_connection_supported_flag"], 0)

    def test_generic_mna_is_conditional_modifier(self) -> None:
        result = translate_context(
            context_row(
                source_form_family="generic_8k",
                context_type="Generic8KClassificationContext",
                primitive_fields_json='{"agreement_family_state":"strategic_mna_context","operating_transmission_state":"no_operating_transmission"}',
                interpretation_states="generic_8k_strategic_mna_context|generic_8k_no_operating_transmission",
            )
        )

        self.assertEqual(result["semantic_state"], "mna_non_operating_review_required")
        self.assertEqual(result["semantic_polarity"], "conditional")
        self.assertIn("integration_risk", result["transmission_channel"])
        self.assertEqual(result["actionability_created_flag"], 0)

    def test_unknown_missing_is_not_adverse(self) -> None:
        result = translate_context(
            context_row(
                source_form_family="generic_8k",
                context_type="Generic8KClassificationContext",
                primitive_fields_json='{"agreement_family_state":"unclassified_generic_8k_context"}',
                interpretation_states="generic_8k_unclassified",
            )
        )

        self.assertIn("unknown", result["semantic_state"])
        self.assertEqual(result["semantic_polarity"], "unknown")

    def test_task736_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task736(out_dir=out_dir)

            for filename in [
                "task736_semantic_translation.csv",
                "task736_semantic_state_distribution.csv",
                "task736_transmission_channel_distribution.csv",
                "task736_layer_modifier_edges.csv",
                "task736_guardrail.csv",
                "task736_gpt_review_summary.csv",
                "task_736_decision.csv",
                "task_736_pass_fail_matrix.csv",
                "task_736_context_semantic_translator.md",
                "task736_semantic_translation.jsonl",
                "task736_layer_modifier_edges.jsonl",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            translations = artifacts["translations"]
            guardrail = artifacts["guardrail"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(len(translations), 5302)
            self.assertGreaterEqual(translations["semantic_polarity"].nunique(), 4)
            self.assertEqual(int(translations["buy_sell_signal_created_flag"].sum()), 0)
            self.assertEqual(int(translations["actionability_created_flag"].sum()), 0)
            self.assertEqual(int(translations["backtest_eligible_flag"].sum()), 0)
            self.assertEqual(int(guardrail["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")


if __name__ == "__main__":
    unittest.main()
