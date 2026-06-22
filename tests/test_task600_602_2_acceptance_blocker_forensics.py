from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.app.task_600_602_2_acceptance_blocker_forensics import (
    ExitRules,
    build_concentration_forensics,
    build_exit_distribution,
    build_exit_generator,
    build_position_replay_rootcause,
)


class Task6006022AcceptanceBlockerForensicsTest(unittest.TestCase):
    def test_exit_generator_creates_timeout_sell_without_broker_truth_mutation(self) -> None:
        position_lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "life-1",
                    "symbol": "MSFT",
                    "entry_order_id": "ord-buy-1",
                    "entry_fill_id": "fill-buy-1",
                    "entry_time": "2026-06-03T13:00:00Z",
                    "entry_price": 100.0,
                    "open_qty": 1.0,
                    "closed_qty": 0.0,
                    "state": "OPEN",
                }
            ]
        )
        snapshots = pd.DataFrame(
            [
                {
                    "symbol": "MSFT",
                    "source_price": 101.5,
                    "source_price_ts": "2026-06-03T19:31:00Z",
                    "snapshot_id": "snapshot-1",
                    "source_type": "TEST_PRICE",
                }
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            generated, sells, residual, matrix = build_exit_generator(
                position_lifecycle,
                snapshots,
                raw_root=Path(tmp),
                rules=ExitRules(max_hold_minutes=390),
            )

        self.assertEqual(len(sells), 1)
        self.assertEqual(sells.iloc[0]["side"], "SELL")
        self.assertEqual(sells.iloc[0]["exit_reason"], "TIMEOUT")
        self.assertEqual(int(sells.iloc[0]["broker_truth_fill_flag"]), 0)
        self.assertEqual(int(sells.iloc[0]["diagnostic_generated_fill_flag"]), 1)
        self.assertEqual(float(sells.iloc[0]["realized_pnl"]), 1.5)
        self.assertTrue(residual.empty)
        self.assertEqual(int(matrix.loc[matrix["metric"].eq("TIMEOUT 발생 수"), "count"].iloc[0]), 1)
        self.assertEqual(generated.iloc[0]["source_note"], "diagnostic_exit_generator_not_broker_truth_fill")

    def test_exit_distribution_groups_pnl_by_exit_type(self) -> None:
        generated = pd.DataFrame(
            [
                {"position_id": "p1", "state": "CLOSED", "exit_reason": "TIMEOUT", "realized_pnl": 1.0},
                {"position_id": "p2", "state": "CLOSED", "exit_reason": "TIMEOUT", "realized_pnl": -3.0},
                {"position_id": "p3", "state": "CLOSED", "exit_reason": "STOP", "realized_pnl": -2.0},
            ]
        )
        distribution = build_exit_distribution(generated)
        timeout = distribution.loc[distribution["exit_type"].eq("TIMEOUT")].iloc[0]
        self.assertEqual(int(timeout["count"]), 2)
        self.assertEqual(float(timeout["avg_pnl"]), -1.0)
        self.assertEqual(float(timeout["median_pnl"]), -1.0)

    def test_concentration_forensics_computes_top_shares_and_root_causes(self) -> None:
        rows = []
        for symbol, fills in [("AMD", 10), ("AMZN", 9), ("MSFT", 5), ("NVDA", 0)]:
            for i in range(max(fills, 1)):
                rows.append({"symbol": symbol, "stage": "GENERATED", "eligibility": "ELIGIBLE"})
                rows.append({"symbol": symbol, "stage": "RANKED", "eligibility": "ELIGIBLE"})
                rows.append({"symbol": symbol, "stage": "ELIGIBLE", "eligibility": "ELIGIBLE"})
            for i in range(fills):
                rows.append({"symbol": symbol, "stage": "ORDERED", "eligibility": "ELIGIBLE"})
                rows.append({"symbol": symbol, "stage": "FILLED", "eligibility": "ELIGIBLE"})
        symbol_counts, metrics, rootcause = build_concentration_forensics(pd.DataFrame(rows))

        self.assertEqual(int(symbol_counts.loc[symbol_counts["symbol"].eq("AMD"), "filled_count"].iloc[0]), 10)
        self.assertEqual(float(metrics.iloc[0]["top3_share"]), 1.0)
        self.assertGreater(float(metrics.iloc[0]["gini_coefficient"]), 0)
        self.assertIn("Cooldown Failure", set(rootcause["rootcause_category"]))

    def test_position_replay_rootcause_identifies_top_failure_categories(self) -> None:
        position_lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "life-1",
                    "symbol": "MSFT",
                    "state": "OPEN",
                    "exit_fill_id": "",
                }
            ]
        )
        generated = pd.DataFrame(
            [
                {
                    "position_id": "life-1",
                    "generated_state": "CLOSED",
                }
            ]
        )
        positions = pd.DataFrame([{"symbol": "MSFT", "quantity": 1}])
        orders = pd.DataFrame([{"order_id": "ord-1", "intent_key": ""}])
        diff, rootcause = build_position_replay_rootcause(position_lifecycle, generated, positions, orders)

        self.assertEqual(diff.iloc[0]["runtime_state"], "OPEN")
        self.assertIn("Missing Exit", diff.iloc[0]["diff_reason"])
        self.assertIn("Position Aggregation Error", set(rootcause["rootcause_category"]))
        self.assertGreaterEqual(len(rootcause.head(5)), 5)


if __name__ == "__main__":
    unittest.main()
