from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task802": (
        ROOT / "docs" / "reports" / "task_802_backend_engineer_quality_review",
        ["backend_engineer_review_matrix.csv", "task_802_backend_engineer_quality_review.md", "task_802_decision.csv", "artifact_manifest.csv"],
    ),
    "Task803": (
        ROOT / "docs" / "reports" / "task_803_validator_strictness_upgrade",
        ["validator_strictness_checks.csv", "task_803_validator_strictness_upgrade.md", "task_803_decision.csv", "artifact_manifest.csv"],
    ),
    "Task804": (
        ROOT / "docs" / "reports" / "task_804_schema_manifest_invariant_contract",
        ["schema_manifest_invariants.csv", "task_804_schema_manifest_invariant_contract.md", "task_804_decision.csv", "artifact_manifest.csv"],
    ),
    "Task805": (
        ROOT / "docs" / "reports" / "task_805_negative_fixture_safety_pack",
        ["negative_fixture_catalog.csv", "task_805_negative_fixture_safety_pack.md", "task_805_decision.csv", "artifact_manifest.csv"],
    ),
    "Task806": (
        ROOT / "docs" / "reports" / "task_806_safe_implementation_handoff",
        ["backend_safe_implementation_packet.md", "task_806_safe_implementation_handoff.md", "task_806_decision.csv", "artifact_manifest.csv"],
    ),
}


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

    review_matrix = TASKS["Task802"][0] / "backend_engineer_review_matrix.csv"
    if review_matrix.exists() and len(read_csv(review_matrix)) != 5:
        errors.append("Task802: expected exactly 5 backend engineer review rows")

    strictness = TASKS["Task803"][0] / "validator_strictness_checks.csv"
    if strictness.exists() and len(read_csv(strictness)) < 8:
        errors.append("Task803: expected at least 8 strictness checks")

    fixtures = TASKS["Task805"][0] / "negative_fixture_catalog.csv"
    if fixtures.exists() and len(read_csv(fixtures)) < 7:
        errors.append("Task805: expected at least 7 negative fixtures")

    handoff = TASKS["Task806"][0] / "backend_safe_implementation_packet.md"
    if handoff.exists():
        text = handoff.read_text(encoding="utf-8", errors="replace").lower()
        required = [
            "relationship graph validator first",
            "no backtest execution",
            "no runtime or broker integration",
            "no missing-to-negative conversion",
        ]
        for phrase in required:
            if phrase not in text:
                errors.append(f"Task806 handoff missing phrase: {phrase}")

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
        "no buy/sell",
        "research_only",
    ]:
        if phrase not in combined:
            errors.append(f"missing required phrase: {phrase}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_BACKEND_SAFETY_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_BACKEND_SAFETY_OK] Task802-Task806 backend safety artifacts are present")


if __name__ == "__main__":
    main()
