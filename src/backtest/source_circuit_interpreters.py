from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.generic_8k_classifier import classify_generic_8k_text
from src.backtest.source_information_router import route_source_event


ROOT = Path(__file__).resolve().parents[2]
TAG_RE = re.compile(r"<[^>]+>")
MONEY_RE = re.compile(r"\$?\s?(\d+(?:,\d{3})*(?:\.\d+)?)\s?(billion|million|thousand|bn|mm|m|k)?", re.IGNORECASE)
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s?%")


@dataclass(frozen=True)
class CircuitContext:
    event_id: str
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    source_form_family: str
    route_state: str
    route_circuit: str
    context_type: str
    primitive_fields_json: str
    interpretation_states: str
    confidence_state: str
    forbidden_fact_families: str
    alive_review_state: str
    operating_primitive_created_flag: int
    source_is_discarded_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


@dataclass(frozen=True)
class ContextEdge:
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
    condition_states: str
    effect_state: str
    layer_links: str
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


def interpret_source_event(row: pd.Series, *, row_index: int = 0, root: Path = ROOT) -> tuple[dict[str, object], dict[str, object]]:
    route = route_source_event(row)
    source_family = str(row.get("source_form_family", ""))
    text = event_text(row, root=root, prefer_raw=source_family in {"generic_8k", "form4_insider"})
    if source_family == "form4_insider":
        primitive, states, confidence, alive = interpret_insider(text)
        context_type = "InsiderBehaviorContext"
        edge = make_edge(row, row_index, context_type, "OperatingCatalystContext", "confidence_cap_or_reinforcing", "INSIDER_CONTEXT_MODIFIES_ONLY_IF_OPERATING_PATH_EXISTS", states, "reinforce_or_cap_context_confidence_only", "L1|L3|L4|L5")
    elif source_family == "schedule_13d_13g":
        primitive, states, confidence, alive = interpret_activist_control(text)
        context_type = "ActivistControlContext"
        edge = make_edge(row, row_index, context_type, "PortfolioSlotContext", "escalation", "ACTIVE_OR_PASSIVE_OWNERSHIP_ROUTES_SPECIAL_SITUATION", states, "route_to_special_situation_review_only", "L1|L3|L4|L5")
    elif source_family == "form_13f":
        primitive, states, confidence, alive = interpret_13f(text)
        context_type = "InstitutionalPositioningContext"
        edge = make_edge(row, row_index, context_type, "RiskBudgetContext", "confidence_cap", "THIRTEENF_POSITIONING_CONTEXT_NOT_FRESH_CATALYST", states, "cap_to_positioning_context_only", "L1|L3|L4|L5")
    elif source_family == "ownership_or_institutional_filing":
        primitive, states, confidence, alive = interpret_ownership_structure(text)
        context_type = "OwnershipStructureContext"
        edge = make_edge(row, row_index, context_type, "RiskBudgetContext", "sizing_modifier", "OWNERSHIP_STRUCTURE_MODIFIES_RISK_NOT_ECONOMICS", states, "modify_float_liquidity_or_crowding_context_only", "L1|L3|L4|L5")
    elif source_family == "generic_8k":
        primitive, states, confidence, alive = interpret_generic_8k(text)
        context_type = "Generic8KClassificationContext"
        edge = make_edge(row, row_index, context_type, "OperatingCatalystContext", "prerequisite", "GENERIC_8K_REQUIRES_CLASSIFICATION_BEFORE_OPERATING_CLAIM", states, "block_operating_fact_creation_until_classified", "L1|L2|L3|L4|L5")
    elif source_family == "financing_8k":
        primitive, states, confidence, alive = interpret_financing(text)
        context_type = "CreditFinancingContext"
        edge = make_edge(row, row_index, context_type, "EconomicTransmissionContext", "offsetting_or_reinforcing", "FINANCING_INTERACTS_WITH_GROWTH_DILUTION_LIQUIDITY", states, "funding_dilution_liquidity_context_review_only", "L1|L2|L3|L4|L5")
    elif source_family == "macro_policy_or_geopolitical_source":
        primitive, states, confidence, alive = interpret_macro_policy(text, row)
        context_type = "MacroPolicyTransmissionContext"
        edge = make_edge(row, row_index, context_type, "OperatingCatalystContext", "prerequisite_or_reinforcing", "MACRO_POLICY_REQUIRES_COMPANY_LINK_FOR_SINGLE_NAME", states, "theme_context_only_unless_company_link_present", "L1|L2|L3|L4|L5")
    else:
        primitive, states, confidence, alive = {}, ["source_gap_context"], "low_source_gap", "source_gap_needs_route"
        context_type = "SourceGapContext"
        edge = make_edge(row, row_index, context_type, "ResearchGovernanceContext", "prerequisite", "SOURCE_GAP_NEEDS_ROUTE_BEFORE_INTERPRETATION", states, "route_required_before_context_use", "L1")

    context = CircuitContext(
        event_id=event_id(row, row_index),
        lifecycle_id=str(row.get("lifecycle_id", "")),
        symbol=str(row.get("symbol", "")),
        theme_id=str(row.get("theme_id", "")),
        entry_ts=str(row.get("entry_ts", "")),
        split_name=str(row.get("split_name", "")),
        source_form_family=source_family,
        route_state=str(route["source_route_state"]),
        route_circuit=str(route["route_circuit"]),
        context_type=context_type,
        primitive_fields_json=json.dumps(primitive, ensure_ascii=False, sort_keys=True),
        interpretation_states="|".join(states),
        confidence_state=confidence,
        forbidden_fact_families=str(route["forbidden_fact_families"]),
        alive_review_state=alive,
        operating_primitive_created_flag=0,
        source_is_discarded_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
    )
    return asdict(context), edge


