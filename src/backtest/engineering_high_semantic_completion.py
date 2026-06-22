from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.generic_8k_classifier import classify_generic_8k_text


ROOT = Path(__file__).resolve().parents[2]
TAG_RE = re.compile(r"<[^>]+>")
DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")
MONEY_RE = re.compile(r"\$?\s?(\d+(?:,\d{3})*(?:\.\d+)?)\s?(billion|million|thousand|bn|mm|m|k)?", re.IGNORECASE)
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s?%")
TRANSACTION_CODES = ["P", "S", "A", "M", "F", "G", "D"]


@dataclass(frozen=True)
class HighPrimitiveExtraction:
    lifecycle_id: str
    bundle_id: str
    source_event_id: str
    symbol: str
    source_circuit: str
    requirement_family: str
    extractor_state: str
    primitive_fields_json: str
    extracted_field_count: int
    raw_text_available_flag: int
    rule_id: str
    research_only_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


@dataclass(frozen=True)
class HighResolverOutput:
    lifecycle_id: str
    bundle_id: str
    source_event_id: str
    symbol: str
    source_circuit: str
    requirement_family: str
    resolver_state: str
    resolver_detail_state: str
    completion_state: str
    unresolved_requirements: str
    allowed_layer_effects: str
    operating_supported_created_flag: int
    buy_sell_signal_created_flag: int
    actionability_created_flag: int
    used_for_trading_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int
    rule_id: str


@dataclass(frozen=True)
class UnresolvedJoinBlocker:
    lifecycle_id: str
    source_event_id: str
    symbol: str
    source_circuit: str
    requirement_family: str
    blocker_family: str
    blocker_reason: str
    required_join_fields: str
    resolution_owner: str
    research_only_flag: int
    backtest_eligible_flag: int
    rule_id: str


def complete_engineering_high_requirement(row: pd.Series, event_detail: pd.Series, *, root: Path = ROOT) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    text = event_text(event_detail, root=root)
    circuit = str(row.get("source_circuit", ""))
    family = str(row.get("requirement_family", ""))
    if circuit == "form4_insider_behavior":
        primitives = extract_form4_primitives(text)
        resolver_state, detail_state, blockers = resolve_form4(primitives, family)
    elif circuit in {"ownership_float_structure", "activist_control"}:
        primitives = extract_ownership_primitives(text, event_detail)
        resolver_state, detail_state, blockers = resolve_ownership(primitives, family, circuit)
    elif circuit == "financial_results_guidance":
        primitives = extract_financial_results_primitives(text)
        resolver_state, detail_state, blockers = resolve_financial_results(primitives)
    elif circuit == "generic_8k_classifier":
        primitives = extract_generic_8k_primitives(text)
        resolver_state, detail_state, blockers = resolve_generic_8k(primitives)
    elif circuit == "credit_financing":
        primitives = extract_financing_primitives(text)
        resolver_state, detail_state, blockers = resolve_financing(primitives)
    else:
        primitives = {"raw_text_available_flag": int(bool(text)), "unsupported_circuit": circuit}
        resolver_state, detail_state, blockers = "semantic_context_needed", "unsupported_high_circuit", ["circuit_resolver_needed"]

    primitive = HighPrimitiveExtraction(
        lifecycle_id=str(row.get("lifecycle_id", "")),
        bundle_id=str(row.get("bundle_id", "")),
        source_event_id=str(row.get("source_event_id", "")),
        symbol=str(row.get("symbol", "")),
        source_circuit=circuit,
        requirement_family=family,
        extractor_state="primitive_extracted" if text else "raw_text_missing",
        primitive_fields_json=json.dumps(primitives, ensure_ascii=False, sort_keys=True),
        extracted_field_count=count_present(primitives),
        raw_text_available_flag=int(bool(text)),
        rule_id="TASK740_ENGINEERING_HIGH_PRIMITIVE_EXTRACTION",
        research_only_flag=1,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
    )
    completion_state = classify_completion_state(text, resolver_state, blockers)
    resolver = HighResolverOutput(
        lifecycle_id=str(row.get("lifecycle_id", "")),
        bundle_id=str(row.get("bundle_id", "")),
        source_event_id=str(row.get("source_event_id", "")),
        symbol=str(row.get("symbol", "")),
        source_circuit=circuit,
        requirement_family=family,
        resolver_state=resolver_state,
        resolver_detail_state=detail_state,
        completion_state=completion_state,
        unresolved_requirements="|".join(blockers),
        allowed_layer_effects=allowed_layer_effects(circuit, resolver_state),
        operating_supported_created_flag=0,
        buy_sell_signal_created_flag=0,
        actionability_created_flag=0,
        used_for_trading_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
        rule_id="TASK740_ENGINEERING_HIGH_RESOLVER_REVIEW_ONLY",
    )
    blocker_rows = [
        asdict(
            UnresolvedJoinBlocker(
                lifecycle_id=str(row.get("lifecycle_id", "")),
                source_event_id=str(row.get("source_event_id", "")),
                symbol=str(row.get("symbol", "")),
                source_circuit=circuit,
                requirement_family=family,
                blocker_family=blocker,
                blocker_reason=blocker_reason(blocker),
                required_join_fields="|".join(required_join_fields(blocker)),
                resolution_owner=resolution_owner(blocker),
                research_only_flag=1,
                backtest_eligible_flag=0,
                rule_id="TASK740_UNRESOLVED_JOIN_BLOCKER_REVIEW_ONLY",
            )
        )
        for blocker in blockers
    ]
    return asdict(primitive), asdict(resolver), blocker_rows


