from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trader_terminal_catalog import _composite_group_quality, _group_quality, _matrix_quality, _net_pct
from src.infra.accelerators import BackendAccelerationEngine, GroupedAggregationMeasure, grouped_numeric_aggregate_accelerated


TASK_ID = "task_3221_3280_backend_acceleration_program"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
SCRIPT = ROOT / "scripts" / "build_trader_terminal_catalog.py"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "bucket": "A",
                "net_return_from_entry": 0.10,
                "multi_day_market_state_v4": "up",
                "theme_regime_state_v4": "ai",
                "intraday_entry_state_v4": "breakout",
                "continuation_state_v4": "hold",
                "entry_reduce_failure_flag": 0,
                "add_scale_success_flag": 1,
            },
            {
                "bucket": "A",
                "net_return_from_entry": -0.05,
                "multi_day_market_state_v4": "up",
                "theme_regime_state_v4": "ai",
                "intraday_entry_state_v4": "fade",
                "continuation_state_v4": "watch",
                "entry_reduce_failure_flag": 1,
                "add_scale_success_flag": 0,
            },
            {
                "bucket": "B",
                "net_return_from_entry": 12.0,
                "multi_day_market_state_v4": "down",
                "theme_regime_state_v4": "rates",
                "intraday_entry_state_v4": "breakout",
                "continuation_state_v4": "hold",
                "entry_reduce_failure_flag": 0,
                "add_scale_success_flag": 1,
            },
            {
                "bucket": None,
                "net_return_from_entry": None,
                "multi_day_market_state_v4": None,
                "theme_regime_state_v4": "rates",
                "intraday_entry_state_v4": "fade",
                "continuation_state_v4": "watch",
                "entry_reduce_failure_flag": None,
                "add_scale_success_flag": None,
            },
        ]
    )


def baseline_group_quality(frame: pd.DataFrame, group_col: str, pnl_col: str, *, limit: int = 20) -> list[dict[str, Any]]:
    net = _net_pct(frame[pnl_col])
    temp = frame[[group_col]].copy()
    temp["_net_pct"] = net
    temp["_win"] = net > 0
    grouped = (
        temp.dropna(subset=[group_col])
        .groupby(group_col, as_index=False)
        .agg(count=("_net_pct", "count"), avg_net_pct=("_net_pct", "mean"), total_net_pct=("_net_pct", "sum"), win_rate=("_win", "mean"))
        .sort_values("total_net_pct", ascending=False)
        .head(limit)
    )
    grouped["win_rate"] = grouped["win_rate"] * 100.0
    return grouped.rename(columns={group_col: "key"}).to_dict(orient="records")


def baseline_composite(frame: pd.DataFrame, group_cols: list[str], pnl_col: str, *, limit: int = 40) -> list[dict[str, Any]]:
    separator = " \u00d7 "
    temp = frame[group_cols].copy()
    temp["_net_pct"] = _net_pct(frame[pnl_col])
    temp["_win"] = temp["_net_pct"] > 0
    temp["_entry_reduce"] = pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_add_scale"] = pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_key"] = temp[group_cols].astype(str).agg(separator.join, axis=1)
    grouped = (
        temp.groupby("_key", as_index=False)
        .agg(
            count=("_net_pct", "count"),
            avg_net_pct=("_net_pct", "mean"),
            total_net_pct=("_net_pct", "sum"),
            win_rate=("_win", "mean"),
            entry_reduce_rate=("_entry_reduce", "mean"),
            add_scale_rate=("_add_scale", "mean"),
        )
        .sort_values(["total_net_pct", "count"], ascending=[False, False])
        .head(limit)
    )
    for column in ["win_rate", "entry_reduce_rate", "add_scale_rate"]:
        grouped[column] = grouped[column] * 100.0
    grouped = grouped.rename(columns={"_key": "key"})
    grouped["group_columns"] = separator.join(group_cols)
    return grouped.to_dict(orient="records")