def interpret_insider(text: str) -> tuple[dict[str, object], list[str], str, str]:
    lower = text.lower()
    primitive = {
        "planned_or_automatic_flag": int("10b5-1" in lower or "rule 10b5" in lower),
        "open_market_buy_flag": int(has_transaction_code(text, "P")),
        "open_market_sale_flag": int(has_transaction_code(text, "S")),
        "option_or_award_flag": int(
            any(token in lower for token in ["option", "award", "restricted stock", "transactioncode a", "transactioncode m"])
            or has_transaction_code(text, "A")
            or has_transaction_code(text, "M")
        ),
        "director_or_officer_language_present": int(any(token in lower for token in ["director", "officer", "chief", "president", "ceo", "cfo"])),
        "reported_amount_count": len(MONEY_RE.findall(text)),
    }
    states = ["non_operating_context_only"]
    if primitive["open_market_buy_flag"]:
        states.append("insider_open_market_buy_observed")
    if primitive["open_market_sale_flag"]:
        states.append("insider_open_market_sale_observed")
    if primitive["option_or_award_flag"]:
        states.append("option_exercise_or_award_observed")
    if primitive["planned_or_automatic_flag"]:
        states.append("automatic_plan_or_admin_transaction")
    if primitive["director_or_officer_language_present"]:
        states.append("executive_or_director_signal_present")
    if len(states) == 1:
        states.append("insider_context_alive_needs_role_and_transaction_type")
    return primitive, states, "medium_context_only" if len(states) > 2 else "low_needs_form4_detail", "insider_context_alive_needs_role_and_transaction_type"


def interpret_activist_control(text: str) -> tuple[dict[str, object], list[str], str, str]:
    lower = text.lower()
    pct = first_percent(text)
    active = "schedule 13d" in lower or "13d" in lower
    passive = "schedule 13g" in lower or "13g" in lower
    control_language = any(token in lower for token in ["purpose of transaction", "control", "board", "strategic", "proposal", "activist"])
    primitive = {
        "beneficial_ownership_percent": pct,
        "active_13d_flag": int(active),
        "passive_13g_flag": int(passive),
        "control_intent_language_present": int(control_language),
        "amendment_flag": int("amendment" in lower),
    }
    states = ["non_operating_special_situation_context"]
    if active:
        states.append("active_13d_control_context")
    if passive:
        states.append("passive_13g_ownership_context")
    if pct is not None:
        states.append("ownership_threshold_observed")
    if control_language:
        states.append("control_intent_language_present")
    if primitive["amendment_flag"]:
        states.append("amendment_update_observed")
    if len(states) == 1:
        states.append("control_context_alive_needs_purpose_classification")
    return primitive, states, "medium_special_situation_context" if active or control_language else "low_needs_schedule_classification", "control_context_alive_needs_purpose_classification"


