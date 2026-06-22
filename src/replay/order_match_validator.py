from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.replay.order_reconstruction_engine import REPORT_DIR, run_order_replay_recovery_from_db


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    summary = run_order_replay_recovery_from_db(args.db_path, args.report_dir)
    print(pd.DataFrame([summary]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
