from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.app.nasdaq_market_calendar import calendar_status
from src.app.task_589_paper_eod_slack_report import _fill_price_repair_audit, run_task589
from src.app.supervisor_slack_alert import send_supervisor_alert


class Task589NasdaqPaperOpsHardeningTest(unittest.TestCase):
    def test_calendar_blocks_closed_days_and_honors_early_close(self) -> None:
        closed = calendar_status(at=__import__("datetime").datetime.fromisoformat("2026-07-03T14:00:00-04:00"))
        self.assertEqual(closed["trading_window_open_flag"], 0)
        self.assertIn("CLOSED", str(closed["reason"]))
        early_open = calendar_status(at=__import__("datetime").datetime.fromisoformat("2026-11-27T12:45:00-05:00"))
        self.assertEqual(early_open["trading_window_open_flag"], 1)
        early_late = calendar_status(at=__import__("datetime").datetime.fromisoformat("2026-11-27T12:55:00-05:00"))
        self.assertEqual(early_late["trading_window_open_flag"], 0)
        self.assertEqual(early_late["eod_due_flag"], 0)
        eod = calendar_status(at=__import__("datetime").datetime.fromisoformat("2026-11-27T13:31:00-05:00"))
        self.assertEqual(eod["eod_due_flag"], 1)

    def test_calendar_blocks_uncovered_year(self) -> None:
        status = calendar_status(at=__import__("datetime").datetime.fromisoformat("2027-01-05T10:00:00-05:00"))
        self.assertEqual(status["calendar_source_status"], "CALENDAR_YEAR_NOT_COVERED")
        self.assertEqual(status["trading_window_open_flag"], 0)

    def test_eod_report_separates_realized_and_open_proxy_pnl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "paper.db"
            report_dir = Path(tmp) / "reports"
            con = sqlite3.connect(db)
            try:
                con.execute("CREATE TABLE fills(fill_id TEXT, order_id TEXT, run_id TEXT, symbol TEXT, side TEXT, filled_quantity REAL, fill_price REAL, filled_at TEXT, source TEXT)")
                con.execute("CREATE TABLE orders(order_id TEXT, run_id TEXT, symbol TEXT, side TEXT, quantity REAL, intent_key TEXT, submitted_at TEXT, status TEXT, raw_status TEXT, environment TEXT)")
                con.execute("CREATE TABLE paper_order_execution_events(event_id TEXT, created_at TEXT, decision_id TEXT, client_order_id TEXT, order_id TEXT, lifecycle_id TEXT, symbol TEXT, side TEXT, quantity REAL, limit_price REAL, order_status TEXT, reason_code TEXT, raw_response_json TEXT, broker_truth_fill_flag INTEGER, filled_qty REAL, filled_avg_price REAL)")
                con.execute("CREATE TABLE runtime_strategy_decisions(decision_id TEXT, created_at TEXT, decision_status TEXT, symbol TEXT, side TEXT, quantity INTEGER, limit_price REAL, reason_code TEXT, reason_detail TEXT, entry_allowed INTEGER, data_fresh INTEGER, selected_for_portfolio INTEGER, score REAL)")
                con.execute("CREATE TABLE indicator_snapshots(snapshot_id TEXT, created_at TEXT, symbol TEXT, bar_end_ts TEXT, close REAL, source_price REAL, data_fresh INTEGER, selected_for_portfolio INTEGER)")
                con.execute("CREATE TABLE continuation_source_events(source_event_id TEXT, lifecycle_id TEXT, setup_id TEXT, symbol TEXT, session_date TEXT, event_type TEXT, event_source TEXT, event_timestamp TEXT, created_at TEXT)")
                con.execute("INSERT INTO fills VALUES('f1','o1','r1','AMZN','BUY',1,100,'2026-05-20T15:00:00Z','ORDER_STATUS')")
                con.execute("INSERT INTO fills VALUES('f2','o2','r2','AMZN','SELL',1,105,'2026-05-20T16:00:00Z','ORDER_STATUS')")
                con.execute("INSERT INTO fills VALUES('f3','o3','r3','MSFT','BUY',2,50,'2026-05-20T17:00:00Z','ORDER_STATUS')")
                con.execute("INSERT INTO orders VALUES('o1','r1','AMZN','BUY',1,'d1','2026-05-20T15:00:00Z','FILLED','FILLED','paper')")
                con.execute("INSERT INTO orders VALUES('o2','r2','AMZN','SELL',1,'d2','2026-05-20T16:00:00Z','FILLED','FILLED','paper')")
                con.execute("INSERT INTO orders VALUES('o3','r3','MSFT','BUY',2,'d3','2026-05-20T17:00:00Z','FILLED','FILLED','paper')")
                con.execute("INSERT INTO paper_order_execution_events VALUES('e1','2026-05-20T15:00:00Z','d1','d1','o1','l1','AMZN','BUY',1,100,'FILLED','ORDER_FILLED','{}',1,1,100)")
                con.execute("INSERT INTO runtime_strategy_decisions VALUES('d1','2026-05-20T14:59:00Z','PAPER_ORDER_CANDIDATE','AMZN','BUY',1,100,'RUNTIME_SIGNAL_SELECTED','reason',1,1,1,0.9)")
                con.execute("INSERT INTO indicator_snapshots VALUES('s1','2026-05-20T18:00:00Z','AMZN','2026-05-20T18:00:00Z',105,105,1,1)")
                con.execute("INSERT INTO indicator_snapshots VALUES('s2','2026-05-20T18:00:00Z','MSFT','2026-05-20T18:00:00Z',55,55,1,0)")
                con.commit()
            finally:
                con.close()
            with (
                patch("src.app.task_589_paper_eod_slack_report.REPORT_DIR", report_dir),
                patch.dict(os.environ, {"SLACK_WEBHOOK_URL": ""}, clear=False),
            ):
                artifacts = run_task589(db_path=db, env_file=Path(tmp) / "missing.env", session_date="2026-05-20")
            summary = artifacts["paper_eod_summary.csv"].iloc[0].to_dict()
            self.assertAlmostEqual(float(summary["realized_pnl_usd"]), 5.0)
            self.assertAlmostEqual(float(summary["mtm_proxy_pnl_usd"]), 10.0)
            self.assertEqual(summary["slack_send_status"], "SLACK_BLOCKED_MISSING_WEBHOOK")
            self.assertEqual(summary["infographic_status"], "HTML_READY")
            self.assertEqual(summary["trading_team_feedback_status"], "READY")
            self.assertEqual(summary["freshness_gap_status"], "CURRENT_EOD_CLOSEOUT")
            self.assertEqual(int(summary["cumulative_fill_rows"]), 3)
            self.assertEqual(int(summary["filled_trade_history_rows"]), 3)
            self.assertEqual(summary["frontend_account_sync_status"], "AUTHORITATIVE_POSITIONS_REBUILT__OPEN_PNL_PROXY_VIEW")
            self.assertEqual(summary["account_truth_source"], "BROKER_TRUTH_FILLS_REPLAYED_TO_POSITIONS")
            self.assertEqual(summary["session_trade_scope"], "CURRENT_SESSION_ONLY")
            self.assertEqual(summary["cumulative_account_scope"], "CUMULATIVE_BROKER_TRUTH_FILLS_UNTIL_SESSION")
            self.assertEqual(summary["position_sync_status"], "REBUILT_FROM_BROKER_TRUTH_FILLS")
            self.assertEqual(int(summary["authoritative_position_rows"]), 1)
            self.assertEqual(int(summary["position_event_rows"]), 3)
            self.assertEqual(int(summary["evaluated_symbol_count"]), 2)
            self.assertEqual(int(summary["fresh_symbol_count"]), 2)
            self.assertGreaterEqual(int(summary["expected_universe_count"]), 2)
            self.assertIn("universe_coverage_status", summary)
            self.assertIn("paper_eod_filled_trade_history.csv", artifacts)
            self.assertIn("paper_eod_filled_decision_evidence.csv", artifacts)
            filled_history = artifacts["paper_eod_filled_trade_history.csv"]
            self.assertEqual(len(filled_history), 3)
            self.assertEqual(set(filled_history["source_scope"].astype(str)), {"CUMULATIVE_BROKER_TRUTH_FILLS"})
            slack_preview = artifacts["paper_eod_slack_audit.csv"].iloc[0]["message_preview"]
            self.assertIn("deployment blocker: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", slack_preview)
            self.assertIn("[PAPER_EOD_FILLED_REPORT]", slack_preview)
            self.assertIn("filled trades only: session_fills=3", slack_preview)
            self.assertIn("AMZN BUY", slack_preview)
            self.assertIn("realized_pnl_usd:", slack_preview)
            self.assertNotIn("account truth:", slack_preview)
            self.assertNotIn("universe coverage status:", slack_preview)
            self.assertNotIn("orders_pending:", slack_preview)
            self.assertNotIn("paper_order_candidates:", slack_preview)
            feedback = artifacts["paper_eod_trading_team_feedback.csv"]
            self.assertIn("Execution Desk", set(feedback["team"].astype(str)))
            self.assertIn("PM / CIO Review", set(feedback["team"].astype(str)))
            html_path = report_dir / "paper_eod_infographic_2026-05-20.html"
            feedback_md_path = report_dir / "paper_eod_trading_team_feedback_2026-05-20.md"
            self.assertTrue(html_path.exists())
            self.assertTrue(feedback_md_path.exists())
            html_text = html_path.read_text(encoding="utf-8")
            self.assertIn("모의거래 장마감 인포그래픽", html_text)
            self.assertIn("Execution Funnel", html_text)
            self.assertIn("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", html_text)
            con = sqlite3.connect(db)
            try:
                position_rows = con.execute("SELECT symbol, quantity, avg_price FROM positions ORDER BY symbol").fetchall()
                event_count = con.execute("SELECT COUNT(*) FROM position_events").fetchone()[0]
            finally:
                con.close()
            self.assertEqual(position_rows, [("MSFT", 2.0, 50.0)])
            self.assertEqual(event_count, 3)

    def test_supervisor_alert_blocks_missing_webhook_without_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch("src.app.supervisor_slack_alert.REPORT_DIR", Path(tmp) / "reports"),
                patch.dict(os.environ, {"SLACK_WEBHOOK_URL": ""}, clear=False),
            ):
                audit = send_supervisor_alert(component="TASK588", status="FAILED", detail="exit_code=1", env_file=Path(tmp) / "missing.env")
        row = audit.iloc[0].to_dict()
        self.assertEqual(row["slack_send_status"], "SLACK_BLOCKED_MISSING_WEBHOOK")
        self.assertEqual(int(row["secret_in_message_flag"]), 0)

    def test_eod_slack_dry_run_does_not_record_sent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "paper.db"
            report_dir = Path(tmp) / "reports"
            con = sqlite3.connect(db)
            try:
                con.execute("CREATE TABLE fills(fill_id TEXT, order_id TEXT, run_id TEXT, symbol TEXT, side TEXT, filled_quantity REAL, fill_price REAL, filled_at TEXT, source TEXT)")
                con.execute("CREATE TABLE orders(order_id TEXT, run_id TEXT, symbol TEXT, side TEXT, quantity REAL, intent_key TEXT, submitted_at TEXT, status TEXT, raw_status TEXT, environment TEXT)")
                con.execute("CREATE TABLE paper_order_execution_events(event_id TEXT, created_at TEXT, decision_id TEXT, client_order_id TEXT, order_id TEXT, lifecycle_id TEXT, symbol TEXT, side TEXT, quantity REAL, limit_price REAL, order_status TEXT, reason_code TEXT, raw_response_json TEXT, broker_truth_fill_flag INTEGER, filled_qty REAL, filled_avg_price REAL)")
                con.execute("CREATE TABLE runtime_strategy_decisions(decision_id TEXT, created_at TEXT, decision_status TEXT, symbol TEXT, side TEXT, quantity INTEGER, limit_price REAL, reason_code TEXT, reason_detail TEXT, entry_allowed INTEGER, data_fresh INTEGER, selected_for_portfolio INTEGER, score REAL)")
                con.execute("CREATE TABLE indicator_snapshots(snapshot_id TEXT, created_at TEXT, symbol TEXT, bar_end_ts TEXT, close REAL, source_price REAL, data_fresh INTEGER, selected_for_portfolio INTEGER)")
                con.execute("CREATE TABLE continuation_source_events(source_event_id TEXT, lifecycle_id TEXT, setup_id TEXT, symbol TEXT, session_date TEXT, event_type TEXT, event_source TEXT, event_timestamp TEXT, created_at TEXT)")
                con.execute("INSERT INTO runtime_strategy_decisions VALUES('d1','2026-05-20T14:59:00Z','NO_TRADE','AMZN','NONE',0,100,'NO_ENTRY','reason',0,1,1,0.9)")
                con.execute("INSERT INTO indicator_snapshots VALUES('s1','2026-05-20T18:00:00Z','AMZN','2026-05-20T18:00:00Z',105,105,1,1)")
                con.commit()
            finally:
                con.close()
            with (
                patch("src.app.task_589_paper_eod_slack_report.REPORT_DIR", report_dir),
                patch("src.app.task_589_paper_eod_slack_report.slack_client.send_message") as send_message,
                patch.dict(os.environ, {"SLACK_WEBHOOK_URL": "https://local.mock", "PAPER_EOD_SLACK_DRY_RUN": "1"}, clear=False),
            ):
                artifacts = run_task589(db_path=db, env_file=Path(tmp) / "missing.env", session_date="2026-05-20")
            summary = artifacts["paper_eod_summary.csv"].iloc[0].to_dict()
            slack_audit = artifacts["paper_eod_slack_audit.csv"].iloc[0].to_dict()
            self.assertEqual(summary["slack_send_status"], "SKIPPED_NO_FILLED_TRADES")
            self.assertEqual(slack_audit["slack_send_status"], "SKIPPED_NO_FILLED_TRADES")
            self.assertEqual(slack_audit["message_type"], "SKIPPED_NO_FILLED_TRADES")
            self.assertEqual(int(slack_audit["dry_run_flag"]), 1)
            send_message.assert_not_called()

    def test_fill_price_repair_audit_uses_exact_order_event_only(self) -> None:
        fills = pd.DataFrame(
            [
                {
                    "fill_id": "f1",
                    "order_id": "o1",
                    "symbol": "AMD",
                    "side": "BUY",
                    "filled_quantity": 1,
                    "fill_price": None,
                    "filled_at": "2026-05-20T15:00:00Z",
                    "source": "POSITION_DELTA_FALLBACK",
                },
                {
                    "fill_id": "f2",
                    "order_id": "o2",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "filled_quantity": 1,
                    "fill_price": None,
                    "filled_at": "2026-05-20T16:00:00Z",
                    "source": "POSITION_DELTA_FALLBACK",
                },
            ]
        )
        events = pd.DataFrame(
            [
                {
                    "order_id": "o1",
                    "decision_id": "d1",
                    "filled_avg_price": 101.25,
                },
                {
                    "order_id": "o2",
                    "decision_id": "d2",
                    "filled_avg_price": None,
                },
            ]
        )
        orders = pd.DataFrame(
            [
                {"order_id": "o1", "intent_key": "d1", "status": "FILLED", "raw_status": "FILLED"},
                {"order_id": "o2", "intent_key": "d2", "status": "FILLED", "raw_status": "UNKNOWN"},
            ]
        )
        decisions = pd.DataFrame(
            [
                {"decision_id": "d1", "limit_price": 100.0},
                {"decision_id": "d2", "limit_price": 200.0},
            ]
        )
        audit = _fill_price_repair_audit(fills, orders, events, decisions, session_date="2026-05-20")
        by_order = {row["order_id"]: row for row in audit.to_dict(orient="records")}
        self.assertEqual(by_order["o1"]["repair_status"], "REPAIRABLE_FROM_EXACT_ORDER_EVENT")
        self.assertEqual(float(by_order["o1"]["repair_price"]), 101.25)
        self.assertEqual(by_order["o2"]["repair_status"], "UNREPAIRABLE_WITH_EXACT_BROKER_EVIDENCE")
        self.assertEqual(by_order["o2"]["quarantine_status"], "ACTIVE_SESSION_BLOCKER")
        self.assertEqual(int(by_order["o2"]["active_session_blocker_flag"]), 1)
        self.assertIn("no_limit_price_substitution", by_order["o2"]["forbidden_repair_methods"])

        historical = _fill_price_repair_audit(fills, orders, events, decisions, session_date="2026-05-21")
        historical_by_order = {row["order_id"]: row for row in historical.to_dict(orient="records")}
        self.assertEqual(historical_by_order["o2"]["quarantine_status"], "QUARANTINED_NON_PROMOTABLE_HISTORY")
        self.assertEqual(int(historical_by_order["o2"]["active_session_blocker_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
