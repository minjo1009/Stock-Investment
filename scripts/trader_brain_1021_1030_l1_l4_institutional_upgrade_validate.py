from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1021_1030_l1_l4_institutional_upgrade"

REQUIRED_FILES = [
    "task1021_institutional_source_catalog.csv",
    "task1022_source_authority_tier_contract.csv",
    "task1023_l1_source_family_contracts.csv",
    "task1024_l2_primitive_schema.csv",
    "task1025_l3_relation_mechanism_schema.csv",
    "task1026_l4_thesis_card_schema.csv",
    "task1027_theme_exposure_chain_templates.csv",
    "task1028_l1_l4_validator_contracts.csv",
    "task1029_next_task_backlog.csv",
    "task1030_no_replay_closeout.csv",
    "task1021_1030_summary.csv",
    "task1021_1030_summary.json",
    "artifact_manifest.csv",
]
REQUIRED_SOURCE_FAMILIES = {
    "macro_economic",
    "policy_geopolitics",
    "semiconductor_theme",
    "ai_theme",
    "energy_power_theme",
    "space_theme",
    "cybersecurity_theme",
    "relation_ontology",
}
REQUIRED_L2 = {
    "macro_release",
    "policy_lifecycle",
    "semiconductor_value_chain",
    "ai_infrastructure",
    "energy_power",
    "cybersecurity",
    "space",
}
REQUIRED_L3 = {
    "discount_rate",
    "demand_pull",
    "supply_constraint",
    "market_access",
    "capex_cycle",
    "cost_pressure",
    "security_risk",
    "contradiction",
}
REQUIRED_L4_FIELDS = {
    "variant_view",
    "consensus_view",
    "economic_driver",
    "denominator",
    "exposure_chain",
    "catalyst_window",
    "invalidation_path",
    "outcome_used_for_assignment_flag",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors

    catalog = rows(ART / "task1021_institutional_source_catalog.csv")
    if len(catalog) < 40:
        errors.append("institutional source catalog must have at least 40 rows")
    if sum(1 for row in catalog if row["download_state"].startswith("downloaded")) < 30:
        errors.append("institutional source catalog must have at least 30 downloaded rows")
    if not REQUIRED_SOURCE_FAMILIES <= {row["source_family"] for row in catalog}:
        errors.append("source catalog missing required families")
    for row in catalog:
        if row["selection_use_allowed"] != "0" or row["replay_use_allowed"] != "0":
            errors.append("source catalog cannot permit selection or replay use")
            break

    l1 = rows(ART / "task1023_l1_source_family_contracts.csv")
    if len(l1) < 5:
        errors.append("L1 source family contracts too thin")
    for row in l1:
        if "local_sha256" not in row["required_fields"]:
            errors.append("L1 contracts must require local_sha256")
            break

    l2 = rows(ART / "task1024_l2_primitive_schema.csv")
    if not REQUIRED_L2 <= {row["primitive_family"] for row in l2}:
        errors.append("L2 primitive schema missing required primitive families")
    for row in l2:
        if "future_return" not in row["forbidden_fields"] or "pnl" not in row["forbidden_fields"]:
            errors.append("L2 primitives must forbid outcome fields")
            break

    l3 = rows(ART / "task1025_l3_relation_mechanism_schema.csv")
    if not REQUIRED_L3 <= {row["mechanism"] for row in l3}:
        errors.append("L3 mechanism schema missing required mechanisms")
    for row in l3:
        if "confidence" not in row["required_fields"]:
            errors.append("L3 mechanisms must require confidence")
            break

    l4 = rows(ART / "task1026_l4_thesis_card_schema.csv")
    if not REQUIRED_L4_FIELDS <= {row["field"] for row in l4}:
        errors.append("L4 thesis card missing required fields")
    for row in l4:
        if row["required"] != "1":
            errors.append("all L4 thesis card fields must be required")
            break

    templates = rows(ART / "task1027_theme_exposure_chain_templates.csv")
    if len(templates) < 5:
        errors.append("theme exposure chain templates too thin")

    backlog = rows(ART / "task1029_next_task_backlog.csv")
    if len(backlog) != 10:
        errors.append("next task backlog must have 10 rows")
    if {row["blocked_replay_until_done"] for row in backlog} != {"1"}:
        errors.append("all next tasks must block replay until done")

    closeout = rows(ART / "task1030_no_replay_closeout.csv")
    summary = json.loads((ART / "task1021_1030_summary.json").read_text(encoding="utf-8"))
    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "0":
            errors.append("closeout must record no replay")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed real capital")
    if summary.get("replay_executed") != "0":
        errors.append("summary must record no replay")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary changed strategy acceptance")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary changed deployment readiness")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary changed real capital")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1021_1030_L1_L4_INSTITUTIONAL_UPGRADE_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1021_1030_L1_L4_INSTITUTIONAL_UPGRADE_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
