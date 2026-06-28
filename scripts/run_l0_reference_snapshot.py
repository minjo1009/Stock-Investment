from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.reference_snapshot import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    DEFAULT_EVENT_PATH,
    DEFAULT_PLAN_PATH,
    DEFAULT_PROGRESS_PATH,
    DEFAULT_RAW_DIR,
    DEFAULT_START_DATE,
    DEFAULT_TRADING_BASE_URL,
    ReferenceSnapshotConfig,
    run_reference_snapshot,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture L0 reference snapshots for assets, calendar, and current market status.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--event-path", type=Path, default=DEFAULT_EVENT_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--contract-path", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default="")
    parser.add_argument("--base-url", default=DEFAULT_TRADING_BASE_URL)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    progress = run_reference_snapshot(
        ReferenceSnapshotConfig(
            raw_dir=args.raw_dir,
            progress_path=args.progress_path,
            event_path=args.event_path,
            plan_path=args.plan_path,
            contract_path=args.contract_path,
            start_date=args.start_date,
            end_date=args.end_date,
            base_url=args.base_url,
        )
    )
    print(
        "[L0_REFERENCE_SNAPSHOT] "
        f"status={progress['status']} processed={progress['processed_events']} "
        f"exported={progress['exported_events']} failed={progress['failed_events']} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
