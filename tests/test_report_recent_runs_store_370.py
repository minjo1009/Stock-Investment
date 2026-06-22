from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from app import report_recent_runs
from state.store import (
    FILL_DUPLICATE_IGNORED,
    FILL_INSERTED,
    build_order_intent_key,
    get_fills_for_order,
    initialize_store,
    record_fill,
    record_order,
    record_reconciliation_event,
    record_reconciliation_run,
    record_trade_run_finish,
    record_trade_run_start,
    upsert_position,
)


class TestReportRecentRunsStore370(unittest.TestCase):
    def _seed_run(self, db_path: str) -> tuple[str, str, str]:
        run_id = record_trade_run_start(
            db_path,
            symbol="NVDA",
            side="BUY",
            requested_quantity=1.0,
            started_at="2026-01-03T14:30:00Z",
            environment="paper",
        )
        intent_key = build_order_intent_key(
            symbol="NVDA",
            side="BUY",
            intended_price=100.0,
            quantity=1.0,
            strategy_id="continuation_sleeve",
        )
        order_id = "order-370-001"
        record_order(
            db_path,
            order_id=order_id,
            run_id=run_id,
            symbol="NVDA",
            side="BUY",
            quantity=1.0,
            intent_key=intent_key,
            submitted_at="2026-01-03T14:30:01Z",
            status="FILLED",
            environment="paper",
            raw_status="filled",
        )
        return run_id, order_id, intent_key

    def test_record_fill_duplicate_is_append_only_friendly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "trading.db")
            initialize_store(db_path)
            run_id, order_id, _intent_key = self._seed_run(db_path)

            first = record_fill(
                db_path,
                fill_id="fill-370-001",
                order_id=order_id,
                run_id=run_id,
                symbol="NVDA",
                side="BUY",
                filled_quantity=1.0,
                fill_price=100.5,
                filled_at="2026-01-03T14:30:02Z",
                source="ORDER_STATUS",
            )
            second = record_fill(
                db_path,
                fill_id="fill-370-002",
                order_id=order_id,
                run_id=run_id,
                symbol="NVDA",
                side="BUY",
                filled_quantity=1.0,
                fill_price=100.5,
                filled_at="2026-01-03T14:30:03Z",
                source="ORDER_STATUS",
            )

            fills = get_fills_for_order(db_path, order_id)
            self.assertEqual(first, FILL_INSERTED)
            self.assertEqual(second, FILL_DUPLICATE_IGNORED)
            self.assertEqual(len(fills), 1)
            self.assertEqual(str(fills[0]["fill_id"]), "fill-370-001")

    def test_report_recent_runs_outputs_run_position_and_reconciliation_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "trading.db")
            initialize_store(db_path)
            run_id, order_id, intent_key = self._seed_run(db_path)
            fill_result = record_fill(
                db_path,
                fill_id="fill-370-003",
                order_id=order_id,
                run_id=run_id,
                symbol="NVDA",
                side="BUY",
                filled_quantity=1.0,
                fill_price=101.25,
                filled_at="2026-01-03T14:30:02Z",
                source="ORDER_STATUS",
            )
            self.assertEqual(fill_result, FILL_INSERTED)
            upsert_position(
                db_path,
                symbol="NVDA",
                side="LONG",
                quantity=1.0,
                avg_price=101.25,
                updated_at="2026-01-03T14:30:02Z",
            )
            record_trade_run_finish(
                db_path,
                run_id=run_id,
                result_status="FILLED",
                finished_at="2026-01-03T14:30:05Z",
            )
            recon_id = record_reconciliation_run(
                db_path,
                run_id=run_id,
                started_at="2026-01-03T14:31:00Z",
                finished_at="2026-01-03T14:31:01Z",
                status="MISMATCH",
                max_severity="WARN",
                block_new_orders=False,
                summary_text="late fill audit",
                raw_snapshot_json="{}",
            )
            record_reconciliation_event(
                db_path,
                reconciliation_id=recon_id,
                symbol="NVDA",
                local_order_id=order_id,
                broker_order_id=order_id,
                event_type="LATE_FILL",
                severity="WARN",
                local_status="FILLED",
                broker_status="FILLED",
                details={"delta": 0.0},
                created_at="2026-01-03T14:31:01Z",
            )

            previous = report_recent_runs.os.environ.get("TRADING_DB_PATH")
            try:
                report_recent_runs.os.environ["TRADING_DB_PATH"] = db_path

                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    exit_code = report_recent_runs.main(["--limit", "5", "--show-intent-key"])
                text = stdout.getvalue()
                self.assertEqual(exit_code, 0)
                self.assertIn("[Recent Runs]", text)
                self.assertIn("run_status=FILLED", text)
                self.assertIn("fill_source=ORDER_STATUS", text)
                self.assertIn(f"intent_key={intent_key}", text)

                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    exit_code = report_recent_runs.main(["--positions"])
                text = stdout.getvalue()
                self.assertEqual(exit_code, 0)
                self.assertIn("[Positions]", text)
                self.assertIn("NVDA | 1.0 | 101.25", text)

                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    exit_code = report_recent_runs.main(["--show-reconciliation"])
                text = stdout.getvalue()
                self.assertEqual(exit_code, 0)
                self.assertIn("[Reconciliation Runs]", text)
                self.assertIn("status=MISMATCH", text)
                self.assertIn("event_count=1", text)
            finally:
                if previous is None:
                    report_recent_runs.os.environ.pop("TRADING_DB_PATH", None)
                else:
                    report_recent_runs.os.environ["TRADING_DB_PATH"] = previous


if __name__ == "__main__":
    unittest.main()
