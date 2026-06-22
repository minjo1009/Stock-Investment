from __future__ import annotations

import pandas as pd


def cost_stress_quality(frame: pd.DataFrame, stresses: dict[str, float] | None = None) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    stresses = stresses or {
        "reported_post_cost": 0.0,
        "additional_25bp_round_trip_cost": 0.0025,
        "additional_50bp_round_trip_cost": 0.0050,
    }
    rows: list[dict[str, object]] = []
    for name, cost in stresses.items():
        adjusted = frame["net_return_from_entry"] - cost
        rows.append(
            {
                "cost_stress_name": name,
                "lifecycle_count": int(len(frame)),
                "avg_net_return_pct": float(adjusted.mean() * 100.0),
                "win_rate": float((adjusted > 0).mean()),
                "entry_reduce_failure_rate": float(frame["entry_reduce_failure_flag"].mean()),
                "add_scale_success_rate": float(frame["add_scale_success_flag"].mean()),
            }
        )
    return pd.DataFrame(rows)