def baseline_matrix(frame: pd.DataFrame, pnl_col: str) -> list[dict[str, Any]]:
    separator = " \u00d7 "
    matrix_cols = [
        col
        for col in ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4", "continuation_state_v4"]
        if col in frame.columns
    ]
    temp = frame[matrix_cols].copy()
    temp["_net_pct"] = _net_pct(frame[pnl_col])
    temp["_win"] = temp["_net_pct"] > 0
    temp["_entry_reduce"] = pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_add_scale"] = pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_cell"] = temp[matrix_cols].astype(str).agg(separator.join, axis=1)
    grouped = (
        temp.groupby("_cell", as_index=False)
        .agg(
            count=("_net_pct", "count"),
            avg_net_pct=("_net_pct", "mean"),
            total_net_pct=("_net_pct", "sum"),
            win_rate=("_win", "mean"),
            entry_reduce_rate=("_entry_reduce", "mean"),
            add_scale_rate=("_add_scale", "mean"),
        )
        .sort_values("total_net_pct", ascending=False)
        .head(80)
    )
    for column in ["win_rate", "entry_reduce_rate", "add_scale_rate"]:
        grouped[column] = grouped[column] * 100.0
    return grouped.rename(columns={"_cell": "key"}).to_dict(orient="records")


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append({key: (None if pd.isna(value) else value) for key, value in row.items()})
    return normalized


def accelerated_engine_checks(frame: pd.DataFrame) -> list[dict[str, object]]:
    temp = frame[["bucket"]].copy()
    temp["_net_pct"] = _net_pct(frame["net_return_from_entry"])
    temp["_win"] = temp["_net_pct"] > 0
    temp = temp.dropna(subset=["bucket"])
    measures = [
        GroupedAggregationMeasure("_net_pct", "count", "count_non_null"),
        GroupedAggregationMeasure("_net_pct", "avg_net_pct", "mean"),
        GroupedAggregationMeasure("_net_pct", "total_net_pct", "sum"),
        GroupedAggregationMeasure("_win", "win_rate", "mean"),
    ]
    rows: list[dict[str, object]] = []
    for engine in [BackendAccelerationEngine.POLARS, BackendAccelerationEngine.DUCKDB]:
        result = grouped_numeric_aggregate_accelerated(temp, ["bucket"], measures, engine=engine)
        rows.append(
            {
                "case_id": f"catalog_{engine.value}_parity",
                "selected_engine": result.decision.selected_engine.value,
                "parity_pass": int(result.decision.parity_pass),
                "result_row_count": result.result.metrics.result_row_count,
                "pandas_checksum": result.pandas_baseline.metrics.aggregate_checksum if result.pandas_baseline else "",
                "candidate_checksum": result.result.metrics.aggregate_checksum,
            }
        )
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = fixture()
    text = SCRIPT.read_text(encoding="utf-8")

    group_actual = _normalize_rows(_group_quality(frame, "bucket", "net_return_from_entry"))
    group_expected = _normalize_rows(baseline_group_quality(frame, "bucket", "net_return_from_entry"))
    composite_cols = ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4"]
    composite_actual = _normalize_rows(_composite_group_quality(frame, composite_cols, "net_return_from_entry"))
    composite_expected = _normalize_rows(baseline_composite(frame, composite_cols, "net_return_from_entry"))
    matrix_actual = _normalize_rows(_matrix_quality(frame, "net_return_from_entry"))
    matrix_expected = _normalize_rows(baseline_matrix(frame, "net_return_from_entry"))
    engine_rows = accelerated_engine_checks(frame)

    checks = [
        {"check_name": "catalog_uses_grouped_accelerator", "pass": int("grouped_numeric_aggregate_accelerated" in text)},
        {"check_name": "group_quality_matches_pandas", "pass": int(group_actual == group_expected)},
        {"check_name": "composite_group_quality_matches_pandas", "pass": int(composite_actual == composite_expected)},
        {"check_name": "matrix_quality_matches_pandas", "pass": int(matrix_actual == matrix_expected)},
        {"check_name": "polars_duckdb_catalog_fixture_parity", "pass": int(all(row["parity_pass"] == 1 for row in engine_rows))},
    ]
    rows = [
        {
            "lane": "catalog",
            "authority": "REPORTING_HEALTH",
            "group_quality_rows": len(group_actual),
            "composite_rows": len(composite_actual),
            "matrix_rows": len(matrix_actual),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    write_csv(OUT_DIR / "catalog_acceleration_result.csv", rows)
    write_csv(OUT_DIR / "catalog_engine_parity.csv", engine_rows)
    write_csv(OUT_DIR / "catalog_acceptance_checks.csv", checks)
    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3231_3245_ERROR] {row['check_name']}")
        return 1
    print("[TASK3231_3245_CATALOG_ACCELERATION_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
