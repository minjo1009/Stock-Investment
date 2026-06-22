from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task512_516_firm_grade_validation import build_task514_live_source_data_contract


class Task514LiveSourceDataContractTest(unittest.TestCase):
    def test_missing_sources_are_blockers_not_approximations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "raw" / "us_intraday").mkdir(parents=True)
            artifacts = build_task514_live_source_data_contract(data_raw=root / "raw", out_dir=root / "out")
            decision = artifacts["task_514_decision"].iloc[0]
            self.assertEqual(int(decision["missing_source_approximation_used_flag"]), 0)
            self.assertEqual(int(decision["live_contract_complete_flag"]), 0)
            self.assertGreater(len(artifacts["missing_source_blocker_audit"]), 0)


if __name__ == "__main__":
    unittest.main()
