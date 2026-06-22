from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK693_DIR = Path("docs/reports/task_693_source_packet_v2_price_packet")
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


class Task693SourcePacketV2PricePacketTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task693_source_packet_interpreter_v2_rulebook.csv",
            "task693_source_event_v2_evidence.csv",
            "task693_leader_source_packet_v2_review.csv",
            "task693_price_absorption_review_ready_packet.csv",
            "task693_integrity_audit.csv",
            "task_693_decision.csv",
            "task_693_pass_fail_matrix.csv",
            "task_693_source_packet_v2_price_packet.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK693_DIR / name).exists(), name)

    def test_source_packet_and_price_packet_counts(self) -> None:
        events = pd.read_csv(TASK693_DIR / "task693_source_event_v2_evidence.csv")
        leader = pd.read_csv(TASK693_DIR / "task693_leader_source_packet_v2_review.csv")
        price = pd.read_csv(TASK693_DIR / "task693_price_absorption_review_ready_packet.csv")

        self.assertEqual(leader["lifecycle_id"].nunique(), 19)
        self.assertGreater(len(events), 19)
        self.assertEqual(len(price), 2)

    def test_v2_interpreter_separates_source_states(self) -> None:
        events = pd.read_csv(TASK693_DIR / "task693_source_event_v2_evidence.csv")
        leader = pd.read_csv(TASK693_DIR / "task693_leader_source_packet_v2_review.csv")

        self.assertGreaterEqual(events["source_event_v2_state"].nunique(), 3)
        self.assertGreaterEqual(leader["source_packet_v2_state"].nunique(), 2)

    def test_no_outcome_columns_in_task693_outputs(self) -> None:
        for name in [
            "task693_source_event_v2_evidence.csv",
            "task693_leader_source_packet_v2_review.csv",
            "task693_price_absorption_review_ready_packet.csv",
        ]:
            frame = pd.read_csv(TASK693_DIR / name, nrows=1)
            self.assertFalse(FORBIDDEN_COLUMNS.intersection(frame.columns), name)

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK693_DIR / "task693_integrity_audit.csv")
        decision = pd.read_csv(TASK693_DIR / "task_693_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
