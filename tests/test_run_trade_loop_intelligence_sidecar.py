from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import app.run_trade_loop as run_trade_loop


class RunTradeLoopIntelligenceSidecarTest(unittest.TestCase):
    def test_loop_runs_sidecar_without_blocking_executor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = str(Path(td) / ".trading.lock")
            run_once = Mock()
            out = io.StringIO()
            sidecar_artifacts = {
                "latest_runtime_intelligence_sidecar_status.csv": pd.DataFrame(
                    [
                        {
                            "decision_status": "INTELLIGENCE_SIDECAR_COLLECTION_OK",
                            "event_store_rows": 3,
                            "sidecar_trade_signal_used_flag": 0,
                        }
                    ]
                )
            }
            with (
                patch.dict(
                    os.environ,
                    {
                        "TRADING_DB_PATH": db_path,
                        "TRADING_KILL_SWITCH": "false",
                        "TRADING_INTELLIGENCE_SIDECAR_ENABLED": "1",
                    },
                    clear=False,
                ),
                patch.object(run_trade_loop, "run_task615_realtime_intelligence_sidecar", return_value=sidecar_artifacts),
                redirect_stdout(out),
            ):
                code = run_trade_loop.run_loop(max_runs=1, lock_path=lock_path, run_once_fn=run_once)
            self.assertEqual(code, 0)
            run_once.assert_called_once()
            self.assertIn("[INTELLIGENCE] status=INTELLIGENCE_SIDECAR_COLLECTION_OK rows=3 trade_signal_used=0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
