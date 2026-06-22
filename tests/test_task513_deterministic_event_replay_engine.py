from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task512_516_firm_grade_validation import build_task513_deterministic_event_replay_engine
from tests.task512_516_fixture import write_firm_grade_fixture


class Task513DeterministicEventReplayEngineTest(unittest.TestCase):
    def test_replay_is_deterministic_and_exact_lifecycle_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_firm_grade_fixture(root, rows=12)
            artifacts = build_task513_deterministic_event_replay_engine(task505_panel_path=panel, out_dir=root / "out")
            audit = artifacts["replay_determinism_audit"].iloc[0]
            self.assertEqual(int(audit["deterministic_replay_pass_flag"]), 1)
            self.assertEqual(int(audit["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertTrue((root / "out" / "canonical_lifecycle_replay_panel.csv").exists())


if __name__ == "__main__":
    unittest.main()
