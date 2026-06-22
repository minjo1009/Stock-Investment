from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_signal_strengthening_339 import (
    ENTRY_ONLY,
    IMMEDIATE_POST_BREAK,
    _breakout_subtype,
    _breakout_time_bucket,
    _final_decision,
    _score_signal_strength,
    _sector_group,
    _vwap_response,
)


class TestAnalysisStructuralBreakoutIntradaySignalStrengthening339(unittest.TestCase):
    def test_time_bucket_is_deterministic(self) -> None:
        self.assertEqual(_breakout_time_bucket("2026-01-05T14:35:00+00:00"), "early_session")
        self.assertEqual(_breakout_time_bucket("2026-01-05T17:00:00+00:00"), "mid_session")
        self.assertEqual(_breakout_time_bucket("2026-01-05T20:10:00+00:00"), "last_hour")

    def test_sector_group_mapping(self) -> None:
        self.assertEqual(_sector_group("semis"), "semis")
        self.assertEqual(_sector_group("software/internet"), "software_internet")
        self.assertEqual(_sector_group("other tech"), "others")

    def test_breakout_subtype_parsing(self) -> None:
        scenario = "RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE"
        self.assertEqual(_breakout_subtype(scenario), "RANGE_COMPRESSION|HIGH_TOUCH")

    def test_vwap_response_depends_on_window_mode(self) -> None:
        frame = pd.DataFrame(
            {
                "price_vs_session_vwap_at_breakout": [0.01, -0.02, 0.03],
                "vwap_reversion_flag_3bars": [0, 0, 1],
            }
        )
        entry = _vwap_response(frame, ENTRY_ONLY).tolist()
        post = _vwap_response(frame, IMMEDIATE_POST_BREAK).tolist()
        self.assertEqual(entry, ["vwap_hold", "vwap_reject", "vwap_hold"])
        self.assertEqual(post, ["vwap_hold", "vwap_reject", "vwap_reject"])

    def test_signal_strength_score_is_deterministic(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "oos_lift_vs_baseline": 0.1,
                    "expectancy_delta": 0.2,
                    "saved_loss": 5.0,
                    "missed_gain": 1.0,
                    "holdout_mean_lift": 0.05,
                    "holdout_positive_share": 0.8,
                    "symbol_concentration_share": 0.4,
                },
                {
                    "oos_lift_vs_baseline": -0.1,
                    "expectancy_delta": -0.2,
                    "saved_loss": 1.0,
                    "missed_gain": 4.0,
                    "holdout_mean_lift": -0.03,
                    "holdout_positive_share": 0.2,
                    "symbol_concentration_share": 0.9,
                },
            ]
        )
        scored = _score_signal_strength(df)
        self.assertGreater(float(scored.iloc[0]["signal_strength_score"]), float(scored.iloc[1]["signal_strength_score"]))

    def test_final_decision_detects_clear_subset(self) -> None:
        signal_df = pd.DataFrame(
            [
                {
                    "subset_id": "x",
                    "deployability": "live_eligible",
                    "oos_lift_vs_baseline": 0.1,
                    "expectancy_delta": 0.2,
                    "saved_loss": 4.0,
                    "missed_gain": 1.0,
                    "holdout_mean_lift": 0.02,
                    "symbol_concentration_share": 0.5,
                    "signal_strength_score": 0.8,
                }
            ]
        )
        decision = _final_decision(signal_df, pd.DataFrame())
        self.assertEqual(str(decision.iloc[0]["decision"]), "CLEAR_STRONG_SUBSET")


if __name__ == "__main__":
    unittest.main()
