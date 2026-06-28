from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Task742RuleInterpretation:
    interpretation_state: str
    economic_direction_hint: str
    confidence_band: str
    ambiguity_flags: tuple[str, ...]
    soft_uncertainty_flags: tuple[str, ...]
    hard_blocker_flags: tuple[str, ...]
    needed_confirmation: tuple[str, ...]
    basis: dict[str, Any]
    relation_ready_tier: str
    relation_ready_reason: str
    usable_without_missing_source_flag: int
    can_create_directional_edge_flag: int
    can_create_structural_edge_flag: int
    context_attachment_only_flag: int
    direction_hint_trade_instruction_flag: int = 0
    asof_change_inference_forbidden_flag: int = 1
    trade_output_flag: int = 0
    score_output_flag: int = 0
    backtest_eligible_flag: int = 0
    outcome_used_for_assignment_flag: int = 0
    rule_id: str = "TASK742_PRAGMATIC_ECONOMIC_MEANING_REVIEW_ONLY"


def interpret_task742_economic_context(
    row: Mapping[str, Any],
    primitive: Mapping[str, Any] | None = None,
    denominators: Mapping[str, Any] | None = None,
    comparators: Mapping[str, Any] | None = None,
    availability: Mapping[str, Any] | None = None,
    timing: Mapping[str, Any] | None = None,
) -> Task742RuleInterpretation:
    base = _empty_interpretation()
    primitive = primitive or {}
    denominators = denominators or {}
    comparators = comparators or {}
    availability = availability or {}
    timing = timing or {}

    if not timing.get("no_future_data_used", True):
        base["hard_blocker_flags"].add("future_data_violation")
    if not availability.get("has_task740_primitive", True):
        base["hard_blocker_flags"].add("primitive_missing")
    if not availability.get("has_raw_text_path", True):
        base["hard_blocker_flags"].add("raw_text_missing")
    if base["hard_blocker_flags"]:
        base["interpretation_state"] = "economic_context_unusable"
        base["confidence_band"] = "insufficient"
        base["economic_direction_hint"] = "unknown"
        return _finalize(base)

    circuit = _text(row.get("source_circuit"))
    if circuit == "form4_insider_behavior":
        base = _interpret_form4(primitive, denominators, comparators, base)
    elif circuit in {"ownership_float_structure", "activist_control"}:
        base = _interpret_ownership(circuit, primitive, denominators, base)
    elif circuit == "credit_financing":
        base = _interpret_financing(primitive, denominators, comparators, base)
    elif circuit == "financial_results_guidance":
        base = _interpret_financial_results(primitive, denominators, base)
    elif circuit == "generic_8k_classifier":
        base = _interpret_generic_8k(primitive, base)
    else:
        base["interpretation_state"] = "source_circuit_context_unknown"
        base["confidence_band"] = "low"
        base["economic_direction_hint"] = "unknown"
        base["soft_uncertainty_flags"].add("unsupported_source_circuit")
        base["needed_confirmation"].add("manual_source_circuit_review")
    return _finalize(base)


def relation_ready_tier(interpretation: Mapping[str, Any] | Task742RuleInterpretation) -> str:
    hard = _as_set(_field(interpretation, "hard_blocker_flags"))
    state = _text(_field(interpretation, "interpretation_state"))
    direction = _text(_field(interpretation, "economic_direction_hint"))
    confidence = _text(_field(interpretation, "confidence_band"))
    if hard or state == "economic_context_unusable":
        return "not_ready"
    if direction in {"positive", "negative"} and confidence in {"high", "medium"}:
        return "directional"
    if direction == "mixed" and confidence in {"high", "medium"}:
        return "structural_mixed"
    if state in {
        "form4_sale_plan_or_compensation_context",
        "ownership_passive_large_holder_context",
        "ownership_percent_source_context",
        "guidance_reaffirm_low_novelty_context",
        "generic_8k_financing_route_modifier",
        "generic_8k_mna_route_modifier",
        "generic_8k_governance_context_modifier",
    }:
        return "context_only"
    return "not_ready"


def _finalize(base: dict[str, Any]) -> Task742RuleInterpretation:
    tier = relation_ready_tier(base)
    relation_ready = int(tier != "not_ready")
    usable = int(_is_usable_without_missing_source(base))
    return Task742RuleInterpretation(
        interpretation_state=base["interpretation_state"],
        economic_direction_hint=base["economic_direction_hint"],
        confidence_band=base["confidence_band"],
        ambiguity_flags=tuple(sorted(base["ambiguity_flags"])),
        soft_uncertainty_flags=tuple(sorted(base["soft_uncertainty_flags"])),
        hard_blocker_flags=tuple(sorted(base["hard_blocker_flags"])),
        needed_confirmation=tuple(sorted(base["needed_confirmation"])),
        basis=dict(base["basis"]),
        relation_ready_tier=tier,
        relation_ready_reason=_relation_ready_reason(relation_ready, base),
        usable_without_missing_source_flag=usable,
        can_create_directional_edge_flag=int(tier == "directional"),
        can_create_structural_edge_flag=int(tier == "structural_mixed"),
        context_attachment_only_flag=int(tier == "context_only"),
    )


