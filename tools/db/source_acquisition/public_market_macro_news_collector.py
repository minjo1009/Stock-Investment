from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

try:
    import requests
except ImportError:  # pragma: no cover - optional runtime fallback
    requests = None  # type: ignore[assignment]

from tools.db.source_acquisition.news_background_collector import classify_news_error, source_event, write_progress
from tools.db.source_acquisition.secret_redaction import redact_text
from tools.db.source_acquisition.source_capability_probe import (
    build_robot_parser,
    load_registry,
    robots_posture,
    robots_url_allowed,
)


PROVIDER = "public_market_macro_news_feeds"
SCHEMA_VERSION = 1
COLLECTOR_VERSION = "public_market_macro_news_collector.v0.1.11"
STOCKTITAN_ENTITY_MAPPING_VERSION = "stocktitan_public_url_symbol_mapper.v0.1.0"
DEFAULT_REGISTRY_PATH = Path("configs/source_registry/l0_public_news_capability_sources.json")
DEFAULT_RAW_DIR = Path("data/raw/l0_public_market_macro_news")
DEFAULT_ARTIFACT_DIR = Path("data/artifacts/l0_public_market_macro_news")
DEFAULT_STATE_PATH = DEFAULT_ARTIFACT_DIR / "collector_state.json"
DEFAULT_EVENT_PATH = DEFAULT_ARTIFACT_DIR / "collector_events.jsonl"
DEFAULT_PROGRESS_PATH = DEFAULT_ARTIFACT_DIR / "collector_progress.json"
DEFAULT_PLAN_PATH = DEFAULT_ARTIFACT_DIR / "collection_plan.json"
DEFAULT_STOP_PATH = DEFAULT_ARTIFACT_DIR / "STOP"
DEFAULT_LOG_PATH = Path("logs/l0_public_market_macro_news_collector.log")
DEFAULT_BACKFILL_RAW_DIR = Path("data/raw/l0_public_market_macro_news_backfill")
DEFAULT_BACKFILL_ARTIFACT_DIR = Path("data/artifacts/l0_public_market_macro_news_backfill")
DEFAULT_LIVE_SOURCES = (
    "cnbc_public_rss",
    "npr_public_radio_rss",
    "pbs_newshour_rss",
    "abc_news_public_rss",
    "cbs_news_public_rss",
    "census_public_rss",
    "yahoo_finance_public_rss",
    "nytimes_public_rss",
    "fox_business_public_rss",
    "investing_public_rss",
    "nasdaq_trader_notices",
    "bbc_public_rss",
    "ft_public_rss",
    "marketwatch_public_rss",
    "cointelegraph_public_rss",
    "decrypt_public_rss",
    "cryptoslate_public_rss",
    "oilprice_public_rss",
    "mining_copper_public_rss",
    "bleepingcomputer_public_rss",
    "krebsonsecurity_public_rss",
    "semiengineering_public_rss",
    "axios_public_rss",
    "the_verge_public_rss",
    "wired_business_public_rss",
    "siliconangle_public_rss",
    "securityweek_public_rss",
    "utilitydive_public_rss",
    "supplychaindive_public_rss",
    "biopharmadive_public_rss",
    "constructiondive_public_rss",
    "cfodive_public_rss",
    "restaurantdive_public_rss",
    "grocerydive_public_rss",
    "marketingdive_public_rss",
    "hrdive_public_rss",
    "medtechdive_public_rss",
    "highereddive_public_rss",
    "k12dive_public_rss",
    "smartcitiesdive_public_rss",
    "fiercebiotech_public_rss",
    "stat_public_rss",
    "breakingdefense_public_rss",
    "defensenews_global_public_rss",
    "spacenews_public_rss",
    "freightwaves_public_rss",
    "loadstar_public_rss",
    "seekingalpha_market_currents_rss",
    "stocktitan_public_rss",
    "finviz_public_news_html",
    "investors_public_rss",
    "investorplace_public_rss",
    "fxstreet_public_rss",
    "defenseone_public_rss",
    "nareit_public_rss",
    "etftrends_public_rss",
    "housingwire_public_rss",
    "americanbanker_public_rss",
    "techmeme_public_rss",
    "bankingdive_public_rss",
    "retaildive_public_rss",
    "ciodive_public_rss",
    "cybersecuritydive_public_rss",
    "paymentsdive_public_rss",
    "manufacturingdive_public_rss",
    "fooddive_public_rss",
    "healthcaredive_public_rss",
    "pharmavoice_public_rss",
)
DEFAULT_BACKFILL_SOURCES = (
    "guardian_open_platform",
    "ap_news_monthly_sitemap",
    "cnbc_public_rss",
    "wikimedia_current_events",
    "common_crawl_market_news_archive",
    "thehill_public_wp",
    "techcrunch_public_wp",
    "electrek_public_wp",
    "teslarati_public_wp",
    "semiengineering_public_wp",
    "bitcoinmagazine_public_wp",
    "nine_to_five_mac_public_wp",
    "nine_to_five_google_public_wp",
    "pv_magazine_usa_public_wp",
    "investors_public_wp",
    "investorplace_public_wp",
    "etftrends_public_wp",
    "housingwire_public_wp",
    "spacenews_public_wp",
    "carbonbrief_public_wp",
    "robotreport_public_wp",
    "utilitydive_public_rss",
    "supplychaindive_public_rss",
    "biopharmadive_public_rss",
    "bankingdive_public_rss",
    "retaildive_public_rss",
    "ciodive_public_rss",
    "cybersecuritydive_public_rss",
    "paymentsdive_public_rss",
    "manufacturingdive_public_rss",
    "fooddive_public_rss",
    "healthcaredive_public_rss",
    "pharmavoice_public_rss",
    "constructiondive_public_rss",
    "cfodive_public_rss",
    "restaurantdive_public_rss",
    "grocerydive_public_rss",
    "marketingdive_public_rss",
    "hrdive_public_rss",
    "medtechdive_public_rss",
    "highereddive_public_rss",
    "k12dive_public_rss",
    "smartcitiesdive_public_rss",
)
DEFAULT_BACKFILL_START_DATE = "2016-01-01"
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; Codex-L0-PublicMarketMacroNews/1.0; contact=operator)"
COMMON_CRAWL_COLLECTIONS_URL = "https://index.commoncrawl.org/collinfo.json"
COMMON_CRAWL_WARC_BASE_URL = "https://data.commoncrawl.org/"
COMMON_CRAWL_DEFAULT_PATTERNS = ("money.cnn.com/2016/*", "money.cnn.com/2018/*")
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
WIKIMEDIA_CONTEXT_HEADINGS = {
    "Armed conflicts and attacks",
    "Business and economy",
    "Disasters and accidents",
    "Health and medicine",
    "International relations",
    "Law and crime",
    "Politics and elections",
    "Science and technology",
}

TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("monetary_policy", ("federal reserve", "fomc", "interest rate", "rate cut", "rate hike", "central bank", "yield")),
    ("inflation", ("inflation", "cpi", "ppi", "prices", "price index", "consumer prices")),
    ("labor_market", ("jobs", "payroll", "employment", "unemployment", "wages", "labor market")),
    ("growth", ("economy", "economic", "gdp", "growth", "recession", "slowdown", "productivity")),
    ("policy", ("policy", "election", "government", "congress", "regulation", "tax", "trade")),
    ("geopolitics", ("war", "sanction", "tariff", "iran", "china", "russia", "ukraine", "export control")),
    ("ai_infrastructure", ("artificial intelligence", "generative ai", "ai", "gpu", "data center", "semiconductor")),
    ("crypto_digital_assets", ("crypto", "bitcoin", "ether", "stablecoin", "digital asset")),
    ("energy", ("oil", "gas", "opec", "energy", "crude", "lng", "solar", "wind")),
    ("supply_chain", ("supply chain", "shipping", "freight", "logistics", "port", "truck", "rail", "container")),
    ("cyber_security", ("cyber", "ransomware", "hack", "breach", "malware", "security flaw", "vulnerability")),
    ("healthcare_biotech", ("fda", "drug", "biotech", "pharma", "vaccine", "clinical trial", "medicare", "healthcare")),
    ("defense_geopolitics", ("defense", "missile", "drone", "military", "pentagon", "nato", "weapons", "fighter jet")),
    ("space_launch", ("space", "satellite", "rocket", "launch", "spacex", "starlink", "orbit")),
    ("climate_policy", ("climate", "emissions", "carbon", "renewable", "electric grid", "utility")),
    ("robotics_automation", ("robot", "robotics", "automation", "industrial automation", "warehouse automation")),
    ("market_structure", ("nasdaq", "exchange", "halt", "listing", "trading", "etf", "index")),
    ("risk_appetite", ("stocks", "stock market", "market", "volatility", "credit", "liquidity", "risk", "bond", "dow", "s&p", "wall street")),
)
COMMON_CRAWL_ARCHIVE_REQUIRED_TITLE_TERMS = (
    "fed",
    "federal reserve",
    "rate",
    "central bank",
    "inflation",
    "cpi",
    "ppi",
    "gdp",
    "jobs",
    "payroll",
    "unemployment",
    "recession",
    "economy",
    "economic",
    "stocks",
    "stock market",
    "bull market",
    "bear market",
    "wall street",
    "dow",
    "s&p",
    "nasdaq",
    "bond",
    "yield",
    "oil",
    "crude",
    "opec",
    "u.s. dollar",
    "dollar index",
    "china",
    "russia",
    "europe",
    "tariff",
    "trade",
    "wholesale sales",
    "retail sales",
    "bitcoin",
    "crypto",
)
AP_ARCHIVE_REQUIRED_TITLE_TERMS = (
    "federal reserve",
    "fed",
    "interest rate",
    "rate hike",
    "rate cut",
    "inflation",
    "economy",
    "economic",
    "recession",
    "jobs",
    "payroll",
    "unemployment",
    "stock market",
    "stocks",
    "wall street",
    "oil",
    "opec",
    "energy",
    "china",
    "russia",
    "ukraine",
    "iran",
    "tariff",
    "trade",
    "election",
    "congress",
    "tax",
    "regulation",
    "border",
    "migrant",
    "migration",
    "refugee",
    "immigration",
    "sanction",
    "cyber",
    "hack",
    "data breach",
    "fda",
    "biotech",
    "drug",
    "defense",
    "missile",
    "satellite",
    "space",
    "climate",
    "shipping",
    "supply chain",
)


@dataclass(frozen=True)
class PublicMarketMacroNewsConfig:
    registry_path: Path = DEFAULT_REGISTRY_PATH
    raw_dir: Path = DEFAULT_RAW_DIR
    state_path: Path = DEFAULT_STATE_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    plan_path: Path = DEFAULT_PLAN_PATH
    stop_path: Path = DEFAULT_STOP_PATH
    log_path: Path = DEFAULT_LOG_PATH
    sources: tuple[str, ...] = DEFAULT_LIVE_SOURCES
    max_items_per_source: int = 50
    max_fetches_per_source: int = 6
    cycle_sleep_seconds: int = 1800
    request_sleep_seconds: float = 1.0
    timeout_seconds: int = 45
    max_bytes: int = 3_000_000
    max_cycles: int = 0
    backfill_start_date: str = DEFAULT_BACKFILL_START_DATE
    backfill_end_date: str = ""
    guardian_page_size: int = 50


class HtmlMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        if lower == "meta":
            key = (values.get("property") or values.get("name") or values.get("itemprop") or "").lower()
            content = normalize_text(values.get("content", ""))
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif lower == "title":
            self._in_title = True

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title = normalize_text(f"{self.title} {data}")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False


class HtmlHeadlineLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = ""
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        href = normalize_text(values.get("href", ""))
        if href:
            self._href = href
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href:
            return
        title = normalize_text(" ".join(self._text_parts))
        if title:
            self.links.append((self._href, title))
        self._href = ""
        self._text_parts = []


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def user_agent() -> str:
    return os.environ.get("L0_NEWS_USER_AGENT") or os.environ.get("SEC_USER_AGENT") or DEFAULT_USER_AGENT


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def deep_text(element: ET.Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for child in element.iter():
        if strip_ns(child.tag) in wanted and child.text:
            return normalize_text(child.text)
        if strip_ns(child.tag) in wanted:
            text = normalize_text(" ".join(child.itertext()))
            if text:
                return text
    return ""


def atom_link(element: ET.Element) -> str:
    for child in element.iter():
        if strip_ns(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return normalize_text(href)
            if child.text:
                return normalize_text(child.text)
    return ""


def parse_datetime_value(value: str) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return f"{text}T00:00:00Z"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, IndexError, AttributeError):
        return text


def parse_date_value(value: str, *, default: date | None = None) -> date | None:
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return default


def row_date_within_window(row: dict[str, Any], *, start: date, end: date) -> bool:
    row_date = parse_date_value(str(row.get("published_at") or row.get("event_time") or ""))
    return row_date is None or start <= row_date <= end


def canonicalize_news_url(source_url: str) -> str:
    parsed = urlparse(source_url.split("#", 1)[0])
    path = re.sub(r"/index\.html?$", "", parsed.path, flags=re.IGNORECASE)
    if path != "/":
        path = path.rstrip("/")
    return parsed._replace(path=path or "/", query="", fragment="").geturl()


def strip_html(value: str) -> str:
    return normalize_text(re.sub(r"<[^>]+>", " ", unescape(str(value or ""))))


def title_matches_terms(title: str, terms: tuple[str, ...] | list[str]) -> bool:
    haystack = normalize_text(title).lower()
    return any(re.search(rf"(?<![a-z0-9]){re.escape(str(term).lower())}(?![a-z0-9])", haystack) for term in terms if normalize_text(str(term)))


def request_sleep_seconds(source: dict[str, Any], config: PublicMarketMacroNewsConfig) -> float:
    try:
        source_delay = float(source.get("crawl_delay_seconds") or 0.0)
    except (TypeError, ValueError):
        source_delay = 0.0
    return max(float(config.request_sleep_seconds), source_delay, 0.0)


def sleep_between_source_requests(source: dict[str, Any], config: PublicMarketMacroNewsConfig) -> None:
    delay = request_sleep_seconds(source, config)
    if delay > 0:
        time.sleep(delay)


def source_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def safe_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.=-]+", "_", value)[:120] or "unknown"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def row_hash(row: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "provider": row.get("provider"),
            "source_key": row.get("source_key"),
            "title": row.get("title"),
            "canonical_url": row.get("canonical_url") or row.get("source_url"),
            "published_at": row.get("published_at"),
        },
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stocktitan_symbol_from_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    match = re.search(r"/news/([A-Z0-9][A-Z0-9.-]{0,11})/[^/]+\.html?$", parsed.path, flags=re.IGNORECASE)
    if not match:
        return ""
    symbol = match.group(1).upper().strip(".-")
    return symbol if re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,11}", symbol) else ""


def apply_stocktitan_source_ticker(row: dict[str, Any]) -> dict[str, Any]:
    symbol = stocktitan_symbol_from_url(str(row.get("source_url") or row.get("canonical_url") or ""))
    if not symbol:
        return row
    row.update(
        {
            "ticker_mapping_required_flag": 1,
            "symbols": [symbol],
            "entities": [],
            "entity_map": [
                {
                    "symbol": symbol,
                    "match_type": "explicit_source_url_path",
                    "matched_text": symbol,
                    "source_field": "source_url",
                    "entity_source": "stocktitan_public_url_path",
                }
            ],
            "entity_mapping_status": "MAPPED_EXPLICIT_SOURCE_TICKER",
            "entity_mapping_methods": ["stocktitan_url_path_symbol"],
            "entity_mapping_version": STOCKTITAN_ENTITY_MAPPING_VERSION,
            "entity_mapping_inferred_flag": 0,
            "stocktitan_source_ticker_flag": 1,
        }
    )
    row["headline_hash"] = row_hash(row)
    return row


def selected_sources(config: PublicMarketMacroNewsConfig) -> list[dict[str, Any]]:
    wanted = set(config.sources)
    return [
        source
        for source in load_registry(config.registry_path)
        if str(source.get("source_key")) in wanted and bool(source.get("enabled", True))
    ]


def context_topics(source: dict[str, Any], title: str) -> list[str]:
    topics = {str(topic) for topic in source.get("context_scope", []) if str(topic)}
    topics.update(keyword_context_topics(title))
    return sorted(topics)


def keyword_context_topics(title: str) -> list[str]:
    topics = set()
    for topic, tokens in TOPIC_RULES:
        if title_matches_terms(title, tokens):
            topics.add(topic)
    return sorted(topics)


def common_crawl_archive_title_is_relevant(title: str) -> bool:
    return title_matches_terms(title, COMMON_CRAWL_ARCHIVE_REQUIRED_TITLE_TERMS)


def ap_archive_text_is_relevant(title: str, description: str) -> bool:
    text = normalize_text(f"{title} {description}")
    return bool(keyword_context_topics(text)) or title_matches_terms(text, AP_ARCHIVE_REQUIRED_TITLE_TERMS)


def build_row(
    *,
    source: dict[str, Any],
    title: str,
    source_url: str,
    published_at: str,
    published_at_text: str,
    captured_at: str,
    source_page_url: str,
    capture_method: str,
    title_source: str = "",
    published_at_source: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_key = str(source.get("source_key", "unknown"))
    cleaned_title = normalize_text(unescape(title))
    parsed_published = parse_datetime_value(published_at)
    row: dict[str, Any] = {
        "provider": PROVIDER,
        "source_key": source_key,
        "source_display_name": source.get("display_name", source_key),
        "source_class": source.get("source_class") or source.get("authority_class", ""),
        "context_source_class": source.get("source_class") or source.get("authority_class", ""),
        "context_scope": [str(item) for item in source.get("context_scope", [])],
        "context_topic_candidates": context_topics(source, cleaned_title),
        "title": cleaned_title,
        "source_url": source_url,
        "canonical_url": canonicalize_news_url(source_url),
        "published_at": parsed_published,
        "published_at_text": published_at_text,
        "detected_at": captured_at,
        "captured_at": captured_at,
        "event_time": parsed_published or captured_at,
        "source_page_url": source_page_url,
        "capture_method": capture_method,
        "language": source.get("language", "en"),
        "title_source": title_source,
        "published_at_source": published_at_source,
        "source_time_certified_flag": int(bool(parsed_published)),
        "usable_for_historical_backtest_flag": 0,
        "macro_context_candidate_flag": 1,
        "ticker_mapping_required_flag": 0,
        "symbols": [],
        "entities": [],
        "entity_map": [],
        "entity_mapping_status": "NOT_REQUIRED_MARKET_MACRO_CONTEXT",
        "entity_mapping_methods": [],
        "entity_mapping_version": "public_market_macro_news_mapper.not_required.v0.1.0",
        "entity_mapping_inferred_flag": 0,
    }
    if extra:
        row.update(extra)
    row["headline_hash"] = row_hash(row)
    return row


def fetch_url_requests_fallback(url: str, config: PublicMarketMacroNewsConfig, *, started: float, fallback_reason: str) -> dict[str, Any] | None:
    if requests is None:
        return None
    try:
        response = requests.get(  # type: ignore[union-attr]
            url,
            headers={
                "User-Agent": user_agent(),
                "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,application/json,text/html,*/*",
            },
            timeout=config.timeout_seconds,
            allow_redirects=True,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": 0,
            "content_type": "",
            "headers": {},
            "bytes": b"",
            "truncated": False,
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": type(exc).__name__,
            "error_message": redact_text(str(exc))[:500],
            "transport": "requests_fallback",
            "fallback_reason": fallback_reason,
        }
    payload = response.content[: config.max_bytes + 1]
    truncated = len(payload) > config.max_bytes
    payload = payload[: config.max_bytes]
    return {
        "ok": 200 <= int(response.status_code) < 400,
        "requested_url": url,
        "resolved_url": response.url,
        "status_code": int(response.status_code),
        "content_type": response.headers.get("Content-Type", ""),
        "headers": dict(response.headers.items()),
        "bytes": payload,
        "truncated": truncated,
        "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
        "error_category": "" if 200 <= int(response.status_code) < 400 else "HTTPError",
        "error_message": "" if 200 <= int(response.status_code) < 400 else f"HTTP status {response.status_code}",
        "transport": "requests_fallback",
        "fallback_reason": fallback_reason,
    }


def fetch_url(url: str, config: PublicMarketMacroNewsConfig) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = Request(
            url,
            headers={
                "User-Agent": user_agent(),
                "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,application/json,text/html,*/*",
            },
        )
        with urlopen(request, timeout=config.timeout_seconds) as response:  # noqa: S310
            payload = response.read(config.max_bytes + 1)
            truncated = len(payload) > config.max_bytes
            payload = payload[: config.max_bytes]
            headers = dict(response.headers.items())
            return {
                "ok": True,
                "requested_url": url,
                "resolved_url": response.geturl(),
                "status_code": int(response.status),
                "content_type": headers.get("Content-Type", ""),
                "headers": headers,
                "bytes": payload,
                "truncated": truncated,
                "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
                "error_category": "",
                "error_message": "",
            }
    except HTTPError as exc:
        try:
            payload = exc.read(config.max_bytes + 1)
        except Exception:  # noqa: BLE001
            payload = b""
        if int(getattr(exc, "code", 0) or 0) == 403:
            fallback = fetch_url_requests_fallback(url, config, started=started, fallback_reason="urllib_http_403")
            if fallback and fallback.get("ok"):
                return fallback
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": int(getattr(exc, "code", 0) or 0),
            "content_type": (exc.headers or {}).get("Content-Type", "") if getattr(exc, "headers", None) else "",
            "headers": dict((exc.headers or {}).items()) if getattr(exc, "headers", None) else {},
            "bytes": payload[: config.max_bytes],
            "truncated": len(payload) > config.max_bytes,
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": type(exc).__name__,
            "error_message": redact_text(str(exc))[:500],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": 0,
            "content_type": "",
            "headers": {},
            "bytes": b"",
            "truncated": False,
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": type(exc).__name__,
            "error_message": redact_text(str(exc))[:500],
        }


def write_response(raw_dir: Path, *, source_key: str, capability: str, url: str, fetched: dict[str, Any]) -> dict[str, Any]:
    captured_at = now_z()
    stamp = captured_at.replace(":", "").replace("-", "").replace(".", "")
    target = raw_dir / f"provider={PROVIDER}" / f"source={safe_part(source_key)}" / f"capability={safe_part(capability)}" / f"captured_at={stamp}"
    target.mkdir(parents=True, exist_ok=True)
    body_path = target / "response.bin"
    metadata_path = target / "metadata.json"
    payload = fetched.get("bytes", b"")
    body_path.write_bytes(payload)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "provider": PROVIDER,
        "source_key": source_key,
        "capability": capability,
        "requested_url": url,
        "resolved_url": fetched.get("resolved_url", url),
        "captured_at": captured_at,
        "status_code": fetched.get("status_code", 0),
        "content_type": fetched.get("content_type", ""),
        "elapsed_ms": fetched.get("elapsed_ms", 0),
        "truncated": bool(fetched.get("truncated", False)),
        "ok": bool(fetched.get("ok", False)),
        "error_category": fetched.get("error_category", ""),
        "error_message_redacted": fetched.get("error_message", ""),
        "transport": fetched.get("transport", "urllib"),
        "fallback_reason": fetched.get("fallback_reason", ""),
        "body_path": str(body_path),
        "body_sha256": sha256_bytes(payload),
        "body_size_bytes": len(payload),
        "secret_logged_flag": 0,
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def parse_feed_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []
    tag = strip_ns(root.tag).lower()
    if tag not in {"rss", "rdf", "feed"}:
        return []
    item_tag = "entry" if tag == "feed" else "item"
    rows: list[dict[str, Any]] = []
    for item in [node for node in root.iter() if strip_ns(node.tag) == item_tag]:
        title = deep_text(item, ("title",))
        link = deep_text(item, ("link",)) or atom_link(item) or deep_text(item, ("guid",))
        published = deep_text(item, ("pubDate", "published", "updated", "date"))
        if not title or not link:
            continue
        row = build_row(
            source=source,
            title=title,
            source_url=link,
            published_at=published,
            published_at_text=published,
            captured_at=captured_at,
            source_page_url=source_page_url,
            capture_method="rss_or_atom",
            title_source="rss_title",
            published_at_source="rss_pubdate" if published else "",
        )
        if bool(source.get("stocktitan_ticker_from_url")):
            row = apply_stocktitan_source_ticker(row)
            if bool(source.get("stocktitan_require_source_ticker", True)) and not row.get("symbols"):
                continue
        rows.append(row)
    return rows


