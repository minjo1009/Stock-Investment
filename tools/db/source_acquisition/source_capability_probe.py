from __future__ import annotations

import argparse
import json
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen


DEFAULT_REGISTRY_PATH = Path("configs/source_registry/l0_public_news_capability_sources.json")
DEFAULT_RAW_DIR = Path("data/raw/l0_source_capability_probe")
DEFAULT_ARTIFACT_DIR = Path("data/artifacts/l0_source_capability_probe")
DEFAULT_SUMMARY_PATH = DEFAULT_ARTIFACT_DIR / "capability_summary.json"
DEFAULT_EVENT_PATH = DEFAULT_ARTIFACT_DIR / "capability_events.jsonl"
PROVIDER = "public_news_source_capability_probe"
PROBE_VERSION = "source_capability_probe.v0.1.0"
USER_AGENT = "Codex-L0-Source-Capability-Probe/1.0 contact=operator"


@dataclass(frozen=True)
class ProbeConfig:
    registry_path: Path = DEFAULT_REGISTRY_PATH
    raw_dir: Path = DEFAULT_RAW_DIR
    summary_path: Path = DEFAULT_SUMMARY_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    source_keys: tuple[str, ...] = ()
    timeout_seconds: int = 30
    max_bytes: int = 2_000_000
    sleep_seconds: float = 0.5


class LinkAndMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.meta: list[dict[str, str]] = []
        self.jsonld: list[str] = []
        self._current_anchor: dict[str, str] | None = None
        self._script_type = ""
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "a":
            self._current_anchor = {"href": values.get("href", ""), "text": ""}
        elif tag.lower() == "link":
            href = values.get("href", "")
            rel = values.get("rel", "")
            typ = values.get("type", "")
            if href:
                self.links.append({"href": href, "text": "", "rel": rel, "type": typ, "tag": "link"})
        elif tag.lower() == "meta":
            self.meta.append(values)
        elif tag.lower() == "script":
            self._script_type = values.get("type", "")
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_anchor is not None:
            self._current_anchor["text"] += data
        if self._script_type.lower() == "application/ld+json":
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current_anchor is not None:
            self._current_anchor["text"] = normalize_text(self._current_anchor.get("text", ""))
            self._current_anchor["tag"] = "a"
            self.links.append(self._current_anchor)
            self._current_anchor = None
        elif tag.lower() == "script" and self._script_type.lower() == "application/ld+json":
            payload = "".join(self._script_parts).strip()
            if payload:
                self.jsonld.append(payload)
            self._script_type = ""
            self._script_parts = []


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.=-]+", "_", value)[:120] or "unknown"


def sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def load_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    sources = payload.get("sources", [])
    return [source for source in sources if isinstance(source, dict)]


