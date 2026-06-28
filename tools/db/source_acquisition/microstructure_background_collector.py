from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, time as dtime, timedelta
from pathlib import Path
from typing import Callable, Iterable
from zoneinfo import ZoneInfo

import pandas as pd

from src.data.alpaca_historical_microstructure_export import AlpacaHistoricalMicrostructureProvider
from tools.db.source_acquisition.microstructure_checkpoint import (
    DEFAULT_CHECKPOINT_PATH,
    MicrostructureCheckpointStore,
    compute_chunk_id,
    sha256_file,
)
from tools.db.source_acquisition.secret_redaction import redact_text


DEFAULT_UNIVERSE_PATH = Path("data/raw/alpaca_active_us_equity_universe.csv")
DEFAULT_RAW_DIR = Path("data/raw/alpaca_historical_microstructure_backfill")
DEFAULT_STATE_DIR = Path("data/artifacts/microstructure_backfill_queue")
DEFAULT_STATE_PATH = DEFAULT_STATE_DIR / "collector_state.json"
DEFAULT_EVENT_PATH = DEFAULT_STATE_DIR / "collector_events.jsonl"
DEFAULT_PROGRESS_PATH = DEFAULT_STATE_DIR / "collector_progress.json"
DEFAULT_STOP_PATH = DEFAULT_STATE_DIR / "STOP"
DEFAULT_LOG_PATH = Path("logs/l0_microstructure_background_collector.log")
DEFAULT_START_DATE = "2016-01-01"
DEFAULT_FEED = "iex"
DEFAULT_CHUNK_MINUTES = 15
SOURCE_TYPES = ("quotes", "trades")
TERMINAL_STATUSES = {"EXPORTED", "SKIPPED_EXISTS", "EMPTY_PROVIDER_RESPONSE", "FAILED_PERMANENT"}
NY_TZ = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class CollectorConfig:
    universe_path: Path = DEFAULT_UNIVERSE_PATH
    raw_dir: Path = DEFAULT_RAW_DIR
    checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH
    state_path: Path = DEFAULT_STATE_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    stop_path: Path = DEFAULT_STOP_PATH
    log_path: Path = DEFAULT_LOG_PATH
    feed: str = DEFAULT_FEED
    start_date: str = DEFAULT_START_DATE
    end_date: str = ""
    direction: str = "backward"
    chunk_minutes: int = DEFAULT_CHUNK_MINUTES
    requests_per_minute: int = 60
    max_chunks: int = 0
    max_runtime_minutes: int = 0
    skip_existing_symbols: bool = True
    raw_roots: tuple[Path, ...] = (
        Path("data/raw/alpaca_historical_microstructure"),
        Path("data/raw/alpaca_historical_microstructure_smoke"),
        Path("data/raw/alpaca_historical_microstructure_backfill"),
    )


@dataclass(frozen=True)
class ChunkPlan:
    symbol: str
    source_type: str
    session_date: str
    chunk_start_ts: str
    chunk_end_ts: str
    chunk_id: str
    raw_path: Path


def latest_complete_market_date(now_utc: datetime | None = None) -> str:
    now = now_utc or datetime.now(UTC)
    candidate = (now - timedelta(days=1)).date()
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate.isoformat()


def load_universe(path: Path = DEFAULT_UNIVERSE_PATH, *, limit: int | None = None) -> list[str]:
    frame = pd.read_csv(path, dtype=str)
    symbol_col = "symbol" if "symbol" in frame.columns else frame.columns[0]
    filtered = frame.copy()
    if "status" in filtered.columns:
        filtered = filtered[filtered["status"].fillna("").str.lower().eq("active")]
    if "tradable" in filtered.columns:
        filtered = filtered[filtered["tradable"].fillna("").str.lower().isin({"true", "1", "yes"})]
    symbols = sorted({str(symbol).strip().upper() for symbol in filtered[symbol_col].tolist() if str(symbol).strip()})
    if limit is not None:
        symbols = symbols[: max(int(limit), 0)]
    return symbols


