from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import scan_db_authority, write_csv, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan DB-like files and classify authority status.")
    parser.add_argument("--csv", type=Path, help="Optional CSV output path.")
    parser.add_argument("--json", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()

    rows = scan_db_authority()
    if args.csv:
        write_csv(args.csv, rows)
    if args.json:
        write_json(args.json, rows)
    if not args.csv and not args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

