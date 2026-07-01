from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4176"
GRAPHS = Path("data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graphs.csv")
BLOCKER_TAXONOMY = Path("data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l4_blocker_taxonomy.csv")
OUT_DIR = Path("data/artifacts/task_4176_l4_diagnostic_blocker_taxonomy_scanner_v1")


SUPPORTED_FOR_DETERMINISTIC_SCAN = {"ENTITY_EVENT", "ENTITY_DIMENSION", "MACRO_FACTOR"}


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def stable_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:20]


def as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def scanner_status(graph: dict[str, str]) -> tuple[str, str]:
    family = graph.get("graph_family", "")
    if family not in SUPPORTED_FOR_DETERMINISTIC_SCAN:
        return "NOT_SCANNED_UNSUPPORTED_FAMILY", "scanner v1 only covers deterministic relation families"
    risk = as_int(graph.get("risk_edge_count"))
    support = as_int(graph.get("support_edge_count"))
    if risk > 0 and support > 0:
        return "SCANNED_MIXED_SUPPORT_AND_RISK", "deterministic internal graph directions contain both support and risk"
    return "SCANNED_NO_INTERNAL_OPPOSING_DIRECTION", "deterministic internal graph directions did not contain both support and risk"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    graphs = read_csv(GRAPHS)
    blocker_rows = read_csv(BLOCKER_TAXONOMY)
    family_counts = Counter(row.get("graph_family", "") for row in graphs)
    taxonomy_rows = []
    for family, count in sorted(family_counts.items()):
        supported = family in SUPPORTED_FOR_DETERMINISTIC_SCAN
        taxonomy_rows.append(
            {
                "task_id": TASK_ID,
                "relation_family": family,
                "graph_count": count,
                "diagnostic_taxonomy_status": "SUPPORTED_V1" if supported else "BLOCKER_UNSUPPORTED_V1",
                "scanner_status": "DETERMINISTIC_SCANNER_V1" if supported else "NOT_SCANNED_BLOCKER",
                "negative_evidence_allowed": 0,
                "diagnostic_only": 1,
            }
        )
    scanner_rows = []
    for graph in graphs:
        status, reason = scanner_status(graph)
        scanner_rows.append(
            {
                "task_id": TASK_ID,
                "scan_id": "l4scan_" + stable_id(graph.get("graph_key", "")),
                "graph_key": graph.get("graph_key", ""),
                "graph_family": graph.get("graph_family", ""),
                "target_key": graph.get("target_key", ""),
                "time_bucket": graph.get("time_bucket", ""),
                "risk_edge_count": graph.get("risk_edge_count", 0),
                "support_edge_count": graph.get("support_edge_count", 0),
                "contradiction_scan_status": status,
                "contradiction_reason": reason,
                "no_contradiction_claimed": 0,
                "negative_evidence_allowed": 0,
                "diagnostic_only": 1,
            }
        )
    write_csv(
        OUT_DIR / "task_4176_l4_relation_taxonomy_v1.csv",
        taxonomy_rows,
        ["task_id", "relation_family", "graph_count", "diagnostic_taxonomy_status", "scanner_status", "negative_evidence_allowed", "diagnostic_only"],
    )
    write_csv(
        OUT_DIR / "task_4176_l4_contradiction_scanner_v1.csv",
        scanner_rows,
        [
            "task_id",
            "scan_id",
            "graph_key",
            "graph_family",
            "target_key",
            "time_bucket",
            "risk_edge_count",
            "support_edge_count",
            "contradiction_scan_status",
            "contradiction_reason",
            "no_contradiction_claimed",
            "negative_evidence_allowed",
            "diagnostic_only",
        ],
    )
    scanned = sum(1 for row in scanner_rows if str(row["contradiction_scan_status"]).startswith("SCANNED_"))
    summary = {
        "task_id": TASK_ID,
        "generated_at": now_z(),
        "input_graph_count": len(graphs),
        "taxonomy_family_count": len(taxonomy_rows),
        "scanner_rows": len(scanner_rows),
        "scanned_supported_family_rows": scanned,
        "not_scanned_rows": len(scanner_rows) - scanned,
        "blocker_taxonomy_input_counts": {row.get("blocker_type", ""): as_int(row.get("count")) for row in blocker_rows},
        "unsupported_relation_count_reference": sum(as_int(row.get("count")) for row in blocker_rows if row.get("blocker_type") == "UNSUPPORTED_RELATION_FAMILY"),
        "contradiction_not_scanned_reference": sum(as_int(row.get("count")) for row in blocker_rows if row.get("blocker_type") == "CONTRADICTION_NOT_SCANNED"),
        "negative_evidence_allowed": 0,
        "diagnostic_only": 1,
    }
    write_json(OUT_DIR / "task_4176_l4_scanner_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
