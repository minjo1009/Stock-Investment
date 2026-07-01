from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.l3_diagnostic_strategy_view_bootstrap.artifact_writer import (
    sha256_file,
    write_csv,
    write_json,
    write_jsonl,
)
from src.brain.l3_diagnostic_strategy_view_bootstrap.contracts import (
    CalibrationStatus,
    CONFIDENCE_STATIC_WEIGHT,
    L3InputPrimitive,
    L3Meaning,
    closed_authority_flags,
)
from src.brain.l3_diagnostic_strategy_view_bootstrap.coverage_policy import load_coverage_gaps
from src.brain.l3_diagnostic_strategy_view_bootstrap.economic_meaning_classifier import classify_economic_meaning
from src.brain.l3_diagnostic_strategy_view_bootstrap.evidence_edge_builder import build_evidence_edge
from src.brain.l3_diagnostic_strategy_view_bootstrap.l2_read_view_bridge import (
    load_l1_article_index,
    load_l1_wide_index,
    normalize_article_features,
    normalize_wide_candidates,
    read_csv_rows,
)
from src.brain.l3_diagnostic_strategy_view_bootstrap.relation_graph_aggregator import aggregate_relation_graph


TASK_ID = "TASK-4150"
SLUG = "task_4150_l3_diagnostic_strategy_view_bootstrap"
REPORT_DIR = Path("docs/reports") / SLUG


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/l3_diagnostic_strategy_view_bootstrap_4150.json")
    args = parser.parse_args()
    build(args.config)
    return 0


