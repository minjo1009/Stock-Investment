from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class SemanticTranslation:
    event_id: str
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    source_form_family: str
    context_type: str
    semantic_state: str
    semantic_polarity: str
    transmission_channel: str
    edge_effect: str
    target_layer: str
    confidence_modifier: str
    risk_modifier: str
    slot_modifier: str
    research_escalation: str
    rule_id: str
    required_next_evidence: str
    operating_connection_supported_flag: int
    buy_sell_signal_created_flag: int
    actionability_created_flag: int
    used_for_trading_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


def translate_context(row: pd.Series) -> dict[str, object]:
    context_type = str(row.get("context_type", ""))
    primitive = parse_json(row.get("primitive_fields_json"))
    states = states_set(row.get("interpretation_states"))

    if context_type == "CreditFinancingContext":
        result = translate_financing_context(primitive, states)
    elif context_type == "Generic8KClassificationContext":
        result = translate_generic_8k_context(primitive, states)
    elif context_type == "InsiderBehaviorContext":
        result = translate_insider_context(primitive, states)
    elif context_type == "ActivistControlContext":
        result = translate_activist_context(primitive, states)
    elif context_type == "InstitutionalPositioningContext":
        result = translate_positioning_context(primitive, states)
    elif context_type == "OwnershipStructureContext":
        result = translate_ownership_context(primitive, states)
    elif context_type == "MacroPolicyTransmissionContext":
        result = translate_macro_context(primitive, states)
    else:
        result = semantic_result(
            "source_gap_unknown",
            "unknown",
            "context_only",
            "research_escalation",
            "L1",
            "none",
            "none",
            "none",
            "source_route_review",
            "SOURCE_GAP_SEMANTIC_UNKNOWN",
            "source route and raw text",
        )

    return asdict(
        SemanticTranslation(
            event_id=str(row.get("event_id", "")),
            lifecycle_id=str(row.get("lifecycle_id", "")),
            symbol=str(row.get("symbol", "")),
            theme_id=str(row.get("theme_id", "")),
            entry_ts=str(row.get("entry_ts", "")),
            split_name=str(row.get("split_name", "")),
            source_form_family=str(row.get("source_form_family", "")),
            context_type=context_type,
            operating_connection_supported_flag=0,
            buy_sell_signal_created_flag=0,
            actionability_created_flag=0,
            used_for_trading_flag=0,
            backtest_eligible_flag=0,
            outcome_used_for_assignment_flag=0,
            **result,
        )
    )


def translate_financing_context(primitive: dict[str, object], states: set[str]) -> dict[str, object]:
    growth = "growth_funding_possible" in states
    dilution = "dilution_overhang_present" in states or "convertible_or_warrant_overhang_present" in states
    rescue = "liquidity_rescue_possible" in states
    refi = "debt_refinancing_context" in states
    if growth and dilution:
        return semantic_result("growth_funding_with_dilution_mixed", "mixed", "growth_funding|dilution_overhang", "risk_modifier|confidence_modifier", "L2|L5", "possible_positive_if_operating_path_exists", "dilution_cap", "none", "terms_review", "FINANCING_GROWTH_AND_DILUTION_MIXED", "use of proceeds, dilution size, conversion/warrant terms, price absorption, and operating path")
    if growth:
        return semantic_result("growth_funding_constructive", "constructive", "growth_funding", "confidence_modifier", "L2", "supports_execution_capacity_if_operating_path_exists", "none", "none", "proceeds_review", "FINANCING_GROWTH_FUNDING_MODIFIER", "use of proceeds, capacity link, denominator, and operating path")
    if dilution:
        return semantic_result("dilution_overhang_adverse", "adverse", "dilution_overhang", "risk_modifier", "L5", "none", "dilution_cap", "slot_penalty_possible", "terms_review", "FINANCING_DILUTION_OVERHANG_MODIFIER", "dilution size, hedge/capped call, conversion, warrant coverage, and price absorption")
    if rescue:
        return semantic_result("liquidity_rescue_conditional", "conditional", "liquidity_rescue", "risk_modifier|research_escalation", "L5", "none", "liquidity_stress_review", "none", "liquidity_review", "FINANCING_LIQUIDITY_RESCUE_CONDITIONAL", "runway, cash burn, going concern, maturity wall, and covenant detail")
    if refi:
        return semantic_result("debt_refinance_neutral_to_constructive", "neutral", "debt_refinance", "risk_modifier", "L5", "none", "maturity_relief_possible", "none", "terms_review", "FINANCING_REFINANCE_RISK_MODIFIER", "maturity relief, interest cost, covenant terms, and balance sheet impact")
    return semantic_result("terms_incomplete_unknown", "unknown", "context_only", "research_escalation", "L1", "none", "none", "none", "terms_missing", "FINANCING_TERMS_INCOMPLETE_UNKNOWN", "instrument type, size, proceeds, maturity, dilution, and liquidity terms")


