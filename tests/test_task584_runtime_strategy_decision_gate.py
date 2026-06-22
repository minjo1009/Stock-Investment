from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.app.task_089_market_data_signal_refresh import _init_tables
from src.app.task_584_runtime_strategy_decision_gate import run_task584


class Task584RuntimeStrategyDecisionGateTest(unittest.TestCase):
    def test_fresh_selected_entry_creates_paper_order_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            _init_tables(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio, source_price_ts, source_price,
                        source_type, freshness_age_sec, stale_reason
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        "snap-1",
                        "2026-05-20T01:00:00Z",
                        "AAPL",
                        "2026-05-20T01:00:00Z",
                        100.0,
                        99.0,
                        98.0,
                        97.0,
                        99.5,
                        1,
                        1,
                        1,
                        1,
                        0,
                        "ENTER",
                        "BUY",
                        "BREAKOUT",
                        1.0,
                        1,
                        1,
                        "2026-05-20T01:00:00Z",
                        100.0,
                        "KIS_CURRENT_PRICE_APPENDED",
                        1.0,
                        "",
                    ),
                )
                con.commit()
            finally:
                con.close()
            state_panel = Path(tmp) / "state_panel.csv"
            state_panel.write_text(
                "\n".join(
                    [
                        "timestamp,trade_date,symbol,multi_day_market_state_v4,theme_regime_state_v4,intraday_entry_state_v4,capital_flow_regime_v6",
                        "2026-05-19T20:00:00Z,2026-05-19,AAPL,constructive_risk_on,persistent_theme_leader,intraday_breakout_acceptance,capital_flow_expansion",
                    ]
                ),
                encoding="utf-8",
            )
            with (
                patch("src.app.task_584_runtime_strategy_decision_gate.REPORT_DIR", Path(tmp) / "reports"),
                patch("src.app.task_584_runtime_strategy_decision_gate.RUNTIME_STATE_PANEL", state_panel),
            ):
                artifacts = run_task584(db_path=db_path)
            row = artifacts["task_584_decision.csv"].iloc[0].to_dict()
            self.assertEqual(row["decision_status"], "PAPER_ORDER_CANDIDATE")
            self.assertEqual(row["runtime_state_capture_status"], "CAPTURED")
            self.assertEqual(row["regime_state"], "constructive_risk_on|persistent_theme_leader")
            self.assertEqual(row["intraday_state"], "intraday_breakout_acceptance")
            self.assertIn("Task567:AAPL", row["state_source_snapshot_id"])
            self.assertEqual(int(row["ready_candidate_rows"]), 1)
            self.assertEqual(int(row["dummy_fallback_used_flag"]), 0)
            self.assertEqual(int(row["used_label_flag"]), 0)

    def test_stale_snapshot_is_no_order_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            _init_tables(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("snap-1", "2026-05-20T01:00:00Z", "AAPL", "2026-04-22T00:00:00Z", 100, 99, 98, 97, 99, 1, 1, 0, 0, 0, "HOLD", "NONE", "STALE", -1, 1, 1),
                )
                con.commit()
            finally:
                con.close()
            with (
                patch("src.app.task_584_runtime_strategy_decision_gate.REPORT_DIR", Path(tmp) / "reports"),
                patch("src.app.task_584_runtime_strategy_decision_gate.RUNTIME_STATE_PANEL", Path(tmp) / "missing_state.csv"),
            ):
                artifacts = run_task584(db_path=db_path)
            row = artifacts["task_584_decision.csv"].iloc[0].to_dict()
            self.assertEqual(row["decision_status"], "DATA_BLOCKED")
            self.assertEqual(row["reason_code"], "STALE_DATA")
            self.assertEqual(row["regime_state"], "NOT_CAPTURED_IN_RUNTIME_DB")
            self.assertEqual(int(row["data_blocked_rows"]), 1)
            decomposition = artifacts["runtime_no_trade_decomposition_audit.csv"]
            self.assertEqual(decomposition.iloc[0]["blocker_category"], "DATA_BLOCKED_STALE_SOURCE")
            self.assertEqual(decomposition.iloc[0]["owner"], "윤헌")

    def test_no_trade_decomposition_splits_strategy_and_portfolio_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            _init_tables(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                rows = [
                    ("snap-1", "AAPL", 1, 1, 0, "BUY", 0.9),
                    ("snap-2", "MSFT", 1, 0, 1, "BUY", 0.8),
                    ("snap-3", "NVDA", 1, 1, 1, "NONE", 0.7),
                ]
                for snapshot_id, symbol, fresh, entry, selected, side, score in rows:
                    con.execute(
                        """
                        INSERT INTO indicator_snapshots(
                            snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                            breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                            data_fresh, insufficient_history, action, side, reason, score, candidate_rank,
                            selected_for_portfolio, source_price_ts, source_price, source_type
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            snapshot_id,
                            "2026-05-20T01:00:00Z",
                            symbol,
                            "2026-05-20T01:00:00Z",
                            100.0,
                            99.0,
                            98.0,
                            97.0,
                            101.0,
                            1,
                            1,
                            entry,
                            fresh,
                            0,
                            "HOLD",
                            side,
                            "TEST",
                            score,
                            1,
                            selected,
                            "2026-05-20T01:00:00Z",
                            100.0,
                            "KIS_CURRENT_PRICE_APPENDED",
                        ),
                    )
                con.commit()
            finally:
                con.close()
            with (
                patch("src.app.task_584_runtime_strategy_decision_gate.REPORT_DIR", Path(tmp) / "reports"),
                patch("src.app.task_584_runtime_strategy_decision_gate.RUNTIME_STATE_PANEL", Path(tmp) / "missing_state.csv"),
            ):
                artifacts = run_task584(db_path=db_path)
            decision = artifacts["task_584_decision.csv"].iloc[0].to_dict()
            self.assertEqual(int(decision["strategy_filter_blocked_rows"]), 1)
            self.assertEqual(int(decision["portfolio_filter_blocked_rows"]), 1)
            self.assertEqual(int(decision["side_contract_blocked_rows"]), 1)
            categories = set(artifacts["runtime_no_trade_decomposition_audit.csv"]["blocker_category"].astype(str))
            self.assertEqual(
                categories,
                {"STRATEGY_FILTER_BLOCKED", "PORTFOLIO_FILTER_BLOCKED", "SIDE_CONTRACT_BLOCKED"},
            )


if __name__ == "__main__":
    unittest.main()
