from __future__ import annotations

import argparse
import csv
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from ops_common import ROOT, ensure_parent, rel


ARTIFACT_ROOT = ROOT / "data" / "artifacts"
REPORT_DIR = ROOT / "docs" / "reports" / "task_4112_historical_data_artifact_retention_cleanup"
DEFAULT_INVENTORY = REPORT_DIR / "historical_data_artifact_inventory.csv"
DEFAULT_DELETED = REPORT_DIR / "deleted_historical_data_artifacts.csv"

REFERENCE_GLOBS = [
    "AGENTS.md",
    "L0_DESKTOP_CODEX_HANDOFF.md",
    "ops/*.yaml",
    "docs/active/*.md",
    "docs/architecture/*.md",
    "docs/db/*.md",
    "docs/frontend_app_ssot/*.md",
    "docs/llm_wiki/*.md",
    "docs/operating_system/*.md",
    "docs/ownership/*.md",
]

PROTECTED_PREFIXES = (
    "task_410",
    "task_411",
)


@dataclass(frozen=True)
class Finding:
    path: str
    files: int
    bytes: int
    action: str
    reason: str


def read_reference_text() -> str:
    chunks: list[str] = []
    for pattern in REFERENCE_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file():
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def referenced_artifact_dirs(text: str) -> set[str]:
    refs: set[str] = set()
    pattern = re.compile(r"data/artifacts/([A-Za-z0-9_.-]+)")
    for match in pattern.finditer(text):
        refs.add(match.group(1).rstrip("/."))
    return refs


def referenced_task_numbers(text: str) -> set[str]:
    refs: set[str] = set()
    for match in re.finditer(r"\b[Tt]ask[-_ ]?(\d{3,4})\b", text):
        refs.add(match.group(1))
    for match in re.finditer(r"\btask_(\d{3,4})(?:_|/|\b)", text):
        refs.add(match.group(1))
    return refs


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


def task_number_from_dir(name: str) -> str | None:
    match = re.match(r"task_(\d{3,4})(?:_|$)", name)
    if match:
        return match.group(1)
    return None


def classify(path: Path, artifact_refs: set[str], task_refs: set[str]) -> Finding:
    files, total = folder_stats(path)
    name = path.name
    if not name.startswith("task_"):
        return Finding(rel(path), files, total, "IGNORE_NON_TASK_ARTIFACT", "outside historical task artifact cleanup scope")
    if name.startswith(PROTECTED_PREFIXES):
        return Finding(rel(path), files, total, "KEEP_CURRENT_GOVERNANCE_ARTIFACT", "current governance task artifact")
    if name in artifact_refs:
        return Finding(rel(path), files, total, "KEEP_REFERENCED_ARTIFACT", "explicitly referenced by current operating documents")
    task_no = task_number_from_dir(name)
    if task_no and task_no in task_refs:
        return Finding(rel(path), files, total, "KEEP_REFERENCED_TASK_ARTIFACT", "task number referenced by current operating documents")
    return Finding(rel(path), files, total, "DELETE_UNREFERENCED_HISTORICAL_TASK_ARTIFACT", "task artifact not referenced by current operating documents")


def scan() -> list[Finding]:
    if not ARTIFACT_ROOT.exists():
        return []
    text = read_reference_text()
    artifact_refs = referenced_artifact_dirs(text)
    task_refs = referenced_task_numbers(text)
    return [classify(path, artifact_refs, task_refs) for path in sorted(ARTIFACT_ROOT.iterdir()) if path.is_dir()]


def write_csv(path: Path, rows: list[Finding]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(Finding.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def delete_rows(rows: list[Finding]) -> list[Finding]:
    deleted: list[Finding] = []
    artifact_root = ARTIFACT_ROOT.resolve()
    for row in rows:
        if row.action != "DELETE_UNREFERENCED_HISTORICAL_TASK_ARTIFACT":
            continue
        target = (ROOT / row.path).resolve()
        if artifact_root not in target.parents:
            raise RuntimeError(f"refusing to delete outside data/artifacts: {target}")
        if not target.name.startswith("task_"):
            raise RuntimeError(f"refusing to delete non-task artifact: {target}")
        if target.name.startswith(PROTECTED_PREFIXES):
            raise RuntimeError(f"refusing to delete current governance artifact: {target}")
        if target.exists():
            shutil.rmtree(target)
            deleted.append(row)
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--deleted-output", default=str(DEFAULT_DELETED))
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

    rows = scan()
    write_csv(ROOT / args.inventory, rows)
    print(f"PASS inventory: {args.inventory}")
    print(f"PASS artifact_dirs_seen: {len(rows)}")
    for action in sorted({row.action for row in rows}):
        subset = [row for row in rows if row.action == action]
        print(f"PASS {action}: {len(subset)} dirs, {sum(row.files for row in subset)} files, {sum(row.bytes for row in subset)} bytes")
    if args.delete:
        deleted = delete_rows(rows)
        write_csv(ROOT / args.deleted_output, deleted)
        print(f"PASS deleted_dirs: {len(deleted)}")
        print(f"PASS deleted_files: {sum(row.files for row in deleted)}")
        print(f"PASS deleted_bytes: {sum(row.bytes for row in deleted)}")
        print(f"PASS deleted_manifest: {args.deleted_output}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
