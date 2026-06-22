from __future__ import annotations

import pandas as pd

from src.infra.accelerators import GroupedAggregationMeasure, grouped_numeric_aggregate_accelerated


def lifecycle_quality(frame: pd.DataFrame) -> dict[str, float | int]:
    if frame.empty:
        return {
            "lifecycle_count": 0,
            "avg_net_return_pct": 0.0,
            "win_rate": 0.0,
            "add_scale_success_rate": 0.0,
            "entry_reduce_failure_rate": 0.0,
            "false_positive_rate": 0.0,
        }
    return {
        "lifecycle_count": int(len(frame)),
        "avg_net_return_pct": float(frame["net_return_from_entry"].mean() * 100.0),
        "win_rate": float(frame["win_flag"].mean()),
        "add_scale_success_rate": float(frame["add_scale_success_flag"].mean()),
        "entry_reduce_failure_rate": float(frame["entry_reduce_failure_flag"].mean()),
        "false_positive_rate": float(frame["false_positive_flag"].mean()) if "false_positive_flag" in frame.columns else 0.0,
    }


def grouped_lifecycle_quality(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    if not keys:
        return pd.DataFrame([lifecycle_quality(frame)])
    return grouped_numeric_aggregate_accelerated(
        frame,
        keys,
        [
            GroupedAggregationMeasure("lifecycle_id", "lifecycle_count", "count_non_null"),
            GroupedAggregationMeasure("net_return_from_entry", "avg_net_return_pct", "mean", scale=100.0),
            GroupedAggregationMeasure("win_flag", "win_rate", "mean"),
            GroupedAggregationMeasure("add_scale_success_flag", "add_scale_success_rate", "mean"),
            GroupedAggregationMeasure("entry_reduce_failure_flag", "entry_reduce_failure_rate", "mean"),
            GroupedAggregationMeasure("false_positive_flag", "false_positive_rate", "mean"),
        ],
        dropna=False,
    ).result.frame
