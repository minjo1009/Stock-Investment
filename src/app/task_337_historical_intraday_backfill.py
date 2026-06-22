from __future__ import annotations

import argparse
import os
from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_backfill_scope_337 import (
    DEFAULT_OUT_DIR,
    build_required_symbol_dates,
)
from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _load_frozen_behavior_state
from src.data.intraday_backfill import (
    DB_PATH,
    DEFAULT_CHUNK_DAYS,
    DEFAULT_INTERVAL,
    DEFAULT_RETRY_LIMIT,
    AlpacaHistoricalBarsProvider,
    IntradayBackfillConfig,
    covered_dates_by_symbol,
    fetch_with_retries,
    record_data_collection_event,
    split_contiguous_date_blocks,
    upsert_market_bars,
)


DEFAULT_SCOPE_CSV = DEFAULT_OUT_DIR / "task_337_required_symbol_dates.csv"


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _load_scope_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
    else:
        _, _, full_df = _load_frozen_behavior_state()
        full_df = full_df[full_df["scope"] == "full_period"].copy().reset_index(drop=True)
        df = build_required_symbol_dates(full_df)
    if df.empty:
        return pd.DataFrame(columns=["symbol", "trade_date", "scope", "scenario", "trade_count_on_date"])
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return df.dropna(subset=["trade_date"]).reset_index(drop=True)


def _subset_scope(df: pd.DataFrame, *, symbols: list[str] | None, start_date: str | None, end_date: str | None) -> pd.DataFrame:
    out = df.copy()
    if symbols:
        allowed = {str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()}
        out = out[out["symbol"].isin(allowed)].copy()
    if start_date:
        out = out[out["trade_date"] >= start_date].copy()
    if end_date:
        out = out[out["trade_date"] <= end_date].copy()
    return out.sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def _build_plan(scope_df: pd.DataFrame, *, db_path: Path, chunk_days: int, skip_existing: bool) -> tuple[list[dict[str, object]], dict[str, int]]:
    covered = covered_dates_by_symbol(db_path) if skip_existing else {}
    planned: list[dict[str, object]] = []
    already_covered = 0
    missing_dates = 0

    for symbol, scoped in scope_df.groupby("symbol"):
        raw_dates = [pd.to_datetime(v).date() for v in scoped["trade_date"].tolist()]
        pending_dates = []
        covered_dates = covered.get(str(symbol), set())
        for d in raw_dates:
            if d.strftime("%Y-%m-%d") in covered_dates:
                already_covered += 1
                continue
            pending_dates.append(d)
        missing_dates += len(pending_dates)
        for block_start, block_end in split_contiguous_date_blocks(pending_dates, max_span_days=chunk_days):
            planned.append(
                {
                    "symbol": str(symbol),
                    "start_date": block_start.isoformat(),
                    "end_date": block_end.isoformat(),
                    "requested_trade_dates": sum(block_start <= d <= block_end for d in pending_dates),
                }
            )

    summary = {
        "required_symbol_dates": int(len(scope_df)),
        "already_covered_dates": int(already_covered),
        "missing_coverage_dates": int(missing_dates),
        "planned_requests": int(len(planned)),
    }
    return planned, summary


def _provider_from_name(name: str):
    provider_name = str(name).strip().lower()
    if provider_name != "alpaca":
        raise ValueError(f"unsupported provider: {name}")
    return AlpacaHistoricalBarsProvider()


def _run_backfill(config: IntradayBackfillConfig, scope_df: pd.DataFrame, *, dry_run: bool) -> None:
    planned, summary = _build_plan(scope_df, db_path=config.db_path, chunk_days=config.chunk_days, skip_existing=config.skip_existing)
    print(
        f"[TASK337 PLAN] required={summary['required_symbol_dates']} covered={summary['already_covered_dates']} "
        f"missing={summary['missing_coverage_dates']} requests={summary['planned_requests']}"
    )
    for row in planned:
        print(f"[TASK337 REQUEST] {row['symbol']} {row['start_date']} -> {row['end_date']} dates={row['requested_trade_dates']}")
    if dry_run:
        return

    provider = _provider_from_name(config.provider_name)
    record_data_collection_event(config.db_path, symbol="TASK337", level="INFO", message="historical intraday backfill started")
    for row in planned:
        symbol = str(row["symbol"])
        start = date.fromisoformat(str(row["start_date"]))
        end = date.fromisoformat(str(row["end_date"]))
        try:
            bars = fetch_with_retries(
                provider,
                symbol=symbol,
                start_date=start,
                end_date=end,
                interval=config.interval,
                retry_limit=config.retry_limit,
            )
            inserted = upsert_market_bars(config.db_path, bars)
            record_data_collection_event(
                config.db_path,
                symbol=symbol,
                level="INFO",
                message=f"task337 chunk success {start.isoformat()}->{end.isoformat()} inserted={inserted}",
            )
            print(f"[TASK337 OK] {symbol} {start.isoformat()} -> {end.isoformat()} inserted={inserted}")
        except Exception as exc:  # noqa: BLE001
            record_data_collection_event(
                config.db_path,
                symbol=symbol,
                level="ERROR",
                message=f"task337 chunk failure {start.isoformat()}->{end.isoformat()} error={exc}",
            )
            print(f"[TASK337 ERROR] {symbol} {start.isoformat()} -> {end.isoformat()} error={exc}")
    record_data_collection_event(config.db_path, symbol="TASK337", level="INFO", message="historical intraday backfill completed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 337: historical intraday backfill.")
    parser.add_argument("--db-path", default=os.environ.get("TRADING_DB_PATH", str(DB_PATH)))
    parser.add_argument("--provider", default="alpaca")
    parser.add_argument("--interval", default=DEFAULT_INTERVAL)
    parser.add_argument("--scope-csv", default=str(DEFAULT_SCOPE_CSV))
    parser.add_argument("--symbols", nargs="*")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--chunk-days", type=int, default=DEFAULT_CHUNK_DAYS)
    parser.add_argument("--retry-limit", type=int, default=DEFAULT_RETRY_LIMIT)
    parser.add_argument("--skip-existing", default="true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    scope_df = _load_scope_csv(Path(args.scope_csv))
    scope_df = _subset_scope(scope_df, symbols=args.symbols, start_date=args.start_date, end_date=args.end_date)
    config = IntradayBackfillConfig(
        provider_name=str(args.provider).strip().lower(),
        db_path=Path(args.db_path),
        interval=args.interval,
        symbols=tuple(sorted(scope_df["symbol"].unique().tolist())),
        start_date=date.fromisoformat(scope_df["trade_date"].min()) if not scope_df.empty else date.today(),
        end_date=date.fromisoformat(scope_df["trade_date"].max()) if not scope_df.empty else date.today(),
        chunk_days=max(int(args.chunk_days), 1),
        retry_limit=max(int(args.retry_limit), 1),
        skip_existing=_parse_bool(args.skip_existing),
    )
    _run_backfill(config, scope_df, dry_run=bool(args.dry_run))


if __name__ == "__main__":
    main()

