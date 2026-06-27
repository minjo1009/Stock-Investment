from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml


LARGE_THRESHOLD = 50 * 1024 * 1024
REPORT_PAYLOAD_SUFFIXES = {".csv", ".json", ".jsonl", ".parquet", ".feather"}
ALLOWED_LARGE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
IGNORED_LARGE_PREFIXES = (
    ".git/",
    ".dvc/cache/",
    ".dvc/tmp/",
    "frontend/trader-terminal/dist/",
)


def _read_dvc_outs(root: Path) -> set[str]:
    outs: set[str] = set()
    for dvc_file in root.rglob("*.dvc"):
        rel_dvc = dvc_file.relative_to(root).as_posix()
        if rel_dvc.startswith(".dvc/"):
            continue
        try:
            data = yaml.safe_load(dvc_file.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        for out in data.get("outs", []) or []:
            out_path = dvc_file.parent / str(out.get("path", ""))
            try:
                outs.add(out_path.resolve().relative_to(root.resolve()).as_posix())
            except ValueError:
                continue
    return outs


def _is_dvc_covered(rel: str, dvc_outs: set[str]) -> bool:
    if rel in dvc_outs:
        return True
    return any(rel.startswith(out + "/") for out in dvc_outs)


def _tracking_status_errors(root: Path) -> list[str]:
    path = root / "docs" / "reports" / "A007_dvc_lfs_artifact_management" / "dvc_tracking_status.csv"
    if not path.exists():
        return ["missing DVC tracking status: docs/reports/A007_dvc_lfs_artifact_management/dvc_tracking_status.csv"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    missing = [row["path"] for row in rows if row.get("dvc_tracked") != "TRUE"]
    return [f"DVC target not tracked: {item}" for item in missing]


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []
    dvc_outs = _read_dvc_outs(root)
    if not (root / ".dvc" / "config").exists():
        errors.append("missing DVC config: .dvc/config")
    if not dvc_outs:
        errors.append("no DVC-tracked outputs found")
    errors.extend(_tracking_status_errors(root))

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(IGNORED_LARGE_PREFIXES):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size < LARGE_THRESHOLD:
            continue
        suffix = path.suffix.lower()
        if rel.startswith("docs/reports/") and suffix in REPORT_PAYLOAD_SUFFIXES and not _is_dvc_covered(rel, dvc_outs):
            errors.append(f"large report payload remains outside DVC: {rel}")
            continue
        if _is_dvc_covered(rel, dvc_outs):
            continue
        if suffix in ALLOWED_LARGE_SUFFIXES:
            warnings.append(f"protected DB authority not DVC-tracked: {rel}")
            continue
        errors.append(f"large payload is not DVC/LFS managed: {rel}")

    if (root / "frontend_data" / "catalog").exists():
        catalog_files = list((root / "frontend_data" / "catalog").glob("*"))
        if catalog_files:
            errors.append("frontend_data/catalog still contains generated staging files")

    for warning in warnings:
        print(f"[ARTIFACT_GUARD_WARN] {warning}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"[ARTIFACT_GUARD_ERROR] {error}")
        sys.exit(1)
    print("[ARTIFACT_GUARD_OK]")


if __name__ == "__main__":
    main()
