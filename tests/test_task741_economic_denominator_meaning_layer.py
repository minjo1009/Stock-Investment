from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.backtest.build_task741_economic_denominator_meaning_layer import build_task741
from src.backtest.economic_denominator_meaning_layer import (
    attach_comparators,
    companyfacts_snapshot,
    resolve_meaning_state,
)


class Task741EconomicDenominatorMeaningLayerTest(unittest.TestCase):
    def test_companyfacts_snapshot_is_asof_and_has_core_denominators(self) -> None:
        snapshot = companyfacts_snapshot("TER", datetime(2025, 1, 1, tzinfo=timezone.utc), {})

        self.assertTrue(snapshot["path"].endswith(".json"))
        self.assertIsNotNone(snapshot["shares_outstanding"])
        self.assertIsNotNone(snapshot["cash"])
        self.assertIsNotNone(snapshot["revenue"])

    def test_form4_comparator_uses_source_denominator_without_trade_signal(self) -> None:
        primitive = {"shares_changed": 1000, "ownership_after": 10000}
        companyfacts = {"shares_outstanding": 1000000, "cash": None, "debt": None}
        price = {"close": 10}
        comparators = attach_comparators(pd.Series(dtype=object), primitive, companyfacts, price)

        self.assertEqual(comparators["shares_changed_pct_of_ownership_after"], 0.1)
        self.assertEqual(comparators["shares_changed_pct_of_shares_outstanding"], 0.001)

    def test_financing_meaning_never_becomes_bullish_or_bearish(self) -> None:
        resolver = pd.Series({"source_circuit": "credit_financing", "resolver_state": "growth_funding_review"})
        primitive = {"principal_amount": 100, "instrument_convertible_flag": 0, "instrument_warrant_flag": 0}
        denominators = {"market_cap_proxy": 1000, "cash": 200, "debt": 50}
        comparators = {}
        availability = {"has_free_float": False}

        meaning, missing = resolve_meaning_state(resolver, primitive, denominators, comparators, availability)

        self.assertEqual(meaning, "financing_principal_market_cap_context")
        self.assertNotIn("bullish", meaning)
        self.assertNotIn("bearish", meaning)
        self.assertFalse(missing)

    def test_task741_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task741(out_dir=out_dir)

            for filename in [
                "task741_economic_meaning_packets.csv",
                "task741_economic_meaning_packets.jsonl",
                "task741_missing_source_blockers.csv",
                "task741_missing_source_blockers.jsonl",
                "task741_quality_metrics.csv",
                "task741_meaning_distribution.csv",
                "task741_source_availability_summary.csv",
                "task741_blocker_summary.csv",
                "task741_coverage_report.csv",
                "task741_guardrail.csv",
                "task741_gpt_review_summary.csv",
                "task_741_decision.csv",
                "task_741_pass_fail_matrix.csv",
                "task_741_economic_denominator_meaning_layer.md",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            self.assertEqual(len(artifacts["packets"]), 3443)
            self.assertGreater(len(artifacts["blockers"]), 0)
            self.assertEqual(int(artifacts["guardrail"]["pass_flag"].min()), 1)
            self.assertEqual(artifacts["decision"].iloc[0]["backtest_permission"], "FAIL")
            self.assertEqual(int(artifacts["packets"]["trade_output_flag"].sum()), 0)
            self.assertEqual(int(artifacts["packets"]["score_output_flag"].sum()), 0)


if __name__ == "__main__":
    unittest.main()