def parse_html_headline_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    parser = HtmlHeadlineLinkParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
    required_url_terms = [str(term).lower() for term in source.get("html_required_url_terms", []) if normalize_text(str(term))]
    min_title_length = int(source.get("html_min_title_length") or 18)
    require_topic = bool(source.get("html_required_topic_match", False))
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for href, raw_title in parser.links:
        if href.lower().startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        source_url = urljoin(source_page_url, href)
        title = normalize_text(raw_title)
        if len(title) < min_title_length:
            continue
        if required_url_terms and not any(term in source_url.lower() for term in required_url_terms):
            continue
        topic_candidates = keyword_context_topics(title)
        if require_topic and not topic_candidates:
            continue
        key = f"{title}|{canonicalize_news_url(source_url)}"
        if key in seen:
            continue
        seen.add(key)
        row = build_row(
            source=source,
            title=title,
            source_url=source_url,
            published_at="",
            published_at_text="",
            captured_at=captured_at,
            source_page_url=source_page_url,
            capture_method="public_html_anchor_headline",
            title_source="html_anchor_text",
            published_at_source="",
            extra={
                "source_time_certified_flag": 0,
                "usable_for_historical_backtest_flag": 0,
                "html_discovery_only_flag": 1,
            },
        )
        row["context_topic_candidates"] = sorted(set(row.get("context_topic_candidates", [])) | set(topic_candidates))
        rows.append(row)
    return rows


def parse_guardian_api_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        decoded = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return [], {}
    response = decoded.get("response", {}) if isinstance(decoded, dict) else {}
    results = response.get("results", []) if isinstance(response, dict) else []
    rows: list[dict[str, Any]] = []
    for item in results if isinstance(results, list) else []:
        if not isinstance(item, dict):
            continue
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        title = str(fields.get("headline") or item.get("webTitle") or "")
        url = str(item.get("webUrl") or fields.get("shortUrl") or "")
        published = str(item.get("webPublicationDate") or "")
        if not title or not url:
            continue
        rows.append(
            build_row(
                source=source,
                title=title,
                source_url=url,
                published_at=published,
                published_at_text=published,
                captured_at=captured_at,
                source_page_url=source_page_url,
                capture_method="guardian_open_platform_api",
                title_source="webTitle",
                published_at_source="webPublicationDate" if published else "",
                extra={
                    "section_id": item.get("sectionId", ""),
                    "document_type": item.get("type", ""),
                    "summary": fields.get("trailText", ""),
                },
            )
        )
    metadata = {
        "status": response.get("status", ""),
        "total": response.get("total", 0),
        "current_page": response.get("currentPage", 0),
        "pages": response.get("pages", 0),
        "page_size": response.get("pageSize", 0),
    }
    return rows, metadata


def parse_wordpress_rest_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        decoded = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return [], {}
    items = decoded if isinstance(decoded, list) else []
    required_terms = [str(term) for term in source.get("wordpress_required_title_terms", [])]
    require_topic = bool(source.get("wordpress_required_topic_match", True))
    require_title_term = bool(source.get("wordpress_required_title_term_match", False))
    rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title_payload = item.get("title") if isinstance(item.get("title"), dict) else {}
        excerpt_payload = item.get("excerpt") if isinstance(item.get("excerpt"), dict) else {}
        title = strip_html(str(title_payload.get("rendered") or item.get("title") or ""))
        summary = strip_html(str(excerpt_payload.get("rendered") or ""))
        url = normalize_text(str(item.get("link") or ""))
        published = normalize_text(str(item.get("date_gmt") or item.get("date") or ""))
        if not title or not url or not published:
            continue
        topic_candidates = keyword_context_topics(title)
        matches_source_terms = title_matches_terms(title, required_terms)
        if require_title_term and required_terms and not matches_source_terms:
            continue
        if require_topic and required_terms and not topic_candidates and not matches_source_terms:
            continue
        row = build_row(
            source=source,
            title=title,
            source_url=url,
            published_at=published,
            published_at_text=published,
            captured_at=captured_at,
            source_page_url=source_page_url,
            capture_method="wordpress_rest_posts_api",
            title_source="wordpress_title_rendered",
            published_at_source="date_gmt" if item.get("date_gmt") else "date",
            extra={
                "summary": summary,
                "wp_post_id": item.get("id", ""),
                "wp_slug": item.get("slug", ""),
                "wp_categories": item.get("categories", []),
                "usable_for_historical_backtest_flag": 1,
            },
        )
        row["context_topic_candidates"] = sorted(set(row.get("context_topic_candidates", [])) | set(topic_candidates))
        rows.append(row)
    metadata = {
        "item_count": len(items),
        "filtered_count": len(rows),
    }
    return rows, metadata


def parse_sitemap_entries(payload: bytes) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []
    entries: list[dict[str, str]] = []
    for item in root:
        tag = strip_ns(item.tag)
        if tag not in {"url", "sitemap"}:
            continue
        entry: dict[str, str] = {}
        for child in item.iter():
            name = strip_ns(child.tag)
            if name in {"loc", "lastmod", "publication_date", "title"} and child.text:
                entry[name] = normalize_text(child.text)
        if entry.get("loc"):
            entries.append(entry)
    return entries


def html_metadata(payload: bytes) -> dict[str, str]:
    parser = HtmlMetadataParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
    return {
        "title": parser.meta.get("og:title") or parser.meta.get("twitter:title") or parser.title,
        "description": parser.meta.get("og:description") or parser.meta.get("description") or parser.meta.get("twitter:description", ""),
        "published_at": parser.meta.get("article:published_time") or parser.meta.get("datepublished") or parser.meta.get("date", ""),
        "modified_at": parser.meta.get("article:modified_time") or parser.meta.get("datemodified", ""),
    }


def cnbc_url_date(value: str) -> str:
    match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", str(value or ""))
    if not match:
        return ""
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}T00:00:00Z"


def cnbc_sitemap_index_url(source: dict[str, Any]) -> str:
    for url in source.get("sitemap_urls", []):
        text = str(url)
        if "sitemapAll.xml" in text:
            return text
    return "https://www.cnbc.com/sitemapAll.xml"


def ap_monthly_sitemap_url(source: dict[str, Any], unit: dict[str, Any]) -> str:
    unit_id = str(unit["unit_id"])
    yyyymm = unit_id.replace("-", "")
    template = normalize_text(str(source.get("ap_monthly_sitemap_template", "")))
    if template:
        return template.replace("{yyyymm}", yyyymm).replace("{yyyy_mm}", unit_id)
    return f"https://apnews.com/ap-sitemap-{yyyymm}.xml"


def monthly_sitemap_url(source: dict[str, Any], unit: dict[str, Any]) -> str:
    unit_id = str(unit["unit_id"])
    unit_date = parse_date_value(str(unit.get("from_date") or f"{unit_id}-01")) or date.fromisoformat(f"{unit_id}-01")
    month_name = MONTH_NAMES[unit_date.month - 1]
    template = normalize_text(str(source.get("monthly_sitemap_template", "")))
    if not template:
        base_url = str(source.get("base_url") or "").rstrip("/")
        template = f"{base_url}/news/archive/{{year}}/{{month_name_lower}}.xml"
    return (
        template.replace("{yyyymm}", unit_id.replace("-", ""))
        .replace("{yyyy_mm}", unit_id)
        .replace("{year}", f"{unit_date.year:04d}")
        .replace("{yyyy}", f"{unit_date.year:04d}")
        .replace("{month}", f"{unit_date.month:02d}")
        .replace("{mm}", f"{unit_date.month:02d}")
        .replace("{month_name_lower}", month_name.lower())
        .replace("{month_name}", month_name)
    )


def sitemap_archive_text_is_relevant(source: dict[str, Any], title: str, summary: str) -> bool:
    required_terms = [str(term) for term in source.get("sitemap_required_title_terms", [])]
    require_title_term = bool(source.get("sitemap_required_title_term_match", False))
    require_topic = bool(source.get("sitemap_required_topic_match", False))
    text = normalize_text(f"{title} {summary}")
    matches_source_terms = title_matches_terms(text, required_terms)
    topic_candidates = keyword_context_topics(text)
    if require_title_term and required_terms and not matches_source_terms:
        return False
    if require_topic and required_terms and not topic_candidates and not matches_source_terms:
        return False
    if require_topic and not required_terms and not topic_candidates:
        return False
    return True


def monthly_sitemap_article_meta_row(
    *,
    source: dict[str, Any],
    entry: dict[str, str],
    article_payload: bytes,
    captured_at: str,
    sitemap_url: str,
) -> dict[str, Any] | None:
    meta = html_metadata(article_payload)
    title = normalize_text(meta.get("title", ""))
    source_url = normalize_text(entry.get("loc", ""))
    summary = normalize_text(meta.get("description", ""))
    if not title or not source_url:
        return None
    if not sitemap_archive_text_is_relevant(source, title, summary):
        return None
    published_at = meta.get("published_at") or entry.get("lastmod", "")
    if not published_at:
        return None
    row = build_row(
        source=source,
        title=title,
        source_url=source_url,
        published_at=published_at,
        published_at_text=published_at,
        captured_at=captured_at,
        source_page_url=sitemap_url,
        capture_method="monthly_sitemap_article_meta",
        title_source="article_meta_og_title",
        published_at_source="article_meta_published_time" if meta.get("published_at") else "sitemap_lastmod",
        extra={
            "summary": summary,
            "archive_provider": source.get("display_name", source.get("source_key", "")),
            "sitemap_url": sitemap_url,
            "sitemap_lastmod": entry.get("lastmod", ""),
            "source_modified_at": normalize_text(meta.get("modified_at", "")),
            "usable_for_historical_backtest_flag": 0,
        },
    )
    row["context_topic_candidates"] = sorted(set(row.get("context_topic_candidates", [])) | set(keyword_context_topics(f"{title} {summary}")))
    return row


def ap_article_meta_row(
    *,
    source: dict[str, Any],
    entry: dict[str, str],
    article_payload: bytes,
    captured_at: str,
    sitemap_url: str,
) -> dict[str, Any] | None:
    meta = html_metadata(article_payload)
    title = normalize_text(meta.get("title", ""))
    source_url = normalize_text(entry.get("loc", ""))
    summary = normalize_text(meta.get("description", ""))
    if not title or not source_url:
        return None
    if not ap_archive_text_is_relevant(title, summary):
        return None
    published_at = meta.get("published_at") or entry.get("lastmod", "")
    if not published_at:
        return None
    row = build_row(
        source=source,
        title=title,
        source_url=source_url,
        published_at=published_at,
        published_at_text=published_at,
        captured_at=captured_at,
        source_page_url=sitemap_url,
        capture_method="ap_monthly_sitemap_article_meta",
        title_source="article_meta_og_title",
        published_at_source="article_meta_published_time" if meta.get("published_at") else "sitemap_lastmod",
        extra={
            "summary": summary,
            "archive_provider": "AP News monthly sitemap",
            "source_modified_at": normalize_text(meta.get("modified_at", "")),
            "usable_for_historical_backtest_flag": 0,
        },
    )
    row["context_topic_candidates"] = sorted(set(row.get("context_topic_candidates", [])) | set(keyword_context_topics(f"{title} {summary}")))
    return row


def cnbc_backfill_entry_date(entry: dict[str, str]) -> date | None:
    from_url = parse_date_value(cnbc_url_date(entry.get("loc", "")))
    if from_url:
        return from_url
    return parse_date_value(entry.get("lastmod", ""))


