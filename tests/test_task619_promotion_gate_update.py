from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task619_promotion_gate_update import build_task619_promotion_gate_update


class Task619PromotionGateUpdateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task619_promotion_gate_update()

    def test_recent_oos_is_top_blocker(self) -> None:
        decision = self.artifacts["task_619_decision"].iloc[0]
        source = self.artifacts["task_619_source_snapshot"].iloc[0]

        self.assertEqual(decision["top_blocker"], "recent_oos_stability")
        self.assertLess(float(source["recent_oos_avg_net_return_pct"]), float(source["validation_avg_net_return_pct"]))
        self.assertGreater(
            float(source["recent_oos_entry_reduce_failure_rate"]),
            float(source["validation_entry_reduce_failure_rate"]),
        )

    def test_gate_order_is_locked(self) -> None:
        matrix = self.artifacts["task_619_gate_priority_matrix"]

        self.assertEqual(matrix["gate"].tolist(), ["recent_oos_stability", "cost_slippage_stress", "live_source_readiness"])
        self.assertEqual(matrix["priority"].tolist(), ["P1", "P2", "P3"])

    def test_gpt_is_review_only_and_refinement_is_blocked(self) -> None:
        gpt = self.artifacts["task_619_gpt_gate_review_status"].iloc[0]
        decision = self.artifacts["task_619_decision"].iloc[0]

        self.assertEqual(int(gpt["gpt_output_used_as_source_flag"]), 0)
        self.assertEqual(int(decision["gpt_or_plugin_used_as_source_flag"]), 0)
        self.assertEqual(int(decision["strategy_refinement_allowed_flag"]), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task619_promotion_gate_update(out_dir=out_dir)

            self.assertTrue((out_dir / "task_619_promotion_gate_update.md").exists())
            self.assertTrue((out_dir / "task_619_gate_priority_matrix.csv").exists())
            self.assertTrue((out_dir / "task_619_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertEqual(len(artifacts["task_619_implementation_packet"]), 3)


if __name__ == "__main__":
    unittest.main()
