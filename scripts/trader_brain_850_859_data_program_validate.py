from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "Task850": ROOT / "docs/reports/task_850_data_acquisition_certification_program",
    "Task851": ROOT / "docs/reports/task_851_dataset_requirement_contract",
    "Task852": ROOT / "docs/reports/task_852_existing_dataset_inventory_audit",
    "Task853": ROOT / "docs/reports/task_853_canonical_market_data_manifest_schema",
    "Task854": ROOT / "docs/reports/task_854_daily_ohlcv_certification_decision",
    "Task855": ROOT / "docs/reports/task_855_intraday_15m_certification_decision",
    "Task856": ROOT / "docs/reports/task_856_microstructure_scope_decision",
    "Task857": ROOT / "docs/reports/task_857_gap_redownload_plan",
    "Task858": ROOT / "docs/reports/task_858_market_calendar_corporate_action_plan",
    "Task859": ROOT / "docs/reports/task_859_market_data_gate_handoff",
}

REQUIRED_850_FILES = [
    "task_850_data_acquisition_certification_program.md",
    "task_850_decision.csv",
    "data_requirement_contract.csv",
    "data_period_universe_contract.csv",
    "data_reuse_redownload_decision_tree.csv",
    "canonical_market_data_manifest_schema.csv",
    "canonical_bar_schema.csv",
    "no_go_gate_matrix.csv",
    "gpt_review_synthesis.md",
    "task_850_859_program_steps.csv",
    "subagent_packet_plan.md",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for task_id, directory in TASKS.items():
        if not directory.exists():
            errors.append(f"{task_id}: missing directory")
            continue
        report_files = list(directory.glob("*.md"))
        decision_files = list(directory.glob("*decision.csv"))
        if not report_files:
            errors.append(f"{task_id}: missing report markdown")
        if not decision_files:
            errors.append(f"{task_id}: missing decision csv")
        manifest = directory / "artifact_manifest.csv"
        if not manifest.exists():
            errors.append(f"{task_id}: missing artifact_manifest.csv")
    task850 = TASKS["Task850"]
    for name in REQUIRED_850_FILES:
        path = task850 / name
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"Task850: missing or empty {name}")

    requirement_rows = read_csv(task850 / "data_requirement_contract.csv")
    families = {row["data_family"]: row for row in requirement_rows}
    for required in [
        "daily_ohlcv_adjusted",
        "intraday_15m_bars",
        "market_calendar",
        "corporate_actions",
        "symbol_master",
        "point_in_time_universe",
        "benchmark_context",
        "microstructure_quotes_trades",
    ]:
        if required not in families:
            errors.append(f"Task850: missing data family {required}")
    if families.get("microstructure_quotes_trades", {}).get("required_for_first_controlled_replay") != "no":
        errors.append("Task850: microstructure must not be required for first controlled replay")
    if families.get("daily_ohlcv_adjusted", {}).get("target_period_start") != "2021-01-01":
        errors.append("Task850: daily target period must start 2021-01-01")
    if families.get("intraday_15m_bars", {}).get("target_period_start") != "2024-01-02":
        errors.append("Task850: first intraday target period must start 2024-01-02")
    if families.get("point_in_time_universe", {}).get("required_for_first_controlled_replay") != "yes":
        errors.append("Task850: point-in-time universe must be required")

    manifest_text = (task850 / "canonical_market_data_manifest_schema.csv").read_text(encoding="utf-8")
    for phrase in ["schema_fingerprint", "data_available_ts", "as_of_cutoff", "content_hash"]:
        if phrase not in manifest_text:
            errors.append(f"Task850 manifest schema missing phrase: {phrase}")

    no_go_rows = read_csv(task850 / "no_go_gate_matrix.csv")
    no_go_names = {row.get("gate_name") for row in no_go_rows}
    for required_gate in [
        "point_in_time_universe",
        "regular_session_calendar",
        "corporate_action_adjustment_proof",
        "intraday_schema_normalization",
        "raw_hash_audit",
    ]:
        if required_gate not in no_go_names:
            errors.append(f"Task850 no-go matrix missing gate: {required_gate}")

    decision_text = (task850 / "data_reuse_redownload_decision_tree.csv").read_text(encoding="utf-8")
    for phrase in [
        "reuse_existing",
        "redownload_gap_only",
        "blocked_or_redownload_slice",
        "no full redownload unless gap pattern is systemic",
        "no source approximation",
    ]:
        if phrase not in decision_text:
            errors.append(f"Task850 decision tree missing phrase: {phrase}")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory in TASKS.values()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    )
    for phrase in [
        "NOT_ACCEPTED",
        "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "Do not delete existing data",
        "Do not redownload everything by default",
    ]:
        if phrase not in combined:
            errors.append(f"missing governance phrase: {phrase}")
    for forbidden in [
        "strategy_acceptance,accepted",
        "deployment_status,deployment_ready",
        "real_capital,allowed",
        "actual backtest execution approved",
    ]:
        if forbidden in combined:
            errors.append(f"forbidden claim found: {forbidden}")

    registry_rows = read_csv(ROOT / "tasks/task_registry.csv")
    registry_ids = {row.get("task_id") for row in registry_rows}
    for idx in range(850, 860):
        if f"Task{idx}" not in registry_ids:
            errors.append(f"registry missing Task{idx}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_850_859_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_850_859_OK] Task850-Task859 data acquisition certification program is defined")


if __name__ == "__main__":
    main()
