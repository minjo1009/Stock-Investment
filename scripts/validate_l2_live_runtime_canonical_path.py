from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC
from src.l2.stores.sqlite_l2_store import ensure_l2_schema


def _json_payload(text: str) -> dict[str, object]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def validate(db_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    conn = sqlite3.connect(db_path) if db_path is not None else sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        if db_path is None:
            ensure_l2_schema(conn)
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        required = {
            "l2_runtime_source_receipts",
            "l2_primitive_batches",
            "l2_primitive_facts",
            "l2_primitive_lineage",
            "l2_primitive_freshness",
            "l2_runtime_context_audit",
        }
        for table in sorted(required - tables):
            errors.append(f"missing table: {table}")
        if errors:
            return errors
        if "indicator_snapshots" in tables:
            latest = conn.execute("SELECT MAX(created_at) FROM indicator_snapshots").fetchone()[0]
            if latest:
                snapshot_rows = conn.execute("SELECT snapshot_id FROM indicator_snapshots WHERE created_at = ?", (latest,)).fetchall()
                snapshot_ids = {str(row["snapshot_id"]) for row in snapshot_rows}
                fact_rows = conn.execute(
                    """
                    SELECT primitive_id, primitive_payload_json
                    FROM l2_primitive_facts
                    WHERE runtime_context = ?
                      AND source_family = 'indicator'
                      AND capture_ts = ?
                    """,
                    (LIVE_INTRADAY_DIAGNOSTIC, str(latest)),
                ).fetchall()
                fact_snapshot_ids = {
                    str(_json_payload(str(row["primitive_payload_json"])).get("snapshot_id") or "")
                    for row in fact_rows
                }
                missing = snapshot_ids - fact_snapshot_ids
                if missing:
                    errors.append(f"latest indicator snapshots missing canonical L2 facts: {sorted(missing)}")
        for row in conn.execute(
            """
            SELECT primitive_id, source_receipt_id, primitive_batch_id, runtime_context,
                   diagnostic_only, trade_output_flag, score_output_flag, order_intent_flag
            FROM l2_primitive_facts
            WHERE runtime_context = ?
            """,
            (LIVE_INTRADAY_DIAGNOSTIC,),
        ).fetchall():
            primitive_id = str(row["primitive_id"])
            if not str(row["source_receipt_id"] or ""):
                errors.append(f"{primitive_id}: missing source_receipt_id")
            receipt = conn.execute(
                "SELECT 1 FROM l2_runtime_source_receipts WHERE source_receipt_id = ?",
                (str(row["source_receipt_id"]),),
            ).fetchone()
            if receipt is None:
                errors.append(f"{primitive_id}: missing runtime source receipt row")
            batch = conn.execute(
                "SELECT 1 FROM l2_primitive_batches WHERE primitive_batch_id = ? AND runtime_context = ?",
                (str(row["primitive_batch_id"]), LIVE_INTRADAY_DIAGNOSTIC),
            ).fetchone()
            if batch is None:
                errors.append(f"{primitive_id}: missing live diagnostic batch row")
            if int(row["diagnostic_only"]) != 1:
                errors.append(f"{primitive_id}: live L2 row must remain diagnostic_only")
            for flag in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
                if int(row[flag]) != 0:
                    errors.append(f"{primitive_id}: {flag} must be 0")
    finally:
        conn.close()
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path)
    args = parser.parse_args()
    errors = validate(args.db_path)
    if errors:
        for error in errors:
            print(f"[L2_LIVE_RUNTIME_ERROR] {error}")
        return 1
    print("[L2_LIVE_RUNTIME_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
