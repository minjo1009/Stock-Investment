from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh")


class Task633QqqBenchmarkFullPeriodRefreshTest(unittest.TestCase):
    def test_latest_horizon_extends_into_june(self) -> None:
        audit = pd.read_csv(REPORT_DIR / "task_633_source_horizon_audit.csv").iloc[0]

        self.assertGreaterEqual(str(audit["strategy_entry_end"]), "2026-06-01")
        self.assertGreaterEqual(str(audit["qqq_end"]), "2026-06-01")
        self.assertEqual(int(audit["date_only_support_used_count"]), 0)
        self.assertEqual(int(audit["future_event_support_leak_count"]), 0)

    def test_1000_account_qqq_comparison_is_primary(self) -> None:
        account = pd.read_csv(REPORT_DIR / "task_633_1000_account_qqq_comparison.csv")
        qqq = account[account["universe"].eq("QQQ_buy_and_hold")].iloc[0]
        original = account[account["universe"].eq("task617_original_broad_intelligence_strategy")]
        strict = account[account["universe"].eq("task632_temporal_strict_chart_qual_strategy")]

        self.assertEqual(float(qqq["initial_capital_usd"]), 1000.0)
        self.assertGreater(float(qqq["final_capital_usd"]), 1000.0)
        self.assertEqual(int(original["beats_qqq_flag"].sum()), 4)
        self.assertEqual(int(strict["beats_qqq_flag"].sum()), 3)
        self.assertLess(
            float(strict[strict["max_positions"].eq(5)]["final_capital_usd"].iloc[0]),
            float(original[original["max_positions"].eq(5)]["final_capital_usd"].iloc[0]),
        )

    def test_decision_blocks_acceptance_despite_qqq_edge(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_633_decision.csv").iloc[0]
        pass_fail = pd.read_csv(REPORT_DIR / "task_633_pass_fail_matrix.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("strict_strategy_beats_qqq_50bp_account")]["pass_flag"].iloc[0]),
            0,
        )
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("strict_strategy_beats_original")]["pass_flag"].iloc[0]),
            0,
        )

    def test_report_artifacts_exist(self) -> None:
        self.assertTrue((REPORT_DIR / "task_633_qqq_benchmark_full_period_refresh.md").exists())
        self.assertTrue((REPORT_DIR / "task_633_1000_account_qqq_comparison.csv").exists())
        self.assertTrue((REPORT_DIR / "task_633_decision.csv").exists())
        self.assertTrue((REPORT_DIR / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