def translate_generic_8k_context(primitive: dict[str, object], states: set[str]) -> dict[str, object]:
    family = str(primitive.get("agreement_family_state", ""))
    if family == "financing_credit_context":
        return semantic_result("generic_financing_review_required", "conditional", "dilution_overhang|growth_funding", "research_escalation", "L2|L5", "none", "financing_terms_unknown", "none", "financing_circuit_review", "GENERIC_8K_FINANCING_SEMANTIC_REVIEW", "financing terms, use of proceeds, dilution, liquidity, and operating path")
    if family == "strategic_investment_context":
        return semantic_result("strategic_investment_conditional", "conditional", "strategic_fit", "research_escalation|slot_modifier", "L2|L4", "strategic_fit_possible", "capital_allocation_risk", "special_situation_review", "strategic_investment_review", "STRATEGIC_INVESTMENT_CONDITIONAL_MODIFIER", "strategic rationale, ownership terms, counterparty quality, capital at risk, and operating link")
    if family == "strategic_mna_context":
        return semantic_result("mna_non_operating_review_required", "conditional", "strategic_fit|integration_risk", "research_escalation|risk_modifier", "L2|L5", "strategic_fit_possible", "integration_risk_unknown", "special_situation_review", "mna_transmission_review", "MNA_STRATEGIC_REVIEW_MODIFIER", "purchase price, consideration mix, acquired revenue/backlog/customers, synergy, integration, and denominator")
    if family in {"governance_board_context", "compensation_award_context", "severance_or_change_in_control_context"}:
        return translate_governance_family(family)
    if family == "financial_results_context":
        return semantic_result("financial_results_review_required", "unknown", "earnings_expectation", "research_escalation", "L2|L3", "none", "none", "none", "earnings_expectation_review", "FINANCIAL_RESULTS_NEED_EXPECTATION_TRANSLATION", "reported result, guidance, consensus/expectations, margin, revenue, and price absorption")
    return semantic_result("generic_8k_unclassified_unknown", "unknown", "context_only", "research_escalation", "L1", "none", "none", "none", "item_classifier_review", "GENERIC_8K_UNCLASSIFIED_SEMANTIC_UNKNOWN", "item type, source text, and circuit route")


def translate_governance_family(family: str) -> dict[str, object]:
    if family == "compensation_award_context":
        return semantic_result("compensation_plan_neutral", "neutral", "governance_quality", "context_only", "L1", "none", "none", "none", "none", "COMPENSATION_PLAN_NEUTRAL_CONTEXT", "none unless compensation change signals retention, dilution, or governance issue")
    if family == "severance_or_change_in_control_context":
        return semantic_result("severance_change_in_control_mixed", "mixed", "governance_quality|governance_disruption", "risk_modifier|research_escalation", "L5", "none", "change_in_control_or_retention_risk", "none", "governance_review", "SEVERANCE_CHANGE_CONTROL_MIXED_MODIFIER", "executive retention, change-in-control trigger, governance implication, and takeover context")
    return semantic_result("governance_quality_unknown", "unknown", "governance_quality", "context_only|research_escalation", "L1", "none", "none", "none", "governance_context_review", "GOVERNANCE_CONTEXT_REVIEW_MODIFIER", "board role, independence, executive departure/appointment reason, and operating relevance")


