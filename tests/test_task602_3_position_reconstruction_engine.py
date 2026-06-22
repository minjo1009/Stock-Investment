from __future__ import annotations

import unittest

import pandas as pd

from src.replay.position_reconstruction_engine import build_position_replay_acceptance


class Task6023PositionReconstructionEngineTest(unittest.TestCase):
    def _fills_for_positions(self, closed_count: int, open_count: int = 0) -> pd.DataFrame:
        rows = []
        for index in range(1, closed_count + 1):
            rows.append(
                {
                    "fill_id": f"entry-{index}",
                    "order_id": f"entry-order-{index}",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "filled_quantity": 1.0,
                    "fill_price": 100.0 + index,
                }
            )
            rows.append(
                {
                    "fill_id": f"exit-{index}",
                    "order_id": f"exit-order-{index}",
                    "symbol": "MSFT",
                    "side": "SELL",
                    "filled_quantity": 1.0,
                    "fill_price": 110.0 + index,
                }
            )
        for index in range(closed_count + 1, closed_count + open_count + 1):
            rows.append(
                {
                    "fill_id": f"entry-{index}",
                    "order_id": f"entry-order-{index}",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "filled_quantity": 1.0,
                    "fill_price": 100.0 + index,
                }
            )
            rows.append(
                {
                    "fill_id": f"same-symbol-unlinked-exit-{index}",
                    "order_id": f"unlinked-exit-order-{index}",
                    "symbol": "MSFT",
                    "side": "SELL",
                    "filled_quantity": 1.0,
                    "fill_price": 110.0 + index,
                }
            )
        return pd.DataFrame(rows)

    def _lifecycle_rows(self, closed_count: int, open_count: int = 0) -> pd.DataFrame:
        rows = []
        for index in range(1, closed_count + 1):
            rows.append(
                {
                    "position_id": f"life-{index}",
                    "symbol": "MSFT",
                    "entry_order_id": f"entry-order-{index}",
                    "entry_fill_id": f"entry-{index}",
                    "exit_order_id": f"exit-order-{index}",
                    "exit_fill_id": f"exit-{index}",
                    "entry_qty": 1.0,
                    "open_qty": 0.0,
                    "closed_qty": 1.0,
                    "entry_price": 100.0 + index,
                    "exit_price": 110.0 + index,
                    "realized_pnl": 10.0,
                    "state": "CLOSED",
                }
            )
        for index in range(closed_count + 1, closed_count + open_count + 1):
            rows.append(
                {
                    "position_id": f"life-{index}",
                    "symbol": "MSFT",
                    "entry_order_id": f"entry-order-{index}",
                    "entry_fill_id": f"entry-{index}",
                    "exit_order_id": "",
                    "exit_fill_id": "",
                    "entry_qty": 1.0,
                    "open_qty": 1.0,
                    "closed_qty": 0.0,
                    "entry_price": 100.0 + index,
                    "exit_price": "",
                    "realized_pnl": "",
                    "state": "OPEN",
                }
            )
        return pd.DataFrame(rows)

    def _decision_order_frames(self, fills: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        decisions = pd.DataFrame([{"decision_id": f"decision-{index}"} for index in range(1, 7)])
        orders = pd.DataFrame(
            [
                {
                    "order_id": row["order_id"],
                    "decision_id": f"decision-{index + 1}",
                }
                for index, row in fills.reset_index(drop=True).iterrows()
            ]
        )
        return decisions, orders

    def test_position_match_rate_passes_above_80_percent_when_closed_lifecycle_rows_exist(self) -> None:
        fills = self._fills_for_positions(closed_count=5, open_count=1)
        lifecycle = self._lifecycle_rows(closed_count=5, open_count=1)
        decisions, orders = self._decision_order_frames(fills)

        result = build_position_replay_acceptance(decisions, orders, fills, lifecycle)

        position = result.validation.loc[result.validation["surface"].eq("Position Match")].iloc[0]
        self.assertGreater(float(position["match_rate"]), 0.80)
        self.assertEqual(float(position["match_rate"]), 0.833333)
        self.assertEqual(position["status"], "PASS")
        self.assertEqual(int(result.decision.iloc[0]["inferred_matching_used_flag"]), 0)
        self.assertEqual(int(result.reconstructed_positions["proximity_fallback_used_flag"].max()), 0)

    def test_position_match_rate_fails_at_or_below_50_percent_when_exits_are_missing(self) -> None:
        fills = self._fills_for_positions(closed_count=0, open_count=4)
        lifecycle = self._lifecycle_rows(closed_count=0, open_count=4)
        decisions, orders = self._decision_order_frames(fills)

        result = build_position_replay_acceptance(decisions, orders, fills, lifecycle)

        position = result.validation.loc[result.validation["surface"].eq("Position Match")].iloc[0]
        self.assertLessEqual(float(position["match_rate"]), 0.50)
        self.assertEqual(float(position["match_rate"]), 0.0)
        self.assertEqual(position["status"], "FAIL")
        self.assertTrue(result.position_replay_diff["diff_reason"].str.contains("Missing Exit").any())
        self.assertTrue(result.position_replay_diff["diff_reason"].str.contains("Missing Fill Link").any())

    def test_same_symbol_exit_fill_is_not_used_without_exact_exit_fill_id(self) -> None:
        fills = pd.DataFrame(
            [
                {
                    "fill_id": "entry-1",
                    "order_id": "entry-order-1",
                    "symbol": "AMD",
                    "side": "BUY",
                    "filled_quantity": 1.0,
                    "fill_price": 100.0,
                },
                {
                    "fill_id": "same-symbol-exit",
                    "order_id": "exit-order-1",
                    "symbol": "AMD",
                    "side": "SELL",
                    "filled_quantity": 1.0,
                    "fill_price": 90.0,
                },
            ]
        )
        lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "life-1",
                    "symbol": "AMD",
                    "entry_order_id": "entry-order-1",
                    "entry_fill_id": "entry-1",
                    "exit_order_id": "exit-order-1",
                    "exit_fill_id": "missing-exact-exit-id",
                    "entry_qty": 1.0,
                    "open_qty": 0.0,
                    "closed_qty": 1.0,
                    "entry_price": 100.0,
                    "exit_price": 90.0,
                    "realized_pnl": -10.0,
                    "state": "CLOSED",
                }
            ]
        )
        decisions = pd.DataFrame([{"decision_id": "decision-1"}])
        orders = pd.DataFrame(
            [
                {"order_id": "entry-order-1", "decision_id": "decision-1"},
                {"order_id": "exit-order-1", "decision_id": "decision-exit-1"},
            ]
        )

        result = build_position_replay_acceptance(decisions, orders, fills, lifecycle)

        position = result.validation.loc[result.validation["surface"].eq("Position Match")].iloc[0]
        self.assertEqual(float(position["match_rate"]), 0.0)
        self.assertEqual(result.reconstructed_positions.iloc[0]["state"], "UNRECONSTRUCTED_MISSING_EXIT_FILL")
        self.assertEqual(int(result.reconstructed_positions.iloc[0]["exit_fill_exact_match_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
