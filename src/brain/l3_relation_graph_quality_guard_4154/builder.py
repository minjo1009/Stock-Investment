from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4154"
SOURCE_ARTIFACT_DIR = Path("data/artifacts/task_4152_l3_relation_graph_v2")
OUTPUT_ARTIFACT_DIR = Path("data/artifacts/task_4154_l3_relation_graph_v2_quality_guard")
EVENT_CLUSTER_BASIS = "l1_packet_id|economic_dimension|event_time_bucket"
EVENT_IDENTITY_STATUS = "PROTO_BUCKET"
UNSUPPORTED_RELATION_FAMILIES = (
    {
        "relation_family": "MACRO_SECTOR",
        "implementation_status": "NOT_IMPLEMENTED",
        "l4_interpretation": "absence of this family is not negative evidence; macro-sector linkage has not been scanned or cleared",
        "priority_hint": "P1",
    },
    {
        "relation_family": "SECTOR_THEME",
        "implementation_status": "NOT_IMPLEMENTED",
        "l4_interpretation": "absence of this family is not negative evidence; sector-theme linkage has not been scanned or cleared",
        "priority_hint": "P1",
    },
    {
        "relation_family": "CONTRADICTION",
        "implementation_status": "NOT_IMPLEMENTED",
        "l4_interpretation": "absence of this family is not negative evidence and does not mean no contradiction exists",
        "priority_hint": "P0_HANDOFF_FLAG_P1_IMPLEMENTATION",
    },
)
FORBIDDEN_L4_ASSUMPTIONS = (
    "graph count does not imply evidence quality",
    "SOURCE_EVENT_CLUSTER does not assert confirmed same event",
    "ENTITY_EVENT does not assert material event",
    "MACRO_FACTOR does not assert causal macro thesis",
    "absence of CONTRADICTION family does not mean no contradiction exists",
    "coverage gaps are UNKNOWN/BLOCKER, not negative evidence",
    "L3 output does not authorize ranking, sizing, order intent, paper/live trading, strategy acceptance, or deployment readiness",
)


