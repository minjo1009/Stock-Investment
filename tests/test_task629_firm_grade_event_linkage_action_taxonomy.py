from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task629_firm_grade_event_linkage_action_taxonomy import (
    build_task629_firm_grade_event_linkage_action_taxonomy,
)


class Task629FirmGradeEventLinkageActionTaxonomyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task629_firm_grade_event_linkage_action_taxonomy()

    def test_strategy_remains_not_accepted(self) -> None:
        decision = self.artifacts["task_629_decision"].iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["source_presence_only_used_flag"]), 0)
        self.assertEqual(int(decision["gpt_score_used_as_source_flag"]), 0)
        self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)

    def test_theme_only_events_do_not_create_actions(self) -> None:
        pass_fail = self.artifacts["task_629_pass_fail_matrix"]
        gate = pass_fail[pass_fail["gate"].eq("economic_linkage_not_theme_only")].iloc[0]

        self.assertEqual(int(gate["pass_flag"]), 1)

    def test_action_taxonomy_is_not_binary_hold_only(self) -> None:
        attachment = self.artifacts["task_629_trade_action_attachment"]
        actions = set(attachment["action_bucket"].unique())

        self.assertIn("NO_ACTION", actions)
        self.assertGreater(len(actions - {"NO_ACTION"}), 0)
        self.assertTrue({"BLOCK_HOLD", "SIZE_DOWN", "DELAY_ENTRY", "CONFIRMATION_REQUIRED"} & actions)

    def test_cost_account_matrix_contains_original_and_taxonomy(self) -> None:
        cost = self.artifacts["task_629_cost_account_matrix"]

        self.assertEqual(set(cost["universe"].unique()), {"turboquant_original", "firm_grade_action_taxonomy"})
        self.assertEqual(set(cost["round_trip_cost_bps"].astype(int).unique()), {50})
        self.assertGreater(len(cost), 10)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task629_firm_grade_event_linkage_action_taxonomy(out_dir=out_dir)

            self.assertTrue((out_dir / "task_629_firm_grade_event_linkage_action_taxonomy.md").exists())
            self.assertTrue((out_dir / "task_629_event_symbol_linkage_registry.csv").exists())
            self.assertTrue((out_dir / "task_629_trade_action_attachment.csv").exists())
            self.assertTrue((out_dir / "task_629_cost_account_matrix.csv").exists())
            self.assertTrue((out_dir / "task_629_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_629_event_symbol_linkage_registry"]), 100)


if __name__ == "__main__":
    unittest.main()
