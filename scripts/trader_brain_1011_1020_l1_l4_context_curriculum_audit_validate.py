from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1011_1020_l1_l4_context_curriculum_audit"

REQUIRED_FILES = [
    "task1011_l1_l4_source_context_manifest.csv",
    "task1012_l1_source_gap_audit.csv",
    "task1013_l2_economic_meaning_gap_audit.csv",
    "task1014_l3_relation_ontology_gap_audit.csv",
    "task1015_l4_candidate_bundle_gap_audit.csv",
    "task1016_macro_policy_theme_curriculum_map.csv",
    "task1017_l1_l4_upgrade_backlog.csv",
    "task1018_expert_feedback_synthesis.csv",
    "task1019_no_replay_gate.csv",
    "task1020_l1_l4_context_curriculum_closeout.csv",
    "task1011_1020_summary.csv",
    "task1011_1020_summary.json",
    "artifact_manifest.csv",
]
REQUIRED_DOMAINS = {
    "macro_economic",
    "policy_geopolitics",
    "semiconductor_theme",
    "ai_theme",
    "energy_power_theme",
    "space_theme",
    "cybersecurity_theme",
    "relation_ontology",
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

    sources = rows(ART / "task1011_l1_l4_source_context_manifest.csv")
    domains = {row["source_family"] for row in sources}
    if not REQUIRED_DOMAINS <= domains:
        errors.append("source manifest missing required domains")
    if sum(1 for row in sources if row["download_state"] == "downloaded") < 15:
        errors.append("too few downloaded source rows")
    for row in sources:
        if row["selection_use_allowed"] != "0" or row["replay_use_allowed"] != "0":
            errors.append("source curriculum cannot be used for selection or replay")
            break

    for name, layer in [
        ("task1012_l1_source_gap_audit.csv", "L1"),
        ("task1013_l2_economic_meaning_gap_audit.csv", "L2"),
        ("task1014_l3_relation_ontology_gap_audit.csv", "L3"),
        ("task1015_l4_candidate_bundle_gap_audit.csv", "L4"),
    ]:
        layer_rows = rows(ART / name)
        if len(layer_rows) < 3:
            errors.append(f"{layer} audit must have at least three gaps")
        if {row["layer"] for row in layer_rows} != {layer}:
            errors.append(f"{layer} audit has wrong layer labels")

    curriculum = rows(ART / "task1016_macro_policy_theme_curriculum_map.csv")
    if REQUIRED_DOMAINS - {row["domain"] for row in curriculum}:
        errors.append("curriculum map missing required domains")

    backlog = rows(ART / "task1017_l1_l4_upgrade_backlog.csv")
    if len(backlog) != 10:
        errors.append("backlog must contain 10 task directions")

    gate = rows(ART / "task1019_no_replay_gate.csv")
    closeout = rows(ART / "task1020_l1_l4_context_curriculum_closeout.csv")
    summary = json.loads((ART / "task1011_1020_summary.json").read_text(encoding="utf-8"))
    for label, gate_rows in [("gate", gate), ("closeout", closeout)]:
        if len(gate_rows) != 1:
            errors.append(f"{label} must have one row")
        else:
            row = gate_rows[0]
            if row["strategy_acceptance"] != "NOT_ACCEPTED":
                errors.append(f"{label} changed strategy acceptance")
            if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
                errors.append(f"{label} changed deployment readiness")
            if row["real_capital"] != "FORBIDDEN":
                errors.append(f"{label} changed real capital")
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
        print("[TRADER_BRAIN_1011_1020_L1_L4_CONTEXT_CURRICULUM_AUDIT_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1011_1020_L1_L4_CONTEXT_CURRICULUM_AUDIT_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
