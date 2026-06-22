from __future__ import annotations

import unittest

from src.backtest.build_task546_microstructure_live_capture_layer import (
    build_microstructure_feature_contract,
    build_microstructure_live_source_contract,
    build_source_availability_audit,
)


class Task546MicrostructureFeatureContractTest(unittest.TestCase):
    def test_features_do_not_use_outcomes_and_missing_sources_are_unavailable(self) -> None:
        audit = build_source_availability_audit(build_microstructure_live_source_contract())
        features = build_microstructure_feature_contract(audit)
        self.assertEqual(int(features["outcome_or_fill_after_field_used_flag"].max()), 0)
        self.assertEqual(int(features["approximation_allowed_flag"].max()), 0)
        self.assertEqual(int(features["missing_source_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
