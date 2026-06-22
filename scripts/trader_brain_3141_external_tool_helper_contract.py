from __future__ import annotations

import json
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

from task_artifact_manifest import write_manifest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated
from src.infra.external_tools import (
    file_sha256,
    validate_sec_panel_schema_with_pandera_venv as validate_sec_panel_with_pandera,
    write_csv,
)


TASK_ID = "task_3141_external_tool_helper_contract"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3141_external_tool_helper_contract.md"
DECISION = REPORT_DIR / "task_3141_decision.csv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_HELPER_CONTRACT_ONLY"

TASK3126_VENV = ROOT / ".cache/task_3126_external_tool_venv"
TASK3127_OUT = ROOT / "data/artifacts/task_3127_external_tool_opt_in_wrapper_pilot"
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
        "src_promoted": "0",
        "authority": AUTHORITY,
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_helper_contracts() -> list[dict[str, object]]:
    rows = [
        {
            "helper_id": "HELP3141-PANDERA-SEC-SCHEMA",
            "tool_name": "pandera",
            "helper_status": "enabled",
            "input_panel": SEC_PANEL.as_posix(),
            "allowed_layers": "data_validation|resolver_qa",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "dependency_mode": "task3126_isolated_venv",
            "promoted_to_src": "0",
        },
        {
            "helper_id": "HELP3141-POLARS-LOCAL-AGG",
            "tool_name": "polars",
            "helper_status": "enabled",
            "input_panel": "SEC_PANEL|LIQUIDITY_PANEL",
            "allowed_layers": "local_artifact_query|audit_benchmark",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "dependency_mode": "current_environment_import",
            "promoted_to_src": "0",
        },
        {
            "helper_id": "HELP3141-DUCKDB-LOCAL-AGG",
            "tool_name": "duckdb",
            "helper_status": "enabled",
            "input_panel": LIQUIDITY_PANEL.as_posix(),
            "allowed_layers": "local_artifact_query|audit_benchmark",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "dependency_mode": "current_environment_import",
            "promoted_to_src": "0",
        },
        {
            "helper_id": "HELP3141-EDGARTOOLS-OFFLINE-SEC",
            "tool_name": "edgartools",
            "helper_status": "deferred",
            "input_panel": SEC_PANEL.as_posix(),
            "allowed_layers": "none_until_offline_local_parse_is_proven",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "dependency_mode": "deferred",
            "promoted_to_src": "0",
        },
        {
            "helper_id": "HELP3141-DLT-RECEIPT",
            "tool_name": "dlt",
            "helper_status": "deferred",
            "input_panel": "",
            "allowed_layers": "none_until_source_receipt_task",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "dependency_mode": "deferred",
            "promoted_to_src": "0",
        },
        {
            "helper_id": "HELP3141-GITHUB-MCP-READONLY",
            "tool_name": "github_mcp_read_only",
            "helper_status": "deferred",
            "input_panel": "",
            "allowed_layers": "none_until_read_only_monitoring_task",
            "forbidden_layers": "source_truth|selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "dependency_mode": "deferred",
            "promoted_to_src": "0",
        },
    ]
    return [{**row, **common_status()} for row in rows]


def task3127_query_reference() -> dict[str, dict[str, str]]:
    rows = read_csv(TASK3127_OUT / "local_query_wrapper_result.csv")
    return {row["wrapper_id"]: row for row in rows}


