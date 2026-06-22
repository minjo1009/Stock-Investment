from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task407_raw_native_vectorized_rebuild import build_task407_raw_native_vectorized_rebuild


class TestTask407RawNativeVectorizedRebuild(unittest.TestCase):
    def test_raw_native_rebuild_does_not_use_task401_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            rows = []
            for day in range(1, 4):
                for i in range(30):
                    close = 10 + i * 0.4 + day * 0.05
                    rows.append(
                        {
                            "timestamp": f"2026-01-0{day}T{14 + (i // 4):02d}:{(i % 4) * 15:02d}:00Z",
                            "open": close - 0.1,
                            "high": close + 0.05,
                            "low": close - 0.2,
                            "close": close,
                            "volume": 1000 + i * 100,
                        }
                    )
            pd.DataFrame(rows).to_csv(raw / "AAA.csv", index=False)
            theme = root / "theme.csv"
            pd.DataFrame([{"symbol": "AAA", "theme": "test_theme", "role": "leader"}]).to_csv(theme, index=False)

            artifacts = build_task407_raw_native_vectorized_rebuild(
                intraday_dir=raw,
                theme_universe_path=theme,
                out_dir=root / "out",
                symbols=["AAA"],
            )

            self.assertGreater(len(artifacts.raw_native_decision_snapshot_log), 0)
            self.assertEqual(int(artifacts.task_407_decision["task401_skeleton_used_flag"].iloc[0]), 0)
            self.assertEqual(int(artifacts.task_407_decision["inferred_matching_used_flag"].iloc[0]), 0)
            self.assertIn("lifecycle_outcome_class", artifacts.raw_native_lifecycle_labels.columns)
            self.assertTrue((root / "out" / "task_407_raw_native_vectorized_rebuild.md").exists())


if __name__ == "__main__":
    unittest.main()
