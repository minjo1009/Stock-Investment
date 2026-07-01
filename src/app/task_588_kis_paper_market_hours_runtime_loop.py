from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

from .paper_runtime_common import append_registry_rows, utc_now, write_csv, write_task_report
from .task_583_live_signal_refresh_repair import run_task583
from .task_584_runtime_strategy_decision_gate import run_task584
from .task_585_kis_paper_order_execution import run_task585
from .task_587_slack_trading_report_integration import run_task587


REPORT_DIR = Path("docs/reports/task_588_kis_paper_market_hours_runtime_loop")


def _first(frame: pd.DataFrame) -> dict[str, Any]:
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _build_catalog_only() -> tuple[int, str, str]:
    env = {**os.environ}
    src_path = str(Path("src").resolve())
    env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, "scripts/build_trader_terminal_catalog.py", "--paper-ops-only"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=180,
        env=env,
    )
    return int(proc.returncode), proc.stdout[-1000:], proc.stderr[-1000:]


def _iteration(*, db_path: Path, env_file: Path, symbols: str, iteration: int) -> dict[str, Any]:
    started = utc_now()
    row: dict[str, Any] = {
        "iteration": iteration,
        "started_at_utc": started,
        "finished_at_utc": "",
        "exception": "",
    }
    try:
        task583 = run_task583(db_path=db_path, env_file=env_file, symbols=symbols)
        task584 = run_task584(db_path=db_path)
        task585 = run_task585(db_path=db_path, env_file=env_file)
        task587 = run_task587(env_file=env_file)
        d583 = _first(task583["task_583_decision.csv"])
        d584 = _first(task584["task_584_decision.csv"])
        d585 = _first(task585["task_585_decision.csv"])
        d587 = _first(task587["task_587_decision.csv"])
        active_refresh = task585.get("paper_active_order_status_refresh.csv", pd.DataFrame())
        active_broker_truth_fills = 0
        if not active_refresh.empty and "broker_truth_fill_flag" in active_refresh.columns:
            active_broker_truth_fills = int(pd.to_numeric(active_refresh["broker_truth_fill_flag"], errors="coerce").fillna(0).sum())
        lineage = task585.get("paper_order_fill_lineage.csv", pd.DataFrame())
        confirmed_broker_truth_fills = 0
        if not lineage.empty and "broker_truth_fill_flag" in lineage.columns:
            confirmed_broker_truth_fills = int(pd.to_numeric(lineage["broker_truth_fill_flag"], errors="coerce").fillna(0).sum())
        row.update(
            {
                "task583_status": d583.get("decision_status", ""),
                "fresh_rows": d583.get("fresh_rows", 0),
                "paper_order_candidate_rows": d583.get("paper_order_candidate_rows", 0),
                "task584_status": d584.get("decision_status", ""),
                "runtime_decision_id": d584.get("runtime_decision_id", ""),
                "symbol": d584.get("symbol", ""),
                "reason_code": d584.get("reason_code", ""),
                "task585_status": d585.get("decision_status", ""),
                "order_status": d585.get("order_status", ""),
                "orders_submitted": d585.get("orders_submitted", 0),
                "broker_truth_fill_count": d585.get("broker_truth_fill_count", 0),
                "active_broker_truth_fill_count": active_broker_truth_fills,
                "confirmed_broker_truth_fill_total": confirmed_broker_truth_fills,
                "task587_status": d587.get("decision_status", ""),
                "catalog_returncode": "",
                "catalog_stdout_tail": "",
                "catalog_stderr_tail": "",
            }
        )
    except Exception as exc:  # pragma: no cover - runtime protection path.
        row["exception"] = str(exc)
    row["finished_at_utc"] = utc_now()
    return row


def run_task588(
    *,
    db_path: Path,
    env_file: Path,
    symbols: str = "",
    iterations: int = 1,
    interval_seconds: int = 60,
) -> dict[str, pd.DataFrame]:
    os.environ["TRADING_MAX_OPEN_ORDERS"] = os.environ.get("TRADING_MAX_OPEN_ORDERS", "1") or "1"
    rows: list[dict[str, Any]] = []
    for idx in range(1, max(1, int(iterations)) + 1):
        rows.append(_iteration(db_path=db_path, env_file=env_file, symbols=symbols, iteration=idx))
        _write_loop_artifacts(rows, partial=True)
        catalog_code, catalog_stdout, catalog_stderr = _build_catalog_only()
        rows[-1].update(
            {
                "catalog_returncode": catalog_code,
                "catalog_stdout_tail": catalog_stdout,
                "catalog_stderr_tail": catalog_stderr,
            }
        )
        _write_loop_artifacts(rows, partial=True)
        _build_catalog_only()
        if idx < iterations:
            time.sleep(max(1, int(interval_seconds)))
    return _write_loop_artifacts(rows, partial=False)


