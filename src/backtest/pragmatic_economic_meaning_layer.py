from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class PragmaticEconomicMeaningPacket:
    lifecycle_id: str
    source_event_id: str
    symbol: str
    event_date: str
    tradable_after_dt: str
    source_form_family: str
    source_circuit: str
    requirement_family: str
    task741_meaning_state: str
    task741_missing_blocker_states: str
    interpretation_state: str
    economic_direction_hint: str
    confidence_band: str
    ambiguity_flags: str
    soft_uncertainty_flags: str
    hard_blocker_flags: str
    needed_confirmation: str
    usable_without_missing_source_flag: int
    relation_ready_flag: int
    relation_ready_tier: str
    can_create_directional_edge_flag: int
    can_create_structural_edge_flag: int
    context_attachment_only_flag: int
    direction_hint_trade_instruction_flag: int
    asof_change_inference_forbidden_flag: int
    relation_ready_reason: str
    pragmatic_basis_json: str
    evidence_trace_json: str
    forbidden_layer_effects: str
    trade_output_flag: int
    score_output_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int
    rule_id: str


def build_pragmatic_economic_meaning_packets(
    task741_packets: pd.DataFrame,
    task740_primitives: pd.DataFrame,
) -> pd.DataFrame:
    primitive_map = {str(row["source_event_id"]): row for _, row in task740_primitives.iterrows()}
    rows = []
    for _, row in task741_packets.iterrows():
        primitive_row = primitive_map.get(str(row["source_event_id"]), pd.Series(dtype=object))
        primitive = parse_json(primitive_row.get("primitive_fields_json"))
        denominators = parse_json(row.get("attached_denominators_json"))
        comparators = parse_json(row.get("attached_comparators_json"))
        availability = parse_json(row.get("source_availability_json"))
        timing = parse_json(row.get("timing_asof_checks_json"))
        interpretation = interpret_row(row, primitive, denominators, comparators, availability, timing)
        rows.append(asdict(packet_from_interpretation(row, primitive_row, interpretation)))
    return pd.DataFrame(rows)


