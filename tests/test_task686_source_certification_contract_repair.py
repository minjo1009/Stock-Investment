from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK686_DIR = Path("docs/reports/task_686_source_certification_contract_repair")


class Task686SourceCertificationContractRepairTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task686_source_certification_summary.csv",
            "task686_macro_assignment_usage_audit.csv",
            "task686_allocation_provenance_audit.csv",
            "task686_guarded_post_repair_audit.csv",
            "task686_gpt_review_pack.csv",
            "task_686_decision.csv",
            "task_686_pass_fail_matrix.csv",
            "task_686_source_certification_contract_repair.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK686_DIR / name).exists(), name)

    def test_source_gap_collapse_is_fixed(self) -> None:
        summary = pd.read_csv(TASK686_DIR / "task686_source_certification_summary.csv")
        core = summary[summary["scope"].eq("task672_core_panel")].iloc[0]

        self.assertEqual(int(core["row_count"]), 1621)
        self.assertEqual(int(core["source_gap_research_only_count"]), 0)
        self.assertEqual(int(core["allocation_assignment_ready_count"]), 1621)
        self.assertEqual(int(core["company_certified_macro_provisional_count"]), 1621)

    def test_macro_remains_diagnostic_only(self) -> None:
        macro = pd.read_csv(TASK686_DIR / "task686_macro_assignment_usage_audit.csv")
        core = macro[macro["scope"].eq("task672_core_panel")].iloc[0]

        self.assertEqual(int(core["macro_assignment_certified_count"]), 0)
        self.assertEqual(int(core["macro_used_for_assignment_count"]), 0)
        self.assertEqual(int(core["macro_provisional_used_as_certified_count"]), 0)
        self.assertEqual(int(core["missing_source_used_as_negative_count"]), 0)

    def test_allocation_provenance_is_preserved(self) -> None:
        provenance = pd.read_csv(TASK686_DIR / "task686_allocation_provenance_audit.csv")

        self.assertTrue(pd.to_numeric(provenance["present_flag"], errors="coerce").eq(1).all())
        self.assertGreater(int(pd.to_numeric(provenance["non_null_count"], errors="coerce").min()), 0)

    def test_guarded_remaining_blocker_is_not_all_row_source_collapse(self) -> None:
        guarded = pd.read_csv(TASK686_DIR / "task686_guarded_post_repair_audit.csv")
        challenger = guarded[guarded["audit_item"].eq("accepted_context_superiority_challenger")].iloc[0]
        source_failed = guarded[guarded["audit_item"].eq("superiority_failed_source")].iloc[0]

        self.assertEqual(int(challenger["metric_value"]), 0)
        self.assertLess(int(source_failed["metric_value"]), 1621)

    def test_decision_remains_not_promoted(self) -> None:
        decision = pd.read_csv(TASK686_DIR / "task_686_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
