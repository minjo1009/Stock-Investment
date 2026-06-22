from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any
from zoneinfo import ZoneInfo

from state.store import has_order_with_status, initialize_store, list_recent_reconciliation_runs

REQUIRED_ENV = (
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
    "KIS_ACCOUNT_NUMBER",
    "KIS_PRODUCT_CODE",
)

LOCKED_PROFILE = {
    "strategy_id": "D_PORTFOLIO_SECTOR_FILTER",
    "execution_policy": "LIMITED_CHASE",
    "risk_policy": "TIME_STOP_ONLY",
    "max_positions": 3,
    "market_order_allowed": False,
    "unknown_order_halt": True,
    "reconciliation_critical_halt": True,
    "kill_switch_required": True,
    "daily_loss_limit_pct": -1.0,
    "hard_daily_loss_limit_krw": -10_000.0,
    "max_total_notional_krw": 300_000.0,
    "max_symbol_notional_krw": 150_000.0,
    "max_sector_notional_krw": 200_000.0,
}

FAILURE_REASON = {
    "live_env": "LIVE_ENVIRONMENT_DETECTED",
    "unknown_order": "UNKNOWN_ORDER_EXISTS",
    "recon_critical": "RECONCILIATION_CRITICAL_EXISTS",
    "kill_switch": "KILL_SWITCH_ON",
    "missing_creds": "MISSING_CREDENTIALS",
    "market_closed": "MARKET_CLOSED",
    "stale_data": "STALE_DATA",
    "risk_breach": "RISK_GUARD_BREACH",
    "market_order_path": "MARKET_ORDER_PATH_TRIGGERED",
    "late_fill_unresolved": "UNRESOLVED_LATE_FILL",
    "cancel_loop_unknown": "CANCEL_LOOP_UNKNOWN_ESCALATION",
    "broker_local_position_mismatch": "BROKER_LOCAL_POSITION_MISMATCH",
}


@dataclass
class EvidenceStatus:
    status: str
    failure_reasons: list[str]
    warnings: list[str]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _fmt_ts(ts: datetime) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def _run_id(ts: datetime) -> str:
    return ts.strftime("%Y%m%d_%H%M%S")


def _safe_ratio(num: float, den: float) -> float:
    return (num / den) if den else 0.0


def _safe_mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _load_env_file(path: Path) -> bool:
    if not path.exists():
        return False
    loaded = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value
            loaded = True
    return loaded


def _is_us_market_open(now_utc: datetime | None = None) -> bool:
    current = now_utc or _utc_now()
    ny = current.astimezone(ZoneInfo("America/New_York"))
    if ny.weekday() >= 5:
        return False
    hhmm = ny.hour * 60 + ny.minute
    return 9 * 60 + 35 <= hhmm <= 15 * 60 + 50


def _is_data_stale(base_dir: Path, max_stale_hours: int) -> bool:
    if not base_dir.exists():
        return True
    latest_mtime = 0.0
    for csv_file in base_dir.glob("*.csv"):
        try:
            latest_mtime = max(latest_mtime, csv_file.stat().st_mtime)
        except OSError:
            continue
    if latest_mtime <= 0.0:
        return True
    age_hours = (_utc_now().timestamp() - latest_mtime) / 3600.0
    return age_hours > float(max_stale_hours)


