from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK687_DIR = Path("docs/reports/task_687_information_ontology_logic_audit")


class Task687InformationOntologyLogicAuditTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task687_information_inventory.csv",
            "task687_overlap_audit.csv",
            "task687_logic_gap_audit.csv",
            "task687_relation_engine_scope_audit.csv",
            "task687_firm_grade_target_ontology.csv",
            "task_687_decision.csv",
            "task_687_pass_fail_matrix.csv",
            "task_687_information_ontology_logic_audit.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK687_DIR / name).exists(), name)

    def test_information_groups_cover_required_domains(self) -> None:
        inventory = pd.read_csv(TASK687_DIR / "task687_information_inventory.csv")
        groups = set(inventory["information_group"].astype(str))

        for group in [
            "chart_price_volume",
            "theme_market_leadership",
            "company_source_event_presence",
            "content_positive_negative_interpretation",
            "company_catalyst_quality",
            "macro_context",
            "relation_engine",
            "portfolio_slot_capacity",
            "microstructure",
        ]:
            self.assertIn(group, groups)

    def test_macro_and_microstructure_are_not_overclaimed(self) -> None:
        inventory = pd.read_csv(TASK687_DIR / "task687_information_inventory.csv")
        macro = inventory[inventory["information_group"].eq("macro_context")].iloc[0]
        micro = inventory[inventory["information_group"].eq("microstructure")].iloc[0]

        self.assertEqual(macro["assignment_status"], "diagnostic_only")
        self.assertEqual(micro["assignment_status"], "not_used_pending_raw_feature_builder")

    def test_overlap_and_logic_gaps_are_documented(self) -> None:
        overlap = pd.read_csv(TASK687_DIR / "task687_overlap_audit.csv")
        logic = pd.read_csv(TASK687_DIR / "task687_logic_gap_audit.csv")

        self.assertGreaterEqual(len(overlap), 5)
        self.assertGreaterEqual(int(logic["severity"].eq("high").sum()), 3)

    def test_relation_engine_is_marked_partial_not_firm_grade(self) -> None:
        decision = pd.read_csv(TASK687_DIR / "task_687_decision.csv").iloc[0]
        relation = pd.read_csv(TASK687_DIR / "task687_relation_engine_scope_audit.csv")

        self.assertEqual(decision["relation_engine_status"], "partial_not_full_context_graph")
        self.assertTrue(relation["firm_grade_gap"].astype(str).str.contains("graph|Static|incomplete", case=False).any())
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
