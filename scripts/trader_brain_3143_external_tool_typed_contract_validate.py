from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3143_external_tool_typed_contract"
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
    require(rows, f"{name} empty")
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy acceptance")
        if "deployment_readiness" in row:
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")
        for col in ["paper_order_intents_created", "live_orders_created", "selector_changed", "sizing_changed", "replay_performed", "source_acquisition_performed", "root_dependency_manifest_created"]:
            if col in row:
                require(row[col] == "0", f"{name} row {idx} has forbidden {col}={row[col]}")


def main() -> None:
    report = REPORT_DIR / "task_3143_external_tool_typed_contract.md"
    decision = REPORT_DIR / "task_3143_decision.csv"
    module = ROOT / "src/infra/external_tools.py"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")
    require(module.exists(), "missing module")

    contracts = read_csv(OUT_DIR / "typed_contracts.csv")
    parity = read_csv(OUT_DIR / "typed_parity_result.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3143_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")
    decision_rows = read_csv(decision)

    for name, rows in [("contracts", contracts), ("parity", parity), ("checks", checks), ("closeout", closeout), ("decision", decision_rows)]:
        assert_status(rows, name)

    require({row["contract_name"] for row in contracts} == {"ToolStatus", "AggregateMetrics", "AggregateResult", "SchemaValidationResult", "MetricComparison"}, "typed contract set mismatch")
    require(all(row["trading_decision_allowed"] == "0" for row in contracts), "typed contract allows trading decision")
    require(len(parity) == 4, "typed parity row count mismatch")
    require(all(row["parity_pass"] == "1" for row in parity), "typed parity failed")
    require(all(row["tool_name"] == "pandera" or row.get("comparison_pass", "0") == "1" for row in parity), "typed comparison failed")
    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(closeout[0]["task_id"] == "Task3143", "bad task id")
    require(closeout[0]["all_acceptance_checks_pass"] == "1", "closeout checks failed")

    module_text = module.read_text(encoding="utf-8")
    for token in ["class AggregateMetrics", "class AggregateResult", "class SchemaValidationResult", "class MetricComparison", "compare_aggregate_results"]:
        require(token in module_text, f"module missing {token}")
    require("paper_order_intents_created" not in module_text, "module contains task/order status text")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3143" for row in registry), "registry missing Task3143")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("Task3143" in op_state, "operating state missing Task3143")
    manifest_paths = {row["relative_path"] for row in manifest}
    for required in ["typed_contracts.csv", "typed_parity_result.csv", "acceptance_checks.csv", "task3143_closeout.csv"]:
        require(required in manifest_paths, f"manifest missing {required}")
    print("[TASK3143_EXTERNAL_TOOL_TYPED_CONTRACT_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
