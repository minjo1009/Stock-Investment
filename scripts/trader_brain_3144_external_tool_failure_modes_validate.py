from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3144_external_tool_failure_modes"
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
    report = REPORT_DIR / "task_3144_external_tool_failure_modes.md"
    decision = REPORT_DIR / "task_3144_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")
    fixtures = read_csv(OUT_DIR / "bad_fixture_manifest.csv")
    failures = read_csv(OUT_DIR / "failure_mode_result.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3144_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")
    decision_rows = read_csv(decision)
    for name, rows in [("fixtures", fixtures), ("failures", failures), ("checks", checks), ("closeout", closeout), ("decision", decision_rows)]:
        require(rows, f"{name} empty")
        assert_status(rows, name)
    require(len(fixtures) == 3, "bad fixture count mismatch")
    require(len(failures) == 8, "failure case count mismatch")
    require(all(row["failure_mode_pass"] == "1" for row in failures), "failure mode failed")
    statuses = {row["actual_status"] for row in failures}
    require({"invalid_input", "schema_execution_failed", "dependency_missing"}.issubset(statuses), "missing expected failure statuses")
    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(closeout[0]["task_id"] == "Task3144", "bad task id")
    require(closeout[0]["all_acceptance_checks_pass"] == "1", "closeout checks failed")
    manifest_paths = {row["relative_path"] for row in manifest}
    for required in ["bad_fixture_manifest.csv", "failure_mode_result.csv", "acceptance_checks.csv", "task3144_closeout.csv"]:
        require(required in manifest_paths, f"manifest missing {required}")
    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3144" for row in registry), "registry missing Task3144")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("Task3144" in op_state, "operating state missing Task3144")
    print("[TASK3144_EXTERNAL_TOOL_FAILURE_MODES_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
