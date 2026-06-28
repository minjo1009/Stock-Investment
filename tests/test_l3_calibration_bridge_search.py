from __future__ import annotations

import unittest

from src.brain.l3.calibration_bridge_search import (
    audit_source_event_outcome_bridge_pair,
    build_source_event_outcome_bridge_rows,
)


class L3CalibrationBridgeSearchTest(unittest.TestCase):
    def test_source_event_to_outcome_bridge_uses_exact_lifecycle_only(self) -> None:
        rows = build_source_event_outcome_bridge_rows(
            (
                {"source_event_id": "event-1", "lifecycle_id": "life-1"},
                {"source_event_id": "event-2", "lifecycle_id": "life-2"},
            ),
            (
                {"lifecycle_id": "life-1", "return_from_entry": "0.04", "positive_return_flag": "1"},
            ),
            outcome_source_table="unit.outcomes",
            bridge_source_artifact="unit.source|unit.outcomes",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].source_receipt_id, "event-1")
        self.assertEqual(rows[0].outcome_bridge_key, "life-1")
        self.assertEqual(rows[0].inferred_matching_used_flag, 0)
        self.assertEqual(rows[0].trade_output_flag, 0)

    def test_mismatched_lifecycle_has_no_bridge_and_marks_inferred_required(self) -> None:
        audit = audit_source_event_outcome_bridge_pair(
            ({"source_event_id": "event-1", "lifecycle_id": "life-1"},),
            ({"lifecycle_id": "life-2", "return_from_entry": "0.04", "positive_return_flag": "1"},),
            source_event_path="unit.source",
            outcome_path="unit.outcomes",
        )
        self.assertEqual(audit.exact_lifecycle_intersection_count, 0)
        self.assertEqual(audit.bridge_row_count, 0)
        self.assertEqual(audit.allowed_for_calibration_flag, 0)
        self.assertEqual(audit.inferred_matching_required_flag, 1)


if __name__ == "__main__":
    unittest.main()
