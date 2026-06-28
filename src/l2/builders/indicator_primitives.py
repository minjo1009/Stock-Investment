from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Mapping

import pandas as pd

from src.l2.contracts import L2PrimitiveFact
from src.l2.freshness import child_freshness_from_parent, freshness_from_runtime_flags
from src.l2.lineage import canonical_json, stable_hash, stable_id
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC, require_runtime_context

INDICATOR_PAYLOAD_COLUMNS = [
    "snapshot_id",
    "created_at",
    "symbol",
    "bar_end_ts",
    "close",
    "ma20",
    "ma50",
    "ma200",
    "breakout_high_20",
    "breakout_condition",
    "ma_condition",
    "data_fresh",
    "insufficient_history",
    "source_price_ts",
    "source_price",
    "source_type",
    "freshness_age_sec",
    "stale_reason",
]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _rows(rows: Iterable[Mapping[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
    if isinstance(rows, pd.DataFrame):
        return rows.where(pd.notnull(rows), None).to_dict("records")
    return [dict(row) for row in rows]


def build_indicator_primitives(
    rows: Iterable[Mapping[str, Any]] | pd.DataFrame,
    *,
    source_receipt_id: str,
    primitive_batch_id: str,
    capture_ts: str | None = None,
    available_to_brain_ts: str | None = None,
    asof_ts: str | None = None,
    runtime_context: str = LIVE_INTRADAY_DIAGNOSTIC,
    provider: str = "runtime_db",
    parent_freshness_by_symbol: Mapping[str, str] | None = None,
) -> list[L2PrimitiveFact]:
    if not source_receipt_id:
        raise ValueError("source_receipt_id is required")
    context = require_runtime_context(runtime_context)
    captured = capture_ts or _utc_now()
    available = available_to_brain_ts or captured
    parent_freshness_by_symbol = parent_freshness_by_symbol or {}
    facts: list[L2PrimitiveFact] = []
    for row in _rows(rows):
        symbol = str(row.get("symbol") or "").upper() or None
        event_time = str(row.get("bar_end_ts") or row.get("source_price_ts") or row.get("created_at") or "")
        source_ts = str(row.get("source_price_ts") or event_time)
        row_asof = asof_ts or str(row.get("created_at") or event_time)
        source_type = str(row.get("source_type") or "").upper()
        stale_reason = str(row.get("stale_reason") or "").upper()
        source_time_certified = bool(source_ts) and source_type != "MISSING_SOURCE" and stale_reason != "MISSING_SOURCE"
        local_freshness = freshness_from_runtime_flags(
            data_fresh=row.get("data_fresh"),
            stale_reason=row.get("stale_reason"),
        )
        parent_freshness = parent_freshness_by_symbol.get(symbol or "", local_freshness)
        freshness_status = child_freshness_from_parent(parent_freshness, local_freshness)
        payload = {col: row.get(col) for col in INDICATOR_PAYLOAD_COLUMNS if col in row}
        input_payload = {
            "source_receipt_id": source_receipt_id,
            "row": payload,
            "parent_freshness": parent_freshness,
        }
        input_hash = stable_hash(input_payload)
        primitive_id = stable_id("l2fact", primitive_batch_id, source_receipt_id, symbol, event_time, "indicator")
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
                source_family="indicator",
                provider=provider,
                symbol=symbol,
                entity_id=None,
                event_time=event_time,
                source_ts=source_ts,
                capture_ts=captured,
                available_to_brain_ts=available,
                asof_ts=row_asof,
                primitive_type="indicator",
                primitive_subtype="runtime_local_feature_snapshot",
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
