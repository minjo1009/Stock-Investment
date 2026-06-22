from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


HIGH_REVIEW_STATES = {
    "control_intent_conditional",
    "financial_results_review_required",
    "generic_financing_review_required",
    "governance_quality_unknown",
    "holder_concentration_mixed",
    "mna_non_operating_review_required",
    "severance_change_in_control_mixed",
    "strategic_investment_conditional",
    "terms_incomplete_unknown",
}


@dataclass(frozen=True)
class EnrichmentRequirement:
    lifecycle_id: str
    bundle_id: str
    source_event_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    source_form_family: str
    context_type: str
    circuit_type: str
    current_semantic_state: str
    current_semantic_polarity: str
    current_transmission_channel: str
    current_edge_effect: str
    requirement_family: str
    missing_primitive_fields: str
    required_denominators: str
    required_comparators: str
    required_timing_checks: str
    required_interaction_fields: str
    resolver_target_state: str
    review_lane: str
    blocker_reason: str
    can_affect_confidence: int
    can_affect_risk: int
    can_affect_slot: int
    can_create_operating_catalyst: int
    actionability_created_flag: int
    used_for_trading_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int
    rule_id: str


def build_enrichment_requirements(attachments: pd.DataFrame, translations: pd.DataFrame) -> pd.DataFrame:
    enrichment_ids = set(
        attachments.loc[
            attachments["queue_transition_state"].astype(str).eq("semantic_enrichment_needed"),
            "lifecycle_id",
        ]
        .dropna()
        .astype(str)
    )
    bundle_ids = dict(zip(attachments["lifecycle_id"].astype(str), attachments["bundle_id"].astype(str)))
    scoped = translations[translations["lifecycle_id"].astype(str).isin(enrichment_ids)].copy()
    rows = []
    for _, row in scoped.iterrows():
        rows.append(asdict(requirement_for_translation(row, bundle_ids.get(str(row.get("lifecycle_id", "")), ""))))
    return pd.DataFrame(rows)


def requirement_for_translation(row: pd.Series, bundle_id: str = "") -> EnrichmentRequirement:
    state = text(row.get("semantic_state"))
    context = text(row.get("context_type"))
    source_family = text(row.get("source_form_family"))
    polarity = text(row.get("semantic_polarity"))
    channel = text(row.get("transmission_channel"))
    effect = text(row.get("edge_effect"))
    spec = requirement_spec(context, state, source_family, polarity, channel, effect)
    return EnrichmentRequirement(
        lifecycle_id=text(row.get("lifecycle_id")),
        bundle_id=bundle_id,
        source_event_id=text(row.get("event_id")),
        symbol=text(row.get("symbol")),
        theme_id=text(row.get("theme_id")),
        entry_ts=text(row.get("entry_ts")),
        split_name=text(row.get("split_name")),
        source_form_family=source_family,
        context_type=context,
        circuit_type=spec["circuit_type"],
        current_semantic_state=state,
        current_semantic_polarity=polarity,
        current_transmission_channel=channel,
        current_edge_effect=effect,
        requirement_family=spec["requirement_family"],
        missing_primitive_fields=pipe(spec["missing_primitive_fields"]),
        required_denominators=pipe(spec["required_denominators"]),
        required_comparators=pipe(spec["required_comparators"]),
        required_timing_checks=pipe(spec["required_timing_checks"]),
        required_interaction_fields=pipe(spec["required_interaction_fields"]),
        resolver_target_state=spec["resolver_target_state"],
        review_lane=spec["review_lane"],
        blocker_reason=spec["blocker_reason"],
        can_affect_confidence=int(spec["can_affect_confidence"]),
        can_affect_risk=int(spec["can_affect_risk"]),
        can_affect_slot=int(spec["can_affect_slot"]),
        can_create_operating_catalyst=0,
        actionability_created_flag=0,
        used_for_trading_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
        rule_id=f"TASK738_{spec['requirement_family'].upper()}",
    )