def extract_form4_primitives(text: str) -> dict[str, object]:
    plain = normalize(text)
    lower = plain.lower()
    codes = transaction_codes(text)
    dates = DATE_RE.findall(plain)
    shares = extract_share_numbers_near_transaction(text)
    owned_after = amount_after_phrase(plain, "beneficially owned following")
    price_values = price_values_from_form4(text)
    return {
        "transaction_codes": "|".join(codes),
        "primary_transaction_code": codes[0] if codes else "",
        "multiple_code_flag": int(len(set(codes)) > 1),
        "planned_10b5_1_flag": int(rule_10b5_checked(text)),
        "tenb5_instruction_present_flag": int("10b5-1" in lower or "rule 10b5" in lower),
        "open_market_buy_flag": int("P" in codes),
        "open_market_sale_flag": int("S" in codes),
        "option_exercise_flag": int("M" in codes or "option" in lower or "exercise" in lower),
        "award_grant_flag": int("A" in codes or "restricted stock" in lower or "award" in lower),
        "non_discretionary_code_flag": int(any(code in codes for code in ["F", "G", "D"])),
        "derivative_table_flag": int("derivative securities" in lower or "conversion or exercise price" in lower),
        "non_derivative_table_flag": int("non-derivative securities" in lower),
        "insider_director_flag": int(role_checked(text, "Director")),
        "insider_officer_flag": int(role_checked(text, "Officer")),
        "insider_ten_percent_owner_flag": int(role_checked(text, "10% Owner")),
        "insider_role_language_present": int(any(token in lower for token in ["director", "officer", "chief", "president", "ceo", "cfo", "10% owner"])),
        "shares_changed": max(shares) if shares else None,
        "shares_changed_present_flag": int(bool(shares)),
        "transaction_value_present_flag": int(any(value and value > 0 for value in price_values)),
        "ownership_after": owned_after,
        "ownership_after_present_flag": int(owned_after is not None),
        "transaction_date": dates[0] if dates else "",
        "filing_or_signature_date": dates[-1] if dates else "",
        "raw_date_count": len(dates),
    }


def extract_ownership_primitives(text: str, row: pd.Series) -> dict[str, object]:
    plain = normalize(text)
    lower = plain.lower()
    percents = [float(match.group(1)) for match in PCT_RE.finditer(plain)]
    schedule_type = schedule_type_from_text(plain, row)
    holder = holder_name(plain)
    shares = share_amounts(plain)
    return {
        "schedule_type": schedule_type,
        "holder_name": holder,
        "holder_name_present_flag": int(bool(holder)),
        "ownership_percent": max(percents) if percents else None,
        "ownership_percent_present_flag": int(bool(percents)),
        "shares_owned": max(shares) if shares else None,
        "shares_owned_present_flag": int(bool(shares)),
        "amendment_flag": int("/a" in schedule_type.lower() or "amendment" in lower),
        "active_13d_flag": int("13d" in schedule_type.lower()),
        "passive_13g_flag": int("13g" in schedule_type.lower()),
        "purpose_language_present_flag": int("purpose of transaction" in lower or "item 4" in lower),
        "control_language_present_flag": int(any(token in lower for token in ["control", "board", "strategic", "proposal", "activist", "proxy"])),
        "sole_voting_power_flag": int("sole voting power" in lower),
        "shared_voting_power_flag": int("shared voting power" in lower),
        "filing_date": first_date(plain),
    }


