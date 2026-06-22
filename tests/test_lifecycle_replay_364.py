from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_lifecycle_replay_364 import main as task_364_main
from src.backtest.continuation_lifecycle_replay import (
    build_add_activation_summary,
    build_compounding_diagnostics,
    build_continuation_lifecycles,
    build_fragility_transition_summary,
    build_replay_state_distribution,
    replay_lifecycle,
    run_lifecycle_replay,
)


class TestLifecycleReplay364(unittest.TestCase):
    def _sample_shadow_log(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "timestamp": "2026-01-03T14:30:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t1",
                    "signal_id": "s1",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.80,
                    "participation_fragility_score": 0.20,
                    "participation_confidence": 0.90,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.20,
                    "factor_exposure_violated": False,
                    "allow_add": True,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "PROBE_ONLY",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "NO_CHANGE",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.20,
                    "baseline_realized_R": 0.40,
                    "shadow_realized_R_proxy": 0.08,
                    "quality_aware_realized_R_proxy": 0.12,
                    "healthy_aggressive_realized_R_proxy": 0.08,
                },
                {
                    "timestamp": "2026-01-03T14:31:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t2",
                    "signal_id": "s2",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.82,
                    "participation_fragility_score": 0.18,
                    "participation_confidence": 0.92,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.18,
                    "factor_exposure_violated": False,
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "quality_aware_policy_stage": "ADD_ALLOWED",
                    "quality_aware_add_allowed": True,
                    "healthy_aggressive_policy_label": "RELAX_SIZE_AND_ADD",
                    "healthy_aggressive_final_add_allowed": True,
                    "healthy_aggressive_final_size_multiplier": 0.50,
                    "baseline_realized_R": 0.60,
                    "shadow_realized_R_proxy": 0.30,
                    "quality_aware_realized_R_proxy": 0.42,
                    "healthy_aggressive_realized_R_proxy": 0.50,
                },
                {
                    "timestamp": "2026-01-03T14:32:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t3",
                    "signal_id": "s3",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.78,
                    "participation_fragility_score": 0.22,
                    "participation_confidence": 0.88,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.22,
                    "factor_exposure_violated": False,
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "PROBE_ONLY",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "NO_CHANGE",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.50,
                    "baseline_realized_R": 0.20,
                    "shadow_realized_R_proxy": 0.10,
                    "quality_aware_realized_R_proxy": 0.10,
                    "healthy_aggressive_realized_R_proxy": 0.10,
                },
                {
                    "timestamp": "2026-01-03T14:33:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t4",
                    "signal_id": "s4",
                    "strategy_id": "continuation",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "participation_expansion_score": 0.30,
                    "participation_fragility_score": 0.82,
                    "participation_confidence": 0.90,
                    "state_label": "ELEVATED",
                    "continuation_risk_score": 0.55,
                    "factor_exposure_violated": False,
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "PROBE_ONLY",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.30,
                    "baseline_realized_R": -0.50,
                    "shadow_realized_R_proxy": -0.15,
                    "quality_aware_realized_R_proxy": -0.15,
                    "healthy_aggressive_realized_R_proxy": -0.15,
                },
                {
                    "timestamp": "2026-01-03T14:34:00Z",
                    "symbol": "NVDA",
                    "trade_id": "t5",
                    "signal_id": "s5",
                    "strategy_id": "continuation",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "participation_expansion_score": 0.20,
                    "participation_fragility_score": 0.90,
                    "participation_confidence": 0.90,
                    "state_label": "DISLOCATION",
                    "continuation_risk_score": 0.90,
                    "factor_exposure_violated": False,
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "BLOCK",
                    "quality_aware_add_allowed": False,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.00,
                    "baseline_realized_R": -1.00,
                    "shadow_realized_R_proxy": 0.00,
                    "quality_aware_realized_R_proxy": 0.00,
                    "healthy_aggressive_realized_R_proxy": 0.00,
                },
                {
                    "timestamp": "2026-01-04T14:30:00Z",
                    "symbol": "AMD",
                    "trade_id": "t6",
                    "signal_id": "s6",
                    "strategy_id": "continuation",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.81,
                    "participation_fragility_score": 0.19,
                    "participation_confidence": 0.89,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.25,
                    "factor_exposure_violated": False,
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "quality_aware_policy_stage": "ADD_ALLOWED",
                    "quality_aware_add_allowed": True,
                    "healthy_aggressive_policy_label": "RELAX_SIZE_AND_ADD",
                    "healthy_aggressive_final_add_allowed": True,
                    "healthy_aggressive_final_size_multiplier": 0.60,
                    "baseline_realized_R": 0.70,
                    "shadow_realized_R_proxy": 0.42,
                    "quality_aware_realized_R_proxy": 0.49,
                    "healthy_aggressive_realized_R_proxy": 0.60,
                },
            ]
        )

    def test_lifecycle_grouping_deterministic(self) -> None:
        first = build_continuation_lifecycles(self._sample_shadow_log())
        second = build_continuation_lifecycles(self._sample_shadow_log())
        self.assertEqual(first, second)

    def test_contiguous_rows_grouped_by_symbol_and_session_date(self) -> None:
        lifecycles = build_continuation_lifecycles(self._sample_shadow_log())
        ids = [l.lifecycle_id for l in lifecycles]
        self.assertEqual(ids, ["AMD|2026-01-04", "NVDA|2026-01-03"])
        nvda = [l for l in lifecycles if l.lifecycle_id == "NVDA|2026-01-03"][0]
        self.assertEqual(len(nvda.rows), 5)

    def test_replay_state_transitions_deterministic(self) -> None:
        lifecycle = [l for l in build_continuation_lifecycles(self._sample_shadow_log()) if l.lifecycle_id == "NVDA|2026-01-03"][0]
        replay_one, transitions_one = replay_lifecycle(lifecycle)
        replay_two, transitions_two = replay_lifecycle(lifecycle)
        pd.testing.assert_frame_equal(replay_one, replay_two)
        pd.testing.assert_frame_equal(transitions_one, transitions_two)

    def test_probe_can_transition_to_building(self) -> None:
        lifecycle = [l for l in build_continuation_lifecycles(self._sample_shadow_log()) if l.lifecycle_id == "NVDA|2026-01-03"][0]
        replay_df, _ = replay_lifecycle(lifecycle)
        self.assertEqual(replay_df.loc[0, "replay_state"], "PROBE")
        self.assertEqual(replay_df.loc[1, "replay_state"], "BUILDING")

    def test_building_can_transition_to_persisting(self) -> None:
        lifecycle = [l for l in build_continuation_lifecycles(self._sample_shadow_log()) if l.lifecycle_id == "NVDA|2026-01-03"][0]
        replay_df, _ = replay_lifecycle(lifecycle)
        self.assertEqual(replay_df.loc[2, "replay_state"], "PERSISTING")

    def test_fragility_triggers_reducing(self) -> None:
        lifecycle = [l for l in build_continuation_lifecycles(self._sample_shadow_log()) if l.lifecycle_id == "NVDA|2026-01-03"][0]
        replay_df, _ = replay_lifecycle(lifecycle)
        self.assertEqual(replay_df.loc[3, "replay_state"], "REDUCING")

    def test_dislocation_triggers_exited(self) -> None:
        lifecycle = [l for l in build_continuation_lifecycles(self._sample_shadow_log()) if l.lifecycle_id == "NVDA|2026-01-03"][0]
        replay_df, _ = replay_lifecycle(lifecycle)
        self.assertEqual(replay_df.loc[4, "replay_state"], "EXITED")

    def test_add_activation_tracked_correctly(self) -> None:
        _, replay_trace_df, transition_matrix_df, lifecycle_summary_df = run_lifecycle_replay(self._sample_shadow_log())
        add_df = build_add_activation_summary(replay_trace_df)
        self.assertTrue((add_df["add_activation_count"] > 0).any())
        self.assertIn("BUILDING", transition_matrix_df["to_state"].astype(str).tolist())
        self.assertTrue(lifecycle_summary_df["has_building"].fillna(False).astype(bool).any())

    def test_no_future_leakage_in_replay_decisions(self) -> None:
        full_log = self._sample_shadow_log()
        prefix_log = full_log.iloc[:3].copy()
        full_lifecycle = [l for l in build_continuation_lifecycles(full_log) if l.lifecycle_id == "NVDA|2026-01-03"][0]
        prefix_lifecycle = [l for l in build_continuation_lifecycles(prefix_log) if l.lifecycle_id == "NVDA|2026-01-03"][0]
        full_replay, _ = replay_lifecycle(full_lifecycle)
        prefix_replay, _ = replay_lifecycle(prefix_lifecycle)
        pd.testing.assert_series_equal(
            full_replay.loc[:2, "replay_state"].reset_index(drop=True),
            prefix_replay["replay_state"].reset_index(drop=True),
        )

    def test_report_generation_creates_required_files(self) -> None:
        shadow_log = self._sample_shadow_log()
        artifacts = SimpleNamespace(shadow_log=shadow_log.copy())
        with tempfile.TemporaryDirectory() as td, patch(
            "src.backtest.analysis_structural_breakout_lifecycle_replay_364.generate_shadow_artifacts",
            return_value=artifacts,
        ), patch("sys.argv", ["task364", "--out-dir", td]):
            task_364_main()
            expected = {
                "task_364_lifecycle_replay.md",
                "task_364_replay_state_distribution.csv",
                "task_364_lifecycle_summary.csv",
                "task_364_transition_matrix.csv",
                "task_364_add_activation.csv",
                "task_364_compounding_diagnostics.csv",
                "task_364_fragility_transition.csv",
            }
            actual = {path.name for path in Path(td).iterdir()}
            self.assertTrue(expected.issubset(actual))

    def test_no_broker_live_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel_path in (
            root / "src" / "backtest" / "continuation_lifecycle_replay.py",
            root / "src" / "backtest" / "analysis_structural_breakout_lifecycle_replay_364.py",
        ):
            tree = ast.parse(rel_path.read_text(encoding="utf-8"))
            imported: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            lowered = "|".join(name.lower() for name in imported)
            self.assertNotIn("broker", lowered)
            self.assertNotIn("live", lowered)

    def test_compounding_and_fragility_diagnostics_build(self) -> None:
        _, replay_trace_df, _transition_matrix_df, lifecycle_summary_df = run_lifecycle_replay(self._sample_shadow_log())
        from src.backtest.continuation_lifecycle_replay import build_transition_matrix

        transition_trace = pd.DataFrame(
            [
                {"from_state": "PROBE", "to_state": "BUILDING", "trade_id": "t2", "participation_quality_label": "HEALTHY_EXPANSION", "size_multiplier": 0.5, "concentration_step": 0.3},
                {"from_state": "PERSISTING", "to_state": "REDUCING", "trade_id": "t4", "participation_quality_label": "FRAGILE_CROWDING", "size_multiplier": 0.3, "concentration_step": -0.2},
            ]
        )
        compounding_df = build_compounding_diagnostics(replay_trace_df, lifecycle_summary_df, transition_trace)
        fragility_df = build_fragility_transition_summary(transition_trace)
        state_dist_df = build_replay_state_distribution(replay_trace_df)
        self.assertIn("metric_name", compounding_df.columns)
        self.assertFalse(fragility_df.empty)
        self.assertIn("replay_state", state_dist_df.columns)


if __name__ == "__main__":
    unittest.main()
