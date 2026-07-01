from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .continuation_runtime_capture_370 import emit_continuation_capture_event
from .paper_runtime_common import (
    append_registry_rows,
    latest_runtime_decision,
    load_runtime_env,
    read_table,
    utc_now,
    write_csv,
    write_task_report,
)
try:
    from src.backtest.canonical_position_lifecycle_event_sourcing import build_canonical_lifecycle_id
    from src.integration.kis_client import KISClient
    from src.state.store import (
        FILL_INSERTED,
        initialize_store,
        record_fill,
        record_order,
        record_trade_run_finish,
        record_trade_run_start,
        update_order_status,
    )
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from backtest.canonical_position_lifecycle_event_sourcing import build_canonical_lifecycle_id
    from integration.kis_client import KISClient
    from state.store import (
        FILL_INSERTED,
        initialize_store,
        record_fill,
        record_order,
        record_trade_run_finish,
        record_trade_run_start,
        update_order_status,
    )


REPORT_DIR = Path("docs/reports/task_585_kis_paper_order_execution")


def _ensure_tables(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_order_execution_events (
                event_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                decision_id TEXT,
                client_order_id TEXT,
                order_id TEXT,
                lifecycle_id TEXT,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                limit_price REAL,
                order_status TEXT NOT NULL,
                reason_code TEXT,
                raw_response_json TEXT,
                broker_truth_fill_flag INTEGER NOT NULL DEFAULT 0,
                filled_qty REAL,
                filled_avg_price REAL
            )
            """
        )
        existing_cols = {row[1] for row in con.execute("PRAGMA table_info(paper_order_execution_events)").fetchall()}
        if "status_refresh_json" not in existing_cols:
            con.execute("ALTER TABLE paper_order_execution_events ADD COLUMN status_refresh_json TEXT")
        if "pre_order_position_qty" not in existing_cols:
            con.execute("ALTER TABLE paper_order_execution_events ADD COLUMN pre_order_position_qty REAL")
        if "post_order_position_qty" not in existing_cols:
            con.execute("ALTER TABLE paper_order_execution_events ADD COLUMN post_order_position_qty REAL")
        if "position_delta_qty" not in existing_cols:
            con.execute("ALTER TABLE paper_order_execution_events ADD COLUMN position_delta_qty REAL")
        if "fill_confirmation_source" not in existing_cols:
            con.execute("ALTER TABLE paper_order_execution_events ADD COLUMN fill_confirmation_source TEXT")
        con.execute("CREATE INDEX IF NOT EXISTS idx_paper_order_events_created ON paper_order_execution_events(created_at)")
        con.commit()
    finally:
        con.close()


def _update_execution_position_audit(
    db_path: Path,
    *,
    order_id: str,
    pre_order_position_qty: Any = None,
    post_order_position_qty: Any = None,
    position_delta_qty: Any = None,
    fill_confirmation_source: Any = None,
) -> None:
    if not order_id:
        return
    _ensure_tables(db_path)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            UPDATE paper_order_execution_events
            SET pre_order_position_qty = COALESCE(?, pre_order_position_qty),
                post_order_position_qty = COALESCE(?, post_order_position_qty),
                position_delta_qty = COALESCE(?, position_delta_qty),
                fill_confirmation_source = COALESCE(?, fill_confirmation_source)
            WHERE order_id = ?
            """,
            (
                None if pre_order_position_qty in (None, "") else float(pre_order_position_qty),
                None if post_order_position_qty in (None, "") else float(post_order_position_qty),
                None if position_delta_qty in (None, "") else float(position_delta_qty),
                None if fill_confirmation_source in (None, "") else str(fill_confirmation_source),
                order_id,
            ),
        )
        con.commit()
    finally:
        con.close()


