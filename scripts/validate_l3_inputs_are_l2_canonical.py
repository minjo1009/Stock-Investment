from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.runtime_context import LIVE_CONTEXTS
from src.l2.stores.primitive_reader import load_l3_inputs
from src.l2.stores.sqlite_l2_store import ensure_l2_schema


def validate(db_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    conn = sqlite3.connect(db_path) if db_path is not None else sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        if db_path is None:
            ensure_l2_schema(conn)
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "l2_primitive_facts" not in tables:
            return ["missing table: l2_primitive_facts"]
        for row in conn.execute("SELECT primitive_id, runtime_context, source_family, source_receipt_id, lineage_edge_id, freshness_status, missing_source_is_negative, trade_output_flag, score_output_flag, order_intent_flag FROM l2_primitive_facts").fetchall():
            primitive_id = str(row["primitive_id"])
            if not str(row["source_receipt_id"] or ""):
                errors.append(f"{primitive_id}: missing source_receipt_id")
            if not str(row["lineage_edge_id"] or ""):
                errors.append(f"{primitive_id}: missing lineage_edge_id")
            if not str(row["freshness_status"] or ""):
                errors.append(f"{primitive_id}: missing freshness_status")
            if str(row["runtime_context"]) in LIVE_CONTEXTS and str(row["source_family"]) == "historical_artifact":
                errors.append(f"{primitive_id}: live L3 input cannot use direct historical artifact source")
            if int(row["missing_source_is_negative"]) != 0:
                errors.append(f"{primitive_id}: missing source treated as negative")
            for flag in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
                if int(row[flag]) != 0:
                    errors.append(f"{primitive_id}: {flag} must be 0")
        mixed = conn.execute(
            """
            SELECT primitive_batch_id, COUNT(DISTINCT runtime_context) AS contexts
            FROM l2_primitive_facts
            GROUP BY primitive_batch_id
            HAVING COUNT(DISTINCT runtime_context) > 1
            """
        ).fetchall()
        for row in mixed:
            errors.append(f"{row['primitive_batch_id']}: mixed runtime_context in L3 input batch")
        for context_row in conn.execute("SELECT runtime_context, MAX(asof_ts) AS asof_ts FROM l2_primitive_facts GROUP BY runtime_context").fetchall():
            context = str(context_row["runtime_context"])
            asof_ts = str(context_row["asof_ts"])
            for fact in load_l3_inputs(conn, asof_ts=asof_ts, runtime_context=context):
                if fact.freshness_status not in {"FRESH", "CURRENT_OR_RECENT"}:
                    errors.append(f"{fact.primitive_id}: stale source passed through canonical L3 reader")
                if not fact.source_time_certified:
                    errors.append(f"{fact.primitive_id}: uncertified source time passed through canonical L3 reader")
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
            print(f"[L3_L2_INPUT_ERROR] {error}")
        return 1
    print("[L3_L2_INPUT_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
