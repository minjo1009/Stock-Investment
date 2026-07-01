from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema import (
    DEPLOYMENT_STATUS,
    REAL_CAPITAL,
    SCHEMA_VERSION_BLOCKER,
    SCHEMA_VERSION_BUNDLE,
    SCHEMA_VERSION_EVIDENCE,
    SCHEMA_VERSION_MANIFEST,
    STRATEGY_STATUS,
    TASK_ID,
)


DEFAULT_OUTPUT_DIR = Path("data/diagnostics/l4")
DEFAULT_INPUTS = {
    "l1_article_packets": "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l1_article_packets.csv",
    "l2_article_features": "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l2_diagnostic_feature_rows.csv",
    "l1_wide_packets": "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l1_wide_normalized_source_packets.csv",
    "l2_wide_candidates": "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l2_feature_materialization_candidates.csv",
    "l3_relation_graphs": "data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graphs.csv",
    "l3_relation_edges": "data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_edges.csv",
    "l3_event_clusters": "data/artifacts/task_4152_l3_relation_graph_v2/l3_event_clusters.csv",
    "l3_coverage_gaps": "data/artifacts/task_4152_l3_relation_graph_v2/l3_coverage_gaps.csv",
    "l3_event_clusters_with_limitations": "data/artifacts/task_4154_l3_relation_graph_v2_quality_guard/l3_event_clusters_with_limitations.csv",
    "l3_unsupported_relation_families": "data/artifacts/task_4154_l3_relation_graph_v2_quality_guard/l3_unsupported_relation_families.csv",
    "l3_l4_handoff_manifest": "data/artifacts/task_4154_l3_relation_graph_v2_quality_guard/l3_l4_diagnostic_handoff_manifest.json",
    "l0_collection_status": "data/artifacts/l0_collection_status/current_status.json",
}

GRAPH_FAMILY_TO_THESIS_TYPE = {
    "ENTITY_EVENT": "ENTITY_EVENT",
    "ENTITY_DIMENSION": "ENTITY_EVENT",
    "MACRO_FACTOR": "MACRO_CONTEXT",
    "SOURCE_EVENT_CLUSTER": "SOURCE_EVENT_PROTO",
    "COVERAGE_GAP": "COVERAGE_GAP",
}


