from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1886_1895_desk_replay_detailed_analysis"
REPORT = ROOT / "docs/reports/task_1886_1895_desk_replay_detailed_analysis/task_1886_1895_desk_replay_detailed_analysis.md"
DECISION = ROOT / "docs/reports/task_1886_1895_desk_replay_detailed_analysis/task_1886_1895_decision.csv"
AUTHORITY = "DIAGNOSTIC_DESK_REPLAY_DETAILED_ANALYSIS_ONLY"

REQUIRED_FILES = [
    "task1886_analysis_input_manifest.csv",
    "task1887_policy_delta_trade_join.csv",
    "task1888_sleeve_attribution.csv",
    "task1889_action_attribution.csv",
    "task1889_financing_attribution.csv",
    "task1889_thesis_attribution.csv",
    "task1890_equity_delta_by_period.csv",
    "task1891_lost_vs_baseline_top_drivers.csv",
    "task1892_improved_vs_source_attached_top_drivers.csv",
    "task1893_failure_diagnosis.csv",
    "task1894_next_task_plan.csv",
    "task1895_closeout.csv",
    "task1895_closeout.json",
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
        "task1886_analysis_input_manifest.csv": 6,
        "task1891_lost_vs_baseline_top_drivers.csv": 50,
        "task1892_improved_vs_source_attached_top_drivers.csv": 50,
        "task1893_failure_diagnosis.csv": 5,
        "task1894_next_task_plan.csv": 5,
        "task1895_closeout.csv": 1,
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


def validate_analysis_findings() -> None:
    joined = read_csv(OUT_DIR / "task1887_policy_delta_trade_join.csv")
    fail_if(len(joined) < 300, "joined trade panel too small")
    sleeve = read_csv(OUT_DIR / "task1888_sleeve_attribution.csv")
    top3_winner = [
        row
        for row in sleeve
        if row["policy_variant_id"] == "desk_specific_top3_v1" and row["strategy_sleeve"] == "winner_compounder"
    ]
    fail_if(len(top3_winner) != 1, "missing top3 winner attribution")
    fail_if(to_float(top3_winner[0]["desk_delta_vs_baseline_sum_audit_only"]) > -500, "top3 winner loss not detected")
    action = read_csv(OUT_DIR / "task1889_action_attribution.csv")
    top3_watch = [
        row
        for row in action
        if row["policy_variant_id"] == "desk_specific_top3_v1"
        and row["strategy_sleeve"] == "winner_compounder"
        and row["desk_action"] == "watch"
    ]
    fail_if(len(top3_watch) != 1, "missing top3 winner watch attribution")
    fail_if(to_float(top3_watch[0]["desk_delta_vs_baseline_sum_audit_only"]) > -300, "winner watch loss not detected")
    improved = read_csv(OUT_DIR / "task1892_improved_vs_source_attached_top_drivers.csv")
    fail_if(to_float(improved[0]["desk_delta_vs_source_attached_pnl_audit_only"]) <= 0, "improvement drivers not positive")
    closeout = read_csv(OUT_DIR / "task1895_closeout.csv")[0]
    fail_if(closeout["primary_bottleneck"] != "winner_watch_calibration_after_broad_trim_repair", "unexpected bottleneck")


def validate_status_and_report() -> None:
    closeout = read_csv(OUT_DIR / "task1895_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital status changed")
    payload = json.loads((OUT_DIR / "task1895_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["strategy_acceptance"] != "NOT_ACCEPTED", "json strategy status changed")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Broad trim problem is mostly fixed",
        "winner",
        "watch",
        "No new price matching",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_analysis_findings()
        validate_status_and_report()
    except AssertionError as exc:
        print(f"[TASK1886_1895_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1886_1895_VALIDATE_OK] desk replay detailed analysis artifacts are valid")


if __name__ == "__main__":
    main()
