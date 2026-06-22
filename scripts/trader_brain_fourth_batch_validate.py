from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task766": {
        "dir": ROOT / "docs" / "reports" / "task_766_compound_interaction_engine_contract",
        "required": [
            "task_766_compound_interaction_engine_contract.md",
            "compound_interaction_engine_contract.md",
            "compound_rule_examples.csv",
            "task_766_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "compound_rule_examples.csv": 10,
        },
        "phrases": [
            "compound_state",
            "single total score",
            "modifier",
            "source_gap",
            "NOT_ACCEPTED",
        ],
    },
    "Task767": {
        "dir": ROOT / "docs" / "reports" / "task_767_candidate_bundle_contract",
        "required": [
            "task_767_candidate_bundle_contract.md",
            "candidate_thesis_bundle_contract.md",
            "bundle_required_fields.csv",
            "task_767_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "bundle_required_fields.csv": 10,
        },
        "phrases": [
            "Candidate",
            "weakest_layer",
            "invalidation",
            "not a trade",
            "NOT_ACCEPTED",
        ],
    },
    "Task768": {
        "dir": ROOT / "docs" / "reports" / "task_768_same_timestamp_slot_competition",
        "required": [
            "task_768_same_timestamp_slot_competition.md",
            "same_timestamp_slot_contract.md",
            "slot_input_catalog.csv",
            "task_768_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "slot_input_catalog.csv": 8,
        },
        "phrases": [
            "same timestamp",
            "cohort",
            "global top5",
            "future PnL",
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
            print(f"[TRADER_BRAIN_FOURTH_BATCH_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_FOURTH_BATCH_OK] Task766/767/768 artifacts are present and non-placeholder")


if __name__ == "__main__":
    main()
