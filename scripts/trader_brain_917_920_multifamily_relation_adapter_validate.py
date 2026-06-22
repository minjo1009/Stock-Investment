from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"

REQUIRED_FILES = [
    "task917_source_family_attachment_manifest.csv",
    "task917_multifamily_l1_evidence.csv",
    "task918_multifamily_l2_primitives.csv",
    "task918_multifamily_l2_meanings.csv",
    "task919_relation_edges_9primitive.csv",
    "task919_relation_primitive_catalog.csv",
    "task919_l4_candidate_bundles_contradiction.csv",
    "task919_l5_dry_decisions.csv",
    "task920_adapter_input_schema.csv",
    "task920_adapter_input_design_rows.csv",
    "task917_920_summary.json",
    "artifact_manifest.csv",
]

SOURCE_FAMILIES = {
    "company_filings_ir",
    "earnings_guidance",
    "macro_policy_official",
    "supply_chain_customer_capex_cross_read",
    "positioning_liquidity_volatility",
    "sector_specialist_official_docs",
}

RELATION_PRIMITIVES = {
    "reinforces",
    "weakens",
    "invalidates",
    "conditions",
    "sequences",
    "explains",
    "contradicts",
    "source_gap_for",
    "noise_for",
}

FORBIDDEN_COLUMNS = {"future_return", "realized_return", "pnl", "rank", "score", "position_size"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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

    family_manifest = rows(ART / "task917_source_family_attachment_manifest.csv")
    l1 = rows(ART / "task917_multifamily_l1_evidence.csv")
    primitives = rows(ART / "task918_multifamily_l2_primitives.csv")
    meanings = rows(ART / "task918_multifamily_l2_meanings.csv")
    relations = rows(ART / "task919_relation_edges_9primitive.csv")
    relation_catalog = rows(ART / "task919_relation_primitive_catalog.csv")
    candidates = rows(ART / "task919_l4_candidate_bundles_contradiction.csv")
    decisions = rows(ART / "task919_l5_dry_decisions.csv")
    adapter_schema = rows(ART / "task920_adapter_input_schema.csv")
    adapter_inputs = rows(ART / "task920_adapter_input_design_rows.csv")
    summary = json.loads((ART / "task917_920_summary.json").read_text(encoding="utf-8"))

    attached_families = {row["source_family"] for row in family_manifest if row["attachment_state"] == "attached"}
    if attached_families != SOURCE_FAMILIES:
        errors.append(f"all six source families must be attached, got {sorted(attached_families)}")
    if not l1 or not primitives or not meanings or not relations or not candidates or not decisions:
        errors.append("L1-L5 panels must be non-empty")
    if len(primitives) != len(l1):
        errors.append("primitive rows must match L1 rows")
    if len(meanings) != len(primitives):
        errors.append("meaning rows must match primitive rows")
    if len(adapter_inputs) != len(candidates):
        errors.append("adapter input design rows must match candidate rows")

    for name, panel in [
        ("l1", l1),
        ("primitive", primitives),
        ("meaning", meanings),
        ("relation", relations),
        ("candidate", candidates),
        ("decision", decisions),
        ("adapter", adapter_inputs),
    ]:
        forbidden = FORBIDDEN_COLUMNS & set(panel[0].keys())
        if forbidden:
            errors.append(f"{name} panel contains forbidden columns: {sorted(forbidden)}")

    l1_ids = {row["evidence_id"] for row in l1}
    primitive_ids = {row["primitive_fact_id"] for row in primitives}
    meaning_ids = {row["economic_meaning_id"] for row in meanings}
    relation_ids = {row["relation_edge_id"] for row in relations}
    candidate_ids = {row["candidate_bundle_id"] for row in candidates}
    decision_ids = {row["trader_decision_id"] for row in decisions}

    for row in l1:
        if row["source_family"] not in SOURCE_FAMILIES:
            errors.append("L1 row has unknown source family")
            break
        path = ROOT / row["raw_storage_path"]
        if not path.exists():
            errors.append(f"L1 raw path missing: {row['raw_storage_path']}")
            break
        if sha256(path) != row["raw_source_hash"]:
            errors.append(f"L1 hash mismatch: {row['raw_storage_path']}")
            break
        if not row["source_span_ref"] or not row["source_span_excerpt"]:
            errors.append("L1 row missing source span")
            break
        if parse_ts(row["available_to_brain_ts"]) < parse_ts(row["published_ts"]):
            errors.append("L1 available_to_brain_ts precedes published_ts")
            break

    for row in primitives:
        if row["evidence_id"] not in l1_ids:
            errors.append("primitive evidence FK missing")
            break
        if row["acceptance_state"] != "accepted_source_backed":
            errors.append("primitive must be source-backed")
            break

    for row in meanings:
        if row["primitive_fact_id"] not in primitive_ids:
            errors.append("meaning primitive FK missing")
            break

    used_primitives = {row["relation_primitive"] for row in relations}
    catalog_primitives = {row["relation_primitive"] for row in relation_catalog}
    if catalog_primitives != RELATION_PRIMITIVES:
        errors.append("relation primitive catalog must contain exactly the nine approved primitives")
    if any(row["absence_policy"] != "do_not_synthesize_edge_without_source_backed_trigger" for row in relation_catalog):
        errors.append("relation primitive catalog must forbid synthetic edges")
    if not used_primitives <= RELATION_PRIMITIVES:
        errors.append(f"unexpected relation primitive: {sorted(used_primitives - RELATION_PRIMITIVES)}")
    required_used = {"reinforces", "weakens", "conditions", "explains", "source_gap_for", "noise_for"}
    if not required_used <= used_primitives:
        errors.append(f"missing required relation primitive coverage: {sorted(required_used - used_primitives)}")
    for row in relations:
        if parse_ts(row["edge_asof_ts"]) > parse_ts(row["decision_asof_ts"]):
            errors.append("relation edge_asof exceeds decision_asof")
            break
        for evidence_id in [value for value in row["edge_evidence_ids"].split(";") if value]:
            if evidence_id not in l1_ids:
                errors.append("relation evidence FK missing")
                break
        for meaning_id in [value for value in row["source_meaning_ids"].split(";") if value]:
            if meaning_id not in meaning_ids:
                errors.append("relation meaning FK missing")
                break
        if errors:
            break

    if not any(row["contradiction_state"] == "contradiction_present" for row in candidates):
        errors.append("L4 must contain at least one contradiction-present candidate")
    for row in candidates:
        relation_refs = []
        for field in ["supporting_relation_ids", "contradicting_relation_ids", "invalidation_relation_ids", "source_gap_relation_ids"]:
            relation_refs.extend(value for value in row[field].split(";") if value)
        if any(value not in relation_ids for value in relation_refs):
            errors.append("candidate relation FK missing")
            break
        if row["adapter_eligible"] != "0":
            errors.append("candidate must not be adapter eligible")
            break
        if not row["invalidation_conditions"] or not row["weakest_layer"]:
            errors.append("candidate missing invalidation or weakest layer")
            break

    for row in decisions:
        if row["candidate_bundle_id"] not in candidate_ids:
            errors.append("decision candidate FK missing")
            break
        if row["trade_spec_allowed"] != "0" or row["diagnostic_replay_allowed"] != "0":
            errors.append("dry decision must keep trade/replay flags zero")
            break

    schema_by_field = {row["field_name"]: row for row in adapter_schema}
    for field in ["side", "entry_rule", "exit_rule", "position_size_rule", "tradable_after_ts", "market_data_manifest_id", "cost_config_id", "slippage_config_id"]:
        row = schema_by_field.get(field)
        if not row:
            errors.append(f"adapter schema missing {field}")
            break
        if row["required_for_adapter"] != "1" or row["allowed_now"] != "0" or row["blocks_backtest_if_missing"] != "1":
            errors.append(f"adapter schema field {field} must be required, disallowed now, and blocking")
            break

    for row in adapter_inputs:
        if row["candidate_bundle_id"] not in candidate_ids or row["trader_decision_id"] not in decision_ids:
            errors.append("adapter input FK missing")
            break
        if row["ready_for_backtest"] != "0":
            errors.append("adapter design rows must not be backtest-ready")
            break
        for field in ["side", "entry_rule", "exit_rule", "position_size_rule", "tradable_after_ts"]:
            if row[field]:
                errors.append(f"adapter design row must leave {field} empty")
                break
        if errors:
            break

    expected = {
        "source_families_attached": len(SOURCE_FAMILIES),
        "l1_evidence_rows": len(l1),
        "primitive_fact_rows": len(primitives),
        "economic_meaning_rows": len(meanings),
        "relation_edge_rows": len(relations),
        "relation_primitive_catalog_rows": len(relation_catalog),
        "candidate_bundle_rows": len(candidates),
        "dry_decision_rows": len(decisions),
        "adapter_schema_rows": len(adapter_schema),
        "adapter_input_rows": len(adapter_inputs),
        "ready_for_backtest_rows": 0,
    }
    for key, expected_value in expected.items():
        if summary.get(key) != expected_value:
            errors.append(f"summary {key} mismatch")
            break
    if summary.get("diagnostic_replay_status") != "not_run_adapter_design_only":
        errors.append("summary must keep replay not run")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment readiness must remain diagnostic only")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital must remain forbidden")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_917_920_MULTIFAMILY_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_917_920_MULTIFAMILY_OK] artifacts validated")


if __name__ == "__main__":
    main()
