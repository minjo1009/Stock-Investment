from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.microstructure_background_collector import (  # noqa: E402
    DEFAULT_CHECKPOINT_PATH,
    DEFAULT_CHUNK_MINUTES,
    DEFAULT_EVENT_PATH,
    DEFAULT_FEED,
    DEFAULT_LOG_PATH,
    DEFAULT_PROGRESS_PATH,
    DEFAULT_RAW_DIR,
    DEFAULT_START_DATE,
    DEFAULT_STATE_PATH,
    DEFAULT_STOP_PATH,
    DEFAULT_UNIVERSE_PATH,
    CollectorConfig,
    latest_complete_market_date,
    run_collector,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resumable L0 Alpaca historical microstructure background collector. "
            "Writes chunked raw quote/trade CSVs without enabling feature builders or broker mutations."
        )
    )
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_UNIVERSE_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--checkpoint-path", type=Path, default=DEFAULT_CHECKPOINT_PATH)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--feed", choices=["iex", "sip"], default=DEFAULT_FEED)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=latest_complete_market_date())
    parser.add_argument("--direction", choices=["backward", "forward"], default="backward")
    parser.add_argument("--chunk-minutes", type=int, default=DEFAULT_CHUNK_MINUTES)
    parser.add_argument("--requests-per-minute", type=int, default=60)
    parser.add_argument("--max-chunks", type=int, default=0, help="0 means keep running until stopped or exhausted.")
    parser.add_argument("--max-runtime-minutes", type=int, default=0, help="0 means no runtime cap.")
    parser.add_argument("--universe-limit", type=int, help="Testing only: cap the universe before collection.")
    parser.add_argument("--include-existing-symbols", action="store_true", help="Do not skip source_type/symbol pairs already present under raw roots.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = CollectorConfig(
        universe_path=args.universe_path,
        raw_dir=args.raw_dir,
        checkpoint_path=args.checkpoint_path,
        state_path=args.state_path,
        event_path=args.event_path,
        progress_path=args.progress_path,
        stop_path=args.stop_path,
        log_path=args.log_path,
        feed=args.feed,
        start_date=args.start_date,
        end_date=args.end_date,
        direction=args.direction,
        chunk_minutes=args.chunk_minutes,
        requests_per_minute=args.requests_per_minute,
        max_chunks=args.max_chunks,
        max_runtime_minutes=args.max_runtime_minutes,
        skip_existing_symbols=not args.include_existing_symbols,
    )
    result = run_collector(config, universe_limit=args.universe_limit)
    print(
        "[L0_MICROSTRUCTURE_BACKGROUND_COLLECTOR] "
        f"status={result['status']} processed_this_run={result['processed_this_run']} "
        f"state_path={result['state_path']} progress_path={result['progress_path']} "
        "feature_builder_allowed_flag=0 broker_mutation_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
