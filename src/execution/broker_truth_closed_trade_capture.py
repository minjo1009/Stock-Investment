from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.execution.broker_trade_lineage_builder import (
    MATCHING_POLICY,
    broker_truth_sell_fill_sources,
    build_broker_trade_lineage,
    runtime_sell_trade_candidates,
)
from src.execution.broker_truth_exit_mapper import is_broker_truth_fill_source


TASK_ID = "T600-6"
REPORT_DIR = Path("docs/reports/task_600_6_broker_truth_closed_trade_capture")


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


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _upper(value: object) -> str:
    return _text(value).upper()


def _float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(parsed):
        return None
    return parsed


def capture_broker_truth_closed_trade_evidence(db_path: Path | str) -> dict[str, pd.DataFrame]:
    db_path = Path(db_path)
    con = sqlite3.connect(db_path)
    try:
        position_lifecycle = _read_table(con, "position_lifecycle")
        fills = _read_table(con, "fills")
        orders = _read_table(con, "orders")
        execution_events = _read_table(con, "paper_order_execution_events")
    finally:
        con.close()

    lineage_artifacts = build_broker_trade_lineage(position_lifecycle, fills, orders, execution_events)
    candidates = runtime_sell_trade_candidates(position_lifecycle)
    sources = broker_truth_sell_fill_sources(fills, execution_events)
    rejected = rejected_sell_source_rows(fills, execution_events)
    summary = summarize_closed_trade_capture(
        db_path=db_path,
        candidates=candidates,
        sources=sources,
        diagnostics=lineage_artifacts["broker_trade_lineage_diagnostics"],
        rejected_sources=rejected,
        fills=fills,
        execution_events=execution_events,
    )

    return {
        "broker_truth_closed_trade_summary": summary,
        "broker_truth_closed_trade_sources": sources,
        "broker_truth_closed_trade_mapping": lineage_artifacts["broker_trade_lineage_diagnostics"],
        "broker_truth_closed_trade_rejected_sources": rejected,
    }


