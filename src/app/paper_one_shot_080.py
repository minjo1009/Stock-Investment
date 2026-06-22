from __future__ import annotations

import argparse
import json
import os
import traceback
from pathlib import Path
from typing import Any

from app import run_trade_once
from src.backtest.build_source_time_capture_371 import build_source_time_capture_371
from state.store import initialize_store, list_recent_reconciliation_runs, list_recent_run_order_fill_rows


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 080 - Paper Pilot One-shot")
    lines.append("")
    lines.append(f"- execution_status: {payload['execution_status']}")
    lines.append(f"- db_path: {payload['db_path']}")
    lines.append(f"- error: {payload['error'] or '(none)'}")
    lines.append("")
    lines.append("## Recent Run Snapshot")
    recent = payload.get("recent_runs", [])
    if not recent:
        lines.append("- no run rows found")
    else:
        for row in recent[:5]:
            lines.append(
                f"- run_id={row.get('run_id')} | run_status={row.get('run_status')} | "
                f"order_id={row.get('order_id')} | order_status={row.get('order_status')} | "
                f"fill_qty={row.get('fill_quantity')} | fill_price={row.get('fill_price')}"
            )
    lines.append("")
    lines.append("## Recent Reconciliation Snapshot")
    recon = payload.get("recent_reconciliation", [])
    if not recon:
        lines.append("- no reconciliation rows found")
    else:
        for row in recon[:5]:
            lines.append(
                f"- reconciliation_id={row.get('reconciliation_id')} | status={row.get('status')} | "
                f"severity={row.get('max_severity')} | block_new_orders={row.get('block_new_orders')} | "
                f"events={row.get('event_count')}"
            )
    lines.append("")
    lines.append("## Source Capture Summary")
    source_capture = payload.get("source_capture", {})
    for key, value in source_capture.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Required Checks")
    checks = payload.get("checks", {})
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 080: Execute one-shot paper pilot and persist report")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_080/task_080_paper_one_shot.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_080/task_080_paper_one_shot.md")
    args = parser.parse_args()

    db_path = args.db_path
    initialize_store(db_path)
    err: str | None = None
    execution_status = "SUCCESS"
    try:
        run_trade_once.run()
    except Exception as exc:
        execution_status = "FAILED"
        err = f"{exc.__class__.__name__}: {exc}"
        traceback.print_exc()

    recent_runs = list_recent_run_order_fill_rows(db_path, limit=5)
    recent_recon = list_recent_reconciliation_runs(db_path, limit=5)
    unknown_exists = any(str(row.get("order_status", "")).upper() == "UNKNOWN" for row in recent_runs)
    recon_critical = any(str(row.get("max_severity", "")).upper() == "CRITICAL" for row in recent_recon)
    terminal_order_rate = 0.0
    if recent_runs:
        terminal_count = 0
        for row in recent_runs:
            status = str(row.get("order_status", "")).upper()
            if status in {"FILLED", "CANCELLED", "REJECTED", "EXPIRED"}:
                terminal_count += 1
        terminal_order_rate = terminal_count / len(recent_runs) * 100.0

    payload = {
        "execution_status": execution_status,
        "error": err,
        "db_path": db_path,
        "recent_runs": recent_runs,
        "recent_reconciliation": recent_recon,
        "source_capture": {
            str(row["metric_name"]): row["metric_value"]
            for _, row in build_source_time_capture_371(db_path).capture_fidelity.iterrows()
        },
        "checks": {
            "unknown_order_zero": not unknown_exists,
            "reconciliation_critical_mismatch_zero": not recon_critical,
            "cancel_loop_terminal_rate_pct": terminal_order_rate,
        },
    }
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"execution_status={execution_status}")
    if err:
        print(f"error={err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
