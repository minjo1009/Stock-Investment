from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task812": (
        ROOT / "docs" / "reports" / "task_812_gpt_expert_next8_program",
        [
            "task_812_gpt_expert_next8_program.md",
            "task_812_decision.csv",
            "gpt_expert_next8_discussion_matrix.csv",
            "gpt_role_implementation_requirements.csv",
            "next8_step_registry.csv",
            "subagent_packet_plan.md",
            "artifact_manifest.csv",
        ],
    ),
    "Task813": (
        ROOT / "docs" / "reports" / "task_813_golden_graph_fixture_pack",
        ["task_813_golden_graph_fixture_pack.md", "task_813_decision.csv", "artifact_manifest.csv"],
    ),
    "Task814": (
        ROOT / "docs" / "reports" / "task_814_graph_batch_runner_contract",
        ["task_814_graph_batch_runner_contract.md", "task_814_decision.csv", "batch_manifest.csv", "artifact_manifest.csv"],
    ),
    "Task815": (
        ROOT / "docs" / "reports" / "task_815_attention_packet_fixture_corpus",
        ["task_815_attention_packet_fixture_corpus.md", "task_815_decision.csv", "artifact_manifest.csv"],
    ),
    "Task816": (
        ROOT / "docs" / "reports" / "task_816_provenance_manifest_linker_contract",
        ["task_816_provenance_manifest_linker_contract.md", "task_816_decision.csv", "provenance_manifest.csv", "artifact_manifest.csv"],
    ),
    "Task817": (
        ROOT / "docs" / "reports" / "task_817_graph_failure_report_contract",
        ["task_817_graph_failure_report_contract.md", "task_817_decision.csv", "sample_failure_report.csv", "artifact_manifest.csv"],
    ),
    "Task818": (
        ROOT / "docs" / "reports" / "task_818_ci_governance_gate_contract",
        [
            "task_818_ci_governance_gate_contract.md",
            "task_818_decision.csv",
            "governance_gate_manifest.csv",
            "governance_failure_report.csv",
            "governance_gate_summary.csv",
            "artifact_manifest.csv",
        ],
    ),
    "Task819": (
        ROOT / "docs" / "reports" / "task_819_next8_closeout_handoff",
        ["task_819_next8_closeout_handoff.md", "task_819_decision.csv", "artifact_manifest.csv"],
    ),
}

IMPLEMENTATION_FILES = [
    ROOT / "scripts" / "trader_brain_graph_batch_validate.py",
    ROOT / "scripts" / "trader_brain_provenance_manifest_linker_validate.py",
    ROOT / "scripts" / "trader_brain_relationship_graph_governance_gate.py",
    ROOT / "tests" / "test_trader_brain_next8_operational_hardening.py",
    ROOT / "docs" / "reports" / "task_813_golden_graph_fixture_pack" / "fixtures" / "ai_capex_mechanism_graph" / "nodes.csv",
    ROOT / "docs" / "reports" / "task_813_golden_graph_fixture_pack" / "fixtures" / "ai_capex_mechanism_graph" / "edges.csv",
    ROOT / "docs" / "reports" / "task_813_golden_graph_fixture_pack" / "fixtures" / "macro_policy_source_gap_graph" / "nodes.csv",
    ROOT / "docs" / "reports" / "task_815_attention_packet_fixture_corpus" / "fixtures" / "attention_packets.csv",
    ROOT / "docs" / "reports" / "task_817_graph_failure_report_contract" / "fixtures" / "bad_missing_edge_evidence" / "edges.csv",
]


FORBIDDEN = [
    "strategy_acceptance,accepted",
    "deployment_status,deployment_ready",
    "real_capital,allowed",
    "verdict,strategy_accepted",
    "verdict,deployment_ready",
    "backtest eligibility assigned",
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

    matrix = TASKS["Task812"][0] / "gpt_expert_next8_discussion_matrix.csv"
    if matrix.exists() and len(read_csv(matrix)) < 15:
        errors.append("Task812: expected at least 15 GPT institution or expert review rows")

    role_requirements = TASKS["Task812"][0] / "gpt_role_implementation_requirements.csv"
    if role_requirements.exists() and len(read_csv(role_requirements)) < 20:
        errors.append("Task812: expected at least 20 GPT role implementation requirement rows")

    step_registry = TASKS["Task812"][0] / "next8_step_registry.csv"
    if step_registry.exists():
        rows = read_csv(step_registry)
        if len(rows) != 7:
            errors.append("Task812: expected exactly 7 child next-step rows for Task813-Task819")
        expected = {f"Task{i}" for i in range(813, 820)}
        observed = {row.get("task_id", "") for row in rows}
        if observed != expected:
            errors.append(f"Task812: child task ids mismatch {sorted(observed)}")

    packet = TASKS["Task812"][0] / "gpt_review_task812_next8" / "gpt_chrome_review_packet.md"
    if not packet.exists():
        errors.append("Task812: missing bounded GPT/Chrome review packet")

    for path in IMPLEMENTATION_FILES:
        if not path.exists():
            errors.append(f"missing implementation artifact {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty implementation artifact {path}")

    failure_report = TASKS["Task817"][0] / "sample_failure_report.csv"
    if failure_report.exists():
        rows = read_csv(failure_report)
        failure_classes = {row.get("failure_class", "") for row in rows}
        observed = {row.get("observed_status", "") for row in rows}
        if "missing_required_evidence" not in failure_classes:
            errors.append("Task817: sample failure report must include missing_required_evidence")
        if "fail" not in observed:
            errors.append("Task817: sample failure report must include an expected fail row")

    gate_summary = TASKS["Task818"][0] / "governance_gate_summary.csv"
    if gate_summary.exists():
        rows = read_csv(gate_summary)
        if not rows or rows[0].get("gate_status") != "diagnostic_only_pass":
            errors.append("Task818: governance gate summary must be diagnostic_only_pass")
        if rows and rows[0].get("strategy_acceptance") != "NOT_ACCEPTED":
            errors.append("Task818: governance gate summary must preserve NOT_ACCEPTED")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory, _ in TASKS.values()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    )
    combined_lower = combined.lower()
    for phrase in [
        "not_accepted",
        "diagnostic_only_not_deployment_ready",
        "forbidden",
        "research_only",
        "no buy/sell",
        "no runtime",
        "no backtest",
    ]:
        if phrase not in combined_lower:
            errors.append(f"missing required phrase: {phrase}")
    for phrase in FORBIDDEN:
        if phrase in combined_lower:
            errors.append(f"forbidden overclaim phrase found: {phrase}")

    for task_id, (directory, _) in TASKS.items():
        decision = directory / f"task_{task_id.replace('Task', '')}_decision.csv"
        if decision.exists():
            values = {row.get("field", ""): row.get("value", "") for row in read_csv(decision)}
            if values.get("strategy_acceptance") != "NOT_ACCEPTED":
                errors.append(f"{decision}: strategy_acceptance must remain NOT_ACCEPTED")
            if values.get("deployment_status") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
                errors.append(f"{decision}: deployment_status must remain DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
            if values.get("real_capital") != "FORBIDDEN":
                errors.append(f"{decision}: real_capital must remain FORBIDDEN")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_NEXT8_PROGRAM_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_NEXT8_PROGRAM_OK] Task812-Task819 next-eight program artifacts are present")


if __name__ == "__main__":
    main()
