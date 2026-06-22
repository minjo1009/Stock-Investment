from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task561_565_firm_grade_context_development import (
    build_task561,
    build_task562,
    build_task563,
    build_task564,
    build_task565,
)


class Task561To565FirmGradeContextDevelopmentTest(unittest.TestCase):
    def _context_fixture(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "context_gate_v3": "regime_theme_symbol_intraday_aligned",
                    "vwap_acceptance_state_v3": "near_high_absorption",
                    "multi_day_market_state_v4": "constructive_risk_on",
                    "theme_regime_state_v4": "persistent_theme_leader",
                    "symbol_multiday_setup_state": "trend_persistence_near_high",
                    "split_name": "validation",
                    "quarter": "2025Q1",
                    "theme_id": "ai",
                    "symbol": "AAA",
                    "net_return_from_entry": 0.05,
                    "entry_reduce_failure_flag": 0,
                    "add_scale_success_flag": 1,
                    "false_positive_flag": 0,
                    "holding_days": 5,
                    "label_used_in_context_assignment_flag": 0,
                    "inferred_matching_used_flag_v3": 0,
                },
                {
                    "context_gate_v3": "context_not_aligned",
                    "vwap_acceptance_state_v3": "upper_wick_rejection",
                    "multi_day_market_state_v4": "weak_risk_off",
                    "theme_regime_state_v4": "weak_theme",
                    "symbol_multiday_setup_state": "weak",
                    "split_name": "recent_oos",
                    "quarter": "2025Q1",
                    "theme_id": "cloud",
                    "symbol": "BBB",
                    "net_return_from_entry": -0.03,
                    "entry_reduce_failure_flag": 1,
                    "add_scale_success_flag": 0,
                    "false_positive_flag": 1,
                    "holding_days": 0,
                    "label_used_in_context_assignment_flag": 0,
                    "inferred_matching_used_flag_v3": 0,
                },
            ]
        )

    def _vwap_fixture(self) -> pd.DataFrame:
        rows = []
        for state, split, er, pnl in [
            ("near_high_absorption", "validation", 0, 0.05),
            ("near_high_absorption", "recent_oos", 0, 0.04),
            ("late_chase_above_vwap", "validation", 1, -0.03),
            ("late_chase_above_vwap", "recent_oos", 1, -0.04),
        ]:
            rows.append(
                {
                    "vwap_acceptance_state_v3": state,
                    "split_name": split,
                    "quarter": "2025Q1",
                    "theme_id": "ai",
                    "symbol": "AAA",
                    "net_return_from_entry": pnl,
                    "entry_reduce_failure_flag": er,
                    "add_scale_success_flag": 1 - er,
                    "false_positive_flag": er,
                    "holding_days": 5,
                    "label_used_in_assignment_flag_v3": 0,
                }
            )
        return pd.DataFrame(rows)

    def test_task561_decomposes_context_gate_failure_without_label_assignment(self) -> None:
        artifacts = build_task561(self._context_fixture())
        self.assertIn("context_gate_failure_decomposition", artifacts)
        decision = artifacts["task_561_decision"].iloc[0]
        self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)
        self.assertIn("context_gate_quality", artifacts)

    def test_task562_generates_oos_stability_audit(self) -> None:
        artifacts = build_task562(self._vwap_fixture())
        audit = artifacts["vwap_acceptance_oos_stability_audit"]
        self.assertIn("oos_stability_status", audit.columns)
        self.assertIn("stable_low_entry_reduce", set(audit["oos_stability_status"]))
        decision = artifacts["task_562_decision"].iloc[0]
        self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)

    def test_task563_capture_activation_keeps_non_ready_rows_blocked(self) -> None:
        artifacts = build_task563()
        run = artifacts["paper_shadow_capture_run_audit"].iloc[0]
        self.assertIn("live_source_truth_status", artifacts["paper_shadow_capture_run_audit"].columns)
        self.assertGreaterEqual(int(run["snapshot_rows"]), 0)
        self.assertIn("paper_shadow_capture_activation_plan", artifacts)

    def test_task564_and_565_block_promotion_without_microstructure(self) -> None:
        t561 = build_task561(self._context_fixture())
        t562 = build_task562(self._vwap_fixture())
        t563 = build_task563()
        t563["paper_shadow_capture_run_audit"].loc[0, "microstructure_ready_rows"] = 0
        t564 = build_task564(t561, t562, t563)
        decision = t564["task_564_decision"].iloc[0]
        self.assertIn(str(decision["strategy_acceptance_status"]), {"DATA_BLOCKED_WAIT_FOR_MICROSTRUCTURE_CAPTURE", "REJECT_PROMOTION_NEEDS_RESEARCH_REDESIGN"})
        t565 = build_task565(t564)
        self.assertEqual(int(t565["task_565_decision"].iloc[0]["approximation_used_flag"]), 0)
        self.assertGreater(int(t565["task_565_decision"].iloc[0]["blocked_grid_axis_count"]), 0)


if __name__ == "__main__":
    unittest.main()
