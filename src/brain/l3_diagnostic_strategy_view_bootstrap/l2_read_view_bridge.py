from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from .contracts import L3InputPrimitive


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_l1_article_index(path: str | Path) -> dict[str, dict[str, str]]:
    return {row.get("l1_article_packet_id", ""): row for row in read_csv_rows(path)}


def load_l1_wide_index(path: str | Path) -> dict[str, dict[str, str]]:
    return {row.get("source_packet_id", ""): row for row in read_csv_rows(path)}


def normalize_article_features(
    l2_rows: list[dict[str, str]],
    l1_index: dict[str, dict[str, str]],
) -> tuple[list[L3InputPrimitive], list[dict[str, str]]]:
    active: list[L3InputPrimitive] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in l2_rows:
        packet_id = row.get("l1_article_packet_id", "")
        l1 = l1_index.get(packet_id, {})
        reasons = _article_rejection_reasons(row, l1)
        target_type, target_key = _target_from_article_row(row)
        dedupe_key = "|".join([packet_id, target_type, target_key, row.get("feature_name", "")])
        if dedupe_key in seen:
            reasons.append("DUPLICATE_NON_CANONICAL_SUPPRESSED")
        if reasons:
            rejected.append(_rejected_row(row, packet_id, reasons, "article_feature"))
            continue
        seen.add(dedupe_key)
        active.append(
            L3InputPrimitive(
                input_id=f"l3input:{row.get('diagnostic_feature_id', _hash_row(row))}",
                source_kind="article_feature",
                l2_row_id=row.get("diagnostic_feature_id", ""),
                l1_packet_id=packet_id,
                source_family=row.get("source_family", ""),
                provider=l1.get("provider") or row.get("source_family", ""),
                source_key=row.get("source_key", ""),
                event_time=row.get("event_date") or l1.get("source_time_utc", ""),
                available_to_brain_ts=row.get("available_to_brain_ts", ""),
                target_node_type=target_type,
                target_node_key=target_key,
                mapping_status=l1.get("mapping_status", ""),
                dedupe_status="CANONICAL",
                l1_status=l1.get("l1_status", ""),
                l2_status="L2_DIAGNOSTIC_FEATURE_READY",
                raw_sha256=row.get("raw_sha256", ""),
                lineage_hash=row.get("lineage_hash", ""),
                title=l1.get("title", ""),
                feature_name=row.get("feature_name", ""),
                feature_value=row.get("feature_value", ""),
                blocker_reasons=(),
                noncritical_gaps=(),
            )
        )
    return active, rejected


def normalize_wide_candidates(
    l2_rows: list[dict[str, str]],
    l1_index: dict[str, dict[str, str]],
) -> tuple[list[L3InputPrimitive], list[dict[str, str]]]:
    active: list[L3InputPrimitive] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in l2_rows:
        packet_id = row.get("source_packet_id", "")
        l1 = l1_index.get(packet_id, {})
        reasons = _wide_rejection_reasons(row, l1)
        target_type, target_key = _target_from_wide_row(row, l1)
        dedupe_key = "|".join([packet_id, target_type, target_key, row.get("event_domain", "")])
        if dedupe_key in seen:
            reasons.append("DUPLICATE_NON_CANONICAL_SUPPRESSED")
        if reasons:
            rejected.append(_rejected_row(row, packet_id, reasons, "wide_candidate"))
            continue
        seen.add(dedupe_key)
        active.append(
            L3InputPrimitive(
                input_id=f"l3input:{row.get('l2_wide_event_id', _hash_row(row))}",
                source_kind="wide_candidate",
                l2_row_id=row.get("l2_wide_event_id", ""),
                l1_packet_id=packet_id,
                source_family=row.get("source_family", ""),
                provider=row.get("provider", ""),
                source_key=l1.get("candidate_id", ""),
                event_time=row.get("decision_asof_ts") or row.get("source_ts", ""),
                available_to_brain_ts=row.get("available_to_brain_ts", ""),
                target_node_type=target_type,
                target_node_key=target_key,
                mapping_status=row.get("mapping_status", ""),
                dedupe_status="CANONICAL",
                l1_status=l1.get("l1_gate_classification", ""),
                l2_status=row.get("admission_status", ""),
                raw_sha256=row.get("raw_sha256", ""),
                lineage_hash=row.get("raw_sha256", ""),
                title="",
                feature_name=row.get("event_domain", ""),
                feature_value=row.get("feature_candidate_count", ""),
                blocker_reasons=(),
                noncritical_gaps=(),
            )
        )
    return active, rejected


