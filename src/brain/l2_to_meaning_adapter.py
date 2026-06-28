from __future__ import annotations

import sqlite3

from src.l2.contracts import L2PrimitiveFact
from src.l2.runtime_context import require_runtime_context
from src.l2.stores.primitive_reader import load_l3_inputs


def load_canonical_l2_meaning_inputs(
    conn: sqlite3.Connection,
    *,
    asof_ts: str,
    runtime_context: str,
    symbols: list[str] | None = None,
    allow_stale_diagnostic: bool = False,
) -> list[L2PrimitiveFact]:
    context = require_runtime_context(runtime_context)
    return load_l3_inputs(
        conn,
        asof_ts=asof_ts,
        runtime_context=context,
        symbols=symbols,
        allow_stale_diagnostic=allow_stale_diagnostic,
    )
