from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError

import pandas as pd

from src.data.intraday_backfill import (
    AlpacaHistoricalBarsProvider,
    DEFAULT_RETRY_LIMIT,
    ensure_bar_schema,
    ensure_market_bars_table,
    fetch_with_retries,
    upsert_market_bars,
)
from tools.db.source_acquisition.secret_redaction import redact_text


DEFAULT_UNIVERSE_PATH = Path("data/raw/alpaca_active_us_equity_universe.csv")
DEFAULT_DAILY_RAW_DIR = Path("data/raw/us_daily_alpaca_full_universe")
DEFAULT_STATE_DIR = Path("data/artifacts/l0_bar_full_backfill")
DEFAULT_STATE_PATH = DEFAULT_STATE_DIR / "collector_state.json"
DEFAULT_EVENT_PATH = DEFAULT_STATE_DIR / "collector_events.jsonl"
DEFAULT_PROGRESS_PATH = DEFAULT_STATE_DIR / "collector_progress.json"
DEFAULT_STOP_PATH = DEFAULT_STATE_DIR / "STOP"
DEFAULT_PLAN_PATH = DEFAULT_STATE_DIR / "full_backfill_plan.json"
DEFAULT_CONTRACT_PATH = DEFAULT_STATE_DIR / "l1_l2_bar_contract.json"
DEFAULT_LOG_PATH = Path("logs/l0_bar_full_backfill_collector.log")
DEFAULT_DB_PATH = Path("trading.db")
DEFAULT_START_DATE = "2016-01-01"
DEFAULT_FIVE_MIN_CHUNK_DAYS = 120
DEFAULT_REQUESTS_PER_MINUTE = 120
LANES = ("daily", "5m")
FIVE_MIN_BARS_PER_FULL_SESSION = 78


class BarsProvider(Protocol):
    def fetch_bars(self, symbol: str, start_date: date, end_date: date, interval: str = "5m") -> pd.DataFrame:
        raise NotImplementedError


@dataclass(frozen=True)
class BarFullBackfillConfig:
    universe_path: Path = DEFAULT_UNIVERSE_PATH
    daily_raw_dir: Path = DEFAULT_DAILY_RAW_DIR
    db_path: Path = DEFAULT_DB_PATH
    state_path: Path = DEFAULT_STATE_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    stop_path: Path = DEFAULT_STOP_PATH
    plan_path: Path = DEFAULT_PLAN_PATH
    contract_path: Path = DEFAULT_CONTRACT_PATH
    log_path: Path = DEFAULT_LOG_PATH
    start_date: str = DEFAULT_START_DATE
    end_date: str = ""
    lanes: tuple[str, ...] = LANES
    five_min_chunk_days: int = DEFAULT_FIVE_MIN_CHUNK_DAYS
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE
    retry_limit: int = DEFAULT_RETRY_LIMIT
    max_requests: int = 0
    max_runtime_minutes: int = 0
    skip_existing_daily: bool = True
    universe_offset: int = 0
    universe_stride: int = 1


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def latest_complete_market_date(now_utc: datetime | None = None) -> str:
    now = now_utc or datetime.now(UTC)
    candidate = (now - timedelta(days=1)).date()
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate.isoformat()


def resolved_end_date(config: BarFullBackfillConfig) -> str:
    return config.end_date or latest_complete_market_date()


def safe_symbol(symbol: str) -> str:
    return str(symbol).strip().upper().replace("/", "_")


def load_universe(
    path: Path = DEFAULT_UNIVERSE_PATH,
    *,
    limit: int | None = None,
    offset: int = 0,
    stride: int = 1,
) -> list[str]:
    frame = pd.read_csv(path, dtype=str)
    symbol_col = "symbol" if "symbol" in frame.columns else frame.columns[0]
    filtered = frame.copy()
    if "status" in filtered.columns:
        filtered = filtered[filtered["status"].fillna("").str.lower().eq("active")]
    if "tradable" in filtered.columns:
        filtered = filtered[filtered["tradable"].fillna("").str.lower().isin({"true", "1", "yes"})]
    symbols = sorted({safe_symbol(symbol) for symbol in filtered[symbol_col].tolist() if str(symbol).strip()})
    normalized_stride = max(int(stride), 1)
    normalized_offset = max(int(offset), 0)
    if normalized_stride > 1 or normalized_offset > 0:
        symbols = [symbol for idx, symbol in enumerate(symbols) if idx % normalized_stride == normalized_offset % normalized_stride]
    if limit is not None:
        symbols = symbols[: max(int(limit), 0)]
    return symbols


