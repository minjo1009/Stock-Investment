from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.execution.broker_truth_exit_mapper import (
    MATCHING_POLICY,
    broker_truth_exit_sources,
    map_broker_truth_exits_to_lifecycle,
    summarize_exit_mapping,
)


REPORT_DIR = Path("docs/reports/task_600_4_broker_truth_exit_lifecycle")
RUNTIME_EXIT_SOURCE = "PAPER_RUNTIME_SYNTHETIC_EXIT"
TASK_ID = "T600-4"


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


def _read_position_lifecycle(con: sqlite3.Connection) -> pd.DataFrame:
    if not _table_exists(con, "position_lifecycle"):
        return pd.DataFrame()
    return pd.read_sql_query("SELECT rowid AS lifecycle_rowid, * FROM position_lifecycle", con)


def _ensure_broker_fill_columns(con: sqlite3.Connection) -> None:
    if not _table_exists(con, "position_lifecycle"):
        return
    existing = {row[1] for row in con.execute("PRAGMA table_info(position_lifecycle)").fetchall()}
    additions = {
        "broker_fill_id": "TEXT",
        "broker_fill_timestamp": "TEXT",
        "broker_fill_price": "REAL",
    }
    for column, type_name in additions.items():
        if column not in existing:
            con.execute(f"ALTER TABLE position_lifecycle ADD COLUMN {column} {type_name}")


def _runtime_exit_count(con: sqlite3.Connection, lifecycle: pd.DataFrame) -> int:
    if _table_exists(con, "fills"):
        row = con.execute(
            """
            SELECT COUNT(*)
            FROM fills
            WHERE UPPER(COALESCE(side, '')) = 'SELL'
              AND UPPER(COALESCE(source, '')) = ?
            """,
            (RUNTIME_EXIT_SOURCE,),
        ).fetchone()
        count = int(row[0]) if row else 0
        if count > 0:
            return count
    if lifecycle.empty:
        return 0
    exit_fill = lifecycle.get("exit_fill_id", pd.Series([""] * len(lifecycle), index=lifecycle.index)).fillna("").astype(str)
    state = lifecycle.get("state", pd.Series([""] * len(lifecycle), index=lifecycle.index)).fillna("").astype(str).str.upper()
    return int((exit_fill.ne("") | state.isin({"CLOSED", "PARTIAL_EXIT"})).sum())


def _apply_broker_fill_links(con: sqlite3.Connection, mapping: pd.DataFrame) -> int:
    if mapping.empty:
        return 0
    mapped = mapping.loc[mapping["mapping_status"].astype(str).eq("MAPPED_EXACT_BROKER_TRUTH_EXIT")]
    applied = 0
    for row in mapped.to_dict(orient="records"):
        rowid = row.get("lifecycle_rowid")
        if rowid in (None, ""):
            continue
        con.execute(
            """
            UPDATE position_lifecycle
            SET broker_fill_id = ?,
                broker_fill_timestamp = ?,
                broker_fill_price = ?
            WHERE rowid = ?
            """,
            (
                row.get("broker_fill_id") or None,
                row.get("broker_fill_timestamp") or None,
                row.get("broker_fill_price"),
                int(rowid),
            ),
        )
        applied += 1
    return applied


def reconcile_exit_fill_lineage(db_path: Path | str) -> dict[str, pd.DataFrame]:
    db_path = Path(db_path)
    con = sqlite3.connect(db_path)
    try:
        _ensure_broker_fill_columns(con)
        lifecycle = _read_position_lifecycle(con)
        fills = _read_table(con, "fills")
        execution_events = _read_table(con, "paper_order_execution_events")
        broker_sources = broker_truth_exit_sources(fills, execution_events)
        mapping = map_broker_truth_exits_to_lifecycle(lifecycle, broker_sources)
        applied_count = _apply_broker_fill_links(con, mapping)
        con.commit()
        runtime_exit_count = _runtime_exit_count(con, lifecycle)
        metrics = summarize_exit_mapping(
            lifecycle,
            broker_sources,
            mapping,
            runtime_exit_count=runtime_exit_count,
        )
        summary = pd.DataFrame(
            [
                {
                    "task_id": TASK_ID,
                    "runtime_exit_count": metrics.runtime_exit_count,
                    "broker_exit_count": metrics.broker_truth_sell_fills,
                    "broker_truth_sell_fills": metrics.broker_truth_sell_fills,
                    "mapped_broker_truth_exits": metrics.mapped_broker_truth_exits,
                    "missing_broker_exit_count": metrics.missing_broker_exit_count,
                    "exit_fill_linkage_coverage": metrics.exit_fill_linkage_coverage,
                    "closed_positions_with_fill": metrics.closed_positions_with_fill,
                    "closed_position_count": metrics.closed_position_count,
                    "db_rows_updated": applied_count,
                    "current_status": _current_status(metrics),
                    "acceptance_status": metrics.acceptance_status,
                    "matching_policy": MATCHING_POLICY,
                    "inferred_matching_used_flag": 0,
                    "proximity_fallback_used_flag": 0,
                    "real_capital_status": "FORBIDDEN",
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                }
            ]
        )
        return {
            "broker_truth_exit_summary": summary,
            "broker_truth_exit_sources": broker_sources,
            "broker_truth_exit_mapping": mapping,
        }
    finally:
        con.close()


