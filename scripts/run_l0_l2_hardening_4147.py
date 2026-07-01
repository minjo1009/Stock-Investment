from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4147"
SLUG = "task_4147_l0_l2_hardening_gpt_review_and_implementation"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
CONFIG_PATH = ROOT / "configs" / "l0_realtime_operational_safe_config_4147.json"
BASE_CONFIG_PATH = ROOT / "configs" / "db_source_acquisition_scheduler.json"
UNIVERSE_PATH = ROOT / "data" / "raw" / "alpaca_active_us_equity_universe.csv"
L0_4146_DIR = ROOT / "data" / "artifacts" / "task_4146_l0_l2_wide_packetization_handoff"
LANE_RELIABILITY_PATH = ROOT / "data" / "artifacts" / "l0_backfill_orchestration" / "lane_reliability.csv"
SCHEDULER_TASK_NAME = "TraderBrainL0L2Hardening4147"

LANE_STATUS_PATHS = {
    "daily": ROOT / "data" / "artifacts" / "l0_bar_daily_full_backfill" / "background_process.json",
    "five_min": ROOT / "data" / "artifacts" / "l0_bar_full_backfill" / "background_process_5m.json",
    "public_context_news_backfill": ROOT / "data" / "artifacts" / "l0_public_context_news_backfill" / "background_process.json",
    "public_newswire_backfill": ROOT / "data" / "artifacts" / "l0_public_newswire_backfill_shards" / "background_process.json",
    "public_market_macro_news_backfill": ROOT / "data" / "artifacts" / "l0_public_market_macro_news_backfill" / "background_process.json",
}

TARGET_FAMILIES = {
    "public_context_news_feeds",
    "public_market_macro_news_feeds",
    "public_newswire_feeds",
}

MAX_ARTICLE_RAW_BYTES = 5_000_000
MAX_ROWS_BY_SOURCE = {
    "public_context_news_feeds": {
        "cftc_press_releases": 4,
        "federal_register_documents": 2,
        "federal_reserve_press_all": 1,
        "worldbank_news_api": 2,
    },
    "public_newswire_feeds": {
        "businesswire": 6,
        "globenewswire": 4,
        "prnewswire": 6,
    },
}
DEFAULT_MACRO_ROWS_PER_SOURCE = 1
MAX_MACRO_SOURCES = 8

ARTICLE_PACKET_COLUMNS = [
    "task_id",
    "l1_article_packet_id",
    "l0_batch_source_packet_id",
    "source_family",
    "source_key",
    "provider",
    "raw_item_index",
    "raw_item_hash",
    "title",
    "source_url",
    "published_at",
    "source_time_utc",
    "available_to_brain_ts",
    "source_time_basis",
    "source_time_certified",
    "raw_path",
    "raw_sha256",
    "symbol_candidates",
    "entity_candidates",
    "mapping_scope",
    "mapping_status",
    "l1_status",
    "blocker_code",
    "lineage_hash",
    "diagnostic_only",
    "trading_eligible",
    "signal_order_export_allowed",
    "broker_mutation_permitted",
]

FEATURE_COLUMNS = [
    "task_id",
    "diagnostic_feature_id",
    "feature_namespace",
    "feature_name",
    "feature_schema_version",
    "l1_article_packet_id",
    "source_family",
    "source_key",
    "symbol",
    "entity_key",
    "macro_key",
    "event_date",
    "available_to_brain_ts",
    "feature_value",
    "feature_value_type",
    "lineage_hash",
    "raw_path",
    "raw_sha256",
    "diagnostic_only",
    "trading_eligible",
    "signal_order_export_allowed",
    "broker_mutation_permitted",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any, length: int = 24) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            return p.relative_to(ROOT).as_posix()
        except ValueError:
            return p.as_posix()
    return p.as_posix().replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def parse_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"$p=Get-Process -Id {pid} -ErrorAction SilentlyContinue; if ($p) {{ '1' }} else {{ '0' }}",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        return result.stdout.strip().endswith("1")
    try:
        import os

        os.kill(pid, 0)
        return True
    except OSError:
        return False


