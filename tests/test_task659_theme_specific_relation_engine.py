from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_659_theme_specific_relation_engine")


class Task659ThemeSpecificRelationEngineTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_659_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_exposure_matrix_covers_active_themes(self) -> None:
        exposure = pd.read_csv(REPORT_DIR / "theme_macro_exposure_matrix.csv")
        panel = pd.read_csv(REPORT_DIR / "theme_macro_company_state_panel.csv", usecols=["theme_id"])

        active = set(panel["theme_id"].dropna().astype(str))
        mapped = set(exposure["theme_id"].dropna().astype(str))
        self.assertTrue(active.issubset(mapped))
        self.assertEqual(len(mapped), 10)

    def test_driver_conflicts_are_split(self) -> None:
        driver = pd.read_csv(REPORT_DIR / "task659_driver_conflict_panel.csv")
        required = {"rates_conflict", "oil_conflict", "dollar_conflict", "credit_conflict", "liquidity_conflict", "conflict_count"}

        self.assertTrue(required.issubset(set(driver.columns)))
        self.assertGreater(len(driver), 0)

    def test_forbidden_macro_authority_not_used(self) -> None:
        blockers = pd.read_csv(REPORT_DIR / "not_do_matrix.csv")

        self.assertTrue(pd.to_numeric(blockers["pass_flag"], errors="coerce").eq(1).all())

    def test_promotion_count_matches_report(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "promotion_eligibility_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_659_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), int(decision["promotion_candidate_count"]))
        self.assertIn("oos_effect_nonzero_flag", set(promotion.columns))


if __name__ == "__main__":
    unittest.main()
