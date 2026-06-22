from __future__ import annotations

import argparse
import threading
import time as time_module
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from src.data.alpaca_historical_microstructure_export import AlpacaHistoricalMicrostructureProvider


DEFAULT_OUT_DIR = Path("data/raw/microstructure_full")
DEFAULT_FEED = "sip"


@dataclass(frozen=True)
class FullMicrostructureBackfillResult:
    audit: pd.DataFrame


@dataclass(frozen=True)
class BackfillPartitionTask:
    symbol: str
    day: date
    chunk_id: str
    start: str
    end: str
    source_type: str


class RequestRateLimiter:
    def __init__(self, requests_per_minute: float) -> None:
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        self.min_interval_sec = 60.0 / float(requests_per_minute)
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time_module.monotonic()
            sleep_for = max(0.0, self._next_allowed - now)
            self._next_allowed = max(now, self._next_allowed) + self.min_interval_sec
        if sleep_for > 0:
            time_module.sleep(sleep_for)


_AUDIT_WRITE_LOCK = threading.Lock()


def export_full_microstructure_partitioned(
    *,
    symbols: list[str],
    start_date: str,
    end_date: str,
    feed: str = DEFAULT_FEED,
    out_dir: Path = DEFAULT_OUT_DIR,
    include_quotes: bool = True,
    include_trades: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
    audit_out: Path | None = None,
    chunk_minutes: int = 60,
    session: str = "regular",
    skip_weekends: bool = True,
    max_chunks_per_day: int | None = None,
    workers: int = 1,
    requests_per_minute: float = 150.0,
) -> FullMicrostructureBackfillResult:
    worker_count = max(int(workers), 1)
    if worker_count > 1 and not dry_run:
        return export_full_microstructure_partitioned_parallel(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            feed=feed,
            out_dir=out_dir,
            include_quotes=include_quotes,
            include_trades=include_trades,
            overwrite=overwrite,
            audit_out=audit_out,
            chunk_minutes=chunk_minutes,
            session=session,
            skip_weekends=skip_weekends,
            max_chunks_per_day=max_chunks_per_day,
            workers=worker_count,
            requests_per_minute=requests_per_minute,
        )
    provider = None if dry_run else AlpacaHistoricalMicrostructureProvider(feed=feed)
    rows: list[dict[str, object]] = []
    for task in iter_partition_tasks(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        include_quotes=include_quotes,
        include_trades=include_trades,
        chunk_minutes=chunk_minutes,
        session=session,
        skip_weekends=skip_weekends,
        max_chunks_per_day=max_chunks_per_day,
    ):
        rows.append(
            row := export_one_partition(
                provider=provider,
                symbol=task.symbol,
                day=task.day,
                chunk_id=task.chunk_id,
                start=task.start,
                end=task.end,
                feed=feed,
                source_type=task.source_type,
                out_dir=out_dir,
                overwrite=overwrite,
                dry_run=dry_run,
            )
        )
        append_audit_row(audit_out, row)
    return FullMicrostructureBackfillResult(audit=pd.DataFrame(rows))


def export_full_microstructure_partitioned_parallel(
    *,
    symbols: list[str],
    start_date: str,
    end_date: str,
    feed: str = DEFAULT_FEED,
    out_dir: Path = DEFAULT_OUT_DIR,
    include_quotes: bool = True,
    include_trades: bool = True,
    overwrite: bool = False,
    audit_out: Path | None = None,
    chunk_minutes: int = 60,
    session: str = "regular",
    skip_weekends: bool = True,
    max_chunks_per_day: int | None = None,
    workers: int = 3,
    requests_per_minute: float = 150.0,
) -> FullMicrostructureBackfillResult:
    rate_limiter = RequestRateLimiter(requests_per_minute=requests_per_minute)
    thread_state = threading.local()
    rows: list[dict[str, object]] = []

    def provider_for_thread() -> AlpacaHistoricalMicrostructureProvider:
        provider = getattr(thread_state, "provider", None)
        if provider is None:
            provider = AlpacaHistoricalMicrostructureProvider(feed=feed, request_sleep_sec=0, request_gate=rate_limiter.wait)
            thread_state.provider = provider
        return provider

    def run_task(task: BackfillPartitionTask) -> dict[str, object]:
        return export_one_partition(
            provider=provider_for_thread(),
            symbol=task.symbol,
            day=task.day,
            chunk_id=task.chunk_id,
            start=task.start,
            end=task.end,
            feed=feed,
            source_type=task.source_type,
            out_dir=out_dir,
            overwrite=overwrite,
            dry_run=False,
        )

    tasks = iter_partition_tasks(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        include_quotes=include_quotes,
        include_trades=include_trades,
        chunk_minutes=chunk_minutes,
        session=session,
        skip_weekends=skip_weekends,
        max_chunks_per_day=max_chunks_per_day,
    )
    worker_count = max(int(workers), 1)
    max_pending = worker_count * 4
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        pending: set[Future[dict[str, object]]] = set()
        for task in tasks:
            pending.add(executor.submit(run_task, task))
            if len(pending) < max_pending:
                continue
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                row = future.result()
                rows.append(row)
                append_audit_row(audit_out, row)
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                row = future.result()
                rows.append(row)
                append_audit_row(audit_out, row)
    return FullMicrostructureBackfillResult(audit=pd.DataFrame(rows))