def requirement_spec(
    context: str,
    state: str,
    source_family: str,
    polarity: str,
    channel: str,
    effect: str,
) -> dict[str, object]:
    if context == "InsiderBehaviorContext":
        return insider_spec(state, polarity, channel, effect)
    if context == "ActivistControlContext":
        return activist_spec(state, polarity, channel, effect)
    if context == "InstitutionalPositioningContext":
        return institutional_positioning_spec(state, polarity, channel, effect)
    if context == "OwnershipStructureContext":
        return ownership_structure_spec(state, polarity, channel, effect)
    if context == "CreditFinancingContext":
        return financing_spec("credit_financing", state, polarity, channel, effect)
    if context == "Generic8KClassificationContext":
        return generic_8k_spec(state, polarity, channel, effect)
    if context == "MacroPolicyTransmissionContext":
        return macro_policy_spec(state, polarity, channel, effect)
    return base_spec(
        circuit_type=source_family or "unknown_source_circuit",
        requirement_family="generic_semantic_enrichment",
        missing_primitive_fields=["source_family", "event_subtype", "economic_subject", "affected_company"],
        required_denominators=["company_scale"],
        required_comparators=["prior_source_state"],
        required_timing_checks=["published_at", "tradable_after_ts"],
        required_interaction_fields=["current_layer_edge", "bundle_context"],
        resolver_target_state="semantic_context_needed",
        review_lane=review_lane_for(state, context),
        blocker_reason="semantic state has no circuit-specific resolver yet",
        polarity=polarity,
        effect=effect,
    )


def insider_spec(state: str, polarity: str, channel: str, effect: str) -> dict[str, object]:
    if state == "automatic_plan_sale_neutral_to_unknown":
        return base_spec(
            circuit_type="form4_insider_behavior",
            requirement_family="form4_plan_pattern_enrichment",
            missing_primitive_fields=[
                "insider_role",
                "transaction_code",
                "plan_adoption_date",
                "shares_sold",
                "transaction_value",
                "ownership_after",
                "percent_of_holdings",
                "cluster_pattern",
            ],
            required_denominators=["insider_total_holdings", "market_cap", "daily_volume"],
            required_comparators=["prior_90d_insider_sales", "same_period_peer_insider_activity"],
            required_timing_checks=["transaction_date", "filing_date", "plan_adoption_date"],
            required_interaction_fields=["financing_or_liquidity_context", "management_role_materiality"],
            resolver_target_state="insider_pattern_needed",
            review_lane="normal_review_lane",
            blocker_reason="10b5-1 or routine sale cannot be read without size, role, plan, and history",
            polarity=polarity,
            effect=effect,
        )
    if state == "transaction_pattern_unknown":
        return base_spec(
            circuit_type="form4_insider_behavior",
            requirement_family="form4_transaction_code_enrichment",
            missing_primitive_fields=["transaction_code", "transaction_type", "open_market_flag", "award_or_exercise_flag", "shares", "value", "ownership_after"],
            required_denominators=["insider_total_holdings", "market_cap"],
            required_comparators=["same_insider_history", "cluster_activity"],
            required_timing_checks=["transaction_date", "filing_date"],
            required_interaction_fields=["role_materiality", "recent_company_catalyst_context"],
            resolver_target_state="insider_transaction_pattern_needed",
            review_lane="normal_review_lane",
            blocker_reason="Form4 transaction code was not resolved into economic behavior",
            polarity=polarity,
            effect=effect,
        )
    if state == "open_market_buy_constructive_modifier":
        return base_spec(
            circuit_type="form4_insider_behavior",
            requirement_family="form4_open_market_buy_context",
            missing_primitive_fields=["insider_role", "transaction_value", "ownership_after", "percent_of_holdings", "cluster_buying"],
            required_denominators=["insider_total_holdings", "market_cap", "daily_volume"],
            required_comparators=["same_insider_history", "peer_insider_buying"],
            required_timing_checks=["transaction_date", "filing_date", "staleness_window"],
            required_interaction_fields=["company_catalyst_alignment", "price_absorption_context"],
            resolver_target_state="insider_modifier_context_needed",
            review_lane="normal_review_lane",
            blocker_reason="open-market buy is only a modifier until size, role, and catalyst alignment are known",
            polarity=polarity,
            effect=effect,
        )
    return base_spec(
        circuit_type="form4_insider_behavior",
        requirement_family="form4_context_only_trace",
        missing_primitive_fields=["unusual_dilution_flag", "retention_signal"],
        required_denominators=["shares_outstanding"],
        required_comparators=["ordinary_award_pattern"],
        required_timing_checks=["transaction_date", "filing_date"],
        required_interaction_fields=["dilution_context"],
        resolver_target_state="insider_context_only",
        review_lane="normal_review_lane",
        blocker_reason="routine award or option exercise is context-only unless unusual dilution or retention appears",
        polarity=polarity,
        effect=effect,
    )


