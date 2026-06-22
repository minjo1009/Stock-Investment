from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK690_DIR = Path("docs/reports/task_690_slot_replacement_hurdle")
FORBIDDEN_COLUMNS = {
    "net_return_from_entry",
    "net_return_pct",
    "return_pct",
    "win_flag",
    "win_eval_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "simulated_exit_price",
    "simulated_exit_ts",
}


class Task690SlotReplacementHurdleTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task690_slot_replacement_rulebook.csv",
            "task690_cohort_slot_competition_panel.csv",
            "task690_slot_claim_explanation_v2.csv",
            "task690_slot_hurdle_decomposition.csv",
            "task690_integrity_audit.csv",
            "task_690_decision.csv",
            "task_690_pass_fail_matrix.csv",
            "task_690_slot_replacement_hurdle.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK690_DIR / name).exists(), name)

    def test_same_timestamp_scope_only(self) -> None:
        panel = pd.read_csv(TASK690_DIR / "task690_cohort_slot_competition_panel.csv")

        self.assertTrue(panel["same_timestamp_rank_scope"].eq("same_entry_ts_split_only").all())
        self.assertNotIn("global_rank", panel.columns)
        self.assertGreater(panel["cohort_id"].nunique(), 1)

    def test_slot_hurdle_is_decomposed(self) -> None:
        panel = pd.read_csv(TASK690_DIR / "task690_cohort_slot_competition_panel.csv")
        hurdle = panel[panel["slot_replacement_hurdle_required_flag"].eq(1)]

        self.assertGreater(len(hurdle), 0)
        self.assertGreaterEqual(hurdle["replacement_hurdle_state"].nunique(), 3)
        self.assertGreaterEqual(panel["slot_claim_tier"].nunique(), 3)

    def test_no_outcome_columns_in_slot_outputs(self) -> None:
        for name in [
            "task690_cohort_slot_competition_panel.csv",
            "task690_slot_claim_explanation_v2.csv",
            "task690_slot_hurdle_decomposition.csv",
        ]:
            frame = pd.read_csv(TASK690_DIR / name, nrows=1)
            self.assertFalse(FORBIDDEN_COLUMNS.intersection(frame.columns), name)

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK690_DIR / "task690_integrity_audit.csv")
        decision = pd.read_csv(TASK690_DIR / "task_690_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
