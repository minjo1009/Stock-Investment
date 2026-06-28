from __future__ import annotations

import json
import sqlite3
import subprocess
import glob
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


DEFAULT_STATUS_DIR = Path("data/artifacts/l0_collection_status")
DEFAULT_STATUS_JSON = DEFAULT_STATUS_DIR / "current_status.json"
DEFAULT_STATUS_MD = DEFAULT_STATUS_DIR / "current_status.md"
DEFAULT_DAILY_PROGRESS = Path("data/artifacts/l0_bar_daily_full_backfill/collector_progress.json")
DEFAULT_FIVE_MIN_PROGRESS = Path("data/artifacts/l0_bar_full_backfill/collector_progress.json")
DEFAULT_NEWS_PROGRESS = Path("data/artifacts/l0_news_full_backfill/collector_progress.json")
DEFAULT_NEWS_PLAN = Path("data/artifacts/l0_news_full_backfill/full_backfill_plan.json")
DEFAULT_NEWS_STATE = Path("data/artifacts/l0_news_full_backfill/collector_state.json")
DEFAULT_NEWS_EVENTS = Path("data/artifacts/l0_news_full_backfill/collector_events.jsonl")
DEFAULT_REFERENCE_PROGRESS = Path("data/artifacts/l0_reference_snapshot/collector_progress.json")
DEFAULT_TICK_PROGRESS = Path("data/artifacts/microstructure_backfill_queue_15m/collector_progress.json")
DEFAULT_DAILY_BACKGROUND = Path("data/artifacts/l0_bar_daily_full_backfill/background_process.json")
DEFAULT_FIVE_MIN_BACKGROUND = Path("data/artifacts/l0_bar_full_backfill/background_process_5m.json")
DEFAULT_NEWS_BACKGROUND = Path("data/artifacts/l0_news_full_backfill/background_process.json")
DEFAULT_PUBLIC_NEWSWIRE_PROGRESS = Path("data/artifacts/l0_public_newswire/collector_progress.json")
DEFAULT_PUBLIC_NEWSWIRE_PLAN = Path("data/artifacts/l0_public_newswire/collection_plan.json")
DEFAULT_PUBLIC_NEWSWIRE_EVENTS = Path("data/artifacts/l0_public_newswire/collector_events.jsonl")
DEFAULT_PUBLIC_NEWSWIRE_BACKGROUND = Path("data/artifacts/l0_public_newswire/background_process.json")
DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_PROGRESS = Path("data/artifacts/l0_public_newswire_backfill/collector_progress.json")
DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_PLAN = Path("data/artifacts/l0_public_newswire_backfill/collection_plan.json")
DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_EVENTS = Path("data/artifacts/l0_public_newswire_backfill/collector_events.jsonl")
DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_BACKGROUND = Path("data/artifacts/l0_public_newswire_backfill/background_process.json")
DEFAULT_PUBLIC_CONTEXT_NEWS_PROGRESS = Path("data/artifacts/l0_public_context_news/collector_progress.json")
DEFAULT_PUBLIC_CONTEXT_NEWS_PLAN = Path("data/artifacts/l0_public_context_news/collection_plan.json")
DEFAULT_PUBLIC_CONTEXT_NEWS_EVENTS = Path("data/artifacts/l0_public_context_news/collector_events.jsonl")
DEFAULT_PUBLIC_CONTEXT_NEWS_BACKGROUND = Path("data/artifacts/l0_public_context_news/background_process.json")
DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_PROGRESS = Path("data/artifacts/l0_public_context_news_backfill/collector_progress.json")
DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_PLAN = Path("data/artifacts/l0_public_context_news_backfill/collection_plan.json")
DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_EVENTS = Path("data/artifacts/l0_public_context_news_backfill/collector_events.jsonl")
DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_BACKGROUND = Path("data/artifacts/l0_public_context_news_backfill/background_process.json")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_PROGRESS = Path("data/artifacts/l0_public_market_macro_news/collector_progress.json")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_PLAN = Path("data/artifacts/l0_public_market_macro_news/collection_plan.json")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_EVENTS = Path("data/artifacts/l0_public_market_macro_news/collector_events.jsonl")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKGROUND = Path("data/artifacts/l0_public_market_macro_news/background_process.json")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_PROGRESS = Path("data/artifacts/l0_public_market_macro_news_backfill/collector_progress.json")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_PLAN = Path("data/artifacts/l0_public_market_macro_news_backfill/collection_plan.json")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_EVENTS = Path("data/artifacts/l0_public_market_macro_news_backfill/collector_events.jsonl")
DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_BACKGROUND = Path("data/artifacts/l0_public_market_macro_news_backfill/background_process.json")
DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_PROGRESS = Path("data/artifacts/l0_public_industry_dive_news_backfill/collector_progress.json")
DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_PLAN = Path("data/artifacts/l0_public_industry_dive_news_backfill/collection_plan.json")
DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_EVENTS = Path("data/artifacts/l0_public_industry_dive_news_backfill/collector_events.jsonl")
DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_BACKGROUND = Path("data/artifacts/l0_public_industry_dive_news_backfill/background_process.json")
DEFAULT_KEEP_AWAKE_STATUS = Path("data/artifacts/l0_source_acquisition/keep_laptop_awake_status.json")
DEFAULT_DAILY_RAW_DIR = Path("data/raw/us_daily_alpaca_full_universe")
DEFAULT_DB_PATH = Path("trading.db")
DEFAULT_TICK_STOP = Path("data/artifacts/microstructure_backfill_queue_15m/STOP")
DEFAULT_UNIVERSE_COUNT = 12_040
DEFAULT_DAILY_SHARD_PROGRESS_GLOB = "data/artifacts/l0_bar_daily_full_backfill_shard_*/collector_progress.json"
DEFAULT_DAILY_SHARD_BACKGROUND_GLOB = "data/artifacts/l0_bar_daily_full_backfill_shard_*/background_process.json"
ONE_MINUTE_ESTIMATED_FULL_UNIVERSE_ROWS = 12_847_161_600