def rejected_sell_source_rows(
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    execution_events: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    fill_frame = fills.copy() if isinstance(fills, pd.DataFrame) else pd.DataFrame(fills or [])
    event_frame = execution_events.copy() if isinstance(execution_events, pd.DataFrame) else pd.DataFrame(execution_events or [])
    rows: list[dict[str, Any]] = []

    if not fill_frame.empty:
        for _, row in fill_frame.iterrows():
            if _upper(row.get("side")) != "SELL":
                continue
            source = _text(row.get("source"))
            if is_broker_truth_fill_source(source):
                continue
            rows.append(
                {
                    "source_table": "fills",
                    "row_id": _text(row.get("fill_id")),
                    "order_id": _text(row.get("order_id")),
                    "symbol": _upper(row.get("symbol")),
                    "side": "SELL",
                    "source": source,
                    "broker_truth_fill_flag": "",
                    "filled_qty": _float(row.get("filled_quantity")),
                    "rejection_reason": _rejection_reason(source, broker_truth_flag=0),
                }
            )

    if not event_frame.empty:
        for _, row in event_frame.iterrows():
            if _upper(row.get("side")) != "SELL":
                continue
            source = _text(row.get("fill_confirmation_source")) or _text(row.get("reason_code"))
            broker_truth_flag = int(_float(row.get("broker_truth_fill_flag")) or 0)
            if broker_truth_flag == 1 and is_broker_truth_fill_source(source):
                continue
            rows.append(
                {
                    "source_table": "paper_order_execution_events",
                    "row_id": _text(row.get("event_id")),
                    "order_id": _text(row.get("order_id")),
                    "symbol": _upper(row.get("symbol")),
                    "side": "SELL",
                    "source": source,
                    "broker_truth_fill_flag": broker_truth_flag,
                    "filled_qty": _float(row.get("filled_qty")),
                    "rejection_reason": _rejection_reason(source, broker_truth_flag=broker_truth_flag),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "source_table",
                "row_id",
                "order_id",
                "symbol",
                "side",
                "source",
                "broker_truth_fill_flag",
                "filled_qty",
                "rejection_reason",
            ]
        )
    return pd.DataFrame(rows).sort_values(["source_table", "order_id", "row_id"]).reset_index(drop=True)


def summarize_closed_trade_capture(
    *,
    db_path: Path,
    candidates: pd.DataFrame,
    sources: pd.DataFrame,
    diagnostics: pd.DataFrame,
    rejected_sources: pd.DataFrame,
    fills: pd.DataFrame,
    execution_events: pd.DataFrame,
) -> pd.DataFrame:
    runtime_count = int(len(candidates))
    broker_truth_sell_fills = int(len(sources))
    linked_rows = 0
    missing_rows = runtime_count
    lineage_coverage = 0.0
    broker_fill_linkage = 0.0
    non_unique = 0
    if not diagnostics.empty:
        linked_rows = int(diagnostics["broker_fill_id"].fillna("").astype(str).ne("").sum())
        missing_rows = int(diagnostics["broker_fill_id"].fillna("").astype(str).eq("").sum())
        complete_local = diagnostics[["position_id", "order_id", "fill_id"]].fillna("").astype(str).ne("").all(axis=1)
        lineage_coverage = _pct(int(complete_local.sum()), runtime_count)
        broker_fill_linkage = _pct(linked_rows, runtime_count)
        non_unique = int(
            diagnostics["mapping_status"].astype(str).eq("NON_UNIQUE_EXACT_BROKER_TRUTH_SELL_FILL").sum()
            if "mapping_status" in diagnostics.columns
            else 0
        )

    rejected_count = int(len(rejected_sources))
    flag_rejected = int(
        rejected_sources["rejection_reason"].astype(str).eq("BROKER_TRUTH_FLAG_WITH_REJECTED_SOURCE").sum()
        if not rejected_sources.empty
        else 0
    )
    synthetic_sell_rows = int(
        rejected_sources["source"].astype(str).str.upper().str.contains("SYNTHETIC|PAPER_RUNTIME", regex=True).sum()
        if not rejected_sources.empty
        else 0
    )
    position_delta_sell_rows = int(
        rejected_sources["source"].astype(str).str.upper().str.contains("POSITION_DELTA").sum()
        if not rejected_sources.empty
        else 0
    )
    accepted_buy_order_status_source_rows = _accepted_buy_order_status_source_rows(fills, execution_events)
    acceptance_status = (
        "PASS"
        if broker_truth_sell_fills > 0 and lineage_coverage > 95.0 and broker_fill_linkage > 95.0
        else "FAIL"
    )
    current_status = _current_status(
        broker_truth_sell_fills=broker_truth_sell_fills,
        linked_rows=linked_rows,
        acceptance_status=acceptance_status,
    )

    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "source_db_path": db_path.as_posix(),
                "runtime_sell_trade_count": runtime_count,
                "broker_truth_sell_fills": broker_truth_sell_fills,
                "broker_fill_linked_rows": linked_rows,
                "missing_broker_fill_count": missing_rows,
                "non_unique_exact_match_count": non_unique,
                "lineage_coverage": lineage_coverage,
                "broker_fill_linkage": broker_fill_linkage,
                "rejected_sell_source_rows": rejected_count,
                "broker_truth_flag_rejected_rows": flag_rejected,
                "synthetic_sell_rows": synthetic_sell_rows,
                "position_delta_fallback_sell_rows": position_delta_sell_rows,
                "accepted_buy_order_status_source_rows": accepted_buy_order_status_source_rows,
                "current_status": current_status,
                "acceptance_status": acceptance_status,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "matching_policy": MATCHING_POLICY,
                "inferred_matching_used_flag": 0,
                "proximity_fallback_used_flag": 0,
                "real_capital_status": "FORBIDDEN",
            }
        ]
    )


