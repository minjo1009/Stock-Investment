from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.db.source_acquisition.public_newswire_shards import atomic_write_json, load_json, now_z


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def iter_event_paths(shard_root: Path, legacy_root: Path | None) -> list[Path]:
    paths = sorted(shard_root.glob("*/*/collector_events.jsonl"))
    if legacy_root:
        legacy_path = legacy_root / "collector_events.jsonl"
        if legacy_path.exists():
            paths.append(legacy_path)
    return paths


def load_raw_headlines(raw_path: str) -> list[dict[str, Any]]:
    if not raw_path:
        return []
    path = Path(raw_path)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return []
    rows = payload.get("headlines", [])
    return rows if isinstance(rows, list) else []


def parse_source(event: dict[str, Any]) -> str:
    source_id = str(event.get("source_id", ""))
    if "::" in source_id:
        return source_id.split("::", 1)[0]
    notes = str(event.get("notes", ""))
    for part in notes.split(";"):
        if part.startswith("source_key="):
            return part.split("=", 1)[1]
    return "unknown"


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def velocity_row(current: dict[str, Any], previous: dict[str, Any], source: str, generated_at: str) -> dict[str, Any]:
    previous_time = parse_time(str(previous.get("generated_at", "")))
    current_time = parse_time(generated_at)
    if not previous_time or not current_time:
        return {"unit_velocity_per_hour": None, "row_velocity_per_hour": None, "eta_hours_by_unit_velocity": None}
    hours = (current_time - previous_time).total_seconds() / 3600.0
    if hours <= 0:
        return {"unit_velocity_per_hour": None, "row_velocity_per_hour": None, "eta_hours_by_unit_velocity": None}
    previous_source = previous.get("by_source", {}).get(source, {}) if isinstance(previous.get("by_source"), dict) else {}
    unit_velocity = (int(current.get("completed_units", 0) or 0) - int(previous_source.get("completed_units", 0) or 0)) / hours
    row_velocity = (int(current.get("row_count", 0) or 0) - int(previous_source.get("row_count", 0) or 0)) / hours
    pending = int(current.get("pending_units", 0) or 0)
    eta = (pending / unit_velocity) if unit_velocity > 0 else None
    return {
        "unit_velocity_per_hour": round(unit_velocity, 4),
        "row_velocity_per_hour": round(row_velocity, 4),
        "eta_hours_by_unit_velocity": round(eta, 4) if eta is not None else None,
    }


