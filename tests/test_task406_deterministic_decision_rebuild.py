from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task406_deterministic_decision_rebuild import build_task406_deterministic_decision_rebuild


class TestTask406DeterministicDecisionRebuild(unittest.TestCase):
    def test_rebuild_starts_from_raw_and_writes_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            rows = []
            for i in range(20):
                close = 10 + i * 0.5
                rows.append(
                    {
                        "timestamp": f"2026-01-02T{14 + (i // 4):02d}:{(i % 4) * 15:02d}:00Z",
                        "open": close - 0.1,
                        "high": close + 0.05,
                        "low": close - 0.2,
                        "close": close,
                        "volume": 1000 + i * 10,
                        "trade_count": 10 + i,
                        "vwap": close,
                    }
                )
            pd.DataFrame(rows).to_csv(raw / "AAA.csv", index=False)
            theme = root / "theme.csv"
            pd.DataFrame([{"symbol": "AAA", "theme": "test_theme", "role": "leader"}]).to_csv(theme, index=False)
            task401 = root / "old_task401.csv"
            pd.DataFrame(
                [
                    {
                        "decision_id": "D0",
                        "decision_kind": "ENTRY",
                        "decision_ts_utc": "2026-01-02T14:30:00Z",
                        "symbol": "AAA",
                        "theme_id": "test_theme",
                        "bucket": "ALLOW",
                        "lifecycle_id": "L0",
                    }
                ]
            ).to_csv(task401, index=False)

            artifacts = build_task406_deterministic_decision_rebuild(
                intraday_dir=raw,
                theme_universe_path=theme,
                task401_decisions_path=task401,
                raw_audit_out_dir=root / "raw_audit",
                out_dir=root / "out",
                symbols=["AAA"],
            )

            self.assertGreater(len(artifacts.enriched_decision_snapshot_log), 0)
            self.assertIn("raw_rebuild_source_of_truth_flag", artifacts.enriched_decision_snapshot_log.columns)
            self.assertGreater(len(artifacts.decision_factor_lineage_audit), 0)
            self.assertEqual(int(artifacts.decision_factor_lineage_audit["inferred_matching_used_flag"].max()), 0)
            self.assertEqual(int(artifacts.task_406b_decision["old_task401_used_as_source_of_truth_flag"].iloc[0]), 1)
            self.assertEqual(str(artifacts.task_406b_decision["raw_rebuild_mode"].iloc[0]), "task401_exact_decision_skeleton_with_raw_lineage")
            self.assertTrue((root / "out" / "task_406_deterministic_decision_rebuild.md").exists())


if __name__ == "__main__":
    unittest.main()