def activist_spec(state: str, polarity: str, channel: str, effect: str) -> dict[str, object]:
    if state == "control_intent_conditional":
        return base_spec(
            circuit_type="activist_control",
            requirement_family="activist_control_intent_enrichment",
            missing_primitive_fields=["filer_identity", "ownership_percent", "purpose_language", "board_control_intent", "amendment_sequence", "settlement_terms"],
            required_denominators=["shares_outstanding", "float"],
            required_comparators=["prior_13d_13g_position", "ownership_threshold", "peer_activist_pattern"],
            required_timing_checks=["event_date", "filing_date", "amendment_sequence_date"],
            required_interaction_fields=["governance_context", "strategic_alternative_context", "slot_crowding_context"],
            resolver_target_state="control_intent_review",
            review_lane="high_review_lane",
            blocker_reason="active/control intent can alter L4/L5 but needs purpose and amendment context",
            polarity=polarity,
            effect=effect,
        )
    if state == "passive_ownership_neutral":
        return passive_ownership_spec(polarity, effect)
    return ownership_change_spec(
        circuit_type="activist_control",
        requirement_family="activist_ownership_change_enrichment",
        resolver_target_state="activist_ownership_change_needed",
        polarity=polarity,
        effect=effect,
    )


def institutional_positioning_spec(state: str, polarity: str, channel: str, effect: str) -> dict[str, object]:
    return base_spec(
        circuit_type="institutional_positioning",
        requirement_family="institutional_positioning_enrichment",
        missing_primitive_fields=["institution_identity", "shares", "market_value", "position_change", "quarter_end_date", "filing_lag"],
        required_denominators=["float", "institution_portfolio_size", "average_volume"],
        required_comparators=["prior_quarter_position", "institution_style", "peer_positioning_change"],
        required_timing_checks=["quarter_end_date", "filing_date", "staleness_window"],
        required_interaction_fields=["crowding_context", "theme_leadership_context"],
        resolver_target_state="positioning_context_needed",
        review_lane="normal_review_lane",
        blocker_reason="13F is stale positioning context, not a fresh operating catalyst",
        polarity=polarity,
        effect=effect,
    )


def ownership_structure_spec(state: str, polarity: str, channel: str, effect: str) -> dict[str, object]:
    if state == "holder_concentration_mixed":
        return base_spec(
            circuit_type="ownership_float_structure",
            requirement_family="holder_concentration_enrichment",
            missing_primitive_fields=["holder_identity", "ownership_percent", "float_percent", "change_vs_prior", "lockup_or_exit_risk"],
            required_denominators=["float", "shares_outstanding", "daily_volume"],
            required_comparators=["prior_holder_concentration", "peer_float_tightness"],
            required_timing_checks=["effective_date", "filing_date", "staleness_window"],
            required_interaction_fields=["liquidity_context", "slot_exposure_context"],
            resolver_target_state="holder_concentration_review",
            review_lane="high_review_lane",
            blocker_reason="holder concentration can help or hurt liquidity, so float and exit risk are required",
            polarity=polarity,
            effect=effect,
        )
    return ownership_change_spec(
        circuit_type="ownership_float_structure",
        requirement_family="ownership_change_enrichment",
        resolver_target_state="ownership_change_needed",
        polarity=polarity,
        effect=effect,
    )


def ownership_change_spec(
    *,
    circuit_type: str,
    requirement_family: str,
    resolver_target_state: str,
    polarity: str,
    effect: str,
) -> dict[str, object]:
    return base_spec(
        circuit_type=circuit_type,
        requirement_family=requirement_family,
        missing_primitive_fields=["holder_identity", "ownership_percent", "change_vs_prior", "active_passive_status", "beneficial_owner_type", "float_impact"],
        required_denominators=["float", "shares_outstanding"],
        required_comparators=["prior_filing", "ownership_threshold", "holder_history"],
        required_timing_checks=["event_date", "filing_date", "effective_date"],
        required_interaction_fields=["control_intent_context", "liquidity_context", "slot_exposure_context"],
        resolver_target_state=resolver_target_state,
        review_lane="normal_review_lane",
        blocker_reason="ownership change is not directional until holder type, magnitude, and purpose are known",
        polarity=polarity,
        effect=effect,
    )


