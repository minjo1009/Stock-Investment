from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.news_background_collector import (  # noqa: E402
    DEFAULT_EVENT_PATH,
    DEFAULT_LOG_PATH,
    DEFAULT_PROGRESS_PATH,
    DEFAULT_RAW_DIR,
    DEFAULT_STATE_PATH,
    DEFAULT_STOP_PATH,
    DEFAULT_UNIVERSE_PATH,
    NewsCollectorConfig,
    run_news_collector,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run resumable L0 news source collection for official/GDELT/Marketaux lanes.")
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_UNIVERSE_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--use-full-universe", action="store_true")
    parser.add_argument("--gdelt-cooldown-minutes", type=int, default=15)
    parser.add_argument("--marketaux-batch-size", type=int, default=5)
    parser.add_argument("--max-requests-per-cycle", type=int, default=4)
    parser.add_argument("--cycle-sleep-seconds", type=int, default=60)
    parser.add_argument("--max-runtime-minutes", type=int, default=0, help="0 means keep running until stopped.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = NewsCollectorConfig(
        universe_path=args.universe_path,
        raw_dir=args.raw_dir,
        state_path=args.state_path,
        event_path=args.event_path,
        progress_path=args.progress_path,
        stop_path=args.stop_path,
        log_path=args.log_path,
        use_full_universe=args.use_full_universe,
        gdelt_cooldown_minutes=args.gdelt_cooldown_minutes,
        marketaux_batch_size=args.marketaux_batch_size,
        max_requests_per_cycle=args.max_requests_per_cycle,
        cycle_sleep_seconds=args.cycle_sleep_seconds,
        max_runtime_minutes=args.max_runtime_minutes,
    )
    result = run_news_collector(config)
    print(
        "[L0_NEWS_BACKGROUND_COLLECTOR] "
        f"status={result['status']} processed_this_run={result['processed_this_run']} "
        f"state_path={result['state_path']} progress_path={result['progress_path']} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
