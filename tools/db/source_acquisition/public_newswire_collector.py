from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import sys
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
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.db.source_acquisition.news_background_collector import classify_news_error, source_event, write_progress
from tools.db.source_acquisition.secret_redaction import redact_text
from tools.db.source_acquisition.source_capability_probe import (
    build_robot_parser,
    load_registry,
    robots_posture,
    robots_url_allowed,
)


PROVIDER = "public_newswire_feeds"
SCHEMA_VERSION = 1
COLLECTOR_VERSION = "public_newswire_collector.v0.1.6"
ENTITY_MAPPING_VERSION = "public_newswire_entity_mapper.v0.1.6"
CANDIDATE_HINT_VERSION = "public_newswire_candidate_hints.v0.1.0"
NEWSWIRE_RECALL_VERSION = "public_newswire_recall_overlay.v0.1.0"
DEFAULT_REGISTRY_PATH = Path("configs/source_registry/l0_public_news_capability_sources.json")
DEFAULT_UNIVERSE_PATH = Path("data/raw/alpaca_active_us_equity_universe.csv")
DEFAULT_RAW_DIR = Path("data/raw/l0_public_newswire")
DEFAULT_ARTIFACT_DIR = Path("data/artifacts/l0_public_newswire")
DEFAULT_STATE_PATH = DEFAULT_ARTIFACT_DIR / "collector_state.json"
DEFAULT_EVENT_PATH = DEFAULT_ARTIFACT_DIR / "collector_events.jsonl"
DEFAULT_PROGRESS_PATH = DEFAULT_ARTIFACT_DIR / "collector_progress.json"
DEFAULT_PLAN_PATH = DEFAULT_ARTIFACT_DIR / "collection_plan.json"
DEFAULT_STOP_PATH = DEFAULT_ARTIFACT_DIR / "STOP"
DEFAULT_LOG_PATH = Path("logs/l0_public_newswire_collector.log")
DEFAULT_SOURCES = ("prnewswire", "globenewswire", "businesswire")
DEFAULT_USER_AGENT = "Codex-L0-PublicNewswire/1.0 contact=operator"
DEFAULT_BACKFILL_START_DATE = "2016-01-01"
MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


@dataclass(frozen=True)
class PublicNewswireConfig:
    registry_path: Path = DEFAULT_REGISTRY_PATH
    universe_path: Path = DEFAULT_UNIVERSE_PATH
    raw_dir: Path = DEFAULT_RAW_DIR
    state_path: Path = DEFAULT_STATE_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    plan_path: Path = DEFAULT_PLAN_PATH
    stop_path: Path = DEFAULT_STOP_PATH
    log_path: Path = DEFAULT_LOG_PATH
    sources: tuple[str, ...] = DEFAULT_SOURCES
    max_items_per_source: int = 50
    max_fetches_per_source: int = 12
    cycle_sleep_seconds: int = 1800
    request_sleep_seconds: float = 1.0
    timeout_seconds: int = 45
    max_bytes: int = 3_000_000
    max_cycles: int = 0
    backfill_start_date: str = DEFAULT_BACKFILL_START_DATE
    backfill_end_date: str = ""
    fetch_missing_title_pages: bool = True
    prnewswire_archive_scope: str = "all"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._anchor: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "a":
            self._anchor = {"href": values.get("href", ""), "text": ""}
        elif tag.lower() == "link":
            href = values.get("href", "")
            if href:
                self.links.append(
                    {
                        "href": href,
                        "text": "",
                        "rel": values.get("rel", ""),
                        "type": values.get("type", ""),
                        "tag": "link",
                    }
                )

    def handle_data(self, data: str) -> None:
        if self._anchor is not None:
            self._anchor["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._anchor is not None:
            self._anchor["text"] = normalize_text(self._anchor.get("text", ""))
            self._anchor["tag"] = "a"
            self.links.append(self._anchor)
            self._anchor = None


class ArticleMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.title = ""
        self.h1 = ""
        self._in_title = False
        self._in_h1 = False

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
        elif lower == "h1":
            self._in_h1 = True

    def handle_data(self, data: str) -> None:
        text = normalize_text(data)
        if not text:
            return
        if self._in_title:
            self.title = normalize_text(f"{self.title} {text}")
        if self._in_h1:
            self.h1 = normalize_text(f"{self.h1} {text}")

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "title":
            self._in_title = False
        elif lower == "h1":
            self._in_h1 = False


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def user_agent() -> str:
    return os.environ.get("L0_NEWS_USER_AGENT") or os.environ.get("SEC_USER_AGENT") or DEFAULT_USER_AGENT


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_entity_text(value: str) -> str:
    text = str(value or "").lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return normalize_text(text)


@dataclass(frozen=True)
class UniverseEntity:
    symbol: str
    name: str
    exchange: str


@dataclass(frozen=True)
class EntityMapper:
    entities_by_symbol: dict[str, UniverseEntity]
    alias_index: dict[str, UniverseEntity]
    ambiguous_aliases: frozenset[str]


LEGAL_SUFFIXES = {
    "ag",
    "bv",
    "co",
    "company",
    "corp",
    "corporation",
    "gmbh",
    "inc",
    "incorporated",
    "limited",
    "llc",
    "lp",
    "ltd",
    "nv",
    "plc",
    "sa",
    "se",
}
SHARE_DESCRIPTOR_PATTERNS = (
    r"\bamerican depositary shares?\b.*$",
    r"\bamerican depositary receipts?\b.*$",
    r"\bordinary shares?\b.*$",
    r"\bcommon shares?\b.*$",
    r"\bcommon stock\b.*$",
    r"\bclass [a-z0-9]+\b.*$",
    r"\badr\b.*$",
)
BLOCKED_ALIASES = {
    "a",
    "all",
    "are",
    "at",
    "be",
    "by",
    "can",
    "go",
    "it",
    "life",
    "amex",
    "arca",
    "bats",
    "cboe",
    "nasdaq",
    "nyse",
    "new",
    "now",
    "on",
    "one",
    "or",
    "so",
    "the",
    "to",
    "us",
    "we",
}
EXCHANGE_TAG_RE = re.compile(
    r"\((?P<exchange>NASDAQ|NYSE(?:\s+AMERICAN)?|NYSEAMERICAN|AMEX|ARCA|BATS|CBOE|OTC(?:QB|QX)?)\s*[:：]\s*(?P<symbols>[^)]+)\)",
    re.IGNORECASE,
)


EXCHANGE_TAG_RE = re.compile(
    r"\((?P<exchange>NASDAQ|NYSE(?:\s+AMERICAN)?|NYSEAMERICAN|AMEX|ARCA|BATS|CBOE|OTC(?:QB|QX)?)\s*:\s*(?P<symbols>[^)]+)\)",
    re.IGNORECASE,
)

NEWSWIRE_CONTEXT_TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("monetary_policy", ("federal reserve", "fomc", "interest rate", "rate cut", "rate hike", "central bank", "riksbank", "reversed auctions", "bond auction")),
    ("inflation", ("inflation", "cpi", "ppi", "price index", "consumer prices")),
    ("labor_market", ("employment", "unemployment", "payroll", "wage growth", "labor market")),
    ("fiscal_policy", ("treasury", "fiscal", "budget", "tax policy", "government spending")),
    ("regulation", ("regulation", "regulatory", "final rule", "proposed rule", "enforcement", "compliance", "rule of law", "independent judiciary", "surface mining", "reclamation act", "task force")),
    ("geopolitics", ("sanction", "tariff", "trade policy", "export control", "war", "geopolitical", "foreign investment", "economic development")),
    (
        "market_structure",
        (
            "market structure",
            "clearing",
            "settlement",
            "trading hours",
            "exchange notice",
            "admission to trading",
            "listing of covered warrants",
            "covered warrants",
            "repo matching",
        ),
    ),
    (
        "capital_markets",
        (
            "ipo",
            "initial public offering",
            "public company",
            "public companies",
            "series a",
            "funding round",
            "global 2000",
            "global insurers",
            "asset management",
            "securities",
            "share buyback",
            "buyback program",
            "bonds initiated",
            "covered warrants",
            "repo matching service",
            "admission to trading",
            "conference call details",
            "earnings report",
            "full year results",
            "quarter results",
            "q4 results",
            "2015 results",
            "ebit",
            "sales record",
        ),
    ),
    (
        "corporate_results",
        (
            "earnings report",
            "conference call details",
            "full year results",
            "quarter results",
            "q4 results",
            "results and webcast",
            "publishes 2015 results",
            "upward adjustment",
            "ebit",
            "sales record",
            "share buyback",
        ),
    ),
    (
        "ai_infrastructure",
        (
            "ai",
            "ia",
            "ki",
            "artificial intelligence",
            " ai ",
            "ai-driven",
            "ai-led",
            "ai-powered",
            "ai cloud",
            "ai security",
            "ai transforms commerce",
            "ai reshapes commerce",
            "agentic ai",
            "automation",
            "automate",
            "digital engineering",
            "embodied ai",
            "generative ai",
            "gpu",
            "gpu network",
            "data center",
            "cloud operators",
            "computer vision",
            "image to video",
            "speech analytics",
            "voice security",
            "robot",
            "robotics",
        ),
    ),
    ("cybersecurity", ("cybersecurity", "cyber security", "ransomware", "zero trust", "data security", "data breach", "voice security")),
    ("healthcare_innovation", ("fda", "clinical trial", "medical device", "surgical", "health assessment", "brain implant", "mental health platform", "medical insight", "skilled nursing", "cell block", "cytopath")),
    (
        "energy_transition",
        (
            "renewable energy",
            "solar",
            "intersolar",
            "wind power",
            "battery",
            "battery storage",
            "energy storage",
            "electric vehicle",
            "electric power",
            "ev buyer",
            "ev charging",
            "clean energy",
            "new energy",
            "new energies",
            "power project",
            "sustainable energy",
            "low carbon",
            "low emissions",
            "co2",
        ),
    ),
    ("mobility_transport", ("urban mobility", "micromobility", "eurobike", "smart vehicle", "public transportation")),
    ("space_satellite", ("spacex ipo", "space economy", "starlink", "direct-to-phone", "satellite", "moon")),
    (
        "defense_drones",
        (
            "drone",
            "defense",
            "defence",
            "defence technology",
            "defense technology",
            "kill vehicle",
            "missile",
            "developmental flight test",
            "raytheon",
        ),
    ),
    (
        "infrastructure_construction",
        (
            "construction technology",
            "construction technology trends",
            "emergency power projects",
            "agri and emergency power",
            "infrastructure",
            "power projects",
        ),
    ),
    ("crypto_digital_assets", ("crypto", "bitcoin", "ethereum", "digital asset", "stablecoin", "blockchain", "blockchain technology", "defi", "dogecoin", "meme coin", "seamless crypto payments", "usdt", "bnb", "xrp", "binance listing")),
    ("consumer_trends", ("consumer behavior", "consumer spending", "social platforms", "social media", "reshapes commerce", "ai transforms commerce", "ai reshapes commerce", "western consumers", "social commerce")),
    ("industry_market_report", ("market size", "market to reach", "market to hit", "market is projected", "market projected", "industry forecast", "industry retail sales", "retail sales", "sales forecast", "forecast period", "cagr", "sns insider", "rising demand", "expanding production")),
    ("telecom_infrastructure", ("telecom", "telecommunications", "5g", "mwc shanghai", "gsma", "network infrastructure")),
    ("food_supply_chain", ("food industry", "food supply", "foodtruth", "agriculture supply", "agri")),
    ("economic_development", ("economic development", "foreign direct investment", "invest in", "landmark investment campaign")),
)
NEWSWIRE_CONTEXT_EXCLUSION_RE = re.compile(
    r"\b(class action|lawsuit|shareholder alert|investors have opportunity|lead plaintiff|securities fraud|investigation alert|"
    r"reminds investors|deadline alert|recover losses|law firm|personal injury attorney|bilingual legal services|hellonation|"
    r"lawyers urge|prime day deal|lawn mower|realtors|testosterone booster|supplements|gummies for weight loss|"
    r"pool style options|yard care|gold ira|portable cooling products|x games)\b",
    re.IGNORECASE,
)

