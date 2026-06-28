from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
        rows = conn.execute(
            """
            SELECT primitive_id, source_receipt_id, primitive_batch_id, provider, runtime_context,
                   freshness_status, diagnostic_only, trade_output_flag, score_output_flag, order_intent_flag
            FROM l2_primitive_facts
            WHERE source_family = 'news_event'
            """
        ).fetchall()
        for row in rows:
            primitive_id = str(row["primitive_id"])
            if not str(row["source_receipt_id"] or ""):
                errors.append(f"{primitive_id}: missing source_receipt_id")
            receipt = conn.execute(
                "SELECT 1 FROM l2_runtime_source_receipts WHERE source_receipt_id = ? AND source_family = 'news_event'",
                (str(row["source_receipt_id"]),),
            ).fetchone()
            if receipt is None:
                errors.append(f"{primitive_id}: missing news source receipt")
            batch = conn.execute(
                "SELECT 1 FROM l2_primitive_batches WHERE primitive_batch_id = ?",
                (str(row["primitive_batch_id"]),),
            ).fetchone()
            if batch is None:
                errors.append(f"{primitive_id}: missing primitive batch")
            if int(row["diagnostic_only"]) != 1:
                errors.append(f"{primitive_id}: diagnostic_only must remain 1")
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
            print(f"[L2_NEWS_ERROR] {error}")
        return 1
    print("[L2_NEWS_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
