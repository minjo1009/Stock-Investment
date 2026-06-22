from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from .common import SNAPSHOT_DIR, rel, sqlite_meta, write_json


def latest_snapshot() -> Path:
    snapshots = sorted(SNAPSHOT_DIR.glob("trading_*.db"))
    if not snapshots:
        raise SystemExit("no snapshots found under data/snapshots")
    return snapshots[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify latest DB snapshot can be restored read-only.")
    parser.add_argument("--snapshot", type=Path, help="Snapshot DB path. Defaults to latest data/snapshots/trading_*.db.")
    parser.add_argument("--json", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()

    source = args.snapshot or latest_snapshot()
    with tempfile.TemporaryDirectory(prefix="trader_brain_restore_drill_") as tmp:
        target = Path(tmp) / source.name
        shutil.copy2(source, target)
        meta = sqlite_meta(target)
        result = {
            "source_snapshot": rel(source),
            "restored_temp_name": target.name,
            "integrity_status": meta["integrity_status"],
            "foreign_key_check_count": meta["foreign_key_check_count"],
            "table_count": meta["table_count"],
            "restore_drill_status": (
                "PASS"
                if meta["integrity_status"] == "ok" and meta["foreign_key_check_count"] == 0
                else "FAIL"
            ),
        }
    if args.json:
        write_json(args.json, result)
    print(result)
    if result["restore_drill_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