def _record_execution_event(db_path: Path, row: dict[str, Any]) -> None:
    _ensure_tables(db_path)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT OR REPLACE INTO paper_order_execution_events(
                event_id, created_at, decision_id, client_order_id, order_id, lifecycle_id,
                symbol, side, quantity, limit_price, order_status, reason_code, raw_response_json,
                broker_truth_fill_flag, filled_qty, filled_avg_price
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                row["event_id"],
                row["created_at"],
                row.get("decision_id"),
                row.get("client_order_id"),
                row.get("order_id"),
                row.get("lifecycle_id"),
                row.get("symbol"),
                row.get("side"),
                row.get("quantity"),
                row.get("limit_price"),
                row["order_status"],
                row.get("reason_code"),
                json.dumps(row.get("raw_response") or {}, ensure_ascii=True, default=str),
                int(row.get("broker_truth_fill_flag") or 0),
                float(row.get("filled_qty") or 0.0),
                None if row.get("filled_avg_price") in (None, "") else float(row.get("filled_avg_price")),
            ),
        )
        con.commit()
    finally:
        con.close()
    if any(key in row for key in ("pre_order_position_qty", "post_order_position_qty", "position_delta_qty", "fill_confirmation_source")):
        _update_execution_position_audit(
            db_path,
            order_id=str(row.get("order_id") or ""),
            pre_order_position_qty=row.get("pre_order_position_qty"),
            post_order_position_qty=row.get("post_order_position_qty"),
            position_delta_qty=row.get("position_delta_qty"),
            fill_confirmation_source=row.get("fill_confirmation_source"),
        )


def _latest_lineage(db_path: Path) -> pd.DataFrame:
    events = read_table(db_path, "paper_order_execution_events", order_by="created_at", limit=50)
    if events.empty:
        return pd.DataFrame()
    return events


def _fills_for_order(kis: KISClient, order_id: str, symbol: str) -> tuple[float, float | None, list[dict[str, Any]]]:
    fills = kis.get_fills(order_id, symbol=symbol)
    return _aggregate_fills(fills)


def _aggregate_fills(fills: list[dict[str, Any]]) -> tuple[float, float | None, list[dict[str, Any]]]:
    if not fills:
        return 0.0, None, []
    qty = sum(float(fill.get("filled_qty") or 0.0) for fill in fills)
    weighted = 0.0
    weighted_qty = 0.0
    for fill in fills:
        px = fill.get("fill_price")
        q = float(fill.get("filled_qty") or 0.0)
        if px not in (None, "") and q > 0:
            weighted += q * float(px)
            weighted_qty += q
    return qty, (weighted / weighted_qty) if weighted_qty > 0 else None, fills


def _fills_from_snapshot(order_id: str, symbol: str, snap: dict[str, Any]) -> tuple[float, float | None, list[dict[str, Any]]]:
    filled_qty = float(snap.get("filled_qty") or 0.0)
    if filled_qty <= 0:
        return 0.0, None, []
    raw_row = snap.get("raw_row") if isinstance(snap.get("raw_row"), dict) else {}
    fill_price = None
    for key in ("avg_ccld_unpr", "ccld_unpr", "ft_ccld_unpr3", "ovrs_ccld_unpr"):
        value = raw_row.get(key) if isinstance(raw_row, dict) else None
        if value not in (None, ""):
            try:
                fill_price = float(value)
                break
            except Exception:
                fill_price = None
    return _aggregate_fills(
        [
            {
                "order_id": str(order_id),
                "symbol": str(snap.get("symbol") or symbol or "").strip().upper(),
                "filled_qty": filled_qty,
                "fill_price": fill_price,
                "filled_at": utc_now(),
                "raw_status": str(snap.get("raw_status") or ""),
                "mapped_status": str(snap.get("mapped_status") or "UNKNOWN"),
            }
        ]
    )


def _position_quantity_with_retry(kis: KISClient, symbol: str, *, attempts: int = 3, sleep_seconds: float = 1.1) -> tuple[float | None, str]:
    last_error = ""
    for attempt in range(max(1, attempts)):
        try:
            return float(kis.get_position_quantity(symbol)), "POSITION_BASELINE_OK"
        except Exception as exc:
            last_error = str(exc)
            if "EGW00201" not in last_error or attempt == attempts - 1:
                break
            time.sleep(max(0.1, sleep_seconds))
    return None, f"POSITION_BASELINE_FAILED:{last_error}"


