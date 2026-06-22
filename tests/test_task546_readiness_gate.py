from __future__ import annotations

import unittest

from src.backtest.build_task546_microstructure_live_capture_layer import (
    build_microstructure_live_source_contract,
    build_next_action_queue,
    build_readiness_gate,
    build_source_availability_audit,
)

import pandas as pd


class Task546ReadinessGateTest(unittest.TestCase):
    def test_gate_allows_nbbo_scope_but_not_deployment_when_full_depth_blocked(self) -> None:
        audit = build_source_availability_audit(build_microstructure_live_source_contract())
        lineage_audit = pd.DataFrame(
            [
                {"audit_name": "decision_to_client_order_to_order_to_fill_to_lifecycle", "pass_flag": 1},
            ]
        )
        gate = build_readiness_gate(audit, lineage_audit, {})
        self.assertEqual(gate.iloc[0]["readiness_gate"], "FULL_DEPTH_BLOCKED_BUT_NBBO_SCOPE_ALLOWED")
        self.assertEqual(int(gate.iloc[0]["paper_shadow_capture_ready_flag"]), 1)
        self.assertEqual(int(gate.iloc[0]["deployment_ready_flag"]), 0)
        actions = build_next_action_queue(gate, pd.DataFrame())
        self.assertEqual(actions.iloc[0]["next_task"], "Task547_Paper_Shadow_Microstructure_Capture_Run")


if __name__ == "__main__":
    unittest.main()
