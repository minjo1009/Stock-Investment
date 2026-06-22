from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task621_source_retyped_cost_portfolio_validation import (
    build_task621_source_retyped_cost_portfolio_validation,
)


class Task621SourceRetypedCostPortfolioValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task621_source_retyped_cost_portfolio_validation()

    def test_full_panel_50bp_edge_passes_but_source_certification_fails(self) -> None:
        decision = self.artifacts["task_621_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_COST_ACCOUNT_EDGE_FAIL_SOURCE_CERTIFICATION_NOT_ACCEPTED")
        self.assertEqual(int(decision["full_panel_50bp_edge_pass_flag"]), 1)
        self.assertEqual(int(decision["source_retyping_certification_pass_flag"]), 0)
        self.assertEqual(decision["source_gate_action"], "HOLD_UNTIL_SOURCE_CERTIFICATION")

    def test_proactive_beats_original_full_panel_at_50bp_all_capacities(self) -> None:
        portfolio = self.artifacts["task_621_cost_portfolio_matrix"]
        full50 = portfolio[
            portfolio["scope"].eq("full_panel")
            & portfolio["round_trip_cost_bps"].astype(int).eq(50)
            & portfolio["universe"].isin(["turboquant_original", "proactive_hold_until_source_certified"])
        ]
        pivot = full50.pivot(index="max_positions", columns="universe", values="final_capital_usd")

        self.assertTrue((pivot["proactive_hold_until_source_certified"] > pivot["turboquant_original"]).all())

    def test_negative_control_is_rejected(self) -> None:
        pass_fail = self.artifacts["task_621_pass_fail_matrix"]
        gate = pass_fail[pass_fail["gate"].eq("negative_control_rejected")].iloc[0]

        self.assertEqual(int(gate["pass_flag"]), 1)

    def test_no_source_subtype_rescues_recent_aerospace(self) -> None:
        source = self.artifacts["task_621_source_retyping_certification_matrix"]
        recent = source[
            source["split_name"].eq("recent_oos")
            & source["source_retype_bucket"].isin(["aerospace_no_ceo_ir", "aerospace_ceo_ir"])
        ]

        self.assertTrue((recent["avg_net_return_pct"].astype(float) < 0.0).all())
        self.assertTrue((recent["source_certified_pass_flag"].astype(int) == 0).all())

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task621_source_retyped_cost_portfolio_validation(out_dir=out_dir)

            self.assertTrue((out_dir / "task_621_source_retyped_cost_portfolio_validation.md").exists())
            self.assertTrue((out_dir / "task_621_cost_portfolio_matrix.csv").exists())
            self.assertTrue((out_dir / "task_621_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_621_cost_portfolio_matrix"]), 100)


if __name__ == "__main__":
    unittest.main()