def weekday_count(start_date: str, end_date: str) -> int:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def calendar_date_blocks(start_date: str, end_date: str, *, max_span_days: int) -> list[tuple[date, date]]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    blocks: list[tuple[date, date]] = []
    current = start
    span = max(int(max_span_days), 1)
    while current <= end:
        block_end = min(end, current + timedelta(days=span - 1))
        blocks.append((current, block_end))
        current = block_end + timedelta(days=1)
    return blocks


def load_state(config: BarFullBackfillConfig, *, universe_count: int, blocks_per_symbol: int) -> dict[str, Any]:
    if config.state_path.exists():
        return json.loads(config.state_path.read_text(encoding="utf-8-sig"))
    return {
        "schema_version": 1,
        "start_date": config.start_date,
        "end_date": resolved_end_date(config),
        "lanes": list(config.lanes),
        "universe_count": universe_count,
        "five_min_blocks_per_symbol": blocks_per_symbol,
        "lane_cursor_index": 0,
        "daily_symbol_index": 0,
        "five_min_symbol_index": 0,
        "five_min_block_index": 0,
        "processed_events": 0,
        "exported_events": 0,
        "empty_events": 0,
        "skipped_events": 0,
        "failed_events": 0,
        "rate_limited_events": 0,
        "daily_rows_written": 0,
        "five_min_rows_written": 0,
        "updated_at": now_z(),
    }


