from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task523_528_gap_closure import build_task523_receive_timestamp_replay
from tests.task523_528_fixture import write_gap_fixture


class Task523ReceiveTimestampReplayTest(unittest.TestCase):
    def test_missing_receive_timestamp_is_not_live_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_gap_fixture(root, rows=20)
            artifacts = build_task523_receive_timestamp_replay(task505_panel_path=panel, raw_intraday_dir=root / "raw", stream_archive_dir=root / "stream", out_dir=root / "out")
            decision = artifacts["task_523_decision"].iloc[0]
            self.assertEqual(int(decision["receive_ts_replay_ready_flag"]), 0)
            self.assertEqual(int(decision["missing_receive_ts_treated_live_ready_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
