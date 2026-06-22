from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK685_DIR = Path("docs/reports/task_685_data_management_source_readiness_audit")


class Task685DataManagementSourceReadinessAuditTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task685_source_readiness_summary.csv",
            "task685_flag_distribution.csv",
            "task685_active_cap3_source_audit.csv",
            "task685_pipeline_root_cause.csv",
            "task685_guarded_identity_audit.csv",
            "task685_engine_input_readiness_by_split.csv",
            "task_685_decision.csv",
            "task_685_pass_fail_matrix.csv",
            "task_685_data_management_source_readiness_audit.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK685_DIR / name).exists(), name)

    def test_universe_source_gap_and_assignment_ready_zero_are_detected(self) -> None:
        summary = pd.read_csv(TASK685_DIR / "task685_source_readiness_summary.csv")
        universe = summary[summary["scope"].eq("universe_stack")].iloc[0]

        self.assertEqual(int(universe["row_count"]), 1621)
        self.assertEqual(int(universe["source_gap_research_only_count"]), 1621)
        self.assertEqual(int(universe["used_for_assignment_count"]), 0)
        self.assertEqual(int(universe["assignment_ready_count"]), 0)

    def test_active_cap3_is_also_not_assignment_ready(self) -> None:
        summary = pd.read_csv(TASK685_DIR / "task685_source_readiness_summary.csv")
        active = summary[summary["scope"].eq("active_cap3_accepted")].iloc[0]

        self.assertEqual(int(active["row_count"]), 51)
        self.assertEqual(int(active["source_gap_research_only_count"]), 51)
        self.assertEqual(int(active["assignment_ready_count"]), 0)

    def test_pipeline_root_cause_contains_hardcoded_assignment_zero(self) -> None:
        root = pd.read_csv(TASK685_DIR / "task685_pipeline_root_cause.csv")

        self.assertIn(
            "used_for_assignment_flag_hardcoded_zero",
            set(root["issue_id"].astype(str)),
        )

    def test_guarded_identity_explains_same_result(self) -> None:
        guarded = pd.read_csv(TASK685_DIR / "task685_guarded_identity_audit.csv")

        challenger = guarded[guarded["audit_item"].eq("accepted_context_superiority_challenger")].iloc[0]
        baseline = guarded[guarded["audit_item"].eq("accepted_baseline_context_preserved")].iloc[0]
        final_delta = guarded[guarded["audit_item"].eq("final_capital_identity_check")].iloc[0]

        self.assertEqual(int(challenger["metric_value"]), 0)
        self.assertEqual(int(baseline["metric_value"]), 51)
        self.assertAlmostEqual(float(final_delta["metric_value"]), 0.0, places=6)

    def test_decision_remains_forbidden(self) -> None:
        decision = pd.read_csv(TASK685_DIR / "task_685_decision.csv").iloc[0]

        self.assertEqual(decision["verdict"], "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
