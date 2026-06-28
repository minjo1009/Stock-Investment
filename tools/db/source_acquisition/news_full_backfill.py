from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tools.db.news_l0_l1 import (
    MARKETAUX_ARTICLES_PER_REQUEST_LIMIT,
    MARKETAUX_DAILY_REQUEST_LIMIT,
    load_marketaux_token,
    marketaux_request_allowed,
    record_marketaux_request,
)
from tools.db.source_acquisition.news_background_collector import (
    collect_official,
    classify_news_error,
    load_universe_records,
    now_z,
    sha256_file,
    source_event,
    write_progress,
)
from tools.db.source_acquisition.news_registry_loader import MARKETAUX_REGISTRY_PATH, enabled_official_sources, load_registry
from tools.db.source_acquisition.secret_redaction import redact_text


DEFAULT_RAW_DIR = Path("data/raw/l0_news_full_backfill")
DEFAULT_STATE_DIR = Path("data/artifacts/l0_news_full_backfill")
DEFAULT_STATE_PATH = DEFAULT_STATE_DIR / "collector_state.json"
DEFAULT_EVENT_PATH = DEFAULT_STATE_DIR / "collector_events.jsonl"
DEFAULT_PROGRESS_PATH = DEFAULT_STATE_DIR / "collector_progress.json"
DEFAULT_STOP_PATH = DEFAULT_STATE_DIR / "STOP"
DEFAULT_PLAN_PATH = DEFAULT_STATE_DIR / "full_backfill_plan.json"
DEFAULT_OFFICIAL_BLOCKERS_PATH = DEFAULT_STATE_DIR / "official_endpoint_missing_universe.csv"
DEFAULT_LOG_PATH = Path("logs/l0_news_full_backfill_collector.log")
DEFAULT_UNIVERSE_PATH = Path("data/raw/alpaca_active_us_equity_universe.csv")
GDELT_ARCHIVE_BASE_URL = "http://data.gdeltproject.org/gdeltv2"
GDELT_START_TS = "20160101000000"
SOURCE_NAMES = ("official", "gdelt", "marketaux")


@dataclass(frozen=True)
class NewsFullBackfillConfig:
    universe_path: Path = DEFAULT_UNIVERSE_PATH
    raw_dir: Path = DEFAULT_RAW_DIR
    state_path: Path = DEFAULT_STATE_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    stop_path: Path = DEFAULT_STOP_PATH
    plan_path: Path = DEFAULT_PLAN_PATH
    official_blockers_path: Path = DEFAULT_OFFICIAL_BLOCKERS_PATH
    log_path: Path = DEFAULT_LOG_PATH
    start_date: str = "2016-01-01"
    end_date: str = ""
    sources: tuple[str, ...] = SOURCE_NAMES
    gdelt_start_ts: str = GDELT_START_TS
    gdelt_requests_per_minute: int = 12
    marketaux_daily_cap: int = MARKETAUX_DAILY_REQUEST_LIMIT
    marketaux_batch_size: int = 5
    marketaux_window_days: int = 366
    marketaux_limit: int = MARKETAUX_ARTICLES_PER_REQUEST_LIMIT
    official_refresh_hours: int = 24
    max_requests: int = 0
    max_runtime_minutes: int = 0
    cycle_sleep_seconds: int = 30


def resolved_end_date(config: NewsFullBackfillConfig) -> str:
    if config.end_date:
        return config.end_date
    return datetime.now(UTC).date().isoformat()


def load_state(config: NewsFullBackfillConfig, *, universe_count: int) -> dict[str, Any]:
    if config.state_path.exists():
        return json.loads(config.state_path.read_text(encoding="utf-8-sig"))
    return {
        "schema_version": 1,
        "start_date": config.start_date,
        "end_date": resolved_end_date(config),
        "universe_count": universe_count,
        "official_done": False,
        "last_official_run_ts": "",
        "gdelt_cursor_ts": config.gdelt_start_ts,
        "marketaux_symbol_index": 0,
        "marketaux_window_start": config.start_date,
        "marketaux_page": 1,
        "marketaux_credential_blocked": False,
        "processed_events": 0,
        "exported_events": 0,
        "skipped_events": 0,
        "empty_events": 0,
        "blocked_events": 0,
        "failed_events": 0,
        "updated_at": now_z(),
    }


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