def interpret_13f(text: str) -> tuple[dict[str, object], list[str], str, str]:
    lower = text.lower()
    primitive = {
        "reported_position_value": max_money(text),
        "quarter_or_period_language_present": int(any(token in lower for token in ["quarter", "period", "calendar year", "information table"])),
        "institutional_manager_language_present": int(any(token in lower for token in ["institutional investment manager", "form 13f", "13f"])),
    }
    states = ["positioning_snapshot_stale_by_design", "non_operating_positioning_context"]
    if primitive["reported_position_value"] is not None:
        states.append("institutional_sponsorship_observed")
    if primitive["institutional_manager_language_present"]:
        states.append("crowding_context_possible")
    states.append("positioning_context_alive_not_trade_signal")
    return primitive, states, "medium_positioning_context_only", "positioning_context_alive_not_trade_signal"


def interpret_ownership_structure(text: str) -> tuple[dict[str, object], list[str], str, str]:
    lower = text.lower()
    primitive = {
        "ownership_percent": first_percent(text),
        "beneficial_owner_language_present": int("beneficial" in lower or "ownership" in lower),
        "holder_concentration_language_present": int(any(token in lower for token in ["sole voting power", "shared voting power", "sole dispositive power", "shared dispositive power"])),
    }
    states = ["ownership_structure_observed", "non_operating_structure_context"]
    if primitive["ownership_percent"] is not None:
        states.append("holder_concentration_possible")
    if primitive["holder_concentration_language_present"]:
        states.append("float_context_possible")
    states.append("ownership_context_alive_needs_holder_and_change_classification")
    return primitive, states, "medium_ownership_context_only", "ownership_context_alive_needs_holder_and_change_classification"


def interpret_generic_8k(text: str) -> tuple[dict[str, object], list[str], str, str]:
    classification = classify_generic_8k_text(text)
    primitive = {
        **classification.to_primitive(),
        "financing_language_flag": int(classification.agreement_family_state == "financing_credit_context"),
        "operating_language_flag": int(classification.operating_candidate_flag),
        "governance_flag": int(
            classification.agreement_family_state
            in {"governance_board_context", "severance_or_change_in_control_context", "compensation_award_context"}
        ),
        "financial_statement_flag": int(classification.agreement_family_state == "financial_results_context"),
        "raw_text_available": int(bool(text)),
    }
    states = [
        "generic_8k_requires_secondary_classifier",
        f"generic_8k_{classification.agreement_family_state}",
        f"generic_8k_{classification.operating_transmission_state}",
        f"generic_8k_permission_{classification.permission_state}",
    ]
    if not classification.item_numbers:
        states.append("generic_8k_unclassified")
    if classification.agreement_family_state == "financing_credit_context":
        states.append("generic_8k_financing_context")
    if classification.operating_candidate_flag:
        states.append("generic_8k_operating_context_possible")
    if classification.operating_supported_flag:
        states.append("generic_8k_operating_context_supported")
    if classification.agreement_family_state in {"governance_board_context", "severance_or_change_in_control_context", "compensation_award_context"}:
        states.append("generic_8k_governance_context")
    if classification.agreement_family_state == "financial_results_context":
        states.append("generic_8k_financial_statement_context")
    return primitive, states, "medium_family_classifier_applied" if classification.item_numbers else "low_unclassified_8k", "generic_8k_alive_pending_item_classifier"


def interpret_financing(text: str) -> tuple[dict[str, object], list[str], str, str]:
    lower = text.lower()
    convertible = "convertible" in lower or "conversion" in lower
    warrant = "warrant" in lower
    atm_or_shelf = "atm" in lower or "at-the-market" in lower or "shelf" in lower or "offering" in lower
    growth = any(token in lower for token in ["growth", "capacity", "capital expenditures", "manufacturing", "expansion"])
    rescue = any(token in lower for token in ["working capital", "general corporate", "liquidity", "going concern"])
    refi = "refinance" in lower or "repay" in lower or "repayment" in lower
    primitive = {
        "principal_amount": max_money(text),
        "conversion_feature_flag": int(convertible),
        "warrant_flag": int(warrant),
        "atm_or_shelf_flag": int(atm_or_shelf),
        "growth_use_of_proceeds_flag": int(growth),
        "liquidity_language_present": int(rescue),
        "debt_refinance_language_present": int(refi),
        "covenant_language_present": int("covenant" in lower),
    }
    states = []
    if growth:
        states.append("growth_funding_possible")
    if rescue:
        states.append("liquidity_rescue_possible")
    if refi:
        states.append("debt_refinancing_context")
    if convertible or warrant or atm_or_shelf:
        states.append("dilution_overhang_present")
    if convertible or warrant:
        states.append("convertible_or_warrant_overhang_present")
    if primitive["covenant_language_present"]:
        states.append("covenant_or_maturity_relief_possible")
    if not states:
        states.append("financing_terms_incomplete")
    states.append("credit_context_alive_terms_incomplete_not_negative")
    return primitive, states, "medium_credit_context_review_only", "credit_context_alive_terms_incomplete_not_negative"


