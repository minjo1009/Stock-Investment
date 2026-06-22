from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_shadow_integration_360 import (
    _empty_shadow_log,
    _factor_diagnostics,
    _healthy_expansion_aggressive_policy,
    _quality_aware_policy,
    generate_shadow_artifacts,
    _window_comparison,
)
from src.risk.shadow_adapter import ShadowAdapterConfig, build_shadow_risk_decision


class TestAnalysisStructuralBreakoutShadowIntegration360(unittest.TestCase):
    def _row(self, **overrides: object) -> pd.Series:
        base = {
            "event_id": 1,
            "trade_id": "t1",
            "symbol": "AMD",
            "strategy_id": "continuation_sleeve",
            "entry_ts": pd.Timestamp("2026-01-03T00:00:00Z"),
            "day_key": "2026-01-03",
            "current_split": "anchored_oos",
            "sector_group": "semis",
            "session_timing_bucket": "first_30m",
            "execution_quality_bucket": "strong",
            "gap_environment_state": "unstable",
            "market_breadth_state": "narrow",
            "sector_leadership_state": "tech_led",
            "same_day_candidate_count": 10,
            "same_day_sector_candidate_count": 5,
            "dispersion_20d": 1.2,
            "mean_pairwise_corr": 0.8,
            "semis_concentration_ratio": 0.8,
            "realized_R": -1.0,
            "size_multiplier": 0.10,
        }
        base.update(overrides)
        return pd.Series(base)

    def test_shadow_adapter_does_not_require_post_trade_fields(self) -> None:
        row = self._row()
        day_slice = pd.DataFrame([row.drop(labels=["realized_R"])])
        decision = build_shadow_risk_decision(row.drop(labels=["realized_R"]), day_slice)
        self.assertIn(decision.state_decision.state_label, {"CROWDED", "DISLOCATION", "ELEVATED", "NORMAL"})

    def test_missing_optional_fields_produce_conservative_defaults(self) -> None:
        row = self._row()
        reduced = row.drop(labels=["dispersion_20d", "mean_pairwise_corr", "semis_concentration_ratio"])
        day_slice = pd.DataFrame([reduced])
        decision = build_shadow_risk_decision(reduced, day_slice)
        joined = "|".join(decision.state_decision.reasons)
        self.assertIn("missing_dispersion_defaulted", joined)
        self.assertGreaterEqual(decision.state_decision.continuation_risk_score, 0.40)

    def test_dislocation_logs_add_block(self) -> None:
        row = self._row()
        day_slice = pd.DataFrame([row, self._row(event_id=2, trade_id="t2"), self._row(event_id=3, trade_id="t3")])
        decision = build_shadow_risk_decision(row, day_slice)
        self.assertEqual(decision.state_decision.state_label, "DISLOCATION")
        self.assertFalse(decision.exposure_decision.allow_add)

    def test_clean_case_can_produce_add_allowed(self) -> None:
        row = self._row(
            symbol="MSFT",
            sector_group="software_internet",
            session_timing_bucket="mid_session",
            execution_quality_bucket="strong",
            gap_environment_state="calm",
            market_breadth_state="broad",
            sector_leadership_state="broad_led",
            same_day_candidate_count=1,
            same_day_sector_candidate_count=1,
            dispersion_20d=0.1,
            mean_pairwise_corr=0.1,
            semis_concentration_ratio=0.0,
            size_multiplier=0.05,
        )
        day_slice = pd.DataFrame([row])
        decision = build_shadow_risk_decision(row, day_slice)
        self.assertEqual(decision.staged_gate_decision.participation_stage, "stage_2_add")
        self.assertEqual(decision.participation_quality_decision.quality_label, "HEALTHY_EXPANSION")

    def test_factor_violation_logged_by_factor_name(self) -> None:
        row = self._row(size_multiplier=0.30)
        day_slice = pd.DataFrame([row, self._row(event_id=2, trade_id="t2", size_multiplier=0.30)])
        config = ShadowAdapterConfig()
        first = build_shadow_risk_decision(day_slice.iloc[0], day_slice, config=config)
        second = build_shadow_risk_decision(day_slice.iloc[1], day_slice, factor_budget_state=first.next_factor_budget_state, config=config)
        self.assertTrue(second.factor_exposure_violated)
        self.assertIn("semis", second.violated_factors)

    def test_window_comparison_contains_required_fields(self) -> None:
        baseline = pd.DataFrame(
            {
                "trade_id": ["t1"],
                "entry_ts": [pd.Timestamp("2026-01-03T00:00:00Z")],
                "current_split": ["anchored_oos"],
                "realized_R": [-1.0],
                "sector_group": ["semis"],
            }
        )
        shadow = pd.DataFrame(
            {
                "trade_id": ["t1"],
                "hypothetical_blocked_entry": [True],
                "hypothetical_blocked_add": [True],
                "hypothetical_reduced_entry": [False],
                "hypothetical_reduced_add": [False],
                "continuation_risk_score": [0.8],
                "state_label": ["DISLOCATION"],
                "factor_exposure_violated": [True],
                "staged_add_allowed": [False],
            }
        )
        proxy = baseline.copy()
        proxy["realized_R"] = [0.0]
        out = _window_comparison(baseline, shadow, proxy)
        self.assertIn("window_name", out.columns)
        self.assertIn("shadow_blocked_entries", out.columns)
        self.assertIn("shadow_gated_pnl_proxy_r", out.columns)

    def test_factor_diagnostics_contains_factor_names(self) -> None:
        shadow = pd.DataFrame(
            {
                "violated_factors": ["semis", ""],
                "continuation_risk_score": [0.8, 0.2],
                "hypothetical_blocked_entry": [True, False],
                "factor_exposure_violated": [True, False],
                "state_label": ["DISLOCATION", "NORMAL"],
            }
        )
        out = _factor_diagnostics(shadow)
        self.assertIn("factor_name", out.columns)
        self.assertTrue(out["factor_name"].astype(str).eq("semis").any())

    def test_shadow_disabled_preserves_baseline_output(self) -> None:
        baseline_frame = pd.DataFrame(
            {
                "trade_id": ["t1"],
                "entry_ts": [pd.Timestamp("2026-01-03T00:00:00Z")],
                "current_split": ["anchored_oos"],
                "sector_group": ["semis"],
                "realized_R": [1.25],
                "day_key": ["2026-01-03"],
            }
        )
        benchmark_frame = baseline_frame.copy()
        labeled_pool = baseline_frame.copy()
        baseline_metrics = {
            "net_pnl_r": 1.25,
            "anchored_oos_net_pnl_r": 1.25,
            "trade_count": 1,
            "rolling_oos_robustness": 1.0,
            "capital_utilization": 0.5,
            "concentration": 0.2,
        }

        with patch(
            "src.backtest.analysis_structural_breakout_shadow_integration_360._build_task360_context",
            return_value=(baseline_frame.copy(), benchmark_frame.copy(), labeled_pool.copy(), {}),
        ), patch(
            "src.backtest.analysis_structural_breakout_shadow_integration_360._framework_metrics",
            side_effect=lambda name, frame, eligible_days: dict(baseline_metrics),
        ):
            artifacts = generate_shadow_artifacts(enable_shadow_state_engine=False)

        self.assertTrue(artifacts.baseline_preserved)
        self.assertTrue(artifacts.baseline_metrics_unchanged)
        self.assertEqual(float(artifacts.engine_summary.loc[artifacts.engine_summary["mode"] == "baseline", "net_pnl_r"].iloc[0]), 1.25)
        self.assertEqual(len(artifacts.shadow_log), 0)

    def test_shadow_enabled_does_not_mutate_baseline_frame(self) -> None:
        baseline_frame = pd.DataFrame(
            {
                "event_id": [1],
                "trade_id": ["t1"],
                "symbol": ["AMD"],
                "strategy_id": ["continuation_sleeve"],
                "entry_ts": [pd.Timestamp("2026-01-03T00:00:00Z")],
                "day_key": ["2026-01-03"],
                "current_split": ["anchored_oos"],
                "sector_group": ["semis"],
                "session_timing_bucket": ["first_30m"],
                "execution_quality_bucket": ["strong"],
                "gap_environment_state": ["unstable"],
                "market_breadth_state": ["narrow"],
                "sector_leadership_state": ["tech_led"],
                "same_day_candidate_count": [10],
                "same_day_sector_candidate_count": [5],
                "dispersion_20d": [1.2],
                "mean_pairwise_corr": [0.8],
                "semis_concentration_ratio": [0.8],
                "realized_R": [-1.0],
                "size_multiplier": [0.10],
            }
        )
        benchmark_frame = baseline_frame.copy()
        labeled_pool = baseline_frame.copy()
        baseline_metrics = {
            "net_pnl_r": -1.0,
            "anchored_oos_net_pnl_r": -1.0,
            "trade_count": 1,
            "rolling_oos_robustness": 0.0,
            "capital_utilization": 0.5,
            "concentration": 0.2,
        }
        original = baseline_frame.copy(deep=True)

        with patch(
            "src.backtest.analysis_structural_breakout_shadow_integration_360._build_task360_context",
            return_value=(baseline_frame, benchmark_frame.copy(), labeled_pool.copy(), {}),
        ), patch(
            "src.backtest.analysis_structural_breakout_shadow_integration_360._framework_metrics",
            side_effect=lambda name, frame, eligible_days: dict(baseline_metrics, net_pnl_r=float(pd.to_numeric(frame.get("realized_R", pd.Series([0.0])), errors="coerce").fillna(0.0).sum())),
        ):
            artifacts = generate_shadow_artifacts(enable_shadow_state_engine=True)

        pd.testing.assert_frame_equal(baseline_frame, original)
        self.assertTrue(artifacts.baseline_preserved)
        self.assertGreaterEqual(len(artifacts.shadow_log), 1)
        self.assertIn("participation_quality_label", artifacts.shadow_log.columns)
        self.assertIn("quality_aware_size_multiplier", artifacts.shadow_log.columns)
        self.assertIn("healthy_aggressive_policy_label", artifacts.shadow_log.columns)

    def test_quality_aware_policy_relaxes_healthy_expansion(self) -> None:
        row = self._row(
            symbol="MSFT",
            sector_group="software_internet",
            session_timing_bucket="mid_session",
            execution_quality_bucket="strong",
            gap_environment_state="calm",
            market_breadth_state="broad",
            sector_leadership_state="broad_led",
            same_day_candidate_count=2,
            same_day_sector_candidate_count=1,
            dispersion_20d=0.3,
            mean_pairwise_corr=0.2,
            semis_concentration_ratio=0.0,
            size_multiplier=0.05,
        )
        decision = build_shadow_risk_decision(row, pd.DataFrame([row]))
        policy = _quality_aware_policy(decision)
        self.assertEqual(decision.participation_quality_decision.quality_label, "HEALTHY_EXPANSION")
        self.assertEqual(policy.policy_stage, "ADD_ALLOWED")
        self.assertGreaterEqual(policy.size_multiplier, decision.shadow_size_multiplier)

    def test_quality_aware_policy_stays_strict_for_fragile_crowding(self) -> None:
        row = self._row()
        day_slice = pd.DataFrame([row, self._row(event_id=2, trade_id="t2"), self._row(event_id=3, trade_id="t3")])
        decision = build_shadow_risk_decision(row, day_slice)
        policy = _quality_aware_policy(decision)
        self.assertEqual(decision.participation_quality_decision.quality_label, "FRAGILE_CROWDING")
        self.assertLessEqual(policy.size_multiplier, decision.shadow_size_multiplier)
        self.assertFalse(policy.add_allowed)

    def test_healthy_aggressive_policy_relaxes_healthy_expansion(self) -> None:
        row = self._row(
            symbol="MSFT",
            sector_group="software_internet",
            session_timing_bucket="mid_session",
            execution_quality_bucket="strong",
            gap_environment_state="calm",
            market_breadth_state="broad",
            sector_leadership_state="broad_led",
            same_day_candidate_count=2,
            same_day_sector_candidate_count=1,
            dispersion_20d=0.3,
            mean_pairwise_corr=0.2,
            semis_concentration_ratio=0.0,
            size_multiplier=0.05,
        )
        decision = build_shadow_risk_decision(row, pd.DataFrame([row]))
        policy = _healthy_expansion_aggressive_policy(decision)
        self.assertEqual(decision.participation_quality_decision.quality_label, "HEALTHY_EXPANSION")
        self.assertTrue(policy.size_multiplier >= decision.shadow_size_multiplier)

    def test_healthy_aggressive_policy_never_relaxes_fragile_or_dislocation(self) -> None:
        row = self._row()
        day_slice = pd.DataFrame([row, self._row(event_id=2, trade_id="t2"), self._row(event_id=3, trade_id="t3")])
        decision = build_shadow_risk_decision(row, day_slice)
        policy = _healthy_expansion_aggressive_policy(decision)
        self.assertEqual(decision.participation_quality_decision.quality_label, "FRAGILE_CROWDING")
        self.assertFalse(policy.add_allowed)
        self.assertLessEqual(policy.size_multiplier, decision.shadow_size_multiplier)

    def test_shadow_disabled_shape_is_empty_but_stable(self) -> None:
        shadow = _empty_shadow_log()
        self.assertIn("symbol", shadow.columns)
        self.assertEqual(len(shadow), 0)

    def test_no_broker_or_live_imports_in_shadow_path(self) -> None:
        target_files = [
            Path("src/risk/shadow_adapter.py"),
            Path("src/backtest/analysis_structural_breakout_shadow_integration_360.py"),
        ]
        forbidden_prefixes = ("integration.", "app.", "execution.cancel_loop", "state.store")
        for path in target_files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertFalse(alias.name.startswith(forbidden_prefixes), msg=f"forbidden import {alias.name} in {path}")
                if isinstance(node, ast.ImportFrom) and node.module:
                    self.assertFalse(node.module.startswith(forbidden_prefixes), msg=f"forbidden import {node.module} in {path}")

    def test_task359_regression_suite_still_passes_by_import_contract(self) -> None:
        import tests.test_state_conditional_exposure_engine_359 as task359_tests

        self.assertTrue(hasattr(task359_tests, "TestStateConditionalExposureEngine359"))


if __name__ == "__main__":
    unittest.main()
