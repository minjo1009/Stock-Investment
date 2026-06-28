from __future__ import annotations

import sqlite3

from src.l2.contracts import L2PrimitiveBatch, L2PrimitiveFact
from src.l2.stores.sqlite_l2_store import ensure_l2_schema


def write_l2_batch(conn: sqlite3.Connection, batch: L2PrimitiveBatch) -> None:
    ensure_l2_schema(conn)
    row = batch.to_db_row()
    cols = list(row.keys())
    placeholders = ",".join(["?"] * len(cols))
    conn.execute(
        f"""
        INSERT OR REPLACE INTO l2_primitive_batches({",".join(cols)})
        VALUES ({placeholders})
        """,
        [row[col] for col in cols],
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO l2_runtime_context_audit(
            batch_id, runtime_context, historical_artifact_count, live_evidence_count,
            mixed_context_violation_flag, freshness_violation_flag, source_time_violation_flag
        ) VALUES (?,?,?,?,?,?,?)
        """,
        (
            batch.primitive_batch_id,
            batch.runtime_context,
            0,
            0,
            0,
            0,
            0,
        ),
    )
    conn.commit()


def write_l2_primitives(conn: sqlite3.Connection, facts: list[L2PrimitiveFact]) -> None:
    ensure_l2_schema(conn)
    if not facts:
        return
    fact_cols = list(facts[0].to_db_row().keys())
    placeholders = ",".join(["?"] * len(fact_cols))
    for fact in facts:
        row = fact.to_db_row()
        conn.execute(
            f"""
            INSERT OR REPLACE INTO l2_primitive_facts({",".join(fact_cols)})
            VALUES ({placeholders})
            """,
            [row[col] for col in fact_cols],
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO l2_primitive_lineage(
                lineage_edge_id, primitive_id, source_receipt_id, input_hash, output_hash, created_at
            ) VALUES (?,?,?,?,?,?)
            """,
            (
                fact.lineage_edge_id,
                fact.primitive_id,
                fact.source_receipt_id,
                fact.input_hash,
                fact.output_hash,
                fact.capture_ts,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO l2_primitive_freshness(
                primitive_id, freshness_status, source_time_certified, closed_bar_only, asof_ts
            ) VALUES (?,?,?,?,?)
            """,
            (
                fact.primitive_id,
                fact.freshness_status,
                1 if fact.source_time_certified else 0,
                1 if fact.closed_bar_only else 0,
                fact.asof_ts,
            ),
        )
    conn.commit()
