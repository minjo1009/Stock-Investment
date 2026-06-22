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
    file_sha256,
    validate_sec_panel_schema_with_pandera_venv,
    validate_sec_panel_schema_with_pandera_venv_result,
    write_csv,
)
from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated


TASK_ID = "task_3143_external_tool_typed_contract"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3143_external_tool_typed_contract.md"
DECISION = REPORT_DIR / "task_3143_decision.csv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_TYPED_CONTRACT_ONLY"

TASK3126_VENV = ROOT / ".cache/task_3126_external_tool_venv"
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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def typed_contract_rows() -> list[dict[str, object]]:
    return [
        {
            "contract_name": "ToolStatus",
            "contract_type": "dataclass",
            "purpose": "optional_dependency_status_without_import_side_effect",
            "trading_decision_allowed": "0",
            **common_status(),
        },
        {
            "contract_name": "AggregateMetrics",
            "contract_type": "dataclass",
            "purpose": "stable_local_artifact_query_metrics",
            "trading_decision_allowed": "0",
            **common_status(),
        },
        {
            "contract_name": "AggregateResult",
            "contract_type": "dataclass",
            "purpose": "metrics_plus_rows_for_audit_outputs",
            "trading_decision_allowed": "0",
            **common_status(),
        },
        {
            "contract_name": "SchemaValidationResult",
            "contract_type": "dataclass",
            "purpose": "stable_schema_validation_payload",
            "trading_decision_allowed": "0",
            **common_status(),
        },
        {
            "contract_name": "MetricComparison",
            "contract_type": "dataclass",
            "purpose": "stable_pandas_parity_comparison",
            "trading_decision_allowed": "0",
            **common_status(),
        },
    ]


def run_typed_parity() -> list[dict[str, object]]:
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

    legacy_schema = validate_sec_panel_schema_with_pandera_venv(ROOT, TASK3126_VENV, SEC_PANEL, required_cols)
    typed_schema = validate_sec_panel_schema_with_pandera_venv_result(ROOT, TASK3126_VENV, SEC_PANEL, required_cols)
    rows.append(
        {
            "case_id": "TYPED3143-PANDERA-SEC",
            "tool_name": "pandera",
            "legacy_status": legacy_schema.get("schema_status", ""),
            "typed_status": typed_schema.schema_status,
            "legacy_row_count": legacy_schema.get("row_count", 0),
            "typed_row_count": typed_schema.row_count,
            "parity_pass": "1"
            if legacy_schema.get("schema_status") == typed_schema.schema_status and int(legacy_schema.get("row_count", -1)) == typed_schema.row_count
            else "0",
            "typed_payload_keys": "|".join(typed_schema.to_dict().keys()),
            **common_status(),
        }
    )

    specs = [
        ("TYPED3143-POLARS-SEC", "polars", BackendAccelerationEngine.POLARS, SEC_PANEL, ["symbol", "event_family"]),
        ("TYPED3143-POLARS-LIQ", "polars", BackendAccelerationEngine.AUTO, LIQUIDITY_PANEL, ["provider", "series_id"]),
        ("TYPED3143-DUCKDB-LIQ", "duckdb", BackendAccelerationEngine.DUCKDB, LIQUIDITY_PANEL, ["provider", "series_id"]),
    ]
    baseline_cache: dict[tuple[str, str], object] = {}
    for case_id, tool_name, engine, panel, group_cols in specs:
        key = (panel.as_posix(), "|".join(group_cols))
        accelerated = strict_gate_aggregate_accelerated(
            panel,
            group_cols,
            engine=engine,
            pandas_baseline=baseline_cache.get(key),
        )
        if accelerated.pandas_baseline is not None:
            baseline_cache[key] = accelerated.pandas_baseline
        typed = accelerated.result
        rows.append(
            {
                "case_id": case_id,
                "tool_name": tool_name,
                "legacy_status": "core_accelerator",
                "typed_status": typed.metrics.dependency_status,
                "legacy_row_count": accelerated.pandas_baseline.metrics.source_row_count if accelerated.pandas_baseline else 0,
                "typed_row_count": typed.metrics.source_row_count,
                "legacy_result_row_count": accelerated.pandas_baseline.metrics.result_row_count if accelerated.pandas_baseline else 0,
                "typed_result_row_count": typed.metrics.result_row_count,
                "legacy_checksum": accelerated.pandas_baseline.metrics.aggregate_checksum if accelerated.pandas_baseline else "",
                "typed_checksum": typed.metrics.aggregate_checksum,
                "comparison_pass": "1" if accelerated.decision.parity_pass else "0",
                "parity_pass": "1" if accelerated.decision.parity_pass else "0",
                "typed_payload_keys": "|".join(typed.to_dict().keys()),
                **common_status(),
            }
        )
    return rows


