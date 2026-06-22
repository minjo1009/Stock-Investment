from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task632_temporal_strict_full_period_backtest import (
    build_task632_temporal_strict_full_period_backtest,
)


class Task632TemporalStrictFullPeriodBacktestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task632_temporal_strict_full_period_backtest()

    def test_runtime_temporal_contract_and_full_period_are_visible(self) -> None:
        audit = self.artifacts["task_632_source_time_contract_audit"].iloc[0]
        decision = self.artifacts["task_632_decision"].iloc[0]

        self.assertEqual(int(audit["event_store_has_received_at_flag"]), 1)
        self.assertEqual(int(audit["event_store_has_published_at_flag"]), 1)
        self.assertEqual(int(audit["event_store_has_tradable_after_ts_flag"]), 1)
        self.assertGreaterEqual(int(audit["entry_count"]), 5000)
        self.assertLessEqual(str(audit["full_period_start"]), "2024-01-02")
        self.assertGreaterEqual(str(audit["full_period_end"]), "2026-05-01")
        self.assertEqual(str(decision["full_period_start"]), str(audit["full_period_start"]))
        self.assertEqual(str(decision["full_period_end"]), str(audit["full_period_end"]))

    def test_date_only_and_future_events_do_not_support_entries(self) -> None:
        audit = self.artifacts["task_632_source_time_contract_audit"].iloc[0]
        pass_fail = self.artifacts["task_632_pass_fail_matrix"]

        self.assertGreater(int(audit["date_only_event_count"]), 0)
        self.assertGreater(int(audit["source_time_gap_entry_count"]), 0)
        self.assertEqual(int(audit["date_only_support_used_count"]), 0)
        self.assertEqual(int(audit["future_event_support_leak_count"]), 0)
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("date_only_events_not_used_as_support")]["pass_flag"].iloc[0]),
            1,
        )
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("future_event_support_leakage")]["pass_flag"].iloc[0]),
            1,
        )

    def test_strategy_remains_not_accepted_due_recent_and_account_gates(self) -> None:
        decision = self.artifacts["task_632_decision"].iloc[0]
        pass_fail = self.artifacts["task_632_pass_fail_matrix"]
        split = self.artifacts["task_632_split_summary"]
        recent = split[split["split_name"].astype(str).eq("recent_oos")].iloc[0]

        self.assertEqual(decision["decision"], "FAIL_TEMPORAL_STRICT_FULL_PERIOD_NOT_ACCEPTED")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertLess(float(recent["avg_net_return_pct"]), 3.0)
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_vs_original")]["pass_flag"].iloc[0]),
            0,
        )
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("full_panel_50bp_account_vs_original")]["pass_flag"].iloc[0]),
            0,
        )

    def test_outputs_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task632_temporal_strict_full_period_backtest(out_dir=out_dir)

            self.assertTrue((out_dir / "task_632_temporal_strict_full_period_backtest.md").exists())
            self.assertTrue((out_dir / "task_632_temporal_strict_scored_entry_panel.csv").exists())
            self.assertTrue((out_dir / "task_632_temporal_strict_strategy_backtest_panel.csv").exists())
            self.assertTrue((out_dir / "task_632_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_632_temporal_strict_strategy_backtest_panel"]), 50)


if __name__ == "__main__":
    unittest.main()
