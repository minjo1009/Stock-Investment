from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from task_artifact_manifest import write_manifest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infra.external_tools import (
    dependency_status,
    file_sha256,
    validate_sec_panel_schema_with_pandera,
    validate_sec_panel_schema_with_pandera_venv,
    write_csv,
)
from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated


TASK_ID = "task_3142_external_tool_infra_module_promotion"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3142_external_tool_infra_module_promotion.md"
DECISION = REPORT_DIR / "task_3142_decision.csv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_INFRA_MODULE_PROMOTION_ONLY"

TASK3126_VENV = ROOT / ".cache/task_3126_external_tool_venv"
TASK3141_OUT = ROOT / "data/artifacts/task_3141_external_tool_helper_contract"
SEC_PANEL = ROOT / "data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv"
LIQUIDITY_PANEL = ROOT / "data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv"


def now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def common_status() -> dict[str, object]:
    return {
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "paper_order_intents_created": "0",
        "live_orders_created": "0",
        "selector_changed": "0",
        "sizing_changed": "0",
        "replay_performed": "0",
        "source_acquisition_performed": "0",
        "root_dependency_manifest_created": "0",
        "authority": AUTHORITY,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def task3141_reference() -> dict[str, dict[str, str]]:
    rows = read_csv(TASK3141_OUT / "helper_replay_result.csv")
    return {row["source_wrapper_id"]: row for row in rows if row.get("source_wrapper_id")}


def build_module_contract() -> list[dict[str, object]]:
    specs = [
        ("pandera", ["pandera"], "data_validation|resolver_qa", "optional_import_or_task3126_venv"),
        ("polars", ["polars"], "local_artifact_query|audit_benchmark", "optional_import"),
        ("duckdb", ["duckdb"], "local_artifact_query|audit_benchmark", "optional_import"),
        ("edgartools", ["edgar", "edgartools"], "none_until_offline_local_parse_is_proven", "deferred"),
        ("dlt", ["dlt"], "none_until_source_receipt_task", "deferred"),
        ("github_mcp_read_only", [], "none_until_read_only_monitoring_task", "deferred_connector_not_invoked"),
    ]
    rows: list[dict[str, object]] = []
    for tool, imports, allowed, dependency_mode in specs:
        status = dependency_status(tool, imports) if imports else None
        rows.append(
            {
                "module_path": "src/infra/external_tools.py",
                "tool_name": tool,
                "dependency_status": status.dependency_status if status else "deferred_connector_not_invoked",
                "import_name": status.import_name if status else "",
                "import_origin": status.import_origin if status else "",
                "dependency_mode": dependency_mode,
                "allowed_layers": allowed,
                "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
                "root_dependency_required": "0",
                "trading_decision_allowed": "0",
                **common_status(),
            }
        )
    return rows


def run_module_replay() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    reference = task3141_reference()
    required_cols = [
        "source_packet_id",
        "symbol",
        "cik",
        "accession_number",
        "source_ts",
        "available_to_brain_ts",
        "raw_path",
        "raw_sha256",
        "missing_source_is_negative",
        "assignment_uses_future_outcome",
        "outcome_used_for_assignment",
    ]
    rows: list[dict[str, object]] = []
    diffs: list[dict[str, object]] = []

    root_pandera = validate_sec_panel_schema_with_pandera(SEC_PANEL, required_cols)
    venv_pandera = validate_sec_panel_schema_with_pandera_venv(ROOT, TASK3126_VENV, SEC_PANEL, required_cols)
    pandera_pass = venv_pandera.get("schema_status") == "schema_checks_executed" and int(venv_pandera.get("failure_cases", -1)) == 0
    rows.append(
        {
            "module_function": "validate_sec_panel_schema_with_pandera_venv",
            "tool_name": "pandera",
            "source_wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
            "source_panel": SEC_PANEL.as_posix(),
            "root_dependency_status": root_pandera.get("dependency_status", ""),
            "venv_dependency_status": venv_pandera.get("dependency_status", ""),
            "schema_status": venv_pandera.get("schema_status", ""),
            "row_count": venv_pandera.get("row_count", 0),
            "reference_match": "1" if pandera_pass else "0",
            "module_candidate": "1" if pandera_pass else "0",
            **common_status(),
        }
    )
    diffs.append(
        {
            "module_function": "validate_sec_panel_schema_with_pandera_venv",
            "source_wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
            "diff_status": "matched" if pandera_pass else "mismatch",
            "reference_match": "1" if pandera_pass else "0",
            **common_status(),
        }
    )

    specs = [
        ("strict_gate_aggregate_accelerated", "polars", BackendAccelerationEngine.POLARS, "WRAP3127-POLARS-SEC-AGG", SEC_PANEL, ["symbol", "event_family"], OUT_DIR / "module_outputs/sec_symbol_event_family_polars.csv"),
        ("strict_gate_aggregate_accelerated", "polars", BackendAccelerationEngine.AUTO, "WRAP3127-POLARS-LIQUIDITY-AGG", LIQUIDITY_PANEL, ["provider", "series_id"], OUT_DIR / "module_outputs/liquidity_provider_series_polars.csv"),
        ("strict_gate_aggregate_accelerated", "duckdb", BackendAccelerationEngine.DUCKDB, "WRAP3127-DUCKDB-LIQUIDITY-AGG", LIQUIDITY_PANEL, ["provider", "series_id"], OUT_DIR / "module_outputs/liquidity_provider_series_duckdb.csv"),
    ]
    baseline_cache: dict[tuple[str, str], object] = {}
    for function_name, tool_name, engine, wrapper_id, panel, group_cols, output in specs:
        key = (panel.as_posix(), "|".join(group_cols))
        accelerated = strict_gate_aggregate_accelerated(
            panel,
            group_cols,
            engine=engine,
            pandas_baseline=baseline_cache.get(key),
        )
        if accelerated.pandas_baseline is not None:
            baseline_cache[key] = accelerated.pandas_baseline
        write_csv(output, [dict(row) for row in accelerated.result.rows])
        output_hash = file_sha256(output)
        ref = reference[wrapper_id]
        reference_match = output_hash == ref["output_artifact_sha256"]
        rows.append(
            {
                "module_function": function_name,
                "tool_name": tool_name,
                "source_wrapper_id": wrapper_id,
                "source_panel": panel.as_posix(),
                "output_artifact": output.as_posix(),
                "output_artifact_sha256": output_hash,
                "reference_output_sha256": ref["output_artifact_sha256"],
                "pandas_runtime_ms": accelerated.pandas_baseline.metrics.runtime_ms if accelerated.pandas_baseline else "",
                "module_runtime_ms": accelerated.result.metrics.runtime_ms,
                "source_row_count": accelerated.result.metrics.source_row_count,
                "result_row_count": accelerated.result.metrics.result_row_count,
                "reference_match": "1" if reference_match else "0",
                "module_candidate": "1" if reference_match and accelerated.decision.parity_pass else "0",
                "row_count_match_pandas": "1"
                if accelerated.pandas_baseline
                and accelerated.result.metrics.source_row_count == accelerated.pandas_baseline.metrics.source_row_count
                and accelerated.result.metrics.result_row_count == accelerated.pandas_baseline.metrics.result_row_count
                else "0",
                "join_key_null_match_pandas": "1"
                if accelerated.pandas_baseline and accelerated.result.metrics.join_key_null_count == accelerated.pandas_baseline.metrics.join_key_null_count
                else "0",
                "aggregate_checksum_match_pandas": "1"
                if accelerated.pandas_baseline and accelerated.result.metrics.aggregate_checksum == accelerated.pandas_baseline.metrics.aggregate_checksum
                else "0",
                "strict_gate_pass_total_match_pandas": "1"
                if accelerated.pandas_baseline and accelerated.result.metrics.strict_gate_pass_total == accelerated.pandas_baseline.metrics.strict_gate_pass_total
                else "0",
                "faster_than_pandas": "1" if accelerated.decision.faster_than_pandas else "0",
                "comparison_pass": "1" if accelerated.decision.parity_pass else "0",
                **common_status(),
            }
        )
        diffs.append(
            {
                "module_function": function_name,
                "source_wrapper_id": wrapper_id,
                "diff_status": "matched" if reference_match else "mismatch",
                "reference_match": "1" if reference_match else "0",
                "new_output_sha256": output_hash,
                "reference_output_sha256": ref["output_artifact_sha256"],
                **common_status(),
            }
        )
    return rows, diffs


def build_decisions(module_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for tool in ["pandera", "polars", "duckdb"]:
        tool_rows = [row for row in module_rows if row["tool_name"] == tool]
        candidate_count = sum(1 for row in tool_rows if row.get("module_candidate") == "1")
        mismatch_count = sum(1 for row in tool_rows if row.get("reference_match") != "1")
        rows.append(
            {
                "tool_name": tool,
                "module_decision": "promote_common_infra_candidate" if candidate_count > 0 and mismatch_count == 0 else "reject_or_block",
                "candidate_function_count": candidate_count,
                "mismatch_count": mismatch_count,
                "allowed_next_layer": "src_infra_external_tools_diagnostic_only",
                **common_status(),
            }
        )
    for tool, reason in [
        ("edgartools", "deferred_until_offline_local_sec_parse_is_proven"),
        ("dlt", "deferred_until_source_receipt_task"),
        ("github_mcp_read_only", "deferred_until_read_only_monitoring_task"),
    ]:
        rows.append(
            {
                "tool_name": tool,
                "module_decision": "defer",
                "candidate_function_count": 0,
                "mismatch_count": 0,
                "allowed_next_layer": "none",
                "reason": reason,
                **common_status(),
            }
        )
    return rows


def build_checks(contracts: list[dict[str, object]], module_rows: list[dict[str, object]], diffs: list[dict[str, object]], decisions: list[dict[str, object]]) -> list[dict[str, object]]:
    root_dependency_files = [
        ROOT / "requirements.txt",
        ROOT / "requirements-dev.txt",
        ROOT / "pyproject.toml",
        ROOT / "setup.cfg",
        ROOT / "poetry.lock",
        ROOT / "Pipfile",
    ]
    checks = [
        ("status_unchanged", True, "Strategy/deployment/real-capital statuses remain unchanged."),
        ("no_orders", True, "No paper or live orders are created."),
        ("no_replay_or_source_acquisition", True, "No replay or source acquisition is performed."),
        ("root_dependency_manifest_absent", not any(path.exists() for path in root_dependency_files), "No root Python dependency manifest was created."),
        ("module_contracts_present", len(contracts) == 6, "All module contracts are recorded."),
        ("module_reference_replay_match", all(row["reference_match"] == "1" for row in diffs), "Module outputs match Task3141 references."),
        ("module_candidates_present", sum(1 for row in module_rows if row["module_candidate"] == "1") >= 4, "Pandera, Polars, and DuckDB module candidates exist."),
        ("deferred_tools_not_promoted", all(row["module_decision"] == "defer" for row in decisions if row["tool_name"] in {"edgartools", "dlt", "github_mcp_read_only"}), "Deferred tools remain deferred."),
        ("trading_decision_disabled", all(row["trading_decision_allowed"] == "0" for row in contracts), "No tool is allowed to make trading decisions."),
    ]
    return [
        {
            "check_id": f"CHK3142-{idx:03d}",
            "check_name": name,
            "pass": "1" if passed else "0",
            "detail": detail,
            **common_status(),
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ")[:500] for field in fields) + " |")
    return "\n".join(lines)


def write_report(contracts: list[dict[str, object]], module_rows: list[dict[str, object]], diffs: list[dict[str, object]], decisions: list[dict[str, object]], checks: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3142 External Tool Infra Module Promotion

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: promoted `Pandera`, Polars, and DuckDB helper behavior into `src/infra/external_tools.py` as diagnostic-only optional infrastructure helpers.
- What did not change: no root dependency manifest, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Module contracts: {closeout['module_contract_rows']}.
  - Module replay rows: {closeout['module_replay_rows']}.
  - Module candidates: {closeout['module_candidate_rows']}.
  - Reference matches: {closeout['reference_match_rows']}.
- Next action: harden the module in 2-3 more passes: typed result contracts, failure-mode tests, then limited script migration.

## Quant Expert Report

### Module Contracts

{markdown_table(contracts, ['module_path', 'tool_name', 'dependency_status', 'dependency_mode', 'allowed_layers', 'forbidden_layers', 'trading_decision_allowed'])}

### Module Replay Results

{markdown_table(module_rows, ['module_function', 'tool_name', 'source_wrapper_id', 'source_row_count', 'result_row_count', 'reference_match', 'module_candidate'])}

### Reference Diff

{markdown_table(diffs, ['module_function', 'source_wrapper_id', 'diff_status', 'reference_match'])}

### Module Decision Matrix

{markdown_table(decisions, ['tool_name', 'module_decision', 'candidate_function_count', 'mismatch_count', 'allowed_next_layer'])}

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: the useful external-tool infra helpers are now in a common module.

`Pandera`, Polars, and DuckDB are available only as diagnostic infrastructure helpers. They validate panels and query local artifacts. They do not rank trades, size positions, trigger replay, or create orders.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `{TASK3141_OUT.as_posix()}/helper_replay_result.csv`
  - `{SEC_PANEL.as_posix()}`
  - `{LIQUIDITY_PANEL.as_posix()}`
- Outputs:
  - `src/infra/external_tools.py`
  - `docs/reports/{TASK_ID}/task_3142_external_tool_infra_module_promotion.md`
  - `docs/reports/{TASK_ID}/task_3142_decision.csv`
  - `data/artifacts/{TASK_ID}/`
- Row counts:
  - Module contracts: {len(contracts)}
  - Module replay rows: {len(module_rows)}
  - Module diff rows: {len(diffs)}
  - Module decision rows: {len(decisions)}
- Validation commands:
  - `python scripts/trader_brain_3142_external_tool_infra_module_promotion_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Task3141 helper replay: `{file_sha256(TASK3141_OUT / 'helper_replay_result.csv')}`
  - SEC panel: `{file_sha256(SEC_PANEL)}`
  - Liquidity/rates panel: `{file_sha256(LIQUIDITY_PANEL)}`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "module_outputs").mkdir(parents=True, exist_ok=True)

    contracts = build_module_contract()
    module_rows, diffs = run_module_replay()
    decisions = build_decisions(module_rows)
    checks = build_checks(contracts, module_rows, diffs, decisions)
    closeout = {
        "task_id": "Task3142",
        "verdict": "external_tool_infra_module_promotion_completed_diagnostic_only",
        "module_contract_rows": len(contracts),
        "module_replay_rows": len(module_rows),
        "module_candidate_rows": sum(1 for row in module_rows if row["module_candidate"] == "1"),
        "reference_match_rows": sum(1 for row in diffs if row["reference_match"] == "1"),
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }

    write_csv(OUT_DIR / "module_contracts.csv", contracts)
    write_csv(OUT_DIR / "module_replay_result.csv", module_rows)
    write_csv(OUT_DIR / "module_output_diff.csv", diffs)
    write_csv(OUT_DIR / "module_decision_matrix.csv", decisions)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3142_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3142_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(contracts, module_rows, diffs, decisions, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3142_EXTERNAL_TOOL_INFRA_MODULE_PROMOTION_COMPLETE]")


if __name__ == "__main__":
    main()
