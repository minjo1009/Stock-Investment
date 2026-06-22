from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_firm_grade_fixture(root: Path, *, rows: int = 120) -> Path:
    records = []
    start = pd.Timestamp("2024-01-02", tz="UTC")
    for idx in range(rows):
        entry = start + pd.Timedelta(days=idx * 5)
        good = idx % 4 != 0
        records.append(
            {
                "lifecycle_id": f"L{idx}",
                "entry_ts": entry.isoformat(),
                "simulated_exit_ts": (entry + pd.Timedelta(days=40)).isoformat(),
                "entry_price": 100.0 + idx,
                "simulated_exit_price": (100.0 + idx) * (1.10 if good else 0.94),
                "net_return_from_entry": 0.10 if good else -0.06,
                "win_flag": int(good),
                "add_scale_success_flag": int(good),
                "entry_reduce_failure_flag": int(not good),
                "false_positive_flag": int(not good),
                "holding_days": 40.0,
                "same_day_exit_flag": 0,
                "theme_id": "theme_a" if idx % 2 else "theme_b",
                "symbol": f"S{idx % 8}",
                "symbol_multiday_setup_state": "trend_persistence_near_high",
                "timing_state": "opening_drive",
                "quarter": f"{entry.year}Q{((entry.month - 1) // 3) + 1}",
                "theme_regime_state_v4": "persistent_theme_leader",
                "exit_reason": "time_exit" if good else "trailing_stop_exit",
            }
        )
    path = root / "panel.csv"
    pd.DataFrame(records).to_csv(path, index=False)
    return path
