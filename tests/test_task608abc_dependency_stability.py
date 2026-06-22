from __future__ import annotations

import unittest

from src.backtest.build_task608abc_dependency_stability import (
    build_parameter_neighborhood_oos,
    build_symbol_dependency_audit,
    build_task608abc_dependency_stability,
    build_theme_dependency_audit,
    baseline_oos_metrics,
    load_oos_panel,
)


class Task608ABCDependencyStabilityTest(unittest.TestCase):
    def test_theme_and_symbol_dependency_audits_produce_pass_flags(self) -> None:
        panel = load_oos_panel("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_assignment_panel.csv")
        baseline = baseline_oos_metrics(panel, {})
        theme = build_theme_dependency_audit(panel, baseline)
        symbol = build_symbol_dependency_audit(panel, baseline)

        self.assertGreater(len(theme), 0)
        self.assertGreater(len(symbol), 0)
        self.assertIn("degradation_ratio", theme.columns)
        self.assertIn("pass_flag", symbol.columns)
        self.assertTrue(set(symbol["scenario"]).issuperset({"leave_top1_symbols_out", "leave_top3_symbols_out", "leave_top5_symbols_out"}))

    def test_parameter_neighborhood_uses_fold_oos_metrics(self) -> None:
        artifacts = build_task608abc_dependency_stability()
        neighborhood = artifacts["parameter_neighborhood_stability"]
        decisions = artifacts["task_608abc_decision"]

        self.assertGreater(len(neighborhood), 0)
        self.assertIn("positive_fold_rate", neighborhood.columns)
        self.assertIn("neighborhood_pass_flag", neighborhood.columns)
        self.assertIn("Task608A", set(decisions["task_id"]))
        self.assertIn("Task608B", set(decisions["task_id"]))
        self.assertIn("Task608C", set(decisions["task_id"]))


if __name__ == "__main__":
    unittest.main()
