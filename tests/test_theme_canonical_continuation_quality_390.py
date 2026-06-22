from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_theme_canonical_continuation_quality_390 import (
    build_theme_canonical_continuation_quality_390,
)


class TestThemeCanonicalContinuationQuality390(unittest.TestCase):
    def test_theme_quality_uses_only_canonical_stream(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task388 = root / "task388"
            task388.mkdir()
            out = root / "out"
            theme_path = root / "themes.csv"
            _write_fixture(task388, theme_path)

            artifacts = build_theme_canonical_continuation_quality_390(
                task388_dir=task388,
                theme_universe_path=theme_path,
                out_dir=out,
            )

            decision = artifacts.task_390_decision.iloc[0]
            add_scale = artifacts.add_scale_reinforcement_quality
            reduce = artifacts.reduce_weakening_quality

            self.assertEqual(str(decision["task_390_verdict"]), "COMPLETE_PASS")
            self.assertEqual(int(decision["reconstruction_used_flag"]), 0)
            self.assertIn("add_scale", set(add_scale["reinforcement_group"].astype(str)))
            self.assertIn("reduce_present", set(reduce["reduce_group"].astype(str)))
            self.assertTrue((out / "theme_continuation_quality.csv").exists())
            self.assertTrue((out / "task_390_theme_canonical_continuation_quality.md").exists())


def _write_fixture(task388: Path, theme_path: Path) -> None:
    pd.DataFrame(
        [
            {"theme": "ai_semiconductors", "symbol": "NVDA", "role": "gpu_leader"},
            {"theme": "cloud_ai_platforms", "symbol": "MSFT", "role": "cloud_leader"},
        ]
    ).to_csv(theme_path, index=False)
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "symbol": "NVDA", "entry_ts": "2026-01-01T14:30:00Z", "exit_ts": "2026-01-01T16:00:00Z", "bars_held": 6, "add_flag": 1, "scale_flag": 1, "reduce_flag": 0, "exit_reason": "intraday_time_exit", "return_from_entry": 0.05},
            {"lifecycle_id": "L2", "symbol": "MSFT", "entry_ts": "2026-01-01T14:30:00Z", "exit_ts": "2026-01-01T15:30:00Z", "bars_held": 4, "add_flag": 0, "scale_flag": 0, "reduce_flag": 1, "exit_reason": "intraday_drawdown_exit", "return_from_entry": -0.02},
        ]
    ).to_csv(task388 / "intraday_canonical_lifecycle_summary.csv", index=False)
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "symbol": "NVDA", "event_type": "ENTRY", "event_timestamp": "2026-01-01T14:30:00Z", "price": 100, "size_multiplier": 0.5},
            {"lifecycle_id": "L1", "symbol": "NVDA", "event_type": "ADD", "event_timestamp": "2026-01-01T14:45:00Z", "price": 102, "size_multiplier": 0.75},
            {"lifecycle_id": "L1", "symbol": "NVDA", "event_type": "SCALE", "event_timestamp": "2026-01-01T15:00:00Z", "price": 105, "size_multiplier": 1.0},
            {"lifecycle_id": "L1", "symbol": "NVDA", "event_type": "EXIT", "event_timestamp": "2026-01-01T16:00:00Z", "price": 105, "size_multiplier": 0.0},
            {"lifecycle_id": "L2", "symbol": "MSFT", "event_type": "ENTRY", "event_timestamp": "2026-01-01T14:30:00Z", "price": 100, "size_multiplier": 0.5},
            {"lifecycle_id": "L2", "symbol": "MSFT", "event_type": "REDUCE", "event_timestamp": "2026-01-01T15:00:00Z", "price": 99, "size_multiplier": 0.5},
            {"lifecycle_id": "L2", "symbol": "MSFT", "event_type": "EXIT", "event_timestamp": "2026-01-01T15:30:00Z", "price": 98, "size_multiplier": 0.0},
        ]
    ).to_csv(task388 / "intraday_canonical_event_log.csv", index=False)


if __name__ == "__main__":
    unittest.main()
