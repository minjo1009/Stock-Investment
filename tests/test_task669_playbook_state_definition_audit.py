from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_669_playbook_state_definition_audit")


class Task669PlaybookStateDefinitionAuditTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_669_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_redefinition_candidates_exist(self) -> None:
        candidates = pd.read_csv(REPORT_DIR / "task669_redefinition_candidates.csv")

        self.assertGreater(len(candidates), 0)
        self.assertIn("confirmation_required", set(candidates["playbook_id"].astype(str)))
        self.assertIn("normal_participation", set(candidates["playbook_id"].astype(str)))

    def test_confirmation_required_positive_payoff_is_visible(self) -> None:
        perf = pd.read_csv(REPORT_DIR / "task669_state_performance_audit.csv")
        row = perf[perf["playbook_id"].eq("confirmation_required")].iloc[0]

        self.assertGreater(float(row["avg_return_pct"]), 50.0)
        self.assertEqual(int(row["high_return_state_flag"]), 1)

    def test_normal_participation_mdd_exposure_is_visible(self) -> None:
        mdd = pd.read_csv(REPORT_DIR / "task669_mdd_state_audit.csv")
        row = mdd[(mdd["audit_group"].eq("playbook_id")) & (mdd["group_value"].eq("normal_participation"))].iloc[0]

        self.assertLess(float(row["avg_return_costed_pct"]), 0.0)
        self.assertEqual(int(row["negative_mdd_exposure_flag"]), 1)

    def test_state_purity_flags_mixed_states(self) -> None:
        purity = pd.read_csv(REPORT_DIR / "task669_state_purity_audit.csv")

        self.assertGreater(int(pd.to_numeric(purity["mixed_state_flag"], errors="coerce").sum()), 0)

    def test_required_artifacts_exist(self) -> None:
        for filename in [
            "task669_state_component_mix.csv",
            "task669_state_purity_audit.csv",
            "task669_state_performance_audit.csv",
            "task669_mdd_state_audit.csv",
            "task669_playbook_catalyst_matrix.csv",
            "task669_redefinition_candidates.csv",
        ]:
            self.assertTrue((REPORT_DIR / filename).exists(), filename)


if __name__ == "__main__":
    unittest.main()
