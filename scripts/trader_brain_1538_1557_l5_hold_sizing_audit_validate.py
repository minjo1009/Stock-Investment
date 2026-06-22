from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1538_1557_l5_hold_sizing_audit"
REPORT = ROOT / "docs/reports/task_1538_1557_l5_hold_sizing_audit/task_1538_1557_l5_hold_sizing_audit.md"
DECISION = ROOT / "docs/reports/task_1538_1557_l5_hold_sizing_audit/task_1538_1557_decision.csv"

REQUIRED = [
    "task1538_expert_audit.csv",
    "task1539_scenario_definitions.csv",
    "task1540_scenario_replay_trades.csv",
    "task1540_scenario_replay_equity.csv",
    "task1540_scenario_replay_metrics.csv",
    "task1541_scenario_comparison.csv",
    "task1542_hold_extension_trade_audit.csv",
    "task1543_cap_sizing_trade_audit.csv",
    "task1544_exit_reason_summary.csv",
    "task1545_audit_diagnosis.csv",
    "task1556_acceptance_gate.csv",
    "task1557_closeout.csv",
    "task1557_closeout.json",
    "artifact_manifest.csv",
]

EXPECTED_SCENARIOS = {
    "actual_l5_operating",
    "no_hold_extension",
    "full_size_no_cap",
    "no_hold_full_size",
    "scheduled_only_counterfactual",
}
EXPECTED_POLICIES = {"l5_operating_top3_v1", "l5_operating_top5_v1"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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
            print(f"[TASK1538_1557_ERROR] {error}")
        return 1

    scenarios = read_csv(OUT_DIR / "task1539_scenario_definitions.csv")
    trades = read_csv(OUT_DIR / "task1540_scenario_replay_trades.csv")
    metrics = read_csv(OUT_DIR / "task1540_scenario_replay_metrics.csv")
    comparisons = read_csv(OUT_DIR / "task1541_scenario_comparison.csv")
    hold_audit = read_csv(OUT_DIR / "task1542_hold_extension_trade_audit.csv")
    cap_audit = read_csv(OUT_DIR / "task1543_cap_sizing_trade_audit.csv")
    diagnosis = read_csv(OUT_DIR / "task1545_audit_diagnosis.csv")
    gate = read_csv(OUT_DIR / "task1556_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1557_closeout.csv")

    scenario_ids = {row["scenario_id"] for row in scenarios}
    if scenario_ids != EXPECTED_SCENARIOS:
        errors.append(f"scenario definitions mismatch: {scenario_ids}")
    metric_pairs = {(row["scenario_id"], row["policy_variant_id"]) for row in metrics}
    expected_pairs = {(scenario, policy) for scenario in EXPECTED_SCENARIOS for policy in EXPECTED_POLICIES}
    if metric_pairs != expected_pairs:
        errors.append(f"metric scenario/policy pairs mismatch: {metric_pairs ^ expected_pairs}")
    if len(metrics) != 10:
        errors.append(f"expected 10 scenario metric rows, found {len(metrics)}")
    if len(comparisons) != 8:
        errors.append(f"expected 8 comparison rows, found {len(comparisons)}")
    comparison_ids = {row["comparison_id"] for row in comparisons}
    for required in {"hold_extension_effect", "cap_only_sizing_effect", "combined_l5_effect", "actual_vs_scheduled_only"}:
        if required not in comparison_ids:
            errors.append(f"missing comparison: {required}")

    for row in metrics + comparisons + hold_audit + cap_audit:
        if row.get("outcome_used_for_assignment") != "0" or row.get("outcome_used_for_audit_only") != "1":
            errors.append(f"audit flag misuse: {row}")
            break
    for row in metrics:
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append(f"strategy overclaim: {row['scenario_id']} {row['policy_variant_id']}")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append(f"deployment overclaim: {row['scenario_id']} {row['policy_variant_id']}")
        if row["real_capital"] != "FORBIDDEN":
            errors.append(f"real capital overclaim: {row['scenario_id']} {row['policy_variant_id']}")

    lookup = {(row["comparison_id"], row["policy_variant_id"]): row for row in comparisons}
    for policy in EXPECTED_POLICIES:
        hold = lookup[("hold_extension_effect", policy)]
        cap = lookup[("cap_only_sizing_effect", policy)]
        if to_float(hold["final_equity_delta"]) <= 0:
            errors.append(f"hold extension did not improve final equity: {policy}")
        if to_float(cap["final_equity_delta"]) >= 0:
            errors.append(f"cap-only unexpectedly improved final equity versus full-size: {policy}")
        if to_float(cap["mdd_delta_positive_is_better"]) <= 0:
            errors.append(f"cap-only did not improve MDD versus full-size: {policy}")

    hold_actual_count = sum(1 for row in trades if row["scenario_id"] == "actual_l5_operating" and row["hold_extension_used"] == "1")
    if len(hold_audit) != hold_actual_count:
        errors.append(f"hold audit count mismatch: audit={len(hold_audit)} actual_hold={hold_actual_count}")
    cap_actual_count = sum(
        1
        for row in trades
        if row["scenario_id"] == "actual_l5_operating" and to_float(row["position_size_cap_multiplier"], 1.0) < 1.0
    )
    if len(cap_audit) != cap_actual_count:
        errors.append(f"cap audit count mismatch: audit={len(cap_audit)} actual_cap={cap_actual_count}")
    if not any(row["finding"] == "hold_extension_is_primary_positive_driver" for row in diagnosis):
        errors.append("missing hold-extension diagnosis")
    if not any(row["finding"] == "cap_only_sizing_costs_return_and_may_reduce_or_increase_drawdown_by_policy" for row in diagnosis):
        errors.append("missing cap-only diagnosis")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")
    if closeout[0]["cap_only_blanket_release_approved"] != "0":
        errors.append("blanket cap release should not be approved")

    report_text = REPORT.read_text(encoding="utf-8")
    if "hold extension is the main positive L5 driver" not in report_text:
        errors.append("report missing key hold conclusion")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1538_1557_ERROR] {error}")
        return 1
    print("[TASK1538_1557_OK] L5 hold/sizing audit artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