def extract_financial_results_primitives(text: str) -> dict[str, object]:
    plain = normalize(text)
    lower = plain.lower()
    return {
        "item_202_flag": int(bool(re.search(r"item\s+2\.02", lower))),
        "earnings_release_flag": int("earnings release" in lower or "results of operations" in lower or "financial condition" in lower),
        "revenue_language_flag": int("revenue" in lower or "sales" in lower),
        "margin_language_flag": int("margin" in lower or "gross profit" in lower),
        "guidance_language_flag": int("guidance" in lower or "outlook" in lower or "forecast" in lower),
        "guidance_raise_flag": int(any(token in lower for token in ["raise guidance", "raised guidance", "increase guidance", "increased guidance", "raises outlook"])),
        "guidance_cut_flag": int(any(token in lower for token in ["lower guidance", "lowered guidance", "reduce guidance", "reduced guidance", "cuts outlook"])),
        "guidance_reaffirm_flag": int(any(token in lower for token in ["reaffirm", "reaffirms", "confirm guidance", "confirmed guidance"])),
        "backlog_or_order_language_flag": int("backlog" in lower or "orders" in lower),
        "period_label_present_flag": int(bool(re.search(r"(first|second|third|fourth)\s+quarter|q[1-4]|fiscal\s+\d{4}", lower))),
        "money_value_present_flag": int(max_money(plain) is not None),
        "percent_value_present_flag": int(first_percent(plain) is not None),
    }


def extract_generic_8k_primitives(text: str) -> dict[str, object]:
    classification = classify_generic_8k_text(text)
    primitive = classification.to_primitive()
    lower = normalize(text).lower()
    primitive.update(
        {
            "item_number_set": "|".join(classification.item_numbers),
            "item_count": len(classification.item_numbers),
            "compensation_flag": int(classification.agreement_family_state == "compensation_award_context"),
            "governance_flag": int(classification.agreement_family_state in {"governance_board_context", "severance_or_change_in_control_context"}),
            "financing_flag": int(classification.agreement_family_state == "financing_credit_context"),
            "mna_flag": int(classification.agreement_family_state == "strategic_mna_context"),
            "financial_results_flag": int(classification.agreement_family_state == "financial_results_context"),
            "operating_language_flag": int(classification.operating_candidate_flag),
            "item_101_flag": int("1.01" in classification.item_numbers),
            "raw_text_span_available_flag": int(bool(text)),
            "agreement_keyword_count": sum(lower.count(token) for token in ["agreement", "contract", "purchase", "credit", "merger"]),
        }
    )
    return primitive


def extract_financing_primitives(text: str) -> dict[str, object]:
    plain = normalize(text)
    lower = plain.lower()
    amounts = money_values(plain)
    return {
        "instrument_credit_agreement_flag": int("credit agreement" in lower),
        "instrument_note_flag": int("note" in lower or "notes" in lower),
        "instrument_convertible_flag": int("convertible" in lower or "conversion" in lower),
        "instrument_warrant_flag": int("warrant" in lower),
        "instrument_atm_or_shelf_flag": int("at-the-market" in lower or "atm" in lower or "shelf" in lower),
        "instrument_securities_purchase_flag": int("securities purchase" in lower or "registered direct" in lower or "private placement" in lower),
        "principal_amount": max(amounts) if amounts else None,
        "principal_amount_present_flag": int(bool(amounts)),
        "maturity_language_present_flag": int("maturity" in lower or "matures" in lower or "due " in lower),
        "coupon_or_interest_language_present_flag": int("interest" in lower or "coupon" in lower or "base rate" in lower or "sofr" in lower),
        "use_of_proceeds_present_flag": int("use of proceeds" in lower or "proceeds" in lower),
        "growth_use_language_flag": int(any(token in lower for token in ["growth", "capacity", "capital expenditures", "manufacturing", "expansion"])),
        "liquidity_rescue_language_flag": int(any(token in lower for token in ["working capital", "general corporate", "liquidity", "going concern"])),
        "debt_refinance_language_flag": int(any(token in lower for token in ["refinance", "repay", "repayment"])),
        "covenant_language_present_flag": int("covenant" in lower),
        "dilution_overhang_language_flag": int(any(token in lower for token in ["convertible", "warrant", "conversion", "shares issuable", "offering"])),
    }