NEWSWIRE_RECALL_TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("earnings_results", ("earnings", "financial results", "quarter results", "full year results", "annual results", "reports fourth quarter", "reports results", "revenue", "guidance")),
    ("corporate_results", ("earnings report", "conference call details", "quarter results", "full year results", "financial results")),
    ("corporate_actions", ("liquidation", "dividend", "spin-off", "spinoff", "reverse split", "stock split", "strategic review", "restructuring")),
    ("capital_markets", ("private placement", "public offering", "registered direct", "at-the-market", "atm offering", "financing", "credit facility", "debt offering", "ipo")),
    ("listing_compliance", ("nasdaq notice", "nyse notice", "delisting", "listing compliance", "continued listing", "minimum bid", "exchange notice")),
    ("clinical_regulatory", ("clinical", "phase 1", "phase 2", "phase 3", "fda", "pdufa", "interim data", "trial data", "regulatory approval")),
    ("healthcare_innovation", ("clinical", "phase 1", "phase 2", "phase 3", "fda", "medical device", "trial data")),
    ("ma_partnerships_contracts", ("acquisition", "merger", "definitive agreement", "partnership", "contract", "contract award", "joint venture", "collaboration")),
    ("industry_market_report", ("industry forecast", "industry retail sales", "retail sales", "market forecast", "market report", "market size", "cagr", "forecast")),
    ("macro_policy_geopolitics", ("tariff", "sanction", "export control", "trade policy", "geopolitical", "election", "government", "federal reserve", "central bank")),
    ("ai_semis_datacenter", ("ai", "artificial intelligence", "semiconductor", "semis", "gpu", "data center", "cloud infrastructure")),
    ("energy_power_grid", ("power grid", "electric power", "solar", "battery", "renewable", "oil production", "natural gas", "lng")),
    ("defense_geopolitics", ("defense", "defence", "missile", "drone", "aerospace", "military", "national security")),
    ("crypto_digital_assets", ("crypto", "bitcoin", "ethereum", "digital asset", "stablecoin", "blockchain")),
)
NEWSWIRE_ENTITY_REVIEW_TOPICS = frozenset(
    {
        "earnings_results",
        "corporate_results",
        "corporate_actions",
        "capital_markets",
        "listing_compliance",
        "clinical_regulatory",
        "healthcare_innovation",
        "ma_partnerships_contracts",
        "industry_market_report",
    }
)

NEWSWIRE_ENTITY_REVIEW_ACTION_RE = re.compile(
    r"^[A-Z0-9][A-Za-z0-9&'.,:/() -]{1,120}?\b("
    r"announces|reports|forecasts|prices|launches|receives|completes|files|appoints|"
    r"acquires|merges|partners|secures|wins|provides|sets|declares|enters|plans|updates|"
    r"publishes|presents|achieves|expands|closes|commences|terminates|releases"
    r")\b",
    re.IGNORECASE,
)
NEWSWIRE_COMPANY_MARKER_RE = re.compile(
    r"\b(inc|inc\.|corp|corp\.|corporation|company|co\.|ltd|limited|plc|holdings|"
    r"bancorp|financial|bank|therapeutics|biotech|pharma|energy|systems|technologies|"
    r"acquisition corp|capital|resources|semiconductor|software|medtech)\b",
    re.IGNORECASE,
)


def parse_date_value(value: str, *, default: date | None = None) -> date | None:
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text).date()
    except (TypeError, ValueError, IndexError, AttributeError):
        return default


def parse_datetime_value(value: str) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, IndexError, AttributeError):
        return text


def date_range(start: date, end: date) -> list[date]:
    if end < start:
        return []
    values = []
    current = start
    while current <= end:
        values.append(current)
        current += timedelta(days=1)
    return values


def month_range(start: date, end: date) -> list[date]:
    if end < start:
        return []
    values = []
    current = date(start.year, start.month, 1)
    final = date(end.year, end.month, 1)
    while current <= final:
        values.append(current)
        current = date(current.year + 1, 1, 1) if current.month == 12 else date(current.year, current.month + 1, 1)
    return values


def backfill_window(config: PublicNewswireConfig) -> tuple[date, date]:
    start = parse_date_value(config.backfill_start_date, default=date.fromisoformat(DEFAULT_BACKFILL_START_DATE))
    end = parse_date_value(config.backfill_end_date, default=datetime.now(UTC).date())
    assert start is not None and end is not None
    return start, end


