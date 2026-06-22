from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1941_1950_gap_hardening"
REPORT = ROOT / "docs/reports/task_1941_1950_gap_hardening/task_1941_1950_gap_hardening.md"
DECISION = ROOT / "docs/reports/task_1941_1950_gap_hardening/task_1941_1950_decision.csv"
AUTHORITY = "DIAGNOSTIC_GAP_HARDENING_ONLY"

REQUIRED_COUNTS = {
    "task1941_gap_hardening_input_manifest.csv": 8,
    "task1942_macro_vintage_readiness_gate.csv": 61,
    "task1943_earnings_guidance_readiness_gate.csv": 377,
    "task1944_primitive_quality_audit.csv": 10,
    "task1945_hardened_l4_thesis_cards.csv": 377,
    "task1946_hardened_top3_replay_trades.csv": 160,
    "task1946_hardened_top3_replay_equity.csv": 61,
    "task1946_hardened_top3_replay_metrics.csv": 1,
    "task1946_split_oos_metrics.csv": 2,
    "task1946_cost_stress_metrics.csv": 4,
    "task1947_top5_shadow_safety_audit.csv": 217,
    "task1948_regression_comparison.csv": 3,
    "task1949_expert_subagent_audit.csv": 5,
    "task1950_acceptance_gate.csv": 1,
    "task1950_closeout.csv": 1,
}


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
    for name in REQUIRED_COUNTS:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task1950_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_counts_and_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{path.name}:{idx} outcome assignment")


def validate_hardening_gates() -> None:
    macro = read_csv(OUT_DIR / "task1942_macro_vintage_readiness_gate.csv")
    fail_if(any(row["alfred_vintage_certified"] != "0" for row in macro), "macro vintage should remain uncertified")
    fail_if(any(row["active_assignment_permission"] != "macro_shadow_only_until_vintage_certified" for row in macro), "macro permission mismatch")
    earnings = read_csv(OUT_DIR / "task1943_earnings_guidance_readiness_gate.csv")
    fail_if(any(row["gate_verdict"] != "vendor_blocked_schema_only" for row in earnings), "earnings gate should remain vendor blocked")
    fail_if(not any(row["expectation_proxy_present"] == "1" for row in earnings), "expectation proxy never present")
    primitive = {row["primitive_name"]: row for row in read_csv(OUT_DIR / "task1944_primitive_quality_audit.csv")}
    fail_if(primitive["macro_offsets_growth"]["hardening_decision"] != "remove_active_score_effect_keep_shadow_audit", "macro hardening missing")
    fail_if(primitive["expectation_gap_expands_payoff"]["hardening_decision"] != "cap_or_downgrade_score_effect_until_pit_source", "expectation hardening missing")
    hardened = read_csv(OUT_DIR / "task1945_hardened_l4_thesis_cards.csv")
    fail_if(not any(to_float(row["macro_vintage_adjustment"]) != 0 for row in hardened), "macro adjustment never applied")
    fail_if(not any(to_float(row["earnings_guidance_adjustment"]) != 0 for row in hardened), "earnings adjustment never applied")


def validate_replay_and_top5_shadow() -> None:
    metric = read_csv(OUT_DIR / "task1946_hardened_top3_replay_metrics.csv")[0]
    fail_if(metric["policy_variant_id"] != "interaction_hardened_top3_v1", "unexpected hardened policy")
    fail_if(to_float(metric["final_equity"]) <= to_float(metric["baseline_final_equity"]), "hardened replay did not beat sleeve baseline")
    fail_if(metric["joint_target_met"] != "1", "hardened replay does not meet diagnostic joint target")
    fail_if(metric["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    top5 = read_csv(OUT_DIR / "task1947_top5_shadow_safety_audit.csv")
    fail_if(any(row["replay_executed"] != "0" for row in top5), "top5 replay should not execute")
    fail_if(not any(row["hardened_top5_gate"] == "blocked_shadow_only" for row in top5), "top5 weak rows not blocked")
    fail_if(not any(row["hardened_top5_gate"] == "blocked_broad_or_live_financing_state" for row in top5), "broad financing top5 rows not blocked")
    fail_if(any(row["previous_dilution_specificity_state"] in {"active_financing_pressure", "live_active_dilution"} and row["hardened_top5_gate"] == "shadow_eligible_but_not_replayed" for row in top5), "broad/live financing row allowed as top5 eligible")


def validate_report_and_closeout() -> None:
    closeout = read_csv(OUT_DIR / "task1950_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "closeout strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "closeout deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "closeout real capital status changed")
    payload = json.loads((OUT_DIR / "task1950_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "gap_hardening_complete_diagnostic_only", "json closeout mismatch")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Gap Hardening",
        "Macro effect: shadow-only",
        "Earnings/guidance effect: confidence-limited",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_hardening_gates()
        validate_replay_and_top5_shadow()
        validate_report_and_closeout()
    except AssertionError as exc:
        print(f"[TASK1941_1950_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1941_1950_VALIDATE_OK] gap hardening artifacts are valid")


if __name__ == "__main__":
    main()
