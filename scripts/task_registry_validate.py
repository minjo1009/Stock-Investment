from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REQUIRED_COLUMNS = {
    "task_id",
    "title",
    "owner_team",
    "status",
    "canonical_state",
    "strategy_acceptance",
    "data_readiness",
    "parent_task",
    "key_report",
    "key_decision",
    "key_artifacts",
    "validation_command",
    "notes",
}


def validate_registry(path: Path, *, root: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing registry: {path}"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return ["registry has no rows"]
    columns = set(rows[0].keys())
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"missing columns: {','.join(sorted(missing))}")
    seen: set[str] = set()
    canonical_count = 0
    for idx, row in enumerate(rows, start=2):
        task_id = str(row.get("task_id", "")).strip()
        if not task_id:
            errors.append(f"row {idx}: empty task_id")
            continue
        if task_id in seen:
            errors.append(f"row {idx}: duplicate task_id={task_id}")
        seen.add(task_id)
        if str(row.get("canonical_state", "")).strip() == "canonical":
            canonical_count += 1
        for field in ["key_report", "key_decision", "key_artifacts"]:
            value = str(row.get(field, "")).strip()
            if value and not (root / value).exists():
                errors.append(f"{task_id}: {field} does not exist: {value}")
        if not str(row.get("validation_command", "")).strip():
            errors.append(f"{task_id}: missing validation_command")
    if canonical_count == 0:
        errors.append("no canonical tasks registered")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("tasks/task_registry.csv"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = validate_registry(args.registry, root=args.root)
    if errors:
        for error in errors:
            print(f"[REGISTRY_ERROR] {error}")
        sys.exit(1)
    print(f"[REGISTRY_OK] {args.registry}")


if __name__ == "__main__":
    main()
