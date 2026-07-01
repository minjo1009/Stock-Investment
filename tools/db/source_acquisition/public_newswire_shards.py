from __future__ import annotations

import calendar
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from tools.db.source_acquisition.public_newswire_collector import newswire_backfill_archive_urls


PROVIDER = "public_newswire_feeds"
SHARD_SCHEMA_VERSION = "l0_public_newswire_sharded_backfill_v1"
DEFAULT_SHARD_ARTIFACT_ROOT = Path("data/artifacts/l0_public_newswire_backfill_shards")
DEFAULT_SHARD_RAW_ROOT = Path("data/raw/l0_public_newswire_backfill_shards")


@dataclass(frozen=True)
class NewswireShard:
    source: str
    shard_key: str
    start_date: str
    end_date: str
    archive_scope: str
    artifact_dir: str
    raw_dir: str
    state_path: str
    event_path: str
    progress_path: str
    plan_path: str
    stop_path: str
    log_path: str
    archive_urls: list[str]
    total_units: int
    legacy_completed_units: int
    pending_units: int
    legacy_completed_archive_urls: list[str]
    legacy_archive_entry_offsets: dict[str, int]
    status: str

    @property
    def shard_id(self) -> str:
        return f"{self.source}:{self.shard_key}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["shard_id"] = self.shard_id
        return payload


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def parse_month(value: str) -> date:
    year, month = value.split("-", 1)
    return date(int(year), int(month), 1)


def month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def month_end(value: date) -> date:
    return date(value.year, value.month, calendar.monthrange(value.year, value.month)[1])


