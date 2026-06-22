from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from statistics import mean, median
from typing import Any


REQUIRED_ENV = (
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
    "KIS_ACCOUNT_NUMBER",
    "KIS_PRODUCT_CODE",
)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _q(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    con.row_factory = sqlite3.Row
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def _safe_ratio(n: float, d: float) -> float:
    return (n / d * 100.0) if d else 0.0


def _compute_realized_metrics(fill_rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Average-cost realized pnl per symbol using broker-truth fills only.
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for row in fill_rows:
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        by_symbol.setdefault(symbol, []).append(row)
    realized_pnls: list[float] = []
    for symbol, rows in by_symbol.items():
        rows_sorted = sorted(rows, key=lambda r: str(r.get("filled_at") or ""))
        qty = 0.0
        avg_cost = 0.0
        for r in rows_sorted:
            side = str(r.get("side") or "").upper()
            fill_qty = float(r.get("filled_quantity") or 0.0)
            fill_px = r.get("fill_price")
            if fill_qty <= 0 or fill_px is None:
                continue
            px = float(fill_px)
            if side == "BUY":
                new_qty = qty + fill_qty
                if new_qty <= 0:
                    continue
                avg_cost = ((qty * avg_cost) + (fill_qty * px)) / new_qty
                qty = new_qty
            elif side == "SELL":
                close_qty = min(qty, fill_qty)
                if close_qty > 0:
                    realized_pnls.append((px - avg_cost) * close_qty)
                    qty -= close_qty
                if qty <= 1e-9:
                    qty = 0.0
                    avg_cost = 0.0
    if not realized_pnls:
        return {
            "trade_count": 0,
            "real_pf": None,
            "real_net_pnl": None,
            "real_mdd": None,
            "real_sharpe": None,
            "series": [],
        }
    gross_win = sum(x for x in realized_pnls if x > 0)
    gross_loss = -sum(x for x in realized_pnls if x < 0)
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    net = sum(realized_pnls)
    equity = 0.0
    peak = 0.0
    mdd = 0.0
    for pnl in realized_pnls:
        equity += pnl
        peak = max(peak, equity)
        mdd = max(mdd, peak - equity)
    avg = mean(realized_pnls)
    variance = mean([(x - avg) ** 2 for x in realized_pnls]) if len(realized_pnls) > 1 else 0.0
    std = variance ** 0.5
    sharpe = (avg / std) * (len(realized_pnls) ** 0.5) if std > 0 else 0.0
    return {
        "trade_count": len(realized_pnls),
        "real_pf": pf,
        "real_net_pnl": net,
        "real_mdd": mdd,
        "real_sharpe": sharpe,
        "series": realized_pnls,
    }


def _decision(
    *,
    precondition_ok: bool,
    real_pf: float | None,
    fill_rate: float,
    avg_slippage: float | None,
) -> tuple[str, str]:
    if not precondition_ok:
        return "FAIL", "NO"
    if real_pf is None:
        return "WARNING", "WARNING"
    slippage_ok = (avg_slippage is None) or (avg_slippage <= 0.003)
    fill_stable = fill_rate >= 50.0
    if real_pf >= 1.1 and slippage_ok and fill_stable:
        return "PASS", "YES"
    if real_pf >= 1.0:
        return "WARNING", "WARNING"
    return "FAIL", "NO"


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 082 - Paper Trading Validation & Reality Gap Analysis")
    lines.append("")
    lines.append("## execution summary")
    es = payload["execution_summary"]
    lines.append(f"- total_orders: {es['total_orders']}")
    lines.append(f"- fill_rate: {es['fill_rate_pct']:.2f}%")
    lines.append(f"- cancel_rate: {es['cancel_rate_pct']:.2f}%")
    lines.append(f"- timeout_count: {es['timeout_count']}")
    lines.append(f"- partial_fill_count: {es['partial_fill_count']}")
    lines.append(f"- cancel_failure_count: {es['cancel_failure_count']}")
    lines.append("")
    lines.append("## backtest vs real comparison")
    cmp = payload["backtest_vs_real"]
    lines.append(f"- backtest_pf_s4: {cmp['backtest_pf_s4']}")
    lines.append(f"- real_pf: {cmp['real_pf']}")
    lines.append(f"- backtest_net_pnl_s4: {cmp['backtest_net_pnl_s4']}")
    lines.append(f"- real_net_pnl: {cmp['real_net_pnl']}")
    lines.append(f"- backtest_mdd_s4: {cmp['backtest_mdd_s4']}")
    lines.append(f"- real_mdd: {cmp['real_mdd']}")
    lines.append(f"- backtest_sharpe_s4: {cmp['backtest_sharpe_s4']}")
    lines.append(f"- real_sharpe: {cmp['real_sharpe']}")
    lines.append(f"- fill_rate_gap_pctp: {cmp['fill_rate_gap_pctp']}")
    lines.append("")
    lines.append("## slippage analysis")
    sl = payload["slippage_analysis"]
    lines.append(f"- sample_count: {sl['sample_count']}")
    lines.append(f"- avg: {sl['avg']}")
    lines.append(f"- median: {sl['median']}")
    lines.append(f"- max: {sl['max']}")
    lines.append(f"- note: {sl['note']}")
    lines.append("")
    lines.append("## failure cases")
    fc = payload["failure_cases"]
    lines.append(f"- timeout: {fc['timeout']}")
    lines.append(f"- partial_fill: {fc['partial_fill']}")
    lines.append(f"- cancel_failure: {fc['cancel_failure']}")
    lines.append(f"- unknown_status: {fc['unknown_status']}")
    lines.append("")
    lines.append("## gap analysis")
    for g in payload["gap_analysis"]:
        lines.append(f"- {g}")
    lines.append("")
    lines.append("## final decision")
    lines.append(f"- status: {payload['final_decision']['status']}")
    lines.append(f"- critical_answer: {payload['final_decision']['critical_answer']}")
    lines.append(f"- reason: {payload['final_decision']['reason']}")
    if payload.get("precondition", {}).get("missing_env"):
        lines.append(f"- missing_env: {payload['precondition']['missing_env']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 082: Paper Trading Validation & Reality Gap Analysis")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--run-paper-steps", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--task077-json", type=str, default="docs/reports/task_077/task_077_gate_revalidation.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_082/task_082_paper_validation.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_082/task_082_paper_validation.md")
    args = parser.parse_args()

    missing_env = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    precondition_ok = len(missing_env) == 0

    step_runs: dict[str, Any] = {"paper_one_shot_080": "SKIPPED", "paper_eod_review_081": "SKIPPED"}
    if args.run_paper_steps and precondition_ok:
        base_cmd = [sys.executable, "-m"]
        cmd_080 = base_cmd + ["app.paper_one_shot_080", "--db-path", args.db_path]
        r080 = subprocess.run(cmd_080, capture_output=True, text=True, check=False)
        step_runs["paper_one_shot_080"] = {
            "returncode": r080.returncode,
            "stdout": r080.stdout[-2000:],
            "stderr": r080.stderr[-2000:],
        }
        cmd_081 = base_cmd + ["app.paper_eod_review_081", "--db-path", args.db_path]
        r081 = subprocess.run(cmd_081, capture_output=True, text=True, check=False)
        step_runs["paper_eod_review_081"] = {
            "returncode": r081.returncode,
            "stdout": r081.stdout[-2000:],
            "stderr": r081.stderr[-2000:],
        }

    con = sqlite3.connect(args.db_path)
    try:
        run_rows = _q(
            con,
            """
            SELECT tr.run_id, tr.started_at AS signal_time, tr.result_status AS run_status,
                   o.order_id, o.symbol, o.side, o.quantity AS requested_qty,
                   o.submitted_at AS order_submit_time, o.status AS order_status
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
            SELECT f.order_id, f.symbol, f.side, f.filled_quantity, f.fill_price, f.filled_at
            FROM fills f
            ORDER BY f.filled_at DESC
            LIMIT ?
            """,
            (args.limit * 3,),
        )
        recon_rows = _q(
            con,
            "SELECT status, max_severity FROM reconciliation_runs ORDER BY started_at DESC LIMIT ?",
            (args.limit,),
        )
    finally:
        con.close()

    fill_by_order: dict[str, list[dict[str, Any]]] = {}
    for row in fill_rows:
        oid = str(row.get("order_id") or "")
        if oid:
            fill_by_order.setdefault(oid, []).append(row)

    trade_level_rows: list[dict[str, Any]] = []
    delays_sec: list[float] = []
    for row in run_rows:
        oid = str(row.get("order_id") or "")
        fills = fill_by_order.get(oid, [])
        fills_sorted = sorted(fills, key=lambda x: str(x.get("filled_at") or ""))
        first_fill = fills_sorted[0] if fills_sorted else None
        requested_price = None  # not stored in current schema
        fill_price = (float(first_fill["fill_price"]) if first_fill and first_fill.get("fill_price") is not None else None)
        slippage_real = (fill_price - requested_price) if (fill_price is not None and requested_price is not None) else None
        partial_fill = False
        if row.get("requested_qty") is not None and fills_sorted:
            total_fill_qty = sum(float(f.get("filled_quantity") or 0.0) for f in fills_sorted)
            req_qty = float(row.get("requested_qty") or 0.0)
            partial_fill = req_qty > 0 and 0 < total_fill_qty < req_qty
        submit = str(row.get("order_submit_time") or "")
        fill_t = str(first_fill.get("filled_at") or "") if first_fill else ""
        delay = None
        if submit and fill_t:
            try:
                s = submit.replace("Z", "+00:00")
                f = fill_t.replace("Z", "+00:00")
                delay = (float(__import__("datetime").datetime.fromisoformat(f).timestamp()) -
                         float(__import__("datetime").datetime.fromisoformat(s).timestamp()))
            except Exception:
                delay = None
        if delay is not None:
            delays_sec.append(delay)

        trade_level_rows.append(
            {
                "run_id": row.get("run_id"),
                "signal_time": row.get("signal_time"),
                "order_submit_time": row.get("order_submit_time"),
                "fill_time": first_fill.get("filled_at") if first_fill else None,
                "fill_price": fill_price,
                "requested_price": requested_price,
                "slippage_real": slippage_real,
                "order_status": row.get("order_status"),
                "cancel_count": 1 if str(row.get("order_status") or "").upper() == "CANCELLED" else 0,
                "partial_fill": partial_fill,
            }
        )

    total_orders = sum(1 for r in run_rows if r.get("order_id"))
    filled_orders = sum(1 for r in run_rows if str(r.get("order_status") or "").upper() == "FILLED")
    cancelled_orders = sum(1 for r in run_rows if str(r.get("order_status") or "").upper() == "CANCELLED")
    timeout_count = sum(1 for r in run_rows if str(r.get("run_status") or "").upper() == "TIMEOUT")
    partial_count = sum(1 for r in trade_level_rows if bool(r.get("partial_fill")))
    unknown_status = sum(1 for r in run_rows if str(r.get("order_status") or "").upper() == "UNKNOWN")
    cancel_failure = sum(
        1 for r in run_rows
        if str(r.get("order_status") or "").upper() in {"FAILED", "UNKNOWN"}
    )
    fill_rate_pct = _safe_ratio(filled_orders, total_orders)
    cancel_rate_pct = _safe_ratio(cancelled_orders, total_orders)

    realized = _compute_realized_metrics(fill_rows)
    real_pf = realized["real_pf"]
    real_net = realized["real_net_pnl"]
    real_mdd = realized["real_mdd"]
    real_sharpe = realized["real_sharpe"]

    task077 = _load_json(Path(args.task077_json)) or {}
    s4 = (task077.get("revalidation_results") or {}).get("S4_KIS_REALISTIC", {})
    backtest_pf = s4.get("profit_factor")
    backtest_net = s4.get("net_pnl")
    backtest_mdd = s4.get("max_drawdown")
    backtest_sharpe = s4.get("sharpe")
    backtest_fill = s4.get("fill_rate")
    fill_rate_gap = (fill_rate_pct - float(backtest_fill)) if backtest_fill is not None else None

    slippage_values = [x["slippage_real"] for x in trade_level_rows if x.get("slippage_real") is not None]
    avg_slippage = mean(slippage_values) if slippage_values else None
    med_slippage = median(slippage_values) if slippage_values else None
    max_slippage = max(slippage_values) if slippage_values else None

    gap_analysis: list[str] = []
    if not precondition_ok:
        gap_analysis.append("Paper execution precondition not met (missing KIS environment variables).")
    if fill_rate_gap is not None and abs(fill_rate_gap) > 15.0:
        gap_analysis.append(f"Fill-rate drift is large: {fill_rate_gap:+.2f} percentage points vs backtest.")
    if delays_sec:
        gap_analysis.append(f"Average signal->fill delay: {mean(delays_sec):.2f} sec.")
    else:
        gap_analysis.append("No valid signal->fill delay sample found.")
    if real_pf is None:
        gap_analysis.append("Real PF/Sharpe unavailable due to insufficient realized exit samples.")
    if partial_count > 0:
        gap_analysis.append(f"Partial-fill cases detected: {partial_count}.")
    if timeout_count > 0:
        gap_analysis.append(f"Timeout cases detected: {timeout_count}.")
    if unknown_status > 0:
        gap_analysis.append(f"UNKNOWN order status detected: {unknown_status}.")

    status, answer = _decision(
        precondition_ok=precondition_ok,
        real_pf=real_pf,
        fill_rate=fill_rate_pct,
        avg_slippage=avg_slippage,
    )
    if not precondition_ok:
        reason = "Execution blocked by missing required KIS environment variables."
    elif real_pf is None:
        reason = "Execution data exists but realized PnL sample is insufficient for PF-grade validation."
    elif status == "PASS":
        reason = "Real execution quality and PF satisfy minimum gate."
    elif status == "WARNING":
        reason = "Execution is live but reality drift remains and requires continued paper validation."
    else:
        reason = "Real PF or execution stability is below required threshold."

    payload = {
        "precondition": {
            "required_env": list(REQUIRED_ENV),
            "missing_env": missing_env,
            "ok": precondition_ok,
        },
        "step_runs": step_runs,
        "execution_summary": {
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
            "fill_rate_pct": fill_rate_pct,
            "cancel_rate_pct": cancel_rate_pct,
            "fill_probability_pct": fill_rate_pct,
            "entry_delay_avg_sec": (mean(delays_sec) if delays_sec else None),
        },
        "backtest_vs_real": {
            "backtest_pf_s4": backtest_pf,
            "real_pf": real_pf,
            "backtest_net_pnl_s4": backtest_net,
            "real_net_pnl": real_net,
            "backtest_mdd_s4": backtest_mdd,
            "real_mdd": real_mdd,
            "backtest_sharpe_s4": backtest_sharpe,
            "real_sharpe": real_sharpe,
            "backtest_fill_rate_s4": backtest_fill,
            "real_fill_rate": fill_rate_pct,
            "fill_rate_gap_pctp": fill_rate_gap,
            "pnl_drift": (real_net - float(backtest_net)) if (real_net is not None and backtest_net is not None) else None,
        },
        "slippage_analysis": {
            "sample_count": len(slippage_values),
            "avg": avg_slippage,
            "median": med_slippage,
            "max": max_slippage,
            "note": "requested_price is not persisted in current schema; slippage sample may be empty.",
        },
        "failure_cases": {
            "timeout": timeout_count,
            "partial_fill": partial_count,
            "cancel_failure": cancel_failure,
            "unknown_status": unknown_status,
        },
        "gap_analysis": gap_analysis,
        "trade_level_data": trade_level_rows,
        "final_decision": {
            "status": status,
            "critical_answer": answer,
            "reason": reason,
        },
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(payload), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"decision={status}")
    print(f"critical_answer={answer}")
    if missing_env:
        print("missing_env=" + ",".join(missing_env))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
