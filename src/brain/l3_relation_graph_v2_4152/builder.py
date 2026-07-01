from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import (
    HORIZON_LABEL,
    TASK_ID,
    CoverageGap,
    DirectionReview,
    EventCluster,
    GraphFamily,
    RelationEdge,
)


MACRO_DIMENSIONS = {"MACRO_CONTEXT", "RATES", "INFLATION", "FX", "ENERGY", "LIQUIDITY", "EMPLOYMENT"}
ALLOWED_DIRECTION_VALUES = {item.value for item in DirectionReview}


def build_from_config(config_path: str | Path) -> dict[str, Any]:
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    output_dir = Path(config["outputs"]["artifact_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    meanings = read_jsonl(inputs["l3_meanings"])
    old_graph = json.loads(Path(inputs["l3_relation_graph"]).read_text(encoding="utf-8"))
    article_l1 = index_csv(inputs["l1_article_packets"], "l1_article_packet_id")
    article_l2 = index_csv(inputs["l2_article_features"], "diagnostic_feature_id")
    wide_l1 = index_csv(inputs["l1_wide_packets"], "source_packet_id")
    wide_l2 = index_csv(inputs["l2_wide_candidates"], "l2_wide_event_id")
    rejected = read_csv_rows(inputs["l3_rejected_or_review_queue"])

    edges: list[RelationEdge] = []
    gaps: list[CoverageGap] = []
    cluster_inputs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_edges: set[str] = set()

    for meaning in meanings:
        context = row_context(meaning, article_l1, article_l2, wide_l1, wide_l2)
        cluster_key = event_cluster_key(meaning, context)
        time_bucket = bucket_time(meaning.get("event_time") or meaning.get("available_to_brain_ts"))
        if is_newswire_unknown_collapse(meaning):
            gap = coverage_gap(
                meaning,
                context,
                time_bucket,
                "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE",
                "mapped newswire row lacks article/entity event feature in L2",
            )
            gaps.append(gap)
            add_edge(edges, seen_edges, coverage_gap_edge(meaning, context, gap, time_bucket))
            continue

        cluster_inputs[cluster_key].append({**meaning, "_context": context, "_time_bucket": time_bucket})
        for edge in relation_edges_for_meaning(meaning, context, cluster_key, time_bucket):
            add_edge(edges, seen_edges, edge)

    for row in rejected:
        source_family = row.get("source_family", "")
        reason = first_reason(row.get("rejection_reasons", "")) or "L1_OR_L2_REVIEW_QUEUE"
        time_bucket = "UNKNOWN_TIME"
        gap = CoverageGap(
            gap_id=f"gap:{stable_hash([row.get('l2_row_id', ''), reason])}",
            graph_key=coverage_graph_key(reason, source_family, time_bucket),
            source_family=source_family,
            provider=source_family,
            time_bucket=time_bucket,
            reason_code=normalize_gap_reason(reason),
            blocked_reason=row.get("rejection_reasons", reason),
            l1_packet_id=row.get("l1_packet_id", ""),
            l2_row_id=row.get("l2_row_id", ""),
            source_row_id=row.get("l2_row_id", ""),
        )
        gaps.append(gap)

    add_wide_l2_relation_candidates(
        edges=edges,
        gaps=gaps,
        cluster_inputs=cluster_inputs,
        seen_edges=seen_edges,
        wide_l1=wide_l1,
        wide_l2=wide_l2,
        source_artifact=inputs["l2_wide_candidates"],
    )

    clusters = build_event_clusters(cluster_inputs)
    graph_rows = aggregate_graphs(edges, gaps)
    manifest = {
        "task_id": TASK_ID,
        "config_path": str(config_path),
        "created_at": now_iso(),
        "inputs": [{"role": key, "path": value, "sha256": sha256_file(value)} for key, value in inputs.items()],
        "old_task_4150_graph_count": old_graph.get("graph_count", 0),
        "output_counts": {
            "l3_relation_edges": len(edges),
            "l3_event_clusters": len(clusters),
            "l3_relation_graphs": len(graph_rows),
            "l3_coverage_gaps": len(gaps),
        },
        "authority": config["authority"],
        "safety": {
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "raw_l0_read": False,
            "broker_mutation_allowed": False,
            "live_order_allowed": False,
            "paper_promotion_allowed": False,
        },
    }

    write_csv(output_dir / "l3_relation_edges.csv", [edge.to_dict() for edge in edges])
    write_csv(output_dir / "l3_event_clusters.csv", [cluster.to_dict() for cluster in clusters])
    write_csv(output_dir / "l3_relation_graphs.csv", graph_rows)
    write_csv(output_dir / "l3_coverage_gaps.csv", [gap.to_dict() for gap in gaps])
    write_json(output_dir / "l3_relation_graph_v2_manifest.json", manifest)
    write_json(output_dir / "l3_relation_graph_validation.json", {"task_id": TASK_ID, "status": "NOT_RUN"})
    return manifest


def relation_edges_for_meaning(
    meaning: dict[str, Any],
    context: dict[str, str],
    cluster_key: str,
    time_bucket: str,
) -> list[RelationEdge]:
    edges: list[RelationEdge] = []
    source_family = meaning.get("source_family", "")
    source_provider = meaning.get("provider") or source_family
    target_type = meaning.get("target_node_type", "")
    target_key = meaning.get("target_node_key", "")
    dimension = meaning.get("economic_dimension", "UNKNOWN") or "UNKNOWN"
    direction = direction_from(meaning.get("direction_review", "CONTEXT_ONLY"))
    evidence_time = meaning.get("event_time") or meaning.get("available_to_brain_ts", "")
    source_artifact = context.get("source_artifact", "l3_meanings.jsonl")
    source_row_id = meaning.get("l3_meaning_id", "")
    l1_packet_id = meaning.get("l1_packet_id", "")
    l2_row_id = meaning.get("l2_row_id", "")
    mapping_status = context.get("mapping_status", "")
    admission_status = context.get("admission_status", "")

    edges.append(
        make_edge(
            graph_family=GraphFamily.SOURCE_EVENT_CLUSTER,
            source_node_id=f"SOURCE_FAMILY:{source_family}",
            target_node_id=f"EVENT_CLUSTER:{cluster_key}",
            edge_type="source_family_to_event_cluster",
            graph_key=f"rg:v2:source_event_cluster:EVENT_CLUSTER:{cluster_key}:source_family:{source_family}:{time_bucket}:{HORIZON_LABEL}",
            source_artifact=source_artifact,
            source_row_id=source_row_id,
            l1_packet_id=l1_packet_id,
            l2_row_id=l2_row_id,
            source_family=source_family,
            source_provider=source_provider,
            mapping_status=mapping_status,
            admission_status=admission_status,
            economic_dimension=dimension,
            direction_review=direction,
            evidence_time=evidence_time,
            time_bucket=time_bucket,
            blocked_reason="",
        )
    )

    if target_type in {"SYMBOL", "ENTITY"} and target_key:
        edges.append(
            make_edge(
                graph_family=GraphFamily.ENTITY_EVENT,
                source_node_id=f"{target_type}:{target_key}",
                target_node_id=f"EVENT_CLUSTER:{cluster_key}",
                edge_type="entity_to_event_cluster",
                graph_key=f"rg:v2:entity_event:{target_type}:{target_key}:event_cluster:{cluster_key}:{time_bucket}:{HORIZON_LABEL}:{source_family}",
                source_artifact=source_artifact,
                source_row_id=source_row_id,
                l1_packet_id=l1_packet_id,
                l2_row_id=l2_row_id,
                source_family=source_family,
                source_provider=source_provider,
                mapping_status=mapping_status,
                admission_status=admission_status,
                economic_dimension=dimension,
                direction_review=direction,
                evidence_time=evidence_time,
                time_bucket=time_bucket,
                blocked_reason="",
            )
        )
        if dimension != "UNKNOWN":
            edges.append(
                make_edge(
                    graph_family=GraphFamily.ENTITY_DIMENSION,
                    source_node_id=f"{target_type}:{target_key}",
                    target_node_id=f"ECONOMIC_DIMENSION:{dimension}",
                    edge_type="entity_to_economic_dimension",
                    graph_key=f"rg:v2:entity_dimension:{target_type}:{target_key}:dimension:{dimension}:{time_bucket}:{HORIZON_LABEL}:{source_family}",
                    source_artifact=source_artifact,
                    source_row_id=source_row_id,
                    l1_packet_id=l1_packet_id,
                    l2_row_id=l2_row_id,
                    source_family=source_family,
                    source_provider=source_provider,
                    mapping_status=mapping_status,
                    admission_status=admission_status,
                    economic_dimension=dimension,
                    direction_review=direction,
                    evidence_time=evidence_time,
                    time_bucket=time_bucket,
                    blocked_reason="",
                )
            )

    if target_type == "MACRO" or dimension in MACRO_DIMENSIONS:
        factor = dimension if dimension in MACRO_DIMENSIONS else "MACRO_CONTEXT"
        edges.append(
            make_edge(
                graph_family=GraphFamily.MACRO_FACTOR,
                source_node_id=f"MACRO:{factor}",
                target_node_id=f"EVENT_CLUSTER:{cluster_key}",
                edge_type="macro_factor_to_event_cluster",
                graph_key=f"rg:v2:macro_factor:MACRO:{factor}:event_cluster:{cluster_key}:{time_bucket}:{HORIZON_LABEL}:{source_family}",
                source_artifact=source_artifact,
                source_row_id=source_row_id,
                l1_packet_id=l1_packet_id,
                l2_row_id=l2_row_id,
                source_family=source_family,
                source_provider=source_provider,
                mapping_status=mapping_status,
                admission_status=admission_status,
                economic_dimension=factor,
                direction_review=direction,
                evidence_time=evidence_time,
                time_bucket=time_bucket,
                blocked_reason="",
            )
        )
    return edges


def add_wide_l2_relation_candidates(
    *,
    edges: list[RelationEdge],
    gaps: list[CoverageGap],
    cluster_inputs: dict[str, list[dict[str, Any]]],
    seen_edges: set[str],
    wide_l1: dict[str, dict[str, str]],
    wide_l2: dict[str, dict[str, str]],
    source_artifact: str,
) -> None:
    represented_l2_ids = {edge.l2_row_id for edge in edges if edge.l2_row_id}
    for row in sorted(wide_l2.values(), key=lambda item: item.get("l2_wide_event_id", "")):
        l2_id = row.get("l2_wide_event_id", "")
        if not l2_id or l2_id in represented_l2_ids:
            continue
        if row.get("l3_read_allowed") != "1" or row.get("feature_candidate_materialization_allowed") != "1":
            continue
        l1_id = row.get("source_packet_id", "")
        l1 = wide_l1.get(l1_id, {})
        time_bucket = bucket_time(row.get("source_ts") or row.get("available_to_brain_ts"))
        cluster_key = f"event_cluster:{stable_hash(['wide_l2', row.get('source_family', ''), row.get('event_domain', ''), row.get('raw_path', ''), time_bucket])}"
        dimension = wide_dimension(row)
        pseudo = {
            "l3_meaning_id": f"wide_l2:{l2_id}",
            "l1_packet_id": l1_id,
            "l2_row_id": l2_id,
            "source_family": row.get("source_family", ""),
            "provider": row.get("provider") or row.get("source_family", ""),
            "event_time": row.get("source_ts") or row.get("available_to_brain_ts", ""),
            "available_to_brain_ts": row.get("available_to_brain_ts", ""),
            "event_class": row.get("event_domain") or "SOURCE_CONTEXT",
            "economic_dimension": dimension,
            "target_node_type": "MACRO" if row.get("mapping_scope") == "MACRO" else "SOURCE_FAMILY",
            "target_node_key": dimension if row.get("mapping_scope") == "MACRO" else row.get("source_family", ""),
            "direction_review": DirectionReview.CONTEXT_ONLY.value,
        }
        cluster_inputs[cluster_key].append(pseudo)
        context = {
            "source_artifact": source_artifact,
            "mapping_status": row.get("mapping_status") or l1.get("mapping_status", ""),
            "admission_status": row.get("admission_status", ""),
            "event_domain": row.get("event_domain", ""),
        }
        for edge in wide_l2_edges(row, context, cluster_key, time_bucket, dimension):
            add_edge(edges, seen_edges, edge)
        gap_reason = wide_l2_gap_reason(row)
        if gap_reason:
            gap = CoverageGap(
                gap_id=f"gap:{stable_hash([l2_id, gap_reason])}",
                graph_key=coverage_graph_key(gap_reason, row.get("source_family", ""), time_bucket),
                source_family=row.get("source_family", ""),
                provider=row.get("provider") or row.get("source_family", ""),
                time_bucket=time_bucket,
                reason_code=gap_reason,
                blocked_reason=wide_l2_gap_blocked_reason(row, gap_reason),
                l1_packet_id=l1_id,
                l2_row_id=l2_id,
                source_row_id=f"wide_l2:{l2_id}",
            )
            gaps.append(gap)
            add_edge(edges, seen_edges, wide_l2_gap_edge(row, context, gap, time_bucket))


def wide_l2_edges(
    row: dict[str, str],
    context: dict[str, str],
    cluster_key: str,
    time_bucket: str,
    dimension: str,
) -> list[RelationEdge]:
    source_family = row.get("source_family", "")
    source_provider = row.get("provider") or source_family
    evidence_time = row.get("source_ts") or row.get("available_to_brain_ts", "")
    l1_packet_id = row.get("source_packet_id", "")
    l2_row_id = row.get("l2_wide_event_id", "")
    base = {
        "source_artifact": context.get("source_artifact", ""),
        "source_row_id": f"wide_l2:{l2_row_id}",
        "l1_packet_id": l1_packet_id,
        "l2_row_id": l2_row_id,
        "source_family": source_family,
        "source_provider": source_provider,
        "mapping_status": context.get("mapping_status", ""),
        "admission_status": context.get("admission_status", ""),
        "economic_dimension": dimension,
        "direction_review": DirectionReview.CONTEXT_ONLY,
        "evidence_time": evidence_time,
        "time_bucket": time_bucket,
        "blocked_reason": "",
    }
    result = [
        make_edge(
            graph_family=GraphFamily.SOURCE_EVENT_CLUSTER,
            source_node_id=f"SOURCE_FAMILY:{source_family}",
            target_node_id=f"EVENT_CLUSTER:{cluster_key}",
            edge_type="wide_l2_source_family_to_event_cluster",
            graph_key=f"rg:v2:wide_source_event_cluster:EVENT_CLUSTER:{cluster_key}:source_family:{source_family}:{time_bucket}:{HORIZON_LABEL}",
            **base,
        )
    ]
    if row.get("mapping_scope") == "MACRO" or row.get("event_domain") == "MACRO_CONTEXT":
        result.append(
            make_edge(
                graph_family=GraphFamily.MACRO_FACTOR,
                source_node_id=f"MACRO:{dimension}",
                target_node_id=f"EVENT_CLUSTER:{cluster_key}",
                edge_type="wide_l2_macro_factor_to_event_cluster",
                graph_key=f"rg:v2:wide_macro_factor:MACRO:{dimension}:event_cluster:{cluster_key}:{time_bucket}:{HORIZON_LABEL}:{source_family}",
                **base,
            )
        )
    return result


def wide_l2_gap_edge(
    row: dict[str, str],
    context: dict[str, str],
    gap: CoverageGap,
    time_bucket: str,
) -> RelationEdge:
    l2_id = row.get("l2_wide_event_id", "")
    return make_edge(
        graph_family=GraphFamily.COVERAGE_GAP,
        graph_key=gap.graph_key,
        source_node_id=f"SOURCE_FAMILY:{row.get('source_family', '')}",
        target_node_id=f"COVERAGE_GAP:{gap.reason_code}",
        edge_type="wide_l2_source_family_to_coverage_gap",
        source_artifact=context.get("source_artifact", ""),
        source_row_id=f"wide_l2:{l2_id}",
        l1_packet_id=row.get("source_packet_id", ""),
        l2_row_id=l2_id,
        source_family=row.get("source_family", ""),
        source_provider=row.get("provider") or row.get("source_family", ""),
        mapping_status=context.get("mapping_status", ""),
        admission_status=context.get("admission_status", ""),
        economic_dimension=wide_dimension(row),
        direction_review=DirectionReview.UNKNOWN_BLOCKER,
        evidence_time=row.get("source_ts") or row.get("available_to_brain_ts", ""),
        time_bucket=time_bucket,
        blocked_reason=gap.blocked_reason,
    )


def wide_dimension(row: dict[str, str]) -> str:
    domain = row.get("event_domain", "")
    if domain == "MACRO_CONTEXT":
        return "MACRO_CONTEXT"
    if row.get("mapping_scope") == "MACRO":
        return "MACRO_CONTEXT"
    if row.get("source_family") == "public_newswire_feeds":
        return "NEWSWIRE_REVIEW"
    return domain or "SOURCE_CONTEXT"


def wide_l2_gap_reason(row: dict[str, str]) -> str:
    if int_value(row.get("newswire_recall_review_count")) > 0 or int_value(row.get("entity_candidate_review_count")) > 0:
        return "NEWSWIRE_RECALL_REVIEW_ENTITY_FEATURE_PENDING"
    if int_value(row.get("blocked_candidate_count")) > 0:
        return "L2_BLOCKED_CANDIDATES_PRESENT"
    return ""


def wide_l2_gap_blocked_reason(row: dict[str, str], reason: str) -> str:
    if reason == "NEWSWIRE_RECALL_REVIEW_ENTITY_FEATURE_PENDING":
        return "newswire recall/entity review rows exist but are not yet materialized as entity-level L2 features"
    return row.get("block_reason") or reason


def make_edge(**kwargs: Any) -> RelationEdge:
    dedupe_key = "|".join(
        [
            kwargs["graph_key"],
            kwargs["source_row_id"],
            kwargs["edge_type"],
            kwargs["source_node_id"],
            kwargs["target_node_id"],
        ]
    )
    return RelationEdge(dedupe_key=dedupe_key, edge_id=f"edge:{stable_hash([dedupe_key])}", **kwargs)


def coverage_gap_edge(
    meaning: dict[str, Any],
    context: dict[str, str],
    gap: CoverageGap,
    time_bucket: str,
) -> RelationEdge:
    return make_edge(
        graph_family=GraphFamily.COVERAGE_GAP,
        graph_key=gap.graph_key,
        source_node_id=f"SOURCE_FAMILY:{meaning.get('source_family', '')}",
        target_node_id=f"COVERAGE_GAP:{gap.reason_code}",
        edge_type="source_family_to_coverage_gap",
        source_artifact=context.get("source_artifact", "l3_meanings.jsonl"),
        source_row_id=meaning.get("l3_meaning_id", ""),
        l1_packet_id=meaning.get("l1_packet_id", ""),
        l2_row_id=meaning.get("l2_row_id", ""),
        source_family=meaning.get("source_family", ""),
        source_provider=meaning.get("provider") or meaning.get("source_family", ""),
        mapping_status=context.get("mapping_status", ""),
        admission_status=context.get("admission_status", ""),
        economic_dimension=meaning.get("economic_dimension", "UNKNOWN"),
        direction_review=DirectionReview.UNKNOWN_BLOCKER,
        evidence_time=meaning.get("event_time") or meaning.get("available_to_brain_ts", ""),
        time_bucket=time_bucket,
        blocked_reason=gap.blocked_reason,
    )


def coverage_gap(
    meaning: dict[str, Any],
    context: dict[str, str],
    time_bucket: str,
    reason_code: str,
    blocked_reason: str,
) -> CoverageGap:
    source_family = meaning.get("source_family", "")
    graph_key = coverage_graph_key(reason_code, source_family, time_bucket)
    return CoverageGap(
        gap_id=f"gap:{stable_hash([meaning.get('l3_meaning_id', ''), reason_code])}",
        graph_key=graph_key,
        source_family=source_family,
        provider=meaning.get("provider") or source_family,
        time_bucket=time_bucket,
        reason_code=reason_code,
        blocked_reason=blocked_reason,
        l1_packet_id=meaning.get("l1_packet_id", ""),
        l2_row_id=meaning.get("l2_row_id", ""),
        source_row_id=meaning.get("l3_meaning_id", ""),
    )


def coverage_graph_key(reason_code: str, source_family: str, time_bucket: str) -> str:
    reason = normalize_gap_reason(reason_code)
    return f"rg:v2:coverage_gap:{reason}:source_family:{source_family}:{time_bucket}:{HORIZON_LABEL}"


def aggregate_graphs(edges: list[RelationEdge], gaps: list[CoverageGap]) -> list[dict[str, Any]]:
    grouped: dict[str, list[RelationEdge]] = defaultdict(list)
    for edge in edges:
        grouped[edge.graph_key].append(edge)

    coverage_reasons = {gap.graph_key: gap.blocked_reason for gap in gaps}
    rows: list[dict[str, Any]] = []
    for graph_key, items in sorted(grouped.items()):
        first = items[0]
        directions = Counter(edge.direction_review.value for edge in items)
        graph_state = graph_state_from(directions, first.graph_family)
        source_families = {edge.source_family for edge in items if edge.source_family}
        forbidden_output_present = 0
        rows.append(
            {
                "graph_key": graph_key,
                "graph_family": first.graph_family.value,
                "target_type": target_type_from_node(first.target_node_id),
                "target_key": target_key_from_node(first.target_node_id),
                "relation_type": first.edge_type,
                "economic_dimension": first.economic_dimension,
                "source_scope": "mixed_public" if len(source_families) > 1 else next(iter(source_families), ""),
                "time_bucket": first.time_bucket,
                "window_start": first.time_bucket,
                "window_end": first.time_bucket,
                "horizon_label": HORIZON_LABEL,
                "edge_count": len(items),
                "evidence_count": len({edge.source_row_id for edge in items}),
                "source_family_count": len(source_families),
                "risk_edge_count": directions.get(DirectionReview.RISK_REVIEW.value, 0),
                "support_edge_count": directions.get(DirectionReview.SUPPORT_REVIEW.value, 0),
                "context_edge_count": directions.get(DirectionReview.CONTEXT_ONLY.value, 0),
                "unknown_blocker_edge_count": directions.get(DirectionReview.UNKNOWN_BLOCKER.value, 0),
                "graph_state": graph_state,
                "coverage_state": "BLOCKED_GAP" if first.graph_family == GraphFamily.COVERAGE_GAP else "LINEAGED",
                "blocked_reason": coverage_reasons.get(graph_key, ""),
                "lineage_complete": int(all(edge.l1_packet_id and edge.l2_row_id for edge in items)),
                "forbidden_output_present": forbidden_output_present,
                "diagnostic_only": 1,
                "trading_eligible": 0,
                "signal_export_allowed": 0,
                "order_intent_allowed": 0,
                "broker_mutation_allowed": 0,
                "paper_promotion_allowed": 0,
                "live_order_allowed": 0,
                "created_at": now_iso(),
            }
        )
    return rows


def build_event_clusters(cluster_inputs: dict[str, list[dict[str, Any]]]) -> list[EventCluster]:
    clusters: list[EventCluster] = []
    for key, rows in sorted(cluster_inputs.items()):
        times = sorted(row.get("event_time") or row.get("available_to_brain_ts", "") for row in rows)
        source_families = {row.get("source_family", "") for row in rows if row.get("source_family")}
        target_types = Counter(row.get("target_node_type", "") for row in rows)
        target_keys = Counter(row.get("target_node_key", "") for row in rows)
        directions = Counter(row.get("direction_review", DirectionReview.CONTEXT_ONLY.value) for row in rows)
        clusters.append(
            EventCluster(
                event_cluster_key=key,
                cluster_basis="l1_packet_id|economic_dimension|event_time_bucket",
                event_domain=rows[0].get("event_class", "SOURCE_CONTEXT"),
                economic_dimension=rows[0].get("economic_dimension", "UNKNOWN"),
                primary_target_type=target_types.most_common(1)[0][0],
                primary_target_key=target_keys.most_common(1)[0][0],
                source_family_count=len(source_families),
                evidence_count=len({row.get("l3_meaning_id", "") for row in rows}),
                first_evidence_time=times[0] if times else "",
                last_evidence_time=times[-1] if times else "",
                cluster_state=graph_state_from(directions, GraphFamily.SOURCE_EVENT_CLUSTER),
                lineage_complete=int(all(row.get("l1_packet_id") and row.get("l2_row_id") for row in rows)),
                blocked_reason="",
            )
        )
    return clusters


def row_context(
    meaning: dict[str, Any],
    article_l1: dict[str, dict[str, str]],
    article_l2: dict[str, dict[str, str]],
    wide_l1: dict[str, dict[str, str]],
    wide_l2: dict[str, dict[str, str]],
) -> dict[str, str]:
    l2_id = meaning.get("l2_row_id", "")
    l1_id = meaning.get("l1_packet_id", "")
    if l2_id.startswith("l2diag"):
        l1 = article_l1.get(l1_id, {})
        l2 = article_l2.get(l2_id, {})
        return {
            "source_artifact": "data/artifacts/task_4150_l3_diagnostic_strategy_view_bootstrap/l3_meanings.jsonl",
            "mapping_status": l1.get("mapping_status", ""),
            "admission_status": l1.get("l1_status", ""),
            "event_domain": l2.get("feature_name", ""),
        }
    l2 = wide_l2.get(l2_id, {})
    l1 = wide_l1.get(l1_id, {})
    return {
        "source_artifact": "data/artifacts/task_4150_l3_diagnostic_strategy_view_bootstrap/l3_meanings.jsonl",
        "mapping_status": l2.get("mapping_status") or l1.get("mapping_status", ""),
        "admission_status": l2.get("admission_status") or l1.get("l1_gate_classification", ""),
        "event_domain": l2.get("event_domain", ""),
    }


def event_cluster_key(meaning: dict[str, Any], context: dict[str, str]) -> str:
    basis = [
        meaning.get("source_family", ""),
        meaning.get("l1_packet_id", ""),
        meaning.get("economic_dimension", "UNKNOWN"),
        context.get("event_domain", ""),
        bucket_time(meaning.get("event_time") or meaning.get("available_to_brain_ts")),
    ]
    return f"event_cluster:{stable_hash(basis)}"


def is_newswire_unknown_collapse(meaning: dict[str, Any]) -> bool:
    return (
        meaning.get("source_family") == "public_newswire_feeds"
        and meaning.get("target_node_type") == "SOURCE_FAMILY"
        and meaning.get("target_node_key") == "public_newswire_feeds"
        and meaning.get("economic_dimension") == "UNKNOWN"
    )


def add_edge(edges: list[RelationEdge], seen: set[str], edge: RelationEdge) -> None:
    if edge.dedupe_key in seen:
        return
    seen.add(edge.dedupe_key)
    edges.append(edge)


def direction_from(value: str) -> DirectionReview:
    if value == "RISK_REVIEW":
        return DirectionReview.RISK_REVIEW
    if value == "SUPPORT_REVIEW":
        return DirectionReview.SUPPORT_REVIEW
    if value == "MIXED_REVIEW":
        return DirectionReview.MIXED_REVIEW
    if value == "UNKNOWN_BLOCKER":
        return DirectionReview.UNKNOWN_BLOCKER
    return DirectionReview.CONTEXT_ONLY


def graph_state_from(directions: Counter[str], family: GraphFamily) -> str:
    if family == GraphFamily.COVERAGE_GAP or directions.get(DirectionReview.UNKNOWN_BLOCKER.value):
        return "UNKNOWN_BLOCKER"
    if directions.get(DirectionReview.RISK_REVIEW.value) and directions.get(DirectionReview.SUPPORT_REVIEW.value):
        return "MIXED_REVIEW"
    if directions.get(DirectionReview.RISK_REVIEW.value):
        return "RISK_REVIEW"
    if directions.get(DirectionReview.SUPPORT_REVIEW.value):
        return "SUPPORT_REVIEW"
    return "CONTEXT_ONLY"


def target_type_from_node(node: str) -> str:
    return node.split(":", 1)[0] if ":" in node else "UNKNOWN"


def target_key_from_node(node: str) -> str:
    return node.split(":", 1)[1] if ":" in node else node


def first_reason(text: str) -> str:
    return next((part for part in text.split(";") if part), "")


def normalize_gap_reason(reason: str) -> str:
    if "UNKNOWN_MAPPING" in reason:
        return "SOURCE_FAMILY_COLLAPSED_TO_UNKNOWN"
    if "L1_BLOCKED" in reason:
        return "L1_BLOCKED"
    if "L2" in reason or "FEATURE_CANDIDATE" in reason:
        return "L2_NOT_ADMITTED"
    return reason or "UNKNOWN_BLOCKER"


def bucket_time(value: str | None) -> str:
    if not value:
        return "UNKNOWN_TIME"
    cleaned = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        try:
            dt = datetime.fromisoformat(cleaned[:10])
        except ValueError:
            return "UNKNOWN_TIME"
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def stable_hash(parts: list[str]) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:20]


def int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def index_csv(path: str | Path, key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv_rows(path)}


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


def write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
