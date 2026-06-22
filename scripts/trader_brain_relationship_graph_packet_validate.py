from __future__ import annotations

import argparse
import csv
from datetime import datetime
import sys
from pathlib import Path


NODE_REQUIRED = {
    "info_node_id",
    "node_type",
    "source_artifact",
    "asof_ts",
    "layer",
    "review_state",
    "uncertainty_cap",
    "forbidden_output_audit",
    "review_owner",
}

EDGE_REQUIRED = {
    "edge_id",
    "from_node_id",
    "to_node_id",
    "edge_type",
    "required_evidence",
    "edge_evidence_id",
    "asof_ts",
    "review_owner",
}

TRANSITION_REQUIRED = {
    "from_node_id",
    "to_node_id",
    "from_layer",
    "to_layer",
    "required_intermediate",
    "intermediate_ref",
}

UPDATE_REQUIRED = {
    "update_id",
    "before_node_id",
    "new_node_id",
    "after_node_id",
    "edge_id",
    "before_state",
    "after_state",
    "asof_ts",
}

ALLOWED_NODE_TYPES = {
    "attention_packet",
    "salience",
    "memory",
    "hypothesis",
    "contradiction",
    "disconfirmation",
    "journal",
    "expert_lens",
    "source_gap",
    "mechanism",
}

ALLOWED_REVIEW_STATES = {
    "enough_for_review",
    "defer",
    "source_gap",
    "block",
    "noise",
    "context_only",
    "cap",
    "review_needed",
}

ALLOWED_LAYERS = {"L1", "L2", "L3", "L4", "L5", "L6", "L7", "governance"}

ALLOWED_EDGE_TYPES = {
    "reinforces",
    "weakens",
    "invalidates",
    "conditions",
    "sequences",
    "explains",
    "contradicts",
    "source_gap_for",
    "noise_for",
}

FORBIDDEN_OUTPUT_MARKERS = {
    "buy_signal",
    "sell_signal",
    "trade_permission",
    "position_sizing",
    "backtest_eligibility",
    "alpha_score",
    "global_rank",
    "order_submit",
    "real_capital",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str, *, label: str, errors: list[str]) -> datetime | None:
    if not value:
        errors.append(f"{label}: missing asof_ts")
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{label}: invalid ISO timestamp {value}")
        return None


def require_columns(path: Path, rows: list[dict[str, str]], required: set[str], errors: list[str]) -> None:
    columns = set(rows[0].keys()) if rows else set()
    missing = required - columns
    if missing:
        errors.append(f"{path.name}: missing columns {','.join(sorted(missing))}")


def scan_forbidden_outputs(scope: str, row: dict[str, str], errors: list[str]) -> None:
    for field, value in row.items():
        if field in {"forbidden_output_audit", "forbidden_effect", "forbidden_use"}:
            continue
        lowered = str(value).lower()
        for marker in FORBIDDEN_OUTPUT_MARKERS:
            if marker in lowered:
                errors.append(f"{scope}: forbidden output marker {marker} in {field}")


def validate_nodes(path: Path, errors: list[str]) -> tuple[dict[str, dict[str, str]], dict[str, datetime]]:
    rows = read_csv(path)
    require_columns(path, rows, NODE_REQUIRED, errors)
    nodes: dict[str, dict[str, str]] = {}
    timestamps: dict[str, datetime] = {}
    for idx, row in enumerate(rows, start=2):
        node_id = row.get("info_node_id", "")
        scope = f"nodes.csv row {idx} {node_id or '<missing>'}"
        if not node_id:
            errors.append(f"{scope}: missing info_node_id")
            continue
        if node_id in nodes:
            errors.append(f"{scope}: duplicate info_node_id")
        nodes[node_id] = row
        if row.get("node_type") not in ALLOWED_NODE_TYPES:
            errors.append(f"{scope}: invalid node_type {row.get('node_type')}")
        if row.get("layer") not in ALLOWED_LAYERS:
            errors.append(f"{scope}: invalid layer {row.get('layer')}")
        if row.get("review_state") not in ALLOWED_REVIEW_STATES:
            errors.append(f"{scope}: invalid review_state {row.get('review_state')}")
        for field in ["source_artifact", "uncertainty_cap", "review_owner", "forbidden_output_audit"]:
            if not row.get(field):
                errors.append(f"{scope}: missing {field}")
        ts = parse_ts(row.get("asof_ts", ""), label=scope, errors=errors)
        if ts is not None:
            timestamps[node_id] = ts
        if row.get("node_type") == "source_gap" and "negative" in row.get("review_state", "").lower():
            errors.append(f"{scope}: source_gap converted to negative")
        scan_forbidden_outputs(scope, row, errors)
    return nodes, timestamps


