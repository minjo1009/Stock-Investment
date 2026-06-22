from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MODULE = "src.backtest.analysis_tbl_314"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    return env


class TestAnalysisTbl314(unittest.TestCase):
    def test_prepare_tbl_feature_frame_uses_shifted_inputs(self) -> None:
        if str(SRC) not in sys.path:
            sys.path.insert(0, str(SRC))
        from backtest.analysis_tbl_314 import prepare_tbl_feature_frame

        rows = []
        for i in range(60):
            rows.append(
                {
                    "timestamp": pd.Timestamp("2020-01-01", tz="UTC") + pd.Timedelta(days=i),
                    "open": 100 + i,
                    "high": 101 + i,
                    "low": 99 + i,
                    "close": 100 + i,
                    "volume": 1_000_000 + i,
                    "symbol": "TEST",
                }
            )
        frame = prepare_tbl_feature_frame(pd.DataFrame(rows))
        self.assertAlmostEqual(frame.iloc[30]["atr_for_entry"], frame.iloc[29]["atr14"])
        self.assertAlmostEqual(frame.iloc[30]["avg_volume_20_prev"], frame.iloc[10:30]["volume"].mean())

    def test_cli_writes_required_schema_and_trade_log_columns(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proc = subprocess.run(
                [sys.executable, "-m", MODULE, "--symbols", "AAPL", "MSFT", "NVDA", "--out-dir", td],
                cwd=str(ROOT),
                env=_env(),
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads((Path(td) / "task_314_tbl_backtest_result.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["strategy"], "TBL_A10_LIFECYCLE")
            self.assertEqual(payload["risk"]["max_positions"], 5)
            self.assertTrue(payload["execution_model"]["next_bar_entry_only"])
            self.assertIn("expectancy_r", payload["metrics"])
            self.assertTrue(payload["integrity"]["shifted_entry_features"])

            with (Path(td) / "task_314_tbl_trade_log.csv").open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                required = {
                    "lifecycle_id",
                    "symbol",
                    "entry_date",
                    "initial_entry_price",
                    "add_price",
                    "partial_exit_price",
                    "final_exit_price",
                    "initial_R",
                    "realized_R_total",
                    "exit_reason",
                    "bars_held",
                }
                self.assertTrue(required.issubset(set(reader.fieldnames or [])))

    def test_parse_volume_multiplier_grid_generates_21_points(self) -> None:
        if str(SRC) not in sys.path:
            sys.path.insert(0, str(SRC))
        from backtest.analysis_tbl_314 import parse_volume_multiplier_grid

        values = parse_volume_multiplier_grid("1.0:2.0:0.05")
        self.assertEqual(len(values), 21)
        self.assertAlmostEqual(values[0], 1.0)
        self.assertAlmostEqual(values[-1], 2.0)

    def test_volume_multiplier_15_matches_default_behavior(self) -> None:
        if str(SRC) not in sys.path:
            sys.path.insert(0, str(SRC))
        from backtest.analysis_tbl_314 import run_tbl_backtest

        kwargs = {
            "symbols": ["AAPL", "MSFT", "NVDA"],
            "base_dir": ROOT / "data",
            "breakout_window": 10,
            "stop_atr_mult": 2.0,
            "partial_tp_r": 2.0,
            "trailing_atr_mult": 3.0,
        }
        baseline = run_tbl_backtest(**kwargs)
        with_explicit = run_tbl_backtest(**kwargs, volume_multiplier=1.5)
        self.assertEqual(baseline["metrics"], with_explicit["metrics"])


if __name__ == "__main__":
    unittest.main()
