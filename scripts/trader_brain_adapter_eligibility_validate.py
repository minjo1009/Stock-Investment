from __future__ import annotations

import argparse
import csv
from datetime import datetime
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_BUNDLE_COLUMNS = {
    "candidate_bundle_id",
    "source_graph_id",
    "asof_ts",
    "thesis_question",
    "supporting_node_ids",
    "supporting_edge_ids",
    "contradiction_node_ids",
    "invalidation_edge_ids",
    "weakest_layer",
    "unresolved_gaps",
    "bundle_state",
    "forbidden_output_audit",
    "pass_does_not_mean",
}

FORBIDDEN_MARKERS = {
    "buy_signal",
    "sell_signal",
    "trade_permission",
    "position_sizing",
    "backtest_eligibility",
    "alpha_score",
    "global_rank",
    "real_capital",
}

PASS_DOES_NOT_MEAN = (
    "strategy acceptance, deployment readiness, broker truth, backtest validity, "
    "source completeness, or real-capital permission"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def parse_ts(value: str, errors: list[str], scope: str) -> datetime | None:
    if not value:
        errors.append(f"{scope}: missing_bundle_asof")
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{scope}: invalid_bundle_asof {value}")
        return None


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def graph_manifest(path: Path) -> dict[str, Path]:
    rows = read_csv(path)
    required = {"source_graph_id", "graph_dir"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"graph manifest missing columns {','.join(sorted(missing))}")
    return {row["source_graph_id"]: resolve_path(row["graph_dir"]) for row in rows}


def graph_indexes(graph_dir: Path) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], list[str]]:
    errors: list[str] = []
    nodes_path = graph_dir / "nodes.csv"
    edges_path = graph_dir / "edges.csv"
    if not nodes_path.exists():
        errors.append(f"missing graph nodes {nodes_path}")
        return {}, {}, errors
    if not edges_path.exists():
        errors.append(f"missing graph edges {edges_path}")
        return {}, {}, errors
    nodes = {row.get("info_node_id", ""): row for row in read_csv(nodes_path)}
    edges = {row.get("edge_id", ""): row for row in read_csv(edges_path)}
    return nodes, edges, errors


def forbidden_marker_errors(row: dict[str, str], scope: str) -> list[str]:
    errors: list[str] = []
    for field, value in row.items():
        if field in {"forbidden_output_audit", "pass_does_not_mean", "expected_error"}:
            continue
        lowered = str(value).lower()
        for marker in FORBIDDEN_MARKERS:
            if marker in lowered:
                errors.append(f"{scope}: forbidden_output_marker {marker} in {field}")
    return errors