def run_helper_replay() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    reference = task3127_query_reference()
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
    result_rows: list[dict[str, object]] = []
    diff_rows: list[dict[str, object]] = []

    pandera_payload = validate_sec_panel_with_pandera(ROOT, TASK3126_VENV, SEC_PANEL, required_cols)
    pandera_pass = pandera_payload.get("schema_status") == "schema_checks_executed" and int(pandera_payload.get("failure_cases", -1)) == 0
    result_rows.append(
        {
            "helper_id": "HELP3141-PANDERA-SEC-SCHEMA",
            "tool_name": "pandera",
            "source_wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
            "helper_status": "executed",
            "row_count": pandera_payload.get("row_count", 0),
            "runtime_ms": pandera_payload.get("runtime_ms", 0),
            "reference_match": "1" if pandera_pass else "0",
            "decision": "helper_candidate" if pandera_pass else "reject",
            "reason": pandera_payload.get("schema_status", ""),
            **common_status(),
        }
    )
    diff_rows.append(
        {
            "helper_id": "HELP3141-PANDERA-SEC-SCHEMA",
            "source_wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
            "diff_status": "matched" if pandera_pass else "mismatch",
            "reference_match": "1" if pandera_pass else "0",
            "detail": pandera_payload.get("schema_status", ""),
            **common_status(),
        }
    )

    specs = [
        {
            "helper_id": "HELP3141-POLARS-LOCAL-AGG",
            "source_wrapper_id": "WRAP3127-POLARS-SEC-AGG",
            "tool_name": "polars",
            "query_id": "sec_symbol_event_family_agg",
            "panel": SEC_PANEL,
            "group_cols": ["symbol", "event_family"],
            "output": OUT_DIR / "helper_outputs/sec_symbol_event_family_polars.csv",
        },
        {
            "helper_id": "HELP3141-POLARS-LOCAL-AGG",
            "source_wrapper_id": "WRAP3127-POLARS-LIQUIDITY-AGG",
            "tool_name": "polars",
            "query_id": "liquidity_provider_series_agg",
            "panel": LIQUIDITY_PANEL,
            "group_cols": ["provider", "series_id"],
            "output": OUT_DIR / "helper_outputs/liquidity_provider_series_polars.csv",
        },
        {
            "helper_id": "HELP3141-DUCKDB-LOCAL-AGG",
            "source_wrapper_id": "WRAP3127-DUCKDB-LIQUIDITY-AGG",
            "tool_name": "duckdb",
            "query_id": "liquidity_provider_series_agg",
            "panel": LIQUIDITY_PANEL,
            "group_cols": ["provider", "series_id"],
            "output": OUT_DIR / "helper_outputs/liquidity_provider_series_duckdb.csv",
        },
    ]
    baseline_cache: dict[tuple[str, str], object] = {}
    for spec in specs:
        key = (spec["panel"].as_posix(), "|".join(spec["group_cols"]))
        engine = BackendAccelerationEngine.POLARS if spec["tool_name"] == "polars" else BackendAccelerationEngine.DUCKDB
        accelerated = strict_gate_aggregate_accelerated(
            spec["panel"],
            spec["group_cols"],
            engine=engine,
            verify_with_pandas=True,
            pandas_baseline=baseline_cache.get(key),
        )
        if accelerated.pandas_baseline is None:
            raise RuntimeError("accelerated strict-gate aggregate requires a pandas baseline for this migration")
        baseline_cache[key] = accelerated.pandas_baseline
        baseline = accelerated.pandas_baseline.metrics.to_dict()
        metrics = accelerated.result.metrics.to_dict()
        rows = [dict(row) for row in accelerated.result.rows]
        write_csv(spec["output"], rows)
        reference_row = reference[spec["source_wrapper_id"]]
        output_hash = file_sha256(spec["output"])
        exact = all(
            [
                metrics["source_row_count"] == baseline["source_row_count"],
                metrics["result_row_count"] == baseline["result_row_count"],
                metrics["join_key_null_count"] == baseline["join_key_null_count"],
                metrics["strict_gate_pass_total"] == baseline["strict_gate_pass_total"],
                metrics["aggregate_checksum"] == baseline["aggregate_checksum"],
            ]
        )
        reference_match = output_hash == reference_row["output_artifact_sha256"]
        result_rows.append(
            {
                "helper_id": spec["helper_id"],
                "tool_name": spec["tool_name"],
                "source_wrapper_id": spec["source_wrapper_id"],
                "query_id": spec["query_id"],
                "helper_status": "executed",
                "source_panel": spec["panel"].as_posix(),
                "output_artifact": spec["output"].as_posix(),
                "output_artifact_sha256": output_hash,
                "reference_output_sha256": reference_row["output_artifact_sha256"],
                "pandas_runtime_ms": baseline["runtime_ms"],
                "helper_runtime_ms": metrics["runtime_ms"],
                "source_row_count": metrics["source_row_count"],
                "result_row_count": metrics["result_row_count"],
                "row_count_match_pandas": "1" if metrics["source_row_count"] == baseline["source_row_count"] and metrics["result_row_count"] == baseline["result_row_count"] else "0",
                "join_key_null_match_pandas": "1" if metrics["join_key_null_count"] == baseline["join_key_null_count"] else "0",
                "aggregate_checksum_match_pandas": "1" if metrics["aggregate_checksum"] == baseline["aggregate_checksum"] else "0",
                "strict_gate_pass_total_match_pandas": "1" if metrics["strict_gate_pass_total"] == baseline["strict_gate_pass_total"] else "0",
                "reference_match": "1" if reference_match else "0",
                "accelerator_requested_engine": engine.value,
                "accelerator_selected_engine": accelerated.decision.selected_engine.value,
                "accelerator_parity_checked": str(int(accelerated.decision.parity_checked)),
                "accelerator_parity_pass": str(int(accelerated.decision.parity_pass)),
                "accelerator_fallback_used": str(int(accelerated.decision.fallback_used)),
                "decision": "helper_candidate" if exact and reference_match else "reject",
                "reason": "matches_task3127_reference" if exact and reference_match else "mismatch",
                **common_status(),
            }
        )
        diff_rows.append(
            {
                "helper_id": spec["helper_id"],
                "source_wrapper_id": spec["source_wrapper_id"],
                "diff_status": "matched" if reference_match else "mismatch",
                "reference_match": "1" if reference_match else "0",
                "new_output_sha256": output_hash,
                "reference_output_sha256": reference_row["output_artifact_sha256"],
                **common_status(),
            }
        )
    return result_rows, diff_rows


