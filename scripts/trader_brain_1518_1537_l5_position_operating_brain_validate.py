from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
REPORT = ROOT / "docs/reports/task_1518_1537_l5_position_operating_brain/task_1518_1537_l5_position_operating_brain.md"

REQUIRED = [
    "task1518_expert_audit.csv",
    "task1519_l5_operating_preregistered_rules.csv",
    "task1520_thesis_state_machine.csv",
    "task1521_entry_gate_panel.csv",
    "task1522_policy_specs_pre_replacement.csv",
    "task1524_replacement_hurdle_panel.csv",
    "task1524_policy_specs_final.csv",
    "task1523_source_receipt_exit_panel.csv",
    "task1523_price_path_exit_panel.csv",
    "task1523_hold_receipt_panel.csv",
    "task1523_exit_decision_panel.csv",
    "task1525_replay_trades.csv",
    "task1525_replay_equity.csv",
    "task1525_replay_metrics.csv",
    "task1526_scheduled_only_trades.csv",
    "task1526_scheduled_only_equity.csv",
    "task1526_scheduled_only_metrics.csv",
    "task1527_l5_delta_audit.csv",
    "task1527_l5_delta_summary.csv",
    "task1528_summary.csv",
    "task1536_acceptance_gate.csv",
    "task1537_closeout.csv",
    "task1537_closeout.json",
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
    if errors:
        for error in errors:
            print(f"[TASK1518_1537_ERROR] {error}")
        return 1

    rules = read_csv(OUT_DIR / "task1519_l5_operating_preregistered_rules.csv")
    states = read_csv(OUT_DIR / "task1520_thesis_state_machine.csv")
    pre_specs = read_csv(OUT_DIR / "task1522_policy_specs_pre_replacement.csv")
    final_specs = read_csv(OUT_DIR / "task1524_policy_specs_final.csv")
    exits = read_csv(OUT_DIR / "task1523_exit_decision_panel.csv")
    metrics = read_csv(OUT_DIR / "task1525_replay_metrics.csv")
    scheduled_metrics = read_csv(OUT_DIR / "task1526_scheduled_only_metrics.csv")
    delta_summary = read_csv(OUT_DIR / "task1527_l5_delta_summary.csv")
    delta_audit = read_csv(OUT_DIR / "task1527_l5_delta_audit.csv")
    gate = read_csv(OUT_DIR / "task1536_acceptance_gate.csv")

    if len(states) != 3100:
        errors.append(f"expected 3100 thesis state rows, found {len(states)}")
    state_names = {row["thesis_state"] for row in states}
    for required in {"active_thesis", "confirmation_wait", "invalidated", "source_gap_watch"}:
        if required not in state_names:
            errors.append(f"missing thesis state: {required}")
    rule_names = {row["rule_name"] for row in rules}
    for required in {"thesis_state_machine", "top3_top5_entry_only", "entry_gate", "hold_extension", "exit_separation", "narrow_replacement_hurdle", "cap_only_sizing", "delta_validation"}:
        if required not in rule_names:
            errors.append(f"missing preregistered rule: {required}")
    for row in states + pre_specs + final_specs + exits:
        if row.get("assignment_uses_future_outcome") != "0":
            errors.append(f"future assignment flag nonzero: {row.get('trade_spec_id') or row.get('state_row_id')}")
    if len(metrics) != 2 or len(scheduled_metrics) != 2 or len(delta_summary) != 2:
        errors.append("expected two top3/top5 metric rows")
    spec_counts: dict[str, int] = {}
    for row in final_specs:
        spec_counts[row["policy_variant_id"]] = spec_counts.get(row["policy_variant_id"], 0) + 1
        if row["policy_variant_id"].endswith("top10_v1"):
            errors.append("top10 policy should not be replayed in L5 operating brain")
        if float(row["position_size_cap_multiplier"]) > 1.0:
            errors.append(f"position size exceeds cap-only rule: {row['trade_spec_id']}")
    expected_counts = {"l5_operating_top3_v1": 153, "l5_operating_top5_v1": 192}
    if spec_counts != expected_counts:
        errors.append(f"policy spec counts mismatch: {spec_counts}")

    for row in delta_summary:
        if row["outcome_used_for_assignment"] != "0" or row["outcome_used_for_audit_only"] != "1":
            errors.append(f"delta summary audit flag misuse: {row['policy_variant_id']}")
        if row["l5_delta_positive"] != "1":
            errors.append(f"L5 delta did not improve scheduled-only: {row['policy_variant_id']}")
        if row["mdd_improved"] != "1":
            errors.append(f"MDD did not improve scheduled-only: {row['policy_variant_id']}")
    for row in delta_audit:
        if row["outcome_used_for_assignment"] != "0" or row["outcome_used_for_audit_only"] != "1":
            errors.append(f"delta audit flag misuse: {row['delta_id']}")
    for row in metrics:
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append(f"strategy overclaim: {row['policy_variant_id']}")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append(f"deployment overclaim: {row['policy_variant_id']}")
        if row["real_capital"] != "FORBIDDEN":
            errors.append(f"real capital overclaim: {row['policy_variant_id']}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")
    if gate[0]["best_l5_delta_positive"] != "1" or gate[0]["best_mdd_improved"] != "1":
        errors.append("acceptance gate did not record L5 improvement")
    report_text = REPORT.read_text(encoding="utf-8")
    if "L5를 단순 exit 규칙에서 포지션 운영 뇌로 바꿨다." not in report_text:
        errors.append("report missing plain-language implementation summary")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1518_1537_ERROR] {error}")
        return 1
    print("[TASK1518_1537_OK] L5 position operating brain artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
