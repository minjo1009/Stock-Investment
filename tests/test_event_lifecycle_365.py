from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_event_lifecycle_365 import main as task_365_main
from src.backtest.continuation_event_chain import (
    build_chain_summary_metrics,
    build_continuation_event_chains,
    build_continuation_evolution_snapshots,
    build_event_transition_summary,
    build_exit_reason_summary,
    build_quality_evolution_summary,
    build_size_evolution_summary,
    summarize_event_chains,
)
from src.backtest.continuation_event_identity import build_continuation_events
from src.backtest.continuation_lifecycle_replay import run_lifecycle_replay


class TestEventLifecycle365(unittest.TestCase):
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
                    "participation_expansion_score": 0.85,
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
                    "participation_expansion_score": 0.83,
                    "participation_fragility_score": 0.20,
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
            ]
        )

    def _build(self) -> tuple[pd.DataFrame, pd.DataFrame, tuple]:
        lifecycle_rows_df, replay_trace_df, _transition_matrix_df, _lifecycle_summary_df = run_lifecycle_replay(self._sample_shadow_log())
        events = build_continuation_events(replay_trace_df, lifecycle_rows_df)
        return lifecycle_rows_df, replay_trace_df, events

    def test_continuation_ids_deterministic(self) -> None:
        _, replay_trace_df, _ = self._build()
        first = build_continuation_events(replay_trace_df, run_lifecycle_replay(self._sample_shadow_log())[0])
        second = build_continuation_events(replay_trace_df, run_lifecycle_replay(self._sample_shadow_log())[0])
        self.assertEqual(first, second)

    def test_event_chains_grouped_correctly(self) -> None:
        lifecycle_rows_df, replay_trace_df, events = self._build()
        chains = build_continuation_event_chains(events, replay_trace_df, lifecycle_rows_df)
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0].continuation_id, "NVDA|2026-01-03")

    def test_chronological_sequencing_preserved(self) -> None:
        _, _, events = self._build()
        indices = [event.event_index for event in events]
        self.assertEqual(indices, [1, 2, 3, 4, 5])

    def test_event_types_assigned_correctly(self) -> None:
        lifecycle_rows_df, replay_trace_df, events = self._build()
        event_types = [event.event_type for event in events]
        self.assertIn("PROBE_ENTRY", event_types)
        self.assertIn("ADD", event_types)
        self.assertIn("PERSIST", event_types)
        self.assertIn("REDUCE", event_types)
        self.assertIn("EXIT", event_types)

    def test_evolution_snapshots_deterministic(self) -> None:
        lifecycle_rows_df, replay_trace_df, _ = self._build()
        first = build_continuation_evolution_snapshots(replay_trace_df, lifecycle_rows_df)
        second = build_continuation_evolution_snapshots(replay_trace_df, lifecycle_rows_df)
        pd.testing.assert_frame_equal(first, second)

    def test_quality_evolution_tracked_correctly(self) -> None:
        lifecycle_rows_df, replay_trace_df, _ = self._build()
        evolution_df = build_continuation_evolution_snapshots(replay_trace_df, lifecycle_rows_df)
        self.assertTrue(evolution_df["participation_quality_transition"].astype(str).eq("HEALTHY_EXPANSION->FRAGILE_CROWDING").any())

    def test_add_scale_transitions_tracked_correctly(self) -> None:
        lifecycle_rows_df, replay_trace_df, events = self._build()
        chains = build_continuation_event_chains(events, replay_trace_df, lifecycle_rows_df)
        evolution_df = build_continuation_evolution_snapshots(replay_trace_df, lifecycle_rows_df)
        summary_df = summarize_event_chains(chains, evolution_df)
        self.assertTrue(pd.to_numeric(summary_df["persistence_duration_events"], errors="coerce").fillna(0.0).ge(1).any())

    def test_no_future_leakage(self) -> None:
        shadow_log = self._sample_shadow_log()
        full_lifecycle_rows_df, full_replay_trace_df, _tm, _ls = run_lifecycle_replay(shadow_log)
        prefix_lifecycle_rows_df, prefix_replay_trace_df, _tm2, _ls2 = run_lifecycle_replay(shadow_log.iloc[:3].copy())
        full_evolution = build_continuation_evolution_snapshots(full_replay_trace_df, full_lifecycle_rows_df)
        prefix_evolution = build_continuation_evolution_snapshots(prefix_replay_trace_df, prefix_lifecycle_rows_df)
        pd.testing.assert_series_equal(
            full_evolution.loc[:2, "event_type"].reset_index(drop=True),
            prefix_evolution["event_type"].reset_index(drop=True),
        )

    def test_report_artifacts_generated(self) -> None:
        shadow_log = self._sample_shadow_log()
        artifacts = SimpleNamespace(shadow_log=shadow_log.copy())
        with tempfile.TemporaryDirectory() as td, patch(
            "src.backtest.analysis_structural_breakout_event_lifecycle_365.generate_shadow_artifacts",
            return_value=artifacts,
        ), patch("sys.argv", ["task365", "--out-dir", td]):
            task_365_main()
            expected = {
                "task_365_event_lifecycle.md",
                "task_365_event_chains.csv",
                "task_365_event_transitions.csv",
                "task_365_quality_evolution.csv",
                "task_365_size_evolution.csv",
                "task_365_exit_reasons.csv",
                "task_365_chain_summary.csv",
            }
            actual = {path.name for path in Path(td).iterdir()}
            self.assertTrue(expected.issubset(actual))

    def test_no_broker_live_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel_path in (
            root / "src" / "backtest" / "continuation_event_identity.py",
            root / "src" / "backtest" / "continuation_event_chain.py",
            root / "src" / "backtest" / "analysis_structural_breakout_event_lifecycle_365.py",
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

    def test_diagnostics_build(self) -> None:
        lifecycle_rows_df, replay_trace_df, events = self._build()
        chains = build_continuation_event_chains(events, replay_trace_df, lifecycle_rows_df)
        evolution_df = build_continuation_evolution_snapshots(replay_trace_df, lifecycle_rows_df)
        chain_summary_df = summarize_event_chains(chains, evolution_df)
        transitions_df = build_event_transition_summary(evolution_df)
        quality_df = build_quality_evolution_summary(evolution_df)
        size_df = build_size_evolution_summary(evolution_df)
        exit_df = build_exit_reason_summary(chain_summary_df)
        metrics_df = build_chain_summary_metrics(chain_summary_df, evolution_df)
        self.assertIn("metric_name", metrics_df.columns)
        self.assertIn("event_type", transitions_df.columns)
        self.assertIn("participation_quality_transition", quality_df.columns)
        self.assertIn("size_multiplier_delta", size_df.columns)
        self.assertIn("exit_reason", exit_df.columns)


if __name__ == "__main__":
    unittest.main()
