from __future__ import annotations

import pandas as pd


def assign_time_splits(frame: pd.DataFrame, ts_col: str = "entry_ts", validation_q: float = 0.70, recent_q: float = 0.85) -> pd.Series:
    timestamps = pd.to_datetime(frame[ts_col], utc=True, errors="coerce")
    valid = timestamps.dropna().sort_values()
    if valid.empty:
        return pd.Series(["unknown"] * len(frame), index=frame.index)
    validation_cut = valid.quantile(validation_q)
    recent_cut = valid.quantile(recent_q)
    split = pd.Series(["train_design"] * len(frame), index=frame.index)
    split.loc[timestamps >= validation_cut] = "validation"
    split.loc[timestamps >= recent_cut] = "recent_oos"
    return split
