from __future__ import annotations

import unittest

from src.backtest.build_task608g_live_detectable_entry_failure_path_diagnostics import (
    build_task608g_live_detectable_entry_failure_path_diagnostics,
    load_assignments,
    load_intraday_sources,
)


class Task608GLiveDetectableEntryFailurePathDiagnosticsTest(unittest.TestCase):
    def test_intraday_sources_cover_task509_oos_symbols(self) -> None:
        assignments = load_assignments("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_assignment_panel.csv")
        symbols = sorted(set(assignments["symbol"].astype(str).str.upper()) | {"QQQ"})
        _, coverage = load_intraday_sources(symbols, "data/raw/us_intraday")

        self.assertGreater(len(coverage), 0)
        self.assertEqual(int(coverage["available_flag"].min()), 1)
        self.assertIn("derived_ohlcv_vwap_flag", coverage.columns)

    def test_state_path_interactions_are_found_without_accepting_strategy(self) -> None:
        artifacts = build_task608g_live_detectable_entry_failure_path_diagnostics()
        path_panel = artifacts["entry_failure_path_panel"]
        simple = artifacts["live_signal_candidate_summary"]
        interactions = artifacts["state_signal_interaction_summary"]
        decisions = artifacts["task_608g_decision"]

        self.assertGreater(len(path_panel), 0)
        self.assertIn("relative_ret_vs_qqq_60m", path_panel.columns)
        self.assertGreater(int(interactions["diagnostic_pass_flag"].sum()), 0)
        self.assertEqual(int(simple["diagnostic_pass_flag"].sum()), 0)
        self.assertEqual(decisions["strategy_acceptance_status"].iloc[0], "NOT_ACCEPTED")
        self.assertEqual(decisions["deployment_status"].iloc[0], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")


if __name__ == "__main__":
    unittest.main()
