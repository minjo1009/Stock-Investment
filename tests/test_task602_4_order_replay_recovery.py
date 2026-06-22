from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.replay.order_reconstruction_engine import (
    build_order_replay_acceptance,
    write_order_replay_outputs,
)


class Task6024OrderReplayRecoveryTest(unittest.TestCase):
    def _orders_with_missing_lineage(self) -> pd.DataFrame:
        rows = []
        for index in range(1, 49):
            rows.append(
                {
                    "order_id": f"order-{index:02d}",
                    "run_id": f"run-{index:02d}",
                    "symbol": "MSFT",
                    "side": "SELL" if index > 25 else "BUY",
                    "quantity": 1.0,
                    "intent_key": f"decision-{index:02d}",
                    "submitted_at": f"2026-06-03T00:{index:02d}:00Z",
                    "status": "FILLED",
                    "raw_status": "UNKNOWN",
                    "environment": "paper",
                }
            )
        for index, state in enumerate(
            ["CANCEL_IN_PROGRESS", "CANCELLED", "CANCELLED", "CANCELLED", "CANCELLED", "UNKNOWN"],
            start=49,
        ):
            rows.append(
                {
                    "order_id": f"order-{index:02d}",
                    "run_id": f"run-{index:02d}",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "quantity": 1.0,
                    "intent_key": None,
                    "submitted_at": f"2026-06-03T00:{index:02d}:00Z",
                    "status": state,
                    "raw_status": "ORDER_NOT_FOUND",
                    "environment": "paper",
                }
            )
        return pd.DataFrame(rows)

    def test_missing_intent_key_cancel_rows_are_lineage_gaps_not_order_mismatches(self) -> None:
        orders = self._orders_with_missing_lineage()
        decisions = pd.DataFrame([{"decision_id": f"decision-{index:02d}"} for index in range(1, 49)])
        fills = pd.DataFrame(
            [
                {
                    "fill_id": f"fill-{index:02d}",
                    "order_id": f"order-{index:02d}",
                    "run_id": f"run-{index:02d}",
                    "symbol": "MSFT",
                    "side": "SELL" if index > 25 else "BUY",
                    "filled_quantity": 1.0,
                    "fill_price": 100.0,
                }
                for index in range(1, 49)
            ]
        )

        result = build_order_replay_acceptance(decisions, orders, fills)

        order = result.validation.loc[result.validation["surface"].eq("Order Match")].iloc[0]
        self.assertEqual(float(order["match_rate"]), 1.0)
        self.assertEqual(order["status"], "STRETCH")
        self.assertEqual(int(result.decision.iloc[0]["missing_intent_key_rows"]), 6)
        self.assertEqual(int(result.decision.iloc[0]["inferred_matching_used_flag"]), 0)
        self.assertEqual(int(result.reconstructed_orders["proximity_fallback_used_flag"].max()), 0)
        self.assertEqual(len(result.order_replay_diff), 6)
        self.assertTrue(result.order_replay_diff["diff_reason"].str.contains("Decision lineage missing").all())

    def test_fill_match_requires_exact_order_id(self) -> None:
        orders = pd.DataFrame(
            [
                {
                    "order_id": "exact-order",
                    "run_id": "run-1",
                    "symbol": "AMD",
                    "side": "BUY",
                    "quantity": 1.0,
                    "intent_key": "decision-1",
                    "status": "FILLED",
                    "raw_status": "UNKNOWN",
                    "environment": "paper",
                }
            ]
        )
        decisions = pd.DataFrame([{"decision_id": "decision-1"}])
        fills = pd.DataFrame(
            [
                {
                    "fill_id": "same-symbol-fill",
                    "order_id": "different-order",
                    "symbol": "AMD",
                    "side": "BUY",
                    "filled_quantity": 1.0,
                    "fill_price": 100.0,
                }
            ]
        )

        result = build_order_replay_acceptance(decisions, orders, fills)

        fill = result.validation.loc[result.validation["surface"].eq("Fill Match")].iloc[0]
        order = result.validation.loc[result.validation["surface"].eq("Order Match")].iloc[0]
        self.assertEqual(float(order["match_rate"]), 1.0)
        self.assertEqual(float(fill["match_rate"]), 0.0)
        self.assertEqual(fill["status"], "FAIL")

    def test_required_artifacts_are_written_with_order_diff_columns(self) -> None:
        orders = self._orders_with_missing_lineage()
        result = build_order_replay_acceptance(pd.DataFrame(), orders, pd.DataFrame())

        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_order_replay_outputs(result, report_dir)

            diff = pd.read_csv(report_dir / "order_replay_diff.csv")
            self.assertEqual(list(diff.columns), ["order_id", "runtime_state", "replay_state", "diff_reason"])
            self.assertTrue((report_dir / "order_replay_gap_report.md").exists())
            self.assertTrue((report_dir / "order_replay_acceptance_report.md").exists())
            self.assertTrue((report_dir / "task_602_4_decision.csv").exists())
            self.assertTrue((report_dir / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