def cnbc_backfill_row(
    *,
    source: dict[str, Any],
    entry: dict[str, str],
    article_payload: bytes,
    captured_at: str,
    sitemap_url: str,
) -> dict[str, Any] | None:
    meta = html_metadata(article_payload)
    title = normalize_text(meta.get("title", ""))
    source_url = entry.get("loc", "")
    if not title or not source_url:
        return None
    title_topics = keyword_context_topics(title)
    if not title_topics:
        return None
    published_at = meta.get("published_at") or cnbc_url_date(source_url) or entry.get("lastmod", "")
    published_source = "article_meta" if meta.get("published_at") else "source_url_date" if cnbc_url_date(source_url) else "sitemap_lastmod"
    row = build_row(
        source=source,
        title=title,
        source_url=source_url,
        published_at=published_at,
        published_at_text=published_at,
        captured_at=captured_at,
        source_page_url=sitemap_url,
        capture_method="cnbc_sitemap_article_meta",
        title_source="article_meta_og_title",
        published_at_source=published_source,
        extra={
            "summary": normalize_text(meta.get("description", "")),
            "sitemap_url": sitemap_url,
            "sitemap_lastmod": entry.get("lastmod", ""),
            "source_time_certified_flag": 0,
            "usable_for_historical_backtest_flag": 0,
        },
    )
    row["context_topic_candidates"] = sorted(set(row.get("context_topic_candidates", [])) | set(title_topics))
    return row


def parse_common_crawl_collections(payload: bytes, *, start: date, end: date) -> list[dict[str, Any]]:
    try:
        decoded = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for item in decoded if isinstance(decoded, list) else []:
        if not isinstance(item, dict):
            continue
        from_date = parse_date_value(str(item.get("from", "")))
        to_date = parse_date_value(str(item.get("to", "")))
        if not from_date or not to_date:
            continue
        if to_date < start or from_date > end:
            continue
        cdx_api = normalize_text(str(item.get("cdx-api", "")))
        collection_id = normalize_text(str(item.get("id", "")))
        if not cdx_api or not collection_id:
            continue
        rows.append(
            {
                "id": collection_id,
                "name": normalize_text(str(item.get("name", ""))),
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "cdx-api": cdx_api,
            }
        )
    return sorted(rows, key=lambda row: (row["from"], row["id"]))


def common_crawl_url_patterns(source: dict[str, Any]) -> list[str]:
    patterns = [normalize_text(str(value)) for value in source.get("common_crawl_url_patterns", []) if normalize_text(str(value))]
    return patterns or list(COMMON_CRAWL_DEFAULT_PATTERNS)


def build_common_crawl_index_url(collection: dict[str, Any], pattern: str, *, limit: int) -> str:
    params = [
        ("url", pattern),
        ("output", "json"),
        ("filter", "status:200"),
        ("filter", "mime:text/html"),
        ("fl", "url,timestamp,status,mime,digest,filename,offset,length"),
        ("limit", str(max(int(limit), 1))),
    ]
    return f"{collection['cdx-api']}?{urlencode(params)}"


def parse_common_crawl_index_rows(payload: bytes) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen = set()
    for line in payload.decode("utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            item = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        url = normalize_text(str(item.get("url", "")))
        filename = normalize_text(str(item.get("filename", "")))
        offset = normalize_text(str(item.get("offset", "")))
        length = normalize_text(str(item.get("length", "")))
        timestamp = normalize_text(str(item.get("timestamp", "")))
        key = f"{url}|{timestamp}|{item.get('digest', '')}"
        if not url or not filename or not offset or not length or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "url": url,
                "timestamp": timestamp,
                "status": normalize_text(str(item.get("status", ""))),
                "mime": normalize_text(str(item.get("mime", ""))),
                "digest": normalize_text(str(item.get("digest", ""))),
                "filename": filename,
                "offset": offset,
                "length": length,
            }
        )
    return rows


def common_crawl_timestamp_to_iso(value: str) -> str:
    text = normalize_text(value)
    if not re.fullmatch(r"\d{14}", text):
        return ""
    try:
        return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        return ""


def common_crawl_warc_url(record: dict[str, str]) -> str:
    return urljoin(COMMON_CRAWL_WARC_BASE_URL, record.get("filename", ""))


def fetch_common_crawl_warc_record(record: dict[str, str], config: PublicMarketMacroNewsConfig) -> dict[str, Any]:
    started = time.monotonic()
    url = common_crawl_warc_url(record)
    try:
        offset = int(record.get("offset", ""))
        length = int(record.get("length", ""))
    except ValueError:
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": 0,
            "content_type": "",
            "bytes": b"",
            "truncated": False,
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": "INVALID_COMMON_CRAWL_RANGE",
            "error_message": "Invalid Common Crawl WARC byte range",
        }
    if length <= 0 or length > int(config.max_bytes):
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": 0,
            "content_type": "",
            "bytes": b"",
            "truncated": length > int(config.max_bytes),
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": "COMMON_CRAWL_RECORD_TOO_LARGE",
            "error_message": f"Common Crawl record length {length} exceeds max_bytes {config.max_bytes}",
        }
    try:
        request = Request(
            url,
            headers={
                "User-Agent": user_agent(),
                "Accept": "application/octet-stream,*/*",
                "Range": f"bytes={offset}-{offset + length - 1}",
            },
        )
        with urlopen(request, timeout=config.timeout_seconds) as response:  # noqa: S310
            payload = response.read(length + 1)
            headers = dict(response.headers.items())
            return {
                "ok": True,
                "requested_url": url,
                "resolved_url": response.geturl(),
                "status_code": int(response.status),
                "content_type": headers.get("Content-Type", ""),
                "bytes": payload[:length],
                "truncated": len(payload) > length,
                "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
                "error_category": "",
                "error_message": "",
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": int(getattr(exc, "code", 0) or 0),
            "content_type": "",
            "bytes": b"",
            "truncated": False,
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": type(exc).__name__,
            "error_message": redact_text(str(exc))[:500],
        }


def common_crawl_html_payload(payload: bytes) -> bytes:
    try:
        decoded = gzip.decompress(payload)
    except (OSError, EOFError):
        decoded = payload
    lowered = decoded.lower()
    positions = [pos for pos in (lowered.find(b"<!doctype"), lowered.find(b"<html")) if pos >= 0]
    if not positions:
        return decoded
    return decoded[min(positions) :]


def common_crawl_archive_row(
    *,
    source: dict[str, Any],
    record: dict[str, str],
    warc_payload: bytes,
    captured_at: str,
    index_url: str,
    collection_id: str,
    url_pattern: str,
) -> dict[str, Any] | None:
    html_payload = common_crawl_html_payload(warc_payload)
    meta = html_metadata(html_payload)
    title = normalize_text(meta.get("title", ""))
    source_url = normalize_text(record.get("url", ""))
    if not title or not source_url:
        return None
    if not common_crawl_archive_title_is_relevant(title):
        return None
    archive_crawl_time = common_crawl_timestamp_to_iso(record.get("timestamp", ""))
    published_at = meta.get("published_at") or archive_crawl_time
    published_source = "article_meta" if meta.get("published_at") else "common_crawl_capture_timestamp" if archive_crawl_time else ""
    return build_row(
        source=source,
        title=title,
        source_url=source_url,
        published_at=published_at,
        published_at_text=published_at,
        captured_at=captured_at,
        source_page_url=index_url,
        capture_method="common_crawl_warc_article_meta",
        title_source="archived_html_meta_title",
        published_at_source=published_source,
        extra={
            "summary": normalize_text(meta.get("description", "")),
            "archive_provider": "Common Crawl",
            "archive_collection_id": collection_id,
            "archive_url_pattern": url_pattern,
            "archive_crawl_timestamp": record.get("timestamp", ""),
            "archive_crawl_time": archive_crawl_time,
            "common_crawl_digest": record.get("digest", ""),
            "warc_filename": record.get("filename", ""),
            "warc_offset": record.get("offset", ""),
            "warc_length": record.get("length", ""),
            "source_time_certified_flag": 0,
            "usable_for_historical_backtest_flag": 0,
        },
    )


def wikimedia_month_page(month: date) -> str:
    month_name = MONTH_NAMES[month.month - 1]
    return f"Portal:Current_events/{month_name}_{month.year:04d}"


def build_wikimedia_url(unit: dict[str, Any]) -> str:
    month = date.fromisoformat(str(unit["from_date"])[:10])
    page = wikimedia_month_page(month)
    return "https://en.wikipedia.org/wiki/" + page.replace(" ", "_")


