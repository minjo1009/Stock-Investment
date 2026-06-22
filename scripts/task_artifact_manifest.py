from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: Path) -> str:
    name = path.name.lower()
    if path.suffix.lower() == ".md":
        return "report"
    if "decision" in name:
        return "decision"
    if path.suffix.lower() == ".csv" and path.stat().st_size > 10 * 1024 * 1024:
        return "large_panel"
    if path.suffix.lower() == ".csv":
        return "small_table"
    return "other"


def build_manifest(task_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(p for p in task_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(task_dir).as_posix()
        stat = path.stat()
        rows.append(
            {
                "relative_path": rel,
                "artifact_class": classify(path),
                "size_bytes": stat.st_size,
                "sha256": file_hash(path),
            }
        )
    return rows


def write_manifest(task_dir: Path, out: Path) -> None:
    rows = build_manifest(task_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "artifact_class", "size_bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or args.task_dir / "artifact_manifest.csv"
    write_manifest(args.task_dir, out)
    print(f"[ARTIFACT_MANIFEST] wrote={out}")


if __name__ == "__main__":
    main()
