from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task523_528_gap_closure import build_task526_depth_scope_decision


class Task526DepthScopeDecisionTest(unittest.TestCase):
    def test_nbbo_scope_is_limited_and_full_depth_not_approximated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = build_task526_depth_scope_decision(out_dir=root / "out")
            decision = artifacts["task_526_decision"].iloc[0]
            self.assertEqual(decision["selected_scope_mode"], "NBBO_ONLY_SCOPE_LIMITED")
            self.assertEqual(int(decision["full_depth_approximated_flag"]), 0)
            self.assertEqual(int(decision["deployment_grade_allowed_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