def strip_html_text(value: str) -> str:
    text = re.sub(r"<style\b.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_text(unescape(text))


def external_links(value: str) -> list[str]:
    links: list[str] = []
    seen = set()
    for href in re.findall(r'href="([^"]+)"', value, flags=re.IGNORECASE):
        link = unescape(href)
        if link.startswith("//"):
            link = "https:" + link
        if not link.startswith(("http://", "https://")):
            continue
        if "wikipedia.org/" in link or "wikimedia.org/" in link:
            continue
        if link in seen:
            continue
        seen.add(link)
        links.append(link)
    return links


def parse_wikimedia_current_events_rows(
    payload: bytes,
    *,
    source: dict[str, Any],
    source_page_url: str,
    captured_at: str,
) -> list[dict[str, Any]]:
    html = payload.decode("utf-8", errors="ignore")
    markers = list(re.finditer(r'<div role="region"[^>]+class="[^"]*current-events-main vevent[^"]*"', html, flags=re.IGNORECASE))
    rows: list[dict[str, Any]] = []
    seen = set()
    for index, marker in enumerate(markers):
        chunk_end = markers[index + 1].start() if index + 1 < len(markers) else len(html)
        day_chunk = html[marker.start() : chunk_end]
        date_match = re.search(r'<span class="[^"]*\bdtstart\b[^"]*">(\d{4}-\d{2}-\d{2})</span>', day_chunk, flags=re.IGNORECASE)
        if not date_match:
            continue
        day = date_match.group(1)
        heading_matches = list(re.finditer(r'<div class="current-events-content-heading"[^>]*>(.*?)</div>', day_chunk, flags=re.IGNORECASE | re.DOTALL))
        for heading_index, heading_match in enumerate(heading_matches):
            heading = strip_html_text(heading_match.group(1))
            if heading not in WIKIMEDIA_CONTEXT_HEADINGS:
                continue
            section_end = heading_matches[heading_index + 1].start() if heading_index + 1 < len(heading_matches) else len(day_chunk)
            section_html = day_chunk[heading_match.end() : section_end]
            for item_match in re.finditer(r"<li>(.*?)</li>", section_html, flags=re.IGNORECASE | re.DOTALL):
                item_html = item_match.group(1)
                text = strip_html_text(item_html)
                if len(text) < 50 or text.lower() in {"edit", "history", "watch"}:
                    continue
                source_links = external_links(item_html)
                key = hashlib.sha256(f"{day}|{heading}|{text}".encode("utf-8")).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                title = text[:260]
                row = build_row(
                    source=source,
                    title=title,
                    source_url=f"{source_page_url}#{day}",
                    published_at=f"{day}T00:00:00Z",
                    published_at_text=day,
                    captured_at=captured_at,
                    source_page_url=source_page_url,
                    capture_method="wikimedia_current_events_archive_html",
                    title_source="current_events_bullet_text",
                    published_at_source="current_events_day_heading",
                    extra={
                        "section_id": heading,
                        "summary": text,
                        "source_links": source_links[:8],
                        "source_time_certified_flag": 0,
                        "usable_for_historical_backtest_flag": 0,
                    },
                )
                rows.append(row)
    return rows


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "processed_events": 0,
            "exported_events": 0,
            "empty_events": 0,
            "failed_events": 0,
            "blocked_events": 0,
            "source_cycles": {},
            "updated_at": now_z(),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {"schema_version": SCHEMA_VERSION, "processed_events": 0, "updated_at": now_z()}
    return payload if isinstance(payload, dict) else {"schema_version": SCHEMA_VERSION, "processed_events": 0, "updated_at": now_z()}


def save_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_z()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def append_event(path: Path, event: dict[str, Any]) -> None:
    event = dict(event)
    event["updated_at"] = now_z()
    event["diagnostic_only_flag"] = 1
    event["trade_authority_flag"] = 0
    event["broker_mutation_permitted_flag"] = 0
    event["real_capital_permitted_flag"] = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def log_line(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{now_z()} {message}\n")


def write_payload(
    config: PublicMarketMacroNewsConfig,
    *,
    source_key: str,
    captured_at: str,
    rows: list[dict[str, Any]],
    fetches: list[dict[str, Any]],
    collection_mode: str,
) -> Path:
    stamp = captured_at.replace(":", "").replace("-", "").replace(".", "")
    path = config.raw_dir / f"provider={PROVIDER}" / f"source={safe_part(source_key)}" / f"captured_at={stamp}" / "headlines.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "provider": PROVIDER,
        "collector_version": COLLECTOR_VERSION,
        "source_key": source_key,
        "captured_at": captured_at,
        "collection_mode": collection_mode,
        "headlines": rows,
        "fetches": fetches,
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def month_range(start: date, end: date) -> list[date]:
    months: list[date] = []
    cursor = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cursor <= last:
        months.append(cursor)
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = date(year, month, 1)
    return months


def month_end(month: date, limit: date) -> date:
    year = month.year + (1 if month.month == 12 else 0)
    next_month = date(year, 1 if month.month == 12 else month.month + 1, 1)
    return min(next_month - timedelta(days=1), limit)


def backfill_window(config: PublicMarketMacroNewsConfig) -> tuple[date, date]:
    start = parse_date_value(config.backfill_start_date, default=date.fromisoformat(DEFAULT_BACKFILL_START_DATE))
    end = parse_date_value(config.backfill_end_date, default=datetime.now(UTC).date())
    assert start is not None and end is not None
    return start, max(start, end)


def source_backfill_window(source: dict[str, Any], config: PublicMarketMacroNewsConfig) -> tuple[date, date]:
    start, end = backfill_window(config)
    source_start = parse_date_value(str(source.get("backfill_start_date") or ""))
    source_end = parse_date_value(str(source.get("backfill_end_date") or ""))
    if source_start and source_start > start:
        start = source_start
    if source_end and source_end < end:
        end = source_end
    return start, max(start, end)


def guardian_backfill_units(start: date, end: date) -> list[dict[str, Any]]:
    return [
        {"unit_id": month.strftime("%Y-%m"), "from_date": month.isoformat(), "to_date": month_end(month, end).isoformat()}
        for month in month_range(start, end)
    ]


def build_guardian_url(source: dict[str, Any], unit: dict[str, Any], *, page: int, page_size: int) -> str:
    base_url = "https://content.guardianapis.com/search"
    for url in source.get("api_urls", []):
        if "content.guardianapis.com/search" in str(url):
            base_url = "https://content.guardianapis.com/search"
            break
    query = {
        "from-date": unit["from_date"],
        "to-date": unit["to_date"],
        "section": "business|world",
        "show-fields": "headline,shortUrl,trailText",
        "api-key": "test",
        "page-size": max(min(int(page_size), 200), 1),
        "page": max(int(page), 1),
    }
    return f"{base_url}?{urlencode(query)}"


def wordpress_posts_api_base_url(source: dict[str, Any]) -> str:
    for url in source.get("api_urls", []):
        text = normalize_text(str(url))
        if "/wp-json/wp/v2/posts" in text:
            return text.split("?", 1)[0]
    return urljoin(str(source.get("base_url") or "").rstrip("/") + "/", "wp-json/wp/v2/posts")


def build_wordpress_posts_url(source: dict[str, Any], unit: dict[str, Any], *, page: int, page_size: int) -> str:
    query = {
        "after": f"{unit['from_date']}T00:00:00",
        "before": f"{unit['to_date']}T23:59:59",
        "per_page": max(min(int(page_size), 100), 1),
        "page": max(int(page), 1),
        "orderby": "date",
        "order": "asc",
        "_fields": "id,date,date_gmt,link,title,excerpt,categories,slug,type,status",
    }
    categories = normalize_text(str(source.get("wordpress_categories", "")))
    if categories:
        query["categories"] = categories
    return f"{wordpress_posts_api_base_url(source)}?{urlencode(query)}"


def build_plan(config: PublicMarketMacroNewsConfig, *, mode: str) -> dict[str, Any]:
    sources = selected_sources(config)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "provider": PROVIDER,
        "collector_version": COLLECTOR_VERSION,
        "mode": mode,
        "source_count": len(sources),
        "max_items_per_source": config.max_items_per_source,
        "max_fetches_per_source": config.max_fetches_per_source,
        "cycle_sleep_seconds": config.cycle_sleep_seconds,
        "request_sleep_seconds": config.request_sleep_seconds,
        "backfill_start_date": config.backfill_start_date,
        "backfill_end_date": config.backfill_end_date,
        "sources": {
            source["source_key"]: {
                "display_name": source.get("display_name", source.get("source_key")),
                "source_class": source.get("source_class") or source.get("authority_class", ""),
                "context_scope": source.get("context_scope", []),
                "rss_or_feed_urls": source.get("rss_or_feed_urls", []),
                "html_page_urls": source.get("html_page_urls", []),
                "sitemap_urls": source.get("sitemap_urls", []),
                "api_urls": source.get("api_urls", []),
                "historical_backfill_mode": source.get("historical_backfill_mode", ""),
                "terms_posture": source.get("terms_posture", ""),
                "diagnostic_only": True,
            }
            for source in sources
        },
        "permissions": {
            "diagnostic_only": True,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        },
    }
    config.plan_path.parent.mkdir(parents=True, exist_ok=True)
    config.plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return plan


def collect_source(source: dict[str, Any], config: PublicMarketMacroNewsConfig) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    base_url = str(source.get("base_url") or source.get("probe_url") or "")
    origin = source_origin(base_url)
    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")
    candidates = [
        {"url": str(url), "capability": "source_url", "parser": "feed"}
        for url in source.get("rss_or_feed_urls", [])
    ] + [
        {"url": str(url), "capability": "html_page", "parser": "html"}
        for url in source.get("html_page_urls", [])
    ]
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = [{"url": robots_url, "capability": "robots", "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json"))}]
    seen_rows = set()
    blocked = 0
    max_fetches = max(int(config.max_fetches_per_source), 1) + 1
    max_rows = max(int(config.max_items_per_source), 1)

    if candidates:
        sleep_between_source_requests(source, config)

    for candidate in candidates:
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        url = candidate["url"]
        if not robots_url_allowed(url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            fetches.append({"url": url, "status": "BLOCKED_ROBOTS", "skipped_by_robots": True})
            blocked += 1
            continue
        fetched = fetch_url(url, config)
        raw_meta = write_response(config.raw_dir, source_key=source_key, capability=str(candidate["capability"]), url=url, fetched=fetched)
        parsed: list[dict[str, Any]] = []
        if fetched.get("ok"):
            if candidate["parser"] == "html":
                parsed = parse_html_headline_rows(fetched.get("bytes", b""), source=source, source_page_url=str(fetched.get("resolved_url") or url), captured_at=captured_at)
            else:
                parsed = parse_feed_rows(fetched.get("bytes", b""), source=source, source_page_url=str(fetched.get("resolved_url") or url), captured_at=captured_at)
            for row in parsed:
                key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                if key in seen_rows:
                    continue
                seen_rows.add(key)
                rows.append(row)
                if len(rows) >= max_rows:
                    break
        record = {
            "url": url,
            "resolved_url": fetched.get("resolved_url", url),
            "ok": bool(fetched.get("ok")),
            "status_code": fetched.get("status_code", 0),
            "content_type": fetched.get("content_type", ""),
            "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
            "row_count": len(parsed),
        }
        if not fetched.get("ok"):
            record["error_category"] = fetched.get("error_category", "")
            record["error_message_redacted"] = fetched.get("error_message", "")
        fetches.append(record)
        sleep_between_source_requests(source, config)

    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="market_macro_watch")
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if blocked and not rows:
        status = "BLOCKED_ROBOTS"
    if not rows and any(fetch.get("error_category") for fetch in fetches):
        status, _category = classify_news_error(Exception("market macro source fetch failed"))
    topic_counts: dict[str, int] = {}
    for row in rows:
        for topic in row.get("context_topic_candidates", []):
            topic_counts[str(topic)] = topic_counts.get(str(topic), 0) + 1
    ticker_mapping_required = int(any(row.get("ticker_mapping_required_flag") in (1, "1", True) for row in rows))
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::market_macro_watch",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};fetches={len(fetches)};blocked_robots={blocked};"
            f"collector_version={COLLECTOR_VERSION};ticker_mapping_required={ticker_mapping_required};"
            f"context_topics={json.dumps(topic_counts, sort_keys=True)}"
        ),
    )


def collect_ap_monthly_sitemap_backfill(source: dict[str, Any], config: PublicMarketMacroNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    start, end = backfill_window(config)
    units = guardian_backfill_units(start, end)
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_units = set(backfill_state.setdefault("completed_units", []))
    entry_offsets = backfill_state.setdefault("entry_offsets", {})
    backfill_state["start_date"] = start.isoformat()
    backfill_state["end_date"] = end.isoformat()
    backfill_state["total_units"] = len(units)

    base_url = str(source.get("base_url") or "https://apnews.com")
    origin = source_origin(base_url)
    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")

    fetches: list[dict[str, Any]] = [
        {"url": robots_url, "capability": "robots", "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json"))}
    ]
    rows: list[dict[str, Any]] = []
    seen_rows = set()
    processed_units: list[str] = []
    skipped_by_robots = 0
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)

    for unit in units:
        unit_id = str(unit["unit_id"])
        if unit_id in completed_units:
            continue
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        sitemap_url = ap_monthly_sitemap_url(source, unit)
        if not robots_url_allowed(sitemap_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            completed_units.add(unit_id)
            processed_units.append(unit_id)
            skipped_by_robots += 1
            continue
        sitemap_fetch = fetch_url(sitemap_url, config)
        sitemap_meta = write_response(config.raw_dir, source_key=source_key, capability="ap_monthly_sitemap", url=sitemap_url, fetched=sitemap_fetch)
        fetches.append(
            {
                "url": sitemap_url,
                "unit_id": unit_id,
                "ok": bool(sitemap_fetch.get("ok")),
                "status_code": sitemap_fetch.get("status_code", 0),
                "content_type": sitemap_fetch.get("content_type", ""),
                "raw_metadata_path": str(Path(sitemap_meta["body_path"]).with_name("metadata.json")),
            }
        )
        if not sitemap_fetch.get("ok"):
            if int(sitemap_fetch.get("status_code", 0) or 0) == 404:
                completed_units.add(unit_id)
                processed_units.append(unit_id)
                entry_offsets.pop(unit_id, None)
                continue
            break
        entries = [
            entry
            for entry in parse_sitemap_entries(sitemap_fetch.get("bytes", b""))
            if entry.get("loc", "").startswith("https://apnews.com/article/")
        ]
        offset = int(entry_offsets.get(unit_id, 0) or 0)
        while offset < len(entries) and len(fetches) < max_fetches and len(rows) < max_rows:
            entry = entries[offset]
            article_url = entry.get("loc", "")
            if not robots_url_allowed(article_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
                skipped_by_robots += 1
                offset += 1
                continue
            article_fetch = fetch_url(article_url, config)
            article_meta = write_response(config.raw_dir, source_key=source_key, capability="ap_article_meta", url=article_url, fetched=article_fetch)
            parsed_row: dict[str, Any] | None = None
            if article_fetch.get("ok"):
                parsed_row = ap_article_meta_row(
                    source=source,
                    entry=entry,
                    article_payload=article_fetch.get("bytes", b""),
                    captured_at=captured_at,
                    sitemap_url=sitemap_url,
                )
                if parsed_row:
                    if not row_date_within_window(parsed_row, start=start, end=end):
                        parsed_row = None
                    else:
                        key = parsed_row.get("headline_hash") or f"{parsed_row.get('title')}|{parsed_row.get('source_url')}"
                        if key not in seen_rows:
                            seen_rows.add(key)
                            rows.append(parsed_row)
            fetches.append(
                {
                    "url": article_url,
                    "unit_id": unit_id,
                    "entry_offset": offset,
                    "ok": bool(article_fetch.get("ok")),
                    "status_code": article_fetch.get("status_code", 0),
                    "content_type": article_fetch.get("content_type", ""),
                    "raw_metadata_path": str(Path(article_meta["body_path"]).with_name("metadata.json")),
                    "row_count": 1 if parsed_row else 0,
                }
            )
            offset += 1
            sleep_between_source_requests(source, config)
        if offset >= len(entries):
            completed_units.add(unit_id)
            entry_offsets.pop(unit_id, None)
            processed_units.append(unit_id)
        else:
            entry_offsets[unit_id] = offset
        if rows or len(fetches) >= max_fetches:
            break

    backfill_state["completed_units"] = sorted(completed_units)
    backfill_state["entry_offsets"] = entry_offsets
    backfill_state["pending_units"] = max(len(units) - len(completed_units), 0)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if not rows and len(units) and len(completed_units) >= len(units):
        status = "BACKFILL_COMPLETE"
    elif skipped_by_robots and not rows:
        status = "BLOCKED_ROBOTS"
    elif not rows and any(fetch.get("ok") is False and int(fetch.get("status_code", 0) or 0) != 404 for fetch in fetches):
        status = "FAILED_RETRYABLE"
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};processed_units={','.join(processed_units[:5])};"
            f"completed_units={len(completed_units)}/{len(units)};fetches={len(fetches)};"
            f"skipped_by_robots={skipped_by_robots};collector_version={COLLECTOR_VERSION};"
            "ticker_mapping_required=0;historical_backtest_certified=0;archive_provider=ap_monthly_sitemap"
        ),
    )


