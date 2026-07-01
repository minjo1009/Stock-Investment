from __future__ import annotations

import pandas as pd


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
    return (
        frame.groupby(keys, dropna=False)
        .agg(
            lifecycle_count=("lifecycle_id", "count"),
            avg_net_return_pct=("net_return_from_entry", lambda s: float(s.mean() * 100.0)),
            win_rate=("win_flag", "mean"),
            add_scale_success_rate=("add_scale_success_flag", "mean"),
            entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
            false_positive_rate=("false_positive_flag", "mean"),
        )
        .reset_index()
    )
