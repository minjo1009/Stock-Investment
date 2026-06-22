from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from src.execution.broker_trade_lineage_builder import (
    BROKER_TRADE_LINEAGE_COLUMNS,
    broker_truth_sell_fill_sources,
    runtime_sell_trade_candidates,
    summarize_broker_trade_lineage,
)


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _read_table(con: sqlite3.Connection, table: str) -> pd.DataFrame:
    if not _table_exists(con, table):
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", con)


def validate_broker_trade_lineage_db(db_path: Path | str) -> pd.DataFrame:
    db_path = Path(db_path)
    con = sqlite3.connect(db_path)
    try:
        position_lifecycle = _read_table(con, "position_lifecycle")
        fills = _read_table(con, "fills")
        execution_events = _read_table(con, "paper_order_execution_events")
        lineage = _read_table(con, "broker_trade_lineage")
        table_present = int(_table_exists(con, "broker_trade_lineage"))
        table_columns = set(lineage.columns) if table_present else set()
    finally:
        con.close()

    candidates = runtime_sell_trade_candidates(position_lifecycle)
    broker_sources = broker_truth_sell_fill_sources(fills, execution_events)
    summary = summarize_broker_trade_lineage(candidates, broker_sources, lineage)
    row = summary.iloc[0].to_dict()
    required_columns_present = int(all(column in table_columns for column in BROKER_TRADE_LINEAGE_COLUMNS))
    non_broker_truth_link_count = _non_broker_truth_link_count(lineage, broker_sources)

    current_status = str(row["current_status"])
    acceptance_status = str(row["acceptance_status"])
    if not table_present:
        current_status = "FAIL_BROKER_TRADE_LINEAGE_TABLE_MISSING"
        acceptance_status = "FAIL"
    elif not required_columns_present:
        current_status = "FAIL_BROKER_TRADE_LINEAGE_SCHEMA_INCOMPLETE"
        acceptance_status = "FAIL"
    elif non_broker_truth_link_count > 0:
        current_status = "FAIL_NON_BROKER_TRUTH_FILL_LINKED"
        acceptance_status = "FAIL"

    row.update(
        {
            "table_present_flag": table_present,
            "required_columns_present_flag": required_columns_present,
            "non_broker_truth_link_count": non_broker_truth_link_count,
            "current_status": current_status,
            "acceptance_status": acceptance_status,
        }
    )
    return pd.DataFrame([row])


def _non_broker_truth_link_count(lineage: pd.DataFrame, broker_sources: pd.DataFrame) -> int:
    if lineage.empty or "broker_fill_id" not in lineage.columns:
        return 0
    accepted = {
        str(value).strip()
        for value in broker_sources.get("broker_fill_id", pd.Series(dtype=str)).tolist()
        if str(value).strip()
    }
    linked = lineage["broker_fill_id"].fillna("").astype(str).str.strip()
    if not accepted:
        return int(linked.ne("").sum())
    return int((linked.ne("") & ~linked.isin(accepted)).sum())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    validation = validate_broker_trade_lineage_db(args.db_path)
    print(validation.to_string(index=False))
    if args.strict and str(validation.iloc[0]["acceptance_status"]) != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