def build_l4_thesis_bundles(
    inputs: dict[str, str] | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    input_paths = dict(DEFAULT_INPUTS)
    if inputs:
        input_paths.update(inputs)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    missing = [key for key, value in input_paths.items() if key != "l0_collection_status" and not Path(value).exists()]
    if missing:
        manifest = fail_closed_manifest(input_paths, out, missing)
        write_json(out / "l4_run_manifest.json", manifest)
        return manifest

    l1_article = index_by(read_csv(input_paths["l1_article_packets"]), "l1_article_packet_id")
    l2_article = index_by(read_csv(input_paths["l2_article_features"]), "diagnostic_feature_id")
    l1_wide = index_by(read_csv(input_paths["l1_wide_packets"]), "source_packet_id")
    l2_wide = index_by(read_csv(input_paths["l2_wide_candidates"]), "l2_wide_event_id")
    graphs = read_csv(input_paths["l3_relation_graphs"])
    edges = read_csv(input_paths["l3_relation_edges"])
    clusters = index_by(read_csv(input_paths["l3_event_clusters"]), "event_cluster_key")
    gaps = read_csv(input_paths["l3_coverage_gaps"])
    unsupported = read_csv(input_paths["l3_unsupported_relation_families"])
    handoff = json.loads(Path(input_paths["l3_l4_handoff_manifest"]).read_text(encoding="utf-8"))
    l0_status = read_json_if_exists(input_paths.get("l0_collection_status", ""))

    edges_by_graph: dict[str, list[dict[str, str]]] = defaultdict(list)
    for edge in edges:
        edges_by_graph[edge.get("graph_key", "")].append(edge)

    gaps_by_graph: dict[str, list[dict[str, str]]] = defaultdict(list)
    for gap in gaps:
        gaps_by_graph[gap.get("graph_key", "")].append(gap)

    source_lane_coverage = build_source_lane_coverage(l0_status)
    bundles: list[dict[str, Any]] = []
    evidence_links: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    created_at = now_iso()
    for graph in sorted(graphs, key=lambda row: row.get("graph_key", "")):
        graph_key = graph.get("graph_key", "")
        graph_edges = edges_by_graph.get(graph_key, [])
        graph_gaps = gaps_by_graph.get(graph_key, [])
        bundle_id = stable_id("l4bundle", graph_key)
        bundle_evidence = build_evidence_links_for_graph(
            bundle_id=bundle_id,
            graph=graph,
            edges=graph_edges,
            l1_article=l1_article,
            l2_article=l2_article,
            l1_wide=l1_wide,
            l2_wide=l2_wide,
        )
        evidence_links.extend(bundle_evidence)

        bundle_blockers = build_blockers_for_graph(
            bundle_id=bundle_id,
            graph=graph,
            graph_gaps=graph_gaps,
            unsupported=unsupported,
            source_lane_coverage=source_lane_coverage,
        )
        blockers.extend(bundle_blockers)

        bundles.append(
            build_bundle(
                graph=graph,
                graph_edges=graph_edges,
                graph_gaps=graph_gaps,
                clusters=clusters,
                bundle_id=bundle_id,
                created_at=created_at,
                evidence_links=bundle_evidence,
                blockers=bundle_blockers,
                source_lane_coverage=source_lane_coverage,
            )
        )

    manifest = build_manifest(
        input_paths=input_paths,
        output_dir=out,
        bundles=bundles,
        evidence_links=evidence_links,
        blockers=blockers,
        source_counts={
            "l1_article_packets": len(l1_article),
            "l2_article_features": len(l2_article),
            "l1_wide_packets": len(l1_wide),
            "l2_wide_candidates": len(l2_wide),
            "l3_relation_graphs": len(graphs),
            "l3_relation_edges": len(edges),
            "l3_coverage_gaps": len(gaps),
        },
        handoff=handoff,
        source_lane_coverage=source_lane_coverage,
    )

    write_jsonl(out / "l4_thesis_bundles.jsonl", bundles)
    write_csv(out / "l4_thesis_evidence_links.csv", evidence_links)
    write_csv(out / "l4_thesis_blockers.csv", blockers)
    write_json(out / "l4_run_manifest.json", manifest)
    return manifest


def build_bundle(
    graph: dict[str, str],
    graph_edges: list[dict[str, str]],
    graph_gaps: list[dict[str, str]],
    clusters: dict[str, dict[str, str]],
    bundle_id: str,
    created_at: str,
    evidence_links: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    source_lane_coverage: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    graph_family = graph.get("graph_family", "")
    source_lanes = sorted({edge.get("source_family", "") for edge in graph_edges if edge.get("source_family")} or {graph.get("source_scope", "")})
    l3_event_cluster_ids = sorted({event_cluster_from_node(edge.get("target_node_id", "")) or event_cluster_from_node(edge.get("source_node_id", "")) for edge in graph_edges} - {""})
    primary_symbols = sorted({node_key(edge.get("source_node_id", ""), "SYMBOL") for edge in graph_edges} | {node_key(edge.get("target_node_id", ""), "SYMBOL") for edge in graph_edges} - {""})
    primary_entity_ids = sorted({node_key(edge.get("source_node_id", ""), "ENTITY") for edge in graph_edges} | {node_key(edge.get("target_node_id", ""), "ENTITY") for edge in graph_edges} - {""})
    context_count = sum(1 for row in evidence_links if row["evidence_role"] == "context")
    supporting_count = sum(1 for row in evidence_links if row["evidence_role"] == "supporting")
    coverage_gap_count = len(graph_gaps) or sum(1 for row in evidence_links if row["evidence_role"] == "coverage_gap")
    hard_blocker = any(str(row.get("is_hard_blocker")).lower() in {"true", "1"} for row in blockers)
    coverage_blocked = graph_family == "COVERAGE_GAP" or coverage_gap_count > 0
    event_status = "PROTO_BUCKET" if graph_family == "SOURCE_EVENT_CLUSTER" else "GRAPH_RELATION_CANDIDATE"
    if l3_event_cluster_ids:
        limited = clusters.get(l3_event_cluster_ids[0], {})
        event_status = limited.get("event_identity_status") or event_status
    return {
        "schema_version": SCHEMA_VERSION_BUNDLE,
        "task_id": TASK_ID,
        "bundle_id": bundle_id,
        "created_at_utc": created_at,
        "diagnostic_only": True,
        "strategy_status": STRATEGY_STATUS,
        "deployment_status": DEPLOYMENT_STATUS,
        "real_capital": REAL_CAPITAL,
        "no_broker_mutation": True,
        "no_live_order": True,
        "no_paper_promotion": True,
        "bundle_status": "DRAFT_BLOCKED" if coverage_blocked else "DRAFT_MIXED",
        "institutional_quality_status": "BLOCKED" if coverage_blocked else "MIXED",
        "thesis_type": GRAPH_FAMILY_TO_THESIS_TYPE.get(graph_family, "MIXED_CONTEXT"),
        "thesis_statement": thesis_statement(graph),
        "thesis_scope": thesis_scope(graph, primary_symbols, primary_entity_ids),
        "primary_symbols": primary_symbols,
        "primary_entity_ids": primary_entity_ids,
        "source_lanes": source_lanes,
        "time_window_start_utc": graph.get("window_start") or None,
        "time_window_end_utc": graph.get("window_end") or None,
        "l3_graph_ids": [graph.get("graph_key", "")],
        "l3_graph_families": [graph_family],
        "l3_event_cluster_ids": l3_event_cluster_ids,
        "event_identity_status": event_status,
        "same_event_assertion": False,
        "supporting_evidence_count": supporting_count,
        "context_evidence_count": context_count,
        "contradicting_evidence_count": 0,
        "coverage_gap_count": coverage_gap_count,
        "lineage_status": "OK" if graph.get("lineage_complete") in {"1", "true", "True"} else "PARTIAL",
        "source_access_status": "PARTIAL" if any(source_lane_coverage.get(lane, {}).get("incomplete") for lane in source_lanes) else "OK",
        "coverage_status": "BLOCKED" if coverage_blocked else coverage_status_for_lanes(graph, source_lanes, source_lane_coverage),
        "contradiction_status": "NOT_SCANNED_BLOCKER",
        "relation_quality_status": relation_quality_status(graph, hard_blocker),
        "thesis_specificity_score": score_specificity(graph, primary_symbols, primary_entity_ids),
        "evidence_linkage_score": score_linkage(evidence_links),
        "source_traceability_score": score_traceability(evidence_links),
        "contradiction_handling_score": None,
        "institutional_quality_score": None,
        "block_reasons": sorted({row["blocker_type"] for row in blockers}),
        "warnings": warning_messages(graph, source_lanes, source_lane_coverage),
    }


def build_evidence_links_for_graph(
    bundle_id: str,
    graph: dict[str, str],
    edges: list[dict[str, str]],
    l1_article: dict[str, dict[str, str]],
    l2_article: dict[str, dict[str, str]],
    l1_wide: dict[str, dict[str, str]],
    l2_wide: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for edge in sorted(edges, key=lambda row: row.get("edge_id", "")):
        l1 = l1_article.get(edge.get("l1_packet_id", "")) or l1_wide.get(edge.get("l1_packet_id", "")) or {}
        l2 = l2_article.get(edge.get("l2_row_id", "")) or l2_wide.get(edge.get("l2_row_id", "")) or {}
        role = evidence_role(graph, edge)
        lineage_ok = bool(edge.get("l1_packet_id")) and bool(edge.get("l2_row_id"))
        rows.append(
            {
                "schema_version": SCHEMA_VERSION_EVIDENCE,
                "bundle_id": bundle_id,
                "evidence_link_id": stable_id("l4evidence", bundle_id, edge.get("edge_id", "")),
                "evidence_role": role,
                "evidence_claim": evidence_claim(graph, edge),
                "source_lane": edge.get("source_family", ""),
                "source_id": edge.get("source_row_id", ""),
                "source_url_or_path": l1.get("source_url") or l1.get("raw_path") or l2.get("raw_path") or edge.get("source_artifact", ""),
                "publisher_or_origin": l1.get("provider") or l2.get("provider") or edge.get("source_provider", ""),
                "source_time_utc": edge.get("evidence_time") or l1.get("source_time_utc") or l1.get("source_ts") or l2.get("event_date") or l2.get("source_ts") or "",
                "ingested_at_utc": l1.get("available_to_brain_ts") or l2.get("available_to_brain_ts") or "",
                "l1_packet_id": edge.get("l1_packet_id", ""),
                "l1_mapping_status": l1.get("mapping_status") or edge.get("mapping_status", ""),
                "l2_feature_id": edge.get("l2_row_id", ""),
                "l2_feature_family": l2.get("feature_namespace") or l2.get("event_domain") or edge.get("economic_dimension", ""),
                "l3_edge_id": edge.get("edge_id", ""),
                "l3_graph_id": edge.get("graph_key", ""),
                "l3_graph_family": edge.get("graph_family", ""),
                "lineage_status": "OK" if lineage_ok else "BLOCKED",
                "source_access_status": "OK" if (l1 or l2 or edge.get("source_artifact")) else "PARTIAL",
                "mapping_confidence": edge.get("mapping_status", ""),
                "evidence_quality_flag": evidence_quality_flag(role, lineage_ok, graph.get("graph_family", "")),
                "negative_evidence_allowed": False,
            }
        )
    return rows


def build_blockers_for_graph(
    bundle_id: str,
    graph: dict[str, str],
    graph_gaps: list[dict[str, str]],
    unsupported: list[dict[str, str]],
    source_lane_coverage: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    graph_key = graph.get("graph_key", "")
    graph_family = graph.get("graph_family", "")
    source_lanes = {graph.get("source_scope", "")}
    rows.append(blocker(bundle_id, "CONTRADICTION_NOT_SCANNED", "P0", "L3", graph_key, "Contradiction relation family is not implemented; absence of contradiction cannot be treated as clear.", "IMPLEMENT_CONTRADICTION_SCAN", True))
    if graph_family == "SOURCE_EVENT_CLUSTER":
        rows.append(blocker(bundle_id, "PROTO_EVENT_IDENTITY", "P1", "L3", graph_key, "SOURCE_EVENT_CLUSTER is a proto bucket and not confirmed same-event identity.", "PRESERVE_PROTO_EVENT_STATUS", False))
    if graph_family == "COVERAGE_GAP":
        rows.append(blocker(bundle_id, "L3_COVERAGE_GAP", "P0", "L3", graph_key, graph.get("blocked_reason") or "L3 reported a coverage gap.", "BACKFILL_OR_MATERIALIZE_MISSING_L2_FEATURE", True))
    for gap in graph_gaps:
        rows.append(blocker(bundle_id, "L3_COVERAGE_GAP", "P0", "L3", gap.get("gap_id", ""), gap.get("blocked_reason") or gap.get("reason_code", ""), "BACKFILL_OR_MATERIALIZE_MISSING_L2_FEATURE", True))
    for row in unsupported:
        family = row.get("relation_family", "")
        if family == "CONTRADICTION":
            continue
        if graph_family in {"MACRO_FACTOR", "ENTITY_DIMENSION", "SOURCE_EVENT_CLUSTER"}:
            rows.append(blocker(bundle_id, "UNSUPPORTED_RELATION_FAMILY", "P1", "L3", family, row.get("l4_interpretation", ""), f"IMPLEMENT_{family}_RELATION_FAMILY", False))
    for lane in source_lanes:
        cov = source_lane_coverage.get(lane, {})
        if cov.get("incomplete"):
            rows.append(blocker(bundle_id, "L0_INCOMPLETE_COVERAGE", "P1", "L0", lane, f"L0 source lane coverage is incomplete: progress_pct={cov.get('progress_pct')}", "CONTINUE_L0_BACKFILL", False))
    return dedupe_blockers(rows)


def blocker(bundle_id: str, blocker_type: str, severity: str, source_layer: str, related_id: str, reason: str, action: str, hard: bool) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_BLOCKER,
        "bundle_id": bundle_id,
        "blocker_id": stable_id("l4blocker", bundle_id, blocker_type, related_id, reason),
        "blocker_type": blocker_type,
        "severity": severity,
        "source_layer": source_layer,
        "related_artifact_id": related_id,
        "reason": reason,
        "required_action": action,
        "is_hard_blocker": hard,
        "negative_evidence_allowed": False,
    }


def build_manifest(
    input_paths: dict[str, str],
    output_dir: Path,
    bundles: list[dict[str, Any]],
    evidence_links: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    source_counts: dict[str, int],
    handoff: dict[str, Any],
    source_lane_coverage: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_MANIFEST,
        "task_id": TASK_ID,
        "created_at_utc": now_iso(),
        "diagnostic_only": True,
        "hard_boundaries": hard_boundaries(),
        "input_artifacts": [{"role": key, "path": value, "exists": Path(value).exists()} for key, value in sorted(input_paths.items())],
        "source_inputs": [source_input_fingerprint(key, value) for key, value in sorted(input_paths.items())],
        "input_counts": source_counts,
        "l0_coverage_state": source_lane_coverage,
        "l3_quality_guard_state": {
            "graph_family_counts": handoff.get("graph_family_counts", {}),
            "unsupported_relation_families": handoff.get("unsupported_relation_families", []),
            "coverage_gap_counts_by_reason": handoff.get("coverage_gap_counts_by_reason", {}),
            "same_event_assertion": handoff.get("same_event_assertion", False),
        },
        "output_artifacts": [
            str(output_dir / "l4_thesis_bundles.jsonl"),
            str(output_dir / "l4_thesis_evidence_links.csv"),
            str(output_dir / "l4_thesis_blockers.csv"),
            str(output_dir / "l4_run_manifest.json"),
        ],
        "bundle_count": len(bundles),
        "evidence_link_count": len(evidence_links),
        "blocker_count": len(blockers),
        "bundle_status_counts": dict(Counter(row["bundle_status"] for row in bundles)),
        "institutional_quality_status_counts": dict(Counter(row["institutional_quality_status"] for row in bundles)),
        "blocker_type_counts": dict(Counter(row["blocker_type"] for row in blockers)),
        "validation_status": "NOT_RUN",
        "validation_errors": [],
        "notes": [
            "L4 artifacts are diagnostic thesis review artifacts, not trading decisions.",
            "Current contradiction scan is not implemented; NO_CONTRADICTION is forbidden.",
        ],
    }


def fail_closed_manifest(input_paths: dict[str, str], output_dir: Path, missing: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_MANIFEST,
        "task_id": TASK_ID,
        "created_at_utc": now_iso(),
        "diagnostic_only": True,
        "hard_boundaries": hard_boundaries(),
        "input_artifacts": [{"role": key, "path": value, "exists": Path(value).exists()} for key, value in sorted(input_paths.items())],
        "source_inputs": [source_input_fingerprint(key, value) for key, value in sorted(input_paths.items())],
        "output_artifacts": [str(output_dir / "l4_run_manifest.json")],
        "bundle_count": 0,
        "evidence_link_count": 0,
        "blocker_count": 0,
        "validation_status": "FAIL",
        "validation_errors": [f"missing input artifact: {key}" for key in missing],
        "notes": ["Fail-closed manifest only. No fake bundles were created."],
    }


def thesis_statement(graph: dict[str, str]) -> str:
    family = graph.get("graph_family", "MIXED")
    target = graph.get("target_key") or graph.get("target_type") or "unknown target"
    dimension = graph.get("economic_dimension") or "UNKNOWN"
    window = graph.get("time_bucket") or graph.get("window_start") or "unknown window"
    if family == "COVERAGE_GAP":
        return f"Coverage blocker for {target} in {window}; missing data is UNKNOWN/BLOCKER, not negative evidence."
    if family == "MACRO_FACTOR":
        return f"Review macro-context thesis candidate for {dimension} during {window}; causal interpretation is not asserted."
    if family == "SOURCE_EVENT_CLUSTER":
        return f"Review proto source-event cluster for {target} during {window}; same-event identity is not asserted."
    if family in {"ENTITY_EVENT", "ENTITY_DIMENSION"}:
        return f"Review entity thesis candidate linked to {dimension} during {window}; materiality is not asserted."
    return f"Review mixed-context thesis candidate for {target} during {window}; diagnostic only."


def thesis_scope(graph: dict[str, str], symbols: list[str], entities: list[str]) -> str:
    if symbols and len(symbols) == 1:
        return "single_entity"
    if symbols or entities:
        return "entity_group"
    if graph.get("graph_family") == "MACRO_FACTOR":
        return "macro_context"
    return "unknown"


def evidence_role(graph: dict[str, str], edge: dict[str, str]) -> str:
    if graph.get("graph_family") == "COVERAGE_GAP":
        return "coverage_gap"
    if edge.get("direction_review") == "RISK_REVIEW":
        return "context"
    if graph.get("graph_family") in {"ENTITY_EVENT", "ENTITY_DIMENSION"}:
        return "supporting"
    return "context"


def evidence_claim(graph: dict[str, str], edge: dict[str, str]) -> str:
    return (
        f"{edge.get('edge_type', 'relation')} links {edge.get('source_node_id', '')} "
        f"to {edge.get('target_node_id', '')} in {graph.get('graph_family', '')}; diagnostic relation only."
    )


def evidence_quality_flag(role: str, lineage_ok: bool, graph_family: str) -> str:
    if not lineage_ok:
        return "BLOCKED"
    if role == "coverage_gap":
        return "BLOCKED"
    if graph_family == "SOURCE_EVENT_CLUSTER":
        return "PROTO_ONLY"
    if role == "context":
        return "CONTEXT_ONLY"
    return "USABLE_DIAGNOSTIC"


def relation_quality_status(graph: dict[str, str], hard_blocker: bool) -> str:
    if graph.get("graph_family") == "SOURCE_EVENT_CLUSTER":
        return "PROTO"
    if hard_blocker and graph.get("graph_family") == "COVERAGE_GAP":
        return "BLOCKED"
    if int_or_zero(graph.get("edge_count")) <= 1:
        return "SPARSE"
    return "MIXED"


def coverage_status_for_lanes(graph: dict[str, str], lanes: list[str], coverage: dict[str, dict[str, Any]]) -> str:
    if graph.get("coverage_state") == "BLOCKED_GAP":
        return "BLOCKED"
    if any(coverage.get(lane, {}).get("incomplete") for lane in lanes):
        return "INCOMPLETE"
    if graph.get("coverage_state") == "LINEAGED":
        return "COMPLETE"
    return "UNKNOWN"


def score_specificity(graph: dict[str, str], symbols: list[str], entities: list[str]) -> int:
    score = 35
    if graph.get("economic_dimension") and graph.get("economic_dimension") != "UNKNOWN":
        score += 20
    if graph.get("time_bucket"):
        score += 15
    if symbols or entities:
        score += 20
    if graph.get("graph_family") == "COVERAGE_GAP":
        score = min(score, 50)
    return min(score, 90)


def score_linkage(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    ok = sum(1 for row in rows if row.get("lineage_status") == "OK")
    return round(ok / len(rows) * 100)


def score_traceability(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    ok = sum(1 for row in rows if row.get("source_id") and row.get("source_time_utc"))
    return round(ok / len(rows) * 100)


def warning_messages(graph: dict[str, str], lanes: list[str], coverage: dict[str, dict[str, Any]]) -> list[str]:
    warnings = ["CONTRADICTION_NOT_SCANNED"]
    if graph.get("graph_family") == "SOURCE_EVENT_CLUSTER":
        warnings.append("PROTO_EVENT_IDENTITY_ONLY")
    for lane in lanes:
        if coverage.get(lane, {}).get("incomplete"):
            warnings.append(f"L0_INCOMPLETE_COVERAGE:{lane}")
    return sorted(set(warnings))


def build_source_lane_coverage(l0_status: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping = {
        "public_newswire_feeds": "public_newswire_backfill",
        "public_market_macro_news_feeds": "public_market_macro_news_backfill",
        "public_context_news_feeds": "public_context_news_backfill",
    }
    coverage: dict[str, dict[str, Any]] = {}
    for lane, key in mapping.items():
        row = find_nested_dict(l0_status, key) or {}
        progress = row.get("progress_pct")
        complete = row.get("complete")
        incomplete = (complete is False) or (isinstance(progress, (int, float)) and progress < 100)
        coverage[lane] = {
            "source_status_key": key,
            "progress_pct": progress,
            "complete": complete,
            "incomplete": bool(incomplete),
            "worker_gate_state": row.get("worker_gate_state") or row.get("status"),
            "row_count": row.get("row_count"),
        }
    return coverage


def find_nested_dict(obj: Any, key: str) -> dict[str, Any] | None:
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], dict):
            return obj[key]
        for value in obj.values():
            found = find_nested_dict(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_nested_dict(value, key)
            if found is not None:
                return found
    return None


def hard_boundaries() -> dict[str, Any]:
    return {
        "strategy_status": STRATEGY_STATUS,
        "deployment_status": DEPLOYMENT_STATUS,
        "real_capital": REAL_CAPITAL,
        "no_broker_mutation": True,
        "no_live_order": True,
        "no_paper_promotion": True,
    }


def source_input_fingerprint(role: str, path_value: str) -> dict[str, Any]:
    path = Path(path_value)
    exists = path.exists()
    stat = path.stat() if exists else None
    return {
        "role": role,
        "path": path_value,
        "exists": exists,
        "row_count": count_rows(path) if exists and path.suffix.lower() in {".csv", ".jsonl"} else None,
        "sha256": file_sha256(path) if exists else "",
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z") if stat else "",
    }


def count_rows(path: Path) -> int:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            return max(sum(1 for _ in fh) - 1, 0)
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    return 0


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dedupe_blockers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = row["blocker_id"]
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def event_cluster_from_node(node: str) -> str:
    if node.startswith("EVENT_CLUSTER:"):
        return node.split(":", 1)[1]
    return ""


def node_key(node: str, node_type: str) -> str:
    prefix = f"{node_type}:"
    if node.startswith(prefix):
        return node.split(":", 1)[1]
    return ""


def index_by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in rows if row.get(key)}


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def int_or_zero(value: str | None) -> int:
    try:
        return int(float(value or "0"))
    except ValueError:
        return 0


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json_if_exists(path: str) -> dict[str, Any]:
    if not path or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