def collect_cnbc_source_backfill(source: dict[str, Any], config: PublicMarketMacroNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    start, end = backfill_window(config)
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_sitemaps = set(backfill_state.setdefault("completed_sitemap_urls", []))
    entry_offsets = backfill_state.setdefault("entry_offsets", {})
    backfill_state["start_date"] = start.isoformat()
    backfill_state["end_date"] = end.isoformat()

    base_url = str(source.get("base_url") or "https://www.cnbc.com")
    origin = source_origin(base_url)
    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")

    index_url = cnbc_sitemap_index_url(source)
    fetches: list[dict[str, Any]] = [
        {"url": robots_url, "capability": "robots", "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json"))}
    ]
    rows: list[dict[str, Any]] = []
    seen_rows = set()
    processed_units: list[str] = []
    skipped_by_robots = 0
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)

    if not robots_url_allowed(index_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
        raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=[], fetches=fetches, collection_mode="historical_backfill")
        return source_event(
            provider=PROVIDER,
            source_id=f"{source_key}::historical_backfill",
            status="BLOCKED_ROBOTS",
            row_count=0,
            raw_path=raw_path,
            notes=f"source_key={source_key};collector_version={COLLECTOR_VERSION};index_blocked_robots=1",
        )

    index_fetch = fetch_url(index_url, config)
    index_meta = write_response(config.raw_dir, source_key=source_key, capability="cnbc_sitemap_index", url=index_url, fetched=index_fetch)
    fetches.append(
        {
            "url": index_url,
            "ok": bool(index_fetch.get("ok")),
            "status_code": index_fetch.get("status_code", 0),
            "content_type": index_fetch.get("content_type", ""),
            "raw_metadata_path": str(Path(index_meta["body_path"]).with_name("metadata.json")),
        }
    )
    if not index_fetch.get("ok"):
        raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=[], fetches=fetches, collection_mode="historical_backfill")
        return source_event(
            provider=PROVIDER,
            source_id=f"{source_key}::historical_backfill",
            status="FAILED_RETRYABLE",
            row_count=0,
            raw_path=raw_path,
            notes=f"source_key={source_key};collector_version={COLLECTOR_VERSION};index_fetch_failed=1",
        )

    sitemap_urls = [entry["loc"] for entry in parse_sitemap_entries(index_fetch.get("bytes", b"")) if "CNBCsitemapAll" in entry.get("loc", "")]
    sitemap_urls = sorted(dict.fromkeys(sitemap_urls))
    backfill_state["total_units"] = len(sitemap_urls)

    for sitemap_url in sitemap_urls:
        if sitemap_url in completed_sitemaps:
            continue
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        if not robots_url_allowed(sitemap_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            completed_sitemaps.add(sitemap_url)
            skipped_by_robots += 1
            continue
        sitemap_fetch = fetch_url(sitemap_url, config)
        sitemap_meta = write_response(config.raw_dir, source_key=source_key, capability="cnbc_sitemap_urlset", url=sitemap_url, fetched=sitemap_fetch)
        if len(fetches) < max_fetches:
            fetches.append(
                {
                    "url": sitemap_url,
                    "unit_id": sitemap_url,
                    "ok": bool(sitemap_fetch.get("ok")),
                    "status_code": sitemap_fetch.get("status_code", 0),
                    "content_type": sitemap_fetch.get("content_type", ""),
                    "raw_metadata_path": str(Path(sitemap_meta["body_path"]).with_name("metadata.json")),
                }
            )
        if not sitemap_fetch.get("ok"):
            break
        entries = [
            entry
            for entry in parse_sitemap_entries(sitemap_fetch.get("bytes", b""))
            if entry.get("loc", "").startswith("https://www.cnbc.com/")
            and entry.get("loc", "").endswith(".html")
            and "/advertorial/" not in entry.get("loc", "")
            and (cnbc_backfill_entry_date(entry) is not None)
            and start <= cnbc_backfill_entry_date(entry) <= end
        ]
        offset = int(entry_offsets.get(sitemap_url, 0) or 0)
        while offset < len(entries) and len(fetches) < max_fetches and len(rows) < max_rows:
            entry = entries[offset]
            article_url = entry.get("loc", "")
            if not robots_url_allowed(article_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
                skipped_by_robots += 1
                offset += 1
                continue
            article_fetch = fetch_url(article_url, config)
            article_meta = write_response(config.raw_dir, source_key=source_key, capability="cnbc_article_meta", url=article_url, fetched=article_fetch)
            parsed_row: dict[str, Any] | None = None
            if article_fetch.get("ok"):
                parsed_row = cnbc_backfill_row(
                    source=source,
                    entry=entry,
                    article_payload=article_fetch.get("bytes", b""),
                    captured_at=captured_at,
                    sitemap_url=sitemap_url,
                )
                if parsed_row:
                    if not row_date_within_window(parsed_row, start=start, end=end):
                        parsed_row = None
                    else:
                        key = parsed_row.get("headline_hash") or f"{parsed_row.get('title')}|{parsed_row.get('source_url')}"
                        if key not in seen_rows:
                            seen_rows.add(key)
                            rows.append(parsed_row)
            fetches.append(
                {
                    "url": article_url,
                    "unit_id": sitemap_url,
                    "entry_offset": offset,
                    "ok": bool(article_fetch.get("ok")),
                    "status_code": article_fetch.get("status_code", 0),
                    "content_type": article_fetch.get("content_type", ""),
                    "raw_metadata_path": str(Path(article_meta["body_path"]).with_name("metadata.json")),
                    "row_count": 1 if parsed_row else 0,
                }
            )
            offset += 1
            sleep_between_source_requests(source, config)
        if offset >= len(entries):
            completed_sitemaps.add(sitemap_url)
            entry_offsets.pop(sitemap_url, None)
            processed_units.append(sitemap_url)
        else:
            entry_offsets[sitemap_url] = offset
        if rows or len(fetches) >= max_fetches:
            break
        continue

    backfill_state["completed_sitemap_urls"] = sorted(completed_sitemaps)
    backfill_state["completed_units"] = sorted(completed_sitemaps)
    backfill_state["entry_offsets"] = entry_offsets
    backfill_state["pending_units"] = max(int(backfill_state.get("total_units", 0)) - len(completed_sitemaps), 0)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    total_units = int(backfill_state.get("total_units", 0))
    if not rows and total_units and len(completed_sitemaps) >= total_units:
        status = "BACKFILL_COMPLETE"
    elif not rows and any(fetch.get("ok") is False for fetch in fetches):
        status = "FAILED_RETRYABLE"
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};processed_units={len(processed_units)};"
            f"completed_units={len(completed_sitemaps)}/{total_units};fetches={len(fetches)};"
            f"skipped_by_robots={skipped_by_robots};collector_version={COLLECTOR_VERSION};"
            "ticker_mapping_required=0;historical_backtest_certified=0"
        ),
    )


def collect_wikimedia_current_events_backfill(source: dict[str, Any], config: PublicMarketMacroNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    start, end = backfill_window(config)
    units = guardian_backfill_units(start, end)
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_units = set(backfill_state.setdefault("completed_units", []))
    entry_offsets = backfill_state.setdefault("entry_offsets", {})
    backfill_state["start_date"] = start.isoformat()
    backfill_state["end_date"] = end.isoformat()
    backfill_state["total_units"] = len(units)
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    seen_rows = set()
    processed_units: list[str] = []
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)

    origin = "https://en.wikipedia.org"
    robots_url = origin + "/robots.txt"
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")
    fetches.append({"url": robots_url, "capability": "robots", "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json"))})

    for unit in units:
        unit_id = str(unit["unit_id"])
        if unit_id in completed_units:
            continue
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        url = build_wikimedia_url(unit)
        if not robots_url_allowed(url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            completed_units.add(unit_id)
            processed_units.append(unit_id)
            continue
        fetched = fetch_url(url, config)
        raw_meta = write_response(config.raw_dir, source_key=source_key, capability="wikimedia_month", url=url, fetched=fetched)
        parsed: list[dict[str, Any]] = []
        if fetched.get("ok"):
            parsed = parse_wikimedia_current_events_rows(
                fetched.get("bytes", b""),
                source=source,
                source_page_url=str(fetched.get("resolved_url") or url),
                captured_at=captured_at,
            )
            offset = int(entry_offsets.get(unit_id, 0) or 0)
            for row in parsed[offset:]:
                key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                if key in seen_rows:
                    offset += 1
                    continue
                seen_rows.add(key)
                rows.append(row)
                offset += 1
                if len(rows) >= max_rows:
                    break
            if offset >= len(parsed):
                completed_units.add(unit_id)
                entry_offsets.pop(unit_id, None)
                processed_units.append(unit_id)
            else:
                entry_offsets[unit_id] = offset
        record = {
            "url": url,
            "unit_id": unit_id,
            "ok": bool(fetched.get("ok")),
            "status_code": fetched.get("status_code", 0),
            "content_type": fetched.get("content_type", ""),
            "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
            "row_count": len(parsed),
        }
        if not fetched.get("ok"):
            record["error_category"] = fetched.get("error_category", "")
            record["error_message_redacted"] = fetched.get("error_message", "")
        fetches.append(record)
        sleep_between_source_requests(source, config)
        if rows or len(fetches) >= max_fetches:
            break

    backfill_state["completed_units"] = sorted(completed_units)
    backfill_state["entry_offsets"] = entry_offsets
    backfill_state["pending_units"] = max(len(units) - len(completed_units), 0)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if not rows and len(units) and len(completed_units) >= len(units):
        status = "BACKFILL_COMPLETE"
    elif not rows and any(fetch.get("ok") is False for fetch in fetches):
        status = "FAILED_RETRYABLE"
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};processed_units={','.join(processed_units)};"
            f"completed_units={len(completed_units)}/{len(units)};fetches={len(fetches)};"
            f"collector_version={COLLECTOR_VERSION};ticker_mapping_required=0;"
            "historical_backtest_certified=0"
        ),
    )


