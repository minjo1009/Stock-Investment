from __future__ import annotations

import sqlite3

from src.l2.contracts import REQUIRED_L2_PRIMITIVE_FACT_FIELDS


L2_PRIMITIVE_BATCH_COLUMNS = [
    "primitive_batch_id",
    "runtime_context",
    "builder_name",
    "builder_version",
    "asof_ts",
    "created_at",
    "source_family_set",
    "symbol_set",
    "row_count",
    "input_hash",
    "output_hash",
    "diagnostic_only",
]

L2_RUNTIME_CONTEXT_AUDIT_COLUMNS = [
    "batch_id",
    "runtime_context",
    "historical_artifact_count",
    "live_evidence_count",
    "mixed_context_violation_flag",
    "freshness_violation_flag",
    "source_time_violation_flag",
]


def ensure_l2_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2_runtime_source_receipts (
            source_receipt_id TEXT PRIMARY KEY,
            runtime_context TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_family TEXT NOT NULL,
            provider TEXT NOT NULL,
            symbol_set TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            asof_ts TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            input_hash TEXT NOT NULL,
            freshness_status TEXT NOT NULL,
            diagnostic_only INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2_primitive_batches (
            primitive_batch_id TEXT PRIMARY KEY,
            runtime_context TEXT NOT NULL,
            builder_name TEXT NOT NULL,
            builder_version TEXT NOT NULL,
            asof_ts TEXT NOT NULL,
            created_at TEXT NOT NULL,
            source_family_set TEXT NOT NULL,
            symbol_set TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            input_hash TEXT NOT NULL,
            output_hash TEXT NOT NULL,
            diagnostic_only INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2_primitive_facts (
            primitive_id TEXT PRIMARY KEY,
            primitive_batch_id TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            source_family TEXT NOT NULL,
            provider TEXT NOT NULL,
            symbol TEXT,
            entity_id TEXT,
            event_time TEXT NOT NULL,
            source_ts TEXT NOT NULL,
            capture_ts TEXT NOT NULL,
            available_to_brain_ts TEXT NOT NULL,
            asof_ts TEXT NOT NULL,
            primitive_type TEXT NOT NULL,
            primitive_subtype TEXT NOT NULL,
            primitive_payload_json TEXT NOT NULL,
            freshness_status TEXT NOT NULL,
            source_time_certified INTEGER NOT NULL,
            closed_bar_only INTEGER NOT NULL,
            runtime_context TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            output_hash TEXT NOT NULL,
            lineage_edge_id TEXT NOT NULL,
            missing_source_is_negative INTEGER NOT NULL DEFAULT 0,
            diagnostic_only INTEGER NOT NULL DEFAULT 1,
            trade_output_flag INTEGER NOT NULL DEFAULT 0,
            score_output_flag INTEGER NOT NULL DEFAULT 0,
            order_intent_flag INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2_primitive_lineage (
            lineage_edge_id TEXT PRIMARY KEY,
            primitive_id TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            output_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2_primitive_freshness (
            primitive_id TEXT PRIMARY KEY,
            freshness_status TEXT NOT NULL,
            source_time_certified INTEGER NOT NULL,
            closed_bar_only INTEGER NOT NULL,
            asof_ts TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2_runtime_context_audit (
            batch_id TEXT PRIMARY KEY,
            runtime_context TEXT NOT NULL,
            historical_artifact_count INTEGER NOT NULL,
            live_evidence_count INTEGER NOT NULL,
            mixed_context_violation_flag INTEGER NOT NULL,
            freshness_violation_flag INTEGER NOT NULL,
            source_time_violation_flag INTEGER NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_l2_receipts_context_asof ON l2_runtime_source_receipts(runtime_context, asof_ts)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_l2_facts_batch ON l2_primitive_facts(primitive_batch_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_l2_facts_context_asof ON l2_primitive_facts(runtime_context, asof_ts)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_l2_facts_symbol_asof ON l2_primitive_facts(symbol, asof_ts)")
    conn.commit()


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def required_fact_columns() -> set[str]:
    return set(REQUIRED_L2_PRIMITIVE_FACT_FIELDS)
