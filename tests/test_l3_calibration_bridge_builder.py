from __future__ import annotations

import unittest

from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod
from src.brain.l3.calibration_bridge_builder import bridge_rows_from_records


class L3CalibrationBridgeBuilderTest(unittest.TestCase):
    def test_builds_bridge_only_from_explicit_keys(self) -> None:
        rows = bridge_rows_from_records(
            [
                {
                    "meaning_id": "l3v2:l2-1",
                    "l2_primitive_id": "l2-1",
                    "source_receipt_id": "receipt-1",
                    "lifecycle_id": "life-1",
                    "win_flag": "1",
                }
            ],
            outcome_source_table="unit.outcomes",
            bridge_source_artifact="unit.bridge",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].bridge_method, L3OutcomeBridgeMethod.DIRECT_MEANING_ID)
        self.assertEqual(rows[0].inferred_matching_used_flag, 0)

    def test_records_without_l3_keys_do_not_create_bridges(self) -> None:
        rows = bridge_rows_from_records(
            [
                {
                    "symbol": "AAPL",
                    "entry_ts": "2026-06-01T10:00:00Z",
                    "lifecycle_id": "life-1",
                    "win_flag": "1",
                }
            ],
            outcome_source_table="unit.outcomes",
            bridge_source_artifact="unit.bridge",
        )
        self.assertEqual(rows, ())


if __name__ == "__main__":
    unittest.main()
