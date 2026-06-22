from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3142_external_tool_infra_module_promotion"
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
    report = REPORT_DIR / "task_3142_external_tool_infra_module_promotion.md"
    decision = REPORT_DIR / "task_3142_decision.csv"
    module = ROOT / "src/infra/external_tools.py"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")
    require(module.exists(), "missing common infra module")

    root_dependency_files = [
        ROOT / "requirements.txt",
        ROOT / "requirements-dev.txt",
        ROOT / "pyproject.toml",
        ROOT / "setup.cfg",
        ROOT / "poetry.lock",
        ROOT / "Pipfile",
    ]
    require(not any(path.exists() for path in root_dependency_files), "root dependency manifest was created")

    contracts = read_csv(OUT_DIR / "module_contracts.csv")
    replay = read_csv(OUT_DIR / "module_replay_result.csv")
    diff = read_csv(OUT_DIR / "module_output_diff.csv")
    decisions = read_csv(OUT_DIR / "module_decision_matrix.csv")
    checks = read_csv(OUT_DIR / "acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task3142_closeout.csv")
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

    require(len(contracts) == 6, "module contract count mismatch")
    contract_tools = {row["tool_name"]: row for row in contracts}
    for tool in ["pandera", "polars", "duckdb"]:
        require(contract_tools[tool]["root_dependency_required"] == "0", f"{tool} requires root dependency")
        require(contract_tools[tool]["trading_decision_allowed"] == "0", f"{tool} allowed trading decision")
    for tool in ["edgartools", "dlt", "github_mcp_read_only"]:
        require(contract_tools[tool]["allowed_layers"].startswith("none_until"), f"{tool} should remain deferred")

    require(len(replay) == 4, "module replay row count mismatch")
    require(all(row["reference_match"] == "1" for row in replay), "module replay did not match references")
    require(sum(1 for row in replay if row["module_candidate"] == "1") == 4, "expected four module candidates")
    for row in replay:
        if row["tool_name"] in {"polars", "duckdb"}:
            for col in [
                "row_count_match_pandas",
                "join_key_null_match_pandas",
                "aggregate_checksum_match_pandas",
                "strict_gate_pass_total_match_pandas",
                "faster_than_pandas",
            ]:
                require(row[col] == "1", f"{row['source_wrapper_id']} failed {col}")

    require(len(diff) == 4, "module diff row count mismatch")
    require(all(row["diff_status"] == "matched" and row["reference_match"] == "1" for row in diff), "module diff mismatch")

    decision_tools = {row["tool_name"]: row for row in decisions}
    require(set(decision_tools) == {"pandera", "polars", "duckdb", "edgartools", "dlt", "github_mcp_read_only"}, "decision tools mismatch")
    for tool in ["pandera", "polars", "duckdb"]:
        require(decision_tools[tool]["module_decision"] == "promote_common_infra_candidate", f"{tool} module not promoted")
        require(decision_tools[tool]["allowed_next_layer"] == "src_infra_external_tools_diagnostic_only", f"{tool} bad next layer")
    for tool in ["edgartools", "dlt", "github_mcp_read_only"]:
        require(decision_tools[tool]["module_decision"] == "defer", f"{tool} should remain deferred")

    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")
    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["task_id"] == "Task3142", "bad task id")
    require(co["verdict"] == "external_tool_infra_module_promotion_completed_diagnostic_only", "bad closeout verdict")
    require(co["all_acceptance_checks_pass"] == "1", "closeout checks did not pass")
    require(co["module_candidate_rows"] == "4", "module candidate row count mismatch")
    require(co["reference_match_rows"] == "4", "reference match row count mismatch")

    manifest_paths = {row["relative_path"] for row in manifest}
    for required in [
        "module_contracts.csv",
        "module_replay_result.csv",
        "module_output_diff.csv",
        "module_decision_matrix.csv",
        "acceptance_checks.csv",
        "task3142_closeout.csv",
    ]:
        require(required in manifest_paths, f"artifact manifest missing {required}")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task3142" for row in registry), "registry missing Task3142")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("Task3141" in op_state, "operating state missing Task3141 prerequisite")
    require("Task3142" in op_state, "operating state missing Task3142")

    module_text = module.read_text(encoding="utf-8")
    require("def dependency_status" in module_text, "module missing dependency_status")
    require("def validate_sec_panel_schema_with_pandera" in module_text, "module missing pandera validator")
    require("def polars_strict_gate_aggregate" in module_text, "module missing polars aggregator")
    require("def duckdb_strict_gate_aggregate" in module_text, "module missing duckdb aggregator")
    forbidden_tokens = ["selector_changed = 1", "paper_order", "live_order"]
    require("paper_order_intents_created" not in module_text, "module should not carry task status fields")
    require(not any(token in module_text for token in forbidden_tokens), "module contains forbidden trading text")

    report_text = report.read_text(encoding="utf-8")
    require("Strategy: `NOT_ACCEPTED`" in report_text, "report missing strategy footer")
    require("Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`" in report_text, "report missing deployment footer")
    require("Real Capital: `FORBIDDEN`" in report_text, "report missing real capital footer")
    print("[TASK3142_EXTERNAL_TOOL_INFRA_MODULE_PROMOTION_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
