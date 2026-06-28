from __future__ import annotations

from pathlib import Path

from src.brain.l3.config_loader import load_simple_yaml


DEFAULT_SOURCE_RELIABILITY_CONFIG = Path("configs/brain/l3_source_reliability.yaml")


def load_source_reliability_config(path: str | Path = DEFAULT_SOURCE_RELIABILITY_CONFIG) -> dict[str, float]:
    raw = load_simple_yaml(path)
    return {str(key): float(value) for key, value in raw.items()}


def source_reliability_score(
    authority_class: str,
    *,
    config: dict[str, float] | None = None,
    default: float = 0.0,
) -> float:
    reliability = config if config is not None else load_source_reliability_config()
    key = str(authority_class or "").strip().lower()
    return max(0.0, min(1.0, float(reliability.get(key, default))))


def classify_source_authority(source_family: str, provider: str = "") -> str:
    family = str(source_family or "").strip().lower()
    vendor = str(provider or "").strip().lower()
    if family in {"sec", "sec_filing", "sec_event"}:
        return "sec_primary"
    if family in {"company_ir", "ir", "company_press_release"}:
        return "company_ir_primary"
    if family in {"market_microstructure", "market_bar", "quote", "trade"}:
        return "official_primary"
    if vendor in {"official_public_releases", "official_primary"}:
        return "official_primary"
    if vendor in {"marketaux", "marketaux_news_free", "licensed_metadata_proxy", "licensed_news_metadata_proxy"}:
        return "licensed_metadata_proxy"
    if vendor in {
        "gdelt",
        "gdelt_news_events",
        "news_discovery_proxy",
        "public_newswire_feeds",
        "public_context_news_feeds",
        "public_market_macro_news_feeds",
    }:
        return "news_discovery_proxy"
    if family in {"news", "news_event", "gdelt", "news_discovery", "historical_artifact"}:
        return "news_discovery_proxy"
    if not family:
        return "missing_source"
    return "uncertified_source"
