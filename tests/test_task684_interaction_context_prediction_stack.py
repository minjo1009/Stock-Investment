from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK684_DIR = Path("docs/reports/task_684_interaction_context_prediction_stack")


class Task684InteractionContextPredictionStackTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task684_leadership_lifecycle_interaction_panel.csv",
            "task684_catalyst_quality_interaction_matrix.csv",
            "task684_archetype_candidate_interaction_engine.csv",
            "task684_same_symbol_context_interaction_matrix.csv",
            "task684_interaction_stack_panel.csv",
            "task684_simulation_result.csv",
            "task684_cohort_slot_qualification.csv",
            "task684_guardrail_audit.csv",
            "task684_forbidden_input_audit.csv",
            "task_684_decision.csv",
            "task_684_pass_fail_matrix.csv",
            "task_684_interaction_context_prediction_stack.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK684_DIR / name).exists(), name)

    def test_five_interaction_columns_exist_without_global_top5_rank(self) -> None:
        stack = pd.read_csv(TASK684_DIR / "task684_interaction_stack_panel.csv", nrows=5)

        self.assertIn("leadership_phase_strength", stack.columns)
        self.assertIn("catalyst_absorption_state", stack.columns)
        self.assertIn("archetype_interaction_context", stack.columns)
        self.assertIn("same_symbol_interaction_state", stack.columns)
        self.assertNotIn("top5_priority_rank", stack.columns)

    def test_forbidden_input_audit_clean(self) -> None:
        forbidden = pd.read_csv(TASK684_DIR / "task684_forbidden_input_audit.csv")

        self.assertEqual(int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum()), 0)

    def test_interaction_candidates_remain_research_only(self) -> None:
        decision = pd.read_csv(TASK684_DIR / "task_684_decision.csv").iloc[0]

        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_guarded_candidate_preserves_big_winners(self) -> None:
        guardrail = pd.read_csv(TASK684_DIR / "task684_guardrail_audit.csv")
        guarded = guardrail[guardrail["candidate_name"].eq("interaction_context_superiority_guarded_v3")].iloc[0]

        self.assertEqual(int(guarded["removed_active_cap3_big_winner_count_eval_only"]), 0)
        self.assertEqual(int(guarded["winner_preservation_guardrail_pass_flag"]), 1)


if __name__ == "__main__":
    unittest.main()
