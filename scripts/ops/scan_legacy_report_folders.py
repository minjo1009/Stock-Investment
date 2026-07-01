from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from ops_common import ROOT, ensure_parent, rel


REPORTS_ROOT = ROOT / "docs" / "reports"


@dataclass(frozen=True)
class LegacyReportFolder:
    path: str
    files: int
    bytes: int
    action: str
    reason: str


def folder_stats(path: Path) -> tuple[int, int]:
    files = 0
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            files += 1
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return files, total


def scan() -> list[LegacyReportFolder]:
    if not REPORTS_ROOT.exists():
        return []
    rows: list[LegacyReportFolder] = []
    for path in sorted(REPORTS_ROOT.iterdir()):
        if path.is_file():
            rows.append(
                LegacyReportFolder(
                    path=rel(path),
                    files=1,
                    bytes=path.stat().st_size,
                    action="DELETE_OBSOLETE_LEGACY_REPORT_FILE",
                    reason="top-level docs/reports file violates current task-folder report rule",
                )
            )
            continue
        if not path.is_dir() or path.name.startswith("task_"):
            continue
        files, total = folder_stats(path)
        rows.append(
            LegacyReportFolder(
                path=rel(path),
                files=files,
                bytes=total,
                action="DELETE_OBSOLETE_LEGACY_REPORT_FOLDER",
                reason="violates current docs/reports/task_* report folder rule and is flagged by doc registry validation",
            )
        )
    return rows


def write_csv(path: Path, rows: list[LegacyReportFolder]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "files", "bytes", "action", "reason"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def delete_rows(rows: list[LegacyReportFolder]) -> list[LegacyReportFolder]:
    deleted: list[LegacyReportFolder] = []
    reports_root = REPORTS_ROOT.resolve()
    for row in rows:
        target = (ROOT / row.path).resolve()
        if reports_root not in target.parents:
            raise RuntimeError(f"refusing to delete outside docs/reports: {target}")
        if target.is_dir() and target.name.startswith("task_"):
            raise RuntimeError(f"refusing to delete task report folder: {target}")
        if target.exists() and target.is_file():
            target.unlink()
            deleted.append(row)
        elif target.exists():
            def onexc(func, path, exc_info):
                try:
                    os.chmod(path, 0o700)
                    func(path)
                except Exception:
                    raise

            shutil.rmtree(target, onexc=onexc)
            deleted.append(row)
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/reports/task_4107_legacy_report_folder_cleanup/legacy_report_folder_inventory.csv")
    parser.add_argument("--deleted-output", default="docs/reports/task_4107_legacy_report_folder_cleanup/deleted_legacy_report_folders.csv")
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

    rows = scan()
    write_csv(ROOT / args.output, rows)
    deleted: list[LegacyReportFolder] = []
    if args.delete:
        deleted = delete_rows(rows)
        write_csv(ROOT / args.deleted_output, deleted)
    print(f"PASS inventory: {args.output}")
    print(f"PASS legacy_report_folders: {len(rows)}")
    print(f"PASS legacy_report_files: {sum(row.files for row in rows)}")
    print(f"PASS legacy_report_bytes: {sum(row.bytes for row in rows)}")
    if args.delete:
        print(f"PASS deleted_folders: {len(deleted)}")
        print(f"PASS deleted_files: {sum(row.files for row in deleted)}")
        print(f"PASS deleted_bytes: {sum(row.bytes for row in deleted)}")
        print(f"PASS deleted_manifest: {args.deleted_output}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
