from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task512_516_firm_grade_validation import build_task516_vectorized_discovery_layer
from tests.task512_516_fixture import write_firm_grade_fixture


class Task516VectorizedDiscoveryLayerTest(unittest.TestCase):
    def test_discovery_queue_requires_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_firm_grade_fixture(root, rows=140)
            artifacts = build_task516_vectorized_discovery_layer(task503_panel_path=panel, out_dir=root / "out")
            decision = artifacts["task_516_decision"].iloc[0]
            self.assertEqual(int(decision["discovery_validation_separated_flag"]), 1)
            self.assertGreaterEqual(int(decision["vectorized_candidate_count"]), 1)
            self.assertTrue((root / "out" / "candidate_to_replay_queue.csv").exists())


if __name__ == "__main__":
    unittest.main()
