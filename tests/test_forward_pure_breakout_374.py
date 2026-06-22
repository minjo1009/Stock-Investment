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

from backtest.analysis_structural_breakout_forward_pure_breakout_374 import main as report_main
from backtest.build_forward_pure_breakout_374 import (
    build_forward_pure_breakout_374,
    write_forward_pure_breakout_374,
)


def _master_fixture() -> pd.DataFrame:
    base = {
        "symbol": "AAPL",
        "entry_ts": "2026-01-05T14:30:00Z",
        "breakout_timestamp": "2026-01-05T14:29:00Z",
        "breakout_hold_duration_bars": 3,
        "return_next_3bars": 0.03,
        "adverse_excursion_next_3bars": -0.01,
        "intraday_pullback_depth_3bars": 0.02,
        "persistence_duration_minutes": 20.0,
        "breakout_response": "breakout_hold",
        "vwap_response": "vwap_hold",
        "volume_persistence_3bars": 0.8,
        "relative_volume_percentile": 0.92,
        "price_vs_session_vwap_at_breakout": 0.02,
        "vwap_deviation_at_breakout": 0.01,
        "vwap_slope_prebreak": 0.005,
        "breakout_bar_close_location": 0.85,
        "dist_to_sma20_pct": 0.03,
        "dist_to_sma50_pct": 0.06,
        "market_breadth_state": "broad",
        "gap_environment_state": "calm",
        "sector_leadership_state": "broad_led",
        "same_day_candidate_count": 2,
        "same_day_sector_candidate_count": 1,
        "dispersion_20d": 0.15,
        "mean_pairwise_corr": 0.20,
        "semis_concentration_ratio": 0.10,
        "current_split": "anchored_oos",
    }
    rows = [
        {"trade_id": "pair_persist", **base, "realized_R": 2.0},
        {"trade_id": "pair_fail", **base, "realized_R": -1.0},
        {
            "trade_id": "first30_blocked",
            **base,
            "entry_ts": "2026-01-06T14:00:00Z",
            "breakout_timestamp": "2026-01-06T13:59:00Z",
            "session_timing_bucket": "first_30m",
            "same_day_candidate_count": 1,
            "same_day_sector_candidate_count": 1,
            "realized_R": -0.5,
        },
        {
            "trade_id": "tech_narrow",
            **base,
            "entry_ts": "2026-01-07T15:00:00Z",
            "breakout_timestamp": "2026-01-07T14:59:00Z",
            "session_timing_bucket": "mid_session",
            "market_breadth_state": "narrow",
            "sector_leadership_state": "tech_led",
            "realized_R": -0.2,
        },
        {
            "trade_id": "semis_conc",
            **base,
            "entry_ts": "2026-01-08T15:30:00Z",
            "breakout_timestamp": "2026-01-08T15:29:00Z",
            "symbol": "NVDA",
            "session_timing_bucket": "mid_session",
            "semis_concentration_ratio": 0.95,
            "same_day_candidate_count": 10,
            "same_day_sector_candidate_count": 8,
            "realized_R": -0.3,
        },
        {
            "trade_id": "full_period_good",
            **base,
            "entry_ts": "2025-11-10T15:00:00Z",
            "breakout_timestamp": "2025-11-10T14:59:00Z",
            "current_split": "train",
            "session_timing_bucket": "mid_session",
            "realized_R": 1.5,
        },
    ]
    frame = pd.DataFrame(rows)
    if "session_timing_bucket" not in frame.columns:
        frame["session_timing_bucket"] = "mid_session"
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True)
    frame["breakout_timestamp"] = pd.to_datetime(frame["breakout_timestamp"], utc=True)
    frame["day_key"] = frame["entry_ts"].dt.strftime("%Y-%m-%d")
    return frame


def _policy_pool_fixture(master: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_id": row.trade_id,
                "event_id": f"evt_{idx:03d}",
                "day_key": row.day_key,
                "endogenous_state": "normal_continuation_state" if row.trade_id != "tech_narrow" else "crowded_dislocation_state",
                "day_endogenous_state": "normal_continuation_state",
                "current_split": row.current_split,
            }
            for idx, row in enumerate(master.itertuples(index=False), start=1)
        ]
    )


