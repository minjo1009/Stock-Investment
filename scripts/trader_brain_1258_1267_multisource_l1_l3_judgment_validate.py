from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1258_1267_multisource_l1_l3_judgment"
REPORT = ROOT / "docs/reports/task_1258_1267_multisource_l1_l3_judgment"

REQUIRED_FILES = [
    "task1258_expert_multisource_rulebook.csv",
    "task1259_source_family_contracts.csv",
    "task1260_l1_multisource_packets.csv",
    "task1261_policy_catalyst_shadow_panel.csv",
    "task1262_l2_multisource_interpretation.csv",
    "task1263_l3_multisource_relation_edges.csv",
    "task1264_source_gap_acquisition_queue.csv",
    "task1265_expert_audit_upgrade.csv",
    "task1266_validation_gate.csv",
    "task1267_closeout.csv",
    "task1267_closeout.json",
    "artifact_manifest.csv",
]

REQUIRED_FAMILIES = {
    "sec_survival",
    "ir_ceo_earnings_call",
    "contract_orders_customer",
    "analyst_institution",
    "policy_news_catalyst",
    "market_price_volume",
}


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1258_1267_multisource_l1_l3_judgment.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1258_1267_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    rulebook = rows("task1258_expert_multisource_rulebook.csv")
    contracts = rows("task1259_source_family_contracts.csv")
    l1 = rows("task1260_l1_multisource_packets.csv")
    policy = rows("task1261_policy_catalyst_shadow_panel.csv")
    l2 = rows("task1262_l2_multisource_interpretation.csv")
    l3 = rows("task1263_l3_multisource_relation_edges.csv")
    gaps = rows("task1264_source_gap_acquisition_queue.csv")
    gate = rows("task1266_validation_gate.csv")
    closeout = rows("task1267_closeout.csv")
    closeout_json = json.loads((ART / "task1267_closeout.json").read_text(encoding="utf-8"))

    if {row["source_family"] for row in rulebook} != REQUIRED_FAMILIES:
        errors.append("rulebook must cover all six source families")
    if {row["source_family"] for row in contracts} != REQUIRED_FAMILIES:
        errors.append("contracts must cover all six source families")
    if len(l1) != 310 or len(l2) != 310:
        errors.append("L1 and L2 must cover 310 slot5 selections")
    if len(l3) != 310 * 6:
        errors.append("L3 must contain six source-family edges per selection")
    if len(policy) == 0:
        errors.append("policy shadow panel must not be empty")
    if len(gaps) < 4:
        errors.append("gap acquisition queue must cover missing non-SEC families")
    if len(gate) != 1 or len(closeout) != 1:
        errors.append("gate and closeout must each contain one row")

    if any(row["missing_is_negative"] != "0" for row in l1):
        errors.append("missing source families must not become negative evidence")
    if any(row["selection_use_allowed"] != "0" or row["replay_use_allowed"] != "0" for row in l1 + l2 + l3 + policy):
        errors.append("multisource judgment layer must remain no-selection/no-replay")
    if any(row["assignment_uses_future_outcome"] != "0" for row in l2 + l3):
        errors.append("L2/L3 must not use outcomes for assignment")
    if not any(row["source_family"] == "ir_ceo_earnings_call" and row["relation_primitive"] == "caps_confidence" for row in l3):
        errors.append("IR/CEO gap must cap confidence")
    if not any(row["source_family"] == "policy_news_catalyst" for row in l3):
        errors.append("policy catalyst edges missing")
    if not any(row["source_family"] == "market_price_volume" and row["relation_primitive"] in {"confirms", "conditions", "contradicts"} for row in l3):
        errors.append("market acceptance edges missing")
    for row in [gate[0], closeout[0], closeout_json]:
        if str(row.get("replay_executed")) != "0":
            errors.append("replay must not be executed")
        if str(row.get("selection_promoted")) != "0":
            errors.append("selection must not be promoted")
        if row.get("strategy_acceptance") != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row.get("real_capital") != "FORBIDDEN":
            errors.append("real capital changed")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1258_1267_MULTISOURCE_L1_L3_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1258_1267_MULTISOURCE_L1_L3_OK] artifacts validated")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
