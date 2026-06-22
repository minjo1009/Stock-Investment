from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.app.task_582_kis_paper_trading_bridge import run_task582


class Task582KisPaperTradingBridgeTest(unittest.TestCase):
    def test_missing_env_blocks_connection_and_dummy_fallback_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "missing.env"
            clear_keys = [
                "KIS_ENVIRONMENT",
                "KIS_APP_KEY",
                "KIS_APP_SECRET",
                "KIS_ACCOUNT_NUMBER",
                "KIS_PRODUCT_CODE",
                "SLACK_WEBHOOK_URL",
                "TRADING_DB_PATH",
                "TRADING_REQUIRE_RUNTIME_SIGNAL",
            ]
            with patch.dict(os.environ, {key: "" for key in clear_keys}, clear=False):
                artifacts = run_task582(db_path=db_path, env_file=env_path, send_slack=False)
            decision = artifacts["task_582_decision.csv"].iloc[0].to_dict()
            run_log = artifacts["paper_trading_run_log.csv"].iloc[0].to_dict()
            self.assertEqual(decision["strategy_acceptance_status"], "DATA_BLOCKED_KIS_CONNECTION")
            self.assertEqual(int(decision["dummy_fallback_blocked_flag"]), 1)
            self.assertEqual(int(run_log["runtime_candidate_available_flag"]), 0)
            self.assertEqual(run_log["paper_order_run_status"], "SKIPPED_BY_DEFAULT")


if __name__ == "__main__":
    unittest.main()