def businesswire_datetime_from_url(url: str) -> str:
    match = re.search(r"/news/home/(\d{14})/", str(url or ""))
    if not match:
        return ""
    try:
        dt = datetime.strptime(match.group(1), "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    except ValueError:
        return ""
    return dt.isoformat().replace("+00:00", "Z")


def newswire_backfill_archive_urls(source_key: str, start: date, end: date, *, prnewswire_archive_scope: str = "all") -> list[str]:
    if source_key == "businesswire":
        return [
            f"https://bw-prod-sitemap.s3.us-east-1.amazonaws.com/webdmz1.vaprod.businesswire.com/home/{day.isoformat()}.xml.gz"
            for day in date_range(start, end)
        ]
    if source_key == "globenewswire":
        return [f"https://sitemaps.globenewswire.com/news/en/{month.year:04d}-{month.month:02d}.xml" for month in month_range(start, end)]
    if source_key == "prnewswire":
        recent_pages = [f"https://www.prnewswire.com/sitemap-news.xml?page={page}" for page in range(1, 16)]
        monthly = [f"https://www.prnewswire.com/Sitemap_Index_{MONTH_ABBR[month.month - 1]}_{month.year:04d}.xml.gz" for month in month_range(start, end)]
        if prnewswire_archive_scope == "recent":
            return recent_pages
        if prnewswire_archive_scope == "monthly":
            return monthly
        return [*recent_pages, *monthly]
    return []


def load_universe_entities(path: Path = DEFAULT_UNIVERSE_PATH) -> list[UniverseEntity]:
    if not path.exists():
        return []
    records: dict[str, UniverseEntity] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = str(row.get("symbol", "")).strip().upper()
            status = str(row.get("status", "active")).strip().lower()
            tradable = str(row.get("tradable", "true")).strip().lower()
            name = normalize_text(str(row.get("name", "")))
            if not symbol or not name or status != "active" or tradable not in {"true", "1", "yes"}:
                continue
            records[symbol] = UniverseEntity(symbol=symbol, name=name, exchange=normalize_text(str(row.get("exchange", ""))).upper())
    return [records[symbol] for symbol in sorted(records)]


def _strip_share_descriptors(alias: str) -> str:
    text = alias
    for pattern in SHARE_DESCRIPTOR_PATTERNS:
        text = re.sub(pattern, "", text).strip()
    return normalize_text(text)


def _strip_legal_suffixes(alias: str) -> str:
    tokens = alias.split()
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    return " ".join(tokens)


def _alias_allowed(alias: str) -> bool:
    if not alias or alias in BLOCKED_ALIASES:
        return False
    tokens = alias.split()
    if len(tokens) == 1 and len(alias) < 6:
        return False
    if len(alias) < 5:
        return False
    return True


def company_aliases(name: str) -> list[str]:
    base = normalize_entity_text(name)
    candidates = [base]
    descriptor_stripped = _strip_share_descriptors(base)
    candidates.append(descriptor_stripped)
    candidates.append(_strip_legal_suffixes(descriptor_stripped))
    out: list[str] = []
    for candidate in candidates:
        candidate = normalize_text(candidate)
        if candidate and candidate not in out and _alias_allowed(candidate):
            out.append(candidate)
    return out


def build_entity_mapper(universe_path: Path = DEFAULT_UNIVERSE_PATH) -> EntityMapper:
    entities = load_universe_entities(universe_path)
    aliases: dict[str, dict[str, UniverseEntity]] = {}
    for entity in entities:
        for alias in company_aliases(entity.name):
            aliases.setdefault(alias, {})[entity.symbol] = entity
    alias_index = {alias: next(iter(symbols.values())) for alias, symbols in aliases.items() if len(symbols) == 1}
    ambiguous = frozenset(alias for alias, symbols in aliases.items() if len(symbols) > 1)
    return EntityMapper(
        entities_by_symbol={entity.symbol: entity for entity in entities},
        alias_index=alias_index,
        ambiguous_aliases=ambiguous,
    )


def safe_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.=-]+", "_", str(value or ""))[:120] or "unknown"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_url(url: str, config: PublicNewswireConfig) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = Request(
            url,
            headers={
                "User-Agent": user_agent(),
                "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,text/html,*/*",
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
        truncated = len(payload) > config.max_bytes
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": int(getattr(exc, "code", 0) or 0),
            "content_type": (exc.headers or {}).get("Content-Type", "") if getattr(exc, "headers", None) else "",
            "bytes": payload[: config.max_bytes],
            "truncated": truncated,
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
            "bytes": b"",
            "truncated": False,
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": type(exc).__name__,
            "error_message": redact_text(str(exc))[:500],
        }


def classify_fetch_failure(fetched: dict[str, Any], *, parsed_rows: int = 0, follow_urls: int = 0) -> str:
    if not bool(fetched.get("ok")):
        status_code = int(fetched.get("status_code") or 0)
        error_category = str(fetched.get("error_category") or "")
        if status_code in {401, 403}:
            return "HTTP_ACCESS_BLOCKED"
        if 400 <= status_code < 500:
            return "HTTP_4XX"
        if status_code >= 500:
            return "HTTP_5XX"
        if "timeout" in error_category.lower():
            return "FETCH_TIMEOUT"
        return "FETCH_EXCEPTION"
    if parsed_rows == 0 and follow_urls == 0:
        return "PARSE_ZERO_ROWS"
    if parsed_rows == 0 and follow_urls > 0:
        return "FOLLOW_ONLY_NO_ROWS"
    return "OK"


def add_candidate(candidates: list[str], candidate_modes: dict[str, str], url: str, mode: str) -> None:
    text = str(url or "").strip()
    if not text or text in candidate_modes:
        return
    candidates.append(text)
    candidate_modes[text] = mode