def _write_loop_artifacts(rows: list[dict[str, Any]], *, partial: bool) -> dict[str, pd.DataFrame]:
    loop_log = pd.DataFrame(rows)
    latest = loop_log.tail(1).copy()
    submitted = int(pd.to_numeric(loop_log.get("orders_submitted", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    active_fills = int(pd.to_numeric(loop_log.get("active_broker_truth_fill_count", pd.Series(dtype=float)), errors="coerce").fillna(0).max())
    confirmed_fills = int(pd.to_numeric(loop_log.get("confirmed_broker_truth_fill_total", pd.Series(dtype=float)), errors="coerce").fillna(0).max())
    exceptions = int(loop_log["exception"].astype(str).ne("").sum()) if "exception" in loop_log.columns else 0
    latest_status = str(latest.iloc[0].get("task585_status") or latest.iloc[0].get("task584_status") or "") if not latest.empty else "NO_LOOP"
    decision_status = "PAPER_RUNTIME_LOOP_RUNNING_OK" if exceptions == 0 else "PAPER_RUNTIME_LOOP_HAS_ERRORS"
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task588",
                "task_name": "KIS Paper Market Hours Runtime Loop",
                "decision_status": decision_status,
                "iterations": len(loop_log),
                "orders_submitted_total": submitted,
                "active_broker_truth_fill_count": active_fills,
                "confirmed_broker_truth_fill_total": confirmed_fills,
                "latest_status": latest_status,
                "exception_count": exceptions,
                "max_open_orders": os.environ.get("TRADING_MAX_OPEN_ORDERS", "1"),
                "partial_loop_active_flag": int(partial),
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
            }
        ]
    )
    artifacts = {
        "paper_runtime_loop_log.csv": loop_log,
        "paper_runtime_loop_latest_status.csv": latest,
        "task_588_decision.csv": decision,
    }
    for name, frame in artifacts.items():
        write_csv(REPORT_DIR, name, frame)
    if partial:
        return artifacts
    write_task_report(
        REPORT_DIR,
        "task_588_kis_paper_market_hours_runtime_loop.md",
        title="Task588 - KIS Paper Market Hours Runtime Loop",
        decision_summary=[
            f"decision_status={decision_status}",
            f"iterations={len(loop_log)}",
            f"orders_submitted_total={submitted}",
            "TRADING_MAX_OPEN_ORDERS defaults to 1 to prevent repeated paper orders.",
        ],
        quant_lines=[
            "The loop runs Task583 signal refresh, Task584 runtime decision, Task585 KIS paper execution, Task587 Slack report, and catalog rebuild in sequence.",
            "Order execution is guarded by Task585 active-order checks; an existing pending/submitted/partial order blocks duplicate submission.",
            "Frontend updates are driven by catalog rebuilds rather than raw CSV reads.",
        ],
        decision_maker_lines=[
            "미장 개장 중 모의투자 흐름을 반복 실행하는 운영 루프입니다.",
            "이미 미체결 주문이 있으면 새 주문을 막아 과매수를 방지합니다.",
            "프론트엔드에서는 최신 데이터, 전략 판단, 주문 상태, Slack 상태를 계속 확인할 수 있습니다.",
        ],
    )
    append_registry_rows(
        [
            {
                "task_id": "Task588",
                "title": "KIS Paper Market Hours Runtime Loop",
                "owner_team": "Execution & Risk",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "diagnostic-only",
                "data_readiness": "runtime-source",
                "parent_task": "Task587",
                "key_report": str(REPORT_DIR / "task_588_kis_paper_market_hours_runtime_loop.md"),
                "key_decision": str(REPORT_DIR / "task_588_decision.csv"),
                "key_artifacts": str(REPORT_DIR),
                "validation_command": "python -m unittest tests.test_task588_kis_paper_market_hours_runtime_loop",
                "notes": "Runs market-hours KIS paper flow with duplicate-order guard and catalog updates.",
            }
        ]
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--env-file", type=Path, default=Path("config/kis_paper.env"))
    parser.add_argument("--symbols", type=str, default="")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=60)
    args = parser.parse_args()
    artifacts = run_task588(
        db_path=args.db_path,
        env_file=args.env_file,
        symbols=args.symbols,
        iterations=args.iterations,
        interval_seconds=args.interval_seconds,
    )
    print(artifacts["task_588_decision.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