def collect_common_crawl_market_news_backfill(source: dict[str, Any], config: PublicMarketMacroNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    start, end = backfill_window(config)
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_units = set(backfill_state.setdefault("completed_units", []))
    entry_offsets = backfill_state.setdefault("entry_offsets", {})
    backfill_state["start_date"] = start.isoformat()
    backfill_state["end_date"] = end.isoformat()

    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    seen_rows = set()
    processed_units: list[str] = []
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)
    patterns = common_crawl_url_patterns(source)

    collinfo_url = str(source.get("common_crawl_collections_url") or COMMON_CRAWL_COLLECTIONS_URL)
    collinfo_fetch = fetch_url(collinfo_url, config)
    collinfo_meta = write_response(config.raw_dir, source_key=source_key, capability="common_crawl_collections", url=collinfo_url, fetched=collinfo_fetch)
    fetches.append(
        {
            "url": collinfo_url,
            "capability": "common_crawl_collections",
            "ok": bool(collinfo_fetch.get("ok")),
            "status_code": collinfo_fetch.get("status_code", 0),
            "content_type": collinfo_fetch.get("content_type", ""),
            "raw_metadata_path": str(Path(collinfo_meta["body_path"]).with_name("metadata.json")),
        }
    )
    if not collinfo_fetch.get("ok"):
        raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=[], fetches=fetches, collection_mode="historical_backfill")
        return source_event(
            provider=PROVIDER,
            source_id=f"{source_key}::historical_backfill",
            status="FAILED_RETRYABLE",
            row_count=0,
            raw_path=raw_path,
            notes=f"source_key={source_key};collector_version={COLLECTOR_VERSION};common_crawl_collinfo_failed=1",
        )

    collections = parse_common_crawl_collections(collinfo_fetch.get("bytes", b""), start=start, end=end)
    units = [(collection, pattern, f"{collection['id']}::{pattern}") for collection in collections for pattern in patterns]
    backfill_state["total_units"] = len(units)
    index_limit = min(max(max_rows * 4, max_rows), 200)

    for collection, pattern, unit_id in units:
        if unit_id in completed_units:
            continue
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        index_url = build_common_crawl_index_url(collection, pattern, limit=index_limit)
        index_fetch = fetch_url(index_url, config)
        index_meta = write_response(config.raw_dir, source_key=source_key, capability="common_crawl_index", url=index_url, fetched=index_fetch)
        fetches.append(
            {
                "url": index_url,
                "unit_id": unit_id,
                "collection_id": collection["id"],
                "url_pattern": pattern,
                "ok": bool(index_fetch.get("ok")),
                "status_code": index_fetch.get("status_code", 0),
                "content_type": index_fetch.get("content_type", ""),
                "raw_metadata_path": str(Path(index_meta["body_path"]).with_name("metadata.json")),
            }
        )
        if not index_fetch.get("ok"):
            if int(index_fetch.get("status_code", 0) or 0) == 404:
                completed_units.add(unit_id)
                processed_units.append(unit_id)
                entry_offsets.pop(unit_id, None)
                continue
            break
        records = parse_common_crawl_index_rows(index_fetch.get("bytes", b""))
        offset = int(entry_offsets.get(unit_id, 0) or 0)
        while offset < len(records) and len(fetches) < max_fetches and len(rows) < max_rows:
            record = records[offset]
            warc_fetch = fetch_common_crawl_warc_record(record, config)
            warc_url = common_crawl_warc_url(record)
            warc_meta = write_response(config.raw_dir, source_key=source_key, capability="common_crawl_warc_record", url=warc_url, fetched=warc_fetch)
            parsed_row: dict[str, Any] | None = None
            if warc_fetch.get("ok"):
                parsed_row = common_crawl_archive_row(
                    source=source,
                    record=record,
                    warc_payload=warc_fetch.get("bytes", b""),
                    captured_at=captured_at,
                    index_url=index_url,
                    collection_id=str(collection["id"]),
                    url_pattern=pattern,
                )
                if parsed_row:
                    if not row_date_within_window(parsed_row, start=start, end=end):
                        parsed_row = None
                    else:
                        key = parsed_row.get("headline_hash") or f"{parsed_row.get('title')}|{parsed_row.get('source_url')}"
                        if key not in seen_rows:
                            seen_rows.add(key)
                            rows.append(parsed_row)
            fetches.append(
                {
                    "url": warc_url,
                    "unit_id": unit_id,
                    "entry_offset": offset,
                    "collection_id": collection["id"],
                    "url_pattern": pattern,
                    "source_url": record.get("url", ""),
                    "ok": bool(warc_fetch.get("ok")),
                    "status_code": warc_fetch.get("status_code", 0),
                    "content_type": warc_fetch.get("content_type", ""),
                    "raw_metadata_path": str(Path(warc_meta["body_path"]).with_name("metadata.json")),
                    "row_count": 1 if parsed_row else 0,
                }
            )
            offset += 1
            sleep_between_source_requests(source, config)
        if offset >= len(records):
            completed_units.add(unit_id)
            processed_units.append(unit_id)
            entry_offsets.pop(unit_id, None)
        else:
            entry_offsets[unit_id] = offset
        if rows or len(fetches) >= max_fetches:
            break

    backfill_state["completed_units"] = sorted(completed_units)
    backfill_state["entry_offsets"] = entry_offsets
    backfill_state["pending_units"] = max(len(units) - len(completed_units), 0)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if not rows and len(units) and len(completed_units) >= len(units):
        status = "BACKFILL_COMPLETE"
    elif not rows and any(fetch.get("ok") is False and int(fetch.get("status_code", 0) or 0) != 404 for fetch in fetches):
        status = "FAILED_RETRYABLE"
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};processed_units={','.join(processed_units[:5])};"
            f"completed_units={len(completed_units)}/{len(units)};fetches={len(fetches)};"
            f"collector_version={COLLECTOR_VERSION};ticker_mapping_required=0;"
            "historical_backtest_certified=0;archive_provider=common_crawl"
        ),
    )


def collect_wordpress_rest_backfill(source: dict[str, Any], config: PublicMarketMacroNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    start, end = backfill_window(config)
    units = guardian_backfill_units(start, end)
    page_size = int(source.get("wordpress_page_size") or min(max(config.guardian_page_size, 1), 100))
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_units = set(backfill_state.setdefault("completed_units", []))
    page_offsets = backfill_state.setdefault("page_offsets", {})
    backfill_state["start_date"] = start.isoformat()
    backfill_state["end_date"] = end.isoformat()
    backfill_state["total_units"] = len(units)
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    processed_units: list[str] = []
    seen_rows = set()
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)

    for unit in units:
        unit_id = str(unit["unit_id"])
        if unit_id in completed_units:
            continue
        page = int(page_offsets.get(unit_id, 1) or 1)
        while len(fetches) < max_fetches and len(rows) < max_rows:
            url = build_wordpress_posts_url(source, unit, page=page, page_size=page_size)
            fetched = fetch_url(url, config)
            raw_meta = write_response(config.raw_dir, source_key=source_key, capability="wordpress_posts_backfill", url=url, fetched=fetched)
            parsed: list[dict[str, Any]] = []
            api_meta: dict[str, Any] = {}
            if fetched.get("ok"):
                parsed, api_meta = parse_wordpress_rest_rows(
                    fetched.get("bytes", b""),
                    source=source,
                    source_page_url=str(fetched.get("resolved_url") or url),
                    captured_at=captured_at,
                )
                for row in parsed:
                    if not row_date_within_window(row, start=start, end=end):
                        continue
                    key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                    if key in seen_rows:
                        continue
                    seen_rows.add(key)
                    rows.append(row)
                    if len(rows) >= max_rows:
                        break
            headers = fetched.get("headers", {}) if isinstance(fetched.get("headers"), dict) else {}
            total_pages_text = str(headers.get("X-WP-TotalPages") or headers.get("x-wp-totalpages") or "")
            try:
                total_pages = int(total_pages_text)
            except ValueError:
                total_pages = page if int(api_meta.get("item_count", 0) or 0) < page_size else page + 1
            record = {
                "url": url,
                "unit_id": unit_id,
                "page": page,
                "ok": bool(fetched.get("ok")),
                "status_code": fetched.get("status_code", 0),
                "content_type": fetched.get("content_type", ""),
                "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
                "row_count": len(parsed),
                "api_metadata": {**api_meta, "total_pages": total_pages_text},
            }
            if not fetched.get("ok"):
                record["error_category"] = fetched.get("error_category", "")
                record["error_message_redacted"] = fetched.get("error_message", "")
            fetches.append(record)
            if not fetched.get("ok"):
                break
            if page >= total_pages:
                completed_units.add(unit_id)
                page_offsets.pop(unit_id, None)
                processed_units.append(unit_id)
                break
            page_offsets[unit_id] = page + 1
            page += 1
            sleep_between_source_requests(source, config)
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break

    backfill_state["completed_units"] = sorted(completed_units)
    backfill_state["page_offsets"] = page_offsets
    backfill_state["pending_units"] = max(len(units) - len(completed_units), 0)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    total_units = len(units)
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if not rows and total_units and len(completed_units) >= total_units:
        status = "BACKFILL_COMPLETE"
    elif not rows and any(fetch.get("error_category") for fetch in fetches):
        status, _category = classify_news_error(Exception("wordpress backfill fetch failed"))
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};processed_units={','.join(processed_units[:5])};"
            f"completed_units={len(completed_units)}/{total_units};fetches={len(fetches)};"
            f"collector_version={COLLECTOR_VERSION};ticker_mapping_required=0;historical_backtest_certified=1;"
            "archive_provider=wordpress_rest"
        ),
    )


def collect_monthly_sitemap_article_meta_backfill(source: dict[str, Any], config: PublicMarketMacroNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    start, end = source_backfill_window(source, config)
    units = guardian_backfill_units(start, end)
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_units = set(backfill_state.setdefault("completed_units", []))
    entry_offsets = backfill_state.setdefault("entry_offsets", {})
    backfill_state["start_date"] = start.isoformat()
    backfill_state["end_date"] = end.isoformat()
    backfill_state["total_units"] = len(units)

    base_url = str(source.get("base_url") or "")
    origin = source_origin(base_url)
    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")

    fetches: list[dict[str, Any]] = [
        {"url": robots_url, "capability": "robots", "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json"))}
    ]
    rows: list[dict[str, Any]] = []
    seen_rows = set()
    processed_units: list[str] = []
    skipped_by_robots = 0
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)
    url_prefix = normalize_text(str(source.get("monthly_sitemap_article_url_prefix") or base_url))

    sleep_between_source_requests(source, config)

    for unit in units:
        unit_id = str(unit["unit_id"])
        if unit_id in completed_units:
            continue
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        sitemap_url = monthly_sitemap_url(source, unit)
        if not robots_url_allowed(sitemap_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            completed_units.add(unit_id)
            processed_units.append(unit_id)
            skipped_by_robots += 1
            continue
        sitemap_fetch = fetch_url(sitemap_url, config)
        sitemap_meta = write_response(config.raw_dir, source_key=source_key, capability="monthly_sitemap", url=sitemap_url, fetched=sitemap_fetch)
        fetches.append(
            {
                "url": sitemap_url,
                "unit_id": unit_id,
                "ok": bool(sitemap_fetch.get("ok")),
                "status_code": sitemap_fetch.get("status_code", 0),
                "content_type": sitemap_fetch.get("content_type", ""),
                "raw_metadata_path": str(Path(sitemap_meta["body_path"]).with_name("metadata.json")),
            }
        )
        if not sitemap_fetch.get("ok"):
            if int(sitemap_fetch.get("status_code", 0) or 0) == 404:
                completed_units.add(unit_id)
                processed_units.append(unit_id)
                entry_offsets.pop(unit_id, None)
                continue
            break
        sleep_between_source_requests(source, config)
        entries = [
            entry
            for entry in parse_sitemap_entries(sitemap_fetch.get("bytes", b""))
            if not url_prefix or entry.get("loc", "").startswith(url_prefix)
        ]
        offset = int(entry_offsets.get(unit_id, 0) or 0)
        while offset < len(entries) and len(fetches) < max_fetches and len(rows) < max_rows:
            entry = entries[offset]
            article_url = entry.get("loc", "")
            if not robots_url_allowed(article_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
                skipped_by_robots += 1
                offset += 1
                continue
            article_fetch = fetch_url(article_url, config)
            article_meta = write_response(config.raw_dir, source_key=source_key, capability="monthly_sitemap_article_meta", url=article_url, fetched=article_fetch)
            parsed_row: dict[str, Any] | None = None
            if article_fetch.get("ok"):
                parsed_row = monthly_sitemap_article_meta_row(
                    source=source,
                    entry=entry,
                    article_payload=article_fetch.get("bytes", b""),
                    captured_at=captured_at,
                    sitemap_url=sitemap_url,
                )
                if parsed_row:
                    if not row_date_within_window(parsed_row, start=start, end=end):
                        parsed_row = None
                    else:
                        key = parsed_row.get("headline_hash") or f"{parsed_row.get('title')}|{parsed_row.get('source_url')}"
                        if key not in seen_rows:
                            seen_rows.add(key)
                            rows.append(parsed_row)
            fetches.append(
                {
                    "url": article_url,
                    "unit_id": unit_id,
                    "entry_offset": offset,
                    "ok": bool(article_fetch.get("ok")),
                    "status_code": article_fetch.get("status_code", 0),
                    "content_type": article_fetch.get("content_type", ""),
                    "raw_metadata_path": str(Path(article_meta["body_path"]).with_name("metadata.json")),
                    "row_count": 1 if parsed_row else 0,
                }
            )
            offset += 1
            sleep_between_source_requests(source, config)
        if offset >= len(entries):
            completed_units.add(unit_id)
            entry_offsets.pop(unit_id, None)
            processed_units.append(unit_id)
        else:
            entry_offsets[unit_id] = offset
        if rows or len(fetches) >= max_fetches:
            break

    backfill_state["completed_units"] = sorted(completed_units)
    backfill_state["entry_offsets"] = entry_offsets
    backfill_state["pending_units"] = max(len(units) - len(completed_units), 0)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    total_units = len(units)
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if not rows and total_units and len(completed_units) >= total_units:
        status = "BACKFILL_COMPLETE"
    elif skipped_by_robots and not rows:
        status = "BLOCKED_ROBOTS"
    elif not rows and any(fetch.get("ok") is False and int(fetch.get("status_code", 0) or 0) != 404 for fetch in fetches):
        status = "FAILED_RETRYABLE"
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};processed_units={','.join(processed_units[:5])};"
            f"completed_units={len(completed_units)}/{total_units};fetches={len(fetches)};"
            f"skipped_by_robots={skipped_by_robots};collector_version={COLLECTOR_VERSION};"
            "ticker_mapping_required=0;historical_backtest_certified=0;archive_provider=monthly_sitemap_article_meta"
        ),
    )


