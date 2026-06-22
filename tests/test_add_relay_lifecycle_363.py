from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from src.backtest.analysis_structural_breakout_add_relay_lifecycle_363 import main as task_363_main
from src.backtest.continuation_lifecycle import build_continuation_lifecycle_diagnostics
from src.risk.add_relay_diagnostics import build_add_relay_diagnostics


class TestAddRelayLifecycle363(unittest.TestCase):
    def _sample_shadow_log(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "trade_id": "t1",
                    "timestamp": "2026-01-03T14:30:00Z",
                    "symbol": "NVDA",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.85,
                    "participation_fragility_score": 0.20,
                    "participation_confidence": 0.80,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.20,
                    "factor_exposure_violated": False,
                    "violated_factors": "",
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "healthy_aggressive_policy_label": "RELAX_SIZE_AND_ADD",
                    "healthy_aggressive_final_add_allowed": True,
                    "healthy_aggressive_final_size_multiplier": 0.70,
                    "quality_aware_add_allowed": True,
                    "quality_aware_size_multiplier": 0.60,
                    "baseline_realized_R": 1.20,
                    "shadow_realized_R_proxy": 0.60,
                    "quality_aware_realized_R_proxy": 0.72,
                    "healthy_aggressive_realized_R_proxy": 0.84,
                },
                {
                    "trade_id": "t2",
                    "timestamp": "2026-01-03T14:35:00Z",
                    "symbol": "NVDA",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "participation_expansion_score": 0.30,
                    "participation_fragility_score": 0.80,
                    "participation_confidence": 0.90,
                    "state_label": "ELEVATED",
                    "continuation_risk_score": 0.55,
                    "factor_exposure_violated": False,
                    "violated_factors": "",
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.10,
                    "quality_aware_add_allowed": False,
                    "quality_aware_size_multiplier": 0.15,
                    "baseline_realized_R": -0.80,
                    "shadow_realized_R_proxy": -0.08,
                    "quality_aware_realized_R_proxy": -0.12,
                    "healthy_aggressive_realized_R_proxy": -0.08,
                },
                {
                    "trade_id": "t3",
                    "timestamp": "2026-01-03T14:40:00Z",
                    "symbol": "AMD",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.82,
                    "participation_fragility_score": 0.18,
                    "participation_confidence": 0.82,
                    "state_label": "DISLOCATION",
                    "continuation_risk_score": 0.88,
                    "factor_exposure_violated": False,
                    "violated_factors": "",
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.10,
                    "quality_aware_add_allowed": False,
                    "quality_aware_size_multiplier": 0.10,
                    "baseline_realized_R": -1.10,
                    "shadow_realized_R_proxy": -0.11,
                    "quality_aware_realized_R_proxy": -0.11,
                    "healthy_aggressive_realized_R_proxy": -0.11,
                },
                {
                    "trade_id": "t4",
                    "timestamp": "2026-01-04T14:30:00Z",
                    "symbol": "MSFT",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.84,
                    "participation_fragility_score": 0.22,
                    "participation_confidence": 0.78,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.28,
                    "factor_exposure_violated": True,
                    "violated_factors": "semis",
                    "allow_add": True,
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.00,
                    "quality_aware_add_allowed": False,
                    "quality_aware_size_multiplier": 0.00,
                    "baseline_realized_R": 0.50,
                    "shadow_realized_R_proxy": 0.00,
                    "quality_aware_realized_R_proxy": 0.00,
                    "healthy_aggressive_realized_R_proxy": 0.00,
                },
                {
                    "trade_id": "t5",
                    "timestamp": "2026-01-04T14:35:00Z",
                    "symbol": "MSFT",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "participation_expansion_score": 0.83,
                    "participation_fragility_score": 0.24,
                    "participation_confidence": 0.79,
                    "state_label": "NORMAL",
                    "continuation_risk_score": 0.30,
                    "factor_exposure_violated": False,
                    "violated_factors": "",
                    "allow_add": False,
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.25,
                    "quality_aware_add_allowed": False,
                    "quality_aware_size_multiplier": 0.35,
                    "baseline_realized_R": 0.40,
                    "shadow_realized_R_proxy": 0.10,
                    "quality_aware_realized_R_proxy": 0.14,
                    "healthy_aggressive_realized_R_proxy": 0.10,
                },
            ]
        )

    def test_add_relay_diagnostics_identify_dropoff_by_gate(self) -> None:
        trace_df, dropoff_df, _reasons_df = build_add_relay_diagnostics(self._sample_shadow_log())
        self.assertIn("first_blocking_reason", trace_df.columns)
        healthy = dropoff_df[dropoff_df["quality_label"].astype(str) == "HEALTHY_EXPANSION"].set_index("gate_name")
        self.assertEqual(int(healthy.loc["state_gate", "block_count"]), 1)
        self.assertEqual(int(healthy.loc["factor_budget", "block_count"]), 1)
        self.assertEqual(int(healthy.loc["exposure_gate", "block_count"]), 1)

    def test_healthy_expansion_rows_can_be_traced_through_all_gates(self) -> None:
        trace_df, _dropoff_df, _reasons_df = build_add_relay_diagnostics(self._sample_shadow_log())
        healthy = trace_df[trace_df["participation_quality_label"].astype(str) == "HEALTHY_EXPANSION"]
        self.assertTrue((healthy["healthy_policy_label"].astype(str).str.len() > 0).all())
        self.assertIn("final_add_allowed", healthy.columns)

    def test_first_blocking_reason_populated_for_blocked_rows(self) -> None:
        trace_df, _dropoff_df, _reasons_df = build_add_relay_diagnostics(self._sample_shadow_log())
        blocked = trace_df[~trace_df["final_add_allowed"].fillna(False).astype(bool)]
        self.assertTrue((blocked["first_blocking_reason"].astype(str).str.len() > 0).all())

    def test_gate_summary_counts_are_consistent(self) -> None:
        _trace_df, dropoff_df, _reasons_df = build_add_relay_diagnostics(self._sample_shadow_log())
        for _, row in dropoff_df.iterrows():
            self.assertEqual(int(row["input_count"]), int(row["pass_count"]) + int(row["block_count"]))

    def test_lifecycle_grouping_is_deterministic(self) -> None:
        first_df, first_summary = build_continuation_lifecycle_diagnostics(self._sample_shadow_log())
        second_df, second_summary = build_continuation_lifecycle_diagnostics(self._sample_shadow_log())
        pd.testing.assert_frame_equal(first_df, second_df)
        pd.testing.assert_frame_equal(first_summary, second_summary)

    def test_lifecycle_diagnostics_aggregate_row_level_proxy_pnl_correctly(self) -> None:
        lifecycle_df, _summary_df = build_continuation_lifecycle_diagnostics(self._sample_shadow_log())
        nvda = lifecycle_df[lifecycle_df["lifecycle_id"].astype(str) == "NVDA|2026-01-03"].iloc[0]
        self.assertAlmostEqual(float(nvda["baseline_pnl_r_sum"]), 0.4, places=6)
        self.assertAlmostEqual(float(nvda["healthy_aggressive_pnl_proxy_sum"]), 0.76, places=6)

    def test_mixed_lifecycle_identified_when_healthy_and_fragile_coexist(self) -> None:
        lifecycle_df, _summary_df = build_continuation_lifecycle_diagnostics(self._sample_shadow_log())
        nvda = lifecycle_df[lifecycle_df["lifecycle_id"].astype(str) == "NVDA|2026-01-03"].iloc[0]
        self.assertEqual(str(nvda["lifecycle_quality_type"]), "mixed")

    def test_report_generation_creates_required_files(self) -> None:
        shadow_log = self._sample_shadow_log()
        artifacts = SimpleNamespace(
            shadow_log=shadow_log.copy(),
            baseline_frame=pd.DataFrame({"entry_ts": pd.to_datetime(shadow_log["timestamp"], utc=True), "realized_R": shadow_log["baseline_realized_R"]}),
        )
        with tempfile.TemporaryDirectory() as td, patch(
            "src.backtest.analysis_structural_breakout_add_relay_lifecycle_363.generate_shadow_artifacts",
            return_value=artifacts,
        ), patch("sys.argv", ["task363", "--out-dir", td]):
            task_363_main()
            expected = {
                "task_363_add_relay_lifecycle.md",
                "task_363_add_relay_summary.csv",
                "task_363_healthy_expansion_relay_trace.csv",
                "task_363_gate_dropoff_summary.csv",
                "task_363_blocking_reasons.csv",
                "task_363_lifecycle_diagnostics.csv",
                "task_363_lifecycle_quality_summary.csv",
            }
            actual = {path.name for path in Path(td).iterdir()}
            self.assertTrue(expected.issubset(actual))

    def test_no_broker_live_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for rel_path in (
            root / "src" / "risk" / "add_relay_diagnostics.py",
            root / "src" / "backtest" / "continuation_lifecycle.py",
            root / "src" / "backtest" / "analysis_structural_breakout_add_relay_lifecycle_363.py",
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


if __name__ == "__main__":
    unittest.main()
