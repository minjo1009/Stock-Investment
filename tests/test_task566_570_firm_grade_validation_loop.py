from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task566_570_firm_grade_validation_loop import (
    build_task566,
    build_task567,
    build_task568,
    build_task569,
    build_task570,
)


class Task566To570FirmGradeValidationLoopTest(unittest.TestCase):
    def _panel(self) -> pd.DataFrame:
        rows = []
        for state, split, er, pnl in [
            ("below_vwap_controlled_pullback", "validation", 0, 0.05),
            ("below_vwap_controlled_pullback", "recent_oos", 0, 0.04),
            ("near_high_absorption", "validation", 0, 0.03),
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
                    "holding_days": 6,
                    "ret_5d_prev": 0.04,
                    "ret_20d_prev": 0.12,
                    "ret_60d_prev": 0.25,
                    "breadth_20d": 0.65,
                    "broad_market_score": 70,
                    "broad_market_stress": 10,
                    "liquidity_ratio": 1.2,
                    "vol_ratio": 0.9,
                    "theme_ret20_prev": 0.08,
                    "theme_breadth20_prev": 0.7,
                    "theme_volume_ratio_prev": 1.2,
                    "near_high60_prev": 0.95,
                    "label_used_in_assignment_flag_v3": 0,
                    "outcome_used_in_assignment_flag_v3": 0,
                    "inferred_matching_used_flag_v3": 0,
                }
            )
        return pd.DataFrame(rows)

    def test_task566_freezes_professional_hypothesis_and_gates(self) -> None:
        artifacts = build_task566()
        self.assertGreaterEqual(len(artifacts["team_perfect_goal_contract"]), 5)
        self.assertGreaterEqual(int(artifacts["firm_grade_validation_gate_contract"]["hard_gate_flag"].sum()), 1)
        self.assertIn("H1", set(artifacts["firm_grade_hypothesis_contract"]["hypothesis_id"]))

    def test_task567_capital_flow_regime_uses_pre_entry_scores(self) -> None:
        artifacts = build_task567(self._panel())
        panel = artifacts["capital_flow_regime_v6_panel"]
        self.assertIn("capital_flow_score_v6", panel.columns)
        self.assertEqual(int(panel["regime_assignment_used_outcome_flag"].max()), 0)
        self.assertIn("capital_flow_regime_v6_quality", artifacts)

    def test_task568_sleeve_robustness_uses_vwap_ontology(self) -> None:
        artifacts = build_task568(self._panel())
        sleeve = artifacts["vwap_pullback_sleeve_assignment_panel"]
        self.assertIn("pullback_sleeve_v1", sleeve.columns)
        self.assertEqual(int(sleeve["sleeve_assignment_used_outcome_flag"].max()), 0)
        self.assertIn("vwap_pullback_sleeve_robustness_audit", artifacts)

    def test_task569_capture_run_keeps_not_ready_rows_blocked(self) -> None:
        snapshots = pd.DataFrame(
            [
                {
                    "decision_id": "D1",
                    "symbol": "AAA",
                    "microstructure_source_ready_flag": 0,
                    "pre_action_snapshot_flag": 1,
                    "order_submission_enabled_flag": 0,
                    "missing_source_codes": "nbbo_quote,status,luld",
                }
            ]
        )
        artifacts = build_task569(snapshots)
        run = artifacts["paper_shadow_microstructure_capture_run_audit"].iloc[0]
        self.assertEqual(int(run["microstructure_ready_rows"]), 0)
        self.assertEqual(int(run["live_truth_ready_flag"]), 0)

    def test_task570_blocks_promotion_without_microstructure(self) -> None:
        t566 = build_task566()
        t567 = build_task567(self._panel())
        t568 = build_task568(self._panel())
        t569 = build_task569(pd.DataFrame([{"microstructure_source_ready_flag": 0, "pre_action_snapshot_flag": 1, "missing_source_codes": "nbbo_quote"}]))
        artifacts = build_task570(t566, t567, t568, t569)
        decision = artifacts["task_570_decision"].iloc[0]
        self.assertEqual(decision["strategy_acceptance_status"], "DATA_BLOCKED_WAIT_FOR_MICROSTRUCTURE_CAPTURE")
        self.assertGreater(int(decision["data_blocked_gate_count"]), 0)


if __name__ == "__main__":
    unittest.main()