def save_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_z()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def append_event(path: Path, event: dict[str, Any]) -> None:
    payload = dict(event)
    payload["updated_at"] = now_z()
    payload["diagnostic_only_flag"] = 1
    payload["trade_authority_flag"] = 0
    payload["broker_mutation_permitted_flag"] = 0
    payload["real_capital_permitted_flag"] = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def log_line(path: Path, message: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{now_z()} {message}\n")
    except OSError as exc:
        fallback = Path("data/artifacts/l0_backfill_orchestration/log_write_failures.jsonl")
        try:
            fallback.parent.mkdir(parents=True, exist_ok=True)
            with fallback.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "ts": now_z(),
                            "collector": "bar_full_backfill",
                            "log_path": str(path),
                            "message": message,
                            "error": str(exc),
                            "diagnostic_only_flag": 1,
                            "trade_authority_flag": 0,
                            "broker_mutation_permitted_flag": 0,
                            "real_capital_permitted_flag": 0,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
        except OSError:
            pass


def total_universe_count(path: Path = DEFAULT_UNIVERSE_PATH) -> int:
    return len(load_universe(path))


def build_plan(config: BarFullBackfillConfig, *, universe_count: int, blocks_per_symbol: int, total_universe: int | None = None) -> dict[str, Any]:
    end_date = resolved_end_date(config)
    weekdays = weekday_count(config.start_date, end_date)
    daily_requests = universe_count if "daily" in config.lanes else 0
    five_min_requests = universe_count * blocks_per_symbol if "5m" in config.lanes else 0
    total_requests = daily_requests + five_min_requests
    rpm = max(int(config.requests_per_minute), 1)
    plan = {
        "created_at": now_z(),
        "objective": "Full-universe L0 daily and 5m bar backfill for L1/L2 canonical consumption while quote/trade ticks remain postponed.",
        "start_date": config.start_date,
        "end_date": end_date,
        "universe_count": universe_count,
        "total_universe_count": total_universe if total_universe is not None else universe_count,
        "universe_shard": {
            "offset": int(config.universe_offset),
            "stride": int(config.universe_stride),
            "sharded": int(config.universe_stride) > 1 or int(config.universe_offset) > 0,
        },
        "lanes": list(config.lanes),
        "daily": {
            "raw_dir": str(config.daily_raw_dir),
            "schema": ["timestamp", "open", "high", "low", "close", "volume", "symbol"],
            "estimated_requests": daily_requests,
            "estimated_rows_weekday_upper_bound": universe_count * weekdays,
            "l1_loader_compatible": True,
        },
        "five_min": {
            "db_path": str(config.db_path),
            "table": "market_bars_5m",
            "chunk_days": int(config.five_min_chunk_days),
            "blocks_per_symbol": blocks_per_symbol,
            "estimated_requests": five_min_requests,
            "estimated_rows_regular_session_upper_bound": universe_count * weekdays * FIVE_MIN_BARS_PER_FULL_SESSION,
            "l2_runtime_source_table": "market_bars_5m",
        },
        "api_throttle": {
            "requests_per_minute": rpm,
            "theoretical_eta_hours_at_configured_rpm": round(total_requests / rpm / 60.0, 2) if total_requests else 0.0,
            "note": "Alpaca optimization is chunk/window based; this runner does not increase the rate above the configured throttle.",
        },
        "permissions": {
            "diagnostic_only": True,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        },
    }
    config.plan_path.parent.mkdir(parents=True, exist_ok=True)
    config.plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    write_l1_l2_contract(config)
    return plan


def write_l1_l2_contract(config: BarFullBackfillConfig) -> None:
    contract = {
        "created_at": now_z(),
        "status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        "tick_quote_trade_full_collection": "POSTPONED",
        "daily_bars": {
            "provider": "alpaca_historical_bars",
            "interval": "1d",
            "path_pattern": str(config.daily_raw_dir / "<SYMBOL>.csv"),
            "required_columns": ["timestamp", "open", "high", "low", "close", "volume", "symbol"],
            "consumer": "src.backtest.data_loader.load_daily_bars(base_dir=...)",
            "source_readiness": "L1_BACKTEST_COMPATIBLE_RAW_CSV",
        },
        "five_min_bars": {
            "provider": "alpaca_historical_bars",
            "interval": "5m",
            "db_path": str(config.db_path),
            "table": "market_bars_5m",
            "required_columns": [
                "bar_id",
                "symbol",
                "bar_start_ts",
                "bar_end_ts",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "tick_count",
                "source",
                "last_updated_at",
            ],
            "consumer": "src.l2.live_runtime.write_live_runtime_l2_primitives_from_db",
            "source_readiness": "L2_CANONICAL_MARKET_BAR_INPUT",
        },
        "non_negotiables": {
            "no_inferred_lifecycle_matching": True,
            "missing_labels_are_not_negatives": True,
            "missing_raw_sources_are_not_approximated": True,
            "strategy_or_deployment_claim": False,
        },
    }
    config.contract_path.parent.mkdir(parents=True, exist_ok=True)
    config.contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True), encoding="utf-8")


def daily_csv_path(raw_dir: Path, symbol: str) -> Path:
    return raw_dir / f"{safe_symbol(symbol)}.csv"


def daily_csv_complete(path: Path, *, end_date: str) -> tuple[bool, int]:
    if not path.exists():
        return False, 0
    try:
        frame = pd.read_csv(path, usecols=["timestamp"])
    except Exception:
        return False, 0
    if frame.empty:
        return False, 0
    ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dropna()
    if ts.empty:
        return False, 0
    latest_date = ts.max().date().isoformat()
    return latest_date >= end_date, int(len(ts))


def daily_loader_frame(bars: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    frame = ensure_bar_schema(bars)
    if frame.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "symbol"])
    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(frame["bar_start_ts"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": frame["open"].astype(float),
            "high": frame["high"].astype(float),
            "low": frame["low"].astype(float),
            "close": frame["close"].astype(float),
            "volume": frame["volume"].astype(float),
            "symbol": safe_symbol(symbol),
        }
    )
    out = out.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    return out.reset_index(drop=True)


