from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_654_relation_engine_audit_upgrade")


class Task654RelationEngineAuditUpgradeTest(unittest.TestCase):
    def test_decision_blocks_relation_authority(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_654_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["promotion_candidate_count"]), 0)

    def test_join_contract_has_required_authority_fields(self) -> None:
        audit = pd.read_csv(REPORT_DIR / "join_contract_audit.csv")
        required = {
            "macro_join_key",
            "company_join_key",
            "macro_join_status",
            "company_join_status",
            "asof_valid_flag",
            "latest_vintage_gap_flag",
            "used_for_assignment_flag",
            "used_for_diagnostic_only_flag",
        }

        self.assertGreater(len(audit), 0)
        self.assertTrue(required.issubset(set(audit.columns)))
        self.assertGreater(pd.to_numeric(audit["used_for_diagnostic_only_flag"], errors="coerce").sum(), 0)

    def test_coverage_scope_marks_task639_assignment_gap(self) -> None:
        coverage = pd.read_csv(REPORT_DIR / "coverage_scope_report.csv")
        task639 = coverage[coverage["scope"].eq("task639_core_delay1d_existing")].iloc[0]

        self.assertGreater(int(task639["row_count"]), 0)
        self.assertLess(float(task639["assignment_eligible_rate"]), 0.80)

    def test_baseline_and_promotion_reports_exist(self) -> None:
        baseline = pd.read_csv(REPORT_DIR / "baseline_preservation_audit.csv")
        promotion = pd.read_csv(REPORT_DIR / "promotion_eligibility_report.csv")

        self.assertGreater(int(baseline["row_count"].sum()), 0)
        self.assertEqual(int(promotion["promotion_pass_flag"].sum()), 0)


if __name__ == "__main__":
    unittest.main()