def iter_partition_tasks(
    *,
    symbols: list[str],
    start_date: str,
    end_date: str,
    include_quotes: bool,
    include_trades: bool,
    chunk_minutes: int,
    session: str,
    skip_weekends: bool,
    max_chunks_per_day: int | None,
) -> list[BackfillPartitionTask]:
    rows: list[BackfillPartitionTask] = []
    for symbol in sorted({s.strip().upper() for s in symbols if s.strip()}):
        for day in iter_dates(start_date, end_date):
            if skip_weekends and day.weekday() >= 5:
                continue
            windows = iter_day_windows(day, chunk_minutes=chunk_minutes, session=session)
            if max_chunks_per_day is not None:
                windows = windows[: max(int(max_chunks_per_day), 0)]
            for chunk_id, start, end in windows:
                if include_quotes:
                    rows.append(BackfillPartitionTask(symbol=symbol, day=day, chunk_id=chunk_id, start=start, end=end, source_type="quotes"))
                if include_trades:
                    rows.append(BackfillPartitionTask(symbol=symbol, day=day, chunk_id=chunk_id, start=start, end=end, source_type="trades"))
    return rows


def export_one_partition(
    *,
    provider: AlpacaHistoricalMicrostructureProvider | None,
    symbol: str,
    day: date,
    chunk_id: str,
    start: str,
    end: str,
    feed: str,
    source_type: str,
    out_dir: Path,
    overwrite: bool,
    dry_run: bool,
) -> dict[str, object]:
    path = partition_path(out_dir, provider_name="alpaca", feed=feed, source_type=source_type, symbol=symbol, day=day, chunk_id=chunk_id)
    if path.exists() and not overwrite:
        return audit_row(symbol, day, chunk_id, start, end, feed, source_type, path, "SKIPPED_EXISTS", 0, "", "", "", dry_run)
    if dry_run:
        return audit_row(symbol, day, chunk_id, start, end, feed, source_type, path, "DRY_RUN", 0, start, end, "", dry_run)
    assert provider is not None
    try:
        frame = provider.fetch_quotes(symbol, start=start, end=end) if source_type == "quotes" else provider.fetch_trades(symbol, start=start, end=end)
        if not frame.empty:
            frame = frame.copy()
            frame["provider"] = "alpaca"
            frame["feed"] = feed
            frame["source_type"] = source_type
            frame["partition_symbol"] = symbol
            frame["partition_date"] = day.isoformat()
            frame["partition_chunk_id"] = chunk_id
            frame["raw_interval_start"] = start
            frame["raw_interval_end"] = end
            frame["historical_live_ready_flag"] = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)
        first_ts, last_ts = timestamp_bounds(frame, "quote_ts" if source_type == "quotes" else "trade_ts")
        return audit_row(symbol, day, chunk_id, start, end, feed, source_type, path, "EXPORTED", int(len(frame)), first_ts, last_ts, "", dry_run)
    except Exception as exc:  # noqa: BLE001
        return audit_row(symbol, day, chunk_id, start, end, feed, source_type, path, "FAILED", 0, start, end, str(exc), dry_run)


def iter_dates(start_date: str, end_date: str) -> list[date]:
    start = pd.Timestamp(start_date).date()
    end = pd.Timestamp(end_date).date()
    if end < start:
        raise ValueError("end_date must be greater than or equal to start_date")
    out = []
    current = start
    while current <= end:
        out.append(current)
        current += timedelta(days=1)
    return out


