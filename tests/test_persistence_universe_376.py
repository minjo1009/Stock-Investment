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

from backtest.analysis_structural_breakout_persistence_universe_376 import main as report_main
from backtest.build_persistence_universe_376 import (
    build_persistence_universe_376,
    write_persistence_universe_376,
)


def _base_candidate() -> dict:
    return {
        "symbol": "AAPL",
        "entry_ts": "2026-01-05T14:30:00Z",
        "prediction_cutoff_ts": "2026-01-05T14:30:00Z",
        "current_split": "train",
        "forward_only_flag": True,
        "feature_set_version": "task374-forward-v1",
        "session_timing_bucket": "mid_session",
        "relative_volume_percentile": 0.90,
        "price_vs_session_vwap_at_breakout": 0.02,
        "vwap_deviation_at_breakout": 0.01,
        "vwap_slope_prebreak": 0.004,
        "breakout_bar_close_location": 0.85,
        "market_breadth_state": "broad",
        "gap_environment_state": "calm",
        "sector_leadership_state": "broad_led",
        "same_day_candidate_count": 2,
        "same_day_sector_candidate_count": 1,
        "dispersion_20d": 0.12,
        "mean_pairwise_corr": 0.25,
        "semis_concentration_ratio": 0.33,
        "daily_bias": "STRONG_BULLISH",
        "context_quality_score": 0.82,
        "risk_pressure_score": 0.30,
        "forward_breakout_score": 0.76,
        "forward_breakout_bucket": "high_quality",
        "forward_high_quality_flag": 1,
        "forward_weak_flag": 0,
        "first_30m_flag": 0,
        "tech_led_narrow_flag": 0,
    }


def _candidates_fixture() -> pd.DataFrame:
    base = _base_candidate()
    rows = [
        {"trade_id": "train_expand_pos", **base},
        {"trade_id": "train_expand_neg", **base, "entry_ts": "2026-01-06T14:30:00Z", "prediction_cutoff_ts": "2026-01-06T14:30:00Z"},
        {"trade_id": "theme_only_weak", **base, "entry_ts": "2026-01-07T14:30:00Z", "prediction_cutoff_ts": "2026-01-07T14:30:00Z", "market_breadth_state": "narrow"},
        {"trade_id": "data_leader_only", **base, "symbol": "ORCL", "entry_ts": "2026-01-08T14:30:00Z", "prediction_cutoff_ts": "2026-01-08T14:30:00Z"},
        {"trade_id": "crowded_fragile", **base, "entry_ts": "2026-01-09T14:30:00Z", "prediction_cutoff_ts": "2026-01-09T14:30:00Z", "risk_pressure_score": 0.60},
        {"trade_id": "missing_lifecycle", **base, "entry_ts": "2026-01-10T14:30:00Z", "prediction_cutoff_ts": "2026-01-10T14:30:00Z"},
        {"trade_id": "anchored_immediate_invalid", **base, "current_split": "anchored_oos", "entry_ts": "2026-01-11T14:30:00Z", "prediction_cutoff_ts": "2026-01-11T14:30:00Z"},
    ]
    frame = pd.DataFrame(rows)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True)
    frame["prediction_cutoff_ts"] = pd.to_datetime(frame["prediction_cutoff_ts"], utc=True)
    return frame


def _persistence_prediction_fixture(candidates: pd.DataFrame) -> pd.DataFrame:
    frame = candidates[["trade_id"]].copy()
    frame["forward_persistence_score"] = 0.72
    frame["forward_persistence_bucket"] = "predicted_expandable"
    frame["predicted_persistence_flag"] = 1
    return frame


def _lifecycle_fixture() -> pd.DataFrame:
    rows = [
        {
            "raw_trade_id": "train_expand_pos",
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
            "identity_confidence": 0.9,
            "persistence_duration_minutes": 20.0,
            "realized_R": 1.0,
        },
        {
            "raw_trade_id": "train_expand_neg",
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
            "identity_confidence": 0.9,
            "persistence_duration_minutes": 0.0,
            "realized_R": -0.2,
        },
        {
            "raw_trade_id": "theme_only_weak",
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
            "identity_confidence": 0.8,
            "persistence_duration_minutes": 0.0,
            "realized_R": -0.1,
        },
        {
            "raw_trade_id": "data_leader_only",
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
            "identity_confidence": 0.8,
            "persistence_duration_minutes": 20.0,
            "realized_R": 0.9,
        },
        {
            "raw_trade_id": "crowded_fragile",
            "evaluation_scope": "full_period",
            "event_count": 2,
            "persistence_depth": 1,
            "add_depth": 0,
            "scale_depth": 0,
            "source_linked_flag": 1,
            "fragile_transition_flag": 1,
            "invalidated_flag": 0,
            "add_confirmed_flag": 0,
            "scale_up_flag": 0,
            "persistence_confirmed_flag": 1,
            "lineage_quality": "source_linked",
            "identity_confidence": 0.8,
            "persistence_duration_minutes": 20.0,
            "realized_R": 0.5,
        },
        {
            "raw_trade_id": "anchored_immediate_invalid",
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
            "identity_confidence": 0.8,
            "persistence_duration_minutes": 0.0,
            "realized_R": -0.5,
        },
    ]
    return pd.DataFrame(rows)