def translate_insider_context(primitive: dict[str, object], states: set[str]) -> dict[str, object]:
    sale = "insider_open_market_sale_observed" in states
    buy = "insider_open_market_buy_observed" in states
    automatic = "automatic_plan_or_admin_transaction" in states
    award = "option_exercise_or_award_observed" in states
    if buy:
        return semantic_result("open_market_buy_constructive_modifier", "constructive", "insider_alignment", "confidence_modifier", "L4", "alignment_positive", "none", "tie_breaker_possible", "role_and_size_review", "FORM4_OPEN_MARKET_BUY_CONSTRUCTIVE_MODIFIER", "insider role, dollar size, history, plan status, and cluster buying")
    if sale and automatic:
        return semantic_result("automatic_plan_sale_neutral_to_unknown", "unknown", "insider_sell_pressure", "context_only", "L1", "none", "none", "none", "plan_and_pattern_review", "FORM4_10B5_SALE_NEUTRAL_UNKNOWN", "10b5-1 plan details, sale size, role, and pattern")
    if sale:
        return semantic_result("open_market_sale_adverse_modifier", "adverse", "insider_sell_pressure", "risk_modifier", "L5", "none", "insider_sell_pressure", "slot_penalty_possible", "role_size_pattern_review", "FORM4_OPEN_MARKET_SALE_ADVERSE_MODIFIER", "insider role, sale size, ownership retained, plan status, and cluster selling")
    if award:
        return semantic_result("option_exercise_or_award_neutral", "neutral", "governance_quality", "context_only", "L1", "none", "none", "none", "none", "FORM4_AWARD_NEUTRAL_CONTEXT", "none unless unusual dilution or retention signal")
    return semantic_result("transaction_pattern_unknown", "unknown", "context_only", "research_escalation", "L1", "none", "none", "none", "transaction_type_review", "FORM4_TRANSACTION_PATTERN_UNKNOWN", "transaction code, role, size, plan status, and history")


def translate_activist_context(primitive: dict[str, object], states: set[str]) -> dict[str, object]:
    active = bool(primitive.get("active_13d_flag"))
    control = bool(primitive.get("control_intent_language_present"))
    passive = bool(primitive.get("passive_13g_flag"))
    if active and control:
        return semantic_result("activist_pressure_constructive_or_mixed", "mixed", "activist_pressure", "slot_modifier|research_escalation", "L4", "special_situation_possible", "governance_disruption_possible", "special_situation_review", "activist_intent_review", "ACTIVIST_CONTROL_MIXED_MODIFIER", "holder identity, purpose, board plan, ownership %, and company response")
    if active:
        return semantic_result("control_intent_conditional", "conditional", "activist_pressure", "research_escalation", "L4", "special_situation_possible", "none", "special_situation_review", "purpose_review", "ACTIVE_13D_CONDITIONAL_MODIFIER", "purpose of transaction, board/strategy language, and ownership change")
    if passive:
        return semantic_result("passive_ownership_neutral", "neutral", "ownership_concentration", "context_only", "L1", "none", "none", "none", "none", "PASSIVE_13G_NEUTRAL_CONTEXT", "none unless ownership change or float impact is material")
    return semantic_result("ownership_change_unknown", "unknown", "ownership_concentration", "research_escalation", "L1", "none", "none", "none", "ownership_purpose_review", "SCHEDULE_13D_13G_UNKNOWN", "active/passive status, owner, purpose, and percent")


