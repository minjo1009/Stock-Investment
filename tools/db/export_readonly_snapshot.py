from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from .common import ACTIVE_DB, READONLY_DIR, SNAPSHOT_DIR, copy_db_with_hash, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Create governed read-only DB copies.")
    parser.add_argument("--readonly", action="store_true", help="Export data/readonly_mcp/trading_readonly_latest.db.")
    parser.add_argument("--snapshot", action="store_true", help="Create timestamped immutable snapshot copy.")
    parser.add_argument("--manifest", type=Path, help="Manifest JSON output path.")
    args = parser.parse_args()

    if not args.readonly and not args.snapshot:
        args.readonly = True
        args.snapshot = True

    rows = []
    if args.readonly:
        rows.append(copy_db_with_hash(ACTIVE_DB, READONLY_DIR / "trading_readonly_latest.db"))
    if args.snapshot:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        rows.append(copy_db_with_hash(ACTIVE_DB, SNAPSHOT_DIR / f"trading_{stamp}.db"))
    if args.manifest:
        write_json(args.manifest, rows)
    for row in rows:
        print(f"{row['path']} {row['sha256']} {row['integrity_status']}")


if __name__ == "__main__":
    main()

