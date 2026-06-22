from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1211_1220_collapse_guard_development"
REPORT = ROOT / "docs/reports/task_1211_1220_collapse_guard_development"

REQUIRED_FILES = [
    "task1211_expert_roster.csv",
    "task1212_authoritative_source_catalog.csv",
    "task1213_collapse_tail_diagnostic_eval_only.csv",
    "task1214_l0_l3_survival_primitives.csv",
    "task1215_l3_relation_edges_design.csv",
    "task1216_l4_candidate_card_extensions.csv",
    "task1217_l5_trade_action_policy.csv",
    "task1218_leverage_handling_policy.csv",
    "task1219_implementation_backlog.csv",
    "task1220_collapse_guard_development_closeout.csv",
    "task1220_collapse_guard_development_closeout.json",
    "artifact_manifest.csv",
]


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
    if not (REPORT / "task_1211_1220_collapse_guard_development.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1211_1220_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    experts = rows("task1211_expert_roster.csv")
    sources = rows("task1212_authoritative_source_catalog.csv")
    cases = rows("task1213_collapse_tail_diagnostic_eval_only.csv")
    primitives = rows("task1214_l0_l3_survival_primitives.csv")
    edges = rows("task1215_l3_relation_edges_design.csv")
    l4 = rows("task1216_l4_candidate_card_extensions.csv")
    l5 = rows("task1217_l5_trade_action_policy.csv")
    leverage = rows("task1218_leverage_handling_policy.csv")
    backlog = rows("task1219_implementation_backlog.csv")
    closeout = rows("task1220_collapse_guard_development_closeout.csv")
    closeout_json = json.loads((ART / "task1220_collapse_guard_development_closeout.json").read_text(encoding="utf-8"))

    if len(experts) < 6:
        errors.append("expert roster must include at least six roles")
    if len(sources) < 10:
        errors.append("source catalog must include at least ten authoritative/reference rows")
    if sum(1 for row in sources if row["download_status"].startswith("downloaded")) < 6:
        errors.append("at least six source files must be downloaded")
    if len(cases) < 10:
        errors.append("collapse tail diagnostic must include meaningful evaluation-only cases")
    if any(row["outcome_used_for_assignment"] != "0" or row["diagnostic_only"] != "1" for row in cases):
        errors.append("collapse tail cases must be diagnostic-only and not assignment inputs")
    if not {"L0", "L1", "L2", "L3"}.issubset({row["layer"] for row in primitives}):
        errors.append("primitives must cover L0 L1 L2 L3")
    if not any(row["primitive_name"] == "leveraged_product_structure" for row in primitives):
        errors.append("leveraged products must be represented as a structure primitive")
    if not any(row["relation_primitive"] == "invalidates" for row in edges):
        errors.append("L3 edges must include source-backed invalidation")
    if not any(row["field_name"] == "product_sleeve" for row in l4):
        errors.append("L4 extensions must include product_sleeve")
    if not any(row["rule_name"] == "leveraged_product_sleeve" for row in l5):
        errors.append("L5 policy must include leveraged product sleeve handling")
    if not any(row["policy_clause"] == "allowed" for row in leverage):
        errors.append("leverage policy must explicitly allow leverage")
    if any(row["selection_promoted"] != "0" for row in l4 + l5):
        errors.append("L4/L5 design rows must not promote selection")
    if len(backlog) < 7:
        errors.append("implementation backlog must include follow-up tasks")

    if len(closeout) != 1:
        errors.append("closeout must contain one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("collapse guard development must not execute replay or promote selection")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("real capital changed")
    if closeout_json.get("replay_executed") != "0":
        errors.append("json closeout must record no replay")
    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json closeout changed strategy acceptance")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1211_1220_COLLAPSE_GUARD_DEVELOPMENT_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1211_1220_COLLAPSE_GUARD_DEVELOPMENT_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