def _current_status(metrics: Any) -> str:
    if int(metrics.broker_truth_sell_fills) == 0:
        return "FAIL_BROKER_TRUTH_SELL_FILLS_ZERO"
    if metrics.acceptance_status == "PASS":
        return "PASS_BROKER_TRUTH_EXIT_LIFECYCLE_LINKED"
    return "FAIL_BROKER_TRUTH_EXIT_COVERAGE_BELOW_THRESHOLD"


def write_broker_truth_exit_reports(report_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["broker_truth_exit_summary"]
    sources = artifacts["broker_truth_exit_sources"]
    mapping = artifacts["broker_truth_exit_mapping"]
    row = summary.iloc[0].to_dict()

    _write_csv(report_dir, "broker_truth_exit_sources.csv", sources)
    _write_csv(report_dir, "broker_truth_exit_mapping.csv", mapping)
    _write_csv(
        report_dir,
        "task_600_4_decision.csv",
        pd.DataFrame(
            [
                {
                    "task_id": TASK_ID,
                    "decision_status": row["current_status"],
                    "acceptance_status": row["acceptance_status"],
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "real_capital_status": "FORBIDDEN",
                    "runtime_exit_count": row["runtime_exit_count"],
                    "broker_truth_sell_fills": row["broker_truth_sell_fills"],
                    "mapped_broker_truth_exits": row["mapped_broker_truth_exits"],
                    "missing_broker_exit_count": row["missing_broker_exit_count"],
                    "exit_fill_linkage_coverage": row["exit_fill_linkage_coverage"],
                    "closed_positions_with_fill": row["closed_positions_with_fill"],
                    "inferred_matching_used_flag": 0,
                    "next_required_task": _next_action(row),
                }
            ]
        ),
    )
    _write_csv(report_dir, "broker_truth_exit_summary.csv", summary)
    _write_report(report_dir / "broker_truth_exit_report.md", row, mapping)
    _write_manifest(report_dir)


def _write_csv(report_dir: Path, name: str, frame: pd.DataFrame) -> None:
    frame.to_csv(report_dir / name, index=False, encoding="utf-8-sig")


def _write_report(path: Path, row: dict[str, Any], mapping: pd.DataFrame) -> None:
    gaps = _remaining_gaps(row, mapping)
    lines = [
        "## Decision Summary",
        "",
        f"- Verdict: {row['acceptance_status']} ({row['current_status']})",
        "- Strategy acceptance status: NOT_ACCEPTED",
        "- Deployment readiness status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "- Real Capital: FORBIDDEN",
        f"- Key metrics: runtime_exit_count={row['runtime_exit_count']}, broker_truth_sell_fills={row['broker_truth_sell_fills']}, exit_fill_linkage_coverage={row['exit_fill_linkage_coverage']}%, closed_positions_with_fill={row['closed_positions_with_fill']}%",
        "- What changed: exit broker truth lineage mapper and reconciliation now write only broker_fill_id, broker_fill_timestamp, and broker_fill_price onto exact-matched lifecycle rows.",
        f"- Next action: {_next_action(row)}",
        "",
        "## Runtime Exit Count",
        "",
        f"- {row['runtime_exit_count']}",
        "",
        "## Broker Exit Count",
        "",
        f"- {row['broker_exit_count']}",
        "",
        "## Missing Broker Exit Count",
        "",
        f"- {row['missing_broker_exit_count']}",
        "",
        "## Exit Mapping Coverage",
        "",
        f"- mapped_broker_truth_exits={row['mapped_broker_truth_exits']}",
        f"- exit_fill_linkage_coverage={row['exit_fill_linkage_coverage']}%",
        f"- closed_positions_with_fill={row['closed_positions_with_fill']}%",
        "",
        "## Current Status",
        "",
        f"- {row['current_status']}",
        "",
        "## Coverage %",
        "",
        f"- {row['exit_fill_linkage_coverage']}%",
        "",
        "## Remaining Gaps",
        "",
    ]
    lines.extend([f"- {gap}" for gap in gaps])
    lines.extend(
        [
            "",
            "## Acceptance Impact",
            "",
            _acceptance_impact(row),
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: broker truth SELL fills are accepted only from order status or broker execution-report style sources; runtime synthetic, shadow, simulated, backtest, and position-delta fallback sources are excluded.",
            "- Exact join keys: exit_fill_id to broker_fill_id, exit_order_id to broker_order_id, or exact broker event lifecycle ID. Symbol/date/price/time proximity matching is not used.",
            "- Leakage audit: labels/outcomes do not enter assignment logic; this task only links exit fill lineage.",
            "- Split/OOS metrics: not applicable to execution lineage integration.",
            "- Failure decomposition: missing or non-unique exact broker truth links remain unmapped and are reported.",
            "- Cost/slippage stress where PnL changed: not applicable; T600-4 does not alter realized PnL or exit prices.",
            "- Remaining blockers: broker truth SELL source availability if broker_truth_sell_fills is zero.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: runtime paper exits exist, but the system now separately checks whether real broker/order-status SELL fill evidence is attached.",
            "- Why it matters: paper runtime exits cannot be treated as broker truth.",
            "- Whether this changes capital/deployment readiness: no; deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY and Real Capital remains FORBIDDEN.",
            f"- Plain-language next step: {_next_action(row)}",
            "",
            "## Artifact Manifest",
            "",
            "- broker_truth_exit_sources.csv",
            "- broker_truth_exit_mapping.csv",
            "- broker_truth_exit_summary.csv",
            "- task_600_4_decision.csv",
            "- artifact_manifest.csv",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _remaining_gaps(row: dict[str, Any], mapping: pd.DataFrame) -> list[str]:
    gaps: list[str] = []
    if int(row["broker_truth_sell_fills"]) == 0:
        gaps.append("No broker truth SELL fills are present in the current DB; runtime synthetic SELL fills were not counted as broker truth.")
    if float(row["exit_fill_linkage_coverage"]) <= 95.0:
        gaps.append("Exit fill linkage coverage is below the >95% acceptance threshold.")
    if float(row["closed_positions_with_fill"]) <= 95.0:
        gaps.append("Closed positions with broker fill coverage is below the >95% acceptance threshold.")
    if not mapping.empty and mapping["mapping_status"].astype(str).eq("NON_UNIQUE_EXACT_BROKER_TRUTH_EXIT_MATCH").any():
        gaps.append("At least one lifecycle row has non-unique exact broker truth fill candidates and was left unmapped.")
    if not gaps:
        gaps.append("No remaining T600-4 lineage gap after exact broker truth mapping.")
    return gaps


def _acceptance_impact(row: dict[str, Any]) -> str:
    if int(row["broker_truth_sell_fills"]) == 0:
        return "- FAIL: broker_truth_sell_fills == 0. No synthetic/runtime paper fill was promoted to broker truth."
    if row["acceptance_status"] == "PASS":
        return "- PASS: broker truth SELL fills exist and both coverage thresholds are above 95%."
    return "- FAIL: broker truth SELL fills exist, but exact-link coverage is below the required thresholds."


def _next_action(row: dict[str, Any]) -> str:
    if int(row["broker_truth_sell_fills"]) == 0:
        return "Ingest actual broker/order-status SELL fills, then rerun T600-4 reconciliation."
    if row["acceptance_status"] == "PASS":
        return "Proceed to reviewer audit of exact broker truth exit lineage artifacts."
    return "Resolve missing or non-unique exact broker truth exit IDs, then rerun reconciliation."


def _write_manifest(report_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for path in sorted(report_dir.iterdir()):
        if path.name == "artifact_manifest.csv" or not path.is_file():
            continue
        rows.append(
            {
                "relative_path": path.name,
                "artifact_class": _artifact_class(path.name),
                "row_count": _row_count(path),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    pd.DataFrame(rows).to_csv(report_dir / "artifact_manifest.csv", index=False, encoding="utf-8-sig")


def _artifact_class(name: str) -> str:
    if name.endswith(".md"):
        return "report"
    if "decision" in name:
        return "decision"
    return "small_table"


def _row_count(path: Path) -> int | str:
    if path.suffix.lower() != ".csv":
        return ""
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = reconcile_exit_fill_lineage(args.db_path)
    write_broker_truth_exit_reports(args.report_dir, artifacts)
    print(artifacts["broker_truth_exit_summary"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
