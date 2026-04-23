"""Execution Persistence / State Store.

This module stores minimal execution traces for one-shot runs:
- trade run lifecycle
- submitted order state
- confirmed fill records

Scope is intentionally minimal and append-friendly; advanced reconciliation and
portfolio accounting are deferred to future tasks.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta


ALLOWED_RUN_RESULTS = {
    "ORDER_SUBMITTED",
    "FILLED",
    "TIMEOUT",
    "FAILED",
    "SKIPPED_DUPLICATE",
    "SKIPPED_RECON_BLOCK",
}
ALLOWED_ORDER_STATUS = {"SUBMITTED", "PENDING", "FILLED", "TIMEOUT", "FAILED", "REJECTED"}
ALLOWED_FILL_SOURCES = {"ORDER_STATUS", "POSITION_DELTA_FALLBACK"}
FILL_INSERTED = "inserted"
FILL_DUPLICATE_IGNORED = "duplicate_ignored"
POSITION_EVENT_INSERTED = "inserted"
POSITION_EVENT_DUPLICATE_IGNORED = "duplicate_ignored"


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def initialize_store(db_path: str) -> None:
    con = _connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS trade_runs (
                run_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                requested_quantity REAL NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                result_status TEXT NOT NULL,
                environment TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                intent_key TEXT,
                submitted_at TEXT NOT NULL,
                status TEXT NOT NULL,
                raw_status TEXT,
                environment TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fills (
                fill_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                filled_quantity REAL NOT NULL,
                fill_price REAL,
                filled_at TEXT NOT NULL,
                source TEXT NOT NULL,
                dedupe_key TEXT
            )
            """
        )
        cur.execute(
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
        cur.execute(
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reconciliation_runs (
                reconciliation_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                max_severity TEXT NOT NULL,
                block_new_orders INTEGER NOT NULL,
                summary_text TEXT NOT NULL,
                raw_snapshot_json TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reconciliation_events (
                event_id TEXT PRIMARY KEY,
                reconciliation_id TEXT NOT NULL,
                symbol TEXT,
                local_order_id TEXT,
                broker_order_id TEXT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                local_status TEXT,
                broker_status TEXT,
                details_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        fill_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(fills)").fetchall()
        }
        order_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(orders)").fetchall()
        }
        if "intent_key" not in order_columns:
            cur.execute("ALTER TABLE orders ADD COLUMN intent_key TEXT")
        recon_run_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(reconciliation_runs)").fetchall()
        }
        if "max_severity" not in recon_run_columns:
            cur.execute("ALTER TABLE reconciliation_runs ADD COLUMN max_severity TEXT NOT NULL DEFAULT 'INFO'")
        recon_event_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(reconciliation_events)").fetchall()
        }
        if "severity" not in recon_event_columns:
            cur.execute("ALTER TABLE reconciliation_events ADD COLUMN severity TEXT NOT NULL DEFAULT 'INFO'")
        if "dedupe_key" not in fill_columns:
            cur.execute("ALTER TABLE fills ADD COLUMN dedupe_key TEXT")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_intent_key ON orders(intent_key)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recon_runs_started_at ON reconciliation_runs(started_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recon_events_recon_id ON reconciliation_events(reconciliation_id)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_fills_dedupe_key ON fills(dedupe_key)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_position_events_fill_id ON position_events(fill_id)")
        con.commit()
    finally:
        con.close()


def record_trade_run_start(
    db_path: str,
    *,
    symbol: str,
    side: str,
    requested_quantity: float,
    started_at: str,
    environment: str,
    result_status: str = "ORDER_SUBMITTED",
) -> str:
    if result_status not in ALLOWED_RUN_RESULTS:
        raise ValueError(f"invalid run result_status: {result_status}")
    run_id = f"run-{uuid.uuid4().hex[:16]}"
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO trade_runs (
                run_id, symbol, side, requested_quantity, started_at, finished_at, result_status, environment
            ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (run_id, symbol, side, requested_quantity, started_at, result_status, environment),
        )
        con.commit()
    finally:
        con.close()
    return run_id


def record_trade_run_finish(db_path: str, run_id: str, result_status: str, finished_at: str) -> None:
    if result_status not in ALLOWED_RUN_RESULTS:
        raise ValueError(f"invalid run result_status: {result_status}")
    con = _connect(db_path)
    try:
        con.execute(
            "UPDATE trade_runs SET finished_at = ?, result_status = ? WHERE run_id = ?",
            (finished_at, result_status, run_id),
        )
        con.commit()
    finally:
        con.close()


def record_order(
    db_path: str,
    *,
    order_id: str,
    run_id: str,
    symbol: str,
    side: str,
    quantity: float,
    intent_key: str | None = None,
    submitted_at: str,
    status: str,
    environment: str,
    raw_status: str | None = None,
) -> None:
    if status not in ALLOWED_ORDER_STATUS:
        raise ValueError(f"invalid order status: {status}")
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO orders (
                order_id, run_id, symbol, side, quantity, intent_key, submitted_at, status, raw_status, environment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, run_id, symbol, side, quantity, intent_key, submitted_at, status, raw_status, environment),
        )
        con.commit()
    finally:
        con.close()