def trading_days(start_date: str, end_date: str, *, direction: str = "backward") -> list[str]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    days: list[str] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current += timedelta(days=1)
    if direction == "backward":
        return list(reversed(days))
    if direction == "forward":
        return days
    raise ValueError("direction must be 'backward' or 'forward'")


def session_chunks(session_date: str, *, chunk_minutes: int = 1) -> list[tuple[str, str]]:
    day = date.fromisoformat(session_date)
    local_open = datetime.combine(day, dtime(9, 30), tzinfo=NY_TZ)
    local_close = datetime.combine(day, dtime(16, 0), tzinfo=NY_TZ)
    chunks: list[tuple[str, str]] = []
    current = local_open
    step = timedelta(minutes=max(int(chunk_minutes), 1))
    while current < local_close:
        end = min(current + step, local_close)
        chunks.append((to_utc_z(current), to_utc_z(end)))
        current = end
    return chunks


def to_utc_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def safe_symbol_path(symbol: str) -> str:
    return symbol.upper().replace("/", "_")


def chunk_raw_path(
    raw_dir: Path,
    *,
    feed: str,
    source_type: str,
    symbol: str,
    session_date: str,
    chunk_start_ts: str,
    chunk_end_ts: str,
) -> Path:
    start = compact_ts(chunk_start_ts)
    end = compact_ts(chunk_end_ts)
    return (
        raw_dir
        / f"feed={feed}"
        / f"source_type={source_type}"
        / f"symbol={safe_symbol_path(symbol)}"
        / f"session_date={session_date}"
        / f"chunk_start={start}_chunk_end={end}.csv"
    )


