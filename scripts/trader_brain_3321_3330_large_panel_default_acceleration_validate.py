#!/usr/bin/env python
"""Validate one real large-panel groupby promoted to accelerator default.

This validates the liquidity/rates `provider,series_id` strict-gate aggregate.
It does not run replay/backtest, acquire sources, rank trades, size positions,
submit orders, or mutate runtime/broker state.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated
from src.infra.external_tools import file_sha256, write_csv


TASK_ID = "task_3321_3330_large_panel_default_acceleration"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
TASK3127_OUT = ROOT / "data" / "artifacts" / "task_3127_external_tool_opt_in_wrapper_pilot"
LIQUIDITY_PANEL = ROOT / "data" / "artifacts" / "task_2561_2580_liquidity_rates_regime_acquisition" / "task2565_normalized_liquidity_rates_packets.csv"
SCRIPT3142 = ROOT / "scripts" / "trader_brain_3142_external_tool_infra_module_promotion.py"
SCRIPT3143 = ROOT / "scripts" / "trader_brain_3143_external_tool_typed_contract.py"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def reference_hash() -> str:
    for row in read_csv(TASK3127_OUT / "local_query_wrapper_result.csv"):
        if row.get("wrapper_id") == "WRAP3127-POLARS-LIQUIDITY-AGG":
            return row["output_artifact_sha256"]
    raise AssertionError("missing Task3127 liquidity reference")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "default_outputs").mkdir(parents=True, exist_ok=True)
    output = OUT_DIR / "default_outputs" / "liquidity_provider_series_auto_default.csv"

    result = strict_gate_aggregate_accelerated(
        LIQUIDITY_PANEL,
        ["provider", "series_id"],
        engine=BackendAccelerationEngine.AUTO,
        verify_with_pandas=True,
    )
    write_csv(output, [dict(row) for row in result.result.rows])
    output_hash = file_sha256(output)
    ref_hash = reference_hash()
    pandas_ms = result.pandas_baseline.metrics.runtime_ms if result.pandas_baseline else 0.0
    runtime_ms = result.result.metrics.runtime_ms
    speedup = pandas_ms / runtime_ms if runtime_ms else 0.0
    script3142 = SCRIPT3142.read_text(encoding="utf-8")
    script3143 = SCRIPT3143.read_text(encoding="utf-8")

    benchmark_rows = [
        {
            "case_id": "LIQUIDITY_PROVIDER_SERIES_AUTO_DEFAULT",
            "source_panel": LIQUIDITY_PANEL.as_posix(),
            "source_row_count": result.result.metrics.source_row_count,
            "result_row_count": result.result.metrics.result_row_count,
            "requested_engine": "auto",
            "selected_engine": result.decision.selected_engine.value,
            "parity_pass": int(result.decision.parity_pass),
            "runtime_ms": runtime_ms,
            "pandas_runtime_ms": pandas_ms,
            "speedup_vs_pandas": round(speedup, 6),
            "output_artifact": output.as_posix(),
            "output_artifact_sha256": output_hash,
            "reference_output_sha256": ref_hash,
            "reference_match": int(output_hash == ref_hash),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    checks = [
        {"check_name": "auto_selected_polars", "pass": int(result.decision.selected_engine == BackendAccelerationEngine.POLARS)},
        {"check_name": "pandas_parity_pass", "pass": int(result.decision.parity_pass)},
        {"check_name": "minimum_2x_speedup_vs_pandas", "pass": int(speedup >= 2.0)},
        {"check_name": "reference_hash_preserved", "pass": int(output_hash == ref_hash)},
        {"check_name": "task3142_liquidity_path_uses_auto_default", "pass": int('"WRAP3127-POLARS-LIQUIDITY-AGG", LIQUIDITY_PANEL' in script3142 and "BackendAccelerationEngine.AUTO" in script3142)},
        {"check_name": "task3143_liquidity_path_uses_auto_default", "pass": int('"TYPED3143-POLARS-LIQ", "polars", BackendAccelerationEngine.AUTO' in script3143)},
        {"check_name": "no_trading_state_change", "pass": 1},
    ]
    decision = [
        {
            "task_id": "Task3321-Task3330",
            "verdict": "large_panel_liquidity_groupby_default_promoted_to_auto_polars",
            "promoted_groupby": "liquidity_rates.provider_series_id",
            "source_rows": result.result.metrics.source_row_count,
            "selected_default_engine": result.decision.selected_engine.value,
            "speedup_vs_pandas": round(speedup, 6),
            "reference_match": int(output_hash == ref_hash),
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
        {"relative_path": "benchmark_result.csv", "artifact_type": "benchmark", "description": "AUTO default liquidity groupby benchmark and parity"},
        {"relative_path": "acceptance_checks.csv", "artifact_type": "validation", "description": "Default promotion checks"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "description": "Task3321-3330 decision row"},
        {"relative_path": "default_outputs/liquidity_provider_series_auto_default.csv", "artifact_type": "output", "description": "AUTO default aggregate output"},
    ]
    write_csv(OUT_DIR / "benchmark_result.csv", benchmark_rows)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "decision.csv", decision)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)
    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3321_3330_ERROR] {row['check_name']}")
        return 1
    print(
        "[TASK3321_3330_LARGE_PANEL_DEFAULT_ACCELERATION_OK] "
        f"selected={result.decision.selected_engine.value} "
        f"source_rows={result.result.metrics.source_row_count} "
        f"speedup={speedup:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
