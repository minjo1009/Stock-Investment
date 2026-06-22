from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3141_external_tool_helper_contract"
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
        for col in [
            "paper_order_intents_created",
            "live_orders_created",
            "selector_changed",
            "sizing_changed",
            "replay_performed",
            "source_acquisition_performed",
            "root_dependency_manifest_created",
            "src_promoted",
        ]:
            if col in row:
                require(row[col] == "0", f"{name} row {idx} has forbidden {col}={row[col]}")


def main() -> None:
    report = REPORT_DIR / "task_3141_external_tool_helper_contract.md"
    decision = REPORT_DIR / "task_3141_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    root_dependency_files = [
        ROOT / "requirements.txt",
        ROOT / "requirements-dev.txt",
        ROOT / "pyproject.toml",
        ROOT / "setup.cfg",
        ROOT / "poetry.lock",
        ROOT / "Pipfile",
    ]
    require(not any(path.exists() for path in root_dependency_files), "root dependency manifest was created")

    contracts = read_csv(OUT_DIR / "helper_contracts.csv")
    replay = read_csv(OUT_DIR / "helper_replay_result.csv")
    diff = read_csv(OUT_DIR / "helper_output_diff.csv")
    decisions = read_csv(OUT_DIR / "helper_decision_matrix.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3141_closeout.csv")
    decision_rows = read_csv(decision)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("contracts", contracts),
        ("replay", replay),
        ("diff", diff),
        ("decisions", decisions),
        ("checks", checks),
        ("closeout", closeout),
        ("decision", decision_rows),
    ]:
        assert_status(rows, name)

    require(len(contracts) == 6, "helper contract count mismatch")
    contract_tools = {row["tool_name"]: row for row in contracts}
    for tool in ["pandera", "polars", "duckdb"]:
        require(contract_tools[tool]["helper_status"] == "enabled", f"{tool} helper should be enabled")
        require(contract_tools[tool]["promoted_to_src"] == "0", f"{tool} helper promoted to src")
    for tool in ["edgartools", "dlt", "github_mcp_read_only"]:
        require(contract_tools[tool]["helper_status"] == "deferred", f"{tool} helper should remain deferred")

    require(len(replay) == 4, "helper replay row count mismatch")
    require(all(row["reference_match"] == "1" for row in replay), "helper replay did not match references")
    require(sum(1 for row in replay if row["decision"] == "helper_candidate") == 4, "expected four helper candidates")
    require(any(row["tool_name"] == "pandera" and row["decision"] == "helper_candidate" for row in replay), "Pandera helper missing")
    require(sum(1 for row in replay if row["tool_name"] == "polars" and row["decision"] == "helper_candidate") == 2, "Polars helper candidates mismatch")
    require(sum(1 for row in replay if row["tool_name"] == "duckdb" and row["decision"] == "helper_candidate") == 1, "DuckDB helper candidates mismatch")

    require(len(diff) == 4, "helper diff row count mismatch")
    require(all(row["diff_status"] == "matched" and row["reference_match"] == "1" for row in diff), "helper diff mismatch")

    decision_tools = {row["tool_name"]: row for row in decisions}
    require(set(decision_tools) == {"pandera", "polars", "duckdb", "edgartools", "dlt", "github_mcp_read_only"}, "decision tools mismatch")
    for tool in ["pandera", "polars", "duckdb"]:
        require(decision_tools[tool]["helper_decision"] == "promote_task_scoped_helper_candidate", f"{tool} helper not promoted as task-scoped candidate")
        require(decision_tools[tool]["allowed_next_layer"] == "task_scoped_helper_only_no_src_promotion", f"{tool} bad next layer")
    for tool in ["edgartools", "dlt", "github_mcp_read_only"]:
        require(decision_tools[tool]["helper_decision"] == "defer", f"{tool} should remain deferred")

    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "external_tool_helper_contract_completed_diagnostic_only", "bad closeout verdict")
    require(co["all_acceptance_checks_pass"] == "1", "closeout checks did not pass")
    require(co["task_id"] == "Task3141", "bad task id")
    require(co["helper_candidate_rows"] == "4", "helper candidate row count mismatch")
    require(co["reference_match_rows"] == "4", "reference match row count mismatch")

    manifest_paths = {row["relative_path"] for row in manifest}
    for required in [
        "helper_contracts.csv",
        "helper_replay_result.csv",
        "helper_output_diff.csv",
        "helper_decision_matrix.csv",
        "acceptance_checks.csv",
        "task3141_closeout.csv",
    ]:
        require(required in manifest_paths, f"artifact manifest missing {required}")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3141" for row in registry), "registry missing Task3141")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("Task3127" in op_state, "operating state missing Task3127 prerequisite")
    require("Task3141" in op_state, "operating state missing Task3141")

    report_text = report.read_text(encoding="utf-8")
    require("Strategy: `NOT_ACCEPTED`" in report_text, "report missing strategy footer")
    require("Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`" in report_text, "report missing deployment footer")
    require("Real Capital: `FORBIDDEN`" in report_text, "report missing real capital footer")
    print("[TASK3141_EXTERNAL_TOOL_HELPER_CONTRACT_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
