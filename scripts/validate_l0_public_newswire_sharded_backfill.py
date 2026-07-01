from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed json: {path}: {exc}") from exc
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed jsonl: {path}:{idx}: {exc}") from exc
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and str(pid) in result.stdout and "No tasks are running" not in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def validate(args: argparse.Namespace) -> tuple[list[str], list[str], list[str]]:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    inventory = load_json(args.inventory_path)
    aggregate = load_json(args.aggregate_progress)
    if not inventory:
        failures.append("missing shard inventory")
        return passes, warnings, failures
    shards = inventory.get("shards", [])
    if not isinstance(shards, list) or not shards:
        failures.append("inventory has no shards")
        return passes, warnings, failures

    ids = set()
    paths_seen: dict[str, str] = {}
    running_locks: dict[str, list[Path]] = {}
    for shard in shards:
        shard_id = str(shard.get("shard_id", ""))
        source = str(shard.get("source", ""))
        key = str(shard.get("shard_key", ""))
        if source not in {"businesswire", "globenewswire", "prnewswire"}:
            failures.append(f"unknown source: {source}")
        if shard_id in ids:
            failures.append(f"duplicate shard_id: {shard_id}")
        ids.add(shard_id)
        for field in ["state_path", "event_path", "progress_path", "raw_dir"]:
            value = str(shard.get(field, ""))
            if value in paths_seen:
                failures.append(f"path collision: {field} {value} shared by {shard_id} and {paths_seen[value]}")
            paths_seen[value] = shard_id
        archive_urls = [str(url) for url in shard.get("archive_urls", [])]
        if source == "prnewswire" and key != "recent" and any("sitemap-news.xml?page=" in url for url in archive_urls):
            failures.append(f"prnewswire recent page included in historical shard: {shard_id}")
        if int(shard.get("legacy_completed_units", 0) or 0) > int(shard.get("total_units", 0) or 0):
            failures.append(f"legacy completed exceeds total units: {shard_id}")
        progress_path = Path(str(shard.get("progress_path", "")))
        if progress_path.exists():
            progress = load_json(progress_path)
            source_state = progress.get("backfill", {}).get(source, {}) if isinstance(progress.get("backfill"), dict) else {}
            if source_state and len(source_state.get("completed_archive_urls", []) or []) > int(shard.get("total_units", 0) or 0):
                failures.append(f"completed units exceeds total units: {shard_id}")
            if source_state.get("archive_entry_offsets") and progress.get("status") == "COMPLETED":
                failures.append(f"active archive offset while completed: {shard_id}")
        worker_progress_path = Path(str(shard.get("artifact_dir", ""))) / "worker_progress.json"
        worker = load_json(worker_progress_path)
        lock_path = Path(str(shard.get("artifact_dir", ""))) / "worker.lock.json"
        lock = load_json(lock_path)
        if lock.get("status") == "RUNNING":
            running_locks.setdefault(shard_id, []).append(lock_path)
            pid = int(lock.get("pid", 0) or 0)
            worker_status = str(worker.get("status", ""))
            if pid and not pid_alive(pid) and "STALE" not in worker_status:
                failures.append(f"dead pid with RUNNING lock: {shard_id} pid={pid}")
        if worker.get("status") in {"COMPLETED", "SHARD_COMPLETE"} and worker.get("active_archive_offset"):
            failures.append(f"active archive offset while worker completed: {shard_id}")
        for event in read_jsonl(Path(str(shard.get("event_path", "")))):
            raw_path = Path(str(event.get("raw_path", "")))
            if raw_path and raw_path.exists() and not is_relative_to(raw_path, Path(str(shard.get("raw_dir", "")))):
                failures.append(f"raw_path outside shard raw root: {raw_path}")
            if raw_path and not str(event.get("raw_sha256", "")):
                failures.append(f"missing raw_sha256: {raw_path}")
            for flag in ["broker_mutation_permitted_flag", "real_capital_permitted_flag", "trade_authority_flag"]:
                if int(event.get(flag, 0) or 0) != 0:
                    failures.append(f"safety flag nonzero: {flag} in {shard_id}")
    for shard_id, paths in running_locks.items():
        if len(paths) > 1:
            failures.append(f"same shard duplicate RUNNING lock: {shard_id}")

    if aggregate:
        for key in [
            "schema_version",
            "status",
            "progress_pct",
            "completed_units",
            "total_units",
            "pending_units",
            "failed_units",
            "partial_units",
            "row_count",
            "by_source",
            "by_shard",
            "active_workers",
            "stale_workers",
            "failed_shards",
            "partial_shards",
            "active_archive_offsets",
            "safety",
        ]:
            if key not in aggregate:
                failures.append(f"aggregate missing field: {key}")
        if int(aggregate.get("completed_units", 0) or 0) > int(aggregate.get("total_units", 0) or 0):
            failures.append("aggregate completed_units exceeds total_units")
        by_shard = aggregate.get("by_shard", {}) if isinstance(aggregate.get("by_shard"), dict) else {}
        active_offsets = aggregate.get("active_archive_offsets", {}) if isinstance(aggregate.get("active_archive_offsets"), dict) else {}
        for shard_id, offsets in active_offsets.items():
            status = str(by_shard.get(shard_id, {}).get("status", ""))
            if status in {"COMPLETED", "SHARD_COMPLETE"} and offsets:
                failures.append(f"aggregate active_archive_offsets present with completed shard: {shard_id}")
        safety = aggregate.get("safety", {})
        for key in ["broker_mutation_count", "order_count", "live_order_count", "paper_promotion_count", "real_capital_flag_count", "trade_authority_count"]:
            if int(safety.get(key, 0) or 0) != 0:
                failures.append(f"aggregate safety nonzero: {key}")
        if int(aggregate.get("l1_unclassified_or_pending_count", 0) or 0) > 0:
            warnings.append("l1_unclassified_or_pending_count > 0")
        if aggregate.get("failed_shards"):
            warnings.append(f"failed shards represented: {len(aggregate.get('failed_shards', []))}")
    else:
        warnings.append("aggregate progress missing; inventory-only validation")

    passes.append(f"shards_checked: {len(shards)}")
    passes.append(f"unique_paths_seen: {len(paths_seen)}")
    if not any("safety" in failure for failure in failures):
        passes.append("safety_flags_closed")
    return passes, warnings, failures


def print_result(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    print("# L0 PUBLIC NEWSWIRE SHARDED BACKFILL VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print("RESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate L0 public newswire sharded backfill artifacts.")
    parser.add_argument("--shard-artifact-root", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill_shards"))
    parser.add_argument("--shard-raw-root", type=Path, default=Path("data/raw/l0_public_newswire_backfill_shards"))
    parser.add_argument("--inventory-path", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json"))
    parser.add_argument("--aggregate-progress", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json"))
    parser.add_argument("--compat-progress", type=Path, default=Path("data/artifacts/l0_public_newswire_backfill/collector_progress.json"))
    return parser.parse_args()


def main() -> int:
    return print_result(*validate(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
