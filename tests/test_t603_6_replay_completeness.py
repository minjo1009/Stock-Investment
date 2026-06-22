from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.replay.replay_completeness_engine import (
    build_replay_completeness_acceptance,
    run_replay_completeness_from_db,
)


class T6036ReplayCompletenessTest(unittest.TestCase):
    def _pass_fixture(self) -> dict[str, pd.DataFrame]:
        decisions = pd.DataFrame(
            [
                {"decision_id": "decision-entry", "symbol": "AMD"},
                {"decision_id": "decision-exit", "symbol": "AMD"},
            ]
        )
        orders = pd.DataFrame(
            [
                {
                    "order_id": "order-entry",
                    "run_id": "run-1",
                    "symbol": "AMD",
                    "side": "BUY",
                    "quantity": 10.0,
                    "intent_key": "decision-entry",
                    "submitted_at": "2026-06-03T01:00:00Z",
                    "status": "FILLED",
                    "raw_status": "UNKNOWN",
                    "environment": "paper",
                },
                {
                    "order_id": "order-exit",
                    "run_id": "run-1",
                    "symbol": "AMD",
                    "side": "SELL",
                    "quantity": 10.0,
                    "intent_key": "decision-exit",
                    "submitted_at": "2026-06-03T02:00:00Z",
                    "status": "FILLED",
                    "raw_status": "UNKNOWN",
                    "environment": "paper",
                },
            ]
        )
        fills = pd.DataFrame(
            [
                {
                    "fill_id": "fill-entry",
                    "order_id": "order-entry",
                    "run_id": "run-1",
                    "symbol": "AMD",
                    "side": "BUY",
                    "filled_quantity": 10.0,
                    "fill_price": 100.0,
                    "filled_at": "2026-06-03T01:01:00Z",
                },
                {
                    "fill_id": "fill-exit",
                    "order_id": "order-exit",
                    "run_id": "run-1",
                    "symbol": "AMD",
                    "side": "SELL",
                    "filled_quantity": 10.0,
                    "fill_price": 110.0,
                    "filled_at": "2026-06-03T02:01:00Z",
                },
            ]
        )
        position_lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "position-1",
                    "symbol": "AMD",
                    "entry_order_id": "order-entry",
                    "entry_fill_id": "fill-entry",
                    "exit_order_id": "order-exit",
                    "exit_fill_id": "fill-exit",
                    "entry_time": "2026-06-03T01:01:00Z",
                    "exit_time": "2026-06-03T02:01:00Z",
                    "holding_minutes": 60.0,
                    "realized_pnl": 100.0,
                    "exit_reason": "TAKE_PROFIT",
                    "state": "CLOSED",
                    "entry_price": 100.0,
                    "exit_price": 110.0,
                    "entry_qty": 10.0,
                    "open_qty": 0.0,
                    "closed_qty": 10.0,
                    "matching_policy": "EXACT_LIFECYCLE_ID_AND_ORDER_FILL_ID_ONLY",
                    "acceptance_status": "CLOSED_ACCEPTED_EXACT_IDS",
                    "proxy_pnl_used_flag": 0,
                    "proximity_fallback_used_flag": 0,
                }
            ]
        )
        broker_trade_lineage = pd.DataFrame(
            [
                {
                    "decision_id": "decision-exit",
                    "order_id": "order-exit",
                    "fill_id": "fill-exit",
                    "position_id": "position-1",
                    "lineage_complete_flag": 1,
                }
            ]
        )
        return {
            "decisions": decisions,
            "orders": orders,
            "fills": fills,
            "position_lifecycle": position_lifecycle,
            "broker_trade_lineage": broker_trade_lineage,
        }

    def test_full_exact_fixture_scores_100_percent_pass(self) -> None:
        fixture = self._pass_fixture()

        result = build_replay_completeness_acceptance(**fixture)
        decision = result.decision.iloc[0]

        self.assertEqual(decision["decision_status"], "PASS")
        self.assertEqual(float(decision["replay_completeness_score"]), 1.0)
        self.assertEqual(float(decision["position_match_rate"]), 1.0)
        self.assertEqual(float(decision["lineage_match_rate"]), 1.0)
        self.assertEqual(int(decision["inferred_matching_used_flag"]), 0)
        self.assertEqual(int(decision["real_capital_used_flag"]), 0)
        self.assertEqual(set(result.validation["weight"].round(1).tolist()), {0.2})
        self.assertEqual(result.gap_breakdown.iloc[0]["gap_type"], "NO_MATERIAL_GAP")

    def test_missing_lineage_source_scores_zero_and_fails_acceptance(self) -> None:
        fixture = self._pass_fixture()
        fixture.pop("broker_trade_lineage")

        result = build_replay_completeness_acceptance(**fixture)
        decision = result.decision.iloc[0]
        lineage = result.validation.loc[result.validation["surface"].eq("Lineage Match")].iloc[0]

        self.assertEqual(decision["decision_status"], "FAIL")
        self.assertEqual(float(decision["replay_completeness_score"]), 0.8)
        self.assertEqual(float(decision["position_match_rate"]), 1.0)
        self.assertEqual(float(decision["lineage_match_rate"]), 0.0)
        self.assertEqual(lineage["status"], "SOURCE_BLOCK")
        self.assertEqual(lineage["source_status"], "SOURCE_BLOCK")
        self.assertEqual(int(lineage["source_blocked_flag"]), 1)

    def test_db_validator_writes_required_reports_with_five_sections(self) -> None:
        fixture = self._pass_fixture()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "fixture.db"
            report_dir = root / "reports"
            con = sqlite3.connect(db_path)
            try:
                fixture["decisions"].to_sql("runtime_strategy_decisions", con, index=False)
                fixture["orders"].to_sql("orders", con, index=False)
                fixture["fills"].to_sql("fills", con, index=False)
                fixture["position_lifecycle"].to_sql("position_lifecycle", con, index=False)
                con.commit()
            finally:
                con.close()

            summary = run_replay_completeness_from_db(db_path, report_dir, program_a_summary_paths=())

            self.assertEqual(summary["decision_status"], "FAIL")
            self.assertEqual(float(summary["replay_completeness_score"]), 0.8)
            for filename in ["replay_completeness_report.md", "replay_gap_breakdown.md"]:
                headings = [
                    line.strip()
                    for line in (report_dir / filename).read_text(encoding="utf-8").splitlines()
                    if line.startswith("# ")
                ]
                self.assertEqual(
                    headings,
                    ["# Problem", "# Evidence", "# Root Cause", "# Fix Candidate", "# Acceptance Impact"],
                )
            self.assertTrue((report_dir / "replay_completeness_validation.csv").exists())
            self.assertTrue((report_dir / "replay_gap_breakdown.csv").exists())
            self.assertTrue((report_dir / "task_603_6_decision.csv").exists())
            self.assertTrue((report_dir / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
