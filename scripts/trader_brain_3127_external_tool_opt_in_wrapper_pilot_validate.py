from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3127_external_tool_opt_in_wrapper_pilot"
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
        ]:
            if col in row:
                require(row[col] == "0", f"{name} row {idx} has forbidden {col}={row[col]}")


def main() -> None:
    report = REPORT_DIR / "task_3127_external_tool_opt_in_wrapper_pilot.md"
    decision = REPORT_DIR / "task_3127_decision.csv"
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

    contracts = read_csv(OUT_DIR / "wrapper_contracts.csv")
    pandera = read_csv(OUT_DIR / "pandera_wrapper_result.csv")
    query = read_csv(OUT_DIR / "local_query_wrapper_result.csv")
    preview = read_csv(OUT_DIR / "local_query_wrapper_preview.csv")
    decisions = read_csv(OUT_DIR / "wrapper_decision_matrix.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3127_closeout.csv")
    decision_rows = read_csv(decision)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("contracts", contracts),
        ("pandera", pandera),
        ("query", query),
        ("decisions", decisions),
        ("checks", checks),
        ("closeout", closeout),
        ("decision", decision_rows),
    ]:
        assert_status(rows, name)

    require(len(contracts) == 7, "wrapper contract count mismatch")
    contract_by_id = {row["wrapper_id"]: row for row in contracts}
    for wrapper_id in [
        "WRAP3127-PANDERA-SEC-SCHEMA",
        "WRAP3127-POLARS-SEC-AGG",
        "WRAP3127-POLARS-LIQUIDITY-AGG",
        "WRAP3127-DUCKDB-LIQUIDITY-AGG",
    ]:
        require(contract_by_id[wrapper_id]["wrapper_status"] == "enabled", f"{wrapper_id} should be enabled")
    for wrapper_id in [
        "WRAP3127-EDGARTOOLS-OFFLINE-SEC",
        "WRAP3127-DLT-RECEIPT",
        "WRAP3127-GITHUB-MCP-READONLY",
    ]:
        require(contract_by_id[wrapper_id]["wrapper_status"] == "deferred", f"{wrapper_id} should be deferred")
    require(all(row["writes_only_under_task_artifacts"] == "1" for row in contracts), "wrapper write scope not constrained")
    require(all(row["requires_root_dependency"] == "0" for row in contracts), "wrapper requires root dependency")

    require(len(pandera) == 1, "Pandera wrapper row count mismatch")
    p = pandera[0]
    require(p["wrapper_status"] == "executed", "Pandera wrapper not executed")
    require(p["schema_status"] == "schema_checks_executed", "Pandera schema did not execute")
    require(p["pandera_validator_pass"] == "1", "Pandera wrapper failed")
    require(p["decision"] == "wrapper_candidate", "Pandera wrapper is not a candidate")
    require(int(p["row_count"]) > 0, "Pandera wrapper row count missing")

    require(len(query) == 3, "query wrapper row count mismatch")
    expected_query_ids = {
        "WRAP3127-POLARS-SEC-AGG",
        "WRAP3127-POLARS-LIQUIDITY-AGG",
        "WRAP3127-DUCKDB-LIQUIDITY-AGG",
    }
    require({row["wrapper_id"] for row in query} == expected_query_ids, "unexpected query wrappers")
    for row in query:
        require(row["wrapper_status"] == "executed", f"{row['wrapper_id']} did not execute")
        for col in [
            "row_count_match_pandas",
            "join_key_null_match_pandas",
            "aggregate_checksum_match_pandas",
            "strict_gate_pass_total_match_pandas",
        ]:
            require(row[col] == "1", f"{row['wrapper_id']} mismatch on {col}")
        require(row["decision"] in {"wrapper_candidate", "reject"}, f"{row['wrapper_id']} has bad decision")
        if row["decision"] == "wrapper_candidate":
            require(row["faster_than_pandas"] == "1", f"{row['wrapper_id']} candidate is not faster")
            output = Path(row["output_artifact"])
            require(output.exists(), f"{row['wrapper_id']} output artifact missing")
    require(any(row["decision"] == "wrapper_candidate" for row in query), "no query wrapper candidate")
    require(len(preview) > 0, "query preview missing")

    decision_tools = {row["tool_name"]: row for row in decisions}
    require(set(decision_tools) == {"pandera", "polars", "duckdb", "edgartools", "dlt", "github_mcp_read_only"}, "decision tools mismatch")
    require(decision_tools["pandera"]["wrapper_decision"] == "adopt_wrapper_candidate", "Pandera wrapper not adopted")
    require(decision_tools["polars"]["wrapper_decision"] == "adopt_wrapper_candidate", "Polars wrapper not adopted")
    require(decision_tools["duckdb"]["wrapper_decision"] in {"adopt_wrapper_candidate", "reject_or_block"}, "bad DuckDB wrapper decision")
    require(decision_tools["edgartools"]["wrapper_decision"] == "defer", "edgartools should remain deferred")
    require(decision_tools["dlt"]["wrapper_decision"] == "defer", "dlt should remain deferred")
    require(decision_tools["github_mcp_read_only"]["wrapper_decision"] == "defer", "GitHub MCP should remain deferred")

    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "external_tool_opt_in_wrapper_pilot_completed_diagnostic_only", "bad closeout verdict")
    require(co["all_acceptance_checks_pass"] == "1", "closeout checks did not pass")
    require(int(co["wrapper_candidate_rows"]) >= 2, "expected at least Pandera and one query candidate")

    manifest_paths = {row["relative_path"] for row in manifest}
    for required in [
        "wrapper_contracts.csv",
        "pandera_wrapper_result.csv",
        "local_query_wrapper_result.csv",
        "local_query_wrapper_preview.csv",
        "wrapper_decision_matrix.csv",
        "acceptance_checks.csv",
        "task3127_closeout.csv",
    ]:
        require(required in manifest_paths, f"artifact manifest missing {required}")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3127" for row in registry), "registry missing Task3127")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("159. Task3126" in op_state, "operating state missing Task3126 prerequisite")
    require("160. Task3127" in op_state, "operating state missing Task3127")

    report_text = report.read_text(encoding="utf-8")
    require("Strategy: `NOT_ACCEPTED`" in report_text, "report missing strategy footer")
    require("Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`" in report_text, "report missing deployment footer")
    require("Real Capital: `FORBIDDEN`" in report_text, "report missing real capital footer")
    print("[TASK3127_EXTERNAL_TOOL_OPT_IN_WRAPPER_PILOT_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
