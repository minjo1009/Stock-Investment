from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4154"
SOURCE_ARTIFACT_DIR = Path("data/artifacts/task_4152_l3_relation_graph_v2")
OUTPUT_ARTIFACT_DIR = Path("data/artifacts/task_4154_l3_relation_graph_v2_quality_guard")
REQUIRED_ARTIFACTS = (
    "l3_graph_quality_summary.csv",
    "l3_graph_quality_summary.json",
    "l3_event_clusters_with_limitations.csv",
    "l3_unsupported_relation_families.csv",
    "l3_coverage_gap_summary_by_reason_source_date.csv",
    "l3_l4_diagnostic_handoff_manifest.json",
)
UNSUPPORTED_REQUIRED = {"MACRO_SECTOR", "SECTOR_THEME", "CONTRADICTION"}
FORBIDDEN_OUTPUT_VALUES = {
    "BUY",
    "SELL",
    "RANK",
    "RANKING",
    "SIZING",
    "ORDER",
    "ORDER_INTENT",
    "ALPHA",
    "RETURN",
    "PRICE_REACTION",
    "PAPER_ELIGIBLE",
    "LIVE_ELIGIBLE",
    "STRATEGY_ACCEPTED",
    "DEPLOYMENT_READY",
}
ALLOWED_BOUNDARY_VALUES = {
    "NOT_ACCEPTED",
    "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "FORBIDDEN",
}


