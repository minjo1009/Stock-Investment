from __future__ import annotations

from .contracts import DirectionReview, L3InputPrimitive


RISK_WORDS = (
    "charges",
    "penalty",
    "fraud",
    "lawsuit",
    "sanction",
    "recall",
    "investigation",
    "default",
    "bankruptcy",
)
SUPPORT_WORDS = (
    "contract",
    "award",
    "approval",
    "guidance raised",
    "record revenue",
    "expansion",
    "new order",
)


def classify_economic_meaning(row: L3InputPrimitive) -> tuple[str, str, DirectionReview, str, tuple[str, ...]]:
    text = " ".join(
        [
            row.source_family,
            row.source_key,
            row.feature_name,
            row.title,
            row.mapping_status,
        ]
    ).lower()
    dimension = "UNKNOWN"
    event_class = "SOURCE_CONTEXT"

    if "macro" in text or row.target_node_type == "MACRO":
        dimension = "MACRO_CONTEXT"
        event_class = "MACRO_CONTEXT_EVENT"
    if any(term in text for term in ("rate", "rates", "fed", "isda", "swap")):
        dimension = "RATES"
        event_class = "RATES_CONTEXT_EVENT"
    if any(term in text for term in ("inflation", "cpi", "ppi")):
        dimension = "INFLATION"
        event_class = "INFLATION_CONTEXT_EVENT"
    if any(term in text for term in ("energy", "oil", "gas", "power")):
        dimension = "ENERGY"
        event_class = "ENERGY_CONTEXT_EVENT"
    if any(term in text for term in ("cftc", "sec", "regulat", "charges", "penalty", "fraud")):
        dimension = "REGULATORY"
        event_class = "REGULATORY_CONTEXT_EVENT"
    if any(term in text for term in ("contract", "order", "customer")):
        dimension = "CUSTOMER_ORDER"
        event_class = "CUSTOMER_ORDER_CONTEXT_EVENT"
    if "guidance" in text or "earnings" in text:
        dimension = "GUIDANCE"
        event_class = "EARNINGS_CONTEXT_EVENT"

    direction = DirectionReview.CONTEXT_ONLY
    if any(term in text for term in RISK_WORDS):
        direction = DirectionReview.RISK_REVIEW
    elif any(term in text for term in SUPPORT_WORDS):
        direction = DirectionReview.SUPPORT_REVIEW

    confidence = "medium" if dimension != "UNKNOWN" and direction != DirectionReview.CONTEXT_ONLY else "low"
    reason_codes = (
        "RULE_BASED_DETERMINISTIC_CLASSIFIER",
        "DIAGNOSTIC_REVIEW_ONLY",
        "STATIC_CONFIDENCE_NOT_PROBABILITY",
    )
    return dimension, event_class, direction, confidence, reason_codes

