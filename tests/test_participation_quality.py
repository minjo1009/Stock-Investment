from __future__ import annotations

import unittest

from src.risk.participation_quality import (
    ParticipationQualityInputs,
    evaluate_participation_quality,
)


class TestParticipationQuality(unittest.TestCase):
    def test_healthy_expansion_classification(self) -> None:
        decision = evaluate_participation_quality(
            ParticipationQualityInputs(
                breadth_change=0.8,
                breadth_participation_ratio=0.8,
                liquidity_change=0.5,
                dip_absorption_score=0.8,
                reversal_stability_score=0.8,
                factor_concentration_score=0.2,
                same_day_signal_crowding=0.2,
                volatility_expansion_score=0.5,
                continuation_persistence_score=0.8,
                session_timing_score=0.8,
            )
        )
        self.assertEqual(decision.quality_label, "HEALTHY_EXPANSION")

    def test_fragile_crowding_classification(self) -> None:
        decision = evaluate_participation_quality(
            ParticipationQualityInputs(
                breadth_change=-0.8,
                breadth_participation_ratio=0.2,
                liquidity_change=-0.5,
                dip_absorption_score=0.2,
                reversal_stability_score=0.2,
                factor_concentration_score=0.9,
                same_day_signal_crowding=0.9,
                volatility_expansion_score=0.9,
                continuation_persistence_score=0.2,
                session_timing_score=0.2,
            )
        )
        self.assertEqual(decision.quality_label, "FRAGILE_CROWDING")

    def test_neutral_participation_classification(self) -> None:
        decision = evaluate_participation_quality(
            ParticipationQualityInputs(
                breadth_change=0.1,
                breadth_participation_ratio=0.5,
                liquidity_change=0.0,
                dip_absorption_score=0.5,
                reversal_stability_score=0.5,
                factor_concentration_score=0.5,
                same_day_signal_crowding=0.5,
                volatility_expansion_score=0.5,
                continuation_persistence_score=0.5,
                session_timing_score=0.5,
            )
        )
        self.assertEqual(decision.quality_label, "NEUTRAL_PARTICIPATION")

    def test_unknown_when_insufficient_inputs(self) -> None:
        decision = evaluate_participation_quality(ParticipationQualityInputs())
        self.assertEqual(decision.quality_label, "UNKNOWN")

    def test_missing_fields_do_not_force_fragile(self) -> None:
        decision = evaluate_participation_quality(
            ParticipationQualityInputs(
                breadth_change=0.4,
                factor_concentration_score=0.2,
                same_day_signal_crowding=0.2,
            )
        )
        self.assertNotEqual(decision.quality_label, "FRAGILE_CROWDING")


if __name__ == "__main__":
    unittest.main()
