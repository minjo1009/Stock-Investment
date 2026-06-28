from __future__ import annotations

import argparse
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

from tools.db.source_acquisition.news_background_collector import classify_news_error, source_event, write_progress
from tools.db.source_acquisition.secret_redaction import redact_text
from tools.db.source_acquisition.source_capability_probe import (
    build_robot_parser,
    robots_posture,
    robots_url_allowed,
)


PROVIDER = "public_context_news_feeds"
SCHEMA_VERSION = 1
COLLECTOR_VERSION = "public_context_news_collector.v0.1.1"
DEFAULT_REGISTRY_PATH = Path("configs/source_registry/l0_public_context_news_sources.json")
DEFAULT_RAW_DIR = Path("data/raw/l0_public_context_news")
DEFAULT_ARTIFACT_DIR = Path("data/artifacts/l0_public_context_news")
DEFAULT_STATE_PATH = DEFAULT_ARTIFACT_DIR / "collector_state.json"
DEFAULT_EVENT_PATH = DEFAULT_ARTIFACT_DIR / "collector_events.jsonl"
DEFAULT_PROGRESS_PATH = DEFAULT_ARTIFACT_DIR / "collector_progress.json"
DEFAULT_PLAN_PATH = DEFAULT_ARTIFACT_DIR / "collection_plan.json"
DEFAULT_STOP_PATH = DEFAULT_ARTIFACT_DIR / "STOP"
DEFAULT_LOG_PATH = Path("logs/l0_public_context_news_collector.log")
DEFAULT_USER_AGENT = "Codex-L0-PublicContextNews/1.0 contact=operator"
DEFAULT_BACKFILL_START_DATE = "2016-01-01"
DEFAULT_BACKFILL_SOURCES = ("federal_register_documents", "federal_reserve_press_all", "cftc_press_releases", "worldbank_news_api")
DEFAULT_SOURCES = (
    "federal_reserve_press_all",
    "bls_cpi_latest_numbers",
    "bls_principal_federal_economic_indicators",
    "bea_news_release_feed",
    "cftc_press_releases",
    "federal_register_documents",
    "white_house_briefing_room",
    "nasdaq_trader_news",
    "coindesk_rss",
    "ecb_press_rss",
    "ecb_statistical_press_rss",
    "bank_of_england_news_rss",
    "bank_of_england_speeches_rss",
    "eia_press_rss",
    "defense_public_press_rss",
    "defense_public_contracts_rss",
    "worldbank_news_api",
)

TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("monetary_policy", ("fed", "federal reserve", "fomc", "interest rate", "rates", "monetary")),
    ("inflation", ("inflation", "cpi", "ppi", "prices", "price index", "deflator")),
    ("labor_market", ("employment", "unemployment", "jobs", "payroll", "wages", "labor")),
    ("growth", ("gdp", "gross domestic product", "growth", "output", "productivity")),
    ("consumer_spending", ("consumer", "retail sales", "spending", "income")),
    ("fiscal_policy", ("treasury", "deficit", "debt", "tax", "budget", "fiscal")),
    ("regulation", ("rule", "regulation", "enforcement", "federal register", "agency")),
    ("market_structure", ("nasdaq", "exchange", "halt", "listing", "trading", "market structure")),
    ("crypto_digital_assets", ("crypto", "bitcoin", "ether", "digital asset", "stablecoin", "blockchain")),
    ("geopolitics", ("sanction", "war", "tariff", "export control", "national security", "geopolitical")),
    ("risk_appetite", ("market", "risk", "volatility", "liquidity", "credit")),
    ("financial_conditions", ("bank capital", "financial stability", "credit conditions", "liquidity", "systemic")),
    ("economic_indicators", ("indicator", "balance of payments", "industrial production", "retail sales", "survey")),
    ("energy", ("energy", "oil", "gas", "electricity", "grid", "power", "hormuz")),
    ("commodities", ("commodity", "commodities", "copper", "wheat", "grain", "mining")),
    ("global_development", ("world bank", "development", "poverty", "emerging market", "frontier market")),
    ("defense_geopolitics", ("defense", "military", "missile", "pentagon", "contract", "weapon", "southern border")),
    ("trade", ("trade", "tariff", "export", "import", "supply chain", "customs")),
)


