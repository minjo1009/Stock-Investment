from __future__ import annotations

import unittest

from app.task_091_broker_lifecycle_gate import _decide


class TestTask091BrokerLifecycleGate(unittest.TestCase):
    def test_fail_on_unknown(self) -> None:
        decision = _decide(
            submitted_orders=1,
            filled_orders=0,
            cancelled_orders=0,
            unknown_events=1,
            reconciliation_critical_count=0,
            market_order_path_count=0,
            cancel_unknown_escalation_count=0,
        )
        self.assertEqual(decision.status, "FAIL")
        self.assertEqual(decision.answer, "NO")

    def test_pass_with_submitted_and_terminal(self) -> None:
        decision = _decide(
            submitted_orders=2,
            filled_orders=1,
            cancelled_orders=0,
            unknown_events=0,
            reconciliation_critical_count=0,
            market_order_path_count=0,
            cancel_unknown_escalation_count=0,
        )
        self.assertEqual(decision.status, "PASS")
        self.assertEqual(decision.answer, "YES")

    def test_warning_without_order_sample(self) -> None:
        decision = _decide(
            submitted_orders=0,
            filled_orders=0,
            cancelled_orders=0,
            unknown_events=0,
            reconciliation_critical_count=0,
            market_order_path_count=0,
            cancel_unknown_escalation_count=0,
        )
        self.assertEqual(decision.status, "WARNING")
        self.assertEqual(decision.answer, "NO")


if __name__ == "__main__":
    unittest.main()

