from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from src.l2.builders.indicator_primitives import build_indicator_primitives
from src.l2.builders.market_bar_primitives import build_market_bar_primitives
from src.l2.contracts import L2PrimitiveBatch
from src.l2.freshness import FRESH, MISSING, STALE
from src.l2.lineage import canonical_json, stable_hash, stable_id
from src.l2.registry import L2_BUILDER_VERSION
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC
from src.l2.stores.primitive_writer import write_l2_batch, write_l2_primitives
from src.l2.stores.sqlite_l2_store import ensure_l2_schema

LIVE_RUNTIME_BUILDER_NAME = "live_runtime_canonical_l2_writer"


def _rows(rows: Iterable[Mapping[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
    if isinstance(rows, pd.DataFrame):
        return rows.where(pd.notnull(rows), None).to_dict("records")
    return [dict(row) for row in rows]


def _symbols(symbols: Iterable[str]) -> list[str]:
    return sorted({str(symbol or "").strip().upper() for symbol in symbols if str(symbol or "").strip()})


def _indicator_rows_with_runtime_ids(rows: list[dict[str, Any]], *, capture_ts: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        symbol = str(row.get("symbol") or "").strip().upper()
        if symbol:
            row.setdefault("snapshot_id", f"{capture_ts}:{symbol}")
        row.setdefault("created_at", capture_ts)
        out.append(row)
    return out


def _read_recent_closed_market_bars(
    conn: sqlite3.Connection,
    *,
    symbols: list[str],
    capture_ts: str,
    limit_per_symbol: int,
) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "market_bars_5m" not in tables:
        return []
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        rows.extend(
            [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT bar_id, symbol, bar_start_ts, bar_end_ts, open, high, low, close, volume, tick_count, source, last_updated_at
                    FROM market_bars_5m
                    WHERE symbol = ?
                      AND bar_end_ts <= ?
                    ORDER BY bar_end_ts DESC
                    LIMIT ?
                    """,
                    (symbol, capture_ts, int(limit_per_symbol)),
                ).fetchall()
            ]
        )
    rows.sort(key=lambda row: (str(row.get("symbol") or ""), str(row.get("bar_end_ts") or "")))
    return rows


def _freshness_by_symbol(
    market_rows: list[dict[str, Any]],
    *,
    symbols: list[str],
    capture_ts: str,
    max_age_minutes: float,
) -> dict[str, str]:
    captured = pd.to_datetime(capture_ts, utc=True, errors="coerce")
    latest_by_symbol: dict[str, pd.Timestamp] = {}
    for row in market_rows:
        symbol = str(row.get("symbol") or "").upper()
        bar_end = pd.to_datetime(row.get("bar_end_ts"), utc=True, errors="coerce")
        if not symbol or pd.isna(bar_end):
            continue
        if symbol not in latest_by_symbol or bar_end > latest_by_symbol[symbol]:
            latest_by_symbol[symbol] = bar_end
    result: dict[str, str] = {}
    for symbol in symbols:
        latest = latest_by_symbol.get(symbol)
        if latest is None or pd.isna(captured):
            result[symbol] = MISSING
            continue
        age_minutes = (captured - latest).total_seconds() / 60.0
        result[symbol] = FRESH if age_minutes <= float(max_age_minutes) else STALE
    return result


def _write_source_receipt(
    conn: sqlite3.Connection,
    *,
    source_receipt_id: str,
    source_table: str,
    source_family: str,
    provider: str,
    symbols: list[str],
    captured_at: str,
    asof_ts: str,
    rows: list[dict[str, Any]],
    freshness_status: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO l2_runtime_source_receipts(
            source_receipt_id, runtime_context, source_table, source_family, provider, symbol_set,
            captured_at, asof_ts, row_count, input_hash, freshness_status, diagnostic_only
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,1)
        """,
        (
            source_receipt_id,
            LIVE_INTRADAY_DIAGNOSTIC,
            source_table,
            source_family,
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


def _write_audit_counts(conn: sqlite3.Connection, *, batch_id: str, row_count: int, freshness_violation: bool = False, source_time_violation: bool = False) -> None:
    conn.execute(
        """
        UPDATE l2_runtime_context_audit
        SET historical_artifact_count = 0,
            live_evidence_count = ?,
            mixed_context_violation_flag = 0,
            freshness_violation_flag = ?,
            source_time_violation_flag = ?
        WHERE batch_id = ?
        """,
        (int(row_count), 1 if freshness_violation else 0, 1 if source_time_violation else 0, batch_id),
    )
    conn.commit()


def write_live_runtime_l2_primitives(
    conn: sqlite3.Connection,
    *,
    capture_ts: str,
    symbols: Iterable[str],
    indicator_rows: Iterable[Mapping[str, Any]] | pd.DataFrame,
    market_bar_limit_per_symbol: int = 320,
    freshness_max_age_minutes: float = 15.0,
) -> dict[str, Any]:
    ensure_l2_schema(conn)
    symbol_list = _symbols(symbols)
    indicator_list = _indicator_rows_with_runtime_ids(_rows(indicator_rows), capture_ts=capture_ts)
    if not symbol_list:
        symbol_list = _symbols(str(row.get("symbol") or "") for row in indicator_list)
    market_rows = _read_recent_closed_market_bars(
        conn,
        symbols=symbol_list,
        capture_ts=capture_ts,
        limit_per_symbol=market_bar_limit_per_symbol,
    )
    parent_freshness = _freshness_by_symbol(
        market_rows,
        symbols=symbol_list,
        capture_ts=capture_ts,
        max_age_minutes=freshness_max_age_minutes,
    )
    aggregate_market_freshness = FRESH if market_rows and all(status == FRESH for status in parent_freshness.values()) else STALE

    market_receipt_id = stable_id("l2receipt", "market_bars_5m", capture_ts, stable_hash(market_rows))
    indicator_receipt_id = stable_id("l2receipt", "indicator_snapshots", capture_ts, stable_hash(indicator_list))
    market_batch_id = stable_id("l2batch", "live_market_bars", capture_ts, market_receipt_id)
    indicator_batch_id = stable_id("l2batch", "live_indicator_snapshots", capture_ts, indicator_receipt_id)

    _write_source_receipt(
        conn,
        source_receipt_id=market_receipt_id,
        source_table="market_bars_5m",
        source_family="market_bar",
        provider="runtime_db",
        symbols=symbol_list,
        captured_at=capture_ts,
        asof_ts=capture_ts,
        rows=market_rows,
        freshness_status=aggregate_market_freshness,
    )
    market_batch = L2PrimitiveBatch(
        primitive_batch_id=market_batch_id,
        runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
        builder_name=LIVE_RUNTIME_BUILDER_NAME,
        builder_version=L2_BUILDER_VERSION,
        asof_ts=capture_ts,
        created_at=capture_ts,
        source_family_set=canonical_json(["market_bar"]),
        symbol_set=canonical_json(symbol_list),
        row_count=len(market_rows),
        input_hash=stable_hash({"receipt": market_receipt_id, "rows": market_rows}),
        output_hash=stable_hash({"batch": market_batch_id, "rows": market_rows}),
    )
    market_facts = build_market_bar_primitives(
        market_rows,
        source_receipt_id=market_receipt_id,
        primitive_batch_id=market_batch_id,
        capture_ts=capture_ts,
        available_to_brain_ts=capture_ts,
        asof_ts=capture_ts,
        freshness_status=aggregate_market_freshness,
        freshness_status_by_symbol=parent_freshness,
    )
    write_l2_batch(conn, market_batch)
    write_l2_primitives(conn, market_facts)
    _write_audit_counts(conn, batch_id=market_batch_id, row_count=len(market_facts))

    _write_source_receipt(
        conn,
        source_receipt_id=indicator_receipt_id,
        source_table="indicator_snapshots",
        source_family="indicator",
        provider="runtime_db",
        symbols=symbol_list,
        captured_at=capture_ts,
        asof_ts=capture_ts,
        rows=indicator_list,
        freshness_status=FRESH if indicator_list else MISSING,
    )
    indicator_batch = L2PrimitiveBatch(
        primitive_batch_id=indicator_batch_id,
        runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
        builder_name=LIVE_RUNTIME_BUILDER_NAME,
        builder_version=L2_BUILDER_VERSION,
        asof_ts=capture_ts,
        created_at=capture_ts,
        source_family_set=canonical_json(["indicator"]),
        symbol_set=canonical_json(symbol_list),
        row_count=len(indicator_list),
        input_hash=stable_hash({"receipt": indicator_receipt_id, "rows": indicator_list, "parent_freshness": parent_freshness}),
        output_hash=stable_hash({"batch": indicator_batch_id, "rows": indicator_list}),
    )
    indicator_facts = build_indicator_primitives(
        indicator_list,
        source_receipt_id=indicator_receipt_id,
        primitive_batch_id=indicator_batch_id,
        capture_ts=capture_ts,
        available_to_brain_ts=capture_ts,
        asof_ts=capture_ts,
        parent_freshness_by_symbol=parent_freshness,
    )
    write_l2_batch(conn, indicator_batch)
    write_l2_primitives(conn, indicator_facts)
    _write_audit_counts(conn, batch_id=indicator_batch_id, row_count=len(indicator_facts))
    return {
        "runtime_context": LIVE_INTRADAY_DIAGNOSTIC,
        "market_source_receipt_id": market_receipt_id,
        "indicator_source_receipt_id": indicator_receipt_id,
        "market_batch_id": market_batch_id,
        "indicator_batch_id": indicator_batch_id,
        "market_fact_count": len(market_facts),
        "indicator_fact_count": len(indicator_facts),
        "parent_freshness_by_symbol": parent_freshness,
        "diagnostic_only": True,
        "trade_output_flag": 0,
        "score_output_flag": 0,
        "order_intent_flag": 0,
    }


def write_live_runtime_l2_primitives_from_db(
    db_path: str | Path,
    *,
    capture_ts: str,
    symbols: Iterable[str],
    indicator_rows: Iterable[Mapping[str, Any]] | pd.DataFrame,
    market_bar_limit_per_symbol: int = 320,
) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        return write_live_runtime_l2_primitives(
            conn,
            capture_ts=capture_ts,
            symbols=symbols,
            indicator_rows=indicator_rows,
            market_bar_limit_per_symbol=market_bar_limit_per_symbol,
        )
    finally:
        conn.close()
