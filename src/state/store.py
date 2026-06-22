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
    "CANCELLED",
    "TIMEOUT",
    "UNKNOWN",
    "FAILED",
    "SKIPPED_NO_SIGNAL",
    "SKIPPED_NO_RUNTIME_SNAPSHOT",
    "SKIPPED_DUPLICATE",
    "SKIPPED_RECON_BLOCK",
}
ALLOWED_ORDER_STATUS = {
    "SUBMITTED",
    "PENDING",
    "PARTIAL",
    "FILLED",
    "CANCEL_REQUESTED",
    "CANCEL_IN_PROGRESS",
    "CANCELLED",
    "EXPIRED",
    "TIMEOUT",
    "UNKNOWN",
    "FAILED",
    "REJECTED",
}
ALLOWED_FILL_SOURCES = {"ORDER_STATUS", "POSITION_DELTA_FALLBACK"}
ALLOWED_CONTINUATION_EVENT_TYPES = {
    "ENTRY",
    "ADD",
    "SCALE",
    "REDUCE",
    "EXIT",
    "SETUP_DETECTED",
    "PROBE_ENTRY",
    "ADD_ATTEMPT",
    "ADD_CONFIRMED",
    "SIZE_INCREASE",
    "PERSISTENCE_CONFIRMED",
    "FRAGILITY_WARNING",
    "REDUCTION_TRIGGER",
    "EXIT_TRIGGER",
    "INVALIDATION",
}
ALLOWED_CONTINUATION_EVENT_SOURCES = {
    "SOURCE_CAPTURED",
    "SESSION_DERIVED",
    "REPLAY_DERIVED",
}
ALLOWED_CAPTURE_MODES = {"paper_runtime", "historical_backfill"}
FILL_INSERTED = "inserted"
FILL_DUPLICATE_IGNORED = "duplicate_ignored"
POSITION_EVENT_INSERTED = "inserted"
POSITION_EVENT_DUPLICATE_IGNORED = "duplicate_ignored"
CONTINUATION_EVENT_INSERTED = "inserted"
CONTINUATION_EVENT_DUPLICATE_IGNORED = "duplicate_ignored"


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 5000")
    try:
        con.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        pass
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS continuation_setups (
                setup_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                session_date TEXT NOT NULL,
                setup_timestamp TEXT NOT NULL,
                setup_origin TEXT NOT NULL,
                signal_event_id TEXT,
                risk_decision_id TEXT,
                capture_mode TEXT NOT NULL DEFAULT 'paper_runtime',
                capture_batch_id TEXT,
                source_dataset_version TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS continuation_lifecycles (
                lifecycle_id TEXT PRIMARY KEY,
                setup_id TEXT NOT NULL,
                parent_lifecycle_id TEXT,
                symbol TEXT NOT NULL,
                session_date TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                identity_origin TEXT NOT NULL,
                identity_confidence REAL NOT NULL,
                capture_mode TEXT NOT NULL DEFAULT 'paper_runtime',
                capture_batch_id TEXT,
                source_dataset_version TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS continuation_events (
                event_id TEXT PRIMARY KEY,
                continuation_id TEXT NOT NULL,
                setup_id TEXT,
                run_id TEXT,
                order_id TEXT,
                symbol TEXT NOT NULL,
                session_date TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_source TEXT NOT NULL,
                replay_state TEXT,
                state_label TEXT,
                participation_quality_label TEXT,
                size_multiplier REAL,
                add_depth INTEGER NOT NULL DEFAULT 0,
                scale_depth INTEGER NOT NULL DEFAULT 0,
                continuation_risk_score REAL,
                expansion_score REAL,
                fragility_score REAL,
                lineage_quality TEXT,
                replay_fidelity TEXT,
                details_json TEXT,
                created_at TEXT NOT NULL,
                dedupe_key TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS continuation_source_events (
                source_event_id TEXT PRIMARY KEY,
                lifecycle_id TEXT NOT NULL,
                setup_id TEXT NOT NULL,
                parent_lifecycle_id TEXT,
                signal_event_id TEXT,
                risk_decision_id TEXT,
                order_intent_id TEXT,
                order_id TEXT,
                fill_id TEXT,
                reconciliation_id TEXT,
                trade_run_id TEXT,
                symbol TEXT NOT NULL,
                session_date TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_source TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                state_label TEXT,
                participation_quality_label TEXT,
                expansion_score REAL NOT NULL,
                fragility_score REAL NOT NULL,
                continuation_risk_score REAL NOT NULL,
                size_multiplier REAL NOT NULL,
                add_depth INTEGER NOT NULL,
                scale_depth INTEGER NOT NULL,
                persistence_depth INTEGER NOT NULL,
                capture_mode TEXT NOT NULL DEFAULT 'paper_runtime',
                capture_batch_id TEXT,
                source_dataset_version TEXT,
                details_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS continuation_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                lifecycle_id TEXT NOT NULL,
                setup_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                snapshot_timestamp TEXT NOT NULL,
                replay_state TEXT NOT NULL,
                size_multiplier REAL NOT NULL,
                add_depth INTEGER NOT NULL,
                scale_depth INTEGER NOT NULL,
                persistence_depth INTEGER NOT NULL,
                weakening_flag INTEGER NOT NULL,
                invalidated_flag INTEGER NOT NULL,
                capture_mode TEXT NOT NULL DEFAULT 'paper_runtime',
                capture_batch_id TEXT,
                source_dataset_version TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnostic_runtime_heartbeats (
                idempotency_key TEXT PRIMARY KEY,
                cadence TEXT NOT NULL,
                heartbeat_bucket_ts TEXT NOT NULL,
                state_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                should_execute INTEGER NOT NULL,
                reason_codes_json TEXT NOT NULL,
                allowed_operations_json TEXT NOT NULL,
                forbidden_operations_json TEXT NOT NULL,
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
        continuation_event_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(continuation_events)").fetchall()
        }
        continuation_source_event_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(continuation_source_events)").fetchall()
        }
        continuation_setup_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(continuation_setups)").fetchall()
        }
        continuation_lifecycle_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(continuation_lifecycles)").fetchall()
        }
        continuation_snapshot_columns = {
            row["name"] for row in cur.execute("PRAGMA table_info(continuation_snapshots)").fetchall()
        }
        if "severity" not in recon_event_columns:
            cur.execute("ALTER TABLE reconciliation_events ADD COLUMN severity TEXT NOT NULL DEFAULT 'INFO'")
        if "dedupe_key" not in fill_columns:
            cur.execute("ALTER TABLE fills ADD COLUMN dedupe_key TEXT")
        if "dedupe_key" not in continuation_event_columns:
            cur.execute("ALTER TABLE continuation_events ADD COLUMN dedupe_key TEXT")
        if "details_json" not in continuation_source_event_columns:
            cur.execute("ALTER TABLE continuation_source_events ADD COLUMN details_json TEXT")
        if "order_intent_id" not in continuation_source_event_columns:
            cur.execute("ALTER TABLE continuation_source_events ADD COLUMN order_intent_id TEXT")
        if "reconciliation_id" not in continuation_source_event_columns:
            cur.execute("ALTER TABLE continuation_source_events ADD COLUMN reconciliation_id TEXT")
        if "trade_run_id" not in continuation_source_event_columns:
            cur.execute("ALTER TABLE continuation_source_events ADD COLUMN trade_run_id TEXT")
        for table_name, columns in (
            ("continuation_setups", continuation_setup_columns),
            ("continuation_lifecycles", continuation_lifecycle_columns),
            ("continuation_source_events", continuation_source_event_columns),
            ("continuation_snapshots", continuation_snapshot_columns),
        ):
            if "capture_mode" not in columns:
                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN capture_mode TEXT NOT NULL DEFAULT 'paper_runtime'")
            if "capture_batch_id" not in columns:
                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN capture_batch_id TEXT")
            if "source_dataset_version" not in columns:
                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN source_dataset_version TEXT")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_intent_key ON orders(intent_key)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_diagnostic_runtime_heartbeats_cadence_bucket "
            "ON diagnostic_runtime_heartbeats(cadence, heartbeat_bucket_ts)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_diagnostic_runtime_heartbeats_cadence_created "
            "ON diagnostic_runtime_heartbeats(cadence, created_at)"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduler_leases (
                lease_key TEXT PRIMARY KEY,
                cadence TEXT NOT NULL,
                bucket_ts TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                lease_token TEXT NOT NULL,
                state_hash TEXT NOT NULL,
                acquired_at TEXT NOT NULL,
                heartbeat_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                released_at TEXT,
                status TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_order_intents (
                intent_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                runtime_decision_id TEXT NOT NULL,
                authority_id TEXT NOT NULL,
                lineage_hash TEXT NOT NULL,
                scheduler_lease_token TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                limit_price REAL NOT NULL,
                broker_supports_client_order_id INTEGER NOT NULL,
                broker_client_order_id TEXT,
                state TEXT NOT NULL,
                broker_order_id TEXT,
                raw_response_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_authority_evidence_ledger (
                authority_hash TEXT PRIMARY KEY,
                authority_id TEXT NOT NULL,
                runtime_decision_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_paper_order_intents_state "
            "ON paper_order_intents(state, updated_at)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_authority_evidence_runtime "
            "ON runtime_authority_evidence_ledger(runtime_decision_id, created_at)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_scheduler_leases_status "
            "ON scheduler_leases(status, expires_at)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_scheduler_leases_bucket "
            "ON scheduler_leases(cadence, bucket_ts)"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recon_runs_started_at ON reconciliation_runs(started_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recon_events_recon_id ON reconciliation_events(reconciliation_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cont_setups_symbol_session ON continuation_setups(symbol, session_date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cont_setups_capture_mode_batch ON continuation_setups(capture_mode, capture_batch_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cont_lifecycle_setup_started ON continuation_lifecycles(setup_id, started_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cont_lifecycles_capture_mode_batch ON continuation_lifecycles(capture_mode, capture_batch_id)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_continuation_events_continuation_id "
            "ON continuation_events(continuation_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_continuation_events_setup_id "
            "ON continuation_events(setup_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_continuation_events_symbol "
            "ON continuation_events(symbol, session_date, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_source_events_lifecycle_ts "
            "ON continuation_source_events(lifecycle_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_source_events_setup_ts "
            "ON continuation_source_events(setup_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_source_events_trade_run "
            "ON continuation_source_events(trade_run_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_source_events_order_id "
            "ON continuation_source_events(order_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_source_events_fill_id "
            "ON continuation_source_events(fill_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_source_events_capture_mode_batch "
            "ON continuation_source_events(capture_mode, capture_batch_id, event_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_snapshots_lifecycle_ts "
            "ON continuation_snapshots(lifecycle_id, snapshot_timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_cont_snapshots_capture_mode_batch "
            "ON continuation_snapshots(capture_mode, capture_batch_id, snapshot_timestamp)"
        )
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_fills_dedupe_key ON fills(dedupe_key)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_position_events_fill_id ON position_events(fill_id)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_continuation_events_dedupe_key ON continuation_events(dedupe_key)")
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


def build_continuation_event_dedupe_key(
    *,
    continuation_id: str,
    symbol: str,
    session_date: str,
    event_type: str,
    event_timestamp: str,
    event_source: str,
    setup_id: str | None = None,
) -> str:
    setup_part = "" if setup_id is None else setup_id.strip()
    normalized = (
        f"{continuation_id.strip()}|{setup_part}|{symbol.strip().upper()}|{session_date.strip()}|"
        f"{event_type.strip().upper()}|{event_timestamp.strip()}|{event_source.strip().upper()}"
    )
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
    return f"contevt-{digest}"


def build_continuation_event_id(
    *,
    continuation_id: str,
    event_type: str,
    event_timestamp: str,
    dedupe_key: str | None = None,
) -> str:
    canonical_key = dedupe_key or build_continuation_event_dedupe_key(
        continuation_id=continuation_id,
        symbol="",
        session_date="",
        event_type=event_type,
        event_timestamp=event_timestamp,
        event_source="",
        setup_id=None,
    )
    seed = f"{continuation_id.strip()}|{event_type.strip().upper()}|{event_timestamp.strip()}|{canonical_key}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    return f"cevt-{digest}"


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


def record_continuation_event(
    db_path: str,
    *,
    continuation_id: str,
    symbol: str,
    session_date: str,
    event_timestamp: str,
    event_type: str,
    event_source: str,
    event_id: str | None = None,
    setup_id: str | None = None,
    run_id: str | None = None,
    order_id: str | None = None,
    replay_state: str | None = None,
    state_label: str | None = None,
    participation_quality_label: str | None = None,
    size_multiplier: float | None = None,
    add_depth: int = 0,
    scale_depth: int = 0,
    continuation_risk_score: float | None = None,
    expansion_score: float | None = None,
    fragility_score: float | None = None,
    lineage_quality: str | None = None,
    replay_fidelity: str | None = None,
    details: dict | None = None,
    created_at: str | None = None,
) -> str:
    if event_type not in ALLOWED_CONTINUATION_EVENT_TYPES:
        raise ValueError(f"invalid continuation event_type: {event_type}")
    if event_source not in ALLOWED_CONTINUATION_EVENT_SOURCES:
        raise ValueError(f"invalid continuation event_source: {event_source}")
    dedupe_key = build_continuation_event_dedupe_key(
        continuation_id=continuation_id,
        setup_id=setup_id,
        symbol=symbol,
        session_date=session_date,
        event_type=event_type,
        event_timestamp=event_timestamp,
        event_source=event_source,
    )
    stored_event_id = event_id or build_continuation_event_id(
        continuation_id=continuation_id,
        event_type=event_type,
        event_timestamp=event_timestamp,
        dedupe_key=dedupe_key,
    )
    stored_created_at = created_at or event_timestamp
    details_json = None if details is None else json.dumps(details, ensure_ascii=True, sort_keys=True)
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO continuation_events (
                event_id,
                continuation_id,
                setup_id,
                run_id,
                order_id,
                symbol,
                session_date,
                event_timestamp,
                event_type,
                event_source,
                replay_state,
                state_label,
                participation_quality_label,
                size_multiplier,
                add_depth,
                scale_depth,
                continuation_risk_score,
                expansion_score,
                fragility_score,
                lineage_quality,
                replay_fidelity,
                details_json,
                created_at,
                dedupe_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stored_event_id,
                continuation_id,
                setup_id,
                run_id,
                order_id,
                symbol,
                session_date,
                event_timestamp,
                event_type,
                event_source,
                replay_state,
                state_label,
                participation_quality_label,
                size_multiplier,
                int(add_depth),
                int(scale_depth),
                continuation_risk_score,
                expansion_score,
                fragility_score,
                lineage_quality,
                replay_fidelity,
                details_json,
                stored_created_at,
                dedupe_key,
            ),
        )
        con.commit()
        if cur.rowcount == 0:
            return CONTINUATION_EVENT_DUPLICATE_IGNORED
        return CONTINUATION_EVENT_INSERTED
    finally:
        con.close()


def list_continuation_events(
    db_path: str,
    *,
    continuation_id: str | None = None,
    setup_id: str | None = None,
    symbol: str | None = None,
    limit: int = 500,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    clauses: list[str] = []
    params: list[object] = []
    if continuation_id is not None:
        clauses.append("continuation_id = ?")
        params.append(continuation_id)
    if setup_id is not None:
        clauses.append("setup_id = ?")
        params.append(setup_id)
    if symbol is not None:
        clauses.append("symbol = ?")
        params.append(symbol)
    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)
    params.append(limit)
    con = _connect(db_path)
    try:
        rows = con.execute(
            f"""
            SELECT
                event_id,
                continuation_id,
                setup_id,
                run_id,
                order_id,
                symbol,
                session_date,
                event_timestamp,
                event_type,
                event_source,
                replay_state,
                state_label,
                participation_quality_label,
                size_multiplier,
                add_depth,
                scale_depth,
                continuation_risk_score,
                expansion_score,
                fragility_score,
                lineage_quality,
                replay_fidelity,
                details_json,
                created_at,
                dedupe_key
            FROM continuation_events
            {where_sql}
            ORDER BY event_timestamp ASC, created_at ASC, event_id ASC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def list_open_orders(db_path: str) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            """
            SELECT order_id, run_id, symbol, side, quantity, submitted_at, status, raw_status, environment
            FROM orders
            WHERE status IN ('SUBMITTED', 'PENDING', 'PARTIAL', 'CANCEL_REQUESTED', 'CANCEL_IN_PROGRESS')
            ORDER BY submitted_at ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def has_order_with_status(db_path: str, *, status: str) -> bool:
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT 1 FROM orders WHERE status = ? LIMIT 1",
            (status,),
        ).fetchone()
        return row is not None
    finally:
        con.close()


def get_latest_diagnostic_state_hash(
    db_path: str,
    *,
    cadence: str,
    heartbeat_bucket_ts: str | None = None,
) -> str | None:
    con = _connect(db_path)
    try:
        if heartbeat_bucket_ts is None:
            row = con.execute(
                """
                SELECT state_hash
                FROM diagnostic_runtime_heartbeats
                WHERE cadence = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (cadence,),
            ).fetchone()
        else:
            row = con.execute(
                """
                SELECT state_hash
                FROM diagnostic_runtime_heartbeats
                WHERE cadence = ? AND heartbeat_bucket_ts = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (cadence, heartbeat_bucket_ts),
            ).fetchone()
        return None if row is None else str(row["state_hash"])
    finally:
        con.close()


def record_diagnostic_runtime_heartbeat(
    db_path: str,
    *,
    idempotency_key: str,
    cadence: str,
    heartbeat_bucket_ts: str,
    state_hash: str,
    status: str,
    should_execute: bool,
    reason_codes: tuple[str, ...],
    allowed_operations: tuple[str, ...],
    forbidden_operations: tuple[str, ...],
    created_at: str,
) -> bool:
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO diagnostic_runtime_heartbeats (
                idempotency_key, cadence, heartbeat_bucket_ts, state_hash, status, should_execute,
                reason_codes_json, allowed_operations_json, forbidden_operations_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idempotency_key,
                cadence,
                heartbeat_bucket_ts,
                state_hash,
                status,
                1 if should_execute else 0,
                json.dumps(list(reason_codes), sort_keys=True, ensure_ascii=True),
                json.dumps(list(allowed_operations), sort_keys=True, ensure_ascii=True),
                json.dumps(list(forbidden_operations), sort_keys=True, ensure_ascii=True),
                created_at,
            ),
        )
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()


def _require_store_value(value: str, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def acquire_scheduler_lease(
    db_path: str,
    *,
    lease_key: str,
    cadence: str,
    bucket_ts: str,
    owner_id: str,
    state_hash: str,
    now: str,
    ttl_seconds: int = 300,
) -> dict:
    """Atomically acquire or steal an expired scheduler lease.

    The timestamp strings must be UTC ISO-8601 values so lexical comparison
    matches chronological ordering.
    """

    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    lease_key = _require_store_value(lease_key, "lease_key")
    cadence = _require_store_value(cadence, "cadence")
    bucket_ts = _require_store_value(bucket_ts, "bucket_ts")
    owner_id = _require_store_value(owner_id, "owner_id")
    state_hash = _require_store_value(state_hash, "state_hash")
    now = _require_store_value(now, "now")
    expires_at = (datetime.fromisoformat(now.replace("Z", "+00:00")) + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z")
    lease_token = f"lease-{uuid.uuid4().hex}"

    con = _connect(db_path)
    try:
        con.isolation_level = None
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            """
            SELECT lease_key, owner_id, lease_token, expires_at, released_at, status
            FROM scheduler_leases
            WHERE lease_key = ?
            """,
            (lease_key,),
        ).fetchone()
        if row is not None and row["status"] == "ACTIVE" and not row["released_at"] and str(row["expires_at"]) > now:
            con.execute("COMMIT")
            return {
                "acquired": False,
                "lease_key": lease_key,
                "lease_token": str(row["lease_token"]),
                "owner_id": str(row["owner_id"]),
                "reason": "LEASE_HELD_BY_ACTIVE_OWNER",
                "expires_at": str(row["expires_at"]),
            }
        if row is None:
            con.execute(
                """
                INSERT INTO scheduler_leases (
                    lease_key, cadence, bucket_ts, owner_id, lease_token, state_hash,
                    acquired_at, heartbeat_at, expires_at, released_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'ACTIVE')
                """,
                (lease_key, cadence, bucket_ts, owner_id, lease_token, state_hash, now, now, expires_at),
            )
            reason = "LEASE_ACQUIRED"
        else:
            con.execute(
                """
                UPDATE scheduler_leases
                SET cadence = ?, bucket_ts = ?, owner_id = ?, lease_token = ?, state_hash = ?,
                    acquired_at = ?, heartbeat_at = ?, expires_at = ?, released_at = NULL, status = 'ACTIVE'
                WHERE lease_key = ?
                """,
                (cadence, bucket_ts, owner_id, lease_token, state_hash, now, now, expires_at, lease_key),
            )
            reason = "EXPIRED_OR_RELEASED_LEASE_STOLEN"
        con.execute("COMMIT")
        return {
            "acquired": True,
            "lease_key": lease_key,
            "lease_token": lease_token,
            "owner_id": owner_id,
            "reason": reason,
            "expires_at": expires_at,
        }
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def heartbeat_scheduler_lease(
    db_path: str,
    *,
    lease_key: str,
    lease_token: str,
    now: str,
    ttl_seconds: int = 300,
) -> bool:
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    lease_key = _require_store_value(lease_key, "lease_key")
    lease_token = _require_store_value(lease_token, "lease_token")
    now = _require_store_value(now, "now")
    expires_at = (datetime.fromisoformat(now.replace("Z", "+00:00")) + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z")
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            UPDATE scheduler_leases
            SET heartbeat_at = ?, expires_at = ?
            WHERE lease_key = ? AND lease_token = ? AND status = 'ACTIVE'
              AND released_at IS NULL AND expires_at > ?
            """,
            (now, expires_at, lease_key, lease_token, now),
        )
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def release_scheduler_lease(
    db_path: str,
    *,
    lease_key: str,
    lease_token: str,
    released_at: str,
) -> bool:
    lease_key = _require_store_value(lease_key, "lease_key")
    lease_token = _require_store_value(lease_token, "lease_token")
    released_at = _require_store_value(released_at, "released_at")
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            UPDATE scheduler_leases
            SET released_at = ?, status = 'RELEASED'
            WHERE lease_key = ? AND lease_token = ? AND status = 'ACTIVE'
            """,
            (released_at, lease_key, lease_token),
        )
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def get_scheduler_lease(db_path: str, *, lease_key: str) -> dict | None:
    lease_key = _require_store_value(lease_key, "lease_key")
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT lease_key, cadence, bucket_ts, owner_id, lease_token, state_hash,
                   acquired_at, heartbeat_at, expires_at, released_at, status
            FROM scheduler_leases
            WHERE lease_key = ?
            """,
            (lease_key,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def validate_scheduler_lease_token(
    db_path: str,
    *,
    lease_key: str,
    lease_token: str,
    now: str,
) -> bool:
    lease_key = _require_store_value(lease_key, "lease_key")
    lease_token = _require_store_value(lease_token, "lease_token")
    now = _require_store_value(now, "now")
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT 1
            FROM scheduler_leases
            WHERE lease_key = ? AND lease_token = ? AND status = 'ACTIVE'
              AND released_at IS NULL AND expires_at > ?
            LIMIT 1
            """,
            (lease_key, lease_token, now),
        ).fetchone()
        return row is not None
    finally:
        con.close()


def record_runtime_authority_evidence(
    db_path: str,
    *,
    authority_hash: str,
    authority_id: str,
    runtime_decision_id: str,
    payload: dict,
    created_at: str,
) -> bool:
    authority_hash = _require_store_value(authority_hash, "authority_hash")
    authority_id = _require_store_value(authority_id, "authority_id")
    runtime_decision_id = _require_store_value(runtime_decision_id, "runtime_decision_id")
    created_at = _require_store_value(created_at, "created_at")
    payload_json = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    con = _connect(db_path)
    try:
        existing = con.execute(
            "SELECT payload_json FROM runtime_authority_evidence_ledger WHERE authority_hash = ?",
            (authority_hash,),
        ).fetchone()
        if existing is not None:
            if str(existing["payload_json"]) != payload_json:
                raise ValueError("authority evidence hash collision or mutation attempt")
            return False
        con.execute(
            """
            INSERT INTO runtime_authority_evidence_ledger (
                authority_hash, authority_id, runtime_decision_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (authority_hash, authority_id, runtime_decision_id, payload_json, created_at),
        )
        con.commit()
        return True
    finally:
        con.close()


def get_runtime_authority_evidence(db_path: str, *, authority_hash: str) -> dict | None:
    authority_hash = _require_store_value(authority_hash, "authority_hash")
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT authority_hash, authority_id, runtime_decision_id, payload_json, created_at
            FROM runtime_authority_evidence_ledger
            WHERE authority_hash = ?
            """,
            (authority_hash,),
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["payload"] = json.loads(str(row["payload_json"]))
        return result
    finally:
        con.close()


PAPER_ORDER_INTENT_TRANSITIONS = {
    "CREATED": {"SUBMITTING", "BLOCKED"},
    "SUBMITTING": {"SUBMITTED_LOCAL_RECORDED", "UNKNOWN", "BLOCKED"},
    "SUBMITTED_LOCAL_RECORDED": {"RECONCILED", "UNKNOWN", "BLOCKED"},
    "UNKNOWN": {"RECONCILED", "BLOCKED"},
    "BLOCKED": set(),
    "RECONCILED": set(),
}


def create_paper_order_intent(
    db_path: str,
    *,
    intent_id: str,
    idempotency_key: str,
    runtime_decision_id: str,
    authority_id: str,
    lineage_hash: str,
    scheduler_lease_token: str,
    symbol: str,
    side: str,
    quantity: float,
    limit_price: float,
    broker_supports_client_order_id: bool,
    broker_client_order_id: str | None,
    created_at: str,
) -> dict:
    intent_id = _require_store_value(intent_id, "intent_id")
    idempotency_key = _require_store_value(idempotency_key, "idempotency_key")
    runtime_decision_id = _require_store_value(runtime_decision_id, "runtime_decision_id")
    authority_id = _require_store_value(authority_id, "authority_id")
    lineage_hash = _require_store_value(lineage_hash, "lineage_hash")
    scheduler_lease_token = _require_store_value(scheduler_lease_token, "scheduler_lease_token")
    symbol = _require_store_value(symbol, "symbol").upper()
    side = _require_store_value(side, "side").upper()
    created_at = _require_store_value(created_at, "created_at")
    con = _connect(db_path)
    try:
        con.isolation_level = None
        con.execute("BEGIN IMMEDIATE")
        existing = con.execute(
            """
            SELECT *
            FROM paper_order_intents
            WHERE idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()
        if existing is not None:
            con.execute("COMMIT")
            row = dict(existing)
            row["inserted"] = False
            return row
        con.execute(
            """
            INSERT INTO paper_order_intents (
                intent_id, idempotency_key, runtime_decision_id, authority_id, lineage_hash,
                scheduler_lease_token, symbol, side, quantity, limit_price,
                broker_supports_client_order_id, broker_client_order_id, state,
                broker_order_id, raw_response_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CREATED', NULL, NULL, ?, ?)
            """,
            (
                intent_id,
                idempotency_key,
                runtime_decision_id,
                authority_id,
                lineage_hash,
                scheduler_lease_token,
                symbol,
                side,
                float(quantity),
                float(limit_price),
                1 if broker_supports_client_order_id else 0,
                broker_client_order_id,
                created_at,
                created_at,
            ),
        )
        con.execute("COMMIT")
        row = get_paper_order_intent(db_path, idempotency_key=idempotency_key)
        assert row is not None
        row["inserted"] = True
        return row
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def get_paper_order_intent(db_path: str, *, idempotency_key: str) -> dict | None:
    idempotency_key = _require_store_value(idempotency_key, "idempotency_key")
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT *
            FROM paper_order_intents
            WHERE idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def list_paper_order_intents(
    db_path: str,
    *,
    states: tuple[str, ...] | None = None,
    limit: int = 100,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    normalized_states = tuple(str(state or "").strip().upper() for state in (states or ()) if str(state or "").strip())
    con = _connect(db_path)
    try:
        if normalized_states:
            placeholders = ",".join("?" for _ in normalized_states)
            rows = con.execute(
                f"""
                SELECT *
                FROM paper_order_intents
                WHERE state IN ({placeholders})
                ORDER BY updated_at ASC, created_at ASC
                LIMIT ?
                """,
                (*normalized_states, limit),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT *
                FROM paper_order_intents
                ORDER BY updated_at ASC, created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def transition_paper_order_intent(
    db_path: str,
    *,
    idempotency_key: str,
    from_state: str,
    to_state: str,
    updated_at: str,
    broker_order_id: str | None = None,
    raw_response: dict | None = None,
) -> bool:
    idempotency_key = _require_store_value(idempotency_key, "idempotency_key")
    from_state = _require_store_value(from_state, "from_state").upper()
    to_state = _require_store_value(to_state, "to_state").upper()
    updated_at = _require_store_value(updated_at, "updated_at")
    if to_state not in PAPER_ORDER_INTENT_TRANSITIONS.get(from_state, set()):
        raise ValueError(f"invalid paper order intent transition: {from_state}->{to_state}")
    raw_response_json = None if raw_response is None else json.dumps(raw_response, ensure_ascii=True, sort_keys=True)
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            UPDATE paper_order_intents
            SET state = ?,
                broker_order_id = COALESCE(?, broker_order_id),
                raw_response_json = COALESCE(?, raw_response_json),
                updated_at = ?
            WHERE idempotency_key = ? AND state = ?
            """,
            (to_state, broker_order_id, raw_response_json, updated_at, idempotency_key, from_state),
        )
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def resolve_paper_order_intent_after_reconciliation(
    db_path: str,
    *,
    idempotency_key: str,
    broker_state: str,
    local_state: str,
    updated_at: str,
) -> str:
    idempotency_key = _require_store_value(idempotency_key, "idempotency_key")
    broker_state = _require_store_value(broker_state, "broker_state").upper()
    local_state = _require_store_value(local_state, "local_state").upper()
    updated_at = _require_store_value(updated_at, "updated_at")
    intent = get_paper_order_intent(db_path, idempotency_key=idempotency_key)
    if intent is None:
        raise ValueError("paper order intent not found")
    current_state = str(intent["state"]).upper()
    if current_state not in {"UNKNOWN", "SUBMITTED_LOCAL_RECORDED"}:
        raise ValueError(f"reconciliation requires UNKNOWN or SUBMITTED_LOCAL_RECORDED, got {current_state}")
    terminal_broker_states = {"FILLED", "SUBMITTED", "PENDING", "PARTIAL", "CANCELLED", "REJECTED"}
    if broker_state in terminal_broker_states and local_state in {"UNKNOWN", "MISSING", "SUBMITTED", "PENDING", "PARTIAL"}:
        transition_paper_order_intent(
            db_path,
            idempotency_key=idempotency_key,
            from_state=current_state,
            to_state="RECONCILED",
            updated_at=updated_at,
            raw_response={"broker_state": broker_state, "local_state": local_state, "resolution_state": "RECONCILED"},
        )
        return "RECONCILED"
    transition_paper_order_intent(
        db_path,
        idempotency_key=idempotency_key,
        from_state=current_state,
        to_state="BLOCKED",
        updated_at=updated_at,
        raw_response={"broker_state": broker_state, "local_state": local_state, "resolution_state": "BLOCKED"},
    )
    return "BLOCKED"


def list_runtime_operating_metrics(db_path: str, *, now_iso: str) -> dict:
    now_iso = _require_store_value(now_iso, "now_iso")
    now_ts = _parse_iso(now_iso)
    con = _connect(db_path)
    try:
        unknown_rows = con.execute(
            "SELECT submitted_at FROM orders WHERE status = 'UNKNOWN'"
        ).fetchall()
        unknown_ages = []
        for row in unknown_rows:
            submitted_at = row["submitted_at"]
            if submitted_at:
                unknown_ages.append(max(0.0, (now_ts - _parse_iso(str(submitted_at))).total_seconds() / 60.0))
        intent_rows = con.execute(
            """
            SELECT state, COUNT(*) AS count
            FROM paper_order_intents
            GROUP BY state
            """
        ).fetchall()
        heartbeat_rows = con.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM diagnostic_runtime_heartbeats
            GROUP BY status
            """
        ).fetchall()
        latest_heartbeat = con.execute(
            """
            SELECT created_at
            FROM diagnostic_runtime_heartbeats
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
        latest_lag_minutes = None
        if latest_heartbeat is not None and latest_heartbeat["created_at"]:
            latest_lag_minutes = max(0.0, (now_ts - _parse_iso(str(latest_heartbeat["created_at"]))).total_seconds() / 60.0)
        blocked_recon = con.execute(
            "SELECT COUNT(*) AS count FROM reconciliation_runs WHERE block_new_orders = 1"
        ).fetchone()
        return {
            "unknown_order_count": len(unknown_rows),
            "oldest_unknown_order_age_minutes": max(unknown_ages) if unknown_ages else 0.0,
            "reconciliation_block_count": int(blocked_recon["count"]) if blocked_recon else 0,
            "paper_order_intent_state_counts": {str(row["state"]): int(row["count"]) for row in intent_rows},
            "heartbeat_status_counts": {str(row["status"]): int(row["count"]) for row in heartbeat_rows},
            "latest_heartbeat_lag_minutes": latest_lag_minutes,
        }
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
    blocking_statuses: tuple[str, ...] = (
        "SUBMITTED",
        "PENDING",
        "PARTIAL",
        "CANCEL_REQUESTED",
        "CANCEL_IN_PROGRESS",
        "UNKNOWN",
    ),
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


def insert_or_ignore_continuation_setup(
    db_path: str,
    *,
    setup_id: str,
    symbol: str,
    session_date: str,
    setup_timestamp: str,
    setup_origin: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    capture_mode: str = "paper_runtime",
    capture_batch_id: str | None = None,
    source_dataset_version: str | None = None,
    created_at: str,
) -> None:
    if capture_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"invalid capture_mode: {capture_mode}")
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT OR IGNORE INTO continuation_setups (
                setup_id, symbol, session_date, setup_timestamp, setup_origin,
                signal_event_id, risk_decision_id, capture_mode, capture_batch_id,
                source_dataset_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                setup_id,
                symbol,
                session_date,
                setup_timestamp,
                setup_origin,
                signal_event_id,
                risk_decision_id,
                capture_mode,
                capture_batch_id,
                source_dataset_version,
                created_at,
            ),
        )
        con.commit()
    finally:
        con.close()


def get_continuation_setup(db_path: str, setup_id: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT setup_id, symbol, session_date, setup_timestamp, setup_origin,
                   signal_event_id, risk_decision_id, capture_mode, capture_batch_id,
                   source_dataset_version, created_at
            FROM continuation_setups
            WHERE setup_id = ?
            """,
            (setup_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def list_continuation_setups(
    db_path: str,
    *,
    symbol: str | None = None,
    capture_mode: str | None = None,
    capture_batch_id: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    clauses: list[str] = []
    params: list[object] = []
    if symbol is not None:
        clauses.append("symbol = ?")
        params.append(symbol)
    if capture_mode is not None:
        clauses.append("capture_mode = ?")
        params.append(capture_mode)
    if capture_batch_id is not None:
        clauses.append("capture_batch_id = ?")
        params.append(capture_batch_id)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    con = _connect(db_path)
    try:
        rows = con.execute(
            f"""
            SELECT setup_id, symbol, session_date, setup_timestamp, setup_origin,
                   signal_event_id, risk_decision_id, capture_mode, capture_batch_id,
                   source_dataset_version, created_at
            FROM continuation_setups
            {where_sql}
            ORDER BY setup_timestamp ASC, setup_id ASC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def insert_continuation_lifecycle(
    db_path: str,
    *,
    lifecycle_id: str,
    setup_id: str,
    parent_lifecycle_id: str | None,
    symbol: str,
    session_date: str,
    started_at: str,
    identity_origin: str,
    identity_confidence: float,
    capture_mode: str = "paper_runtime",
    capture_batch_id: str | None = None,
    source_dataset_version: str | None = None,
    created_at: str,
) -> None:
    if capture_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"invalid capture_mode: {capture_mode}")
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT OR IGNORE INTO continuation_lifecycles (
                lifecycle_id, setup_id, parent_lifecycle_id, symbol, session_date,
                started_at, ended_at, identity_origin, identity_confidence,
                capture_mode, capture_batch_id, source_dataset_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)
            """,
            (
                lifecycle_id,
                setup_id,
                parent_lifecycle_id,
                symbol,
                session_date,
                started_at,
                identity_origin,
                float(identity_confidence),
                capture_mode,
                capture_batch_id,
                source_dataset_version,
                created_at,
            ),
        )
        con.commit()
    finally:
        con.close()


def close_continuation_lifecycle(db_path: str, lifecycle_id: str, ended_at: str) -> None:
    con = _connect(db_path)
    try:
        con.execute(
            """
            UPDATE continuation_lifecycles
            SET ended_at = COALESCE(ended_at, ?)
            WHERE lifecycle_id = ?
            """,
            (ended_at, lifecycle_id),
        )
        con.commit()
    finally:
        con.close()


def get_continuation_lifecycle(db_path: str, lifecycle_id: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT lifecycle_id, setup_id, parent_lifecycle_id, symbol, session_date,
                   started_at, ended_at, identity_origin, identity_confidence,
                   capture_mode, capture_batch_id, source_dataset_version, created_at
            FROM continuation_lifecycles
            WHERE lifecycle_id = ?
            """,
            (lifecycle_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def get_active_continuation_lifecycle(
    db_path: str,
    *,
    setup_id: str,
    symbol: str,
    session_date: str,
    capture_mode: str | None = None,
) -> dict | None:
    clauses = ["setup_id = ?", "symbol = ?", "session_date = ?", "ended_at IS NULL"]
    params: list[object] = [setup_id, symbol, session_date]
    if capture_mode is not None:
        clauses.append("capture_mode = ?")
        params.append(capture_mode)
    con = _connect(db_path)
    try:
        row = con.execute(
            f"""
            SELECT lifecycle_id, setup_id, parent_lifecycle_id, symbol, session_date,
                   started_at, ended_at, identity_origin, identity_confidence,
                   capture_mode, capture_batch_id, source_dataset_version, created_at
            FROM continuation_lifecycles
            WHERE {' AND '.join(clauses)}
            ORDER BY started_at DESC, lifecycle_id DESC
            LIMIT 1
            """,
            tuple(params),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def list_continuation_lifecycles(
    db_path: str,
    *,
    setup_id: str | None = None,
    symbol: str | None = None,
    capture_mode: str | None = None,
    capture_batch_id: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    clauses: list[str] = []
    params: list[object] = []
    if setup_id is not None:
        clauses.append("setup_id = ?")
        params.append(setup_id)
    if symbol is not None:
        clauses.append("symbol = ?")
        params.append(symbol)
    if capture_mode is not None:
        clauses.append("capture_mode = ?")
        params.append(capture_mode)
    if capture_batch_id is not None:
        clauses.append("capture_batch_id = ?")
        params.append(capture_batch_id)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    con = _connect(db_path)
    try:
        rows = con.execute(
            f"""
            SELECT lifecycle_id, setup_id, parent_lifecycle_id, symbol, session_date,
                   started_at, ended_at, identity_origin, identity_confidence,
                   capture_mode, capture_batch_id, source_dataset_version, created_at
            FROM continuation_lifecycles
            {where_sql}
            ORDER BY started_at ASC, lifecycle_id ASC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def get_latest_continuation_source_event(db_path: str, lifecycle_id: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT source_event_id, lifecycle_id, setup_id, parent_lifecycle_id, signal_event_id,
                   risk_decision_id, order_intent_id, order_id, fill_id, reconciliation_id, trade_run_id, symbol, session_date, event_type,
                   event_source, event_timestamp, state_label, participation_quality_label,
                   expansion_score, fragility_score, continuation_risk_score, size_multiplier,
                   add_depth, scale_depth, persistence_depth, details_json, created_at
            FROM continuation_source_events
            WHERE lifecycle_id = ?
            ORDER BY event_timestamp DESC, source_event_id DESC
            LIMIT 1
            """,
            (lifecycle_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def get_continuation_source_event_count(db_path: str, lifecycle_id: str) -> int:
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT COUNT(*) AS event_count FROM continuation_source_events WHERE lifecycle_id = ?",
            (lifecycle_id,),
        ).fetchone()
        return int(row["event_count"]) if row is not None else 0
    finally:
        con.close()


def find_matching_continuation_source_event(
    db_path: str,
    *,
    lifecycle_id: str,
    event_type: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    order_id: str | None,
    fill_id: str | None,
) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT source_event_id, lifecycle_id, setup_id, parent_lifecycle_id, signal_event_id,
                   risk_decision_id, order_intent_id, order_id, fill_id, reconciliation_id, trade_run_id, symbol, session_date, event_type,
                   event_source, event_timestamp, state_label, participation_quality_label,
                   expansion_score, fragility_score, continuation_risk_score, size_multiplier,
                   add_depth, scale_depth, persistence_depth, details_json, created_at
            FROM continuation_source_events
            WHERE lifecycle_id = ?
              AND event_type = ?
              AND event_timestamp = ?
              AND COALESCE(signal_event_id, '') = COALESCE(?, '')
              AND COALESCE(risk_decision_id, '') = COALESCE(?, '')
              AND COALESCE(order_id, '') = COALESCE(?, '')
              AND COALESCE(fill_id, '') = COALESCE(?, '')
            ORDER BY source_event_id ASC
            LIMIT 1
            """,
            (lifecycle_id, event_type, event_timestamp, signal_event_id, risk_decision_id, order_id, fill_id),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def insert_continuation_source_event(
    db_path: str,
    *,
    source_event_id: str,
    lifecycle_id: str,
    setup_id: str,
    parent_lifecycle_id: str | None,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    order_intent_id: str | None,
    order_id: str | None,
    fill_id: str | None,
    reconciliation_id: str | None,
    trade_run_id: str | None,
    symbol: str,
    session_date: str,
    event_type: str,
    event_source: str,
    event_timestamp: str,
    state_label: str | None,
    participation_quality_label: str | None,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    add_depth: int,
    scale_depth: int,
    persistence_depth: int,
    capture_mode: str = "paper_runtime",
    capture_batch_id: str | None = None,
    source_dataset_version: str | None = None,
    details_json: str | None,
    created_at: str,
) -> None:
    if event_type not in ALLOWED_CONTINUATION_EVENT_TYPES:
        raise ValueError(f"invalid continuation event_type: {event_type}")
    if event_source not in ALLOWED_CONTINUATION_EVENT_SOURCES:
        raise ValueError(f"invalid continuation event_source: {event_source}")
    if capture_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"invalid capture_mode: {capture_mode}")
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT OR IGNORE INTO continuation_source_events (
                source_event_id, lifecycle_id, setup_id, parent_lifecycle_id, signal_event_id,
                risk_decision_id, order_intent_id, order_id, fill_id, reconciliation_id, trade_run_id, symbol, session_date, event_type, event_source,
                event_timestamp, state_label, participation_quality_label, expansion_score, fragility_score,
                continuation_risk_score, size_multiplier, add_depth, scale_depth, persistence_depth,
                capture_mode, capture_batch_id, source_dataset_version, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_event_id,
                lifecycle_id,
                setup_id,
                parent_lifecycle_id,
                signal_event_id,
                risk_decision_id,
                order_intent_id,
                order_id,
                fill_id,
                reconciliation_id,
                trade_run_id,
                symbol,
                session_date,
                event_type,
                event_source,
                event_timestamp,
                state_label,
                participation_quality_label,
                float(expansion_score),
                float(fragility_score),
                float(continuation_risk_score),
                float(size_multiplier),
                int(add_depth),
                int(scale_depth),
                int(persistence_depth),
                capture_mode,
                capture_batch_id,
                source_dataset_version,
                details_json,
                created_at,
            ),
        )
        con.commit()
    finally:
        con.close()


def list_continuation_source_events(
    db_path: str,
    *,
    lifecycle_id: str | None = None,
    setup_id: str | None = None,
    symbol: str | None = None,
    capture_mode: str | None = None,
    capture_batch_id: str | None = None,
    limit: int = 5000,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    clauses: list[str] = []
    params: list[object] = []
    if lifecycle_id is not None:
        clauses.append("lifecycle_id = ?")
        params.append(lifecycle_id)
    if setup_id is not None:
        clauses.append("setup_id = ?")
        params.append(setup_id)
    if symbol is not None:
        clauses.append("symbol = ?")
        params.append(symbol)
    if capture_mode is not None:
        clauses.append("capture_mode = ?")
        params.append(capture_mode)
    if capture_batch_id is not None:
        clauses.append("capture_batch_id = ?")
        params.append(capture_batch_id)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    con = _connect(db_path)
    try:
        rows = con.execute(
            f"""
            SELECT source_event_id, lifecycle_id, setup_id, parent_lifecycle_id, signal_event_id,
                   risk_decision_id, order_intent_id, order_id, fill_id, reconciliation_id, trade_run_id, symbol, session_date, event_type,
                   event_source, event_timestamp, state_label, participation_quality_label,
                   expansion_score, fragility_score, continuation_risk_score, size_multiplier,
                   add_depth, scale_depth, persistence_depth, capture_mode, capture_batch_id,
                   source_dataset_version, details_json, created_at
            FROM continuation_source_events
            {where_sql}
            ORDER BY event_timestamp ASC, source_event_id ASC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def get_latest_continuation_snapshot(db_path: str, lifecycle_id: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT snapshot_id, lifecycle_id, setup_id, event_id, snapshot_timestamp, replay_state,
                   size_multiplier, add_depth, scale_depth, persistence_depth,
                   weakening_flag, invalidated_flag, created_at
            FROM continuation_snapshots
            WHERE lifecycle_id = ?
            ORDER BY snapshot_timestamp DESC, snapshot_id DESC
            LIMIT 1
            """,
            (lifecycle_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def insert_continuation_snapshot(
    db_path: str,
    *,
    snapshot_id: str,
    lifecycle_id: str,
    setup_id: str,
    event_id: str,
    snapshot_timestamp: str,
    replay_state: str,
    size_multiplier: float,
    add_depth: int,
    scale_depth: int,
    persistence_depth: int,
    weakening_flag: bool,
    invalidated_flag: bool,
    capture_mode: str = "paper_runtime",
    capture_batch_id: str | None = None,
    source_dataset_version: str | None = None,
    created_at: str,
) -> None:
    if capture_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"invalid capture_mode: {capture_mode}")
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT OR IGNORE INTO continuation_snapshots (
                snapshot_id, lifecycle_id, setup_id, event_id, snapshot_timestamp, replay_state,
                size_multiplier, add_depth, scale_depth, persistence_depth,
                weakening_flag, invalidated_flag, capture_mode, capture_batch_id,
                source_dataset_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                lifecycle_id,
                setup_id,
                event_id,
                snapshot_timestamp,
                replay_state,
                float(size_multiplier),
                int(add_depth),
                int(scale_depth),
                int(persistence_depth),
                1 if weakening_flag else 0,
                1 if invalidated_flag else 0,
                capture_mode,
                capture_batch_id,
                source_dataset_version,
                created_at,
            ),
        )
        con.commit()
    finally:
        con.close()


def list_continuation_snapshots(
    db_path: str,
    *,
    lifecycle_id: str | None = None,
    setup_id: str | None = None,
    capture_mode: str | None = None,
    capture_batch_id: str | None = None,
    limit: int = 5000,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    clauses: list[str] = []
    params: list[object] = []
    if lifecycle_id is not None:
        clauses.append("lifecycle_id = ?")
        params.append(lifecycle_id)
    if setup_id is not None:
        clauses.append("setup_id = ?")
        params.append(setup_id)
    if capture_mode is not None:
        clauses.append("capture_mode = ?")
        params.append(capture_mode)
    if capture_batch_id is not None:
        clauses.append("capture_batch_id = ?")
        params.append(capture_batch_id)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    con = _connect(db_path)
    try:
        rows = con.execute(
            f"""
            SELECT snapshot_id, lifecycle_id, setup_id, event_id, snapshot_timestamp, replay_state,
                   size_multiplier, add_depth, scale_depth, persistence_depth,
                   weakening_flag, invalidated_flag, capture_mode, capture_batch_id,
                   source_dataset_version, created_at
            FROM continuation_snapshots
            {where_sql}
            ORDER BY snapshot_timestamp ASC, snapshot_id ASC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def get_active_continuation_lifecycle_for_trade_run(
    db_path: str,
    *,
    trade_run_id: str,
    symbol: str,
) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT cl.lifecycle_id, cl.setup_id, cl.parent_lifecycle_id, cl.symbol, cl.session_date,
                   cl.started_at, cl.ended_at, cl.identity_origin, cl.identity_confidence, cl.created_at
            FROM continuation_source_events cse
            JOIN continuation_lifecycles cl ON cl.lifecycle_id = cse.lifecycle_id
            WHERE cse.trade_run_id = ? AND cse.symbol = ? AND cl.ended_at IS NULL
            ORDER BY cse.event_timestamp DESC, cse.source_event_id DESC
            LIMIT 1
            """,
            (trade_run_id, symbol),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def get_latest_continuation_source_event_by_order_id(db_path: str, order_id: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT source_event_id, lifecycle_id, setup_id, parent_lifecycle_id, signal_event_id,
                   risk_decision_id, order_intent_id, order_id, fill_id, reconciliation_id, trade_run_id, symbol, session_date, event_type,
                   event_source, event_timestamp, state_label, participation_quality_label,
                   expansion_score, fragility_score, continuation_risk_score, size_multiplier,
                   add_depth, scale_depth, persistence_depth, details_json, created_at
            FROM continuation_source_events
            WHERE order_id = ?
            ORDER BY event_timestamp DESC, source_event_id DESC
            LIMIT 1
            """,
            (order_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def get_latest_continuation_source_event_by_fill_id(db_path: str, fill_id: str) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            """
            SELECT source_event_id, lifecycle_id, setup_id, parent_lifecycle_id, signal_event_id,
                   risk_decision_id, order_intent_id, order_id, fill_id, reconciliation_id, trade_run_id, symbol, session_date, event_type,
                   event_source, event_timestamp, state_label, participation_quality_label,
                   expansion_score, fragility_score, continuation_risk_score, size_multiplier,
                   add_depth, scale_depth, persistence_depth, details_json, created_at
            FROM continuation_source_events
            WHERE fill_id = ?
            ORDER BY event_timestamp DESC, source_event_id DESC
            LIMIT 1
            """,
            (fill_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def list_continuation_lifecycle_event_timeline(db_path: str, lifecycle_id: str) -> list[dict]:
    return list_continuation_source_events(db_path, lifecycle_id=lifecycle_id, limit=10000)


def summarize_continuation_lifecycle_completeness(db_path: str, *, limit: int = 5000) -> list[dict]:
    return summarize_continuation_lifecycle_completeness_filtered(db_path, limit=limit)


def summarize_continuation_lifecycle_completeness_filtered(
    db_path: str,
    *,
    capture_mode: str | None = None,
    capture_batch_id: str | None = None,
    limit: int = 5000,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    rows = list_continuation_source_events(
        db_path,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        limit=100000,
    )
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("lifecycle_id") or ""), []).append(row)
    summaries: list[dict] = []
    for lifecycle_id, events in grouped.items():
        ordered = sorted(
            events,
            key=lambda row: (str(row.get("event_timestamp") or ""), str(row.get("source_event_id") or "")),
        )
        event_types = [str(row.get("event_type") or "") for row in ordered]
        source_rows = sum(1 for row in ordered if str(row.get("event_source") or "") == "SOURCE_CAPTURED")
        derived_rows = len(ordered) - source_rows
        summaries.append(
            {
                "lifecycle_id": lifecycle_id,
                "setup_id": str(ordered[0].get("setup_id") or ""),
                "symbol": str(ordered[0].get("symbol") or ""),
                "event_count": len(ordered),
                "has_probe": int("PROBE_ENTRY" in event_types),
                "has_add_confirmed": int("ADD_CONFIRMED" in event_types),
                "has_size_increase": int("SIZE_INCREASE" in event_types),
                "has_persistence": int("PERSISTENCE_CONFIRMED" in event_types),
                "has_weakening": int(any(event_type in {"FRAGILITY_WARNING", "REDUCTION_TRIGGER"} for event_type in event_types)),
                "has_terminal": int(any(event_type in {"EXIT_TRIGGER", "INVALIDATION"} for event_type in event_types)),
                "is_full_lifecycle": int(
                    "PROBE_ENTRY" in event_types
                    and "ADD_CONFIRMED" in event_types
                    and "SIZE_INCREASE" in event_types
                    and "PERSISTENCE_CONFIRMED" in event_types
                    and any(event_type in {"FRAGILITY_WARNING", "REDUCTION_TRIGGER"} for event_type in event_types)
                    and any(event_type in {"EXIT_TRIGGER", "INVALIDATION"} for event_type in event_types)
                ),
                "source_captured_rows": source_rows,
                "derived_rows": derived_rows,
            }
        )
    ordered_summaries = sorted(
        summaries,
        key=lambda row: (-int(row["is_full_lifecycle"]), -int(row["event_count"]), str(row["lifecycle_id"])),
    )
    return ordered_summaries[:limit]


def summarize_continuation_capture_coverage(db_path: str) -> dict[str, float]:
    return summarize_continuation_capture_coverage_filtered(db_path)


def summarize_continuation_capture_coverage_filtered(
    db_path: str,
    *,
    capture_mode: str | None = None,
    capture_batch_id: str | None = None,
) -> dict[str, float]:
    lifecycle_summary = summarize_continuation_lifecycle_completeness_filtered(
        db_path,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        limit=100000,
    )
    events = list_continuation_source_events(
        db_path,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        limit=100000,
    )
    lifecycle_count = max(len(lifecycle_summary), 1)
    event_count = max(len(events), 1)
    explicit_events = sum(1 for row in events if str(row.get("event_source") or "") == "SOURCE_CAPTURED")
    identifier_non_null = 0
    identifier_total = 0
    for row in events:
        for key in ("signal_event_id", "risk_decision_id", "order_intent_id", "order_id", "fill_id", "reconciliation_id", "trade_run_id"):
            identifier_total += 1
            if str(row.get(key) or "").strip():
                identifier_non_null += 1
    return {
        "source_rows_recorded": float(len(events)),
        "lifecycles_recorded": float(len(lifecycle_summary)),
        "full_lifecycle_sample_count": float(sum(int(row["is_full_lifecycle"]) for row in lifecycle_summary)),
        "blocked_invalidation_sample_count": float(
            sum(int(row["has_terminal"]) for row in lifecycle_summary if int(row["event_count"]) <= 2)
        ),
        "filled_add_sample_count": float(sum(int(row["has_add_confirmed"]) for row in lifecycle_summary)),
        "persistence_sample_count": float(sum(int(row["has_persistence"]) for row in lifecycle_summary)),
        "weakening_sample_count": float(sum(int(row["has_weakening"]) for row in lifecycle_summary)),
        "terminal_sample_count": float(sum(int(row["has_terminal"]) for row in lifecycle_summary)),
        "identifier_linkage_completeness": float(identifier_non_null / identifier_total) if identifier_total else 0.0,
        "source_captured_share": float(explicit_events / event_count) if events else 0.0,
    }


def delete_continuation_capture_batch(
    db_path: str,
    *,
    capture_mode: str,
    capture_batch_id: str,
) -> None:
    if capture_mode != "historical_backfill":
        raise ValueError("batch deletion is only allowed for historical_backfill rows")
    if not str(capture_batch_id).strip():
        raise ValueError("capture_batch_id is required")
    con = _connect(db_path)
    try:
        con.execute(
            "DELETE FROM continuation_snapshots WHERE capture_mode = ? AND capture_batch_id = ?",
            (capture_mode, capture_batch_id),
        )
        con.execute(
            "DELETE FROM continuation_source_events WHERE capture_mode = ? AND capture_batch_id = ?",
            (capture_mode, capture_batch_id),
        )
        con.execute(
            "DELETE FROM continuation_lifecycles WHERE capture_mode = ? AND capture_batch_id = ?",
            (capture_mode, capture_batch_id),
        )
        con.execute(
            "DELETE FROM continuation_setups WHERE capture_mode = ? AND capture_batch_id = ?",
            (capture_mode, capture_batch_id),
        )
        con.commit()
    finally:
        con.close()
