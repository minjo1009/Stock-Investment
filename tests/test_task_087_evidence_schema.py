from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTask087EvidenceSchema(unittest.TestCase):
    def test_no_order_sample_becomes_warning(self) -> None:
        from app.task_087_pilot_evidence import evaluate_evidence_status

        payload = {
            "failure_reasons": [],
            "warnings": [],
            "order_attempts": 0,
            "filled_orders": 0,
            "cancel_observed": False,
            "cancel_success_rate": 0.0,
            "unknown_events": 0,
            "reconciliation_critical_count": 0,
            "unresolved_late_fill_count": 0,
            "cancel_unknown_escalation_count": 0,
            "position_mismatch_count": 0,
            "market_order_attempted": False,
        }
        status = evaluate_evidence_status(payload)
        self.assertEqual(status.status, "WARNING")
        self.assertIn("NO_SIGNAL_OR_NO_ORDER_SAMPLE", status.warnings)

    def test_unknown_event_becomes_fail(self) -> None:
        from app.task_087_pilot_evidence import evaluate_evidence_status

        payload = {
            "failure_reasons": [],
            "warnings": [],
            "order_attempts": 3,
            "filled_orders": 1,
            "cancel_observed": True,
            "cancel_success_rate": 1.0,
            "unknown_events": 1,
            "reconciliation_critical_count": 0,
            "unresolved_late_fill_count": 0,
            "cancel_unknown_escalation_count": 0,
            "position_mismatch_count": 0,
            "market_order_attempted": False,
        }
        status = evaluate_evidence_status(payload)
        self.assertEqual(status.status, "FAIL")
        self.assertIn("UNKNOWN_ORDER_EXISTS", status.failure_reasons)


if __name__ == "__main__":
    unittest.main()