def update_order_status(db_path: str, order_id: str, status: str, raw_status: str | None = None) -> None:
    if status not in ALLOWED_ORDER_STATUS:
        raise ValueError(f"invalid order status: {status}")
    con = _connect(db_path)
    try:
        con.execute(
            "UPDATE orders SET status = ?, raw_status = ? WHERE order_id = ?",
            (status, raw_status, order_id),
        )
        con.commit()
    finally:
        con.close()


def record_fill(
    db_path: str,
    *,
    fill_id: str,
    order_id: str,
    run_id: str,
    symbol: str,
    side: str,
    filled_quantity: float,
    fill_price: float | None,
    filled_at: str,
    source: str,
) -> str:
    if source not in ALLOWED_FILL_SOURCES:
        raise ValueError(f"invalid fill source: {source}")
    dedupe_key = build_fill_dedupe_key(
        order_id=order_id,
        symbol=symbol,
        side=side,
        filled_quantity=filled_quantity,
        fill_price=fill_price,
        source=source,
    )
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO fills (
                fill_id, order_id, run_id, symbol, side, filled_quantity, fill_price, filled_at, source, dedupe_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fill_id, order_id, run_id, symbol, side, filled_quantity, fill_price, filled_at, source, dedupe_key),
        )
        con.commit()
        if cur.rowcount == 0:
            return FILL_DUPLICATE_IGNORED
        return FILL_INSERTED
    finally:
        con.close()