def interpret_macro_policy(text: str, row: pd.Series) -> tuple[dict[str, object], list[str], str, str]:
    lower = text.lower()
    symbol = str(row.get("symbol", "")).lower()
    company_mentioned = bool(symbol and re.search(rf"\b{re.escape(symbol)}\b", lower))
    demand = any(token in lower for token in ["demand", "budget", "funding", "procurement", "investment"])
    regulatory = any(token in lower for token in ["regulation", "regulatory", "tariff", "sanction", "ftc", "sec"])
    supply = any(token in lower for token in ["supply chain", "export control", "shortage", "import"])
    primitive = {
        "company_mentioned_flag": int(company_mentioned),
        "demand_language_present": int(demand),
        "regulatory_or_budget_language_present": int(regulatory or demand),
        "supply_chain_language_present": int(supply),
        "affected_theme": str(row.get("theme_id", "")),
    }
    states = ["macro_theme_context_only"]
    if company_mentioned and demand:
        states.append("policy_tailwind_with_company_link")
    elif demand:
        states.append("policy_tailwind_company_link_weak")
    if regulatory:
        states.append("geopolitical_or_regulatory_risk_context")
    if supply:
        states.append("supply_chain_transmission_possible")
    if demand:
        states.append("demand_transmission_possible")
    if not company_mentioned:
        states.append("single_name_link_missing")
    states.append("macro_context_alive_theme_only_not_single_name")
    return primitive, states, "medium_theme_context_only", "macro_context_alive_theme_only_not_single_name"


def make_edge(
    row: pd.Series,
    row_index: int,
    source_context_type: str,
    target_context_type: str,
    relation_type: str,
    rule_id: str,
    states: list[str],
    effect_state: str,
    layer_links: str,
) -> dict[str, object]:
    return asdict(
        ContextEdge(
            event_id=event_id(row, row_index),
            lifecycle_id=str(row.get("lifecycle_id", "")),
            symbol=str(row.get("symbol", "")),
            theme_id=str(row.get("theme_id", "")),
            entry_ts=str(row.get("entry_ts", "")),
            split_name=str(row.get("split_name", "")),
            source_context_type=source_context_type,
            target_context_type=target_context_type,
            relation_type=relation_type,
            rule_id=rule_id,
            condition_states="|".join(states),
            effect_state=effect_state,
            layer_links=layer_links,
            backtest_eligible_flag=0,
            outcome_used_for_assignment_flag=0,
        )
    )


def event_text(row: pd.Series, *, root: Path = ROOT, prefer_raw: bool = False) -> str:
    raw_path = clean_missing(row.get("raw_text_path"))
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if path.exists() and prefer_raw:
            return normalize(path.read_text(encoding="utf-8", errors="ignore")[:20000])
    span = clean_missing(row.get("content_interpretation_evidence_span"))
    if span:
        return normalize(span)
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            return normalize(path.read_text(encoding="utf-8", errors="ignore")[:20000])
    return ""


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html.unescape(text))).strip()


def has_transaction_code(text: str, code: str) -> bool:
    patterns = [
        rf"transaction\s*code\s*{re.escape(code)}\b",
        rf"transactionCode\s*{re.escape(code)}\b",
        rf"<transactionCode>\s*{re.escape(code)}\s*</transactionCode>",
        rf"\b\d{{1,2}}/\d{{1,2}}/\d{{4}}\s+{re.escape(code)}\b",
        rf"\bcode\s*{re.escape(code)}\b",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def max_money(text: str) -> float | None:
    values = []
    for match in MONEY_RE.finditer(text):
        raw = match.group(1)
        scale = (match.group(2) or "").lower()
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        if scale in {"billion", "bn"}:
            value *= 1_000_000_000
        elif scale in {"million", "mm", "m"}:
            value *= 1_000_000
        elif scale in {"thousand", "k"}:
            value *= 1_000
        values.append(value)
    return max(values) if values else None


def first_percent(text: str) -> float | None:
    match = PCT_RE.search(text)
    return float(match.group(1)) if match else None


def event_id(row: pd.Series, row_index: int) -> str:
    value = clean_missing(row.get("event_id"))
    return value or f"task732_event_{row_index:06d}"


def clean_missing(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text
