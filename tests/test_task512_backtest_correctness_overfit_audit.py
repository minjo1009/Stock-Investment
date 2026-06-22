from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task512_516_firm_grade_validation import build_task512_backtest_correctness_overfit_audit
from tests.task512_516_fixture import write_firm_grade_fixture


class Task512BacktestCorrectnessOverfitAuditTest(unittest.TestCase):
    def test_overfit_audit_outputs_diagnostic_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_firm_grade_fixture(root)
            candidates = root / "candidates.csv"
            pd.DataFrame(
                [
                    {
                        "candidate_strategy_name": "c1",
                        "two_year_capital_pnl_pct": 100.0,
                        "lifecycle_count": 100,
                        "avg_net_return_pct": 5.0,
                    }
                ]
            ).to_csv(candidates, index=False)
            wf = root / "wf.csv"
            pd.DataFrame([{"walk_forward_avg_net_pct": 1.0, "walk_forward_win_rate": 0.5, "walk_forward_entry_reduce_rate": 0.4}]).to_csv(wf, index=False)
            artifacts = build_task512_backtest_correctness_overfit_audit(task505_panel_path=panel, task505_candidates_path=candidates, task509_decision_path=wf, out_dir=root / "out")
            self.assertIn("overfit_risk_audit", artifacts)
            self.assertEqual(int(artifacts["task_512_decision"].iloc[0]["deployment_ready_flag"]), 0)
            self.assertTrue((root / "out" / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
