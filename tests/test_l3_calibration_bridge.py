from __future__ import annotations

import unittest

from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow, bridge_row_to_dict


class L3CalibrationBridgeTest(unittest.TestCase):
    def test_explicit_bridge_row_is_diagnostic_only(self) -> None:
        row = L3OutcomeBridgeRow(
            bridge_id="bridge-1",
            meaning_id="l3v2:l2-1",
            l2_primitive_id="l2-1",
            source_receipt_id="receipt-1",
            outcome_source_table="docs/reports/task_391_intraday_canonical_oos_validation/split_lifecycle_panel.csv",
            outcome_bridge_key="life-1",
            lifecycle_id="life-1",
            continuation_id="",
            bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
            bridge_source_artifact="docs/reports/task_l3_calibration_rule_migration/l3_calibration_bridge_gap_audit.csv",
            inferred_matching_used_flag=0,
        )
        self.assertTrue(row.diagnostic_only)
        self.assertEqual(row.trade_output_flag, 0)
        self.assertEqual(bridge_row_to_dict(row)["bridge_method"], "MANIFEST_BACKED_EXACT_KEY")

    def test_inferred_bridge_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            L3OutcomeBridgeRow(
                bridge_id="bridge-2",
                meaning_id="l3v2:l2-1",
                l2_primitive_id="",
                source_receipt_id="",
                outcome_source_table="unsafe.proximity",
                outcome_bridge_key="AAPL:2026-06-01",
                lifecycle_id="",
                continuation_id="",
                bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
                bridge_source_artifact="unsafe",
                inferred_matching_used_flag=1,
            )


if __name__ == "__main__":
    unittest.main()