def build_collection_candidates(source: dict[str, Any], robots: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    candidates: list[str] = []
    candidate_modes: dict[str, str] = {}
    for url in source.get("rss_or_feed_urls", []):
        add_candidate(candidates, candidate_modes, str(url), "rss_or_feed")
    for url in source.get("sitemap_urls", []):
        add_candidate(candidates, candidate_modes, str(url), "sitemap")
    for url in robots.get("sitemap_samples", []):
        add_candidate(candidates, candidate_modes, str(url), "robots_sitemap")
    if source.get("probe_url"):
        add_candidate(candidates, candidate_modes, str(source.get("probe_url")), "static_html_probe")
    if source.get("base_url"):
        add_candidate(candidates, candidate_modes, str(source.get("base_url")), "static_html_base")
    return candidates, candidate_modes


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
        "failure_reason": fetched.get("failure_reason", "") or classify_fetch_failure(fetched),
        "error_message_redacted": fetched.get("error_message", ""),
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


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child_text(element: ET.Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for child in list(element):
        if strip_ns(child.tag) in wanted and child.text:
            return normalize_text(child.text)
    return ""


def decode_payload(payload: bytes) -> bytes:
    if not payload.startswith(b"\x1f\x8b"):
        return payload
    try:
        return gzip.decompress(payload)
    except (OSError, EOFError):
        return payload


def deep_text(element: ET.Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for child in element.iter():
        if strip_ns(child.tag) in wanted and child.text:
            return normalize_text(child.text)
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


def deep_text_from_namespace(element: ET.Element, name: str, namespace_token: str) -> str:
    for child in element.iter():
        if strip_ns(child.tag) == name and namespace_token in child.tag and child.text:
            return normalize_text(child.text)
    return ""


def regex_tag_text(block: str, local_name: str) -> str:
    match = re.search(rf"<(?:[A-Za-z0-9_.-]+:)?{re.escape(local_name)}(?:\s[^>]*)?>(.*?)</(?:[A-Za-z0-9_.-]+:)?{re.escape(local_name)}>", block, re.IGNORECASE | re.DOTALL)
    return normalize_text(unescape(re.sub(r"<[^>]+>", " ", match.group(1)))) if match else ""


def parse_sitemap_entries(payload: bytes) -> tuple[list[dict[str, str]], list[str], bool]:
    payload = decode_payload(payload)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return parse_sitemap_entries_fallback(payload)
    tag = strip_ns(root.tag).lower()
    entries: list[dict[str, str]] = []
    follow_urls: list[str] = []
    if tag == "sitemapindex":
        for item in [node for node in root.iter() if strip_ns(node.tag) == "sitemap"]:
            loc = deep_text(item, ("loc",))
            if loc:
                follow_urls.append(loc)
        return entries, follow_urls, True
    if tag != "urlset":
        return entries, follow_urls, True
    for item in [node for node in root.iter() if strip_ns(node.tag) == "url"]:
        loc = deep_text(item, ("loc",))
        if not loc:
            continue
        news_title = deep_text_from_namespace(item, "title", "sitemap-news")
        publication_date = deep_text_from_namespace(item, "publication_date", "sitemap-news")
        lastmod = deep_text(item, ("lastmod",))
        entries.append({"loc": loc, "title": news_title, "published_at": publication_date or lastmod, "published_at_source": "news_sitemap" if publication_date else "sitemap_lastmod"})
    return entries, follow_urls, True


def parse_sitemap_entries_fallback(payload: bytes) -> tuple[list[dict[str, str]], list[str], bool]:
    text = decode_payload(payload).decode("utf-8", errors="ignore")
    entries: list[dict[str, str]] = []
    follow_urls: list[str] = []
    sitemap_blocks = re.findall(r"<sitemap\b.*?</sitemap>", text, flags=re.IGNORECASE | re.DOTALL)
    if sitemap_blocks:
        for block in sitemap_blocks:
            loc = regex_tag_text(block, "loc")
            if loc:
                follow_urls.append(loc)
        return entries, follow_urls, False
    for block in re.findall(r"<url\b.*?</url>", text, flags=re.IGNORECASE | re.DOTALL):
        loc = regex_tag_text(block, "loc")
        if not loc:
            continue
        title = regex_tag_text(block, "title") if "sitemap-news" in block or "<news:" in block else ""
        publication_date = regex_tag_text(block, "publication_date")
        lastmod = regex_tag_text(block, "lastmod")
        entries.append({"loc": loc, "title": title, "published_at": publication_date or lastmod, "published_at_source": "news_sitemap" if publication_date else "sitemap_lastmod"})
    return entries, follow_urls, False


def clean_article_title(title: str, source_key: str) -> str:
    text = normalize_text(title)
    if not text:
        return ""
    suffixes = [
        " | business wire",
        " - business wire",
        " | pr newswire",
        " - pr newswire",
        " | globenewswire",
        " - globenewswire",
    ]
    lower = text.lower()
    for suffix in suffixes:
        if lower.endswith(suffix):
            return text[: -len(suffix)].strip()
    return text


def parse_article_metadata(payload: bytes, *, source_key: str) -> dict[str, str]:
    parser = ArticleMetadataParser()
    parser.feed(decode_payload(payload).decode("utf-8", errors="ignore"))
    meta = parser.meta
    title = (
        meta.get("og:title")
        or meta.get("twitter:title")
        or meta.get("headline")
        or meta.get("parsely-title")
        or parser.h1
        or parser.title
    )
    published = (
        meta.get("article:published_time")
        or meta.get("datepublished")
        or meta.get("date")
        or meta.get("publishdate")
        or meta.get("publish-date")
        or meta.get("sailthru.date")
    )
    description = meta.get("description") or meta.get("og:description") or meta.get("twitter:description") or ""
    return {
        "title": clean_article_title(title, source_key),
        "description": normalize_text(description),
        "published_at": parse_datetime_value(published),
        "title_source": "article_html_meta",
        "published_at_source": "article_html_meta" if published else "",
    }


def row_hash(row: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "provider": row.get("provider"),
            "source_key": row.get("source_key"),
            "title": row.get("title"),
            "source_url": row.get("source_url"),
            "published_at": row.get("published_at"),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_row(
    *,
    source_key: str,
    title: str,
    source_url: str,
    published_at: str,
    published_at_text: str,
    captured_at: str,
    source_page_url: str,
    capture_method: str,
    evidence_text: str = "",
    source_time_certified_flag: int | None = None,
    title_source: str = "",
    published_at_source: str = "",
) -> dict[str, Any]:
    certified = int(bool(published_at)) if source_time_certified_flag is None else int(source_time_certified_flag)
    row = {
        "provider": PROVIDER,
        "source_key": source_key,
        "title": normalize_text(title),
        "source_url": source_url,
        "canonical_url": source_url.split("#", 1)[0],
        "published_at": published_at,
        "published_at_text": published_at_text,
        "detected_at": captured_at,
        "captured_at": captured_at,
        "event_time": published_at or captured_at,
        "source_page_url": source_page_url,
        "capture_method": capture_method,
        "source_time_certified_flag": certified,
        "usable_for_historical_backtest_flag": 0,
        "evidence_text_span": normalize_text(evidence_text)[:500],
        "title_source": title_source,
        "published_at_source": published_at_source,
        "source_class": "public_newswire",
        "context_source_class": "",
        "context_scope": [],
        "context_topic_candidates": [],
        "macro_context_candidate_flag": 0,
        "ticker_mapping_required_flag": 1,
        "context_classification_methods": [],
        "symbols": [],
        "entities": [],
        "entity_map": [],
        "entity_candidate_hints": [],
        "entity_candidate_hint_version": CANDIDATE_HINT_VERSION,
        "entity_candidate_hints_are_authority": 0,
        "newswire_recall_review_flag": 0,
        "newswire_recall_topics": [],
        "newswire_recall_reason": [],
        "newswire_recall_version": NEWSWIRE_RECALL_VERSION,
        "newswire_recall_candidate_authority_flag": 0,
        "entity_mapping_status": "BLOCKED_UNMAPPED",
        "entity_mapping_methods": [],
        "entity_mapping_version": ENTITY_MAPPING_VERSION,
        "entity_mapping_inferred_flag": 0,
    }
    row["headline_hash"] = row_hash(row)
    return row


def newswire_context_topics(title: str) -> list[str]:
    text = f" {normalize_text(unescape(str(title or ''))).lower()} "
    if not text.strip() or NEWSWIRE_CONTEXT_EXCLUSION_RE.search(text):
        return []
    topics = []
    for topic, tokens in NEWSWIRE_CONTEXT_TOPIC_RULES:
        if any(newswire_context_token_matches(text, token) for token in tokens):
            topics.append(topic)
    return sorted(set(topics))


def newswire_context_token_matches(text: str, token: str) -> bool:
    cleaned = normalize_text(str(token or "").lower())
    if not cleaned:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(cleaned)}(?![a-z0-9])"
    return bool(re.search(pattern, text))


def newswire_recall_topics(title: str, evidence_text: str = "") -> list[str]:
    text = f" {normalize_text(unescape(str(title or ''))).lower()} {normalize_text(unescape(str(evidence_text or ''))).lower()} "
    if not text.strip() or NEWSWIRE_CONTEXT_EXCLUSION_RE.search(text):
        return []
    topics = []
    for topic, tokens in NEWSWIRE_RECALL_TOPIC_RULES:
        if any(newswire_context_token_matches(text, token) for token in tokens):
            topics.append(topic)
    return sorted(set(topics))


def newswire_entity_review_reasons(title: str, evidence_text: str = "") -> list[str]:
    text = normalize_text(unescape(str(title or "")))
    evidence = normalize_text(unescape(str(evidence_text or "")))
    joined = f" {text} {evidence} "
    if not joined.strip() or NEWSWIRE_CONTEXT_EXCLUSION_RE.search(joined):
        return []
    reasons: list[str] = []
    topics = set(newswire_recall_topics(text, evidence))
    has_company_marker = bool(NEWSWIRE_COMPANY_MARKER_RE.search(joined))
    has_material_topic = bool(topics & NEWSWIRE_ENTITY_REVIEW_TOPICS)
    if NEWSWIRE_ENTITY_REVIEW_ACTION_RE.search(text) and (has_company_marker or has_material_topic):
        reasons.append("company_like_headline_action")
    if has_company_marker:
        reasons.append("company_marker")
    return sorted(set(reasons))


def apply_newswire_recall_overlay(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("entity_mapping_status") or "")
    title = str(row.get("title") or "")
    evidence = str(row.get("evidence_text_span") or "")
    topics = newswire_recall_topics(title, evidence)
    entity_reasons = newswire_entity_review_reasons(title, evidence)
    out = dict(row)
    out.setdefault("newswire_recall_version", NEWSWIRE_RECALL_VERSION)
    out.setdefault("newswire_recall_candidate_authority_flag", 0)
    out.setdefault("newswire_recall_review_flag", 0)
    out.setdefault("newswire_recall_topics", [])
    out.setdefault("newswire_recall_reason", [])
    if status == "NOT_REQUIRED_CONTEXT_NEWSWIRE":
        context_topics = list(out.get("context_topic_candidates") or out.get("context_scope") or [])
        out.update(
            {
                "newswire_recall_review_flag": 1,
                "newswire_recall_topics": sorted(set(context_topics + topics)),
                "newswire_recall_reason": ["context_topic_candidate"],
                "newswire_recall_version": NEWSWIRE_RECALL_VERSION,
                "newswire_recall_candidate_authority_flag": 0,
            }
        )
        return out
    if status == "BLOCKED_AMBIGUOUS_ENTITY" and (topics or entity_reasons):
        out.update(
            {
                "newswire_recall_review_flag": 1,
                "newswire_recall_topics": topics,
                "newswire_recall_reason": sorted(set(["ambiguous_entity_review"] + entity_reasons)),
                "newswire_recall_version": NEWSWIRE_RECALL_VERSION,
                "newswire_recall_candidate_authority_flag": 0,
            }
        )
        return out
    if status != "BLOCKED_UNMAPPED":
        return out
    if not topics and not entity_reasons:
        return out
    out.update(
        {
            "entity_mapping_status": "ENTITY_CANDIDATE_REVIEW",
            "ticker_mapping_required_flag": 0,
            "macro_context_candidate_flag": 0,
            "newswire_recall_review_flag": 1,
            "newswire_recall_topics": topics,
            "newswire_recall_reason": sorted(set(entity_reasons + (["recall_topic_candidate"] if topics else []))),
            "newswire_recall_version": NEWSWIRE_RECALL_VERSION,
            "newswire_recall_candidate_authority_flag": 0,
            "entity_mapping_inferred_flag": 0,
        }
    )
    return out


def apply_newswire_context_classification(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("entity_mapping_status") != "BLOCKED_UNMAPPED":
        return apply_newswire_recall_overlay(row)
    topics = newswire_context_topics(str(row.get("title") or ""))
    if not topics:
        return apply_newswire_recall_overlay(row)
    if newswire_entity_review_reasons(str(row.get("title") or ""), str(row.get("evidence_text_span") or "")):
        return apply_newswire_recall_overlay(row)
    out = dict(row)
    out.update(
        {
            "entity_mapping_status": "NOT_REQUIRED_CONTEXT_NEWSWIRE",
            "macro_context_candidate_flag": 1,
            "ticker_mapping_required_flag": 0,
            "context_source_class": "public_newswire_context",
            "context_scope": topics,
            "context_topic_candidates": topics,
            "context_classification_methods": ["deterministic_newswire_context_keyword"],
            "entity_mapping_inferred_flag": 0,
        }
    )
    return apply_newswire_recall_overlay(out)


def parse_feed_rows(payload: bytes, *, source_key: str, source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    payload = decode_payload(payload)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []
    tag = strip_ns(root.tag).lower()
    if tag not in {"rss", "rdf", "feed"}:
        return []
    if tag == "feed":
        items = [item for item in root.iter() if strip_ns(item.tag) == "entry"]
    else:
        items = [item for item in root.iter() if strip_ns(item.tag) == "item"]
    rows = []
    for item in items:
        title = child_text(item, ("title",))
        link = child_text(item, ("link",)) or atom_link(item) or child_text(item, ("guid",))
        published = child_text(item, ("pubDate", "published", "updated", "date"))
        if not title or not link:
            continue
        rows.append(
            build_row(
                source_key=source_key,
                title=title,
                source_url=link,
                published_at=published,
                published_at_text=published,
                captured_at=captured_at,
                source_page_url=source_page_url,
                capture_method="rss_or_atom",
                evidence_text=title,
            )
        )
    return rows


def parse_sitemap(payload: bytes, *, source_key: str, source_page_url: str, captured_at: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    entries, follow_urls, _parse_ok = parse_sitemap_entries(payload)
    for item in entries:
        loc = item.get("loc", "")
        title = item.get("title", "")
        published = item.get("published_at", "")
        if not loc or not title:
            continue
        rows.append(
            build_row(
                source_key=source_key,
                title=title,
                source_url=loc,
                published_at=published,
                published_at_text=published,
                captured_at=captured_at,
                source_page_url=source_page_url,
                capture_method="news_sitemap",
                evidence_text=title,
                source_time_certified_flag=1 if item.get("published_at_source") == "news_sitemap" else 0,
                title_source="news_sitemap",
                published_at_source=item.get("published_at_source", ""),
            )
        )
    return rows, follow_urls


def parse_html_links(payload: bytes, *, base_url: str) -> dict[str, list[dict[str, str]]]:
    payload = decode_payload(payload)
    parser = LinkParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
    links = []
    for link in parser.links:
        href = link.get("href", "")
        if not href:
            continue
        links.append({**link, "href": urljoin(base_url, href)})
    feed_links = [
        link
        for link in links
        if any(token in link.get("href", "").lower() for token in ("rss", "atom", "feed"))
        or "rss" in link.get("rel", "").lower()
        or "atom" in link.get("type", "").lower()
    ]
    article_links = [
        link
        for link in links
        if is_probable_article_url(link.get("href", ""))
        and len(normalize_text(link.get("text", ""))) >= 20
    ]
    return {"feed_links": feed_links, "article_links": article_links}


def is_probable_article_url(url: str) -> bool:
    lower = str(url or "").lower()
    if any(blocked in lower for blocked in ("/multimedia/", "/resources/", "/rss/", "/contact/", "/account/")):
        return False
    if not re.search(r"/(?:news-release|news-releases|press-release)/", lower):
        return False
    return lower.endswith((".html", ".htm")) or bool(re.search(r"/\d{4}/\d{2}/\d{2}/", lower))


def html_article_rows(payload: bytes, *, source_key: str, source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    rows = []
    for link in parse_html_links(payload, base_url=source_page_url)["article_links"]:
        rows.append(
            build_row(
                source_key=source_key,
                title=link.get("text", ""),
                source_url=link.get("href", ""),
                published_at="",
                published_at_text="",
                captured_at=captured_at,
                source_page_url=source_page_url,
                capture_method="static_html_article_link",
                evidence_text=link.get("text", ""),
            )
        )
    return rows


def is_probable_newswire_article_url(url: str) -> bool:
    lower = str(url or "").lower()
    return is_probable_article_url(lower) or "/news/home/" in lower or "/news-release/" in lower


def row_date(row: dict[str, Any]) -> date | None:
    for key in ("published_at", "published_at_text", "event_time"):
        parsed = parse_date_value(str(row.get(key) or ""))
        if parsed:
            return parsed
    return None


def in_backfill_window(row: dict[str, Any], start: date, end: date) -> bool:
    parsed = row_date(row)
    if parsed is None:
        return True
    return start <= parsed <= end


def entry_datetime(entry: dict[str, str]) -> tuple[str, int, str]:
    published = parse_datetime_value(entry.get("published_at", ""))
    source = entry.get("published_at_source", "")
    if published:
        return published, int(source == "news_sitemap"), source
    from_url = businesswire_datetime_from_url(entry.get("loc", ""))
    if from_url:
        return from_url, 0, "source_url_timestamp"
    return "", 0, ""


def build_row_from_archive_entry(
    *,
    source_key: str,
    entry: dict[str, str],
    captured_at: str,
    archive_url: str,
    title: str,
    title_source: str,
    published_at: str,
    source_time_certified_flag: int,
    published_at_source: str,
    evidence_text: str,
) -> dict[str, Any]:
    return build_row(
        source_key=source_key,
        title=title,
        source_url=entry.get("loc", ""),
        published_at=published_at,
        published_at_text=entry.get("published_at", "") or published_at,
        captured_at=captured_at,
        source_page_url=archive_url,
        capture_method="historical_archive_sitemap",
        evidence_text=evidence_text or title,
        source_time_certified_flag=source_time_certified_flag,
        title_source=title_source,
        published_at_source=published_at_source,
    )


def is_nonretryable_missing_archive(source_key: str, archive_url: str, fetch_record: dict[str, Any]) -> bool:
    status_code = int(fetch_record.get("status_code") or 0)
    message = str(fetch_record.get("error_message_redacted") or "")
    if status_code == 404 or "HTTP Error 404" in message:
        return True
    parsed = urlparse(archive_url)
    is_businesswire_daily_s3 = (
        source_key == "businesswire"
        and parsed.netloc == "bw-prod-sitemap.s3.us-east-1.amazonaws.com"
        and re.search(r"/home/\d{4}-\d{2}-\d{2}\.xml\.gz$", parsed.path)
    )
    return bool(is_businesswire_daily_s3 and (status_code == 403 or "HTTP Error 403" in message))


def ordered_unique(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        out.append(text)
        seen.add(text)
    return out


def _entity_record(entity: UniverseEntity, *, match_type: str, matched_text: str, source_field: str, exchange_tag: str = "") -> dict[str, Any]:
    return {
        "symbol": entity.symbol,
        "name": entity.name,
        "exchange": entity.exchange,
        "match_type": match_type,
        "matched_text": matched_text,
        "source_field": source_field,
        "exchange_tag": exchange_tag,
        "confidence": 1.0,
        "entity_source": "alpaca_active_us_equity_universe",
        "inferred_flag": 0,
    }


def _source_declared_exchange_record(symbol: str, *, matched_text: str, source_field: str, exchange_tag: str) -> dict[str, Any]:
    return {
        "symbol": symbol.upper(),
        "name": "",
        "exchange": exchange_tag,
        "match_type": "exchange_tag",
        "matched_text": matched_text,
        "source_field": source_field,
        "exchange_tag": exchange_tag,
        "confidence": 1.0,
        "entity_source": "public_newswire_source_declared_exchange_tag",
        "active_universe_match_flag": 0,
        "inferred_flag": 0,
    }


def _add_match(matches: dict[str, dict[str, Any]], record: dict[str, Any]) -> None:
    symbol = str(record.get("symbol") or "").upper()
    if not symbol:
        return
    existing = matches.get(symbol)
    if existing and existing.get("match_type") == "exchange_tag":
        return
    matches[symbol] = record


def _exchange_tag_matches(evidence: str, mapper: EntityMapper) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for exchange_match in EXCHANGE_TAG_RE.finditer(evidence):
        exchange = normalize_text(exchange_match.group("exchange")).upper()
        raw_symbols = exchange_match.group("symbols")
        for symbol in re.findall(r"\b[A-Z][A-Z0-9.-]{0,11}\b", raw_symbols.upper()):
            entity = mapper.entities_by_symbol.get(symbol)
            if entity is None:
                record = _source_declared_exchange_record(
                    symbol,
                    matched_text=symbol,
                    source_field="title_or_evidence_text",
                    exchange_tag=exchange,
                )
            else:
                record = _entity_record(
                    entity,
                    match_type="exchange_tag",
                    matched_text=symbol,
                    source_field="title_or_evidence_text",
                    exchange_tag=exchange,
                )
                record["active_universe_match_flag"] = 1
            _add_match(matches, record)
    return matches


def _alias_matches(evidence: str, mapper: EntityMapper) -> tuple[dict[str, dict[str, Any]], list[str]]:
    normalized = f" {normalize_entity_text(unescape(evidence))} "
    matches: dict[str, dict[str, Any]] = {}
    ambiguous_hits: list[str] = []
    for alias, entity in mapper.alias_index.items():
        if f" {alias} " not in normalized:
            continue
        _add_match(
            matches,
            _entity_record(
                entity,
                match_type="exact_universe_alias",
                matched_text=alias,
                source_field="title_or_evidence_text",
            ),
        )
    for alias in mapper.ambiguous_aliases:
        if f" {alias} " in normalized:
            ambiguous_hits.append(alias)
    return matches, sorted(set(ambiguous_hits))


def _candidate_hints(evidence: str, mapper: EntityMapper) -> list[dict[str, Any]]:
    normalized = f" {normalize_entity_text(unescape(evidence))} "
    hints: list[dict[str, Any]] = []
    for alias, entity in mapper.alias_index.items():
        if f" {alias} " in normalized:
            hints.append(
                {
                    "symbol": entity.symbol,
                    "name": entity.name,
                    "matched_text": alias,
                    "hint_type": "exact_universe_alias_candidate",
                    "candidate_only_flag": 1,
                    "mapping_authority_flag": 0,
                }
            )
    for alias in mapper.ambiguous_aliases:
        if f" {alias} " in normalized:
            hints.append(
                {
                    "symbol": "",
                    "name": "",
                    "matched_text": alias,
                    "hint_type": "ambiguous_alias_candidate",
                    "candidate_only_flag": 1,
                    "mapping_authority_flag": 0,
                }
            )
    return sorted(hints, key=lambda item: (str(item.get("hint_type")), str(item.get("symbol")), str(item.get("matched_text"))))[:12]


def apply_entity_mapping(row: dict[str, Any], mapper: EntityMapper) -> dict[str, Any]:
    out = dict(row)
    evidence = " ".join(
        value
        for value in (
            str(out.get("title") or ""),
            str(out.get("evidence_text_span") or ""),
        )
        if value
    )
    matches = _exchange_tag_matches(evidence, mapper)
    alias_matches, ambiguous_hits = _alias_matches(evidence, mapper)
    for record in alias_matches.values():
        _add_match(matches, record)
    entities = [matches[symbol] for symbol in sorted(matches)]
    methods = sorted({str(record.get("match_type")) for record in entities if record.get("match_type")})
    if entities:
        status = "MAPPED_MULTIPLE"
        if methods == ["exchange_tag"]:
            status = "MAPPED_EXCHANGE_TAG"
        elif methods == ["exact_universe_alias"]:
            status = "MAPPED_EXACT_ALIAS"
        elif "exchange_tag" in methods and "exact_universe_alias" in methods:
            status = "MAPPED_MIXED_EVIDENCE"
    elif ambiguous_hits:
        status = "BLOCKED_AMBIGUOUS_ENTITY"
    else:
        status = "BLOCKED_UNMAPPED"
    out.update(
        {
            "symbols": [record["symbol"] for record in entities],
            "entities": entities,
            "entity_map": entities,
            "entity_candidate_hints": _candidate_hints(evidence, mapper),
            "entity_candidate_hint_version": CANDIDATE_HINT_VERSION,
            "entity_candidate_hints_are_authority": 0,
            "entity_mapping_status": status,
            "entity_mapping_methods": methods,
            "entity_mapping_ambiguous_aliases": ambiguous_hits,
            "entity_mapping_version": ENTITY_MAPPING_VERSION,
            "entity_mapping_inferred_flag": 0,
        }
    )
    return apply_newswire_context_classification(out)


def apply_entity_mapping_to_rows(rows: list[dict[str, Any]], mapper: EntityMapper) -> list[dict[str, Any]]:
    return [apply_entity_mapping(row, mapper) for row in rows]


def selected_sources(config: PublicNewswireConfig) -> list[dict[str, Any]]:
    wanted = set(config.sources)
    return [
        source
        for source in load_registry(config.registry_path)
        if str(source.get("source_key")) in wanted and str(source.get("source_key")) != "sec_edgar"
    ]


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
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


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


def fetch_failure_counts(fetches: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in fetches:
        reason = str(item.get("failure_reason") or "")
        if not reason:
            continue
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def fetch_stage_counts(fetches: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in fetches:
        stage = str(item.get("fallback_stage") or item.get("capability") or "")
        if not stage:
            continue
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def log_line(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{now_z()} {message}\n")


def write_payload(
    config: PublicNewswireConfig,
    *,
    source_key: str,
    captured_at: str,
    rows: list[dict[str, Any]],
    fetches: list[dict[str, Any]],
    collection_mode: str = "watcher",
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
        "fetch_failure_counts": fetch_failure_counts(fetches),
        "fetch_stage_counts": fetch_stage_counts(fetches),
        "fallback_order": ["rss_or_feed", "sitemap", "robots_sitemap", "static_html_probe", "static_html_base", "discovered_follow_url"],
        "chrome_smoke_role": "selector_drift_and_public_page_diagnostics_only_not_runtime_collection",
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def collect_source(source: dict[str, Any], config: PublicNewswireConfig, mapper: EntityMapper) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    base_url = str(source.get("base_url") or source.get("probe_url") or "")
    origin = source_origin(base_url)
    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False, "sitemap_samples": []}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")
    candidates, candidate_modes = build_collection_candidates(source, robots)
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = [
        {
            "url": robots_url,
            "capability": "robots",
            "fallback_stage": "robots_preflight",
            "failure_reason": classify_fetch_failure(robots_fetch),
            "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json")),
        }
    ]
    seen_rows = set()
    index = 0
    while index < len(candidates) and len(fetches) <= max(int(config.max_fetches_per_source), 1) and len(rows) < max(int(config.max_items_per_source), 1):
        url = candidates[index]
        index += 1
        fallback_stage = candidate_modes.get(url, "follow_url")
        if not robots_url_allowed(url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            fetches.append({"url": url, "status": "BLOCKED_ROBOTS", "skipped_by_robots": True, "fallback_stage": fallback_stage, "failure_reason": "ROBOTS_BLOCKED"})
            continue
        fetched = fetch_url(url, config)
        raw_meta = write_response(config.raw_dir, source_key=source_key, capability=fallback_stage, url=url, fetched=fetched)
        fetch_record = {
            "url": url,
            "resolved_url": fetched.get("resolved_url", url),
            "ok": bool(fetched.get("ok")),
            "status_code": fetched.get("status_code", 0),
            "content_type": fetched.get("content_type", ""),
            "fallback_stage": fallback_stage,
            "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
            "row_count": 0,
            "follow_url_count": 0,
        }
        if fetched.get("ok"):
            payload = fetched.get("bytes", b"")
            parsed_rows = parse_feed_rows(payload, source_key=source_key, source_page_url=url, captured_at=captured_at)
            sitemap_rows, follow_urls = parse_sitemap(payload, source_key=source_key, source_page_url=url, captured_at=captured_at)
            parsed_rows.extend(sitemap_rows)
            if "html" in str(fetched.get("content_type", "")).lower():
                links = parse_html_links(payload, base_url=url)
                follow_urls.extend(link["href"] for link in links["feed_links"])
                parsed_rows.extend(html_article_rows(payload, source_key=source_key, source_page_url=url, captured_at=captured_at))
            for follow in ordered_unique(follow_urls):
                if follow not in candidate_modes:
                    add_candidate(candidates, candidate_modes, follow, "discovered_follow_url")
            for row in parsed_rows:
                key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                if key in seen_rows:
                    continue
                seen_rows.add(key)
                rows.append(row)
                if len(rows) >= max(int(config.max_items_per_source), 1):
                    break
            fetch_record["row_count"] = len(parsed_rows)
            fetch_record["follow_url_count"] = len(follow_urls)
            fetch_record["failure_reason"] = classify_fetch_failure(fetched, parsed_rows=len(parsed_rows), follow_urls=len(follow_urls))
        else:
            fetch_record["error_category"] = fetched.get("error_category", "")
            fetch_record["error_message_redacted"] = fetched.get("error_message", "")
            fetch_record["failure_reason"] = classify_fetch_failure(fetched)
        fetches.append(fetch_record)
        time.sleep(max(float(config.request_sleep_seconds), 0.0))
    rows = apply_entity_mapping_to_rows(rows, mapper)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches)
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    blocked = sum(1 for item in fetches if item.get("status") == "BLOCKED_ROBOTS")
    failure_reasons = sorted({str(item.get("failure_reason") or "") for item in fetches if str(item.get("failure_reason") or "") not in {"", "OK"}})
    if blocked and not rows:
        status = "BLOCKED_ROBOTS"
    elif not rows and failure_reasons:
        status = f"EMPTY_PROVIDER_RESPONSE_{failure_reasons[0]}"
    mapped = sum(1 for row in rows if row.get("symbols"))
    hinted = sum(1 for row in rows if row.get("entity_candidate_hints"))
    ambiguous = sum(1 for row in rows if row.get("entity_mapping_status") == "BLOCKED_AMBIGUOUS_ENTITY")
    unmapped = sum(1 for row in rows if row.get("entity_mapping_status") == "BLOCKED_UNMAPPED")
    recall = sum(1 for row in rows if row.get("newswire_recall_review_flag") in (1, "1", True))
    entity_review = sum(1 for row in rows if row.get("entity_mapping_status") == "ENTITY_CANDIDATE_REVIEW")
    event = source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::rss_sitemap",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};fetches={len(fetches)};blocked_robots={blocked};"
            f"fallback_order=rss_or_feed>sitemap>robots_sitemap>static_html_probe>static_html_base>discovered_follow_url;"
            f"failure_reasons={','.join(failure_reasons) or 'none'};"
            f"collector_version={COLLECTOR_VERSION};entity_mapping_version={ENTITY_MAPPING_VERSION};"
            f"mapped_rows={mapped};candidate_hint_rows={hinted};blocked_unmapped_rows={unmapped};"
            f"blocked_ambiguous_rows={ambiguous};newswire_recall_review_rows={recall};"
            f"entity_candidate_review_rows={entity_review}"
        ),
    )
    return event


def collect_source_backfill(source: dict[str, Any], config: PublicNewswireConfig, mapper: EntityMapper, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    start_date, end_date = backfill_window(config)
    archive_urls = newswire_backfill_archive_urls(source_key, start_date, end_date, prnewswire_archive_scope=config.prnewswire_archive_scope)
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_urls = set(backfill_state.setdefault("completed_archive_urls", []))
    unavailable_urls = set(backfill_state.setdefault("unavailable_archive_urls", []))
    entry_offsets = backfill_state.setdefault("archive_entry_offsets", {})
    pending_urls = [url for url in archive_urls if url not in completed_urls]
    captured_at = now_z()
    base_url = str(source.get("base_url") or source.get("probe_url") or "")
    origin = source_origin(base_url)
    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False, "sitemap_samples": []}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")
    fetches: list[dict[str, Any]] = [{"url": robots_url, "capability": "robots", "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json"))}]
    rows: list[dict[str, Any]] = []
    seen_rows = set()
    processed_archives: list[str] = []
    missing_archives = 0
    blocked = 0
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)

    for archive_url in pending_urls:
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        if not robots_url_allowed(archive_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            fetches.append({"url": archive_url, "status": "BLOCKED_ROBOTS", "skipped_by_robots": True})
            completed_urls.add(archive_url)
            blocked += 1
            continue
        archive_fetch = fetch_url(archive_url, config)
        archive_meta = write_response(config.raw_dir, source_key=source_key, capability="archive_url", url=archive_url, fetched=archive_fetch)
        fetch_record = {
            "url": archive_url,
            "resolved_url": archive_fetch.get("resolved_url", archive_url),
            "ok": bool(archive_fetch.get("ok")),
            "status_code": archive_fetch.get("status_code", 0),
            "content_type": archive_fetch.get("content_type", ""),
            "raw_metadata_path": str(Path(archive_meta["body_path"]).with_name("metadata.json")),
            "row_count": 0,
            "follow_url_count": 0,
        }
        if not archive_fetch.get("ok"):
            fetch_record["error_category"] = archive_fetch.get("error_category", "")
            fetch_record["error_message_redacted"] = archive_fetch.get("error_message", "")
            fetches.append(fetch_record)
            if is_nonretryable_missing_archive(source_key, archive_url, fetch_record):
                completed_urls.add(archive_url)
                unavailable_urls.add(archive_url)
                missing_archives += 1
                continue
            break
        entries, follow_urls, parse_ok = parse_sitemap_entries(archive_fetch.get("bytes", b""))
        fetch_record["row_count"] = len(entries)
        fetch_record["follow_url_count"] = len(follow_urls)
        fetch_record["xml_parse_ok"] = parse_ok
        if not parse_ok and not entries and not follow_urls:
            fetch_record["status"] = "TRANSIENT_EMPTY_RESPONSE"
            fetch_record["error_category"] = "SITEMAP_PARSE_FAILED"
            fetch_record["error_message_redacted"] = "archive sitemap parse failed or compressed payload was incomplete"
            fetches.append(fetch_record)
            break
        fetches.append(fetch_record)
        processed_archives.append(archive_url)
        start_offset = int(entry_offsets.get(archive_url, 0) or 0)
        archive_complete = True
        next_offset = start_offset
        for index in range(start_offset, len(entries)):
            if len(rows) >= max_rows or len(fetches) >= max_fetches:
                archive_complete = False
                break
            entry = entries[index]
            next_offset = index + 1
            loc = entry.get("loc", "")
            if not loc or not is_probable_newswire_article_url(loc):
                continue
            published_at, certified, published_source = entry_datetime(entry)
            title = normalize_text(entry.get("title", ""))
            title_source = "news_sitemap" if title else ""
            evidence_text = title
            fetch_article_for_mapping = bool(source.get("fetch_article_metadata_for_mapping"))
            if (not title and config.fetch_missing_title_pages) or fetch_article_for_mapping:
                if len(fetches) >= max_fetches:
                    archive_complete = False
                    next_offset = index
                    break
                if not robots_url_allowed(loc, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
                    fetches.append({"url": loc, "status": "BLOCKED_ROBOTS", "skipped_by_robots": True})
                    blocked += 1
                    continue
                article_fetch = fetch_url(loc, config)
                article_meta = write_response(config.raw_dir, source_key=source_key, capability="article_page", url=loc, fetched=article_fetch)
                fetches.append(
                    {
                        "url": loc,
                        "capability": "article_page",
                        "resolved_url": article_fetch.get("resolved_url", loc),
                        "ok": bool(article_fetch.get("ok")),
                        "status_code": article_fetch.get("status_code", 0),
                        "content_type": article_fetch.get("content_type", ""),
                        "raw_metadata_path": str(Path(article_meta["body_path"]).with_name("metadata.json")),
                    }
                )
                if article_fetch.get("ok"):
                    metadata = parse_article_metadata(article_fetch.get("bytes", b""), source_key=source_key)
                    if metadata.get("title"):
                        title = metadata.get("title", "")
                        title_source = metadata.get("title_source", "")
                    evidence_text = " ".join(value for value in (title, metadata.get("description", "")) if value)
                    if metadata.get("published_at"):
                        published_at = metadata["published_at"]
                        published_source = metadata.get("published_at_source", "article_html_meta")
                        certified = 1
                time.sleep(max(float(config.request_sleep_seconds), 0.0))
            if not title:
                continue
            row = build_row_from_archive_entry(
                source_key=source_key,
                entry=entry,
                captured_at=captured_at,
                archive_url=archive_url,
                title=title,
                title_source=title_source,
                published_at=published_at,
                source_time_certified_flag=certified,
                published_at_source=published_source,
                evidence_text=evidence_text,
            )
            if not in_backfill_window(row, start_date, end_date):
                continue
            key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
            if key in seen_rows:
                continue
            seen_rows.add(key)
            rows.append(row)
        if archive_complete:
            completed_urls.add(archive_url)
            unavailable_urls.discard(archive_url)
            entry_offsets.pop(archive_url, None)
        else:
            entry_offsets[archive_url] = next_offset
            break
        time.sleep(max(float(config.request_sleep_seconds), 0.0))

    backfill_state["completed_archive_urls"] = sorted(completed_urls)
    backfill_state["unavailable_archive_urls"] = sorted(unavailable_urls)
    backfill_state["archive_entry_offsets"] = entry_offsets
    backfill_state["start_date"] = start_date.isoformat()
    backfill_state["end_date"] = end_date.isoformat()
    backfill_state["total_archive_urls"] = len(archive_urls)
    backfill_state["pending_archive_urls"] = max(len(archive_urls) - len(completed_urls), 0)
    rows = apply_entity_mapping_to_rows(rows, mapper)
    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches, collection_mode="historical_backfill")
    retryable_fetch_failure = any(str(item.get("status", "")) == "TRANSIENT_EMPTY_RESPONSE" or str(item.get("error_category", "")) for item in fetches)
    status = (
        "EXPORTED"
        if rows
        else ("BACKFILL_COMPLETE" if len(completed_urls) >= len(archive_urls) else "FAILED_RETRYABLE" if retryable_fetch_failure else "EMPTY_PROVIDER_RESPONSE")
    )
    mapped = sum(1 for row in rows if row.get("symbols"))
    ambiguous = sum(1 for row in rows if row.get("entity_mapping_status") == "BLOCKED_AMBIGUOUS_ENTITY")
    unmapped = sum(1 for row in rows if row.get("entity_mapping_status") == "BLOCKED_UNMAPPED")
    recall = sum(1 for row in rows if row.get("newswire_recall_review_flag") in (1, "1", True))
    entity_review = sum(1 for row in rows if row.get("entity_mapping_status") == "ENTITY_CANDIDATE_REVIEW")
    metadata_enrichment_fetches = sum(1 for item in fetches if item.get("capability") == "article_page")
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};mode=historical_backfill;archives_processed={len(processed_archives)};"
            f"completed_archives={len(completed_urls)}/{len(archive_urls)};unavailable_archives={missing_archives};"
            f"fetches={len(fetches)};metadata_enrichment_fetches={metadata_enrichment_fetches};blocked_robots={blocked};"
            f"collector_version={COLLECTOR_VERSION};entity_mapping_version={ENTITY_MAPPING_VERSION};"
            f"mapped_rows={mapped};blocked_unmapped_rows={unmapped};blocked_ambiguous_rows={ambiguous};"
            f"newswire_recall_review_rows={recall};entity_candidate_review_rows={entity_review}"
        ),
    )


def build_plan(config: PublicNewswireConfig) -> dict[str, Any]:
    sources = selected_sources(config)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_z(),
        "provider": PROVIDER,
        "collector_version": COLLECTOR_VERSION,
        "entity_mapping_version": ENTITY_MAPPING_VERSION,
        "universe_path": str(config.universe_path),
        "source_count": len(sources),
        "backfill": {
            "supported": True,
            "start_date": config.backfill_start_date,
            "end_date": config.backfill_end_date or datetime.now(UTC).date().isoformat(),
            "fetch_missing_title_pages": bool(config.fetch_missing_title_pages),
            "prnewswire_archive_scope": config.prnewswire_archive_scope,
            "source_archive_modes": {
                "prnewswire": "monthly_gzip_sitemap_index_then_article_meta_title",
                "globenewswire": "monthly_news_sitemap_with_title",
                "businesswire": "daily_gzip_sitemap_then_article_meta_title",
            },
        },
        "sources": {
            source["source_key"]: {
                "display_name": source.get("display_name", source.get("source_key")),
                "base_url": source.get("base_url", ""),
                "rss_or_feed_urls": source.get("rss_or_feed_urls", []),
                "sitemap_urls": source.get("sitemap_urls", []),
                "static_html_fallback_urls": [url for url in ordered_unique([str(source.get("probe_url", "")), str(source.get("base_url", ""))]) if url],
                "terms_posture": source.get("terms_posture", ""),
                "mode": "rss_sitemap_static_html_probe_cascade",
                "fallback_order": ["rss_or_feed", "sitemap", "robots_sitemap", "static_html_probe", "static_html_base", "discovered_follow_url"],
                "entity_mapping_policy": "exchange-tag or exact unique universe alias only; no symbol-token fallback",
                "entity_candidate_hint_policy": "candidate hints are non-authority L2 review inputs and cannot open trading gates",
                "chrome_smoke_role": "selector_drift_and_public_page_diagnostics_only_not_runtime_collection",
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


def update_state_for_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    source_id = str(event.get("source_id", ""))
    source_key = source_id.split("::", 1)[0]
    state["processed_events"] = int(state.get("processed_events", 0)) + 1
    status = str(event.get("status", ""))
    if status == "EXPORTED":
        state["exported_events"] = int(state.get("exported_events", 0)) + 1
    elif status == "BACKFILL_COMPLETE":
        state["completed_events"] = int(state.get("completed_events", 0)) + 1
    elif status == "EMPTY_PROVIDER_RESPONSE":
        state["empty_events"] = int(state.get("empty_events", 0)) + 1
    elif status.startswith("BLOCKED"):
        state["blocked_events"] = int(state.get("blocked_events", 0)) + 1
    else:
        state["failed_events"] = int(state.get("failed_events", 0)) + 1
    cycles = state.setdefault("source_cycles", {})
    payload = cycles.setdefault(source_key, {"events": 0, "rows": 0, "last_status": ""})
    payload["events"] = int(payload.get("events", 0)) + 1
    payload["rows"] = int(payload.get("rows", 0)) + int(event.get("row_count", 0) or 0)
    payload["last_status"] = status
    payload["last_updated_at"] = event.get("updated_at", now_z())


def run_collector(config: PublicNewswireConfig, *, smoke: bool = False) -> dict[str, Any]:
    sources = selected_sources(config)
    build_plan(config)
    mapper = build_entity_mapper(config.universe_path)
    state = load_state(config.state_path)
    processed_this_run = 0
    last_status = "STARTED"
    cycle = 0
    log_line(
        config.log_path,
        (
            f"[L0_PUBLIC_NEWSWIRE_START] smoke={int(smoke)} sources={','.join(config.sources)} "
            f"universe_entities={len(mapper.entities_by_symbol)} aliases={len(mapper.alias_index)}"
        ),
    )
    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        for source in sources:
            event = collect_source(source, config, mapper)
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
                    "last_status": last_status,
                    "processed_this_run": processed_this_run,
                    "source_count": len(sources),
                    "plan_path": str(config.plan_path),
                },
            )
            if smoke:
                continue
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
    }
    write_progress(config.progress_path, state, result)
    log_line(config.log_path, f"[L0_PUBLIC_NEWSWIRE_EXIT] {json.dumps(result, sort_keys=True)}")
    return result


def run_backfill(config: PublicNewswireConfig, *, smoke: bool = False) -> dict[str, Any]:
    sources = selected_sources(config)
    build_plan(config)
    mapper = build_entity_mapper(config.universe_path)
    state = load_state(config.state_path)
    processed_this_run = 0
    last_status = "STARTED"
    cycle = 0
    log_line(
        config.log_path,
        (
            f"[L0_PUBLIC_NEWSWIRE_BACKFILL_START] smoke={int(smoke)} sources={','.join(config.sources)} "
            f"window={config.backfill_start_date}:{config.backfill_end_date or 'today'} "
            f"universe_entities={len(mapper.entities_by_symbol)} aliases={len(mapper.alias_index)}"
        ),
    )
    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        active_sources = 0
        for source in sources:
            event = collect_source_backfill(source, config, mapper, state)
            append_event(config.event_path, event)
            update_state_for_event(state, event)
            processed_this_run += 1
            last_status = str(event.get("status", ""))
            if last_status != "BACKFILL_COMPLETE":
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
            if smoke:
                continue
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
    log_line(config.log_path, f"[L0_PUBLIC_NEWSWIRE_BACKFILL_EXIT] {json.dumps(result, sort_keys=True)}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public newswire headlines from RSS/sitemap/static public routes.")
    parser.add_argument("--mode", choices=["smoke", "background", "backfill"], default="smoke")
    parser.add_argument("--sources", nargs="+", default=list(DEFAULT_SOURCES))
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_UNIVERSE_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--max-items-per-source", type=int, default=50)
    parser.add_argument("--max-fetches-per-source", type=int, default=12)
    parser.add_argument("--cycle-sleep-seconds", type=int, default=1800)
    parser.add_argument("--request-sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-cycles", type=int, default=0)
    parser.add_argument("--max-bytes", type=int, default=3_000_000)
    parser.add_argument("--backfill-start-date", default=DEFAULT_BACKFILL_START_DATE)
    parser.add_argument("--backfill-end-date", default="")
    parser.add_argument("--no-fetch-missing-title-pages", action="store_true")
    parser.add_argument("--prnewswire-archive-scope", choices=["all", "monthly", "recent"], default="all")
    parser.add_argument("--exit-when-complete", action="store_true", help="Accepted for sharded backfill compatibility; backfill mode already exits when complete.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = PublicNewswireConfig(
        registry_path=args.registry_path,
        universe_path=args.universe_path,
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
        fetch_missing_title_pages=not args.no_fetch_missing_title_pages,
        prnewswire_archive_scope=args.prnewswire_archive_scope,
    )
    result = run_backfill(config, smoke=args.mode == "smoke") if args.mode == "backfill" else run_collector(config, smoke=args.mode == "smoke")
    print(
        "[L0_PUBLIC_NEWSWIRE] "
        f"mode={args.mode} sources={','.join(args.sources)} status={result['status']} "
        f"processed_this_run={result['processed_this_run']} event_path={result['event_path']} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
