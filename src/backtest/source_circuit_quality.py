from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import pandas as pd


OPERATING_CONTEXT = "OperatingCatalystContext"
NON_OPERATING_CONTEXTS = {
    "InsiderBehaviorContext",
    "ActivistControlContext",
    "InstitutionalPositioningContext",
    "OwnershipStructureContext",
}


@dataclass(frozen=True)
class ContextQuality:
    event_id: str
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    source_form_family: str
    context_type: str
    quality_state: str
    classification_state: str
    permission_state: str
    operating_path_visibility_state: str
    connection_rule_id: str
    required_next_evidence: str
    can_create_operating_fact_flag: int
    can_create_operating_connection_flag: int
    used_for_trading_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


@dataclass(frozen=True)
class QualityEdge:
    event_id: str
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    source_context_type: str
    target_context_type: str
    relation_type: str
    rule_id: str
    permission_state: str
    quality_state: str
    effect_state: str
    used_for_trading_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


def build_context_quality(contexts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_visibility = build_group_operating_visibility(contexts)
    quality_rows = []
    edge_rows = []
    for _, row in contexts.iterrows():
        group_key = tuple(row.get(col, "") for col in ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"])
        visible = group_visibility.get(group_key, "operating_path_not_visible")
        quality = evaluate_context(row, visible)
        edge = build_quality_edge(row, quality)
        quality_rows.append(asdict(quality))
        edge_rows.append(asdict(edge))
    return pd.DataFrame(quality_rows), pd.DataFrame(edge_rows)


def build_group_operating_visibility(contexts: pd.DataFrame) -> dict[tuple[object, ...], str]:
    visibility: dict[tuple[object, ...], str] = {}
    keys = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
    for key, group in contexts.groupby(keys, dropna=False):
        states = "|".join(group["interpretation_states"].fillna("").astype(str).tolist())
        if any(
            token in states
            for token in [
                "generic_8k_operating_transmission_candidate",
                "generic_8k_operating_transmission_supported",
                "policy_tailwind_with_company_link",
            ]
        ):
            visibility[key] = "operating_path_visible_in_candidate_context"
        elif "policy_tailwind_company_link_weak" in states or "demand_transmission_possible" in states:
            visibility[key] = "operating_path_weak_or_indirect"
        else:
            visibility[key] = "operating_path_not_visible"
    return visibility


def evaluate_context(row: pd.Series, visibility: str) -> ContextQuality:
    context_type = str(row.get("context_type", ""))
    primitive = parse_json(row.get("primitive_fields_json"))
    states = states_set(row.get("interpretation_states"))

    if context_type == "InsiderBehaviorContext":
        quality_state, classification_state = insider_quality(primitive, states)
        permission, rule, evidence, can_connect = "modifier_only", "INSIDER_MODIFIER_ONLY", "operating catalyst must exist separately", 0
    elif context_type == "ActivistControlContext":
        quality_state, classification_state = activist_quality(primitive, states)
        permission, rule, evidence, can_connect = "modifier_only", "ACTIVIST_CONTROL_SPECIAL_SITUATION_MODIFIER_ONLY", "purpose language and governance path review", 0
    elif context_type == "InstitutionalPositioningContext":
        quality_state, classification_state = positioning_quality(primitive, states)
        permission, rule, evidence, can_connect = "modifier_only", "THIRTEENF_POSITIONING_MODIFIER_ONLY", "position change and filing lag review", 0
    elif context_type == "OwnershipStructureContext":
        quality_state, classification_state = ownership_quality(primitive, states)
        permission, rule, evidence, can_connect = "modifier_only", "OWNERSHIP_STRUCTURE_MODIFIER_ONLY", "holder identity and float change review", 0
    elif context_type == "CreditFinancingContext":
        quality_state, classification_state = financing_quality(primitive, states)
        permission, rule, evidence, can_connect = financing_permission(states, visibility)
    elif context_type == "Generic8KClassificationContext":
        quality_state, classification_state = generic_8k_quality(primitive, states)
        permission, rule, evidence, can_connect = generic_8k_permission(primitive, states)
    elif context_type == "MacroPolicyTransmissionContext":
        quality_state, classification_state = macro_quality(primitive, states)
        permission, rule, evidence, can_connect = macro_permission(states)
    else:
        quality_state, classification_state = "source_gap_quality_unknown", "source_gap_unclassified"
        permission, rule, evidence, can_connect = "review_required", "SOURCE_GAP_REVIEW_REQUIRED", "source route and raw text", 0

    return ContextQuality(
        event_id=str(row.get("event_id", "")),
        lifecycle_id=str(row.get("lifecycle_id", "")),
        symbol=str(row.get("symbol", "")),
        theme_id=str(row.get("theme_id", "")),
        entry_ts=str(row.get("entry_ts", "")),
        split_name=str(row.get("split_name", "")),
        source_form_family=str(row.get("source_form_family", "")),
        context_type=context_type,
        quality_state=quality_state,
        classification_state=classification_state,
        permission_state=permission,
        operating_path_visibility_state=visibility,
        connection_rule_id=rule,
        required_next_evidence=evidence,
        can_create_operating_fact_flag=0,
        can_create_operating_connection_flag=can_connect,
        used_for_trading_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
    )


def build_quality_edge(row: pd.Series, quality: ContextQuality) -> QualityEdge:
    relation_type = {
        "connection_supported": "reinforcing_review_only",
        "connection_candidate": "candidate_edge_review_only",
        "review_required": "prerequisite_review_required",
        "not_applicable": "non_operating_or_not_applicable",
        "modifier_only": "modifier_only",
    }.get(quality.permission_state, "review_only")
    target = OPERATING_CONTEXT if quality.can_create_operating_connection_flag else non_operating_target(str(row.get("context_type", "")))
    return QualityEdge(
        event_id=quality.event_id,
        lifecycle_id=quality.lifecycle_id,
        symbol=quality.symbol,
        theme_id=quality.theme_id,
        entry_ts=quality.entry_ts,
        split_name=quality.split_name,
        source_context_type=quality.context_type,
        target_context_type=target,
        relation_type=relation_type,
        rule_id=quality.connection_rule_id,
        permission_state=quality.permission_state,
        quality_state=quality.quality_state,
        effect_state=effect_state(quality.permission_state),
        used_for_trading_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
    )


def insider_quality(primitive: dict[str, object], states: set[str]) -> tuple[str, str]:
    has_type = any(s in states for s in ["insider_open_market_buy_observed", "insider_open_market_sale_observed", "option_exercise_or_award_observed"])
    has_role = bool(primitive.get("director_or_officer_language_present"))
    if has_type and has_role:
        return "insider_context_complete", "insider_transaction_classified"
    if has_type or has_role:
        return "insider_context_partial", "insider_transaction_partially_classified"
    return "insider_context_sparse", "insider_transaction_unclassified"


def activist_quality(primitive: dict[str, object], states: set[str]) -> tuple[str, str]:
    has_schedule = bool(primitive.get("active_13d_flag") or primitive.get("passive_13g_flag"))
    has_pct = primitive.get("beneficial_ownership_percent") is not None
    has_purpose = bool(primitive.get("control_intent_language_present"))
    if has_schedule and has_pct and has_purpose:
        return "control_context_complete", "active_passive_and_purpose_classified"
    if has_schedule or has_pct or has_purpose:
        return "control_context_partial", "active_passive_or_ownership_classified"
    return "control_context_sparse", "control_context_unclassified"


def positioning_quality(primitive: dict[str, object], states: set[str]) -> tuple[str, str]:
    if primitive.get("reported_position_value") is not None and primitive.get("institutional_manager_language_present"):
        return "positioning_context_complete", "positioning_snapshot_classified"
    return "positioning_context_partial", "positioning_snapshot_stale_by_design"


def ownership_quality(primitive: dict[str, object], states: set[str]) -> tuple[str, str]:
    if primitive.get("ownership_percent") is not None and primitive.get("beneficial_owner_language_present"):
        return "ownership_context_complete", "holder_and_percent_classified"
    return "ownership_context_partial", "ownership_structure_partially_classified"


def financing_quality(primitive: dict[str, object], states: set[str]) -> tuple[str, str]:
    has_amount = primitive.get("principal_amount") is not None
    has_terms = any(primitive.get(key) for key in ["conversion_feature_flag", "warrant_flag", "atm_or_shelf_flag", "covenant_language_present"])
    has_use = any(primitive.get(key) for key in ["growth_use_of_proceeds_flag", "liquidity_language_present", "debt_refinance_language_present"])
    if has_amount and has_terms and has_use:
        return "financing_terms_complete", financing_classification(states)
    if has_amount or has_terms or has_use:
        return "financing_terms_partial", financing_classification(states)
    return "financing_terms_sparse", "financing_terms_incomplete"


def financing_classification(states: set[str]) -> str:
    labels = []
    if "growth_funding_possible" in states:
        labels.append("growth_funding_context")
    if "dilution_overhang_present" in states:
        labels.append("dilution_overhang_context")
    if "liquidity_rescue_possible" in states:
        labels.append("liquidity_rescue_context")
    if "debt_refinancing_context" in states:
        labels.append("debt_refinance_context")
    return "|".join(labels) if labels else "financing_terms_incomplete"


def financing_permission(states: set[str], visibility: str) -> tuple[str, str, str, int]:
    if "growth_funding_possible" in states and visibility == "operating_path_visible_in_candidate_context":
        return "connection_supported", "FINANCING_GROWTH_FUNDING_SUPPORTS_EXECUTION", "denominator and execution-capacity evidence", 1
    if "growth_funding_possible" in states:
        return "connection_candidate", "FINANCING_GROWTH_FUNDING_NEEDS_VISIBLE_OPERATING_PATH", "visible order/backlog/revenue path", 1
    if "dilution_overhang_present" in states:
        return "review_required", "FINANCING_DILUTION_CAPS_OPERATING_CONFIDENCE", "dilution size, hedge, absorption, and operating path", 0
    if "liquidity_rescue_possible" in states:
        return "review_required", "LIQUIDITY_RESCUE_REQUIRES_SEPARATE_REVIEW", "runway, going-concern, and use-of-proceeds details", 0
    if "debt_refinancing_context" in states:
        return "review_required", "DEBT_REFINANCE_NEUTRAL_UNTIL_LINKED", "maturity relief and covenant details", 0
    return "review_required", "INCOMPLETE_TERMS_NO_OPERATING_LINK", "instrument type, proceeds, maturity, dilution terms", 0


def generic_8k_quality(primitive: dict[str, object], states: set[str]) -> tuple[str, str]:
    family = primitive.get("agreement_family_state")
    transmission = primitive.get("operating_transmission_state")
    if family and transmission:
        quality = "classified_8k"
        if family == "unclassified_generic_8k_context":
            quality = "unclassified_8k"
        elif transmission == "no_operating_transmission":
            quality = "classified_8k_non_operating"
        elif transmission == "operating_transmission_supported":
            quality = "classified_8k_operating_transmission_supported"
        elif transmission == "operating_transmission_candidate":
            quality = "classified_8k_operating_transmission_candidate"
        return quality, f"{family}|{transmission}"
    item_numbers = primitive.get("item_numbers") or []
    flags = sum(int(bool(primitive.get(key))) for key in ["financing_language_flag", "operating_language_flag", "governance_flag", "financial_statement_flag"])
    if item_numbers and flags:
        return "classified_8k", generic_8k_classification(states)
    if item_numbers or flags:
        return "partially_classified_8k", generic_8k_classification(states)
    return "unclassified_8k", "unclassified_8k"


def generic_8k_classification(states: set[str]) -> str:
    labels = []
    if "generic_8k_operating_context_possible" in states:
        labels.append("operating_language_present")
    if "generic_8k_financing_context" in states:
        labels.append("financing_route_context")
    if "generic_8k_governance_context" in states:
        labels.append("governance_only_context")
    if "generic_8k_financial_statement_context" in states:
        labels.append("financial_statement_context")
    return "|".join(labels) if labels else "unclassified_8k"


def generic_8k_permission(primitive: dict[str, object], states: set[str]) -> tuple[str, str, str, int]:
    permission = primitive.get("permission_state")
    rule = primitive.get("connection_rule_id")
    evidence = primitive.get("required_next_evidence")
    if permission and rule and evidence:
        can_connect = int(str(permission) in {"connection_candidate", "connection_supported"})
        return str(permission), str(rule), str(evidence), can_connect
    item_numbers = set(str(x) for x in (primitive.get("item_numbers") or []))
    if "generic_8k_operating_context_possible" in states and "1.01" in item_numbers:
        return "connection_supported", "MATERIAL_AGREEMENT_OPERATING_CANDIDATE", "contract economics, customer, duration, and denominator", 1
    if "generic_8k_operating_context_possible" in states:
        return "connection_candidate", "OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL", "item number and economic detail", 1
    if "generic_8k_financing_context" in states:
        return "review_required", "ROUTE_TO_FINANCING_CIRCUIT", "financing terms and use of proceeds", 0
    if "generic_8k_governance_context" in states:
        return "not_applicable", "GOVERNANCE_8K_NON_OPERATING", "governance circuit only", 0
    return "review_required", "UNCLASSIFIED_8K_REVIEW_REQUIRED", "item classifier and raw text review", 0


def macro_quality(primitive: dict[str, object], states: set[str]) -> tuple[str, str]:
    company = bool(primitive.get("company_mentioned_flag"))
    transmission = any(primitive.get(key) for key in ["demand_language_present", "regulatory_or_budget_language_present", "supply_chain_language_present"])
    if company and transmission:
        return "macro_link_complete", "strong_company_link_context"
    if transmission:
        return "macro_link_partial", "theme_or_weak_company_link_context"
    return "macro_theme_only", "theme_only_context"


def macro_permission(states: set[str]) -> tuple[str, str, str, int]:
    if "policy_tailwind_with_company_link" in states and "demand_transmission_possible" in states:
        return "connection_supported", "POLICY_WITH_COMPANY_LINK_REINFORCES_OPERATING_PATH", "company-specific demand transmission and denominator", 1
    if "policy_tailwind_company_link_weak" in states or "demand_transmission_possible" in states or "supply_chain_transmission_possible" in states:
        return "connection_candidate", "MACRO_THEME_TAILWIND_NEEDS_COMPANY_LINK", "company anchor and transmission path", 1
    if "geopolitical_or_regulatory_risk_context" in states:
        return "review_required", "REGULATORY_RISK_CAPS_ECONOMIC_CONFIDENCE", "company exposure and regulatory mechanism", 0
    return "not_applicable", "MACRO_THEME_ONLY_NOT_SINGLE_NAME", "company link", 0


def non_operating_target(context_type: str) -> str:
    return {
        "InsiderBehaviorContext": "SlotConfidenceContext",
        "ActivistControlContext": "SpecialSituationReviewContext",
        "InstitutionalPositioningContext": "CrowdingRiskContext",
        "OwnershipStructureContext": "LiquidityAndFloatRiskContext",
    }.get(context_type, "ResearchReviewContext")


def effect_state(permission: str) -> str:
    return {
        "connection_supported": "operating_connection_supported_review_only",
        "connection_candidate": "operating_connection_candidate_review_only",
        "review_required": "additional_evidence_required_before_connection",
        "not_applicable": "operating_connection_not_applicable",
        "modifier_only": "non_operating_modifier_context_only",
    }.get(permission, "review_only")


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
