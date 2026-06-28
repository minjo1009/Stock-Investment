from __future__ import annotations

import unittest

from src.brain.l3.confidence import build_static_l3_confidence, map_confidence_band_to_static_weight
from src.brain.l3.contracts import L3CalibrationStatus, L3Confidence


class L3ConfidenceComponentsTest(unittest.TestCase):
    def test_medium_maps_to_static_weight_not_probability(self) -> None:
        confidence = build_static_l3_confidence("medium")
        self.assertEqual(map_confidence_band_to_static_weight("medium"), 0.60)
        self.assertEqual(confidence.static_weight, 0.60)
        self.assertEqual(confidence.calibration_status, L3CalibrationStatus.NOT_CALIBRATED)
        self.assertIsNone(confidence.calibrated_probability)

    def test_uncalibrated_confidence_rejects_probability(self) -> None:
        with self.assertRaises(ValueError):
            L3Confidence(
                raw_band="medium",
                static_weight=0.60,
                calibrated_probability=0.60,
                calibration_status=L3CalibrationStatus.NOT_CALIBRATED,
                calibration_version="UNAVAILABLE",
                sample_size=None,
                brier_score=None,
                calibration_error=None,
            )


if __name__ == "__main__":
    unittest.main()
