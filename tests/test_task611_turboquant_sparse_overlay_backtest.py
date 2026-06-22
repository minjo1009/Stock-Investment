from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task611_turboquant_sparse_overlay_backtest import (
    build_task611_turboquant_sparse_overlay_backtest,
)


class Task611TurboQuantSparseOverlayBacktestTest(unittest.TestCase):
    def test_os_passes_but_trading_overlay_fails(self) -> None:
        artifacts = build_task611_turboquant_sparse_overlay_backtest()
        decision = artifacts["task_611_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_TURBOQUANT_OS_FAIL_TRADING_OVERLAY")
        self.assertEqual(int(decision["os_design_pass_flag"]), 1)
        self.assertEqual(int(decision["review_candidate_pass_flag"]), 1)
        self.assertEqual(int(decision["trading_overlay_pass_flag"]), 0)
        self.assertEqual(int(decision["fold_stability_pass_flag"]), 0)
        self.assertEqual(int(decision["plugin_operability_pass_flag"]), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_exact_rule_profile_matches_task610_candidate(self) -> None:
        artifacts = build_task611_turboquant_sparse_overlay_backtest()
        profile = artifacts["task610_exact_rule_turboquant_profile"].iloc[0]

        self.assertEqual(int(profile["trigger_count"]), 6)
        self.assertEqual(int(profile["failure_count"]), 5)
        self.assertEqual(int(profile["clean_false_count"]), 1)
        self.assertGreater(float(profile["failure_rate_lift_pct_point"]), 40.0)
        self.assertEqual(int(profile["label_used_in_assignment_flag"]), 0)
        self.assertEqual(int(profile["plugin_direct_trade_flag"]), 0)

    def test_turbo_score_scenarios_do_not_pass_trading_gate(self) -> None:
        artifacts = build_task611_turboquant_sparse_overlay_backtest()
        pass_fail = artifacts["task_611_pass_fail_matrix"]
        scenario_summary = artifacts["turboquant_overlay_scenario_summary"]

        trading_gate = pass_fail[pass_fail["gate"].eq("turbo_score_trading_overlay")].iloc[0]
        self.assertEqual(int(trading_gate["pass_flag"]), 0)
        self.assertTrue((scenario_summary["size_down_50_avg_return_delta_pct_point"] < 1.0).all())

    def test_gpt_review_is_review_only(self) -> None:
        artifacts = build_task611_turboquant_sparse_overlay_backtest()
        gpt = artifacts["gpt_turboquant_review_pack"]
        decision = artifacts["task_611_decision"].iloc[0]

        self.assertEqual(int(gpt["gpt_output_used_as_source_flag"].max()), 0)
        self.assertEqual(int(decision["gpt_review_used_flag"]), 1)
        self.assertEqual(int(decision["gpt_used_as_source_flag"]), 0)

    def test_report_artifacts_are_written_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            build_task611_turboquant_sparse_overlay_backtest(out_dir=out_dir)

            self.assertTrue((out_dir / "task_611_turboquant_sparse_overlay_backtest.md").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertTrue((out_dir / "turboquant_overlay_scenario_summary.csv").exists())
            self.assertTrue((out_dir / "task_611_decision.csv").exists())


if __name__ == "__main__":
    unittest.main()
