from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.bar_full_backfill import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    DEFAULT_DAILY_RAW_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_EVENT_PATH,
    DEFAULT_FIVE_MIN_CHUNK_DAYS,
    DEFAULT_LOG_PATH,
    DEFAULT_PLAN_PATH,
    DEFAULT_PROGRESS_PATH,
    DEFAULT_REQUESTS_PER_MINUTE,
    DEFAULT_START_DATE,
    DEFAULT_STATE_PATH,
    DEFAULT_STOP_PATH,
    DEFAULT_UNIVERSE_PATH,
    LANES,
    BarFullBackfillConfig,
    run_bar_full_backfill,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan/run L0 full-universe daily and 5m bar backfill for L1/L2 consumption.")
    parser.add_argument("--mode", choices=["smoke", "historical_backfill"], default="smoke")
    parser.add_argument("--lanes", nargs="+", choices=list(LANES), default=list(LANES))
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_UNIVERSE_PATH)
    parser.add_argument("--daily-raw-dir", type=Path, default=DEFAULT_DAILY_RAW_DIR)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--contract-path", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default="")
    parser.add_argument("--five-min-chunk-days", type=int, default=DEFAULT_FIVE_MIN_CHUNK_DAYS)
    parser.add_argument("--requests-per-minute", type=int, default=DEFAULT_REQUESTS_PER_MINUTE)
    parser.add_argument("--retry-limit", type=int, default=3)
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--max-runtime-minutes", type=int, default=0)
    parser.add_argument("--universe-limit", type=int)
    parser.add_argument("--universe-offset", type=int, default=0)
    parser.add_argument("--universe-stride", type=int, default=1)
    parser.add_argument("--no-skip-existing-daily", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = BarFullBackfillConfig(
        universe_path=args.universe_path,
        daily_raw_dir=args.daily_raw_dir,
        db_path=args.db_path,
        state_path=args.state_path,
        event_path=args.event_path,
        progress_path=args.progress_path,
        stop_path=args.stop_path,
        plan_path=args.plan_path,
        contract_path=args.contract_path,
        log_path=args.log_path,
        start_date=args.start_date,
        end_date=args.end_date,
        lanes=tuple(args.lanes),
        five_min_chunk_days=max(int(args.five_min_chunk_days), 1),
        requests_per_minute=max(int(args.requests_per_minute), 1),
        retry_limit=max(int(args.retry_limit), 1),
        max_requests=max(int(args.max_requests), 0),
        max_runtime_minutes=max(int(args.max_runtime_minutes), 0),
        skip_existing_daily=not bool(args.no_skip_existing_daily),
        universe_offset=max(int(args.universe_offset), 0),
        universe_stride=max(int(args.universe_stride), 1),
    )
    result = run_bar_full_backfill(config, universe_limit=args.universe_limit, smoke=args.mode == "smoke")
    print(
        "[L0_BAR_FULL_BACKFILL] "
        f"mode={args.mode} lanes={','.join(args.lanes)} status={result['status']} "
        f"processed_this_run={result['processed_this_run']} progress_path={result['progress_path']} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
