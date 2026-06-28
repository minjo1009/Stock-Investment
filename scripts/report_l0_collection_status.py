from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.l0_collection_status import (  # noqa: E402
    DEFAULT_STATUS_JSON,
    DEFAULT_STATUS_MD,
    L0CollectionStatusConfig,
    write_status,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a consolidated L0 collection status snapshot.")
    parser.add_argument("--status-json", type=Path, default=DEFAULT_STATUS_JSON)
    parser.add_argument("--status-md", type=Path, default=DEFAULT_STATUS_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status = write_status(L0CollectionStatusConfig(status_json=args.status_json, status_md=args.status_md))
    daily = status["daily_bars"]
    five = status["five_min_bars"]
    news = status["news"]
    print(
        "[L0_COLLECTION_STATUS] "
        f"daily={daily.get('progress_pct')}% five_min={five.get('progress_pct')}% "
        f"news_processed={news.get('processed_events')} status_json={args.status_json} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