@dataclass(frozen=True)
class L0CollectionStatusConfig:
    status_json: Path = DEFAULT_STATUS_JSON
    status_md: Path = DEFAULT_STATUS_MD
    daily_progress: Path = DEFAULT_DAILY_PROGRESS
    five_min_progress: Path = DEFAULT_FIVE_MIN_PROGRESS
    news_progress: Path = DEFAULT_NEWS_PROGRESS
    news_plan: Path = DEFAULT_NEWS_PLAN
    news_state: Path = DEFAULT_NEWS_STATE
    news_events: Path = DEFAULT_NEWS_EVENTS
    reference_progress: Path = DEFAULT_REFERENCE_PROGRESS
    tick_progress: Path = DEFAULT_TICK_PROGRESS
    daily_background: Path = DEFAULT_DAILY_BACKGROUND
    daily_shard_progress_glob: str = DEFAULT_DAILY_SHARD_PROGRESS_GLOB
    daily_shard_background_glob: str = DEFAULT_DAILY_SHARD_BACKGROUND_GLOB
    five_min_background: Path = DEFAULT_FIVE_MIN_BACKGROUND
    news_background: Path = DEFAULT_NEWS_BACKGROUND
    public_newswire_progress: Path = DEFAULT_PUBLIC_NEWSWIRE_PROGRESS
    public_newswire_plan: Path = DEFAULT_PUBLIC_NEWSWIRE_PLAN
    public_newswire_events: Path = DEFAULT_PUBLIC_NEWSWIRE_EVENTS
    public_newswire_background: Path = DEFAULT_PUBLIC_NEWSWIRE_BACKGROUND
    public_newswire_backfill_progress: Path = DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_PROGRESS
    public_newswire_backfill_plan: Path = DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_PLAN
    public_newswire_backfill_events: Path = DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_EVENTS
    public_newswire_backfill_background: Path = DEFAULT_PUBLIC_NEWSWIRE_BACKFILL_BACKGROUND
    public_context_news_progress: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_PROGRESS
    public_context_news_plan: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_PLAN
    public_context_news_events: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_EVENTS
    public_context_news_background: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_BACKGROUND
    public_context_news_backfill_progress: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_PROGRESS
    public_context_news_backfill_plan: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_PLAN
    public_context_news_backfill_events: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_EVENTS
    public_context_news_backfill_background: Path = DEFAULT_PUBLIC_CONTEXT_NEWS_BACKFILL_BACKGROUND
    public_market_macro_news_progress: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_PROGRESS
    public_market_macro_news_plan: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_PLAN
    public_market_macro_news_events: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_EVENTS
    public_market_macro_news_background: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKGROUND
    public_market_macro_news_backfill_progress: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_PROGRESS
    public_market_macro_news_backfill_plan: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_PLAN
    public_market_macro_news_backfill_events: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_EVENTS
    public_market_macro_news_backfill_background: Path = DEFAULT_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_BACKGROUND
    public_industry_dive_news_backfill_progress: Path = DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_PROGRESS
    public_industry_dive_news_backfill_plan: Path = DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_PLAN
    public_industry_dive_news_backfill_events: Path = DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_EVENTS
    public_industry_dive_news_backfill_background: Path = DEFAULT_PUBLIC_INDUSTRY_DIVE_NEWS_BACKFILL_BACKGROUND
    keep_awake_status: Path = DEFAULT_KEEP_AWAKE_STATUS
    daily_raw_dir: Path = DEFAULT_DAILY_RAW_DIR
    db_path: Path = DEFAULT_DB_PATH
    tick_stop: Path = DEFAULT_TICK_STOP
    universe_count: int = DEFAULT_UNIVERSE_COUNT


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {"read_error": "JSONDecodeError", "path": str(path)}
    return payload if isinstance(payload, dict) else {"payload_type": type(payload).__name__, "path": str(path)}


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def progress_pct(completed: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round(min(max(completed, 0), total) / total * 100.0, 4)


def format_counts(counts: dict[str, Any]) -> str:
    if not counts:
        return "{}"
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))


def news_event_summary(path: Path) -> dict[str, Any]:
    providers: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return {"path": str(path), "exists": False, "providers": providers}
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        return {"path": str(path), "exists": False, "read_error": type(exc).__name__, "providers": providers}
    with handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            provider = str(event.get("provider") or event.get("source_family") or "unknown")
            status = str(event.get("status") or "unknown")
            provider_payload = providers.setdefault(
                provider,
                {
                    "events": 0,
                    "rows": 0,
                    "l1_ready_discovery_only_count": 0,
                    "l1_ready_diagnostic_only_count": 0,
                    "l1_context_ready_count": 0,
                    "l1_blocked_count": 0,
                    "status_counts": Counter(),
                    "last_by_source_id": {},
                },
            )
            provider_payload["events"] += 1
            provider_payload["rows"] += int_value(event.get("row_count"))
            provider_payload["l1_ready_discovery_only_count"] += int_value(event.get("l1_ready_discovery_only_count"))
            provider_payload["l1_ready_diagnostic_only_count"] += int_value(event.get("l1_ready_diagnostic_only_count"))
            provider_payload["l1_context_ready_count"] += int_value(event.get("l1_context_ready_count"))
            provider_payload["l1_blocked_count"] += int_value(event.get("l1_blocked_count"))
            provider_payload["status_counts"][status] += 1
            source_id = str(event.get("source_id") or "")
            if source_id:
                provider_payload["last_by_source_id"][source_id] = status
                source_key = source_id.split("::", 1)[0]
                source_payload = provider_payload.setdefault("source_stats", {}).setdefault(
                    source_key,
                    {
                        "events": 0,
                        "rows": 0,
                        "l1_ready_discovery_only_count": 0,
                        "l1_ready_diagnostic_only_count": 0,
                        "l1_context_ready_count": 0,
                        "l1_blocked_count": 0,
                        "status_counts": Counter(),
                        "last_status": "",
                        "last_updated_at": "",
                    },
                )
                source_payload["events"] += 1
                source_payload["rows"] += int_value(event.get("row_count"))
                source_payload["l1_ready_discovery_only_count"] += int_value(event.get("l1_ready_discovery_only_count"))
                source_payload["l1_ready_diagnostic_only_count"] += int_value(event.get("l1_ready_diagnostic_only_count"))
                source_payload["l1_context_ready_count"] += int_value(event.get("l1_context_ready_count"))
                source_payload["l1_blocked_count"] += int_value(event.get("l1_blocked_count"))
                source_payload["status_counts"][status] += 1
                source_payload["last_status"] = status
                source_payload["last_updated_at"] = str(event.get("updated_at") or "")
    normalized: dict[str, dict[str, Any]] = {}
    for provider, payload in providers.items():
        latest_counts = Counter(payload["last_by_source_id"].values())
        normalized[provider] = {
            "events": int(payload["events"]),
            "rows": int(payload["rows"]),
            "l1_ready_discovery_only_count": int(payload["l1_ready_discovery_only_count"]),
            "l1_ready_diagnostic_only_count": int(payload["l1_ready_diagnostic_only_count"]),
            "l1_context_ready_count": int(payload["l1_context_ready_count"]),
            "l1_blocked_count": int(payload["l1_blocked_count"]),
            "status_counts": dict(sorted(payload["status_counts"].items())),
            "unique_source_ids": len(payload["last_by_source_id"]),
            "latest_source_status_counts": dict(sorted(latest_counts.items())),
            "source_stats": {
                source_key: {
                    "events": int(source_payload["events"]),
                    "rows": int(source_payload["rows"]),
                    "l1_ready_discovery_only_count": int(source_payload["l1_ready_discovery_only_count"]),
                    "l1_ready_diagnostic_only_count": int(source_payload["l1_ready_diagnostic_only_count"]),
                    "l1_context_ready_count": int(source_payload["l1_context_ready_count"]),
                    "l1_blocked_count": int(source_payload["l1_blocked_count"]),
                    "status_counts": dict(sorted(source_payload["status_counts"].items())),
                    "last_status": source_payload.get("last_status", ""),
                    "last_updated_at": source_payload.get("last_updated_at", ""),
                }
                for source_key, source_payload in sorted((payload.get("source_stats") or {}).items())
            },
        }
    return {"path": str(path), "exists": True, "providers": normalized}


def parse_gdelt_ts(value: Any) -> datetime | None:
    text = str(value or "")
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    except ValueError:
        return None


