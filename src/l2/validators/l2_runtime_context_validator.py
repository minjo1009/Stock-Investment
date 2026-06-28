from __future__ import annotations

import sqlite3

from src.l2.runtime_context import HISTORICAL_CONTEXTS, LIVE_CONTEXTS


def validate_historical_live_separation(conn: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    conn.row_factory = sqlite3.Row
    tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "l2_primitive_batches" not in tables or "l2_primitive_facts" not in tables:
        return ["missing L2 primitive batch or fact table"]
    batch_rows = conn.execute("SELECT primitive_batch_id, runtime_context FROM l2_primitive_batches").fetchall()
    batch_context = {str(row["primitive_batch_id"]): str(row["runtime_context"]) for row in batch_rows}
    for batch_id, context in batch_context.items():
        contexts = {
            str(row[0])
            for row in conn.execute(
                "SELECT DISTINCT runtime_context FROM l2_primitive_facts WHERE primitive_batch_id = ?",
                (batch_id,),
            ).fetchall()
        }
        if len(contexts) > 1:
            errors.append(f"{batch_id}: mixed runtime_context values {sorted(contexts)}")
        if contexts and context not in contexts:
            errors.append(f"{batch_id}: fact context does not match batch context")
    for row in conn.execute(
        """
        SELECT primitive_id, primitive_batch_id, runtime_context, source_family
        FROM l2_primitive_facts
        WHERE source_family = 'historical_artifact'
        """,
    ).fetchall():
        if str(row["runtime_context"]) in LIVE_CONTEXTS:
            errors.append(f"{row['primitive_id']}: historical artifact cannot be live diagnostic evidence")
    for row in conn.execute(
        """
        SELECT primitive_batch_id, COUNT(DISTINCT source_family) AS family_count,
               SUM(CASE WHEN source_family = 'historical_artifact' THEN 1 ELSE 0 END) AS historical_rows,
               SUM(CASE WHEN source_family <> 'historical_artifact' THEN 1 ELSE 0 END) AS live_rows
        FROM l2_primitive_facts
        GROUP BY primitive_batch_id
        """,
    ).fetchall():
        if int(row["historical_rows"] or 0) > 0 and int(row["live_rows"] or 0) > 0:
            errors.append(f"{row['primitive_batch_id']}: historical and live/source-local rows mixed in one batch")
    for row in conn.execute("SELECT * FROM l2_runtime_context_audit").fetchall():
        for flag in ("mixed_context_violation_flag", "freshness_violation_flag", "source_time_violation_flag"):
            if int(row[flag]) != 0:
                errors.append(f"{row['batch_id']}: {flag} is set")
        context = str(row["runtime_context"])
        if context in HISTORICAL_CONTEXTS and int(row["live_evidence_count"]) > 0:
            errors.append(f"{row['batch_id']}: live evidence counted in historical context")
        if context in LIVE_CONTEXTS and int(row["historical_artifact_count"]) > 0:
            errors.append(f"{row['batch_id']}: historical artifact counted in live context")
    return errors
