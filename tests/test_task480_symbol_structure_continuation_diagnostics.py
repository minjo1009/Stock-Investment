from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task480_symbol_structure_continuation_diagnostics import (
    build_task480_symbol_structure_continuation_diagnostics,
)


class TestTask480SymbolStructureContinuationDiagnostics(unittest.TestCase):
    def test_task480_uses_exact_lifecycle_and_entry_safe_symbol_factors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task407 = root / "task407"
            raw = root / "raw"
            out = root / "out"
            task407.mkdir()
            raw.mkdir()
            rows = []
            for i in range(40):
                close = 100 + i * 0.35
                rows.append(
                    {
                        "timestamp": f"2026-01-05T{14 + (i // 4):02d}:{(i % 4) * 15:02d}:00Z",
                        "open": close - 0.15,
                        "high": close + 0.20,
                        "low": close - 0.35,
                        "close": close,
                        "volume": 10000 + i * 100,
                        "trade_count": 100 + i,
                        "vwap": close - 0.05,
                    }
                )
            pd.DataFrame(rows).to_csv(raw / "AAA.csv", index=False)
            decisions = pd.DataFrame(
                [
                    {
                        "decision_id": "D1",
                        "candidate_id": "C1",
                        "lifecycle_id": "L1",
                        "decision_kind": "ENTRY",
                        "decision_action": "ENTRY",
                        "symbol": "AAA",
                        "bucket": "ALLOW",
                        "decision_ts_utc": "2026-01-05T16:45:00Z",
                        "raw_bar_id": "AAA|2026-01-05T16:45:00Z",
                    },
                    {
                        "decision_id": "D2",
                        "candidate_id": "C2",
                        "lifecycle_id": "L2",
                        "decision_kind": "ENTRY",
                        "decision_action": "ENTRY",
                        "symbol": "AAA",
                        "bucket": "ALLOW",
                        "decision_ts_utc": "2026-01-05T17:00:00Z",
                        "raw_bar_id": "AAA|2026-01-05T17:00:00Z",
                    },
                    {
                        "decision_id": "D3",
                        "candidate_id": "C3",
                        "lifecycle_id": "",
                        "decision_kind": "ENTRY",
                        "decision_action": "SKIP",
                        "symbol": "AAA",
                        "bucket": "REJECT",
                        "decision_ts_utc": "2026-01-05T17:15:00Z",
                        "raw_bar_id": "AAA|2026-01-05T17:15:00Z",
                    },
                ]
            )
            labels = pd.DataFrame(
                [
                    {
                        "lifecycle_id": "L1",
                        "entry_decision_id": "D1",
                        "symbol": "AAA",
                        "entry_ts": "2026-01-05T16:45:00Z",
                        "exit_ts": "2026-01-05T18:00:00Z",
                        "event_path": "ENTRY_ADD_SCALE_EXIT",
                        "add_flag": 1,
                        "scale_flag": 1,
                        "reduce_flag": 0,
                        "exit_flag": 1,
                        "return_from_entry": 0.03,
                        "net_return_from_entry": 0.027,
                        "lifecycle_outcome_class": "add_scale_success",
                    },
                    {
                        "lifecycle_id": "L2",
                        "entry_decision_id": "D2",
                        "symbol": "AAA",
                        "entry_ts": "2026-01-05T17:00:00Z",
                        "exit_ts": "2026-01-05T18:15:00Z",
                        "event_path": "ENTRY_REDUCE_EXIT",
                        "add_flag": 0,
                        "scale_flag": 0,
                        "reduce_flag": 1,
                        "exit_flag": 1,
                        "return_from_entry": -0.01,
                        "net_return_from_entry": -0.013,
                        "lifecycle_outcome_class": "entry_reduce_failure",
                    },
                ]
            )
            decisions.to_csv(task407 / "raw_native_decision_snapshot_log.csv", index=False)
            labels.to_csv(task407 / "raw_native_lifecycle_labels.csv", index=False)

            artifacts = build_task480_symbol_structure_continuation_diagnostics(
                task407_dir=task407,
                intraday_dir=raw,
                out_dir=out,
            )

            self.assertEqual(int(artifacts.task_480_decision["inferred_lifecycle_matching_used_flag"].iloc[0]), 0)
            self.assertEqual(int(artifacts.task_480_decision["symbol_date_price_time_fallback_used_flag"].iloc[0]), 0)
            self.assertIn("entry_bar_quality_state", artifacts.symbol_structure_snapshot_log.columns)
            self.assertIn("lifecycle_outcome_class", artifacts.symbol_structure_label_panel.columns)
            self.assertEqual(int(artifacts.symbol_structure_leakage_audit["leakage_audit_pass"].iloc[0]), 1)
            self.assertTrue(
                artifacts.missing_microstructure_factor_audit["availability_status"].eq("missing_raw_source").any()
            )
            self.assertTrue((out / "task_480_symbol_structure_continuation_diagnostics.md").exists())


if __name__ == "__main__":
    unittest.main()
