from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.news_full_backfill import (  # noqa: E402
    DEFAULT_EVENT_PATH,
    DEFAULT_LOG_PATH,
    DEFAULT_OFFICIAL_BLOCKERS_PATH,
    DEFAULT_PLAN_PATH,
    DEFAULT_PROGRESS_PATH,
    DEFAULT_RAW_DIR,
    DEFAULT_STATE_PATH,
    DEFAULT_STOP_PATH,
    DEFAULT_UNIVERSE_PATH,
    GDELT_START_TS,
    SOURCE_NAMES,
    NewsFullBackfillConfig,
    run_full_backfill,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan/run L0 full news source backfill for official, GDELT, and Marketaux lanes.")
    parser.add_argument("--mode", choices=["smoke", "historical_backfill"], default="smoke")
    parser.add_argument("--sources", nargs="+", choices=list(SOURCE_NAMES), default=list(SOURCE_NAMES))
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_UNIVERSE_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--official-blockers-path", type=Path, default=DEFAULT_OFFICIAL_BLOCKERS_PATH)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--start-date", default="2016-01-01")
    parser.add_argument("--end-date", default="")
    parser.add_argument("--gdelt-start-ts", default=GDELT_START_TS)
    parser.add_argument("--gdelt-requests-per-minute", type=int, default=12)
    parser.add_argument("--marketaux-daily-cap", type=int, default=95)
    parser.add_argument("--marketaux-batch-size", type=int, default=5)
    parser.add_argument("--marketaux-window-days", type=int, default=366)
    parser.add_argument("--marketaux-limit", type=int, default=3)
    parser.add_argument("--official-refresh-hours", type=int, default=24)
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--max-runtime-minutes", type=int, default=0)
    parser.add_argument("--cycle-sleep-seconds", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = NewsFullBackfillConfig(
        universe_path=args.universe_path,
        raw_dir=args.raw_dir,
        state_path=args.state_path,
        event_path=args.event_path,
        progress_path=args.progress_path,
        stop_path=args.stop_path,
        plan_path=args.plan_path,
        official_blockers_path=args.official_blockers_path,
        log_path=args.log_path,
        start_date=args.start_date,
        end_date=args.end_date,
        sources=tuple(args.sources),
        gdelt_start_ts=args.gdelt_start_ts,
        gdelt_requests_per_minute=args.gdelt_requests_per_minute,
        marketaux_daily_cap=args.marketaux_daily_cap,
        marketaux_batch_size=args.marketaux_batch_size,
        marketaux_window_days=args.marketaux_window_days,
        marketaux_limit=args.marketaux_limit,
        official_refresh_hours=args.official_refresh_hours,
        max_requests=args.max_requests,
        max_runtime_minutes=args.max_runtime_minutes,
        cycle_sleep_seconds=args.cycle_sleep_seconds,
    )
    result = run_full_backfill(config, smoke=args.mode == "smoke")
    print(
        "[L0_NEWS_FULL_BACKFILL] "
        f"mode={args.mode} sources={','.join(args.sources)} status={result['status']} "
        f"processed_this_run={result['processed_this_run']} plan_path={result['plan_path']} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
