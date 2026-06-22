from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT / "docs" / "reports" / "task_756_trader_brain_15_step_program"
STEP_REGISTRY = PARENT_DIR / "step_registry.csv"

REQUIRED_STEP_COLUMNS = {
    "task_id",
    "title",
    "brain_layer",
    "owner_team",
    "objective",
    "success_criteria",
    "forbidden_actions",
    "minimal_artifacts",
    "validation_command",
    "overengineering_stop_rule",
}

REQUIRED_LAYERS = {
    "source_evidence",
    "primitive_fact",
    "economic_meaning",
    "relation_edge",
    "candidate_bundle",
    "slot_decision",
    "qa_resolver",
}

FORBIDDEN_WORDS_IN_OBJECTIVE = {
    "buy",
    "sell",
    "sizing",
    "accepted strategy",
    "deployment ready",
    "real capital",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def task_dir_for(task_id: str, slug: str) -> Path:
    task_no = task_id.replace("Task", "").lower()
    return ROOT / "docs" / "reports" / f"task_{task_no}_{slug}"


def validate() -> list[str]:
    errors: list[str] = []
    if not STEP_REGISTRY.exists():
        return [f"missing {STEP_REGISTRY}"]

    rows = read_rows(STEP_REGISTRY)
    if len(rows) != 15:
        errors.append(f"expected 15 steps, observed {len(rows)}")

    columns = set(rows[0].keys()) if rows else set()
    missing_columns = REQUIRED_STEP_COLUMNS - columns
    if missing_columns:
        errors.append(f"step_registry missing columns: {','.join(sorted(missing_columns))}")

    expected_ids = [f"Task{task_no}" for task_no in range(757, 772)]
    observed_ids = [row.get("task_id", "") for row in rows]
    if observed_ids != expected_ids:
        errors.append(f"expected task ids {expected_ids}, observed {observed_ids}")

    observed_layers = {row.get("brain_layer", "") for row in rows}
    missing_layers = REQUIRED_LAYERS - observed_layers
    if missing_layers:
        errors.append(f"missing brain layers: {','.join(sorted(missing_layers))}")

    for row in rows:
        task_id = row.get("task_id", "")
        slug = row.get("slug", "")
        if not slug:
            errors.append(f"{task_id}: missing slug")
            continue
        task_dir = task_dir_for(task_id, slug)
        task_no = task_id.replace("Task", "").lower()
        report = task_dir / f"task_{task_no}_{slug}.md"
        decision = task_dir / f"task_{task_no}_decision.csv"
        if not report.exists():
            errors.append(f"{task_id}: missing report {report}")
        if not decision.exists():
            errors.append(f"{task_id}: missing decision {decision}")
        objective = row.get("objective", "").lower()
        for word in FORBIDDEN_WORDS_IN_OBJECTIVE:
            if word in objective:
                errors.append(f"{task_id}: objective contains forbidden wording {word}")
        if "no" not in row.get("forbidden_actions", "").lower():
            errors.append(f"{task_id}: forbidden_actions does not contain explicit no-rule")
        if not row.get("overengineering_stop_rule", "").strip():
            errors.append(f"{task_id}: missing overengineering stop rule")

    parent_required = [
        PARENT_DIR / "task_756_trader_brain_15_step_program.md",
        PARENT_DIR / "task756_summary.csv",
        PARENT_DIR / "task_756_decision.csv",
        PARENT_DIR / "gpt_review_notes.md",
        PARENT_DIR / "subagent_packet_plan.md",
        PARENT_DIR / "validation_log.md",
    ]
    for path in parent_required:
        if not path.exists():
            errors.append(f"missing parent artifact {path}")

    parent_report = (PARENT_DIR / "task_756_trader_brain_15_step_program.md").read_text(encoding="utf-8")
    required_statuses = [
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "Missing data != negative label",
        "GPT review != source-of-truth",
    ]
    for phrase in required_statuses:
        if phrase not in parent_report:
            errors.append(f"parent report missing phrase: {phrase}")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_PROGRAM_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_PROGRAM_OK] Task756 parent and Task757-Task771 steps are registered")


if __name__ == "__main__":
    main()
