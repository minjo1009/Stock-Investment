from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task759": {
        "dir": ROOT / "docs" / "reports" / "task_759_l2_primitive_fact_contract",
        "required": [
            "task_759_l2_primitive_fact_contract.md",
            "primitive_fact_contract.md",
            "primitive_fact_catalog.csv",
            "task_759_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "primitive_fact_catalog.csv": 9,
        },
        "phrases": [
            "PrimitiveFact",
            "non-directional",
            "missing fact",
            "buy/sell",
            "NOT_ACCEPTED",
        ],
    },
    "Task760": {
        "dir": ROOT / "docs" / "reports" / "task_760_l3_pragmatic_meaning_contract",
        "required": [
            "task_760_l3_pragmatic_meaning_contract.md",
            "l3_pragmatic_meaning_contract.md",
            "meaning_taxonomy.csv",
            "task_760_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "meaning_taxonomy.csv": 12,
        },
        "phrases": [
            "MeaningObject",
            "direction hint",
            "relation_ready_tier",
            "not a trade instruction",
            "NOT_ACCEPTED",
        ],
    },
    "Task762": {
        "dir": ROOT / "docs" / "reports" / "task_762_primitive_gate_repair_design",
        "required": [
            "task_762_primitive_gate_repair_design.md",
            "primitive_gate_repair_contract.md",
            "gate_state_catalog.csv",
            "task_762_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "gate_state_catalog.csv": 5,
        },
        "phrases": [
            "primitive_fact_gate_pass",
            "primitive_fact_adapter_gate_state",
            "pass",
            "context_only",
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
        for path in task_dir.glob("*.md")
        if path.is_file()
    )
    for phrase in spec["phrases"]:
        if phrase not in report_text:
            errors.append(f"{task_id}: missing phrase {phrase}")
    return errors


def main() -> None:
    errors: list[str] = []
    for task_id, spec in TASKS.items():
        errors.extend(validate_task(task_id, spec))
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_SECOND_BATCH_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_SECOND_BATCH_OK] Task759/760/762 artifacts are present and non-placeholder")


if __name__ == "__main__":
    main()