def _require_pre_order_position_baseline() -> bool:
    return str(os.environ.get("KIS_REQUIRE_PRE_ORDER_POSITION_BASELINE", "1")).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _active_order_blocker(db_path: Path, symbol: str) -> str:
    max_open = int(os.environ.get("TRADING_MAX_OPEN_ORDERS", "1") or "1")
    grace_minutes = float(os.environ.get("TRADING_ACTIVE_ORDER_GRACE_MINUTES", "20") or "20")
    cutoff = datetime.now(UTC).timestamp() - (grace_minutes * 60.0)
    max_daily_orders = int(os.environ.get("TRADING_MAX_PAPER_ORDERS_PER_DAY", "3") or "3")
    session_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    active_statuses = {"SUBMITTED", "PENDING", "PARTIAL"}
    orders = read_table(db_path, "orders", order_by="submitted_at", limit=200)
    active = pd.DataFrame()
    if not orders.empty and {"status", "symbol"}.issubset(orders.columns):
        if max_daily_orders > 0 and "submitted_at" in orders.columns:
            submitted_all = pd.to_datetime(orders["submitted_at"], utc=True, errors="coerce").astype("int64") / 1e9
            todays_orders = orders.loc[submitted_all.fillna(0) >= session_start]
            if len(todays_orders) >= max_daily_orders:
                return "MAX_DAILY_PAPER_ORDER_LIMIT"
        active = orders.loc[orders["status"].astype(str).str.upper().isin(active_statuses)].copy()
        if "submitted_at" in active.columns:
            submitted = pd.to_datetime(active["submitted_at"], utc=True, errors="coerce").astype("int64") / 1e9
            active = active.loc[submitted.fillna(0) >= cutoff].copy()
    if not active.empty and len(active) >= max_open:
        return "MAX_OPEN_ORDER_LIMIT"
    if not active.empty and active["symbol"].astype(str).str.upper().eq(symbol.upper()).any():
        return "ACTIVE_ORDER_EXISTS_FOR_SYMBOL"

    events = read_table(db_path, "paper_order_execution_events", order_by="created_at", limit=200)
    if not events.empty and {"order_status", "symbol"}.issubset(events.columns):
        active_events = events.loc[events["order_status"].astype(str).str.upper().isin(active_statuses)].copy()
        if "created_at" in active_events.columns:
            created = pd.to_datetime(active_events["created_at"], utc=True, errors="coerce").astype("int64") / 1e9
            active_events = active_events.loc[created.fillna(0) >= cutoff].copy()
        if not active_events.empty and len(active_events) >= max_open:
            return "MAX_OPEN_ORDER_LIMIT"
        if not active_events.empty and active_events["symbol"].astype(str).str.upper().eq(symbol.upper()).any():
            return "ACTIVE_ORDER_EXISTS_FOR_SYMBOL"
    return ""


