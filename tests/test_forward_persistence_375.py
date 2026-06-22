from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.analysis_structural_breakout_forward_persistence_375 import main as report_main
from backtest.build_forward_persistence_375 import (
    build_forward_persistence_375,
    write_forward_persistence_375,
)


def _base_candidate() -> dict:
    return {
        "symbol": "AAPL",
        "entry_ts": "2026-01-05T14:30:00Z",
        "prediction_cutoff_ts": "2026-01-05T14:30:00Z",
        "current_split": "anchored_oos",
        "forward_only_flag": True,
        "feature_set_version": "task374-forward-v1",
        "session_timing_bucket": "mid_session",
        "relative_volume_percentile": 0.92,
        "price_vs_session_vwap_at_breakout": 0.02,
        "vwap_deviation_at_breakout": 0.01,
        "vwap_slope_prebreak": 0.005,
        "breakout_bar_close_location": 0.85,
        "market_breadth_state": "broad",
        "gap_environment_state": "calm",
        "sector_leadership_state": "broad_led",
        "same_day_candidate_count": 2,
        "same_day_sector_candidate_count": 1,
        "dispersion_20d": 0.15,
        "mean_pairwise_corr": 0.20,
        "semis_concentration_ratio": 0.10,
        "ker": None,
        "volume_percentile": None,
        "daily_bias": "STRONG_BULLISH",
        "context_quality_score": 0.82,
        "risk_pressure_score": 0.20,
        "forward_breakout_score": 0.78,
        "forward_breakout_bucket": "high_quality",
        "forward_high_quality_flag": 1,
        "forward_weak_flag": 0,
        "first_30m_flag": 0,
        "tech_led_narrow_flag": 0,
    }


def _prediction_candidates_fixture() -> pd.DataFrame:
    base = _base_candidate()
    rows = [
        {"trade_id": "persist_good", **base},
        {"trade_id": "add_good", **base, "symbol": "MSFT", "entry_ts": "2026-01-06T14:30:00Z", "prediction_cutoff_ts": "2026-01-06T14:30:00Z"},
        {"trade_id": "scale_good", **base, "symbol": "NVDA", "entry_ts": "2026-01-07T14:30:00Z", "prediction_cutoff_ts": "2026-01-07T14:30:00Z", "forward_breakout_bucket": "mixed_quality"},
        {"trade_id": "late_fail", **base},
        {"trade_id": "immediate_invalid", **base, "symbol": "META", "entry_ts": "2026-01-08T14:30:00Z", "prediction_cutoff_ts": "2026-01-08T14:30:00Z"},
        {
            "trade_id": "weak_no_follow",
            **base,
            "symbol": "TSLA",
            "entry_ts": "2026-01-09T14:30:00Z",
            "prediction_cutoff_ts": "2026-01-09T14:30:00Z",
            "forward_breakout_score": 0.40,
            "forward_breakout_bucket": "fragile_candidate",
            "forward_high_quality_flag": 0,
            "forward_weak_flag": 1,
            "context_quality_score": 0.45,
            "risk_pressure_score": 0.65,
        },
    ]
    frame = pd.DataFrame(rows)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True)
    frame["prediction_cutoff_ts"] = pd.to_datetime(frame["prediction_cutoff_ts"], utc=True)
    return frame


