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

from src.app.paper_capture_harness_371 import run_paper_capture_harness_371
from src.backtest.build_source_time_capture_371 import build_source_time_capture_371


REQUIRED_ENV = (
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
    "KIS_ACCOUNT_NUMBER",
    "KIS_PRODUCT_CODE",
)


def _q(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    con.row_factory = sqlite3.Row
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def _safe_pct(num: float, den: float) -> float:
    return (num / den * 100.0) if den else 0.0


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _decision(
    *,
    guard_unknown_ok: bool,
    recon_critical_zero: bool,
    execution_ok: bool,
    fill_rate: float,
    timeout_rate: float,
    late_fill_count: int,
    mismatch_rate: float,
) -> tuple[str, str]:
    if not guard_unknown_ok or not recon_critical_zero:
        return "FAIL", "NO"
    if execution_ok and fill_rate >= 40.0 and timeout_rate <= 40.0 and mismatch_rate <= 5.0 and late_fill_count <= 3:
        return "PASS", "YES"
    if execution_ok:
        return "WARNING", "WARNING"
    return "FAIL", "NO"


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 085 - Paper Pilot Execution Plan & Operational Validation")
    lines.append("")
    lines.append("## 1. Execution Summary")
    es = report["execution_summary"]
    lines.append(f"- strategy: {report['pilot_config']['strategy_id']}")
    lines.append(f"- db_path: {report['db_path']}")
    lines.append(f"- total_runs: {es['total_runs']}")
    lines.append(f"- total_orders: {es['total_orders']}")
    lines.append(f"- filled_orders: {es['filled_orders']}")
    lines.append(f"- cancelled_orders: {es['cancelled_orders']}")
    lines.append("")
    lines.append("## 2. Operational Metrics")
    om = report["operational_metrics"]
    for k, v in om.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 3. Failure Cases")
    for k, v in report["failure_cases"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 4. Slippage Analysis")
    for k, v in report["slippage_analysis"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 5. Backtest vs Reality Gap")
    for k, v in report["backtest_vs_reality_gap"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 6. Stability Analysis")
    for k, v in report["stability_analysis"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 7. Final Decision")
    lines.append(f"- status: {report['final_decision']['status']}")
    lines.append(f"- critical_answer_q1: {report['final_decision']['answer_operable']}")
    lines.append(f"- critical_answer_q2: {report['final_decision']['answer_sustainable']}")
    lines.append(f"- reason: {report['final_decision']['reason']}")
    lines.append("")
    lines.append("## 8. Source Capture")
    for k, v in report["source_capture"].items():
        lines.append(f"- {k}: {v}")
    if report.get("source_capture_harness") is not None:
        lines.append("- source_capture_harness: executed")
    lines.append("")
    lines.append("## Guard Validation")
    for k, v in report["risk_guards"].items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 085: Paper pilot operational validation")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--run-paper", action="store_true", help="Run one-shot and EOD scripts before analysis")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--task084-json", type=str, default="docs/reports/task_084/task_084_strategy_lock.json")
    parser.add_argument("--task082-json", type=str, default="docs/reports/task_082/task_082_paper_validation.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_085/task_085_paper_pilot.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_085/task_085_paper_pilot.md")
    parser.add_argument("--run-capture-harness", action="store_true", help="Populate source capture tables with deterministic harness rows.")
    args = parser.parse_args()

    missing_env = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    precondition_ok = len(missing_env) == 0
    step_runs: dict[str, Any] = {"paper_one_shot_080": "SKIPPED", "paper_eod_review_081": "SKIPPED"}
    if args.run_paper:
        cmd_080 = [sys.executable, "-m", "app.paper_one_shot_080", "--db-path", args.db_path]
        r080 = subprocess.run(cmd_080, check=False, capture_output=True, text=True)
        step_runs["paper_one_shot_080"] = {"returncode": r080.returncode, "stdout": r080.stdout[-1200:], "stderr": r080.stderr[-1200:]}

        cmd_081 = [sys.executable, "-m", "app.paper_eod_review_081", "--db-path", args.db_path]
        r081 = subprocess.run(cmd_081, check=False, capture_output=True, text=True)
        step_runs["paper_eod_review_081"] = {"returncode": r081.returncode, "stdout": r081.stdout[-1200:], "stderr": r081.stderr[-1200:]}
    harness_summary: dict[str, float] | None = None
    if args.run_capture_harness:
        harness_summary = run_paper_capture_harness_371(args.db_path)

    con = sqlite3.connect(args.db_path)
    try:
        run_rows = _q(
            con,
            """
            SELECT run_id, started_at, finished_at, result_status
            FROM trade_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (args.limit,),
        )
        order_rows = _q(
            con,
            """
            SELECT order_id, run_id, symbol, side, quantity, submitted_at, status, raw_status
            FROM orders
            ORDER BY submitted_at DESC
            LIMIT ?
            """,
            (args.limit,),
        )
        fill_rows = _q(
            con,
            """
            SELECT fill_id, order_id, symbol, side, filled_quantity, fill_price, filled_at, source
            FROM fills
            ORDER BY filled_at DESC
            LIMIT ?
            """,
            (args.limit * 3,),
        )
        recon_runs = _q(
            con,
            """
            SELECT reconciliation_id, run_id, status, max_severity, block_new_orders, started_at
            FROM reconciliation_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (args.limit,),
        )
        recon_events = _q(
            con,
            """
            SELECT reconciliation_id, event_type, severity, local_status, broker_status, created_at
            FROM reconciliation_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (args.limit * 3,),
        )
    finally:
        con.close()

    total_orders = len(order_rows)
    filled_orders = sum(1 for r in order_rows if str(r.get("status") or "").upper() == "FILLED")
    cancelled_orders = sum(1 for r in order_rows if str(r.get("status") or "").upper() == "CANCELLED")
    timeout_orders = sum(1 for r in order_rows if str(r.get("status") or "").upper() in {"TIMEOUT", "EXPIRED"})
    unknown_orders = sum(1 for r in order_rows if str(r.get("status") or "").upper() == "UNKNOWN")
    partial_orders = sum(1 for r in order_rows if str(r.get("status") or "").upper() == "PARTIAL")
    failed_orders = sum(1 for r in order_rows if str(r.get("status") or "").upper() in {"FAILED", "REJECTED"})
    late_fill_count = sum(1 for e in recon_events if str(e.get("event_type") or "").upper() == "LATE_FILL")
    cancel_fail_count = sum(
        1
        for e in recon_events
        if str(e.get("event_type") or "").upper() in {"CANCEL_FAILED", "CANCEL_TIMEOUT", "UNKNOWN_ESCALATED"}
    )
    retry_count = sum(1 for e in recon_events if "RETRY" in str(e.get("event_type") or "").upper())
    recon_mismatch = sum(1 for r in recon_runs if str(r.get("status") or "").upper() == "MISMATCH")
    recon_critical = sum(1 for r in recon_runs if str(r.get("max_severity") or "").upper() == "CRITICAL")

    fill_rate = _safe_pct(filled_orders, total_orders)
    cancel_rate = _safe_pct(cancelled_orders, total_orders)
    timeout_rate = _safe_pct(timeout_orders, total_orders)
    mismatch_rate = _safe_pct(recon_mismatch, max(len(recon_runs), 1))
    unknown_rate = _safe_pct(unknown_orders, total_orders)
    partial_rate = _safe_pct(partial_orders, total_orders)

    fill_price_map: dict[str, float] = {}
    for f in fill_rows:
        oid = str(f.get("order_id") or "")
        if oid and f.get("fill_price") is not None and oid not in fill_price_map:
            fill_price_map[oid] = float(f["fill_price"])
    order_price_samples: list[float] = []
    slippage_samples: list[float] = []
    for o in order_rows:
        raw = str(o.get("raw_status") or "")
        maybe_price = None
        # raw_status often has compact text; keep defensive parse minimal.
        for token in raw.replace(",", " ").split():
            if token.startswith("price="):
                try:
                    maybe_price = float(token.split("=", 1)[1])
                except Exception:
                    maybe_price = None
        if maybe_price is not None:
            order_price_samples.append(maybe_price)
            fp = fill_price_map.get(str(o.get("order_id") or ""))
            if fp is not None:
                slippage_samples.append(fp - maybe_price)

    avg_slippage = mean(slippage_samples) if slippage_samples else None
    med_slippage = median(slippage_samples) if slippage_samples else None
    max_slippage = max(slippage_samples) if slippage_samples else None

    task084 = _load_json(Path(args.task084_json)) or {}
    task082 = _load_json(Path(args.task082_json)) or {}
    bt_s4 = (task084.get("cost_sensitivity") or {}).get("S4_KIS_REALISTIC", {})
    bt_pf = bt_s4.get("profit_factor")
    bt_fill = bt_s4.get("fill_rate")
    bt_sharpe = bt_s4.get("sharpe")
    prev_real_pf = (task082.get("backtest_vs_real") or {}).get("real_pf")

    gap = {
        "backtest_pf_s4": bt_pf,
        "paper_real_pf_reference": prev_real_pf,
        "backtest_fill_rate_s4": bt_fill,
        "paper_fill_rate": _f(fill_rate),
        "fill_rate_gap_pctp": _f(fill_rate - float(bt_fill)) if bt_fill is not None else None,
        "backtest_sharpe_s4": bt_sharpe,
    }

    execution_ok = (step_runs["paper_one_shot_080"] == "SKIPPED" or step_runs["paper_one_shot_080"]["returncode"] == 0) and (
        step_runs["paper_eod_review_081"] == "SKIPPED" or step_runs["paper_eod_review_081"]["returncode"] == 0
    )
    guard_unknown_ok = unknown_orders == 0
    recon_critical_zero = recon_critical == 0
    status, answer = _decision(
        guard_unknown_ok=guard_unknown_ok,
        recon_critical_zero=recon_critical_zero,
        execution_ok=execution_ok,
        fill_rate=fill_rate,
        timeout_rate=timeout_rate,
        late_fill_count=late_fill_count,
        mismatch_rate=mismatch_rate,
    )

    reason = (
        "Operational checks are stable and no critical safety breach detected."
        if status == "PASS"
        else (
            "Operational path works but drift/mismatch risk remains."
            if status == "WARNING"
            else "Safety-critical signal detected (UNKNOWN or reconciliation critical or execution failure)."
        )
    )
    if not precondition_ok:
        reason += f" Missing env: {', '.join(missing_env)}"

    risk_guards = {
        "daily_loss_limit_configured": False,
        "max_exposure_cap_configured": False,
        "symbol_cap_configured": False,
        "unknown_order_halt_enabled": True,
        "kill_switch_enabled": True,
    }
    source_capture = {
        str(row["metric_name"]): row["metric_value"]
        for _, row in build_source_time_capture_371(args.db_path).capture_fidelity.iterrows()
    }

    report = {
        "pilot_config": {
            "strategy_id": "D_PORTFOLIO_SECTOR_FILTER",
            "max_positions": 3,
            "max_notional_per_trade_pct": 0.02,
            "initial_capital_krw": 1_000_000,
            "execution_policy": "LIMITED_CHASE",
            "risk_policy": "TIME_STOP_ONLY",
        },
        "db_path": args.db_path,
        "precondition": {"required_env": list(REQUIRED_ENV), "missing_env": missing_env, "ok": precondition_ok},
        "step_runs": step_runs,
        "execution_summary": {
            "total_runs": len(run_rows),
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
            "failed_orders": failed_orders,
        },
        "operational_metrics": {
            "fill_rate_pct": _f(fill_rate),
            "cancel_rate_pct": _f(cancel_rate),
            "timeout_rate_pct": _f(timeout_rate),
            "unknown_rate_pct": _f(unknown_rate),
            "partial_fill_rate_pct": _f(partial_rate),
            "late_fill_count": int(late_fill_count),
            "reconciliation_mismatch_rate_pct": _f(mismatch_rate),
            "reconciliation_critical_count": int(recon_critical),
            "retry_count": int(retry_count),
        },
        "failure_cases": {
            "cancel_failure": int(cancel_fail_count),
            "partial_fill_then_cancel": int(partial_orders),
            "timeout_events": int(timeout_orders),
            "timeout_after_late_fill": int(late_fill_count),
            "api_error_or_failed": int(failed_orders),
            "unknown_status": int(unknown_orders),
        },
        "slippage_analysis": {
            "sample_count": len(slippage_samples),
            "avg_slippage": _f(avg_slippage) if avg_slippage is not None else None,
            "median_slippage": _f(med_slippage) if med_slippage is not None else None,
            "max_slippage": _f(max_slippage) if max_slippage is not None else None,
            "note": "requested_price is not persistently stored in schema; slippage samples may be sparse.",
        },
        "backtest_vs_reality_gap": gap,
        "stability_analysis": {
            "system_runs_without_crash": bool(execution_ok),
            "cancel_reconcile_loop_health": "ok" if recon_critical_zero else "warning",
            "unknown_free_operation": bool(guard_unknown_ok),
            "db_state_alignment": bool(recon_critical_zero and recon_mismatch == 0),
        },
        "source_capture": source_capture,
        "source_capture_harness": harness_summary,
        "risk_guards": risk_guards,
        "final_decision": {
            "status": status,
            "answer_operable": answer,
            "answer_sustainable": ("YES" if status == "PASS" else ("WARNING" if status == "WARNING" else "NO")),
            "reason": reason,
        },
    }

    out_json = Path(args.json_out)
    out_md = Path(args.md_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={out_json}")
    print(f"written_md={out_md}")
    print(f"final_status={status}")
    print(f"answer_operable={answer}")
    return 0


def _f(v: float | None, digits: int = 6) -> float:
    if v is None:
        return 0.0
    return float(round(float(v), digits))


if __name__ == "__main__":
    raise SystemExit(main())