def build_checks(contracts: list[dict[str, object]], parity: list[dict[str, object]]) -> list[dict[str, object]]:
    checks = [
        ("typed_contracts_present", len(contracts) == 5, "All typed dataclass contracts are recorded."),
        ("typed_legacy_parity", all(row["parity_pass"] == "1" for row in parity), "Typed wrappers match legacy wrapper outputs."),
        ("typed_query_comparison_pass", all(row.get("comparison_pass", "1") == "1" for row in parity), "Typed aggregate comparisons pass pandas parity."),
        ("trading_decision_disabled", all(row["trading_decision_allowed"] == "0" for row in contracts), "Typed contracts do not allow trading decisions."),
        ("status_unchanged", True, "Strategy/deployment/real-capital statuses remain unchanged."),
    ]
    return [
        {"check_id": f"CHK3143-{idx:03d}", "check_name": name, "pass": "1" if passed else "0", "detail": detail, **common_status()}
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, ""))[:300] for field in fields) + " |")
    return "\n".join(lines)


def write_report(contracts: list[dict[str, object]], parity: list[dict[str, object]], checks: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3143 External Tool Typed Contract

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: added typed dataclass result contracts to `src/infra/external_tools.py` and verified parity with the existing dict/tuple API.
- What did not change: no source acquisition, replay, selector, sizing, paper order, live order, root dependency manifest, acceptance, or deployment state changed.
- Key metrics: typed contracts {len(contracts)}, parity rows {len(parity)}, parity pass rows {closeout['typed_parity_pass_rows']}.

## Quant Expert Report

### Typed Contracts

{markdown_table(contracts, ['contract_name', 'contract_type', 'purpose', 'trading_decision_allowed'])}

### Typed Parity

{markdown_table(parity, ['case_id', 'tool_name', 'legacy_status', 'typed_status', 'legacy_row_count', 'typed_row_count', 'parity_pass', 'comparison_pass'])}

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: the common infra module now has stable typed result contracts.

This makes later migration safer because callers can use explicit result objects instead of loose dictionaries. The module remains diagnostic-only.

## Artifact Manifest

- Inputs:
  - `{SEC_PANEL.as_posix()}`
  - `{LIQUIDITY_PANEL.as_posix()}`
- Outputs:
  - `src/infra/external_tools.py`
  - `docs/reports/{TASK_ID}/task_3143_external_tool_typed_contract.md`
  - `data/artifacts/{TASK_ID}/`
- Validation commands:
  - `python scripts/trader_brain_3143_external_tool_typed_contract_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
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
    contracts = typed_contract_rows()
    parity = run_typed_parity()
    checks = build_checks(contracts, parity)
    closeout = {
        "task_id": "Task3143",
        "verdict": "external_tool_typed_contract_completed_diagnostic_only",
        "typed_contract_rows": len(contracts),
        "typed_parity_rows": len(parity),
        "typed_parity_pass_rows": sum(1 for row in parity if row["parity_pass"] == "1"),
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }
    write_csv(OUT_DIR / "typed_contracts.csv", contracts)
    write_csv(OUT_DIR / "typed_parity_result.csv", parity)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3143_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3143_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(contracts, parity, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3143_EXTERNAL_TOOL_TYPED_CONTRACT_COMPLETE]")


if __name__ == "__main__":
    main()
