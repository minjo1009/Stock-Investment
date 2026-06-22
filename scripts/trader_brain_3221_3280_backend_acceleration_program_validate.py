from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3221_3280_backend_acceleration_program"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
REPORT = REPORT_DIR / "task_3221_3280_backend_acceleration_program.md"
DECISION = REPORT_DIR / "task_3280_decision.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_command(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1000:],
        "stderr_tail": completed.stderr[-1000:],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    commands = [
        [sys.executable, "-m", "unittest", "tests.test_backend_accelerators"],
        [sys.executable, "-m", "unittest", "tests.test_backtest_core_metrics_accelerated"],
        [sys.executable, "-m", "unittest", "tests.test_trader_terminal_catalog"],
        [sys.executable, "scripts/trader_brain_3231_3245_catalog_acceleration_validate.py"],
        [sys.executable, "scripts/trader_brain_3246_3260_backtest_core_metrics_acceleration_validate.py"],
        [sys.executable, "scripts/trader_brain_3261_3270_source_panel_acceleration_validate.py"],
        [sys.executable, "scripts/task_registry_validate.py"],
        [sys.executable, "scripts/operating_closeout_validate.py"],
        [sys.executable, "scripts/governance_completion_audit.py"],
    ]
    command_rows = [run_command(command) for command in commands]
    registry_rows = read_csv(ROOT / "tasks" / "task_registry.csv")
    registry_ids = {row["task_id"] for row in registry_rows}
    report_text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    validation_map = (ROOT / "docs" / "architecture" / "test_validation_canonicalization_map.md").read_text(encoding="utf-8")
    src_map = (ROOT / "docs" / "architecture" / "src_canonicalization_map.md").read_text(encoding="utf-8")
    op_state = (ROOT / "docs" / "operating_system" / "project_operating_state.md").read_text(encoding="utf-8")

    required_artifacts = [
        "catalog_acceleration_result.csv",
        "catalog_engine_parity.csv",
        "backtest_core_metrics_acceleration_result.csv",
        "source_panel_acceleration_result.csv",
    ]
    checks = [
        {"check_name": "lane_validators_pass", "pass": int(all(row["returncode"] == 0 for row in command_rows))},
        {"check_name": "report_exists", "pass": int(REPORT.exists())},
        {"check_name": "decision_exists", "pass": int(DECISION.exists())},
        {"check_name": "required_registry_rows_exist", "pass": int(all(task_id in registry_ids for task_id in ["Task3221", "Task3231", "Task3246", "Task3261", "Task3271", "Task3280"]))},
        {"check_name": "operating_state_mentions_task3280", "pass": int("Task3221-Task3280" in op_state)},
        {"check_name": "validation_map_mentions_task3280", "pass": int("Task3221-Task3280" in validation_map)},
        {"check_name": "src_map_mentions_grouped_accelerator", "pass": int("grouped_numeric_aggregate_accelerated" in src_map)},
        {"check_name": "report_has_required_footer", "pass": int("Strategy: `NOT_ACCEPTED`" in report_text and "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`" in report_text and "Real Capital: `FORBIDDEN`" in report_text)},
        {"check_name": "required_artifacts_exist", "pass": int(all((OUT_DIR / artifact).exists() for artifact in required_artifacts))},
    ]
    inventory = [
        {"candidate_id": "CATALOG-GROUP-QUALITY", "lane": "catalog", "path": "scripts/build_trader_terminal_catalog.py", "function": "_group_quality", "status": "migrated_to_grouped_numeric_aggregate_accelerated"},
        {"candidate_id": "CATALOG-MATRIX-QUALITY", "lane": "catalog", "path": "scripts/build_trader_terminal_catalog.py", "function": "_matrix_quality", "status": "migrated_to_grouped_numeric_aggregate_accelerated"},
        {"candidate_id": "CATALOG-COMPOSITE-QUALITY", "lane": "catalog", "path": "scripts/build_trader_terminal_catalog.py", "function": "_composite_group_quality", "status": "migrated_to_grouped_numeric_aggregate_accelerated"},
        {"candidate_id": "BACKTEST-LIFECYCLE-QUALITY", "lane": "backtest_core", "path": "src/backtest/core/metrics.py", "function": "grouped_lifecycle_quality", "status": "migrated_to_grouped_numeric_aggregate_accelerated"},
        {"candidate_id": "SOURCE-TASK3142", "lane": "source_panel", "path": "scripts/trader_brain_3142_external_tool_infra_module_promotion.py", "function": "run_module_replay", "status": "migrated_to_strict_gate_aggregate_accelerated"},
        {"candidate_id": "SOURCE-TASK3143", "lane": "source_panel", "path": "scripts/trader_brain_3143_external_tool_typed_contract.py", "function": "run_typed_parity", "status": "migrated_to_strict_gate_aggregate_accelerated"},
    ]
    manifest = [
        {"relative_path": "candidate_inventory.csv", "artifact_type": "inventory", "description": "Accelerator migration candidate inventory"},
        {"relative_path": "catalog_acceleration_result.csv", "artifact_type": "validation", "description": "Catalog lane focused parity result"},
        {"relative_path": "catalog_engine_parity.csv", "artifact_type": "validation", "description": "Catalog Polars/DuckDB fixture parity"},
        {"relative_path": "backtest_core_metrics_acceleration_result.csv", "artifact_type": "validation", "description": "Backtest core metrics parity result"},
        {"relative_path": "source_panel_acceleration_result.csv", "artifact_type": "validation", "description": "Source panel migration result"},
        {"relative_path": "source_panel_regeneration_commands.csv", "artifact_type": "validation", "description": "Task3142 and Task3143 current-code regeneration command evidence"},
        {"relative_path": "program_validation_commands.csv", "artifact_type": "validation", "description": "Program validator command results"},
        {"relative_path": "program_acceptance_checks.csv", "artifact_type": "validation", "description": "Program closeout checks"},
    ]
    closeout = [
        {
            "task_id": "Task3221-Task3280",
            "verdict": "backend_acceleration_program_structure_and_parity_completed",
            "candidate_rows": len(inventory),
            "all_acceptance_checks_pass": int(all(row["pass"] == 1 for row in checks)),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "replay_performed": 0,
            "source_acquisition_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
        }
    ]
    write_csv(OUT_DIR / "candidate_inventory.csv", inventory)
    write_csv(OUT_DIR / "program_validation_commands.csv", command_rows)
    write_csv(OUT_DIR / "program_acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3221_3280_closeout.csv", closeout)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)
    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3221_3280_ERROR] {row['check_name']}")
        return 1
    print("[TASK3221_3280_BACKEND_ACCELERATION_PROGRAM_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
