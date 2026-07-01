from __future__ import annotations

import argparse
import csv
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from ops_common import ROOT, ensure_parent, rel


SAFE_DELETE = "SAFE_DELETE"
REVIEW_NEEDED = "REVIEW_NEEDED"
KEEP = "KEEP"


@dataclass(frozen=True)
class Finding:
    path: str
    kind: str
    action: str
    reason: str
    bytes: int


def path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return total


def add_if_exists(findings: list[Finding], path: Path, kind: str, action: str, reason: str) -> None:
    if path.exists():
        findings.append(Finding(rel(path), kind, action, reason, path_size(path)))


def scan() -> list[Finding]:
    findings: list[Finding] = []

    for path in ROOT.iterdir():
        name = path.name
        if name == "__pycache__":
            add_if_exists(findings, path, "python_cache", SAFE_DELETE, "generated Python cache")
        elif name.startswith(".codex_tmp_"):
            add_if_exists(findings, path, "codex_temp", SAFE_DELETE, "temporary Codex cache")
        elif name.startswith(".codex_remote_task"):
            add_if_exists(findings, path, "codex_remote_temp", SAFE_DELETE, "temporary remote Codex task artifact")
        elif "-DESKTOP-" in name and path.suffix.lower() in {".md", ".gitignore"}:
            add_if_exists(findings, path, "onedrive_conflict_text", SAFE_DELETE, "OneDrive desktop conflict copy superseded by canonical file")
        elif "-DESKTOP-" in name and path.suffix.lower() in {".env", ".json"}:
            add_if_exists(findings, path, "sensitive_onedrive_conflict", REVIEW_NEEDED, "local sensitive conflict copy; delete only after explicit secret backup decision")
        elif name.startswith("trading-DESKTOP-") and path.suffix.lower() == ".db":
            add_if_exists(findings, path, "db_onedrive_conflict", REVIEW_NEEDED, "large DB conflict copy; requires data retention decision before delete")

    docs_root = ROOT / "docs"
    if docs_root.exists():
        for path in docs_root.glob("*-DESKTOP-*.md"):
            add_if_exists(findings, path, "onedrive_conflict_doc", SAFE_DELETE, "OneDrive desktop conflict doc superseded by canonical docs")

    for cache_name in [".pytest_cache", ".mypy_cache", ".ruff_cache"]:
        add_if_exists(findings, ROOT / cache_name, "tool_cache", SAFE_DELETE, "generated tool cache")

    return sorted(findings, key=lambda item: item.path)


def write_csv(path: Path, rows: list[Finding]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "kind", "action", "reason", "bytes"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def delete_safe(rows: list[Finding]) -> list[Finding]:
    deleted: list[Finding] = []
    for row in rows:
        if row.action != SAFE_DELETE:
            continue
        target = (ROOT / row.path).resolve()
        if ROOT not in target.parents and target != ROOT:
            raise RuntimeError(f"refusing to delete outside repo: {target}")
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        deleted.append(row)
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/reports/task_4106_l0_efficiency_obsolete_material_cleanup/obsolete_material_inventory.csv")
    parser.add_argument("--deleted-output", default="docs/reports/task_4106_l0_efficiency_obsolete_material_cleanup/deleted_materials.csv")
    parser.add_argument("--deleted-review-output", default="docs/reports/task_4106_l0_efficiency_obsolete_material_cleanup/deleted_review_needed_materials.csv")
    parser.add_argument("--delete-safe", action="store_true")
    parser.add_argument("--delete-review-needed", action="store_true")
    args = parser.parse_args()

    rows = scan()
    write_csv(ROOT / args.output, rows)
    deleted: list[Finding] = []
    if args.delete_safe:
        deleted = delete_safe(rows)
        write_csv(ROOT / args.deleted_output, deleted)
    deleted_review: list[Finding] = []
    if args.delete_review_needed:
        review_rows = [
            Finding(row.path, row.kind, SAFE_DELETE, row.reason, row.bytes)
            for row in rows
            if row.action == REVIEW_NEEDED
        ]
        deleted_review = delete_safe(review_rows)
        write_csv(ROOT / args.deleted_review_output, deleted_review)

    safe_count = sum(1 for row in rows if row.action == SAFE_DELETE)
    review_count = sum(1 for row in rows if row.action == REVIEW_NEEDED)
    safe_bytes = sum(row.bytes for row in rows if row.action == SAFE_DELETE)
    deleted_bytes = sum(row.bytes for row in deleted)
    print(f"PASS inventory: {args.output}")
    print(f"PASS safe_delete_candidates: {safe_count}")
    print(f"PASS review_needed_candidates: {review_count}")
    print(f"PASS safe_delete_bytes: {safe_bytes}")
    if args.delete_safe:
        print(f"PASS deleted_count: {len(deleted)}")
        print(f"PASS deleted_bytes: {deleted_bytes}")
        print(f"PASS deleted_manifest: {args.deleted_output}")
    if args.delete_review_needed:
        print(f"PASS deleted_review_needed_count: {len(deleted_review)}")
        print(f"PASS deleted_review_needed_bytes: {sum(row.bytes for row in deleted_review)}")
        print(f"PASS deleted_review_needed_manifest: {args.deleted_review_output}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
