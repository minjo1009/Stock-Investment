from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT / "docs" / "reports" / "task_782_branchpoint_expert_panel_program"
STEP_REGISTRY = PARENT_DIR / "step_registry.csv"
ROLE_MATRIX = PARENT_DIR / "expert_role_matrix.csv"

EXPECTED_TASKS = {
    "Task782": "branchpoint_expert_panel_program",
    "Task783": "institutional_trader_panel_contract",
    "Task784": "macro_politics_filter_contract",
    "Task785": "economic_cycle_liquidity_contract",
    "Task786": "semiconductor_ai_infra_contract",
    "Task787": "space_defense_industrial_contract",
    "Task788": "backend_data_budget_contract",
    "Task789": "source_sufficiency_state_contract",
    "Task790": "cross_expert_conflict_arbitration",
    "Task791": "task773_execution_handoff",
}

TASK_REQUIRED_EXTRA_FILES = {
    "Task783": ["institutional_lens_questions.csv"],
    "Task784": ["macro_politics_filter_states.csv"],
    "Task785": ["economic_cycle_liquidity_states.csv"],
    "Task786": ["semiconductor_ai_source_budget.csv"],
    "Task787": ["space_defense_theme_filter.csv"],
    "Task788": ["backend_data_budget_schema.csv"],
    "Task789": ["source_sufficiency_state_catalog.csv"],
    "Task790": ["cross_expert_conflict_catalog.csv"],
    "Task791": ["task773_handoff_packet.md"],
}

REQUIRED_PARENT_FILES = [
    "step_registry.csv",
    "expert_role_matrix.csv",
    "gpt_role_prompt_packet.md",
    "subagent_packet_plan.md",
    "task782_summary.csv",
    "validation_log.md",
    "task_782_branchpoint_expert_panel_program.md",
    "task_782_decision.csv",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def task_dir(task_id: str, slug: str) -> Path:
    number = task_id.replace("Task", "").lower()
    return ROOT / "docs" / "reports" / f"task_{number}_{slug}"


def validate() -> list[str]:
    errors: list[str] = []
    if not STEP_REGISTRY.exists():
        return [f"missing {STEP_REGISTRY}"]
    rows = read_csv(STEP_REGISTRY)
    if [row.get("task_id", "") for row in rows] != list(EXPECTED_TASKS):
        errors.append("Task782-Task791 step ids are missing or out of order")
    if len(rows) != 10:
        errors.append(f"expected 10 branchpoint steps, observed {len(rows)}")

    for row in rows:
        task_id = row.get("task_id", "")
        slug = row.get("slug", "")
        if EXPECTED_TASKS.get(task_id) != slug:
            errors.append(f"{task_id}: unexpected slug {slug}")
            continue
        directory = task_dir(task_id, slug)
        number = task_id.replace("Task", "").lower()
        for path in [
            directory,
            directory / f"task_{number}_{slug}.md",
            directory / f"task_{number}_decision.csv",
        ]:
            if not path.exists():
                errors.append(f"{task_id}: missing {path}")
        for name in TASK_REQUIRED_EXTRA_FILES.get(task_id, []):
            path = directory / name
            if not path.exists():
                errors.append(f"{task_id}: missing required contract artifact {path}")
            elif path.stat().st_size == 0:
                errors.append(f"{task_id}: empty required contract artifact {path}")
        if "No " not in row.get("forbidden_actions", ""):
            errors.append(f"{task_id}: missing explicit no-rule")
        if not row.get("overengineering_stop_rule", "").strip():
            errors.append(f"{task_id}: missing overengineering stop rule")

    for name in REQUIRED_PARENT_FILES:
        path = PARENT_DIR / name
        if not path.exists():
            errors.append(f"missing parent artifact {path}")

    if ROLE_MATRIX.exists():
        roles = read_csv(ROLE_MATRIX)
        institution_count = sum(1 for row in roles if row.get("role_group") == "institution")
        domain_count = sum(1 for row in roles if row.get("role_group") == "domain")
        if institution_count != 10:
            errors.append(f"expected 10 institution roles, observed {institution_count}")
        if domain_count < 5:
            errors.append(f"expected at least 5 domain roles, observed {domain_count}")
        forbidden_text = " ".join(row.get("forbidden_output", "") for row in roles).lower()
        for phrase in ["buy", "sell", "sizing", "rank"]:
            if phrase not in forbidden_text:
                errors.append(f"role matrix forbidden outputs missing {phrase}")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory in [PARENT_DIR, *[task_dir(t, s) for t, s in EXPECTED_TASKS.items()]]
        for path in directory.glob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    )
    for phrase in [
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "source-of-truth",
        "No missing-to-negative",
        "COMPLETE_RESEARCH_ONLY",
    ]:
        if phrase.lower() not in combined.lower():
            errors.append(f"missing required phrase: {phrase}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_BRANCHPOINT_PANEL_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_BRANCHPOINT_PANEL_OK] Task782-Task791 expert-panel branchpoint artifacts are present")


if __name__ == "__main__":
    main()
