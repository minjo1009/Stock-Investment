from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1901_1910_watch_recovery_replay"
REPORT = ROOT / "docs/reports/task_1901_1910_watch_recovery_replay/task_1901_1910_watch_recovery_replay.md"
DECISION = ROOT / "docs/reports/task_1901_1910_watch_recovery_replay/task_1901_1910_decision.csv"
AUTHORITY = "DIAGNOSTIC_WATCH_RECOVERY_REPLAY_ONLY"

REQUIRED_FILES = [
    "task1901_input_manifest.csv",
    "task1902_frozen_policy_config.csv",
    "task1903_recovery_candidate_audit.csv",
    "task1904_watch_recovery_budget.csv",
    "task1905_watch_recovery_replay_trades.csv",
    "task1905_watch_recovery_replay_equity.csv",
    "task1906_watch_recovery_metrics.csv",
    "task1906_split_oos_metrics.csv",
    "task1907_cost_stress_metrics.csv",
    "task1908_failure_attribution.csv",
    "task1909_acceptance_gate.csv",
    "task1910_closeout.csv",
    "task1910_closeout.json",
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
        "task1901_input_manifest.csv": 5,
        "task1902_frozen_policy_config.csv": 2,
        "task1903_recovery_candidate_audit.csv": 113,
        "task1906_watch_recovery_metrics.csv": 2,
        "task1906_split_oos_metrics.csv": 4,
        "task1907_cost_stress_metrics.csv": 8,
        "task1909_acceptance_gate.csv": 1,
        "task1910_closeout.csv": 1,
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


def validate_recovery_contract() -> None:
    audit = read_csv(OUT_DIR / "task1903_recovery_candidate_audit.csv")
    eligible = [row for row in audit if row["eligible_for_recovery"] == "1"]
    ineligible = [row for row in audit if row["eligible_for_recovery"] == "0"]
    fail_if(len(eligible) != 36, f"eligible recovery count expected 36 got {len(eligible)}")
    fail_if(len(ineligible) != 77, f"ineligible watch count expected 77 got {len(ineligible)}")
    actions = {row["recovery_action"] for row in eligible}
    fail_if(actions != {"near_full_hold", "restore_full_hold"}, f"unexpected eligible actions: {actions}")
    for row in ineligible:
        fail_if(row["recovery_action"] != "unchanged", "ineligible watch row changed")
        fail_if(to_float(row["multiplier_delta"]) != 0.0, "ineligible watch multiplier changed")
    budget = read_csv(OUT_DIR / "task1904_watch_recovery_budget.csv")
    damage = [row for row in budget if row["watch_subtype"] == "damage_watch"]
    fail_if(not damage, "no damage watch rows in budget")
    for row in damage:
        fail_if(row["recovery_action"] != "unchanged", "damage watch was rerisked")


def validate_metrics() -> None:
    metrics = {row["policy_variant_id"]: row for row in read_csv(OUT_DIR / "task1906_watch_recovery_metrics.csv")}
    fail_if(set(metrics) != {"watch_recovery_top3_v1", "watch_recovery_top5_v1"}, "unexpected policy set")
    top3 = metrics["watch_recovery_top3_v1"]
    top5 = metrics["watch_recovery_top5_v1"]
    fail_if(to_float(top3["delta_vs_desk_final"]) <= 0, "top3 did not improve vs desk-specific replay")
    fail_if(to_float(top3["delta_vs_desk_mdd"]) < -0.001, "top3 MDD worsened materially")
    fail_if(top3["target_mdd_minus30pct_met"] != "1", "top3 MDD target failed")
    fail_if(top3["target_cagr_30pct_met"] != "0", "top3 unexpectedly marked CAGR target met")
    fail_if(to_float(top5["delta_vs_desk_final"]) >= 0, "top5 should show failed broad recovery")
    for row in metrics.values():
        fail_if(row["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
        fail_if(row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
        fail_if(row["real_capital"] != "FORBIDDEN", "real capital status changed")


def validate_status_and_report() -> None:
    closeout = read_csv(OUT_DIR / "task1910_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "closeout strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "closeout deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "closeout real capital status changed")
    payload = json.loads((OUT_DIR / "task1910_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["real_capital"] != "FORBIDDEN", "json real capital status changed")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Only `normal_winner_volatility_watch` and `upgrade_candidate_watch`",
        "Damage-watch names stayed defensive",
        "no new price matching",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_recovery_contract()
        validate_metrics()
        validate_status_and_report()
    except AssertionError as exc:
        print(f"[TASK1901_1910_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1901_1910_VALIDATE_OK] watch recovery replay artifacts are valid")


if __name__ == "__main__":
    main()