def write_broker_truth_closed_trade_reports(report_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["broker_truth_closed_trade_summary"]
    sources = artifacts["broker_truth_closed_trade_sources"]
    mapping = artifacts["broker_truth_closed_trade_mapping"]
    rejected = artifacts["broker_truth_closed_trade_rejected_sources"]
    decision = _decision_frame(summary)

    _write_csv(report_dir, "broker_truth_closed_trade_summary.csv", summary)
    _write_csv(report_dir, "broker_truth_closed_trade_sources.csv", sources)
    _write_csv(report_dir, "broker_truth_closed_trade_mapping.csv", mapping)
    _write_csv(report_dir, "broker_truth_closed_trade_rejected_sources.csv", rejected)
    _write_csv(report_dir, "task_600_6_decision.csv", decision)
    _write_report(report_dir / "broker_truth_closed_trade_report.md", summary.iloc[0].to_dict())
    _write_manifest(report_dir, summary, sources, mapping, rejected, decision)


def _write_csv(report_dir: Path, name: str, frame: pd.DataFrame) -> None:
    frame.to_csv(report_dir / name, index=False, encoding="utf-8-sig")


def _decision_frame(summary: pd.DataFrame) -> pd.DataFrame:
    row = summary.iloc[0].to_dict()
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": row["current_status"],
                "strategy_acceptance_status": row["strategy_acceptance_status"],
                "deployment_status": row["deployment_status"],
                "real_capital_status": row["real_capital_status"],
                "next_action": _next_action(row),
            }
        ]
    )


