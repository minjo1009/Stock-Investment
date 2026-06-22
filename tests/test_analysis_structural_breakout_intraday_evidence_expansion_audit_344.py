from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_evidence_expansion_audit_344 import (
    _anchored_oos_reason_breakdown,
    _attempt_summary,
    _decision,
)


class TestAnalysisStructuralBreakoutIntradayEvidenceExpansionAudit344(unittest.TestCase):
    def test_attempt_summary_detects_no_gain(self) -> None:
        scope_df = pd.DataFrame({"symbol": ["A"], "trade_date": ["2024-01-01"]})
        audit_df = pd.DataFrame({"symbol": ["A"], "trade_date": ["2024-01-01"], "coverage_status": ["insufficient_window"]})
        summary = _attempt_summary(scope_df, audit_df).iloc[0]
        self.assertEqual(int(summary["coverage_gain_dates"]), 0)
        self.assertEqual(str(summary["retry_result"]), "no_coverage_gain")

    def test_reason_breakdown_is_deterministic(self) -> None:
        flags_df = pd.DataFrame(
            {
                "split": ["anchored_oos", "anchored_oos", "train"],
                "missing_reason": ["incomplete_intraday_window", "covered", "covered"],
                "is_covered": [False, True, True],
                "symbol": ["A", "B", "C"],
            }
        )
        breakdown = _anchored_oos_reason_breakdown(flags_df)
        self.assertEqual(breakdown["trade_count"].sum(), 2)
        self.assertEqual(breakdown.iloc[0]["reason"], "covered")

    def test_decision_prefers_alignment_bottleneck_when_no_gain(self) -> None:
        task341_df = pd.DataFrame([{"decision": "REGIME_CONDITIONAL_EDGE"}])
        task342_df = pd.DataFrame([{"decision": "NO_IMPROVEMENT"}])
        attempt_df = pd.DataFrame(
            [
                {
                    "attempt_scope_count": 17,
                    "covered_after_retry": 0,
                    "still_insufficient_after_retry": 17,
                    "coverage_gain_dates": 0,
                    "retry_result": "no_coverage_gain",
                }
            ]
        )
        reasons_df = pd.DataFrame([{"reason": "incomplete_intraday_window", "trade_count": 149}])
        decision = _decision(task341_df, task342_df, attempt_df, reasons_df).iloc[0]
        self.assertEqual(decision["decision"], "NO_EVIDENCE_EXPANSION_GAIN")
        self.assertEqual(decision["next_bottleneck"], "event_alignment_or_provider_coverage")


if __name__ == "__main__":
    unittest.main()
