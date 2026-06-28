from __future__ import annotations

from enum import StrEnum

from src.l2.runtime_context import LIVE_CONTEXTS


class L3SourceGap(StrEnum):
    MISSING_RAW_SOURCE = "MISSING_RAW_SOURCE"
    MISSING_L2_PRIMITIVE = "MISSING_L2_PRIMITIVE"
    MISSING_ASOF_TIMESTAMP = "MISSING_ASOF_TIMESTAMP"
    MISSING_CONFIRMATION = "MISSING_CONFIRMATION"
    MISSING_COMPARATOR = "MISSING_COMPARATOR"
    MISSING_DENOMINATOR = "MISSING_DENOMINATOR"
    MISSING_FRESHNESS_CERTIFICATION = "MISSING_FRESHNESS_CERTIFICATION"
    DISCOVERY_ONLY_SOURCE = "DISCOVERY_ONLY_SOURCE"
    STALE_SOURCE = "STALE_SOURCE"
    UNCERTIFIED_SOURCE = "UNCERTIFIED_SOURCE"


_CRITICAL_ALWAYS = {
    L3SourceGap.MISSING_RAW_SOURCE,
    L3SourceGap.MISSING_L2_PRIMITIVE,
    L3SourceGap.MISSING_ASOF_TIMESTAMP,
}


def classify_source_gaps(
    uncertainty_flags: tuple[str, ...],
    *,
    runtime_context: str,
    source_time_certified: bool,
    freshness_status: str,
    authority_class: str,
) -> tuple[tuple[L3SourceGap, ...], tuple[L3SourceGap, ...]]:
    critical: set[L3SourceGap] = set()
    noncritical: set[L3SourceGap] = set()
    for flag in uncertainty_flags:
        normalized = flag.strip().lower()
        if "missing_raw" in normalized or normalized in {"missing_source", "raw_source_missing"}:
            critical.add(L3SourceGap.MISSING_RAW_SOURCE)
        elif "missing_l2" in normalized:
            critical.add(L3SourceGap.MISSING_L2_PRIMITIVE)
        elif "missing_asof" in normalized or "timestamp" in normalized:
            critical.add(L3SourceGap.MISSING_ASOF_TIMESTAMP)
        elif "confirmation" in normalized or "not_ready" in normalized:
            noncritical.add(L3SourceGap.MISSING_CONFIRMATION)
        elif "comparator" in normalized:
            noncritical.add(L3SourceGap.MISSING_COMPARATOR)
        elif "denominator" in normalized:
            noncritical.add(L3SourceGap.MISSING_DENOMINATOR)
        elif "incomplete" in normalized or "missing" in normalized:
            noncritical.add(L3SourceGap.MISSING_CONFIRMATION)
    authority = str(authority_class or "").strip().lower()
    if authority in {"news_discovery_proxy", "licensed_metadata_proxy"}:
        noncritical.add(L3SourceGap.DISCOVERY_ONLY_SOURCE)
    if not source_time_certified:
        gap = L3SourceGap.MISSING_FRESHNESS_CERTIFICATION
        if str(runtime_context or "").strip().upper() in LIVE_CONTEXTS:
            critical.add(gap)
        else:
            noncritical.add(gap)
    if str(freshness_status or "").strip().upper() == "STALE":
        if str(runtime_context or "").strip().upper() in LIVE_CONTEXTS:
            critical.add(L3SourceGap.STALE_SOURCE)
        else:
            noncritical.add(L3SourceGap.STALE_SOURCE)
    if authority in {"uncertified_source", "missing_source"}:
        noncritical.add(L3SourceGap.UNCERTIFIED_SOURCE)
    critical |= {gap for gap in noncritical if gap in _CRITICAL_ALWAYS}
    noncritical -= critical
    return (
        tuple(sorted(critical, key=lambda item: item.value)),
        tuple(sorted(noncritical, key=lambda item: item.value)),
    )
