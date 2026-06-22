from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/research/l1_l4_institutional_upgrade"
PREV_MANIFEST = ROOT / "data/raw/research/l1_l4_context_curriculum/download_manifest.csv"
OUT_DIR = ROOT / "data/artifacts/task_1021_1030_l1_l4_institutional_upgrade"

AUTHORITY = "RESEARCH_ONLY_L1_L4_INSTITUTIONAL_UPGRADE_NO_REPLAY"
STATUS = {
    "strategy_acceptance": "NOT_ACCEPTED",
    "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
}

NEW_SOURCES = [
    ("macro_economic", "official", "bea_developer_docs.html", "https://www.bea.gov/resources/for-developers"),
    ("macro_economic", "official", "bls_api_features.html", "https://www.bls.gov/bls/api_features.htm"),
    ("macro_economic", "official", "bls_api_getting_started.html", "https://www.bls.gov/developers/home.htm"),
    ("macro_economic", "official", "bls_api_signature_v2.html", "https://www.bls.gov/developers/api_signature_v2.htm"),
    ("macro_economic", "official", "census_available_apis.html", "https://www.census.gov/data/developers/data-sets.html"),
    ("macro_economic", "official", "census_economic_api.html", "https://www.census.gov/programs-surveys/economic-census/data/api.html"),
    ("macro_economic", "official", "eia_api_documentation.html", "https://www.eia.gov/opendata/documentation.php"),
    ("macro_economic", "official", "eia_open_data.html", "https://www.eia.gov/opendata/"),
    ("macro_economic", "official", "treasury_fiscaldata_api.html", "https://fiscaldata.treasury.gov/api-documentation/"),
    ("policy_geopolitics", "official", "chips_nist_home.html", "https://www.nist.gov/chips"),
    ("policy_geopolitics", "official", "commerce_bis_home.html", "https://www.commerce.gov/bureaus-and-offices/bis"),
    ("policy_geopolitics", "official", "defense_budget_materials.html", "https://comptroller.defense.gov/Budget-Materials/"),
    ("policy_geopolitics", "official", "sec_edgar_api_docs.html", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces"),
    ("semiconductor_theme", "official", "chips_research_development.html", "https://www.nist.gov/chips/research-and-development-programs"),
    ("semiconductor_theme", "official", "chips_manufacturing.html", "https://www.nist.gov/chips/chips-incentives-program"),
    ("ai_theme", "official", "nist_ai_home.html", "https://www.nist.gov/artificial-intelligence"),
    ("ai_theme", "official", "nist_generative_ai_profile.pdf", "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf"),
    ("energy_power_theme", "official", "doe_data_center_electricity_demand.html", "https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers"),
    ("energy_power_theme", "official", "ferc_electric_power_markets.html", "https://www.ferc.gov/electric-power-markets"),
    ("space_theme", "official", "faa_commercial_space_data.html", "https://www.faa.gov/space/additional_information/commercial_space_data"),
    ("space_theme", "official", "faa_commercial_space_transportation.html", "https://www.faa.gov/space"),
    ("cybersecurity_theme", "official", "nvd_api_docs.html", "https://nvd.nist.gov/developers/vulnerabilities"),
    ("cybersecurity_theme", "official", "cisa_cybersecurity_advisories.html", "https://www.cisa.gov/news-events/cybersecurity-advisories"),
    ("relation_ontology", "official_standard", "w3c_prov_dm.html", "https://www.w3.org/TR/prov-dm/"),
    ("relation_ontology", "official_standard", "w3c_prov_o.html", "https://www.w3.org/TR/prov-o/"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, local_path: Path) -> tuple[str, int]:
    if local_path.exists() and local_path.stat().st_size > 0:
        return "downloaded_existing", local_path.stat().st_size
    local_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 research-audit"})
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            local_path.write_bytes(response.read())
        return "downloaded", local_path.stat().st_size
    except Exception as exc:
        return f"download_failed: {exc}", 0


def source_tier(row: dict[str, str]) -> str:
    family = row["source_family"]
    name = row["source_name"]
    if row.get("source_authority_tier"):
        return row["source_authority_tier"]
    if family in {"macro_economic", "policy_geopolitics"}:
        return "official"
    if family in {"relation_ontology"}:
        return "official_standard"
    if name.startswith(("sia_", "stanford_")):
        return "industry_or_academic_reference"
    if name.startswith(("nist_", "eia_", "nasa_", "cisa_", "oecd_", "bis_", "bea_", "federal_", "congress_", "ofac_")):
        return "official"
    return "reference"


def build_catalog() -> list[dict[str, object]]:
    prior = read_csv(PREV_MANIFEST)
    rows: list[dict[str, object]] = []
    seen_urls = set()
    for row in prior:
        seen_urls.add(row["url"])
        local_path = Path(row["local_path"])
        rows.append(
            {
                **row,
                "source_authority_tier": source_tier(row),
                "institutional_use": "source_contract_seed",
                "content_extraction_state": "raw_available" if row["download_state"] == "downloaded" else "raw_missing_recorded",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    for family, tier, name, url in NEW_SOURCES:
        if url in seen_urls:
            continue
        local_path = RAW_DIR / name
        state, size = download(url, local_path)
        rows.append(
            {
                "source_family": family,
                "source_name": name,
                "url": url,
                "local_path": str(local_path.relative_to(ROOT)),
                "download_state": state,
                "size_bytes": size,
                "sha256": sha256(local_path),
                "source_authority_tier": tier,
                "institutional_use": "source_contract_seed",
                "content_extraction_state": "raw_available" if state.startswith("downloaded") else "raw_missing_recorded",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build() -> dict[str, object]:
    catalog = build_catalog()
    l1_contracts = [
        {"source_family": "macro_economic", "required_fields": "source_id issuer source_url local_path local_sha256 release_ts vintage_ts period_start period_end metric_name unit seasonal_adjustment revision_flag", "reject_if_missing": "issuer;release_ts;vintage_ts;metric_name;local_sha256", "purpose": "prevent macro values from losing release and revision context", "authority": AUTHORITY},
        {"source_family": "policy_geopolitics", "required_fields": "source_id issuer source_url local_path local_sha256 published_ts lifecycle_state effective_from effective_until jurisdiction affected_entities policy_domain", "reject_if_missing": "issuer;published_ts;lifecycle_state;affected_entities;effective_from", "purpose": "separate proposal final effective enforcement and revoked policy states", "authority": AUTHORITY},
        {"source_family": "company_filings_ir", "required_fields": "source_id issuer cik accession filed_ts period_end form_type exhibit item local_sha256 symbol", "reject_if_missing": "issuer;cik;filed_ts;form_type;local_sha256;symbol", "purpose": "retain raw company filing provenance and period alignment", "authority": AUTHORITY},
        {"source_family": "theme_official_industry", "required_fields": "source_id issuer source_url local_path local_sha256 published_ts theme domain_node value_chain_node metric_name denominator", "reject_if_missing": "issuer;published_ts;theme;domain_node;local_sha256", "purpose": "turn broad theme reports into auditable theme mechanism evidence", "authority": AUTHORITY},
        {"source_family": "relation_ontology", "required_fields": "source_id standard_body source_url local_path local_sha256 concept valid_time_model provenance_model", "reject_if_missing": "standard_body;concept;valid_time_model;provenance_model", "purpose": "standardize provenance and time semantics for L3 edges", "authority": AUTHORITY},
    ]
    l2_primitives = [
        {"primitive_family": "macro_release", "primitive_type": "level_trend_surprise_revision", "required_fields": "metric actual prior revised consensus surprise zscore period vintage_ts release_ts", "forbidden_fields": "future_return pnl outcome_rank", "example_use": "CPI/PCE/GDP/payrolls/rates as macro state input not trade instruction", "authority": AUTHORITY},
        {"primitive_family": "policy_lifecycle", "primitive_type": "proposal_final_effective_enforcement", "required_fields": "policy_domain lifecycle_state affected_entities jurisdiction effective_from effective_until enforcement_scope", "forbidden_fields": "future_return pnl outcome_rank", "example_use": "export control or sanctions change as market access constraint", "authority": AUTHORITY},
        {"primitive_family": "semiconductor_value_chain", "primitive_type": "bottleneck_capacity_export_customer_capex", "required_fields": "value_chain_node upstream_node downstream_node bottleneck_type affected_products affected_symbols denominator", "forbidden_fields": "future_return pnl outcome_rank", "example_use": "equipment/foundry/memory/networking exposure primitive", "authority": AUTHORITY},
        {"primitive_family": "ai_infrastructure", "primitive_type": "compute_capex_power_networking_model_demand", "required_fields": "ai_demand_driver compute_layer capex_channel power_load_proxy supplier_node beneficiary_symbols cost_bearer_symbols", "forbidden_fields": "future_return pnl outcome_rank", "example_use": "AI demand mapped to GPU/cloud/power/cooling/networking chain", "authority": AUTHORITY},
        {"primitive_family": "energy_power", "primitive_type": "load_generation_grid_price_constraint", "required_fields": "load_driver region power_market generation_mix grid_constraint price_channel affected_symbols", "forbidden_fields": "future_return pnl outcome_rank", "example_use": "data-center load to utility/grid/equipment exposure", "authority": AUTHORITY},
        {"primitive_family": "cybersecurity", "primitive_type": "exploited_vulnerability_vendor_budget_pressure", "required_fields": "cve vendor product exploit_status due_date affected_customer_type remediation_pressure vendor_symbols", "forbidden_fields": "future_return pnl outcome_rank", "example_use": "CISA KEV to vendor/security budget pressure", "authority": AUTHORITY},
        {"primitive_family": "space", "primitive_type": "launch_budget_contract_backlog", "required_fields": "agency customer budget_line launch_cadence contract_type backlog_proxy supplier_symbols", "forbidden_fields": "future_return pnl outcome_rank", "example_use": "NASA/FAA/DoD space activity to launch and supplier exposure", "authority": AUTHORITY},
    ]
    l3_mechanisms = [
        {"mechanism": "discount_rate", "base_primitive": "conditions", "transmission_channel": "rates_to_duration_multiple", "lag_model": "same_day_to_3_months", "required_fields": "source_node target_node direction confidence valid_from valid_until denominator", "authority": AUTHORITY},
        {"mechanism": "demand_pull", "base_primitive": "reinforces", "transmission_channel": "end_demand_to_revenue", "lag_model": "1_to_4_quarters", "required_fields": "demand_driver supplier_node target_symbol exposure_basis confidence valid_from valid_until", "authority": AUTHORITY},
        {"mechanism": "supply_constraint", "base_primitive": "conditions", "transmission_channel": "capacity_bottleneck_to_pricing_or_shortage", "lag_model": "1_to_8_quarters", "required_fields": "bottleneck_node affected_product target_symbol denominator confidence", "authority": AUTHORITY},
        {"mechanism": "market_access", "base_primitive": "weakens", "transmission_channel": "policy_or_sanction_to_revenue_access", "lag_model": "effective_date_to_2_quarters", "required_fields": "policy_node affected_entity target_symbol effective_from effective_until confidence", "authority": AUTHORITY},
        {"mechanism": "capex_cycle", "base_primitive": "sequences", "transmission_channel": "customer_capex_to_supplier_orders", "lag_model": "1_to_6_quarters", "required_fields": "customer_node supplier_node order_proxy backlog_proxy confidence", "authority": AUTHORITY},
        {"mechanism": "cost_pressure", "base_primitive": "weakens", "transmission_channel": "input_cost_to_margin", "lag_model": "same_quarter_to_4_quarters", "required_fields": "cost_driver cost_bearer pass_through_ability denominator confidence", "authority": AUTHORITY},
        {"mechanism": "security_risk", "base_primitive": "conditions", "transmission_channel": "vulnerability_to_budget_or_liability", "lag_model": "immediate_to_2_quarters", "required_fields": "risk_node vendor_node customer_node severity due_date confidence", "authority": AUTHORITY},
        {"mechanism": "contradiction", "base_primitive": "contradicts", "transmission_channel": "source_claim_conflict", "lag_model": "valid_until_resolved", "required_fields": "claim_a claim_b conflict_basis source_priority confidence", "authority": AUTHORITY},
    ]
    l4_thesis_card = [
        {"field": "thesis_id", "required": "1", "purpose": "stable candidate identity", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "variant_view", "required": "1", "purpose": "what the system believes differently from consensus", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "consensus_view", "required": "1", "purpose": "what market/common narrative likely already sees", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "economic_driver", "required": "1", "purpose": "macro policy theme or company mechanism driving the thesis", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "denominator", "required": "1", "purpose": "scale base such as revenue capex unit shipment power load or backlog", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "exposure_chain", "required": "1", "purpose": "source -> primitive -> mechanism -> theme node -> symbol exposure", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "catalyst_window", "required": "1", "purpose": "when the thesis should matter", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "invalidation_path", "required": "1", "purpose": "what source-backed event would kill or weaken the thesis", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "uncertainty_state", "required": "1", "purpose": "known unknowns and missing source conditions", "reject_if_missing": "1", "authority": AUTHORITY},
        {"field": "outcome_used_for_assignment_flag", "required": "1", "purpose": "must be zero before candidate can reach adapter", "reject_if_missing": "1", "authority": AUTHORITY},
    ]
    exposure_templates = [
        {"template_id": "AI_TO_SEMIS_POWER", "chain": "AI demand -> compute capex -> GPU/networking/data center -> power/cooling constraint -> semis/power/utility symbols", "required_sources": "NIST_AI;Stanford_AI_Index;EIA;company_filings", "authority": AUTHORITY},
        {"template_id": "EXPORT_CONTROL_TO_SEMIS", "chain": "BIS rule -> affected chip/equipment entity -> market access constraint -> revenue exposure -> symbol thesis", "required_sources": "BIS;FederalRegister;company_filings;SIA/OECD", "authority": AUTHORITY},
        {"template_id": "RATE_PATH_TO_DURATION_GROWTH", "chain": "Fed/BEA/BLS release -> rate path/inflation/growth primitive -> discount rate mechanism -> high-duration equity exposure", "required_sources": "Fed;BEA;BLS;Treasury", "authority": AUTHORITY},
        {"template_id": "CYBER_KEV_TO_SECURITY_SPEND", "chain": "CISA KEV -> exploited product/vendor/customer urgency -> security budget pressure -> vendor exposure", "required_sources": "CISA_KEV;NVD;company_filings", "authority": AUTHORITY},
        {"template_id": "SPACE_BUDGET_TO_LAUNCH_SUPPLY", "chain": "NASA/DoD/FAA activity -> contract/budget/launch cadence primitive -> supplier backlog or capacity mechanism -> symbol exposure", "required_sources": "NASA;FAA;DoD;company_filings", "authority": AUTHORITY},
    ]
    validators = [
        {"validator_id": "L1_SOURCE_CONTRACT", "checks": "source_family issuer published_or_release_ts local_sha256 authority_tier update_cadence", "pass_does_not_mean": "source complete or strategy accepted", "authority": AUTHORITY},
        {"validator_id": "L2_PRIMITIVE_CONTRACT", "checks": "primitive_family required_fields no_outcome_fields source_id lineage", "pass_does_not_mean": "economic meaning is true", "authority": AUTHORITY},
        {"validator_id": "L3_MECHANISM_CONTRACT", "checks": "base_primitive mechanism direction confidence valid_from valid_until denominator", "pass_does_not_mean": "edge predicts returns", "authority": AUTHORITY},
        {"validator_id": "L4_THESIS_CARD_CONTRACT", "checks": "variant consensus driver denominator exposure_chain catalyst invalidation uncertainty outcome_flag_zero", "pass_does_not_mean": "candidate is tradable", "authority": AUTHORITY},
        {"validator_id": "NO_REPLAY_GATE", "checks": "no selection replay or adapter promotion until L1-L4 contracts pass", "pass_does_not_mean": "deployment readiness", "authority": AUTHORITY},
    ]
    next_tasks = [
        {"task": "Task1031", "title": "L1 Source Contract Implementation", "scope": "implement schema and validator for source authority/release/vintage contracts", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1032", "title": "Macro Vintage Primitive Builder", "scope": "build macro release/vintage primitive rows from BEA/BLS/Fed/Treasury/EIA docs and API contracts", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1033", "title": "Policy Lifecycle Primitive Builder", "scope": "build proposal/final/effective/enforcement policy lifecycle schema for Federal Register/Congress/BIS/OFAC", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1034", "title": "Theme Exposure Chain Builder", "scope": "map semiconductor AI energy space cyber source nodes to theme nodes and symbol exposure templates", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1035", "title": "L3 Mechanism Relation Adapter", "scope": "extend nine primitives with mechanism/channel/lag/denominator/confidence modifiers", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1036", "title": "L4 Thesis Card Contract", "scope": "require variant view consensus view exposure chain catalyst window and invalidation path", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1037", "title": "L1-L4 Contract Validator Suite", "scope": "validate L1-L4 before adapter or replay can run", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1038", "title": "Small Manual Golden Set", "scope": "build 20 hand-reviewable source-to-thesis examples across macro policy and themes", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1039", "title": "Cross-Read Relation QA", "scope": "audit whether cross-read chains are causal directional and symbol-specific", "blocked_replay_until_done": "1", "authority": AUTHORITY},
        {"task": "Task1040", "title": "Replay Gate Reopen Decision", "scope": "decide if L1-L4 contracts are sufficient to reopen controlled replay", "blocked_replay_until_done": "1", "authority": AUTHORITY},
    ]
    downloaded_count = sum(1 for row in catalog if str(row["download_state"]).startswith("downloaded"))
    summary = {
        "task_id": "Task1021-1030",
        "verdict": "l1_l4_institutional_upgrade_contracts_complete_no_replay",
        "source_rows": len(catalog),
        "downloaded_source_rows": downloaded_count,
        "l1_contract_rows": len(l1_contracts),
        "l2_primitive_rows": len(l2_primitives),
        "l3_mechanism_rows": len(l3_mechanisms),
        "l4_thesis_card_rows": len(l4_thesis_card),
        "exposure_template_rows": len(exposure_templates),
        "next_task_rows": len(next_tasks),
        "replay_executed": "0",
        "next_action": "implement_Task1031_1040_L1_L4_contract_validators_and_golden_source_to_thesis_examples",
        **STATUS,
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task1021_institutional_source_catalog.csv", catalog, [
        "source_family", "source_name", "url", "local_path", "download_state", "size_bytes", "sha256",
        "source_authority_tier", "institutional_use", "content_extraction_state",
        "selection_use_allowed", "replay_use_allowed", "authority",
    ])
    write_csv(OUT_DIR / "task1022_source_authority_tier_contract.csv", [
        {"source_authority_tier": "official", "allowed_uses": "L1_source_contract;L2_primitive_seed;L3_mechanism_reference", "cannot_do": "direct_buy_sell_or_acceptance", "authority": AUTHORITY},
        {"source_authority_tier": "official_standard", "allowed_uses": "provenance_time_relation_schema", "cannot_do": "market_claim_or_trade_signal", "authority": AUTHORITY},
        {"source_authority_tier": "industry_or_academic_reference", "allowed_uses": "theme_context_and_mechanism_reference", "cannot_do": "source_of_truth_for_company_specific_fact_without_primary_source", "authority": AUTHORITY},
        {"source_authority_tier": "reference", "allowed_uses": "auxiliary_context_only", "cannot_do": "candidate_assignment_or_replay_input", "authority": AUTHORITY},
    ], ["source_authority_tier", "allowed_uses", "cannot_do", "authority"])
    write_csv(OUT_DIR / "task1023_l1_source_family_contracts.csv", l1_contracts, ["source_family", "required_fields", "reject_if_missing", "purpose", "authority"])
    write_csv(OUT_DIR / "task1024_l2_primitive_schema.csv", l2_primitives, ["primitive_family", "primitive_type", "required_fields", "forbidden_fields", "example_use", "authority"])
    write_csv(OUT_DIR / "task1025_l3_relation_mechanism_schema.csv", l3_mechanisms, ["mechanism", "base_primitive", "transmission_channel", "lag_model", "required_fields", "authority"])
    write_csv(OUT_DIR / "task1026_l4_thesis_card_schema.csv", l4_thesis_card, ["field", "required", "purpose", "reject_if_missing", "authority"])
    write_csv(OUT_DIR / "task1027_theme_exposure_chain_templates.csv", exposure_templates, ["template_id", "chain", "required_sources", "authority"])
    write_csv(OUT_DIR / "task1028_l1_l4_validator_contracts.csv", validators, ["validator_id", "checks", "pass_does_not_mean", "authority"])
    write_csv(OUT_DIR / "task1029_next_task_backlog.csv", next_tasks, ["task", "title", "scope", "blocked_replay_until_done", "authority"])
    write_csv(OUT_DIR / "task1030_no_replay_closeout.csv", [summary], list(summary.keys()))
    write_csv(OUT_DIR / "task1021_1030_summary.csv", [summary], list(summary.keys()))
    (OUT_DIR / "task1021_1030_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_1021_1030_L1_L4_INSTITUTIONAL_UPGRADE_OK] "
        f"sources={summary['source_rows']} downloaded={summary['downloaded_source_rows']} "
        f"l2={summary['l2_primitive_rows']} l3={summary['l3_mechanism_rows']} replay=0"
    )


if __name__ == "__main__":
    main()
