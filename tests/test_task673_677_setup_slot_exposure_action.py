from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK673_DIR = Path("docs/reports/task_673_setup_quality_layer")
TASK674_DIR = Path("docs/reports/task_674_slot_value_displacement_engine")
TASK675_DIR = Path("docs/reports/task_675_exposure_cluster_audit")
TASK676_DIR = Path("docs/reports/task_676_conservative_capacity_cap")
TASK677_DIR = Path("docs/reports/task_677_action_permission_matrix")


class Task673677SetupSlotExposureActionTest(unittest.TestCase):
    def test_task673_setup_quality_is_research_only_and_clean(self) -> None:
        decision = pd.read_csv(TASK673_DIR / "task_673_decision.csv").iloc[0]
        panel = pd.read_csv(TASK673_DIR / "task673_setup_quality_panel.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertGreaterEqual(panel["setup_quality_bucket"].nunique(), 4)
        self.assertEqual(int(panel["return_used_in_setup_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["label_used_in_setup_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_in_setup_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["relation_name_alone_high_quality_flag"].sum()), 0)
        self.assertEqual(int(panel["proxy_risk_used_as_hard_rule_flag"].sum()), 0)

    def test_task674_slot_value_outputs_exist(self) -> None:
        grid = pd.read_csv(TASK674_DIR / "task674_slot_value_candidate_grid.csv")
        displacement = pd.read_csv(TASK674_DIR / "task674_displacement_audit.csv")
        winner_damage = pd.read_csv(TASK674_DIR / "task674_winner_damage_audit.csv")

        self.assertIn("setup_slot_priority_only", set(grid["candidate_name"]))
        self.assertFalse(displacement.empty)
        self.assertFalse(winner_damage.empty)
        self.assertTrue(pd.to_numeric(grid["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(grid["return_used_in_assignment_flag"], errors="coerce").eq(0).all())

    def test_task675_exposure_audit_is_diagnostic_only(self) -> None:
        exposure = pd.read_csv(TASK675_DIR / "task675_exposure_cluster_report.csv")
        decision = pd.read_csv(TASK675_DIR / "task_675_decision.csv").iloc[0]

        self.assertFalse(exposure.empty)
        self.assertEqual(int(pd.to_numeric(exposure["assignment_used_flag"], errors="coerce").sum()), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")

    def test_task676_no_promotion_candidate_and_reference_preserved(self) -> None:
        grid = pd.read_csv(TASK676_DIR / "task676_capacity_candidate_grid.csv")
        promotion = pd.read_csv(TASK676_DIR / "task676_promotion_report.csv")

        baseline = grid[grid["candidate_name"].eq("baseline_task639") & grid["split_name"].eq("all")].iloc[0]
        active = grid[grid["candidate_name"].eq("active_relation_cap3_reference") & grid["split_name"].eq("all")].iloc[0]
        action = grid[grid["candidate_name"].eq("action_permission_research_block") & grid["split_name"].eq("all")].iloc[0]

        self.assertAlmostEqual(float(baseline["final_capital_usd"]), 7639.620310821465, places=6)
        self.assertAlmostEqual(float(active["final_capital_usd"]), 10887.474713480713, places=6)
        self.assertLess(float(action["max_drawdown_pct"]), 0.0)
        self.assertGreater(float(action["max_drawdown_pct"]), float(active["max_drawdown_pct"]))
        self.assertEqual(int(pd.to_numeric(promotion["promotion_candidate_flag"], errors="coerce").sum()), 0)

    def test_task676_forbidden_inputs_clean(self) -> None:
        forbidden = pd.read_csv(TASK676_DIR / "task676_forbidden_input_audit.csv")

        self.assertEqual(int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum()), 0)

    def test_task677_action_matrix_has_no_forbidden_actions(self) -> None:
        matrix = pd.read_csv(TASK677_DIR / "task677_action_permission_matrix.csv")
        decision = pd.read_csv(TASK677_DIR / "task_677_decision.csv").iloc[0]

        self.assertIn("priority_eligible", set(matrix["action_permission"]))
        self.assertIn("research_only", set(matrix["action_permission"]))
        self.assertEqual(int(matrix[["full_entry_or_size_boost_flag", "symbol_block_flag", "theme_block_flag", "hard_block_flag"]].sum().sum()), 0)
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_required_reports_exist(self) -> None:
        for path in [
            TASK673_DIR / "task_673_setup_quality_layer.md",
            TASK674_DIR / "task_674_slot_value_displacement_engine.md",
            TASK675_DIR / "task_675_exposure_cluster_audit.md",
            TASK676_DIR / "task_676_conservative_capacity_cap.md",
            TASK677_DIR / "task_677_action_permission_matrix.md",
        ]:
            self.assertTrue(path.exists(), str(path))


if __name__ == "__main__":
    unittest.main()