def fetch_url(url: str, *, timeout_seconds: int, max_bytes: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml,text/xml,application/rss+xml,application/json,*/*"})
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            payload = response.read(max_bytes + 1)
            truncated = len(payload) > max_bytes
            payload = payload[:max_bytes]
            headers = dict(response.headers.items())
            return {
                "ok": True,
                "url": response.geturl(),
                "status_code": int(response.status),
                "content_type": headers.get("Content-Type", ""),
                "headers": headers,
                "bytes": payload,
                "truncated": truncated,
                "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
                "error_category": "",
                "error_message": "",
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "url": url,
            "status_code": 0,
            "content_type": "",
            "headers": {},
            "bytes": b"",
            "truncated": False,
            "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
            "error_category": type(exc).__name__,
            "error_message": str(exc)[:500],
        }


def write_raw(raw_dir: Path, *, source_key: str, capability: str, url: str, fetched: dict[str, Any]) -> dict[str, Any]:
    captured_at = now_z()
    stamp = captured_at.replace(":", "").replace("-", "").replace(".", "")
    target_dir = raw_dir / f"provider={PROVIDER}" / f"source={safe_name(source_key)}" / f"capability={safe_name(capability)}" / f"captured_at={stamp}"
    target_dir.mkdir(parents=True, exist_ok=True)
    body_path = target_dir / "response.bin"
    meta_path = target_dir / "metadata.json"
    payload = fetched.get("bytes", b"")
    body_path.write_bytes(payload)
    metadata = {
        "schema_version": 1,
        "provider": PROVIDER,
        "source_key": source_key,
        "capability": capability,
        "requested_url": url,
        "resolved_url": fetched.get("url", url),
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
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def parse_html(payload: bytes, base_url: str) -> dict[str, Any]:
    text = payload.decode("utf-8", errors="ignore")
    parser = LinkAndMetaParser()
    parser.feed(text)
    links = []
    for link in parser.links:
        href = link.get("href", "")
        if not href:
            continue
        links.append({**link, "href": urljoin(base_url, href)})
    article_links = [
        link
        for link in links
        if is_probable_article_url(link.get("href", "")) and len(normalize_text(link.get("text", ""))) >= 12
    ]
    feed_links = [
        link
        for link in links
        if looks_like_feed_url(link.get("href", "")) or "rss" in link.get("rel", "").lower() or "atom" in link.get("type", "").lower()
    ]
    sitemap_links = [link for link in links if "sitemap" in link.get("href", "").lower()]
    jsonld_types = []
    for raw in parser.jsonld[:20]:
        for obj in load_jsonld_objects(raw):
            typ = obj.get("@type") if isinstance(obj, dict) else ""
            if isinstance(typ, list):
                jsonld_types.extend(str(item) for item in typ)
            elif typ:
                jsonld_types.append(str(typ))
    meta_names = {str(item.get("property") or item.get("name") or "").lower(): str(item.get("content") or "") for item in parser.meta}
    return {
        "link_count": len(links),
        "article_link_count": len(article_links),
        "article_link_samples": article_links[:10],
        "feed_link_count": len(feed_links),
        "feed_link_samples": feed_links[:10],
        "sitemap_link_count": len(sitemap_links),
        "sitemap_link_samples": sitemap_links[:10],
        "jsonld_count": len(parser.jsonld),
        "jsonld_types": sorted(set(jsonld_types))[:20],
        "has_newsarticle_jsonld": any("NewsArticle" in item or item == "Article" for item in jsonld_types),
        "meta_title": meta_names.get("og:title", "") or meta_names.get("twitter:title", ""),
        "meta_published_time": meta_names.get("article:published_time", ""),
        "has_article_meta": any(key.startswith("article:") for key in meta_names),
    }


def load_jsonld_objects(raw: str) -> list[Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("@graph"), list):
        return [payload, *payload["@graph"]]
    return [payload]


def is_probable_article_url(url: str) -> bool:
    lower = url.lower()
    if any(part in lower for part in ("/news-release/", "/news-releases/", "/press-release/", "/release/")):
        if lower.endswith((".html", ".htm")) or re.search(r"/\d{4}/\d{2}/\d{2}/", lower):
            return True
    return bool(re.search(r"/\d{4}/\d{2}/\d{2}/", lower) and not lower.endswith((".xml", ".rss")))


def looks_like_feed_url(url: str) -> bool:
    lower = url.lower()
    return any(token in lower for token in ("rss", "atom", "feed")) and not lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg"))


def parse_xml_capability(payload: bytes) -> dict[str, Any]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return {"xml_parse_ok": False, "root_tag": "", "feed_item_count": 0, "sitemap_url_count": 0}
    tag = strip_ns(root.tag).lower()
    feed_item_count = 0
    sitemap_url_count = 0
    if tag in {"rss", "rdf"} or tag == "feed":
        feed_item_count = len(root.findall(".//item")) + len([child for child in root.findall(".//{http://www.w3.org/2005/Atom}entry")])
    if tag in {"urlset", "sitemapindex"}:
        sitemap_url_count = len(root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url")) + len(
            root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap")
        )
        if sitemap_url_count == 0:
            sitemap_url_count = len(root.findall(".//url")) + len(root.findall(".//sitemap"))
    return {
        "xml_parse_ok": True,
        "root_tag": tag,
        "feed_item_count": feed_item_count,
        "sitemap_url_count": sitemap_url_count,
    }


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def robots_posture(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    disallows = [line.partition(":")[2].strip() for line in lines if line.lower().startswith("disallow:")]
    sitemaps = [line.partition(":")[2].strip() for line in lines if line.lower().startswith("sitemap:")]
    return {
        "robots_present": bool(text.strip()),
        "disallow_count": len(disallows),
        "sitemap_count": len(sitemaps),
        "sitemap_samples": sitemaps[:10],
        "robots_text_sample": "\n".join(lines[:20]),
    }


def build_robot_parser(origin: str, payload: bytes) -> RobotFileParser:
    parser = RobotFileParser()
    parser.set_url(urljoin(origin + "/", "robots.txt"))
    parser.parse(payload.decode("utf-8", errors="ignore").splitlines())
    return parser


def robots_url_allowed(url: str, *, base_origin: str, robots_present: bool, robot_parser: RobotFileParser) -> bool:
    if not robots_present:
        return True
    if source_origin(url) != base_origin:
        return True
    return bool(robot_parser.can_fetch(USER_AGENT, url))


def robots_skipped_result(url: str, reason: str) -> dict[str, Any]:
    return {
        "url": url,
        "skipped_by_robots": True,
        "skip_reason": reason,
        "xml": {"xml_parse_ok": False, "root_tag": "", "feed_item_count": 0, "sitemap_url_count": 0},
        "html": {},
    }


def source_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def select_recommended_mode(capabilities: dict[str, Any]) -> str:
    if capabilities.get("api", {}).get("ok"):
        return "api_or_official_index"
    if capabilities.get("feed", {}).get("feed_ready"):
        return "rss_or_atom"
    if capabilities.get("sitemap", {}).get("sitemap_ready"):
        return "sitemap_or_news_sitemap"
    if capabilities.get("structured_data", {}).get("jsonld_or_meta_ready"):
        return "jsonld_or_meta"
    if capabilities.get("static_html", {}).get("article_links_ready"):
        return "static_html"
    robots_blocked_machine_route = any(
        item.get("skipped_by_robots")
        for family in ("api", "feed")
        for item in capabilities.get(family, {}).get("results", [])
    )
    if robots_blocked_machine_route:
        return "blocked_or_manual_review"
    if capabilities.get("browser_fallback", {}).get("needed"):
        return "chrome_fallback_probe"
    return "blocked_or_manual_review"


def probe_one(source: dict[str, Any], config: ProbeConfig) -> dict[str, Any]:
    source_key = str(source.get("source_key", "unknown"))
    base_url = str(source.get("base_url") or source.get("probe_url") or "")
    origin = source_origin(base_url)
    raw: dict[str, Any] = {}

    robots_url = urljoin(origin + "/", "robots.txt")
    robots_fetch = fetch_url(robots_url, timeout_seconds=config.timeout_seconds, max_bytes=config.max_bytes)
    raw["robots"] = write_raw(config.raw_dir, source_key=source_key, capability="robots", url=robots_url, fetched=robots_fetch)
    robots = robots_posture(robots_fetch["bytes"]) if robots_fetch["ok"] else {"robots_present": False, "disallow_count": 0, "sitemap_count": 0, "sitemap_samples": []}
    robot_parser = build_robot_parser(origin, robots_fetch["bytes"]) if robots_fetch["ok"] else build_robot_parser(origin, b"")

    feed_results = []
    for url in list(source.get("rss_or_feed_urls", []))[:5]:
        url = str(url)
        if not robots_url_allowed(url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            feed_results.append(robots_skipped_result(url, "robots_disallow"))
            continue
        fetched = fetch_url(str(url), timeout_seconds=config.timeout_seconds, max_bytes=config.max_bytes)
        raw_meta = write_raw(config.raw_dir, source_key=source_key, capability="feed", url=str(url), fetched=fetched)
        xml = parse_xml_capability(fetched["bytes"]) if fetched["ok"] else {"xml_parse_ok": False, "feed_item_count": 0}
        html = parse_html(fetched["bytes"], str(url)) if fetched["ok"] and "html" in str(fetched.get("content_type", "")).lower() else {}
        feed_results.append({"url": str(url), "raw": raw_meta, "xml": xml, "html": html})
        time.sleep(config.sleep_seconds)

    sitemap_urls = [*list(source.get("sitemap_urls", [])), *robots.get("sitemap_samples", [])]
    sitemap_results = []
    for url in sitemap_urls[:5]:
        fetched = fetch_url(str(url), timeout_seconds=config.timeout_seconds, max_bytes=config.max_bytes)
        raw_meta = write_raw(config.raw_dir, source_key=source_key, capability="sitemap", url=str(url), fetched=fetched)
        xml = parse_xml_capability(fetched["bytes"]) if fetched["ok"] else {"xml_parse_ok": False, "sitemap_url_count": 0}
        sitemap_results.append({"url": str(url), "raw": raw_meta, "xml": xml})
        time.sleep(config.sleep_seconds)

    api_results = []
    for url in list(source.get("api_urls", []))[:5]:
        url = str(url)
        if not robots_url_allowed(url, base_origin=origin, robots_present=bool(robots.get("robots_present")), robot_parser=robot_parser):
            api_results.append({"url": url, "ok": False, "status_code": 0, "content_type": "", "skipped_by_robots": True, "skip_reason": "robots_disallow"})
            continue
        fetched = fetch_url(str(url), timeout_seconds=config.timeout_seconds, max_bytes=config.max_bytes)
        raw_meta = write_raw(config.raw_dir, source_key=source_key, capability="api", url=str(url), fetched=fetched)
        api_results.append(
            {
                "url": str(url),
                "raw": raw_meta,
                "ok": bool(fetched.get("ok")),
                "content_type": fetched.get("content_type", ""),
                "status_code": fetched.get("status_code", 0),
            }
        )
        time.sleep(config.sleep_seconds)

    probe_url = str(source.get("probe_url") or base_url)
    page_fetch = fetch_url(probe_url, timeout_seconds=config.timeout_seconds, max_bytes=config.max_bytes)
    page_raw = write_raw(config.raw_dir, source_key=source_key, capability="probe_page", url=probe_url, fetched=page_fetch)
    page_html = parse_html(page_fetch["bytes"], probe_url) if page_fetch["ok"] else {}
    page_xml = parse_xml_capability(page_fetch["bytes"]) if page_fetch["ok"] else {}

    feed_ready = any(item["xml"].get("feed_item_count", 0) > 0 for item in feed_results) or any(
        item.get("html", {}).get("feed_link_count", 0) > 0 for item in feed_results
    ) or any(
        item["xml"].get("root_tag", "") in {"rss", "rdf", "feed"} for item in sitemap_results
    )
    sitemap_ready = any(item["xml"].get("sitemap_url_count", 0) > 0 for item in sitemap_results)
    api_ready = any(item.get("ok") for item in api_results)
    jsonld_ready = bool(page_html.get("has_newsarticle_jsonld") or page_html.get("has_article_meta"))
    static_ready = int(page_html.get("article_link_count", 0) or 0) > 0
    browser_needed = bool(page_fetch.get("ok")) and not any([feed_ready, sitemap_ready, api_ready, jsonld_ready, static_ready])

    capabilities = {
        "robots": robots,
        "api": {"ok": api_ready, "results": api_results},
        "feed": {"feed_ready": feed_ready, "results": compact_feed_results(feed_results)},
        "sitemap": {"sitemap_ready": sitemap_ready, "results": compact_sitemap_results(sitemap_results)},
        "structured_data": {
            "jsonld_or_meta_ready": jsonld_ready,
            "jsonld_count": page_html.get("jsonld_count", 0),
            "jsonld_types": page_html.get("jsonld_types", []),
            "has_article_meta": page_html.get("has_article_meta", False),
        },
        "static_html": {
            "article_links_ready": static_ready,
            "article_link_count": page_html.get("article_link_count", 0),
            "article_link_samples": page_html.get("article_link_samples", []),
            "feed_link_samples": page_html.get("feed_link_samples", []),
        },
        "browser_fallback": {
            "needed": browser_needed,
            "reason": "no machine-readable or static article route found" if browser_needed else "",
        },
        "probe_page": {
            "ok": bool(page_fetch.get("ok")),
            "raw": page_raw,
            "xml": page_xml,
            "content_type": page_fetch.get("content_type", ""),
            "status_code": page_fetch.get("status_code", 0),
        },
    }
    recommended = select_recommended_mode(capabilities)
    return {
        "schema_version": 1,
        "provider": PROVIDER,
        "probe_version": PROBE_VERSION,
        "source_key": source_key,
        "display_name": source.get("display_name", source_key),
        "authority_class": source.get("authority_class", ""),
        "base_url": base_url,
        "probe_url": probe_url,
        "terms_posture": source.get("terms_posture", ""),
        "recommended_capture_mode": recommended,
        "capabilities": capabilities,
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
        "updated_at": now_z(),
    }


def compact_feed_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in results:
        raw = item.get("raw", {})
        out.append(
            {
                "url": item["url"],
                "ok": raw.get("ok", False),
                "status_code": raw.get("status_code", 0),
                "content_type": raw.get("content_type", ""),
                "raw_metadata_path": str(Path(raw["body_path"]).with_name("metadata.json")) if raw.get("body_path") else "",
                "skipped_by_robots": bool(item.get("skipped_by_robots", False)),
                "skip_reason": item.get("skip_reason", ""),
                "xml_parse_ok": item["xml"].get("xml_parse_ok", False),
                "root_tag": item["xml"].get("root_tag", ""),
                "feed_item_count": item["xml"].get("feed_item_count", 0),
                "feed_link_count": item.get("html", {}).get("feed_link_count", 0),
                "feed_link_samples": item.get("html", {}).get("feed_link_samples", [])[:5],
            }
        )
    return out


def compact_sitemap_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in results:
        out.append(
            {
                "url": item["url"],
                "ok": item["raw"].get("ok"),
                "status_code": item["raw"].get("status_code"),
                "content_type": item["raw"].get("content_type"),
                "raw_metadata_path": str(Path(item["raw"]["body_path"]).with_name("metadata.json")),
                "xml_parse_ok": item["xml"].get("xml_parse_ok", False),
                "root_tag": item["xml"].get("root_tag", ""),
                "sitemap_url_count": item["xml"].get("sitemap_url_count", 0),
            }
        )
    return out


def append_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def run_probe(config: ProbeConfig) -> dict[str, Any]:
    sources = load_registry(config.registry_path)
    if config.source_keys:
        wanted = set(config.source_keys)
        sources = [source for source in sources if str(source.get("source_key")) in wanted]
    results = []
    for source in sources:
        result = probe_one(source, config)
        results.append(result)
        append_event(
            config.event_path,
            {
                "provider": PROVIDER,
                "source_family": PROVIDER,
                "source_id": result["source_key"],
                "status": "EXPORTED",
                "row_count": 1,
                "recommended_capture_mode": result["recommended_capture_mode"],
                "updated_at": result["updated_at"],
                "diagnostic_only_flag": 1,
                "trade_authority_flag": 0,
                "broker_mutation_permitted_flag": 0,
                "real_capital_permitted_flag": 0,
            },
        )
    summary = {
        "schema_version": 1,
        "provider": PROVIDER,
        "probe_version": PROBE_VERSION,
        "updated_at": now_z(),
        "registry_path": str(config.registry_path),
        "source_count": len(results),
        "recommended_mode_counts": mode_counts(results),
        "results": results,
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    config.summary_path.parent.mkdir(parents=True, exist_ok=True)
    config.summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def mode_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        mode = str(result.get("recommended_capture_mode", "unknown"))
        counts[mode] = counts.get(mode, 0) + 1
    return dict(sorted(counts.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe public news sources for free L0 capture capabilities.")
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--source-key", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_probe(
        ProbeConfig(
            registry_path=args.registry_path,
            raw_dir=args.raw_dir,
            summary_path=args.summary_path,
            event_path=args.event_path,
            source_keys=tuple(args.source_key or ()),
            timeout_seconds=args.timeout_seconds,
            max_bytes=args.max_bytes,
            sleep_seconds=args.sleep_seconds,
        )
    )
    print(
        "[SOURCE_CAPABILITY_PROBE] "
        f"sources={summary['source_count']} modes={summary['recommended_mode_counts']} "
        f"summary_path={args.summary_path} diagnostic_only=1 trade_authority_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
