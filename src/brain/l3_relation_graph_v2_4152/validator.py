from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .contracts import FORBIDDEN_OUTPUT_VALUES, GraphFamily, TASK_ID


REQUIRED_FILES = (
    "l3_relation_edges.csv",
    "l3_event_clusters.csv",
    "l3_relation_graphs.csv",
    "l3_coverage_gaps.csv",
    "l3_relation_graph_v2_manifest.json",
)
ALLOWED_DIRECTIONS = {"RISK_REVIEW", "SUPPORT_REVIEW", "CONTEXT_ONLY", "MIXED_REVIEW", "UNKNOWN_BLOCKER"}
PRICE_LEAKAGE_FIELDS = {"return", "returns", "alpha", "abnormal_return", "price_reaction", "entry_score"}


def validate_artifacts(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    passes: list[str] = []
    failures: list[str] = []
    for name in REQUIRED_FILES:
        path = root / name
        if path.exists():
            passes.append(f"exists: {path}")
        else:
            failures.append(f"missing: {path}")

    if failures:
        return result("FAIL", passes, failures)

    edges = read_csv(root / "l3_relation_edges.csv")
    clusters = read_csv(root / "l3_event_clusters.csv")
    graphs = read_csv(root / "l3_relation_graphs.csv")
    gaps = read_csv(root / "l3_coverage_gaps.csv")
    manifest = json.loads((root / "l3_relation_graph_v2_manifest.json").read_text(encoding="utf-8"))

    if edges:
        passes.append(f"edge_rows: {len(edges)}")
    else:
        failures.append("no relation edges")
    if clusters:
        passes.append(f"event_cluster_rows: {len(clusters)}")
    else:
        failures.append("no event clusters")
    if graphs:
        passes.append(f"graph_rows: {len(graphs)}")
    else:
        failures.append("no relation graphs")
    passes.append(f"coverage_gap_rows: {len(gaps)}")

    edge_dedupe = [row.get("dedupe_key", "") for row in edges]
    if len(edge_dedupe) == len(set(edge_dedupe)):
        passes.append("edge dedupe keys are unique")
    else:
        failures.append("duplicate edge dedupe keys found")

    graph_keys = [row.get("graph_key", "") for row in graphs]
    if len(graph_keys) == len(set(graph_keys)):
        passes.append("graph keys are unique")
    else:
        failures.append("duplicate graph keys found")

    for row in edges:
        if row.get("raw_l0_read") not in {"0", "False", "false", ""}:
            failures.append(f"raw L0 bypass detected: {row.get('edge_id')}")
        if not row.get("l1_packet_id") or not row.get("l2_row_id"):
            failures.append(f"missing L1/L2 lineage: {row.get('edge_id')}")
        if row.get("direction_review") not in ALLOWED_DIRECTIONS:
            failures.append(f"invalid direction_review: {row.get('edge_id')} {row.get('direction_review')}")
        if forbidden_value_present(row):
            failures.append(f"forbidden trading output value in edge: {row.get('edge_id')}")
    passes.append("edges checked for lineage, no raw L0 bypass, direction enum, and forbidden outputs")

    for row in graphs:
        family = row.get("graph_family", "")
        if family not in {item.value for item in GraphFamily}:
            failures.append(f"invalid graph family: {row.get('graph_key')} {family}")
        if row.get("forbidden_output_present") not in {"0", ""}:
            failures.append(f"graph reports forbidden output: {row.get('graph_key')}")
        if row.get("lineage_complete") != "1":
            failures.append(f"graph lineage incomplete: {row.get('graph_key')}")
        if forbidden_value_present(row):
            failures.append(f"forbidden trading output value in graph: {row.get('graph_key')}")
    passes.append("graphs checked for family enum, lineage, and forbidden outputs")

    for row in gaps:
        if row.get("negative_evidence_allowed") not in {"0", ""}:
            failures.append(f"coverage gap allowed negative evidence: {row.get('gap_id')}")
        if not row.get("reason_code"):
            failures.append(f"coverage gap missing reason code: {row.get('gap_id')}")
    passes.append("coverage gaps are non-negative and reason-coded")

    normal_newswire_unknown = [
        row
        for row in edges
        if row.get("source_family") == "public_newswire_feeds"
        and row.get("graph_family") != GraphFamily.COVERAGE_GAP.value
        and row.get("target_node_id") in {"SOURCE_FAMILY:public_newswire_feeds", "ECONOMIC_DIMENSION:UNKNOWN"}
    ]
    if normal_newswire_unknown:
        failures.append(f"mapped newswire collapsed into normal UNKNOWN graph: {len(normal_newswire_unknown)}")
    else:
        passes.append("newswire SOURCE_FAMILY/UNKNOWN collapse is routed out of normal relation graphs")

    gap_reasons = {row.get("reason_code", "") for row in gaps}
    if "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE" in gap_reasons:
        passes.append("newswire mapped-but-not-article-feature gap is explicit")
    else:
        failures.append("missing NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE coverage gap")

    all_fields = set().union(*(row.keys() for row in [*edges, *graphs, *clusters, *gaps])) if edges or graphs or clusters or gaps else set()
    leaked_fields = {field for field in all_fields if field.lower() in PRICE_LEAKAGE_FIELDS}
    if leaked_fields:
        failures.append(f"price leakage fields present: {sorted(leaked_fields)}")
    else:
        passes.append("price reaction/return/alpha fields absent")

    old_count = int(manifest.get("old_task_4150_graph_count", 0))
    new_count = len(graphs)
    if new_count > old_count:
        passes.append(f"graph count expanded from {old_count} to {new_count}")
    else:
        failures.append(f"graph count did not expand: old={old_count} new={new_count}")

    status = "PASS" if not failures else "FAIL"
    return result(status, passes, failures)


def result(status: str, passes: list[str], failures: list[str]) -> dict[str, Any]:
    return {"task_id": TASK_ID, "status": status, "passes": passes, "failures": failures}


def forbidden_value_present(row: dict[str, str]) -> bool:
    for key, value in row.items():
        upper = value.upper()
        if key.endswith("_allowed") or key in {"trading_eligible", "diagnostic_only"}:
            continue
        if upper in FORBIDDEN_OUTPUT_VALUES:
            return True
    return False


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

