from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tools.db.news_l0_l1 import (
    GDELT_COOLDOWN_MINUTES,
    GDELT_MAX_RECORDS,
    GDELT_TIMESPAN_MINUTES,
    MARKETAUX_ARTICLES_PER_REQUEST_LIMIT,
    MARKETAUX_DAILY_REQUEST_LIMIT,
    evaluate_news_l1_row,
    load_marketaux_token,
    marketaux_request_allowed,
    record_marketaux_request,
)
from tools.db.source_acquisition.news_registry_loader import (
    GDELT_REGISTRY_PATH,
    MARKETAUX_REGISTRY_PATH,
    enabled_official_sources,
    load_registry,
)
from tools.db.source_acquisition.secret_redaction import redact_text


DEFAULT_UNIVERSE_PATH = Path("data/raw/alpaca_active_us_equity_universe.csv")
DEFAULT_RAW_DIR = Path("data/raw/l0_news")
DEFAULT_STATE_DIR = Path("data/artifacts/l0_news_background_queue")
DEFAULT_STATE_PATH = DEFAULT_STATE_DIR / "collector_state.json"
DEFAULT_EVENT_PATH = DEFAULT_STATE_DIR / "collector_events.jsonl"
DEFAULT_PROGRESS_PATH = DEFAULT_STATE_DIR / "collector_progress.json"
DEFAULT_STOP_PATH = DEFAULT_STATE_DIR / "STOP"
DEFAULT_LOG_PATH = Path("logs/l0_news_background_collector.log")
SOURCE_FAMILIES = ("official_public_releases", "gdelt_news_events", "marketaux_news_free")


@dataclass(frozen=True)
class NewsCollectorConfig:
    universe_path: Path = DEFAULT_UNIVERSE_PATH
    raw_dir: Path = DEFAULT_RAW_DIR
    state_path: Path = DEFAULT_STATE_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    stop_path: Path = DEFAULT_STOP_PATH
    log_path: Path = DEFAULT_LOG_PATH
    use_full_universe: bool = False
    gdelt_cooldown_minutes: int = GDELT_COOLDOWN_MINUTES
    marketaux_batch_size: int = 5
    max_requests_per_cycle: int = 4
    cycle_sleep_seconds: int = 60
    max_runtime_minutes: int = 0


def load_universe(path: Path = DEFAULT_UNIVERSE_PATH) -> list[str]:
    return [record["symbol"] for record in load_universe_records(path)]