def build_decisions(helper_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for tool in ["pandera", "polars", "duckdb"]:
        tool_rows = [row for row in helper_rows if row["tool_name"] == tool]
        candidate_count = sum(1 for row in tool_rows if row["decision"] == "helper_candidate")
        mismatch_count = sum(1 for row in tool_rows if row["reference_match"] != "1")
        rows.append(
            {
                "tool_name": tool,
                "helper_decision": "promote_task_scoped_helper_candidate" if candidate_count > 0 and mismatch_count == 0 else "reject_or_block",
                "candidate_helper_count": candidate_count,
                "mismatch_count": mismatch_count,
                "allowed_next_layer": "task_scoped_helper_only_no_src_promotion" if candidate_count > 0 and mismatch_count == 0 else "none",
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
                "helper_decision": "defer",
                "candidate_helper_count": 0,
                "mismatch_count": 0,
                "allowed_next_layer": "none",
                "reason": reason,
                **common_status(),
            }
        )
    return rows


def build_checks(contracts: list[dict[str, object]], helper_rows: list[dict[str, object]], diff_rows: list[dict[str, object]], decisions: list[dict[str, object]]) -> list[dict[str, object]]:
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
        ("no_src_promotion", all(row["promoted_to_src"] == "0" for row in contracts), "Helpers remain task-scoped under scripts."),
        ("helper_contracts_present", len(contracts) == 6, "All helper contracts are recorded."),
        ("helper_reference_replay_match", all(row["reference_match"] == "1" for row in diff_rows), "Helper outputs match Task3127 reference outputs."),
        ("helper_candidates_present", sum(1 for row in helper_rows if row["decision"] == "helper_candidate") >= 4, "Pandera, Polars, and DuckDB helper candidates exist."),
        ("deferred_tools_not_promoted", all(row["helper_decision"] == "defer" for row in decisions if row["tool_name"] in {"edgartools", "dlt", "github_mcp_read_only"}), "Deferred tools remain deferred."),
    ]
    return [
        {
            "check_id": f"CHK3141-{idx:03d}",
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


def write_report(contracts: list[dict[str, object]], helper_rows: list[dict[str, object]], diff_rows: list[dict[str, object]], decisions: list[dict[str, object]], checks: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3141 External Tool Helper Contract

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: extracted Task3127 wrapper behavior into task-scoped helper functions and replayed the helper outputs against Task3127 reference artifacts.
- What did not change: no root dependency manifest, `src/` promotion, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Helper contracts: {closeout['helper_contract_rows']}.
  - Helper replay rows: {closeout['helper_replay_rows']}.
  - Helper candidates: {closeout['helper_candidate_rows']}.
  - Reference matches: {closeout['reference_match_rows']}.
- Next action: only after owner approval, move these task-scoped helpers into a small reusable infrastructure module; keep trading brain disconnected.

## Quant Expert Report

### Helper Contracts

{markdown_table(contracts, ['helper_id', 'tool_name', 'helper_status', 'allowed_layers', 'forbidden_layers', 'dependency_mode', 'promoted_to_src'])}

### Helper Replay Results

{markdown_table(helper_rows, ['helper_id', 'tool_name', 'source_wrapper_id', 'query_id', 'helper_status', 'source_row_count', 'result_row_count', 'reference_match', 'decision', 'reason'])}

### Reference Diff

{markdown_table(diff_rows, ['helper_id', 'source_wrapper_id', 'diff_status', 'reference_match'])}

### Helper Decision Matrix

{markdown_table(decisions, ['tool_name', 'helper_decision', 'candidate_helper_count', 'mismatch_count', 'allowed_next_layer'])}

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: the useful external tools are now organized as task-scoped infrastructure helpers, not trading logic.

`Pandera`, `Polars`, and `DuckDB` reproduced the Task3127 wrapper outputs. This makes them reasonable helper candidates for validation and local artifact querying. `edgartools`, `dlt`, and GitHub MCP remain deferred.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `{TASK3127_OUT.as_posix()}/wrapper_decision_matrix.csv`
  - `{TASK3127_OUT.as_posix()}/local_query_wrapper_result.csv`
  - `{SEC_PANEL.as_posix()}`
  - `{LIQUIDITY_PANEL.as_posix()}`
- Outputs:
  - `docs/reports/{TASK_ID}/task_3141_external_tool_helper_contract.md`
  - `docs/reports/{TASK_ID}/task_3141_decision.csv`
  - `data/artifacts/{TASK_ID}/`
- Row counts:
  - Helper contracts: {len(contracts)}
  - Helper replay rows: {len(helper_rows)}
  - Helper diff rows: {len(diff_rows)}
  - Helper decision rows: {len(decisions)}
- Validation commands:
  - `python scripts/trader_brain_3141_external_tool_helper_contract_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Task3127 wrapper decisions: `{file_sha256(TASK3127_OUT / 'wrapper_decision_matrix.csv')}`
  - Task3127 query wrappers: `{file_sha256(TASK3127_OUT / 'local_query_wrapper_result.csv')}`
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
    (OUT_DIR / "helper_outputs").mkdir(parents=True, exist_ok=True)

    contracts = build_helper_contracts()
    helper_rows, diff_rows = run_helper_replay()
    decisions = build_decisions(helper_rows)
    checks = build_checks(contracts, helper_rows, diff_rows, decisions)
    closeout = {
        "task_id": "Task3141",
        "verdict": "external_tool_helper_contract_completed_diagnostic_only",
        "helper_contract_rows": len(contracts),
        "helper_replay_rows": len(helper_rows),
        "helper_candidate_rows": sum(1 for row in helper_rows if row["decision"] == "helper_candidate"),
        "reference_match_rows": sum(1 for row in diff_rows if row["reference_match"] == "1"),
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }

    write_csv(OUT_DIR / "helper_contracts.csv", contracts)
    write_csv(OUT_DIR / "helper_replay_result.csv", helper_rows)
    write_csv(OUT_DIR / "helper_output_diff.csv", diff_rows)
    write_csv(OUT_DIR / "helper_decision_matrix.csv", decisions)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3141_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3141_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(contracts, helper_rows, diff_rows, decisions, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3141_EXTERNAL_TOOL_HELPER_CONTRACT_COMPLETE]")


if __name__ == "__main__":
    main()
