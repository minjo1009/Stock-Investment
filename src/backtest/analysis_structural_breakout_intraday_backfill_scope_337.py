from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    FROZEN_SELECTED_CLUSTERS,
    _load_frozen_behavior_state,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_337_historical_intraday_ingestion")


def build_required_symbol_dates(full_df: pd.DataFrame) -> pd.DataFrame:
    scoped = full_df.copy()
    scoped["symbol"] = scoped["symbol"].astype(str).str.upper()
    scoped["trade_date"] = pd.to_datetime(scoped["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    scoped = scoped.dropna(subset=["trade_date"])
    grouped = (
        scoped.groupby(["symbol", "trade_date"], dropna=False)
        .agg(
            scope=("scope", "first"),
            scenario=("scenario", lambda s: "|".join(sorted({str(v) for v in s if str(v)}))),
            trade_count_on_date=("trade_id", "count") if "trade_id" in scoped.columns else ("entry_date", "count"),
        )
        .reset_index()
        .sort_values(["symbol", "trade_date"])
        .reset_index(drop=True)
    )
    return grouped


def build_symbol_summary(required_df: pd.DataFrame) -> pd.DataFrame:
    if required_df.empty:
        return pd.DataFrame(
            columns=["symbol", "required_trade_dates", "earliest_trade_date", "latest_trade_date", "total_trade_count"]
        )
    summary = (
        required_df.groupby("symbol", dropna=False)
        .agg(
            required_trade_dates=("trade_date", "nunique"),
            earliest_trade_date=("trade_date", "min"),
            latest_trade_date=("trade_date", "max"),
            total_trade_count=("trade_count_on_date", "sum"),
        )
        .reset_index()
        .sort_values("symbol")
        .reset_index(drop=True)
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 337: extract required symbol/date scope for historical intraday backfill.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--frozen-csv", default=str(FROZEN_SELECTED_CLUSTERS))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    _, _, full_df = _load_frozen_behavior_state() if str(args.frozen_csv) == str(FROZEN_SELECTED_CLUSTERS) else (None, None, pd.read_csv(args.frozen_csv))
    full_df = full_df[full_df["scope"] == "full_period"].copy().reset_index(drop=True)
    required_df = build_required_symbol_dates(full_df)
    summary_df = build_symbol_summary(required_df)

    required_df.to_csv(out_dir / "task_337_required_symbol_dates.csv", index=False)
    summary_df.to_csv(out_dir / "task_337_required_symbol_summary.csv", index=False)


if __name__ == "__main__":
    main()

