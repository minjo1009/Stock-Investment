from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


TASKS = {
    "Task881": ("docs/reports/task_881_historical_trader_brain_backtest_program", "task_881_historical_trader_brain_backtest_program.md", "task_881_decision.csv"),
    "Task882": ("docs/reports/task_882_period_split_universe_contract", "task_882_period_split_universe_contract.md", "task_882_decision.csv"),
    "Task883": ("docs/reports/task_883_historical_evidence_source_time_panel", "task_883_historical_evidence_source_time_panel.md", "task_883_decision.csv"),
    "Task884": ("docs/reports/task_884_brain_layer_state_reconstruction", "task_884_brain_layer_state_reconstruction.md", "task_884_decision.csv"),
    "Task885": ("docs/reports/task_885_relationship_graph_rolling_snapshot", "task_885_relationship_graph_rolling_snapshot.md", "task_885_decision.csv"),
    "Task886": ("docs/reports/task_886_candidate_bundle_generation_contract", "task_886_candidate_bundle_generation_contract.md", "task_886_decision.csv"),
    "Task887": ("docs/reports/task_887_trader_decision_policy_contract", "task_887_trader_decision_policy_contract.md", "task_887_decision.csv"),
    "Task888": ("docs/reports/task_888_historical_trade_spec_adapter_contract", "task_888_historical_trade_spec_adapter_contract.md", "task_888_decision.csv"),
    "Task889": ("docs/reports/task_889_replay_harness_config_data_gate", "task_889_replay_harness_config_data_gate.md", "task_889_decision.csv"),
    "Task890": ("docs/reports/task_890_leakage_oos_cost_go_no_go", "task_890_leakage_oos_cost_go_no_go.md", "task_890_decision.csv"),
}


REQUIRED_TABLES = [
    "docs/reports/task_881_historical_trader_brain_backtest_program/task_881_890_program_steps.csv",
    "docs/reports/task_882_period_split_universe_contract/period_split_universe_contract.csv",
    "docs/reports/task_883_historical_evidence_source_time_panel/historical_evidence_source_time_panel_contract.csv",
    "docs/reports/task_884_brain_layer_state_reconstruction/brain_layer_state_reconstruction_contract.csv",
    "docs/reports/task_885_relationship_graph_rolling_snapshot/rolling_graph_snapshot_contract.csv",
    "docs/reports/task_886_candidate_bundle_generation_contract/candidate_bundle_generation_contract.csv",
    "docs/reports/task_887_trader_decision_policy_contract/trader_decision_policy_contract.csv",
    "docs/reports/task_888_historical_trade_spec_adapter_contract/historical_trade_spec_adapter_contract.csv",
    "docs/reports/task_889_replay_harness_config_data_gate/replay_harness_config_data_gate.csv",
    "docs/reports/task_890_leakage_oos_cost_go_no_go/go_no_go_matrix.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for task_id, (directory, report_name, decision_name) in TASKS.items():
        report = ROOT / directory / report_name
        decision = ROOT / directory / decision_name
        if not report.exists():
            errors.append(f"{task_id} missing report")
        if not decision.exists():
            errors.append(f"{task_id} missing decision csv")
        if report.exists():
            text = report.read_text(encoding="utf-8")
            for phrase in ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
                if phrase not in text:
                    errors.append(f"{task_id} missing required status phrase {phrase}")
    for rel in REQUIRED_TABLES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required table {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required table {rel}")
    program = ROOT / "docs/reports/task_881_historical_trader_brain_backtest_program/task_881_890_program_steps.csv"
    if program.exists():
        step_rows = rows(program)
        if len(step_rows) != 10:
            errors.append("program steps must define exactly 10 tasks")
        ids = {row["task_id"] for row in step_rows}
        expected = {f"Task{task_id}" for task_id in range(881, 891)}
        if ids != expected:
            errors.append("program steps must cover Task881 through Task890")
    split = ROOT / "docs/reports/task_882_period_split_universe_contract/period_split_universe_contract.csv"
    if split.exists():
        values = {(row["field"], row["value"]) for row in rows(split)}
        required_values = {
            ("start_date", "2021-01-01"),
            ("end_date", "2026-03-31"),
            ("universe", "data/raw/theme_universe_10x7.csv"),
            ("universe_authority", "fixed_research_universe_diagnostic_only"),
            ("benchmark", "QQQ"),
            ("initial_capital", "1000"),
        }
        missing = required_values - values
        if missing:
            errors.append(f"period split contract missing {sorted(missing)}")
    go_no_go = ROOT / "docs/reports/task_890_leakage_oos_cost_go_no_go/go_no_go_matrix.csv"
    if go_no_go.exists():
        matrix = rows(go_no_go)
        if not any(row["gate"] == "first_real_historical_brain_replay" and row["current_status"] == "no_go" for row in matrix):
            errors.append("first real historical brain replay must remain no_go")
        required_gates = {"negative_fixture_leakage_guard", "policy_freeze"}
        present_gates = {row["gate"] for row in matrix}
        missing_gates = required_gates - present_gates
        if missing_gates:
            errors.append(f"go/no-go matrix missing required gates {sorted(missing_gates)}")
    policy = ROOT / "docs/reports/task_887_trader_decision_policy_contract/trader_decision_policy_contract.csv"
    if policy.exists():
        policy_rows = rows(policy)
        if "policy_version" not in policy_rows[0]:
            errors.append("trader decision policy must include policy_version")
        reduce_rows = [row for row in policy_rows if row["decision_state"] == "reduce"]
        if not reduce_rows or any(row.get("requires_existing_position") != "1" for row in reduce_rows):
            errors.append("reduce policy must require existing position")
    review = ROOT / "docs/reports/task_881_historical_trader_brain_backtest_program/gpt_institutional_review_synthesis.md"
    if not review.exists():
        errors.append("missing GPT institutional review synthesis")
    elif "critique only, not source-of-truth" not in review.read_text(encoding="utf-8"):
        errors.append("GPT institutional review synthesis must preserve critique-only authority")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_881_890_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_881_890_OK] historical Trader Brain backtest preparation tasks are defined")


if __name__ == "__main__":
    main()
