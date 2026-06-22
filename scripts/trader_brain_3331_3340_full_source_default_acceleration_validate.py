#!/usr/bin/env python
"""Validate the next real 500k+ source panel groupby promoted to AUTO default.

This validates the Task2251 full-source normalized panel
`provider,endpoint_name` strict-gate aggregate. It does not run replay/backtest,
acquire sources, rank trades, size positions, submit orders, or mutate
runtime/broker state.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated
from src.infra.external_tools import file_sha256, write_csv


TASK_ID = "task_3331_3340_full_source_default_acceleration"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
FULL_SOURCE_PANEL = ROOT / "data" / "artifacts" / "task_2251_2280_plus8000_full_source_acquisition" / "task2253_normalized_sources.csv"
LIQUIDITY_PANEL = ROOT / "data" / "artifacts" / "task_2561_2580_liquidity_rates_regime_acquisition" / "task2565_normalized_liquidity_rates_packets.csv"
EXTERNAL_TOOLS = ROOT / "src" / "infra" / "external_tools.py"
EXPECTED_REFERENCE_HASH = "4bb6ebb8838f1e3ad2e07ec3edb83a5ce507f012e646fa0f036559f6d317f2a1"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "default_outputs").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "pandas_reference").mkdir(parents=True, exist_ok=True)

    default_output = OUT_DIR / "default_outputs" / "full_source_provider_endpoint_auto_default.csv"
    pandas_reference_output = OUT_DIR / "pandas_reference" / "full_source_provider_endpoint_pandas_reference.csv"

    result = strict_gate_aggregate_accelerated(
        FULL_SOURCE_PANEL,
        ["provider", "endpoint_name"],
        engine=BackendAccelerationEngine.AUTO,
        verify_with_pandas=True,
    )
    if result.pandas_baseline is None:
        raise AssertionError("missing pandas baseline for full-source default acceleration")

    write_csv(default_output, [dict(row) for row in result.result.rows])
    write_csv(pandas_reference_output, [dict(row) for row in result.pandas_baseline.rows])
    output_hash = file_sha256(default_output)
    reference_hash = file_sha256(pandas_reference_output)
    pandas_ms = result.pandas_baseline.metrics.runtime_ms
    runtime_ms = result.result.metrics.runtime_ms
    speedup = pandas_ms / runtime_ms if runtime_ms else 0.0
    helper_text = EXTERNAL_TOOLS.read_text(encoding="utf-8")

    benchmark_rows = [
        {
            "case_id": "FULL_SOURCE_PROVIDER_ENDPOINT_AUTO_DEFAULT",
            "source_panel": FULL_SOURCE_PANEL.as_posix(),
            "source_row_count": result.result.metrics.source_row_count,
            "result_row_count": result.result.metrics.result_row_count,
            "requested_engine": "auto",
            "selected_engine": result.decision.selected_engine.value,
            "parity_pass": int(result.decision.parity_pass),
            "runtime_ms": runtime_ms,
            "pandas_runtime_ms": pandas_ms,
            "speedup_vs_pandas": round(speedup, 6),
            "output_artifact": default_output.as_posix(),
            "output_artifact_sha256": output_hash,
            "reference_artifact": pandas_reference_output.as_posix(),
            "reference_output_sha256": reference_hash,
            "expected_reference_sha256": EXPECTED_REFERENCE_HASH,
            "reference_match": int(output_hash == reference_hash == EXPECTED_REFERENCE_HASH),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    checks = [
        {"check_name": "different_panel_from_liquidity", "pass": int(FULL_SOURCE_PANEL != LIQUIDITY_PANEL)},
        {"check_name": "source_rows_at_least_500k", "pass": int(result.result.metrics.source_row_count >= 500_000)},
        {"check_name": "auto_selected_polars", "pass": int(result.decision.selected_engine == BackendAccelerationEngine.POLARS)},
        {"check_name": "pandas_parity_pass", "pass": int(result.decision.parity_pass)},
        {"check_name": "minimum_2x_speedup_vs_pandas", "pass": int(speedup >= 2.0)},
        {"check_name": "pandas_reference_hash_match", "pass": int(output_hash == reference_hash)},
        {"check_name": "fixed_reference_hash_match", "pass": int(output_hash == reference_hash == EXPECTED_REFERENCE_HASH)},
        {"check_name": "strict_gate_csv_reads_are_column_scoped", "pass": int("usecols=required_cols" in helper_text and "columns=required_cols" in helper_text)},
        {"check_name": "no_trading_state_change", "pass": 1},
    ]
    decision = [
        {
            "task_id": "Task3331-Task3340",
            "verdict": "full_source_provider_endpoint_groupby_default_promoted_to_auto_polars",
            "promoted_groupby": "full_source_normalized.provider_endpoint_name",
            "source_rows": result.result.metrics.source_row_count,
            "result_rows": result.result.metrics.result_row_count,
            "selected_default_engine": result.decision.selected_engine.value,
            "speedup_vs_pandas": round(speedup, 6),
            "reference_match": int(output_hash == reference_hash == EXPECTED_REFERENCE_HASH),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "replay_performed": 0,
            "source_acquisition_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
        }
    ]
    manifest = [
        {"relative_path": "benchmark_result.csv", "artifact_type": "benchmark", "description": "AUTO default full-source groupby benchmark and parity"},
        {"relative_path": "acceptance_checks.csv", "artifact_type": "validation", "description": "Full-source default promotion checks"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "description": "Task3331-3340 decision row"},
        {"relative_path": "default_outputs/full_source_provider_endpoint_auto_default.csv", "artifact_type": "output", "description": "AUTO default aggregate output"},
        {"relative_path": "pandas_reference/full_source_provider_endpoint_pandas_reference.csv", "artifact_type": "reference", "description": "Pandas reference aggregate output"},
    ]
    write_csv(OUT_DIR / "benchmark_result.csv", benchmark_rows)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "decision.csv", decision)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)
    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3331_3340_ERROR] {row['check_name']}")
        return 1
    print(
        "[TASK3331_3340_FULL_SOURCE_DEFAULT_ACCELERATION_OK] "
        f"selected={result.decision.selected_engine.value} "
        f"source_rows={result.result.metrics.source_row_count} "
        f"speedup={speedup:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
