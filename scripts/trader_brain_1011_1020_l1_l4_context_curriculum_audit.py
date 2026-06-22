from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/research/l1_l4_context_curriculum"
OUT_DIR = ROOT / "data/artifacts/task_1011_1020_l1_l4_context_curriculum_audit"
SOURCE_MANIFEST = RAW_DIR / "download_manifest.csv"

AUTHORITY = "RESEARCH_ONLY_L1_L4_CONTEXT_CURRICULUM_AUDIT_NO_REPLAY"
STATUS = {
    "strategy_acceptance": "NOT_ACCEPTED",
    "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def layer_for_family(family: str) -> str:
    if family in {"macro_economic", "policy_geopolitics", "relation_ontology"}:
        return "L1-L3"
    return "L1-L4"


def build() -> dict[str, object]:
    sources = read_csv(SOURCE_MANIFEST)
    downloaded = [row for row in sources if row["download_state"] == "downloaded"]
    source_rows = []
    for row in sources:
        source_rows.append(
            {
                **row,
                "intended_brain_layers": layer_for_family(row["source_family"]),
                "use_mode": "learning_context_and_source_contract_design_only",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )

    l1_gap_rows = [
        {
            "layer": "L1",
            "gap_id": "L1-G01",
            "gap": "source_family_rows_exist_but_institutional_source_corpus_is_not_systematic",
            "evidence": "Task917 attached six families from bounded existing project sources; Task1011 corpus adds official macro policy and theme materials",
            "severity": "high",
            "repair_requirement": "create source-family-specific raw source contracts with published_ts received_ts vintage_ts source_url local_hash and issuer authority",
            "blocked_from_replay_claim": "1",
            "authority": AUTHORITY,
        },
        {
            "layer": "L1",
            "gap_id": "L1-G02",
            "gap": "macro_and_policy_release_calendar_not_modeled_as_source_time_objects",
            "evidence": "FOMC Federal Register Congress and BEA/BLS style sources require release/vintage semantics before interpretation",
            "severity": "high",
            "repair_requirement": "add event/release calendar object and vintage-aware source admission ledger",
            "blocked_from_replay_claim": "1",
            "authority": AUTHORITY,
        },
        {
            "layer": "L1",
            "gap_id": "L1-G03",
            "gap": "theme_documents_are_not_yet_mapped_to_symbols_supply_chain_nodes_or revenue_denominators",
            "evidence": "SIA/OECD/Stanford/EIA/NASA/CISA documents are collected but not admitted into symbol-level L1 evidence",
            "severity": "high",
            "repair_requirement": "build theme taxonomy to symbol exposure map before generating L2 primitives",
            "blocked_from_replay_claim": "1",
            "authority": AUTHORITY,
        },
    ]
    l2_gap_rows = [
        {
            "layer": "L2",
            "gap_id": "L2-G01",
            "gap": "economic_meanings_are_too_generic_for_macro_policy_and_theme_mechanisms",
            "evidence": "Current L2 maps source rows to meaning rows but does not decompose level trend surprise revision duration denominator or pass-through",
            "severity": "high",
            "repair_requirement": "add primitive classes: level trend surprise revision policy_stance capex_constraint demand_pull supply_constraint margin_pressure",
            "authority": AUTHORITY,
        },
        {
            "layer": "L2",
            "gap_id": "L2-G02",
            "gap": "political_events_lack_probability_timing_and_jurisdiction_fields",
            "evidence": "Federal Register Congress BIS OFAC sources need proposal/final/effective/enforcement states",
            "severity": "high",
            "repair_requirement": "add policy lifecycle primitive: proposed final effective stayed revoked enforcement_scope affected_entities",
            "authority": AUTHORITY,
        },
        {
            "layer": "L2",
            "gap_id": "L2-G03",
            "gap": "theme_facts_do_not_preserve_mechanism_denominators",
            "evidence": "AI energy demand semiconductor value chain space economic impact and KEV vulnerability evidence require denominators",
            "severity": "medium",
            "repair_requirement": "require denominator fields: addressable_market capex_base installed_base shipment_units electricity_load launch_cadence vulnerability_count",
            "authority": AUTHORITY,
        },
    ]
    l3_gap_rows = [
        {
            "layer": "L3",
            "gap_id": "L3-G01",
            "gap": "nine_relation_primitives_are_too_flat_for_cross_domain_causality",
            "evidence": "reinforces/weakens/conditions/explains are useful but do not encode mechanism type or transmission path",
            "severity": "high",
            "repair_requirement": "keep nine primitives but add relation_modifier fields: mechanism transmission_channel lag confidence denominator and affected_exposure",
            "authority": AUTHORITY,
        },
        {
            "layer": "L3",
            "gap_id": "L3-G02",
            "gap": "macro_policy_theme_edges_are_not_separated_by causal_direction",
            "evidence": "rates export controls AI capex power constraints cyber risk and space funding need directional edges",
            "severity": "high",
            "repair_requirement": "add typed edge templates for discount_rate demand_pull supply_constraint market_access capex_cycle regulatory_blocker security_risk",
            "authority": AUTHORITY,
        },
        {
            "layer": "L3",
            "gap_id": "L3-G03",
            "gap": "source_conflict_and_time_decay_are_under-modeled",
            "evidence": "Task917 records contradiction but not source age decay confidence decay or policy effective-date expiry",
            "severity": "medium",
            "repair_requirement": "add edge_valid_from edge_valid_until decay_half_life contradiction_basis and stale_reason fields",
            "authority": AUTHORITY,
        },
    ]
    l4_gap_rows = [
        {
            "layer": "L4",
            "gap_id": "L4-G01",
            "gap": "candidate_bundles_are_not_yet_thesis_specific_enough",
            "evidence": "Candidate bundles reflect source and relation counts but not explicit variant perception, consensus gap, or thesis unit economics",
            "severity": "high",
            "repair_requirement": "require thesis card fields: variant_view consensus_view economic_driver denominator catalyst_window invalidation_path",
            "authority": AUTHORITY,
        },
        {
            "layer": "L4",
            "gap_id": "L4-G02",
            "gap": "cross_read_chains_do_not_force_theme_to_symbol_mapping",
            "evidence": "AI demand can affect semis power cooling cloud cybersecurity but L4 needs exposure chain before candidate creation",
            "severity": "high",
            "repair_requirement": "add exposure_chain: macro_or_policy_event -> theme_mechanism -> sector_node -> symbol_revenue_or_cost_exposure",
            "authority": AUTHORITY,
        },
        {
            "layer": "L4",
            "gap_id": "L4-G03",
            "gap": "bundle_readiness_is_too_close_to_source_availability_not_trade_quality",
            "evidence": "More sources do not guarantee better candidate quality; bundle must show mechanism completeness and contradiction coverage",
            "severity": "medium",
            "repair_requirement": "add L4 readiness tiers: source_complete mechanism_complete exposure_complete contradiction_reviewed catalyst_time_validated",
            "authority": AUTHORITY,
        },
    ]

    curriculum_rows = [
        {"domain": "macro_economic", "primary_sources": "BEA_NIPA;BLS_CPI;FRED_ALFRED;FederalReserve_FOMC", "must_teach": "release_vintage_revision_surprise_level_trend_rate_path", "required_layer_upgrade": "L1_vintage_calendar;L2_macro_primitive;L3_discount_rate_and_growth_edges", "authority": AUTHORITY},
        {"domain": "policy_geopolitics", "primary_sources": "FederalRegister;CongressAPI;BIS;OFAC", "must_teach": "proposal_final_rule_effective_date_jurisdiction_entity_scope_market_access", "required_layer_upgrade": "L1_policy_lifecycle;L2_policy_state;L3_regulatory_blocker_edges", "authority": AUTHORITY},
        {"domain": "semiconductor_theme", "primary_sources": "SIA;OECD;CHIPS_NIST;BIS", "must_teach": "value_chain_bottleneck_equipment_materials_foundry_export_control_customer_capex", "required_layer_upgrade": "L2_supply_chain_primitive;L3_bottleneck_and_market_access_edges;L4_symbol_exposure_chain", "authority": AUTHORITY},
        {"domain": "ai_theme", "primary_sources": "NIST_AI_RMF;Stanford_AI_Index", "must_teach": "capability_adoption_capex_risk_governance_compute_demand", "required_layer_upgrade": "L2_ai_capex_and_adoption_primitive;L3_compute_power_cloud_semis_edges", "authority": AUTHORITY},
        {"domain": "energy_power_theme", "primary_sources": "EIA_AEO;EIA_data_center_energy", "must_teach": "electricity_load_power_price_grid_constraint_generation_mix", "required_layer_upgrade": "L2_power_load_primitive;L3_ai_to_power_constraint_edges;L4_utility_and_datacenter_exposure", "authority": AUTHORITY},
        {"domain": "space_theme", "primary_sources": "NASA_economic_impact;BEA_space_economy", "must_teach": "launch_cadence_contract_backlog_budget_dependency_supply_chain", "required_layer_upgrade": "L2_space_activity_primitive;L3_budget_and_launch_capacity_edges", "authority": AUTHORITY},
        {"domain": "cybersecurity_theme", "primary_sources": "CISA_KEV;CISA_catalog", "must_teach": "exploited_vulnerability_vendor_product_due_date_remediation_pressure", "required_layer_upgrade": "L2_vulnerability_primitive;L3_security_risk_and_vendor_exposure_edges", "authority": AUTHORITY},
        {"domain": "relation_ontology", "primary_sources": "W3C_PROV;W3C_Time", "must_teach": "provenance_entity_activity_agent_valid_time_interval", "required_layer_upgrade": "L1_provenance_contract;L3_temporal_relation_contract", "authority": AUTHORITY},
    ]

    backlog_rows = [
        {"priority": 1, "task_direction": "L1 authoritative source admission contracts", "description": "convert downloaded corpus into source-family contracts with timestamps, hashes, issuer authority, and update cadence", "done_condition": "every source family has admission schema and validator", "authority": AUTHORITY},
        {"priority": 2, "task_direction": "Macro release and vintage calendar", "description": "model BEA/BLS/Fed/FRED/ALFRED releases with vintage and revision semantics", "done_condition": "macro primitives cannot be created without release_ts and vintage_ts", "authority": AUTHORITY},
        {"priority": 3, "task_direction": "Policy lifecycle primitives", "description": "model Federal Register/Congress/BIS/OFAC as proposal/final/effective/enforced/revoked states", "done_condition": "policy L2 rows include lifecycle_state affected_entities and effective window", "authority": AUTHORITY},
        {"priority": 4, "task_direction": "Theme exposure taxonomy", "description": "map AI semis energy cyber space documents to theme nodes sector nodes and symbol exposure", "done_condition": "L4 bundles include explicit exposure_chain", "authority": AUTHORITY},
        {"priority": 5, "task_direction": "Relation mechanism modifiers", "description": "keep nine primitives but add mechanism, channel, lag, denominator, confidence, valid_until", "done_condition": "L3 edges can distinguish discount_rate, supply_constraint, demand_pull, market_access, capex_cycle", "authority": AUTHORITY},
        {"priority": 6, "task_direction": "Candidate thesis card upgrade", "description": "force variant_view, consensus_view, economic_driver, denominator, catalyst_window, invalidation_path", "done_condition": "L4 candidate is blocked if any core thesis card field is missing", "authority": AUTHORITY},
        {"priority": 7, "task_direction": "Cross-read chain validator", "description": "validate macro/policy/theme -> symbol chain before candidate creation", "done_condition": "no L4 bundle without source->mechanism->exposure->symbol path", "authority": AUTHORITY},
        {"priority": 8, "task_direction": "Contradiction and uncertainty upgrade", "description": "separate missing source, conflicting source, stale source, and true invalidation", "done_condition": "L4 contradiction_state no longer collapses uncertainty into weakness", "authority": AUTHORITY},
        {"priority": 9, "task_direction": "Learning corpus refresh manifest", "description": "formalize which corpus sources are official, industry, academic, or auxiliary", "done_condition": "downloaded/failed state and source authority tier are tracked", "authority": AUTHORITY},
        {"priority": 10, "task_direction": "No replay until L1-L4 contracts pass", "description": "block another policy replay until source contracts and relation mechanism upgrades are implemented", "done_condition": "Task1020 no-go remains active until L1-L4 validators exist", "authority": AUTHORITY},
    ]

    expert_rows = [
        {"reviewer_role": "macro_economist", "feedback": "L1-L4 must understand release timing, revisions, surprises, and rate-path transmission; raw macro values alone are insufficient", "priority": "high", "authority": AUTHORITY},
        {"reviewer_role": "policy_geopolitics_specialist", "feedback": "policy sources need lifecycle state and affected-entity scope; proposed rules and final effective rules cannot be treated the same", "priority": "high", "authority": AUTHORITY},
        {"reviewer_role": "semiconductor_specialist", "feedback": "semiconductor thesis must map value-chain segment, bottleneck, export-control exposure, and customer capex; generic sector labels are too weak", "priority": "high", "authority": AUTHORITY},
        {"reviewer_role": "ai_infrastructure_specialist", "feedback": "AI theme must connect model demand to compute, data center power, cloud capex, networking, cooling, and semis rather than AI as a single bucket", "priority": "high", "authority": AUTHORITY},
        {"reviewer_role": "relation_graph_engineer", "feedback": "the nine primitives should remain stable but need typed mechanism modifiers and valid-time semantics", "priority": "high", "authority": AUTHORITY},
        {"reviewer_role": "portfolio_pm", "feedback": "L4 must produce tradeable thesis cards, not just evidence aggregates; variant perception and invalidation path are mandatory", "priority": "high", "authority": AUTHORITY},
    ]

    no_go = {
        "task_id": "Task1011-1020",
        "verdict": "l1_l4_context_curriculum_audit_complete_no_replay",
        "source_rows": len(sources),
        "downloaded_source_rows": len(downloaded),
        "failed_source_rows": len(sources) - len(downloaded),
        "l1_gap_count": len(l1_gap_rows),
        "l2_gap_count": len(l2_gap_rows),
        "l3_gap_count": len(l3_gap_rows),
        "l4_gap_count": len(l4_gap_rows),
        "next_action": "implement_L1_L4_source_contracts_relation_mechanism_and_candidate_thesis_card_before_another_replay",
        **STATUS,
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task1011_l1_l4_source_context_manifest.csv", source_rows, [
        "source_family", "source_name", "url", "local_path", "download_state", "size_bytes", "sha256",
        "intended_brain_layers", "use_mode", "selection_use_allowed", "replay_use_allowed", "authority",
    ])
    write_csv(OUT_DIR / "task1012_l1_source_gap_audit.csv", l1_gap_rows, ["layer", "gap_id", "gap", "evidence", "severity", "repair_requirement", "blocked_from_replay_claim", "authority"])
    write_csv(OUT_DIR / "task1013_l2_economic_meaning_gap_audit.csv", l2_gap_rows, ["layer", "gap_id", "gap", "evidence", "severity", "repair_requirement", "authority"])
    write_csv(OUT_DIR / "task1014_l3_relation_ontology_gap_audit.csv", l3_gap_rows, ["layer", "gap_id", "gap", "evidence", "severity", "repair_requirement", "authority"])
    write_csv(OUT_DIR / "task1015_l4_candidate_bundle_gap_audit.csv", l4_gap_rows, ["layer", "gap_id", "gap", "evidence", "severity", "repair_requirement", "authority"])
    write_csv(OUT_DIR / "task1016_macro_policy_theme_curriculum_map.csv", curriculum_rows, ["domain", "primary_sources", "must_teach", "required_layer_upgrade", "authority"])
    write_csv(OUT_DIR / "task1017_l1_l4_upgrade_backlog.csv", backlog_rows, ["priority", "task_direction", "description", "done_condition", "authority"])
    write_csv(OUT_DIR / "task1018_expert_feedback_synthesis.csv", expert_rows, ["reviewer_role", "feedback", "priority", "authority"])
    write_csv(OUT_DIR / "task1019_no_replay_gate.csv", [no_go], list(no_go.keys()))
    write_csv(OUT_DIR / "task1020_l1_l4_context_curriculum_closeout.csv", [no_go], list(no_go.keys()))
    write_csv(OUT_DIR / "task1011_1020_summary.csv", [no_go], list(no_go.keys()))
    (OUT_DIR / "task1011_1020_summary.json").write_text(json.dumps(no_go, indent=2), encoding="utf-8")
    return no_go


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_1011_1020_L1_L4_CONTEXT_CURRICULUM_AUDIT_OK] "
        f"sources={summary['source_rows']} downloaded={summary['downloaded_source_rows']} "
        f"gaps={summary['l1_gap_count'] + summary['l2_gap_count'] + summary['l3_gap_count'] + summary['l4_gap_count']} replay=0"
    )


if __name__ == "__main__":
    main()
