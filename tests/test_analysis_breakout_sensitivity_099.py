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
RUNNER_PATH = SRC / "backtest" / "analysis_breakout_sensitivity_099.py"
MODULE = "backtest.analysis_breakout_sensitivity_099"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    return env


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", MODULE, *args]
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
        cwd=str(cwd or ROOT),
    )


@unittest.skipUnless(RUNNER_PATH.exists(), "T099 runner not available yet: src/backtest/analysis_breakout_sensitivity_099.py")
class TestAnalysisBreakoutSensitivity099(unittest.TestCase):
    def _help_text(self) -> str:
        proc = _run(["--help"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout + "\n" + proc.stderr

    def test_schema_presence_in_output_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_json = Path(td) / "result.json"
            out_md = Path(td) / "result.md"

            help_text = self._help_text()
            args: list[str] = []
            if "--profile" in help_text:
                args.extend(["--profile", "baseline"])
            if "--json-out" in help_text:
                args.extend(["--json-out", str(out_json)])
            if "--md-out" in help_text:
                args.extend(["--md-out", str(out_md)])

            proc = _run(args)
            self.assertEqual(proc.returncode, 0, proc.stderr)

            if out_json.exists():
                payload = json.loads(out_json.read_text(encoding="utf-8"))
            else:
                default_out = ROOT / "docs" / "reports" / "task_099" / "task_099_breakout_sensitivity_results.json"
                self.assertTrue(default_out.exists(), "Expected result JSON was not created.")
                payload = json.loads(default_out.read_text(encoding="utf-8"))

            required_top = {
                "task",
                "status",
                "baseline",
                "matrix",
                "runs",
                "scenario_results",
                "acceptance",
                "rejections",
                "recommended_next",
                "final_answer",
            }
            self.assertTrue(required_top.issubset(payload.keys()))
            self.assertIsInstance(payload.get("runs"), list)

    def test_independence_rule_enforced_in_runs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_json = Path(td) / "result.json"

            help_text = self._help_text()
            args: list[str] = []
            if "--family" in help_text:
                args.extend(["--family", "A"])
            if "--json-out" in help_text:
                args.extend(["--json-out", str(out_json)])

            proc = _run(args)
            self.assertEqual(proc.returncode, 0, proc.stderr)

            if not out_json.exists():
                out_json = ROOT / "docs" / "reports" / "task_099" / "task_099_breakout_sensitivity_results.json"
            self.assertTrue(out_json.exists(), "Expected result JSON was not created.")

            payload = json.loads(out_json.read_text(encoding="utf-8"))
            runs = payload.get("runs", [])
            self.assertIsInstance(runs, list)
            self.assertGreater(len(runs), 0, "runs[] should contain at least one executed run.")
            for run in runs:
                self.assertIn("independence_ok", run)
                self.assertTrue(bool(run["independence_ok"]), f"Independence violated in run: {run.get('run_id')}")

    def test_non_crash_when_optional_input_path_missing(self) -> None:
        help_text = self._help_text()
        candidate_flags = [
            "--input-t098",
            "--input-t097",
            "--input-t096",
            "--input-t093",
            "--input-optional",
            "--plan-json",
        ]
        optional_flag = next((f for f in candidate_flags if f in help_text), None)
        if optional_flag is None:
            self.skipTest("No recognizable optional input flag exposed by runner --help.")

        with tempfile.TemporaryDirectory() as td:
            out_json = Path(td) / "result.json"
            missing = Path(td) / "definitely_missing.json"

            args = [optional_flag, str(missing)]
            if "--profile" in help_text:
                args.extend(["--profile", "baseline"])
            if "--json-out" in help_text:
                args.extend(["--json-out", str(out_json)])

            proc = _run(args)
            self.assertEqual(
                proc.returncode,
                0,
                f"Runner should not crash with missing optional input ({optional_flag}). stderr={proc.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
