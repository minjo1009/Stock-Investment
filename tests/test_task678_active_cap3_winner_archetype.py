from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK678_DIR = Path("docs/reports/task_678_active_cap3_winner_archetype")


class Task678ActiveCap3WinnerArchetypeTest(unittest.TestCase):
    def test_max_position_comparison_preserves_active_cap3_reference(self) -> None:
        grid = pd.read_csv(TASK678_DIR / "task678_max_position_comparison.csv")

        active5 = grid[grid["candidate_name"].eq("active_relation_cap3_reference") & grid["split_name"].eq("all")].iloc[0]
        active10 = grid[grid["candidate_name"].eq("active_relation_cap3_max10") & grid["split_name"].eq("all")].iloc[0]

        self.assertAlmostEqual(float(active5["final_capital_usd"]), 10887.474713480713, places=6)
        self.assertEqual(int(active5["max_positions"]), 5)
        self.assertEqual(int(active10["max_positions"]), 10)
        self.assertGreater(int(active10["accepted_trade_count"]), int(active5["accepted_trade_count"]))
        self.assertTrue(pd.to_numeric(grid["return_used_in_assignment_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(grid["label_used_in_assignment_flag"], errors="coerce").eq(0).all())

    def test_winner_archetype_outputs_are_diagnostic_only(self) -> None:
        archetypes = pd.read_csv(TASK678_DIR / "task678_winner_archetype_study.csv")
        preservation = pd.read_csv(TASK678_DIR / "task678_winner_preservation_audit.csv")
        decision = pd.read_csv(TASK678_DIR / "task_678_decision.csv").iloc[0]

        self.assertFalse(archetypes.empty)
        self.assertGreaterEqual(archetypes["winner_archetype"].nunique(), 4)
        self.assertGreater(int(pd.to_numeric(archetypes["big_winner_count_eval_only"], errors="coerce").sum()), 0)
        self.assertGreater(int(pd.to_numeric(preservation["removed_active_cap3_big_winner_count_eval_only"], errors="coerce").max()), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_five_requested_studies_exist(self) -> None:
        for name in [
            "task678_winner_archetype_study.csv",
            "task678_same_symbol_divergence.csv",
            "task678_catalyst_path_study.csv",
            "task678_winner_preservation_audit.csv",
            "task678_slot_competition_study.csv",
            "task678_max10_delta.csv",
            "task_678_active_cap3_winner_archetype.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK678_DIR / name).exists(), name)

    def test_max10_capacity_probe_is_not_promoted(self) -> None:
        gates = pd.read_csv(TASK678_DIR / "task_678_pass_fail_matrix.csv")
        max10_return_gate = gates[gates["gate_name"].eq("max10_beats_active_cap3_max5_return")].iloc[0]
        strategy_gate = gates[gates["gate_name"].eq("strategy_accepted")].iloc[0]

        self.assertEqual(int(max10_return_gate["pass_flag"]), 0)
        self.assertEqual(int(strategy_gate["pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
