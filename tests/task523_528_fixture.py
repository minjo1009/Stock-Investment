from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_gap_fixture(root: Path, *, rows: int = 140) -> Path:
    records = []
    start = pd.Timestamp("2024-01-02", tz="UTC")
    for idx in range(rows):
        entry = start + pd.Timedelta(days=idx * 5)
        weak = idx % 5 == 0
        records.append(
            {
                "lifecycle_id": f"L{idx}",
                "entry_ts": entry.isoformat(),
                "simulated_exit_ts": (entry + pd.Timedelta(days=40)).isoformat(),
                "entry_price": 100.0,
                "simulated_exit_price": 108.0 if not weak else 96.0,
                "net_return_from_entry": 0.08 if not weak else -0.04,
                "win_flag": int(not weak),
                "add_scale_success_flag": int(not weak),
                "entry_reduce_failure_flag": int(weak),
                "false_positive_flag": int(weak),
                "holding_days": 40.0,
                "same_day_exit_flag": 0,
                "theme_id": "theme_a" if idx % 2 else "theme_b",
                "symbol": f"S{idx % 5}",
                "theme_regime_state_v4": "theme_participation" if weak else "persistent_theme_leader",
                "symbol_multiday_setup_state": "volume_confirmed_reclaim" if weak else "trend_persistence_near_high",
                "timing_state": "opening_drive" if weak else "late_day_confirmation",
                "quarter": f"{entry.year}Q{((entry.month - 1) // 3) + 1}",
            }
        )
    path = root / "panel.csv"
    pd.DataFrame(records).to_csv(path, index=False)
    return path