def aggregate(args: argparse.Namespace) -> dict[str, Any]:
    inventory = load_json(args.inventory_path)
    previous = load_json(args.out)
    by_source: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "completed_units": 0,
            "total_units": 0,
            "pending_units": 0,
            "failed_units": 0,
            "partial_units": 0,
            "row_count": 0,
            "l1_context_ready_count": 0,
            "l1_blocked_count": 0,
        }
    )
    by_shard: dict[str, dict[str, Any]] = {}
    failed_shards: list[str] = []
    partial_shards: list[str] = []
    active_workers: list[dict[str, Any]] = []
    stale_workers: list[dict[str, Any]] = []
    active_offsets: dict[str, Any] = {}

    if inventory:
        for shard in inventory.get("shards", []):
            source = shard.get("source", "unknown")
            shard_id = shard.get("shard_id", f"{source}:{shard.get('shard_key', '')}")
            total = int(shard.get("total_units", 0) or 0)
            legacy_completed = int(shard.get("legacy_completed_units", 0) or 0)
            pending = int(shard.get("pending_units", 0) or 0)
            worker = load_json(Path(shard.get("artifact_dir", "")) / "worker_progress.json")
            lock = load_json(Path(shard.get("artifact_dir", "")) / "worker.lock.json")
            status = str(worker.get("status") or shard.get("status") or "")
            completed = legacy_completed if pending == 0 else legacy_completed
            progress = load_json(Path(shard.get("progress_path", "")))
            source_state = progress.get("backfill", {}).get(source, {}) if isinstance(progress.get("backfill"), dict) else {}
            offsets = {}
            if source_state:
                completed = max(completed, len(source_state.get("completed_archive_urls", []) or []))
                offsets = source_state.get("archive_entry_offsets", {}) or {}
                if offsets:
                    active_offsets[shard_id] = offsets
                    partial_shards.append(shard_id)
            if status.startswith("FAILED") and total and completed >= total and not offsets:
                status = "COMPLETED_WITH_NONZERO_EXIT"
            if status.startswith("FAILED"):
                failed_shards.append(shard_id)
            by_shard[shard_id] = {
                "source": source,
                "status": status,
                "completed_units": completed,
                "total_units": total,
                "pending_units": max(total - completed, 0),
                "artifact_dir": shard.get("artifact_dir", ""),
                "raw_dir": shard.get("raw_dir", ""),
            }
            if lock.get("status") == "RUNNING":
                active_workers.append(
                    {
                        "shard_id": shard_id,
                        "source": source,
                        "shard_key": shard.get("shard_key", ""),
                        "pid": int(lock.get("pid") or worker.get("pid") or worker.get("worker_pid") or 0),
                        "started_at": lock.get("started_at") or "",
                        "last_progress_at": worker.get("last_progress_at") or worker.get("updated_at") or "",
                        "current_archive_url": worker.get("current_archive_url") or "",
                        "active_archive_offset": worker.get("active_archive_offset"),
                        "row_count": worker.get("row_count"),
                    }
                )
            if "STALE" in status or "RECYCLED" in status:
                stale_workers.append({"shard_id": shard_id, "source": source, "status": status, "pid": int(worker.get("pid") or worker.get("worker_pid") or 0)})
            by_source[source]["completed_units"] += completed
            by_source[source]["total_units"] += total
            by_source[source]["pending_units"] += max(total - completed, 0)
            if status.startswith("FAILED"):
                by_source[source]["failed_units"] += 1
            if shard_id in partial_shards:
                by_source[source]["partial_units"] += 1

    events: list[dict[str, Any]] = []
    for path in iter_event_paths(args.shard_artifact_root, args.legacy_artifact_root):
        events.extend(read_jsonl(path))

    safety = Counter()
    status_counts = Counter()
    source_url_counter = Counter()
    headline_hash_counter = Counter()
    row_count = 0
    mapped_rows = 0
    l1_context_ready = 0
    l1_blocked = 0
    raw_events_scanned = 0
    raw_events_skipped = 0
    for event in events:
        source = parse_source(event)
        status_counts[str(event.get("status", ""))] += 1
        count = int(event.get("row_count", 0) or 0)
        row_count += count
        by_source[source]["row_count"] += count
        l1_context_ready += int(event.get("l1_context_ready_count", 0) or 0)
        l1_blocked += int(event.get("l1_blocked_count", 0) or 0)
        by_source[source]["l1_context_ready_count"] += int(event.get("l1_context_ready_count", 0) or 0)
        by_source[source]["l1_blocked_count"] += int(event.get("l1_blocked_count", 0) or 0)
        safety["broker_mutation_count"] += int(event.get("broker_mutation_permitted_flag", 0) or 0)
        safety["real_capital_flag_count"] += int(event.get("real_capital_permitted_flag", 0) or 0)
        safety["trade_authority_count"] += int(event.get("trade_authority_flag", 0) or 0)
        if args.skip_raw_dedupe or (args.max_raw_events and raw_events_scanned >= args.max_raw_events):
            raw_events_skipped += 1
        else:
            raw_events_scanned += 1
            for row in load_raw_headlines(str(event.get("raw_path", ""))):
                if row.get("source_url"):
                    source_url_counter[str(row.get("source_url"))] += 1
                if row.get("headline_hash"):
                    headline_hash_counter[str(row.get("headline_hash"))] += 1
                if row.get("symbols"):
                    mapped_rows += 1
    total_units = sum(int(row.get("total_units", 0) or 0) for row in by_source.values()) or int(inventory.get("total_units", 0) or 0)
    completed_units = sum(int(row.get("completed_units", 0) or 0) for row in by_source.values()) or int(inventory.get("legacy_completed_units", 0) or 0)
    pending_units = max(total_units - completed_units, 0)
    l1_unclassified = max(row_count - l1_context_ready - l1_blocked, 0)
    # Failed shard evidence should stay visible, but it should not make a live backfill look stopped.
    # The launcher can continue through represented failures/recycles while other shards are active.
    status = "COMPLETED" if total_units and pending_units == 0 else ("RUNNING" if active_workers or pending_units else "FAILED")
    generated_at = now_z()
    for source, row in by_source.items():
        row.update(velocity_row(row, previous, source, generated_at))
    eta_values = [
        float(row["eta_hours_by_unit_velocity"])
        for row in by_source.values()
        if row.get("eta_hours_by_unit_velocity") is not None
    ]
    payload = {
        "schema_version": "l0_public_newswire_sharded_backfill_v1",
        "generated_at": generated_at,
        "provider": "public_newswire_feeds",
        "status": status,
        "mode": "historical_backfill_sharded",
        "progress_pct": round((completed_units / total_units * 100.0), 4) if total_units else 0.0,
        "completed_units": completed_units,
        "total_units": total_units,
        "pending_units": pending_units,
        "failed_units": len(failed_shards),
        "partial_units": len(set(partial_shards)),
        "long_tail_eta_hours_by_source_unit_velocity": round(max(eta_values), 4) if eta_values else None,
        "row_count": row_count,
        "mapped_rows": mapped_rows,
        "l1_context_ready_count": l1_context_ready,
        "l1_blocked_count": l1_blocked,
        "l1_unclassified_or_pending_count": l1_unclassified,
        "event_status_counts": dict(status_counts),
        "dedupe": {
            "unique_source_url_count": len(source_url_counter),
            "duplicate_source_url_count": sum(count - 1 for count in source_url_counter.values() if count > 1),
            "duplicate_headline_hash_count": sum(count - 1 for count in headline_hash_counter.values() if count > 1),
            "possible_hash_collision_count": 0,
            "raw_events_scanned": raw_events_scanned,
            "raw_events_skipped": raw_events_skipped,
            "raw_dedupe_skipped_flag": int(bool(args.skip_raw_dedupe)),
        },
        "by_source": dict(by_source),
        "by_shard": by_shard,
        "active_workers": active_workers,
        "stale_workers": stale_workers,
        "failed_shards": failed_shards,
        "partial_shards": sorted(set(partial_shards)),
        "active_archive_offsets": active_offsets,
        "safety": {
            "broker_mutation_count": int(safety["broker_mutation_count"]),
            "order_count": 0,
            "live_order_count": 0,
            "paper_promotion_count": 0,
            "real_capital_flag_count": int(safety["real_capital_flag_count"]),
            "trade_authority_count": int(safety["trade_authority_count"]),
        },
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate L0 public newswire sharded backfill progress.")
    parser.add_argument("--shard-artifact-root", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill_shards"))
    parser.add_argument("--shard-raw-root", type=Path, default=Path("data/raw/l0_public_newswire_backfill_shards"))
    parser.add_argument("--legacy-artifact-root", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill"))
    parser.add_argument("--inventory-path", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json"))
    parser.add_argument("--out", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json"))
    parser.add_argument("--compat-out", type=Path, default=None)
    parser.add_argument("--skip-raw-dedupe", action="store_true")
    parser.add_argument("--max-raw-events", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = aggregate(args)
    atomic_write_json(args.out, payload)
    if args.compat_out:
        atomic_write_json(args.compat_out, payload)
    print(json.dumps({"status": payload["status"], "progress_pct": payload["progress_pct"], "out": str(args.out)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
