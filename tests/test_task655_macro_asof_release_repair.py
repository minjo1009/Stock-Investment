from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_655_macro_asof_release_repair")


class Task655MacroAsofReleaseRepairTest(unittest.TestCase):
    def test_decision_keeps_trading_blocked(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_655_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(float(decision["task639_strict_assignment_eligible_rate"]), 0.0)

    def test_release_repair_covers_task639_core(self) -> None:
        coverage = pd.read_csv(REPORT_DIR / "task_655_coverage_after_release_repair.csv")
        task639 = coverage[coverage["scope"].eq("task639_core_delay1d_existing")].iloc[0]

        self.assertEqual(int(task639["row_count"]), 1621)
        self.assertGreaterEqual(float(task639["release_timestamp_repaired_rate"]), 0.95)
        self.assertGreaterEqual(float(task639["provisional_diagnostic_eligible_rate"]), 0.95)
        self.assertEqual(float(task639["strict_assignment_eligible_rate"]), 0.0)

    def test_vintage_still_blocks_assignment(self) -> None:
        source = pd.read_csv(REPORT_DIR / "task_655_macro_source_audit.csv")

        self.assertTrue(pd.to_numeric(source["release_time_repaired_flag"], errors="coerce").eq(1).all())
        self.assertTrue(pd.to_numeric(source["latest_vintage_only_flag"], errors="coerce").eq(1).all())
        self.assertTrue(pd.to_numeric(source["vintage_asof_certified_flag"], errors="coerce").eq(0).all())

    def test_pass_fail_has_expected_blockers(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_655_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(gates["release_timestamp_repair_built"], 1)
        self.assertEqual(gates["task639_core_release_repair_coverage"], 1)
        self.assertEqual(gates["vintage_asof_certified"], 0)
        self.assertEqual(gates["strict_assignment_eligible"], 0)


if __name__ == "__main__":
    unittest.main()
