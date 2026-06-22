from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task757": {
        "dir": ROOT / "docs" / "reports" / "task_757_brain_dependency_dag_supersession",
        "required": [
            "task_757_brain_dependency_dag_supersession.md",
            "brain_dependency_dag.csv",
            "current_supersession_map.csv",
            "task_757_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "brain_dependency_dag.csv": 10,
            "current_supersession_map.csv": 10,
        },
        "phrases": [
            "Task727",
            "Task742",
            "current",
            "superseded",
            "NOT_ACCEPTED",
        ],
    },
    "Task758": {
        "dir": ROOT / "docs" / "reports" / "task_758_l1_evidence_contract",
        "required": [
            "task_758_l1_evidence_contract.md",
            "l1_evidence_contract.md",
            "l1_source_family_policy.csv",
            "task_758_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "l1_source_family_policy.csv": 7,
        },
        "phrases": [
            "good-enough",
            "context",
            "source text",
            "buy/sell",
            "missing",
            "NOT_ACCEPTED",
        ],
    },
    "Task761": {
        "dir": ROOT / "docs" / "reports" / "task_761_task742_to_task729_adapter_contract",
        "required": [
            "task_761_task742_to_task729_adapter_contract.md",
            "task742_task729_adapter_contract.md",
            "adapter_field_map.csv",
            "adapter_representative_replay_examples.csv",
            "task_761_decision.csv",
            "artifact_manifest.csv",
        ],
        "csv_min_rows": {
            "adapter_field_map.csv": 8,
            "adapter_representative_replay_examples.csv": 10,
        },
        "phrases": [
            "Task742",
            "Task729",
            "primitive_fact_gate_pass",
            "No assignment output",
            "Representative Replay",
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
            print(f"[TRADER_BRAIN_FIRST_BATCH_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_FIRST_BATCH_OK] Task757/758/761 artifacts are present and non-placeholder")


if __name__ == "__main__":
    main()