@dataclass(frozen=True)
class PublicContextNewsConfig:
    registry_path: Path = DEFAULT_REGISTRY_PATH
    raw_dir: Path = DEFAULT_RAW_DIR
    state_path: Path = DEFAULT_STATE_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    plan_path: Path = DEFAULT_PLAN_PATH
    stop_path: Path = DEFAULT_STOP_PATH
    log_path: Path = DEFAULT_LOG_PATH
    sources: tuple[str, ...] = DEFAULT_SOURCES
    max_items_per_source: int = 25
    max_fetches_per_source: int = 4
    cycle_sleep_seconds: int = 1800
    request_sleep_seconds: float = 1.0
    timeout_seconds: int = 45
    max_bytes: int = 3_000_000
    max_cycles: int = 0
    backfill_start_date: str = DEFAULT_BACKFILL_START_DATE
    backfill_end_date: str = ""
    federal_register_per_page: int = 1000


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._anchor: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "a":
            self._anchor = {"href": values.get("href", ""), "text": ""}

    def handle_data(self, data: str) -> None:
        if self._anchor is not None:
            self._anchor["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._anchor is not None:
            self._anchor["text"] = normalize_text(self._anchor.get("text", ""))
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


class CftcArchiveParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, str]] = []
        self.page_numbers: list[int] = []
        self._in_row = False
        self._row_date = ""
        self._anchor: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        if lower == "tr":
            self._in_row = True
            self._row_date = ""
        elif lower == "time" and self._in_row:
            self._row_date = normalize_text(values.get("datetime", ""))
        elif lower == "a":
            href = values.get("href", "")
            if "/PressRoom/PressReleases/" in href:
                self._anchor = {"href": href, "text": "", "published_at": self._row_date}
            page_match = re.search(r"[?&]page=(\d+)", href)
            if page_match:
                self.page_numbers.append(int(page_match.group(1)) + 1)

    def handle_data(self, data: str) -> None:
        if self._anchor is not None:
            self._anchor["text"] += data

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "a" and self._anchor is not None:
            self._anchor["text"] = normalize_text(self._anchor.get("text", ""))
            if self._anchor["text"]:
                self.rows.append(self._anchor)
            self._anchor = None
        elif lower == "tr":
            self._in_row = False
            self._row_date = ""


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def user_agent() -> str:
    return os.environ.get("L0_NEWS_USER_AGENT") or os.environ.get("SEC_USER_AGENT") or DEFAULT_USER_AGENT


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child_text(element: ET.Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for child in list(element):
        if strip_ns(child.tag) in wanted and child.text:
            return normalize_text(child.text)
    return ""


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


def month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def next_month(value: date) -> date:
    return date(value.year + 1, 1, 1) if value.month == 12 else date(value.year, value.month + 1, 1)


def month_end(value: date) -> date:
    return next_month(month_start(value)) - timedelta(days=1)


def month_range(start: date, end: date) -> list[date]:
    if end < start:
        return []
    values = []
    current = month_start(start)
    final = month_start(end)
    while current <= final:
        values.append(current)
        current = next_month(current)
    return values


def backfill_window(config: PublicContextNewsConfig) -> tuple[date, date]:
    start = parse_date_value(config.backfill_start_date, default=date.fromisoformat(DEFAULT_BACKFILL_START_DATE))
    end = parse_date_value(config.backfill_end_date, default=datetime.now(UTC).date())
    assert start is not None and end is not None
    return start, end


def safe_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.=-]+", "_", str(value or ""))[:120] or "unknown"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def source_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def ordered_unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for value in values:
        value = str(value or "")
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


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


def federal_reserve_date_from_url(url: str) -> str:
    match = re.search(r"(\d{8})[a-z]?\.(?:htm|html)$", str(url or ""), re.IGNORECASE)
    if not match:
        return ""
    try:
        return datetime.strptime(match.group(1), "%Y%m%d").replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        return ""


def load_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    sources = payload.get("sources", [])
    return [source for source in sources if isinstance(source, dict)]


def selected_sources(config: PublicContextNewsConfig) -> list[dict[str, Any]]:
    wanted = set(config.sources)
    return [
        source
        for source in load_registry(config.registry_path)
        if str(source.get("source_key")) in wanted and bool(source.get("enabled", True))
    ]


def context_topics(source: dict[str, Any], title: str) -> list[str]:
    topics = {str(topic) for topic in source.get("context_scope", []) if str(topic)}
    haystack = title.lower()
    for topic, tokens in TOPIC_RULES:
        if any(token in haystack for token in tokens):
            topics.add(topic)
    return sorted(topics)


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
    row: dict[str, Any] = {
        "provider": PROVIDER,
        "source_key": source_key,
        "source_display_name": source.get("display_name", source_key),
        "source_class": source.get("source_class", ""),
        "context_source_class": source.get("source_class", ""),
        "context_scope": [str(item) for item in source.get("context_scope", [])],
        "context_topic_candidates": context_topics(source, cleaned_title),
        "title": cleaned_title,
        "source_url": source_url,
        "canonical_url": source_url.split("#", 1)[0],
        "published_at": parse_datetime_value(published_at),
        "published_at_text": published_at_text,
        "detected_at": captured_at,
        "captured_at": captured_at,
        "event_time": parse_datetime_value(published_at) or captured_at,
        "source_page_url": source_page_url,
        "capture_method": capture_method,
        "language": source.get("language", "en"),
        "title_source": title_source,
        "published_at_source": published_at_source,
        "source_time_certified_flag": int(bool(published_at)),
        "usable_for_historical_backtest_flag": 0,
        "macro_context_candidate_flag": 1,
        "ticker_mapping_required_flag": 0,
        "symbols": [],
        "entities": [],
        "entity_map": [],
        "entity_mapping_status": "NOT_REQUIRED_CONTEXT_NEWS",
        "entity_mapping_methods": [],
        "entity_mapping_version": "public_context_news_mapper.not_required.v0.1.0",
        "entity_mapping_inferred_flag": 0,
    }
    if extra:
        row.update(extra)
    row["headline_hash"] = row_hash(row)
    return row


