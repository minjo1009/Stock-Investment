from __future__ import annotations

import unittest

from src.backtest.canonical_continuation_multifactor_filter import (
    evaluate_multifactor_continuation_filter,
)


class TestCanonicalContinuationMultiFactorFilter401(unittest.TestCase):
    def test_scorecard_accepts_clean_positive_selection_snapshot(self) -> None:
        decision = evaluate_multifactor_continuation_filter(_features())

        self.assertEqual(decision.bucket, "ALLOW")
        self.assertEqual(decision.decision_action, "ENTRY")
        self.assertFalse(decision.hard_gate_fail)
        self.assertEqual(decision.policy_version, "scorecard_v1_65_35")

    def test_blocked_outcome_fields_are_rejected(self) -> None:
        features = _features()
        features["return_from_entry"] = 0.05

        with self.assertRaises(ValueError):
            evaluate_multifactor_continuation_filter(features)

    def test_hard_gate_overrides_high_score(self) -> None:
        features = _features()
        features["feed"] = "iex"

        decision = evaluate_multifactor_continuation_filter(features)

        self.assertEqual(decision.bucket, "REJECT")
        self.assertTrue(decision.hard_gate_fail)
        self.assertIn("INVALID_FEED_NOT_SIP", decision.reason_codes)

    def test_policy_variants_are_deterministic(self) -> None:
        first = evaluate_multifactor_continuation_filter(_features(), policy_version="scorecard_v1_55_45")
        second = evaluate_multifactor_continuation_filter(_features(), policy_version="scorecard_v1_55_45")

        self.assertEqual(first.final_score_q, second.final_score_q)
        self.assertEqual(first.source_hash, second.source_hash)


def _features() -> dict:
    return {
        "feed": "sip",
        "adjustment": "raw",
        "asof": "-",
        "session_type": "regular",
        "quote_status": "unavailable",
        "luld_status": "unavailable",
        "forward_live_breadth_positive_rate": 0.72,
        "forward_live_avg_symbol_return": 0.012,
        "forward_live_liquidity_ratio": 1.2,
        "forward_live_theme_return": 0.02,
        "forward_live_theme_rank": 1,
        "forward_live_theme_count": 5,
        "forward_live_theme_breadth_positive_rate": 0.8,
        "forward_live_theme_leadership_regime": "theme_leader",
        "entry_return_so_far": 0.025,
        "entry_momentum_2bar": 0.015,
        "entry_range_pos": 0.85,
        "entry_range_exp_ratio": 1.2,
        "symbol_liquidity_ratio": 1.3,
        "estimated_total_cost": 0.004,
        "cost_to_range": 0.12,
        "role": "leader",
        "entry_hour": 15,
    }


if __name__ == "__main__":
    unittest.main()
