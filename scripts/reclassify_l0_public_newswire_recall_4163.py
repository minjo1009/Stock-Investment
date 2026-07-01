from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.db.source_acquisition.public_newswire_collector import (  # noqa: E402
    NEWSWIRE_RECALL_VERSION,
    apply_entity_mapping,
    build_entity_mapper,
)

TASK_ID = "TASK-4163"
DEFAULT_RAW_ROOTS = (
    Path("data/raw/l0_public_newswire_backfill_shards"),
    Path("data/raw/l0_public_newswire_backfill"),
    Path("data/raw/l0_public_newswire"),
)
DEFAULT_OUT_DIR = Path("data/artifacts/task_4163_gn_filtering_recall_audit")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def shard_key(path: Path) -> tuple[str, str]:
    parts = list(path.parts)
    for index, part in enumerate(parts):
        if part in {"businesswire", "globenewswire", "prnewswire"} and index + 1 < len(parts):
            return part, parts[index + 1]
    source = ""
    for part in parts:
        if part.startswith("source="):
            source = part.split("=", 1)[1]
            break
    return source or "unknown", str(path.parent)


def captured_at_key(path: Path) -> str:
    for part in path.parts:
        if part.startswith("captured_at="):
            return part.split("=", 1)[1]
    return ""


def source_from_event(event: dict[str, Any]) -> str:
    source_id = str(event.get("source_id", ""))
    if "::" in source_id:
        return source_id.split("::", 1)[0]
    notes = str(event.get("notes", ""))
    for part in notes.split(";"):
        if part.startswith("source_key="):
            return part.split("=", 1)[1]
    return ""


def discover_event_raw_files(event_roots: list[Path], source: str = "") -> list[Path]:
    files: dict[str, Path] = {}
    for root in event_roots:
        if not root.exists():
            continue
        for event_path in root.rglob("collector_events.jsonl"):
            with event_path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    event_source = source_from_event(event)
                    if source and event_source != source:
                        continue
                    raw_path = Path(str(event.get("raw_path", "")))
                    if raw_path.name != "headlines.json" or not raw_path.exists():
                        continue
                    files[str(raw_path)] = raw_path
    return [files[key] for key in sorted(files)]


def discover_latest_files(raw_roots: list[Path], source: str = "") -> list[Path]:
    grouped: dict[tuple[str, str], Path] = {}
    for root in raw_roots:
        if not root.exists():
            continue
        for path in root.rglob("headlines.json"):
            key = shard_key(path)
            if source and key[0] != source:
                continue
            current = grouped.get(key)
            if current is None or captured_at_key(path) > captured_at_key(current):
                grouped[key] = path
    return [grouped[key] for key in sorted(grouped)]


def row_status(row: dict[str, Any]) -> str:
    return str(row.get("entity_mapping_status") or "")


