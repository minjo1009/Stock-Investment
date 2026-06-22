from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from src.app.task_586_frontend_paper_ops_integration import run_task586


class Task586FrontendPaperOpsIntegrationTest(unittest.TestCase):
    def test_contract_is_catalog_backed(self) -> None:
        fake_proc = subprocess.CompletedProcess(args=["x"], returncode=0, stdout="ok", stderr="")
        with patch("subprocess.run", return_value=fake_proc):
            artifacts = run_task586()
        decision = artifacts["task_586_decision.csv"].iloc[0].to_dict()
        contract = artifacts["frontend_paper_ops_contract_v2.csv"]
        self.assertEqual(int(decision["ui_reads_catalog_only_flag"]), 1)
        self.assertIn("data_status", set(contract["section"]))

    def test_paper_ops_page_exposes_trade_history(self) -> None:
        app_source = Path("frontend/trader-terminal/src/App.jsx").read_text(encoding="utf-8")
        self.assertIn("거래내역", app_source)
        self.assertIn("tradeHistoryRows", app_source)
        self.assertIn("filled_avg_price", app_source)
        self.assertIn("tradeDetailViews", app_source)
        self.assertIn("PAPER_TRADE_DETAIL_VIEW", app_source)
        self.assertIn("나스닥 장중 자동 실행", app_source)
        self.assertIn("supervisorRows", app_source)
        self.assertIn("UNIVERSE_COVERAGE_GAP", app_source)
        self.assertIn("latestRuntimeDecision", app_source)
        self.assertIn("universeCoverage", app_source)


if __name__ == "__main__":
    unittest.main()
