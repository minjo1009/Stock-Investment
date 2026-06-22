from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def migrate(root: Path, *, plan_path: Path | None = None, out: Path | None = None) -> list[dict[str, object]]:
    plan_path = plan_path or root / "docs" / "artifact_migration_plan.csv"
    out = out or root / "docs" / "artifact_migration_result.csv"
    plan_rows = _read_csv(plan_path)
    result_rows: list[dict[str, object]] = []
    moved_at = datetime.now(timezone.utc).isoformat()

    for row in plan_rows:
        action = row.get("migration_action", "")
        source_rel = row.get("source_path", "")
        target_rel = row.get("target_path", "")
        source = root / source_rel
        target = root / target_rel
        status = "skipped"
        sha256 = ""
        message = action

        if action == "move_to_data_artifacts":
            if not source.exists():
                status = "missing_source"
                message = "source file was already absent"
            else:
                sha256 = _file_hash(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    target_hash = _file_hash(target)
                    if target_hash != sha256:
                        raise RuntimeError(f"target exists with different hash: {target}")
                    source.unlink()
                else:
                    shutil.move(str(source), str(target))
                stub = source.with_name(source.name + ".migrated.txt")
                stub.write_text(
                    "\n".join(
                        [
                            "artifact_migrated=true",
                            f"moved_at_utc={moved_at}",
                            f"source_path={source_rel}",
                            f"target_path={target_rel}",
                            f"sha256={sha256}",
                            "reason=large archive candidate moved out of docs/reports",
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )
                status = "moved"
                message = "moved large archive artifact to data/artifacts"

        result_rows.append(
            {
                "report_dir": row.get("report_dir", ""),
                "relative_path": row.get("relative_path", ""),
                "source_path": source_rel,
                "target_path": target_rel,
                "migration_action": action,
                "migration_status": status,
                "size_bytes": row.get("size_bytes", "0"),
                "sha256": sha256,
                "message": message,
            }
        )

    fieldnames = [
        "report_dir",
        "relative_path",
        "source_path",
        "target_path",
        "migration_action",
        "migration_status",
        "size_bytes",
        "sha256",
        "message",
    ]
    _write_csv(out, result_rows, fieldnames)
    return result_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    rows = migrate(root, plan_path=args.plan, out=args.out)
    moved = [row for row in rows if row["migration_status"] == "moved"]
    moved_bytes = sum(int(row["size_bytes"]) for row in moved)
    print(f"[ARTIFACT_MIGRATE_SAFE] rows={len(rows)} moved={len(moved)} moved_bytes={moved_bytes}")


if __name__ == "__main__":
    main()
