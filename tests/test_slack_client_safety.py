from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.integration import slack_client


class SlackClientSafetyTest(unittest.TestCase):
    def test_missing_webhook_blocks_send(self) -> None:
        with patch.dict(os.environ, {"SLACK_WEBHOOK_URL": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "SLACK_WEBHOOK_URL"):
                slack_client.send_message("safe operational message")

    def test_configured_secret_in_message_blocks_before_network(self) -> None:
        env = {
            "SLACK_WEBHOOK_URL": "https://hooks.slack.test/services/AAA/BBB/CCCCCCCC",
            "KIS_APP_SECRET": "secret-value-123",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("src.integration.slack_client.request.urlopen") as urlopen:
                with self.assertRaisesRegex(RuntimeError, "configured secret"):
                    slack_client.send_message("leaked secret-value-123")
                urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
