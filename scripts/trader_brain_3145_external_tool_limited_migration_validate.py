from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3145_external_tool_limited_migration"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        for col, expected in [
            ("strategy_acceptance", "NOT_ACCEPTED"),
            ("deployment_readiness", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"),
            ("real_capital", "FORBIDDEN"),
        ]:
            if col in row:
                require(row[col] == expected, f"{name} row {idx} changed {col}")
        for col in ["paper_order_intents_created", "live_orders_created", "selector_changed", "sizing_changed", "replay_performed", "source_acquisition_performed", "root_dependency_manifest_created"]:
            if col in row:
                require(row[col] == "0", f"{name} row {idx} has forbidden {col}={row[col]}")


def main() -> None:
    report = REPORT_DIR / "task_3145_external_tool_limited_migration.md"
    decision = REPORT_DIR / "task_3145_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")
    migrations = read_csv(OUT_DIR / "migration_result.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3145_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")
    decision_rows = read_csv(decision)
    for name, rows in [("migrations", migrations), ("checks", checks), ("closeout", closeout), ("decision", decision_rows)]:
        require(rows, f"{name} empty")
        assert_status(rows, name)
    require(len(migrations) == 1, "migration row count mismatch")
    row = migrations[0]
    require(row["migration_pass"] == "1", "migration failed")
    require(row["old_task_helper_import_present"] == "0", "old task helper import still present")
    require(row["common_module_import_present"] == "1", "common module import missing")
    require(row["reference_match_rows"] == "4", "reference matches changed")
    require(row["helper_candidate_rows"] == "4", "helper candidates changed")
    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(closeout[0]["task_id"] == "Task3145", "bad task id")
    require(closeout[0]["all_acceptance_checks_pass"] == "1", "closeout checks failed")
    manifest_paths = {row["relative_path"] for row in manifest}
    for required in ["migration_result.csv", "acceptance_checks.csv", "task3145_closeout.csv"]:
        require(required in manifest_paths, f"manifest missing {required}")
    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3145" for row in registry), "registry missing Task3145")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("Task3145" in op_state, "operating state missing Task3145")
    print("[TASK3145_EXTERNAL_TOOL_LIMITED_MIGRATION_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
