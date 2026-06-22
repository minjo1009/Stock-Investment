from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task840": (ROOT / "docs/reports/task_840_backtest_harness_program", ["task_840_backtest_harness_program.md", "task_840_decision.csv", "subagent_packet_plan.md", "harness_program_steps.csv", "artifact_manifest.csv"]),
    "Task841": (ROOT / "docs/reports/task_841_backtest_input_manifest_schema", ["task_841_backtest_input_manifest_schema.md", "task_841_decision.csv", "backtest_input_manifest_schema.csv", "backtest_input_manifest.csv", "artifact_manifest.csv"]),
    "Task842": (ROOT / "docs/reports/task_842_tradable_after_timestamp_contract", ["task_842_tradable_after_timestamp_contract.md", "task_842_decision.csv", "tradable_after_timestamp_rules.csv", "artifact_manifest.csv"]),
    "Task843": (ROOT / "docs/reports/task_843_market_data_source_gate", ["task_843_market_data_source_gate.md", "task_843_decision.csv", "market_data_source_gate.csv", "market_data_source_manifest_schema.csv", "artifact_manifest.csv"]),
    "Task844": (ROOT / "docs/reports/task_844_replay_config_contract", ["task_844_replay_config_contract.md", "task_844_decision.csv", "replay_config_contract.csv", "artifact_manifest.csv"]),
    "Task845": (ROOT / "docs/reports/task_845_no_execution_dry_replay_harness", ["task_845_no_execution_dry_replay_harness.md", "task_845_decision.csv", "harness_run_plan.csv", "harness_run_summary.csv", "artifact_manifest.csv"]),
    "Task846": (ROOT / "docs/reports/task_846_split_oos_cost_slippage_plan", ["task_846_split_oos_cost_slippage_plan.md", "task_846_decision.csv", "split_oos_cost_slippage_plan.csv", "artifact_manifest.csv"]),
    "Task847": (ROOT / "docs/reports/task_847_failure_decomposition_schema", ["task_847_failure_decomposition_schema.md", "task_847_decision.csv", "failure_decomposition_schema.csv", "artifact_manifest.csv"]),
    "Task848": (ROOT / "docs/reports/task_848_harness_artifact_audit_validator", ["task_848_harness_artifact_audit_validator.md", "task_848_decision.csv", "harness_artifact_audit.csv", "artifact_manifest.csv"]),
    "Task849": (ROOT / "docs/reports/task_849_first_controlled_backtest_go_no_go", ["task_849_first_controlled_backtest_go_no_go.md", "task_849_decision.csv", "go_no_go_matrix.csv", "artifact_manifest.csv"]),
}

IMPLEMENTATION_FILES = [
    ROOT / "docs/operating_system/backtest_harness_operating_discipline.md",
    ROOT / "scripts/trader_brain_backtest_dry_replay_harness.py",
    ROOT / "scripts/trader_brain_backtest_harness_artifact_audit.py",
    ROOT / "scripts/trader_brain_840_849_program_validate.py",
    ROOT / "tests/test_trader_brain_840_849_backtest_harness.py",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8", errors="replace")
    if "backtest_harness_operating_discipline.md" not in agents:
        errors.append("AGENTS.md must require backtest harness discipline for backtest work")
    discipline = IMPLEMENTATION_FILES[0].read_text(encoding="utf-8", errors="replace")
    for phrase in ["No price data lookup", "No trade generation", "No PnL", "Required Backtest Work Read Order"]:
        if phrase not in discipline:
            errors.append(f"backtest discipline missing phrase: {phrase}")

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

    packet = TASKS["Task840"][0] / "gpt_review_task840_backtest_harness" / "gpt_chrome_review_packet.md"
    if not packet.exists():
        errors.append("Task840: missing GPT review packet")

    for path in IMPLEMENTATION_FILES:
        if not path.exists():
            errors.append(f"missing implementation file {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty implementation file {path}")

    gate_rows = read_csv(TASKS["Task843"][0] / "market_data_source_gate.csv")
    if not gate_rows or any(row.get("current_state") != "blocked" for row in gate_rows):
        errors.append("Task843: market data gate must remain blocked")

    split_rows = read_csv(TASKS["Task846"][0] / "split_oos_cost_slippage_plan.csv")
    if not split_rows or any(row.get("current_state") != "not_ready" for row in split_rows):
        errors.append("Task846: split/OOS rows must remain not_ready")

    summary_rows = read_csv(TASKS["Task845"][0] / "harness_run_summary.csv")
    if not summary_rows:
        errors.append("Task845: missing summary rows")
    else:
        summary = summary_rows[0]
        for field in ["price_lookup_count", "trade_row_count", "pnl_metric_count", "engine_call_count"]:
            if summary.get(field) != "0":
                errors.append(f"Task845: {field} must be 0")
        if summary.get("blocked_before_replay_count") != "2":
            errors.append("Task845: both harness inputs should be blocked before replay")

    audit_rows = read_csv(TASKS["Task848"][0] / "harness_artifact_audit.csv")
    if not audit_rows or audit_rows[0].get("audit_state") != "pass":
        errors.append("Task848: artifact audit must pass")

    go_rows = read_csv(TASKS["Task849"][0] / "go_no_go_matrix.csv")
    if not any(row.get("decision_area") == "first_controlled_backtest_run" and row.get("status") == "no_go" for row in go_rows):
        errors.append("Task849: first controlled backtest run must remain no_go")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory, _ in TASKS.values()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    ).lower()
    for phrase in ["not_accepted", "diagnostic_only_not_deployment_ready", "forbidden", "no backtest", "no runtime"]:
        if phrase not in combined:
            errors.append(f"missing boundary phrase: {phrase}")
    for phrase in ["strategy_acceptance,accepted", "deployment_status,deployment_ready", "real_capital,allowed", "pnl_metric_count,1", "trade_row_count,1", "engine_call_count,1"]:
        if phrase in combined:
            errors.append(f"forbidden phrase found: {phrase}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_840_849_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_840_849_OK] Task840-Task849 no-execution backtest harness artifacts are present")


if __name__ == "__main__":
    main()
