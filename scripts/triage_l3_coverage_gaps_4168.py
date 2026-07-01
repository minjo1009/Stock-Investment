from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4168"
DEFAULT_ARTIFACT_DIR = Path("data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability")
L3_DIR = Path("data/artifacts/task_4152_l3_relation_graph_v2")
L1_L2_DIR = Path("data/artifacts/task_4146_l0_l2_wide_packetization_handoff")
L4_DIR = Path("data/diagnostics/l4")

TRIAGE_COLUMNS = [
    "task_id",
    "l3_gap_id",
    "graph_key",
    "gap_reason",
    "gap_subreason",
    "source",
    "provider",
    "event_date",
    "event_month",
    "time_bucket",
    "entity",
    "ticker",
    "l0_reference",
    "l1_reference",
    "l2_reference",
    "trace_status",
    "trace_notes",
    "l1_mapping_status",
    "l1_gate_classification",
    "l2_admission_status",
    "l2_event_domain",
    "l2_block_reason",
    "l1_l0_row_count",
    "l1_mapped_rows",
    "l1_blocked_unmapped_rows",
    "l1_newswire_recall_review_rows",
    "l1_entity_candidate_review_rows",
    "l2_feature_candidate_count",
    "l2_review_candidate_count",
    "l2_newswire_recall_review_count",
    "l2_entity_candidate_review_count",
    "l2_blocked_candidate_count",
    "negative_evidence_allowed",
    "diagnostic_only",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def as_int(value: Any) -> int:
    try:
        if value in ("", None):
            return 0
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def first_nonempty(*values: Any) -> str:
    for value in values:
        text = "" if value is None else str(value).strip()
        if text:
            return text
    return ""


def event_date_from_timestamp(value: str) -> tuple[str, str]:
    if not value:
        return "", ""
    date_part = value[:10]
    if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
        return date_part, date_part[:7]
    if len(value) >= 7 and value[4] == "-":
        return "", value[:7]
    return "", ""


def subreason_for_gap(gap: dict[str, str], l1: dict[str, str], l2: dict[str, str]) -> tuple[str, str]:
    reason = gap.get("reason_code", "")
    notes: list[str] = []

    if reason == "L2_BLOCKED_CANDIDATES_PRESENT":
        blocked_count = as_int(l2.get("blocked_candidate_count"))
        block_reason = first_nonempty(l2.get("block_reason"), l1.get("blocker_reason"), gap.get("blocked_reason"))
        if blocked_count > 0:
            notes.append(f"l2_blocked_candidate_count={blocked_count}")
        if as_int(l1.get("blocked_unmapped_rows")) > 0:
            return "L1_BLOCKED_UNMAPPED_ROWS_PRESENT", "; ".join(notes)
        if as_int(l1.get("l1_blocked_count")) > 0:
            return "L1_BLOCKED_ROWS_PRESENT", "; ".join(notes)
        if block_reason:
            normalized = block_reason.upper().replace(" ", "_")[:80]
            return f"L2_BLOCK_REASON_PRESENT:{normalized}", "; ".join(notes)
        if blocked_count > 0:
            return "L2_BLOCKED_CANDIDATE_COUNT_PRESENT", "; ".join(notes)
        return "BLOCKED_CANDIDATES_PRESENT_UNCLASSIFIED", "; ".join(notes)

    if reason == "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE":
        if l2.get("admission_status") and l2.get("feature_candidate_materialization_allowed") == "0":
            return "L2_FEATURE_MATERIALIZATION_NOT_ALLOWED", "mapped newswire row did not become article/entity feature"
        if l2.get("admission_status") and as_int(l2.get("feature_candidate_count")) == 0:
            return "L2_ARTICLE_ENTITY_FEATURE_COUNT_ZERO", "mapped newswire row has no admitted article/entity feature count"
        if not l2:
            return "L2_REFERENCE_MISSING_FOR_MAPPED_NEWSWIRE", "gap row references missing L2 row"
        return "NEWSWIRE_ENTITY_OR_ARTICLE_FEATURE_MISSING", "mapped newswire row lacks usable article/entity event feature"

    if reason == "NEWSWIRE_RECALL_REVIEW_ENTITY_FEATURE_PENDING":
        l1_recall = as_int(l1.get("newswire_recall_review_rows"))
        l1_entity = as_int(l1.get("entity_candidate_review_rows"))
        l2_recall = as_int(l2.get("newswire_recall_review_count"))
        l2_entity = as_int(l2.get("entity_candidate_review_count"))
        if (l1_recall or l2_recall) and (l1_entity or l2_entity):
            return "RECALL_AND_ENTITY_REVIEW_PENDING", "recall review and entity review rows are both present"
        if l1_recall or l2_recall:
            return "NEWSWIRE_RECALL_REVIEW_PENDING", "recall review rows need article/entity feature decision"
        if l1_entity or l2_entity:
            return "ENTITY_CANDIDATE_REVIEW_PENDING", "entity candidate rows need mapping/materialization decision"
        return "RECALL_REVIEW_PENDING_WITHOUT_COUNT_DETAIL", "reason present but review counts not available"

    return "UNCLASSIFIED_GAP_REASON", first_nonempty(gap.get("blocked_reason"), "no narrower rule matched")


def trace_status_for(gap: dict[str, str], l1: dict[str, str], l2: dict[str, str]) -> tuple[str, str]:
    has_l1_ref = bool(gap.get("l1_packet_id"))
    has_l2_ref = bool(gap.get("l2_row_id"))
    found_l1 = bool(l1)
    found_l2 = bool(l2)
    raw_ref = first_nonempty(l2.get("raw_path"), l1.get("raw_path"))

    if has_l1_ref and has_l2_ref and found_l1 and found_l2 and raw_ref:
        return "TRACE_OK", "L0/L1/L2 references available"
    if (found_l1 or found_l2) and raw_ref:
        return "TRACE_PARTIAL", "raw path available but one intermediate reference is missing"
    if has_l1_ref or has_l2_ref:
        return "TRACE_REFERENCE_MISSING", "gap row has reference id but referenced artifact row was not found"
    return "TRACE_UNAVAILABLE", "gap row has no L1/L2 reference id"


def build_triage_rows(gaps: list[dict[str, str]], l1_rows: list[dict[str, str]], l2_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    l1_by_id = {row.get("source_packet_id", ""): row for row in l1_rows if row.get("source_packet_id")}
    l2_by_id = {row.get("l2_wide_event_id", ""): row for row in l2_rows if row.get("l2_wide_event_id")}

    triage_rows: list[dict[str, Any]] = []
    for gap in gaps:
        l1 = l1_by_id.get(gap.get("l1_packet_id", ""), {})
        l2 = l2_by_id.get(gap.get("l2_row_id", ""), {})
        event_ts = first_nonempty(l2.get("source_ts"), l1.get("source_ts"))
        event_date, event_month = event_date_from_timestamp(event_ts)
        subreason, subreason_notes = subreason_for_gap(gap, l1, l2)
        trace_status, trace_notes = trace_status_for(gap, l1, l2)
        extra_notes = "; ".join(part for part in [trace_notes, subreason_notes] if part)

        triage_rows.append(
            {
                "task_id": TASK_ID,
                "l3_gap_id": gap.get("gap_id", ""),
                "graph_key": gap.get("graph_key", ""),
                "gap_reason": gap.get("reason_code", ""),
                "gap_subreason": subreason,
                "source": first_nonempty(gap.get("source_family"), l2.get("source_family"), l1.get("endpoint_or_source_family")),
                "provider": first_nonempty(gap.get("provider"), l2.get("provider"), l1.get("provider")),
                "event_date": event_date,
                "event_month": event_month,
                "time_bucket": gap.get("time_bucket", ""),
                "entity": first_nonempty(l1.get("candidate_id"), gap.get("source_row_id")),
                "ticker": first_nonempty(l1.get("symbol"), "UNMAPPED"),
                "l0_reference": first_nonempty(l2.get("raw_path"), l1.get("raw_path"), "UNAVAILABLE"),
                "l1_reference": first_nonempty(gap.get("l1_packet_id"), "UNAVAILABLE"),
                "l2_reference": first_nonempty(gap.get("l2_row_id"), "UNAVAILABLE"),
                "trace_status": trace_status,
                "trace_notes": extra_notes,
                "l1_mapping_status": l1.get("mapping_status", ""),
                "l1_gate_classification": l1.get("l1_gate_classification", ""),
                "l2_admission_status": l2.get("admission_status", ""),
                "l2_event_domain": l2.get("event_domain", ""),
                "l2_block_reason": first_nonempty(l2.get("block_reason"), l1.get("blocker_reason")),
                "l1_l0_row_count": l1.get("l0_row_count", ""),
                "l1_mapped_rows": l1.get("mapped_rows", ""),
                "l1_blocked_unmapped_rows": l1.get("blocked_unmapped_rows", ""),
                "l1_newswire_recall_review_rows": l1.get("newswire_recall_review_rows", ""),
                "l1_entity_candidate_review_rows": l1.get("entity_candidate_review_rows", ""),
                "l2_feature_candidate_count": l2.get("feature_candidate_count", ""),
                "l2_review_candidate_count": l2.get("review_candidate_count", ""),
                "l2_newswire_recall_review_count": l2.get("newswire_recall_review_count", ""),
                "l2_entity_candidate_review_count": l2.get("entity_candidate_review_count", ""),
                "l2_blocked_candidate_count": l2.get("blocked_candidate_count", ""),
                "negative_evidence_allowed": "0",
                "diagnostic_only": "1",
            }
        )
    return triage_rows


def counts_by(rows: list[dict[str, Any]], *fields: str) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        counter[tuple(str(row.get(field, "")) for field in fields)] += 1
    output = []
    for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        record = {field: value for field, value in zip(fields, key)}
        record["count"] = count
        output.append(record)
    return output


def reconcile_l3_l4(
    gaps: list[dict[str, str]],
    graphs: list[dict[str, str]],
    l4_blockers: list[dict[str, str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    l3_gap_count = len(gaps)
    l4_gap_blockers = [row for row in l4_blockers if row.get("blocker_type") == "L3_COVERAGE_GAP"]
    coverage_gap_graphs = [row for row in graphs if row.get("graph_family") == "COVERAGE_GAP"]
    gap_ids = {gap.get("gap_id", "") for gap in gaps}
    graph_keys = {graph.get("graph_key", "") for graph in coverage_gap_graphs}
    graph_level_l4_gap_blockers = [
        row
        for row in l4_gap_blockers
        if row.get("related_artifact_id") in graph_keys
    ]
    expected_l4_gap_blockers = l3_gap_count + len(coverage_gap_graphs)
    observed_l4_gap_blockers = len(l4_gap_blockers)
    difference = observed_l4_gap_blockers - l3_gap_count
    expected_difference = len(coverage_gap_graphs)

    if observed_l4_gap_blockers == expected_l4_gap_blockers:
        status = "EXPECTED_GRAPH_LEVEL_BLOCKERS_EXPLAIN_DIFFERENCE"
    elif observed_l4_gap_blockers == l3_gap_count:
        status = "NO_DIFFERENCE"
    else:
        status = "RECONCILIATION_MISMATCH_REQUIRES_REBUILD_OR_INVESTIGATION"

    detail_rows: list[dict[str, Any]] = []
    for row in l4_gap_blockers:
        related_id = row.get("related_artifact_id", "")
        if related_id in gap_ids:
            grain = "ROW_LEVEL"
            match_status = "MATCHED_L3_GAP_ID"
        elif related_id in graph_keys:
            grain = "GRAPH_LEVEL"
            match_status = "MATCHED_COVERAGE_GAP_GRAPH_KEY"
        else:
            grain = "UNMATCHED"
            match_status = "UNMATCHED_L3_L4_REFERENCE"
        detail_rows.append(
            {
                "task_id": TASK_ID,
                "blocker_grain": grain,
                "match_status": match_status,
                "bundle_id": row.get("bundle_id", ""),
                "blocker_id": row.get("blocker_id", ""),
                "related_artifact_id": related_id,
                "blocker_type": row.get("blocker_type", ""),
                "severity": row.get("severity", ""),
                "source_layer": row.get("source_layer", ""),
                "reason": row.get("reason", ""),
                "required_action": row.get("required_action", ""),
                "is_hard_blocker": row.get("is_hard_blocker", ""),
                "negative_evidence_allowed": row.get("negative_evidence_allowed", ""),
                "diagnostic_only": "1",
            }
        )

    return {
        "task_id": TASK_ID,
        "created_at": utc_now(),
        "status": status,
        "l3_coverage_gap_rows": l3_gap_count,
        "l4_l3_coverage_gap_blockers": observed_l4_gap_blockers,
        "difference_l4_minus_l3": difference,
        "coverage_gap_graph_count": len(coverage_gap_graphs),
        "expected_difference_from_graph_level_blockers": expected_difference,
        "expected_l4_l3_coverage_gap_blockers": expected_l4_gap_blockers,
        "graph_level_l4_gap_blockers": len(graph_level_l4_gap_blockers),
        "explanation": (
            "L4 carries one blocker for each individual L3 coverage gap plus one graph-level blocker "
            "for each L3 graph whose graph_family is COVERAGE_GAP."
            if status == "EXPECTED_GRAPH_LEVEL_BLOCKERS_EXPLAIN_DIFFERENCE"
            else "Observed L3/L4 counts do not match the expected blocker accounting."
        ),
    }, detail_rows


def build_l4_blocker_taxonomy(l4_blockers: list[dict[str, str]]) -> list[dict[str, Any]]:
    global_blockers = {"CONTRADICTION_NOT_SCANNED", "L0_INCOMPLETE_COVERAGE", "PROTO_EVENT_IDENTITY"}
    local_blockers = {"L3_COVERAGE_GAP", "UNSUPPORTED_RELATION_FAMILY"}
    grouped: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for row in l4_blockers:
        blocker_type = row.get("blocker_type", "")
        if blocker_type in global_blockers:
            scope = "GLOBAL_OR_BUNDLE_LEVEL"
        elif blocker_type in local_blockers:
            scope = "LOCAL_GRAPH_OR_EVIDENCE_LEVEL"
        else:
            scope = "UNCLASSIFIED_SCOPE"
        grouped[(blocker_type, scope, row.get("severity", ""), row.get("source_layer", ""))] += 1
    return [
        {
            "task_id": TASK_ID,
            "blocker_type": blocker_type,
            "blocker_scope": scope,
            "severity": severity,
            "source_layer": source_layer,
            "count": count,
            "diagnostic_only": "1",
            "negative_evidence_allowed": "0",
        }
        for (blocker_type, scope, severity, source_layer), count in sorted(grouped.items(), key=lambda item: (-item[1], item[0]))
    ]


def build_event_identity_audit(triage_rows: list[dict[str, Any]], graphs: list[dict[str, str]]) -> dict[str, Any]:
    gap_ids = [row["l3_gap_id"] for row in triage_rows]
    graph_keys = [row["graph_key"] for row in triage_rows]
    graph_family_counts = Counter(row.get("graph_family", "") for row in graphs)
    return {
        "task_id": TASK_ID,
        "created_at": utc_now(),
        "status": "AUDIT_PASS" if len(gap_ids) == len(set(gap_ids)) else "DUPLICATE_GAP_ID_BLOCKER",
        "l3_gap_rows": len(gap_ids),
        "unique_l3_gap_ids": len(set(gap_ids)),
        "duplicate_l3_gap_ids": len(gap_ids) - len(set(gap_ids)),
        "gap_graph_key_count": len(graph_keys),
        "unique_gap_graph_keys": len(set(graph_keys)),
        "graph_family_counts": dict(sorted(graph_family_counts.items())),
        "event_identity_scope": "diagnostic_audit_only_no_schema_rewrite",
        "negative_evidence_allowed": 0,
        "diagnostic_only": 1,
    }


def load_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "MALFORMED_JSON", "path": str(path)}


def build_l0_status_snapshot() -> dict[str, Any]:
    public_context = load_json_if_exists(Path("data/artifacts/l0_public_context_news_backfill/collector_progress.json"))
    newswire = load_json_if_exists(Path("data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json"))
    market_macro = load_json_if_exists(Path("data/artifacts/l0_public_market_macro_news_backfill/collector_progress.json"))

    context_pending = {}
    if isinstance(public_context, dict):
        for source, state in public_context.get("backfill", {}).items():
            if as_int(state.get("pending_units")) > 0:
                context_pending[source] = {
                    "pending_units": state.get("pending_units"),
                    "page_offsets": state.get("page_offsets", {}),
                    "entry_offsets": state.get("entry_offsets", {}),
                }

    return {
        "task_id": TASK_ID,
        "created_at": utc_now(),
        "public_context_news_backfill": {
            "status": public_context.get("last_status") if isinstance(public_context, dict) else "UNAVAILABLE",
            "pending_units_by_source": context_pending,
            "explicit_blocker": (
                "FEDERAL_REGISTER_2020_10_PENDING_OFFSET_EMPTY_RESPONSE"
                if context_pending
                else "NONE"
            ),
        },
        "public_newswire_backfill": {
            "status": newswire.get("status") if isinstance(newswire, dict) else "UNAVAILABLE",
            "progress_pct": newswire.get("progress_pct") if isinstance(newswire, dict) else None,
            "completed_units": newswire.get("completed_units") if isinstance(newswire, dict) else None,
            "pending_units": newswire.get("pending_units") if isinstance(newswire, dict) else None,
            "failed_units": newswire.get("failed_units") if isinstance(newswire, dict) else None,
            "partial_units": newswire.get("partial_units") if isinstance(newswire, dict) else None,
            "by_source": newswire.get("by_source", {}) if isinstance(newswire, dict) else {},
        },
        "public_market_macro_news_backfill": {
            "status": market_macro.get("last_status") if isinstance(market_macro, dict) else "UNAVAILABLE",
            "provider": market_macro.get("provider") if isinstance(market_macro, dict) else None,
        },
        "safety": {
            "diagnostic_only": 1,
            "negative_evidence_allowed": 0,
            "broker_mutation_count": 0,
            "order_count": 0,
            "paper_promotion_count": 0,
            "live_order_count": 0,
        },
    }


def build_p1_p2_ledger(triage_rows: list[dict[str, Any]], reconciliation: dict[str, Any]) -> dict[str, Any]:
    trace_counts = Counter(row["trace_status"] for row in triage_rows)
    subreason_counts = Counter(row["gap_subreason"] for row in triage_rows)
    return {
        "task_id": TASK_ID,
        "created_at": utc_now(),
        "safety": {
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "broker_mutation_count": 0,
            "order_count": 0,
            "paper_promotion_count": 0,
            "live_order_count": 0,
            "missing_or_stale_data_policy": "UNKNOWN_BLOCKER_NOT_NEGATIVE_EVIDENCE",
        },
        "p0_completed": [
            "l3_coverage_gap_reason_narrowing_artifact",
            "newswire_recall_pending_traceability_artifact",
            "l3_l4_coverage_gap_reconciliation",
        ],
        "p1_bounded": [
            {
                "item": "stable_event_identity",
                "status": "AUDIT_READY_NOT_SCHEMA_REWRITE",
                "reason": "Triage artifact exposes graph_key, l3_gap_id, L1/L2 references, and trace_status for deterministic review without rewriting event IDs.",
            },
            {
                "item": "blocker_taxonomy_global_vs_local",
                "status": "DIAGNOSTIC_LEDGER_ONLY",
                "reason": "L4 blocker taxonomy should be changed in L4 builder only after gap reasons are stable.",
            },
            {
                "item": "macro_sector_sector_theme_relation_support",
                "status": "DEFERRED_UNTIL_L2_FEATURE_ADMISSION_RULES_ARE_CLEAR",
                "reason": "Adding relation families before feature admission would hide missing L2 materialization behind broader labels.",
            },
        ],
        "p2_deferred": [
            {
                "item": "contradiction_scanner",
                "status": "DEFERRED_BY_EVIDENCE",
                "reason": "Contradiction scanning before stable event identity and feature admission would create noisy blockers rather than actionable fixes.",
            },
            {
                "item": "five_min_downstream_integration",
                "status": "DEFERRED_UNTIL_L0_BACKFILL_REALTIME_COVERAGE_STABILIZES",
                "reason": "Five-minute bars are operational coverage work first; they should not be mixed into L3/L4 thesis quality yet.",
            },
            {
                "item": "collector_speed_retuning",
                "status": "DEFERRED_WHILE_FAILED_ZERO_AND_ALERTS_ZERO",
                "reason": "TASK-4168 is L3/L4 traceability; L0 concurrency changes are a separate operational task.",
            },
        ],
        "trace_status_counts": dict(sorted(trace_counts.items())),
        "top_gap_subreasons": dict(subreason_counts.most_common(20)),
        "reconciliation_status": reconciliation.get("status"),
    }


def write_markdown_summary(path: Path, summary: dict[str, Any], reconciliation: dict[str, Any]) -> None:
    lines = [
        "# TASK-4168 L3 Gap Triage Summary",
        "",
        "## Safety",
        "",
        "- Strategy remains NOT_ACCEPTED.",
        "- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
        "- Real capital, broker mutation, live order, paper promotion remain forbidden and zero.",
        "- Missing or stale data remains UNKNOWN/BLOCKER, not negative evidence.",
        "",
        "## Gap Counts",
        "",
        "| Field | Count |",
        "|---|---:|",
    ]
    for item in summary["gap_reason_counts"]:
        lines.append(f"| {item['gap_reason']} | {item['count']} |")

    lines.extend(
        [
            "",
            "## Top Subreasons",
            "",
            "| Subreason | Count |",
            "|---|---:|",
        ]
    )
    for item in summary["gap_subreason_counts"][:20]:
        lines.append(f"| {item['gap_subreason']} | {item['count']} |")

    lines.extend(
        [
            "",
            "## Trace Status",
            "",
            "| Trace Status | Count |",
            "|---|---:|",
        ]
    )
    for item in summary["trace_status_counts"]:
        lines.append(f"| {item['trace_status']} | {item['count']} |")

    lines.extend(
        [
            "",
            "## L3/L4 Reconciliation",
            "",
            f"- Status: `{reconciliation['status']}`",
            f"- L3 coverage gap rows: {reconciliation['l3_coverage_gap_rows']}",
            f"- L4 L3_COVERAGE_GAP blockers: {reconciliation['l4_l3_coverage_gap_blockers']}",
            f"- Difference: {reconciliation['difference_l4_minus_l3']}",
            f"- Coverage-gap graph count: {reconciliation['coverage_gap_graph_count']}",
            f"- Explanation: {reconciliation['explanation']}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TASK-4168 L3 coverage gap triage artifacts.")
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    args = parser.parse_args()

    artifact_dir = args.artifact_dir
    artifact_dir.mkdir(parents=True, exist_ok=True)

    gaps = read_csv_rows(L3_DIR / "l3_coverage_gaps.csv")
    graphs = read_csv_rows(L3_DIR / "l3_relation_graphs.csv")
    l1_rows = read_csv_rows(L1_L2_DIR / "l1_wide_normalized_source_packets.csv")
    l2_rows = read_csv_rows(L1_L2_DIR / "l2_feature_materialization_candidates.csv")
    l4_blockers = read_csv_rows(L4_DIR / "l4_thesis_blockers.csv")

    triage_rows = build_triage_rows(gaps, l1_rows, l2_rows)
    reconciliation, reconciliation_detail_rows = reconcile_l3_l4(gaps, graphs, l4_blockers)
    l4_blocker_taxonomy_rows = build_l4_blocker_taxonomy(l4_blockers)
    event_identity_audit = build_event_identity_audit(triage_rows, graphs)
    l0_status_snapshot = build_l0_status_snapshot()
    p1_p2_ledger = build_p1_p2_ledger(triage_rows, reconciliation)

    summary = {
        "task_id": TASK_ID,
        "created_at": utc_now(),
        "row_count": len(triage_rows),
        "gap_reason_counts": counts_by(triage_rows, "gap_reason"),
        "gap_subreason_counts": counts_by(triage_rows, "gap_subreason"),
        "trace_status_counts": counts_by(triage_rows, "trace_status"),
        "source_month_counts": counts_by(triage_rows, "source", "event_month"),
        "safety": p1_p2_ledger["safety"],
    }

    write_csv(artifact_dir / "task_4168_l3_gap_triage.csv", triage_rows, TRIAGE_COLUMNS)
    write_json(
        artifact_dir / "task_4168_l3_gap_triage.json",
        {
            "summary": summary,
            "rows": triage_rows,
        },
    )
    write_csv(
        artifact_dir / "task_4168_gap_subreason_summary.csv",
        summary["gap_subreason_counts"],
        ["gap_subreason", "count"],
    )
    write_csv(
        artifact_dir / "task_4168_source_month_linkage.csv",
        summary["source_month_counts"],
        ["source", "event_month", "count"],
    )
    write_json(artifact_dir / "task_4168_l3_l4_gap_reconciliation.json", reconciliation)
    write_csv(
        artifact_dir / "task_4168_l3_l4_gap_reconciliation_detail.csv",
        reconciliation_detail_rows,
        [
            "task_id",
            "blocker_grain",
            "match_status",
            "bundle_id",
            "blocker_id",
            "related_artifact_id",
            "blocker_type",
            "severity",
            "source_layer",
            "reason",
            "required_action",
            "is_hard_blocker",
            "negative_evidence_allowed",
            "diagnostic_only",
        ],
    )
    write_csv(
        artifact_dir / "task_4168_l4_blocker_taxonomy.csv",
        l4_blocker_taxonomy_rows,
        [
            "task_id",
            "blocker_type",
            "blocker_scope",
            "severity",
            "source_layer",
            "count",
            "diagnostic_only",
            "negative_evidence_allowed",
        ],
    )
    write_json(artifact_dir / "task_4168_event_identity_audit.json", event_identity_audit)
    write_json(artifact_dir / "task_4168_l0_status_snapshot.json", l0_status_snapshot)
    write_json(artifact_dir / "task_4168_p1_p2_priority_ledger.json", p1_p2_ledger)
    write_markdown_summary(artifact_dir / "task_4168_l3_gap_triage.md", summary, reconciliation)

    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "status": "PASS",
                "artifact_dir": str(artifact_dir),
                "triage_rows": len(triage_rows),
                "reconciliation_status": reconciliation["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