def passive_ownership_spec(polarity: str, effect: str) -> dict[str, object]:
    return base_spec(
        circuit_type="activist_control",
        requirement_family="passive_ownership_context",
        missing_primitive_fields=["filer_identity", "ownership_percent", "change_vs_prior"],
        required_denominators=["float", "shares_outstanding"],
        required_comparators=["prior_filing", "ownership_threshold"],
        required_timing_checks=["event_date", "filing_date"],
        required_interaction_fields=["sponsorship_context"],
        resolver_target_state="passive_ownership_context",
        review_lane="normal_review_lane",
        blocker_reason="passive 13G is ownership context only unless position change is material",
        polarity=polarity,
        effect=effect,
    )


def generic_8k_spec(state: str, polarity: str, channel: str, effect: str) -> dict[str, object]:
    if state == "financial_results_review_required":
        return base_spec(
            circuit_type="financial_results_guidance",
            requirement_family="financial_results_expectation_enrichment",
            missing_primitive_fields=["revenue", "margin", "eps_or_fcf", "guidance_change", "backlog_or_segment_data", "expectation_reference"],
            required_denominators=["prior_guidance", "consensus_or_expectation_proxy", "yoy_qoq_base", "company_scale"],
            required_comparators=["prior_period", "management_prior_commentary", "peer_results"],
            required_timing_checks=["release_timestamp", "fiscal_period", "pre_or_post_market"],
            required_interaction_fields=["price_absorption_context", "macro_regime_context", "sector_leadership_context"],
            resolver_target_state="results_denominator_needed",
            review_lane="high_review_lane",
            blocker_reason="results/guidance cannot be read without expectation and denominator comparison",
            polarity=polarity,
            effect=effect,
        )
    if state in {"generic_financing_review_required"}:
        return financing_spec("generic_8k_financing", state, polarity, channel, effect)
    if state in {"strategic_investment_conditional", "mna_non_operating_review_required"}:
        return strategic_mna_spec(state, polarity, effect)
    if state == "severance_change_in_control_mixed":
        return governance_spec(state, polarity, effect, high=True, family="governance_change_in_control_enrichment")
    if state == "governance_quality_unknown":
        return governance_spec(state, polarity, effect, high=True, family="governance_management_change_enrichment")
    if state == "compensation_plan_neutral":
        return governance_spec(state, polarity, effect, high=False, family="governance_compensation_context")
    return base_spec(
        circuit_type="generic_8k_classifier",
        requirement_family="generic_8k_item_classifier_enrichment",
        missing_primitive_fields=["item_number", "agreement_family", "event_subtype", "operating_language", "raw_text_family"],
        required_denominators=["company_scale_if_applicable"],
        required_comparators=["prior_8k_family", "agreement_subtype"],
        required_timing_checks=["event_date", "filing_date", "amendment_date"],
        required_interaction_fields=["routed_source_circuit", "operating_transmission_context"],
        resolver_target_state="generic_8k_route_needed",
        review_lane="normal_review_lane",
        blocker_reason="generic 8-K must be routed before it can affect any brain layer",
        polarity=polarity,
        effect=effect,
    )


def financing_spec(circuit_type: str, state: str, polarity: str, channel: str, effect: str) -> dict[str, object]:
    return base_spec(
        circuit_type=circuit_type,
        requirement_family="financing_terms_enrichment",
        missing_primitive_fields=["instrument", "principal_amount", "coupon_or_cost", "maturity", "conversion_or_warrant_terms", "use_of_proceeds", "covenants", "closing_condition"],
        required_denominators=["cash", "debt", "market_cap", "shares_outstanding", "funding_need"],
        required_comparators=["prior_liquidity", "operating_runway", "dilution_threshold", "peer_financing_terms"],
        required_timing_checks=["announcement_date", "closing_date", "maturity_date", "conversion_period"],
        required_interaction_fields=["operating_catalyst_alignment", "dilution_overhang", "liquidity_rescue_risk", "price_absorption_context"],
        resolver_target_state="financing_terms_needed",
        review_lane="high_review_lane",
        blocker_reason="financing can fund growth or dilute holders; terms, use, and operating path are required",
        polarity=polarity,
        effect=effect,
    )


