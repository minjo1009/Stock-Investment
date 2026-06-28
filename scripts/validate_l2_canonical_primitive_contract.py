from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.contracts import REQUIRED_L2_PRIMITIVE_FACT_FIELDS
from src.l2.runtime_context import ALLOWED_RUNTIME_CONTEXTS
from src.l2.stores.sqlite_l2_store import ensure_l2_schema, table_columns
from src.l2.validators.l2_contract_validator import validate_l2_rows


REQUIRED_DOCS = [
    Path("docs/contracts/l2_canonical_primitive_contract.md"),
    Path("docs/architecture/l2_runtime_context_policy.md"),
    Path("docs/architecture/l2_historical_live_separation_policy.md"),
]


def open_connection(db_path: Path | None) -> sqlite3.Connection:
    if db_path is None:
        conn = sqlite3.connect(":memory:")
        ensure_l2_schema(conn)
        return conn
    return sqlite3.connect(db_path)


def validate(db_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    for doc in REQUIRED_DOCS:
        if not (ROOT / doc).exists():
            errors.append(f"missing required doc: {doc}")
    if not ALLOWED_RUNTIME_CONTEXTS:
        errors.append("allowed runtime contexts are empty")
    conn = open_connection(db_path)
    try:
        if db_path is None:
            ensure_l2_schema(conn)
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "l2_primitive_facts" not in tables:
            errors.append("missing table: l2_primitive_facts")
        else:
            cols = table_columns(conn, "l2_primitive_facts")
            missing = set(REQUIRED_L2_PRIMITIVE_FACT_FIELDS) - cols
            for col in sorted(missing):
                errors.append(f"missing L2 fact column: {col}")
            errors.extend(validate_l2_rows(conn))
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
            print(f"[L2_CONTRACT_ERROR] {error}")
        return 1
    print("[L2_CONTRACT_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