def validate_edges(path: Path, nodes: dict[str, dict[str, str]], timestamps: dict[str, datetime], errors: list[str]) -> set[str]:
    rows = read_csv(path)
    require_columns(path, rows, EDGE_REQUIRED, errors)
    edge_ids: set[str] = set()
    for idx, row in enumerate(rows, start=2):
        edge_id = row.get("edge_id", "")
        scope = f"edges.csv row {idx} {edge_id or '<missing>'}"
        if not edge_id:
            errors.append(f"{scope}: missing edge_id")
            continue
        if edge_id in edge_ids:
            errors.append(f"{scope}: duplicate edge_id")
        edge_ids.add(edge_id)
        from_id = row.get("from_node_id", "")
        to_id = row.get("to_node_id", "")
        edge_type = row.get("edge_type", "")
        if from_id not in nodes:
            errors.append(f"{scope}: unknown from_node_id {from_id}")
        if to_id not in nodes:
            errors.append(f"{scope}: unknown to_node_id {to_id}")
        if edge_type not in ALLOWED_EDGE_TYPES:
            errors.append(f"{scope}: invalid edge_type {edge_type}")
        for field in ["required_evidence", "edge_evidence_id", "review_owner"]:
            if not row.get(field):
                errors.append(f"{scope}: missing {field}")
        if edge_type in {"explains", "reinforces"} and not row.get("mechanism_id"):
            errors.append(f"{scope}: mechanism_identity_missing")
        if edge_type == "sequences":
            predecessor = row.get("predecessor_node_id", "")
            if not predecessor:
                errors.append(f"{scope}: temporal_identity_missing")
            elif predecessor != from_id:
                errors.append(f"{scope}: predecessor_node_id must equal from_node_id for sequences")
            if from_id in timestamps and to_id in timestamps and timestamps[from_id] > timestamps[to_id]:
                errors.append(f"{scope}: sequence from_node_id occurs after to_node_id")
        if edge_type in {"invalidates", "contradicts"} and not row.get("affected_node_id"):
            errors.append(f"{scope}: invalidation edge missing affected_node_id")
        if edge_type == "source_gap_for" and not row.get("missing_source_family"):
            errors.append(f"{scope}: source_gap edge missing missing_source_family")
        if "missing_as_negative" in " ".join(row.values()).lower():
            errors.append(f"{scope}: missing_to_negative_detected")
        parse_ts(row.get("asof_ts", ""), label=scope, errors=errors)
        scan_forbidden_outputs(scope, row, errors)
    return edge_ids


def validate_transitions(path: Path, nodes: dict[str, dict[str, str]], errors: list[str]) -> None:
    rows = read_csv(path)
    require_columns(path, rows, TRANSITION_REQUIRED, errors)
    for idx, row in enumerate(rows, start=2):
        scope = f"transitions.csv row {idx}"
        from_id = row.get("from_node_id", "")
        to_id = row.get("to_node_id", "")
        if from_id not in nodes:
            errors.append(f"{scope}: unknown from_node_id {from_id}")
        if to_id not in nodes:
            errors.append(f"{scope}: unknown to_node_id {to_id}")
        if row.get("from_layer") == "L1" and row.get("to_layer") in {"L5", "L6", "L7"}:
            errors.append(f"{scope}: cross_layer_jump_detected")
        if not row.get("required_intermediate") or not row.get("intermediate_ref"):
            errors.append(f"{scope}: missing required intermediate trace")
        scan_forbidden_outputs(scope, row, errors)


def validate_updates(path: Path, nodes: dict[str, dict[str, str]], edge_ids: set[str], timestamps: dict[str, datetime], errors: list[str]) -> None:
    rows = read_csv(path)
    require_columns(path, rows, UPDATE_REQUIRED, errors)
    for idx, row in enumerate(rows, start=2):
        update_id = row.get("update_id", "")
        scope = f"update_chains.csv row {idx} {update_id or '<missing>'}"
        for field in ["before_node_id", "new_node_id", "after_node_id"]:
            value = row.get(field, "")
            if value not in nodes:
                errors.append(f"{scope}: unknown {field} {value}")
        if row.get("edge_id") not in edge_ids:
            errors.append(f"{scope}: unknown edge_id {row.get('edge_id')}")
        update_ts = parse_ts(row.get("asof_ts", ""), label=scope, errors=errors)
        new_id = row.get("new_node_id", "")
        if update_ts is not None and new_id in timestamps and update_ts < timestamps[new_id]:
            errors.append(f"{scope}: update asof_ts precedes new_node_id asof_ts")
        scan_forbidden_outputs(scope, row, errors)


def validate_graph_dir(graph_dir: Path) -> list[str]:
    errors: list[str] = []
    required_files = ["nodes.csv", "edges.csv", "transitions.csv"]
    for name in required_files:
        path = graph_dir / name
        if not path.exists():
            errors.append(f"missing {path}")
    if errors:
        return errors
    nodes, timestamps = validate_nodes(graph_dir / "nodes.csv", errors)
    edge_ids = validate_edges(graph_dir / "edges.csv", nodes, timestamps, errors)
    validate_transitions(graph_dir / "transitions.csv", nodes, errors)
    updates = graph_dir / "update_chains.csv"
    if updates.exists():
        validate_updates(updates, nodes, edge_ids, timestamps, errors)
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph-dir", required=True, type=Path)
    args = parser.parse_args()
    errors = validate_graph_dir(args.graph_dir)
    if errors:
        for error in errors:
            print(f"[RELATIONSHIP_GRAPH_PACKET_ERROR] {error}")
        sys.exit(1)
    print(f"[RELATIONSHIP_GRAPH_PACKET_OK] {args.graph_dir}")


if __name__ == "__main__":
    main()