def fetch_url(url: str, config: PublicContextNewsConfig) -> dict[str, Any]:
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
        return {
            "ok": False,
            "requested_url": url,
            "resolved_url": url,
            "status_code": int(getattr(exc, "code", 0) or 0),
            "content_type": (exc.headers or {}).get("Content-Type", "") if getattr(exc, "headers", None) else "",
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
    items = [item for item in root.iter() if strip_ns(item.tag) == ("entry" if tag == "feed" else "item")]
    rows = []
    for item in items:
        title = deep_text(item, ("title",))
        link = child_text(item, ("link",)) or atom_link(item) or child_text(item, ("guid",))
        published = deep_text(item, ("pubDate", "published", "updated", "date"))
        if not title or not link:
            continue
        rows.append(
            build_row(
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
        )
    return rows


def parse_federal_register_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    try:
        decoded = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(decoded, dict):
        return []
    results = decoded.get("results", [])
    rows: list[dict[str, Any]] = []
    for item in results if isinstance(results, list) else []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        url = str(item.get("html_url") or item.get("pdf_url") or item.get("public_inspection_pdf_url") or "")
        published = str(item.get("publication_date") or "")
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
                capture_method="official_json_api",
                title_source="federal_register_title",
                published_at_source="publication_date" if published else "",
                extra={
                    "document_type": item.get("type", ""),
                    "agencies": item.get("agencies", []),
                    "docket_ids": item.get("docket_ids", []),
                },
            )
        )
    return rows


def json_cdata_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("cdata!", "#text", "text", "value"):
            if key in value:
                return normalize_text(str(value.get(key) or ""))
        return normalize_text(" ".join(str(item) for item in value.values() if item))
    return normalize_text(str(value or ""))


def parse_worldbank_news_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    try:
        decoded = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(decoded, dict):
        return []
    documents = decoded.get("documents", {})
    if isinstance(documents, dict):
        items = list(documents.values())
    elif isinstance(documents, list):
        items = documents
    else:
        items = []
    allowed_languages = {str(item) for item in source.get("worldbank_languages", ["English"]) if str(item)}
    rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        language = normalize_text(str(item.get("lang") or ""))
        if allowed_languages and language and language not in allowed_languages:
            continue
        title = json_cdata_text(item.get("title"))
        url = normalize_text(str(item.get("url") or ""))
        published = normalize_text(str(item.get("lnchdt") or item.get("date") or ""))
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
                capture_method="worldbank_news_json_api",
                title_source="worldbank_title",
                published_at_source="lnchdt" if published else "",
                extra={
                    "language": language or source.get("language", "en"),
                    "worldbank_document_id": item.get("id", ""),
                    "worldbank_content_type": item.get("conttype", ""),
                    "worldbank_display_content_type": item.get("displayconttype", ""),
                    "worldbank_region": item.get("regionname", ""),
                    "worldbank_country": item.get("country", ""),
                    "worldbank_topic": item.get("topic", ""),
                    "worldbank_keywords": item.get("keywd", ""),
                    "summary": json_cdata_text(item.get("descr") or item.get("content_1000") or item.get("content")),
                },
            )
        )
    return rows


def parse_static_listing_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    text = payload.decode("utf-8", errors="ignore")
    parser = LinkParser()
    parser.feed(text)
    rows = []
    for link in parser.links:
        href = str(link.get("href") or "")
        title = normalize_text(link.get("text", ""))
        if len(title) < 12 or not href:
            continue
        full_url = urljoin(source_page_url, href)
        if not looks_like_news_url(full_url):
            continue
        rows.append(
            build_row(
                source=source,
                title=title,
                source_url=full_url,
                published_at="",
                published_at_text="",
                captured_at=captured_at,
                source_page_url=source_page_url,
                capture_method="static_html_listing",
                title_source="html_anchor_text",
            )
        )
    return rows


def parse_federal_reserve_archive_rows(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> list[dict[str, Any]]:
    parser = LinkParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
    rows = []
    seen = set()
    for link in parser.links:
        href = str(link.get("href") or "")
        title = normalize_text(link.get("text", ""))
        full_url = urljoin(source_page_url, href)
        lower = full_url.lower()
        if not title or "/newsevents/pressreleases/" not in lower or not lower.endswith((".htm", ".html")):
            continue
        if re.search(r"/\d{4}-press\.htm$", lower):
            continue
        published = federal_reserve_date_from_url(full_url)
        key = f"{title}|{full_url}"
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            build_row(
                source=source,
                title=title,
                source_url=full_url,
                published_at=published,
                published_at_text=published,
                captured_at=captured_at,
                source_page_url=source_page_url,
                capture_method="federal_reserve_year_archive",
                title_source="archive_anchor_text",
                published_at_source="url_date" if published else "",
            )
        )
    return rows


def parse_cftc_archive(payload: bytes, *, source: dict[str, Any], source_page_url: str, captured_at: str) -> tuple[list[dict[str, Any]], int]:
    parser = CftcArchiveParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
    rows = []
    for item in parser.rows:
        published = parse_datetime_value(item.get("published_at", ""))
        rows.append(
            build_row(
                source=source,
                title=item.get("text", ""),
                source_url=urljoin(source_page_url, item.get("href", "")),
                published_at=published,
                published_at_text=item.get("published_at", ""),
                captured_at=captured_at,
                source_page_url=source_page_url,
                capture_method="cftc_year_archive",
                title_source="archive_anchor_text",
                published_at_source="html_time_datetime" if published else "",
            )
        )
    total_pages = max(parser.page_numbers) if parser.page_numbers else 1
    return rows, total_pages


def parse_article_metadata(payload: bytes) -> dict[str, str]:
    parser = ArticleMetadataParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
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
    return {
        "title": normalize_text(unescape(title)),
        "published_at": parse_datetime_value(published),
        "title_source": "article_html_meta" if title else "",
        "published_at_source": "article_html_meta" if published else "",
    }