def reclassify_file(
    path: Path,
    mapper: Any,
    overlay_writer: csv.DictWriter[str],
    *,
    task_id: str,
    keep_derived_payload: bool,
) -> dict[str, Any]:
    payload = read_json(path)
    rows = payload.get("headlines", [])
    if not isinstance(rows, list):
        rows = []
    before = Counter(row_status(row) for row in rows)
    after = Counter()
    recall_rows = 0
    status_changed = 0
    derived_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        updated = apply_entity_mapping(row, mapper)
        if keep_derived_payload:
            derived_rows.append(updated)
        after[row_status(updated)] += 1
        changed = row_status(updated) != row_status(row)
        if changed:
            status_changed += 1
        if updated.get("newswire_recall_review_flag") in (1, "1", True):
            recall_rows += 1
            overlay_writer.writerow(
                {
                    "task_id": task_id,
                    "raw_path": str(path),
                    "row_index": index,
                    "source_key": updated.get("source_key", payload.get("source_key", "")),
                    "published_at": updated.get("published_at", ""),
                    "title": updated.get("title", ""),
                    "source_url": updated.get("source_url", ""),
                    "old_entity_mapping_status": row_status(row),
                    "new_entity_mapping_status": row_status(updated),
                    "status_changed": int(changed),
                    "symbols": "|".join(str(item) for item in updated.get("symbols", [])),
                    "newswire_recall_topics": "|".join(str(item) for item in updated.get("newswire_recall_topics", [])),
                    "newswire_recall_reason": "|".join(str(item) for item in updated.get("newswire_recall_reason", [])),
                    "newswire_recall_version": updated.get("newswire_recall_version", NEWSWIRE_RECALL_VERSION),
                    "authority_flag": updated.get("newswire_recall_candidate_authority_flag", 0),
                }
            )
    return {
        "raw_path": str(path),
        "source_key": payload.get("source_key", shard_key(path)[0]),
        "row_count": len(rows),
        "before_status_counts": dict(before),
        "after_status_counts": dict(after),
        "recall_review_rows": recall_rows,
        "status_changed_rows": status_changed,
        "derived_payload": (
            {**payload, "headlines": derived_rows, "newswire_recall_overlay_version": NEWSWIRE_RECALL_VERSION}
            if keep_derived_payload
            else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reclassify existing L0 public newswire raw into a non-authority recall overlay.")
    parser.add_argument("--raw-root", action="append", type=Path, default=[])
    parser.add_argument("--event-root", action="append", type=Path, default=[])
    parser.add_argument("--source", default="")
    parser.add_argument("--max-files", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--task-id", default=TASK_ID)
    parser.add_argument("--write-derived-copies", action="store_true")
    args = parser.parse_args()

    raw_roots = args.raw_root or list(DEFAULT_RAW_ROOTS)
    mapper = build_entity_mapper()
    files = discover_event_raw_files(args.event_root, source=args.source) if args.event_root else discover_latest_files(raw_roots, source=args.source)
    if args.max_files > 0:
        files = files[: args.max_files]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = args.out_dir / "l0_public_newswire_recall_overlay.csv"
    summary_rows: list[dict[str, Any]] = []
    total_before: Counter[str] = Counter()
    total_after: Counter[str] = Counter()
    by_source: dict[str, Counter[str]] = defaultdict(Counter)

    with overlay_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "task_id",
            "raw_path",
            "row_index",
            "source_key",
            "published_at",
            "title",
            "source_url",
            "old_entity_mapping_status",
            "new_entity_mapping_status",
            "status_changed",
            "symbols",
            "newswire_recall_topics",
            "newswire_recall_reason",
            "newswire_recall_version",
            "authority_flag",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for path in files:
            result = reclassify_file(path, mapper, writer, task_id=args.task_id, keep_derived_payload=args.write_derived_copies)
            derived_payload = result.pop("derived_payload")
            summary_rows.append(result)
            total_before.update(result["before_status_counts"])
            total_after.update(result["after_status_counts"])
            source_key = str(result.get("source_key") or "")
            by_source[source_key]["files"] += 1
            by_source[source_key]["rows"] += int(result["row_count"])
            by_source[source_key]["recall_review_rows"] += int(result["recall_review_rows"])
            by_source[source_key]["status_changed_rows"] += int(result["status_changed_rows"])
            if args.write_derived_copies:
                if derived_payload is None:
                    continue
                rel = path
                for root in raw_roots:
                    try:
                        rel = path.relative_to(root)
                        break
                    except ValueError:
                        continue
                write_json(args.out_dir / "derived_l0_reclassified" / rel, derived_payload)

    summary = {
        "task_id": args.task_id,
        "schema_version": "l0_public_newswire_recall_overlay_v1",
        "newswire_recall_version": NEWSWIRE_RECALL_VERSION,
        "raw_roots": [str(path) for path in raw_roots],
        "event_roots": [str(path) for path in args.event_root],
        "discovery_mode": "event_raw_paths" if args.event_root else "latest_raw_per_shard",
        "source_filter": args.source,
        "latest_shard_files_processed": len(files),
        "overlay_path": str(overlay_path),
        "derived_copies_written": bool(args.write_derived_copies),
        "before_status_counts": dict(total_before),
        "after_status_counts": dict(total_after),
        "by_source": {source: dict(counts) for source, counts in sorted(by_source.items())},
        "file_summaries": summary_rows,
        "safety": {
            "raw_mutation_count": 0,
            "broker_mutation_count": 0,
            "live_order_count": 0,
            "paper_promotion_count": 0,
            "real_capital_flag_count": 0,
        },
    }
    write_json(args.out_dir / "recall_reclassification_summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