def iter_days(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current = date.fromordinal(current.toordinal() + 1)
    return days


def iter_months(start_month: str, end_month: str) -> list[date]:
    current = parse_month(start_month)
    end = parse_month(end_month)
    values: list[date] = []
    while current <= end:
        values.append(current)
        next_year = current.year + (1 if current.month == 12 else 0)
        next_month = 1 if current.month == 12 else current.month + 1
        current = date(next_year, next_month, 1)
    return values


def default_end_month() -> str:
    return month_key(datetime.now(UTC).date())


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def legacy_source_state(legacy_state: dict[str, Any], source: str) -> dict[str, Any]:
    payload = legacy_state.get("backfill", {}).get(source, {})
    return payload if isinstance(payload, dict) else {}


def merge_source_state(target: dict[str, Any], source: str, state: dict[str, Any]) -> None:
    source_state = legacy_source_state(state, source)
    if not source_state:
        return
    backfill = target.setdefault("backfill", {}).setdefault(source, {})
    completed = set(backfill.get("completed_archive_urls", []) or [])
    completed.update(source_state.get("completed_archive_urls", []) or [])
    backfill["completed_archive_urls"] = sorted(completed)
    unavailable = set(backfill.get("unavailable_archive_urls", []) or [])
    unavailable.update(source_state.get("unavailable_archive_urls", []) or [])
    backfill["unavailable_archive_urls"] = sorted(unavailable)
    offsets = dict(backfill.get("archive_entry_offsets", {}) or {})
    for url, offset in (source_state.get("archive_entry_offsets", {}) or {}).items():
        try:
            offsets[url] = max(int(offset or 0), int(offsets.get(url, 0) or 0))
        except (TypeError, ValueError):
            offsets[url] = offset
    backfill["archive_entry_offsets"] = offsets


def merged_existing_state(
    *,
    artifact_root: Path,
    sources: list[str],
    legacy_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {"backfill": {}}
    for source in sources:
        merge_source_state(merged, source, legacy_state or {})
        source_root = artifact_root / source
        if not source_root.exists():
            continue
        for state_path in sorted(source_root.glob("*/collector_state.json")):
            merge_source_state(merged, source, load_json(state_path))
    return merged


def shard_archive_urls(source: str, shard_key: str, start: date, end: date) -> tuple[list[str], str]:
    if source == "prnewswire" and shard_key == "recent":
        return newswire_backfill_archive_urls(source, start, end, prnewswire_archive_scope="recent"), "recent"
    if source == "prnewswire":
        return newswire_backfill_archive_urls(source, start, end, prnewswire_archive_scope="monthly"), "monthly"
    return newswire_backfill_archive_urls(source, start, end), "all"


def build_shard(
    *,
    source: str,
    shard_key: str,
    start: date,
    end: date,
    artifact_root: Path = DEFAULT_SHARD_ARTIFACT_ROOT,
    raw_root: Path = DEFAULT_SHARD_RAW_ROOT,
    legacy_state: dict[str, Any] | None = None,
    log_root: Path = Path("logs"),
) -> NewswireShard:
    legacy_state = legacy_state or {}
    archive_urls, scope = shard_archive_urls(source, shard_key, start, end)
    artifact_dir = artifact_root / source / shard_key
    raw_dir = raw_root / source / shard_key
    legacy_source = legacy_source_state(legacy_state, source)
    local_source = legacy_source_state(load_json(artifact_dir / "collector_state.json"), source)
    legacy_completed_all = set(legacy_source.get("completed_archive_urls", []) or [])
    local_completed_all = set(local_source.get("completed_archive_urls", []) or [])
    completed_all = legacy_completed_all | local_completed_all
    legacy_completed = sorted(url for url in archive_urls if url in legacy_completed_all)
    local_completed = sorted(url for url in archive_urls if url in local_completed_all)
    completed_for_pending = set(legacy_completed) | set(local_completed)
    legacy_offsets_all = legacy_source.get("archive_entry_offsets", {}) or {}
    local_offsets_all = local_source.get("archive_entry_offsets", {}) or {}
    legacy_offsets = {url: int(offset) for url, offset in legacy_offsets_all.items() if url in archive_urls}
    local_offsets = {url: int(offset) for url, offset in local_offsets_all.items() if url in archive_urls}
    merged_offsets = {**legacy_offsets, **local_offsets}
    pending_units = len([url for url in archive_urls if url not in completed_all])
    status = "LEGACY_COMPLETED" if archive_urls and pending_units == 0 else "PENDING"
    return NewswireShard(
        source=source,
        shard_key=shard_key,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        archive_scope=scope,
        artifact_dir=str(artifact_dir),
        raw_dir=str(raw_dir),
        state_path=str(artifact_dir / "collector_state.json"),
        event_path=str(artifact_dir / "collector_events.jsonl"),
        progress_path=str(artifact_dir / "collector_progress.json"),
        plan_path=str(artifact_dir / "collection_plan.json"),
        stop_path=str(artifact_root / "STOP"),
        log_path=str(log_root / f"l0_public_newswire_shard_{source}_{shard_key}.log"),
        archive_urls=archive_urls,
        total_units=len(archive_urls),
        legacy_completed_units=len(completed_for_pending),
        pending_units=pending_units,
        legacy_completed_archive_urls=sorted(completed_for_pending),
        legacy_archive_entry_offsets=merged_offsets,
        status=status,
    )


def build_inventory(
    *,
    start_month: str = "2016-01",
    end_month: str | None = None,
    sources: list[str] | None = None,
    artifact_root: Path = DEFAULT_SHARD_ARTIFACT_ROOT,
    raw_root: Path = DEFAULT_SHARD_RAW_ROOT,
    legacy_state: dict[str, Any] | None = None,
    businesswire_shard_granularity: str = "month",
) -> dict[str, Any]:
    end_month = end_month or default_end_month()
    sources = sources or ["businesswire", "globenewswire", "prnewswire"]
    if businesswire_shard_granularity not in {"month", "day"}:
        raise ValueError(f"unsupported businesswire_shard_granularity: {businesswire_shard_granularity}")
    inherited_state = merged_existing_state(artifact_root=artifact_root, sources=sources, legacy_state=legacy_state)
    shards: list[NewswireShard] = []
    for source in sources:
        for month in iter_months(start_month, end_month):
            key = month_key(month)
            if source == "businesswire" and businesswire_shard_granularity == "day":
                for day in iter_days(month, month_end(month)):
                    shards.append(
                        build_shard(
                            source=source,
                            shard_key=day.isoformat(),
                            start=day,
                            end=day,
                            artifact_root=artifact_root,
                            raw_root=raw_root,
                            legacy_state=inherited_state,
                        )
                    )
            else:
                shards.append(
                    build_shard(
                        source=source,
                        shard_key=key,
                        start=month,
                        end=month_end(month),
                        artifact_root=artifact_root,
                        raw_root=raw_root,
                        legacy_state=inherited_state,
                    )
                )
        if source == "prnewswire":
            start = parse_month(start_month)
            end = month_end(parse_month(end_month))
            shards.append(
                build_shard(
                    source=source,
                    shard_key="recent",
                    start=start,
                    end=end,
                    artifact_root=artifact_root,
                    raw_root=raw_root,
                    legacy_state=inherited_state,
                )
            )
    by_source: dict[str, dict[str, int]] = {}
    for shard in shards:
        row = by_source.setdefault(shard.source, {"total_units": 0, "legacy_completed_units": 0, "pending_units": 0, "shards": 0})
        row["total_units"] += shard.total_units
        row["legacy_completed_units"] += shard.legacy_completed_units
        row["pending_units"] += shard.pending_units
        row["shards"] += 1
    return {
        "schema_version": SHARD_SCHEMA_VERSION,
        "generated_at": now_z(),
        "provider": PROVIDER,
        "start_month": start_month,
        "end_month": end_month,
        "businesswire_shard_granularity": businesswire_shard_granularity,
        "by_source": by_source,
        "total_units": sum(shard.total_units for shard in shards),
        "legacy_completed_units": sum(shard.legacy_completed_units for shard in shards),
        "pending_units": sum(shard.pending_units for shard in shards),
        "shards": [shard.as_dict() for shard in shards],
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }


def seed_shard_state(shard: dict[str, Any]) -> None:
    state_path = Path(shard["state_path"])
    state = load_json(state_path)
    backfill = state.setdefault("backfill", {}).setdefault(shard["source"], {})
    existing_completed = set(backfill.get("completed_archive_urls", []) or [])
    existing_completed.update(shard.get("legacy_completed_archive_urls", []) or [])
    backfill["completed_archive_urls"] = sorted(existing_completed)
    backfill["unavailable_archive_urls"] = sorted(set(backfill.get("unavailable_archive_urls", []) or []))
    offsets = dict(backfill.get("archive_entry_offsets", {}) or {})
    offsets.update(shard.get("legacy_archive_entry_offsets", {}) or {})
    backfill["archive_entry_offsets"] = offsets
    backfill["start_date"] = shard["start_date"]
    backfill["end_date"] = shard["end_date"]
    backfill["total_archive_urls"] = int(shard["total_units"])
    backfill["pending_archive_urls"] = int(shard["pending_units"])
    state["schema_version"] = 1
    state["updated_at"] = now_z()
    atomic_write_json(state_path, state)
