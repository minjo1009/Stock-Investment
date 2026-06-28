from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.news_runtime import DEFAULT_NEWS_EVENT_PATHS, load_news_collector_events, write_news_l2_primitives
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest L0 news collector events into canonical L2 news_event primitives.")
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--event-path", action="append", type=Path, default=[])
    parser.add_argument("--limit-per-path", type=int, default=500)
    parser.add_argument("--capture-ts", type=str, default="")
    parser.add_argument("--runtime-context", type=str, default=LIVE_INTRADAY_DIAGNOSTIC)
    args = parser.parse_args()
    event_paths = args.event_path or DEFAULT_NEWS_EVENT_PATHS
    events = load_news_collector_events(event_paths, limit_per_path=args.limit_per_path)
    conn = sqlite3.connect(args.db_path)
    try:
        result = write_news_l2_primitives(
            conn,
            events=events,
            capture_ts=args.capture_ts or utc_now(),
            runtime_context=args.runtime_context,
            source_table=";".join(path.as_posix() for path in event_paths),
        )
    finally:
        conn.close()
    print(
        "[L2_NEWS_INGEST] "
        f"events={result['input_event_count']} facts={result['news_fact_count']} "
        f"context={result['runtime_context']} batch={result['news_batch_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
