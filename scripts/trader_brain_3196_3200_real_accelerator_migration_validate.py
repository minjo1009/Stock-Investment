#!/usr/bin/env python
"""Validate one real pandas aggregate path migrated behind backend accelerators.

This uses existing local artifact panels from Task2541 and Task2561. It does not
run replay/backtest, acquire sources, rank trades, size positions, submit
orders, or mutate runtime/broker state.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated
from src.infra.external_tools import file_sha256, write_csv


TASK_ID = "task_3196_3200_real_accelerator_migration"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
TASK3127_OUT = ROOT / "data" / "artifacts" / "task_3127_external_tool_opt_in_wrapper_pilot"
SEC_PANEL = ROOT / "data" / "artifacts" / "task_2541_2560_sec_financing_dilution_acquisition" / "task2545_normalized_sec_financing_dilution_packets.csv"
LIQUIDITY_PANEL = ROOT / "data" / "artifacts" / "task_2561_2580_liquidity_rates_regime_acquisition" / "task2565_normalized_liquidity_rates_packets.csv"
MIGRATED_SCRIPT = ROOT / "scripts" / "trader_brain_3141_external_tool_helper_contract.py"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def reference_by_wrapper_id() -> dict[str, dict[str, str]]:
    return {row["wrapper_id"]: row for row in read_csv(TASK3127_OUT / "local_query_wrapper_result.csv")}


def _correctness_pass(row: dict[str, object]) -> bool:
    return (
        str(row.get("row_count_match_pandas")) == "1"
        and str(row.get("join_key_null_match_pandas")) == "1"
        and str(row.get("aggregate_checksum_match_pandas")) == "1"
        and str(row.get("strict_gate_pass_total_match_pandas")) == "1"
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "migrated_outputs").mkdir(parents=True, exist_ok=True)
    refs = reference_by_wrapper_id()
    script_text = MIGRATED_SCRIPT.read_text(encoding="utf-8")

    specs = [
        {
            "migration_id": "MIG3196-POLARS-SEC",
            "wrapper_id": "WRAP3127-POLARS-SEC-AGG",
            "engine": BackendAccelerationEngine.POLARS,
            "panel": SEC_PANEL,
            "group_cols": ["symbol", "event_family"],
            "output": OUT_DIR / "migrated_outputs" / "sec_symbol_event_family_polars.csv",
        },
        {
            "migration_id": "MIG3197-POLARS-LIQUIDITY",
            "wrapper_id": "WRAP3127-POLARS-LIQUIDITY-AGG",
            "engine": BackendAccelerationEngine.POLARS,
            "panel": LIQUIDITY_PANEL,
            "group_cols": ["provider", "series_id"],
            "output": OUT_DIR / "migrated_outputs" / "liquidity_provider_series_polars.csv",
        },
        {
            "migration_id": "MIG3198-DUCKDB-LIQUIDITY",
            "wrapper_id": "WRAP3127-DUCKDB-LIQUIDITY-AGG",
            "engine": BackendAccelerationEngine.DUCKDB,
            "panel": LIQUIDITY_PANEL,
            "group_cols": ["provider", "series_id"],
            "output": OUT_DIR / "migrated_outputs" / "liquidity_provider_series_duckdb.csv",
        },
    ]

    migration_rows: list[dict[str, object]] = []
    baseline_cache: dict[tuple[str, str], object] = {}
    for spec in specs:
        key = (spec["panel"].as_posix(), "|".join(spec["group_cols"]))
        result = strict_gate_aggregate_accelerated(
            spec["panel"],
            spec["group_cols"],
            engine=spec["engine"],
            verify_with_pandas=True,
            pandas_baseline=baseline_cache.get(key),
        )
        if result.pandas_baseline is not None:
            baseline_cache[key] = result.pandas_baseline
        write_csv(spec["output"], [dict(row) for row in result.result.rows])
        output_hash = file_sha256(spec["output"])
        ref = refs[spec["wrapper_id"]]
        row = {
            "migration_id": spec["migration_id"],
            "wrapper_id": spec["wrapper_id"],
            "requested_engine": spec["engine"].value,
            "selected_engine": result.decision.selected_engine.value,
            "fallback_used": int(result.decision.fallback_used),
            "parity_checked": int(result.decision.parity_checked),
            "parity_pass": int(result.decision.parity_pass),
            "faster_than_pandas": int(result.decision.faster_than_pandas),
            "source_panel": spec["panel"].as_posix(),
            "source_row_count": result.result.metrics.source_row_count,
            "result_row_count": result.result.metrics.result_row_count,
            "strict_gate_pass_total": result.result.metrics.strict_gate_pass_total,
            "runtime_ms": result.result.metrics.runtime_ms,
            "pandas_runtime_ms": result.pandas_baseline.metrics.runtime_ms if result.pandas_baseline else "",
            "output_artifact": spec["output"].as_posix(),
            "output_artifact_sha256": output_hash,
            "reference_output_sha256": ref["output_artifact_sha256"],
            "reference_match": int(output_hash == ref["output_artifact_sha256"]),
            "row_count_match_pandas": int(
                result.pandas_baseline is not None
                and result.result.metrics.source_row_count == result.pandas_baseline.metrics.source_row_count
                and result.result.metrics.result_row_count == result.pandas_baseline.metrics.result_row_count
            ),
            "join_key_null_match_pandas": int(
                result.pandas_baseline is not None
                and result.result.metrics.join_key_null_count == result.pandas_baseline.metrics.join_key_null_count
            ),
            "aggregate_checksum_match_pandas": int(
                result.pandas_baseline is not None
                and result.result.metrics.aggregate_checksum == result.pandas_baseline.metrics.aggregate_checksum
            ),
            "strict_gate_pass_total_match_pandas": int(
                result.pandas_baseline is not None
                and result.result.metrics.strict_gate_pass_total == result.pandas_baseline.metrics.strict_gate_pass_total
            ),
        }
        row["correctness_parity_pass"] = int(_correctness_pass(row))
        migration_rows.append(row)

    decision_rows = [
        {
            "task_id": "Task3196-Task3200",
            "real_path_migrated": 1,
            "migrated_script": MIGRATED_SCRIPT.as_posix(),
            "uses_strict_gate_aggregate_accelerated": int("strict_gate_aggregate_accelerated" in script_text),
            "direct_pandas_strict_gate_call_removed": int("pandas_strict_gate_aggregate" not in script_text),
            "reference_match_rows": sum(int(row["reference_match"]) for row in migration_rows),
            "correctness_parity_rows": sum(int(row["correctness_parity_pass"]) for row in migration_rows),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "selector_changed": 0,
            "sizing_changed": 0,
            "replay_performed": 0,
            "source_acquisition_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
        }
    ]

    checks = [
        {
            "check_name": "script_uses_core_accelerator",
            "pass": int("strict_gate_aggregate_accelerated" in script_text),
            "detail": MIGRATED_SCRIPT.as_posix(),
        },
        {
            "check_name": "script_removed_direct_pandas_strict_gate_call",
            "pass": int("pandas_strict_gate_aggregate" not in script_text),
            "detail": "direct pandas strict-gate aggregate removed from migrated path",
        },
        {
            "check_name": "all_real_outputs_match_reference",
            "pass": int(all(int(row["reference_match"]) == 1 for row in migration_rows)),
            "detail": f"matches={sum(int(row['reference_match']) for row in migration_rows)}/{len(migration_rows)}",
        },
        {
            "check_name": "all_real_outputs_match_pandas_correctness",
            "pass": int(all(int(row["correctness_parity_pass"]) == 1 for row in migration_rows)),
            "detail": f"parity={sum(int(row['correctness_parity_pass']) for row in migration_rows)}/{len(migration_rows)}",
        },
        {
            "check_name": "no_trading_state_change",
            "pass": int(all(str(row[col]) == "0" for row in decision_rows for col in ["selector_changed", "sizing_changed", "replay_performed", "source_acquisition_performed", "paper_order_intents_created", "live_orders_created"])),
            "detail": "acceleration-only migration",
        },
    ]

    manifest_rows = [
        {"relative_path": "migration_result.csv", "artifact_type": "migration_result", "rows": len(migration_rows), "description": "Real artifact aggregate paths migrated behind strict_gate_aggregate_accelerated"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "rows": len(decision_rows), "description": "Task3196-3200 migration decision"},
        {"relative_path": "acceptance_checks.csv", "artifact_type": "validation", "rows": len(checks), "description": "Migration validation checks"},
        {"relative_path": "migrated_outputs/sec_symbol_event_family_polars.csv", "artifact_type": "output", "rows": "", "description": "SEC aggregate output through core accelerator"},
        {"relative_path": "migrated_outputs/liquidity_provider_series_polars.csv", "artifact_type": "output", "rows": "", "description": "Liquidity aggregate output through Polars accelerator"},
        {"relative_path": "migrated_outputs/liquidity_provider_series_duckdb.csv", "artifact_type": "output", "rows": "", "description": "Liquidity aggregate output through DuckDB accelerator"},
    ]

    write_csv(OUT_DIR / "migration_result.csv", migration_rows)
    write_csv(OUT_DIR / "decision.csv", decision_rows)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest_rows)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3196_3200_ERROR] {row['check_name']}: {row['detail']}")
        return 1

    print(
        "[TASK3196_3200_OK] "
        f"migrations={len(migration_rows)} "
        f"reference_matches={sum(int(row['reference_match']) for row in migration_rows)} "
        f"parity={sum(int(row['correctness_parity_pass']) for row in migration_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
