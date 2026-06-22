from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1911_1920_watch_recovery_decomposition"
REPORT = ROOT / "docs/reports/task_1911_1920_watch_recovery_decomposition/task_1911_1920_watch_recovery_decomposition.md"
DECISION = ROOT / "docs/reports/task_1911_1920_watch_recovery_decomposition/task_1911_1920_decision.csv"
AUTHORITY = "DIAGNOSTIC_WATCH_RECOVERY_DECOMPOSITION_ONLY"

REQUIRED_FILES = [
    "task1911_input_manifest.csv",
    "task1912_policy_trade_delta.csv",
    "task1913_subtype_view.csv",
    "task1913_action_view.csv",
    "task1914_symbol_view.csv",
    "task1914_month_view.csv",
    "task1915_overlap_cohort_detail.csv",
    "task1915_overlap_cohort_view.csv",
    "task1916_best_recovery_rows.csv",
    "task1916_worst_recovery_rows.csv",
    "task1917_narrow_candidate_audit.csv",
    "task1918_diagnosis.csv",
    "task1919_next_task_plan.csv",
    "task1920_closeout.csv",
    "task1920_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name in REQUIRED_FILES:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_counts_and_authority() -> None:
    expected_counts = {
        "task1911_input_manifest.csv": 5,
        "task1913_subtype_view.csv": 12,
        "task1915_overlap_cohort_view.csv": 3,
        "task1918_diagnosis.csv": 4,
        "task1919_next_task_plan.csv": 5,
        "task1920_closeout.csv": 1,
    }
    for name, expected in expected_counts.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} rows got {len(rows)}")
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome guard")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{path.name}:{idx} outcome assignment guard")


def validate_decomposition_findings() -> None:
    cohort = read_csv(OUT_DIR / "task1915_overlap_cohort_view.csv")
    top5_only = [
        row
        for row in cohort
        if row["policy_variant_id"] == "watch_recovery_top5_v1" and row["slot_overlap_cohort"] == "top5_only"
    ]
    fail_if(len(top5_only) != 1, "missing top5-only cohort row")
    fail_if(to_float(top5_only[0]["incremental_pnl_sum_audit_only"]) >= 0, "top5-only cohort should be negative")
    subtype = read_csv(OUT_DIR / "task1913_subtype_view.csv")
    top3_normal = [
        row
        for row in subtype
        if row["policy_variant_id"] == "watch_recovery_top3_v1"
        and row["watch_subtype"] == "normal_winner_volatility_watch"
    ]
    top5_upgrade = [
        row
        for row in subtype
        if row["policy_variant_id"] == "watch_recovery_top5_v1"
        and row["watch_subtype"] == "upgrade_candidate_watch"
    ]
    fail_if(len(top3_normal) != 1, "missing top3 normal winner subtype")
    fail_if(to_float(top3_normal[0]["incremental_pnl_sum_audit_only"]) <= 0, "top3 normal winner subtype should be positive")
    fail_if(len(top5_upgrade) != 1, "missing top5 upgrade subtype")
    fail_if(to_float(top5_upgrade[0]["incremental_pnl_sum_audit_only"]) >= 0, "top5 upgrade subtype should be negative")
    symbol = read_csv(OUT_DIR / "task1914_symbol_view.csv")
    anet_top5 = [row for row in symbol if row["policy_variant_id"] == "watch_recovery_top5_v1" and row["symbol"] == "ANET"]
    fail_if(len(anet_top5) != 1, "missing top5 ANET symbol row")
    fail_if(to_float(anet_top5[0]["incremental_pnl_sum_audit_only"]) >= -10, "ANET top5 drag not detected")
    closeout = read_csv(OUT_DIR / "task1920_closeout.csv")[0]
    fail_if(closeout["primary_bottleneck"] != "top5_recovery_candidate_quality_and_overlap_fragility", "unexpected bottleneck")


def validate_status_and_report() -> None:
    closeout = read_csv(OUT_DIR / "task1920_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital status changed")
    payload = json.loads((OUT_DIR / "task1920_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["real_capital"] != "FORBIDDEN", "json real capital status changed")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Top3 improved",
        "Top5 worsened",
        "top5-only",
        "outcome deltas only for audit",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_decomposition_findings()
        validate_status_and_report()
    except AssertionError as exc:
        print(f"[TASK1911_1920_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1911_1920_VALIDATE_OK] watch recovery decomposition artifacts are valid")


if __name__ == "__main__":
    main()
