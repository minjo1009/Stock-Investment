from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


def _q(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _safe_ratio(n: float, d: float) -> float:
    return (n / d * 100.0) if d else 0.0


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 081 - Paper Pilot EOD Review")
    lines.append("")
    lines.append(f"- db_path: {payload['db_path']}")
    lines.append(f"- review_window_runs: {payload['summary']['run_count']}")
    lines.append("")
    lines.append("## Summary")
    s = payload["summary"]
    lines.append(f"- fill_rate_pct: {s['fill_rate_pct']:.2f}")
    lines.append(f"- cancel_success_rate_pct: {s['cancel_success_rate_pct']:.2f}")
    lines.append(f"- mismatch_rate_pct: {s['mismatch_rate_pct']:.2f}")
    lines.append(f"- unknown_orders: {s['unknown_orders']}")
    lines.append(f"- avg_fill_price: {s['avg_fill_price']:.4f}")
    lines.append("")
    lines.append("## Decision")
    lines.append(f"- pilot_status: {payload['pilot_status']}")
    lines.append(f"- note: {payload['note']}")
    lines.append("")
    lines.append("## Next-Day Adjustments")
    for item in payload["next_day_actions"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 081: EOD review for paper pilot run")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_081/task_081_paper_eod_review.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_081/task_081_paper_eod_review.md")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    db_path = args.db_path
    con = sqlite3.connect(db_path)
    try:
        run_rows = _q(
            con,
            """
            SELECT tr.run_id, tr.result_status AS run_status, o.status AS order_status
            FROM trade_runs tr
            LEFT JOIN orders o ON o.run_id = tr.run_id
            ORDER BY tr.started_at DESC
            LIMIT ?
            """,
            (args.limit,),
        )
        fill_rows = _q(
            con,
            """
            SELECT fill_price, filled_quantity, source
            FROM fills
            ORDER BY filled_at DESC
            LIMIT ?
            """,
            (args.limit,),
        )
        recon_rows = _q(
            con,
            """
            SELECT status, max_severity, block_new_orders
            FROM reconciliation_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (args.limit,),
        )
    finally:
        con.close()

    run_count = len(run_rows)
    filled_count = sum(1 for r in run_rows if str(r.get("order_status", "")).upper() == "FILLED")
    cancelled_count = sum(1 for r in run_rows if str(r.get("order_status", "")).upper() == "CANCELLED")
    unknown_orders = sum(1 for r in run_rows if str(r.get("order_status", "")).upper() == "UNKNOWN")
    recon_critical = sum(1 for r in recon_rows if str(r.get("max_severity", "")).upper() == "CRITICAL")
    mismatch_count = sum(1 for r in recon_rows if str(r.get("status", "")).upper() == "MISMATCH")
    fill_prices = [float(r["fill_price"]) for r in fill_rows if r.get("fill_price") is not None]
    avg_fill_price = (sum(fill_prices) / len(fill_prices)) if fill_prices else 0.0

    summary = {
        "run_count": run_count,
        "fill_rate_pct": _safe_ratio(filled_count, run_count),
        "cancel_success_rate_pct": _safe_ratio(cancelled_count, run_count),
        "mismatch_rate_pct": _safe_ratio(mismatch_count, max(len(recon_rows), 1)),
        "unknown_orders": unknown_orders,
        "recon_critical_count": recon_critical,
        "avg_fill_price": avg_fill_price,
    }

    if unknown_orders > 0 or recon_critical > 0:
        pilot_status = "WARNING"
        note = "Unknown/critical reconciliation signals found; keep strict guard and no scale-up."
    elif summary["fill_rate_pct"] <= 0 and run_count > 0:
        pilot_status = "WARNING"
        note = "No fill observed; execution environment needs closer monitoring."
    else:
        pilot_status = "PASS"
        note = "No blocking safety signal in sampled runs."

    payload = {
        "db_path": db_path,
        "summary": summary,
        "pilot_status": pilot_status,
        "note": note,
        "next_day_actions": [
            "Keep UNKNOWN-order hard block enabled.",
            "If reconciliation critical count > 0, halt new order submissions until resolved.",
            "Track fill-rate drift and cancel-confirm loop completion on each run.",
        ],
    }
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"pilot_status={pilot_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
