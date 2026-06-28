from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.db.news_l0_l1 import evaluate_news_l1_row

from src.l2.builders.news_event_primitives import build_news_event_primitives
from src.l2.contracts import L2PrimitiveBatch
from src.l2.freshness import BLOCKED, CURRENT_OR_RECENT, LAGGED, MISSING
from src.l2.lineage import canonical_json, stable_hash, stable_id
from src.l2.registry import L2_BUILDER_VERSION
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC, require_runtime_context
from src.l2.stores.primitive_writer import write_l2_batch, write_l2_primitives
from src.l2.stores.sqlite_l2_store import ensure_l2_schema

NEWS_RUNTIME_BUILDER_NAME = "news_runtime_canonical_l2_writer"
DEFAULT_NEWS_EVENT_PATHS = [
    Path("data/artifacts/l0_news_background_queue/collector_events.jsonl"),
    Path("data/artifacts/l0_public_newswire/collector_events.jsonl"),
    Path("data/artifacts/l0_public_context_news/collector_events.jsonl"),
    Path("data/artifacts/l0_public_market_macro_news/collector_events.jsonl"),
    Path("data/artifacts/l0_public_market_macro_news_backfill/collector_events.jsonl"),
]


def _read_jsonl(path: Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if limit is not None and limit >= 0:
        return rows[-int(limit) :]
    return rows


def load_news_collector_events(paths: Iterable[Path], *, limit_per_path: int | None = None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in paths:
        for event in _read_jsonl(path, limit=limit_per_path):
            event = dict(event)
            event["_collector_event_path"] = path.as_posix()
            events.append(event)
    return events


def _load_raw_json(raw_path: str | Path) -> dict[str, Any]:
    path = Path(raw_path)
    if not path.exists() or path.suffix.lower() != ".json":
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _marketaux_rows(event: Mapping[str, Any], raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    payload = raw.get("payload")
    if isinstance(payload, dict) and "payload" in payload and isinstance(payload["payload"], dict):
        payload = payload["payload"]
    if not isinstance(payload, dict):
        return []
    articles = payload.get("data", [])
    symbols = raw.get("symbols") or []
    rows: list[dict[str, Any]] = []
    for article in articles if isinstance(articles, list) else []:
        if not isinstance(article, dict):
            continue
        article_symbols = symbols
        entities = article.get("entities")
        if isinstance(entities, list):
            entity_symbols = [item.get("symbol") for item in entities if isinstance(item, dict) and item.get("symbol")]
            article_symbols = entity_symbols or symbols
        rows.append(
            {
                "provider": "marketaux_news_free",
                "published_at": article.get("published_at") or "",
                "source_url": article.get("url") or article.get("source_url") or "",
                "title": article.get("title") or "",
                "symbols": article_symbols,
                "entities": entities or [],
                "collector_status": event.get("status"),
                "collector_updated_at": event.get("updated_at"),
                "source_id": event.get("source_id"),
                "raw_path": event.get("raw_path"),
                "raw_sha256": event.get("raw_sha256"),
                "row_count": event.get("row_count"),
                "notes": event.get("notes"),
            }
        )
    return rows


def _official_rows(event: Mapping[str, Any], raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    parsed = raw.get("parsed_rows")
    if not isinstance(parsed, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.update(
            {
                "provider": "official_public_releases",
                "collector_status": event.get("status"),
                "collector_updated_at": event.get("updated_at"),
                "source_id": event.get("source_id"),
                "raw_path": event.get("raw_path"),
                "raw_sha256": event.get("raw_sha256"),
                "row_count": event.get("row_count"),
                "notes": event.get("notes"),
            }
        )
        rows.append(row)
    return rows


def _gdelt_rows(event: Mapping[str, Any], raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    payload = raw.get("payload")
    if isinstance(payload, dict) and "payload" in payload and isinstance(payload["payload"], dict):
        payload = payload["payload"]
    if not isinstance(payload, dict):
        return []
    articles = payload.get("articles", [])
    rows: list[dict[str, Any]] = []
    for article in articles if isinstance(articles, list) else []:
        if not isinstance(article, dict):
            continue
        rows.append(
            {
                "provider": "gdelt_news_events",
                "published_at": article.get("seendate") or article.get("date") or "",
                "source_url": article.get("url") or "",
                "title": article.get("title") or "",
                "symbols": [event.get("source_id")] if event.get("source_id") else [],
                "collector_status": event.get("status"),
                "collector_updated_at": event.get("updated_at"),
                "source_id": event.get("source_id"),
                "raw_path": event.get("raw_path"),
                "raw_sha256": event.get("raw_sha256"),
                "row_count": event.get("row_count"),
                "notes": event.get("notes"),
            }
        )
    return rows


def _public_headline_browser_rows(event: Mapping[str, Any], raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    headlines = raw.get("headlines", [])
    if not isinstance(headlines, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in headlines:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "provider": "public_headline_browser_watch",
                "published_at": item.get("published_at") or "",
                "event_time": item.get("event_time") or item.get("detected_at") or raw.get("captured_at") or "",
                "source_url": item.get("url") or item.get("canonical_url") or "",
                "title": item.get("title") or "",
                "symbols": item.get("symbols") or [],
                "entities": item.get("entities") or [],
                "entity_map": item.get("entity_map") or [],
                "entity_mapping_status": item.get("entity_mapping_status") or "",
                "entity_mapping_methods": item.get("entity_mapping_methods") or [],
                "entity_mapping_ambiguous_aliases": item.get("entity_mapping_ambiguous_aliases") or [],
                "entity_mapping_version": item.get("entity_mapping_version") or "",
                "entity_mapping_inferred_flag": item.get("entity_mapping_inferred_flag", 0),
                "detected_at": item.get("detected_at") or raw.get("captured_at") or "",
                "source_page_url": item.get("source_page_url") or raw.get("source_url") or "",
                "headline_hash": item.get("headline_hash") or "",
                "selector_version": raw.get("selector_version") or item.get("selector_version") or "",
                "collector_status": event.get("status"),
                "collector_updated_at": event.get("updated_at"),
                "source_id": event.get("source_id"),
                "raw_path": event.get("raw_path"),
                "raw_sha256": event.get("raw_sha256"),
                "row_count": event.get("row_count"),
                "notes": event.get("notes"),
            }
        )
    return rows


def _public_newswire_rows(event: Mapping[str, Any], raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    headlines = raw.get("headlines", [])
    if not isinstance(headlines, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in headlines:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "provider": "public_newswire_feeds",
                "published_at": item.get("published_at") or "",
                "event_time": item.get("event_time") or item.get("detected_at") or raw.get("captured_at") or "",
                "source_url": item.get("source_url") or item.get("canonical_url") or "",
                "title": item.get("title") or "",
                "symbols": item.get("symbols") or [],
                "entities": item.get("entities") or [],
                "entity_map": item.get("entity_map") or [],
                "entity_mapping_status": item.get("entity_mapping_status") or "",
                "entity_mapping_methods": item.get("entity_mapping_methods") or [],
                "entity_mapping_ambiguous_aliases": item.get("entity_mapping_ambiguous_aliases") or [],
                "entity_mapping_version": item.get("entity_mapping_version") or "",
                "entity_mapping_inferred_flag": item.get("entity_mapping_inferred_flag", 0),
                "detected_at": item.get("detected_at") or raw.get("captured_at") or "",
                "captured_at": item.get("captured_at") or raw.get("captured_at") or "",
                "published_at_text": item.get("published_at_text") or "",
                "source_page_url": item.get("source_page_url") or "",
                "headline_hash": item.get("headline_hash") or "",
                "capture_method": item.get("capture_method") or "",
                "title_source": item.get("title_source") or "",
                "published_at_source": item.get("published_at_source") or "",
                "source_time_certified_flag": item.get("source_time_certified_flag", 0),
                "usable_for_historical_backtest_flag": item.get("usable_for_historical_backtest_flag", 0),
                "source_class": item.get("source_class") or "",
                "context_source_class": item.get("context_source_class") or "",
                "context_scope": item.get("context_scope") or [],
                "context_topic_candidates": item.get("context_topic_candidates") or [],
                "context_classification_methods": item.get("context_classification_methods") or [],
                "macro_context_candidate_flag": item.get("macro_context_candidate_flag", 0),
                "ticker_mapping_required_flag": item.get("ticker_mapping_required_flag", 1),
                "collector_status": event.get("status"),
                "collector_updated_at": event.get("updated_at"),
                "source_id": event.get("source_id"),
                "raw_path": event.get("raw_path"),
                "raw_sha256": event.get("raw_sha256"),
                "row_count": event.get("row_count"),
                "notes": event.get("notes"),
            }
        )
    return rows


def _public_context_news_rows(event: Mapping[str, Any], raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    headlines = raw.get("headlines", [])
    if not isinstance(headlines, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in headlines:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "provider": "public_context_news_feeds",
                "source_key": item.get("source_key") or raw.get("source_key") or "",
                "source_display_name": item.get("source_display_name") or "",
                "published_at": item.get("published_at") or "",
                "event_time": item.get("event_time") or item.get("detected_at") or raw.get("captured_at") or "",
                "source_url": item.get("source_url") or item.get("canonical_url") or "",
                "title": item.get("title") or "",
                "symbols": item.get("symbols") or [],
                "entities": item.get("entities") or [],
                "entity_map": item.get("entity_map") or [],
                "entity_mapping_status": item.get("entity_mapping_status") or "",
                "entity_mapping_methods": item.get("entity_mapping_methods") or [],
                "entity_mapping_version": item.get("entity_mapping_version") or "",
                "entity_mapping_inferred_flag": item.get("entity_mapping_inferred_flag", 0),
                "detected_at": item.get("detected_at") or raw.get("captured_at") or "",
                "captured_at": item.get("captured_at") or raw.get("captured_at") or "",
                "published_at_text": item.get("published_at_text") or "",
                "source_page_url": item.get("source_page_url") or "",
                "headline_hash": item.get("headline_hash") or "",
                "capture_method": item.get("capture_method") or "",
                "title_source": item.get("title_source") or "",
                "published_at_source": item.get("published_at_source") or "",
                "source_time_certified_flag": item.get("source_time_certified_flag", 0),
                "usable_for_historical_backtest_flag": item.get("usable_for_historical_backtest_flag", 0),
                "source_class": item.get("source_class") or "",
                "context_source_class": item.get("context_source_class") or item.get("source_class") or "",
                "context_scope": item.get("context_scope") or [],
                "context_topic_candidates": item.get("context_topic_candidates") or [],
                "macro_context_candidate_flag": item.get("macro_context_candidate_flag", 1),
                "ticker_mapping_required_flag": item.get("ticker_mapping_required_flag", 0),
                "language": item.get("language") or "",
                "document_type": item.get("document_type") or "",
                "agencies": item.get("agencies") or [],
                "docket_ids": item.get("docket_ids") or [],
                "collector_status": event.get("status"),
                "collector_updated_at": event.get("updated_at"),
                "source_id": event.get("source_id"),
                "raw_path": event.get("raw_path"),
                "raw_sha256": event.get("raw_sha256"),
                "row_count": event.get("row_count"),
                "notes": event.get("notes"),
            }
        )
    return rows


def _public_market_macro_news_rows(event: Mapping[str, Any], raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    headlines = raw.get("headlines", [])
    if not isinstance(headlines, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in headlines:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "provider": "public_market_macro_news_feeds",
                "source_key": item.get("source_key") or raw.get("source_key") or "",
                "source_display_name": item.get("source_display_name") or "",
                "published_at": item.get("published_at") or "",
                "event_time": item.get("event_time") or item.get("detected_at") or raw.get("captured_at") or "",
                "source_url": item.get("source_url") or item.get("canonical_url") or "",
                "title": item.get("title") or "",
                "symbols": item.get("symbols") or [],
                "entities": item.get("entities") or [],
                "entity_map": item.get("entity_map") or [],
                "entity_mapping_status": item.get("entity_mapping_status") or "",
                "entity_mapping_methods": item.get("entity_mapping_methods") or [],
                "entity_mapping_version": item.get("entity_mapping_version") or "",
                "entity_mapping_inferred_flag": item.get("entity_mapping_inferred_flag", 0),
                "detected_at": item.get("detected_at") or raw.get("captured_at") or "",
                "captured_at": item.get("captured_at") or raw.get("captured_at") or "",
                "published_at_text": item.get("published_at_text") or "",
                "source_page_url": item.get("source_page_url") or "",
                "headline_hash": item.get("headline_hash") or "",
                "capture_method": item.get("capture_method") or "",
                "title_source": item.get("title_source") or "",
                "published_at_source": item.get("published_at_source") or "",
                "source_time_certified_flag": item.get("source_time_certified_flag", 0),
                "usable_for_historical_backtest_flag": item.get("usable_for_historical_backtest_flag", 0),
                "source_class": item.get("source_class") or "",
                "context_source_class": item.get("context_source_class") or item.get("source_class") or "",
                "context_scope": item.get("context_scope") or [],
                "context_topic_candidates": item.get("context_topic_candidates") or [],
                "macro_context_candidate_flag": item.get("macro_context_candidate_flag", 1),
                "ticker_mapping_required_flag": item.get("ticker_mapping_required_flag", 0),
                "language": item.get("language") or "",
                "document_type": item.get("document_type") or "",
                "section_id": item.get("section_id") or "",
                "summary": item.get("summary") or "",
                "collector_status": event.get("status"),
                "collector_updated_at": event.get("updated_at"),
                "source_id": event.get("source_id"),
                "raw_path": event.get("raw_path"),
                "raw_sha256": event.get("raw_sha256"),
                "row_count": event.get("row_count"),
                "notes": event.get("notes"),
            }
        )
    return rows


def _event_blocker_row(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "provider": event.get("provider") or event.get("source_family") or "",
        "source_id": event.get("source_id") or "",
        "published_at": "",
        "source_url": "",
        "title": "",
        "symbols": [],
        "collector_status": event.get("status") or "",
        "collector_updated_at": event.get("updated_at") or "",
        "raw_path": event.get("raw_path") or "",
        "raw_sha256": event.get("raw_sha256") or "",
        "row_count": event.get("row_count") or 0,
        "notes": event.get("notes") or event.get("error_category") or "",
        "freshness_status": _event_freshness(event),
    }


def _event_freshness(event: Mapping[str, Any]) -> str:
    status = str(event.get("status") or "").upper()
    if status == "EXPORTED":
        return CURRENT_OR_RECENT
    if status == "EMPTY_PROVIDER_RESPONSE":
        return MISSING
    if status in {"RATE_LIMITED", "SKIPPED_QUERY_TOO_BROAD", "SKIPPED_EXISTS"}:
        return LAGGED
    return BLOCKED


def news_rows_from_collector_event(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = _load_raw_json(str(event.get("raw_path") or ""))
    provider = str(event.get("provider") or event.get("source_family") or "")
    rows: list[dict[str, Any]] = []
    if provider == "official_public_releases":
        rows = _official_rows(event, raw)
    elif provider == "marketaux_news_free":
        rows = _marketaux_rows(event, raw)
    elif provider == "gdelt_news_events":
        rows = _gdelt_rows(event, raw)
    elif provider == "public_headline_browser_watch":
        rows = _public_headline_browser_rows(event, raw)
    elif provider == "public_newswire_feeds":
        rows = _public_newswire_rows(event, raw)
    elif provider == "public_context_news_feeds":
        rows = _public_context_news_rows(event, raw)
    elif provider == "public_market_macro_news_feeds":
        rows = _public_market_macro_news_rows(event, raw)
    if rows:
        out: list[dict[str, Any]] = []
        for row in rows:
            evaluation = evaluate_news_l1_row(row).as_dict()
            row.update(
                {
                    "authority_class": evaluation["authority_class"],
                    "promotion_status": evaluation["promotion_status"],
                    "quality_flags": evaluation["quality_flags"],
                    "freshness_status": _event_freshness(event),
                }
            )
            out.append(row)
        return out
    return [_event_blocker_row(event)]


def _write_news_source_receipt(
    conn: sqlite3.Connection,
    *,
    source_receipt_id: str,
    runtime_context: str,
    source_table: str,
    provider: str,
    captured_at: str,
    asof_ts: str,
    rows: list[dict[str, Any]],
    freshness_status: str,
) -> None:
    symbols = sorted({symbol for row in rows for symbol in _symbols(row)})
    conn.execute(
        """
        INSERT OR REPLACE INTO l2_runtime_source_receipts(
            source_receipt_id, runtime_context, source_table, source_family, provider, symbol_set,
            captured_at, asof_ts, row_count, input_hash, freshness_status, diagnostic_only
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,1)
        """,
        (
            source_receipt_id,
            runtime_context,
            source_table,
            "news_event",
            provider,
            canonical_json(symbols),
            captured_at,
            asof_ts,
            len(rows),
            stable_hash({"source_table": source_table, "rows": rows}),
            freshness_status,
        ),
    )
    conn.commit()


def _symbols(row: Mapping[str, Any]) -> list[str]:
    value = row.get("symbols") or []
    if isinstance(value, str):
        values = value.replace("|", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = []
    return sorted({str(symbol).strip().upper() for symbol in values if str(symbol).strip()})


def write_news_l2_primitives(
    conn: sqlite3.Connection,
    *,
    events: Iterable[Mapping[str, Any]],
    capture_ts: str,
    runtime_context: str = LIVE_INTRADAY_DIAGNOSTIC,
    source_table: str = "l0_news_collector_events",
    provider: str = "news_collector",
    max_lag_minutes: float = 180.0,
) -> dict[str, Any]:
    ensure_l2_schema(conn)
    context = require_runtime_context(runtime_context)
    event_list = [dict(event) for event in events]
    news_rows = [row for event in event_list for row in news_rows_from_collector_event(event)]
    source_receipt_id = stable_id("l2receipt", "news", context, capture_ts, stable_hash(event_list))
    primitive_batch_id = stable_id("l2batch", "news", context, capture_ts, source_receipt_id)
    freshness_values = {str(row.get("freshness_status") or "") for row in news_rows}
    receipt_freshness = CURRENT_OR_RECENT if freshness_values and freshness_values <= {CURRENT_OR_RECENT} else (MISSING if not news_rows else LAGGED)
    _write_news_source_receipt(
        conn,
        source_receipt_id=source_receipt_id,
        runtime_context=context,
        source_table=source_table,
        provider=provider,
        captured_at=capture_ts,
        asof_ts=capture_ts,
        rows=news_rows,
        freshness_status=receipt_freshness,
    )
    batch = L2PrimitiveBatch(
        primitive_batch_id=primitive_batch_id,
        runtime_context=context,
        builder_name=NEWS_RUNTIME_BUILDER_NAME,
        builder_version=L2_BUILDER_VERSION,
        asof_ts=capture_ts,
        created_at=capture_ts,
        source_family_set=canonical_json(["news_event"]),
        symbol_set=canonical_json(sorted({symbol for row in news_rows for symbol in _symbols(row)})),
        row_count=len(news_rows),
        input_hash=stable_hash({"receipt": source_receipt_id, "events": event_list}),
        output_hash=stable_hash({"batch": primitive_batch_id, "rows": news_rows}),
    )
    facts = build_news_event_primitives(
        news_rows,
        source_receipt_id=source_receipt_id,
        primitive_batch_id=primitive_batch_id,
        capture_ts=capture_ts,
        available_to_brain_ts=capture_ts,
        asof_ts=capture_ts,
        runtime_context=context,
        provider=provider,
        max_lag_minutes=max_lag_minutes,
    )
    write_l2_batch(conn, batch)
    write_l2_primitives(conn, facts)
    conn.execute(
        """
        UPDATE l2_runtime_context_audit
        SET historical_artifact_count = 0,
            live_evidence_count = ?,
            mixed_context_violation_flag = 0,
            freshness_violation_flag = 0,
            source_time_violation_flag = 0
        WHERE batch_id = ?
        """,
        (len(facts), primitive_batch_id),
    )
    conn.commit()
    return {
        "runtime_context": context,
        "news_source_receipt_id": source_receipt_id,
        "news_batch_id": primitive_batch_id,
        "news_fact_count": len(facts),
        "input_event_count": len(event_list),
        "diagnostic_only": True,
        "trade_output_flag": 0,
        "score_output_flag": 0,
        "order_intent_flag": 0,
    }
