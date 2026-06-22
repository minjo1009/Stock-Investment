from __future__ import annotations

import argparse
import html
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from .paper_runtime_common import append_registry_rows, load_runtime_env, read_table, utc_now, write_csv, write_task_report
from .task_089_market_data_signal_refresh import load_theme_universe_symbols
try:
    from src.integration import slack_client
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from integration import slack_client


REPORT_DIR = Path("docs/reports/task_589_nasdaq_paper_ops_hardening")
EASTERN = ZoneInfo("America/New_York")


def _to_et_date(value: object) -> str:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return ""
    return ts.to_pydatetime().astimezone(EASTERN).date().isoformat()


def _filter_et_date(frame: pd.DataFrame, column: str, session_date: str) -> pd.DataFrame:
    if frame.empty or column not in frame.columns:
        return frame.iloc[0:0].copy()
    work = frame.copy()
    work["_session_date_et"] = work[column].map(_to_et_date)
    return work.loc[work["_session_date_et"].eq(session_date)].copy()


def _filter_until_et_date(frame: pd.DataFrame, column: str, session_date: str) -> pd.DataFrame:
    if frame.empty or column not in frame.columns:
        return frame.iloc[0:0].copy()
    work = frame.copy()
    work["_session_date_et"] = work[column].map(_to_et_date)
    return work.loc[work["_session_date_et"].le(session_date)].copy()


def _latest_marks(db_path: Path) -> dict[str, float]:
    snapshots = read_table(db_path, "indicator_snapshots", order_by="created_at", limit=1000)
    if snapshots.empty:
        return {}
    marks: dict[str, float] = {}
    snapshots = snapshots.sort_values("created_at")
    for _, row in snapshots.iterrows():
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        value = row.get("source_price")
        if value in (None, "") or pd.isna(value):
            value = row.get("close")
        try:
            marks[symbol] = float(value)
        except Exception:
            continue
    return marks


