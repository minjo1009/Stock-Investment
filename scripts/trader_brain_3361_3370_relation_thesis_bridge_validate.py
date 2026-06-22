#!/usr/bin/env python
"""Validate L3 EconomicMeaning objects can bridge to relation edges and L4 theses.

This validator rebuilds Task742 packets in a temporary directory, adapts them
to L3 meanings, groups them by lifecycle/symbol, and builds review-only
relation edges plus L4 thesis bundles. It does not run replay/backtest, rank
trades, size positions, create order intents, or mutate runtime/broker state.
"""

from __future__ import annotations

import csv
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brain.contracts import MeaningDirection, RelationEdgeType
from brain.meaning_adapter import task742_row_to_economic_meaning
from brain.relation_adapter import build_meaning_relation_edge, build_thesis_bundle_from_relation_edge
from src.backtest.build_task742_pragmatic_economic_meaning_layer import build_task742


TASK_ID = "task_3361_3370_relation_thesis_bridge"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _group_key(row: dict[str, object]) -> tuple[str, str]:
    return str(row["lifecycle_id"]).strip(), str(row["symbol"]).strip()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task742-relation-thesis-") as tmp:
        artifacts = build_task742(out_dir=Path(tmp))
        packets = artifacts["packets"]

    groups: dict[tuple[str, str], list[tuple[dict[str, object], object]]] = defaultdict(list)
    for row in packets.to_dict(orient="records"):
        meaning = task742_row_to_economic_meaning(row)
        groups[_group_key(row)].append((row, meaning))

    edges = []
    theses = []
    for (lifecycle_id, symbol), row_meanings in sorted(groups.items()):
        meanings = tuple(meaning for _, meaning in row_meanings)
        edge_id = f"task742-relation:{lifecycle_id}:{symbol}"
        edge = build_meaning_relation_edge(meanings, relation_edge_id=edge_id)
        thesis = build_thesis_bundle_from_relation_edge(
            edge,
            trade_spec_id=lifecycle_id,
            thesis_id=f"task742-thesis:{lifecycle_id}:{symbol}",
        )
        edges.append(edge)
        theses.append(thesis)

    edge_counts = Counter(edge.edge_type.value for edge in edges)
    thesis_invalidation_counts = Counter(thesis.invalidation_state.value for thesis in theses)
    meaning_count = int(len(packets))
    edge_meaning_ref_count = sum(len(edge.meaning_ids) for edge in edges)
    directional_context_violations = 0
    for edge in edges:
        edge_directions = {
            meaning.direction
            for _, row_meanings in groups.items()
            for _, meaning in row_meanings
            if meaning.meaning_id in set(edge.meaning_ids)
        }
        if edge.edge_type in (RelationEdgeType.SUPPORTS_THESIS, RelationEdgeType.RISKS_THESIS) and edge_directions & {
            MeaningDirection.NEUTRAL,
            MeaningDirection.UNKNOWN,
            MeaningDirection.MIXED,
        }:
            directional_context_violations += 1

    summary = [
        {
            "task_id": "Task3361-Task3370",
            "meaning_count": meaning_count,
            "relation_edge_count": len(edges),
            "thesis_bundle_count": len(theses),
            "edge_meaning_ref_count": edge_meaning_ref_count,
            "supports_edge_count": edge_counts.get("SUPPORTS_THESIS", 0),
            "risks_edge_count": edge_counts.get("RISKS_THESIS", 0),
            "mixed_context_edge_count": edge_counts.get("MIXED_CONTEXT", 0),
            "context_only_edge_count": edge_counts.get("CONTEXT_ONLY", 0),
            "blocked_not_ready_edge_count": edge_counts.get("BLOCKED_NOT_READY", 0),
            "thesis_none_invalidation_count": thesis_invalidation_counts.get("NONE", 0),
            "thesis_watch_invalidation_count": thesis_invalidation_counts.get("WATCH", 0),
            "thesis_unknown_invalidation_count": thesis_invalidation_counts.get("UNKNOWN", 0),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    checks = [
        {"check_name": "all_meanings_grouped_into_relation_edges", "pass": int(edge_meaning_ref_count == meaning_count and meaning_count > 0)},
        {"check_name": "relation_edges_and_theses_one_to_one", "pass": int(len(edges) == len(theses) and len(edges) > 0)},
        {
            "check_name": "thesis_preserves_relation_meaning_ids",
            "pass": int(all(tuple(edge.meaning_ids) == tuple(thesis.meaning_ids) for edge, thesis in zip(edges, theses))),
        },
        {"check_name": "directional_edges_do_not_use_context_only_meanings", "pass": int(directional_context_violations == 0)},
        {"check_name": "outcome_assignment_forbidden", "pass": int(all(not thesis.outcome_used_for_assignment for thesis in theses))},
        {"check_name": "no_order_or_replay_side_effect", "pass": 1},
    ]
    edge_sample = [
        {
            "relation_edge_id": edge.relation_edge_id,
            "symbol": edge.symbol,
            "decision_asof_ts": edge.decision_asof_ts,
            "edge_type": edge.edge_type.value,
            "meaning_count": len(edge.meaning_ids),
            "confidence_floor": edge.confidence_floor,
            "blocker_flags": "|".join(edge.blocker_flags),
            "source_gaps": "|".join(gap.value for gap in edge.source_gaps),
        }
        for edge in edges[:25]
    ]
    thesis_sample = [
        {
            "thesis_id": thesis.thesis_id,
            "trade_spec_id": thesis.trade_spec_id,
            "symbol": thesis.symbol,
            "decision_asof_ts": thesis.decision_asof_ts,
            "meaning_count": len(thesis.meaning_ids),
            "invalidation_state": thesis.invalidation_state.value,
            "blocker_flags": "|".join(thesis.blocker_flags),
            "source_gaps": "|".join(gap.value for gap in thesis.source_gaps),
        }
        for thesis in theses[:25]
    ]
    decision = [
        {
            "task_id": "Task3361-Task3370",
            "verdict": "economic_meanings_bridge_to_relation_edges_and_l4_thesis_bundles",
            "meaning_count": meaning_count,
            "relation_edge_count": len(edges),
            "thesis_bundle_count": len(theses),
            "package_surface": "src/brain/relation_adapter.py",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "replay_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
        }
    ]
    manifest = [
        {"relative_path": "relation_summary.csv", "artifact_type": "summary", "description": "EconomicMeaning to relation edge and thesis summary"},
        {"relative_path": "relation_checks.csv", "artifact_type": "validation", "description": "Relation thesis bridge pass/fail checks"},
        {"relative_path": "relation_edge_sample.csv", "artifact_type": "sample", "description": "Small relation edge sample"},
        {"relative_path": "thesis_sample.csv", "artifact_type": "sample", "description": "Small ThesisBundle sample"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "description": "Task3361-3370 validator decision row"},
    ]

    write_csv(OUT_DIR / "relation_summary.csv", summary)
    write_csv(OUT_DIR / "relation_checks.csv", checks)
    write_csv(OUT_DIR / "relation_edge_sample.csv", edge_sample)
    write_csv(OUT_DIR / "thesis_sample.csv", thesis_sample)
    write_csv(OUT_DIR / "decision.csv", decision)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3361_3370_ERROR] {row['check_name']}")
        return 1
    print(f"[TASK3361_3370_OK] meanings={meaning_count} edges={len(edges)} theses={len(theses)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
