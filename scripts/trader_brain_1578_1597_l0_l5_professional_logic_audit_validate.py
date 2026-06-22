from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1578_1597_l0_l5_professional_logic_audit"
REPORT = ROOT / "docs/reports/task_1578_1597_l0_l5_professional_logic_audit/task_1578_1597_l0_l5_professional_logic_audit.md"
DECISION = ROOT / "docs/reports/task_1578_1597_l0_l5_professional_logic_audit/task_1578_1597_decision.csv"

REQUIRED = [
    "task1578_professional_source_standards.csv",
    "task1579_implementation_inventory.csv",
    "task1580_current_metric_ladder.csv",
    "task1581_l2_distribution_audit.csv",
    "task1582_l3_distribution_audit.csv",
    "task1583_l4_distribution_audit.csv",
    "task1584_l5_action_audit.csv",
    "task1585_requirement_gap_matrix.csv",
    "task1590_root_cause_matrix.csv",
    "task1596_acceptance_gate.csv",
    "task1597_closeout.csv",
    "task1597_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED:
        if not (OUT_DIR / name).exists():
            errors.append(f"missing artifact: {name}")
    if not REPORT.exists():
        errors.append(f"missing report: {REPORT}")
    if not DECISION.exists():
        errors.append(f"missing decision: {DECISION}")
    if errors:
        for error in errors:
            print(f"[TASK1578_1597_ERROR] {error}")
        return 1

    standards = read_csv(OUT_DIR / "task1578_professional_source_standards.csv")
    inventory = read_csv(OUT_DIR / "task1579_implementation_inventory.csv")
    metrics = read_csv(OUT_DIR / "task1580_current_metric_ladder.csv")
    l2_dist = read_csv(OUT_DIR / "task1581_l2_distribution_audit.csv")
    gaps = read_csv(OUT_DIR / "task1585_requirement_gap_matrix.csv")
    roots = read_csv(OUT_DIR / "task1590_root_cause_matrix.csv")
    gate = read_csv(OUT_DIR / "task1596_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1597_closeout.csv")

    if len(standards) < 5:
        errors.append("professional standards packet too small")
    if not any("SEC Form 8-K" in row["standard_name"] for row in standards):
        errors.append("missing SEC 8-K professional standard")
    if not any("MacKinlay" in row["standard_name"] for row in standards):
        errors.append("missing event study professional standard")
    if not any(row["layer"] == "L5" for row in inventory):
        errors.append("missing L5 implementation inventory")
    if len(metrics) < 8:
        errors.append("metric ladder too small")
    if not any(row["gap_name"] == "analyst_pit_and_external_expectation" and row["severity_1_to_5"] == "5" for row in gaps):
        errors.append("missing analyst PIT severity-5 gap")
    if not any(row["gap_name"] == "surprise_expectation_quality" and row["severity_1_to_5"] == "5" for row in gaps):
        errors.append("missing surprise quality severity-5 gap")
    if not any(row["gap_name"] == "position_operation_vs_alpha_tradeoff" for row in gaps):
        errors.append("missing L5 alpha/risk tradeoff gap")
    if gate[0]["implementation_plumbing_broken"] != "0":
        errors.append("gate should not claim plumbing is broken")
    if gate[0]["professional_logic_missing_or_weak"] != "1":
        errors.append("gate should claim professional logic gap")
    if gate[0]["primary_next_fix"] != "expectation_to_payoff_and_re_risk_bridge":
        errors.append("wrong primary next fix")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")
    if closeout[0]["answer_to_user_question"] != "implementation_is_not_randomly_broken_but_professional_logic_is_incomplete_and_partly_shallow":
        errors.append("closeout answer mismatch")
    if not any(row["root_cause"] == "core_missing_bridge_is_expectation_to_payoff" for row in roots):
        errors.append("missing expectation-to-payoff root cause")

    dist_lookup = {(row["field"], row["value"]): row for row in l2_dist}
    if dist_lookup.get(("expectation_v6_state", "true_surprise_proxy"), {}).get("row_count") != "77":
        errors.append("unexpected true_surprise_proxy count")
    if dist_lookup.get(("absorption_v6_state", "sustained_market_acceptance"), {}).get("row_count") != "190":
        errors.append("unexpected sustained_market_acceptance count")

    report_text = REPORT.read_text(encoding="utf-8")
    if "implementation plumbing is not the main failure" not in report_text:
        errors.append("report missing direct implementation answer")
    if "expectation -> payoff -> L5 re-risk bridge" not in report_text:
        errors.append("report missing primary bridge gap")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1578_1597_ERROR] {error}")
        return 1
    print("[TASK1578_1597_OK] L0-L5 professional logic audit artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
