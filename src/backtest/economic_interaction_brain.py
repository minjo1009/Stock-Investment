from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import pandas as pd


@dataclass(frozen=True)
class EvidenceObject:
    source_event_id: str
    source_family: str
    source_url: str | None
    filing_type: str | None
    asof_timestamp: str
    raw_text_path: str | None
    evidence_span: str
    blocker_span: str | None = None
    numeric_units: str | None = None
    provenance_hash: str | None = None
    parser_confidence_state: str = "unknown"
    reject_reason: str | None = None

    def certified(self) -> bool:
        return bool(self.asof_timestamp and self.evidence_span and self.raw_text_path) and not self.reject_reason


@dataclass(frozen=True)
class PrimitiveFactObject:
    event_type: str
    counterparty: str | None = None
    amount: float | None = None
    currency: str | None = None
    duration_months: float | None = None
    delivery_schedule: str | None = None
    backlog_impact: str | None = None
    revenue_impact: str | None = None
    margin_language: str | None = None
    guidance_language: str | None = None
    financing_terms: str | None = None
    use_of_proceeds: str | None = None
    price_reaction_state: str | None = None


@dataclass(frozen=True)
class EconomicMeaningObject:
    order_size_vs_revenue: str = "unknown"
    order_size_vs_guidance: str = "unknown"
    order_size_vs_backlog: str = "unknown"
    order_size_vs_market_cap: str = "unknown"
    backlog_conversion_quality: str = "unknown"
    margin_accretion_state: str = "unknown"
    customer_quality_state: str = "unknown"
    repeatability_state: str = "unknown"
    financing_quality_state: str = "unknown"
    demand_supply_fit_state: str = "unknown"
    missing_denominators: tuple[str, ...] = field(default_factory=tuple)

    def strong_claim_allowed(self) -> bool:
        return not self.missing_denominators and self.order_size_vs_revenue != "unknown"


@dataclass(frozen=True)
class InteractionEdgeObject:
    edge_id: str
    source_node: str
    target_node: str
    relation_type: str
    precondition: str
    confidence_cap_state: str = "uncapped"
    blocker_reason: str | None = None


@dataclass(frozen=True)
class CandidateThesisBundle:
    thesis_type: str
    expected_transmission_path: tuple[str, ...]
    required_confirmations: tuple[str, ...]
    contradiction_flags: tuple[str, ...]
    thesis_half_life_state: str
    invalidation_conditions: tuple[str, ...]


@dataclass(frozen=True)
class SlotDecisionExplanation:
    actionability: str
    same_timestamp_cohort_id: str
    reason: str
    missing_fields: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    assignment_allowed_flag: int = 0


CONTRACT_LAYERS = [
    {
        "contract_layer": "evidence_object",
        "purpose": "raw source proof",
        "required_fields": "source_family, event_ts, raw_text_path, evidence_span, blocker_span, numeric_units, provenance_hash",
        "hard_rule": "source lineage, as-of timestamp, and exact evidence span must be explicit",
    },
    {
        "contract_layer": "primitive_fact_object",
        "purpose": "atomic extracted facts",
        "required_fields": "order_award, revenue, backlog, guidance, margin, supply_demand, financing_terms",
        "hard_rule": "facts are not trade signals and must keep unknown separate from false",
    },
    {
        "contract_layer": "denominator_object",
        "purpose": "scale and expectation base",
        "required_fields": "revenue_run_rate, prior_guidance, consensus, backlog_base, market_cap_proxy, capacity_base",
        "hard_rule": "missing denominator blocks strong economic claim",
    },
    {
        "contract_layer": "expectation_object",
        "purpose": "surprise and revision context",
        "required_fields": "raise/reaffirm/cut, prior_guidance_delta, consensus_delta, already_priced_state",
        "hard_rule": "reaffirmation is not positive surprise by itself",
    },
    {
        "contract_layer": "economic_meaning_object",
        "purpose": "business value interpretation",
        "required_fields": "size_materiality, margin_effect, duration, repeatability, customer_quality, capacity_fit",
        "hard_rule": "requires primitive fact plus denominator or explicit source statement",
    },
    {
        "contract_layer": "financing_quality_object",
        "purpose": "capital structure interpretation",
        "required_fields": "use_of_proceeds, dilution_risk, credit_stress, runway_extension, growth_funding",
        "hard_rule": "financing is not default bearish or bullish",
    },
    {
        "contract_layer": "interaction_edge_object",
        "purpose": "cross-factor relationship",
        "required_fields": "reinforcing, offsetting, prerequisite, blocker, confidence_cap",
        "hard_rule": "edge must cite both source states",
    },
    {
        "contract_layer": "candidate_thesis_bundle",
        "purpose": "coherent thesis",
        "required_fields": "base_case, upside_path, risk_path, missing_evidence, invalidation",
        "hard_rule": "bundle is review-only until all hard gates pass",
    },
    {
        "contract_layer": "slot_decision_explanation",
        "purpose": "same timestamp competition",
        "required_fields": "why_this_candidate, why_not_others, cluster_risk, price_acceptance",
        "hard_rule": "no global rank; same-cohort only",
    },
]