def resolve_form4(primitives: dict[str, object], family: str) -> tuple[str, str, list[str]]:
    codes = split_pipe(primitives.get("transaction_codes"))
    blockers = ["pattern_denominator_needed"]
    if not codes:
        return "form4_transaction_code_unknown", "transaction_code_missing", blockers + ["transaction_code_needed"]
    if primitives["multiple_code_flag"]:
        detail = "transaction_code_ambiguous"
    elif primitives["open_market_buy_flag"]:
        detail = "transaction_code_resolved"
        return "form4_open_market_buy_context", detail, blockers
    elif primitives["open_market_sale_flag"] and primitives["planned_10b5_1_flag"]:
        detail = "non_discretionary_transaction_context"
        return "form4_automatic_plan_context_only", detail, blockers
    elif primitives["open_market_sale_flag"]:
        detail = "transaction_code_resolved"
        return "form4_open_market_sale_context", detail, blockers
    elif primitives["award_grant_flag"] or primitives["option_exercise_flag"] or primitives["non_discretionary_code_flag"]:
        detail = "non_discretionary_transaction_context"
        return "form4_award_or_option_context_only", detail, blockers
    else:
        detail = "transaction_code_resolved"
    return "form4_pattern_enrichment_closed_source_only", detail, blockers


def resolve_ownership(primitives: dict[str, object], family: str, circuit: str) -> tuple[str, str, list[str]]:
    blockers = ["ownership_denominator_needed"]
    if primitives["active_13d_flag"] and primitives["control_language_present_flag"]:
        return "active_control_intent_review", "control_language_present", blockers + ["control_impact_unresolved"]
    if primitives["active_13d_flag"]:
        return "control_intent_unknown", "active_schedule_without_control_resolution", blockers + ["control_impact_unresolved"]
    if primitives["passive_13g_flag"]:
        return "passive_ownership_context", "active_passive_resolved", blockers
    if primitives["ownership_percent_present_flag"]:
        return "ownership_structure_resolved_source_only", "ownership_percent_extracted", blockers
    return "ownership_change_unknown", "ownership_percent_missing", blockers + ["holder_identity_or_percent_needed"]


def resolve_financial_results(primitives: dict[str, object]) -> tuple[str, str, list[str]]:
    blockers = ["expectation_comparator_needed", "guidance_baseline_needed"]
    if primitives["guidance_raise_flag"] or primitives["guidance_cut_flag"] or primitives["guidance_reaffirm_flag"]:
        return "guidance_revision_language_present", "guidance_language_resolved_source_only", blockers
    if primitives["margin_language_flag"]:
        return "margin_bridge_needed", "margin_language_present_source_only", blockers + ["margin_bridge_needed"]
    if primitives["item_202_flag"] or primitives["earnings_release_flag"] or primitives["revenue_language_flag"]:
        return "financial_results_context_resolved_source_only", "results_language_present_source_only", blockers
    return "results_denominator_needed", "results_language_weak_or_missing", blockers


def resolve_generic_8k(primitives: dict[str, object]) -> tuple[str, str, list[str]]:
    family = str(primitives.get("agreement_family_state", ""))
    if family == "financing_credit_context":
        return "financing_route_required", "generic_8k_routed_to_financing", ["capital_structure_denominator_needed"]
    if family == "strategic_mna_context":
        return "mna_route_required", "generic_8k_routed_to_mna", ["mna_operating_link_needed"]
    if family in {"governance_board_context", "severance_or_change_in_control_context"}:
        return "governance_context_only", "generic_8k_governance_context", []
    if family == "compensation_award_context":
        return "compensation_context_only", "generic_8k_compensation_context", []
    if primitives.get("operating_candidate_flag"):
        return "operating_transmission_needed", "generic_8k_operating_language_source_only", ["operating_denominator_needed"]
    return "generic_8k_classified", "generic_8k_family_classified_source_only", []


def resolve_financing(primitives: dict[str, object]) -> tuple[str, str, list[str]]:
    blockers = ["capital_structure_denominator_needed"]
    instrument_present = any(
        primitives.get(key)
        for key in [
            "instrument_credit_agreement_flag",
            "instrument_note_flag",
            "instrument_convertible_flag",
            "instrument_warrant_flag",
            "instrument_atm_or_shelf_flag",
            "instrument_securities_purchase_flag",
        ]
    )
    complete_terms = instrument_present and primitives["principal_amount_present_flag"] and (
        primitives["maturity_language_present_flag"] or primitives["coupon_or_interest_language_present_flag"] or primitives["use_of_proceeds_present_flag"]
    )
    if primitives["dilution_overhang_language_flag"]:
        return "dilution_overhang_review", "financing_terms_dilution_language_source_only", blockers
    if primitives["growth_use_language_flag"]:
        return "growth_funding_review", "financing_growth_use_language_source_only", blockers
    if primitives["liquidity_rescue_language_flag"]:
        return "liquidity_rescue_review", "financing_liquidity_language_source_only", blockers
    if primitives["debt_refinance_language_flag"]:
        return "debt_refinance_context", "financing_refinance_language_source_only", blockers
    if complete_terms:
        return "financing_terms_complete_source_only", "financing_terms_minimum_source_complete", blockers
    if instrument_present:
        return "financing_terms_partial", "financing_instrument_present_terms_partial", blockers
    return "terms_incomplete_unknown", "financing_terms_missing_source_only", blockers + ["instrument_terms_needed"]


