from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task742_pragmatic_economic_meaning_layer import build_task742
from src.backtest.pragmatic_economic_meaning_layer import interpret_row


class Task742PragmaticEconomicMeaningLayerTest(unittest.TestCase):
    def test_financing_growth_uses_available_primitives_without_hard_blocking(self) -> None:
        row = pd.Series({"source_circuit": "credit_financing"})
        primitive = {
            "principal_amount": 750000000,
            "growth_use_language_flag": 1,
            "instrument_convertible_flag": 0,
            "instrument_warrant_flag": 0,
        }
        denominators = {"market_cap_proxy": None}
        comparators = {"principal_pct_of_cash": 0.25, "principal_pct_of_debt": 0.5, "principal_pct_of_market_cap": None}
        availability = {"has_task740_primitive": True, "has_raw_text_path": True}
        timing = {"no_future_data_used": True}

        result = interpret_row(row, primitive, denominators, comparators, availability, timing)

        self.assertEqual(result["interpretation_state"], "financing_growth_funding_size_known")
        self.assertEqual(result["economic_direction_hint"], "positive")
        self.assertFalse(result["hard_blocker_flags"])
        self.assertIn("size_known_but_market_scale_unknown", result["soft_uncertainty_flags"])

    def test_form4_planned_sale_is_context_not_blanket_negative(self) -> None:
        row = pd.Series({"source_circuit": "form4_insider_behavior"})
        primitive = {
            "open_market_sale_flag": 1,
            "planned_10b5_1_flag": 1,
            "award_grant_flag": 0,
            "option_exercise_flag": 0,
        }
        denominators = {"market_cap_proxy": None}
        comparators = {"shares_changed_pct_of_ownership_after": 0.1, "shares_changed_pct_of_shares_outstanding": None}
        availability = {"has_task740_primitive": True, "has_raw_text_path": True}
        timing = {"no_future_data_used": True}

        result = interpret_row(row, primitive, denominators, comparators, availability, timing)

        self.assertEqual(result["interpretation_state"], "form4_sale_plan_or_compensation_context")
        self.assertEqual(result["economic_direction_hint"], "neutral")
        self.assertFalse(result["hard_blocker_flags"])

    def test_task742_build_outputs_review_only_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task742(out_dir=out_dir)

            for filename in [
                "task742_pragmatic_economic_meaning_packets.csv",
                "task742_pragmatic_economic_meaning_packets.jsonl",
                "task742_quality_metrics.csv",
                "task742_interpretation_distribution.csv",
                "task742_blocker_reclassification.csv",
                "task742_guardrail.csv",
                "task742_gpt_review_summary.csv",
                "task_742_decision.csv",
                "task_742_pass_fail_matrix.csv",
                "task_742_pragmatic_economic_meaning_layer.md",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            packets = artifacts["packets"]
            self.assertEqual(len(packets), 3443)
            self.assertGreater(int(packets["relation_ready_flag"].sum()), 0)
            self.assertIn("directional", set(packets["relation_ready_tier"]))
            self.assertIn("structural_mixed", set(packets["relation_ready_tier"]))
            self.assertIn("context_only", set(packets["relation_ready_tier"]))
            self.assertIn("not_ready", set(packets["relation_ready_tier"]))
            self.assertEqual(
                int(
                    packets[
                        packets["economic_direction_hint"].isin({"neutral", "unknown"})
                        & packets["can_create_directional_edge_flag"].ne(0)
                    ].shape[0]
                ),
                0,
            )
            self.assertEqual(int(packets["direction_hint_trade_instruction_flag"].sum()), 0)
            self.assertEqual(int(packets["asof_change_inference_forbidden_flag"].min()), 1)
            self.assertEqual(int(artifacts["guardrail"]["pass_flag"].min()), 1)
            self.assertEqual(int(packets["trade_output_flag"].sum()), 0)
            self.assertEqual(int(packets["score_output_flag"].sum()), 0)
            self.assertEqual(artifacts["decision"].iloc[0]["backtest_permission"], "FAIL")


if __name__ == "__main__":
    unittest.main()
