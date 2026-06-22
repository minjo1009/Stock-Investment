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


def manifest_index(path: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    required = {"evidence_id", "artifact_path", "source_family", "source_state", "asof_ts"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"provenance manifest missing columns {','.join(sorted(missing))}")
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        evidence_id = row.get("evidence_id", "")
        if evidence_id in index:
            raise ValueError(f"duplicate evidence_id {evidence_id}")
        index[evidence_id] = row
    return index


def validate_graph_provenance(graph_dir: Path, provenance_manifest: Path) -> list[str]:
    errors: list[str] = []
    try:
        index = manifest_index(provenance_manifest)
    except ValueError as exc:
        return [str(exc)]

    for filename, id_fields in {
        "nodes.csv": ["evidence_id", "edge_evidence_id"],
        "edges.csv": ["edge_evidence_id"],
    }.items():
        path = graph_dir / filename
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            scope = f"{filename} row {idx}"
            source_artifact = row.get("source_artifact", "")
            if filename == "nodes.csv":
                if not source_artifact:
                    errors.append(f"{scope}: missing source_artifact")
                elif not resolve_path(source_artifact).exists():
                    errors.append(f"{scope}: source_artifact not found {source_artifact}")
            for field in id_fields:
                evidence_id = row.get(field, "")
                if not evidence_id:
                    errors.append(f"{scope}: missing {field}")
                    continue
                if evidence_id not in index:
                    errors.append(f"{scope}: manifest_orphan {field} {evidence_id}")
                    continue
                manifest_row = index[evidence_id]
                if manifest_row.get("source_state") == "source_gap" and row.get("review_state", "") not in {"source_gap", "defer", "context_only", ""}:
                    errors.append(f"{scope}: source_gap provenance used by non-gap state {evidence_id}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph-dir", required=True, type=Path)
    parser.add_argument("--provenance-manifest", required=True, type=Path)
    args = parser.parse_args()
    errors = validate_graph_provenance(args.graph_dir, args.provenance_manifest)
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_PROVENANCE_ERROR] {error}")
        sys.exit(1)
    print(f"[TRADER_BRAIN_PROVENANCE_OK] {args.graph_dir}")


if __name__ == "__main__":
    main()
