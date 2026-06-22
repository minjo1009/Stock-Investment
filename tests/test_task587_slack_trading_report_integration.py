from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.app.task_587_slack_trading_report_integration import run_task587


class Task587SlackTradingReportIntegrationTest(unittest.TestCase):
    def test_missing_webhook_is_blocked_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "empty.env"
            rows = [
                {"decision_status": "PAPER_ORDER_CANDIDATE", "symbol": "AMD", "side": "BUY", "quantity": 1, "limit_price": 100, "reason_code": "RUNTIME_SIGNAL_SELECTED"},
                {"order_status": "FILLED", "order_id": "o1", "symbol": "AMD", "side": "BUY", "quantity": 1, "filled_qty": 1, "filled_avg_price": 99.5, "broker_truth_fill_flag": 1},
            ]
            with (
                patch.dict(os.environ, {"SLACK_WEBHOOK_URL": ""}, clear=False),
                patch("src.app.task_587_slack_trading_report_integration._read_latest", side_effect=rows),
            ):
                artifacts = run_task587(env_file=env_path)
            decision = artifacts["task_587_decision.csv"].iloc[0].to_dict()
            audit = artifacts["slack_trading_notification_audit.csv"].iloc[0].to_dict()
            payload = artifacts["slack_message_payload_sample.csv"].iloc[0].to_dict()
            self.assertEqual(decision["decision_status"], "SLACK_BLOCKED_MISSING_WEBHOOK")
            self.assertEqual(audit["message_type"], "FILLED_TRADE_REPORT")
            self.assertEqual(int(audit["secret_in_message_flag"]), 0)
            self.assertEqual(int(payload["secret_logged_flag"]), 0)

    def test_unfilled_trade_is_not_sent_to_slack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "empty.env"
            rows = [
                {"decision_status": "PAPER_ORDER_CANDIDATE", "symbol": "AMD", "side": "BUY", "quantity": 1, "limit_price": 100, "reason_code": "RUNTIME_SIGNAL_SELECTED"},
                {"order_status": "SUBMITTED", "order_id": "o1", "symbol": "AMD", "side": "BUY", "quantity": 1, "broker_truth_fill_flag": 0},
            ]
            with (
                patch.dict(os.environ, {"SLACK_WEBHOOK_URL": "https://local.mock"}, clear=False),
                patch("src.app.task_587_slack_trading_report_integration._read_latest", side_effect=rows),
                patch("src.app.task_587_slack_trading_report_integration.slack_client.send_message") as send_message,
            ):
                artifacts = run_task587(env_file=env_path)
            decision = artifacts["task_587_decision.csv"].iloc[0].to_dict()
            audit = artifacts["slack_trading_notification_audit.csv"].iloc[0].to_dict()
            self.assertEqual(decision["decision_status"], "SKIPPED_NO_FILLED_TRADE")
            self.assertEqual(audit["message_type"], "SKIPPED_NO_FILLED_TRADE")
            send_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