def source_key_from_path(raw_path: str) -> str:
    for part in re.split(r"[\\/]", raw_path):
        if part.startswith("source="):
            return part.split("=", 1)[1]
    return ""


def normalize_ts(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.endswith("Z"):
        return text
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return f"{text}T12:00:00Z"
    return text.replace("+00:00", "Z")


def date_from_ts(value: str) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", value or "")
    return match.group(1) if match else ""


def read_universe(limit: int = 2000) -> tuple[set[str], dict[str, str]]:
    symbols: set[str] = set()
    names: dict[str, str] = {}
    for row in read_csv(UNIVERSE_PATH)[:limit]:
        symbol = row.get("symbol", "").strip().upper()
        name = row.get("name", "").strip()
        if not symbol:
            continue
        symbols.add(symbol)
        if name and len(name) >= 4:
            names[name.lower()] = symbol
    return symbols, names


def map_text_to_symbols(text: str, symbols: set[str], names: dict[str, str]) -> tuple[list[str], list[str], str]:
    haystack = f" {text} "
    found: set[str] = set()
    entities: set[str] = set()
    for token in re.findall(r"(?<![A-Z0-9])\$?([A-Z]{1,5})(?![A-Z0-9])", haystack):
        if token in symbols:
            found.add(token)
    lower = haystack.lower()
    for name, symbol in names.items():
        if name in lower and len(name) >= 8:
            found.add(symbol)
            entities.add(name)
            if len(found) >= 10:
                break
    status = "HIGH_CONFIDENCE_DETERMINISTIC" if found else "UNMAPPED_DETERMINISTIC"
    return sorted(found), sorted(entities)[:10], status


def article_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    for key in ["headlines", "articles", "items", "rows"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def load_articles_from_raw(raw_path: str, max_items: int) -> tuple[list[dict[str, Any]], str]:
    path = ROOT / raw_path
    try:
        if not path.exists():
            return [], "raw_missing"
        if path.stat().st_size > MAX_ARTICLE_RAW_BYTES:
            return [], "raw_too_large_for_15m_loop"
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001 - artifact records the blocker.
        return [], f"raw_read_error:{type(exc).__name__}"
    rows = article_list(payload)
    return rows[:max_items], "" if rows else "no_article_array"


def article_symbols_and_entities(article: dict[str, Any]) -> tuple[list[str], list[str], str]:
    symbols: set[str] = set()
    entities: set[str] = set()
    for symbol in article.get("symbols", []):
        if isinstance(symbol, str) and symbol.strip():
            symbols.add(symbol.strip().upper())
    for entity in article.get("entities", []):
        if isinstance(entity, str) and entity.strip():
            entities.add(entity.strip())
        elif isinstance(entity, dict):
            symbol = str(entity.get("symbol") or "").strip().upper()
            if symbol:
                symbols.add(symbol)
            name = str(entity.get("name") or entity.get("matched_text") or "").strip()
            if name:
                entities.add(name)
    raw_status = str(article.get("entity_mapping_status") or "").strip()
    return sorted(symbols), sorted(entities), raw_status


def choose_l0_rows() -> list[dict[str, str]]:
    l0_rows = read_csv(L0_4146_DIR / "l0_wide_source_ledger.csv")
    candidates = [
        row for row in l0_rows
        if row.get("source_family") in TARGET_FAMILIES
        and row.get("raw_path_exists") == "1"
        and parse_int(row.get("row_count")) > 0
    ]
    by_family_source: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        source_key = row.get("source_key") or source_key_from_path(row.get("raw_path", ""))
        by_family_source[(row.get("source_family", ""), source_key)].append(row)
    selected: list[dict[str, str]] = []

    def raw_size(row: dict[str, str]) -> int:
        try:
            return (ROOT / row.get("raw_path", "")).stat().st_size
        except OSError:
            return MAX_ARTICLE_RAW_BYTES + 1

    def row_score(row: dict[str, str]) -> tuple[int, int, str, str]:
        mapped = parse_int(row.get("mapped_rows"))
        review = parse_int(row.get("newswire_recall_review_rows")) + parse_int(row.get("entity_candidate_review_rows"))
        return (mapped + review, parse_int(row.get("row_count")), row.get("updated_at", ""), row.get("raw_path", ""))

    for (family, source_key), rows in by_family_source.items():
        readable = [row for row in rows if raw_size(row) <= MAX_ARTICLE_RAW_BYTES]
        readable.sort(key=row_score, reverse=True)
        limit = MAX_ROWS_BY_SOURCE.get(family, {}).get(source_key, 0)
        if limit:
            selected.extend(readable[:limit])

    macro_sources = sorted({source for family, source in by_family_source if family == "public_market_macro_news_feeds"})
    for source_key in macro_sources[:MAX_MACRO_SOURCES]:
        rows = by_family_source.get(("public_market_macro_news_feeds", source_key), [])
        readable = [row for row in rows if raw_size(row) <= MAX_ARTICLE_RAW_BYTES]
        readable.sort(key=row_score, reverse=True)
        selected.extend(readable[:DEFAULT_MACRO_ROWS_PER_SOURCE])

    deduped: dict[str, dict[str, str]] = {}
    for row in selected:
        deduped[row.get("raw_path", "")] = row
    return sorted(
        deduped.values(),
        key=lambda r: (r.get("source_family", ""), r.get("source_key", ""), r.get("updated_at", ""), r.get("raw_path", "")),
    )


def build_article_packets() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    symbols, names = read_universe()
    packets: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for l0 in choose_l0_rows():
        raw_path = l0.get("raw_path", "")
        family = l0.get("source_family", "")
        articles, blocker = load_articles_from_raw(raw_path, max_items=250)
        if blocker:
            blockers.append({
                "task_id": TASK_ID,
                "source_family": family,
                "source_key": l0.get("source_key") or source_key_from_path(raw_path),
                "raw_path": raw_path,
                "blocker_code": blocker,
                "reported_row_count": l0.get("row_count", ""),
                "raw_sha256": l0.get("raw_sha256", ""),
            })
            continue
        for index, article in enumerate(articles):
            title = str(article.get("title") or article.get("headline") or article.get("name") or "").strip()
            source_url = str(article.get("source_url") or article.get("url") or article.get("canonical_url") or article.get("link") or "").strip()
            published = normalize_ts(article.get("published_at") or article.get("event_time") or article.get("date") or article.get("published_at_text"))
            source_time = published or normalize_ts(article.get("captured_at") or l0.get("updated_at"))
            available = normalize_ts(article.get("detected_at") or article.get("captured_at") or l0.get("updated_at") or utc_now())
            raw_item_hash = str(article.get("headline_hash") or stable_hash({"raw_path": raw_path, "index": index, "title": title, "url": source_url}))
            article_symbols, article_entities, raw_mapping_status = article_symbols_and_entities(article)
            mapped_symbols: list[str] = []
            mapped_entities: list[str] = []
            if not article_symbols and not article_entities and family == "public_context_news_feeds":
                mapped_symbols, mapped_entities, _ = map_text_to_symbols(" ".join([title, source_url]), symbols, names)
            symbol_candidates = sorted(set(article_symbols) | set(mapped_symbols))
            entity_candidates = sorted(set(article_entities) | set(mapped_entities))
            if raw_mapping_status and raw_mapping_status not in {"BLOCKED_UNMAPPED", "UNMAPPED_DETERMINISTIC"}:
                map_status = raw_mapping_status
            elif symbol_candidates:
                map_status = "HIGH_CONFIDENCE_DETERMINISTIC"
            elif entity_candidates:
                map_status = "ENTITY_CANDIDATE_REVIEW"
            else:
                map_status = raw_mapping_status or "UNMAPPED_DETERMINISTIC"
            source_key = str(article.get("source_key") or l0.get("source_key") or source_key_from_path(raw_path))
            source_time_certified = "1" if source_time and (article.get("source_time_certified_flag", 1) in [1, "1", True]) else "0"
            l1_status = "READY" if source_time and (title or source_url) else "BLOCKED"
            blocker_code = "" if l1_status == "READY" else "source_time_or_locator_missing"
            if family == "public_newswire_feeds" and not symbol_candidates and not entity_candidates:
                map_status = "NEWSWIRE_MAPPING_REVIEW_REQUIRED"
            elif family != "public_newswire_feeds" and not symbol_candidates:
                map_status = "MACRO_OR_CONTEXT_NO_TICKER_REQUIRED"
            mapping_scope = "TICKER" if symbol_candidates else "ENTITY" if entity_candidates else "MACRO" if family != "public_newswire_feeds" else "UNKNOWN"
            packet_id = "l1article_" + stable_hash({"raw_sha": l0.get("raw_sha256"), "item": raw_item_hash, "index": index})
            lineage = stable_hash({"packet": packet_id, "raw_path": raw_path, "raw_sha256": l0.get("raw_sha256"), "item": raw_item_hash}, 32)
            packets.append({
                "task_id": TASK_ID,
                "l1_article_packet_id": packet_id,
                "l0_batch_source_packet_id": "l1wide_" + stable_hash({"raw_path": raw_path, "sha": l0.get("raw_sha256")}, 18),
                "source_family": family,
                "source_key": source_key,
                "provider": l0.get("provider", ""),
                "raw_item_index": index,
                "raw_item_hash": raw_item_hash,
                "title": title,
                "source_url": source_url,
                "published_at": published,
                "source_time_utc": source_time,
                "available_to_brain_ts": available,
                "source_time_basis": "article_published_at_or_event_time",
                "source_time_certified": source_time_certified,
                "raw_path": raw_path,
                "raw_sha256": l0.get("raw_sha256", ""),
                "symbol_candidates": "|".join(symbol_candidates),
                "entity_candidates": "|".join(entity_candidates),
                "mapping_scope": mapping_scope,
                "mapping_status": map_status,
                "l1_status": l1_status,
                "blocker_code": blocker_code,
                "lineage_hash": lineage,
                "diagnostic_only": "1",
                "trading_eligible": "0",
                "signal_order_export_allowed": "0",
                "broker_mutation_permitted": "0",
            })
    return packets, blockers


def build_newswire_mapping_queue() -> list[dict[str, Any]]:
    rows = [row for row in read_csv(L0_4146_DIR / "l0_wide_source_ledger.csv") if row.get("source_family") == "public_newswire_feeds"]
    queue: list[dict[str, Any]] = []
    for row in rows:
        mapped = parse_int(row.get("mapped_rows"))
        unmapped = parse_int(row.get("blocked_unmapped_rows"))
        ambiguous = parse_int(row.get("blocked_ambiguous_rows"))
        queue.append({
            "task_id": TASK_ID,
            "source_key": row.get("source_key") or source_key_from_path(row.get("raw_path", "")),
            "raw_path": row.get("raw_path", ""),
            "reported_row_count": row.get("row_count", ""),
            "l0_mapped_rows": mapped,
            "l0_unmapped_rows": unmapped,
            "l0_ambiguous_rows": ambiguous,
            "mapping_action": "KEEP_L0_HIGH_CONFIDENCE_AND_REVIEW_UNMAPPED",
            "rule_added": "ticker_token_and_company_name_deterministic_mapper_when_raw_item_is_readable",
            "runtime_note": "newswire raw hydration is not allowed to block the 15m loop",
        })
    return queue


def build_feature_rows(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_rows: list[dict[str, Any]] = []
    for packet in packets:
        if packet["l1_status"] != "READY":
            continue
        if packet["mapping_scope"] == "UNKNOWN":
            continue
        event_date = date_from_ts(packet["source_time_utc"])
        feature_name = "news_article_presence"
        if packet["source_family"] == "public_market_macro_news_feeds":
            feature_name = "macro_news_article_presence"
        elif packet["source_family"] == "public_context_news_feeds":
            feature_name = "official_context_article_presence"
        symbols = packet["symbol_candidates"].split("|") if packet["symbol_candidates"] else [""]
        for symbol in symbols[:5]:
            feature_rows.append({
                "task_id": TASK_ID,
                "diagnostic_feature_id": "l2diag_" + stable_hash({"packet": packet["l1_article_packet_id"], "symbol": symbol, "name": feature_name}),
                "feature_namespace": "l2_diagnostic_news",
                "feature_name": feature_name,
                "feature_schema_version": "2026-06-30.task-4147.v1",
                "l1_article_packet_id": packet["l1_article_packet_id"],
                "source_family": packet["source_family"],
                "source_key": packet["source_key"],
                "symbol": symbol,
                "entity_key": packet["entity_candidates"].split("|")[0] if packet["entity_candidates"] else "",
                "macro_key": packet["source_key"] if packet["mapping_scope"] == "MACRO" else "",
                "event_date": event_date,
                "available_to_brain_ts": packet["available_to_brain_ts"],
                "feature_value": "1",
                "feature_value_type": "presence_indicator",
                "lineage_hash": packet["lineage_hash"],
                "raw_path": packet["raw_path"],
                "raw_sha256": packet["raw_sha256"],
                "diagnostic_only": "1",
                "trading_eligible": "0",
                "signal_order_export_allowed": "0",
                "broker_mutation_permitted": "0",
            })
    return feature_rows


def backfill_rows() -> list[dict[str, Any]]:
    reliability_rows = read_csv(LANE_RELIABILITY_PATH)
    rows: list[dict[str, Any]] = []
    for row in reliability_rows:
        lane = row.get("lane", "")
        if lane not in {"daily", "five_min", "public_context_news_backfill", "public_newswire_backfill", "public_market_macro_news_backfill"}:
            continue
        complete = row.get("complete", "0") == "1"
        progress = parse_int(row.get("completed_units"))
        total = parse_int(row.get("total_units"))
        status = read_json(LANE_STATUS_PATHS.get(lane, ROOT / "missing"), {})
        pid = parse_int(status.get("pid")) if isinstance(status, dict) else 0
        alive = int(pid_alive(pid))
        proof_status = "COMPLETE_PROVEN" if complete else "IN_PROGRESS_OR_INCOMPLETE_PROVEN"
        if not complete and lane in {"public_newswire_backfill", "public_market_macro_news_backfill"} and alive != 1:
            proof_status = "BLOCKED_WORKER_NOT_ALIVE"
        rows.append({
            "task_id": TASK_ID,
            "lane": lane,
            "health": row.get("health", ""),
            "running": row.get("running", ""),
            "complete": row.get("complete", ""),
            "pid_recorded": pid,
            "pid_alive": alive,
            "progress_pct": row.get("progress_pct", ""),
            "completed_units": progress,
            "total_units": total,
            "remaining_units": max(total - progress, 0) if total else "",
            "last_status": row.get("last_status", ""),
            "last_event_at": row.get("last_event_at", ""),
            "proof_status": proof_status,
            "unknown_is_blocker": "1",
            "diagnostic_only_flag": row.get("diagnostic_only_flag", "1"),
            "trade_authority_flag": row.get("trade_authority_flag", "0"),
            "broker_mutation_permitted_flag": row.get("broker_mutation_permitted_flag", "0"),
            "real_capital_permitted_flag": row.get("real_capital_permitted_flag", "0"),
        })
    return rows


def write_operational_config() -> None:
    payload = {
        "version": 1,
        "task_id": TASK_ID,
        "purpose": "safe separated L0 realtime collector config; diagnostic-only; no broker/order/signal authority",
        "based_on": rel(BASE_CONFIG_PATH),
        "activation_posture": "operator_safe_realtime_ready",
        "permissions": {
            "diagnostic_only": True,
            "execution_permitted": 0,
            "broker_mutation_permitted": 0,
            "paper_promotion_permitted": 0,
            "real_capital_permitted": 0,
            "live_order_enabled": 0,
            "buy_sell_signal_generation_permitted": 0,
        },
        "jobs": [
            {
                "name": "public_newswire_feeds_realtime_safe",
                "enabled": True,
                "interval_minutes": 30,
                "allow_network": True,
                "provider": "public_newswire_feeds",
                "mode": "realtime_incremental",
                "sources": ["prnewswire", "globenewswire", "businesswire"],
                "max_items_per_source": 50,
                "request_sleep_seconds": 1,
                "diagnostic_only": True,
            },
            {
                "name": "public_context_news_feeds_realtime_safe",
                "enabled": True,
                "interval_minutes": 30,
                "allow_network": True,
                "provider": "public_context_news_feeds",
                "mode": "realtime_incremental",
                "sources": ["federal_reserve_press_all", "cftc_press_releases", "federal_register_documents"],
                "max_items_per_source": 50,
                "request_sleep_seconds": 1,
                "diagnostic_only": True,
            },
            {
                "name": "public_market_macro_news_feeds_realtime_safe",
                "enabled": True,
                "interval_minutes": 30,
                "allow_network": True,
                "provider": "public_market_macro_news_feeds",
                "mode": "realtime_incremental",
                "sources": ["cnbc_public_rss", "wikimedia_current_events", "nasdaq_trader_notices"],
                "max_items_per_source": 50,
                "request_sleep_seconds": 1,
                "diagnostic_only": True,
            },
        ],
        "runtime_boundary": {
            "chrome_crawling": "smoke_only_not_runtime_collection",
            "codex_gpt": "planning_review_recovery_only_not_runtime_collection",
            "l1_l2_loop_minutes": 15,
            "scheduler_task_name": SCHEDULER_TASK_NAME,
        },
    }
    write_json(CONFIG_PATH, payload)


def write_mapping_rules() -> None:
    payload = {
        "version": 1,
        "task_id": TASK_ID,
        "purpose": "deterministic ticker/entity mapping rules for article packets",
        "rules": [
            {"name": "explicit_ticker_token", "example": "$AAPL or AAPL token", "confidence": "high"},
            {"name": "active_universe_company_name", "source": rel(UNIVERSE_PATH), "confidence": "medium_high"},
            {"name": "existing_l0_newswire_mapper_counts", "confidence": "kept_as_collector_evidence"},
        ],
        "cut": [
            "do_not_force_unknown_newswire_to_ticker",
            "do_not_use_llm_sentiment_or_entity_guessing_in_task_4147",
            "do_not_block_macro_context_when_no_ticker_exists",
        ],
    }
    write_json(ARTIFACT_DIR / "newswire_ticker_entity_mapping_rules.json", payload)


def write_feature_schema() -> None:
    payload = {
        "version": 1,
        "task_id": TASK_ID,
        "schema_name": "l2_diagnostic_news_feature_schema",
        "namespace": "l2_diagnostic_news",
        "diagnostic_only": True,
        "trading_eligible": False,
        "forbidden_downstream": ["signal", "order_intent", "broker", "paper_live", "real_capital", "ranking", "forward_return"],
        "columns": FEATURE_COLUMNS,
        "done_definition": "durable diagnostic feature rows exist with lineage and explicit closed authority flags",
    }
    write_json(ARTIFACT_DIR / "l2_diagnostic_feature_schema.json", payload)


def write_scheduler_proof_placeholder() -> None:
    proof_path = ARTIFACT_DIR / "windows_task_scheduler_registration.json"
    current = read_json(proof_path, {})
    if current:
        return
    write_json(proof_path, {
        "task_id": TASK_ID,
        "task_name": SCHEDULER_TASK_NAME,
        "status": "NOT_REGISTERED_YET",
        "registered_at": "",
    })


def write_manifest(summary: dict[str, Any]) -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4147 task definition and closeout state", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4147 document registry entries", "modified"),
        ("configs/l0_realtime_operational_safe_config_4147.json", "config", "separated safe L0 realtime config", "created"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "TASK-4147 active report pointer", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "TASK-4147 completed task pointer", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "TASK-4147 current status note", "modified"),
        ("scripts/run_l0_l2_hardening_4147.py", "script", "build article packets, mapping proof, feature schema rows, backfill proof", "created"),
        ("scripts/validate_l0_l2_hardening_4147.py", "validator", "validate TASK-4147 outputs", "created"),
        ("scripts/run_l0_l2_hardening_once_4147.ps1", "script", "one-shot 15 minute scheduler target", "created"),
        ("scripts/install_l0_l2_hardening_scheduler_4147.ps1", "script", "register Windows Scheduled Task", "created"),
        (f"docs/reports/{SLUG}/gpt_prompt.md", "gpt_evidence", "GPT Pro prompt", "created"),
        (f"docs/reports/{SLUG}/gpt_response.md", "gpt_evidence", "GPT Pro response", "created"),
        (f"docs/reports/{SLUG}/gpt_review_digest_ko.md", "gpt_evidence", "Korean digest of GPT review and Codex cut", "created"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4147 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4147 artifact manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4147 validation results", "created"),
        (f"docs/reports/{SLUG}/l0_l2_hardening_summary.json", "summary", "machine-readable summary", "created"),
        (f"data/artifacts/{SLUG}/l1_article_packets.csv", "artifact", "row/article-level L1 packets", "created"),
        (f"data/artifacts/{SLUG}/raw_article_packet_blockers.csv", "artifact", "raw files not expanded and why", "created"),
        (f"data/artifacts/{SLUG}/newswire_mapping_review_queue.csv", "artifact", "newswire mapping coverage/review queue", "created"),
        (f"data/artifacts/{SLUG}/newswire_ticker_entity_mapping_rules.json", "artifact", "mapping rule contract", "created"),
        (f"data/artifacts/{SLUG}/l2_diagnostic_feature_schema.json", "artifact", "diagnostic feature schema", "created"),
        (f"data/artifacts/{SLUG}/l2_diagnostic_feature_rows.csv", "artifact", "durable diagnostic feature rows", "created"),
        (f"data/artifacts/{SLUG}/backfill_completion_proof.csv", "artifact", "backfill proof by lane", "created"),
        (f"data/artifacts/{SLUG}/windows_task_scheduler_registration.json", "runtime_evidence", "Windows Task Scheduler proof", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "machine-readable validation report", "created"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [{"path": path, "type": kind, "purpose": purpose, "created_or_modified": state, "task_id": TASK_ID} for path, kind, purpose, state in rows],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )


def write_report(summary: dict[str, Any]) -> None:
    digest = """# TASK-4147 GPT Pro Review Digest

GPT Pro 검수 요지:
- 먼저 L1을 기사/행 단위 packet으로 넓힌다.
- L2는 L1 packet만 먹게 하고, L0 raw 직접 우회는 막는다.
- 뉴스와이어 매핑은 deterministic rule + review queue가 맞다. 모르는 것을 억지 ticker로 만들면 안 된다.
- L0 실시간 config는 기존 보수 config와 분리한다.
- 15분 loop는 무한 루프 하나 더 만들기보다 Windows Task Scheduler에 one-shot job을 15분 반복으로 등록하는 쪽이 안정적이다.
- feature schema에는 올리되, signal/order/broker로는 절대 연결하지 않는다.

Codex cut:
- 대형 DAG/orchestrator 재작성은 하지 않는다.
- LLM sentiment/NER는 넣지 않는다.
- feature store 전체 재구축은 하지 않는다.
- backfill 완료를 과장하지 않고, 완료/미완료/UNKNOWN을 proof로 남긴다.
"""
    (REPORT_DIR / "gpt_review_digest_ko.md").write_text(digest, encoding="utf-8", newline="\n")

    report = "# TASK-4147 L0-L2 Production Hardening\n\n"
    report += "## 결론\n\n"
    report += "TASK-4147은 L0 raw를 L1/L2가 더 넓게 먹도록 만드는 보강 작업이다. 기존 4146의 batch-level handoff 위에 article-level packet, 뉴스와이어 mapping proof, 안전한 실시간 config, 15분 durable loop, backfill proof, diagnostic feature schema를 추가했다.\n\n"
    report += "| 항목 | 값 |\n|---|---:|\n"
    for key in [
        "l1_article_packets",
        "l1_article_ready_packets",
        "raw_article_packet_blockers",
        "newswire_mapping_queue_rows",
        "newswire_l0_mapped_rows",
        "l2_diagnostic_feature_rows",
        "backfill_proof_rows",
        "trading_eligible_rows",
        "signal_order_export_allowed_rows",
        "broker_mutation_permitted_rows",
    ]:
        report += f"| {key} | {summary.get(key, 0)} |\n"
    report += "\n## 중요한 해석\n\n"
    report += "- L1은 이제 batch 하나가 아니라 raw 기사/행 하나를 packet으로 만들 수 있다.\n"
    report += "- L2 diagnostic feature row는 실제 schema row지만 trading feature/signal/order는 아니다.\n"
    report += "- 뉴스와이어 raw가 느리거나 hydrate되지 않는 경우 15분 loop를 막지 않고 review/blocker 증거로 남긴다.\n"
    report += "- L0 실시간 collector용 config는 별도 파일로 분리했고 기존 보수 config를 직접 enable하지 않았다.\n"
    report += "- Windows Task Scheduler 등록 증거는 `windows_task_scheduler_registration.json`에 남긴다.\n"
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")


def build_and_write() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    packets, blockers = build_article_packets()
    mapping_queue = build_newswire_mapping_queue()
    feature_rows = build_feature_rows(packets)
    backfill = backfill_rows()
    write_csv(ARTIFACT_DIR / "l1_article_packets.csv", packets, ARTICLE_PACKET_COLUMNS)
    write_csv(ARTIFACT_DIR / "raw_article_packet_blockers.csv", blockers, ["task_id", "source_family", "source_key", "raw_path", "blocker_code", "reported_row_count", "raw_sha256"])
    write_csv(ARTIFACT_DIR / "newswire_mapping_review_queue.csv", mapping_queue, ["task_id", "source_key", "raw_path", "reported_row_count", "l0_mapped_rows", "l0_unmapped_rows", "l0_ambiguous_rows", "mapping_action", "rule_added", "runtime_note"])
    write_csv(ARTIFACT_DIR / "l2_diagnostic_feature_rows.csv", feature_rows, FEATURE_COLUMNS)
    write_csv(ARTIFACT_DIR / "backfill_completion_proof.csv", backfill, ["task_id", "lane", "health", "running", "complete", "pid_recorded", "pid_alive", "progress_pct", "completed_units", "total_units", "remaining_units", "last_status", "last_event_at", "proof_status", "unknown_is_blocker", "diagnostic_only_flag", "trade_authority_flag", "broker_mutation_permitted_flag", "real_capital_permitted_flag"])
    write_operational_config()
    write_mapping_rules()
    write_feature_schema()
    write_scheduler_proof_placeholder()
    source_counts = Counter(row["source_family"] for row in packets)
    write_csv(
        ARTIFACT_DIR / "article_packet_source_rollup.csv",
        [{"task_id": TASK_ID, "source_family": key, "l1_article_packets": value} for key, value in sorted(source_counts.items())],
        ["task_id", "source_family", "l1_article_packets"],
    )
    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "gpt_review_status": "captured_and_digested",
        "l1_article_packets": len(packets),
        "l1_article_ready_packets": sum(1 for row in packets if row["l1_status"] == "READY"),
        "raw_article_packet_blockers": len(blockers),
        "newswire_mapping_queue_rows": len(mapping_queue),
        "newswire_l0_mapped_rows": sum(parse_int(row.get("l0_mapped_rows")) for row in mapping_queue),
        "l2_diagnostic_feature_rows": len(feature_rows),
        "backfill_proof_rows": len(backfill),
        "critical_incomplete_dead_backfill_lanes": [
            row["lane"]
            for row in backfill
            if row["lane"] in {"public_newswire_backfill", "public_market_macro_news_backfill"}
            and row["complete"] != "1"
            and row["pid_alive"] != 1
        ],
        "separated_realtime_config": rel(CONFIG_PATH),
        "scheduler_task_name": SCHEDULER_TASK_NAME,
        "trading_eligible_rows": sum(1 for row in feature_rows if row["trading_eligible"] != "0"),
        "signal_order_export_allowed_rows": sum(1 for row in feature_rows if row["signal_order_export_allowed"] != "0"),
        "broker_mutation_permitted_rows": sum(1 for row in feature_rows if row["broker_mutation_permitted"] != "0"),
    }
    write_json(REPORT_DIR / "l0_l2_hardening_summary.json", summary)
    write_json(ARTIFACT_DIR / "l0_l2_hardening_summary.json", summary)
    write_report(summary)
    write_manifest(summary)
    return summary


def main() -> int:
    print(json.dumps(build_and_write(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