def write_daily_csv(raw_dir: Path, *, symbol: str, bars: pd.DataFrame) -> int:
    out = daily_loader_frame(bars, symbol=symbol)
    if out.empty:
        return 0
    path = daily_csv_path(raw_dir, symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    return int(len(out))


def source_event(
    *,
    lane: str,
    symbol: str,
    source_id: str,
    status: str,
    row_count: int,
    raw_path: Path | None = None,
    db_path: Path | None = None,
    error_category: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    event = {
        "provider": "alpaca_historical_bars",
        "lane": lane,
        "symbol": safe_symbol(symbol),
        "source_id": source_id,
        "status": status,
        "row_count": int(row_count),
        "raw_path": "" if raw_path is None else str(raw_path),
        "db_path": "" if db_path is None else str(db_path),
        "error_category": error_category,
        "error_message": redact_text(error_message),
    }
    return event


def classify_error(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, HTTPError) and exc.code == 429:
        return "RATE_LIMITED", "HTTP_429"
    text = str(exc)
    if "429" in text or "rate limit" in text.lower():
        return "RATE_LIMITED", type(exc).__name__
    return "FAILED_RETRYABLE", type(exc).__name__


def collect_daily_symbol(config: BarFullBackfillConfig, provider: BarsProvider, symbol: str) -> dict[str, Any]:
    end_date = resolved_end_date(config)
    raw_path = daily_csv_path(config.daily_raw_dir, symbol)
    if config.skip_existing_daily:
        complete, row_count = daily_csv_complete(raw_path, end_date=end_date)
        if complete:
            return source_event(lane="daily", symbol=symbol, source_id=f"{symbol}:1d", status="SKIPPED_EXISTS", row_count=row_count, raw_path=raw_path)
    try:
        bars = fetch_with_retries(
            provider,
            symbol=symbol,
            start_date=date.fromisoformat(config.start_date),
            end_date=date.fromisoformat(end_date),
            interval="1d",
            retry_limit=config.retry_limit,
        )
        written = write_daily_csv(config.daily_raw_dir, symbol=symbol, bars=bars)
        status = "EXPORTED" if written else "EMPTY_PROVIDER_RESPONSE"
        return source_event(lane="daily", symbol=symbol, source_id=f"{symbol}:1d", status=status, row_count=written, raw_path=raw_path)
    except Exception as exc:  # noqa: BLE001
        status, category = classify_error(exc)
        return source_event(
            lane="daily",
            symbol=symbol,
            source_id=f"{symbol}:1d",
            status=status,
            row_count=0,
            raw_path=raw_path,
            error_category=category,
            error_message=str(exc),
        )


def collect_five_min_block(
    config: BarFullBackfillConfig,
    provider: BarsProvider,
    *,
    symbol: str,
    block_start: date,
    block_end: date,
) -> dict[str, Any]:
    source_id = f"{symbol}:5m:{block_start.isoformat()}:{block_end.isoformat()}"
    try:
        bars = fetch_with_retries(
            provider,
            symbol=symbol,
            start_date=block_start,
            end_date=block_end,
            interval="5m",
            retry_limit=config.retry_limit,
        )
        inserted = upsert_market_bars(config.db_path, bars)
        status = "EXPORTED" if inserted else "EMPTY_PROVIDER_RESPONSE"
        return source_event(lane="5m", symbol=symbol, source_id=source_id, status=status, row_count=inserted, db_path=config.db_path)
    except Exception as exc:  # noqa: BLE001
        status, category = classify_error(exc)
        return source_event(
            lane="5m",
            symbol=symbol,
            source_id=source_id,
            status=status,
            row_count=0,
            db_path=config.db_path,
            error_category=category,
            error_message=str(exc),
        )


def lane_pending(lane: str, state: dict[str, Any], *, symbol_count: int, block_count: int) -> bool:
    if lane == "daily":
        return int(state.get("daily_symbol_index", 0)) < symbol_count
    if lane == "5m":
        return block_count > 0 and int(state.get("five_min_symbol_index", 0)) < symbol_count
    return False


def next_lane(config: BarFullBackfillConfig, state: dict[str, Any], *, symbol_count: int, block_count: int) -> str:
    lanes = [lane for lane in config.lanes if lane in LANES]
    if not lanes:
        raise ValueError("at least one valid lane is required")
    start = int(state.get("lane_cursor_index", 0)) % len(lanes)
    for offset in range(len(lanes)):
        index = (start + offset) % len(lanes)
        lane = lanes[index]
        if lane_pending(lane, state, symbol_count=symbol_count, block_count=block_count):
            state["lane_cursor_index"] = (index + 1) % len(lanes)
            return lane
    return ""


def advance_cursor(lane: str, state: dict[str, Any], *, block_count: int) -> None:
    if lane == "daily":
        state["daily_symbol_index"] = int(state.get("daily_symbol_index", 0)) + 1
        return
    if lane == "5m":
        next_block = int(state.get("five_min_block_index", 0)) + 1
        if next_block >= block_count:
            state["five_min_symbol_index"] = int(state.get("five_min_symbol_index", 0)) + 1
            state["five_min_block_index"] = 0
        else:
            state["five_min_block_index"] = next_block


def progress_payload(
    config: BarFullBackfillConfig,
    state: dict[str, Any],
    *,
    symbol_count: int,
    block_count: int,
    started_monotonic: float,
    processed_this_run: int,
    last_status: str,
) -> dict[str, Any]:
    daily_done = min(int(state.get("daily_symbol_index", 0)), symbol_count)
    five_min_done = min(int(state.get("five_min_symbol_index", 0)) * block_count + int(state.get("five_min_block_index", 0)), symbol_count * block_count)
    daily_total = symbol_count if "daily" in config.lanes else 0
    five_min_total = symbol_count * block_count if "5m" in config.lanes else 0
    overall_done = (daily_done if daily_total else 0) + (five_min_done if five_min_total else 0)
    overall_total = daily_total + five_min_total
    elapsed = max(time.monotonic() - started_monotonic, 0.001)
    observed_rpm = processed_this_run / elapsed * 60.0 if processed_this_run else 0.0
    remaining = max(overall_total - overall_done, 0)
    eta_hours_observed = remaining / observed_rpm / 60.0 if observed_rpm > 0 else None
    eta_hours_configured = remaining / max(int(config.requests_per_minute), 1) / 60.0 if remaining else 0.0
    payload = dict(state)
    payload.update(
        {
            "last_status": last_status,
            "processed_this_run": processed_this_run,
            "daily_progress_pct": round((daily_done / daily_total * 100.0), 4) if daily_total else 100.0,
            "five_min_progress_pct": round((five_min_done / five_min_total * 100.0), 4) if five_min_total else 100.0,
            "overall_progress_pct": round((overall_done / overall_total * 100.0), 4) if overall_total else 100.0,
            "remaining_request_units": remaining,
            "observed_requests_per_minute_this_run": round(observed_rpm, 4),
            "eta_hours_at_observed_rate": None if eta_hours_observed is None else round(eta_hours_observed, 2),
            "eta_hours_at_configured_rpm": round(eta_hours_configured, 2) if eta_hours_configured is not None else None,
            "plan_path": str(config.plan_path),
            "contract_path": str(config.contract_path),
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
            "updated_at": now_z(),
        }
    )
    return payload


def write_progress(config: BarFullBackfillConfig, payload: dict[str, Any]) -> None:
    config.progress_path.parent.mkdir(parents=True, exist_ok=True)
    config.progress_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def update_counters(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["processed_events"] = int(state.get("processed_events", 0)) + 1
    status = str(event.get("status", ""))
    if status == "EXPORTED":
        state["exported_events"] = int(state.get("exported_events", 0)) + 1
        if event.get("lane") == "daily":
            state["daily_rows_written"] = int(state.get("daily_rows_written", 0)) + int(event.get("row_count", 0))
        elif event.get("lane") == "5m":
            state["five_min_rows_written"] = int(state.get("five_min_rows_written", 0)) + int(event.get("row_count", 0))
    elif status == "EMPTY_PROVIDER_RESPONSE":
        state["empty_events"] = int(state.get("empty_events", 0)) + 1
    elif status.startswith("SKIPPED"):
        state["skipped_events"] = int(state.get("skipped_events", 0)) + 1
    elif status == "RATE_LIMITED":
        state["rate_limited_events"] = int(state.get("rate_limited_events", 0)) + 1
    else:
        state["failed_events"] = int(state.get("failed_events", 0)) + 1


def run_bar_full_backfill(
    config: BarFullBackfillConfig,
    *,
    provider: BarsProvider | None = None,
    universe_limit: int | None = None,
    smoke: bool = False,
) -> dict[str, Any]:
    total_universe = total_universe_count(config.universe_path)
    symbols = load_universe(
        config.universe_path,
        limit=universe_limit,
        offset=config.universe_offset,
        stride=config.universe_stride,
    )
    end_date = resolved_end_date(config)
    blocks = calendar_date_blocks(config.start_date, end_date, max_span_days=config.five_min_chunk_days)
    plan = build_plan(config, universe_count=len(symbols), blocks_per_symbol=len(blocks), total_universe=total_universe)
    state = load_state(config, universe_count=len(symbols), blocks_per_symbol=len(blocks))
    state["end_date"] = end_date
    state["lanes"] = list(config.lanes)
    state["universe_count"] = len(symbols)
    state["five_min_blocks_per_symbol"] = len(blocks)
    ensure_market_bars_table(config.db_path)
    active_provider = provider or AlpacaHistoricalBarsProvider()
    started = time.monotonic()
    processed_this_run = 0
    last_status = "STARTED"
    sleep_seconds = 60.0 / max(int(config.requests_per_minute), 1)
    log_line(config.log_path, f"[L0_BAR_FULL_BACKFILL_START] smoke={int(smoke)} lanes={','.join(config.lanes)}")

    while True:
        if config.stop_path.exists():
            last_status = "STOP_REQUESTED"
            break
        if config.max_requests and processed_this_run >= config.max_requests:
            last_status = "MAX_REQUESTS_REACHED"
            break
        if config.max_runtime_minutes and (time.monotonic() - started) >= config.max_runtime_minutes * 60:
            last_status = "MAX_RUNTIME_REACHED"
            break
        lane = next_lane(config, state, symbol_count=len(symbols), block_count=len(blocks))
        if not lane:
            last_status = "EXHAUSTED"
            break
        if lane == "daily":
            symbol = symbols[int(state.get("daily_symbol_index", 0))]
            event = collect_daily_symbol(config, active_provider, symbol)
        else:
            symbol = symbols[int(state.get("five_min_symbol_index", 0))]
            block_start, block_end = blocks[int(state.get("five_min_block_index", 0))]
            event = collect_five_min_block(config, active_provider, symbol=symbol, block_start=block_start, block_end=block_end)
        append_event(config.event_path, event)
        processed_this_run += 1
        last_status = str(event.get("status", ""))
        update_counters(state, event)
        if last_status != "RATE_LIMITED":
            advance_cursor(lane, state, block_count=len(blocks))
        save_state(config.state_path, state)
        write_progress(
            config,
            progress_payload(
                config,
                state,
                symbol_count=len(symbols),
                block_count=len(blocks),
                started_monotonic=started,
                processed_this_run=processed_this_run,
                last_status=last_status,
            ),
        )
        if smoke:
            break
        time.sleep(sleep_seconds if last_status != "RATE_LIMITED" else max(sleep_seconds, 60.0))

    result = {
        "status": last_status,
        "processed_this_run": processed_this_run,
        "state_path": str(config.state_path),
        "event_path": str(config.event_path),
        "progress_path": str(config.progress_path),
        "plan_path": str(config.plan_path),
        "contract_path": str(config.contract_path),
        "daily_raw_dir": str(config.daily_raw_dir),
        "db_path": str(config.db_path),
        "permissions_closed": True,
        "plan": plan,
    }
    write_progress(
        config,
        progress_payload(
            config,
            state,
            symbol_count=len(symbols),
            block_count=len(blocks),
            started_monotonic=started,
            processed_this_run=processed_this_run,
            last_status=last_status,
        )
        | result,
    )
    log_line(config.log_path, f"[L0_BAR_FULL_BACKFILL_EXIT] {json.dumps(result, sort_keys=True)}")
    return result


def market_bars_5m_row_count(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    con = sqlite3.connect(db_path)
    try:
        table_exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='market_bars_5m'").fetchone()
        if not table_exists:
            return 0
        return int(con.execute("SELECT COUNT(*) FROM market_bars_5m").fetchone()[0])
    finally:
        con.close()