def build_quality_guard(
    source_dir: str | Path = SOURCE_ARTIFACT_DIR,
    output_dir: str | Path = OUTPUT_ARTIFACT_DIR,
) -> dict[str, Any]:
    source = Path(source_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    graphs = read_csv(source / "l3_relation_graphs.csv")
    edges = read_csv(source / "l3_relation_edges.csv")
    clusters = read_csv(source / "l3_event_clusters.csv")
    gaps = read_csv(source / "l3_coverage_gaps.csv")
    source_manifest = json.loads((source / "l3_relation_graph_v2_manifest.json").read_text(encoding="utf-8"))

    quality_rows = build_graph_quality_summary(graphs, edges, gaps)
    clusters_limited = build_event_cluster_limitations(clusters, edges)
    unsupported_rows = [dict(row) for row in UNSUPPORTED_RELATION_FAMILIES]
    gap_summary_rows = build_coverage_gap_summary(gaps)
    handoff_manifest = build_handoff_manifest(
        source_manifest=source_manifest,
        quality_rows=quality_rows,
        edges=edges,
        graphs=graphs,
        gaps=gaps,
        unsupported_rows=unsupported_rows,
    )

    write_csv(out / "l3_graph_quality_summary.csv", quality_rows)
    write_json(out / "l3_graph_quality_summary.json", {"task_id": TASK_ID, "rows": quality_rows})
    write_csv(out / "l3_event_clusters_with_limitations.csv", clusters_limited)
    write_csv(out / "l3_unsupported_relation_families.csv", unsupported_rows)
    write_csv(out / "l3_coverage_gap_summary_by_reason_source_date.csv", gap_summary_rows)
    write_json(out / "l3_l4_diagnostic_handoff_manifest.json", handoff_manifest)
    write_json(out / "l3_quality_guard_validation.json", {"task_id": TASK_ID, "status": "NOT_RUN"})

    return {
        "task_id": TASK_ID,
        "source_artifact_dir": str(source),
        "output_artifact_dir": str(out),
        "output_counts": {
            "graph_quality_summary_rows": len(quality_rows),
            "event_clusters_with_limitations": len(clusters_limited),
            "unsupported_relation_families": len(unsupported_rows),
            "coverage_gap_summary_rows": len(gap_summary_rows),
        },
        "task_4152_counts_unchanged": {
            "graphs": len(graphs),
            "edges": len(edges),
            "clusters": len(clusters),
            "coverage_gaps": len(gaps),
        },
    }


def build_graph_quality_summary(
    graphs: list[dict[str, str]],
    edges: list[dict[str, str]],
    gaps: list[dict[str, str]],
) -> list[dict[str, Any]]:
    graphs_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    edges_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in graphs:
        graphs_by_family[row.get("graph_family", "")].append(row)
    for row in edges:
        edges_by_family[row.get("graph_family", "")].append(row)

    families = sorted(set(graphs_by_family) | set(edges_by_family))
    rows: list[dict[str, Any]] = []
    for family in families:
        family_graphs = graphs_by_family.get(family, [])
        family_edges = edges_by_family.get(family, [])
        graph_count = len(family_graphs)
        edge_count = len(family_edges)
        singleton_count = sum(1 for row in family_graphs if int_or_zero(row.get("edge_count")) == 1)
        rows.append(
            {
                "graph_family": family,
                "graph_count": graph_count,
                "edge_count": edge_count,
                "edges_per_graph": round(edge_count / graph_count, 6) if graph_count else 0,
                "singleton_graph_count": singleton_count,
                "singleton_graph_rate": round(singleton_count / graph_count, 6) if graph_count else 0,
                "distinct_l1_packet_count": len({row.get("l1_packet_id", "") for row in family_edges if row.get("l1_packet_id")}),
                "distinct_l2_feature_count": len({row.get("l2_row_id", "") for row in family_edges if row.get("l2_row_id")}),
                "distinct_entity_count": count_distinct_nodes(family_edges, {"SYMBOL", "ENTITY"}),
                "distinct_source_family_count": len({row.get("source_family", "") for row in family_edges if row.get("source_family")}),
                "distinct_event_cluster_count": count_distinct_nodes(family_edges, {"EVENT_CLUSTER"}),
                "coverage_gap_count": len(gaps) if family == "COVERAGE_GAP" else 0,
                "diagnostic_interpretation": "quality metric for review only; not a signal or thesis acceptance",
            }
        )
    return rows


def build_event_cluster_limitations(
    clusters: list[dict[str, str]],
    edges: list[dict[str, str]],
) -> list[dict[str, Any]]:
    edge_counts: Counter[str] = Counter()
    source_families: dict[str, set[str]] = defaultdict(set)
    entities: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        cluster_key = extract_event_cluster_key(edge.get("target_node_id", "")) or extract_event_cluster_key(edge.get("source_node_id", ""))
        if not cluster_key:
            continue
        edge_counts[cluster_key] += 1
        if edge.get("source_family"):
            source_families[cluster_key].add(edge["source_family"])
        for node in (edge.get("source_node_id", ""), edge.get("target_node_id", "")):
            node_type, node_key = split_node(node)
            if node_type in {"SYMBOL", "ENTITY"} and node_key:
                entities[cluster_key].add(node)

    rows: list[dict[str, Any]] = []
    for row in clusters:
        cluster_key = row.get("event_cluster_key", "")
        rows.append(
            {
                **row,
                "cluster_basis": row.get("cluster_basis") or EVENT_CLUSTER_BASIS,
                "event_identity_status": EVENT_IDENTITY_STATUS,
                "same_event_assertion": "false",
                "edge_count": edge_counts.get(cluster_key, 0),
                "distinct_source_family_count": len(source_families.get(cluster_key, set())),
                "distinct_entity_count": len(entities.get(cluster_key, set())),
                "l4_interpretation": "proto event bucket only; not confirmed same-event identity",
            }
        )
    return rows


def build_coverage_gap_summary(gaps: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in gaps:
        key = (
            row.get("reason_code", ""),
            row.get("source_family", ""),
            row.get("time_bucket", ""),
        )
        grouped[key].append(row)

    rows: list[dict[str, Any]] = []
    for (reason, source_family, bucket), items in sorted(grouped.items()):
        example = items[0]
        rows.append(
            {
                "reason_code": reason,
                "source_family": source_family,
                "event_time_bucket": bucket,
                "gap_count": len(items),
                "example_lineage_id": example.get("source_row_id", ""),
                "example_l1_packet_id": example.get("l1_packet_id", ""),
                "negative_evidence_allowed": 0,
                "l4_interpretation": "UNKNOWN/BLOCKER, not negative evidence",
            }
        )
    return rows


def build_handoff_manifest(
    source_manifest: dict[str, Any],
    quality_rows: list[dict[str, Any]],
    edges: list[dict[str, str]],
    graphs: list[dict[str, str]],
    gaps: list[dict[str, str]],
    unsupported_rows: list[dict[str, str]],
) -> dict[str, Any]:
    graph_family_counts = Counter(row.get("graph_family", "") for row in graphs)
    edge_family_counts = Counter(row.get("graph_family", "") for row in edges)
    gap_reason_counts = Counter(row.get("reason_code", "") for row in gaps)
    return {
        "task_id": TASK_ID,
        "created_at": now_iso(),
        "diagnostic_only": True,
        "strategy_status": "NOT_ACCEPTED",
        "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "no_broker_mutation": True,
        "no_live_order": True,
        "no_paper_promotion": True,
        "input_artifacts": source_manifest.get("inputs", []),
        "source_task_4152_output_counts": source_manifest.get("output_counts", {}),
        "output_artifacts": [
            "l3_graph_quality_summary.csv",
            "l3_graph_quality_summary.json",
            "l3_event_clusters_with_limitations.csv",
            "l3_unsupported_relation_families.csv",
            "l3_coverage_gap_summary_by_reason_source_date.csv",
            "l3_l4_diagnostic_handoff_manifest.json",
        ],
        "graph_family_counts": dict(sorted(graph_family_counts.items())),
        "edge_family_counts": dict(sorted(edge_family_counts.items())),
        "coverage_gap_counts_by_reason": dict(sorted(gap_reason_counts.items())),
        "unsupported_relation_families": unsupported_rows,
        "event_identity_status": EVENT_IDENTITY_STATUS,
        "same_event_assertion": False,
        "quality_summary": quality_rows,
        "forbidden_l4_assumptions": list(FORBIDDEN_L4_ASSUMPTIONS),
    }


def count_distinct_nodes(edges: list[dict[str, str]], node_types: set[str]) -> int:
    nodes: set[str] = set()
    for edge in edges:
        for key in ("source_node_id", "target_node_id"):
            node_type, node_key = split_node(edge.get(key, ""))
            if node_type in node_types and node_key:
                nodes.add(edge.get(key, ""))
    return len(nodes)


def extract_event_cluster_key(node: str) -> str:
    if node.startswith("EVENT_CLUSTER:"):
        return node.split(":", 1)[1]
    return ""


def split_node(node: str) -> tuple[str, str]:
    if ":" not in node:
        return node, ""
    left, right = node.split(":", 1)
    return left, right


def int_or_zero(value: str | None) -> int:
    try:
        return int(value or "0")
    except ValueError:
        return 0


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