def compact_ts(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("+00:00", "Z")


def legacy_existing_source_symbols(raw_roots: Iterable[Path]) -> set[tuple[str, str]]:
    existing: set[tuple[str, str]] = set()
    for root in raw_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            if is_chunked_raw_path(path):
                continue
            source_type = source_type_from_path(path)
            symbol = symbol_from_path(path)
            if source_type in SOURCE_TYPES and symbol:
                existing.add((source_type, symbol.upper()))
    return existing


def is_chunked_raw_path(path: Path) -> bool:
    return any(part.startswith("source_type=") for part in path.parts) and any(part.startswith("session_date=") for part in path.parts)


def source_type_from_path(path: Path) -> str:
    normalized = path.as_posix()
    if "/source_type=quotes/" in normalized or "/quotes/" in normalized:
        return "quotes"
    if "/source_type=trades/" in normalized or "/trades/" in normalized:
        return "trades"
    return ""


def symbol_from_path(path: Path) -> str:
    for part in path.parts:
        if part.startswith("symbol="):
            return part.split("=", 1)[1].upper()
    return path.stem.upper()


def load_terminal_chunk_ids(event_path: Path, checkpoint_path: Path) -> set[str]:
    terminal: set[str] = set()
    if event_path.exists():
        for line in event_path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("status") in TERMINAL_STATUSES and row.get("chunk_id"):
                terminal.add(str(row["chunk_id"]))
    store = MicrostructureCheckpointStore(checkpoint_path)
    for row in store.load():
        if row.get("status") in TERMINAL_STATUSES and row.get("chunk_id"):
            terminal.add(str(row["chunk_id"]))
    return terminal


def initial_state(config: CollectorConfig, *, total_symbols: int, total_days: int, chunks_per_day: int) -> dict[str, object]:
    return {
        "schema_version": 1,
        "feed": config.feed,
        "start_date": config.start_date,
        "end_date": resolved_end_date(config),
        "direction": config.direction,
        "chunk_minutes": int(config.chunk_minutes),
        "date_index": 0,
        "symbol_index": 0,
        "chunk_index": 0,
        "source_type_index": 0,
        "total_symbols": int(total_symbols),
        "total_days": int(total_days),
        "chunks_per_day": int(chunks_per_day),
        "processed_chunks": 0,
        "exported_chunks": 0,
        "empty_chunks": 0,
        "skipped_chunks": 0,
        "failed_chunks": 0,
        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def resolved_end_date(config: CollectorConfig) -> str:
    return config.end_date or latest_complete_market_date()


def load_state(config: CollectorConfig, *, total_symbols: int, total_days: int, chunks_per_day: int) -> dict[str, object]:
    if not config.state_path.exists():
        return initial_state(config, total_symbols=total_symbols, total_days=total_days, chunks_per_day=chunks_per_day)
    state = json.loads(config.state_path.read_text(encoding="utf-8-sig"))
    expected = {
        "feed": config.feed,
        "start_date": config.start_date,
        "end_date": resolved_end_date(config),
        "direction": config.direction,
        "chunk_minutes": int(config.chunk_minutes),
    }
    if any(state.get(key) != value for key, value in expected.items()):
        raise ValueError(f"collector state at {config.state_path} belongs to a different collection scope")
    state["total_symbols"] = int(total_symbols)
    state["total_days"] = int(total_days)
    state["chunks_per_day"] = int(chunks_per_day)
    return state


def save_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def advance_state(state: dict[str, object], *, total_days: int, total_symbols: int, chunks_per_day: int) -> bool:
    source_idx = int(state["source_type_index"]) + 1
    chunk_idx = int(state["chunk_index"])
    symbol_idx = int(state["symbol_index"])
    date_idx = int(state["date_index"])
    if source_idx >= len(SOURCE_TYPES):
        source_idx = 0
        chunk_idx += 1
    if chunk_idx >= chunks_per_day:
        chunk_idx = 0
        symbol_idx += 1
    if symbol_idx >= total_symbols:
        symbol_idx = 0
        date_idx += 1
    state["source_type_index"] = source_idx
    state["chunk_index"] = chunk_idx
    state["symbol_index"] = symbol_idx
    state["date_index"] = date_idx
    return date_idx < total_days


def current_chunk(
    *,
    config: CollectorConfig,
    state: dict[str, object],
    days: list[str],
    symbols: list[str],
    chunks_by_date: dict[str, list[tuple[str, str]]],
) -> ChunkPlan | None:
    date_idx = int(state["date_index"])
    symbol_idx = int(state["symbol_index"])
    chunk_idx = int(state["chunk_index"])
    source_type_idx = int(state["source_type_index"])
    if date_idx >= len(days) or symbol_idx >= len(symbols):
        return None
    session_date = days[date_idx]
    chunks = chunks_by_date[session_date]
    if chunk_idx >= len(chunks):
        return None
    chunk_start_ts, chunk_end_ts = chunks[chunk_idx]
    symbol = symbols[symbol_idx]
    source_type = SOURCE_TYPES[source_type_idx]
    chunk_id = compute_chunk_id(
        provider="alpaca",
        feed=config.feed,
        source_type=source_type,
        symbol=symbol,
        chunk_start_ts=chunk_start_ts,
        chunk_end_ts=chunk_end_ts,
    )
    raw_path = chunk_raw_path(
        config.raw_dir,
        feed=config.feed,
        source_type=source_type,
        symbol=symbol,
        session_date=session_date,
        chunk_start_ts=chunk_start_ts,
        chunk_end_ts=chunk_end_ts,
    )
    return ChunkPlan(
        symbol=symbol,
        source_type=source_type,
        session_date=session_date,
        chunk_start_ts=chunk_start_ts,
        chunk_end_ts=chunk_end_ts,
        chunk_id=chunk_id,
        raw_path=raw_path,
    )


def append_event(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = dict(event)
    event["updated_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_progress(path: Path, state: dict[str, object], extra: dict[str, object]) -> None:
    payload = dict(state)
    payload.update(extra)
    payload["feature_builder_allowed_flag"] = 0
    payload["broker_mutation_permitted_flag"] = 0
    payload["updated_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def log_line(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{now} {message}\n")


def process_chunk(
    plan: ChunkPlan,
    *,
    provider: AlpacaHistoricalMicrostructureProvider,
    config: CollectorConfig,
    checkpoint_store: MicrostructureCheckpointStore,
    fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
) -> tuple[str, int, str]:
    if plan.raw_path.exists():
        return "SKIPPED_EXISTS", _csv_row_count(plan.raw_path), ""
    fetcher = fetcher or _fetch_from_provider(provider, plan.source_type)
    frame = fetcher(plan.symbol, plan.chunk_start_ts, plan.chunk_end_ts)
    if frame.empty:
        return "EMPTY_PROVIDER_RESPONSE", 0, ""
    plan.raw_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(plan.raw_path, index=False, encoding="utf-8-sig")
    checkpoint_store.record(
        provider="alpaca",
        feed=config.feed,
        source_type=plan.source_type,
        symbol=plan.symbol,
        session_date=plan.session_date,
        chunk_start_ts=plan.chunk_start_ts,
        chunk_end_ts=plan.chunk_end_ts,
        status="EXPORTED",
        row_count=int(len(frame)),
        raw_path=plan.raw_path,
    )
    return "EXPORTED", int(len(frame)), sha256_file(plan.raw_path)


def _fetch_from_provider(provider: AlpacaHistoricalMicrostructureProvider, source_type: str) -> Callable[[str, str, str], pd.DataFrame]:
    if source_type == "quotes":
        return lambda symbol, start, end: provider.fetch_quotes(symbol, start=start, end=end)
    if source_type == "trades":
        return lambda symbol, start, end: provider.fetch_trades(symbol, start=start, end=end)
    raise ValueError(f"unsupported source_type: {source_type}")


def _csv_row_count(path: Path) -> int:
    try:
        return max(sum(1 for _ in path.open("r", encoding="utf-8-sig")) - 1, 0)
    except Exception:
        return 0


def classify_error(exc: Exception) -> tuple[str, str]:
    text = str(exc)
    lower = text.lower()
    code = getattr(exc, "code", None)
    if code == 429 or "429" in lower or "rate limit" in lower:
        return "RATE_LIMITED", "RATE_LIMITED"
    if code in {401, 403} or "credential" in lower or "unauthorized" in lower or "forbidden" in lower or "subscription" in lower:
        return "CREDENTIAL_BLOCKED", "CREDENTIAL_BLOCKED"
    return "FAILED_RETRYABLE", type(exc).__name__


def run_collector(config: CollectorConfig, *, universe_limit: int | None = None) -> dict[str, object]:
    end_date = resolved_end_date(config)
    symbols = load_universe(config.universe_path, limit=universe_limit)
    days = trading_days(config.start_date, end_date, direction=config.direction)
    chunks_by_date = {day: session_chunks(day, chunk_minutes=config.chunk_minutes) for day in days}
    chunks_per_day = len(next(iter(chunks_by_date.values()))) if chunks_by_date else 0
    state = load_state(config, total_symbols=len(symbols), total_days=len(days), chunks_per_day=chunks_per_day)
    existing_source_symbols = legacy_existing_source_symbols(config.raw_roots) if config.skip_existing_symbols else set()
    terminal_chunk_ids = load_terminal_chunk_ids(config.event_path, config.checkpoint_path)
    provider = AlpacaHistoricalMicrostructureProvider(feed=config.feed)
    checkpoint_store = MicrostructureCheckpointStore(config.checkpoint_path)
    started = time.monotonic()
    processed_this_run = 0
    last_status = "STARTED"
    last_plan: ChunkPlan | None = None
    sleep_seconds = 60.0 / max(int(config.requests_per_minute), 1)
    log_line(
        config.log_path,
        (
            "[COLLECTOR_START] "
            f"feed={config.feed} start_date={config.start_date} end_date={end_date} "
            f"symbols={len(symbols)} days={len(days)} chunk_minutes={config.chunk_minutes} "
            f"skip_existing_symbols={int(config.skip_existing_symbols)}"
        ),
    )
    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        if config.max_chunks and processed_this_run >= config.max_chunks:
            last_status = "MAX_CHUNKS_REACHED"
            break
        if config.max_runtime_minutes and (time.monotonic() - started) >= config.max_runtime_minutes * 60:
            last_status = "MAX_RUNTIME_REACHED"
            break
        plan = current_chunk(config=config, state=state, days=days, symbols=symbols, chunks_by_date=chunks_by_date)
        if plan is None:
            last_status = "DONE"
            break
        last_plan = plan
        status = ""
        row_count = 0
        raw_sha = ""
        error_category = ""
        error_message = ""
        try:
            if (plan.source_type, plan.symbol) in existing_source_symbols:
                status = "SKIPPED_EXISTS"
            elif plan.chunk_id in terminal_chunk_ids:
                status = "SKIPPED_EXISTS"
            else:
                status, row_count, raw_sha = process_chunk(plan, provider=provider, config=config, checkpoint_store=checkpoint_store)
                if status in TERMINAL_STATUSES:
                    terminal_chunk_ids.add(plan.chunk_id)
        except Exception as exc:  # noqa: BLE001
            status, error_category = classify_error(exc)
            error_message = redact_text(str(exc))
            if status == "RATE_LIMITED":
                time.sleep(max(60.0, sleep_seconds))
            elif status == "CREDENTIAL_BLOCKED":
                last_status = status
        append_event(
            config.event_path,
            {
                "provider": "alpaca",
                "feed": config.feed,
                "source_type": plan.source_type,
                "symbol": plan.symbol,
                "session_date": plan.session_date,
                "chunk_start_ts": plan.chunk_start_ts,
                "chunk_end_ts": plan.chunk_end_ts,
                "chunk_id": plan.chunk_id,
                "status": status,
                "row_count": int(row_count),
                "raw_path": str(plan.raw_path) if status == "EXPORTED" else "",
                "raw_sha256": raw_sha,
                "error_category": error_category,
                "error_message_redacted": error_message,
                "feature_builder_allowed_flag": 0,
                "broker_mutation_permitted_flag": 0,
            },
        )
        state["processed_chunks"] = int(state.get("processed_chunks", 0)) + 1
        if status == "EXPORTED":
            state["exported_chunks"] = int(state.get("exported_chunks", 0)) + 1
        elif status == "EMPTY_PROVIDER_RESPONSE":
            state["empty_chunks"] = int(state.get("empty_chunks", 0)) + 1
        elif status == "SKIPPED_EXISTS":
            state["skipped_chunks"] = int(state.get("skipped_chunks", 0)) + 1
        elif status:
            state["failed_chunks"] = int(state.get("failed_chunks", 0)) + 1
        processed_this_run += 1
        still_has_work = advance_state(state, total_days=len(days), total_symbols=len(symbols), chunks_per_day=chunks_per_day)
        save_state(config.state_path, state)
        write_progress(
            config.progress_path,
            state,
            {
                "last_status": status,
                "last_symbol": plan.symbol,
                "last_source_type": plan.source_type,
                "last_session_date": plan.session_date,
                "last_chunk_start_ts": plan.chunk_start_ts,
                "last_chunk_end_ts": plan.chunk_end_ts,
                "processed_this_run": processed_this_run,
                "estimated_total_chunks": len(days) * len(symbols) * chunks_per_day * len(SOURCE_TYPES),
            },
        )
        if status == "CREDENTIAL_BLOCKED":
            break
        if not still_has_work:
            last_status = "DONE"
            break
        if status != "SKIPPED_EXISTS":
            time.sleep(sleep_seconds)
    result = {
        "status": last_status,
        "processed_this_run": processed_this_run,
        "state_path": str(config.state_path),
        "event_path": str(config.event_path),
        "progress_path": str(config.progress_path),
        "last_symbol": "" if last_plan is None else last_plan.symbol,
        "last_source_type": "" if last_plan is None else last_plan.source_type,
        "feature_builder_allowed_flag": 0,
        "broker_mutation_permitted_flag": 0,
    }
    write_progress(config.progress_path, state, result)
    log_line(config.log_path, f"[COLLECTOR_EXIT] {json.dumps(result, sort_keys=True)}")
    return result