def _lifecycle_panel_fixture() -> pd.DataFrame:
    rows = [
        {
            "raw_trade_id": "persist_good",
            "current_split": "anchored_oos",
            "evaluation_scope": "full_period",
            "event_count": 3,
            "persistence_depth": 1,
            "add_depth": 0,
            "scale_depth": 0,
            "source_linked_flag": 1,
            "fragile_transition_flag": 0,
            "invalidated_flag": 0,
            "add_confirmed_flag": 0,
            "scale_up_flag": 0,
            "persistence_confirmed_flag": 1,
            "lineage_quality": "source_linked",
            "persistence_duration_minutes": 20.0,
            "realized_R": 1.2,
        },
        {
            "raw_trade_id": "add_good",
            "current_split": "anchored_oos",
            "evaluation_scope": "full_period",
            "event_count": 3,
            "persistence_depth": 0,
            "add_depth": 1,
            "scale_depth": 0,
            "source_linked_flag": 1,
            "fragile_transition_flag": 0,
            "invalidated_flag": 0,
            "add_confirmed_flag": 1,
            "scale_up_flag": 0,
            "persistence_confirmed_flag": 0,
            "lineage_quality": "source_linked",
            "persistence_duration_minutes": 10.0,
            "realized_R": 1.4,
        },
        {
            "raw_trade_id": "scale_good",
            "current_split": "anchored_oos",
            "evaluation_scope": "full_period",
            "event_count": 3,
            "persistence_depth": 0,
            "add_depth": 0,
            "scale_depth": 1,
            "source_linked_flag": 1,
            "fragile_transition_flag": 0,
            "invalidated_flag": 0,
            "add_confirmed_flag": 0,
            "scale_up_flag": 1,
            "persistence_confirmed_flag": 0,
            "lineage_quality": "source_linked",
            "persistence_duration_minutes": 10.0,
            "realized_R": 1.1,
        },
        {
            "raw_trade_id": "late_fail",
            "current_split": "anchored_oos",
            "evaluation_scope": "full_period",
            "event_count": 2,
            "persistence_depth": 0,
            "add_depth": 0,
            "scale_depth": 0,
            "source_linked_flag": 1,
            "fragile_transition_flag": 1,
            "invalidated_flag": 1,
            "add_confirmed_flag": 0,
            "scale_up_flag": 0,
            "persistence_confirmed_flag": 0,
            "lineage_quality": "source_linked",
            "persistence_duration_minutes": 12.0,
            "realized_R": -1.0,
        },
        {
            "raw_trade_id": "immediate_invalid",
            "current_split": "anchored_oos",
            "evaluation_scope": "full_period",
            "event_count": 1,
            "persistence_depth": 0,
            "add_depth": 0,
            "scale_depth": 0,
            "source_linked_flag": 1,
            "fragile_transition_flag": 0,
            "invalidated_flag": 1,
            "add_confirmed_flag": 0,
            "scale_up_flag": 0,
            "persistence_confirmed_flag": 0,
            "lineage_quality": "source_linked",
            "persistence_duration_minutes": 0.0,
            "realized_R": -0.2,
        },
        {
            "raw_trade_id": "weak_no_follow",
            "current_split": "anchored_oos",
            "evaluation_scope": "full_period",
            "event_count": 2,
            "persistence_depth": 0,
            "add_depth": 0,
            "scale_depth": 0,
            "source_linked_flag": 1,
            "fragile_transition_flag": 0,
            "invalidated_flag": 0,
            "add_confirmed_flag": 0,
            "scale_up_flag": 0,
            "persistence_confirmed_flag": 0,
            "lineage_quality": "source_linked",
            "persistence_duration_minutes": 0.0,
            "realized_R": -0.1,
        },
    ]
    return pd.DataFrame(rows).rename(columns={"raw_trade_id": "trade_id"})