def evaluate_bundle(row: dict[str, str], graphs: dict[str, Path]) -> dict[str, str]:
    bundle_id = row.get("candidate_bundle_id", "")
    errors: list[str] = []
    scope = f"bundle {bundle_id or '<missing>'}"
    bundle_ts = parse_ts(row.get("asof_ts", ""), errors, scope)
    errors.extend(forbidden_marker_errors(row, scope))

    graph_id = row.get("source_graph_id", "")
    graph_dir = graphs.get(graph_id)
    mechanism_ids: set[str] = set()
    evidence_refs: set[str] = set()
    if graph_dir is None:
        errors.append(f"{scope}: unknown_graph_id {graph_id}")
        nodes: dict[str, dict[str, str]] = {}
        edges: dict[str, dict[str, str]] = {}
    else:
        nodes, edges, graph_errors = graph_indexes(graph_dir)
        errors.extend(f"{scope}: {error}" for error in graph_errors)

    for node_id in split_ids(row.get("supporting_node_ids", "")) + split_ids(row.get("contradiction_node_ids", "")):
        node = nodes.get(node_id)
        if node is None:
            errors.append(f"{scope}: unknown_node_id {node_id}")
            continue
        if node.get("mechanism_id"):
            mechanism_ids.add(node["mechanism_id"])
        if node.get("evidence_id"):
            evidence_refs.add(node["evidence_id"])
        if node.get("edge_evidence_id"):
            evidence_refs.add(node["edge_evidence_id"])
        node_ts = parse_ts(node.get("asof_ts", ""), errors, f"{scope} node {node_id}")
        if bundle_ts is not None and node_ts is not None and node_ts > bundle_ts:
            errors.append(f"{scope}: future_node_leakage {node_id}")

    for edge_id in split_ids(row.get("supporting_edge_ids", "")) + split_ids(row.get("invalidation_edge_ids", "")):
        edge = edges.get(edge_id)
        if edge is None:
            errors.append(f"{scope}: unknown_edge_id {edge_id}")
            continue
        if edge.get("mechanism_id"):
            mechanism_ids.add(edge["mechanism_id"])
        if edge.get("edge_evidence_id"):
            evidence_refs.add(edge["edge_evidence_id"])
        edge_ts = parse_ts(edge.get("asof_ts", ""), errors, f"{scope} edge {edge_id}")
        if bundle_ts is not None and edge_ts is not None and edge_ts > bundle_ts:
            errors.append(f"{scope}: future_edge_leakage {edge_id}")

    bundle_state = row.get("bundle_state", "")
    unresolved = row.get("unresolved_gaps", "")
    has_contradiction = bool(row.get("contradiction_node_ids") or row.get("invalidation_edge_ids"))
    if bundle_state == "research_review_only" and (unresolved or has_contradiction):
        if unresolved:
            errors.append(f"{scope}: source_gap_to_eligible")
        if has_contradiction:
            errors.append(f"{scope}: contradiction_to_eligible")

    if errors:
        return {
            "candidate_bundle_id": bundle_id,
            "source_graph_id": graph_id,
            "eligibility_state": "invalid",
            "eligible_reason": "",
            "blocked_reason": "|".join(errors),
            "mechanism_ids": ";".join(sorted(mechanism_ids)),
            "evidence_refs": ";".join(sorted(evidence_refs)),
            "validation_authority": "GOVERNANCE_HEALTH",
            "pass_does_not_mean": PASS_DOES_NOT_MEAN,
        }

    if bundle_state == "research_review_only":
        return {
            "candidate_bundle_id": bundle_id,
            "source_graph_id": graph_id,
            "eligibility_state": "eligible",
            "eligible_reason": "clean_research_bundle",
            "blocked_reason": "",
            "mechanism_ids": ";".join(sorted(mechanism_ids)),
            "evidence_refs": ";".join(sorted(evidence_refs)),
            "validation_authority": "RESEARCH_ONLY",
            "pass_does_not_mean": PASS_DOES_NOT_MEAN,
        }

    reason = {
        "blocked_by_gap": "source_gap_unresolved",
        "blocked_by_contradiction": "contradiction_unresolved",
        "context_only": "context_only_not_adapter_ready",
    }.get(bundle_state, f"unsupported_bundle_state_{bundle_state}")
    return {
        "candidate_bundle_id": bundle_id,
        "source_graph_id": graph_id,
        "eligibility_state": "blocked",
        "eligible_reason": "",
        "blocked_reason": reason,
        "mechanism_ids": ";".join(sorted(mechanism_ids)),
        "evidence_refs": ";".join(sorted(evidence_refs)),
        "validation_authority": "RESEARCH_ONLY",
        "pass_does_not_mean": PASS_DOES_NOT_MEAN,
    }


def validate_bundles(bundles_path: Path, graph_manifest_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    rows = read_csv(bundles_path)
    if not rows:
        return [], [f"{bundles_path}: no rows"]
    missing = REQUIRED_BUNDLE_COLUMNS - set(rows[0].keys())
    if missing:
        return [], [f"{bundles_path.name}: missing columns {','.join(sorted(missing))}"]
    try:
        graphs = graph_manifest(graph_manifest_path)
    except ValueError as exc:
        return [], [str(exc)]

    seen: set[str] = set()
    audit_rows: list[dict[str, str]] = []
    for row in rows:
        bundle_id = row.get("candidate_bundle_id", "")
        if bundle_id in seen:
            errors.append(f"bundle {bundle_id}: duplicate_candidate_bundle_id")
        seen.add(bundle_id)
        result = evaluate_bundle(row, graphs)
        audit_rows.append(result)
        if result["eligibility_state"] == "invalid":
            errors.append(result["blocked_reason"])
    return audit_rows, errors


AUDIT_FIELDS = [
    "candidate_bundle_id",
    "source_graph_id",
    "eligibility_state",
    "eligible_reason",
    "blocked_reason",
    "mechanism_ids",
    "evidence_refs",
    "validation_authority",
    "pass_does_not_mean",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundles", required=True, type=Path)
    parser.add_argument("--graph-manifest", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    audit_rows, errors = validate_bundles(args.bundles, args.graph_manifest)
    if args.audit_output:
        write_csv(args.audit_output, audit_rows, AUDIT_FIELDS)
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_ADAPTER_ELIGIBILITY_ERROR] {error}")
        sys.exit(1)
    eligible = sum(1 for row in audit_rows if row["eligibility_state"] == "eligible")
    blocked = sum(1 for row in audit_rows if row["eligibility_state"] == "blocked")
    print(f"[TRADER_BRAIN_ADAPTER_ELIGIBILITY_OK] eligible={eligible} blocked={blocked}")


if __name__ == "__main__":
    main()
