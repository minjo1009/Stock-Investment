from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task769": {
        "dir": ROOT / "docs" / "reports" / "task_769_resolver_conflict_layer",
        "required": [
            "task_769_resolver_conflict_layer.md",
            "resolver_conflict_contract.md",
            "conflict_state_catalog.csv",
            "task_769_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "conflict_state_catalog.csv": 10,
        },
        "phrases": [
            "repair_needed",
            "review_needed",
            "silent default pass",
            "GPT-only",
            "NOT_ACCEPTED",
        ],
    },
    "Task770": {
        "dir": ROOT / "docs" / "reports" / "task_770_brain_contract_validation",
        "required": [
            "task_770_brain_contract_validation.md",
            "brain_validation_registry.csv",
            "validation_gate_catalog.csv",
            "task_770_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "validation_gate_catalog.csv": 12,
        },
        "phrases": [
            "layer_jump",
            "forbidden_output",
            "outcome_leakage",
            "not strategy acceptance",
            "NOT_ACCEPTED",
        ],
    },
    "Task771": {
        "dir": ROOT / "docs" / "reports" / "task_771_canonical_brain_registry",
        "required": [
            "task_771_canonical_brain_registry.md",
            "canonical_brain_registry.csv",
            "future_backtest_gate_contract.md",
            "task_771_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "canonical_brain_registry.csv": 15,
        },
        "phrases": [
            "canonical",
            "future backtest",
            "not executing",
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

    task_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in list(task_dir.glob("*.md")) + list(task_dir.glob("*.csv"))
        if path.is_file()
    ).lower()
    for phrase in spec["phrases"]:
        if phrase.lower() not in task_text:
            errors.append(f"{task_id}: missing phrase {phrase}")
    return errors


def main() -> None:
    errors: list[str] = []
    for task_id, spec in TASKS.items():
        errors.extend(validate_task(task_id, spec))
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_FINAL_BATCH_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_FINAL_BATCH_OK] Task769/770/771 artifacts are present and non-placeholder")


if __name__ == "__main__":
    main()
