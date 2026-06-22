from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task828": (ROOT / "docs/reports/task_828_controlled_adapter_program", ["task_828_controlled_adapter_program.md", "task_828_decision.csv", "subagent_packet_plan.md", "adapter_program_steps.csv", "gpt_adapter_review_requirements.csv", "artifact_manifest.csv"]),
    "Task829": (ROOT / "docs/reports/task_829_controlled_adapter_design_contract", ["task_829_controlled_adapter_design_contract.md", "task_829_decision.csv", "adapter_eligibility_rules.csv", "artifact_manifest.csv"]),
    "Task830": (ROOT / "docs/reports/task_830_adapter_input_schema_contract", ["task_830_adapter_input_schema_contract.md", "task_830_decision.csv", "adapter_input_schema.csv", "artifact_manifest.csv"]),
    "Task831": (ROOT / "docs/reports/task_831_source_time_namespace_contract", ["task_831_source_time_namespace_contract.md", "task_831_decision.csv", "source_time_namespace.csv", "graph_packet_manifest.csv", "artifact_manifest.csv"]),
    "Task832": (ROOT / "docs/reports/task_832_leakage_guard_validator_design", ["task_832_leakage_guard_validator_design.md", "task_832_decision.csv", "leakage_guard_rules.csv", "artifact_manifest.csv"]),
    "Task833": (ROOT / "docs/reports/task_833_candidate_bundle_expansion_pack", ["task_833_candidate_bundle_expansion_pack.md", "task_833_decision.csv", "expanded_candidate_bundles.csv", "artifact_manifest.csv"]),
    "Task834": (ROOT / "docs/reports/task_834_negative_adapter_fixture_pack", ["task_834_negative_adapter_fixture_pack.md", "task_834_decision.csv", "negative_adapter_bundles.csv", "negative_adapter_audit.csv", "artifact_manifest.csv"]),
    "Task835": (ROOT / "docs/reports/task_835_adapter_eligibility_validator", ["task_835_adapter_eligibility_validator.md", "task_835_decision.csv", "artifact_manifest.csv"]),
    "Task836": (ROOT / "docs/reports/task_836_controlled_adapter_input_builder", ["task_836_controlled_adapter_input_builder.md", "task_836_decision.csv", "adapter_inputs.csv", "artifact_manifest.csv"]),
    "Task837": (ROOT / "docs/reports/task_837_adapter_output_audit_report", ["task_837_adapter_output_audit_report.md", "task_837_decision.csv", "adapter_eligibility_audit.csv", "artifact_manifest.csv"]),
    "Task838": (ROOT / "docs/reports/task_838_adapter_dry_run_governance_gate", ["task_838_adapter_dry_run_governance_gate.md", "task_838_decision.csv", "adapter_dry_run_gate_summary.csv", "artifact_manifest.csv"]),
    "Task839": (ROOT / "docs/reports/task_839_controlled_backtest_go_no_go", ["task_839_controlled_backtest_go_no_go.md", "task_839_decision.csv", "go_no_go_matrix.csv", "artifact_manifest.csv"]),
}

IMPLEMENTATION_FILES = [
    ROOT / "scripts/trader_brain_adapter_eligibility_validate.py",
    ROOT / "scripts/trader_brain_adapter_input_builder.py",
    ROOT / "scripts/trader_brain_adapter_dry_run_gate.py",
    ROOT / "scripts/trader_brain_828_839_program_validate.py",
    ROOT / "tests/test_trader_brain_828_839_adapter.py",
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

    packet = TASKS["Task828"][0] / "gpt_review_task828_adapter" / "gpt_chrome_review_packet.md"
    if not packet.exists():
        errors.append("Task828: missing GPT/Chrome review packet")

    for path in IMPLEMENTATION_FILES:
        if not path.exists():
            errors.append(f"missing implementation file {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty implementation file {path}")

    bundles = TASKS["Task833"][0] / "expanded_candidate_bundles.csv"
    if bundles.exists():
        rows = read_csv(bundles)
        if len(rows) < 12:
            errors.append("Task833: expected at least 12 expanded bundles")
        states = {row.get("bundle_state", "") for row in rows}
        for required in {"research_review_only", "context_only", "blocked_by_gap", "blocked_by_contradiction"}:
            if required not in states:
                errors.append(f"Task833: missing bundle_state {required}")

    negative = TASKS["Task834"][0] / "negative_adapter_bundles.csv"
    if negative.exists() and len(read_csv(negative)) < 6:
        errors.append("Task834: expected at least 6 negative fixtures")

    adapter_inputs = TASKS["Task836"][0] / "adapter_inputs.csv"
    if adapter_inputs.exists():
        rows = read_csv(adapter_inputs)
        if len(rows) != 2:
            errors.append("Task836: expected exactly 2 dry adapter input rows")
        if any(row.get("adapter_input_state") != "dry_adapter_input" for row in rows):
            errors.append("Task836: adapter_input_state must be dry_adapter_input")

    audit = TASKS["Task837"][0] / "adapter_eligibility_audit.csv"
    if audit.exists():
        rows = read_csv(audit)
        if len(rows) != 12:
            errors.append("Task837: expected 12 audit rows")
        state_counts = {state: sum(1 for row in rows if row.get("eligibility_state") == state) for state in {"eligible", "blocked", "invalid"}}
        if state_counts.get("eligible") != 2 or state_counts.get("blocked") != 10 or state_counts.get("invalid") != 0:
            errors.append(f"Task837: unexpected audit state counts {state_counts}")

    summary = TASKS["Task838"][0] / "adapter_dry_run_gate_summary.csv"
    if summary.exists():
        rows = read_csv(summary)
        if not rows or rows[0].get("gate_status") != "diagnostic_only_pass":
            errors.append("Task838: gate_status must be diagnostic_only_pass")
        if rows and rows[0].get("adapter_input_count") != "2":
            errors.append("Task838: adapter_input_count must be 2")
        if rows and rows[0].get("strategy_acceptance") != "NOT_ACCEPTED":
            errors.append("Task838: strategy acceptance must remain NOT_ACCEPTED")

    go_no_go = TASKS["Task839"][0] / "go_no_go_matrix.csv"
    if go_no_go.exists():
        rows = read_csv(go_no_go)
        if not any(row.get("decision_area") == "controlled_backtest_implementation" and row.get("status") == "no_go" for row in rows):
            errors.append("Task839: controlled_backtest_implementation must remain no_go")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory, _ in TASKS.values()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    ).lower()
    for phrase in ["not_accepted", "diagnostic_only_not_deployment_ready", "forbidden", "research_only", "no backtest", "no runtime"]:
        if phrase not in combined:
            errors.append(f"missing boundary phrase: {phrase}")
    for phrase in ["strategy_acceptance,accepted", "deployment_status,deployment_ready", "real_capital,allowed", "backtest eligibility assigned"]:
        if phrase in combined:
            errors.append(f"forbidden overclaim phrase found: {phrase}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_828_839_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_828_839_OK] Task828-Task839 adapter dry-run program artifacts are present")


if __name__ == "__main__":
    main()
