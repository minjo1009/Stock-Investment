from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.app.task_600_603_acceptance_program_implementation import (
    build_candidate_funnel_events,
    build_position_lifecycle,
    build_replay_acceptance,
    write_runtime_tables,
)
from src.reporting.readiness_registry import build_readiness_registry_payload


class Task600603AcceptanceProgramImplementationTest(unittest.TestCase):
    def test_position_lifecycle_closes_only_with_exact_lifecycle_id(self) -> None:
        fills = pd.DataFrame(
            [
                {
                    "fill_id": "fill-buy-1",
                    "order_id": "ord-buy-1",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "filled_quantity": 1,
                    "fill_price": 100.0,
                    "filled_at": "2026-06-03T13:00:00Z",
                },
                {
                    "fill_id": "fill-sell-1",
                    "order_id": "ord-sell-1",
                    "symbol": "MSFT",
                    "side": "SELL",
                    "filled_quantity": 1,
                    "fill_price": 95.0,
                    "filled_at": "2026-06-03T14:00:00Z",
                },
            ]
        )
        orders = pd.DataFrame(
            [
                {"order_id": "ord-buy-1", "intent_key": "decision-1", "symbol": "MSFT", "side": "BUY"},
                {"order_id": "ord-sell-1", "intent_key": "decision-exit-1", "symbol": "MSFT", "side": "SELL"},
            ]
        )
        execution_events = pd.DataFrame(
            [
                {"order_id": "ord-buy-1", "decision_id": "decision-1", "lifecycle_id": "life-1", "reason_code": "ORDER_SUBMITTED"},
                {"order_id": "ord-sell-1", "decision_id": "decision-exit-1", "lifecycle_id": "life-1", "reason_code": "STOP"},
            ]
        )

        lifecycle, hard_stop, unresolved, validation = build_position_lifecycle(
            fills,
            orders,
            execution_events,
            {"MSFT": 94.0},
        )

        self.assertEqual(len(lifecycle), 1)
        row = lifecycle.iloc[0]
        self.assertEqual(row["position_id"], "life-1")
        self.assertEqual(row["state"], "CLOSED")
        self.assertEqual(row["exit_reason"], "STOP")
        self.assertEqual(float(row["realized_pnl"]), -5.0)
        self.assertEqual(int(row["proximity_fallback_used_flag"]), 0)
        self.assertTrue(unresolved.empty)
        self.assertTrue(hard_stop.empty)
        self.assertEqual(int(validation.iloc[0]["accepted_closed_position_rows"]), 1)

    def test_unmatched_sell_is_unresolved_not_closed_by_symbol_proximity(self) -> None:
        fills = pd.DataFrame(
            [
                {
                    "fill_id": "fill-buy-1",
                    "order_id": "ord-buy-1",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "filled_quantity": 1,
                    "fill_price": 100.0,
                    "filled_at": "2026-06-03T13:00:00Z",
                },
                {
                    "fill_id": "fill-sell-1",
                    "order_id": "ord-sell-1",
                    "symbol": "MSFT",
                    "side": "SELL",
                    "filled_quantity": 1,
                    "fill_price": 95.0,
                    "filled_at": "2026-06-03T14:00:00Z",
                },
            ]
        )
        orders = pd.DataFrame([{"order_id": "ord-buy-1"}, {"order_id": "ord-sell-1"}])
        execution_events = pd.DataFrame(
            [
                {"order_id": "ord-buy-1", "decision_id": "decision-1", "lifecycle_id": "life-1", "reason_code": "ORDER_SUBMITTED"},
                {"order_id": "ord-sell-1", "decision_id": "decision-exit-1", "lifecycle_id": "different-life", "reason_code": "STOP"},
            ]
        )

        lifecycle, _, unresolved, validation = build_position_lifecycle(fills, orders, execution_events, {"MSFT": 94.0})

        self.assertEqual(lifecycle.iloc[0]["state"], "OPEN")
        self.assertEqual(int(validation.iloc[0]["accepted_closed_position_rows"]), 0)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved.iloc[0]["resolution_status"], "UNRESOLVED_EXIT_NO_EXACT_ENTRY_LIFECYCLE")
        self.assertIn("no_symbol_date_price_time_proximity", unresolved.iloc[0]["forbidden_fallbacks"])

    def test_candidate_funnel_uses_decision_order_fill_and_closed_stages(self) -> None:
        decisions = pd.DataFrame(
            [
                {
                    "decision_id": "decision-1",
                    "created_at": "2026-06-03T13:00:00Z",
                    "symbol": "MSFT",
                    "score": 0.7,
                    "entry_allowed": 1,
                    "data_fresh": 1,
                    "source_snapshot_id": "snapshot-1",
                    "reason_code": "RUNTIME_SIGNAL_SELECTED",
                    "reason_detail": "BREAKOUT",
                }
            ]
        )
        execution_events = pd.DataFrame(
            [
                {
                    "decision_id": "decision-1",
                    "order_id": "ord-buy-1",
                    "order_status": "FILLED",
                    "lifecycle_id": "life-1",
                }
            ]
        )
        fills = pd.DataFrame([{"order_id": "ord-buy-1", "fill_id": "fill-buy-1", "symbol": "MSFT"}])
        position_lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "life-1",
                    "entry_order_id": "ord-buy-1",
                    "entry_fill_id": "fill-buy-1",
                    "state": "CLOSED",
                    "acceptance_status": "CLOSED_ACCEPTED_EXACT_IDS",
                }
            ]
        )

        funnel, metrics = build_candidate_funnel_events(decisions, execution_events, fills, position_lifecycle)

        stages = set(funnel["stage"])
        self.assertEqual(stages, {"GENERATED", "RANKED", "ELIGIBLE", "ORDERED", "FILLED", "CLOSED"})
        self.assertEqual(int(funnel["proximity_fallback_used_flag"].max()), 0)
        self.assertEqual(int(metrics.iloc[0]["ordered_candidates"]), 1)
        self.assertEqual(int(metrics.iloc[0]["filled_candidates"]), 1)
        self.assertEqual(int(metrics.iloc[0]["closed_candidates"]), 1)

    def test_replay_acceptance_fails_position_surface_without_closed_lifecycle(self) -> None:
        decisions = pd.DataFrame([{"decision_id": "decision-1"}])
        orders = pd.DataFrame([{"order_id": "ord-buy-1", "intent_key": "decision-1"}])
        fills = pd.DataFrame([{"fill_id": "fill-buy-1", "order_id": "ord-buy-1"}])
        position_lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "life-1",
                    "state": "OPEN",
                    "acceptance_status": "OPEN_ACCEPTED_EXACT_ENTRY",
                }
            ]
        )

        diff, validation = build_replay_acceptance(decisions, orders, fills, position_lifecycle)

        position = validation.loc[validation["surface"].eq("Position Match")].iloc[0]
        self.assertEqual(position["status"], "FAIL")
        self.assertIn("SELL fills", diff.iloc[0]["diff_reason"])

    def test_runtime_tables_are_written_with_contract_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            lifecycle = pd.DataFrame([{"position_id": "life-1", "symbol": "MSFT"}])
            funnel = pd.DataFrame([{"candidate_id": "decision-1", "stage": "GENERATED"}])
            write_runtime_tables(db_path, lifecycle, funnel)
            con = sqlite3.connect(db_path)
            try:
                tables = {
                    row[0]
                    for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                }
            finally:
                con.close()
        self.assertIn("position_lifecycle", tables)
        self.assertIn("candidate_funnel_events", tables)

    def test_readiness_registry_payload_exposes_canonical_statuses(self) -> None:
        payload = build_readiness_registry_payload()
        self.assertEqual(payload["contract_version"], "readiness-registry-v1")
        self.assertEqual(payload["paper_operation"]["status"], "READY_FOR_CONTROLLED_PAPER_RUN")
        self.assertEqual(payload["strategy_acceptance"]["status"], "NOT_ACCEPTED")
        self.assertEqual(payload["real_capital"]["status"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
