from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Mapping

import pandas as pd

from src.l2.contracts import L2PrimitiveFact
from src.l2.freshness import BLOCKED, CURRENT_OR_RECENT, LAGGED, MISSING, normalize_freshness_status
from src.l2.lineage import canonical_json, stable_hash, stable_id
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC, require_runtime_context

NEWS_PAYLOAD_COLUMNS = [
    "provider",
    "source_id",
    "source_key",
    "source_display_name",
    "published_at",
    "source_url",
    "title",
    "symbols",
    "entities",
    "entity_map",
    "entity_mapping_status",
    "entity_mapping_methods",
    "entity_mapping_ambiguous_aliases",
    "entity_mapping_version",
    "entity_mapping_inferred_flag",
    "detected_at",
    "source_page_url",
    "headline_hash",
    "selector_version",
    "capture_method",
    "title_source",
    "published_at_source",
    "source_time_certified_flag",
    "usable_for_historical_backtest_flag",
    "source_class",
    "context_source_class",
    "context_scope",
    "context_topic_candidates",
    "context_classification_methods",
    "macro_context_candidate_flag",
    "ticker_mapping_required_flag",
    "language",
    "document_type",
    "section_id",
    "summary",
    "agencies",
    "docket_ids",
    "authority_class",
    "promotion_status",
    "quality_flags",
    "raw_path",
    "raw_sha256",
    "collector_status",
    "collector_updated_at",
    "row_count",
    "notes",
]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _rows(rows: Iterable[Mapping[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
    if isinstance(rows, pd.DataFrame):
        return rows.where(pd.notnull(rows), None).to_dict("records")
    return [dict(row) for row in rows]


def _symbols(row: Mapping[str, Any]) -> list[str]:
    value = row.get("symbols") or row.get("tickers") or []
    if isinstance(value, str):
        parts = value.replace("|", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        parts = []
    return sorted({str(part).strip().upper() for part in parts if str(part).strip()})


def _event_time(row: Mapping[str, Any], fallback: str) -> tuple[str, bool]:
    for key in ("published_at", "publication_time", "published_ts", "event_time", "source_ts"):
        value = str(row.get(key) or "").strip()
        if value:
            return value, True
    return fallback, False


def _provider_freshness(row: Mapping[str, Any], *, capture_ts: str, max_lag_minutes: float) -> str:
    status = str(row.get("collector_status") or row.get("status") or "").upper()
    if status in {"CREDENTIAL_BLOCKED", "FAILED_RETRYABLE", "BLOCKED"}:
        return BLOCKED
    if status in {"RATE_LIMITED", "SKIPPED_QUERY_TOO_BROAD"}:
        return LAGGED
    if status == "EMPTY_PROVIDER_RESPONSE":
        return MISSING
    collector_updated_at = str(row.get("collector_updated_at") or row.get("updated_at") or capture_ts)
    captured = pd.to_datetime(capture_ts, utc=True, errors="coerce")
    updated = pd.to_datetime(collector_updated_at, utc=True, errors="coerce")
    if pd.isna(captured) or pd.isna(updated):
        return LAGGED
    lag_minutes = (captured - updated).total_seconds() / 60.0
    return CURRENT_OR_RECENT if lag_minutes <= float(max_lag_minutes) else LAGGED


def build_news_event_primitives(
    rows: Iterable[Mapping[str, Any]] | pd.DataFrame,
    *,
    source_receipt_id: str,
    primitive_batch_id: str,
    capture_ts: str | None = None,
    available_to_brain_ts: str | None = None,
    asof_ts: str | None = None,
    runtime_context: str = LIVE_INTRADAY_DIAGNOSTIC,
    provider: str = "news_collector",
    max_lag_minutes: float = 180.0,
) -> list[L2PrimitiveFact]:
    if not source_receipt_id:
        raise ValueError("source_receipt_id is required")
    context = require_runtime_context(runtime_context)
    captured = capture_ts or _utc_now()
    available = available_to_brain_ts or captured
    facts: list[L2PrimitiveFact] = []
    for idx, row in enumerate(_rows(rows), start=1):
        row_provider = str(row.get("provider") or provider)
        event_time, source_time_certified = _event_time(row, captured)
        row_asof = asof_ts or str(row.get("collector_updated_at") or row.get("updated_at") or captured)
        symbols = _symbols(row)
        freshness_status = normalize_freshness_status(
            str(row.get("freshness_status") or _provider_freshness(row, capture_ts=captured, max_lag_minutes=max_lag_minutes))
        )
        payload = {col: row.get(col) for col in NEWS_PAYLOAD_COLUMNS if col in row}
        payload["symbols"] = symbols
        input_payload = {
            "source_receipt_id": source_receipt_id,
            "row": payload,
        }
        input_hash = stable_hash(input_payload)
        primitive_id = stable_id(
            "l2fact",
            primitive_batch_id,
            source_receipt_id,
            row_provider,
            event_time,
            row.get("source_url") or row.get("source_id") or idx,
        )
        lineage_edge_id = stable_id("l2lineage", primitive_id, input_hash)
        output_hash = stable_hash(
            {
                "primitive_id": primitive_id,
                "payload": payload,
                "runtime_context": context,
                "freshness_status": freshness_status,
            }
        )
        facts.append(
            L2PrimitiveFact(
                primitive_id=primitive_id,
                primitive_batch_id=primitive_batch_id,
                source_receipt_id=source_receipt_id,
                source_family="news_event",
                provider=row_provider,
                symbol=symbols[0] if len(symbols) == 1 else None,
                entity_id=None,
                event_time=event_time,
                source_ts=event_time,
                capture_ts=captured,
                available_to_brain_ts=available,
                asof_ts=row_asof,
                primitive_type="news",
                primitive_subtype=str(row.get("primitive_subtype") or row_provider),
                primitive_payload_json=canonical_json(payload),
                freshness_status=freshness_status,
                source_time_certified=source_time_certified,
                closed_bar_only=True,
                runtime_context=context,
                input_hash=input_hash,
                output_hash=output_hash,
                lineage_edge_id=lineage_edge_id,
            )
        )
    return facts
