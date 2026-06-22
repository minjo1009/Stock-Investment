from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK692_DIR = Path("docs/reports/task_692_source_packet_price_absorption")
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


class Task692SourcePacketPriceAbsorptionTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task692_confirmation_rulebook.csv",
            "task692_leader_source_packet_review.csv",
            "task692_price_absorption_confirmation_panel.csv",
            "task692_confirmation_readiness_summary.csv",
            "task692_integrity_audit.csv",
            "task_692_decision.csv",
            "task_692_pass_fail_matrix.csv",
            "task_692_source_packet_price_absorption.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK692_DIR / name).exists(), name)

    def test_target_counts_match_task691(self) -> None:
        source = pd.read_csv(TASK692_DIR / "task692_leader_source_packet_review.csv")
        price = pd.read_csv(TASK692_DIR / "task692_price_absorption_confirmation_panel.csv")
        decision = pd.read_csv(TASK692_DIR / "task_692_decision.csv").iloc[0]

        self.assertEqual(len(source), 19)
        self.assertEqual(len(price), 293)
        self.assertEqual(int(decision["leader_source_packet_review_count"]), 19)
        self.assertEqual(int(decision["price_absorption_review_count"]), 293)

    def test_confirmation_states_are_decomposed(self) -> None:
        source = pd.read_csv(TASK692_DIR / "task692_leader_source_packet_review.csv")
        price = pd.read_csv(TASK692_DIR / "task692_price_absorption_confirmation_panel.csv")

        self.assertGreaterEqual(source["source_packet_state"].nunique(), 1)
        self.assertTrue(source["source_packet_verdict"].isin(["not_promotable", "review_ready_not_trade_approved", "research_only_needs_better_source_packet"]).all())
        self.assertGreaterEqual(price["price_absorption_state"].nunique(), 2)

    def test_no_outcome_columns_in_confirmation_outputs(self) -> None:
        for name in [
            "task692_leader_source_packet_review.csv",
            "task692_price_absorption_confirmation_panel.csv",
            "task692_confirmation_readiness_summary.csv",
        ]:
            frame = pd.read_csv(TASK692_DIR / name, nrows=1)
            self.assertFalse(FORBIDDEN_COLUMNS.intersection(frame.columns), name)

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK692_DIR / "task692_integrity_audit.csv")
        decision = pd.read_csv(TASK692_DIR / "task_692_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