def get_order(db_path: str, order_id: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def get_fills_for_order(db_path: str, order_id: str) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute("SELECT * FROM fills WHERE order_id = ? ORDER BY filled_at ASC", (order_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def build_fill_dedupe_key(
    *,
    order_id: str,
    symbol: str,
    side: str,
    filled_quantity: float,
    fill_price: float | None,
    source: str,
) -> str:
    """Build a deterministic key used to dedupe identical fill inserts."""
    price_part = "NONE" if fill_price is None else f"{fill_price:.8f}"
    qty_part = f"{filled_quantity:.8f}"
    normalized = f"{order_id}|{symbol}|{side}|{qty_part}|{price_part}|{source}"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
    return f"filldedupe-{digest}"


def list_recent_run_order_fill_rows(db_path: str, *, limit: int = 10) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    con = _connect(db_path)
    try:
        run_rows = con.execute(
            """
            SELECT run_id, started_at, finished_at, result_status, symbol, side, requested_quantity, environment
            FROM trade_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        result: list[dict] = []
        for run_row in run_rows:
            run = dict(run_row)
            order_row = con.execute(
                """
                SELECT order_id, status, quantity, intent_key, submitted_at, raw_status
                FROM orders
                WHERE run_id = ?
                ORDER BY submitted_at DESC
                LIMIT 1
                """,
                (run["run_id"],),
            ).fetchone()
            order = dict(order_row) if order_row is not None else None
            fill = None
            if order is not None:
                fill_row = con.execute(
                    """
                    SELECT fill_id, filled_quantity, fill_price, filled_at, source
                    FROM fills
                    WHERE order_id = ?
                    ORDER BY filled_at DESC
                    LIMIT 1
                    """,
                    (order["order_id"],),
                ).fetchone()
                fill = dict(fill_row) if fill_row is not None else None

            result.append(
                {
                    "run_id": run["run_id"],
                    "started_at": run["started_at"],
                    "finished_at": run["finished_at"],
                    "run_status": run["result_status"],
                    "symbol": run["symbol"],
                    "side": run["side"],
                    "requested_quantity": run["requested_quantity"],
                    "environment": run["environment"],
                    "order_id": None if order is None else order["order_id"],
                    "order_status": None if order is None else order["status"],
                    "order_raw_status": None if order is None else order["raw_status"],
                    "intent_key": None if order is None else order["intent_key"],
                    "fill_id": None if fill is None else fill["fill_id"],
                    "fill_quantity": None if fill is None else fill["filled_quantity"],
                    "fill_price": None if fill is None else fill["fill_price"],
                    "fill_source": None if fill is None else fill["source"],
                    "fallback_used": bool(fill is not None and fill["source"] == "POSITION_DELTA_FALLBACK"),
                }
            )
        return result
    finally:
        con.close()


def list_open_orders(db_path: str) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            """
            SELECT order_id, run_id, symbol, side, quantity, submitted_at, status, raw_status, environment
            FROM orders
            WHERE status IN ('SUBMITTED', 'PENDING')
            ORDER BY submitted_at ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def list_local_filled_order_ids(db_path: str, *, symbol: str | None = None) -> set[str]:
    con = _connect(db_path)
    try:
        if symbol is None:
            rows = con.execute("SELECT DISTINCT order_id FROM fills").fetchall()
        else:
            rows = con.execute("SELECT DISTINCT order_id FROM fills WHERE symbol = ?", (symbol,)).fetchall()
        return {str(row["order_id"]) for row in rows if row["order_id"] not in (None, "")}
    finally:
        con.close()


def build_order_intent_key(
    *,
    symbol: str,
    side: str,
    intended_price: float,
    quantity: float,
    strategy_id: str | None = None,
) -> str:
    strategy = (strategy_id or "default").strip() or "default"
    canonical = (
        f"{symbol.strip().upper()}|{side.strip().upper()}|{float(intended_price):.4f}|"
        f"{float(quantity):.8f}|{strategy}"
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"intent-{digest}"


def has_blocking_order_intent(
    db_path: str,
    *,
    intent_key: str,
    blocking_statuses: tuple[str, ...] = ("SUBMITTED", "PENDING"),
) -> bool:
    placeholders = ", ".join("?" for _ in blocking_statuses)
    params: tuple[str, ...] = (intent_key,) + blocking_statuses
    con = _connect(db_path)
    try:
        row = con.execute(
            f"SELECT 1 FROM orders WHERE intent_key = ? AND status IN ({placeholders}) LIMIT 1",
            params,
        ).fetchone()
        return row is not None
    finally:
        con.close()


def has_recent_order_intent(
    db_path: str,
    *,
    intent_key: str,
    within_seconds: int,
    now_iso: str,
) -> bool:
    if within_seconds <= 0:
        return False
    now_ts = _parse_iso(now_iso)
    threshold = now_ts - timedelta(seconds=within_seconds)
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT submitted_at FROM orders WHERE intent_key = ? ORDER BY submitted_at DESC LIMIT 20",
            (intent_key,),
        ).fetchall()
        for row in rows:
            submitted_at = row["submitted_at"]
            if submitted_at is None:
                continue
            submitted_ts = _parse_iso(submitted_at)
            if submitted_ts >= threshold:
                return True
        return False
    finally:
        con.close()


def _parse_iso(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def get_position(db_path: str, symbol: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute("SELECT * FROM positions WHERE symbol = ?", (symbol,)).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def list_positions(db_path: str) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute("SELECT symbol, side, quantity, avg_price, updated_at FROM positions ORDER BY symbol ASC").fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def apply_fill_to_position(
    *,
    old_quantity: float,
    old_avg_price: float,
    fill_side: str,
    fill_quantity: float,
    fill_price: float | None,
) -> tuple[float, float]:
    """Apply one fill to a LONG-only position model and return (quantity, avg_price)."""
    if fill_quantity <= 0:
        raise ValueError("fill_quantity must be positive")

    side = fill_side.strip().upper()
    if side == "BUY":
        price = old_avg_price if fill_price is None and old_quantity > 0 else (0.0 if fill_price is None else fill_price)
        new_quantity = old_quantity + fill_quantity
        if new_quantity <= 0:
            raise ValueError("resulting position quantity must be positive for BUY")
        new_avg_price = ((old_quantity * old_avg_price) + (fill_quantity * price)) / new_quantity
        return new_quantity, new_avg_price

    if side == "SELL":
        # Minimal SELL handling for scope control: reduce quantity only.
        new_quantity = old_quantity - fill_quantity
        if new_quantity < 0:
            new_quantity = 0.0
        if new_quantity == 0:
            return 0.0, 0.0
        return new_quantity, old_avg_price

    raise ValueError(f"unsupported fill side: {fill_side}")


def upsert_position(
    db_path: str,
    *,
    symbol: str,
    side: str,
    quantity: float,
    avg_price: float,
    updated_at: str,
) -> None:
    if quantity < 0:
        raise ValueError("quantity must be non-negative")
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO positions (symbol, side, quantity, avg_price, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                side = excluded.side,
                quantity = excluded.quantity,
                avg_price = excluded.avg_price,
                updated_at = excluded.updated_at
            """,
            (symbol, side, quantity, avg_price, updated_at),
        )
        con.commit()
    finally:
        con.close()


def record_position_event(
    db_path: str,
    *,
    run_id: str,
    order_id: str,
    fill_id: str,
    symbol: str,
    side: str,
    fill_qty: float,
    fill_price: float | None,
    position_qty_after: float,
    avg_price_after: float,
    created_at: str,
) -> str:
    event_id = f"pevt-{uuid.uuid4().hex[:16]}"
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO position_events (
                event_id,
                run_id,
                order_id,
                fill_id,
                symbol,
                side,
                fill_qty,
                fill_price,
                position_qty_after,
                avg_price_after,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                run_id,
                order_id,
                fill_id,
                symbol,
                side,
                fill_qty,
                fill_price,
                position_qty_after,
                avg_price_after,
                created_at,
            ),
        )
        con.commit()
        if cur.rowcount == 0:
            return POSITION_EVENT_DUPLICATE_IGNORED
        return POSITION_EVENT_INSERTED
    finally:
        con.close()


def list_position_events_for_symbol(db_path: str, symbol: str) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            """
            SELECT event_id, run_id, order_id, fill_id, symbol, side, fill_qty, fill_price, position_qty_after, avg_price_after, created_at
            FROM position_events
            WHERE symbol = ?
            ORDER BY created_at ASC
            """,
            (symbol,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def record_reconciliation_run(
    db_path: str,
    *,
    run_id: str,
    started_at: str,
    finished_at: str,
    status: str,
    max_severity: str,
    block_new_orders: bool,
    summary_text: str,
    raw_snapshot_json: str | None = None,
) -> str:
    reconciliation_id = f"recon-{uuid.uuid4().hex[:16]}"
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO reconciliation_runs (
                reconciliation_id, run_id, started_at, finished_at, status, max_severity, block_new_orders, summary_text, raw_snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reconciliation_id,
                run_id,
                started_at,
                finished_at,
                status,
                max_severity,
                1 if block_new_orders else 0,
                summary_text,
                raw_snapshot_json,
            ),
        )
        con.commit()
    finally:
        con.close()
    return reconciliation_id


def record_reconciliation_event(
    db_path: str,
    *,
    reconciliation_id: str,
    symbol: str | None,
    local_order_id: str | None,
    broker_order_id: str | None,
    event_type: str,
    severity: str,
    local_status: str | None,
    broker_status: str | None,
    details: dict | None,
    created_at: str,
) -> str:
    event_id = f"revent-{uuid.uuid4().hex[:16]}"
    details_json = None if details is None else json.dumps(details, ensure_ascii=True, sort_keys=True)
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO reconciliation_events (
                event_id, reconciliation_id, symbol, local_order_id, broker_order_id, event_type, severity,
                local_status, broker_status, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                reconciliation_id,
                symbol,
                local_order_id,
                broker_order_id,
                event_type,
                severity,
                local_status,
                broker_status,
                details_json,
                created_at,
            ),
        )
        con.commit()
    finally:
        con.close()
    return event_id


def list_recent_reconciliation_runs(db_path: str, *, limit: int = 10) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    con = _connect(db_path)
    try:
        rows = con.execute(
            """
            SELECT
                rr.reconciliation_id,
                rr.run_id,
                rr.started_at,
                rr.finished_at,
                rr.status,
                rr.max_severity,
                rr.block_new_orders,
                rr.summary_text,
                (
                    SELECT COUNT(*)
                    FROM reconciliation_events re
                    WHERE re.reconciliation_id = rr.reconciliation_id
                ) AS event_count
            FROM reconciliation_runs rr
            ORDER BY rr.started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def list_reconciliation_events(db_path: str, reconciliation_id: str) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            """
            SELECT event_id, reconciliation_id, symbol, local_order_id, broker_order_id, event_type,
                   severity, local_status, broker_status, details_json, created_at
            FROM reconciliation_events
            WHERE reconciliation_id = ?
            ORDER BY created_at ASC
            """,
            (reconciliation_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()