def load_universe_records(path: Path = DEFAULT_UNIVERSE_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    records: dict[str, dict[str, str]] = {}
    for row in rows:
        status = str(row.get("status", "active")).lower()
        tradable = str(row.get("tradable", "true")).lower()
        symbol = str(row.get("symbol", "")).strip().upper()
        if symbol and status == "active" and tradable in {"true", "1", "yes"}:
            records[symbol] = {"symbol": symbol, "name": str(row.get("name", "")).strip()}
    return [records[symbol] for symbol in sorted(records)]


def load_state(config: NewsCollectorConfig, *, universe_count: int) -> dict[str, Any]:
    if config.state_path.exists():
        return json.loads(config.state_path.read_text(encoding="utf-8-sig"))
    return {
        "schema_version": 1,
        "universe_count": universe_count,
        "official_completed_once": False,
        "gdelt_symbol_index": 0,
        "marketaux_symbol_index": 0,
        "marketaux_credential_blocked": False,
        "last_gdelt_request_ts": "",
        "processed_events": 0,
        "exported_events": 0,
        "empty_events": 0,
        "skipped_events": 0,
        "blocked_events": 0,
        "failed_events": 0,
        "updated_at": now_z(),
    }


def save_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_z()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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


def write_progress(path: Path, state: dict[str, Any], extra: dict[str, Any]) -> None:
    payload = dict(state)
    payload.update(extra)
    payload["diagnostic_only_flag"] = 1
    payload["trade_authority_flag"] = 0
    payload["broker_mutation_permitted_flag"] = 0
    payload["real_capital_permitted_flag"] = 0
    payload["updated_at"] = now_z()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def log_line(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{now_z()} {message}\n")


def collect_official(config: NewsCollectorConfig, *, max_sources: int | None = None) -> list[dict[str, Any]]:
    events = []
    for source in enabled_official_sources()[: max_sources or None]:
        source_id = str(source.get("source_id", "unknown"))
        url = str(source.get("url", ""))
        source_type = str(source.get("source_type", ""))
        try:
            content, headers = fetch_bytes(url)
            parsed_rows = parse_official_rows(source, content)
            raw_path = write_raw(
                config.raw_dir,
                provider="official_public_releases",
                key=source_id,
                payload={
                    "source": source,
                    "headers": safe_headers(headers),
                    "parsed_rows": parsed_rows,
                    "raw_text_preview": content[:4096].decode("utf-8", errors="ignore"),
                },
            )
            events.append(
                source_event(
                    provider="official_public_releases",
                    source_id=source_id,
                    status="EXPORTED",
                    row_count=len(parsed_rows),
                    raw_path=raw_path,
                    l1_rows=parsed_rows,
                    notes=f"source_type={source_type}",
                )
            )
        except Exception as exc:  # noqa: BLE001
            events.append(
                source_event(
                    provider="official_public_releases",
                    source_id=source_id,
                    status="FAILED_RETRYABLE",
                    row_count=0,
                    error_category=type(exc).__name__,
                    error_message=str(exc),
                )
            )
    return events


def collect_gdelt(config: NewsCollectorConfig, symbol: str, *, name: str = "") -> dict[str, Any]:
    registry = load_registry(GDELT_REGISTRY_PATH)
    query_text = gdelt_query_text(symbol, name)
    if not query_text:
        return source_event(
            provider="gdelt_news_events",
            source_id=symbol,
            status="SKIPPED_QUERY_TOO_BROAD",
            row_count=0,
            error_category="QUERY_TOO_BROAD",
            error_message=f"Skipped broad GDELT query for symbol={symbol}",
        )
    params = {
        "query": query_text,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(int(registry.get("max_records", GDELT_MAX_RECORDS))),
        "timespan": f"{int(registry.get('timespan_minutes', GDELT_TIMESPAN_MINUTES))}m",
        "sort": "DateDesc",
    }
    endpoint = f"https://api.gdeltproject.org/api/v2/doc/doc?{urlencode(params)}"
    try:
        payload = fetch_json(endpoint)
        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        rows = [
            {
                "provider": "gdelt_news_events",
                "published_at": article.get("seendate") or article.get("date") or "",
                "source_url": article.get("url") or "",
                "title": article.get("title") or "",
                "symbols": [symbol],
            }
            for article in articles
            if isinstance(article, dict)
        ]
        raw_path = write_raw(config.raw_dir, provider="gdelt_news_events", key=symbol, payload={"symbol": symbol, "query": query_text, "payload": payload})
        status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
        return source_event(provider="gdelt_news_events", source_id=symbol, status=status, row_count=len(rows), raw_path=raw_path, l1_rows=rows)
    except Exception as exc:  # noqa: BLE001
        status, category = classify_news_error(exc)
        return source_event(
            provider="gdelt_news_events",
            source_id=symbol,
            status=status,
            row_count=0,
            error_category=category,
            error_message=str(exc),
        )


def gdelt_query_text(symbol: str, name: str = "") -> str:
    clean_name = re.sub(r"\b(Inc|Inc\.|Corp|Corp\.|Corporation|Co|Co\.|Ltd|Ltd\.|PLC|ADR|Class [A-Z])\b", "", name, flags=re.IGNORECASE)
    clean_name = re.sub(r"[^A-Za-z0-9 &.-]+", " ", clean_name)
    clean_name = re.sub(r"\s+\.", " ", clean_name)
    clean_name = clean_name.strip(" .")
    clean_name = re.sub(r"\s+", " ", clean_name).strip()
    if len(clean_name) >= 5:
        return f'"{clean_name}"'
    if len(symbol.strip()) >= 5:
        return f'"{symbol.strip().upper()}"'
    return ""


def collect_marketaux(config: NewsCollectorConfig, symbols: list[str]) -> dict[str, Any]:
    token = load_marketaux_token()
    if not token:
        return source_event(
            provider="marketaux_news_free",
            source_id=",".join(symbols),
            status="CREDENTIAL_BLOCKED",
            row_count=0,
            error_category="CREDENTIAL_BLOCKED",
            error_message="Marketaux token missing from operator environment or configs/local/marketaux.env",
        )
    registry = load_registry(MARKETAUX_REGISTRY_PATH)
    daily_cap = int(registry.get("daily_request_cap", MARKETAUX_DAILY_REQUEST_LIMIT))
    if not marketaux_request_allowed(daily_limit=daily_cap):
        return source_event(
            provider="marketaux_news_free",
            source_id=",".join(symbols),
            status="RATE_LIMITED",
            row_count=0,
            error_category="DAILY_REQUEST_CAP_REACHED",
            error_message="Marketaux daily request cap reached",
        )
    params = {
        "symbols": ",".join(symbols),
        "limit": str(min(int(registry.get("articles_per_request", MARKETAUX_ARTICLES_PER_REQUEST_LIMIT)), MARKETAUX_ARTICLES_PER_REQUEST_LIMIT)),
        "language": "en",
        "api_token": token,
    }
    endpoint = f"https://api.marketaux.com/v1/news/all?{urlencode(params)}"
    try:
        payload = fetch_json(endpoint)
        record_marketaux_request(request_count=1)
        articles = payload.get("data", []) if isinstance(payload, dict) else []
        rows = [
            {
                "provider": "marketaux_news_free",
                "published_at": article.get("published_at") or "",
                "source_url": article.get("url") or "",
                "title": article.get("title") or "",
                "symbols": symbols,
            }
            for article in articles
            if isinstance(article, dict)
        ]
        raw_path = write_raw(config.raw_dir, provider="marketaux_news_free", key="-".join(symbols), payload={"symbols": symbols, "payload": payload})
        status = "EXPORTED" if rows else "EMPTY_PROVIDER_RESPONSE"
        return source_event(provider="marketaux_news_free", source_id=",".join(symbols), status=status, row_count=len(rows), raw_path=raw_path, l1_rows=rows)
    except Exception as exc:  # noqa: BLE001
        status, category = classify_news_error(exc)
        return source_event(
            provider="marketaux_news_free",
            source_id=",".join(symbols),
            status=status,
            row_count=0,
            error_category=category,
            error_message=str(exc),
        )


def fetch_bytes(url: str) -> tuple[bytes, dict[str, str]]:
    request = Request(url, headers={"User-Agent": "Codex-L0-Source-Acquisition/1.0"})
    with urlopen(request, timeout=45) as response:  # noqa: S310
        return response.read(), dict(response.headers.items())


def fetch_json(url: str) -> Any:
    data, _headers = fetch_bytes(url)
    return json.loads(data.decode("utf-8"))


def safe_headers(headers: dict[str, str]) -> dict[str, str]:
    safe = {}
    for key, value in headers.items():
        lower = key.lower()
        if any(term in lower for term in ("token", "key", "secret", "authorization", "cookie")):
            safe[key] = "***REDACTED***"
        else:
            safe[key] = redact_text(value)
    return safe


def parse_official_rows(source: dict[str, Any], content: bytes) -> list[dict[str, Any]]:
    source_type = str(source.get("source_type", ""))
    if source_type == "rss":
        return parse_rss_rows(source, content)
    text = content.decode("utf-8", errors="ignore")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else str(source.get("name", "Official source captured"))
    return [
        {
            "provider": "official_public_releases",
            "published_at": now_z(),
            "source_url": source.get("url", ""),
            "title": title,
            "symbols": source.get("symbol_scope") or source.get("macro_scope") or ["MACRO"],
        }
    ]


def parse_rss_rows(source: dict[str, Any], content: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(content)
    rows = []
    for item in root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = first_text(item, ("title", "{http://www.w3.org/2005/Atom}title"))
        published = first_text(item, ("pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}updated"))
        link = first_text(item, ("link", "{http://www.w3.org/2005/Atom}link"))
        if not link:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            link = "" if atom_link is None else str(atom_link.attrib.get("href", ""))
        rows.append(
            {
                "provider": "official_public_releases",
                "published_at": published or now_z(),
                "source_url": link or source.get("url", ""),
                "title": title,
                "symbols": source.get("symbol_scope") or source.get("macro_scope") or ["MACRO"],
            }
        )
    return rows


def first_text(item: ET.Element, names: tuple[str, ...]) -> str:
    for name in names:
        child = item.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def write_raw(raw_dir: Path, *, provider: str, key: str, payload: dict[str, Any]) -> Path:
    stamp = now_z().replace(":", "").replace("-", "")
    safe_key = re.sub(r"[^A-Za-z0-9_.=-]+", "_", key)[:120] or "unknown"
    path = raw_dir / f"provider={provider}" / f"key={safe_key}" / f"collected_at={stamp}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def source_event(
    *,
    provider: str,
    source_id: str,
    status: str,
    row_count: int,
    raw_path: Path | str = "",
    l1_rows: list[dict[str, Any]] | None = None,
    error_category: str = "",
    error_message: str = "",
    notes: str = "",
) -> dict[str, Any]:
    l1_rows = l1_rows or []
    l1_evals = [evaluate_news_l1_row(row).as_dict() for row in l1_rows]
    return {
        "provider": provider,
        "source_family": provider,
        "source_id": source_id,
        "status": status,
        "row_count": int(row_count),
        "raw_path": str(raw_path),
        "raw_sha256": sha256_file(Path(raw_path)) if raw_path else "",
        "l1_ready_discovery_only_count": sum(1 for row in l1_evals if row.get("promotion_status") == "READY_DISCOVERY_ONLY"),
        "l1_ready_diagnostic_only_count": sum(1 for row in l1_evals if row.get("promotion_status") == "READY_DIAGNOSTIC_ONLY"),
        "l1_context_ready_count": sum(
            1
            for row in l1_rows
            if row.get("macro_context_candidate_flag") in (1, "1", True) or row.get("ticker_mapping_required_flag") in (0, "0", False)
        ),
        "newswire_recall_review_rows": sum(1 for row in l1_rows if row.get("newswire_recall_review_flag") in (1, "1", True)),
        "entity_candidate_review_rows": sum(1 for row in l1_rows if row.get("entity_mapping_status") == "ENTITY_CANDIDATE_REVIEW"),
        "l1_blocked_count": sum(1 for row in l1_evals if row.get("promotion_status") == "BLOCKED"),
        "error_category": error_category,
        "error_message_redacted": redact_text(error_message),
        "secret_logged_flag": 0,
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
        "notes": notes,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_news_error(exc: Exception) -> tuple[str, str]:
    code = exc.code if isinstance(exc, HTTPError) else None
    text = str(exc).lower()
    if code == 429 or "rate" in text:
        return "RATE_LIMITED", "RATE_LIMITED"
    if code in {401, 403} or "token" in text or "credential" in text or "subscription" in text:
        return "CREDENTIAL_BLOCKED", "CREDENTIAL_BLOCKED"
    if code == 402 or "usage" in text:
        return "RATE_LIMITED", "USAGE_LIMIT_REACHED"
    return "FAILED_RETRYABLE", type(exc).__name__


def gdelt_cooldown_ready(state: dict[str, Any], cooldown_minutes: int) -> bool:
    last = str(state.get("last_gdelt_request_ts", ""))
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(UTC) - last_dt).total_seconds() >= cooldown_minutes * 60


def next_batch(symbols: list[str], start: int, batch_size: int) -> tuple[list[str], int]:
    if not symbols:
        return [], 0
    start = start % len(symbols)
    end = min(start + max(int(batch_size), 1), len(symbols))
    batch = symbols[start:end]
    next_index = 0 if end >= len(symbols) else end
    return batch, next_index


def run_news_collector(config: NewsCollectorConfig) -> dict[str, Any]:
    universe_records = load_universe_records(config.universe_path) if config.use_full_universe else []
    symbols = [record["symbol"] for record in universe_records]
    names = {record["symbol"]: record.get("name", "") for record in universe_records}
    if not symbols:
        marketaux_registry = load_registry(MARKETAUX_REGISTRY_PATH)
        symbols = sorted({symbol for query in marketaux_registry.get("queries", []) for symbol in query.get("symbols", [])})
        names = {symbol: "" for symbol in symbols}
    state = load_state(config, universe_count=len(symbols))
    started = time.monotonic()
    processed_this_run = 0
    last_status = "STARTED"
    log_line(config.log_path, f"[NEWS_COLLECTOR_START] use_full_universe={int(config.use_full_universe)} symbols={len(symbols)}")
    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        if config.max_runtime_minutes and (time.monotonic() - started) >= config.max_runtime_minutes * 60:
            last_status = "MAX_RUNTIME_REACHED"
            break
        cycle_events: list[dict[str, Any]] = []
        if not state.get("official_completed_once"):
            cycle_events.extend(collect_official(config))
            state["official_completed_once"] = True
        if len(cycle_events) < config.max_requests_per_cycle and gdelt_cooldown_ready(state, config.gdelt_cooldown_minutes) and symbols:
            symbol = symbols[int(state.get("gdelt_symbol_index", 0)) % len(symbols)]
            cycle_events.append(collect_gdelt(config, symbol, name=names.get(symbol, "")))
            state["gdelt_symbol_index"] = (int(state.get("gdelt_symbol_index", 0)) + 1) % len(symbols)
            state["last_gdelt_request_ts"] = now_z()
        if len(cycle_events) < config.max_requests_per_cycle and symbols and not state.get("marketaux_credential_blocked"):
            batch, next_index = next_batch(symbols, int(state.get("marketaux_symbol_index", 0)), config.marketaux_batch_size)
            if batch:
                cycle_events.append(collect_marketaux(config, batch))
                state["marketaux_symbol_index"] = next_index
        for event in cycle_events:
            append_event(config.event_path, event)
            state["processed_events"] = int(state.get("processed_events", 0)) + 1
            processed_this_run += 1
            if event["status"] == "EXPORTED":
                state["exported_events"] = int(state.get("exported_events", 0)) + 1
            elif event["status"] == "EMPTY_PROVIDER_RESPONSE":
                state["empty_events"] = int(state.get("empty_events", 0)) + 1
            elif event["status"] == "CREDENTIAL_BLOCKED":
                state["blocked_events"] = int(state.get("blocked_events", 0)) + 1
                if event.get("provider") == "marketaux_news_free":
                    state["marketaux_credential_blocked"] = True
            elif str(event["status"]).startswith("SKIPPED"):
                state["skipped_events"] = int(state.get("skipped_events", 0)) + 1
            elif event["status"] not in {"SKIPPED_EXISTS"}:
                state["failed_events"] = int(state.get("failed_events", 0)) + 1
            last_status = str(event["status"])
        save_state(config.state_path, state)
        write_progress(
            config.progress_path,
            state,
            {
                "last_status": last_status,
                "processed_this_run": processed_this_run,
                "source_families": list(SOURCE_FAMILIES),
            },
        )
        if config.max_runtime_minutes == 0:
            time.sleep(max(int(config.cycle_sleep_seconds), 1))
            continue
        if not cycle_events:
            time.sleep(max(int(config.cycle_sleep_seconds), 1))
            continue
    result = {
        "status": last_status,
        "processed_this_run": processed_this_run,
        "state_path": str(config.state_path),
        "event_path": str(config.event_path),
        "progress_path": str(config.progress_path),
    }
    write_progress(config.progress_path, state, result)
    log_line(config.log_path, f"[NEWS_COLLECTOR_EXIT] {json.dumps(result, sort_keys=True)}")
    return result
