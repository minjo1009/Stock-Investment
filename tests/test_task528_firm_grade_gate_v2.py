from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task523_528_gap_closure import build_task528_firm_grade_gate_v2


class Task528FirmGradeGateV2Test(unittest.TestCase):
    def test_gate_emits_next_action_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = build_task528_firm_grade_gate_v2(out_dir=root / "out")
            decision = artifacts["task_528_decision"].iloc[0]
            self.assertEqual(int(decision["deployment_ready_flag"]), 0)
            self.assertIn("promotion_decision_v2", decision.index)
            self.assertTrue((root / "out" / "next_action_queue.csv").exists())


if __name__ == "__main__":
    unittest.main()