def strategic_mna_spec(state: str, polarity: str, effect: str) -> dict[str, object]:
    return base_spec(
        circuit_type="strategic_mna_investment",
        requirement_family="strategic_mna_enrichment",
        missing_primitive_fields=["counterparty_or_target", "consideration_mix", "deal_size", "business_description", "strategic_rationale", "synergy_or_capacity_language", "closing_conditions"],
        required_denominators=["market_cap", "revenue", "cash", "debt", "target_contribution_if_available"],
        required_comparators=["deal_size_vs_company_scale", "integration_burden", "prior_strategy"],
        required_timing_checks=["announcement_date", "expected_close", "approval_or_condition_dates"],
        required_interaction_fields=["strategic_fit", "integration_risk", "funding_or_dilution_context", "price_absorption_context"],
        resolver_target_state="strategic_mna_review",
        review_lane="high_review_lane",
        blocker_reason="strategic deal needs fit, scale, funding, and integration before economic interpretation",
        polarity=polarity,
        effect=effect,
    )


def governance_spec(state: str, polarity: str, effect: str, *, high: bool, family: str) -> dict[str, object]:
    return base_spec(
        circuit_type="governance_management",
        requirement_family=family,
        missing_primitive_fields=["role", "appointment_or_departure", "reason_if_stated", "key_person_relevance", "audit_or_control_language", "compensation_or_severance_terms"],
        required_denominators=["company_scale_if_compensation", "management_role_materiality"],
        required_comparators=["prior_governance_state", "peer_governance_norms"],
        required_timing_checks=["effective_date", "filing_date"],
        required_interaction_fields=["operating_execution_risk", "financing_or_control_context"],
        resolver_target_state="governance_quality_needed",
        review_lane="high_review_lane" if high else "normal_review_lane",
        blocker_reason="governance items are risk/context modifiers unless role, reason, and severity are known",
        polarity=polarity,
        effect=effect,
    )


def macro_policy_spec(state: str, polarity: str, channel: str, effect: str) -> dict[str, object]:
    return base_spec(
        circuit_type="macro_policy_transmission",
        requirement_family="macro_company_link_enrichment",
        missing_primitive_fields=["policy_event", "affected_sector", "company_specific_mention", "transmission_path", "duration_or_implementation_window"],
        required_denominators=["company_revenue_exposure", "theme_exposure", "sector_weight"],
        required_comparators=["theme_only_vs_company_specific", "prior_policy_state", "sector_leadership_state"],
        required_timing_checks=["policy_date", "implementation_date", "staleness_window"],
        required_interaction_fields=["theme_lifecycle_context", "company_catalyst_context", "macro_regime_context"],
        resolver_target_state="macro_company_link_needed",
        review_lane="normal_review_lane",
        blocker_reason="theme-only macro is context until company-specific transmission is established",
        polarity=polarity,
        effect=effect,
    )


def base_spec(
    *,
    circuit_type: str,
    requirement_family: str,
    missing_primitive_fields: list[str],
    required_denominators: list[str],
    required_comparators: list[str],
    required_timing_checks: list[str],
    required_interaction_fields: list[str],
    resolver_target_state: str,
    review_lane: str,
    blocker_reason: str,
    polarity: str,
    effect: str,
) -> dict[str, object]:
    return {
        "circuit_type": circuit_type,
        "requirement_family": requirement_family,
        "missing_primitive_fields": missing_primitive_fields,
        "required_denominators": required_denominators,
        "required_comparators": required_comparators,
        "required_timing_checks": required_timing_checks,
        "required_interaction_fields": required_interaction_fields,
        "resolver_target_state": resolver_target_state,
        "review_lane": review_lane,
        "blocker_reason": blocker_reason,
        "can_affect_confidence": ("confidence_modifier" in effect) or polarity in {"constructive", "conditional"},
        "can_affect_risk": ("risk_modifier" in effect) or polarity in {"adverse", "mixed", "conditional", "unknown"},
        "can_affect_slot": ("slot_modifier" in effect) or circuit_type in {"ownership_float_structure", "activist_control", "institutional_positioning", "macro_policy_transmission"},
    }


def review_lane_for(state: str, context: str) -> str:
    if state in HIGH_REVIEW_STATES:
        return "high_review_lane"
    if context in {"CreditFinancingContext"}:
        return "high_review_lane"
    return "normal_review_lane"


def pipe(values: list[str]) -> str:
    return "|".join(values)


def text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)
