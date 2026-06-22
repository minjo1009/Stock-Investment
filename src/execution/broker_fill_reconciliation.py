from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.execution.broker_trade_lineage_builder import (
    BROKER_TRADE_LINEAGE_COLUMNS,
    TASK_ID,
    build_broker_trade_lineage,
)
from src.execution.validate_broker_trade_lineage import validate_broker_trade_lineage_db


REPORT_DIR = Path("docs/reports/task_603_6_acceptance_promotion_program/program_a_broker_truth")


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


def _ensure_broker_trade_lineage_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS broker_trade_lineage (
            lineage_id TEXT PRIMARY KEY,
            position_id TEXT,
            signal_id TEXT,
            order_id TEXT,
            broker_order_id TEXT,
            fill_id TEXT,
            broker_fill_id TEXT,
            broker_status TEXT,
            broker_fill_price REAL,
            broker_fill_timestamp TEXT,
            created_at TEXT
        )
        """
    )


def _replace_broker_trade_lineage(con: sqlite3.Connection, lineage: pd.DataFrame) -> None:
    _ensure_broker_trade_lineage_table(con)
    con.execute("DELETE FROM broker_trade_lineage")
    if lineage.empty:
        return
    rows = []
    for row in lineage.to_dict(orient="records"):
        rows.append(tuple(row.get(column) or None for column in BROKER_TRADE_LINEAGE_COLUMNS))
    placeholders = ",".join(["?"] * len(BROKER_TRADE_LINEAGE_COLUMNS))
    columns = ",".join(BROKER_TRADE_LINEAGE_COLUMNS)
    con.executemany(
        f"INSERT INTO broker_trade_lineage ({columns}) VALUES ({placeholders})",
        rows,
    )


def reconcile_broker_trade_lineage(db_path: Path | str) -> dict[str, pd.DataFrame]:
    db_path = Path(db_path)
    con = sqlite3.connect(db_path)
    try:
        position_lifecycle = _read_table(con, "position_lifecycle")
        fills = _read_table(con, "fills")
        orders = _read_table(con, "orders")
        execution_events = _read_table(con, "paper_order_execution_events")
        artifacts = build_broker_trade_lineage(position_lifecycle, fills, orders, execution_events)
        _replace_broker_trade_lineage(con, artifacts["broker_trade_lineage"])
        con.commit()
    finally:
        con.close()

    artifacts["broker_trade_lineage_validation"] = validate_broker_trade_lineage_db(db_path)
    return artifacts


def write_broker_trade_lineage_reports(report_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["broker_trade_lineage_summary"]
    validation = artifacts["broker_trade_lineage_validation"]
    lineage = artifacts["broker_trade_lineage"]
    sources = artifacts["broker_truth_sell_sources"]
    diagnostics = artifacts["broker_trade_lineage_diagnostics"]
    _write_csv(report_dir, "broker_trade_lineage.csv", lineage)
    _write_csv(report_dir, "broker_truth_sell_sources.csv", sources)
    _write_csv(report_dir, "broker_trade_lineage_diagnostics.csv", diagnostics)
    _write_csv(report_dir, "broker_trade_lineage_summary.csv", summary)
    _write_csv(report_dir, "broker_trade_lineage_validation.csv", validation)
    row = validation.iloc[0].to_dict()
    _write_trade_lineage_report(report_dir / "broker_trade_lineage_report.md", row)
    _write_fill_coverage_report(report_dir / "broker_fill_coverage_report.md", row)


def _write_csv(report_dir: Path, name: str, frame: pd.DataFrame) -> None:
    frame.to_csv(report_dir / name, index=False, encoding="utf-8-sig")


def _write_trade_lineage_report(path: Path, row: dict[str, Any]) -> None:
    lines = [
        "## Problem",
        "",
        "T603-6 Program A needs a broker_trade_lineage table that records runtime SELL trade lineage separately from broker truth. Runtime synthetic paper SELL fills must not be promoted to broker truth.",
        "",
        "## Evidence",
        "",
        f"- task_id: {TASK_ID}",
        f"- current_status: {row['current_status']}",
        f"- acceptance_status: {row['acceptance_status']}",
        f"- runtime_sell_trade_count: {row['runtime_sell_trade_count']}",
        f"- lineage_rows: {row['lineage_rows']}",
        f"- broker_truth_sell_fills: {row['broker_truth_sell_fills']}",
        f"- lineage_coverage: {row['lineage_coverage']}%",
        f"- broker_fill_linkage: {row['broker_fill_linkage']}%",
        f"- required_columns_present_flag: {row['required_columns_present_flag']}",
        f"- non_broker_truth_link_count: {row['non_broker_truth_link_count']}",
        "- table_columns: lineage_id, position_id, signal_id, order_id, broker_order_id, fill_id, broker_fill_id, broker_status, broker_fill_price, broker_fill_timestamp, created_at",
        "",
        "## Root Cause",
        "",
        _root_cause(row),
        "",
        "## Fix Candidate",
        "",
        _fix_candidate(row),
        "",
        "## Acceptance Impact",
        "",
        _acceptance_impact(row),
        "- Real Capital: FORBIDDEN",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_fill_coverage_report(path: Path, row: dict[str, Any]) -> None:
    lines = [
        "## Problem",
        "",
        "Broker fill coverage must be measured from broker/order-status SELL evidence only. Symbol, date, price, or time proximity is not accepted as linkage.",
        "",
        "## Evidence",
        "",
        f"- broker_truth_sell_fills: {row['broker_truth_sell_fills']}",
        f"- broker_fill_linked_rows: {row['broker_fill_linked_rows']}",
        f"- missing_broker_fill_count: {row['missing_broker_fill_count']}",
        f"- broker_fill_linkage: {row['broker_fill_linkage']}%",
        f"- inferred_matching_used_flag: {row['inferred_matching_used_flag']}",
        f"- proximity_fallback_used_flag: {row['proximity_fallback_used_flag']}",
        f"- non_broker_truth_link_count: {row['non_broker_truth_link_count']}",
        "",
        "## Root Cause",
        "",
        _root_cause(row),
        "",
        "## Fix Candidate",
        "",
        _fix_candidate(row),
        "",
        "## Acceptance Impact",
        "",
        _acceptance_impact(row),
        "- Strategy acceptance remains NOT_ACCEPTED; deployment remains diagnostic-only until broker truth SELL fills are available and linked.",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _root_cause(row: dict[str, Any]) -> str:
    if int(row["broker_truth_sell_fills"]) == 0:
        return "The current DB has no accepted broker truth SELL fills. Existing runtime paper SELL fills are synthetic and were left out of broker truth linkage."
    if int(row["non_broker_truth_link_count"]) > 0:
        return "At least one broker_fill_id in broker_trade_lineage is not backed by an accepted broker truth SELL source."
    if float(row["broker_fill_linkage"]) <= 95.0:
        return "Accepted broker truth SELL fills exist, but exact ID linkage does not cover enough runtime SELL trades."
    if float(row["lineage_coverage"]) <= 95.0:
        return "Runtime SELL trade rows are missing one or more local exact IDs: position_id, order_id, or fill_id."
    return "No broker truth lineage blocker remains under the T603-6 Program A acceptance metrics."


def _fix_candidate(row: dict[str, Any]) -> str:
    if int(row["broker_truth_sell_fills"]) == 0:
        return "Ingest actual broker/order-status SELL fills with exact broker_order_id, broker_fill_id, or broker event lifecycle_id, then rerun T603-6 reconciliation."
    if int(row["non_broker_truth_link_count"]) > 0:
        return "Remove non-broker-truth links and rerun exact-ID reconciliation from accepted broker truth sources only."
    if str(row["acceptance_status"]) == "PASS":
        return "Proceed to reviewer audit of the broker_trade_lineage artifacts."
    return "Resolve missing or non-unique exact broker SELL fill IDs, then rerun reconciliation and validation."


def _acceptance_impact(row: dict[str, Any]) -> str:
    if str(row["acceptance_status"]) == "PASS":
        return "- PASS: broker_truth_sell_fills > 0 and exact-ID lineage_coverage and broker_fill_linkage are above 95%."
    if int(row["broker_truth_sell_fills"]) == 0:
        return "- FAIL: broker_truth_sell_fills == 0. Synthetic runtime paper SELL fills were not promoted to broker truth."
    return "- FAIL: exact-ID broker truth linkage is below the required acceptance threshold."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = reconcile_broker_trade_lineage(args.db_path)
    write_broker_trade_lineage_reports(args.report_dir, artifacts)
    print(artifacts["broker_trade_lineage_validation"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