class ForwardPersistence375Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        return build_forward_persistence_375(
            prediction_candidates_df=_prediction_candidates_fixture(),
            evaluation_panel_df=_lifecycle_panel_fixture(),
        )

    def test_target_labeling_marks_persistence_add_or_scale_positive(self) -> None:
        labels = self._build_fixture_artifacts().forward_persistence_labels.set_index("trade_id")

        self.assertEqual(int(labels.loc["persist_good", "forward_persistence_target"]), 1)
        self.assertEqual(int(labels.loc["add_good", "forward_persistence_target"]), 1)
        self.assertEqual(int(labels.loc["scale_good", "forward_persistence_target"]), 1)
        self.assertEqual(int(labels.loc["late_fail", "forward_persistence_target"]), 0)
        self.assertEqual(int(labels.loc["weak_no_follow", "forward_persistence_target"]), 0)

        self.assertEqual(str(labels.loc["persist_good", "target_reason"]), "persistence_confirmed")
        self.assertEqual(str(labels.loc["add_good", "target_reason"]), "add_confirmed")
        self.assertEqual(str(labels.loc["scale_good", "target_reason"]), "scale_up")

    def test_immediate_invalidation_is_excluded_from_training_labels(self) -> None:
        artifacts = self._build_fixture_artifacts()
        labels = artifacts.forward_persistence_labels.set_index("trade_id")
        train = artifacts.forward_persistence_training_frame

        self.assertEqual(int(labels.loc["immediate_invalid", "excluded_from_training"]), 1)
        self.assertEqual(str(labels.loc["immediate_invalid", "exclusion_reason"]), "immediate_invalidation")
        self.assertNotIn("immediate_invalid", set(train["trade_id"].astype(str)))

        self.assertIn("late_fail", set(train["trade_id"].astype(str)))
        self.assertEqual(int(train.set_index("trade_id").loc["late_fail", "forward_persistence_target"]), 0)

    def test_prediction_frame_has_no_outcome_or_label_columns(self) -> None:
        artifacts = self._build_fixture_artifacts()
        prediction = artifacts.forward_persistence_prediction_frame

        for forbidden in (
            "forward_persistence_target",
            "target_reason",
            "excluded_from_training",
            "exclusion_reason",
            "realized_R",
            "invalidated_flag",
            "add_confirmed_flag",
            "scale_up_flag",
            "persistence_confirmed_flag",
            "persistence_duration_minutes",
            "event_count",
            "lineage_quality",
        ):
            self.assertNotIn(forbidden, prediction.columns)

        self.assertIn("trade_id", prediction.columns)
        self.assertIn("prediction_cutoff_ts", prediction.columns)
        self.assertIn("forward_breakout_score", prediction.columns)
        self.assertTrue(prediction["forward_only_flag"].astype(bool).all())
        self.assertIn("forward_persistence_target", artifacts.forward_persistence_labels.columns)
        self.assertIn("invalidated_flag", artifacts.forward_persistence_evaluation_panel.columns)

    def test_leakage_audit_blocks_lifecycle_and_realized_outcomes(self) -> None:
        audit = self._build_fixture_artifacts().persistence_leakage_audit.set_index("feature_name")

        for feature in (
            "realized_R",
            "invalidated_flag",
            "add_confirmed_flag",
            "scale_up_flag",
            "persistence_confirmed_flag",
            "persistence_duration_minutes",
            "event_count",
        ):
            self.assertIn(feature, audit.index)
            self.assertFalse(bool(audit.loc[feature, "allowed_for_prediction"]))
            self.assertIn(
                str(audit.loc[feature, "temporal_classification"]),
                {"outcome", "lifecycle_outcome", "post_entry"},
            )

        self.assertTrue(bool(audit.loc["forward_breakout_score", "allowed_for_prediction"]))
        self.assertEqual(str(audit.loc["forward_breakout_score", "temporal_classification"]), "entry_time")

    def test_paired_future_outcomes_do_not_change_prediction_inputs(self) -> None:
        prediction = self._build_fixture_artifacts().forward_persistence_prediction_frame.set_index("trade_id")

        for column in (
            "forward_breakout_score",
            "forward_breakout_bucket",
            "context_quality_score",
            "risk_pressure_score",
            "session_timing_bucket",
            "market_breadth_state",
            "sector_leadership_state",
        ):
            self.assertEqual(prediction.loc["persist_good", column], prediction.loc["late_fail", column])

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_forward_persistence_375(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_forward_persistence_375.build_forward_persistence_375",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["forward_persistence_375", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "forward_persistence_prediction_frame.csv",
                "forward_persistence_labels.csv",
                "forward_persistence_training_frame.csv",
                "forward_persistence_evaluation_panel.csv",
                "persistence_leakage_audit.csv",
                "persistence_target_summary.csv",
                "task_375_forward_persistence.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)

            report_text = (out_dir / "task_375_forward_persistence.md").read_text(encoding="utf-8-sig")
            self.assertIn("Immediate invalidation exclusions", report_text)
            self.assertIn("Leakage Audit", report_text)
            self.assertRegex(report_text, r"Final Task 375 verdict: `(COMPLETE_PASS|NOT_YET)`")


if __name__ == "__main__":
    unittest.main()
