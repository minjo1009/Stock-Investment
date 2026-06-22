from __future__ import annotations

from pathlib import Path
import pandas as pd


def assess_csv_quality(path: str | Path) -> dict[str, object]:
    csv_path = Path(path)
    if not csv_path.exists():
        return {
            "exists": False,
            "row_count": 0,
            "missing_rows": 0,
            "start_date": None,
            "end_date": None,
        }

    frame = pd.read_csv(csv_path)
    row_count = int(len(frame))
    missing_rows = int(frame.isna().any(axis=1).sum()) if not frame.empty else 0

    start_date = None
    end_date = None
    if "timestamp" in frame.columns and not frame.empty:
        ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dropna()
        if not ts.empty:
            start_date = ts.min().isoformat()
            end_date = ts.max().isoformat()

    return {
        "exists": True,
        "row_count": row_count,
        "missing_rows": missing_rows,
        "start_date": start_date,
        "end_date": end_date,
    }
