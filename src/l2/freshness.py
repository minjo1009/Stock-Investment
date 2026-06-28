from __future__ import annotations

FRESH = "FRESH"
CURRENT_OR_RECENT = "CURRENT_OR_RECENT"
STALE = "STALE"
LAGGED = "LAGGED"
MISSING = "MISSING"
BLOCKED = "BLOCKED"
UNKNOWN = "UNKNOWN"

ALLOWED_FRESHNESS_STATUSES = {
    FRESH,
    CURRENT_OR_RECENT,
    STALE,
    LAGGED,
    MISSING,
    BLOCKED,
    UNKNOWN,
}


def normalize_freshness_status(value: object) -> str:
    status = str(value or "").strip().upper()
    if status in ALLOWED_FRESHNESS_STATUSES:
        return status
    if status in {"1", "TRUE", "YES"}:
        return FRESH
    if status in {"0", "FALSE", "NO"}:
        return STALE
    return UNKNOWN


def freshness_from_runtime_flags(*, data_fresh: object = None, stale_reason: object = None) -> str:
    if str(stale_reason or "").strip().upper() == "MISSING_SOURCE":
        return MISSING
    if str(data_fresh).strip().lower() in {"1", "1.0", "true", "yes"}:
        return FRESH
    if data_fresh is not None:
        return STALE
    return UNKNOWN


def child_freshness_from_parent(parent_status: str, local_status: str) -> str:
    parent = normalize_freshness_status(parent_status)
    local = normalize_freshness_status(local_status)
    if parent in {STALE, LAGGED, MISSING, BLOCKED}:
        return parent
    return local
