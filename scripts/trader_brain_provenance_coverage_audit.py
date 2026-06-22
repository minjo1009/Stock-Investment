from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def audit_graph(graph_dir: Path, provenance_manifest: Path) -> list[dict[str, str]]:
    provenance_rows = read_csv(provenance_manifest)
    evidence_ids = {row.get("evidence_id", "") for row in provenance_rows}
    rows: list[dict[str, str]] = []
    for filename, fields in {"nodes.csv": ["evidence_id", "edge_evidence_id"], "edges.csv": ["edge_evidence_id"]}.items():
        path = graph_dir / filename
        if not path.exists():
            rows.append(
                {
                    "graph_dir": graph_dir.as_posix(),
                    "file": filename,
                    "row_id": "",
                    "evidence_field": "",
                    "evidence_id": "",
                    "coverage_state": "missing_file",
                    "validation_authority": "GOVERNANCE_HEALTH",
                }
            )
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            row_id = row.get("info_node_id") or row.get("edge_id") or str(idx)
            for field in fields:
                evidence_id = row.get(field, "")
                coverage = "covered" if evidence_id in evidence_ids else "orphan"
                rows.append(
                    {
                        "graph_dir": graph_dir.as_posix(),
                        "file": filename,
                        "row_id": row_id,
                        "evidence_field": field,
                        "evidence_id": evidence_id,
                        "coverage_state": coverage,
                        "validation_authority": "GOVERNANCE_HEALTH",
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["graph_dir", "file", "row_id", "evidence_field", "evidence_id", "coverage_state", "validation_authority"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph-dir", action="append", required=True)
    parser.add_argument("--provenance-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows: list[dict[str, str]] = []
    for graph_dir in args.graph_dir:
        rows.extend(audit_graph(resolve_path(graph_dir), args.provenance_manifest))
    write_csv(args.output, rows)
    orphan_count = sum(1 for row in rows if row["coverage_state"] != "covered")
    if orphan_count:
        print(f"[TRADER_BRAIN_PROVENANCE_COVERAGE_ERROR] orphan_count={orphan_count} output={args.output}")
        sys.exit(1)
    print(f"[TRADER_BRAIN_PROVENANCE_COVERAGE_OK] rows={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
