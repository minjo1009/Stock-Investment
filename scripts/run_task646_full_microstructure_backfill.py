from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.data.alpaca_historical_microstructure_export import AlpacaHistoricalMicrostructureProvider
from tools.db.source_acquisition.microstructure_checkpoint import MicrostructureCheckpointStore
from tools.db.source_acquisition.microstructure_coverage import build_microstructure_coverage
from tools.db.source_acquisition.scheduler_override import DEFAULT_OVERRIDE_PATH, load_effective_scheduler_config


RAW_DIR = Path("data/raw/alpaca_historical_microstructure")


def _chunks_for_date(session_date: str, *, max_chunks: int, chunk_minutes: int) -> list[tuple[str, str]]:
    start = datetime.fromisoformat(f"{session_date}T14:30:00+00:00")
    chunks = []
    for idx in range(max(int(max_chunks), 1)):
        chunk_start = start + timedelta(minutes=idx * max(int(chunk_minutes), 1))
        chunk_end = chunk_start + timedelta(minutes=max(int(chunk_minutes), 1))
        chunks.append((chunk_start.isoformat().replace("+00:00", "Z"), chunk_end.isoformat().replace("+00:00", "Z")))
    return chunks


def _write_raw(frame: pd.DataFrame, *, feed: str, source_type: str, symbol: str, out_dir: Path) -> Path:
    path = out_dir / f"feed={feed}" / source_type / f"{symbol.upper()}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def run_backfill(
    *,
    mode: str,
    symbols: list[str],
    session_dates: list[str],
    feed: str,
    max_chunks: int,
    chunk_minutes: int,
    out_dir: Path = RAW_DIR,
    checkpoint_path: Path = MicrostructureCheckpointStore().path,
    coverage_output_dir: Path | None = None,
    dry_run: bool = True,
    force: bool = False,
) -> dict[str, int]:
    if mode not in {"smoke", "bounded_batch", "historical_backfill"}:
        raise ValueError(f"unsupported backfill mode: {mode}")
    symbol_limit = 1 if mode == "smoke" else len(symbols)
    date_limit = 1 if mode == "smoke" else len(session_dates)
    selected_symbols = [symbol.upper() for symbol in symbols[:symbol_limit]]
    selected_dates = session_dates[:date_limit]
    store = MicrostructureCheckpointStore(checkpoint_path)
    provider = None if dry_run else AlpacaHistoricalMicrostructureProvider(feed=feed)
    exported = failed = skipped = 0
    for symbol in selected_symbols:
        for session_date in selected_dates:
            for chunk_start, chunk_end in _chunks_for_date(session_date, max_chunks=max_chunks, chunk_minutes=chunk_minutes):
                for source_type in ["quotes", "trades"]:
                    if dry_run:
                        continue
                    chunk_id = store.record(
                        provider="alpaca",
                        feed=feed,
                        source_type=source_type,
                        symbol=symbol,
                        session_date=session_date,
                        chunk_start_ts=chunk_start,
                        chunk_end_ts=chunk_end,
                        status="PENDING",
                    )["chunk_id"]
                    if store.should_skip(chunk_id=chunk_id, force=force):
                        store.record(
                            provider="alpaca",
                            feed=feed,
                            source_type=source_type,
                            symbol=symbol,
                            session_date=session_date,
                            chunk_start_ts=chunk_start,
                            chunk_end_ts=chunk_end,
                            status="SKIPPED_EXISTS",
                        )
                        skipped += 1
                        continue
                    try:
                        assert provider is not None
                        frame = provider.fetch_quotes(symbol, start=chunk_start, end=chunk_end) if source_type == "quotes" else provider.fetch_trades(symbol, start=chunk_start, end=chunk_end)
                        if frame.empty:
                            status = "EMPTY_PROVIDER_RESPONSE"
                            raw_path = ""
                        else:
                            raw_path = _write_raw(frame, feed=feed, source_type=source_type, symbol=symbol, out_dir=out_dir)
                            status = "EXPORTED"
                        store.record(
                            provider="alpaca",
                            feed=feed,
                            source_type=source_type,
                            symbol=symbol,
                            session_date=session_date,
                            chunk_start_ts=chunk_start,
                            chunk_end_ts=chunk_end,
                            status=status,
                            row_count=int(len(frame)),
                            raw_path=raw_path,
                        )
                        exported += int(status == "EXPORTED")
                    except RuntimeError as exc:
                        category = "CREDENTIAL_BLOCKED" if "credential" in str(exc).lower() else "FAILED_RETRYABLE"
                        store.record(
                            provider="alpaca",
                            feed=feed,
                            source_type=source_type,
                            symbol=symbol,
                            session_date=session_date,
                            chunk_start_ts=chunk_start,
                            chunk_end_ts=chunk_end,
                            status=category,
                            error_category=category,
                            error_message=str(exc),
                        )
                        failed += 1
                    except Exception as exc:  # noqa: BLE001
                        store.record(
                            provider="alpaca",
                            feed=feed,
                            source_type=source_type,
                            symbol=symbol,
                            session_date=session_date,
                            chunk_start_ts=chunk_start,
                            chunk_end_ts=chunk_end,
                            status="FAILED_RETRYABLE",
                            error_category=type(exc).__name__,
                            error_message=str(exc),
                        )
                        failed += 1
    coverage_raw_dir = out_dir if not dry_run else Path("data/artifacts/microstructure/dry_run_raw_placeholder")
    build_microstructure_coverage(raw_dir=coverage_raw_dir, output_dir=coverage_output_dir, symbols=selected_symbols, session_dates=selected_dates)
    return {"exported": exported, "failed": failed, "skipped": skipped, "planned_chunks": len(selected_symbols) * len(selected_dates) * max_chunks * 2}


