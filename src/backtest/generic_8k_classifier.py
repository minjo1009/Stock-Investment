from __future__ import annotations

import re
from dataclasses import asdict, dataclass


ITEM_RE = re.compile(r"item\s+(\d+\.\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class Generic8KClassification:
    item_numbers: list[str]
    agreement_family_state: str
    operating_transmission_state: str
    permission_state: str
    connection_rule_id: str
    required_next_evidence: str
    operating_candidate_flag: int
    operating_supported_flag: int
    material_definitive_agreement_flag: int
    purchase_agreement_flag: int
    operating_primitive_count: int
    subtype_trace: str

    def to_primitive(self) -> dict[str, object]:
        return asdict(self)


def classify_generic_8k_text(text: str) -> Generic8KClassification:
    lower = text.lower()
    item_numbers = sorted(set(ITEM_RE.findall(lower)))
    material = "material definitive agreement" in lower
    purchase_agreement = "purchase agreement" in lower
    operating_primitives = operating_primitive_matches(lower)
    primitive_count = len(operating_primitives)

    family, trace = classify_agreement_family(lower, purchase_agreement)
    transmission = classify_operating_transmission(family, primitive_count, lower)
    permission, rule, evidence, candidate, supported = classify_permission(family, transmission)

    return Generic8KClassification(
        item_numbers=item_numbers,
        agreement_family_state=family,
        operating_transmission_state=transmission,
        permission_state=permission,
        connection_rule_id=rule,
        required_next_evidence=evidence,
        operating_candidate_flag=candidate,
        operating_supported_flag=supported,
        material_definitive_agreement_flag=int(material),
        purchase_agreement_flag=int(purchase_agreement),
        operating_primitive_count=primitive_count,
        subtype_trace=trace,
    )


def classify_agreement_family(lower: str, purchase_agreement: bool) -> tuple[str, str]:
    if has_severance_language(lower):
        return "severance_or_change_in_control_context", "severance_or_change_in_control_language"
    if has_governance_board_language(lower):
        return "governance_board_context", "board_director_proxy_or_bylaws_language"
    if has_compensation_language(lower):
        return "compensation_award_context", "compensation_award_language"
    if has_strategic_investment_language(lower):
        return "strategic_investment_context", "investment_or_equity_purchase_language"
    if has_strategic_mna_language(lower, purchase_agreement):
        return "strategic_mna_context", "acquisition_merger_or_business_purchase_language"
    if has_financing_language(lower):
        return "financing_credit_context", "financing_or_securities_purchase_language"
    if has_financial_results_language(lower):
        return "financial_results_context", "financial_results_language"
    if has_supply_or_customer_contract_language(lower):
        return "supply_or_customer_contract_context", "customer_supply_order_or_contract_award_language"
    if has_commercial_operating_contract_language(lower):
        return "commercial_operating_contract_context", "commercial_operating_primitive_language"
    return "unclassified_generic_8k_context", "no_specific_8k_family_matched"


def classify_operating_transmission(family: str, primitive_count: int, lower: str) -> str:
    if family in {
        "compensation_award_context",
        "governance_board_context",
        "severance_or_change_in_control_context",
        "financial_results_context",
        "financing_credit_context",
        "strategic_investment_context",
        "unclassified_generic_8k_context",
    }:
        return "no_operating_transmission"
    if family == "strategic_mna_context":
        return "operating_transmission_candidate" if has_mna_transmission_language(lower) else "no_operating_transmission"
    if family in {"commercial_operating_contract_context", "supply_or_customer_contract_context"}:
        if primitive_count >= 2 and has_non_boilerplate_economic_language(lower):
            return "operating_transmission_supported"
        if primitive_count >= 1:
            return "operating_transmission_candidate"
        return "operating_language_only"
    return "no_operating_transmission"


def classify_permission(family: str, transmission: str) -> tuple[str, str, str, int, int]:
    if family == "compensation_award_context":
        return "not_applicable", "COMPENSATION_NEVER_OPERATING", "none; compensation awards belong to compensation/governance context", 0, 0
    if family == "governance_board_context":
        return "modifier_only", "GOVERNANCE_NEVER_OPERATING", "board, proxy, bylaw, or director-change context only", 0, 0
    if family == "severance_or_change_in_control_context":
        return "modifier_only", "SEVERANCE_NEVER_OPERATING", "severance/change-in-control terms are governance compensation context", 0, 0
    if family == "financial_results_context":
        return "review_required", "FINANCIAL_RESULTS_NEED_EARNINGS_INTERPRETER", "earnings/guidance surprise and expectations context", 0, 0
    if family == "financing_credit_context":
        return "review_required", "FINANCING_ROUTE_OUT", "financing instrument, proceeds, dilution, liquidity, and operating path", 0, 0
    if family == "strategic_investment_context":
        return "review_required", "INVESTMENT_TRANSACTION_REVIEW_REQUIRED", "business-unit economics, strategic fit, capital allocation, and operating path", 0, 0
    if family == "strategic_mna_context":
        if transmission == "operating_transmission_candidate":
            return "connection_candidate", "MNA_REQUIRES_TRANSMISSION", "acquired business revenue, customer, backlog, synergy, integration, capacity, or guidance evidence", 1, 0
        return "review_required", "MNA_REQUIRES_TRANSMISSION", "acquired business operating transmission evidence", 0, 0
    if family in {"commercial_operating_contract_context", "supply_or_customer_contract_context"}:
        if transmission == "operating_transmission_supported":
            return "connection_supported", "OPERATING_PATH_VISIBLE", "denominator, expectations, price absorption, and bundle review", 1, 1
        return "connection_candidate", "OPERATING_LANGUAGE_NEEDS_ECONOMIC_PATH", "customer, duration, revenue/order/backlog/guidance/margin/capacity, and denominator", 1, 0
    return "review_required", "UNCLASSIFIED_8K_REVIEW_REQUIRED", "item classifier and source text review", 0, 0


def has_financing_language(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(credit agreement|loan agreement|note purchase|securities purchase|convertible|warrants?|at-the-market|atm offering|shelf registration|registered direct offering|private placement|debenture)\b",
            lower,
        )
    )


