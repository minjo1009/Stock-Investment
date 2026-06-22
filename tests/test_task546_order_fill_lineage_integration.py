from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task546_microstructure_live_capture_layer import (
    build_decision_to_lifecycle_lineage_audit,
    build_order_lineage,
)


class Task546OrderFillLineageIntegrationTest(unittest.TestCase):
    def test_decision_client_order_fill_lifecycle_lineage_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions = root / "decisions.csv"
            lineage = root / "lineage.csv"
            pd.DataFrame(
                [
                    {
                        "decision_id": "D1",
                        "symbol": "AAA",
                        "decision_action": "SHADOW_ENTRY",
                        "receive_ts_available_flag": 0,
                        "live_clock_record_flag": 0,
                        "historical_seed_record_flag": 1,
                    }
                ]
            ).to_csv(decisions, index=False)
            pd.DataFrame(
                [
                    {
                        "decision_id": "D1",
                        "client_order_id": "C1",
                        "order_id": "O1",
                        "fill_id": "F1",
                        "lifecycle_id": "L1",
                        "lineage_complete_flag": 1,
                        "broker_truth_flag": 0,
                        "shadow_mode_flag": 1,
                    }
                ]
            ).to_csv(lineage, index=False)
            out = build_order_lineage(decisions, lineage)
            audit = build_decision_to_lifecycle_lineage_audit(out)
            self.assertEqual(int(out.iloc[0]["historical_seed_only_flag"]), 1)
            complete = audit[audit["audit_name"].eq("decision_to_client_order_to_order_to_fill_to_lifecycle")].iloc[0]
            self.assertEqual(int(complete["pass_flag"]), 1)


if __name__ == "__main__":
    unittest.main()