def classify_completion_state(text: str, resolver_state: str, blockers: list[str]) -> str:
    if not text:
        return "raw_text_missing"
    if blockers:
        return "unresolved_join_needed"
    if "unknown" in resolver_state or "needed" in resolver_state:
        return "source_only_resolved"
    return "source_only_resolved"


def allowed_layer_effects(circuit: str, resolver_state: str) -> str:
    if circuit in {"financial_results_guidance", "credit_financing", "generic_8k_classifier"}:
        return "L1_source_trace|L2_economic_interpretation_review"
    if circuit in {"ownership_float_structure", "activist_control"}:
        return "L1_source_trace|L4_slot_context_review|L5_risk_review"
    if circuit == "form4_insider_behavior":
        return "L1_source_trace|L5_risk_review"
    return "L1_source_trace"


def blocker_reason(blocker: str) -> str:
    return {
        "pattern_denominator_needed": "Form4 behavior needs holdings, role history, and prior insider pattern before directionality.",
        "ownership_denominator_needed": "Ownership impact needs float, shares outstanding, and prior holder state.",
        "control_impact_unresolved": "13D purpose language is not equivalent to realized control or board outcome.",
        "expectation_comparator_needed": "Financial results need consensus, prior guidance, or expectation baseline.",
        "guidance_baseline_needed": "Guidance language needs prior guidance baseline before surprise interpretation.",
        "margin_bridge_needed": "Margin language needs bridge, segment mix, and one-off context.",
        "capital_structure_denominator_needed": "Financing needs cash, debt, runway, market cap, and dilution denominator.",
        "mna_operating_link_needed": "M&A needs target contribution, synergy, backlog, customers, or integration path.",
        "operating_denominator_needed": "Operating language needs size, duration, customer, revenue, backlog, or guidance denominator.",
        "transaction_code_needed": "Form4 transaction code is required before behavior classification.",
        "holder_identity_or_percent_needed": "Ownership filing lacks enough holder or percent primitives.",
        "instrument_terms_needed": "Financing source lacks instrument and core term primitives.",
    }.get(blocker, "Additional source or join required before economic interpretation.")


def required_join_fields(blocker: str) -> list[str]:
    return {
        "pattern_denominator_needed": ["insider_total_holdings", "prior_90d_insider_sales", "role_history"],
        "ownership_denominator_needed": ["float", "shares_outstanding", "prior_holder_percent"],
        "control_impact_unresolved": ["board_outcome", "company_response", "settlement_or_proxy_status"],
        "expectation_comparator_needed": ["consensus_revenue", "consensus_eps", "prior_guidance"],
        "guidance_baseline_needed": ["prior_guidance_low", "prior_guidance_high", "management_prior_commentary"],
        "margin_bridge_needed": ["segment_margin", "gross_margin_bridge", "one_off_adjustments"],
        "capital_structure_denominator_needed": ["cash", "debt", "market_cap", "shares_outstanding", "cash_burn"],
        "mna_operating_link_needed": ["target_revenue", "target_backlog", "synergy_estimate", "integration_cost"],
        "operating_denominator_needed": ["contract_value", "duration", "customer_name", "revenue_or_backlog_impact"],
        "transaction_code_needed": ["form4_transaction_code"],
        "holder_identity_or_percent_needed": ["holder_name", "ownership_percent"],
        "instrument_terms_needed": ["instrument", "principal", "maturity", "coupon", "use_of_proceeds"],
    }.get(blocker, ["source_join_required"])


def resolution_owner(blocker: str) -> str:
    if blocker in {"pattern_denominator_needed", "transaction_code_needed"}:
        return "Data & Market Microstructure"
    if blocker in {"ownership_denominator_needed", "control_impact_unresolved", "holder_identity_or_percent_needed"}:
        return "Research Governance"
    if blocker in {"capital_structure_denominator_needed", "instrument_terms_needed"}:
        return "Research Governance"
    return "Research Governance"


