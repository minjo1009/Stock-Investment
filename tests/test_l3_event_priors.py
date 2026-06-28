from __future__ import annotations

import unittest

from src.brain.l3.contracts import L3CalibrationStatus
from src.brain.l3.event_priors import event_prior_score, load_event_type_priors_config


class L3EventPriorsTest(unittest.TestCase):
    def test_configured_event_prior_is_not_calibrated_probability(self) -> None:
        priors = load_event_type_priors_config()
        prior = priors["guidance_raise_with_margin_language"]
        self.assertEqual(prior.base_prior_score, 0.65)
        self.assertEqual(prior.calibration_status, L3CalibrationStatus.NOT_CALIBRATED)
        self.assertEqual(event_prior_score("guidance_raise_with_margin_language", config=priors), 0.65)


if __name__ == "__main__":
    unittest.main()