def _shadow_log_fixture(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in master.itertuples(index=False):
        blocked = row.trade_id in {"first30_blocked", "tech_narrow"}
        add_blocked = row.trade_id in {"first30_blocked", "tech_narrow", "semis_conc"}
        rows.append(
            {
                "trade_id": row.trade_id,
                "state_label": "DISLOCATION" if row.trade_id == "tech_narrow" else "NORMAL",
                "continuation_risk_score": 0.70 if row.trade_id == "tech_narrow" else 0.20,
                "allow_new_entry": not blocked,
                "allow_add": not add_blocked,
                "factor_exposure_violated": row.trade_id == "semis_conc",
                "violated_factors": "semis" if row.trade_id == "semis_conc" else "",
                "staged_gate_stage": "stage_1_probe" if row.trade_id == "first30_blocked" else "stage_2_add",
                "staged_add_allowed": row.trade_id not in {"first30_blocked", "semis_conc"},
                "participation_quality_label": "HEALTHY_EXPANSION" if row.trade_id != "tech_narrow" else "FRAGILE_CROWDING",
                "participation_expansion_score": 0.80 if row.trade_id != "tech_narrow" else 0.30,
                "participation_fragility_score": 0.20 if row.trade_id != "tech_narrow" else 0.80,
                "participation_confidence": 0.90,
                "healthy_aggressive_policy_label": "KEEP_SUPPRESSED" if blocked else "RELAX_SIZE_AND_ADD",
                "healthy_aggressive_final_add_allowed": not add_blocked,
                "healthy_aggressive_final_size_multiplier": 0.0 if blocked else 0.75,
                "hypothetical_blocked_entry": blocked,
                "hypothetical_blocked_add": add_blocked,
                "hypothetical_reduced_entry": row.trade_id == "semis_conc",
                "hypothetical_reduced_add": row.trade_id == "semis_conc",
            }
        )
    return pd.DataFrame(rows)


def _lifecycle_panel_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "raw_trade_id": "pair_persist",
                "evaluation_scope": "full_period",
                "event_count": 5,
                "persistence_depth": 1,
                "add_depth": 1,
                "scale_depth": 1,
                "source_linked_flag": 1,
                "fragile_transition_flag": 0,
                "invalidated_flag": 0,
                "add_confirmed_flag": 1,
                "scale_up_flag": 1,
                "persistence_confirmed_flag": 1,
                "lineage_quality": "source_linked",
                "persistence_duration_minutes": 20.0,
            },
            {
                "raw_trade_id": "pair_fail",
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
                "persistence_duration_minutes": 0.0,
            },
            {
                "raw_trade_id": "first30_blocked",
                "evaluation_scope": "full_period",
                "event_count": 2,
                "persistence_depth": 0,
                "add_depth": 0,
                "scale_depth": 0,
                "source_linked_flag": 0,
                "fragile_transition_flag": 0,
                "invalidated_flag": 1,
                "add_confirmed_flag": 0,
                "scale_up_flag": 0,
                "persistence_confirmed_flag": 0,
                "lineage_quality": "replay_derived",
                "persistence_duration_minutes": 0.0,
            },
            {
                "raw_trade_id": "tech_narrow",
                "evaluation_scope": "full_period",
                "event_count": 2,
                "persistence_depth": 0,
                "add_depth": 0,
                "scale_depth": 0,
                "source_linked_flag": 0,
                "fragile_transition_flag": 1,
                "invalidated_flag": 1,
                "add_confirmed_flag": 0,
                "scale_up_flag": 0,
                "persistence_confirmed_flag": 0,
                "lineage_quality": "replay_derived",
                "persistence_duration_minutes": 0.0,
            },
            {
                "raw_trade_id": "semis_conc",
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
            },
            {
                "raw_trade_id": "full_period_good",
                "evaluation_scope": "full_period",
                "event_count": 4,
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
                "persistence_duration_minutes": 30.0,
            },
        ]
    )