def _update_execution_event_status(
    db_path: Path,
    *,
    order_id: str,
    order_status: str,
    raw_response: dict[str, Any],
    broker_truth_fill_flag: int = 0,
    filled_qty: float = 0.0,
    filled_avg_price: float | None = None,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            UPDATE paper_order_execution_events
            SET order_status = ?,
                status_refresh_json = ?,
                broker_truth_fill_flag = ?,
                filled_qty = ?,
                filled_avg_price = ?
            WHERE order_id = ?
            """,
            (
                order_status,
                json.dumps(raw_response, ensure_ascii=True, default=str),
                int(broker_truth_fill_flag),
                float(filled_qty or 0.0),
                None if filled_avg_price is None else float(filled_avg_price),
                order_id,
            ),
        )
        con.commit()
    finally:
        con.close()


def _refresh_active_local_orders(db_path: Path, kis: KISClient) -> pd.DataFrame:
    orders = read_table(db_path, "orders", order_by="submitted_at", limit=200)
    if orders.empty:
        return pd.DataFrame(
            [
                {
                    "refresh_ts_utc": utc_now(),
                    "order_id": "",
                    "symbol": "",
                    "previous_status": "",
                    "refreshed_status": "NO_LOCAL_ORDERS",
                    "raw_status": "",
                    "filled_qty": 0.0,
                    "filled_avg_price": None,
                    "broker_truth_fill_flag": 0,
                    "post_order_position_qty": None,
                    "position_delta_qty": None,
                    "position_fill_inference_status": "NO_LOCAL_ORDERS",
                    "error": "",
                }
            ]
        )
    active_statuses = {"SUBMITTED", "PENDING", "PARTIAL", "UNKNOWN"}
    active = orders.loc[orders["status"].astype(str).str.upper().isin(active_statuses)].copy()
    rows: list[dict[str, Any]] = []
    if active.empty:
        return pd.DataFrame(
            [
                {
                    "refresh_ts_utc": utc_now(),
                    "order_id": "",
                    "symbol": "",
                    "previous_status": "",
                    "refreshed_status": "NO_ACTIVE_LOCAL_ORDERS",
                    "raw_status": "",
                    "filled_qty": 0.0,
                    "filled_avg_price": None,
                    "broker_truth_fill_flag": 0,
                    "post_order_position_qty": None,
                    "position_delta_qty": None,
                    "position_fill_inference_status": "NO_ACTIVE_LOCAL_ORDERS",
                    "error": "",
                }
            ]
        )
    for _, order in active.iterrows():
        order_id = str(order.get("order_id") or "")
        symbol = str(order.get("symbol") or "").upper()
        previous_status = str(order.get("status") or "")
        row = {
            "refresh_ts_utc": utc_now(),
            "order_id": order_id,
            "symbol": symbol,
            "previous_status": previous_status,
            "refreshed_status": "",
            "raw_status": "",
            "filled_qty": 0.0,
            "filled_avg_price": None,
            "broker_truth_fill_flag": 0,
            "post_order_position_qty": None,
            "position_delta_qty": None,
            "position_fill_inference_status": "",
            "error": "",
        }
        try:
            snap = kis.get_order_snapshot(order_id, symbol=symbol)
            mapped = str(snap.get("mapped_status") or "UNKNOWN").upper()
            raw_status = str(snap.get("raw_status") or "").upper()
            submitted_ts = pd.to_datetime(order.get("submitted_at"), utc=True, errors="coerce")
            age_minutes = 999999.0
            if not pd.isna(submitted_ts):
                age_minutes = (datetime.now(UTC) - submitted_ts.to_pydatetime()).total_seconds() / 60.0
            grace_minutes = float(os.environ.get("TRADING_ACTIVE_ORDER_GRACE_MINUTES", "20") or "20")
            if mapped == "UNKNOWN" and raw_status == "ORDER_NOT_FOUND":
                local_status = "PENDING" if age_minutes <= grace_minutes else "UNKNOWN"
            else:
                local_status = "PENDING" if mapped == "UNKNOWN" else mapped
            if local_status not in {"SUBMITTED", "PENDING", "PARTIAL", "FILLED", "CANCELLED", "REJECTED", "UNKNOWN"}:
                local_status = "UNKNOWN"
            events = read_table(db_path, "paper_order_execution_events", order_by="created_at", limit=200)
            event_row: dict[str, Any] = {}
            if not events.empty and "order_id" in events.columns:
                matched = events.loc[events["order_id"].astype(str).eq(order_id)]
                if not matched.empty:
                    event_row = matched.iloc[0].to_dict()
            pre_qty_raw = event_row.get("pre_order_position_qty") if event_row else None
            baseline_available = int(pre_qty_raw not in (None, "") and not pd.isna(pre_qty_raw))
            filled_qty, filled_avg_price, broker_fills = _fills_from_snapshot(order_id, symbol, snap)
            broker_truth_fill_flag = int(filled_qty > 0)
            fill_confirmation_source = "ORDER_STATUS" if broker_truth_fill_flag else ""
            if broker_truth_fill_flag:
                local_status = "FILLED"
                fill_id = f"{order_id}:{utc_now()}:ORDER_STATUS"
                record_fill(
                    str(db_path),
                    fill_id=fill_id,
                    order_id=order_id,
                    run_id=str(order.get("run_id") or ""),
                    symbol=symbol,
                    side=str(order.get("side") or ""),
                    filled_quantity=filled_qty,
                    fill_price=filled_avg_price,
                    filled_at=utc_now(),
                    source="ORDER_STATUS",
                )
                lifecycle_id = ""
                if event_row:
                    lifecycle_id = str(event_row.get("lifecycle_id") or "")
                if lifecycle_id:
                    emit_continuation_capture_event(
                        db_path=str(db_path),
                        environment="paper",
                        run_id=str(order.get("run_id") or ""),
                        event_type="FILL_CONFIRMED",
                        symbol=symbol,
                        side=str(order.get("side") or ""),
                        reason="broker_truth_fill_confirmed_by_status_refresh",
                        order_id=order_id,
                        result_status="FILLED",
                        payload={
                            "canonical_lifecycle_id": lifecycle_id,
                            "fill_id": fill_id,
                            "filled_quantity": filled_qty,
                            "price": filled_avg_price,
                            "event_timestamp": utc_now(),
                            "order_intent_id": str(order.get("intent_key") or ""),
                            "trade_run_id": str(order.get("run_id") or ""),
                        },
                    )
            position_qty = None
            position_delta = None
            position_inference_status = "NOT_CHECKED"
            position_min_age = float(os.environ.get("KIS_POSITION_FALLBACK_MIN_AGE_MINUTES", os.environ.get("TRADING_ACTIVE_ORDER_GRACE_MINUTES", "60")) or "60")
            try:
                if previous_status.upper() == "UNKNOWN" and raw_status == "ORDER_NOT_FOUND":
                    raise RuntimeError("POSITION_CHECK_SKIPPED_UNKNOWN_ORDER")
                if age_minutes < position_min_age:
                    raise RuntimeError(f"POSITION_CHECK_DEFERRED_UNTIL_{position_min_age:.0f}M")
                position_qty = float(kis.get_position_quantity(symbol))
                order_qty = float(order.get("quantity") or event_row.get("quantity") or 0.0)
                order_side = str(order.get("side") or event_row.get("side") or "").upper()
                if pre_qty_raw in (None, "") or pd.isna(pre_qty_raw):
                    position_inference_status = "POSITION_PRESENT_BASELINE_MISSING" if position_qty > 0 else "NO_POSITION_BASELINE_MISSING"
                else:
                    pre_qty = float(pre_qty_raw)
                    position_delta = position_qty - pre_qty
                    buy_confirmed = order_side == "BUY" and order_qty > 0 and position_delta >= order_qty
                    sell_confirmed = order_side == "SELL" and order_qty > 0 and position_delta <= -order_qty
                    if not broker_truth_fill_flag and (buy_confirmed or sell_confirmed):
                        local_status = "FILLED"
                        filled_qty = order_qty
                        broker_truth_fill_flag = 1
                        fill_confirmation_source = "POSITION_DELTA_FALLBACK"
                        position_inference_status = "POSITION_DELTA_CONFIRMED_FILL"
                        fill_id = f"{order_id}:{utc_now()}:POSITION_DELTA"
                        record_fill(
                            str(db_path),
                            fill_id=fill_id,
                            order_id=order_id,
                            run_id=str(order.get("run_id") or ""),
                            symbol=symbol,
                            side=order_side,
                            filled_quantity=filled_qty,
                            fill_price=None,
                            filled_at=utc_now(),
                            source="POSITION_DELTA_FALLBACK",
                        )
                    else:
                        position_inference_status = "POSITION_DELTA_NOT_CONFIRMED"
            except Exception as pos_exc:
                position_inference_status = str(pos_exc)
            update_order_status(str(db_path), order_id, local_status, raw_status=str(snap.get("raw_status") or local_status))
            _update_execution_event_status(
                db_path,
                order_id=order_id,
                order_status=local_status,
                raw_response={"snapshot_refresh": snap, "fills": broker_fills if broker_truth_fill_flag else []},
                broker_truth_fill_flag=broker_truth_fill_flag,
                filled_qty=filled_qty,
                filled_avg_price=filled_avg_price,
            )
            _update_execution_position_audit(
                db_path,
                order_id=order_id,
                post_order_position_qty=position_qty,
                position_delta_qty=position_delta,
                fill_confirmation_source=fill_confirmation_source,
            )
            row.update(
                {
                    "refreshed_status": local_status,
                    "raw_status": str(snap.get("raw_status") or ""),
                    "age_minutes": age_minutes,
                    "filled_qty": filled_qty,
                    "filled_avg_price": filled_avg_price,
                    "broker_truth_fill_flag": broker_truth_fill_flag,
                    "post_order_position_qty": position_qty,
                    "position_delta_qty": position_delta,
                    "position_fill_inference_status": position_inference_status,
                    "fill_confirmation_source": fill_confirmation_source,
                    "position_baseline_available_flag": baseline_available,
                    "position_fill_fallback_eligible_flag": int(
                        baseline_available
                        and previous_status.upper() != "UNKNOWN"
                        and not broker_truth_fill_flag
                        and age_minutes >= position_min_age
                    ),
                }
            )
        except Exception as exc:
            row["refreshed_status"] = "REFRESH_FAILED"
            row["error"] = str(exc)
        rows.append(row)
    return pd.DataFrame(rows)


def run_task585(*, db_path: Path, env_file: Path) -> dict[str, pd.DataFrame]:
    load_runtime_env(env_file)
    initialize_store(str(db_path))
    _ensure_tables(db_path)
    decision = latest_runtime_decision(db_path)
    now = utc_now()
    execution_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    status_refresh = pd.DataFrame(
        [
            {
                "refresh_ts_utc": now,
                "order_id": "",
                "symbol": "",
                "previous_status": "",
                "refreshed_status": "NOT_RUN",
                "raw_status": "",
                "filled_qty": 0.0,
                "filled_avg_price": None,
                "broker_truth_fill_flag": 0,
                "error": "",
            }
        ]
    )

    kis_for_order: KISClient | None = None
    if str(os.environ.get("KIS_ENVIRONMENT", "paper")).strip().lower() == "paper":
        try:
            kis_for_order = KISClient.from_env()
            status_refresh = _refresh_active_local_orders(db_path, kis_for_order)
        except Exception as exc:
            status_refresh = pd.DataFrame(
                [
                    {
                        "refresh_ts_utc": utc_now(),
                        "order_id": "",
                        "symbol": "",
                        "previous_status": "",
                        "refreshed_status": "REFRESH_FAILED",
                        "raw_status": "",
                        "filled_qty": 0.0,
                        "filled_avg_price": None,
                        "broker_truth_fill_flag": 0,
                        "error": str(exc),
                    }
                ]
            )

    def skipped(reason: str) -> dict[str, Any]:
        return {
            "event_id": f"paper-exec-{now}-{reason}",
            "created_at": now,
            "decision_id": "" if decision is None else str(decision.get("decision_id") or ""),
            "client_order_id": "" if decision is None else str(decision.get("decision_id") or ""),
            "order_id": "",
            "lifecycle_id": "",
            "symbol": "" if decision is None else str(decision.get("symbol") or ""),
            "side": "" if decision is None else str(decision.get("side") or ""),
            "quantity": 0,
            "limit_price": 0.0 if decision is None else float(decision.get("limit_price") or 0.0),
            "order_status": "SKIPPED",
            "reason_code": reason,
            "raw_response": {},
            "broker_truth_fill_flag": 0,
            "filled_qty": 0.0,
            "filled_avg_price": None,
        }

    if decision is None:
        row = skipped("NO_RUNTIME_DECISION")
        _record_execution_event(db_path, row)
        execution_rows.append(row)
        failure_rows.append(row)
    elif str(decision.get("decision_status") or "") != "PAPER_ORDER_CANDIDATE":
        row = skipped("NO_PAPER_ORDER_CANDIDATE")
        _record_execution_event(db_path, row)
        execution_rows.append(row)
        failure_rows.append(row)
    elif str(os.environ.get("KIS_ENVIRONMENT", "paper")).strip().lower() != "paper":
        row = skipped("KIS_ENVIRONMENT_NOT_PAPER")
        _record_execution_event(db_path, row)
        execution_rows.append(row)
        failure_rows.append(row)
    else:
        symbol = str(decision.get("symbol") or "").upper()
        side = str(decision.get("side") or "").upper()
        quantity = int(float(decision.get("quantity") or 0))
        limit_price = float(decision.get("limit_price") or 0.0)
        decision_id = str(decision.get("decision_id") or "")
        active_blocker = _active_order_blocker(db_path, symbol)
        if active_blocker:
            row = skipped(active_blocker)
            _record_execution_event(db_path, row)
            execution_rows.append(row)
            failure_rows.append(row)
            active_blocker_handled = True
        else:
            active_blocker_handled = False
    if "active_blocker_handled" in locals() and active_blocker_handled:
        pass
    elif decision is not None and str(decision.get("decision_status") or "") == "PAPER_ORDER_CANDIDATE" and str(os.environ.get("KIS_ENVIRONMENT", "paper")).strip().lower() == "paper":
        symbol = str(decision.get("symbol") or "").upper()
        side = str(decision.get("side") or "").upper()
        quantity = int(float(decision.get("quantity") or 0))
        limit_price = float(decision.get("limit_price") or 0.0)
        decision_id = str(decision.get("decision_id") or "")
        run_id = record_trade_run_start(
            str(db_path),
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            started_at=now,
            environment="paper",
            result_status="ORDER_SUBMITTED",
        )
        try:
            kis = kis_for_order or KISClient.from_env()
            pre_order_position_qty, pre_order_position_status = _position_quantity_with_retry(kis, symbol)
            if _require_pre_order_position_baseline() and pre_order_position_qty is None:
                raise RuntimeError(f"PRE_ORDER_POSITION_BASELINE_BLOCKED:{pre_order_position_status}")
            order_id, raw_response = kis.submit_order_with_response(
                symbol=symbol,
                side=side,
                quantity=quantity,
                limit_price=limit_price,
            )
            submitted_at = utc_now()
            lifecycle_id = build_canonical_lifecycle_id(
                symbol=symbol,
                entry_timestamp=submitted_at,
                entry_order_id=order_id,
                trade_run_id=run_id,
            )
            record_order(
                str(db_path),
                order_id=order_id,
                run_id=run_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                intent_key=decision_id,
                submitted_at=submitted_at,
                status="SUBMITTED",
                environment="paper",
                raw_status="SUBMITTED",
            )
            emit_continuation_capture_event(
                db_path=str(db_path),
                environment="paper",
                run_id=run_id,
                event_type="PROBE_ENTRY",
                symbol=symbol,
                side=side,
                reason="paper_order_submitted_from_runtime_decision",
                order_id=order_id,
                result_status="ORDER_SUBMITTED",
                payload={
                    "canonical_lifecycle_id": lifecycle_id,
                    "event_timestamp": submitted_at,
                    "order_intent_id": decision_id,
                    "limit_price": limit_price,
                    "quantity": quantity,
                    "trade_run_id": run_id,
                },
            )
            broker_snapshot = kis.get_order_snapshot(order_id, symbol=symbol)
            mapped_status = str(broker_snapshot.get("mapped_status") or "PENDING").upper()
            if mapped_status not in {"SUBMITTED", "PENDING", "PARTIAL", "FILLED", "CANCELLED", "REJECTED", "UNKNOWN"}:
                mapped_status = "UNKNOWN"
            local_status = "PENDING" if mapped_status == "UNKNOWN" else mapped_status
            update_order_status(str(db_path), order_id, local_status, raw_status=str(broker_snapshot.get("raw_status") or mapped_status))
            filled_qty, filled_avg_price, broker_fills = _fills_from_snapshot(order_id, symbol, broker_snapshot)
            broker_truth_fill_flag = int(filled_qty > 0)
            if broker_truth_fill_flag:
                fill_id = f"{order_id}:{utc_now()}:ORDER_STATUS"
                fill_result = record_fill(
                    str(db_path),
                    fill_id=fill_id,
                    order_id=order_id,
                    run_id=run_id,
                    symbol=symbol,
                    side=side,
                    filled_quantity=filled_qty,
                    fill_price=filled_avg_price,
                    filled_at=utc_now(),
                    source="ORDER_STATUS",
                )
                if fill_result == FILL_INSERTED:
                    update_order_status(str(db_path), order_id, "FILLED", raw_status=str(broker_snapshot.get("raw_status") or "FILLED"))
                    local_status = "FILLED"
                    emit_continuation_capture_event(
                        db_path=str(db_path),
                        environment="paper",
                        run_id=run_id,
                        event_type="FILL_CONFIRMED",
                        symbol=symbol,
                        side=side,
                        reason="broker_truth_fill_confirmed",
                        order_id=order_id,
                        result_status="FILLED",
                        payload={
                            "canonical_lifecycle_id": lifecycle_id,
                            "fill_id": fill_id,
                            "filled_quantity": filled_qty,
                            "price": filled_avg_price,
                            "event_timestamp": utc_now(),
                            "order_intent_id": decision_id,
                            "trade_run_id": run_id,
                        },
                    )
            record_trade_run_finish(str(db_path), run_id, "FILLED" if local_status == "FILLED" else "ORDER_SUBMITTED", utc_now())
            row = {
                "event_id": f"paper-exec-{decision_id}-{order_id}",
                "created_at": submitted_at,
                "decision_id": decision_id,
                "client_order_id": decision_id,
                "order_id": order_id,
                "lifecycle_id": lifecycle_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "limit_price": limit_price,
                "order_status": local_status,
                "reason_code": "ORDER_SUBMITTED" if local_status != "FILLED" else "ORDER_FILLED",
                "raw_response": {"submit": raw_response, "snapshot": broker_snapshot, "fills": broker_fills},
                "broker_truth_fill_flag": broker_truth_fill_flag,
                "filled_qty": filled_qty,
                "filled_avg_price": filled_avg_price,
                "pre_order_position_qty": pre_order_position_qty,
                "post_order_position_qty": None,
                "position_delta_qty": None,
                "fill_confirmation_source": "ORDER_STATUS" if broker_truth_fill_flag else pre_order_position_status,
            }
            _record_execution_event(db_path, row)
            execution_rows.append(row)
        except Exception as exc:
            record_trade_run_finish(str(db_path), run_id, "FAILED", utc_now())
            row = {
                "event_id": f"paper-exec-{decision_id}-failed",
                "created_at": utc_now(),
                "decision_id": decision_id,
                "client_order_id": decision_id,
                "order_id": "",
                "lifecycle_id": "",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "limit_price": limit_price,
                "order_status": "FAILED",
                "reason_code": "KIS_ORDER_FAILED",
                "raw_response": {"error": str(exc)},
                "broker_truth_fill_flag": 0,
                "filled_qty": 0.0,
                "filled_avg_price": None,
            }
            _record_execution_event(db_path, row)
            execution_rows.append(row)
            failure_rows.append(row)

    execution_log = pd.DataFrame(execution_rows)
    lineage = _latest_lineage(db_path)
    lifecycle_events = read_table(db_path, "continuation_source_events", order_by="created_at", limit=50)
    failures = pd.DataFrame(failure_rows)
    final_status = str(execution_log.iloc[0]["order_status"]) if not execution_log.empty else "NO_LOG"
    decision_status = "ORDER_SUBMITTED_OR_TERMINAL_RECORDED" if final_status not in {"SKIPPED", "FAILED"} else f"ORDER_{final_status}"
    task_decision = pd.DataFrame(
        [
            {
                "task_id": "Task585",
                "task_name": "KIS Paper Order Execution And Lineage",
                "decision_status": decision_status,
                "order_status": final_status,
                "orders_submitted": int((execution_log.get("order_id", pd.Series(dtype=str)).astype(str) != "").sum()) if not execution_log.empty else 0,
                "broker_truth_fill_count": int(execution_log.get("broker_truth_fill_flag", pd.Series(dtype=int)).fillna(0).astype(int).sum()) if not execution_log.empty else 0,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
            }
        ]
    )
    artifacts = {
        "paper_order_execution_log.csv": execution_log,
        "paper_order_fill_lineage.csv": lineage,
        "paper_lifecycle_event_log.csv": lifecycle_events,
        "paper_order_failure_audit.csv": failures,
        "paper_active_order_status_refresh.csv": status_refresh,
        "task_585_decision.csv": task_decision,
    }
    for name, frame in artifacts.items():
        write_csv(REPORT_DIR, name, frame)
    write_task_report(
        REPORT_DIR,
        "task_585_kis_paper_order_execution.md",
        title="Task585 - KIS Paper Order Execution And Lineage",
        decision_summary=[
            f"decision_status={decision_status}",
            f"order_status={final_status}",
            "Only PAPER_ORDER_CANDIDATE decisions can submit KIS paper orders.",
            "Unfilled orders are not shown as fills.",
        ],
        quant_lines=[
            "The execution gate is downstream of Task584 and preserves decision_id as the local client_order_id.",
            "Broker truth fill is recorded only when KIS order status/fill data confirms filled quantity.",
            "Canonical lifecycle events are emitted after order submission and again after broker-confirmed fill, if present.",
        ],
        decision_maker_lines=[
            "이번 단계는 실제 모의계좌 주문 실행과 주문 계보 기록입니다.",
            "신호가 없으면 주문을 내지 않고, 주문이 나가도 체결 확인 전에는 체결로 표시하지 않습니다.",
            "프론트엔드에서는 decision_id에서 주문, 체결, lifecycle까지 이어지는 흐름을 확인할 수 있습니다.",
        ],
    )
    append_registry_rows(
        [
            {
                "task_id": "Task585",
                "title": "KIS Paper Order Execution And Lineage",
                "owner_team": "Execution & Risk",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "diagnostic-only",
                "data_readiness": "runtime-source",
                "parent_task": "Task584",
                "key_report": str(REPORT_DIR / "task_585_kis_paper_order_execution.md"),
                "key_decision": str(REPORT_DIR / "task_585_decision.csv"),
                "key_artifacts": str(REPORT_DIR),
                "validation_command": "python -m unittest tests.test_task585_kis_paper_order_execution",
                "notes": "Executes KIS paper orders only from runtime candidates and records lineage.",
            }
        ]
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--env-file", type=Path, default=Path("config/kis_paper.env"))
    args = parser.parse_args()
    artifacts = run_task585(db_path=args.db_path, env_file=args.env_file)
    print(artifacts["task_585_decision.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