def _write_report(path: Path, row: dict[str, Any]) -> None:
    lines = [
        "# T600-6 Broker Truth Closed-Trade Capture And SELL Lineage Certification",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: {row['current_status']}",
        f"- Strategy acceptance status: {row['strategy_acceptance_status']}",
        f"- Deployment readiness: {row['deployment_status']}",
        f"- Runtime SELL trade count: {row['runtime_sell_trade_count']}",
        f"- Broker-truth SELL fills: {row['broker_truth_sell_fills']}",
        f"- Broker fill linkage: {row['broker_fill_linkage']}%",
        f"- Rejected SELL source rows: {row['rejected_sell_source_rows']}",
        f"- What changed: T600-6 now inventories broker/order-status SELL evidence and rejected synthetic/fallback SELL rows without changing strategy logic.",
        f"- Next action: {_next_action(row)}",
        "",
        "## Quant Expert Report",
        "",
        f"- Data source and source readiness: source DB `{row['source_db_path']}` has {row['accepted_buy_order_status_source_rows']} accepted BUY order-status source rows but {row['broker_truth_sell_fills']} accepted SELL broker-truth fills.",
        f"- Exact join keys: {row['matching_policy']}. Accepted keys are exact broker fill ID, exact broker order ID, or exact broker event lifecycle ID.",
        "- Leakage audit: labels/outcomes do not enter assignment logic; this task only audits runtime order/fill evidence.",
        "- Split/OOS metrics: not applicable because this is execution evidence certification, not alpha validation.",
        "- Failure decomposition: synthetic/runtime SELL rows and position-delta fallback rows are reported as rejected sources, not promoted to broker truth.",
        "- Cost/slippage stress: not changed. No PnL, execution cost, or strategy claim was updated.",
        f"- Remaining blockers: broker_truth_sell_fills must be > 0 and exact linkage must exceed 95%; current status is {row['current_status']}.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- What happened: we checked whether the system has real broker/order-status evidence for closed SELL trades.",
        "- Why it matters: without broker-truth SELL fills, a profitable backtest or controlled paper closeout still cannot prove executable exits.",
        f"- Whether this changes capital/deployment readiness: no. Strategy remains `{row['strategy_acceptance_status']}`, deployment remains `{row['deployment_status']}`, and real capital remains `{row['real_capital_status']}`.",
        f"- Plain-language next step: {_next_action(row)}",
        "",
        "## Artifact Manifest",
        "",
        "- Inputs: source DB, `position_lifecycle`, `fills`, `orders`, `paper_order_execution_events`.",
        "- Outputs: `broker_truth_closed_trade_summary.csv`, `broker_truth_closed_trade_sources.csv`, `broker_truth_closed_trade_mapping.csv`, `broker_truth_closed_trade_rejected_sources.csv`, `task_600_6_decision.csv`.",
        "- Validation commands: `python -m unittest tests.test_task600_6_broker_truth_closed_trade_capture tests.test_task600_4_broker_truth_exit_lifecycle tests.test_task600_5_stop_tp_validation`.",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_manifest(
    report_dir: Path,
    summary: pd.DataFrame,
    sources: pd.DataFrame,
    mapping: pd.DataFrame,
    rejected: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    frames = {
        "broker_truth_closed_trade_summary.csv": summary,
        "broker_truth_closed_trade_sources.csv": sources,
        "broker_truth_closed_trade_mapping.csv": mapping,
        "broker_truth_closed_trade_rejected_sources.csv": rejected,
        "task_600_6_decision.csv": decision,
        "broker_truth_closed_trade_report.md": pd.DataFrame(),
    }
    rows = []
    for name, frame in frames.items():
        path = report_dir / name
        rows.append(
            {
                "artifact": path.as_posix(),
                "artifact_type": "report" if path.suffix == ".md" else "csv",
                "row_count": "" if path.suffix == ".md" else int(len(frame)),
                "file_size_bytes": path.stat().st_size if path.exists() else 0,
                "validation_command": "python -m unittest tests.test_task600_6_broker_truth_closed_trade_capture",
            }
        )
    pd.DataFrame(rows).to_csv(report_dir / "artifact_manifest.csv", index=False, encoding="utf-8-sig")


def _rejection_reason(source: str, *, broker_truth_flag: int) -> str:
    source_upper = source.upper()
    if broker_truth_flag == 1 and not is_broker_truth_fill_source(source):
        return "BROKER_TRUTH_FLAG_WITH_REJECTED_SOURCE"
    if "POSITION_DELTA" in source_upper:
        return "POSITION_DELTA_FALLBACK_NOT_BROKER_TRUTH"
    if "SYNTHETIC" in source_upper or "PAPER_RUNTIME" in source_upper:
        return "SYNTHETIC_RUNTIME_SELL_NOT_BROKER_TRUTH"
    if not source_upper:
        return "MISSING_BROKER_TRUTH_SOURCE"
    return "NON_BROKER_TRUTH_SOURCE"


def _accepted_buy_order_status_source_rows(fills: pd.DataFrame, execution_events: pd.DataFrame) -> int:
    count = 0
    if not fills.empty and {"side", "source"}.issubset(fills.columns):
        mask = fills["side"].fillna("").astype(str).str.upper().eq("BUY")
        mask &= fills["source"].fillna("").astype(str).map(is_broker_truth_fill_source)
        count += int(mask.sum())
    if not execution_events.empty and {"side", "fill_confirmation_source", "broker_truth_fill_flag"}.issubset(
        execution_events.columns
    ):
        mask = execution_events["side"].fillna("").astype(str).str.upper().eq("BUY")
        mask &= execution_events["broker_truth_fill_flag"].fillna(0).astype(int).eq(1)
        mask &= execution_events["fill_confirmation_source"].fillna("").astype(str).map(is_broker_truth_fill_source)
        count += int(mask.sum())
    return count


def _current_status(*, broker_truth_sell_fills: int, linked_rows: int, acceptance_status: str) -> str:
    if broker_truth_sell_fills == 0:
        return "FAIL_BROKER_TRUTH_SELL_SOURCE_MISSING"
    if linked_rows == 0:
        return "FAIL_BROKER_TRUTH_SELL_SOURCE_UNLINKED"
    if acceptance_status == "PASS":
        return "PASS_BROKER_TRUTH_CLOSED_TRADE_CERTIFIED"
    return "FAIL_BROKER_TRUTH_CLOSED_TRADE_INCOMPLETE"


def _next_action(row: dict[str, Any]) -> str:
    if int(row["broker_truth_sell_fills"]) == 0:
        return "Capture actual broker/order-status SELL fills from KIS status/fill polling, then rerun T600-6 and T600-4 exact reconciliation."
    if int(row["broker_fill_linked_rows"]) == 0:
        return "Repair exact broker_order_id, broker_fill_id, or broker event lifecycle_id linkage; do not use symbol/time/price proximity."
    if str(row["acceptance_status"]) == "PASS":
        return "Proceed to Data & Market Microstructure reviewer audit of the T600-6 and T600-4 artifacts."
    return "Close remaining exact-ID broker SELL gaps until linkage exceeds 95%."


def _pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = capture_broker_truth_closed_trade_evidence(args.db_path)
    write_broker_truth_closed_trade_reports(args.report_dir, artifacts)
    print(artifacts["broker_truth_closed_trade_summary"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
