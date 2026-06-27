from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REQUIRED_COLUMNS = {
    "active_id",
    "title",
    "status",
    "domain",
    "owner",
    "reviewer",
    "read_scope",
    "write_scope",
    "forbidden_actions",
    "deliverables",
    "validation",
    "report_path",
    "next_blocker",
}

ALLOWED_STATUSES = {
    "active",
    "blocked",
    "blocked_reference_required",
    "blocked_user_approval",
    "completed",
    "pending",
    "superseded",
}


def validate_active_registry(path: Path, *, root: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing active registry: {path}"]

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        return ["active registry has no rows"]

    columns = set(rows[0].keys())
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"missing columns: {','.join(sorted(missing))}")

    seen: set[str] = set()
    active_or_blocked_count = 0
    for idx, row in enumerate(rows, start=2):
        active_id = str(row.get("active_id", "")).strip()
        status = str(row.get("status", "")).strip()
        if not active_id:
            errors.append(f"row {idx}: empty active_id")
            continue
        if active_id in seen:
            errors.append(f"row {idx}: duplicate active_id={active_id}")
        seen.add(active_id)

        if status not in ALLOWED_STATUSES:
            errors.append(f"{active_id}: unsupported status={status}")
        if status in {"active", "blocked", "blocked_reference_required", "blocked_user_approval"}:
            active_or_blocked_count += 1

        for field in [
            "title",
            "domain",
            "owner",
            "reviewer",
            "read_scope",
            "write_scope",
            "forbidden_actions",
            "deliverables",
            "validation",
            "report_path",
        ]:
            if not str(row.get(field, "")).strip():
                errors.append(f"{active_id}: missing {field}")

        report_path = str(row.get("report_path", "")).strip()
        if report_path and not (root / report_path).exists():
            errors.append(f"{active_id}: report_path does not exist: {report_path}")

        if status != "completed" and not str(row.get("next_blocker", "")).strip():
            errors.append(f"{active_id}: non-completed row missing next_blocker")

    if active_or_blocked_count == 0:
        errors.append("no active or blocked work item remains visible")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("tasks/active_task_registry.csv"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = validate_active_registry(args.registry, root=args.root)
    if errors:
        for error in errors:
            print(f"[ACTIVE_REGISTRY_ERROR] {error}")
        sys.exit(1)
    print(f"[ACTIVE_REGISTRY_OK] {args.registry}")


if __name__ == "__main__":
    main()

