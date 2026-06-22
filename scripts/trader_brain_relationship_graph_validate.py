from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT / "docs" / "reports" / "task_792_information_relationship_graph_program"
STEP_REGISTRY = PARENT_DIR / "step_registry.csv"

EXPECTED_TASKS = {
    "Task792": "information_relationship_graph_program",
    "Task793": "information_node_identity_contract",
    "Task794": "relationship_edge_taxonomy_contract",
    "Task795": "cross_layer_link_contract",
    "Task796": "temporal_update_chain_contract",
    "Task797": "mechanism_theme_graph_contract",
    "Task798": "conflict_invalidation_graph_contract",
    "Task799": "attention_memory_graph_integration",
    "Task800": "relationship_graph_validator_design",
    "Task801": "task773_validator_handoff_revision",
}

PARENT_REQUIRED = [
    "step_registry.csv",
    "node_identity_schema.csv",
    "relationship_edge_taxonomy.csv",
    "layer_transition_map.csv",
    "expert_critical_review_matrix.csv",
    "subagent_packet_plan.md",
    "task_792_information_relationship_graph_program.md",
    "task_792_decision.csv",
    "artifact_manifest.csv",
]

CSV_REQUIRED_COLUMNS = {
    "node_identity_schema.csv": {"field", "required", "description", "forbidden_use"},
    "relationship_edge_taxonomy.csv": {"edge_type", "meaning", "required_evidence", "allowed_effect", "forbidden_effect"},
    "layer_transition_map.csv": {"from_layer", "to_layer", "required_intermediate", "allowed_transition", "forbidden_shortcut"},
    "expert_critical_review_matrix.csv": {"review_role", "critical_risk", "upgrade_applied", "owner_task", "forbidden_drift"},
}

CSV_REQUIRED_VALUES = {
    "node_identity_schema.csv": ("field", {"mechanism_id", "predecessor_node_id", "edge_evidence_id", "review_owner"}),
    "relationship_edge_taxonomy.csv": (
        "edge_type",
        {"reinforces", "weakens", "invalidates", "conditions", "sequences", "explains", "contradicts", "source_gap_for", "noise_for"},
    ),
}


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
        errors.append("Task792-Task801 step ids are missing or out of order")
    if len(rows) != 10:
        errors.append(f"expected 10 relationship graph steps, observed {len(rows)}")
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
        if "No " not in row.get("forbidden_actions", ""):
            errors.append(f"{task_id}: missing explicit no-rule")
        if not row.get("overengineering_stop_rule", "").strip():
            errors.append(f"{task_id}: missing overengineering stop rule")
    for name in PARENT_REQUIRED:
        path = PARENT_DIR / name
        if not path.exists():
            errors.append(f"missing parent artifact {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty parent artifact {path}")

    for name, columns in CSV_REQUIRED_COLUMNS.items():
        path = PARENT_DIR / name
        if not path.exists():
            continue
        rows_for_file = read_csv(path)
        observed_columns = set(rows_for_file[0].keys()) if rows_for_file else set()
        missing_columns = columns - observed_columns
        if missing_columns:
            errors.append(f"{name}: missing columns {','.join(sorted(missing_columns))}")
        if name == "expert_critical_review_matrix.csv" and len(rows_for_file) < 18:
            errors.append("expert_critical_review_matrix.csv: expected at least 18 review roles")

    for name, (column, required_values) in CSV_REQUIRED_VALUES.items():
        path = PARENT_DIR / name
        if not path.exists():
            continue
        observed_values = {row.get(column, "") for row in read_csv(path)}
        missing_values = required_values - observed_values
        if missing_values:
            errors.append(f"{name}: missing required values {','.join(sorted(missing_values))}")

    handoff = ROOT / "docs" / "reports" / "task_791_task773_execution_handoff" / "task773_handoff_packet.md"
    if handoff.exists():
        handoff_text = handoff.read_text(encoding="utf-8", errors="replace").lower()
        if "relationship graph contracts before controlled task773 validator implementation" not in handoff_text:
            errors.append("Task791 handoff does not require relationship graph contracts before Task773 validator implementation")
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory in [PARENT_DIR, *[task_dir(t, s) for t, s in EXPECTED_TASKS.items()]]
        for path in directory.glob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    ).lower()
    for phrase in [
        "not_accepted",
        "diagnostic_only_not_deployment_ready",
        "forbidden",
        "relationship",
        "source_gap",
        "no buy sell rank score sizing",
        "critical review",
        "mechanism_id",
        "edge_evidence_id",
    ]:
        if phrase not in combined:
            errors.append(f"missing required phrase: {phrase}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_RELATIONSHIP_GRAPH_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_RELATIONSHIP_GRAPH_OK] Task792-Task801 relationship graph artifacts are present")


if __name__ == "__main__":
    main()