def _default_date() -> str:
    return (datetime.now(UTC) - timedelta(days=1)).date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task646-compatible microstructure quote/trade backfill with chunk checkpoints.")
    parser.add_argument("--mode", choices=["smoke", "bounded_batch", "historical_backfill"], default="smoke")
    parser.add_argument("--symbols", nargs="+")
    parser.add_argument("--session-dates", nargs="+")
    parser.add_argument("--feed", choices=["iex", "sip"])
    parser.add_argument("--max-chunks", type=int)
    parser.add_argument("--chunk-minutes", type=int)
    parser.add_argument("--out-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--checkpoint-path", type=Path, default=MicrostructureCheckpointStore().path)
    parser.add_argument("--coverage-output-dir", type=Path, default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = load_effective_scheduler_config(override_path=DEFAULT_OVERRIDE_PATH)
    job = next(job for job in config["jobs"] if job["name"] == "microstructure_backfill_batch")
    symbols = args.symbols or job.get("symbols", ["AAPL"])
    dates = args.session_dates or [_default_date()]
    feed = args.feed or str(job.get("feed", "iex"))
    max_chunks = args.max_chunks or int(job.get("max_chunks", 1))
    chunk_minutes = args.chunk_minutes or int(job.get("chunk_minutes", 1))
    result = run_backfill(
        mode=args.mode,
        symbols=symbols,
        session_dates=dates,
        feed=feed,
        max_chunks=max_chunks,
        chunk_minutes=chunk_minutes,
        out_dir=args.out_dir,
        checkpoint_path=args.checkpoint_path,
        coverage_output_dir=args.coverage_output_dir,
        dry_run=not args.execute,
        force=args.force,
    )
    print(
        "[TASK646_MICROSTRUCTURE_BACKFILL] "
        f"mode={args.mode} dry_run={not args.execute} chunk_minutes={chunk_minutes} planned_chunks={result['planned_chunks']} "
        f"exported={result['exported']} failed={result['failed']} skipped={result['skipped']} "
        "feature_builder_enabled=0 broker_mutation_permitted=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
