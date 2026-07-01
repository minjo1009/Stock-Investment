from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from pathlib import Path

from ops_common import ROOT, print_result


SCAN_ROOTS = [
    ".codex",
    "apps",
    "configs",
    "docs",
    "frontend",
    "ops",
    "schemas",
    "scripts",
    "src",
    "tasks",
    "tests",
    "tools",
]

OPTIONAL_ABSENT_ROOTS = [
    ".pytest_cache",
    "config",
    "prompts",
    "skills",
]

GENERATED_DIRS_ABSENT = [
    "apps/ios-trader-brain/node_modules",
    "apps/ios-trader-brain/dist",
    "apps/ios-trader-brain/.expo",
    "frontend/trader-terminal/node_modules",
    "frontend/trader-terminal/dist",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    for root_name in OPTIONAL_ABSENT_ROOTS:
        path = ROOT / root_name
        if path.exists():
            failures.append(f"legacy root alias/cache present: {root_name}")
        else:
            passes.append(f"legacy root absent: {root_name}")

    for rel_path in GENERATED_DIRS_ABSENT:
        path = ROOT / rel_path
        if path.exists():
            failures.append(f"generated dependency/build directory present: {rel_path}")
        else:
            passes.append(f"generated dependency/build directory absent: {rel_path}")

    pycache: list[str] = []
    for root_name in SCAN_ROOTS:
        scan_root = ROOT / root_name
        if not scan_root.exists():
            continue
        pycache.extend(rel(path) for path in scan_root.rglob("__pycache__") if path.is_dir())

    if pycache:
        failures.append(f"python cache directories present: {', '.join(sorted(pycache)[:40])}")
    else:
        passes.append("no python cache directories in managed roots")

    archive_root = ROOT / "docs/archive"
    active_conflicts: list[str] = []
    root_conflict_db = ROOT / "trading-DESKTOP-2R00TB4.db"
    if root_conflict_db.exists():
        warnings.append("root machine-conflict DB remains blocked for owner review: trading-DESKTOP-2R00TB4.db")
    for root_name in [".codex", "apps", "configs", "docs", "frontend", "ops", "schemas", "scripts", "src", "tasks", "tests", "tools"]:
        scan_root = ROOT / root_name
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*DESKTOP-2R00TB4*"):
            if not path.is_file():
                continue
            if is_under(path, archive_root):
                continue
            active_conflicts.append(rel(path))

    if active_conflicts:
        failures.append(f"active DESKTOP conflict files present: {', '.join(sorted(active_conflicts))}")
    else:
        passes.append("no active DESKTOP conflict files outside archive")

    required_archive = ROOT / "docs/archive/task_4194_desktop_conflict_docs"
    if required_archive.exists():
        archived = sorted(path.name for path in required_archive.glob("*DESKTOP-2R00TB4.md"))
        passes.append(f"desktop conflict docs archived: {len(archived)}")
    else:
        warnings.append("TASK-4194 desktop conflict archive folder absent")

    return print_result("INTERNAL CLEANLINESS VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
