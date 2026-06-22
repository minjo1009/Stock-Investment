from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT / "docs" / "reports" / "task_772_trader_brain_precision_program"
STEP_REGISTRY = PARENT_DIR / "step_registry.csv"

EXPECTED_TASKS = {
    "Task772": "trader_brain_precision_program",
    "Task773": "attention_budget_contract",
    "Task774": "salience_triage_contract",
    "Task775": "working_memory_state_contract",
    "Task776": "hypothesis_ladder_contract",
    "Task777": "contradiction_pressure_contract",
    "Task778": "disconfirming_evidence_minimal_pack",
    "Task779": "decision_journal_trace_contract",
    "Task780": "controlled_adapter_boundary_contract",
    "Task781": "program_governance_closeout",
}

TASK_REQUIRED_EXTRA_FILES = {
    "Task773": [
        "intake_state_catalog.csv",
        "minimal_input_packet_schema.csv",
        "expert_lens_budget.csv",
    ],
    "Task774": ["salience_class_catalog.csv"],
    "Task775": ["working_memory_slot_catalog.csv"],
    "Task776": ["hypothesis_state_catalog.csv"],
    "Task777": ["contradiction_pressure_catalog.csv"],
    "Task778": ["disconfirming_evidence_checklist.csv"],
    "Task779": ["decision_journal_trace_schema.csv"],
    "Task780": ["adapter_boundary_io.csv"],
    "Task781": ["precision_program_closeout.csv"],
}

REQUIRED_COLUMNS = {
    "task_id",
    "slug",
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

FORBIDDEN_PHRASES = {
    "strategy accepted",
    "deployment ready",
    "real capital allowed",
    "backtest executed: yes",
    "real capital: allowed",
}

REQUIRED_PARENT_FILES = [
    "task_772_trader_brain_precision_program.md",
    "step_registry.csv",
    "gpt_review_packet.md",
    "gpt_institutional_backend_review_summary.csv",
    "subagent_packet_plan.md",
    "task772_summary.csv",
    "task_772_decision.csv",
    "validation_log.md",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def task_dir(task_id: str, slug: str) -> Path:
    task_number = task_id.replace("Task", "").lower()
    return ROOT / "docs" / "reports" / f"task_{task_number}_{slug}"


def collect_text(paths: list[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        if path.exists() and path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks).lower()


def validate() -> list[str]:
    errors: list[str] = []
    if not STEP_REGISTRY.exists():
        return [f"missing {STEP_REGISTRY}"]

    rows = read_csv(STEP_REGISTRY)
    if len(rows) != 10:
        errors.append(f"expected 10 precision steps, observed {len(rows)}")
    if rows:
        missing_columns = REQUIRED_COLUMNS - set(rows[0].keys())
        if missing_columns:
            errors.append(f"step_registry missing columns: {','.join(sorted(missing_columns))}")

    observed = [row.get("task_id", "") for row in rows]
    expected = list(EXPECTED_TASKS.keys())
    if observed != expected:
        errors.append(f"expected task ids {expected}, observed {observed}")

    for row in rows:
        task_id = row.get("task_id", "")
        slug = row.get("slug", "")
        expected_slug = EXPECTED_TASKS.get(task_id)
        if slug != expected_slug:
            errors.append(f"{task_id}: expected slug {expected_slug}, observed {slug}")
            continue
        directory = task_dir(task_id, slug)
        task_number = task_id.replace("Task", "").lower()
        report = directory / f"task_{task_number}_{slug}.md"
        decision = directory / f"task_{task_number}_decision.csv"
        for path in [directory, report, decision]:
            if not path.exists():
                errors.append(f"{task_id}: missing {path}")
        for name in TASK_REQUIRED_EXTRA_FILES.get(task_id, []):
            path = directory / name
            if not path.exists():
                errors.append(f"{task_id}: missing required contract artifact {path}")
            elif path.stat().st_size == 0:
                errors.append(f"{task_id}: empty required contract artifact {path}")
        if "No " not in row.get("forbidden_actions", ""):
            errors.append(f"{task_id}: forbidden_actions must contain explicit No-rules")
        if not row.get("overengineering_stop_rule", "").strip():
            errors.append(f"{task_id}: missing overengineering stop rule")

    for name in REQUIRED_PARENT_FILES:
        path = PARENT_DIR / name
        if not path.exists():
            errors.append(f"missing parent artifact {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty parent artifact {path}")

    text_paths = list(PARENT_DIR.glob("*.md")) + list(PARENT_DIR.glob("*.csv"))
    for task_id, slug in EXPECTED_TASKS.items():
        directory = task_dir(task_id, slug)
        text_paths.extend(directory.glob("*.md"))
        text_paths.extend(directory.glob("*.csv"))
    text = collect_text(text_paths)

    required_phrases = [
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "input hunger",
        "overengineering",
        "GPT review can improve",
        "COMPLETE_RESEARCH_ONLY",
    ]
    for phrase in required_phrases:
        if phrase.lower() not in text:
            errors.append(f"missing required phrase: {phrase}")

    for phrase in FORBIDDEN_PHRASES:
        if phrase in text:
            errors.append(f"forbidden overclaim phrase present: {phrase}")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_PRECISION_PROGRAM_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_PRECISION_PROGRAM_OK] Task772-Task781 research-only precision program artifacts are present")


if __name__ == "__main__":
    main()
