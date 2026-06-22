from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK712_DIR = Path("docs/reports/task_712_firm_grade_translator_engine")


class Task712FirmGradeTranslatorEngineTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task712_context_gather_source_map.csv",
            "task712_context_state_panel.csv",
            "task712_interaction_matrix.csv",
            "task712_review_packet.csv",
            "task712_guardrail_audit.csv",
            "task712_governance_audit.csv",
            "task_712_decision.csv",
            "task_712_pass_fail_matrix.csv",
            "task_712_firm_grade_translator_engine.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK712_DIR / name).exists(), name)

    def test_scope_context_states_and_no_action_output(self) -> None:
        panel = pd.read_csv(TASK712_DIR / "task712_context_state_panel.csv")

        self.assertEqual(len(panel), 5265)
        self.assertEqual(int(panel["source_event_available_flag"].sum()), 2445)
        self.assertGreaterEqual(panel["firm_grade_context_state"].nunique(), 6)
        self.assertGreaterEqual(panel["financing_context_state"].nunique(), 4)
        self.assertGreaterEqual(panel["high_noise_context_state"].nunique(), 4)
        self.assertGreaterEqual(panel["low_novelty_context_state"].nunique(), 4)
        self.assertEqual(int(panel["translator_output_is_action_flag"].sum()), 0)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["missing_source_used_as_negative_flag"].sum()), 0)
        self.assertEqual(int(panel["macro_used_for_assignment_flag"].sum()), 0)

    def test_context_gather_source_map(self) -> None:
        source_map = pd.read_csv(TASK712_DIR / "task712_context_gather_source_map.csv")

        self.assertGreaterEqual(len(source_map), 8)
        self.assertTrue(source_map["url"].str.startswith("https://").all())
        self.assertIn("official_research", set(source_map["source_type"]))
        self.assertIn("institution_research", set(source_map["source_type"]))
        self.assertIn("academic_research", set(source_map["source_type"]))

    def test_interaction_and_guardrail_outputs(self) -> None:
        interaction = pd.read_csv(TASK712_DIR / "task712_interaction_matrix.csv")
        guardrail = pd.read_csv(TASK712_DIR / "task712_guardrail_audit.csv")

        self.assertGreater(len(interaction), 0)
        self.assertEqual(int(interaction["candidate_count"].sum()), 5265)
        self.assertGreater(len(guardrail), 0)
        self.assertEqual(int(guardrail["candidate_count"].sum()), 5265)
        self.assertEqual(int(guardrail["top50_winner_count"].sum()), 50)
        self.assertEqual(int(guardrail["bottom50_loser_count"].sum()), 50)
        self.assertEqual(int(guardrail["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(set(guardrail["outcome_used_for_evaluation_flag"]), {1})

    def test_decision_and_pass_fail(self) -> None:
        decision = pd.read_csv(TASK712_DIR / "task_712_decision.csv").iloc[0]
        pass_fail = pd.read_csv(TASK712_DIR / "task_712_pass_fail_matrix.csv")
        governance = pd.read_csv(TASK712_DIR / "task712_governance_audit.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertEqual(int(governance["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
