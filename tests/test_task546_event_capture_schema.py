from __future__ import annotations

import unittest

from src.backtest.build_task546_microstructure_live_capture_layer import (
    build_decision_snapshot_contract,
    build_event_clock_consistency_contract,
    build_microstructure_capture_schema,
)


class Task546EventCaptureSchemaTest(unittest.TestCase):
    def test_capture_schema_requires_receive_timestamp_and_preorder_snapshot(self) -> None:
        schema = build_microstructure_capture_schema()
        self.assertIn("recv_ts_utc", set(schema["field_name"]))
        self.assertIn("decision_microstructure_snapshot_log", set(schema["table_name"]))
        snapshot = build_decision_snapshot_contract()
        self.assertEqual(int(snapshot["pre_order_required_flag"].min()), 1)
        clock = build_event_clock_consistency_contract()
        self.assertIn("historical_without_recv_ts_not_live_ready", set(clock["rule_name"]))


if __name__ == "__main__":
    unittest.main()
