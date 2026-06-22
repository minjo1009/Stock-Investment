from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task807": (
        ROOT / "docs" / "reports" / "task_807_relationship_graph_validator_implementation",
        ["task_807_relationship_graph_validator_implementation.md", "subagent_packet_plan.md", "task_807_decision.csv", "artifact_manifest.csv"],
    ),
    "Task808": (
        ROOT / "docs" / "reports" / "task_808_negative_fixture_test_harness",
        ["task_808_negative_fixture_test_harness.md", "task_808_decision.csv", "artifact_manifest.csv"],
    ),
    "Task809": (
        ROOT / "docs" / "reports" / "task_809_task773_packet_validator_implementation",
        ["task_809_task773_packet_validator_implementation.md", "task_809_decision.csv", "artifact_manifest.csv"],
    ),
    "Task810": (
        ROOT / "docs" / "reports" / "task_810_cross_layer_jump_guard",
        ["task_810_cross_layer_jump_guard.md", "task_810_decision.csv", "artifact_manifest.csv"],
    ),
    "Task811": (
        ROOT / "docs" / "reports" / "task_811_temporal_coherence_guard",
        ["task_811_temporal_coherence_guard.md", "task_811_decision.csv", "artifact_manifest.csv"],
    ),
}

IMPLEMENTATION_FILES = [
    ROOT / "scripts" / "trader_brain_relationship_graph_packet_validate.py",
    ROOT / "scripts" / "trader_brain_attention_packet_validate.py",
    ROOT / "tests" / "test_trader_brain_relationship_graph_packet_validator.py",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for task_id, (directory, required_files) in TASKS.items():
        if not directory.exists():
            errors.append(f"{task_id}: missing directory {directory}")
            continue
        for name in required_files:
            path = directory / name
            if not path.exists():
                errors.append(f"{task_id}: missing {name}")
            elif path.stat().st_size == 0:
                errors.append(f"{task_id}: empty {name}")

    for path in IMPLEMENTATION_FILES:
        if not path.exists():
            errors.append(f"missing implementation file {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty implementation file {path}")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory, _ in TASKS.values()
        for path in directory.glob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    ).lower()
    for phrase in [
        "not_accepted",
        "diagnostic_only_not_deployment_ready",
        "forbidden",
        "no runtime",
        "no backtest",
        "research_only",
    ]:
        if phrase not in combined:
            errors.append(f"missing required phrase: {phrase}")

    decisions = [TASKS[task_id][0] / f"task_{task_id.replace('Task', '').lower()}_decision.csv" for task_id in TASKS]
    for decision in decisions:
        if decision.exists():
            rows = read_csv(decision)
            values = {row.get("field", ""): row.get("value", "") for row in rows}
            if values.get("strategy_acceptance") != "NOT_ACCEPTED":
                errors.append(f"{decision}: strategy_acceptance must remain NOT_ACCEPTED")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_VALIDATOR_IMPLEMENTATION_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_VALIDATOR_IMPLEMENTATION_OK] Task807-Task811 validator implementation artifacts are present")


if __name__ == "__main__":
    main()
