from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task763": {
        "dir": ROOT / "docs" / "reports" / "task_763_typed_relation_edge_schema",
        "required": [
            "task_763_typed_relation_edge_schema.md",
            "typed_relation_edge_schema.md",
            "relation_type_catalog.csv",
            "task_763_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "relation_type_catalog.csv": 7,
        },
        "phrases": [
            "RelationEdge",
            "reinforcing",
            "offsetting",
            "invalidation",
            "NOT_ACCEPTED",
        ],
    },
    "Task764": {
        "dir": ROOT / "docs" / "reports" / "task_764_source_circuit_good_enough_interpreters",
        "required": [
            "task_764_source_circuit_good_enough_interpreters.md",
            "source_circuit_good_enough_policy.md",
            "circuit_state_catalog.csv",
            "task_764_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "circuit_state_catalog.csv": 8,
        },
        "phrases": [
            "good-enough",
            "Form4",
            "financing",
            "blanket block",
            "NOT_ACCEPTED",
        ],
    },
    "Task765": {
        "dir": ROOT / "docs" / "reports" / "task_765_modifier_contracts_regime_sector_price",
        "required": [
            "task_765_modifier_contracts_regime_sector_price.md",
            "modifier_contracts.md",
            "modifier_state_catalog.csv",
            "task_765_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "modifier_state_catalog.csv": 7,
        },
        "phrases": [
            "modifier",
            "supportive",
            "hostile",
            "price acceptance",
            "NOT_ACCEPTED",
        ],
    },
}


def csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def validate_task(task_id: str, spec: dict[str, object]) -> list[str]:
    errors: list[str] = []
    task_dir = spec["dir"]
    assert isinstance(task_dir, Path)
    if not task_dir.exists():
        return [f"{task_id}: missing directory {task_dir}"]

    for name in spec["required"]:
        path = task_dir / name
        if not path.exists():
            errors.append(f"{task_id}: missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{task_id}: empty {name}")

    for name, min_rows in spec["csv_min_rows"].items():
        path = task_dir / name
        if path.exists() and csv_row_count(path) < min_rows:
            errors.append(f"{task_id}: {name} has fewer than {min_rows} data rows")

    report_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in list(task_dir.glob("*.md")) + list(task_dir.glob("*.csv"))
        if path.is_file()
    )
    for phrase in spec["phrases"]:
        if phrase.lower() not in report_text.lower():
            errors.append(f"{task_id}: missing phrase {phrase}")
    return errors


def main() -> None:
    errors: list[str] = []
    for task_id, spec in TASKS.items():
        errors.extend(validate_task(task_id, spec))
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_THIRD_BATCH_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_THIRD_BATCH_OK] Task763/764/765 artifacts are present and non-placeholder")


if __name__ == "__main__":
    main()
