from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK682_DIR = Path("docs/reports/task_682_integrated_prediction_stack")


class Task682IntegratedPredictionStackTest(unittest.TestCase):
    def test_five_engine_artifacts_exist(self) -> None:
        for name in [
            "task682_leadership_lifecycle_panel.csv",
            "task682_catalyst_quality_matrix.csv",
            "task682_archetype_candidate_panel.csv",
            "task682_same_symbol_context_matrix.csv",
            "task682_slot_qualification_panel.csv",
            "task682_integrated_stack_panel.csv",
            "task682_simulation_result.csv",
            "task682_guardrail_audit.csv",
            "task_682_integrated_prediction_stack.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK682_DIR / name).exists(), name)

    def test_old_top5_assignment_columns_are_absent(self) -> None:
        stack = pd.read_csv(TASK682_DIR / "task682_integrated_stack_panel.csv", nrows=5)

        self.assertIn("archetype_candidate", stack.columns)
        self.assertIn("leadership_lifecycle_state", stack.columns)
        self.assertIn("catalyst_economic_quality", stack.columns)
        self.assertIn("catalyst_negative_overhang", stack.columns)
        self.assertIn("catalyst_signal_density", stack.columns)
        self.assertIn("same_symbol_prior_setup_count", stack.columns)
        self.assertNotIn("entry_time_archetype_candidate", stack.columns)
        self.assertNotIn("top5_priority_rank", stack.columns)

    def test_forbidden_input_audit_clean(self) -> None:
        forbidden = pd.read_csv(TASK682_DIR / "task682_forbidden_input_audit.csv")

        self.assertEqual(int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum()), 0)

    def test_cohort_slot_candidate_not_promoted(self) -> None:
        grid = pd.read_csv(TASK682_DIR / "task682_simulation_result.csv")
        decision = pd.read_csv(TASK682_DIR / "task_682_decision.csv").iloc[0]

        active = grid[grid["candidate_name"].eq("active_relation_cap3_reference") & grid["split_name"].eq("all")].iloc[0]
        cohort = grid[grid["candidate_name"].eq("integrated_cohort_slot_v1") & grid["split_name"].eq("all")].iloc[0]

        self.assertAlmostEqual(float(active["final_capital_usd"]), 10887.474713480713, places=6)
        self.assertLess(float(cohort["final_capital_usd"]), float(active["final_capital_usd"]))
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_displacement_hurdle_preserves_active_cap3_winners(self) -> None:
        guardrail = pd.read_csv(TASK682_DIR / "task682_guardrail_audit.csv")
        v2 = guardrail[guardrail["candidate_name"].eq("integrated_cohort_slot_displacement_hurdle_v2")].iloc[0]

        self.assertEqual(int(v2["removed_active_cap3_big_winner_count_eval_only"]), 0)
        self.assertEqual(int(v2["winner_preservation_guardrail_pass_flag"]), 1)

    def test_guardrail_detects_removed_active_cap3_winners(self) -> None:
        guardrail = pd.read_csv(TASK682_DIR / "task682_guardrail_audit.csv")
        cohort = guardrail[guardrail["candidate_name"].eq("integrated_cohort_slot_v1")].iloc[0]
        active = guardrail[guardrail["candidate_name"].eq("active_relation_cap3_reference")].iloc[0]

        self.assertEqual(int(active["removed_active_cap3_big_winner_count_eval_only"]), 0)
        self.assertGreater(int(cohort["removed_active_cap3_big_winner_count_eval_only"]), 0)
        self.assertEqual(int(cohort["winner_preservation_guardrail_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
