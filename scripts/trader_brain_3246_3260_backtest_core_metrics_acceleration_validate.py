from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.core.metrics import grouped_lifecycle_quality


TASK_ID = "task_3221_3280_backend_acceleration_program"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
METRICS = ROOT / "src" / "backtest" / "core" / "metrics.py"


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
            {"bucket": "A", "regime": "up", "lifecycle_id": "L1", "net_return_from_entry": 0.10, "win_flag": 1.0, "add_scale_success_flag": 1.0, "entry_reduce_failure_flag": 0.0, "false_positive_flag": 0.0},
            {"bucket": "A", "regime": "up", "lifecycle_id": None, "net_return_from_entry": None, "win_flag": 0.0, "add_scale_success_flag": None, "entry_reduce_failure_flag": 1.0, "false_positive_flag": 1.0},
            {"bucket": "B", "regime": None, "lifecycle_id": "L3", "net_return_from_entry": -0.20, "win_flag": 0.0, "add_scale_success_flag": 0.0, "entry_reduce_failure_flag": 1.0, "false_positive_flag": 0.0},
            {"bucket": "C", "regime": "flat", "lifecycle_id": "L4", "net_return_from_entry": None, "win_flag": None, "add_scale_success_flag": None, "entry_reduce_failure_flag": None, "false_positive_flag": None},
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = fixture()
    expected = (
        frame.groupby(["bucket", "regime"], dropna=False)
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
    actual = grouped_lifecycle_quality(frame, ["bucket", "regime"])
    expected = expected.astype(object).where(pd.notna(expected), None)
    actual = actual.astype(object).where(pd.notna(actual), None)
    parity_pass = True
    try:
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=False)
    except AssertionError:
        parity_pass = False
    missing_flag_raises = False
    try:
        grouped_lifecycle_quality(frame.drop(columns=["false_positive_flag"]), ["bucket"])
    except KeyError:
        missing_flag_raises = True

    text = METRICS.read_text(encoding="utf-8")
    checks = [
        {"check_name": "metrics_uses_grouped_accelerator", "pass": int("grouped_numeric_aggregate_accelerated" in text)},
        {"check_name": "grouped_lifecycle_quality_matches_pandas", "pass": int(parity_pass)},
        {"check_name": "dropna_false_keeps_null_key_group", "pass": int(actual["regime"].isna().any())},
        {"check_name": "non_null_lifecycle_count_preserved", "pass": int(int(actual[(actual["bucket"] == "A") & (actual["regime"] == "up")].iloc[0]["lifecycle_count"]) == 1)},
        {"check_name": "missing_false_positive_flag_still_raises", "pass": int(missing_flag_raises)},
    ]
    rows = [
        {
            "lane": "backtest_core_metrics",
            "authority": "PACKAGE_HEALTH",
            "result_rows": len(actual),
            "replay_performed": 0,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    write_csv(OUT_DIR / "backtest_core_metrics_acceleration_result.csv", rows)
    write_csv(OUT_DIR / "backtest_core_metrics_acceptance_checks.csv", checks)
    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3246_3260_ERROR] {row['check_name']}")
        return 1
    print("[TASK3246_3260_BACKTEST_CORE_METRICS_ACCELERATION_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
