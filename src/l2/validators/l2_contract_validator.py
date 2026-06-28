from __future__ import annotations

import sqlite3
from typing import Iterable

from src.l2.contracts import REQUIRED_L2_PRIMITIVE_FACT_FIELDS, L2PrimitiveFact
from src.l2.freshness import ALLOWED_FRESHNESS_STATUSES
from src.l2.runtime_context import ALLOWED_RUNTIME_CONTEXTS
from src.l2.stores.sqlite_l2_store import table_columns


def validate_l2_primitive_fact(fact: L2PrimitiveFact) -> list[str]:
    errors: list[str] = []
    try:
        L2PrimitiveFact(**fact.__dict__)
    except ValueError as exc:
        errors.append(str(exc))
    if fact.freshness_status not in ALLOWED_FRESHNESS_STATUSES:
        errors.append(f"{fact.primitive_id}: invalid freshness_status={fact.freshness_status}")
    return errors


def validate_l2_fact_schema(conn: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    required_tables = {
        "l2_primitive_batches",
        "l2_primitive_facts",
        "l2_primitive_lineage",
        "l2_runtime_context_audit",
    }
    for table in sorted(required_tables - tables):
        errors.append(f"missing table: {table}")
    if "l2_primitive_facts" in tables:
        cols = table_columns(conn, "l2_primitive_facts")
        for col in sorted(set(REQUIRED_L2_PRIMITIVE_FACT_FIELDS) - cols):
            errors.append(f"l2_primitive_facts missing column: {col}")
    return errors


def validate_l2_rows(conn: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    conn.row_factory = sqlite3.Row
    if validate_l2_fact_schema(conn):
        return validate_l2_fact_schema(conn)
    rows = conn.execute("SELECT * FROM l2_primitive_facts").fetchall()
    for row in rows:
        primitive_id = str(row["primitive_id"])
        for col in REQUIRED_L2_PRIMITIVE_FACT_FIELDS:
            if col in {"symbol", "entity_id"}:
                continue
            if row[col] is None or str(row[col]) == "":
                errors.append(f"{primitive_id}: missing {col}")
        if str(row["runtime_context"]) not in ALLOWED_RUNTIME_CONTEXTS:
            errors.append(f"{primitive_id}: invalid runtime_context")
        if str(row["freshness_status"]) not in ALLOWED_FRESHNESS_STATUSES:
            errors.append(f"{primitive_id}: invalid freshness_status")
        if int(row["missing_source_is_negative"]) != 0:
            errors.append(f"{primitive_id}: missing_source_is_negative must be 0")
        if int(row["diagnostic_only"]) != 1:
            errors.append(f"{primitive_id}: diagnostic_only must be 1")
        for flag in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
            if int(row[flag]) != 0:
                errors.append(f"{primitive_id}: {flag} must be 0")
        if str(row["source_family"]) == "market_bar" and int(row["closed_bar_only"]) != 1:
            errors.append(f"{primitive_id}: market_bar primitive must be closed_bar_only")
    return errors


def validate_facts(facts: Iterable[L2PrimitiveFact]) -> list[str]:
    errors: list[str] = []
    for fact in facts:
        errors.extend(validate_l2_primitive_fact(fact))
    return errors
