from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1558_1577_l5_damage_control_engine"
REPORT = ROOT / "docs/reports/task_1558_1577_l5_damage_control_engine/task_1558_1577_l5_damage_control_engine.md"
DECISION = ROOT / "docs/reports/task_1558_1577_l5_damage_control_engine/task_1558_1577_decision.csv"

REQUIRED = [
    "task1558_perfect_goal.csv",
    "task1559_damage_control_rulebook.csv",
    "task1561_damage_action_panel.csv",
    "task1562_damage_replay_trades.csv",
    "task1562_damage_replay_equity.csv",
    "task1563_damage_replay_metrics.csv",
    "task1564_damage_action_summary.csv",
    "task1576_acceptance_gate.csv",
    "task1577_closeout.csv",
    "task1577_closeout.json",
    "artifact_manifest.csv",
]


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
            print(f"[TASK1558_1577_ERROR] {error}")
        return 1

    goals = read_csv(OUT_DIR / "task1558_perfect_goal.csv")
    rules = read_csv(OUT_DIR / "task1559_damage_control_rulebook.csv")
    actions = read_csv(OUT_DIR / "task1561_damage_action_panel.csv")
    trades = read_csv(OUT_DIR / "task1562_damage_replay_trades.csv")
    metrics = read_csv(OUT_DIR / "task1563_damage_replay_metrics.csv")
    summary = read_csv(OUT_DIR / "task1564_damage_action_summary.csv")
    gate = read_csv(OUT_DIR / "task1576_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1577_closeout.csv")

    if len(goals) < 6:
        errors.append("perfect goal packet too small")
    rule_names = {row["rule_name"] for row in rules}
    for required in {"reuse_existing_signals", "source_damage_priority", "price_damage_reduce_first", "no_reentry_cooling", "return_preservation_gate", "audit_only"}:
        if required not in rule_names:
            errors.append(f"missing rule: {required}")
    if len(metrics) != 2:
        errors.append(f"expected two top3/top5 damage metrics, found {len(metrics)}")
    policy_ids = {row["policy_variant_id"] for row in metrics}
    expected_policies = {"l5_damage_reduce_first_top3_v1", "l5_damage_reduce_first_top5_v1"}
    if policy_ids != expected_policies:
        errors.append(f"policy ids mismatch: {policy_ids}")
    action_names = {row["damage_action"] for row in actions}
    for required in {"hold", "reduce", "exit", "no_reentry"}:
        if required not in action_names:
            errors.append(f"missing damage action: {required}")
    if any(row.get("damage_reason") == "price_damage_exit" for row in actions):
        errors.append("price-only full exit should be disabled in reduce-first policy")
    for row in actions + trades + metrics:
        if row.get("assignment_uses_future_outcome") != "0":
            errors.append(f"future assignment flag misuse: {row}")
            break
    for row in trades + metrics:
        if row.get("outcome_used_for_assignment") != "0" or row.get("outcome_used_for_audit_only") != "1":
            errors.append(f"outcome audit flag misuse: {row}")
            break
    for row in metrics:
        if row["mdd_improved_vs_actual_l5"] != "1":
            errors.append(f"MDD did not improve versus actual L5: {row['policy_variant_id']}")
        if row["target_mdd_minus30pct_met"] != "1":
            errors.append(f"MDD target not met: {row['policy_variant_id']}")
        if row["beats_qqq"] != "1":
            errors.append(f"QQQ not beaten: {row['policy_variant_id']}")
        if to_float(row["return_preservation_ratio"]) < 0.75:
            errors.append(f"return preservation too low: {row['policy_variant_id']}")
        if row["target_cagr_30pct_met"] != "0":
            errors.append(f"CAGR target should not be claimed as met: {row['policy_variant_id']}")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append(f"strategy overclaim: {row['policy_variant_id']}")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append(f"deployment overclaim: {row['policy_variant_id']}")
        if row["real_capital"] != "FORBIDDEN":
            errors.append(f"real capital overclaim: {row['policy_variant_id']}")
    if len(summary) < 6:
        errors.append("action summary too small")
    if gate[0]["viable_damage_policy_count"] != "2":
        errors.append("expected two viable damage policies")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")
    if closeout[0]["mdd_target_met_by_any_policy"] != "1":
        errors.append("closeout did not record MDD target pass")
    if closeout[0]["cagr_target_met_by_any_policy"] != "0":
        errors.append("closeout should not record CAGR target pass")

    report_text = REPORT.read_text(encoding="utf-8")
    if "hold/reduce/exit/no-reentry" not in report_text:
        errors.append("report missing action-state goal")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1558_1577_ERROR] {error}")
        return 1
    print("[TASK1558_1577_OK] L5 damage control engine artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