class PersistenceUniverse376Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        candidates = _candidates_fixture()
        return build_persistence_universe_376(
            candidates_df=candidates,
            lifecycle_df=_lifecycle_fixture(),
            persistence_prediction_df=_persistence_prediction_fixture(candidates),
        )

    def test_stateful_target_and_missing_lifecycle(self) -> None:
        labels = self._build_fixture_artifacts().stateful_persistence_labels.set_index("trade_id")

        self.assertEqual(int(labels.loc["train_expand_pos", "stateful_persistence_target_v1"]), 1)
        self.assertEqual(int(labels.loc["train_expand_neg", "stateful_persistence_target_v1"]), 0)
        self.assertTrue(pd.isna(labels.loc["missing_lifecycle", "stateful_persistence_target_v1"]))
        self.assertEqual(int(labels.loc["missing_lifecycle", "lifecycle_coverage_flag"]), 0)
        self.assertEqual(str(labels.loc["missing_lifecycle", "target_confidence"]), "low")

    def test_immediate_invalidation_is_excluded(self) -> None:
        labels = self._build_fixture_artifacts().stateful_persistence_labels.set_index("trade_id")

        self.assertEqual(int(labels.loc["anchored_immediate_invalid", "label_eligible_flag"]), 0)
        self.assertEqual(str(labels.loc["anchored_immediate_invalid", "exclusion_reason"]), "immediate_invalidation")

    def test_universe_buckets_respect_theme_data_and_risk_gates(self) -> None:
        prediction = self._build_fixture_artifacts().persistence_universe_prediction_frame.set_index("trade_id")

        self.assertEqual(str(prediction.loc["train_expand_pos", "persistence_universe_bucket"]), "persistence_core")
        self.assertNotEqual(str(prediction.loc["theme_only_weak", "persistence_universe_bucket"]), "persistence_core")
        self.assertEqual(str(prediction.loc["data_leader_only", "persistence_universe_bucket"]), "qualified_watchlist")
        self.assertEqual(str(prediction.loc["crowded_fragile", "persistence_universe_bucket"]), "suppressed_crowding_risk")

    def test_prediction_frame_excludes_outcomes_and_labels(self) -> None:
        prediction = self._build_fixture_artifacts().persistence_universe_prediction_frame
        for forbidden in (
            "stateful_persistence_target_v1",
            "target_reason",
            "label_eligible_flag",
            "lifecycle_coverage_flag",
            "target_confidence",
            "exclusion_reason",
            "realized_R",
            "invalidated_flag",
            "persistence_confirmed_flag",
            "event_count",
            "lineage_quality",
        ):
            self.assertNotIn(forbidden, prediction.columns)

    def test_anchored_oos_is_diagnostic_only_when_sparse(self) -> None:
        sample = self._build_fixture_artifacts().persistence_universe_sample_adequacy_audit
        anchored = sample[sample["evaluation_scope"].astype(str).eq("anchored_oos")].iloc[0]
        self.assertEqual(str(anchored["gate_status"]), "diagnostic_only")
        self.assertEqual(str(anchored["gate_reason"]), "insufficient_bucket_counts")

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_persistence_universe_376(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_persistence_universe_376.build_persistence_universe_376",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["persistence_universe_376", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "persistence_universe_prediction_frame.csv",
                "stateful_persistence_labels.csv",
                "persistence_universe_evaluation_panel.csv",
                "persistence_universe_bucket_audit.csv",
                "persistence_universe_leakage_audit.csv",
                "persistence_universe_sample_adequacy_audit.csv",
                "persistence_universe_decision.csv",
                "task_376_persistence_universe_rebuild.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)

            report_text = (out_dir / "task_376_persistence_universe_rebuild.md").read_text(encoding="utf-8-sig")
            self.assertIn("Complete-Pass Checklist", report_text)
            self.assertIn("anchored_oos_gate_status: diagnostic_only", report_text)
            self.assertRegex(report_text, r"Final Task 376 verdict: `(COMPLETE_PASS|NOT_YET)`")
            self.assertNotIn("deployable alpha", report_text.lower())


if __name__ == "__main__":
    unittest.main()