def packet_from_interpretation(
    row: pd.Series,
    primitive_row: pd.Series,
    interpretation: dict[str, Any],
) -> PragmaticEconomicMeaningPacket:
    hard = interpretation["hard_blocker_flags"]
    relation_tier = relation_ready_tier(interpretation)
    relation_ready = int(relation_tier != "not_ready")
    usable = int(is_usable_without_missing_source(interpretation))
    return PragmaticEconomicMeaningPacket(
        lifecycle_id=text(row.get("lifecycle_id")),
        source_event_id=text(row.get("source_event_id")),
        symbol=text(row.get("symbol")),
        event_date=text(row.get("event_date")),
        tradable_after_dt=text(row.get("tradable_after_dt")),
        source_form_family=text(row.get("source_form_family")),
        source_circuit=text(row.get("source_circuit")),
        requirement_family=text(row.get("requirement_family")),
        task741_meaning_state=text(row.get("meaning_state")),
        task741_missing_blocker_states=text(row.get("missing_blocker_states")),
        interpretation_state=interpretation["interpretation_state"],
        economic_direction_hint=interpretation["economic_direction_hint"],
        confidence_band=interpretation["confidence_band"],
        ambiguity_flags="|".join(sorted(interpretation["ambiguity_flags"])),
        soft_uncertainty_flags="|".join(sorted(interpretation["soft_uncertainty_flags"])),
        hard_blocker_flags="|".join(sorted(hard)),
        needed_confirmation="|".join(sorted(interpretation["needed_confirmation"])),
        usable_without_missing_source_flag=usable,
        relation_ready_flag=relation_ready,
        relation_ready_tier=relation_tier,
        can_create_directional_edge_flag=int(relation_tier == "directional"),
        can_create_structural_edge_flag=int(relation_tier == "structural_mixed"),
        context_attachment_only_flag=int(relation_tier == "context_only"),
        direction_hint_trade_instruction_flag=0,
        asof_change_inference_forbidden_flag=1,
        relation_ready_reason=relation_ready_reason(relation_ready, interpretation),
        pragmatic_basis_json=json.dumps(interpretation["basis"], ensure_ascii=False, sort_keys=True),
        evidence_trace_json=json.dumps(
            {
                "task740_primitive_rule_id": text(primitive_row.get("rule_id")),
                "task741_rule_id": text(row.get("rule_id")),
                "source_event_id": text(row.get("source_event_id")),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        forbidden_layer_effects="buy_sell|score_rank|trade_ready|backtest_ready|outcome_label",
        trade_output_flag=0,
        score_output_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
        rule_id="TASK742_PRAGMATIC_ECONOMIC_MEANING_REVIEW_ONLY",
    )


def interpret_row(
    row: pd.Series,
    primitive: dict[str, Any],
    denominators: dict[str, Any],
    comparators: dict[str, Any],
    availability: dict[str, Any],
    timing: dict[str, Any],
) -> dict[str, Any]:
    base = empty_interpretation()
    if not timing.get("no_future_data_used", True):
        base["hard_blocker_flags"].add("future_data_violation")
    if not availability.get("has_task740_primitive"):
        base["hard_blocker_flags"].add("primitive_missing")
    if not availability.get("has_raw_text_path"):
        base["hard_blocker_flags"].add("raw_text_missing")
    if base["hard_blocker_flags"]:
        base["interpretation_state"] = "economic_context_unusable"
        base["confidence_band"] = "insufficient"
        base["economic_direction_hint"] = "unknown"
        return base

    circuit = text(row.get("source_circuit"))
    if circuit == "form4_insider_behavior":
        return interpret_form4(primitive, denominators, comparators, base)
    if circuit in {"ownership_float_structure", "activist_control"}:
        return interpret_ownership(circuit, primitive, denominators, comparators, base)
    if circuit == "credit_financing":
        return interpret_financing(primitive, denominators, comparators, base)
    if circuit == "financial_results_guidance":
        return interpret_financial_results(primitive, denominators, base)
    if circuit == "generic_8k_classifier":
        return interpret_generic_8k(primitive, base)
    base["interpretation_state"] = "source_circuit_context_unknown"
    base["confidence_band"] = "low"
    base["economic_direction_hint"] = "unknown"
    base["soft_uncertainty_flags"].add("unsupported_source_circuit")
    base["needed_confirmation"].add("manual_source_circuit_review")
    return base


def interpret_form4(
    primitive: dict[str, Any],
    denominators: dict[str, Any],
    comparators: dict[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    buy = truthy(primitive.get("open_market_buy_flag"))
    sale = truthy(primitive.get("open_market_sale_flag"))
    award = truthy(primitive.get("award_grant_flag")) or truthy(primitive.get("option_exercise_flag"))
    plan = truthy(primitive.get("planned_10b5_1_flag")) or truthy(primitive.get("tenb5_instruction_present_flag"))
    size_known = any(
        value is not None
        for value in [
            comparators.get("shares_changed_pct_of_ownership_after"),
            comparators.get("shares_changed_pct_of_shares_outstanding"),
            denominators.get("estimated_transaction_value"),
        ]
    )
    if buy and not award:
        base["interpretation_state"] = "form4_open_market_buy_economic_hint"
        base["economic_direction_hint"] = "positive"
        base["confidence_band"] = "medium" if size_known else "low"
        base["needed_confirmation"].add("price_absorption_after_filing")
    elif sale and (plan or award):
        base["interpretation_state"] = "form4_sale_plan_or_compensation_context"
        base["economic_direction_hint"] = "neutral"
        base["confidence_band"] = "medium" if size_known else "low"
        base["ambiguity_flags"].add("sale_may_be_plan_or_compensation")
    elif sale:
        base["interpretation_state"] = "form4_open_market_sale_economic_hint"
        base["economic_direction_hint"] = "negative"
        base["confidence_band"] = "medium" if size_known else "low"
        base["needed_confirmation"].add("check_clustered_insider_selling")
    else:
        base["interpretation_state"] = "form4_non_directional_insider_context"
        base["economic_direction_hint"] = "neutral"
        base["confidence_band"] = "low"
        base["ambiguity_flags"].add("transaction_code_not_directional")
    if not size_known:
        base["soft_uncertainty_flags"].add("transaction_scale_soft_unknown")
    if denominators.get("market_cap_proxy") is None:
        base["soft_uncertainty_flags"].add("market_scale_unknown")
    base["basis"].update(
        {
            "open_market_buy_flag": int(buy),
            "open_market_sale_flag": int(sale),
            "plan_or_award_flag": int(plan or award),
            "size_known_flag": int(size_known),
        }
    )
    return base


def interpret_ownership(
    circuit: str,
    primitive: dict[str, Any],
    denominators: dict[str, Any],
    comparators: dict[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    ownership_percent = numeric(primitive.get("ownership_percent"))
    active = truthy(primitive.get("active_13d_flag")) or truthy(primitive.get("control_language_present_flag"))
    passive = truthy(primitive.get("passive_13g_flag"))
    holder_known = truthy(primitive.get("holder_name_present_flag"))
    if active:
        base["interpretation_state"] = "ownership_active_control_context"
        base["economic_direction_hint"] = "mixed"
        base["confidence_band"] = "medium" if ownership_percent is not None else "low"
        base["needed_confirmation"].add("control_intent_and_operating_plan_review")
    elif passive and ownership_percent is not None:
        base["interpretation_state"] = "ownership_passive_large_holder_context"
        base["economic_direction_hint"] = "neutral"
        base["confidence_band"] = "medium"
    elif ownership_percent is not None:
        base["interpretation_state"] = "ownership_percent_source_context"
        base["economic_direction_hint"] = "neutral"
        base["confidence_band"] = "medium"
    elif denominators.get("market_cap_proxy") is not None:
        base["interpretation_state"] = "ownership_market_scale_context_only"
        base["economic_direction_hint"] = "unknown"
        base["confidence_band"] = "low"
        base["soft_uncertainty_flags"].add("ownership_percent_missing_soft")
    else:
        base["interpretation_state"] = "ownership_context_too_thin"
        base["economic_direction_hint"] = "unknown"
        base["confidence_band"] = "low"
        base["soft_uncertainty_flags"].add("ownership_percent_missing_soft")
    if not holder_known:
        base["soft_uncertainty_flags"].add("holder_identity_soft_unknown")
    if denominators.get("public_float_usd") is None:
        base["soft_uncertainty_flags"].add("float_precision_unknown")
    base["basis"].update(
        {
            "source_circuit": circuit,
            "ownership_percent": ownership_percent,
            "active_control_flag": int(active),
            "passive_holder_flag": int(passive),
            "holder_known_flag": int(holder_known),
        }
    )
    return base


def interpret_financing(
    primitive: dict[str, Any],
    denominators: dict[str, Any],
    comparators: dict[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    principal = numeric(primitive.get("principal_amount"))
    growth = truthy(primitive.get("growth_use_language_flag"))
    liquidity = truthy(primitive.get("liquidity_rescue_language_flag"))
    refi = truthy(primitive.get("debt_refinance_language_flag"))
    dilution = any(
        truthy(primitive.get(key))
        for key in ["instrument_convertible_flag", "instrument_warrant_flag", "instrument_atm_or_shelf_flag", "dilution_overhang_language_flag"]
    )
    has_cash_debt_scale = comparators.get("principal_pct_of_cash") is not None or comparators.get("principal_pct_of_debt") is not None
    has_market_scale = comparators.get("principal_pct_of_market_cap") is not None
    if principal is None:
        base["interpretation_state"] = "financing_terms_context_without_size"
        base["economic_direction_hint"] = "mixed" if growth or dilution or liquidity or refi else "unknown"
        base["confidence_band"] = "low"
        base["soft_uncertainty_flags"].add("principal_amount_missing_soft")
    elif growth and not dilution:
        base["interpretation_state"] = "financing_growth_funding_size_known"
        base["economic_direction_hint"] = "positive"
        base["confidence_band"] = "medium" if has_cash_debt_scale or has_market_scale else "low"
        base["needed_confirmation"].add("operating_catalyst_alignment")
    elif liquidity or refi:
        base["interpretation_state"] = "financing_liquidity_or_refi_size_known"
        base["economic_direction_hint"] = "mixed"
        base["confidence_band"] = "medium" if has_cash_debt_scale else "low"
        base["needed_confirmation"].add("balance_sheet_stress_review")
    elif dilution:
        base["interpretation_state"] = "financing_dilution_overhang_size_known"
        base["economic_direction_hint"] = "negative"
        base["confidence_band"] = "medium" if has_market_scale else "low"
        base["needed_confirmation"].add("price_absorption_and_use_of_proceeds_review")
    else:
        base["interpretation_state"] = "financing_size_known_terms_ambiguous"
        base["economic_direction_hint"] = "mixed"
        base["confidence_band"] = "low"
        base["ambiguity_flags"].add("use_of_proceeds_unclear")
    if principal is not None and not has_market_scale:
        base["soft_uncertainty_flags"].add("size_known_but_market_scale_unknown")
    if dilution:
        base["ambiguity_flags"].add("dilution_terms_need_resolution")
    base["basis"].update(
        {
            "principal_amount": principal,
            "growth_use_flag": int(growth),
            "liquidity_or_refi_flag": int(liquidity or refi),
            "dilution_flag": int(dilution),
            "has_cash_debt_scale": int(has_cash_debt_scale),
            "has_market_scale": int(has_market_scale),
        }
    )
    return base


def interpret_financial_results(
    primitive: dict[str, Any],
    denominators: dict[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    raise_flag = truthy(primitive.get("guidance_raise_flag"))
    cut_flag = truthy(primitive.get("guidance_cut_flag"))
    reaffirm = truthy(primitive.get("guidance_reaffirm_flag"))
    backlog = truthy(primitive.get("backlog_or_order_language_flag"))
    margin = truthy(primitive.get("margin_language_flag"))
    revenue_baseline = denominators.get("revenue") is not None
    if raise_flag and margin:
        base["interpretation_state"] = "guidance_raise_with_margin_language"
        base["economic_direction_hint"] = "positive"
        base["confidence_band"] = "medium"
    elif raise_flag or backlog:
        base["interpretation_state"] = "growth_or_backlog_language_context"
        base["economic_direction_hint"] = "positive"
        base["confidence_band"] = "medium" if revenue_baseline else "low"
    elif cut_flag:
        base["interpretation_state"] = "guidance_cut_context"
        base["economic_direction_hint"] = "negative"
        base["confidence_band"] = "medium" if revenue_baseline else "low"
    elif reaffirm:
        base["interpretation_state"] = "guidance_reaffirm_low_novelty_context"
        base["economic_direction_hint"] = "neutral"
        base["confidence_band"] = "low"
        base["ambiguity_flags"].add("reaffirm_is_low_novelty")
    else:
        base["interpretation_state"] = "financial_results_source_only_context"
        base["economic_direction_hint"] = "unknown"
        base["confidence_band"] = "low"
        base["soft_uncertainty_flags"].add("expectation_comparator_missing_soft")
    if not revenue_baseline:
        base["soft_uncertainty_flags"].add("revenue_baseline_missing_soft")
    base["needed_confirmation"].add("price_acceptance_after_result")
    base["basis"].update(
        {
            "guidance_raise_flag": int(raise_flag),
            "guidance_cut_flag": int(cut_flag),
            "guidance_reaffirm_flag": int(reaffirm),
            "backlog_or_order_language_flag": int(backlog),
            "margin_language_flag": int(margin),
            "revenue_baseline_flag": int(revenue_baseline),
        }
    )
    return base


def interpret_generic_8k(primitive: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    financing = truthy(primitive.get("financing_flag"))
    mna = truthy(primitive.get("mna_flag"))
    governance = truthy(primitive.get("governance_flag")) or truthy(primitive.get("compensation_flag"))
    operating = truthy(primitive.get("operating_supported_flag")) or truthy(primitive.get("operating_candidate_flag"))
    if financing:
        base["interpretation_state"] = "generic_8k_financing_route_modifier"
        base["economic_direction_hint"] = "mixed"
        base["confidence_band"] = "low"
        base["needed_confirmation"].add("route_to_financing_interpreter")
    elif mna:
        base["interpretation_state"] = "generic_8k_mna_route_modifier"
        base["economic_direction_hint"] = "mixed"
        base["confidence_band"] = "low"
        base["needed_confirmation"].add("strategic_fit_and_price_review")
    elif governance:
        base["interpretation_state"] = "generic_8k_governance_context_modifier"
        base["economic_direction_hint"] = "neutral"
        base["confidence_band"] = "low"
    elif operating:
        base["interpretation_state"] = "generic_8k_operating_candidate_unconfirmed"
        base["economic_direction_hint"] = "unknown"
        base["confidence_band"] = "low"
        base["soft_uncertainty_flags"].add("explicit_operating_transmission_missing_soft")
        base["needed_confirmation"].add("source_text_operating_transmission_review")
    else:
        base["interpretation_state"] = "generic_8k_non_operating_context"
        base["economic_direction_hint"] = "neutral"
        base["confidence_band"] = "low"
    base["basis"].update(
        {
            "financing_route_flag": int(financing),
            "mna_route_flag": int(mna),
            "governance_route_flag": int(governance),
            "operating_candidate_flag": int(operating),
        }
    )
    return base


def empty_interpretation() -> dict[str, Any]:
    return {
        "interpretation_state": "economic_context_unusable",
        "economic_direction_hint": "unknown",
        "confidence_band": "insufficient",
        "ambiguity_flags": set(),
        "soft_uncertainty_flags": set(),
        "hard_blocker_flags": set(),
        "needed_confirmation": set(),
        "basis": {},
    }


def relation_ready_reason(relation_ready: int, interpretation: dict[str, Any]) -> str:
    if not relation_ready:
        if interpretation["hard_blocker_flags"]:
            return "hard_blocker_or_unusable_context"
        return "context_preserved_but_not_relation_edge_ready"
    if interpretation["economic_direction_hint"] == "unknown":
        return "relation_modifier_ready_but_direction_unknown"
    return "relation_edge_review_ready_not_trade_signal"


def is_relation_ready(interpretation: dict[str, Any]) -> bool:
    return relation_ready_tier(interpretation) != "not_ready"


def relation_ready_tier(interpretation: dict[str, Any]) -> str:
    if interpretation["hard_blocker_flags"]:
        return "not_ready"
    state = interpretation["interpretation_state"]
    if state == "economic_context_unusable":
        return "not_ready"
    if interpretation["economic_direction_hint"] in {"positive", "negative"} and interpretation["confidence_band"] in {"high", "medium"}:
        return "directional"
    if interpretation["economic_direction_hint"] == "mixed" and interpretation["confidence_band"] in {"high", "medium"}:
        return "structural_mixed"
    relation_modifier_states = {
        "form4_sale_plan_or_compensation_context",
        "ownership_passive_large_holder_context",
        "ownership_percent_source_context",
        "guidance_reaffirm_low_novelty_context",
        "generic_8k_financing_route_modifier",
        "generic_8k_mna_route_modifier",
        "generic_8k_governance_context_modifier",
    }
    if state in relation_modifier_states:
        return "context_only"
    return "not_ready"


def is_usable_without_missing_source(interpretation: dict[str, Any]) -> bool:
    if interpretation["hard_blocker_flags"]:
        return False
    if interpretation["confidence_band"] in {"high", "medium"}:
        return True
    return is_relation_ready(interpretation) and interpretation["economic_direction_hint"] != "unknown"


def parse_json(value: object) -> dict[str, Any]:
    if value is None or pd.isna(value):
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def truthy(value: object) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def numeric(value: object) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)
