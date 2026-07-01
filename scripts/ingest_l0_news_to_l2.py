from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def l1_handoff_ready(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return bool(rows) and all(
        row.get("trading_authority") == "0" and row.get("write_l2_materialization") == "0"
        for row in rows
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest L0 news collector events into canonical L2 news_event primitives.")
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--event-path", action="append", type=Path, default=[])
    parser.add_argument("--limit-per-path", type=int, default=500)
    parser.add_argument("--capture-ts", type=str, default="")
    parser.add_argument("--runtime-context", type=str, default="LIVE_INTRADAY_DIAGNOSTIC")
    parser.add_argument("--l1-handoff-candidates", type=Path, default=Path("data/artifacts/task_4133_l1_development_plan/l1_l2_handoff_candidates_sample.csv"))
    parser.add_argument("--allow-legacy-direct-l2", action="store_true")
    args = parser.parse_args()
    if not args.allow_legacy_direct_l2:
        print(
            "[L2_NEWS_INGEST_BLOCKED] legacy direct L0-to-L2 ingest is disabled by default. "
            "Run normalized L1 gates first and pass --allow-legacy-direct-l2 only for explicit diagnostic repair.",
            file=sys.stderr,
        )
        return 2
    if not l1_handoff_ready(args.l1_handoff_candidates):
        print(
            f"[L2_NEWS_INGEST_BLOCKED] L1 handoff candidate file is missing or unsafe: {args.l1_handoff_candidates}",
            file=sys.stderr,
        )
        return 2

    from src.l2.news_runtime import DEFAULT_NEWS_EVENT_PATHS, load_news_collector_events, write_news_l2_primitives

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
