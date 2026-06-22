from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTask087ExternalFailure(unittest.TestCase):
    def test_external_failure_is_recorded_and_marks_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db_path = root / "trading.db"
            runs_dir = root / "runs"
            latest_json = root / "latest.json"
            latest_md = root / "latest.md"

            env = dict(os.environ)
            env["PYTHONPATH"] = str(SRC)
            env["KIS_ENVIRONMENT"] = "paper"
            env["TRADING_DB_PATH"] = str(db_path)

            cmd = [
                sys.executable,
                "-m",
                "app.task_087_pilot_evidence",
                "--db-path",
                str(db_path),
                "--runs-dir",
                str(runs_dir),
                "--latest-json-out",
                str(latest_json),
                "--latest-md-out",
                str(latest_md),
                "--dry-run",
                "--failed-component",
                "task_089",
                "--external-failure-reason",
                "TASK_089_FAILED",
                "--external-failure-reason",
                "TASK_089_STEP_NON_ZERO_EXIT",
                "--external-stack-trace",
                "simulated stack trace",
            ]
            proc = subprocess.run(cmd, check=False, capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)

            payload = json.loads(latest_json.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "FAIL")
            self.assertEqual(payload.get("failed_component"), "task_089")
            self.assertIn("TASK_089_FAILED", payload.get("failure_reasons", []))
            self.assertIn("TASK_089_STEP_NON_ZERO_EXIT", payload.get("failure_reasons", []))
            self.assertIn("simulated stack trace", str(payload.get("stack_trace")))


if __name__ == "__main__":
    unittest.main()

