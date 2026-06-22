from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task820": (ROOT / "docs/reports/task_820_end_goal_roadmap_program", ["task_820_end_goal_roadmap_program.md", "task_820_decision.csv", "end_goal_roadmap.csv", "subagent_packet_plan.md", "artifact_manifest.csv"]),
    "Task821": (ROOT / "docs/reports/task_821_graph_fixture_corpus_expansion", ["task_821_graph_fixture_corpus_expansion.md", "task_821_decision.csv", "fixture_manifest.csv", "artifact_manifest.csv"]),
    "Task822": (ROOT / "docs/reports/task_822_provenance_coverage_audit", ["task_822_provenance_coverage_audit.md", "task_822_decision.csv", "provenance_coverage_audit.csv", "artifact_manifest.csv"]),
    "Task823": (ROOT / "docs/reports/task_823_candidate_bundle_adapter_contract", ["task_823_candidate_bundle_adapter_contract.md", "task_823_decision.csv", "candidate_bundle_schema.csv", "candidate_bundles.csv", "artifact_manifest.csv"]),
    "Task824": (ROOT / "docs/reports/task_824_contradiction_invalidation_propagation", ["task_824_contradiction_invalidation_propagation.md", "task_824_decision.csv", "contradiction_propagation_rules.csv", "artifact_manifest.csv"]),
    "Task825": (ROOT / "docs/reports/task_825_attention_memory_eviction_rules", ["task_825_attention_memory_eviction_rules.md", "task_825_decision.csv", "memory_eviction_policy.csv", "memory_eviction_fixture.csv", "artifact_manifest.csv"]),
    "Task826": (ROOT / "docs/reports/task_826_backtest_adapter_readiness_checklist", ["task_826_backtest_adapter_readiness_checklist.md", "task_826_decision.csv", "backtest_adapter_readiness_checklist.csv", "artifact_manifest.csv"]),
    "Task827": (ROOT / "docs/reports/task_827_go_no_go_closeout", ["task_827_go_no_go_closeout.md", "task_827_decision.csv", "go_no_go_matrix.csv", "artifact_manifest.csv"]),
}

REQUIRED_FILES = [
    ROOT / "README.md",
    ROOT / "scripts/trader_brain_provenance_coverage_audit.py",
    ROOT / "scripts/trader_brain_candidate_bundle_validate.py",
    ROOT / "tests/test_trader_brain_820_827_program.py",
    ROOT / "docs/reports/task_821_graph_fixture_corpus_expansion/fixtures/semiconductor_export_control_graph/nodes.csv",
    ROOT / "docs/reports/task_821_graph_fixture_corpus_expansion/fixtures/space_defense_policy_graph/nodes.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8", errors="replace")
    if "Project End Goal" not in readme or "institution-grade decision system" not in readme:
        errors.append("README.md missing Project End Goal block")
    for task_id, (directory, files) in TASKS.items():
        if not directory.exists():
            errors.append(f"{task_id}: missing directory {directory}")
            continue
        for name in files:
            path = directory / name
            if not path.exists():
                errors.append(f"{task_id}: missing {name}")
            elif path.stat().st_size == 0:
                errors.append(f"{task_id}: empty {name}")
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"missing required file {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required file {path}")

    coverage = TASKS["Task822"][0] / "provenance_coverage_audit.csv"
    if coverage.exists():
        rows = read_csv(coverage)
        if not rows:
            errors.append("Task822: provenance coverage audit has no rows")
        if any(row.get("coverage_state") != "covered" for row in rows):
            errors.append("Task822: provenance coverage audit contains uncovered evidence")

    bundles = TASKS["Task823"][0] / "candidate_bundles.csv"
    if bundles.exists():
        rows = read_csv(bundles)
        if len(rows) < 4:
            errors.append("Task823: expected at least 4 candidate bundle rows")
        if not any(row.get("bundle_state") == "blocked_by_contradiction" for row in rows):
            errors.append("Task823: expected contradiction-blocked candidate bundle")
        if not any(row.get("bundle_state") == "blocked_by_gap" for row in rows):
            errors.append("Task823: expected source-gap-blocked candidate bundle")

    readiness = TASKS["Task826"][0] / "backtest_adapter_readiness_checklist.csv"
    if readiness.exists():
        rows = read_csv(readiness)
        if not rows or any(row.get("status") != "not_ready" for row in rows):
            errors.append("Task826: all readiness rows must remain not_ready")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory, _ in TASKS.values()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    ).lower()
    for phrase in ["not_accepted", "diagnostic_only_not_deployment_ready", "forbidden", "research_only", "no backtest", "no runtime"]:
        if phrase not in combined:
            errors.append(f"missing required boundary phrase: {phrase}")
    for phrase in ["strategy_acceptance,accepted", "deployment_status,deployment_ready", "real_capital,allowed", "backtest eligibility assigned"]:
        if phrase in combined:
            errors.append(f"forbidden overclaim phrase found: {phrase}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_820_827_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_820_827_OK] Task820-Task827 artifacts are present")


if __name__ == "__main__":
    main()