def translate_positioning_context(primitive: dict[str, object], states: set[str]) -> dict[str, object]:
    if primitive.get("reported_position_value") is not None:
        return semantic_result("institutional_sponsorship_constructive_modifier", "constructive", "institutional_sponsorship", "context_only", "L3", "sponsorship_possible", "crowding_unknown", "none", "stale_positioning_review", "THIRTEENF_SPONSORSHIP_STALE_MODIFIER", "position change, manager quality, filing lag, and crowding")
    return semantic_result("positioning_snapshot_stale_neutral", "neutral", "institutional_sponsorship", "context_only", "L1", "none", "none", "none", "none", "THIRTEENF_STALE_NEUTRAL_CONTEXT", "none unless position change is available")


def translate_ownership_context(primitive: dict[str, object], states: set[str]) -> dict[str, object]:
    if primitive.get("ownership_percent") is not None:
        return semantic_result("holder_concentration_mixed", "mixed", "ownership_concentration|float_tightness", "risk_modifier|slot_modifier", "L4|L5", "sponsorship_possible", "liquidity_or_exit_risk_possible", "float_context_modifier", "holder_change_review", "OWNERSHIP_CONCENTRATION_MIXED_MODIFIER", "holder identity, ownership change, float, liquidity, and lockup/exit risk")
    return semantic_result("ownership_change_unknown", "unknown", "ownership_concentration", "research_escalation", "L1", "none", "none", "none", "holder_identity_review", "OWNERSHIP_CONTEXT_UNKNOWN", "holder identity, percent, and change")


def translate_macro_context(primitive: dict[str, object], states: set[str]) -> dict[str, object]:
    regulatory = "geopolitical_or_regulatory_risk_context" in states
    demand = "demand_transmission_possible" in states
    strong_link = "policy_tailwind_with_company_link" in states
    weak_link = "policy_tailwind_company_link_weak" in states
    if regulatory:
        return semantic_result("regulatory_risk_adverse", "adverse", "regulatory_risk", "risk_modifier", "L5", "none", "policy_or_regulatory_risk", "slot_penalty_possible", "exposure_review", "MACRO_REGULATORY_RISK_MODIFIER", "company exposure, rule path, timing, and offsetting demand")
    if demand and strong_link:
        return semantic_result("company_link_strong_modifier", "constructive", "policy_tailwind", "confidence_modifier", "L2", "demand_tailwind_possible", "none", "tie_breaker_possible", "company_link_review", "MACRO_COMPANY_LINK_CONSTRUCTIVE_MODIFIER", "company-specific policy link, demand mechanism, and denominator")
    if demand or weak_link:
        return semantic_result("policy_transmission_conditional", "conditional", "policy_tailwind", "research_escalation", "L2", "theme_tailwind_possible", "none", "none", "company_link_review", "MACRO_POLICY_TRANSMISSION_CONDITIONAL", "company anchor, theme linkage, budget/procurement channel, and timing")
    return semantic_result("macro_theme_only_neutral", "neutral", "theme_context", "context_only", "L1", "none", "none", "none", "none", "MACRO_THEME_ONLY_NEUTRAL_CONTEXT", "none unless company link or explicit transmission emerges")


def semantic_result(
    semantic_state: str,
    semantic_polarity: str,
    transmission_channel: str,
    edge_effect: str,
    target_layer: str,
    confidence_modifier: str,
    risk_modifier: str,
    slot_modifier: str,
    research_escalation: str,
    rule_id: str,
    required_next_evidence: str,
) -> dict[str, object]:
    return {
        "semantic_state": semantic_state,
        "semantic_polarity": semantic_polarity,
        "transmission_channel": transmission_channel,
        "edge_effect": edge_effect,
        "target_layer": target_layer,
        "confidence_modifier": confidence_modifier,
        "risk_modifier": risk_modifier,
        "slot_modifier": slot_modifier,
        "research_escalation": research_escalation,
        "rule_id": rule_id,
        "required_next_evidence": required_next_evidence,
    }


def states_set(value: object) -> set[str]:
    if value is None or pd.isna(value):
        return set()
    return {item for item in str(value).split("|") if item}


def parse_json(value: object) -> dict[str, object]:
    if value is None or pd.isna(value):
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
