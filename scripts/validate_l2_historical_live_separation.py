from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.stores.sqlite_l2_store import ensure_l2_schema
from src.l2.validators.l2_runtime_context_validator import validate_historical_live_separation


def validate(db_path: Path | None = None) -> list[str]:
    conn = sqlite3.connect(db_path) if db_path is not None else sqlite3.connect(":memory:")
    try:
        if db_path is None:
            ensure_l2_schema(conn)
        return validate_historical_live_separation(conn)
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path)
    args = parser.parse_args()
    errors = validate(args.db_path)
    if errors:
        for error in errors:
            print(f"[L2_HISTORICAL_LIVE_ERROR] {error}")
        return 1
    print("[L2_HISTORICAL_LIVE_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
