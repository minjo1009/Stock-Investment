from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_661_mechanism_relation_engine")


class Task661MechanismRelationEngineTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_661_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_transmission_template_is_not_return_tuned(self) -> None:
        template = pd.read_csv(REPORT_DIR / "institutional_transmission_template.csv")
        required = {
            "theme_id",
            "capital_intensity",
            "funding_sensitivity",
            "duration_sensitivity",
            "energy_sensitivity",
            "capex_demand_sensitivity",
            "policy_sensitivity",
            "liquidity_sensitivity",
            "return_tuned_flag",
        }

        self.assertTrue(required.issubset(set(template.columns)))
        self.assertEqual(len(template), 10)
        self.assertTrue(pd.to_numeric(template["return_tuned_flag"], errors="coerce").eq(0).all())

    def test_mechanism_panel_has_five_bottleneck_fields(self) -> None:
        panel = pd.read_csv(
            REPORT_DIR / "theme_mechanism_state_panel.csv",
            usecols=[
                "lifecycle_id",
                "catalyst_quality_tier",
                "price_acceptance_state",
                "mechanism_relation_state",
                "candidate_action_family",
                "scenario_base_case",
                "scenario_invalidation_condition",
                "used_for_assignment_flag",
                "allocation_assignment_ready_flag",
                "company_source_assignment_certified_flag",
                "macro_assignment_certified_flag",
                "macro_used_for_assignment_flag",
                "macro_provisional_used_as_certified",
                "return_used_in_assignment_flag",
            ],
        )

        self.assertGreater(len(panel), 0)
        self.assertTrue(panel["catalyst_quality_tier"].notna().all())
        self.assertTrue(panel["price_acceptance_state"].notna().all())
        self.assertTrue(panel["scenario_invalidation_condition"].notna().all())
        self.assertGreater(int(pd.to_numeric(panel["used_for_assignment_flag"], errors="coerce").sum()), 0)
        self.assertTrue(
            pd.to_numeric(panel["used_for_assignment_flag"], errors="coerce")
            .eq(pd.to_numeric(panel["allocation_assignment_ready_flag"], errors="coerce"))
            .all()
        )
        self.assertGreater(int(pd.to_numeric(panel["company_source_assignment_certified_flag"], errors="coerce").sum()), 0)
        self.assertTrue(pd.to_numeric(panel["macro_assignment_certified_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(panel["macro_used_for_assignment_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(panel["macro_provisional_used_as_certified"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(panel["return_used_in_assignment_flag"], errors="coerce").eq(0).all())

    def test_oos_and_attribution_artifacts_exist(self) -> None:
        oos = pd.read_csv(REPORT_DIR / "oos_effect_audit.csv")
        attribution = pd.read_csv(REPORT_DIR / "accepted_trade_attribution.csv")

        self.assertIn("changed_trade_count", set(oos.columns))
        self.assertIn("avg_return_delta_pct_point", set(oos.columns))
        self.assertIn("task639_accepted_flag", set(attribution.columns))
        self.assertIn("task661_accepted_flag", set(attribution.columns))
        self.assertGreater(len(attribution), 0)

    def test_forbidden_macro_authority_not_used(self) -> None:
        blockers = pd.read_csv(REPORT_DIR / "not_do_matrix.csv")

        self.assertTrue(pd.to_numeric(blockers["pass_flag"], errors="coerce").eq(1).all())

    def test_promotion_report_matches_decision(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "promotion_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_661_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), int(decision["promotion_candidate_count"]))
        self.assertIn("validation_improves_task639_flag", set(promotion.columns))
        self.assertIn("recent_oos_improves_task639_flag", set(promotion.columns))

    def test_relation_engine_does_not_add_fixed_hold_exit_rules(self) -> None:
        grid = pd.read_csv(REPORT_DIR / "mechanism_soft_wrapper_grid.csv")
        names = " ".join(grid["candidate_name"].astype(str).tolist())

        self.assertNotIn("hold5", names)
        self.assertNotIn("hold10", names)
        self.assertNotIn("hold20", names)
        self.assertIn("diagnostic_relation_state_only_no_exit_override", set(grid["candidate_name"].astype(str)))


if __name__ == "__main__":
    unittest.main()