def build_plan(config: NewsFullBackfillConfig) -> dict[str, Any]:
    universe = load_universe_records(config.universe_path)
    official_sources = enabled_official_sources()
    covered_symbols = {
        str(symbol).upper()
        for source in official_sources
        for symbol in source.get("symbol_scope", [])
        if str(symbol).strip()
    }
    missing_official = [record for record in universe if record["symbol"] not in covered_symbols]
    write_official_blockers(config.official_blockers_path, missing_official)
    start = date.fromisoformat(config.start_date)
    end = date.fromisoformat(resolved_end_date(config))
    gdelt_intervals = max(int(((end - start).days + 1) * 96), 0)
    marketaux_batches = (len(universe) + max(config.marketaux_batch_size, 1) - 1) // max(config.marketaux_batch_size, 1)
    marketaux_windows = max(((end - start).days + max(config.marketaux_window_days, 1)) // max(config.marketaux_window_days, 1), 1)
    plan = {
        "created_at": now_z(),
        "start_date": config.start_date,
        "end_date": end.isoformat(),
        "universe_count": len(universe),
        "sources": {
            "official_public_releases": {
                "mode": "registry_endpoint_capture",
                "known_enabled_source_count": len(official_sources),
                "symbols_with_known_official_endpoint": len(covered_symbols),
                "symbols_missing_official_endpoint": len(missing_official),
                "blocker_path": str(config.official_blockers_path),
                "historical_2016_full_depth_status": "BLOCKED_UNLESS_OFFICIAL_ARCHIVE_ENDPOINT_EXISTS",
            },
            "gdelt_news_events": {
                "mode": "gdelt_v2_15min_archive_download",
                "archive_base_url": GDELT_ARCHIVE_BASE_URL,
                "source_kind": "export.CSV.zip",
                "estimated_15min_files": gdelt_intervals,
                "requests_per_minute_cap": config.gdelt_requests_per_minute,
                "notes": "Covers global GDELT event archive; ticker/entity mapping remains downstream discovery metadata.",
            },
            "marketaux_news_free": {
                "mode": "symbol_batch_year_window_pagination",
                "estimated_symbol_batches": marketaux_batches,
                "estimated_year_windows": marketaux_windows,
                "daily_request_cap": config.marketaux_daily_cap,
                "articles_per_request": min(config.marketaux_limit, MARKETAUX_ARTICLES_PER_REQUEST_LIMIT),
                "credential_present": bool(load_marketaux_token()),
            },
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


def write_official_blockers(path: Path, missing_records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "name", "missing_reason"])
        writer.writeheader()
        for record in missing_records:
            writer.writerow(
                {
                    "symbol": record.get("symbol", ""),
                    "name": record.get("name", ""),
                    "missing_reason": "OFFICIAL_ENDPOINT_NOT_VERIFIED_NOT_APPROXIMATED",
                }
            )


def gdelt_raw_path(raw_dir: Path, ts: str) -> Path:
    return raw_dir / "provider=gdelt_news_events" / f"year={ts[:4]}" / f"month={ts[4:6]}" / f"{ts}.export.CSV.zip"


def gdelt_url(ts: str) -> str:
    return f"{GDELT_ARCHIVE_BASE_URL}/{ts}.export.CSV.zip"


def next_gdelt_ts(ts: str) -> str:
    value = datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    return (value + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")


def collect_gdelt_archive_chunk(config: NewsFullBackfillConfig, ts: str) -> dict[str, Any]:
    raw_path = gdelt_raw_path(config.raw_dir, ts)
    if raw_path.exists():
        return source_event(provider="gdelt_news_events", source_id=ts, status="SKIPPED_EXISTS", row_count=0, raw_path=raw_path)
    url = gdelt_url(ts)
    try:
        request = Request(url, headers={"User-Agent": "Codex-L0-Source-Acquisition/1.0"})
        with urlopen(request, timeout=90) as response:  # noqa: S310
            payload = response.read()
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(payload)
        return source_event(
            provider="gdelt_news_events",
            source_id=ts,
            status="EXPORTED",
            row_count=0,
            raw_path=raw_path,
            notes="gdelt_v2_export_archive_zip",
        )
    except HTTPError as exc:
        status, category = classify_news_error(exc)
        if exc.code == 404:
            status, category = "EMPTY_PROVIDER_RESPONSE", "ARCHIVE_FILE_NOT_FOUND"
        return source_event(provider="gdelt_news_events", source_id=ts, status=status, row_count=0, error_category=category, error_message=str(exc))
    except Exception as exc:  # noqa: BLE001
        status, category = classify_news_error(exc)
        return source_event(provider="gdelt_news_events", source_id=ts, status=status, row_count=0, error_category=category, error_message=str(exc))


def official_due(state: dict[str, Any], config: NewsFullBackfillConfig) -> bool:
    last = str(state.get("last_official_run_ts", ""))
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(UTC) - last_dt).total_seconds() >= max(int(config.official_refresh_hours), 1) * 3600


def marketaux_window_end(start_date: str, *, days: int, max_end: str) -> str:
    start = date.fromisoformat(start_date)
    end = min(start + timedelta(days=max(int(days), 1)), date.fromisoformat(max_end))
    return end.isoformat()


def advance_marketaux_window(state: dict[str, Any], config: NewsFullBackfillConfig, *, universe_count: int, has_more: bool) -> None:
    if has_more:
        state["marketaux_page"] = int(state.get("marketaux_page", 1)) + 1
        return
    state["marketaux_page"] = 1
    next_symbol_index = int(state.get("marketaux_symbol_index", 0)) + max(int(config.marketaux_batch_size), 1)
    if next_symbol_index < universe_count:
        state["marketaux_symbol_index"] = next_symbol_index
        return
    state["marketaux_symbol_index"] = 0
    next_start = date.fromisoformat(str(state.get("marketaux_window_start", config.start_date))) + timedelta(days=max(int(config.marketaux_window_days), 1))
    state["marketaux_window_start"] = next_start.isoformat()


def collect_marketaux_window(config: NewsFullBackfillConfig, symbols: list[str], *, window_start: str, window_end: str, page: int) -> tuple[dict[str, Any], bool]:
    token = load_marketaux_token()
    source_id = f"{','.join(symbols)}::{window_start}::{window_end}::page={page}"
    if not token:
        return (
            source_event(
                provider="marketaux_news_free",
                source_id=source_id,
                status="CREDENTIAL_BLOCKED",
                row_count=0,
                error_category="CREDENTIAL_BLOCKED",
                error_message="Marketaux token missing from operator environment or configs/local/marketaux.env",
            ),
            False,
        )
    registry = load_registry(MARKETAUX_REGISTRY_PATH)
    daily_cap = int(config.marketaux_daily_cap or registry.get("daily_request_cap", MARKETAUX_DAILY_REQUEST_LIMIT))
    if not marketaux_request_allowed(daily_limit=daily_cap):
        return (
            source_event(
                provider="marketaux_news_free",
                source_id=source_id,
                status="RATE_LIMITED",
                row_count=0,
                error_category="DAILY_REQUEST_CAP_REACHED",
                error_message="Marketaux daily request cap reached",
            ),
            True,
        )
    limit = min(int(config.marketaux_limit), MARKETAUX_ARTICLES_PER_REQUEST_LIMIT)
    params = {
        "symbols": ",".join(symbols),
        "filter_entities": "true",
        "language": "en",
        "published_after": window_start,
        "published_before": window_end,
        "sort": "published_at",
        "limit": str(limit),
        "page": str(page),
        "api_token": token,
    }
    endpoint = f"https://api.marketaux.com/v1/news/all?{urlencode(params)}"
    try:
        request = Request(endpoint, headers={"User-Agent": "Codex-L0-Source-Acquisition/1.0"})
        with urlopen(request, timeout=60) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        record_marketaux_request(request_count=1)
        returned = int(payload.get("meta", {}).get("returned", len(payload.get("data", []))))
        raw_path = marketaux_raw_path(config.raw_dir, symbols=symbols, window_start=window_start, window_end=window_end, page=page)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps({"symbols": symbols, "window_start": window_start, "window_end": window_end, "page": page, "payload": payload}, indent=2, sort_keys=True), encoding="utf-8")
        has_more = returned >= limit
        status = "EXPORTED" if returned > 0 else "EMPTY_PROVIDER_RESPONSE"
        return (
            source_event(provider="marketaux_news_free", source_id=source_id, status=status, row_count=returned, raw_path=raw_path),
            has_more,
        )
    except Exception as exc:  # noqa: BLE001
        status, category = classify_news_error(exc)
        return (
            source_event(
                provider="marketaux_news_free",
                source_id=source_id,
                status=status,
                row_count=0,
                error_category=category,
                error_message=redact_text(str(exc)),
            ),
            status == "RATE_LIMITED",
        )


def marketaux_raw_path(raw_dir: Path, *, symbols: list[str], window_start: str, window_end: str, page: int) -> Path:
    key = "-".join(symbols[:5])
    return raw_dir / "provider=marketaux_news_free" / f"symbols={key}" / f"window={window_start}_{window_end}" / f"page={page}.json"


def run_full_backfill(config: NewsFullBackfillConfig, *, smoke: bool = False) -> dict[str, Any]:
    plan = build_plan(config)
    universe = load_universe_records(config.universe_path)
    symbols = [record["symbol"] for record in universe]
    state = load_state(config, universe_count=len(universe))
    started = time.monotonic()
    processed_this_run = 0
    last_status = "STARTED"
    log_line(config.log_path, f"[L0_NEWS_FULL_BACKFILL_START] smoke={int(smoke)} sources={','.join(config.sources)}")
    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        if config.max_requests and processed_this_run >= config.max_requests:
            last_status = "MAX_REQUESTS_REACHED"
            break
        if config.max_runtime_minutes and (time.monotonic() - started) >= config.max_runtime_minutes * 60:
            last_status = "MAX_RUNTIME_REACHED"
            break
        events: list[dict[str, Any]] = []
        if "official" in config.sources and official_due(state, config):
            official_events = collect_official(config, max_sources=1 if smoke else None)
            events.extend(official_events)
            if official_events:
                state["official_done"] = True
                state["last_official_run_ts"] = now_z()
        if "gdelt" in config.sources and len(events) + processed_this_run < (config.max_requests or 10**12):
            ts = str(state.get("gdelt_cursor_ts", config.gdelt_start_ts))
            events.append(collect_gdelt_archive_chunk(config, ts))
            state["gdelt_cursor_ts"] = next_gdelt_ts(ts)
        if "marketaux" in config.sources and not state.get("marketaux_credential_blocked") and symbols and len(events) + processed_this_run < (config.max_requests or 10**12):
            today = datetime.now(UTC).date().isoformat()
            if state.get("marketaux_daily_cap_exhausted_date") == today:
                pass
            else:
                start_idx = int(state.get("marketaux_symbol_index", 0)) % len(symbols)
                batch = symbols[start_idx : start_idx + max(int(config.marketaux_batch_size), 1)]
                window_start = str(state.get("marketaux_window_start", config.start_date))
                window_end = marketaux_window_end(window_start, days=config.marketaux_window_days, max_end=resolved_end_date(config))
                page = int(state.get("marketaux_page", 1))
                marketaux_event, has_more = collect_marketaux_window(config, batch, window_start=window_start, window_end=window_end, page=page)
                events.append(marketaux_event)
                if marketaux_event["status"] == "CREDENTIAL_BLOCKED":
                    state["marketaux_credential_blocked"] = True
                elif marketaux_event["status"] == "RATE_LIMITED" and marketaux_event.get("error_category") == "DAILY_REQUEST_CAP_REACHED":
                    state["marketaux_daily_cap_exhausted_date"] = today
                elif marketaux_event["status"] != "RATE_LIMITED":
                    state.pop("marketaux_daily_cap_exhausted_date", None)
                    advance_marketaux_window(state, config, universe_count=len(symbols), has_more=has_more)
        if not events:
            time.sleep(max(int(config.cycle_sleep_seconds), 1))
            continue
        for event in events:
            append_event(config.event_path, event)
            processed_this_run += 1
            state["processed_events"] = int(state.get("processed_events", 0)) + 1
            status = str(event.get("status", ""))
            last_status = status
            if status == "EXPORTED":
                state["exported_events"] = int(state.get("exported_events", 0)) + 1
            elif status == "EMPTY_PROVIDER_RESPONSE":
                state["empty_events"] = int(state.get("empty_events", 0)) + 1
            elif status == "CREDENTIAL_BLOCKED":
                state["blocked_events"] = int(state.get("blocked_events", 0)) + 1
            elif status.startswith("SKIPPED"):
                state["skipped_events"] = int(state.get("skipped_events", 0)) + 1
            else:
                state["failed_events"] = int(state.get("failed_events", 0)) + 1
        save_state(config.state_path, state)
        write_progress(
            config.progress_path,
            state,
            {
                "last_status": last_status,
                "processed_this_run": processed_this_run,
                "plan_path": str(config.plan_path),
                "official_blockers_path": str(config.official_blockers_path),
            },
        )
        if smoke:
            break
        time.sleep(60.0 / max(int(config.gdelt_requests_per_minute), 1))
    result = {
        "status": last_status,
        "processed_this_run": processed_this_run,
        "state_path": str(config.state_path),
        "event_path": str(config.event_path),
        "progress_path": str(config.progress_path),
        "plan_path": str(config.plan_path),
        "official_blockers_path": str(config.official_blockers_path),
        "permissions_closed": True,
    }
    write_progress(config.progress_path, state, result)
    log_line(config.log_path, f"[L0_NEWS_FULL_BACKFILL_EXIT] {json.dumps(result, sort_keys=True)}")
    return result
