from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK683_DIR = Path("docs/reports/task_683_firm_grade_context_gather_5_engine_review")


class Task683FirmGradeContextGatherTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task683_engine_distribution_audit.csv",
            "task683_engine_context_gap_audit.csv",
            "task683_active_mixed_context_decomposition.csv",
            "task683_active_catalyst_low_reinterpretation.csv",
            "task683_same_symbol_conflict_interpreter.csv",
            "task683_context_superiority_contract.csv",
            "task683_method_context_sources.csv",
            "task_683_decision.csv",
            "task_683_pass_fail_matrix.csv",
            "task_683_firm_grade_context_gather_5_engine_review.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK683_DIR / name).exists(), name)

    def test_active_problem_buckets_are_decomposed(self) -> None:
        mixed = pd.read_csv(TASK683_DIR / "task683_active_mixed_context_decomposition.csv")
        catalyst_low = pd.read_csv(TASK683_DIR / "task683_active_catalyst_low_reinterpretation.csv")
        same_symbol = pd.read_csv(TASK683_DIR / "task683_same_symbol_conflict_interpreter.csv")

        self.assertGreaterEqual(len(mixed), 1)
        self.assertGreaterEqual(len(catalyst_low), 1)
        self.assertGreaterEqual(len(same_symbol), 1)
        self.assertIn("mixed_sub_context", mixed.columns)
        self.assertIn("catalyst_low_reinterpretation", catalyst_low.columns)
        self.assertIn("same_symbol_conflict_interpretation", same_symbol.columns)

    def test_no_strategy_promotion(self) -> None:
        decision = pd.read_csv(TASK683_DIR / "task_683_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_superiority_contract_stays_inside_five_engines(self) -> None:
        contract = pd.read_csv(TASK683_DIR / "task683_context_superiority_contract.csv")
        dimensions = set(contract["packet_dimension"].astype(str))

        self.assertIn("catalyst_absorption", dimensions)
        self.assertIn("archetype_context", dimensions)
        self.assertIn("same_symbol", dimensions)
        self.assertIn("tiebreak", dimensions)
        self.assertEqual(int(pd.to_numeric(contract["return_used_in_assignment_flag"], errors="coerce").sum()), 0)


if __name__ == "__main__":
    unittest.main()