REQUIRED_SCHEMA_FIELDS = [
    ("evidence", "source_event_id", "stable id of source event", "required"),
    ("evidence", "source_form_family", "8-K/10-Q/Form4/13D/13G/13F/news/IR/other", "required"),
    ("evidence", "raw_text_path", "path to immutable source text", "required"),
    ("evidence", "evidence_span", "exact operational evidence span", "required"),
    ("evidence", "blocker_span", "exact span causing rejection or confidence cap", "separate_from_evidence_span"),
    ("evidence", "asof_timestamp", "timestamp available to strategy", "required"),
    ("evidence", "used_for_assignment_flag", "whether allowed in assignment", "must_be_0_until_contract_pass"),
    ("order_award", "contract_value_amount", "exact value from source text if present", "missing_unknown_not_zero"),
    ("order_award", "contract_value_currency", "currency or blank", "missing_unknown_not_zero"),
    ("order_award", "customer_name", "named customer/counterparty", "generic_customer_is_weak"),
    ("order_award", "customer_quality_tier", "government/hyperscaler/blue_chip/repeat_customer/unknown", "source_or_dictionary_required"),
    ("order_award", "funded_status", "funded/unfunded/framework/unknown", "unfunded_blocks_strong_claim"),
    ("order_award", "duration_months", "contract duration if stated", "missing_caps_confidence"),
    ("scale", "revenue_run_rate_denominator", "company revenue run-rate denominator", "missing_blocks_materiality"),
    ("scale", "prior_guidance_denominator", "prior guidance denominator", "missing_blocks_surprise"),
    ("scale", "backlog_denominator", "company backlog denominator", "missing_blocks_conversion_claim"),
    ("scale", "market_cap_denominator", "market cap denominator", "missing_blocks_valuation_claim"),
    ("scale", "capacity_denominator", "capacity denominator", "missing_blocks_supply_demand_claim"),
    ("scale", "consensus_expectation_denominator", "consensus or estimate denominator", "missing_blocks_revision_claim"),
    ("guidance", "guidance_direction_state", "raise/reaffirm/cut/withdraw/soft/none", "reaffirm_not_positive_surprise"),
    ("guidance", "guidance_surprise_state", "above_prior/above_consensus/reaffirm/below/unknown", "unknown_blocks_surprise_claim"),
    ("margin", "margin_effect_state", "accretive/dilutive/mixed/unknown", "must_not_infer_from_revenue_alone"),
    ("supply_demand", "supply_demand_tightness_state", "tight/easing/oversupply/unknown", "must_link_to_company_capacity_or_pricing"),
    ("financing", "financing_use_of_proceeds_state", "growth_funding/refinancing/liquidity_rescue/general_corporate/unknown", "use_of_proceeds_required"),
    ("financing", "financing_cost_state", "low_cost/high_cost/convertible/warrant_heavy/unknown", "cost_and_structure_required"),
    ("financing", "dilution_overhang_state", "none/possible/material/severe/unknown", "not_all_financing_equal"),
    ("pricing", "price_acceptance_state", "accepted/building/rejected/extended/unknown", "timestamped_market_reaction_only"),
    ("slot", "same_timestamp_cohort_id", "cohort id for slot comparison", "no_global_rank"),
]