def validate_quality_guard(
    output_dir: str | Path = OUTPUT_ARTIFACT_DIR,
    source_dir: str | Path = SOURCE_ARTIFACT_DIR,
) -> dict[str, Any]:
    out = Path(output_dir)
    source = Path(source_dir)
    passes: list[str] = []
    failures: list[str] = []

    for artifact in REQUIRED_ARTIFACTS:
        path = out / artifact
        if path.exists():
            passes.append(f"exists: {path}")
        else:
            failures.append(f"missing: {path}")
    if failures:
        return result("FAIL", passes, failures)

    source_graphs = read_csv(source / "l3_relation_graphs.csv")
    source_edges = read_csv(source / "l3_relation_edges.csv")
    source_clusters = read_csv(source / "l3_event_clusters.csv")
    source_gaps = read_csv(source / "l3_coverage_gaps.csv")
    quality = read_csv(out / "l3_graph_quality_summary.csv")
    quality_json = json.loads((out / "l3_graph_quality_summary.json").read_text(encoding="utf-8"))
    clusters = read_csv(out / "l3_event_clusters_with_limitations.csv")
    unsupported = read_csv(out / "l3_unsupported_relation_families.csv")
    gap_summary = read_csv(out / "l3_coverage_gap_summary_by_reason_source_date.csv")
    handoff = json.loads((out / "l3_l4_diagnostic_handoff_manifest.json").read_text(encoding="utf-8"))

    if len(quality_json.get("rows", [])) == len(quality):
        passes.append("quality csv/json row counts reconcile")
    else:
        failures.append("quality csv/json row counts mismatch")

    graph_total = sum(int_or_zero(row.get("graph_count")) for row in quality)
    edge_total = sum(int_or_zero(row.get("edge_count")) for row in quality)
    if graph_total == len(source_graphs):
        passes.append(f"quality graph total reconciles: {graph_total}")
    else:
        failures.append(f"quality graph total mismatch: {graph_total} vs {len(source_graphs)}")
    if edge_total == len(source_edges):
        passes.append(f"quality edge total reconciles: {edge_total}")
    else:
        failures.append(f"quality edge total mismatch: {edge_total} vs {len(source_edges)}")

    required_quality_fields = {
        "graph_family",
        "graph_count",
        "edge_count",
        "edges_per_graph",
        "singleton_graph_count",
        "singleton_graph_rate",
        "distinct_l1_packet_count",
        "distinct_l2_feature_count",
    }
    if quality and required_quality_fields <= set(quality[0]):
        passes.append("quality summary required fields present")
    else:
        failures.append("quality summary required fields missing")

    if len(clusters) == len(source_clusters):
        passes.append("event cluster limitation rows reconcile")
    else:
        failures.append(f"event cluster limitation count mismatch: {len(clusters)} vs {len(source_clusters)}")
    if clusters and all(row.get("event_identity_status") == "PROTO_BUCKET" for row in clusters):
        passes.append("event clusters marked PROTO_BUCKET")
    else:
        failures.append("event clusters missing PROTO_BUCKET status")
    if clusters and all(row.get("same_event_assertion") == "false" for row in clusters):
        passes.append("same_event_assertion is false for every cluster")
    else:
        failures.append("same_event_assertion is not false for every cluster")

    unsupported_families = {row.get("relation_family", "") for row in unsupported}
    if UNSUPPORTED_REQUIRED <= unsupported_families:
        passes.append("unsupported relation families declared")
    else:
        failures.append(f"unsupported relation families missing: {sorted(UNSUPPORTED_REQUIRED - unsupported_families)}")
    if all(row.get("implementation_status") == "NOT_IMPLEMENTED" for row in unsupported):
        passes.append("unsupported families are marked NOT_IMPLEMENTED")
    else:
        failures.append("unsupported families have invalid implementation_status")

    gap_reasons = {row.get("reason_code", "") for row in gap_summary}
    if "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE" in gap_reasons:
        passes.append("newswire article feature coverage gap remains visible")
    else:
        failures.append("newswire article feature coverage gap missing from summary")
    if sum(int_or_zero(row.get("gap_count")) for row in gap_summary) == len(source_gaps):
        passes.append("coverage gap summary reconciles to source gaps")
    else:
        failures.append("coverage gap summary does not reconcile to source gaps")

    required_flags = {
        "diagnostic_only": True,
        "strategy_status": "NOT_ACCEPTED",
        "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "no_broker_mutation": True,
        "no_live_order": True,
        "no_paper_promotion": True,
        "event_identity_status": "PROTO_BUCKET",
        "same_event_assertion": False,
    }
    for key, expected in required_flags.items():
        if handoff.get(key) == expected:
            passes.append(f"handoff flag valid: {key}")
        else:
            failures.append(f"handoff flag invalid: {key}={handoff.get(key)!r}")
    if len(handoff.get("forbidden_l4_assumptions", [])) >= 7:
        passes.append("handoff forbidden assumptions present")
    else:
        failures.append("handoff forbidden assumptions missing or too short")

    public_newswire_normal_unknown = [
        row
        for row in source_edges
        if row.get("source_family") == "public_newswire_feeds"
        and row.get("graph_family") != "COVERAGE_GAP"
        and row.get("target_node_id") in {"SOURCE_FAMILY:public_newswire_feeds", "ECONOMIC_DIMENSION:UNKNOWN"}
    ]
    if not public_newswire_normal_unknown:
        passes.append("public newswire UNKNOWN collapse remains outside normal relation graphs")
    else:
        failures.append(f"public newswire UNKNOWN collapse found in normal graphs: {len(public_newswire_normal_unknown)}")

    forbidden_hits = find_forbidden_values([quality, clusters, unsupported, gap_summary], handoff)
    if not forbidden_hits:
        passes.append("no forbidden trading output values in TASK-4154 outputs")
    else:
        failures.append(f"forbidden output values found: {forbidden_hits[:10]}")

    status = "PASS" if not failures else "FAIL"
    return result(status, passes, failures)


def find_forbidden_values(csv_groups: list[list[dict[str, str]]], handoff: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for rows in csv_groups:
        for row in rows:
            for key, value in row.items():
                upper = str(value).strip().upper()
                if key in {"l4_interpretation", "diagnostic_interpretation"}:
                    continue
                if upper in FORBIDDEN_OUTPUT_VALUES and upper not in ALLOWED_BOUNDARY_VALUES:
                    hits.append(f"{key}={value}")
    for key in ("strategy_status", "deployment_status", "real_capital"):
        value = str(handoff.get(key, "")).strip().upper()
        if value in FORBIDDEN_OUTPUT_VALUES and value not in ALLOWED_BOUNDARY_VALUES:
            hits.append(f"{key}={handoff.get(key)}")
    return hits


def result(status: str, passes: list[str], failures: list[str]) -> dict[str, Any]:
    return {"task_id": TASK_ID, "status": status, "passes": passes, "failures": failures}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def int_or_zero(value: str | None) -> int:
    try:
        return int(float(value or "0"))
    except ValueError:
        return 0

