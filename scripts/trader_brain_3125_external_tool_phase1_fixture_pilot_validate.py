from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3125_external_tool_phase1_fixture_pilot"
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
        for col in ["paper_order_intents_created", "live_orders_created", "selector_changed", "sizing_changed", "replay_performed", "source_acquisition_performed"]:
            if col in row:
                require(row[col] == "0", f"{name} row {idx} has forbidden {col}={row[col]}")


def main() -> None:
    report = REPORT_DIR / "task_3125_external_tool_phase1_fixture_pilot.md"
    decision = REPORT_DIR / "task_3125_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    intake = read_csv(OUT_DIR / "tool_intake_matrix.csv")
    risks = read_csv(OUT_DIR / "tool_risk_register.csv")
    sec = read_csv(OUT_DIR / "sec_fixture_comparison.csv")
    pandera = read_csv(OUT_DIR / "pandera_schema_pilot.csv")
    benchmark = read_csv(OUT_DIR / "local_query_benchmark.csv")
    preview = read_csv(OUT_DIR / "local_query_join_preview.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3125_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")
    decision_rows = read_csv(decision)

    for name, rows in [
        ("intake", intake),
        ("risks", risks),
        ("sec", sec),
        ("pandera", pandera),
        ("benchmark", benchmark),
        ("checks", checks),
        ("closeout", closeout),
        ("decision", decision_rows),
    ]:
        assert_status(rows, name)

    require(len(intake) == 6, "intake must cover six tool families")
    tools = {row["tool_name"]: row for row in intake}
    for tool in ["edgartools", "pandera", "duckdb", "polars", "dlt", "github_mcp_read_only"]:
        require(tool in tools, f"missing intake tool {tool}")
    require(tools["github_mcp_read_only"]["dependency_status"] == "deferred_connector_not_invoked", "GitHub MCP must not be invoked")
    require(tools["edgartools"]["network_required"] == "0_for_fixture_pilot", "edgartools pilot should be offline")

    require(len(risks) == 6, "risk register row count mismatch")
    require(all(row["stop_rule_triggered"] == "0" for row in risks), "stop rule should not be triggered")

    require(len(sec) == 1, "SEC pilot row count mismatch")
    s = sec[0]
    require(int(s["fixture_row_count"]) > 0, "SEC fixture must be nonempty")
    require(s["required_columns_present"] == "1", "SEC fixture required columns missing")
    require(s["raw_identity_preserved_in_existing_fixture"] == "1", "SEC raw identity not preserved in fixture")
    require(s["edgartools_comparison_status"] in {"blocked_dependency_missing", "blocked_adapter_not_promoted_in_fixture_pilot"}, "bad edgartools comparison status")

    require(len(pandera) == 1, "Pandera pilot row count mismatch")
    p = pandera[0]
    require(int(p["row_count"]) == int(s["fixture_row_count"]), "Pandera target should match SEC fixture count")
    require(p["schema_status"] in {"blocked_dependency_missing", "schema_checks_executed"}, "bad Pandera schema status")
    require(p["schema_design_pass_without_dependency"] == "1", "schema design checks should pass")
    require(p["timestamp_missing_rows"] == "0", "timestamp rows missing")

    engines = {row["engine"]: row for row in benchmark}
    for engine in ["pandas", "duckdb", "polars"]:
        require(engine in engines, f"missing benchmark engine {engine}")
    baseline = engines["pandas"]
    require(baseline["dependency_status"] == "available", "pandas baseline missing")
    for engine in ["duckdb", "polars"]:
        if engines[engine]["dependency_status"] == "available":
            require(engines[engine]["row_count_match_pandas"] == "1", f"{engine} row count mismatch")
            require(engines[engine]["join_key_null_match_pandas"] == "1", f"{engine} null count mismatch")
            require(engines[engine]["l3_edge_match_pandas"] == "1", f"{engine} L3 edge count mismatch")
    require(any(row["dependency_status"] == "available" and row["row_count_match_pandas"] == "1" for row in benchmark if row["engine"] in {"duckdb", "polars"}), "no local query engine matched pandas")
    require(len(preview) > 0, "join preview missing")

    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "external_tool_phase1_fixture_pilot_completed_diagnostic_only", "bad closeout verdict")
    require(co["all_acceptance_checks_pass"] == "1", "closeout checks did not pass")

    manifest_paths = {row["relative_path"] for row in manifest}
    for required in [
        "tool_intake_matrix.csv",
        "tool_risk_register.csv",
        "sec_fixture_comparison.csv",
        "pandera_schema_pilot.csv",
        "local_query_benchmark.csv",
        "acceptance_checks.csv",
        "task3125_closeout.csv",
    ]:
        require(required in manifest_paths, f"artifact manifest missing {required}")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3125" for row in registry), "registry missing Task3125")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("157. Task3124" in op_state, "operating state missing Task3124 prerequisite")
    require("158. Task3125" in op_state, "operating state missing Task3125")

    report_text = report.read_text(encoding="utf-8")
    require("Strategy: `NOT_ACCEPTED`" in report_text, "report missing strategy footer")
    require("Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`" in report_text, "report missing deployment footer")
    require("Real Capital: `FORBIDDEN`" in report_text, "report missing real capital footer")
    print("[TASK3125_EXTERNAL_TOOL_PHASE1_FIXTURE_PILOT_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