def build(config_path: str | Path) -> dict[str, Any]:
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    out_dir = Path(config["outputs"]["artifact_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    l2_article_rows = read_csv_rows(inputs["l2_article_features"])
    l1_article_index = load_l1_article_index(inputs["l1_article_packets"])
    article_inputs, article_rejections = normalize_article_features(l2_article_rows, l1_article_index)

    l2_wide_rows = read_csv_rows(inputs["l2_wide_candidates"])
    l1_wide_index = load_l1_wide_index(inputs["l1_wide_packets"])
    wide_inputs, wide_rejections = normalize_wide_candidates(l2_wide_rows, l1_wide_index)

    coverage_gaps = load_coverage_gaps(inputs["l0_status"])
    l3_inputs = article_inputs + wide_inputs
    rejected = article_rejections + wide_rejections
    meanings = [build_meaning(row) for row in l3_inputs]
    edges = [build_evidence_edge(meaning) for meaning in meanings]
    relation_graph = aggregate_relation_graph(edges, coverage_gaps)

    blocker_gap_rows = build_blocker_gap_rows(coverage_gaps, rejected)
    review_summary_rows = build_review_summary_rows(relation_graph)

    manifest = {
        "task_id": TASK_ID,
        "config_path": str(config_path),
        "inputs": [
            {
                "path": path,
                "sha256": sha256_file(path),
                "role": key,
            }
            for key, path in inputs.items()
        ],
        "input_counts": {
            "l2_article_features": len(l2_article_rows),
            "l1_article_packets": len(l1_article_index),
            "l2_wide_candidates": len(l2_wide_rows),
            "l1_wide_packets": len(l1_wide_index),
        },
        "output_counts": {
            "l3_input_primitives": len(l3_inputs),
            "l3_meanings": len(meanings),
            "l3_evidence_edges": len(edges),
            "l3_relation_graphs": len(relation_graph["graphs"]),
            "l3_rejected_or_review_queue": len(rejected),
            "coverage_gaps": len(coverage_gaps),
            "blocker_gap_rows": len(blocker_gap_rows),
        },
        "row_reconciliation": {
            "l2_article_features_plus_l2_wide_candidates": len(l2_article_rows) + len(l2_wide_rows),
            "active_inputs_plus_rejected": len(l3_inputs) + len(rejected),
            "balanced": (len(l2_article_rows) + len(l2_wide_rows)) == (len(l3_inputs) + len(rejected)),
        },
        "authority": config["authority"],
    }

    write_json(out_dir / "l3_input_manifest.json", manifest)
    write_jsonl(out_dir / "l3_meanings.jsonl", meanings)
    write_jsonl(out_dir / "l3_evidence_edges.jsonl", edges)
    write_json(out_dir / "l3_relation_graph.json", relation_graph)
    write_csv(out_dir / "l3_blocker_gap_ledger.csv", blocker_gap_rows)
    write_csv(out_dir / "l3_review_summary.csv", review_summary_rows)
    write_csv(out_dir / "l3_rejected_or_review_queue.csv", rejected)
    write_json(out_dir / "l3_validator_report.json", {"task_id": TASK_ID, "status": "NOT_RUN"})
    write_report(manifest, relation_graph, blocker_gap_rows)
    write_artifact_manifest(out_dir)
    return manifest


def build_meaning(row: L3InputPrimitive) -> L3Meaning:
    dimension, event_class, direction, confidence, reason_codes = classify_economic_meaning(row)
    return L3Meaning(
        l3_meaning_id=f"l3meaning:{row.input_id.split(':', 1)[-1]}",
        input_id=row.input_id,
        l2_row_id=row.l2_row_id,
        l1_packet_id=row.l1_packet_id,
        source_family=row.source_family,
        provider=row.provider,
        event_time=row.event_time,
        available_to_brain_ts=row.available_to_brain_ts,
        target_node_type=row.target_node_type,
        target_node_key=row.target_node_key,
        economic_dimension=dimension,
        event_class=event_class,
        direction_review=direction,
        confidence_band=confidence,
        static_confidence_weight=CONFIDENCE_STATIC_WEIGHT[confidence],
        calibration_status=CalibrationStatus.NOT_CALIBRATED,
        calibrated_probability=None,
        critical_blockers=row.blocker_reasons,
        noncritical_gaps=row.noncritical_gaps,
        reason_codes=reason_codes,
        authority_flags=closed_authority_flags(),
    )


def build_blocker_gap_rows(coverage_gaps: list[dict[str, object]], rejected: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gap in coverage_gaps:
        rows.append({**gap, "row_type": "coverage_gap"})
    for row in rejected:
        rows.append(
            {
                "gap_id": f"review_queue:{row.get('l2_row_id')}",
                "lane": row.get("source_kind", ""),
                "source_family": row.get("source_family", ""),
                "progress_pct": "",
                "status": "REVIEW_QUEUE",
                "running": "",
                "severity": "REVIEW_REQUIRED",
                "gap_type": row.get("rejection_reasons", ""),
                "negative_evidence_allowed": 0,
                "diagnostic_only": 1,
                "reason_codes": row.get("rejection_reasons", ""),
                "row_type": "rejected_or_review_queue",
            }
        )
    return rows


def build_review_summary_rows(relation_graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "graph_key": row["graph_key"],
            "graph_state": row["graph_state"],
            "evidence_edge_count": row["evidence_edge_count"],
            "support_edge_count": row["support_edge_count"],
            "risk_edge_count": row["risk_edge_count"],
            "context_edge_count": row["context_edge_count"],
            "critical_blocker_count": row["critical_blocker_count"],
            "noncritical_gap_count": row["noncritical_gap_count"],
            "diagnostic_only": 1,
            "trading_eligible": 0,
            "signal_export_allowed": 0,
            "order_intent_allowed": 0,
            "broker_mutation_allowed": 0,
        }
        for row in relation_graph["graphs"]
    ]


def write_report(manifest: dict[str, Any], relation_graph: dict[str, Any], blocker_gap_rows: list[dict[str, Any]]) -> None:
    counts = manifest["output_counts"]
    lines = [
        "# TASK-4150 L3 Diagnostic Strategy View Bootstrap Implementation",
        "",
        "## Conclusion",
        "",
        "TASK-4150 implements the first safe L3 diagnostic bridge from current L2 artifacts into review-only economic meanings, evidence edges, relation graphs, and blocker/gap ledgers.",
        "",
        "It does not restore the old L3 package wholesale and does not import the deleted `src.l2.contracts.L2PrimitiveFact` surface.",
        "",
        "## Counts",
        "",
        "| item | count |",
        "|---|---:|",
        f"| l3_input_primitives | {counts['l3_input_primitives']} |",
        f"| l3_meanings | {counts['l3_meanings']} |",
        f"| l3_evidence_edges | {counts['l3_evidence_edges']} |",
        f"| l3_relation_graphs | {counts['l3_relation_graphs']} |",
        f"| l3_rejected_or_review_queue | {counts['l3_rejected_or_review_queue']} |",
        f"| coverage_gaps | {counts['coverage_gaps']} |",
        f"| blocker_gap_rows | {len(blocker_gap_rows)} |",
        "",
        "## L3 Goal",
        "",
        "L3 converts L2 diagnostic/read candidates into economic meaning and relation review state. It is diagnostic only.",
        "",
        "## Inputs",
        "",
    ]
    for item in manifest["inputs"]:
        lines.append(f"- `{item['role']}`: `{item['path']}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Strategy: `NOT_ACCEPTED`",
            "- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
            "- Real Capital: `FORBIDDEN`",
            "- No broker mutation.",
            "- No live order.",
            "- No paper promotion.",
            "- Missing/stale data remains `UNKNOWN/BLOCKER`, not negative evidence.",
            "- No signal, rank, sizing, order, paper/live, broker, strategy acceptance, or deployment authority opened.",
            "",
            "## Relation Graph Authority",
            "",
            f"- graph_count: `{relation_graph['graph_count']}`",
            f"- coverage_gap_count: `{relation_graph['coverage_gap_count']}`",
        ]
    )
    (REPORT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_artifact_manifest(out_dir: Path) -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4150 task registration and closeout", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4150 document registration", "modified"),
        ("configs/l3_diagnostic_strategy_view_bootstrap_4150.json", "config", "L3 bootstrap config", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/__init__.py", "package", "L3 bootstrap package marker", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/contracts.py", "code", "L3 bootstrap contracts", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/l2_read_view_bridge.py", "code", "L2 artifact bridge", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/coverage_policy.py", "code", "L0 coverage gap policy", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/economic_meaning_classifier.py", "code", "Rule-based economic meaning classifier", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/evidence_edge_builder.py", "code", "Evidence edge builder", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/relation_graph_aggregator.py", "code", "Relation graph aggregator", "created"),
        ("src/brain/l3_diagnostic_strategy_view_bootstrap/artifact_writer.py", "code", "Artifact writer helpers", "created"),
        ("scripts/build_l3_diagnostic_strategy_view_4150.py", "script", "Build L3 diagnostic strategy view artifacts", "created"),
        ("scripts/validate_l3_diagnostic_strategy_view_4150.py", "validator", "Validate L3 diagnostic strategy view artifacts", "created"),
        ("tests/test_l3_diagnostic_strategy_view_bootstrap_4150.py", "test", "Unit tests for L3 bootstrap behavior", "created"),
        (str(out_dir / "l3_input_manifest.json").replace("\\", "/"), "artifact", "Input manifest and row reconciliation", "created"),
        (str(out_dir / "l3_meanings.jsonl").replace("\\", "/"), "artifact", "L3 economic meanings", "created"),
        (str(out_dir / "l3_evidence_edges.jsonl").replace("\\", "/"), "artifact", "L3 evidence edges", "created"),
        (str(out_dir / "l3_relation_graph.json").replace("\\", "/"), "artifact", "L3 relation graph", "created"),
        (str(out_dir / "l3_blocker_gap_ledger.csv").replace("\\", "/"), "artifact", "L3 blocker and gap ledger", "created"),
        (str(out_dir / "l3_review_summary.csv").replace("\\", "/"), "artifact", "L3 review summary", "created"),
        (str(out_dir / "l3_rejected_or_review_queue.csv").replace("\\", "/"), "artifact", "L3 rejected or review queue", "created"),
        (str(out_dir / "l3_validator_report.json").replace("\\", "/"), "artifact", "L3 validator report", "created"),
        ("docs/reports/task_4150_l3_diagnostic_strategy_view_bootstrap/report.md", "report", "TASK-4150 report", "created"),
        ("docs/reports/task_4150_l3_diagnostic_strategy_view_bootstrap/artifact_manifest.csv", "manifest", "TASK-4150 artifact manifest", "created"),
        ("docs/reports/task_4150_l3_diagnostic_strategy_view_bootstrap/validation_results.md", "validation", "TASK-4150 validation results", "created"),
    ]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with (REPORT_DIR / "artifact_manifest.csv").open("w", encoding="utf-8", newline="") as fh:
        fh.write("path,type,purpose,created_or_modified,task_id\n")
        for row in rows:
            fh.write(",".join([row[0], row[1], row[2], row[3], TASK_ID]) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