def utc_day_window(day: date) -> tuple[str, str]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    end = datetime.combine(day, time.max, tzinfo=UTC).replace(microsecond=0)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def iter_day_windows(day: date, *, chunk_minutes: int, session: str) -> list[tuple[str, str, str]]:
    chunk = max(int(chunk_minutes), 1)
    if session == "full_day":
        start_utc = datetime.combine(day, time.min, tzinfo=UTC)
        end_utc = datetime.combine(day, time.max, tzinfo=UTC).replace(microsecond=0)
    elif session == "regular":
        ny = ZoneInfo("America/New_York")
        start_utc = datetime.combine(day, time(9, 30), tzinfo=ny).astimezone(UTC)
        end_utc = datetime.combine(day, time(16, 0), tzinfo=ny).astimezone(UTC)
    else:
        raise ValueError("session must be regular or full_day")
    rows: list[tuple[str, str, str]] = []
    current = start_utc
    while current < end_utc:
        next_dt = min(current + timedelta(minutes=chunk), end_utc)
        chunk_id = f"{current.strftime('%H%M')}_{next_dt.strftime('%H%M')}"
        rows.append((chunk_id, current.isoformat().replace("+00:00", "Z"), next_dt.isoformat().replace("+00:00", "Z")))
        current = next_dt
    return rows


def partition_path(out_dir: Path, *, provider_name: str, feed: str, source_type: str, symbol: str, day: date, chunk_id: str) -> Path:
    return out_dir / f"provider={provider_name}" / f"feed={feed}" / f"type={source_type}" / f"symbol={symbol.upper()}" / f"date={day.isoformat()}" / f"chunk={chunk_id}.parquet"


def timestamp_bounds(frame: pd.DataFrame, timestamp_column: str) -> tuple[str, str]:
    if frame.empty or timestamp_column not in frame.columns:
        return "", ""
    ts = pd.to_datetime(frame[timestamp_column], utc=True, errors="coerce").dropna()
    if ts.empty:
        return "", ""
    return ts.min().isoformat().replace("+00:00", "Z"), ts.max().isoformat().replace("+00:00", "Z")


def audit_row(
    symbol: str,
    day: date,
    chunk_id: str,
    chunk_start: str,
    chunk_end: str,
    feed: str,
    source_type: str,
    path: Path,
    status: str,
    row_count: int,
    first_timestamp: str,
    last_timestamp: str,
    error: str,
    dry_run: bool,
) -> dict[str, object]:
    return {
        "provider": "alpaca",
        "feed": feed,
        "source_type": source_type,
        "symbol": symbol.upper(),
        "date": day.isoformat(),
        "chunk_id": chunk_id,
        "chunk_start": chunk_start,
        "chunk_end": chunk_end,
        "path": str(path),
        "export_status": status,
        "row_count": int(row_count),
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "error": error,
        "dry_run_flag": int(dry_run),
        "secret_value_logged_flag": 0,
        "historical_live_ready_flag": 0,
    }


def append_audit_row(path: Path | None, row: dict[str, object]) -> None:
    if path is None:
        return
    with _AUDIT_WRITE_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame([row])
        frame.to_csv(path, mode="a", header=not path.exists(), index=False, encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill full-day Alpaca quote/trade partitions for a raw microstructure data lake.")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--feed", default=DEFAULT_FEED, choices=["sip", "iex"])
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--no-quotes", action="store_true")
    parser.add_argument("--no-trades", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audit-out", type=Path)
    parser.add_argument("--chunk-minutes", type=int, default=60)
    parser.add_argument("--session", choices=["regular", "full_day"], default="regular")
    parser.add_argument("--include-weekends", action="store_true")
    parser.add_argument("--max-chunks-per-day", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--requests-per-minute", type=float, default=150.0)
    args = parser.parse_args()
    result = export_full_microstructure_partitioned(
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        feed=args.feed,
        out_dir=args.out_dir,
        include_quotes=not args.no_quotes,
        include_trades=not args.no_trades,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        audit_out=args.audit_out,
        chunk_minutes=args.chunk_minutes,
        session=args.session,
        skip_weekends=not args.include_weekends,
        max_chunks_per_day=args.max_chunks_per_day,
        workers=args.workers,
        requests_per_minute=args.requests_per_minute,
    )
    if args.audit_out and not args.audit_out.exists():
        args.audit_out.parent.mkdir(parents=True, exist_ok=True)
        result.audit.to_csv(args.audit_out, index=False, encoding="utf-8-sig")
    exported = int(result.audit["export_status"].eq("EXPORTED").sum()) if not result.audit.empty else 0
    dry = int(result.audit["export_status"].eq("DRY_RUN").sum()) if not result.audit.empty else 0
    failed = int(result.audit["export_status"].eq("FAILED").sum()) if not result.audit.empty else 0
    print(f"[FULL_MICROSTRUCTURE_BACKFILL] exported={exported} dry_run={dry} failed={failed} feed={args.feed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
