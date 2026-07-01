from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


LAYER_OUTCOME_UNITS = {
    "L0": {
        "failed_shard_count",
        "incomplete_backfill_units",
        "unclassified_l0_terminal_status_count",
        "stale_realtime_collector_count",
        "raw_integrity_error_count",
        "collector_config_gap_count",
    },
    "L1": {
        "unmapped_entity_count",
        "unclassified_article_count",
        "l1_blocked_packet_count",
        "stale_l1_packet_count",
        "missing_l1_materialization_count",
    },
    "L2": {
        "blocked_feature_count",
        "missing_materialization_count",
        "unsupported_feature_source_count",
        "feature_schema_gap_count",
        "l1_l2_compatibility_gap_count",
    },
    "L3": {
        "unsupported_relation_count",
        "low_confidence_relation_count",
        "missing_relation_evidence_count",
        "relation_graph_quality_gap_count",
        "orphan_relation_node_count",
    },
    "L4": {
        "diagnostic_draft_blocker_count",
        "missing_thesis_evidence_count",
        "mixed_context_unresolved_count",
        "institutional_quality_gap_count",
        "thesis_bundle_blocker_count",
    },
}


def load_contract(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def validate_layer_outcome_unit(contract: dict[str, Any], failures: list[str], passes: list[str]) -> None:
    layer = detect_layer(contract)
    if not layer:
        passes.append("layer outcome unit check not applicable")
        return

    outcome_name = ((contract.get("outcome_unit") or {}).get("name") or "").strip()
    allowed = LAYER_OUTCOME_UNITS[layer]
    if outcome_name not in allowed:
        failures.append(f"{layer} outcome_unit.name is not allowed: {outcome_name}")
    else:
        passes.append(f"{layer} outcome_unit allowed: {outcome_name}")

    commands = ((contract.get("measurement_method") or {}).get("commands") or [])
    evidence = ((contract.get("evidence_artifacts") or {}).get("required") or [])
    if not commands:
        failures.append(f"{layer} outcome unit requires measurement_method.commands")
    if not evidence:
        failures.append(f"{layer} outcome unit requires evidence_artifacts.required")

    if (contract.get("progress_claim_policy") or {}).get("actual_underlying_progress") is True:
        baseline = contract.get("baseline") or {}
        after = contract.get("after") or {}
        if baseline.get("value") is None or after.get("value") is None:
            failures.append(f"{layer} actual progress requires baseline.value and after.value")


def validate_contract_path(path: str | Path) -> dict[str, Any]:
    passes: list[str] = []
    failures: list[str] = []
    validate_layer_outcome_unit(load_contract(path), failures, passes)
    return {"status": "FAIL" if failures else "PASS", "passes": passes, "failures": failures}


def detect_layer(contract: dict[str, Any]) -> str | None:
    declared = (contract.get("layer_outcome_validation") or {}).get("layer")
    if declared:
        normalized = str(declared).upper()
        return normalized if normalized in LAYER_OUTCOME_UNITS else None

    domain = str(contract.get("domain") or "").upper()
    match = re.search(r"\bL([0-4])\b|LAYER[_ -]?([0-4])", domain)
    if not match:
        return None
    number = match.group(1) or match.group(2)
    return f"L{number}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate L0-L4 Prime outcome_unit names.")
    parser.add_argument("contracts", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    exit_code = 0
    for contract_path in args.contracts:
        validation = validate_contract_path(contract_path)
        if args.json:
            print(json.dumps({"path": contract_path, **validation}, ensure_ascii=False, indent=2))
        else:
            print(f"{validation['status']} {contract_path}")
            for failure in validation["failures"]:
                print(f"  FAIL: {failure}")
        if validation["status"] != "PASS":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