def has_severance_language(lower: str) -> bool:
    return any(token in lower for token in ["severance benefits policy", "change in control severance", "change-in-control severance"])


def has_compensation_language(lower: str) -> bool:
    return any(
        token in lower
        for token in [
            "restricted stock unit",
            "performance stock unit",
            "stock option grant",
            "compensatory plan",
            "equity incentive",
            "long-term incentive",
            "award agreement",
        ]
    )


def has_governance_board_language(lower: str) -> bool:
    if any(token in lower for token in ["proxy statement", "bylaws", "audit committee", "compensation committee"]):
        return True
    if "director" not in lower and "board" not in lower:
        return False
    return bool(
        re.search(r"appointed[^.]{0,120}director", lower)
        or re.search(r"director[^.]{0,120}appointed", lower)
        or re.search(r"election[^.]{0,120}director", lower)
        or "fill a vacancy" in lower
        or "class iii director" in lower
        or "board of directors" in lower
    )


def has_financial_results_language(lower: str) -> bool:
    return bool(
        re.search(r"item\s+2\.02[^.]{0,160}(results of operations|financial condition)", lower)
        or "earnings release" in lower
        or "quarterly results" in lower
    )


def has_strategic_mna_language(lower: str, purchase_agreement: bool) -> bool:
    if any(token in lower for token in ["agreement to acquire", "merger agreement", "business combination", "acquisition agreement"]):
        return True
    if purchase_agreement and any(token in lower for token in ["acquire", "acquisition", "assets", "business", "subsidiary", "transaction"]):
        return True
    return False


def has_strategic_investment_language(lower: str) -> bool:
    return any(token in lower for token in ["investment agreement", "equity purchase agreement", "share purchase agreement", "strategic investment"])


def has_supply_or_customer_contract_language(lower: str) -> bool:
    return any(
        token in lower
        for token in [
            "customer agreement",
            "customer contract",
            "customer purchase order",
            "purchase order",
            "contract award",
            "supply agreement",
            "sales agreement",
            "master services agreement",
        ]
    )


def has_commercial_operating_contract_language(lower: str) -> bool:
    return any(
        token in lower
        for token in [
            "backlog",
            "revenue contribution",
            "guidance",
            "margin",
            "production capacity",
            "manufacturing capacity",
            "capacity expansion",
            "commercial contract",
            "customer",
        ]
    )


def has_mna_transmission_language(lower: str) -> bool:
    return any(
        token in lower
        for token in [
            "revenue contribution",
            "customer relationships",
            "backlog",
            "synergy",
            "integration",
            "production capacity",
            "manufacturing capacity",
            "guidance",
        ]
    )


def has_non_boilerplate_economic_language(lower: str) -> bool:
    return any(
        token in lower
        for token in [
            "revenue",
            "backlog",
            "guidance",
            "margin",
            "capacity",
            "production",
            "customer",
            "purchase order",
            "contract award",
            "duration",
            "term of",
        ]
    )


def operating_primitive_matches(lower: str) -> list[str]:
    primitives = []
    checks = {
        "named_customer_or_customer": ["customer"],
        "order_or_award": ["purchase order", "contract award", "order award"],
        "backlog": ["backlog"],
        "revenue": ["revenue contribution", "revenue"],
        "guidance": ["guidance"],
        "margin": ["margin"],
        "capacity_or_production": ["production capacity", "manufacturing capacity", "capacity expansion", "production"],
        "duration_or_scope": ["duration", "term of", "scope of work"],
        "supply_or_sales": ["supply agreement", "sales agreement"],
    }
    for name, tokens in checks.items():
        if any(token in lower for token in tokens):
            primitives.append(name)
    return primitives