def event_text(row: pd.Series, *, root: Path = ROOT) -> str:
    raw_path = clean_missing(row.get("raw_text_path"))
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")[:30000]
    span = clean_missing(row.get("content_interpretation_evidence_span"))
    return span


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html.unescape(text))).strip()


def transaction_codes(text: str) -> list[str]:
    found: list[str] = []
    for code in TRANSACTION_CODES:
        patterns = [
            rf"<transactionCode>\s*{code}\s*</transactionCode>",
            rf"transaction\s*code\s*{code}\b",
            rf"\b\d{{1,2}}/\d{{1,2}}/\d{{4}}\s+{code}\b",
            rf">\s*{code}\s*</span>",
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            found.append(code)
    return found


def rule_10b5_checked(text: str) -> bool:
    return bool(re.search(r"<isRule10b5-1>\s*(1|true|yes)\s*</isRule10b5-1>", text, re.IGNORECASE))


def role_checked(text: str, role: str) -> bool:
    plain = normalize(text)
    pattern = rf"X\s+{re.escape(role)}|{re.escape(role)}\s+X"
    return bool(re.search(pattern, plain, re.IGNORECASE))


def extract_share_numbers_near_transaction(text: str) -> list[float]:
    plain = normalize(text)
    numbers = []
    for match in re.finditer(r"\b(?:P|S|A|M|F|G|D)\b\s+([0-9][0-9,]*(?:\.\d+)?)", plain):
        try:
            numbers.append(float(match.group(1).replace(",", "")))
        except ValueError:
            pass
    for match in re.finditer(r"(?:acquired|disposed of|underlying).*?([0-9][0-9,]*(?:\.\d+)?)", plain, re.IGNORECASE):
        try:
            numbers.append(float(match.group(1).replace(",", "")))
        except ValueError:
            pass
    return numbers


def amount_after_phrase(plain: str, phrase: str) -> float | None:
    idx = plain.lower().find(phrase)
    if idx < 0:
        return None
    window = plain[idx : idx + 400]
    match = re.search(r"\b([0-9][0-9,]*(?:\.\d+)?)\b", window)
    return float(match.group(1).replace(",", "")) if match else None


def price_values_from_form4(text: str) -> list[float]:
    plain = normalize(text)
    values = []
    for match in re.finditer(r"\$\s*([0-9][0-9,]*(?:\.\d+)?)", plain):
        try:
            values.append(float(match.group(1).replace(",", "")))
        except ValueError:
            pass
    return values


def schedule_type_from_text(plain: str, row: pd.Series) -> str:
    event_title = clean_missing(row.get("event_title"))
    combined = f"{event_title} {plain[:1000]}"
    match = re.search(r"\b(SC\s+13[DG](?:/A)?|13[DG](?:/A)?)\b", combined, re.IGNORECASE)
    return match.group(1).upper().replace(" ", "_") if match else ""


def holder_name(plain: str) -> str:
    patterns = [
        r"Name of Reporting Person\s*[:\-]?\s*([A-Z][A-Za-z0-9 .,&'-]{2,120})",
        r"Reporting Person\s*[:\-]?\s*([A-Z][A-Za-z0-9 .,&'-]{2,120})",
        r"Filed by\s*([A-Z][A-Za-z0-9 .,&'-]{2,120})",
    ]
    for pattern in patterns:
        match = re.search(pattern, plain, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def share_amounts(plain: str) -> list[float]:
    values = []
    for match in re.finditer(r"([0-9][0-9,]*)\s+(?:shares|shares of)", plain, re.IGNORECASE):
        try:
            values.append(float(match.group(1).replace(",", "")))
        except ValueError:
            pass
    return values


def money_values(text: str) -> list[float]:
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
    return values


def max_money(text: str) -> float | None:
    values = money_values(text)
    return max(values) if values else None


def first_percent(text: str) -> float | None:
    match = PCT_RE.search(text)
    return float(match.group(1)) if match else None


def first_date(text: str) -> str:
    match = DATE_RE.search(text)
    return match.group(0) if match else ""


def count_present(primitives: dict[str, object]) -> int:
    count = 0
    for value in primitives.values():
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        if isinstance(value, list) and not value:
            continue
        if isinstance(value, (int, float)) and value == 0:
            continue
        count += 1
    return count


def split_pipe(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part for part in str(value).split("|") if part]


def clean_missing(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)
