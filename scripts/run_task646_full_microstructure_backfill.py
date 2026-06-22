from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.data.alpaca_full_microstructure_backfill import export_full_microstructure_partitioned


REPORT_DIR = Path("docs/reports/task_646_full_microstructure_data_lake")
UNIVERSE_PATH = REPORT_DIR / "task_646_universe_scope.csv"
LOG_PATH = REPORT_DIR / "task_646_full_backfill_progress.log"


def append_log(message: str, log_path: Path = LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {message}\n")


def run_full_backfill(
    *,
    universe_path: Path = UNIVERSE_PATH,
    report_dir: Path = REPORT_DIR,
    feed: str = "sip",
    start_symbol_index: int = 0,
    max_symbols: int | None = None,
    quotes_chunk_minutes: int = 10,
    trades_chunk_minutes: int = 60,
    workers: int = 3,
    requests_per_minute: float = 150.0,
) -> None:
    universe = pd.read_csv(universe_path)
    symbols = universe["symbol"].astype(str).str.upper().drop_duplicates().sort_values().tolist()
    symbols = symbols[start_symbol_index:]
    if max_symbols is not None:
        symbols = symbols[: max(int(max_symbols), 0)]
    if not symbols:
        append_log("NO_SYMBOLS_TO_BACKFILL")
        return
    start_date = str(universe["lake_start_date"].min())
    end_date = str(universe["lake_end_date"].max())
    append_log(f"START feed={feed} symbols={len(symbols)} start={start_date} end={end_date} workers={workers} requests_per_minute={requests_per_minute}")
    for ordinal, symbol in enumerate(symbols, start=start_symbol_index + 1):
        append_log(f"SYMBOL_START ordinal={ordinal} symbol={symbol}")
        quote_audit = report_dir / f"backfill_quotes_{ordinal:03d}_{symbol}.csv"
        trade_audit = report_dir / f"backfill_trades_{ordinal:03d}_{symbol}.csv"
        try:
            export_full_microstructure_partitioned(
                symbols=[symbol],
                start_date=start_date,
                end_date=end_date,
                feed=feed,
                include_quotes=True,
                include_trades=False,
                audit_out=quote_audit,
                chunk_minutes=quotes_chunk_minutes,
                session="regular",
                workers=workers,
                requests_per_minute=requests_per_minute,
            )
            append_log(f"QUOTES_DONE ordinal={ordinal} symbol={symbol} audit={quote_audit}")
        except Exception as exc:  # noqa: BLE001
            append_log(f"QUOTES_FAILED ordinal={ordinal} symbol={symbol} error={type(exc).__name__}: {exc}")
        try:
            export_full_microstructure_partitioned(
                symbols=[symbol],
                start_date=start_date,
                end_date=end_date,
                feed=feed,
                include_quotes=False,
                include_trades=True,
                audit_out=trade_audit,
                chunk_minutes=trades_chunk_minutes,
                session="regular",
                workers=workers,
                requests_per_minute=requests_per_minute,
            )
            append_log(f"TRADES_DONE ordinal={ordinal} symbol={symbol} audit={trade_audit}")
        except Exception as exc:  # noqa: BLE001
            append_log(f"TRADES_FAILED ordinal={ordinal} symbol={symbol} error={type(exc).__name__}: {exc}")
        append_log(f"SYMBOL_DONE ordinal={ordinal} symbol={symbol}")
    append_log("COMPLETE")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Task646 full microstructure backfill sequentially and resumably.")
    parser.add_argument("--universe-path", type=Path, default=UNIVERSE_PATH)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--feed", default="sip", choices=["sip", "iex"])
    parser.add_argument("--start-symbol-index", type=int, default=0)
    parser.add_argument("--max-symbols", type=int)
    parser.add_argument("--quotes-chunk-minutes", type=int, default=10)
    parser.add_argument("--trades-chunk-minutes", type=int, default=60)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--requests-per-minute", type=float, default=150.0)
    args = parser.parse_args()
    run_full_backfill(
        universe_path=args.universe_path,
        report_dir=args.report_dir,
        feed=args.feed,
        start_symbol_index=args.start_symbol_index,
        max_symbols=args.max_symbols,
        quotes_chunk_minutes=args.quotes_chunk_minutes,
        trades_chunk_minutes=args.trades_chunk_minutes,
        workers=args.workers,
        requests_per_minute=args.requests_per_minute,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
