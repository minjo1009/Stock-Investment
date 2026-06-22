from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.task_artifact_manifest import write_manifest


def build_bulk_manifests(root: Path, *, min_size_mb: float, limit: int | None) -> list[Path]:
    reports = root / "docs" / "reports"
    candidates: list[tuple[int, Path]] = []
    for directory in reports.iterdir() if reports.exists() else []:
        if not directory.is_dir():
            continue
        size = sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())
        if size >= min_size_mb * 1024 * 1024:
            candidates.append((size, directory))
    candidates.sort(reverse=True, key=lambda item: item[0])
    if limit is not None:
        candidates = candidates[:limit]
    outputs: list[Path] = []
    for _, directory in candidates:
        out = directory / "artifact_manifest.csv"
        write_manifest(directory, out)
        outputs.append(out)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--min-size-mb", type=float, default=10.0)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    outputs = build_bulk_manifests(args.root, min_size_mb=args.min_size_mb, limit=args.limit)
    print(f"[BULK_ARTIFACT_MANIFEST] wrote={len(outputs)} manifests")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