def _pnl_from_fills(fills: pd.DataFrame, marks: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    if fills.empty:
        return pd.DataFrame(), pd.DataFrame(), {"realized_pnl_usd": 0.0, "mtm_proxy_pnl_usd": 0.0}
    frame = fills.copy().sort_values("filled_at")
    lots: dict[str, list[dict[str, float]]] = {}
    realized_rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        symbol = str(row.get("symbol") or "").upper()
        side = str(row.get("side") or "").upper()
        qty = float(row.get("filled_quantity") or 0.0)
        price_raw = row.get("fill_price")
        if not symbol or qty <= 0 or price_raw in (None, "") or pd.isna(price_raw):
            continue
        price = float(price_raw)
        if side == "BUY":
            lots.setdefault(symbol, []).append(
                {
                    "qty": qty,
                    "price": price,
                    "entry_time": row.get("filled_at"),
                    "entry_order_id": row.get("order_id"),
                    "entry_fill_id": row.get("fill_id"),
                }
            )
        elif side == "SELL":
            remaining = qty
            while remaining > 0 and lots.get(symbol):
                lot = lots[symbol][0]
                close_qty = min(remaining, lot["qty"])
                pnl = (price - lot["price"]) * close_qty
                realized_rows.append(
                    {
                        "symbol": symbol,
                        "closed_qty": close_qty,
                        "entry_time": lot.get("entry_time"),
                        "exit_time": row.get("filled_at"),
                        "entry_order_id": lot.get("entry_order_id"),
                        "exit_order_id": row.get("order_id"),
                        "entry_price": lot["price"],
                        "exit_price": price,
                        "realized_pnl_usd": pnl,
                    }
                )
                lot["qty"] -= close_qty
                remaining -= close_qty
                if lot["qty"] <= 0:
                    lots[symbol].pop(0)
    open_rows: list[dict[str, Any]] = []
    for symbol, symbol_lots in lots.items():
        mark = marks.get(symbol)
        for lot in symbol_lots:
            mtm = None if mark is None else (mark - lot["price"]) * lot["qty"]
            open_rows.append(
                {
                    "symbol": symbol,
                    "open_qty": lot["qty"],
                    "entry_time": lot.get("entry_time"),
                    "entry_order_id": lot.get("entry_order_id"),
                    "entry_fill_id": lot.get("entry_fill_id"),
                    "avg_entry_price": lot["price"],
                    "mark_price": mark,
                    "mtm_proxy_pnl_usd": mtm,
                    "pnl_status": "PROXY_FROM_LATEST_RUNTIME_MARK" if mark is not None else "OPEN_POSITION_MARK_MISSING",
                }
            )
    realized = pd.DataFrame(realized_rows)
    open_positions = pd.DataFrame(open_rows)
    realized_pnl = float(realized["realized_pnl_usd"].sum()) if not realized.empty else 0.0
    mtm_proxy = float(pd.to_numeric(open_positions.get("mtm_proxy_pnl_usd", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    return realized, open_positions, {"realized_pnl_usd": realized_pnl, "mtm_proxy_pnl_usd": mtm_proxy}


def _filled_trade_history(
    fills: pd.DataFrame,
    orders: pd.DataFrame,
    events: pd.DataFrame,
    decisions: pd.DataFrame,
) -> pd.DataFrame:
    if fills.empty:
        return pd.DataFrame()
    order_by_id = {
        str(row.get("order_id") or ""): row
        for _, row in orders.iterrows()
    } if not orders.empty and "order_id" in orders.columns else {}
    events_by_order: dict[str, pd.Series] = {}
    if not events.empty and "order_id" in events.columns:
        sortable = events.copy()
        if "created_at" in sortable.columns:
            sortable = sortable.sort_values("created_at")
        for _, row in sortable.iterrows():
            order_id = str(row.get("order_id") or "")
            if order_id:
                events_by_order[order_id] = row
    decisions_by_id = {
        str(row.get("decision_id") or ""): row
        for _, row in decisions.iterrows()
    } if not decisions.empty and "decision_id" in decisions.columns else {}
    rows: list[dict[str, Any]] = []
    for _, fill in fills.sort_values("filled_at", ascending=False).iterrows():
        order_id = str(fill.get("order_id") or "")
        order = order_by_id.get(order_id, pd.Series(dtype=object))
        event = events_by_order.get(order_id, pd.Series(dtype=object))
        decision_id = str(event.get("decision_id") or order.get("intent_key") or "")
        decision = decisions_by_id.get(decision_id, pd.Series(dtype=object))
        rows.append(
            {
                "created_at": fill.get("filled_at"),
                "filled_at": fill.get("filled_at"),
                "decision_id": decision_id,
                "order_id": order_id,
                "lifecycle_id": event.get("lifecycle_id") or "",
                "symbol": str(fill.get("symbol") or order.get("symbol") or "").upper(),
                "side": fill.get("side") or order.get("side") or "",
                "quantity": fill.get("filled_quantity"),
                "limit_price": event.get("limit_price") if "limit_price" in event else decision.get("limit_price"),
                "order_status": "FILLED",
                "reason_code": event.get("reason_code") or decision.get("reason_code") or "ORDER_FILLED",
                "reason_detail": decision.get("reason_detail") or "",
                "broker_truth_fill_flag": 1,
                "filled_qty": fill.get("filled_quantity"),
                "filled_avg_price": fill.get("fill_price"),
                "source_scope": "CUMULATIVE_BROKER_TRUTH_FILLS",
            }
        )
    return pd.DataFrame(rows)


def _secret_free(text: str) -> bool:
    needles = [
        os.environ.get("KIS_APP_KEY", ""),
        os.environ.get("KIS_APP_SECRET", ""),
        os.environ.get("KIS_ACCOUNT_NUMBER", ""),
        os.environ.get("SLACK_WEBHOOK_URL", ""),
    ]
    return not any(value and value in text for value in needles)


def _fmt_money(value: object) -> str:
    try:
        number = float(value)
    except Exception:
        return "$0.00"
    sign = "-" if number < 0 else ""
    return f"{sign}${abs(number):,.2f}"


def _pct(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(part / total * 100.0, 1)


def _safe_int(value: object) -> int:
    try:
        if value in (None, "") or pd.isna(value):
            return 0
        return int(float(value))
    except Exception:
        return 0


def _task583_universe_coverage() -> dict[str, Any]:
    path = Path("docs/reports/task_583_live_signal_refresh_repair/indicator_snapshot_freshness_audit.csv")
    if not path.exists():
        return {
            "universe_scope": "theme_10x7",
            "expected_universe_count": 0,
            "evaluated_symbol_count": 0,
            "fresh_symbol_count": 0,
            "selected_symbol_count": 0,
            "missing_or_stale_symbol_count": 0,
            "universe_coverage_status": "UNKNOWN_BLOCKER",
        }
    try:
        frame = pd.read_csv(path)
    except Exception:
        frame = pd.DataFrame()
    if frame.empty:
        return {
            "universe_scope": "theme_10x7",
            "expected_universe_count": 0,
            "evaluated_symbol_count": 0,
            "fresh_symbol_count": 0,
            "selected_symbol_count": 0,
            "missing_or_stale_symbol_count": 0,
            "universe_coverage_status": "UNKNOWN_BLOCKER",
        }
    row = frame.iloc[-1].to_dict()
    return {
        "universe_scope": row.get("universe_scope", "theme_10x7"),
        "expected_universe_count": _safe_int(row.get("expected_universe_count")),
        "evaluated_symbol_count": _safe_int(row.get("evaluated_symbol_count") or row.get("rows")),
        "fresh_symbol_count": _safe_int(row.get("fresh_symbol_count") or row.get("fresh_rows")),
        "selected_symbol_count": _safe_int(row.get("selected_symbol_count") or row.get("selected_fresh_rows")),
        "missing_or_stale_symbol_count": _safe_int(row.get("missing_or_stale_symbol_count")),
        "universe_coverage_status": str(row.get("coverage_status") or "UNKNOWN_BLOCKER"),
    }


def _latest_universe_coverage_from_db(db_path: Path, session_date: str) -> dict[str, Any]:
    expected = _safe_int(_task583_universe_coverage().get("expected_universe_count"))
    snapshots = read_table(db_path, "indicator_snapshots", order_by="created_at", limit=20000)
    if snapshots.empty:
        coverage = _task583_universe_coverage()
        coverage["canonical_universe_source"] = "TASK583_FALLBACK_NO_CURRENT_DB_ROWS"
        return coverage
    snapshots = snapshots.copy()
    snapshots["symbol_norm"] = snapshots["symbol"].astype(str).str.strip().str.upper() if "symbol" in snapshots.columns else ""
    expected_symbols = {symbol.upper() for symbol in load_theme_universe_symbols()}
    if expected_symbols:
        snapshots = snapshots.loc[snapshots["symbol_norm"].isin(expected_symbols)].copy()
        expected = len(expected_symbols)
    if snapshots.empty:
        coverage = _task583_universe_coverage()
        coverage["canonical_universe_source"] = "TASK583_FALLBACK_NO_THEME_UNIVERSE_DB_ROWS"
        return coverage
    latest_rows = snapshots.sort_values("created_at").groupby("symbol_norm", as_index=False).tail(1)
    evaluated = int(latest_rows["symbol_norm"].astype(str).str.upper().nunique()) if "symbol_norm" in latest_rows.columns else 0
    fresh = int(pd.to_numeric(latest_rows.get("data_fresh", pd.Series(dtype=float)), errors="coerce").fillna(0).eq(1).sum())
    selected = int(pd.to_numeric(latest_rows.get("selected_for_portfolio", pd.Series(dtype=float)), errors="coerce").fillna(0).eq(1).sum())
    if expected <= 0:
        expected = evaluated
    missing_or_stale = max(expected - fresh, 0)
    coverage_status = "FULL_UNIVERSE_EVALUATED_WITH_SOURCE_GAPS"
    if evaluated < expected:
        coverage_status = "UNIVERSE_COVERAGE_GAP"
    elif missing_or_stale == 0:
        coverage_status = "FULL_UNIVERSE_FRESH"
    return {
        "universe_scope": "theme_10x7",
        "expected_universe_count": expected,
        "evaluated_symbol_count": evaluated,
        "fresh_symbol_count": fresh,
        "selected_symbol_count": selected,
        "missing_or_stale_symbol_count": missing_or_stale,
        "universe_coverage_status": coverage_status,
        "canonical_universe_source": "TRADING_DB_LATEST_INDICATOR_PER_SYMBOL_CURRENT_READINESS",
    }


def _ensure_position_tables(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS positions (
            symbol TEXT PRIMARY KEY,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS position_events (
            event_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            fill_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            fill_qty REAL NOT NULL,
            fill_price REAL,
            position_qty_after REAL NOT NULL,
            avg_price_after REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_position_events_fill_id ON position_events(fill_id)")


def _sync_positions_from_fills(db_path: Path, fills: pd.DataFrame) -> dict[str, Any]:
    frame = fills.copy().sort_values("filled_at") if not fills.empty else pd.DataFrame()
    state: dict[str, dict[str, float]] = {}
    events: list[dict[str, Any]] = []
    skipped = 0
    for _, row in frame.iterrows():
        symbol = str(row.get("symbol") or "").upper()
        side = str(row.get("side") or "").upper()
        qty = float(row.get("filled_quantity") or 0.0)
        price_raw = row.get("fill_price")
        if not symbol or qty <= 0 or price_raw in (None, "") or pd.isna(price_raw):
            skipped += 1
            continue
        price = float(price_raw)
        current = state.setdefault(symbol, {"quantity": 0.0, "avg_price": 0.0})
        old_qty = current["quantity"]
        old_avg = current["avg_price"]
        if side == "BUY":
            new_qty = old_qty + qty
            new_avg = ((old_qty * old_avg) + (qty * price)) / new_qty if new_qty else 0.0
        elif side == "SELL":
            new_qty = max(old_qty - qty, 0.0)
            new_avg = old_avg if new_qty else 0.0
        else:
            skipped += 1
            continue
        current["quantity"] = new_qty
        current["avg_price"] = new_avg
        fill_id = str(row.get("fill_id") or f"{row.get('order_id')}:{row.get('filled_at')}")
        events.append(
            {
                "event_id": f"replay-{fill_id}",
                "run_id": str(row.get("run_id") or ""),
                "order_id": str(row.get("order_id") or ""),
                "fill_id": fill_id,
                "symbol": symbol,
                "side": side,
                "fill_qty": qty,
                "fill_price": price,
                "position_qty_after": new_qty,
                "avg_price_after": new_avg,
                "created_at": str(row.get("filled_at") or utc_now()),
            }
        )
    positions = [
        {"symbol": symbol, "side": "LONG", "quantity": values["quantity"], "avg_price": values["avg_price"], "updated_at": utc_now()}
        for symbol, values in sorted(state.items())
        if values["quantity"] > 0
    ]
    con = sqlite3.connect(db_path)
    try:
        _ensure_position_tables(con)
        con.execute("DELETE FROM positions")
        con.execute("DELETE FROM position_events")
        con.executemany(
            "INSERT INTO positions(symbol, side, quantity, avg_price, updated_at) VALUES(?,?,?,?,?)",
            [(row["symbol"], row["side"], row["quantity"], row["avg_price"], row["updated_at"]) for row in positions],
        )
        con.executemany(
            """
            INSERT INTO position_events(
                event_id, run_id, order_id, fill_id, symbol, side, fill_qty, fill_price,
                position_qty_after, avg_price_after, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            [
                (
                    row["event_id"],
                    row["run_id"],
                    row["order_id"],
                    row["fill_id"],
                    row["symbol"],
                    row["side"],
                    row["fill_qty"],
                    row["fill_price"],
                    row["position_qty_after"],
                    row["avg_price_after"],
                    row["created_at"],
                )
                for row in events
            ],
        )
        con.commit()
    finally:
        con.close()
    return {
        "position_sync_status": "REBUILT_FROM_BROKER_TRUTH_FILLS" if not frame.empty else "NO_FILLS_POSITION_TABLES_CLEARED",
        "authoritative_position_rows": len(positions),
        "position_event_rows": len(events),
        "position_fill_rows_skipped": skipped,
    }


def _fill_price_repair_audit(
    fills: pd.DataFrame,
    orders: pd.DataFrame,
    events: pd.DataFrame,
    decisions: pd.DataFrame,
    *,
    session_date: str = "",
) -> pd.DataFrame:
    if fills.empty:
        return pd.DataFrame(
            columns=[
                "fill_id",
                "order_id",
                "symbol",
                "source",
                "repair_status",
                "quarantine_status",
                "active_session_blocker_flag",
                "exact_evidence_checked",
                "repair_price",
                "blocker_reason",
            ]
        )
    order_by_id = {str(row.get("order_id") or ""): row for _, row in orders.iterrows()} if not orders.empty else {}
    event_by_order = {str(row.get("order_id") or ""): row for _, row in events.iterrows()} if not events.empty and "order_id" in events.columns else {}
    decision_by_id = {str(row.get("decision_id") or ""): row for _, row in decisions.iterrows()} if not decisions.empty and "decision_id" in decisions.columns else {}
    rows: list[dict[str, Any]] = []
    for _, fill in fills.iterrows():
        price_raw = fill.get("fill_price")
        if price_raw not in (None, "") and not pd.isna(price_raw):
            continue
        order_id = str(fill.get("order_id") or "")
        event = event_by_order.get(order_id, pd.Series(dtype=object))
        order = order_by_id.get(order_id, pd.Series(dtype=object))
        decision = decision_by_id.get(str(order.get("intent_key") or event.get("decision_id") or ""), pd.Series(dtype=object))
        event_price = event.get("filled_avg_price")
        repair_price = None
        repair_status = "UNREPAIRABLE_WITH_EXACT_BROKER_EVIDENCE"
        blocker = "fill_price_missing_and_no_exact_order_status_fill_price"
        if event_price not in (None, "") and not pd.isna(event_price):
            repair_price = float(event_price)
            repair_status = "REPAIRABLE_FROM_EXACT_ORDER_EVENT"
            blocker = ""
        filled_at = str(fill.get("filled_at") or "")
        fill_session_date = _to_et_date(filled_at) if filled_at else ""
        active_session_blocker = bool(repair_status != "REPAIRABLE_FROM_EXACT_ORDER_EVENT" and session_date and fill_session_date == session_date)
        quarantine_status = "NOT_REQUIRED"
        if repair_status != "REPAIRABLE_FROM_EXACT_ORDER_EVENT":
            quarantine_status = "ACTIVE_SESSION_BLOCKER" if active_session_blocker else "QUARANTINED_NON_PROMOTABLE_HISTORY"
        rows.append(
            {
                "fill_id": fill.get("fill_id"),
                "order_id": order_id,
                "symbol": str(fill.get("symbol") or "").upper(),
                "side": fill.get("side"),
                "filled_quantity": fill.get("filled_quantity"),
                "filled_at": filled_at,
                "fill_session_date_et": fill_session_date,
                "source": fill.get("source"),
                "repair_status": repair_status,
                "quarantine_status": quarantine_status,
                "active_session_blocker_flag": int(active_session_blocker),
                "exact_evidence_checked": "fills.order_id -> paper_order_execution_events.order_id -> orders.intent_key -> runtime_strategy_decisions.decision_id",
                "repair_price": repair_price,
                "event_filled_avg_price": event_price,
                "order_status": order.get("status"),
                "order_raw_status": order.get("raw_status"),
                "decision_limit_price": decision.get("limit_price"),
                "blocker_reason": blocker,
                "forbidden_repair_methods": "no_symbol_date_price_time_proximity; no_limit_price_substitution; no_market_tick_inference",
            }
        )
    return pd.DataFrame(rows)


def _latest_runtime_session_date(db_path: Path) -> str:
    all_decisions = read_table(db_path, "runtime_strategy_decisions", order_by="created_at", limit=1)
    if all_decisions.empty or "created_at" not in all_decisions.columns:
        return ""
    return _to_et_date(all_decisions.iloc[-1].get("created_at"))


def _freshness_gap_status(*, latest_runtime_date: str, session_date: str) -> str:
    if not latest_runtime_date:
        return "STALE_EOD_CLOSEOUT"
    if latest_runtime_date < session_date:
        return "STALE_EOD_CLOSEOUT"
    return "CURRENT_EOD_CLOSEOUT"


def _html_cell(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return html.escape(str(value))


def _session_fill_lines(session_fills: pd.DataFrame) -> list[str]:
    if session_fills.empty:
        return []
    lines: list[str] = []
    for _, row in session_fills.iterrows():
        symbol = str(row.get("symbol") or "-").upper()
        side = str(row.get("side") or "-").upper()
        qty = row.get("filled_quantity")
        price = row.get("fill_price")
        filled_at = row.get("filled_at") or "-"
        order_id = row.get("order_id") or "-"
        lines.append(
            f"- {symbol} {side} qty={qty} price={price} filled_at={filled_at} order_id={order_id}"
        )
    return lines


def _slack_text(summary: dict[str, Any], session_fills: pd.DataFrame) -> str:
    fill_lines = _session_fill_lines(session_fills)
    return (
        "[PAPER_EOD_FILLED_REPORT]\n"
        "deployment blocker: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY\n"
        f"filled trades only: session_fills={summary['session_fill_rows']}\n"
        "filled_trade_lines:\n"
        + "\n".join(fill_lines)
        + "\n"
        f"account truth: {summary.get('account_truth_source', '')}; realized/proxy PnL separated\n"
        f"universe coverage status: {summary.get('universe_coverage_status', 'UNKNOWN_BLOCKER')} "
        f"{summary.get('evaluated_symbol_count', 0)}/{summary.get('expected_universe_count', 0)} evaluated; "
        f"{summary.get('missing_or_stale_symbol_count', 0)} missing_or_stale\n"
        f"next owner action: 필수 총괄, 윤헌 source freshness closeout, 규승 frontend visibility 확인\n"
        f"freshness closeout: {summary.get('freshness_gap_status', '')} latest_runtime_session_date_et={summary.get('latest_runtime_session_date_et', '')}\n"
        f"date_et: {summary['session_date_et']}\n"
        f"realized_pnl_usd: {summary['realized_pnl_usd']:.2f}\n"
        f"mtm_proxy_pnl_usd: {summary['mtm_proxy_pnl_usd']:.2f}\n"
        f"open_positions: {summary['open_position_rows']}\n"
        f"top_reason: {summary['top_reason']}\n"
        f"infographic_status: {summary.get('infographic_status', '')}\n"
        f"infographic: {summary.get('infographic_report_path', '')}\n"
        f"trading_team_feedback_status: {summary.get('trading_team_feedback_status', '')}\n"
        f"trading_team_feedback: {summary.get('trading_team_feedback_path', '')}\n"
        "frontend: React Trader Terminal > 모의거래"
    )


def _slack_text_filled_only(summary: dict[str, Any], session_fills: pd.DataFrame) -> str:
    fill_lines = _session_fill_lines(session_fills)
    return (
        "[PAPER_EOD_FILLED_REPORT]\n"
        "deployment blocker: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY\n"
        f"filled trades only: session_fills={summary['session_fill_rows']}\n"
        "filled_trade_lines:\n"
        + "\n".join(fill_lines)
        + "\n"
        f"date_et: {summary['session_date_et']}\n"
        f"realized_pnl_usd: {summary['realized_pnl_usd']:.2f}\n"
        f"mtm_proxy_pnl_usd: {summary['mtm_proxy_pnl_usd']:.2f}\n"
        f"infographic_status: {summary.get('infographic_status', '')}\n"
        f"infographic: {summary.get('infographic_report_path', '')}\n"
        f"trading_team_feedback_status: {summary.get('trading_team_feedback_status', '')}\n"
        f"trading_team_feedback: {summary.get('trading_team_feedback_path', '')}\n"
        "frontend: React Trader Terminal > filled trades"
    )


def _build_trading_team_feedback(
    summary: dict[str, Any],
    decision_detail: pd.DataFrame,
    snapshot_detail: pd.DataFrame,
    trade_detail: pd.DataFrame,
) -> pd.DataFrame:
    orders_submitted = int(summary["orders_submitted"])
    orders_filled = int(summary["orders_filled"])
    runtime_decisions = int(summary["runtime_decisions"])
    broker_truth_fills = int(summary["broker_truth_fills"])
    fresh_ratio = 0.0
    if not snapshot_detail.empty and "data_fresh" in snapshot_detail.columns:
        fresh_flags = pd.to_numeric(snapshot_detail["data_fresh"], errors="coerce").fillna(0)
        fresh_ratio = _pct(int(fresh_flags.eq(1).sum()), int(len(fresh_flags)))
    candidate_ratio = _pct(int(summary["paper_order_candidates"]), runtime_decisions)
    feedback_rows = [
        {
            "team": "Execution Desk",
            "severity": "P1" if orders_submitted and broker_truth_fills < orders_filled else "P2",
            "technical_feedback": "Broker-truth fill count must remain the canonical execution source; keep event/order/fill reconciliation visible before any live readiness claim.",
            "evidence": f"orders_filled={orders_filled}; broker_truth_fills={broker_truth_fills}; trade_rows={len(trade_detail)}",
            "recommended_action": "Keep the report diagnostic-only until each filled order has a matching lifecycle/order/fill trail.",
        },
        {
            "team": "Risk Manager",
            "severity": "P1" if summary["open_position_rows"] else "P2",
            "technical_feedback": "Open-position PnL is marked as proxy and must not be mixed with realized PnL for deployment decisions.",
            "evidence": f"realized_pnl={_fmt_money(summary['realized_pnl_usd'])}; mtm_proxy={_fmt_money(summary['mtm_proxy_pnl_usd'])}; open_positions={summary['open_position_rows']}",
            "recommended_action": "Review open exposure, max symbol concentration, stop policy, and kill-switch state before next session.",
        },
        {
            "team": "Strategy Quant",
            "severity": "P2",
            "technical_feedback": "Runtime decisions are reported as evidence only; no label, future outcome, or AI-generated judgement is allowed to become an order signal.",
            "evidence": f"runtime_decisions={runtime_decisions}; paper_order_candidate_ratio={candidate_ratio:.1f}%; top_reason={summary['top_reason']}",
            "recommended_action": "Compare selected candidates against regime and intraday continuation snapshots in the frontend review page.",
        },
        {
            "team": "Market Data",
            "severity": "P1" if snapshot_detail.empty else "P2",
            "technical_feedback": "Indicator and source-price evidence must be timestamped, fresh, and aligned to the decision snapshot.",
            "evidence": f"snapshot_rows={len(snapshot_detail)}; data_fresh_ratio={fresh_ratio:.1f}%",
            "recommended_action": "Block promotion if snapshot lineage, source_price_ts, or freshness evidence is missing for traded symbols.",
        },
        {
            "team": "PM / CIO Review",
            "severity": "P0",
            "technical_feedback": "This report is an operational review artifact, not approval for real-capital deployment.",
            "evidence": "deployment_ready_flag=0; diagnostic_only_flag=1",
            "recommended_action": "Require split/OOS evidence, cost/slippage validation, reconciliation, and live-source readiness before any live switch.",
        },
    ]
    return pd.DataFrame(feedback_rows)


def _write_trading_feedback_markdown(path: Path, feedback: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Task589 Paper EOD Trading Team Feedback",
        "",
        f"- session_date_et: {summary['session_date_et']}",
        "- status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "- source: Task589 broker/order/fill/runtime-decision artifacts",
        "",
    ]
    for _, row in feedback.iterrows():
        lines.extend(
            [
                f"## {row['team']} [{row['severity']}]",
                "",
                f"- Technical feedback: {row['technical_feedback']}",
                f"- Evidence: {row['evidence']}",
                f"- Recommended action: {row['recommended_action']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_infographic_html(
    path: Path,
    summary: dict[str, Any],
    trade_detail: pd.DataFrame,
    decision_detail: pd.DataFrame,
    feedback: pd.DataFrame,
) -> None:
    orders_submitted = int(summary["orders_submitted"])
    orders_filled = int(summary["orders_filled"])
    orders_pending = int(summary["orders_pending"])
    runtime_decisions = int(summary["runtime_decisions"])
    candidates = int(summary["paper_order_candidates"])
    fill_pct = _pct(orders_filled, orders_submitted)
    candidate_pct = _pct(candidates, runtime_decisions)
    reasons = []
    if not decision_detail.empty and "reason_code" in decision_detail.columns:
        counts = decision_detail["reason_code"].astype(str).replace("", "-").value_counts().head(6)
        max_count = int(counts.max()) if not counts.empty else 1
        for reason, count in counts.items():
            width = max(3.0, float(count) / max_count * 100.0)
            reasons.append((reason, int(count), width))
    if not reasons:
        reasons = [("NO_DECISION_REASON_ROWS", 0, 3.0)]
    latest_rows = []
    if not decision_detail.empty:
        cols = [col for col in ["created_at", "symbol", "decision_status", "side", "score", "reason_code"] if col in decision_detail.columns]
        if cols:
            latest_rows = decision_detail.sort_values(cols[0], ascending=False).head(8)[cols].to_dict("records")
    feedback_cards = "\n".join(
        f"""
        <section class="feedback-card severity-{_html_cell(row['severity']).lower()}">
          <div class="feedback-head"><span>{_html_cell(row['team'])}</span><b>{_html_cell(row['severity'])}</b></div>
          <p>{_html_cell(row['technical_feedback'])}</p>
          <small>{_html_cell(row['evidence'])}</small>
        </section>
        """
        for _, row in feedback.iterrows()
    )
    reason_bars = "\n".join(
        f"""
        <div class="bar-row">
          <span>{_html_cell(reason)}</span>
          <div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>
          <b>{count}</b>
        </div>
        """
        for reason, count, width in reasons
    )
    decision_rows = "\n".join(
        "<tr>" + "".join(f"<td>{_html_cell(value)}</td>" for value in row.values()) + "</tr>"
        for row in latest_rows
    )
    if not decision_rows:
        decision_rows = '<tr><td colspan="6">No runtime decision rows for this session.</td></tr>'
    html_text = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Task589 Paper EOD Infographic</title>
  <style>
    :root {{ color-scheme: dark; --bg:#071013; --panel:#101b20; --line:#263941; --text:#edf7f8; --muted:#9bb3b9; --green:#5ed6a3; --amber:#ffd166; --red:#ff6b6b; --cyan:#4cc9f0; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family: Arial, "Malgun Gothic", sans-serif; }}
    main {{ width:min(1180px, 96vw); margin:0 auto; padding:32px 0 42px; }}
    header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; border-bottom:1px solid var(--line); padding-bottom:18px; }}
    h1 {{ margin:0; font-size:34px; line-height:1.1; letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:19px; letter-spacing:0; }}
    .subtitle {{ color:var(--muted); margin-top:8px; }}
    .stamp {{ text-align:right; color:var(--muted); font-size:13px; }}
    .verdict {{ color:var(--red); font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin:22px 0; }}
    .metric, .panel, .feedback-card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .metric span {{ color:var(--muted); font-size:13px; }}
    .metric b {{ display:block; margin-top:8px; font-size:28px; }}
    .metric small {{ color:var(--muted); }}
    .layout {{ display:grid; grid-template-columns:1.1fr .9fr; gap:14px; }}
    .funnel {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; }}
    .step {{ border-left:4px solid var(--cyan); background:#0b171b; padding:14px; border-radius:6px; min-height:94px; }}
    .step b {{ display:block; font-size:25px; margin:5px 0; }}
    .bar-row {{ display:grid; grid-template-columns:170px 1fr 44px; gap:10px; align-items:center; margin:9px 0; }}
    .bar-track {{ height:12px; background:#091215; border-radius:999px; overflow:hidden; border:1px solid var(--line); }}
    .bar-fill {{ height:100%; background:linear-gradient(90deg, var(--cyan), var(--green)); }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    td {{ border-top:1px solid var(--line); padding:9px 7px; color:#dcebed; vertical-align:top; }}
    .feedback-grid {{ display:grid; grid-template-columns:repeat(2, 1fr); gap:12px; }}
    .feedback-head {{ display:flex; justify-content:space-between; gap:12px; margin-bottom:8px; }}
    .feedback-card p {{ margin:0 0 10px; line-height:1.45; }}
    .feedback-card small {{ color:var(--muted); line-height:1.35; }}
    .severity-p0 {{ border-color:var(--red); }}
    .severity-p1 {{ border-color:var(--amber); }}
    footer {{ margin-top:22px; color:var(--muted); font-size:12px; border-top:1px solid var(--line); padding-top:12px; }}
    @media (max-width: 860px) {{ .grid, .layout, .feedback-grid {{ grid-template-columns:1fr; }} header {{ display:block; }} .stamp {{ text-align:left; margin-top:12px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>모의거래 장마감 인포그래픽</h1>
      <div class="subtitle">Verified runtime artifacts · trading-team technical feedback · deterministic HTML report</div>
    </div>
    <div class="stamp">
      <div>session_date_et: <b>{_html_cell(summary['session_date_et'])}</b></div>
      <div class="verdict">DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY</div>
    </div>
  </header>
  <section class="grid">
    <div class="metric"><span>Realized PnL</span><b>{_fmt_money(summary['realized_pnl_usd'])}</b><small>paired BUY/SELL fills only</small></div>
    <div class="metric"><span>MTM Proxy PnL</span><b>{_fmt_money(summary['mtm_proxy_pnl_usd'])}</b><small>open positions only</small></div>
    <div class="metric"><span>Filled Orders</span><b>{orders_filled}/{orders_submitted}</b><small>{fill_pct:.1f}% execution funnel</small></div>
    <div class="metric"><span>Runtime Candidates</span><b>{candidates}/{runtime_decisions}</b><small>{candidate_pct:.1f}% selected</small></div>
  </section>
  <section class="layout">
    <div class="panel">
      <h2>Execution Funnel</h2>
      <div class="funnel">
        <div class="step"><span>Submitted</span><b>{orders_submitted}</b><small>order rows</small></div>
        <div class="step"><span>Filled</span><b>{orders_filled}</b><small>broker/order fill evidence</small></div>
        <div class="step"><span>Pending</span><b>{orders_pending}</b><small>requires next-session review</small></div>
      </div>
    </div>
    <div class="panel">
      <h2>Decision Reasons</h2>
      {reason_bars}
    </div>
  </section>
  <section class="panel" style="margin-top:14px;">
    <h2>Latest Runtime Decisions</h2>
    <table>{decision_rows}</table>
  </section>
  <section class="panel" style="margin-top:14px;">
    <h2>Professional Trading Team Feedback</h2>
    <div class="feedback-grid">{feedback_cards}</div>
  </section>
  <footer>
    Sources: paper_eod_summary.csv, paper_eod_trade_detail.csv, paper_eod_decision_evidence.csv, paper_eod_indicator_snapshot_evidence.csv, paper_eod_trading_team_feedback.csv. No image-generation model or LLM-generated trading signal is used.
  </footer>
</main>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def run_task589(*, db_path: Path, env_file: Path, session_date: str = "") -> dict[str, pd.DataFrame]:
    load_runtime_env(env_file)
    generated_utc = utc_now()
    if not session_date:
        session_date = _latest_runtime_session_date(db_path) or datetime.now(UTC).astimezone(EASTERN).date().isoformat()
    all_events = read_table(db_path, "paper_order_execution_events", order_by="created_at", limit=5000)
    all_orders = read_table(db_path, "orders", order_by="submitted_at", limit=5000)
    all_fills = read_table(db_path, "fills", order_by="filled_at", limit=5000)
    all_decisions = read_table(db_path, "runtime_strategy_decisions", order_by="created_at", limit=5000)
    all_lifecycle = read_table(db_path, "continuation_source_events", order_by="created_at", limit=5000)
    events = _filter_et_date(all_events, "created_at", session_date)
    orders = _filter_et_date(all_orders, "submitted_at", session_date)
    session_fills = _filter_et_date(all_fills, "filled_at", session_date)
    fills = _filter_until_et_date(all_fills, "filled_at", session_date)
    decisions = _filter_et_date(all_decisions, "created_at", session_date)
    lifecycle = _filter_et_date(all_lifecycle, "created_at", session_date)
    snapshots_all = read_table(db_path, "indicator_snapshots", order_by="created_at", limit=5000)

    marks = _latest_marks(db_path)
    universe = _latest_universe_coverage_from_db(db_path, session_date)
    latest_runtime_session_date = _latest_runtime_session_date(db_path)
    freshness_gap_status = _freshness_gap_status(latest_runtime_date=latest_runtime_session_date, session_date=session_date)
    realized, open_positions, pnl = _pnl_from_fills(fills, marks)
    position_sync = _sync_positions_from_fills(db_path, fills)
    filled_trade_history = _filled_trade_history(fills, all_orders, all_events, all_decisions)
    fill_price_repair_audit = _fill_price_repair_audit(fills, all_orders, all_events, all_decisions, session_date=session_date)
    order_status = orders["status"].astype(str).str.upper() if not orders.empty and "status" in orders.columns else pd.Series(dtype=str)
    event_reason = events["reason_code"].astype(str) if not events.empty and "reason_code" in events.columns else pd.Series(dtype=str)
    top_reason = event_reason[event_reason.ne("")].mode().iloc[0] if not event_reason[event_reason.ne("")].empty else "-"
    fill_price_repair_status = fill_price_repair_audit.get("repair_status", pd.Series(dtype=str)).astype(str) if not fill_price_repair_audit.empty else pd.Series(dtype=str)
    fill_price_quarantine_status = fill_price_repair_audit.get("quarantine_status", pd.Series(dtype=str)).astype(str) if not fill_price_repair_audit.empty else pd.Series(dtype=str)
    fill_price_active_blocker = pd.to_numeric(
        fill_price_repair_audit.get("active_session_blocker_flag", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0) if not fill_price_repair_audit.empty else pd.Series(dtype=float)
    summary = {
        "task_id": "Task589",
        "generated_utc": generated_utc,
        "session_date_et": session_date,
        "orders_submitted": int(len(orders)),
        "orders_filled": int(order_status.eq("FILLED").sum()) if not order_status.empty else 0,
        "orders_pending": int(order_status.isin(["SUBMITTED", "PENDING", "PARTIAL", "UNKNOWN"]).sum()) if not order_status.empty else 0,
        "session_fill_rows": int(len(session_fills)),
        "cumulative_fill_rows": int(len(fills)),
        "filled_trade_history_rows": int(len(filled_trade_history)),
        "runtime_decisions": int(len(decisions)),
        "paper_order_candidates": int(decisions.get("decision_status", pd.Series(dtype=str)).astype(str).eq("PAPER_ORDER_CANDIDATE").sum()) if not decisions.empty else 0,
        "broker_truth_fills": int(pd.to_numeric(events.get("broker_truth_fill_flag", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not events.empty else 0,
        "realized_pnl_usd": pnl["realized_pnl_usd"],
        "mtm_proxy_pnl_usd": pnl["mtm_proxy_pnl_usd"],
        "open_position_rows": int(len(open_positions)),
        "authoritative_position_rows": int(position_sync["authoritative_position_rows"]),
        "position_event_rows": int(position_sync["position_event_rows"]),
        "position_fill_rows_skipped": int(position_sync["position_fill_rows_skipped"]),
        "fill_price_repairable_rows": int(fill_price_repair_status.eq("REPAIRABLE_FROM_EXACT_ORDER_EVENT").sum()),
        "fill_price_unrepairable_rows": int(fill_price_repair_status.eq("UNREPAIRABLE_WITH_EXACT_BROKER_EVIDENCE").sum()),
        "fill_price_quarantined_rows": int(fill_price_quarantine_status.eq("QUARANTINED_NON_PROMOTABLE_HISTORY").sum()),
        "fill_price_active_blocker_rows": int(fill_price_active_blocker.eq(1).sum()),
        "fill_price_integrity_status": "ACTIVE_BLOCKER" if int(fill_price_active_blocker.eq(1).sum()) else "QUARANTINED_NON_PROMOTABLE_HISTORY" if int(fill_price_quarantine_status.eq("QUARANTINED_NON_PROMOTABLE_HISTORY").sum()) else "PASS",
        "position_sync_status": position_sync["position_sync_status"],
        "frontend_account_sync_status": "AUTHORITATIVE_POSITIONS_REBUILT__OPEN_PNL_PROXY_VIEW",
        "account_truth_source": "BROKER_TRUTH_FILLS_REPLAYED_TO_POSITIONS",
        "session_trade_scope": "CURRENT_SESSION_ONLY",
        "cumulative_account_scope": "CUMULATIVE_BROKER_TRUTH_FILLS_UNTIL_SESSION",
        "current_session_trade_status": "NO_SESSION_ORDER_OR_FILL" if len(orders) == 0 and len(session_fills) == 0 else "SESSION_ACTIVITY_PRESENT",
        "top_reason": top_reason,
        **universe,
        "latest_runtime_session_date_et": latest_runtime_session_date,
        "freshness_gap_status": freshness_gap_status,
        "pnl_policy": "REALIZED_ONLY_FROM_BUY_SELL_FILLS__OPEN_POSITIONS_MARKED_AS_PROXY",
        "deployment_ready_flag": 0,
        "diagnostic_only_flag": 1,
    }
    webhook_present = bool(os.environ.get("SLACK_WEBHOOK_URL", "").strip())
    slack_dry_run = os.environ.get("PAPER_EOD_SLACK_DRY_RUN", "").strip() == "1"
    secret_free = True
    slack_status = "SLACK_NOT_SENT"
    error = ""
    trade_detail_cols = [
        col
        for col in [
            "created_at",
            "decision_id",
            "order_id",
            "lifecycle_id",
            "symbol",
            "side",
            "quantity",
            "limit_price",
            "order_status",
            "reason_code",
            "broker_truth_fill_flag",
            "filled_qty",
            "filled_avg_price",
        ]
        if col in events.columns
    ]
    trade_detail = events[trade_detail_cols].copy() if trade_detail_cols else pd.DataFrame()
    decision_detail_cols = [
        col
        for col in [
            "created_at",
            "decision_id",
            "decision_status",
            "symbol",
            "side",
            "quantity",
            "limit_price",
            "reason_code",
            "reason_detail",
            "entry_allowed",
            "data_fresh",
            "selected_for_portfolio",
            "score",
            "source_snapshot_id",
            "source_price_ts",
            "source_type",
            "regime_state",
            "intraday_state",
            "runtime_state_capture_status",
            "state_source_snapshot_id",
        ]
        if col in decisions.columns
    ]
    decision_detail = decisions[decision_detail_cols].copy() if decision_detail_cols else pd.DataFrame()
    filled_decision_detail = pd.DataFrame()
    if not filled_trade_history.empty and not all_decisions.empty and "decision_id" in all_decisions.columns:
        filled_decision_ids = set(filled_trade_history.get("decision_id", pd.Series(dtype=str)).dropna().astype(str))
        filled_decision_cols = [
            col
            for col in [
                "created_at",
                "decision_id",
                "decision_status",
                "symbol",
                "side",
                "quantity",
                "limit_price",
                "reason_code",
                "reason_detail",
                "entry_allowed",
                "data_fresh",
                "selected_for_portfolio",
                "score",
                "source_snapshot_id",
                "source_price_ts",
                "source_type",
                "regime_state",
                "intraday_state",
                "runtime_state_capture_status",
                "state_source_snapshot_id",
            ]
            if col in all_decisions.columns
        ]
        filled_decision_detail = all_decisions.loc[
            all_decisions["decision_id"].astype(str).isin(filled_decision_ids),
            filled_decision_cols,
        ].copy()
    snapshot_detail = pd.DataFrame()
    snapshot_decision_source = pd.concat([decision_detail, filled_decision_detail], ignore_index=True)
    if not snapshots_all.empty and not snapshot_decision_source.empty and "source_snapshot_id" in snapshot_decision_source.columns and "snapshot_id" in snapshots_all.columns:
        snapshot_ids = set(snapshot_decision_source["source_snapshot_id"].dropna().astype(str))
        snapshot_cols = [
            col
            for col in [
                "snapshot_id",
                "created_at",
                "symbol",
                "bar_end_ts",
                "close",
                "ma20",
                "ma50",
                "ma200",
                "breakout_high_20",
                "breakout_condition",
                "ma_condition",
                "entry_allowed",
                "data_fresh",
                "insufficient_history",
                "action",
                "side",
                "reason",
                "score",
                "candidate_rank",
                "selected_for_portfolio",
                "source_price_ts",
                "source_price",
                "source_type",
                "freshness_age_sec",
                "stale_reason",
            ]
            if col in snapshots_all.columns
        ]
        snapshot_detail = snapshots_all.loc[snapshots_all["snapshot_id"].astype(str).isin(snapshot_ids), snapshot_cols].copy()

    feedback = _build_trading_team_feedback(summary, decision_detail, snapshot_detail, trade_detail)
    infographic_path = REPORT_DIR / f"paper_eod_infographic_{session_date}.html"
    feedback_md_path = REPORT_DIR / f"paper_eod_trading_team_feedback_{session_date}.md"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary["infographic_status"] = "HTML_READY"
    summary["infographic_report_path"] = str(infographic_path)
    summary["trading_team_feedback_status"] = "READY"
    summary["trading_team_feedback_path"] = str(feedback_md_path)
    _write_infographic_html(infographic_path, summary, trade_detail, decision_detail, feedback)
    _write_trading_feedback_markdown(feedback_md_path, feedback, summary)

    text = _slack_text_filled_only(summary, session_fills) if not session_fills.empty else (
        "[PAPER_EOD_SKIPPED_NO_FILLED_TRADES]\n"
        "reason: Slack EOD trade reports are sent only when the session has broker-truth filled trades."
    )
    secret_free = _secret_free(text)
    if session_fills.empty:
        slack_status = "SKIPPED_NO_FILLED_TRADES"
        error = ""
    elif slack_dry_run:
        slack_status = "DRY_RUN_NOT_SENT"
        error = ""
    elif not webhook_present:
        slack_status = "SLACK_BLOCKED_MISSING_WEBHOOK"
        error = ""
    elif not secret_free:
        slack_status = "SLACK_BLOCKED_SECRET_IN_MESSAGE"
        error = ""
    else:
        try:
            slack_client.send_message(text)
            slack_status = "SENT"
            error = ""
        except Exception as exc:  # pragma: no cover - external Slack availability.
            slack_status = "FAILED"
            error = str(exc)
    summary["slack_send_status"] = slack_status
    summary_frame = pd.DataFrame([summary])
    slack_audit = pd.DataFrame(
        [
            {
                "created_at_utc": utc_now(),
                "session_date_et": session_date,
                "message_type": "PAPER_EOD_FILLED_REPORT" if not session_fills.empty else "SKIPPED_NO_FILLED_TRADES",
                "slack_send_status": slack_status,
                "message_preview": text[:500],
                "webhook_present_flag": int(webhook_present),
                "dry_run_flag": int(slack_dry_run),
                "secret_in_message_flag": int(not secret_free),
                "error": error,
                "infographic_report_path": str(infographic_path),
                "trading_team_feedback_path": str(feedback_md_path),
            }
        ]
    )

    artifacts = {
        "paper_eod_summary.csv": summary_frame,
        "paper_eod_trade_detail.csv": trade_detail,
        "paper_eod_filled_trade_history.csv": filled_trade_history,
        "paper_eod_decision_evidence.csv": decision_detail,
        "paper_eod_filled_decision_evidence.csv": filled_decision_detail,
        "paper_eod_indicator_snapshot_evidence.csv": snapshot_detail,
        "paper_eod_trading_team_feedback.csv": feedback,
        "paper_eod_realized_pnl.csv": realized,
        "paper_eod_open_position_proxy.csv": open_positions,
        "paper_eod_fill_price_repair_audit.csv": fill_price_repair_audit,
        "paper_eod_lifecycle_events.csv": lifecycle.head(200),
        "paper_eod_slack_audit.csv": slack_audit,
    }
    for name, frame in artifacts.items():
        write_csv(REPORT_DIR, name, frame)
    write_task_report(
        REPORT_DIR,
        "task_589_nasdaq_paper_ops_hardening.md",
        title="Task589 - Nasdaq Paper Ops Hardening",
        decision_summary=[
            "decision_status=PRIMARY_PASS",
            "deployment_blocker=DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            f"universe_coverage_status={summary['universe_coverage_status']}",
            f"freshness_gap_status={summary['freshness_gap_status']}",
            f"session_date_et={session_date}",
            f"slack_send_status={slack_status}",
            f"infographic_status={summary['infographic_status']}",
            f"trading_team_feedback_status={summary['trading_team_feedback_status']}",
            "Calendar guard, EOD report, and supervisor alert paths are operational infrastructure, not deployment approval.",
        ],
        quant_lines=[
            "Nasdaq calendar guard uses the checked-in Nasdaq holiday/early-close source for covered years.",
            "Realized PnL is computed only from paired BUY/SELL broker-truth fills; open positions are separated as mark-to-market proxy.",
            "The EOD infographic is deterministic HTML/CSS built from Task589 CSV artifacts; no image-generation model is used.",
            "Slack EOD trade reports are sent only when the session has broker-truth filled trades; no-fill sessions are audited as SKIPPED_NO_FILLED_TRADES.",
            "Professional trading-team feedback is diagnostic governance evidence and must not feed back into order generation.",
            "No labels or future outcomes enter runtime assignment logic.",
            "Missing calendar years block trading rather than approximating holiday status.",
        ],
        decision_maker_lines=[
            "장마감 후 모의거래 내역과 PnL 요약을 Slack과 HTML 보고서로 확인할 수 있습니다.",
            "오늘 세션의 주문/체결과 누적 모의계좌 상태를 분리해서 보고합니다.",
            "실현손익은 BUY/SELL 체결쌍에서만 계산하고, 열린 포지션 평가는 proxy로 분리합니다.",
            "이 결과는 DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY 상태입니다.",
        ],
    )
    append_registry_rows(
        [
            {
                "task_id": "Task589",
                "title": "Nasdaq Paper Ops Hardening",
                "owner_team": "Execution & Risk",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "diagnostic-only",
                "data_readiness": "runtime-source",
                "parent_task": "Task588",
                "key_report": str(REPORT_DIR / "task_589_nasdaq_paper_ops_hardening.md"),
                "key_decision": str(REPORT_DIR / "paper_eod_summary.csv"),
                "key_artifacts": str(REPORT_DIR),
                "validation_command": "python -m unittest tests.test_task589_nasdaq_paper_ops_hardening",
                "notes": "Adds Nasdaq holiday/early-close guard, filled-trade-only EOD Slack report, deterministic infographic artifact, professional trading-team feedback, and supervisor/lifecycle alerts.",
            }
        ]
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--env-file", type=Path, default=Path("config/kis_paper.env"))
    parser.add_argument("--session-date", type=str, default="")
    args = parser.parse_args()
    artifacts = run_task589(db_path=args.db_path, env_file=args.env_file, session_date=args.session_date)
    print(artifacts["paper_eod_summary.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
