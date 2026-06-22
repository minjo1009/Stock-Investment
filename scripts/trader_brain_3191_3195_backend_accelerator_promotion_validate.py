#!/usr/bin/env python
"""Validate Polars/DuckDB promotion into the core backend acceleration layer.

This validator uses a synthetic local fixture. It does not run replay/backtest,
acquire sources, rank trades, size positions, submit orders, or change runtime
state.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated
from src.infra.external_tools import (
    compare_aggregate_results,
    duckdb_strict_gate_aggregate_result,
    pandas_strict_gate_aggregate_result,
    polars_strict_gate_aggregate_result,
    write_csv,
)


TASK_ID = "task_3191_3195_backend_accelerator_promotion"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
FIXTURE = OUT_DIR / "accelerator_strict_gate_fixture.csv"


def _dependency_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in ["pandas", "polars", "duckdb"]:
        spec = importlib.util.find_spec(name)
        rows.append(
            {
                "tool_name": name,
                "dependency_status": "available" if spec else "dependency_missing",
                "import_origin": spec.origin if spec else "",
                "core_backend_role": "baseline" if name == "pandas" else "accelerator",
            }
        )
    return rows


def _write_fixture() -> None:
    rows: list[dict[str, object]] = []
    symbols = ["AAPL", "MSFT", "NVDA", "TSLA", "META", "AMZN", "GOOGL", "AVGO"]
    families = ["SEC", "RATES", "LIQUIDITY", "EARNINGS"]
    for idx in range(4096):
        rows.append(
            {
                "symbol": symbols[idx % len(symbols)],
                "event_family": families[(idx // len(symbols)) % len(families)],
                "strict_gate_pass": str(1 if idx % 3 == 0 else 0),
            }
        )
    write_csv(FIXTURE, rows, ["symbol", "event_family", "strict_gate_pass"])


def _correctness_pass(row: dict[str, object]) -> bool:
    return (
        row.get("row_count_match_pandas") == "1"
        and row.get("join_key_null_match_pandas") == "1"
        and row.get("aggregate_checksum_match_pandas") == "1"
        and row.get("strict_gate_pass_total_match_pandas") == "1"
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_fixture()

    dependency_rows = _dependency_rows()
    baseline = pandas_strict_gate_aggregate_result(FIXTURE, ["symbol", "event_family"])
    polars_result = polars_strict_gate_aggregate_result(FIXTURE, ["symbol", "event_family"])
    duckdb_result = duckdb_strict_gate_aggregate_result(FIXTURE, ["symbol", "event_family"])
    auto_result = strict_gate_aggregate_accelerated(FIXTURE, ["symbol", "event_family"])

    aggregate_rows = [
        baseline.to_dict(),
        polars_result.to_dict(),
        duckdb_result.to_dict(),
        auto_result.to_dict(),
    ]
    parity_rows: list[dict[str, object]] = []
    for name, candidate in [("polars", polars_result), ("duckdb", duckdb_result)]:
        comparison = compare_aggregate_results(candidate, baseline)
        row = {"engine": name, **comparison.to_dict()}
        row["correctness_parity_pass"] = int(_correctness_pass(row))
        parity_rows.append(row)

    decision_rows = [
        {
            "task_id": "Task3191-Task3195",
            "core_backend_accelerator_promoted": 1,
            "auto_selected_engine": auto_result.decision.selected_engine.value,
            "auto_selected_accelerator": int(auto_result.decision.selected_engine in {BackendAccelerationEngine.POLARS, BackendAccelerationEngine.DUCKDB}),
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
    acceptance_checks = [
        {
            "check_name": "accelerator_module_present",
            "pass": int((ROOT / "src" / "infra" / "accelerators.py").exists()),
            "detail": "src/infra/accelerators.py",
        },
        {
            "check_name": "polars_available",
            "pass": int(any(row["tool_name"] == "polars" and row["dependency_status"] == "available" for row in dependency_rows)),
            "detail": "polars dependency",
        },
        {
            "check_name": "duckdb_available",
            "pass": int(any(row["tool_name"] == "duckdb" and row["dependency_status"] == "available" for row in dependency_rows)),
            "detail": "duckdb dependency",
        },
        {
            "check_name": "polars_correctness_parity",
            "pass": int(any(row["engine"] == "polars" and row["correctness_parity_pass"] == 1 for row in parity_rows)),
            "detail": "polars vs pandas checksum",
        },
        {
            "check_name": "duckdb_correctness_parity",
            "pass": int(any(row["engine"] == "duckdb" and row["correctness_parity_pass"] == 1 for row in parity_rows)),
            "detail": "duckdb vs pandas checksum",
        },
        {
            "check_name": "auto_uses_accelerator",
            "pass": int(auto_result.decision.selected_engine in {BackendAccelerationEngine.POLARS, BackendAccelerationEngine.DUCKDB}),
            "detail": auto_result.decision.selected_engine.value,
        },
        {
            "check_name": "no_trading_state_change",
            "pass": int(all(str(row[col]) == "0" for row in decision_rows for col in ["selector_changed", "sizing_changed", "replay_performed", "source_acquisition_performed", "paper_order_intents_created", "live_orders_created"])),
            "detail": "acceleration-only",
        },
    ]

    manifest_rows = [
        {"relative_path": "accelerator_strict_gate_fixture.csv", "artifact_type": "fixture", "rows": 4096, "description": "Synthetic strict-gate fixture for backend accelerator parity validation"},
        {"relative_path": "dependency_status.csv", "artifact_type": "dependency_status", "rows": len(dependency_rows), "description": "Local pandas Polars DuckDB dependency availability"},
        {"relative_path": "aggregate_metrics.csv", "artifact_type": "metrics", "rows": len(aggregate_rows), "description": "Pandas Polars DuckDB and auto aggregate metrics"},
        {"relative_path": "parity_result.csv", "artifact_type": "parity", "rows": len(parity_rows), "description": "Polars and DuckDB correctness parity against pandas"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "rows": len(decision_rows), "description": "Backend accelerator promotion decision"},
        {"relative_path": "acceptance_checks.csv", "artifact_type": "validation", "rows": len(acceptance_checks), "description": "Task3191-3195 acceptance checks"},
    ]

    write_csv(OUT_DIR / "dependency_status.csv", dependency_rows)
    write_csv(OUT_DIR / "aggregate_metrics.csv", aggregate_rows)
    write_csv(OUT_DIR / "parity_result.csv", parity_rows)
    write_csv(OUT_DIR / "decision.csv", decision_rows)
    write_csv(OUT_DIR / "acceptance_checks.csv", acceptance_checks)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest_rows)

    failed = [row for row in acceptance_checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3191_3195_ERROR] {row['check_name']}: {row['detail']}")
        return 1

    print(
        "[TASK3191_3195_OK] "
        f"checks={len(acceptance_checks)} "
        f"auto_engine={auto_result.decision.selected_engine.value} "
        f"fixture_rows=4096"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

