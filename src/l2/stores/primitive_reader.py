from __future__ import annotations

import sqlite3

from src.l2.contracts import L2PrimitiveFact
from src.l2.runtime_context import require_runtime_context


def load_l3_inputs(
    conn: sqlite3.Connection,
    *,
    asof_ts: str,
    runtime_context: str,
    symbols: list[str] | None = None,
    allow_stale_diagnostic: bool = False,
) -> list[L2PrimitiveFact]:
    context = require_runtime_context(runtime_context)
    freshness_clause = "" if allow_stale_diagnostic else "AND freshness_status IN ('FRESH', 'CURRENT_OR_RECENT')"
    params: list[object] = [asof_ts, context]
    symbol_clause = ""
    if symbols:
        placeholders = ",".join(["?"] * len(symbols))
        symbol_clause = f"AND symbol IN ({placeholders})"
        params.extend([str(symbol).upper() for symbol in symbols])
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"""
        SELECT *
        FROM l2_primitive_facts
        WHERE asof_ts <= ?
          AND runtime_context = ?
          AND source_time_certified = 1
          {freshness_clause}
          AND diagnostic_only = 1
          AND missing_source_is_negative = 0
          AND trade_output_flag = 0
          AND score_output_flag = 0
          AND order_intent_flag = 0
          {symbol_clause}
        ORDER BY asof_ts, primitive_id
        """,
        params,
    ).fetchall()
    return [L2PrimitiveFact.from_row(row) for row in rows]
