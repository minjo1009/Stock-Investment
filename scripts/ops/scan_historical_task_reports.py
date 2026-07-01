from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from ops_common import ROOT, ensure_parent, rel


REPORTS_ROOT = ROOT / "docs" / "reports"
REFERENCE_FILES = [
    "docs/ownership/current_operating_model.md",
    "docs/operating_system/project_operating_state.md",
    "ops/doc_registry.yaml",
    "ops/task_registry.yaml",
]


@dataclass(frozen=True)
class TaskReportFinding:
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


def referenced_report_dirs() -> set[str]:
    refs: set[str] = set()
    pattern = re.compile(r"docs/reports/(task_[A-Za-z0-9_\-]+)")
    for ref_file in REFERENCE_FILES:
        path = ROOT / ref_file
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in pattern.finditer(text):
            refs.add(f"docs/reports/{match.group(1)}")
    return refs


def scan() -> tuple[list[TaskReportFinding], set[str]]:
    refs = referenced_report_dirs()
    findings: list[TaskReportFinding] = []
    if not REPORTS_ROOT.exists():
        return findings, refs
    for path in sorted(REPORTS_ROOT.iterdir()):
        if not path.is_dir() or not path.name.startswith("task_"):
            continue
        rpath = rel(path)
        files, total = folder_stats(path)
        if path.name.startswith("task_410"):
            action = "KEEP"
            reason = "current L0/governance cleanup task report"
        elif rpath in refs:
            action = "KEEP"
            reason = "referenced by current operating model or governance registry"
        else:
            action = "DELETE_OBSOLETE_TASK_REPORT"
            reason = "not referenced by current operating model or governance registry"
        findings.append(TaskReportFinding(rpath, files, total, action, reason))
    return findings, refs


def write_csv(path: Path, rows: list[TaskReportFinding]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "files", "bytes", "action", "reason"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def delete_rows(rows: list[TaskReportFinding]) -> list[TaskReportFinding]:
    deleted: list[TaskReportFinding] = []
    reports_root = REPORTS_ROOT.resolve()
    for row in rows:
        if row.action != "DELETE_OBSOLETE_TASK_REPORT":
            continue
        target = (ROOT / row.path).resolve()
        if reports_root not in target.parents:
            raise RuntimeError(f"refusing to delete outside docs/reports: {target}")
        if not target.name.startswith("task_"):
            raise RuntimeError(f"refusing to delete non-task report folder: {target}")
        if target.name.startswith("task_410"):
            raise RuntimeError(f"refusing to delete governance cleanup report folder: {target}")
        if target.exists():
            def onexc(func, path, exc_info):
                os.chmod(path, 0o700)
                func(path)

            shutil.rmtree(target, onexc=onexc)
            deleted.append(row)
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/reports/task_4108_historical_task_report_cleanup/historical_task_report_inventory.csv")
    parser.add_argument("--deleted-output", default="docs/reports/task_4108_historical_task_report_cleanup/deleted_historical_task_reports.csv")
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

    rows, refs = scan()
    write_csv(ROOT / args.output, rows)
    deleted: list[TaskReportFinding] = []
    if args.delete:
        deleted = delete_rows(rows)
        write_csv(ROOT / args.deleted_output, deleted)
    delete_rows_count = sum(1 for row in rows if row.action == "DELETE_OBSOLETE_TASK_REPORT")
    keep_rows_count = sum(1 for row in rows if row.action == "KEEP")
    print(f"PASS inventory: {args.output}")
    print(f"PASS referenced_report_dirs: {len(refs)}")
    print(f"PASS keep_task_report_dirs: {keep_rows_count}")
    print(f"PASS delete_task_report_dirs: {delete_rows_count}")
    print(f"PASS delete_task_report_files: {sum(row.files for row in rows if row.action == 'DELETE_OBSOLETE_TASK_REPORT')}")
    print(f"PASS delete_task_report_bytes: {sum(row.bytes for row in rows if row.action == 'DELETE_OBSOLETE_TASK_REPORT')}")
    if args.delete:
        print(f"PASS deleted_dirs: {len(deleted)}")
        print(f"PASS deleted_files: {sum(row.files for row in deleted)}")
        print(f"PASS deleted_bytes: {sum(row.bytes for row in deleted)}")
        print(f"PASS deleted_manifest: {args.deleted_output}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