def _table_exists(con: sqlite3.Connection, table_name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _kill_switch_state(db_path: str) -> bool:
    if not os.path.exists(db_path):
        return False
    con = sqlite3.connect(db_path)
    try:
        if not _table_exists(con, "control_state"):
            return False
        row = con.execute(
            "SELECT kill_switch_active FROM control_state WHERE control_key='default' LIMIT 1"
        ).fetchone()
        if row is None:
            return False
        return int(row[0]) == 1
    finally:
        con.close()


def _has_recon_critical(db_path: str) -> bool:
    runs = list_recent_reconciliation_runs(db_path, limit=20)
    return any(str(r.get("max_severity") or "").upper() == "CRITICAL" for r in runs)


def _compute_notional_breach(db_path: str) -> bool:
    con = sqlite3.connect(db_path)
    try:
        if not _table_exists(con, "positions"):
            return False
        rows = con.execute("SELECT symbol, quantity, avg_price FROM positions").fetchall()
    finally:
        con.close()
    total = 0.0
    symbol_max = 0.0
    for symbol, qty, avg in rows:
        notional = abs(float(qty or 0.0) * float(avg or 0.0))
        total += notional
        symbol_max = max(symbol_max, notional)
    return total > LOCKED_PROFILE["max_total_notional_krw"] or symbol_max > LOCKED_PROFILE["max_symbol_notional_krw"]


def _preflight_failures(
    *,
    db_path: str,
    allow_market_closed: bool,
    allow_stale_data: bool,
    data_dir: Path,
    max_stale_hours: int,
    dry_run: bool,
) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    env = (os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper")
    if env != "paper":
        failures.append(FAILURE_REASON["live_env"])

    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        if dry_run:
            warnings.append("MISSING_CREDENTIALS_DRY_RUN")
        else:
            failures.append(FAILURE_REASON["missing_creds"])

    if has_order_with_status(db_path, status="UNKNOWN"):
        failures.append(FAILURE_REASON["unknown_order"])
    if _has_recon_critical(db_path):
        failures.append(FAILURE_REASON["recon_critical"])
    if _kill_switch_state(db_path):
        failures.append(FAILURE_REASON["kill_switch"])
    if _compute_notional_breach(db_path):
        failures.append(FAILURE_REASON["risk_breach"])

    market_open = _is_us_market_open()
    if not market_open and not allow_market_closed:
        failures.append(FAILURE_REASON["market_closed"])

    stale = _is_data_stale(data_dir, max_stale_hours=max_stale_hours)
    if stale and not allow_stale_data:
        failures.append(FAILURE_REASON["stale_data"])

    return failures, warnings


def _q(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _collect_window_stats(*, db_path: str, started_at: str) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    try:
        order_rows = _q(
            con,
            """
            SELECT order_id, symbol, status, quantity, raw_status, submitted_at
            FROM orders
            WHERE submitted_at >= ?
            ORDER BY submitted_at ASC
            """,
            (started_at,),
        )
        fill_rows = _q(
            con,
            """
            SELECT order_id, fill_price, filled_quantity, filled_at
            FROM fills
            WHERE filled_at >= ?
            ORDER BY filled_at ASC
            """,
            (started_at,),
        )
        recon_rows = _q(
            con,
            """
            SELECT status, max_severity, started_at
            FROM reconciliation_runs
            WHERE started_at >= ?
            ORDER BY started_at ASC
            """,
            (started_at,),
        )
        recon_events = _q(
            con,
            """
            SELECT event_type, severity, created_at
            FROM reconciliation_events
            WHERE created_at >= ?
            ORDER BY created_at ASC
            """,
            (started_at,),
        )
    finally:
        con.close()

    statuses = [str(r.get("status") or "").upper() for r in order_rows]
    order_attempts = len(order_rows)
    submitted_orders = sum(1 for s in statuses if s in {"SUBMITTED", "PENDING", "PARTIAL", "FILLED", "CANCELLED", "EXPIRED", "TIMEOUT", "FAILED", "REJECTED"})
    filled_orders = sum(1 for s in statuses if s == "FILLED")
    cancelled_orders = sum(1 for s in statuses if s == "CANCELLED")
    partial_fills = sum(1 for s in statuses if s == "PARTIAL")
    timeout_events = sum(1 for s in statuses if s in {"TIMEOUT", "EXPIRED"})
    unknown_events = sum(1 for s in statuses if s == "UNKNOWN")
    reconciliation_checks = len(recon_rows)
    reconciliation_critical_count = sum(1 for r in recon_rows if str(r.get("max_severity") or "").upper() == "CRITICAL")
    late_fills = sum(1 for e in recon_events if str(e.get("event_type") or "").upper() == "LATE_FILL")

    cancel_related = [
        str(e.get("event_type") or "").upper()
        for e in recon_events
        if "CANCEL" in str(e.get("event_type") or "").upper()
    ]
    cancel_confirmed = sum(1 for e in cancel_related if e in {"CANCEL_CONFIRMED", "CANCELLED"})
    cancel_failed = sum(1 for e in cancel_related if e in {"CANCEL_FAILED", "CANCEL_TIMEOUT", "UNKNOWN_ESCALATED"})
    cancel_observed = len(cancel_related) > 0 or cancelled_orders > 0
    cancel_success_rate = _safe_ratio(cancel_confirmed, cancel_confirmed + cancel_failed) if (cancel_confirmed + cancel_failed) > 0 else (1.0 if cancelled_orders > 0 else 0.0)

    fills_by_order: dict[str, float] = {}
    total_filled_notional = 0.0
    for row in fill_rows:
        oid = str(row.get("order_id") or "")
        price = row.get("fill_price")
        qty = float(row.get("filled_quantity") or 0.0)
        if price is not None:
            px = float(price)
            total_filled_notional += px * qty
            fills_by_order[oid] = px

    requested_price: dict[str, float] = {}
    total_requested_notional = 0.0
    slippages: list[float] = []
    symbols: list[str] = []
    for row in order_rows:
        oid = str(row.get("order_id") or "")
        raw = str(row.get("raw_status") or "")
        maybe_price: float | None = None
        for token in raw.replace(",", " ").split():
            if token.startswith("price="):
                try:
                    maybe_price = float(token.split("=", 1)[1])
                except Exception:
                    maybe_price = None
        qty = float(row.get("quantity") or 0.0)
        if maybe_price is not None:
            requested_price[oid] = maybe_price
            total_requested_notional += maybe_price * qty
            if oid in fills_by_order:
                slippages.append(float(fills_by_order[oid]) - maybe_price)
        symbol = str(row.get("symbol") or "").upper()
        if symbol:
            symbols.append(symbol)

    avg_slippage = _safe_mean(slippages)
    max_slippage = max(slippages) if slippages else 0.0

    realized_pnl = 0.0
    if len(fill_rows) >= 2:
        # Diagnostic proxy only: match sequential BUY/SELL fills in run window.
        inv = 0.0
        for row in fill_rows:
            qty = float(row.get("filled_quantity") or 0.0)
            px = float(row.get("fill_price") or 0.0)
            if qty <= 0 or px <= 0:
                continue
            inv += qty * px
        realized_pnl = -inv

    selected_symbols = sorted(set(symbols))
    selected_sectors: list[str] = []
    try:
        from sector.sector_model import map_symbol_to_sector

        selected_sectors = sorted({map_symbol_to_sector(sym) for sym in selected_symbols if sym})
    except Exception:
        selected_sectors = []

    # Data/indicator quality snapshot (latest signal snapshot set).
    data_fresh_ratio = 0.0
    missing_bar_ratio = 1.0
    signal_generated_run = 0
    try:
        con2 = sqlite3.connect(db_path)
        con2.row_factory = sqlite3.Row
        latest = con2.execute("SELECT MAX(created_at) AS created_at FROM indicator_snapshots").fetchone()
        latest_created = str(latest["created_at"] if isinstance(latest, sqlite3.Row) else (latest[0] if latest else "") or "")
        if latest_created:
            rows = [
                dict(r)
                for r in con2.execute(
                    """
                    SELECT data_fresh, insufficient_history, entry_allowed
                    FROM indicator_snapshots
                    WHERE created_at = ?
                    """,
                    (latest_created,),
                ).fetchall()
            ]
            if rows:
                total = len(rows)
                data_fresh_ratio = _safe_ratio(sum(1 for r in rows if int(r.get("data_fresh") or 0) == 1), total)
                missing_bar_ratio = _safe_ratio(
                    sum(1 for r in rows if int(r.get("insufficient_history") or 0) == 1),
                    total,
                )
                signal_generated_run = 1 if any(int(r.get("entry_allowed") or 0) == 1 for r in rows) else 0
    except Exception:
        pass
    finally:
        try:
            con2.close()  # type: ignore[name-defined]
        except Exception:
            pass

    return {
        "selected_symbols": selected_symbols,
        "selected_sectors": selected_sectors,
        "order_attempts": order_attempts,
        "submitted_orders": submitted_orders,
        "filled_orders": filled_orders,
        "cancelled_orders": cancelled_orders,
        "partial_fills": partial_fills,
        "late_fills": late_fills,
        "timeout_events": timeout_events,
        "unknown_events": unknown_events,
        "reconciliation_checks": reconciliation_checks,
        "reconciliation_critical_count": reconciliation_critical_count,
        "total_requested_notional": round(total_requested_notional, 6),
        "total_filled_notional": round(total_filled_notional, 6),
        "fill_rate": round(_safe_ratio(filled_orders, order_attempts), 6),
        "cancel_success_rate": round(cancel_success_rate, 6),
        "average_slippage": round(avg_slippage, 6),
        "max_slippage": round(max_slippage, 6),
        "realized_pnl": round(realized_pnl, 6),
        "cancel_observed": cancel_observed,
        "cancel_unknown_escalation_count": sum(1 for e in recon_events if str(e.get("event_type") or "").upper() == "UNKNOWN_ESCALATED"),
        "market_order_attempted": any("MARKET" in str(r.get("raw_status") or "").upper() for r in order_rows),
        "unresolved_late_fill_count": 0,
        "position_mismatch_count": sum(
            1
            for e in recon_events
            if str(e.get("event_type") or "").upper() in {"MISSING_LOCAL", "MISSING_BROKER", "FILL_MISMATCH", "STATUS_MISMATCH"}
            and str(e.get("severity") or "").upper() == "CRITICAL"
        ),
        "data_fresh_ratio": round(data_fresh_ratio, 6),
        "missing_bar_ratio": round(missing_bar_ratio, 6),
        "signal_generated_run": int(signal_generated_run),
        "warnings": [],
    }


def evaluate_evidence_status(payload: dict[str, Any]) -> EvidenceStatus:
    failures = list(payload.get("failure_reasons") or [])
    warnings = list(payload.get("warnings") or [])

    if payload.get("market_order_attempted"):
        failures.append(FAILURE_REASON["market_order_path"])
    if int(payload.get("unknown_events") or 0) > 0:
        failures.append(FAILURE_REASON["unknown_order"])
    if int(payload.get("reconciliation_critical_count") or 0) > 0:
        failures.append(FAILURE_REASON["recon_critical"])
    if int(payload.get("unresolved_late_fill_count") or 0) > 0:
        failures.append(FAILURE_REASON["late_fill_unresolved"])
    if int(payload.get("cancel_unknown_escalation_count") or 0) > 0:
        failures.append(FAILURE_REASON["cancel_loop_unknown"])
    if int(payload.get("position_mismatch_count") or 0) > 0:
        failures.append(FAILURE_REASON["broker_local_position_mismatch"])

    if int(payload.get("order_attempts") or 0) == 0:
        warnings.append("NO_SIGNAL_OR_NO_ORDER_SAMPLE")
    if int(payload.get("order_attempts") or 0) > 0 and int(payload.get("filled_orders") or 0) == 0:
        warnings.append("INSUFFICIENT_EXECUTION_SAMPLE")
    cancel_observed = bool(payload.get("cancel_observed"))
    if not cancel_observed:
        warnings.append("NO_CANCEL_SAMPLE_OBSERVED")
    elif float(payload.get("cancel_success_rate") or 0.0) < 1.0:
        warnings.append("CANCEL_NOT_FULLY_CONFIRMED")

    unique_failures = sorted(set(failures))
    unique_warnings = sorted(set(warnings))

    if unique_failures:
        return EvidenceStatus(status="FAIL", failure_reasons=unique_failures, warnings=unique_warnings)
    if unique_warnings:
        return EvidenceStatus(status="WARNING", failure_reasons=unique_failures, warnings=unique_warnings)
    return EvidenceStatus(status="PASS", failure_reasons=unique_failures, warnings=unique_warnings)


def _to_markdown(evidence: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 087 - Pilot Execution Evidence")
    lines.append("")
    lines.append(f"- run_id: {evidence['run_id']}")
    lines.append(f"- status: {evidence['status']}")
    lines.append(f"- environment: {evidence['environment']}")
    lines.append(f"- strategy_id: {evidence['strategy_id']}")
    lines.append(f"- started_at: {evidence['started_at']}")
    lines.append(f"- ended_at: {evidence['ended_at']}")
    if evidence.get("failed_component"):
        lines.append(f"- failed_component: {evidence.get('failed_component')}")
    if evidence.get("stack_trace"):
        lines.append(f"- stack_trace: {evidence.get('stack_trace')}")
    lines.append("")
    lines.append("## Execution Metrics")
    metric_keys = (
        "order_attempts",
        "submitted_orders",
        "filled_orders",
        "cancelled_orders",
        "partial_fills",
        "late_fills",
        "timeout_events",
        "unknown_events",
        "reconciliation_checks",
        "reconciliation_critical_count",
        "fill_rate",
        "cancel_success_rate",
        "average_slippage",
        "max_slippage",
        "realized_pnl",
        "data_fresh_ratio",
        "missing_bar_ratio",
        "signal_generated_run",
    )
    for key in metric_keys:
        lines.append(f"- {key}: {evidence.get(key)}")
    lines.append("")
    lines.append("## Selection")
    lines.append(f"- selected_symbols: {', '.join(evidence.get('selected_symbols') or []) or '(none)'}")
    lines.append(f"- selected_sectors: {', '.join(evidence.get('selected_sectors') or []) or '(none)'}")
    lines.append("")
    lines.append("## Failure Reasons")
    if evidence.get("failure_reasons"):
        for reason in evidence["failure_reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Warnings")
    if evidence.get("warnings"):
        for reason in evidence["warnings"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- (none)")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 087: pilot execution evidence collection")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--runs-dir", type=str, default="docs/reports/task_087/runs")
    parser.add_argument("--latest-json-out", type=str, default="docs/reports/task_087/task_087_latest_run.json")
    parser.add_argument("--latest-md-out", type=str, default="docs/reports/task_087/task_087_latest_run.md")
    parser.add_argument("--task085-json", type=str, default="docs/reports/task_085/task_085_paper_pilot.json")
    parser.add_argument("--task085-md", type=str, default="docs/reports/task_085/task_085_paper_pilot.md")
    parser.add_argument("--allow-market-closed", action="store_true")
    parser.add_argument("--allow-stale-data", action="store_true")
    parser.add_argument("--max-stale-hours", type=int, default=120)
    parser.add_argument("--data-dir", type=str, default="data/raw/us_daily")
    parser.add_argument("--env-file", type=str, default="config/kis_paper.env")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--external-failure-reason", action="append", default=[])
    parser.add_argument("--failed-component", type=str, default="")
    parser.add_argument("--external-stack-trace", type=str, default="")
    args = parser.parse_args()

    _load_env_file(Path(args.env_file))
    initialize_store(args.db_path)
    started = _utc_now()
    run_id = _run_id(started)

    failures, warnings = _preflight_failures(
        db_path=args.db_path,
        allow_market_closed=args.allow_market_closed,
        allow_stale_data=args.allow_stale_data,
        data_dir=Path(args.data_dir),
        max_stale_hours=args.max_stale_hours,
        dry_run=args.dry_run,
    )

    step_run: dict[str, Any] = {"task_085": "SKIPPED"}
    external_failures = [str(x).strip() for x in (args.external_failure_reason or []) if str(x).strip()]
    failures.extend(external_failures)
    if not failures and not args.dry_run:
        cmd = [
            sys.executable,
            "-m",
            "app.task_085_paper_pilot",
            "--run-paper",
            "--db-path",
            args.db_path,
            "--json-out",
            args.task085_json,
            "--md-out",
            args.task085_md,
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        step_run["task_085"] = {
            "returncode": proc.returncode,
            "stdout": proc.stdout[-1000:],
            "stderr": proc.stderr[-1000:],
        }
        if proc.returncode != 0:
            failures.append("TASK_085_RUN_FAILED")

    window_stats = _collect_window_stats(db_path=args.db_path, started_at=_fmt_ts(started))
    ended = _utc_now()

    payload: dict[str, Any] = {
        "run_id": run_id,
        "started_at": _fmt_ts(started),
        "ended_at": _fmt_ts(ended),
        "environment": (os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper"),
        "strategy_id": LOCKED_PROFILE["strategy_id"],
        "risk_guard_snapshot": LOCKED_PROFILE,
        "kill_switch_state": _kill_switch_state(args.db_path),
        "failure_reasons": sorted(set(failures)),
        "warnings": sorted(set(warnings)),
        "step_run": step_run,
        "failed_component": (str(args.failed_component).strip() or None),
        "stack_trace": (str(args.external_stack_trace).strip() or None),
        "external_failure_reasons": sorted(set(external_failures)),
        "eod_review_completed": (step_run["task_085"] != "SKIPPED"),
        **window_stats,
    }

    final = evaluate_evidence_status(payload)
    payload["status"] = final.status
    payload["failure_reasons"] = final.failure_reasons
    payload["warnings"] = final.warnings

    runs_dir = Path(args.runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_json = runs_dir / f"{run_id}_pilot_run.json"
    run_md = runs_dir / f"{run_id}_pilot_run.md"
    run_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    run_md.write_text(_to_markdown(payload), encoding="utf-8")

    latest_json = Path(args.latest_json_out)
    latest_md = Path(args.latest_md_out)
    latest_json.parent.mkdir(parents=True, exist_ok=True)
    latest_md.parent.mkdir(parents=True, exist_ok=True)
    latest_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    latest_md.write_text(_to_markdown(payload), encoding="utf-8")

    print(f"written_run_json={run_json}")
    print(f"written_run_md={run_md}")
    print(f"written_latest_json={latest_json}")
    print(f"written_latest_md={latest_md}")
    print(f"status={payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
