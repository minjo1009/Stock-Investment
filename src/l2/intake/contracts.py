from __future__ import annotations

import hashlib

INTAKE_ONLY_NOT_MATERIALIZED = "INTAKE_ONLY_NOT_MATERIALIZED"
FEATURE_ADMISSION_PENDING_PRIMITIVE_VALIDATION = "FEATURE_ADMISSION_PENDING_PRIMITIVE_VALIDATION"
FEATURE_ADMISSION_PENDING_MAPPING_VALIDATION = "FEATURE_ADMISSION_PENDING_MAPPING_VALIDATION"
FEATURE_ADMISSION_PENDING_NEWS_EFFECT_VALIDATION = "FEATURE_ADMISSION_PENDING_NEWS_EFFECT_VALIDATION"


FAMILY_POLICIES: dict[str, dict[str, str]] = {
    "daily_bars": {
        "primitive_envelope_type": "DAILY_MARKET_OBSERVATION",
        "feature_admission_state": FEATURE_ADMISSION_PENDING_PRIMITIVE_VALIDATION,
        "trading_feature_path": "CAN_BECOME_MARKET_FEATURE_AFTER_L2_PRIMITIVE_VALIDATION",
        "mapping_gate": "SYMBOL_MAPPING_REQUIRED",
    },
    "market_bars_5m": {
        "primitive_envelope_type": "INTRADAY_5M_MARKET_OBSERVATION",
        "feature_admission_state": FEATURE_ADMISSION_PENDING_PRIMITIVE_VALIDATION,
        "trading_feature_path": "CAN_BECOME_MARKET_FEATURE_AFTER_L2_PRIMITIVE_VALIDATION",
        "mapping_gate": "SYMBOL_MAPPING_REQUIRED",
    },
    "public_market_macro_news_feeds": {
        "primitive_envelope_type": "MACRO_CONTEXT_EVENT",
        "feature_admission_state": FEATURE_ADMISSION_PENDING_MAPPING_VALIDATION,
        "trading_feature_path": "CAN_BECOME_TRADING_FEATURE_AFTER_MACRO_SCOPE_AND_ASOF_VALIDATION",
        "mapping_gate": "MACRO_SCOPE_OR_SYMBOL_MAPPING_REQUIRED",
    },
    "public_context_news_feeds": {
        "primitive_envelope_type": "PUBLIC_CONTEXT_EVENT",
        "feature_admission_state": FEATURE_ADMISSION_PENDING_MAPPING_VALIDATION,
        "trading_feature_path": "CAN_BECOME_TRADING_FEATURE_AFTER_ENTITY_MAPPING_AND_ASOF_VALIDATION",
        "mapping_gate": "ENTITY_OR_SYMBOL_MAPPING_REQUIRED",
    },
    "public_newswire_feeds": {
        "primitive_envelope_type": "NEWSWIRE_DISCOVERY_EVENT",
        "feature_admission_state": FEATURE_ADMISSION_PENDING_NEWS_EFFECT_VALIDATION,
        "trading_feature_path": "CAN_BECOME_TRADING_FEATURE_AFTER_TICKER_MAPPING_DEDUP_AND_EFFECT_WINDOW_VALIDATION",
        "mapping_gate": "HIGH_CONFIDENCE_TICKER_NEWS_MAPPING_REQUIRED",
    },
}


def family_policy(source_family: str) -> dict[str, str]:
    try:
        return FAMILY_POLICIES[source_family]
    except KeyError as exc:
        raise ValueError(f"unknown L2 intake source family: {source_family}") from exc


def build_intake_id(task_id: str, source_family: str, source_packet_id: str) -> str:
    payload = "|".join([task_id, source_family, source_packet_id])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"l2intake_{digest}"