def _article_rejection_reasons(row: dict[str, str], l1: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if not l1:
        reasons.append("MISSING_L1_PACKET")
    if l1 and l1.get("l1_status") != "READY":
        reasons.append("L1_BLOCKED_OR_NOT_READY")
    mapping_status = l1.get("mapping_status", "")
    mapping_scope = l1.get("mapping_scope", "")
    if "UNKNOWN" in mapping_status or mapping_scope == "UNKNOWN":
        reasons.append("UNKNOWN_MAPPING")
    if not (row.get("symbol") or row.get("entity_key") or row.get("macro_key")):
        reasons.append("MISSING_TARGET_NODE")
    if row.get("diagnostic_only") != "1":
        reasons.append("NOT_DIAGNOSTIC_ONLY")
    for flag in ("trading_eligible", "signal_order_export_allowed", "broker_mutation_permitted"):
        if row.get(flag) not in {"", "0"}:
            reasons.append(f"FORBIDDEN_AUTHORITY_{flag.upper()}")
    if l1 and l1.get("source_time_certified") not in {"1", "true", "True"}:
        reasons.append("MISSING_SOURCE_TIME_CERTIFICATION")
    return reasons


def _wide_rejection_reasons(row: dict[str, str], l1: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if not l1:
        reasons.append("MISSING_L1_WIDE_PACKET")
    if row.get("l3_read_allowed") != "1":
        reasons.append("L3_READ_NOT_ALLOWED")
    if "UNKNOWN" in row.get("mapping_status", "") or row.get("mapping_scope") == "UNKNOWN":
        reasons.append("UNKNOWN_MAPPING")
    if row.get("feature_candidate_materialization_allowed") != "1":
        reasons.append("FEATURE_CANDIDATE_NOT_ALLOWED")
    for flag in ("trading_authority_opened", "paper_live_broker_order_opened"):
        if row.get(flag) not in {"", "0"}:
            reasons.append(f"FORBIDDEN_AUTHORITY_{flag.upper()}")
    if l1 and l1.get("missing_source_is_negative") not in {"0", ""}:
        reasons.append("MISSING_SOURCE_NEGATIVE_RISK")
    if l1 and l1.get("outcome_used_for_assignment") not in {"0", ""}:
        reasons.append("OUTCOME_LEAKAGE_RISK")
    return reasons


def _target_from_article_row(row: dict[str, str]) -> tuple[str, str]:
    if row.get("symbol"):
        return "SYMBOL", row["symbol"]
    if row.get("entity_key"):
        return "ENTITY", row["entity_key"]
    if row.get("macro_key"):
        return "MACRO", row["macro_key"]
    return "UNKNOWN", ""


def _target_from_wide_row(row: dict[str, str], l1: dict[str, str]) -> tuple[str, str]:
    if l1.get("symbol"):
        return "SYMBOL", l1["symbol"]
    if row.get("mapping_scope") == "MACRO" or row.get("event_domain") == "MACRO_CONTEXT":
        return "MACRO", row.get("source_family", "MACRO_CONTEXT")
    return "SOURCE_FAMILY", row.get("source_family", "")


def _rejected_row(row: dict[str, str], packet_id: str, reasons: list[str], source_kind: str) -> dict[str, str]:
    return {
        "source_kind": source_kind,
        "l2_row_id": row.get("diagnostic_feature_id") or row.get("l2_wide_event_id", ""),
        "l1_packet_id": packet_id,
        "source_family": row.get("source_family", ""),
        "rejection_reasons": ";".join(dict.fromkeys(reasons)),
        "active_l3_candidate": "0",
        "missing_is_negative": "0",
        "diagnostic_only": "1",
    }


def _hash_row(row: dict[str, str]) -> str:
    joined = "|".join(f"{k}={row[k]}" for k in sorted(row))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]