class ForwardPureBreakout374Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        master = _master_fixture()
        return build_forward_pure_breakout_374(
            master_df=master,
            policy_pool_df=_policy_pool_fixture(master),
            shadow_log_df=_shadow_log_fixture(master),
            lifecycle_panel_df=_lifecycle_panel_fixture(),
        )

    def test_forward_only_registry_excludes_future_fields(self) -> None:
        artifacts = self._build_fixture_artifacts()
        registry = artifacts.forward_only_feature_matrix
        leakage = artifacts.prediction_leakage_audit

        for feature in (
            "breakout_hold_duration_bars",
            "return_next_3bars",
            "adverse_excursion_next_3bars",
            "intraday_pullback_depth_3bars",
            "persistence_duration_minutes",
        ):
            row = registry[registry["feature_name"].astype(str) == feature].iloc[0]
            self.assertFalse(bool(row["allowed_for_task_374"]))
            self.assertTrue(bool(row["uses_future_bars"]))
            self.assertTrue(leakage["feature_name"].astype(str).eq(feature).any())

    def test_ambiguous_fields_are_not_allowed(self) -> None:
        artifacts = self._build_fixture_artifacts()
        registry = artifacts.forward_only_feature_matrix
        for feature in ("breakout_response", "vwap_response", "volume_persistence_3bars"):
            row = registry[registry["feature_name"].astype(str) == feature].iloc[0]
            self.assertFalse(bool(row["allowed_for_task_374"]))

    def test_prediction_frame_has_no_realized_or_lifecycle_outcomes(self) -> None:
        artifacts = self._build_fixture_artifacts()
        candidates = artifacts.forward_pure_breakout_candidates
        self.assertNotIn("realized_R", candidates.columns)
        self.assertNotIn("invalidated_flag", candidates.columns)
        self.assertIn("realized_R", artifacts.forward_breakout_evaluation_panel.columns)
        self.assertIn("invalidated_flag", artifacts.forward_breakout_evaluation_panel.columns)

    def test_paired_future_outcomes_do_not_change_entry_prediction(self) -> None:
        artifacts = self._build_fixture_artifacts()
        candidates = artifacts.forward_pure_breakout_candidates.set_index("trade_id")
        persist = candidates.loc["pair_persist"]
        fail = candidates.loc["pair_fail"]

        self.assertEqual(float(persist["forward_breakout_score"]), float(fail["forward_breakout_score"]))
        self.assertEqual(str(persist["forward_breakout_bucket"]), str(fail["forward_breakout_bucket"]))

    def test_overlap_audit_is_non_empty_and_detects_disagreement(self) -> None:
        artifacts = self._build_fixture_artifacts()
        overlap = artifacts.prediction_vs_policy_overlap
        self.assertFalse(overlap.empty)
        self.assertTrue(overlap["prediction_policy_disagreement_flag"].astype(int).gt(0).any())

    def test_prediction_input_completeness_records_materialized_and_unavailable(self) -> None:
        artifacts = self._build_fixture_artifacts()
        completeness = artifacts.prediction_input_completeness.set_index("feature_name")
        self.assertEqual(str(completeness.loc["daily_bias", "materialization_status"]), "materialized")
        self.assertEqual(str(completeness.loc["ker", "materialization_status"]), "forward_safe_but_unavailable")
        self.assertEqual(str(completeness.loc["volume_percentile", "materialization_status"]), "forward_safe_but_unavailable")

    def test_bucket_audit_and_degradation_classification_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        audit = artifacts.forward_breakout_bucket_audit
        summary = artifacts.breakout_purity_summary
        self.assertFalse(audit.empty)
        meta = audit[audit["forward_breakout_bucket"].astype(str).eq("meta_monotonicity_check")].copy()
        self.assertFalse(meta.empty)
        anchored_meta = meta[meta["evaluation_scope"].astype(str) == "anchored_oos"].copy()
        self.assertFalse(anchored_meta.empty)
        self.assertEqual(str(anchored_meta.iloc[0]["gate_status"]), "diagnostic_only")
        self.assertEqual(str(anchored_meta.iloc[0]["gate_reason"]), "insufficient_bucket_counts")
        degr = summary[summary["evaluation_cut"].astype(str) == "degradation_classification"].copy()
        self.assertFalse(degr.empty)
        self.assertIn(
            str(degr.iloc[0]["degradation_class"]),
            {"selection_failure", "policy_contamination", "mixed", "indeterminate_low_signal"},
        )
        blocked = audit[
            audit["evaluation_scope"].astype(str).eq("anchored_oos")
            & audit["forward_breakout_bucket"].astype(str).eq("blocked_candidate")
        ].copy()
        self.assertFalse(blocked.empty)
        blocked_count = int(blocked.iloc[0]["trade_count"])
        blocked_note = str(blocked.iloc[0]["audit_note"])
        self.assertTrue(blocked_count >= 3 or blocked_note == "structurally_empty_bucket")

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_forward_pure_breakout_374(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_forward_pure_breakout_374.build_forward_pure_breakout_374",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["forward_pure_breakout_374", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "forward_only_feature_matrix.csv",
                "prediction_leakage_audit.csv",
                "prediction_input_completeness.csv",
                "forward_breakout_rulebook.csv",
                "forward_pure_breakout_candidates.csv",
                "prediction_vs_policy_overlap.csv",
                "forward_breakout_evaluation_panel.csv",
                "forward_breakout_bucket_audit.csv",
                "breakout_purity_summary.csv",
                "task_375_interface_ready.csv",
                "task_374_forward_pure_breakout.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)

            report_text = (out_dir / "task_374_forward_pure_breakout.md").read_text(encoding="utf-8-sig")
            self.assertNotIn("selection_failure` if", report_text)
            self.assertIn("Q4 larger driver of negative OOS:", report_text)
            self.assertIn("Complete-Pass Checklist", report_text)
            self.assertIn("anchored_bucket_monotonicity_gate_status: diagnostic_only", report_text)
            self.assertIn("Anchored bucket monotonicity diagnostic result", report_text)
            self.assertRegex(report_text, r"Final Task 374 verdict: `(COMPLETE_PASS|NOT_YET)`")
            self.assertRegex(report_text, r"Task 375 READY: `(YES|NO)`")


if __name__ == "__main__":
    unittest.main()
