from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1896_1900_watch_subtype_calibration"
REPORT = ROOT / "docs/reports/task_1896_1900_watch_subtype_calibration/task_1896_1900_watch_subtype_calibration.md"
DECISION = ROOT / "docs/reports/task_1896_1900_watch_subtype_calibration/task_1896_1900_decision.csv"
AUTHORITY = "DIAGNOSTIC_WATCH_SUBTYPE_CALIBRATION_ONLY"

REQUIRED_FILES = [
    "task1896_input_manifest.csv",
    "task1896_watch_subtype_panel.csv",
    "task1897_watch_subtype_attribution.csv",
    "task1897_watch_policy_attribution.csv",
    "task1897_watch_action_attribution.csv",
    "task1898_live_dilution_precision_panel.csv",
    "task1899_speculative_block_payoff_audit.csv",
    "task1900_hold_calibration_contract.csv",
    "task1900_closeout.csv",
    "task1900_closeout.json",
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
        "task1896_input_manifest.csv": 6,
        "task1896_watch_subtype_panel.csv": 113,
        "task1897_watch_subtype_attribution.csv": 5,
        "task1900_hold_calibration_contract.csv": 5,
        "task1900_closeout.csv": 1,
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


def validate_subtypes() -> None:
    rows = read_csv(OUT_DIR / "task1896_watch_subtype_panel.csv")
    subtypes = {row["watch_subtype"] for row in rows}
    expected = {
        "damage_watch",
        "normal_winner_volatility_watch",
        "information_gap_watch",
        "overhang_watch",
        "upgrade_candidate_watch",
    }
    fail_if(subtypes != expected, f"unexpected watch subtypes: {subtypes}")
    normal = [row for row in rows if row["watch_subtype"] == "normal_winner_volatility_watch"]
    upgrade = [row for row in rows if row["watch_subtype"] == "upgrade_candidate_watch"]
    damage = [row for row in rows if row["watch_subtype"] == "damage_watch"]
    fail_if(len(normal) < 20, "normal winner volatility subtype too sparse")
    fail_if(len(upgrade) < 3, "upgrade candidate subtype too sparse")
    fail_if(len(damage) < 20, "damage subtype too sparse")
    for row in normal + upgrade:
        fail_if(row["financing_specificity_state"] == "live_active_dilution", "rerisk subtype contains live dilution")
    subtype_attr = {row["watch_subtype"]: row for row in read_csv(OUT_DIR / "task1897_watch_subtype_attribution.csv")}
    fail_if(to_float(subtype_attr["normal_winner_volatility_watch"]["desk_delta_vs_baseline_sum_audit_only"]) >= 0, "normal winner volatility audit delta should show lost upside")
    fail_if(to_float(subtype_attr["damage_watch"]["damage_watch_count"]) != len(damage), "damage count mismatch")


def validate_precision_and_contract() -> None:
    live = read_csv(OUT_DIR / "task1898_live_dilution_precision_panel.csv")
    fail_if(len(live) < 20, "live dilution precision panel too small")
    states = {row["precision_state"] for row in live}
    fail_if("hard_live_financing_risk" not in states, "hard live financing risk missing")
    spec = read_csv(OUT_DIR / "task1899_speculative_block_payoff_audit.csv")
    fail_if(len(spec) < 10, "speculative block audit too small")
    contract = read_csv(OUT_DIR / "task1900_hold_calibration_contract.csv")
    gates = {row["watch_subtype"]: row["next_replay_gate"] for row in contract}
    fail_if(gates["damage_watch"] == "eligible_for_frozen_replay", "damage watch cannot be rerisk eligible")
    fail_if(gates["upgrade_candidate_watch"] != "eligible_for_frozen_replay", "upgrade candidate must be replay eligible")
    fail_if(gates["normal_winner_volatility_watch"] != "eligible_for_frozen_replay", "normal winner volatility must be replay eligible")


def validate_status_and_report() -> None:
    closeout = read_csv(OUT_DIR / "task1900_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital status changed")
    fail_if(closeout["decision"] != "watch_subtype_calibration_complete_no_replay", "unexpected closeout decision")
    payload = json.loads((OUT_DIR / "task1900_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["real_capital"] != "FORBIDDEN", "json real capital status changed")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Watch is no longer one bucket",
        "normal winner volatility",
        "No replay was executed",
        "Outcome deltas are audit-only",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_subtypes()
        validate_precision_and_contract()
        validate_status_and_report()
    except AssertionError as exc:
        print(f"[TASK1896_1900_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1896_1900_VALIDATE_OK] watch subtype calibration artifacts are valid")


if __name__ == "__main__":
    main()