def _empty_interpretation() -> dict[str, Any]:
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


def _interpret_form4(
    primitive: Mapping[str, Any],
    denominators: Mapping[str, Any],
    comparators: Mapping[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    buy = _truthy(primitive.get("open_market_buy_flag"))
    sale = _truthy(primitive.get("open_market_sale_flag"))
    award = _truthy(primitive.get("award_grant_flag")) or _truthy(primitive.get("option_exercise_flag"))
    plan = _truthy(primitive.get("planned_10b5_1_flag")) or _truthy(primitive.get("tenb5_instruction_present_flag"))
    size_known = any(
        value is not None
        for value in (
            comparators.get("shares_changed_pct_of_ownership_after"),
            comparators.get("shares_changed_pct_of_shares_outstanding"),
            denominators.get("estimated_transaction_value"),
        )
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


def _interpret_ownership(
    circuit: str,
    primitive: Mapping[str, Any],
    denominators: Mapping[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    ownership_percent = _numeric(primitive.get("ownership_percent"))
    active = _truthy(primitive.get("active_13d_flag")) or _truthy(primitive.get("control_language_present_flag"))
    passive = _truthy(primitive.get("passive_13g_flag"))
    holder_known = _truthy(primitive.get("holder_name_present_flag"))
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


def _interpret_financing(
    primitive: Mapping[str, Any],
    denominators: Mapping[str, Any],
    comparators: Mapping[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    principal = _numeric(primitive.get("principal_amount"))
    growth = _truthy(primitive.get("growth_use_language_flag"))
    liquidity = _truthy(primitive.get("liquidity_rescue_language_flag"))
    refi = _truthy(primitive.get("debt_refinance_language_flag"))
    dilution = any(
        _truthy(primitive.get(key))
        for key in (
            "instrument_convertible_flag",
            "instrument_warrant_flag",
            "instrument_atm_or_shelf_flag",
            "dilution_overhang_language_flag",
        )
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


def _interpret_financial_results(
    primitive: Mapping[str, Any],
    denominators: Mapping[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    raise_flag = _truthy(primitive.get("guidance_raise_flag"))
    cut_flag = _truthy(primitive.get("guidance_cut_flag"))
    reaffirm = _truthy(primitive.get("guidance_reaffirm_flag"))
    backlog = _truthy(primitive.get("backlog_or_order_language_flag"))
    margin = _truthy(primitive.get("margin_language_flag"))
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


def _interpret_generic_8k(primitive: Mapping[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    financing = _truthy(primitive.get("financing_flag"))
    mna = _truthy(primitive.get("mna_flag"))
    governance = _truthy(primitive.get("governance_flag")) or _truthy(primitive.get("compensation_flag"))
    operating = _truthy(primitive.get("operating_supported_flag")) or _truthy(primitive.get("operating_candidate_flag"))
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


def _relation_ready_reason(relation_ready: int, interpretation: Mapping[str, Any]) -> str:
    hard = _as_set(interpretation["hard_blocker_flags"])
    if not relation_ready:
        if hard:
            return "hard_blocker_or_unusable_context"
        return "context_preserved_but_not_relation_edge_ready"
    if interpretation["economic_direction_hint"] == "unknown":
        return "relation_modifier_ready_but_direction_unknown"
    return "relation_edge_review_ready_not_trade_signal"


def _is_usable_without_missing_source(interpretation: Mapping[str, Any]) -> bool:
    if _as_set(interpretation["hard_blocker_flags"]):
        return False
    if interpretation["confidence_band"] in {"high", "medium"}:
        return True
    return relation_ready_tier(interpretation) != "not_ready" and interpretation["economic_direction_hint"] != "unknown"


def _field(value: Mapping[str, Any] | Task742RuleInterpretation, name: str) -> Any:
    if isinstance(value, Task742RuleInterpretation):
        return getattr(value, name)
    return value.get(name)


def _as_set(value: object) -> set[str]:
    if isinstance(value, set):
        return {str(item) for item in value}
    if isinstance(value, (tuple, list)):
        return {str(item) for item in value}
    text = _text(value)
    return {part for part in text.split("|") if part}


def _truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _numeric(value: object) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: object) -> str:
    return "" if value is None else str(value)
