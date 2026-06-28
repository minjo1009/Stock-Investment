from __future__ import annotations

import unittest

from src.brain.contracts import MeaningDirection
from src.brain.l3.adapters.task742_rule_adapter import adapt_task742_rule_inputs_to_l3_meaning
from src.brain.l3.task742_rules import interpret_task742_economic_context


class L3Task742RuleMigrationTest(unittest.TestCase):
    def test_form4_open_market_buy_matches_recovered_rule(self) -> None:
        interpretation = interpret_task742_economic_context(
            {"source_circuit": "form4_insider_behavior"},
            primitive={"open_market_buy_flag": 1},
            denominators={"estimated_transaction_value": 1000000, "market_cap_proxy": 100000000},
        )
        self.assertEqual(interpretation.interpretation_state, "form4_open_market_buy_economic_hint")
        self.assertEqual(interpretation.economic_direction_hint, "positive")
        self.assertEqual(interpretation.confidence_band, "medium")
        self.assertEqual(interpretation.relation_ready_tier, "directional")
        self.assertEqual(interpretation.trade_output_flag, 0)

    def test_financing_dilution_overhang_matches_recovered_rule(self) -> None:
        interpretation = interpret_task742_economic_context(
            {"source_circuit": "credit_financing"},
            primitive={"principal_amount": 10000000, "instrument_warrant_flag": 1},
            comparators={"principal_pct_of_market_cap": 0.05},
        )
        self.assertEqual(interpretation.interpretation_state, "financing_dilution_overhang_size_known")
        self.assertEqual(interpretation.economic_direction_hint, "negative")
        self.assertEqual(interpretation.confidence_band, "medium")

    def test_hard_blocker_stays_not_ready(self) -> None:
        interpretation = interpret_task742_economic_context(
            {"source_circuit": "financial_results_guidance"},
            primitive={"guidance_raise_flag": 1},
            availability={"has_task740_primitive": False, "has_raw_text_path": False},
        )
        self.assertEqual(interpretation.interpretation_state, "economic_context_unusable")
        self.assertEqual(interpretation.confidence_band, "insufficient")
        self.assertEqual(interpretation.relation_ready_tier, "not_ready")
        self.assertIn("primitive_missing", interpretation.hard_blocker_flags)

    def test_task742_rule_adapter_outputs_historical_diagnostic_l3(self) -> None:
        meaning = adapt_task742_rule_inputs_to_l3_meaning(
            {
                "source_circuit": "credit_financing",
                "source_event_id": "event-1",
                "symbol": "AAPL",
                "lifecycle_id": "life-1",
                "tradable_after_dt": "2026-06-01T10:00:00Z",
            },
            primitive={"principal_amount": 10000000, "instrument_warrant_flag": 1},
            comparators={"principal_pct_of_market_cap": 0.05},
        )
        self.assertEqual(meaning.direction, MeaningDirection.RISK)
        self.assertEqual(meaning.runtime_context, "HISTORICAL_RESEARCH")
        self.assertFalse(meaning.source_time_certified)
        self.assertEqual(meaning.trade_output_flag, 0)
        self.assertEqual(meaning.score_output_flag, 0)
        self.assertEqual(meaning.order_intent_flag, 0)


if __name__ == "__main__":
    unittest.main()
