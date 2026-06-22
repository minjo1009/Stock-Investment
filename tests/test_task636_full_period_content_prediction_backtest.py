from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task636_full_period_content_prediction_backtest import score_event_text


REPORT_DIR = Path("docs/reports/task_636_full_period_content_prediction_backtest")


class Task636FullPeriodContentPredictionBacktestTest(unittest.TestCase):
    def test_source_text_and_content_prediction_coverage(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_636_decision.csv").iloc[0]
        source_audit = pd.read_csv(REPORT_DIR / "task_636_source_and_prediction_coverage_audit.csv").iloc[0]

        self.assertEqual(int(decision["unique_linked_event_count"]), 3319)
        self.assertEqual(int(decision["source_text_certified_event_count"]), int(decision["unique_linked_event_count"]))
        self.assertGreaterEqual(int(decision["entries_with_content_prediction_count"]), 1800)
        self.assertEqual(int(source_audit["presence_field_used_for_assignment_flag"]), 0)
        self.assertEqual(int(source_audit["label_used_in_assignment_flag"]), 0)

    def test_sec_ownership_and_financing_contexts_are_not_economic_catalysts(self) -> None:
        cases = [
            (
                {
                    "event_title": "ABC FORM 4",
                    "source_lane": "institution_investment_actions",
                    "event_category": "insider_or_sale_notice",
                },
                "Form 4 non-derivative securities. Common stock acquired. Officer director purchase or sale of securities.",
                "ownership_or_insider_filing_blocker",
            ),
            (
                {
                    "event_title": "ABC SC 13G",
                    "source_lane": "institution_investment_actions",
                    "event_category": "passive_13g",
                },
                "Schedule 13G beneficial ownership. Reporting person has sole voting power and shared voting power.",
                "ownership_or_insider_filing_blocker",
            ),
            (
                {
                    "event_title": "ABC 8-K",
                    "source_lane": "ceo_ir_transcripts_and_presentations",
                    "event_category": "company_filing",
                },
                "Item 1.01 Entry into a Material Definitive Agreement. Securities purchase agreement with warrants and an exhibit 10.1.",
                "financing_context_requires_separate_review",
            ),
            (
                {
                    "event_title": "ABC 8-K",
                    "source_lane": "ceo_ir_transcripts_and_presentations",
                    "event_category": "company_filing",
                },
                "Annual meeting results. Approved compensation paid to named executive officers and elected director nominees to the board of directors.",
                "governance_or_compensation_filing_blocker",
            ),
        ]

        for row, text, blocker in cases:
            scored = score_event_text(pd.Series(row), text)
            self.assertEqual(scored["economic_evidence_certified_flag"], 0)
            self.assertEqual(scored["content_revenue_or_backlog_signal"], 0)
            self.assertEqual(scored["content_guidance_or_margin_signal"], 0)
            self.assertEqual(scored["content_supply_demand_signal"], 0)
            self.assertEqual(scored["interpretation_blocker"], blocker)
            self.assertNotEqual(scored["content_stock_specific_causal_link"], "company_direct_economic_update")

    def test_substring_matches_do_not_create_fake_backlog_or_sales(self) -> None:
        scored = score_event_text(
            pd.Series(
                {
                    "event_title": "ABC 8-K",
                    "source_lane": "ceo_ir_transcripts_and_presentations",
                    "event_category": "company_filing",
                }
            ),
            "The company approved proposals at the annual meeting and filed the report with the corporation secretary.",
        )

        self.assertEqual(scored["content_revenue_or_backlog_signal"], 0)
        self.assertEqual(scored["economic_evidence_certified_flag"], 0)

    def test_operational_award_requires_real_anchor_and_can_certify(self) -> None:
        scored = score_event_text(
            pd.Series(
                {
                    "event_title": "ABC wins NASA contract",
                    "source_lane": "ceo_ir_transcripts_and_presentations",
                    "event_category": "company_press_release",
                }
            ),
            "ABC announced it was awarded a $500 million NASA contract award. The funded award increases backlog and supports revenue growth.",
        )

        self.assertEqual(scored["economic_evidence_certified_flag"], 1)
        self.assertEqual(scored["content_revenue_or_backlog_signal"], 1)
        self.assertEqual(scored["content_named_customer_or_counterparty"], 1)
        self.assertEqual(scored["interpretation_blocker"], "")
        self.assertEqual(scored["content_stock_specific_causal_link"], "company_direct_economic_update")

    def test_form4_boilerplate_is_not_counted_as_supply_demand(self) -> None:
        events = pd.read_csv(REPORT_DIR / "task_636_event_content_predictions.csv")
        bad = events[
            events["source_lane"].eq("institution_investment_actions")
            & events["content_supply_demand_signal"].astype(int).eq(1)
        ]

        self.assertEqual(len(bad), 0)
        self.assertEqual(int(events[events["source_lane"].eq("institution_investment_actions")]["economic_evidence_certified_flag"].sum()), 0)


if __name__ == "__main__":
    unittest.main()
