from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3126_external_tool_isolated_install_pilot"
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
    report = REPORT_DIR / "task_3126_external_tool_isolated_install_pilot.md"
    decision = REPORT_DIR / "task_3126_decision.csv"
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

    install_log = read_csv(OUT_DIR / "install_run_log.csv")
    install_lock = read_csv(OUT_DIR / "tool_install_lock.csv")
    edgar_comparison = read_csv(OUT_DIR / "edgartools_local_parse_comparison.csv")
    edgar_summary = read_csv(OUT_DIR / "edgartools_local_parse_summary.csv")
    pandera_validation = read_csv(OUT_DIR / "pandera_validation_report.csv")
    validator_diff = read_csv(OUT_DIR / "validator_diff_report.csv")
    benchmark = read_csv(OUT_DIR / "large_panel_query_benchmark.csv")
    decisions = read_csv(OUT_DIR / "adoption_decision_matrix.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3126_closeout.csv")
    decision_rows = read_csv(decision)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("install_log", install_log),
        ("install_lock", install_lock),
        ("edgar_comparison", edgar_comparison),
        ("edgar_summary", edgar_summary),
        ("pandera_validation", pandera_validation),
        ("validator_diff", validator_diff),
        ("benchmark", benchmark),
        ("decisions", decisions),
        ("checks", checks),
        ("closeout", closeout),
        ("decision", decision_rows),
    ]:
        assert_status(rows, name)

    tools = {row["tool_name"]: row for row in install_lock}
    require(set(tools) == {"edgartools", "pandera"}, "install lock must cover edgartools and pandera")
    for tool, row in tools.items():
        require(row["network_used_for_pip_install"] == "1" or row["install_status"].startswith("blocked"), f"{tool} install network flag missing")
        require(row["raw_source_downloaded"] == "0", f"{tool} downloaded raw source")
        if row["install_status"] == "installed":
            require(row["import_available"] == "1", f"{tool} installed without import")
            require(row["version"], f"{tool} missing installed version")

    require((OUT_DIR / "pip_freeze_external_tool_pilot.txt").exists(), "missing pip freeze")

    require(len(edgar_summary) == 1, "edgartools summary row count mismatch")
    edgar = edgar_summary[0]
    require(edgar["adoption_decision"] in {"blocked", "defer", "reject"}, "edgartools must not be a direct adoption")
    require(edgar["comparison_status"] in {"blocked_install_or_py_compat", "tool_api_not_local_file_compatible", "local_parser_candidates_found_not_executed_no_safe_constructor"}, "bad edgartools comparison status")
    require(int(edgar["sample_row_count"]) > 0, "edgartools comparison sample missing")
    require(all(row["raw_identity_preserved"] == "1" for row in edgar_comparison), "edgartools sample lost raw identity")

    require(len(pandera_validation) == 1, "Pandera validation row count mismatch")
    require(len(validator_diff) == 1, "validator diff row count mismatch")
    require(pandera_validation[0]["imperative_validator_pass"] == "1", "existing imperative validator checks should pass")
    require(validator_diff[0]["adoption_decision"] in {"adopt", "blocked", "reject"}, "bad Pandera adoption decision")
    if validator_diff[0]["adoption_decision"] == "adopt":
        require(pandera_validation[0]["pandera_validator_pass"] == "1", "Pandera adopted without passing")
        require(validator_diff[0]["row_count_match"] == "1", "Pandera adopted without row count match")

    require(len(benchmark) == 6, "large panel benchmark must cover two queries and three engines")
    by_query: dict[str, dict[str, dict[str, str]]] = {}
    for row in benchmark:
        by_query.setdefault(row["query_id"], {})[row["engine"]] = row
    require(set(by_query) == {"sec_symbol_event_family_agg", "liquidity_provider_series_agg"}, "unexpected benchmark query ids")
    for query_id, engines in by_query.items():
        require(set(engines) == {"pandas", "duckdb", "polars"}, f"{query_id} missing engines")
        require(engines["pandas"]["dependency_status"] == "available", f"{query_id} pandas baseline missing")
        for engine in ["duckdb", "polars"]:
            if engines[engine]["dependency_status"] == "available":
                for col in [
                    "row_count_match_pandas",
                    "join_key_null_match_pandas",
                    "aggregate_checksum_match_pandas",
                    "strict_gate_pass_total_match_pandas",
                ]:
                    require(engines[engine][col] == "1", f"{query_id} {engine} mismatch on {col}")

    decision_tools = {row["tool_name"]: row for row in decisions}
    require(set(decision_tools) == {"edgartools", "pandera", "duckdb", "polars", "dlt", "github_mcp_read_only"}, "decisions do not cover all planned tools")
    for row in decisions:
        require(row["decision"] in {"adopt", "defer", "reject", "blocked"}, f"bad decision for {row['tool_name']}")
    require(decision_tools["dlt"]["decision"] == "defer", "dlt should remain deferred")
    require(decision_tools["github_mcp_read_only"]["decision"] == "defer", "GitHub MCP should remain deferred")

    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "external_tool_isolated_install_pilot_completed_diagnostic_only", "bad closeout verdict")
    require(co["all_acceptance_checks_pass"] == "1", "closeout checks did not pass")

    manifest_paths = {row["relative_path"] for row in manifest}
    for required in [
        "install_run_log.csv",
        "tool_install_lock.csv",
        "pip_freeze_external_tool_pilot.txt",
        "edgartools_local_parse_comparison.csv",
        "edgartools_local_parse_summary.csv",
        "pandera_validation_report.csv",
        "validator_diff_report.csv",
        "large_panel_query_benchmark.csv",
        "adoption_decision_matrix.csv",
        "acceptance_checks.csv",
        "task3126_closeout.csv",
    ]:
        require(required in manifest_paths, f"artifact manifest missing {required}")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3126" for row in registry), "registry missing Task3126")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("158. Task3125" in op_state, "operating state missing Task3125 prerequisite")
    require("159. Task3126" in op_state, "operating state missing Task3126")

    report_text = report.read_text(encoding="utf-8")
    require("Strategy: `NOT_ACCEPTED`" in report_text, "report missing strategy footer")
    require("Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`" in report_text, "report missing deployment footer")
    require("Real Capital: `FORBIDDEN`" in report_text, "report missing real capital footer")
    print("[TASK3126_EXTERNAL_TOOL_ISOLATED_INSTALL_PILOT_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