def parse_date(value: Any) -> date | None:
    text = str(value or "")
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def gdelt_completed_units(*, start_ts: str, cursor_ts: str, event_units: int) -> int:
    start = parse_gdelt_ts(start_ts)
    cursor = parse_gdelt_ts(cursor_ts)
    cursor_units = 0
    if start and cursor and cursor >= start:
        cursor_units = int((cursor - start).total_seconds() // (15 * 60))
    return max(cursor_units, event_units)


def marketaux_completed_units(
    *,
    start_date: str,
    window_start: str,
    symbol_index: int,
    universe_count: int,
    estimated_symbol_batches: int,
    estimated_year_windows: int,
    window_days: int = 366,
) -> int:
    if estimated_symbol_batches <= 0 or estimated_year_windows <= 0:
        return 0
    batch_size = max(int(round(universe_count / estimated_symbol_batches)), 1) if universe_count else 5
    start = parse_date(start_date)
    current = parse_date(window_start)
    window_index = 0
    if start and current and current >= start:
        window_index = min((current - start).days // max(window_days, 1), estimated_year_windows)
    batch_index = min(max(symbol_index, 0) // batch_size, estimated_symbol_batches)
    return min(window_index * estimated_symbol_batches + batch_index, estimated_symbol_batches * estimated_year_windows)


def one_minute_bars_status() -> dict[str, Any]:
    return {
        "included": False,
        "status": "NOT_IN_CURRENT_L1_L2_MINIMUM_SCOPE",
        "reason": (
            "Current L1/L2 consumers are wired to daily CSV and trading.db::market_bars_5m. "
            "Full-universe 1m bars are about 5x the 5m request and storage surface, so they were excluded "
            "from the minimum required backfill while quote/trade ticks are postponed."
        ),
        "estimated_full_universe_rows_regular_session_upper_bound": ONE_MINUTE_ESTIMATED_FULL_UNIVERSE_ROWS,
        "next_decision": "Add as a separate optional lane only if an L1/L2 contract explicitly requires 1m bars.",
    }


def news_source_breakdown(plan: dict[str, Any], state: dict[str, Any], progress: dict[str, Any], event_path: Path) -> dict[str, Any]:
    merged = dict(state)
    merged.update(progress)
    sources = plan.get("sources", {}) if isinstance(plan.get("sources"), dict) else {}
    event_summary = news_event_summary(event_path)
    provider_stats = event_summary.get("providers", {})

    official_plan = sources.get("official_public_releases", {})
    official_stats = provider_stats.get("official_public_releases", {})
    official_total = int_value(official_plan.get("known_enabled_source_count"))
    official_completed = min(int_value(official_stats.get("unique_source_ids")), official_total) if official_total else int_value(official_stats.get("unique_source_ids"))
    official_latest_counts = official_stats.get("latest_source_status_counts", {})
    official_status = "PENDING"
    if bool(merged.get("official_done")):
        official_status = "ENABLED_ENDPOINT_REFRESH_DONE"
        if int_value(official_latest_counts.get("FAILED_RETRYABLE")) > 0:
            official_status = "ENABLED_ENDPOINT_REFRESH_DONE_WITH_RETRYABLE_FAILURES"

    gdelt_plan = sources.get("gdelt_news_events", {})
    gdelt_stats = provider_stats.get("gdelt_news_events", {})
    gdelt_total = int_value(gdelt_plan.get("estimated_15min_files"))
    gdelt_cursor = str(merged.get("gdelt_cursor_ts") or "")
    gdelt_completed = gdelt_completed_units(
        start_ts=str(plan.get("start_date", "2016-01-01")).replace("-", "") + "000000",
        cursor_ts=gdelt_cursor,
        event_units=int_value(gdelt_stats.get("unique_source_ids")),
    )
    gdelt_completed = min(gdelt_completed, gdelt_total) if gdelt_total else gdelt_completed
    gdelt_status = "COMPLETE" if gdelt_total and gdelt_completed >= gdelt_total else "RUNNING"

    marketaux_plan = sources.get("marketaux_news_free", {})
    marketaux_stats = provider_stats.get("marketaux_news_free", {})
    marketaux_batches = int_value(marketaux_plan.get("estimated_symbol_batches"))
    marketaux_windows = int_value(marketaux_plan.get("estimated_year_windows"))
    marketaux_total = marketaux_batches * marketaux_windows
    marketaux_symbol_index = int_value(merged.get("marketaux_symbol_index"))
    marketaux_window_start = str(merged.get("marketaux_window_start") or plan.get("start_date") or "")
    marketaux_completed = marketaux_completed_units(
        start_date=str(plan.get("start_date") or "2016-01-01"),
        window_start=marketaux_window_start,
        symbol_index=marketaux_symbol_index,
        universe_count=int_value(plan.get("universe_count"), int_value(merged.get("universe_count"))),
        estimated_symbol_batches=marketaux_batches,
        estimated_year_windows=marketaux_windows,
    )
    marketaux_status = "RUNNING"
    if bool(merged.get("marketaux_credential_blocked")):
        marketaux_status = "CREDENTIAL_BLOCKED"
    elif str(merged.get("marketaux_daily_cap_exhausted_date") or ""):
        marketaux_status = "DAILY_CAP_EXHAUSTED_WAITING_NEXT_UTC_DAY"
    elif marketaux_total and marketaux_completed >= marketaux_total:
        marketaux_status = "COMPLETE"

    return {
        "event_log": event_summary,
        "official_public_releases": {
            "status": official_status,
            "completed_units": official_completed,
            "total_units": official_total,
            "progress_pct": progress_pct(official_completed, official_total),
            "unit": "enabled_official_endpoint",
            "known_enabled_source_count": official_total,
            "symbols_with_known_official_endpoint": int_value(official_plan.get("symbols_with_known_official_endpoint")),
            "symbols_missing_official_endpoint": int_value(official_plan.get("symbols_missing_official_endpoint")),
            "historical_2016_full_depth_status": official_plan.get("historical_2016_full_depth_status", ""),
            "blocker_path": official_plan.get("blocker_path", ""),
            "last_official_run_ts": merged.get("last_official_run_ts", ""),
            "event_status_counts": official_stats.get("status_counts", {}),
            "latest_source_status_counts": official_latest_counts,
        },
        "gdelt_news_events": {
            "status": gdelt_status,
            "completed_units": gdelt_completed,
            "total_units": gdelt_total,
            "progress_pct": progress_pct(gdelt_completed, gdelt_total),
            "unit": "15min_archive_file",
            "cursor_ts": gdelt_cursor,
            "requests_per_minute_cap": int_value(gdelt_plan.get("requests_per_minute_cap")),
            "event_status_counts": gdelt_stats.get("status_counts", {}),
        },
        "marketaux_news_free": {
            "status": marketaux_status,
            "completed_units": marketaux_completed,
            "total_units": marketaux_total,
            "progress_pct": progress_pct(marketaux_completed, marketaux_total),
            "unit": "symbol_batch_year_window_minimum_request",
            "current_symbol_index": marketaux_symbol_index,
            "current_window_start": marketaux_window_start,
            "current_page": int_value(merged.get("marketaux_page"), 1),
            "daily_request_cap": int_value(marketaux_plan.get("daily_request_cap")),
            "daily_cap_exhausted_date": merged.get("marketaux_daily_cap_exhausted_date", ""),
            "credential_blocked": bool(merged.get("marketaux_credential_blocked", False)),
            "event_status_counts": marketaux_stats.get("status_counts", {}),
        },
    }


def public_newswire_status(plan: dict[str, Any], progress: dict[str, Any], event_path: Path) -> dict[str, Any]:
    sources = plan.get("sources", {}) if isinstance(plan.get("sources"), dict) else {}
    stats = news_event_summary(event_path).get("providers", {}).get("public_newswire_feeds", {})
    total = int_value(plan.get("source_count"), len(sources))
    completed = min(int_value(stats.get("unique_source_ids")), total) if total else int_value(stats.get("unique_source_ids"))
    latest_counts = stats.get("latest_source_status_counts", {})
    status = "PENDING"
    if completed:
        status = "RUNNING"
    if total and completed >= total and int_value(latest_counts.get("EXPORTED")) == total:
        status = "PRIMARY_PASS"
    elif int_value(latest_counts.get("BLOCKED_ROBOTS")) or int_value(latest_counts.get("FAILED_RETRYABLE")):
        status = "RUNNING_WITH_BLOCKERS"
    return {
        "status": status,
        "completed_units": completed,
        "total_units": total,
        "progress_pct": progress_pct(completed, total),
        "unit": "public_newswire_source",
        "provider": "public_newswire_feeds",
        "processed_events": progress.get("processed_events", 0),
        "exported_events": progress.get("exported_events", 0),
        "empty_events": progress.get("empty_events", 0),
        "failed_events": progress.get("failed_events", 0),
        "blocked_events": progress.get("blocked_events", 0),
        "row_count": int_value(stats.get("rows")),
        "l1_ready_discovery_only_count": int_value(stats.get("l1_ready_discovery_only_count")),
        "l1_ready_diagnostic_only_count": int_value(stats.get("l1_ready_diagnostic_only_count")),
        "l1_context_ready_count": int_value(stats.get("l1_context_ready_count")),
        "l1_blocked_count": int_value(stats.get("l1_blocked_count")),
        "event_status_counts": stats.get("status_counts", {}),
        "latest_source_status_counts": latest_counts,
    }


def public_newswire_backfill_status(plan: dict[str, Any], progress: dict[str, Any], event_path: Path) -> dict[str, Any]:
    stats = news_event_summary(event_path).get("providers", {}).get("public_newswire_feeds", {})
    backfill = progress.get("backfill", {}) if isinstance(progress.get("backfill"), dict) else {}
    source_states: dict[str, Any] = {}
    total_archives = 0
    completed_archives = 0
    pending_archives = 0
    active_offsets = 0
    unavailable_archives = 0
    for source_key, payload in backfill.items():
        if not isinstance(payload, dict):
            continue
        completed = len(payload.get("completed_archive_urls", []) or [])
        unavailable = len(payload.get("unavailable_archive_urls", []) or [])
        total = int_value(payload.get("total_archive_urls"))
        pending = int_value(payload.get("pending_archive_urls"), max(total - completed, 0))
        offsets = payload.get("archive_entry_offsets", {}) if isinstance(payload.get("archive_entry_offsets"), dict) else {}
        source_states[source_key] = {
            "completed_archive_urls": completed,
            "unavailable_archive_urls": unavailable,
            "total_archive_urls": total,
            "pending_archive_urls": pending,
            "active_archive_offsets": len(offsets),
            "start_date": payload.get("start_date", ""),
            "end_date": payload.get("end_date", ""),
        }
        total_archives += total
        completed_archives += completed
        pending_archives += pending
        active_offsets += len(offsets)
        unavailable_archives += unavailable
    status = "PENDING"
    if int_value(stats.get("events")) or total_archives:
        status = "RUNNING"
    if total_archives and completed_archives >= total_archives:
        status = "COMPLETE"
    return {
        "status": status,
        "provider": "public_newswire_feeds",
        "mode": "historical_backfill",
        "completed_units": completed_archives,
        "total_units": total_archives,
        "progress_pct": progress_pct(completed_archives, total_archives),
        "pending_archive_urls": pending_archives,
        "active_archive_offsets": active_offsets,
        "unavailable_archive_urls": unavailable_archives,
        "row_count": int_value(stats.get("rows")),
        "l1_ready_discovery_only_count": int_value(stats.get("l1_ready_discovery_only_count")),
        "l1_context_ready_count": int_value(stats.get("l1_context_ready_count")),
        "l1_blocked_count": int_value(stats.get("l1_blocked_count")),
        "event_status_counts": stats.get("status_counts", {}),
        "source_states": source_states,
        "plan_start_date": (plan.get("backfill", {}) if isinstance(plan.get("backfill"), dict) else {}).get("start_date", ""),
        "plan_end_date": (plan.get("backfill", {}) if isinstance(plan.get("backfill"), dict) else {}).get("end_date", ""),
    }


def public_context_news_status(plan: dict[str, Any], progress: dict[str, Any], event_path: Path) -> dict[str, Any]:
    sources = plan.get("sources", {}) if isinstance(plan.get("sources"), dict) else {}
    stats = news_event_summary(event_path).get("providers", {}).get("public_context_news_feeds", {})
    total = int_value(plan.get("source_count"), len(sources))
    completed = min(int_value(stats.get("unique_source_ids")), total) if total else int_value(stats.get("unique_source_ids"))
    latest_counts = stats.get("latest_source_status_counts", {})
    status = "PENDING"
    if completed:
        status = "RUNNING"
    if total and completed >= total and int_value(latest_counts.get("EXPORTED")) == total:
        status = "PRIMARY_PASS"
    elif int_value(latest_counts.get("BLOCKED_ROBOTS")) or int_value(latest_counts.get("FAILED_RETRYABLE")):
        status = "RUNNING_WITH_BLOCKERS"
    return {
        "status": status,
        "completed_units": completed,
        "total_units": total,
        "progress_pct": progress_pct(completed, total),
        "unit": "public_context_news_source",
        "provider": "public_context_news_feeds",
        "processed_events": progress.get("processed_events", 0),
        "exported_events": progress.get("exported_events", 0),
        "empty_events": progress.get("empty_events", 0),
        "failed_events": progress.get("failed_events", 0),
        "blocked_events": progress.get("blocked_events", 0),
        "row_count": int_value(stats.get("rows")),
        "l1_ready_discovery_only_count": int_value(stats.get("l1_ready_discovery_only_count")),
        "l1_ready_diagnostic_only_count": int_value(stats.get("l1_ready_diagnostic_only_count")),
        "l1_context_ready_count": int_value(stats.get("l1_context_ready_count")),
        "l1_blocked_count": int_value(stats.get("l1_blocked_count")),
        "event_status_counts": stats.get("status_counts", {}),
        "latest_source_status_counts": latest_counts,
        "historical_backfill_status": plan.get("historical_backfill_status", ""),
    }


def public_context_news_backfill_status(plan: dict[str, Any], progress: dict[str, Any], event_path: Path) -> dict[str, Any]:
    stats = news_event_summary(event_path).get("providers", {}).get("public_context_news_feeds", {})
    backfill = progress.get("backfill", {}) if isinstance(progress.get("backfill"), dict) else {}
    source_states: dict[str, Any] = {}
    total_units = 0
    completed_units = 0
    pending_units = 0
    active_page_offsets = 0
    for source_key, payload in backfill.items():
        if not isinstance(payload, dict):
            continue
        completed = len(payload.get("completed_units", []) or [])
        total = int_value(payload.get("total_units"))
        pending = int_value(payload.get("pending_units"), max(total - completed, 0))
        page_offsets = payload.get("page_offsets", {}) if isinstance(payload.get("page_offsets"), dict) else {}
        entry_offsets = payload.get("entry_offsets", {}) if isinstance(payload.get("entry_offsets"), dict) else {}
        offsets = {**page_offsets, **entry_offsets}
        source_states[source_key] = {
            "completed_units": completed,
            "total_units": total,
            "pending_units": pending,
            "active_page_offsets": len(offsets),
            "start_date": payload.get("start_date", ""),
            "end_date": payload.get("end_date", ""),
        }
        total_units += total
        completed_units += completed
        pending_units += pending
        active_page_offsets += len(offsets)
    status = "PENDING"
    if int_value(stats.get("events")) or total_units:
        status = "RUNNING"
    if total_units and completed_units >= total_units:
        status = "COMPLETE"
    return {
        "status": status,
        "provider": "public_context_news_feeds",
        "mode": "historical_backfill",
        "completed_units": completed_units,
        "total_units": total_units,
        "progress_pct": progress_pct(completed_units, total_units),
        "pending_units": pending_units,
        "active_page_offsets": active_page_offsets,
        "row_count": int_value(stats.get("rows")),
        "l1_ready_discovery_only_count": int_value(stats.get("l1_ready_discovery_only_count")),
        "l1_context_ready_count": int_value(stats.get("l1_context_ready_count")),
        "l1_blocked_count": int_value(stats.get("l1_blocked_count")),
        "event_status_counts": stats.get("status_counts", {}),
        "source_states": source_states,
        "plan_start_date": (plan.get("backfill", {}) if isinstance(plan.get("backfill"), dict) else {}).get("start_date", ""),
        "plan_end_date": (plan.get("backfill", {}) if isinstance(plan.get("backfill"), dict) else {}).get("end_date", ""),
        "supported_sources": (plan.get("backfill", {}) if isinstance(plan.get("backfill"), dict) else {}).get("supported_sources", []),
    }


def public_market_macro_news_status(plan: dict[str, Any], progress: dict[str, Any], event_path: Path) -> dict[str, Any]:
    sources = plan.get("sources", {}) if isinstance(plan.get("sources"), dict) else {}
    stats = news_event_summary(event_path).get("providers", {}).get("public_market_macro_news_feeds", {})
    total = int_value(plan.get("source_count"), len(sources))
    completed = min(int_value(stats.get("unique_source_ids")), total) if total else int_value(stats.get("unique_source_ids"))
    latest_counts = stats.get("latest_source_status_counts", {})
    status = "PENDING"
    if completed:
        status = "RUNNING"
    if total and completed >= total and int_value(latest_counts.get("EXPORTED")) == total:
        status = "PRIMARY_PASS"
    elif int_value(latest_counts.get("BLOCKED_ROBOTS")) or int_value(latest_counts.get("FAILED_RETRYABLE")):
        status = "RUNNING_WITH_BLOCKERS"
    return {
        "status": status,
        "completed_units": completed,
        "total_units": total,
        "progress_pct": progress_pct(completed, total),
        "unit": "public_market_macro_news_source",
        "provider": "public_market_macro_news_feeds",
        "processed_events": progress.get("processed_events", 0),
        "exported_events": progress.get("exported_events", 0),
        "empty_events": progress.get("empty_events", 0),
        "failed_events": progress.get("failed_events", 0),
        "blocked_events": progress.get("blocked_events", 0),
        "row_count": int_value(stats.get("rows")),
        "l1_ready_discovery_only_count": int_value(stats.get("l1_ready_discovery_only_count")),
        "l1_ready_diagnostic_only_count": int_value(stats.get("l1_ready_diagnostic_only_count")),
        "l1_context_ready_count": int_value(stats.get("l1_context_ready_count")),
        "l1_blocked_count": int_value(stats.get("l1_blocked_count")),
        "event_status_counts": stats.get("status_counts", {}),
        "latest_source_status_counts": latest_counts,
    }


def public_market_macro_news_backfill_status(plan: dict[str, Any], progress: dict[str, Any], event_path: Path) -> dict[str, Any]:
    stats = news_event_summary(event_path).get("providers", {}).get("public_market_macro_news_feeds", {})
    backfill = progress.get("backfill", {}) if isinstance(progress.get("backfill"), dict) else {}
    source_states: dict[str, Any] = {}
    total_units = 0
    completed_units = 0
    pending_units = 0
    active_page_offsets = 0
    for source_key, payload in backfill.items():
        if not isinstance(payload, dict):
            continue
        completed = len(payload.get("completed_units", []) or [])
        total = int_value(payload.get("total_units"))
        pending = int_value(payload.get("pending_units"), max(total - completed, 0))
        page_offsets = payload.get("page_offsets", {}) if isinstance(payload.get("page_offsets"), dict) else {}
        entry_offsets = payload.get("entry_offsets", {}) if isinstance(payload.get("entry_offsets"), dict) else {}
        offsets = {**page_offsets, **entry_offsets}
        source_states[source_key] = {
            "completed_units": completed,
            "total_units": total,
            "pending_units": pending,
            "active_page_offsets": len(offsets),
            "start_date": payload.get("start_date", ""),
            "end_date": payload.get("end_date", ""),
        }
        total_units += total
        completed_units += completed
        pending_units += pending
        active_page_offsets += len(offsets)
    status = "PENDING"
    if int_value(stats.get("events")) or total_units:
        status = "RUNNING"
    if total_units and completed_units >= total_units:
        status = "COMPLETE"
    return {
        "status": status,
        "provider": "public_market_macro_news_feeds",
        "mode": "historical_backfill",
        "completed_units": completed_units,
        "total_units": total_units,
        "progress_pct": progress_pct(completed_units, total_units),
        "pending_units": pending_units,
        "active_page_offsets": active_page_offsets,
        "row_count": int_value(stats.get("rows")),
        "l1_ready_discovery_only_count": int_value(stats.get("l1_ready_discovery_only_count")),
        "l1_context_ready_count": int_value(stats.get("l1_context_ready_count")),
        "l1_blocked_count": int_value(stats.get("l1_blocked_count")),
        "event_status_counts": stats.get("status_counts", {}),
        "source_states": source_states,
        "plan_start_date": plan.get("backfill_start_date", ""),
        "plan_end_date": plan.get("backfill_end_date", ""),
    }


def pid_running(pid: int | str | None) -> bool | None:
    if pid in (None, ""):
        return None
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return None
    try:
        result = subprocess.run(  # noqa: S603
            ["tasklist", "/FI", f"PID eq {pid_int}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return str(pid_int) in result.stdout


def keep_awake_pids() -> list[int]:
    try:
        result = subprocess.run(  # noqa: S603
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '-File\\s+.*keep_laptop_awake\\.ps1' } | Select-Object -ExpandProperty ProcessId",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        text = line.strip()
        if not text.isdigit():
            continue
        pids.append(int(text))
    return sorted(set(pids))


def background_status(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    pid = payload.get("pid")
    return {
        "path": str(path),
        "pid": pid,
        "running": pid_running(pid),
        "started_at": payload.get("started_at", ""),
        "lanes": payload.get("lanes", payload.get("sources", "")),
    }


def daily_file_count(path: Path) -> int:
    return len(list(path.glob("*.csv"))) if path.exists() else 0


def sorted_glob(pattern: str) -> list[Path]:
    return [Path(path) for path in sorted(glob.glob(pattern))]


def market_bars_summary(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"db_path": str(db_path), "exists": False, "row_count": 0, "distinct_symbols": 0}
    con = sqlite3.connect(db_path)
    try:
        exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='market_bars_5m'").fetchone()
        if not exists:
            return {"db_path": str(db_path), "exists": True, "table_exists": False, "row_count": 0, "distinct_symbols": 0}
        row = con.execute("SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(bar_start_ts), MAX(bar_end_ts) FROM market_bars_5m").fetchone()
        return {
            "db_path": str(db_path),
            "exists": True,
            "table_exists": True,
            "row_count": int(row[0] or 0),
            "distinct_symbols": int(row[1] or 0),
            "min_bar_start_ts": row[2] or "",
            "max_bar_end_ts": row[3] or "",
        }
    finally:
        con.close()


def lane_summary(progress: dict[str, Any], *, total_units_key: str, progress_key: str) -> dict[str, Any]:
    total = int(progress.get(total_units_key, progress.get("universe_count", DEFAULT_UNIVERSE_COUNT)) or 0)
    completed = int(progress.get(progress_key, 0) or 0)
    remaining = int(progress.get("remaining_request_units", max(total - completed, 0)) or 0)
    return {
        "updated_at": progress.get("updated_at", ""),
        "last_status": progress.get("last_status", progress.get("status", "")),
        "completed_units": completed,
        "total_units": total,
        "progress_pct": progress.get("overall_progress_pct", progress.get("daily_progress_pct", progress.get("five_min_progress_pct", ""))),
        "remaining_request_units": remaining,
        "observed_requests_per_minute_this_run": progress.get("observed_requests_per_minute_this_run", ""),
        "eta_hours_at_observed_rate": progress.get("eta_hours_at_observed_rate", ""),
        "eta_hours_at_configured_rpm": progress.get("eta_hours_at_configured_rpm", ""),
        "exported_events": progress.get("exported_events", 0),
        "empty_events": progress.get("empty_events", 0),
        "failed_events": progress.get("failed_events", 0),
        "rate_limited_events": progress.get("rate_limited_events", 0),
    }


def build_status(config: L0CollectionStatusConfig = L0CollectionStatusConfig()) -> dict[str, Any]:
    daily = load_json(config.daily_progress)
    daily_shard_progresses = [{"path": str(path), **load_json(path)} for path in sorted_glob(config.daily_shard_progress_glob)]
    daily_shard_backgrounds = [background_status(path) for path in sorted_glob(config.daily_shard_background_glob)]
    five_min = load_json(config.five_min_progress)
    news = load_json(config.news_progress)
    news_plan = load_json(config.news_plan)
    news_state = load_json(config.news_state)
    public_newswire_progress = load_json(config.public_newswire_progress)
    public_newswire_plan = load_json(config.public_newswire_plan)
    public_newswire_backfill_progress = load_json(config.public_newswire_backfill_progress)
    public_newswire_backfill_plan = load_json(config.public_newswire_backfill_plan)
    public_context_news_progress = load_json(config.public_context_news_progress)
    public_context_news_plan = load_json(config.public_context_news_plan)
    public_context_news_backfill_progress = load_json(config.public_context_news_backfill_progress)
    public_context_news_backfill_plan = load_json(config.public_context_news_backfill_plan)
    public_market_macro_news_progress = load_json(config.public_market_macro_news_progress)
    public_market_macro_news_plan = load_json(config.public_market_macro_news_plan)
    public_market_macro_news_backfill_progress = load_json(config.public_market_macro_news_backfill_progress)
    public_market_macro_news_backfill_plan = load_json(config.public_market_macro_news_backfill_plan)
    public_industry_dive_news_backfill_progress = load_json(config.public_industry_dive_news_backfill_progress)
    public_industry_dive_news_backfill_plan = load_json(config.public_industry_dive_news_backfill_plan)
    reference = load_json(config.reference_progress)
    tick = load_json(config.tick_progress)
    five_min_summary_input = dict(five_min)
    five_min_total = int(five_min_summary_input.get("universe_count", config.universe_count) or 0) * int(
        five_min_summary_input.get("five_min_blocks_per_symbol", 0) or 0
    )
    if five_min_total:
        five_min_summary_input["total_request_units"] = five_min_total
    keep_awake = load_json(config.keep_awake_status)
    detected_keep_awake_pids = keep_awake_pids()
    if "pid" in keep_awake:
        keep_awake["running"] = pid_running(keep_awake.get("pid"))
    keep_awake["detected_running_pids"] = detected_keep_awake_pids
    keep_awake["detected_running"] = bool(detected_keep_awake_pids)
    actual_daily_files = daily_file_count(config.daily_raw_dir)
    daily_summary_input = dict(daily)
    daily_summary_input["daily_symbol_index"] = actual_daily_files
    daily_summary_input["universe_count"] = int(config.universe_count)
    daily_summary_input["overall_progress_pct"] = round(actual_daily_files / max(int(config.universe_count), 1) * 100.0, 4)
    daily_summary_input["remaining_request_units"] = max(int(config.universe_count) - actual_daily_files, 0)
    if daily_shard_progresses:
        latest_daily_updates = [
            str(progress.get("updated_at", ""))
            for progress in daily_shard_progresses + [daily]
            if str(progress.get("updated_at", ""))
        ]
        daily_summary_input["last_status"] = ",".join(
            sorted({str(progress.get("last_status", progress.get("status", ""))) for progress in daily_shard_progresses if progress})
        )
        daily_summary_input["exported_events"] = sum(int(progress.get("exported_events", 0) or 0) for progress in daily_shard_progresses)
        daily_summary_input["empty_events"] = sum(int(progress.get("empty_events", 0) or 0) for progress in daily_shard_progresses)
        daily_summary_input["failed_events"] = sum(int(progress.get("failed_events", 0) or 0) for progress in daily_shard_progresses)
        daily_summary_input["rate_limited_events"] = sum(int(progress.get("rate_limited_events", 0) or 0) for progress in daily_shard_progresses)
        observed = [float(progress.get("observed_requests_per_minute_this_run", 0.0) or 0.0) for progress in daily_shard_progresses]
        observed_rpm = sum(observed)
        daily_summary_input["observed_requests_per_minute_this_run"] = round(observed_rpm, 4)
        daily_summary_input["eta_hours_at_observed_rate"] = (
            round(max(int(config.universe_count) - actual_daily_files, 0) / observed_rpm / 60.0, 2) if observed_rpm > 0 else None
        )
        daily_summary_input["eta_hours_at_configured_rpm"] = round(max(int(config.universe_count) - actual_daily_files, 0) / 60.0 / 60.0, 2)
        if latest_daily_updates:
            daily_summary_input["updated_at"] = max(latest_daily_updates)
    status = {
        "updated_at": now_z(),
        "objective": "L0 full-universe collection status for daily/5m bars, universe/calendar/status, news/official sources, with quote/trade ticks postponed.",
        "permissions": {
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        },
        "background_processes": {
            "daily": background_status(config.daily_background),
            "daily_shards": daily_shard_backgrounds,
            "five_min": background_status(config.five_min_background),
            "news": background_status(config.news_background),
            "public_newswire": background_status(config.public_newswire_background),
            "public_newswire_backfill": background_status(config.public_newswire_backfill_background),
            "public_context_news": background_status(config.public_context_news_background),
            "public_context_news_backfill": background_status(config.public_context_news_backfill_background),
            "public_market_macro_news": background_status(config.public_market_macro_news_background),
            "public_market_macro_news_backfill": background_status(config.public_market_macro_news_backfill_background),
            "public_industry_dive_news_backfill": background_status(config.public_industry_dive_news_backfill_background),
            "keep_awake": keep_awake,
        },
        "daily_bars": lane_summary(daily_summary_input, total_units_key="universe_count", progress_key="daily_symbol_index")
        | {"raw_csv_files": actual_daily_files, "raw_dir": str(config.daily_raw_dir), "shard_count": len(daily_shard_progresses)},
        "five_min_bars": lane_summary(five_min_summary_input, total_units_key="total_request_units", progress_key="processed_events")
        | {"market_bars_5m": market_bars_summary(config.db_path)},
        "one_minute_bars": one_minute_bars_status(),
        "news": {
            "updated_at": news.get("updated_at", ""),
            "processed_events": news.get("processed_events", 0),
            "exported_events": news.get("exported_events", 0),
            "empty_events": news.get("empty_events", 0),
            "failed_events": news.get("failed_events", 0),
            "blocked_events": news.get("blocked_events", 0),
            "gdelt_cursor_ts": news.get("gdelt_cursor_ts", ""),
            "marketaux_daily_cap_exhausted_date": news.get("marketaux_daily_cap_exhausted_date", ""),
            "marketaux_credential_blocked": bool(news.get("marketaux_credential_blocked", False)),
            "sources": news_source_breakdown(news_plan, news_state, news, config.news_events),
        },
        "public_newswire": public_newswire_status(public_newswire_plan, public_newswire_progress, config.public_newswire_events),
        "public_newswire_backfill": public_newswire_backfill_status(
            public_newswire_backfill_plan,
            public_newswire_backfill_progress,
            config.public_newswire_backfill_events,
        ),
        "public_context_news": public_context_news_status(
            public_context_news_plan,
            public_context_news_progress,
            config.public_context_news_events,
        ),
        "public_context_news_backfill": public_context_news_backfill_status(
            public_context_news_backfill_plan,
            public_context_news_backfill_progress,
            config.public_context_news_backfill_events,
        ),
        "public_market_macro_news": public_market_macro_news_status(
            public_market_macro_news_plan,
            public_market_macro_news_progress,
            config.public_market_macro_news_events,
        ),
        "public_market_macro_news_backfill": public_market_macro_news_backfill_status(
            public_market_macro_news_backfill_plan,
            public_market_macro_news_backfill_progress,
            config.public_market_macro_news_backfill_events,
        ),
        "public_industry_dive_news_backfill": public_market_macro_news_backfill_status(
            public_industry_dive_news_backfill_plan,
            public_industry_dive_news_backfill_progress,
            config.public_industry_dive_news_backfill_events,
        ),
        "reference": {
            "updated_at": reference.get("updated_at", ""),
            "status": reference.get("status", ""),
            "processed_events": reference.get("processed_events", 0),
            "exported_events": reference.get("exported_events", 0),
            "failed_events": reference.get("failed_events", 0),
            "raw_dir": reference.get("raw_dir", ""),
        },
        "quote_trade_ticks": {
            "status": tick.get("status", "UNKNOWN"),
            "stop_file_exists": config.tick_stop.exists(),
            "processed_chunks": tick.get("processed_chunks", 0),
            "exported_chunks": tick.get("exported_chunks", 0),
            "failed_chunks": tick.get("failed_chunks", 0),
            "note": "Full quote/trade tick collection is postponed by user scope decision.",
        },
    }
    return status


def write_markdown(path: Path, status: dict[str, Any]) -> None:
    lines = [
        "# L0 Collection Status",
        "",
        f"- Updated at: {status['updated_at']}",
        "- Status: DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        "",
        "## Background",
    ]
    for name, payload in status["background_processes"].items():
        if name == "keep_awake" and isinstance(payload, dict):
            lines.append(
                f"- {name}: detected_running={payload.get('detected_running')} "
                f"detected_pids={payload.get('detected_running_pids')} recorded_pid={payload.get('pid')} "
                f"recorded_pid_running={payload.get('running')}"
            )
        elif isinstance(payload, list):
            running = sum(1 for item in payload if isinstance(item, dict) and item.get("running") is True)
            lines.append(f"- {name}: workers={len(payload)} running={running}")
        elif isinstance(payload, dict) and "pid" in payload:
            lines.append(f"- {name}: pid={payload.get('pid')} running={payload.get('running')} started_at={payload.get('started_at')}")
        else:
            lines.append(f"- {name}: status_json_present={bool(payload)}")
    daily = status["daily_bars"]
    five = status["five_min_bars"]
    one_min = status["one_minute_bars"]
    news = status["news"]
    news_sources = news.get("sources", {})
    reference = status["reference"]
    public_newswire = status["public_newswire"]
    public_newswire_backfill = status["public_newswire_backfill"]
    public_context_news = status["public_context_news"]
    public_context_news_backfill = status["public_context_news_backfill"]
    public_market_macro_news = status["public_market_macro_news"]
    public_market_macro_news_backfill = status["public_market_macro_news_backfill"]
    public_industry_dive_news_backfill = status["public_industry_dive_news_backfill"]
    ticks = status["quote_trade_ticks"]
    official = news_sources.get("official_public_releases", {})
    gdelt = news_sources.get("gdelt_news_events", {})
    marketaux = news_sources.get("marketaux_news_free", {})
    lines.extend(
        [
            "",
            "## Bars",
            f"- Daily: {daily.get('completed_units')}/{daily.get('total_units')} symbols, progress={daily.get('progress_pct')}%, files={daily.get('raw_csv_files')}, failed={daily.get('failed_events')}, rate_limited={daily.get('rate_limited_events')}.",
            f"- 5m: progress={five.get('progress_pct')}%, processed_events={five.get('completed_units')}, failed={five.get('failed_events')}, rate_limited={five.get('rate_limited_events')}, observed_rpm={five.get('observed_requests_per_minute_this_run')}.",
            f"- market_bars_5m: rows={five['market_bars_5m'].get('row_count')}, symbols={five['market_bars_5m'].get('distinct_symbols')}, range={five['market_bars_5m'].get('min_bar_start_ts')} to {five['market_bars_5m'].get('max_bar_end_ts')}.",
            f"- 1m: included={one_min.get('included')}, status={one_min.get('status')}, estimated_rows_upper_bound={one_min.get('estimated_full_universe_rows_regular_session_upper_bound')}.",
            f"- 1m rationale: {one_min.get('reason')}",
            "",
            "## News And Reference",
            f"- News: processed={news.get('processed_events')}, exported={news.get('exported_events')}, failed={news.get('failed_events')}, GDELT cursor={news.get('gdelt_cursor_ts')}, Marketaux cap date={news.get('marketaux_daily_cap_exhausted_date')}.",
            f"- Reference: status={reference.get('status')}, exported={reference.get('exported_events')}, failed={reference.get('failed_events')}, raw_dir={reference.get('raw_dir')}.",
            "",
            "## News By Source",
            f"- Official: status={official.get('status')}, endpoint_refresh={official.get('completed_units')}/{official.get('total_units')} ({official.get('progress_pct')}%), symbols_with_known_endpoint={official.get('symbols_with_known_official_endpoint')}, missing_symbols={official.get('symbols_missing_official_endpoint')}, latest_statuses={format_counts(official.get('latest_source_status_counts', {}))}.",
            f"- GDELT: status={gdelt.get('status')}, chunks={gdelt.get('completed_units')}/{gdelt.get('total_units')} ({gdelt.get('progress_pct')}%), cursor={gdelt.get('cursor_ts')}, event_statuses={format_counts(gdelt.get('event_status_counts', {}))}.",
            f"- Marketaux: status={marketaux.get('status')}, units={marketaux.get('completed_units')}/{marketaux.get('total_units')} ({marketaux.get('progress_pct')}%), window_start={marketaux.get('current_window_start')}, symbol_index={marketaux.get('current_symbol_index')}, page={marketaux.get('current_page')}, daily_cap={marketaux.get('daily_request_cap')}, cap_date={marketaux.get('daily_cap_exhausted_date')}, event_statuses={format_counts(marketaux.get('event_status_counts', {}))}.",
            f"- Newswire: status={public_newswire.get('status')}, sources={public_newswire.get('completed_units')}/{public_newswire.get('total_units')} ({public_newswire.get('progress_pct')}%), rows={public_newswire.get('row_count')}, l1_ready_discovery={public_newswire.get('l1_ready_discovery_only_count')}, l1_context_ready={public_newswire.get('l1_context_ready_count')}, l1_blocked={public_newswire.get('l1_blocked_count')}, event_statuses={format_counts(public_newswire.get('event_status_counts', {}))}.",
            f"- Newswire backfill: status={public_newswire_backfill.get('status')}, archives={public_newswire_backfill.get('completed_units')}/{public_newswire_backfill.get('total_units')} ({public_newswire_backfill.get('progress_pct')}%), pending_archives={public_newswire_backfill.get('pending_archive_urls')}, unavailable_archives={public_newswire_backfill.get('unavailable_archive_urls')}, active_offsets={public_newswire_backfill.get('active_archive_offsets')}, rows={public_newswire_backfill.get('row_count')}, l1_ready_discovery={public_newswire_backfill.get('l1_ready_discovery_only_count')}, l1_context_ready={public_newswire_backfill.get('l1_context_ready_count')}, l1_blocked={public_newswire_backfill.get('l1_blocked_count')}, event_statuses={format_counts(public_newswire_backfill.get('event_status_counts', {}))}.",
            f"- Context news: status={public_context_news.get('status')}, sources={public_context_news.get('completed_units')}/{public_context_news.get('total_units')} ({public_context_news.get('progress_pct')}%), rows={public_context_news.get('row_count')}, l1_ready_discovery={public_context_news.get('l1_ready_discovery_only_count')}, l1_context_ready={public_context_news.get('l1_context_ready_count')}, l1_blocked={public_context_news.get('l1_blocked_count')}, backfill_status={public_context_news.get('historical_backfill_status')}, event_statuses={format_counts(public_context_news.get('event_status_counts', {}))}.",
            f"- Context news backfill: status={public_context_news_backfill.get('status')}, units={public_context_news_backfill.get('completed_units')}/{public_context_news_backfill.get('total_units')} ({public_context_news_backfill.get('progress_pct')}%), pending_units={public_context_news_backfill.get('pending_units')}, active_page_offsets={public_context_news_backfill.get('active_page_offsets')}, rows={public_context_news_backfill.get('row_count')}, l1_ready_discovery={public_context_news_backfill.get('l1_ready_discovery_only_count')}, l1_context_ready={public_context_news_backfill.get('l1_context_ready_count')}, l1_blocked={public_context_news_backfill.get('l1_blocked_count')}, event_statuses={format_counts(public_context_news_backfill.get('event_status_counts', {}))}.",
            f"- Market/macro news: status={public_market_macro_news.get('status')}, sources={public_market_macro_news.get('completed_units')}/{public_market_macro_news.get('total_units')} ({public_market_macro_news.get('progress_pct')}%), rows={public_market_macro_news.get('row_count')}, l1_ready_discovery={public_market_macro_news.get('l1_ready_discovery_only_count')}, l1_context_ready={public_market_macro_news.get('l1_context_ready_count')}, l1_blocked={public_market_macro_news.get('l1_blocked_count')}, event_statuses={format_counts(public_market_macro_news.get('event_status_counts', {}))}.",
            f"- Market/macro news backfill: status={public_market_macro_news_backfill.get('status')}, units={public_market_macro_news_backfill.get('completed_units')}/{public_market_macro_news_backfill.get('total_units')} ({public_market_macro_news_backfill.get('progress_pct')}%), pending_units={public_market_macro_news_backfill.get('pending_units')}, active_page_offsets={public_market_macro_news_backfill.get('active_page_offsets')}, rows={public_market_macro_news_backfill.get('row_count')}, l1_ready_discovery={public_market_macro_news_backfill.get('l1_ready_discovery_only_count')}, l1_context_ready={public_market_macro_news_backfill.get('l1_context_ready_count')}, l1_blocked={public_market_macro_news_backfill.get('l1_blocked_count')}, event_statuses={format_counts(public_market_macro_news_backfill.get('event_status_counts', {}))}.",
            f"- Industry Dive backfill: status={public_industry_dive_news_backfill.get('status')}, units={public_industry_dive_news_backfill.get('completed_units')}/{public_industry_dive_news_backfill.get('total_units')} ({public_industry_dive_news_backfill.get('progress_pct')}%), pending_units={public_industry_dive_news_backfill.get('pending_units')}, active_page_offsets={public_industry_dive_news_backfill.get('active_page_offsets')}, rows={public_industry_dive_news_backfill.get('row_count')}, l1_ready_discovery={public_industry_dive_news_backfill.get('l1_ready_discovery_only_count')}, l1_context_ready={public_industry_dive_news_backfill.get('l1_context_ready_count')}, l1_blocked={public_industry_dive_news_backfill.get('l1_blocked_count')}, event_statuses={format_counts(public_industry_dive_news_backfill.get('event_status_counts', {}))}.",
            "",
            "## Postponed",
            f"- Quote/trade ticks: status={ticks.get('status')}, stop_file_exists={ticks.get('stop_file_exists')}, processed_chunks={ticks.get('processed_chunks')}.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status(config: L0CollectionStatusConfig = L0CollectionStatusConfig()) -> dict[str, Any]:
    status = build_status(config)
    config.status_json.parent.mkdir(parents=True, exist_ok=True)
    config.status_json.write_text(json.dumps(status, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(config.status_md, status)
    return status
