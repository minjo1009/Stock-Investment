from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK679_DIR = Path("docs/reports/task_679_top5_qualification_engine")


class Task679Top5QualificationEngineTest(unittest.TestCase):
    def test_top5_columns_and_forbidden_inputs_are_clean(self) -> None:
        panel = pd.read_csv(TASK679_DIR / "task679_entry_time_archetype_panel.csv")

        for col in [
            "entry_time_archetype_candidate",
            "entry_time_catalyst_path",
            "top5_qualification_tier",
            "top5_priority_rank",
        ]:
            self.assertIn(col, panel.columns)

        self.assertEqual(int(pd.to_numeric(panel["top5_return_used_in_assignment_flag"], errors="coerce").sum()), 0)
        self.assertEqual(int(pd.to_numeric(panel["top5_label_used_in_assignment_flag"], errors="coerce").sum()), 0)
        self.assertEqual(int(pd.to_numeric(panel["top5_future_price_used_in_assignment_flag"], errors="coerce").sum()), 0)

    def test_active_cap3_reference_is_preserved_and_new_rules_are_not_promoted(self) -> None:
        grid = pd.read_csv(TASK679_DIR / "task679_top5_candidate_grid.csv")
        decision = pd.read_csv(TASK679_DIR / "task_679_decision.csv").iloc[0]

        active = grid[grid["candidate_name"].eq("active_relation_cap3_reference") & grid["split_name"].eq("all")].iloc[0]
        top5 = grid[grid["candidate_name"].eq("top5_qualification_priority_v1") & grid["split_name"].eq("all")].iloc[0]

        self.assertAlmostEqual(float(active["final_capital_usd"]), 10887.474713480713, places=6)
        self.assertLess(float(top5["final_capital_usd"]), float(active["final_capital_usd"]))
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_winner_preservation_guardrail_flags_removed_big_winners(self) -> None:
        guardrail = pd.read_csv(TASK679_DIR / "task679_winner_preservation_guardrail.csv")

        active = guardrail[guardrail["candidate_name"].eq("active_relation_cap3_reference")].iloc[0]
        priority = guardrail[guardrail["candidate_name"].eq("top5_qualification_priority_v1")].iloc[0]
        elite_only = guardrail[guardrail["candidate_name"].eq("top5_elite_contender_only_probe")].iloc[0]

        self.assertEqual(int(active["winner_preservation_guardrail_pass_flag"]), 1)
        self.assertEqual(int(active["removed_active_cap3_big_winner_count_eval_only"]), 0)
        self.assertEqual(int(priority["winner_preservation_guardrail_pass_flag"]), 0)
        self.assertGreater(int(priority["removed_active_cap3_big_winner_count_eval_only"]), 0)
        self.assertGreater(int(elite_only["removed_active_cap3_big_winner_count_eval_only"]), 0)

    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task679_top5_rule_matrix.csv",
            "task679_archetype_candidate_performance.csv",
            "task679_qualification_tier_performance.csv",
            "task679_slot_qualification_audit.csv",
            "task_679_top5_qualification_engine.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK679_DIR / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
