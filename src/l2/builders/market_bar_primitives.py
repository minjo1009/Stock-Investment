from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Mapping

import pandas as pd

from src.l2.contracts import L2PrimitiveFact
from src.l2.freshness import FRESH, normalize_freshness_status
from src.l2.lineage import canonical_json, stable_hash, stable_id
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC, require_runtime_context


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _rows(rows: Iterable[Mapping[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
    if isinstance(rows, pd.DataFrame):
        return rows.where(pd.notnull(rows), None).to_dict("records")
    return [dict(row) for row in rows]


def _is_closed(row: Mapping[str, Any], capture_ts: str) -> bool:
    bar_end = pd.to_datetime(row.get("bar_end_ts") or row.get("timestamp"), utc=True, errors="coerce")
    captured = pd.to_datetime(capture_ts, utc=True, errors="coerce")
    if pd.isna(bar_end) or pd.isna(captured):
        return False
    return bool(bar_end <= captured)


def build_market_bar_primitives(
    rows: Iterable[Mapping[str, Any]] | pd.DataFrame,
    *,
    source_receipt_id: str,
    primitive_batch_id: str,
    capture_ts: str | None = None,
    available_to_brain_ts: str | None = None,
    asof_ts: str | None = None,
    runtime_context: str = LIVE_INTRADAY_DIAGNOSTIC,
    provider: str = "runtime_db",
    freshness_status: str = FRESH,
    freshness_status_by_symbol: Mapping[str, str] | None = None,
) -> list[L2PrimitiveFact]:
    if not source_receipt_id:
        raise ValueError("source_receipt_id is required")
    context = require_runtime_context(runtime_context)
    captured = capture_ts or _utc_now()
    available = available_to_brain_ts or captured
    freshness_status_by_symbol = freshness_status_by_symbol or {}
    facts: list[L2PrimitiveFact] = []
    for row in _rows(rows):
        if not _is_closed(row, captured):
            continue
        symbol = str(row.get("symbol") or "").upper() or None
        row_freshness = freshness_status_by_symbol.get(symbol or "", freshness_status)
        event_time = str(row.get("bar_end_ts") or row.get("timestamp") or "")
        source_ts = event_time
        row_asof = asof_ts or event_time
        payload = {
            "bar_id": row.get("bar_id"),
            "bar_start_ts": row.get("bar_start_ts"),
            "bar_end_ts": row.get("bar_end_ts") or row.get("timestamp"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
            "tick_count": row.get("tick_count"),
            "source": row.get("source"),
        }
        input_payload = {
            "source_receipt_id": source_receipt_id,
            "row": payload,
        }
        input_hash = stable_hash(input_payload)
        primitive_id = stable_id("l2fact", primitive_batch_id, source_receipt_id, symbol, event_time, "market_bar")
        lineage_edge_id = stable_id("l2lineage", primitive_id, input_hash)
        output_hash = stable_hash(
            {
                "primitive_id": primitive_id,
                "payload": payload,
                "runtime_context": context,
            }
        )
        facts.append(
            L2PrimitiveFact(
                primitive_id=primitive_id,
                primitive_batch_id=primitive_batch_id,
                source_receipt_id=source_receipt_id,
                source_family="market_bar",
                provider=provider,
                symbol=symbol,
                entity_id=None,
                event_time=event_time,
                source_ts=source_ts,
                capture_ts=captured,
                available_to_brain_ts=available,
                asof_ts=row_asof,
                primitive_type="market",
                primitive_subtype="closed_5m_bar",
                primitive_payload_json=canonical_json(payload),
                freshness_status=normalize_freshness_status(row_freshness),
                source_time_certified=True,
                closed_bar_only=True,
                runtime_context=context,
                input_hash=input_hash,
                output_hash=output_hash,
                lineage_edge_id=lineage_edge_id,
            )
        )
    return facts