def parse_sitemap_entries(payload: bytes) -> tuple[list[dict[str, str]], list[str]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return [], []
    tag = strip_ns(root.tag).lower()
    entries: list[dict[str, str]] = []
    follow: list[str] = []
    if tag == "sitemapindex":
        for item in root.iter():
            if strip_ns(item.tag) != "sitemap":
                continue
            loc = deep_text(item, ("loc",))
            if loc:
                follow.append(loc)
        return entries, ordered_unique(follow)
    if tag != "urlset":
        return entries, follow
    for item in root.iter():
        if strip_ns(item.tag) != "url":
            continue
        loc = deep_text(item, ("loc",))
        if not loc or not looks_like_news_url(loc):
            continue
        entries.append({"loc": loc, "lastmod": deep_text(item, ("lastmod",))})
    return entries, follow


def looks_like_news_url(url: str) -> bool:
    lower = url.lower()
    if lower.endswith((".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".css", ".js")):
        return False
    return any(token in lower for token in ("/news/", "/press", "/briefing-room/", "/tradernews", "/article/", "/markets/"))


def parse_rows_for_url(payload: bytes, *, source: dict[str, Any], url: str, content_type: str, captured_at: str) -> list[dict[str, Any]]:
    source_key = str(source.get("source_key", ""))
    if source_key == "worldbank_news_api":
        api_rows = parse_worldbank_news_rows(payload, source=source, source_page_url=url, captured_at=captured_at)
        if api_rows:
            return api_rows
    if source_key == "federal_register_documents" or "json" in content_type.lower() or url.endswith(".json"):
        api_rows = parse_federal_register_rows(payload, source=source, source_page_url=url, captured_at=captured_at)
        if api_rows:
            return api_rows
    feed_rows = parse_feed_rows(payload, source=source, source_page_url=url, captured_at=captured_at)
    if feed_rows:
        return feed_rows
    if "html" in content_type.lower():
        return parse_static_listing_rows(payload, source=source, source_page_url=url, captured_at=captured_at)
    return []


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
    config: PublicContextNewsConfig,
    *,
    source_key: str,
    captured_at: str,
    rows: list[dict[str, Any]],
    fetches: list[dict[str, Any]],
    collection_mode: str = "context_watch",
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


def context_backfill_units(source_key: str, start: date, end: date) -> list[dict[str, Any]]:
    if source_key == "federal_register_documents":
        units = []
        for month in month_range(start, end):
            unit_start = max(month, start)
            unit_end = min(month_end(month), end)
            units.append(
                {
                    "unit_id": month.strftime("%Y-%m"),
                    "kind": "federal_register_month",
                    "start_date": unit_start.isoformat(),
                    "end_date": unit_end.isoformat(),
                }
            )
        return units
    if source_key == "federal_reserve_press_all":
        return [
            {
                "unit_id": str(year),
                "kind": "federal_reserve_press_year",
                "url": f"https://www.federalreserve.gov/newsevents/pressreleases/{year}-press.htm",
            }
            for year in range(start.year, end.year + 1)
        ]
    if source_key == "cftc_press_releases":
        return [
            {
                "unit_id": str(year),
                "kind": "cftc_press_release_year",
                "year": year,
            }
            for year in range(start.year, end.year + 1)
        ]
    if source_key == "worldbank_news_api":
        return [
            {
                "unit_id": "worldbank_news_desc_cursor",
                "kind": "worldbank_news_api_offset",
            }
        ]
    return []


def federal_register_url(unit: dict[str, Any], *, page: int, per_page: int) -> str:
    params = {
        "per_page": str(max(min(int(per_page), 1000), 1)),
        "page": str(max(int(page), 1)),
        "order": "oldest",
        "conditions[publication_date][gte]": str(unit["start_date"]),
        "conditions[publication_date][lte]": str(unit["end_date"]),
    }
    return f"https://www.federalregister.gov/api/v1/documents.json?{urlencode(params)}"


def in_backfill_window(row: dict[str, Any], start: date, end: date) -> bool:
    value = parse_date_value(str(row.get("published_at") or row.get("event_time") or ""))
    if value is None:
        return True
    return start <= value <= end


def collect_federal_register_backfill_unit(
    source: dict[str, Any],
    config: PublicContextNewsConfig,
    unit: dict[str, Any],
    page: int,
    captured_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], int, bool]:
    per_page = min(max(int(config.federal_register_per_page), 1), max(int(config.max_items_per_source), 1))
    url = federal_register_url(unit, page=page, per_page=per_page)
    fetched = fetch_url(url, config)
    raw_meta = write_response(config.raw_dir, source_key=str(source.get("source_key")), capability="backfill_api", url=url, fetched=fetched)
    fetch_record = {
        "url": url,
        "resolved_url": fetched.get("resolved_url", url),
        "ok": bool(fetched.get("ok")),
        "status_code": fetched.get("status_code", 0),
        "content_type": fetched.get("content_type", ""),
        "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
        "row_count": 0,
        "page": page,
        "unit_id": unit["unit_id"],
    }
    if not fetched.get("ok"):
        fetch_record["error_category"] = fetched.get("error_category", "")
        fetch_record["error_message_redacted"] = fetched.get("error_message", "")
        return [], fetch_record, page, False
    rows = parse_federal_register_rows(
        fetched.get("bytes", b""),
        source=source,
        source_page_url=str(fetched.get("resolved_url") or url),
        captured_at=captured_at,
    )
    try:
        payload = json.loads(fetched.get("bytes", b"").decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {}
    total_pages = int(payload.get("total_pages", 1) or 1) if isinstance(payload, dict) else 1
    fetch_record["row_count"] = len(rows)
    fetch_record["total_pages"] = total_pages
    complete = page >= total_pages
    return rows, fetch_record, page + 1, complete


def collect_federal_reserve_backfill_unit(
    source: dict[str, Any],
    config: PublicContextNewsConfig,
    unit: dict[str, Any],
    captured_at: str,
    start: date,
    end: date,
) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    url = str(unit["url"])
    fetched = fetch_url(url, config)
    raw_meta = write_response(config.raw_dir, source_key=str(source.get("source_key")), capability="backfill_archive_page", url=url, fetched=fetched)
    fetch_record = {
        "url": url,
        "resolved_url": fetched.get("resolved_url", url),
        "ok": bool(fetched.get("ok")),
        "status_code": fetched.get("status_code", 0),
        "content_type": fetched.get("content_type", ""),
        "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
        "row_count": 0,
        "unit_id": unit["unit_id"],
    }
    if not fetched.get("ok"):
        fetch_record["error_category"] = fetched.get("error_category", "")
        fetch_record["error_message_redacted"] = fetched.get("error_message", "")
        return [], fetch_record, False
    rows = [
        row
        for row in parse_federal_reserve_archive_rows(
            fetched.get("bytes", b""),
            source=source,
            source_page_url=str(fetched.get("resolved_url") or url),
            captured_at=captured_at,
        )
        if in_backfill_window(row, start, end)
    ]
    fetch_record["row_count"] = len(rows)
    return rows, fetch_record, True


def cftc_archive_url(year: int, page: int) -> str:
    params = {
        "field_press_release_type_tid": "All",
        "year": str(year),
        "page": str(max(int(page), 1) - 1),
    }
    return f"https://www.cftc.gov/PressRoom/PressReleases?{urlencode(params)}"


def worldbank_rows_per_page(source: dict[str, Any], config: PublicContextNewsConfig) -> int:
    configured = int(source.get("worldbank_rows_per_page", 100) or 100)
    return min(max(configured, 1), max(int(config.max_items_per_source), 1))


def worldbank_news_api_url(source: dict[str, Any], *, offset: int, rows_per_page: int) -> str:
    endpoint = str(source.get("worldbank_api_endpoint") or "https://search.worldbank.org/api/v2/news")
    params = {
        "format": "json",
        "rows": str(max(int(rows_per_page), 1)),
        "os": str(max(int(offset), 0)),
    }
    return f"{endpoint}?{urlencode(params)}"


def collect_worldbank_news_backfill_unit(
    source: dict[str, Any],
    config: PublicContextNewsConfig,
    unit: dict[str, Any],
    offset: int,
    captured_at: str,
    start: date,
    end: date,
) -> tuple[list[dict[str, Any]], dict[str, Any], int, bool]:
    rows_per_page = worldbank_rows_per_page(source, config)
    url = worldbank_news_api_url(source, offset=offset, rows_per_page=rows_per_page)
    fetched = fetch_url(url, config)
    raw_meta = write_response(config.raw_dir, source_key=str(source.get("source_key")), capability="backfill_api", url=url, fetched=fetched)
    fetch_record = {
        "url": url,
        "resolved_url": fetched.get("resolved_url", url),
        "ok": bool(fetched.get("ok")),
        "status_code": fetched.get("status_code", 0),
        "content_type": fetched.get("content_type", ""),
        "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
        "row_count": 0,
        "offset": offset,
        "rows_per_page": rows_per_page,
        "unit_id": unit["unit_id"],
    }
    if not fetched.get("ok"):
        fetch_record["error_category"] = fetched.get("error_category", "")
        fetch_record["error_message_redacted"] = fetched.get("error_message", "")
        return [], fetch_record, offset, False
    all_rows = parse_worldbank_news_rows(
        fetched.get("bytes", b""),
        source=source,
        source_page_url=str(fetched.get("resolved_url") or url),
        captured_at=captured_at,
    )
    rows = [row for row in all_rows if in_backfill_window(row, start, end)]
    try:
        payload = json.loads(fetched.get("bytes", b"").decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {}
    total = int(payload.get("total", 0) or 0) if isinstance(payload, dict) else 0
    next_offset = offset + rows_per_page
    dated = [value for value in (parse_date_value(str(row.get("published_at") or "")) for row in all_rows) if value is not None]
    passed_start_floor = bool(dated) and min(dated) < start
    complete = bool(all_rows) and (passed_start_floor or (total > 0 and next_offset >= total))
    fetch_record["row_count"] = len(rows)
    fetch_record["raw_row_count"] = len(all_rows)
    fetch_record["total"] = total
    fetch_record["next_offset"] = next_offset
    fetch_record["passed_start_floor"] = passed_start_floor
    return rows, fetch_record, next_offset, complete


def collect_cftc_backfill_unit(
    source: dict[str, Any],
    config: PublicContextNewsConfig,
    unit: dict[str, Any],
    page: int,
    captured_at: str,
    start: date,
    end: date,
) -> tuple[list[dict[str, Any]], dict[str, Any], int, bool]:
    year = int(unit["year"])
    url = cftc_archive_url(year, page)
    fetched = fetch_url(url, config)
    raw_meta = write_response(config.raw_dir, source_key=str(source.get("source_key")), capability="backfill_archive_page", url=url, fetched=fetched)
    fetch_record = {
        "url": url,
        "resolved_url": fetched.get("resolved_url", url),
        "ok": bool(fetched.get("ok")),
        "status_code": fetched.get("status_code", 0),
        "content_type": fetched.get("content_type", ""),
        "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
        "row_count": 0,
        "page": page,
        "unit_id": unit["unit_id"],
    }
    if not fetched.get("ok"):
        fetch_record["error_category"] = fetched.get("error_category", "")
        fetch_record["error_message_redacted"] = fetched.get("error_message", "")
        return [], fetch_record, page, False
    parsed_rows, total_pages = parse_cftc_archive(
        fetched.get("bytes", b""),
        source=source,
        source_page_url=str(fetched.get("resolved_url") or url),
        captured_at=captured_at,
    )
    rows = [row for row in parsed_rows if in_backfill_window(row, start, end)]
    fetch_record["row_count"] = len(rows)
    fetch_record["total_pages"] = total_pages
    complete = page >= total_pages
    return rows, fetch_record, page + 1, complete


def build_plan(config: PublicContextNewsConfig) -> dict[str, Any]:
    sources = selected_sources(config)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_z(),
        "provider": PROVIDER,
        "collector_version": COLLECTOR_VERSION,
        "source_count": len(sources),
        "mode": "public_rss_api_static_context_watch",
        "ticker_mapping_policy": "not required for macro/context rows; no GPT/entity inference",
        "historical_backfill_status": "SUPPORTED_FOR_FEDERAL_REGISTER_FEDERAL_RESERVE_CFTC_AND_WORLDBANK_ARCHIVES",
        "backfill": {
            "supported_sources": list(DEFAULT_BACKFILL_SOURCES),
            "start_date": config.backfill_start_date,
            "end_date": config.backfill_end_date or datetime.now(UTC).date().isoformat(),
            "modes": {
                "federal_register_documents": "official_api_monthly_pages",
                "federal_reserve_press_all": "official_year_archive_pages",
                "cftc_press_releases": "official_year_archive_pages",
                "worldbank_news_api": "official_public_json_api_offset_pages_descending_lnchdt",
            },
        },
        "sources": {
            source["source_key"]: {
                "display_name": source.get("display_name", source.get("source_key")),
                "source_class": source.get("source_class", ""),
                "context_scope": source.get("context_scope", []),
                "rss_or_feed_urls": source.get("rss_or_feed_urls", []),
                "api_urls": source.get("api_urls", []),
                "page_urls": source.get("page_urls", []),
                "sitemap_urls": source.get("sitemap_urls", []),
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


def collect_source(source: dict[str, Any], config: PublicContextNewsConfig) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    captured_at = now_z()
    base_url = str(source.get("base_url") or source.get("probe_url") or "")
    origin = source_origin(base_url)
    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, config)
    robots_meta = write_response(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else {"robots_present": False, "sitemap_samples": []}
    robot_parser = build_robot_parser(origin, robots_fetch.get("bytes", b"")) if robots_fetch.get("ok") else build_robot_parser(origin, b"")
    candidates = ordered_unique([
        *[str(url) for url in source.get("rss_or_feed_urls", [])],
        *[str(url) for url in source.get("api_urls", [])],
        *[str(url) for url in source.get("page_urls", [])],
        *[str(url) for url in source.get("sitemap_urls", [])],
        *[str(url) for url in robots.get("sitemap_samples", [])],
    ])
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = [{"url": robots_url, "capability": "robots", "raw_metadata_path": str(Path(robots_meta["body_path"]).with_name("metadata.json"))}]
    seen_rows = set()
    blocked = 0
    index = 0
    max_fetches = max(int(config.max_fetches_per_source), 1) + 1
    max_rows = max(int(config.max_items_per_source), 1)

    while index < len(candidates) and len(fetches) < max_fetches and len(rows) < max_rows:
        url = candidates[index]
        index += 1
        if len(rows) >= max_rows:
            break
        if not robots_url_allowed(url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            fetches.append({"url": url, "status": "BLOCKED_ROBOTS", "skipped_by_robots": True})
            blocked += 1
            continue
        fetched = fetch_url(url, config)
        raw_meta = write_response(config.raw_dir, source_key=source_key, capability="source_url", url=url, fetched=fetched)
        fetch_record = {
            "url": url,
            "resolved_url": fetched.get("resolved_url", url),
            "ok": bool(fetched.get("ok")),
            "status_code": fetched.get("status_code", 0),
            "content_type": fetched.get("content_type", ""),
            "raw_metadata_path": str(Path(raw_meta["body_path"]).with_name("metadata.json")),
            "row_count": 0,
        }
        if fetched.get("ok"):
            parsed = parse_rows_for_url(
                fetched.get("bytes", b""),
                source=source,
                url=str(fetched.get("resolved_url") or url),
                content_type=str(fetched.get("content_type", "")),
                captured_at=captured_at,
            )
            sitemap_entries, follow_urls = parse_sitemap_entries(fetched.get("bytes", b""))
            for follow in follow_urls:
                if follow not in candidates:
                    candidates.append(follow)
            if sitemap_entries and not parsed:
                for entry in sitemap_entries:
                    if len(rows) >= max_rows or len(fetches) >= max_fetches:
                        break
                    article_url = entry.get("loc", "")
                    if not article_url or not robots_url_allowed(article_url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
                        continue
                    article_fetch = fetch_url(article_url, config)
                    article_meta = write_response(config.raw_dir, source_key=source_key, capability="article_page", url=article_url, fetched=article_fetch)
                    article_record = {
                        "url": article_url,
                        "resolved_url": article_fetch.get("resolved_url", article_url),
                        "ok": bool(article_fetch.get("ok")),
                        "status_code": article_fetch.get("status_code", 0),
                        "content_type": article_fetch.get("content_type", ""),
                        "raw_metadata_path": str(Path(article_meta["body_path"]).with_name("metadata.json")),
                        "row_count": 0,
                    }
                    if article_fetch.get("ok"):
                        metadata = parse_article_metadata(article_fetch.get("bytes", b""))
                        title = metadata.get("title", "")
                        if title:
                            parsed.append(
                                build_row(
                                    source=source,
                                    title=title,
                                    source_url=str(article_fetch.get("resolved_url") or article_url),
                                    published_at=metadata.get("published_at") or entry.get("lastmod", ""),
                                    published_at_text=metadata.get("published_at") or entry.get("lastmod", ""),
                                    captured_at=captured_at,
                                    source_page_url=url,
                                    capture_method="sitemap_article_meta",
                                    title_source=metadata.get("title_source", ""),
                                    published_at_source=metadata.get("published_at_source", "") or ("sitemap_lastmod" if entry.get("lastmod") else ""),
                                )
                            )
                            article_record["row_count"] = 1
                    else:
                        article_record["error_category"] = article_fetch.get("error_category", "")
                        article_record["error_message_redacted"] = article_fetch.get("error_message", "")
                    fetches.append(article_record)
                    time.sleep(max(float(config.request_sleep_seconds), 0.0))
            for row in parsed:
                key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                if key in seen_rows:
                    continue
                seen_rows.add(key)
                rows.append(row)
                if len(rows) >= max_rows:
                    break
            fetch_record["row_count"] = len(parsed)
        else:
            fetch_record["error_category"] = fetched.get("error_category", "")
            fetch_record["error_message_redacted"] = fetched.get("error_message", "")
        fetches.append(fetch_record)
        time.sleep(max(float(config.request_sleep_seconds), 0.0))

    raw_path = write_payload(config, source_key=source_key, captured_at=captured_at, rows=rows, fetches=fetches)
    status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
    if blocked and not rows:
        status = "BLOCKED_ROBOTS"
    if not rows and any(fetch.get("error_category") for fetch in fetches):
        status, _category = classify_news_error(Exception("context source fetch failed"))
    topic_counts: dict[str, int] = {}
    for row in rows:
        for topic in row.get("context_topic_candidates", []):
            topic_counts[str(topic)] = topic_counts.get(str(topic), 0) + 1
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::context_watch",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};fetches={len(fetches)};blocked_robots={blocked};"
            f"collector_version={COLLECTOR_VERSION};ticker_mapping_required=0;"
            f"context_topics={json.dumps(topic_counts, sort_keys=True)}"
        ),
    )


def collect_source_backfill(source: dict[str, Any], config: PublicContextNewsConfig, state: dict[str, Any]) -> dict[str, Any]:
    source_key = str(source.get("source_key"))
    start_date, end_date = backfill_window(config)
    units = context_backfill_units(source_key, start_date, end_date)
    captured_at = now_z()
    backfill_state = state.setdefault("backfill", {}).setdefault(source_key, {})
    completed_units = set(backfill_state.setdefault("completed_units", []))
    page_offsets = backfill_state.setdefault("page_offsets", {})
    unsupported = not units
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    seen_rows = set()
    processed_units: list[str] = []
    max_fetches = max(int(config.max_fetches_per_source), 1)
    max_rows = max(int(config.max_items_per_source), 1)

    for unit in units:
        unit_id = str(unit["unit_id"])
        if unit_id in completed_units:
            continue
        if len(fetches) >= max_fetches or len(rows) >= max_rows:
            break
        if source_key == "federal_register_documents":
            page = int(page_offsets.get(unit_id, 1) or 1)
            while len(fetches) < max_fetches and len(rows) < max_rows:
                parsed_rows, fetch_record, next_page, complete = collect_federal_register_backfill_unit(
                    source,
                    config,
                    unit,
                    page,
                    captured_at,
                )
                fetches.append(fetch_record)
                for row in parsed_rows:
                    key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                    if key in seen_rows:
                        continue
                    seen_rows.add(key)
                    rows.append(row)
                    if len(rows) >= max_rows:
                        break
                if complete:
                    completed_units.add(unit_id)
                    page_offsets.pop(unit_id, None)
                    processed_units.append(unit_id)
                    break
                page_offsets[unit_id] = next_page
                break
        elif source_key == "federal_reserve_press_all":
            parsed_rows, fetch_record, complete = collect_federal_reserve_backfill_unit(
                source,
                config,
                unit,
                captured_at,
                start_date,
                end_date,
            )
            fetches.append(fetch_record)
            for row in parsed_rows:
                key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                if key in seen_rows:
                    continue
                seen_rows.add(key)
                rows.append(row)
                if len(rows) >= max_rows:
                    break
            if complete:
                completed_units.add(unit_id)
                processed_units.append(unit_id)
        elif source_key == "cftc_press_releases":
            page = int(page_offsets.get(unit_id, 1) or 1)
            while len(fetches) < max_fetches and len(rows) < max_rows:
                parsed_rows, fetch_record, next_page, complete = collect_cftc_backfill_unit(
                    source,
                    config,
                    unit,
                    page,
                    captured_at,
                    start_date,
                    end_date,
                )
                fetches.append(fetch_record)
                for row in parsed_rows:
                    key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                    if key in seen_rows:
                        continue
                    seen_rows.add(key)
                    rows.append(row)
                    if len(rows) >= max_rows:
                        break
                if complete:
                    completed_units.add(unit_id)
                    page_offsets.pop(unit_id, None)
                    processed_units.append(unit_id)
                    break
                page_offsets[unit_id] = next_page
                break
        elif source_key == "worldbank_news_api":
            offset = int(page_offsets.get(unit_id, 0) or 0)
            while len(fetches) < max_fetches and len(rows) < max_rows:
                parsed_rows, fetch_record, next_offset, complete = collect_worldbank_news_backfill_unit(
                    source,
                    config,
                    unit,
                    offset,
                    captured_at,
                    start_date,
                    end_date,
                )
                fetches.append(fetch_record)
                for row in parsed_rows:
                    key = row.get("headline_hash") or f"{row.get('title')}|{row.get('source_url')}"
                    if key in seen_rows:
                        continue
                    seen_rows.add(key)
                    rows.append(row)
                    if len(rows) >= max_rows:
                        break
                if complete:
                    completed_units.add(unit_id)
                    page_offsets.pop(unit_id, None)
                    processed_units.append(unit_id)
                    break
                page_offsets[unit_id] = next_offset
                offset = next_offset
                if len(rows) >= max_rows:
                    break
        time.sleep(max(float(config.request_sleep_seconds), 0.0))

    backfill_state["completed_units"] = sorted(completed_units)
    backfill_state["page_offsets"] = page_offsets
    backfill_state["total_units"] = len(units)
    backfill_state["pending_units"] = max(len(units) - len(completed_units), 0)
    backfill_state["start_date"] = start_date.isoformat()
    backfill_state["end_date"] = end_date.isoformat()
    raw_path = write_payload(
        config,
        source_key=source_key,
        captured_at=captured_at,
        rows=rows,
        fetches=fetches,
        collection_mode="historical_backfill",
    )
    if unsupported:
        status = "BACKFILL_UNSUPPORTED"
    elif rows:
        status = "EXPORTED"
    elif len(completed_units) >= len(units):
        status = "BACKFILL_COMPLETE"
    else:
        status = "EMPTY_PROVIDER_RESPONSE"
    return source_event(
        provider=PROVIDER,
        source_id=f"{source_key}::historical_backfill",
        status=status,
        row_count=len(rows),
        raw_path=raw_path,
        l1_rows=rows,
        notes=(
            f"source_key={source_key};mode=historical_backfill;window={start_date.isoformat()}:{end_date.isoformat()};"
            f"units_processed={len(processed_units)};completed_units={len(completed_units)}/{len(units)};"
            f"active_page_offsets={len(page_offsets)};fetches={len(fetches)};"
            f"collector_version={COLLECTOR_VERSION};ticker_mapping_required=0"
        ),
    )


def update_state_for_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    source_id = str(event.get("source_id", ""))
    source_key = source_id.split("::", 1)[0]
    state["processed_events"] = int(state.get("processed_events", 0)) + 1
    status = str(event.get("status", ""))
    if status == "EXPORTED":
        state["exported_events"] = int(state.get("exported_events", 0)) + 1
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


def run_collector(config: PublicContextNewsConfig, *, smoke: bool = False) -> dict[str, Any]:
    sources = selected_sources(config)
    build_plan(config)
    state = load_state(config.state_path)
    processed_this_run = 0
    last_status = "STARTED"
    cycle = 0
    log_line(config.log_path, f"[L0_PUBLIC_CONTEXT_NEWS_START] smoke={int(smoke)} sources={','.join(config.sources)}")
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
    log_line(config.log_path, f"[L0_PUBLIC_CONTEXT_NEWS_EXIT] {json.dumps(result, sort_keys=True)}")
    return result


def run_backfill(config: PublicContextNewsConfig, *, smoke: bool = False) -> dict[str, Any]:
    sources = selected_sources(config)
    build_plan(config)
    state = load_state(config.state_path)
    processed_this_run = 0
    last_status = "STARTED"
    cycle = 0
    log_line(
        config.log_path,
        (
            f"[L0_PUBLIC_CONTEXT_NEWS_BACKFILL_START] smoke={int(smoke)} sources={','.join(config.sources)} "
            f"window={config.backfill_start_date}:{config.backfill_end_date or 'today'}"
        ),
    )
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
    log_line(config.log_path, f"[L0_PUBLIC_CONTEXT_NEWS_BACKFILL_EXIT] {json.dumps(result, sort_keys=True)}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public macro/context news from RSS/API/static public routes.")
    parser.add_argument("--mode", choices=["smoke", "background", "backfill"], default="smoke")
    parser.add_argument("--sources", nargs="+", default=list(DEFAULT_SOURCES))
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--max-items-per-source", type=int, default=25)
    parser.add_argument("--max-fetches-per-source", type=int, default=4)
    parser.add_argument("--cycle-sleep-seconds", type=int, default=1800)
    parser.add_argument("--request-sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-cycles", type=int, default=0)
    parser.add_argument("--max-bytes", type=int, default=3_000_000)
    parser.add_argument("--backfill-start-date", default=DEFAULT_BACKFILL_START_DATE)
    parser.add_argument("--backfill-end-date", default="")
    parser.add_argument("--federal-register-per-page", type=int, default=1000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = PublicContextNewsConfig(
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
        federal_register_per_page=args.federal_register_per_page,
    )
    result = run_backfill(config, smoke=args.mode == "smoke") if args.mode == "backfill" else run_collector(config, smoke=args.mode == "smoke")
    print(
        "[L0_PUBLIC_CONTEXT_NEWS] "
        f"mode={args.mode} sources={','.join(args.sources)} status={result['status']} "
        f"processed_this_run={result['processed_this_run']} event_path={result['event_path']} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