def collect_source_backfill(source: dict[str, Any], config: PublicMarketMacroNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    if source_key == "ap_news_monthly_sitemap":
        return collect_ap_monthly_sitemap_backfill(source, config, state)
    if source_key == "cnbc_public_rss":
        return collect_cnbc_source_backfill(source, config, state)
    if source_key == "wikimedia_current_events":
        return collect_wikimedia_current_events_backfill(source, config, state)
    if source_key == "common_crawl_market_news_archive":
        return collect_common_crawl_market_news_backfill(source, config, state)
    if str(source.get("historical_backfill_mode")) == "wordpress_rest_posts":
        return collect_wordpress_rest_backfill(source, config, state)
    if str(source.get("historical_backfill_mode")) == "monthly_sitemap_article_meta":
        return collect_monthly_sitemap_article_meta_backfill(source, config, state)
    if source_key != "guardian_open_platform":
        raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=[], fetches=[], collection_mode="historical_backfill")
        return source_event(
            provider=PROVIDER,
            source_id=f"{source_key}::historical_backfill",
            status="BACKFILL_UNSUPPORTED",
            row_count=0,
            raw_path=raw_path,
            notes=f"source_key={source_key};collector_version={COLLECTOR_VERSION};unsupported_backfill=1",
        )
    start, end = backfill_window(config)
    units = guardian_backfill_units(start, end)
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_units = set(backfill_state.setdefault("completed_units", []))
    page_offsets = backfill_state.setdefault("page_offsets", {})
    backfill_state["start_date"] = start.isoformat()
    backfill_state["end_date"] = end.isoformat()
    backfill_state["total_units"] = len(units)
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    processed_units: list[str] = []
    seen_rows = set()
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)

    for unit in units:
        unit_id = str(unit["unit_id"])
        if unit_id in completed_units:
            continue
        page = int(page_offsets.get(unit_id, 1) or 1)
        while len(fetches) < max_fetches and len(rows) < max_rows:
            url = build_guardian_url(source, unit, page=page, page_size=config.guardian_page_size)
            fetched = fetch_url(url, config)
            raw_meta = write_response(config.raw_dir, source_key=source_key, capability="guardian_api_backfill", url=url, fetched=fetched)
            parsed: list[dict[str, Any]] = []
            api_meta: dict[str, Any] = {}
            if fetched.get("ok"):
                parsed, api_meta = parse_guardian_api_rows(
                    fetched.get("bytes", b""),
                    source=source,
                    source_page_url=str(fetched.get("resolved_url") or url),
                    captured_at=captured_at,
                )
                for row in parsed:
                    row["usable_for_historical_backtest_flag"] = 1
                    key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                    if key in seen_rows:
                        continue
                    seen_rows.add(key)
                    rows.append(row)
                    if len(rows) >= max_rows:
                        break
            record = {
                "url": url,
                "unit_id": unit_id,
                "page": page,
                "ok": bool(fetched.get("ok")),
                "status_code": fetched.get("status_code", 0),
                "content_type": fetched.get("content_type", ""),
                "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
                "row_count": len(parsed),
                "api_metadata": api_meta,
            }
            if not fetched.get("ok"):
                record["error_category"] = fetched.get("error_category", "")
                record["error_message_redacted"] = fetched.get("error_message", "")
            fetches.append(record)
            total_pages = int(api_meta.get("pages") or page)
            if page >= total_pages:
                completed_units.add(unit_id)
                page_offsets.pop(unit_id, None)
                processed_units.append(unit_id)
                break
            page_offsets[unit_id] = page + 1
            break
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break

    backfill_state["completed_units"] = sorted(completed_units)
    backfill_state["page_offsets"] = page_offsets
    backfill_state["pending_units"] = max(len(units) - len(completed_units), 0)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    total_units = len(units)
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if not rows and total_units and len(completed_units) >= total_units:
        status = "BACKFILL_COMPLETE"
    elif not rows and any(fetch.get("error_category") for fetch in fetches):
        status, _category = classify_news_error(Exception("guardian backfill fetch failed"))
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};processed_units={','.join(processed_units)};"
            f"completed_units={len(completed_units)}/{total_units};fetches={len(fetches)};"
            f"collector_version={COLLECTOR_VERSION};ticker_mapping_required=0"
        ),
    )


def update_state_for_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    source_key = str(event.get("source_id", "unknown")).split("::", 1)[0]
    status = str(event.get("status", ""))
    state["processed_events"] = int(state.get("processed_events", 0)) + 1
    if status == "EXPORTED":
        state["exported_events"] = int(state.get("exported_events", 0)) + 1
    elif status in {"EMPTY_PROVIDER_RESPONSE", "BACKFILL_COMPLETE", "BACKFILL_UNSUPPORTED"}:
        state["empty_events"] = int(state.get("empty_events", 0)) + 1
    elif status == "BLOCKED_ROBOTS":
        state["blocked_events"] = int(state.get("blocked_events", 0)) + 1
    else:
        state["failed_events"] = int(state.get("failed_events", 0)) + 1
    cycles = state.setdefault("source_cycles", {})
    payload = cycles.setdefault(source_key, {"events": 0, "rows": 0, "last_status": ""})
    payload["events"] = int(payload.get("events", 0)) + 1
    payload["rows"] = int(payload.get("rows", 0)) + int(event.get("row_count", 0) or 0)
    payload["last_status"] = status
    payload["last_updated_at"] = event.get("updated_at", now_z())


def run_collector(config: PublicMarketMacroNewsConfig, *, smoke: bool = False) -> dict[str, Any]:
    sources = selected_sources(config)
    build_plan(config, mode="market_macro_watch")
    state = load_state(config.state_path)
    processed_this_run = 0
    last_status = "STARTED"
    cycle = 0
    log_line(config.log_path, f"[L0_PUBLIC_MARKET_MACRO_NEWS_START] smoke={int(smoke)} sources={','.join(config.sources)}")
    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        for source in sources:
            event = collect_source(source, config)
            append_event(config.event_path, event)
            update_state_for_event(state, event)
            processed_this_run += 1
            last_status = str(event.get("status", ""))
            save_state(config.state_path, state)
            write_progress(
                config.progress_path,
                state,
                {
                    "provider": PROVIDER,
                    "mode": "market_macro_watch",
                    "last_status": last_status,
                    "processed_this_run": processed_this_run,
                    "source_count": len(sources),
                    "plan_path": str(config.plan_path),
                },
            )
        cycle += 1
        if smoke or (config.max_cycles and cycle >= config.max_cycles):
            break
        time.sleep(max(int(config.cycle_sleep_seconds), 1))
    result = {
        "status": last_status,
        "processed_this_run": processed_this_run,
        "state_path": str(config.state_path),
        "event_path": str(config.event_path),
        "progress_path": str(config.progress_path),
        "plan_path": str(config.plan_path),
        "permissions_closed": True,
        "mode": "market_macro_watch",
    }
    write_progress(config.progress_path, state, result)
    log_line(config.log_path, f"[L0_PUBLIC_MARKET_MACRO_NEWS_EXIT] {json.dumps(result, sort_keys=True)}")
    return result


def run_backfill(config: PublicMarketMacroNewsConfig, *, smoke: bool = False) -> dict[str, Any]:
    sources = selected_sources(config)
    build_plan(config, mode="historical_backfill")
    state = load_state(config.state_path)
    processed_this_run = 0
    last_status = "STARTED"
    cycle = 0
    log_line(config.log_path, f"[L0_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_START] smoke={int(smoke)} sources={','.join(config.sources)}")
    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        active_sources = 0
        for source in sources:
            event = collect_source_backfill(source, config, state)
            append_event(config.event_path, event)
            update_state_for_event(state, event)
            processed_this_run += 1
            last_status = str(event.get("status", ""))
            if last_status not in {"BACKFILL_COMPLETE", "BACKFILL_UNSUPPORTED"}:
                active_sources += 1
            save_state(config.state_path, state)
            write_progress(
                config.progress_path,
                state,
                {
                    "provider": PROVIDER,
                    "mode": "historical_backfill",
                    "last_status": last_status,
                    "processed_this_run": processed_this_run,
                    "source_count": len(sources),
                    "plan_path": str(config.plan_path),
                },
            )
        cycle += 1
        if smoke or active_sources == 0 or (config.max_cycles and cycle >= config.max_cycles):
            break
        time.sleep(max(int(config.cycle_sleep_seconds), 1))
    result = {
        "status": last_status,
        "processed_this_run": processed_this_run,
        "state_path": str(config.state_path),
        "event_path": str(config.event_path),
        "progress_path": str(config.progress_path),
        "plan_path": str(config.plan_path),
        "permissions_closed": True,
        "mode": "historical_backfill",
    }
    write_progress(config.progress_path, state, result)
    log_line(config.log_path, f"[L0_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_EXIT] {json.dumps(result, sort_keys=True)}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect free public market/macro headline news from RSS/API routes.")
    parser.add_argument("--mode", choices=["smoke", "background", "backfill"], default="smoke")
    parser.add_argument("--sources", nargs="+", default=list(DEFAULT_LIVE_SOURCES))
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--max-items-per-source", type=int, default=50)
    parser.add_argument("--max-fetches-per-source", type=int, default=6)
    parser.add_argument("--cycle-sleep-seconds", type=int, default=1800)
    parser.add_argument("--request-sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-cycles", type=int, default=0)
    parser.add_argument("--max-bytes", type=int, default=3_000_000)
    parser.add_argument("--backfill-start-date", default=DEFAULT_BACKFILL_START_DATE)
    parser.add_argument("--backfill-end-date", default="")
    parser.add_argument("--guardian-page-size", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = PublicMarketMacroNewsConfig(
        registry_path=args.registry_path,
        raw_dir=args.raw_dir,
        state_path=args.state_path,
        event_path=args.event_path,
        progress_path=args.progress_path,
        plan_path=args.plan_path,
        stop_path=args.stop_path,
        log_path=args.log_path,
        sources=tuple(args.sources),
        max_items_per_source=args.max_items_per_source,
        max_fetches_per_source=args.max_fetches_per_source,
        cycle_sleep_seconds=args.cycle_sleep_seconds,
        request_sleep_seconds=args.request_sleep_seconds,
        max_bytes=args.max_bytes,
        max_cycles=args.max_cycles,
        backfill_start_date=args.backfill_start_date,
        backfill_end_date=args.backfill_end_date,
        guardian_page_size=args.guardian_page_size,
    )
    result = run_backfill(config, smoke=args.mode == "smoke") if args.mode == "backfill" else run_collector(config, smoke=args.mode == "smoke")
    print(
        "[L0_PUBLIC_MARKET_MACRO_NEWS] "
        f"mode={args.mode} sources={','.join(args.sources)} status={result['status']} "
        f"processed_this_run={result['processed_this_run']} event_path={result['event_path']} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
