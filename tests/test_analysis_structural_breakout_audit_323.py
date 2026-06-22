from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MODULE = "src.backtest.analysis_structural_breakout_audit_323"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    return env


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=_env(),
    )


class TestAnalysisStructuralBreakoutAudit323(unittest.TestCase):
    def test_help_smoke(self) -> None:
        proc = _run(["--help"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Task 323 structural breakout robustness audit", proc.stdout)

    def test_scenario_name_is_unique_across_hidden_parameters(self) -> None:
        from src.backtest.analysis_structural_breakout_322 import StructuralConfig, _scenario_name

        base = StructuralConfig(structure_mode="RANGE_COMPRESSION", range_lookback=20, max_range_width_pct=0.10)
        changed_lookback = StructuralConfig(structure_mode="RANGE_COMPRESSION", range_lookback=30, max_range_width_pct=0.10)
        changed_liquidity = StructuralConfig(structure_mode="RANGE_COMPRESSION", range_lookback=20, max_range_width_pct=0.10, min_avg_dollar_volume_20=30_000_000.0)

        names = {_scenario_name(base), _scenario_name(changed_lookback), _scenario_name(changed_liquidity)}
        self.assertEqual(len(names), 3)


if __name__ == "__main__":
    unittest.main()
