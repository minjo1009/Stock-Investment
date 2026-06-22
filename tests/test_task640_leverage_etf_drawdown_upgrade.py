from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_640_leverage_etf_drawdown_upgrade")


class Task640LeverageEtfDrawdownUpgradeTest(unittest.TestCase):
    def test_task639_baseline_is_reproduced(self) -> None:
        baseline = pd.read_csv(REPORT_DIR / "task_640_task639_baseline_recheck.csv").iloc[0]

        self.assertEqual(int(baseline["task639_recheck_match_flag"]), 1)
        self.assertAlmostEqual(float(baseline["final_capital_usd"]), float(baseline["task639_expected_final_capital_usd"]), places=2)
        self.assertAlmostEqual(float(baseline["max_drawdown_pct"]), float(baseline["task639_expected_max_drawdown_pct"]), places=2)

    def test_leveraged_etf_overlay_is_rejected(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_640_decision.csv").iloc[0]
        pass_fail = pd.read_csv(REPORT_DIR / "task_640_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(gates["leveraged_etf_data_available"], 1)
        self.assertEqual(gates["leveraged_etf_improves_task639"], 0)
        self.assertLess(float(decision["best_leverage_final_capital_usd"]), float(decision["task639_baseline_final_capital_usd"]))

    def test_combo_improves_return_and_drawdown_but_is_not_accepted(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_640_decision.csv").iloc[0]
        pass_fail = pd.read_csv(REPORT_DIR / "task_640_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(decision["decision"], "PASS_COMBO_RETURN_UP_DRAWDOWN_DOWN_RESEARCH_CANDIDATE_NOT_ACCEPTED")
        self.assertEqual(decision["best_combo_target"], "symbol:MDB")
        self.assertGreater(float(decision["best_combo_final_capital_usd"]), float(decision["task639_baseline_final_capital_usd"]))
        self.assertGreater(float(decision["best_combo_max_drawdown_pct"]), float(decision["task639_baseline_max_drawdown_pct"]))
        self.assertEqual(gates["exclusion_plus_throttle_improves_task639"], 1)
        self.assertEqual(gates["combo_overfit_risk_block"], 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
