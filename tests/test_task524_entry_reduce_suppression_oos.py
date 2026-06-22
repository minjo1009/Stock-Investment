from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task523_528_gap_closure import build_task524_entry_reduce_suppression_oos
from tests.task523_528_fixture import write_gap_fixture


class Task524EntryReduceSuppressionOosTest(unittest.TestCase):
    def test_suppression_uses_entry_safe_rules_and_emits_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_gap_fixture(root)
            artifacts = build_task524_entry_reduce_suppression_oos(task503_panel_path=panel, out_dir=root / "out")
            pool = artifacts["entry_reduce_suppression_candidate_pool"]
            self.assertIn("family_name", pool.columns)
            self.assertEqual(int(pool["pass_flag"].max()), 1)
            self.assertNotIn("lifecycle_outcome_class", pool.columns)


if __name__ == "__main__":
    unittest.main()
