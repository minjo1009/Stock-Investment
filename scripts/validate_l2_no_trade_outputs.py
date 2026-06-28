from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.stores.sqlite_l2_store import ensure_l2_schema


def _readiness_status_errors() -> list[str]:
    path = ROOT / "docs/ownership/readiness_registry.yaml"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    errors: list[str] = []
    for required in ("NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"):
        if required not in text:
            errors.append(f"readiness registry missing required status: {required}")
    return errors


def validate(db_path: Path | None = None) -> list[str]:
    errors = _readiness_status_errors()
    conn = sqlite3.connect(db_path) if db_path is not None else sqlite3.connect(":memory:")
    try:
        if db_path is None:
            ensure_l2_schema(conn)
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "l2_primitive_facts" not in tables:
            errors.append("missing table: l2_primitive_facts")
            return errors
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(trade_output_flag), 0) AS trade_flags,
                COALESCE(SUM(score_output_flag), 0) AS score_flags,
                COALESCE(SUM(order_intent_flag), 0) AS order_flags,
                COALESCE(SUM(CASE WHEN diagnostic_only <> 1 THEN 1 ELSE 0 END), 0) AS non_diagnostic_rows,
                COALESCE(SUM(CASE WHEN missing_source_is_negative <> 0 THEN 1 ELSE 0 END), 0) AS missing_negative_rows
            FROM l2_primitive_facts
            """
        ).fetchone()
        labels = ["trade_output_flag", "score_output_flag", "order_intent_flag", "diagnostic_only", "missing_source_is_negative"]
        for label, value in zip(labels, row, strict=False):
            if int(value or 0) != 0:
                errors.append(f"{label} violation count={int(value or 0)}")
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
            print(f"[L2_NO_TRADE_OUTPUT_ERROR] {error}")
        return 1
    print("[L2_NO_TRADE_OUTPUT_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