INTERACTION_EDGE_RULES = [
    ("order_large_vs_guidance_raise", "order_award + guidance", "contract materiality and guidance raise both source-backed", "reinforcing", "priority_review_candidate"),
    ("order_without_denominator", "order_award + scale", "contract exists but revenue/backlog/guidance denominator missing", "confidence_cap", "research_only"),
    ("order_unfunded_or_framework", "order_award + funded_status", "order is unfunded/framework/indefinite delivery without committed value", "confidence_cap", "confirmation_required"),
    ("order_margin_unknown", "order_award + margin", "revenue signal present but margin effect unknown", "confidence_cap", "confirmation_required"),
    ("guidance_reaffirm_after_news", "guidance + novelty", "guidance is reaffirmation, not a raise", "offsetting", "reduced_confidence"),
    ("guidance_raise_with_demand_tightness", "guidance + supply_demand", "raise plus company-linked demand tightness", "reinforcing", "priority_review_candidate"),
    ("financing_growth_funds_order", "financing + order_award", "use of proceeds funds capacity/backlog conversion with manageable dilution", "reinforcing_if_absorbed", "confirmation_required"),
    ("financing_dilution_offsets_order", "financing + order_award", "warrants/convertibles/ATM dominate order economics", "offsetting", "confirmation_required_or_block"),
    ("credit_stress_blocks_catalyst", "financing + liquidity", "credit agreement or note purchase indicates rescue/liquidity stress", "blocker", "research_only"),
    ("price_accepts_after_interaction", "pricing + thesis", "price acceptance after economic interaction is coherent", "prerequisite", "eligible_review_candidate"),
    ("price_extended_before_news", "pricing + novelty", "price already extended before event", "confidence_cap", "delayed_or_research_only"),
    ("sector_leadership_reinforces", "theme + company", "sector/theme leadership supports company catalyst", "reinforcing", "slot_candidate"),
    ("sector_rotation_offsets", "theme + company", "capital rotating away from theme despite company catalyst", "offsetting", "reduced_slot_claim"),
    ("same_timestamp_better_candidate", "slot + thesis", "another candidate has better evidence/interaction/price package", "blocker", "do_not_displace_slot"),
]


DANGEROUS_LEGACY_SURFACES = [
    ("src/backtest/build_task713_717_firm_grade_trader_brain.py", "revenue_path_state", "count co-occurrence", "build_economic_meaning_object"),
    ("src/backtest/build_task713_717_firm_grade_trader_brain.py", "margin_path_state", "guidance_margin_count plus supply_count", "build_margin_bridge_object"),
    ("src/backtest/build_task713_717_firm_grade_trader_brain.py", "order_backlog_path_state", "revenue_backlog_count", "build_order_backlog_conversion_object"),
    ("src/backtest/build_task713_717_firm_grade_trader_brain.py", "funding_path_state", "financing subtype labels", "build_financing_quality_object"),
    ("src/backtest/build_task713_717_firm_grade_trader_brain.py", "economic_transmission_state", "state names from shallow path labels", "build_interaction_edges"),
    ("src/backtest/build_task720_watch_bucket_interaction_diagnostics.py", "cashflow_evidence_axis", "legacy cashflow count axis", "consume candidate_thesis_bundle"),
    ("src/backtest/build_task720_watch_bucket_interaction_diagnostics.py", "layer_interaction_state", "fixed if/else labels", "derive typed edge graph"),
    ("src/backtest/build_task636_full_period_content_prediction_backtest.py", "score_event_text", "parser hygiene only", "extract primitive facts with spans and denominators"),
]


def contract_frame() -> pd.DataFrame:
    frame = pd.DataFrame(CONTRACT_LAYERS)
    frame["assignment_allowed_flag"] = 0
    frame["backtest_allowed_before_gate_flag"] = 0
    return frame


def schema_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "domain": domain,
                "field_name": field,
                "definition": definition,
                "governance_rule": rule,
            }
            for domain, field, definition, rule in REQUIRED_SCHEMA_FIELDS
        ]
    )


def edge_rulebook_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "edge_id": edge_id,
                "edge_domain": domain,
                "precondition": precondition,
                "relation_type": relation,
                "review_action_state": action,
                "assignment_allowed_flag": 0,
            }
            for edge_id, domain, precondition, relation, action in INTERACTION_EDGE_RULES
        ]
    )


def code_restructure_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "file_path": file_path,
                "current_function_or_surface": surface,
                "current_problem": problem,
                "required_restructure": required,
                "change_status": "CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED",
            }
            for file_path, surface, problem, required in DANGEROUS_LEGACY_SURFACES
        ]
    )


def backtest_gate(metrics: Mapping[str, int | float | str]) -> dict[str, object]:
    clean_events = int(metrics.get("clean_economic_events", 0))
    denominator_fields_present = int(metrics.get("denominator_fields_present", 0))
    contamination_count = int(metrics.get("contamination_count", 0))
    interaction_objects_present = int(metrics.get("interaction_objects_present", 0))
    passed = clean_events > 0 and denominator_fields_present > 0 and contamination_count == 0 and interaction_objects_present > 0
    return {
        "gate_name": "economic_interaction_backtest_gate",
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": (
            f"clean_events={clean_events};denominator_fields_present={denominator_fields_present};"
            f"contamination_count={contamination_count};interaction_objects_present={interaction_objects_present}"
        ),
        "required": "clean events, denominators, zero contamination, and interaction objects",
    }
