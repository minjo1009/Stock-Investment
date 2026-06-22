from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from app.reconciliation import ReconciliationOutcome, reconcile_local_and_broker
from execution.cancel_loop import cancel_until_terminal
from integration.kis_client import KISClient
from state.store import (
    FILL_INSERTED,
    POSITION_EVENT_INSERTED,
    apply_fill_to_position,
    get_fills_for_order,
    get_position,
    has_order_with_status,
    initialize_store,
    list_local_filled_order_ids,
    list_open_orders,
    record_fill,
    record_order,
    record_position_event,
    record_reconciliation_event,
    record_reconciliation_run,
    record_trade_run_finish,
    record_trade_run_start,
    update_order_status,
    upsert_position,
)

MODE_FILL_TEST = "FILL_TEST"
MODE_CANCEL_TEST = "CANCEL_TEST"
ALLOWED_MODES = {MODE_FILL_TEST, MODE_CANCEL_TEST}
TERMINAL_STATES = {"FILLED", "CANCELLED", "REJECTED", "EXPIRED"}
ACTIVE_ORDER_STATES = {"SUBMITTED", "PENDING", "PARTIAL", "CANCEL_REQUESTED", "CANCEL_IN_PROGRESS"}

REQUIRED_ENV = ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NUMBER", "KIS_PRODUCT_CODE")
SENSITIVE_KEYS = {
    "authorization",
    "appkey",
    "appsecret",
    "token",
    "access_token",
    "refresh_token",
    "hashkey",
    "cano",
    "acnt_prdt_cd",
    "account",
    "account_number",
}


class BrokerAdapter(Protocol):
    def get_current_price(self, symbol: str) -> tuple[float, dict[str, Any]]: ...

    def submit_limit_buy(self, symbol: str, qty: int, limit_price: float) -> tuple[str, dict[str, Any]]: ...

    def get_order_snapshot(self, order_id: str, symbol: str) -> dict[str, Any]: ...

    def get_fills(self, order_id: str, symbol: str) -> list[dict[str, Any]]: ...

    def cancel_order(self, order_id: str, symbol: str, qty: int, price: float, order_type: str) -> dict[str, Any]: ...

    def fetch_broker_order_statuses(self, symbol: str) -> list[dict[str, Any]]: ...


@dataclass
class RunArtifacts:
    quote_response: Any = None
    submit_response: Any = None
    status_initial: Any = None
    status_final: Any = None
    fills_response: Any = None
    cancel_response: Any = None
    reconciliation_snapshot: Any = None


class KISBrokerAdapter:
    def __init__(self, client: KISClient) -> None:
        self.client = client

    def get_current_price(self, symbol: str) -> tuple[float, dict[str, Any]]:
        return self.client.get_current_price_with_response(symbol)

    def submit_limit_buy(self, symbol: str, qty: int, limit_price: float) -> tuple[str, dict[str, Any]]:
        return self.client.submit_order_with_response(symbol=symbol, side="BUY", quantity=qty, limit_price=limit_price)

    def get_order_snapshot(self, order_id: str, symbol: str) -> dict[str, Any]:
        return self.client.get_order_snapshot(order_id, symbol=symbol)

    def get_fills(self, order_id: str, symbol: str) -> list[dict[str, Any]]:
        return self.client.get_fills(order_id, symbol=symbol)

    def cancel_order(self, order_id: str, symbol: str, qty: int, price: float, order_type: str) -> dict[str, Any]:
        return self.client.cancel_order(
            order_id=order_id,
            account=self.client.account_number,
            symbol=symbol,
            qty=qty,
            price=price,
            order_type=order_type,
        )

    def fetch_broker_order_statuses(self, symbol: str) -> list[dict[str, Any]]:
        return self.client.fetch_broker_order_statuses(symbol=symbol)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(ts: datetime | None = None) -> str:
    return (ts or _utc_now()).isoformat().replace("+00:00", "Z")


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


def _is_market_open(now_utc: datetime | None = None) -> bool:
    current = now_utc or _utc_now()
    ny = current.astimezone(ZoneInfo("America/New_York"))
    if ny.weekday() >= 5:
        return False
    hhmm = ny.hour * 60 + ny.minute
    return 9 * 60 + 35 <= hhmm <= 15 * 60 + 50


def _is_live_environment(env: str) -> bool:
    return env.strip().lower() not in {"paper", ""}


def _compute_limit_price(mode: str, current_price: float) -> float:
    if mode == MODE_FILL_TEST:
        return current_price * 1.002
    if mode == MODE_CANCEL_TEST:
        return current_price * 0.95
    raise ValueError(f"unsupported mode: {mode}")


def _validate_qty(qty: int) -> list[str]:
    if qty != 1:
        return ["QTY_NOT_EQUAL_1"]
    return []


def _validate_notional(price: float, qty: int, max_notional: float) -> list[str]:
    if price <= 0:
        return ["INVALID_PRICE"]
    if (price * qty) > max_notional:
        return ["NOTIONAL_CAP_BREACH"]
    return []


def _sanitize(data: Any) -> Any:
    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for k, v in data.items():
            key = str(k)
            if key.strip().lower() in SENSITIVE_KEYS:
                out[key] = "__REDACTED__"
            else:
                out[key] = _sanitize(v)
        return out
    if isinstance(data, list):
        return [_sanitize(x) for x in data]
    return data


def _ensure_db_writable(db_path: str) -> bool:
    try:
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE IF NOT EXISTS _t091a_writable_probe (k TEXT PRIMARY KEY, v TEXT)")
        con.execute("INSERT OR REPLACE INTO _t091a_writable_probe(k,v) VALUES('probe','ok')")
        con.commit()
        con.close()
        return True
    except Exception:
        return False


def _table_exists(con: sqlite3.Connection, table_name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _has_reconciliation_critical(db_path: str) -> bool:
    con = sqlite3.connect(db_path)
    try:
        if not _table_exists(con, "reconciliation_runs"):
            return False
        cnt = con.execute("SELECT COUNT(*) FROM reconciliation_runs WHERE UPPER(max_severity)='CRITICAL'").fetchone()[0]
        return int(cnt) > 0
    finally:
        con.close()


def _has_active_order_for_symbol(db_path: str, symbol: str) -> bool:
    con = sqlite3.connect(db_path)
    try:
        if not _table_exists(con, "orders"):
            return False
        cnt = con.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE UPPER(symbol)=?
              AND UPPER(status) IN ('SUBMITTED','PENDING','PARTIAL','CANCEL_REQUESTED','CANCEL_IN_PROGRESS','UNKNOWN')
            """,
            (symbol.upper(),),
        ).fetchone()[0]
        return int(cnt) > 0
    finally:
        con.close()


def _run_reconciliation(
    *,
    db_path: str,
    run_id: str,
    symbol: str,
    adapter: BrokerAdapter,
) -> ReconciliationOutcome:
    started_at = _iso()
    try:
        raw_broker_orders = adapter.fetch_broker_order_statuses(symbol=symbol)
        broker_orders = [
            row
            for row in raw_broker_orders
            if str(row.get("mapped_status") or row.get("state") or "").upper() in ACTIVE_ORDER_STATES
        ]
        local_open_orders = [row for row in list_open_orders(db_path) if str(row.get("symbol") or "").upper() == symbol.upper()]
        local_filled_order_ids = list_local_filled_order_ids(db_path, symbol=symbol)
        outcome = reconcile_local_and_broker(
            local_open_orders=local_open_orders,
            local_filled_order_ids=local_filled_order_ids,
            broker_orders=broker_orders,
        )
    except Exception as exc:
        finished_at = _iso()
        recon_id = record_reconciliation_run(
            db_path,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status="ERROR",
            max_severity="CRITICAL",
            block_new_orders=True,
            summary_text=f"reconciliation error: {exc}",
            raw_snapshot_json=json.dumps({"error": str(exc)}),
        )
        record_reconciliation_event(
            db_path,
            reconciliation_id=recon_id,
            symbol=symbol,
            local_order_id=None,
            broker_order_id=None,
            event_type="RECONCILIATION_ERROR",
            severity="CRITICAL",
            local_status=None,
            broker_status=None,
            details={"error": str(exc)},
            created_at=finished_at,
        )
        return ReconciliationOutcome(
            status="ERROR",
            severity="CRITICAL",
            block_new_orders=True,
            summary_text=f"reconciliation error: {exc}",
            events=(),
        )

    finished_at = _iso()
    recon_id = record_reconciliation_run(
        db_path,
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        status=outcome.status,
        max_severity=outcome.severity,
        block_new_orders=outcome.block_new_orders,
        summary_text=outcome.summary_text,
        raw_snapshot_json=json.dumps(
            {"broker_orders_open": broker_orders, "broker_orders_raw": raw_broker_orders},
            ensure_ascii=True,
            default=str,
        ),
    )
    for event in outcome.events:
        record_reconciliation_event(
            db_path,
            reconciliation_id=recon_id,
            symbol=event.get("symbol"),
            local_order_id=event.get("local_order_id"),
            broker_order_id=event.get("broker_order_id"),
            event_type=str(event.get("event_type") or "UNKNOWN"),
            severity=str(event.get("severity") or "INFO"),
            local_status=event.get("local_status"),
            broker_status=event.get("broker_status"),
            details=event.get("details"),
            created_at=finished_at,
        )
    return outcome


def _record_fill_and_position(
    *,
    db_path: str,
    run_id: str,
    order_id: str,
    symbol: str,
    qty: float,
    fill_price: float | None,
) -> float:
    source = "ORDER_STATUS"
    fill_id = f"{order_id}:{_iso()}:{source}"
    write = record_fill(
        db_path,
        fill_id=fill_id,
        order_id=order_id,
        run_id=run_id,
        symbol=symbol,
        side="BUY",
        filled_quantity=qty,
        fill_price=fill_price,
        filled_at=_iso(),
        source=source,
    )
    if write != FILL_INSERTED:
        return 0.0

    current = get_position(db_path, symbol)
    old_qty = 0.0 if current is None else float(current["quantity"])
    old_avg = 0.0 if current is None else float(current["avg_price"])
    px = float(fill_price if fill_price is not None else old_avg)
    new_qty, new_avg = apply_fill_to_position(
        old_quantity=old_qty,
        old_avg_price=old_avg,
        fill_side="BUY",
        fill_quantity=float(qty),
        fill_price=px,
    )
    upsert_position(
        db_path,
        symbol=symbol,
        side="LONG",
        quantity=new_qty,
        avg_price=new_avg,
        updated_at=_iso(),
    )
    event_result = record_position_event(
        db_path,
        run_id=run_id,
        order_id=order_id,
        fill_id=fill_id,
        symbol=symbol,
        side="LONG",
        fill_qty=float(qty),
        fill_price=px,
        position_qty_after=new_qty,
        avg_price_after=new_avg,
        created_at=_iso(),
    )
    if event_result != POSITION_EVENT_INSERTED:
        return 0.0
    return qty


def _apply_broker_fills(
    *,
    db_path: str,
    run_id: str,
    order_id: str,
    symbol: str,
    fills: list[dict[str, Any]],
) -> tuple[float, float | None]:
    broker_total = sum(float(x.get("filled_qty") or 0.0) for x in fills)
    local_total = sum(float(x.get("filled_quantity") or 0.0) for x in get_fills_for_order(db_path, order_id))
    delta = broker_total - local_total
    if delta <= 0:
        return 0.0, None
    weighted_value = 0.0
    weighted_qty = 0.0
    for fill in fills:
        q = float(fill.get("filled_qty") or 0.0)
        p = fill.get("fill_price")
        if q > 0 and p not in (None, ""):
            weighted_value += q * float(p)
            weighted_qty += q
    avg_fill = (weighted_value / weighted_qty) if weighted_qty > 0 else None
    applied = _record_fill_and_position(
        db_path=db_path,
        run_id=run_id,
        order_id=order_id,
        symbol=symbol,
        qty=delta,
        fill_price=avg_fill,
    )
    return applied, avg_fill


def _write_fixture(path: Path, *, name: str, response: Any, captured: bool, reason: str | None = None) -> str:
    payload = {
        "_fixture_meta": {
            "source": "KIS paper",
            "captured_at": _iso(),
            "sanitized": True,
            "captured": bool(captured),
            "reason": reason,
            "case": name.replace(".json", ""),
        },
        "response": _sanitize(response),
    }
    out = path / name
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return str(out)


def _collect_unknown_and_recon(db_path: str) -> tuple[int, int]:
    con = sqlite3.connect(db_path)
    try:
        unknown = 0
        recon_critical = 0
        if _table_exists(con, "orders"):
            unknown = int(con.execute("SELECT COUNT(*) FROM orders WHERE UPPER(status)='UNKNOWN'").fetchone()[0])
        if _table_exists(con, "reconciliation_runs"):
            recon_critical = int(
                con.execute("SELECT COUNT(*) FROM reconciliation_runs WHERE UPPER(max_severity)='CRITICAL'").fetchone()[0]
            )
        return unknown, recon_critical
    finally:
        con.close()


def _count_recon_critical_for_run(db_path: str, run_id: str) -> int:
    con = sqlite3.connect(db_path)
    try:
        if not _table_exists(con, "reconciliation_runs"):
            return 0
        row = con.execute(
            "SELECT COUNT(*) FROM reconciliation_runs WHERE run_id=? AND UPPER(max_severity)='CRITICAL'",
            (run_id,),
        ).fetchone()
        return int(row[0]) if row else 0
    finally:
        con.close()


def _build_decision(report: dict[str, Any]) -> tuple[str, str]:
    failures = report["failure_reasons"]
    if failures:
        return "FAIL", "NO"
    if report["order_submitted"] and report["order_status_final"] in {"FILLED", "CANCELLED"}:
        return "PASS", "YES"
    if report.get("dry_run"):
        return "WARNING", "NO"
    return "WARNING", "NO"


def run_controlled_lifecycle(
    *,
    mode: str,
    symbol: str,
    qty: int,
    max_notional: float,
    db_path: str,
    adapter: BrokerAdapter,
    dry_run: bool,
    status_poll_interval_seconds: int,
    max_status_poll_attempts: int,
    cancel_poll_interval_seconds: int,
    max_cancel_attempts: int,
    hard_timeout_seconds: int,
) -> tuple[dict[str, Any], RunArtifacts]:
    started_at = _iso()
    failures: list[str] = []
    warnings: list[str] = []
    artifacts = RunArtifacts()

    env_name = (os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper")
    missing_env = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if _is_live_environment(env_name):
        failures.append("LIVE_ENVIRONMENT_DETECTED")
    if missing_env:
        failures.append("MISSING_CREDENTIALS")
    if qty != 1:
        failures.extend(_validate_qty(qty))
    if mode not in ALLOWED_MODES:
        failures.append("INVALID_MODE")
    if not _ensure_db_writable(db_path):
        failures.append("DB_WRITE_FAILED")
    if has_order_with_status(db_path, status="UNKNOWN"):
        failures.append("UNKNOWN_ORDER_EXISTS")
    if _has_reconciliation_critical(db_path):
        warnings.append("PREEXISTING_RECONCILIATION_CRITICAL")
    if _has_active_order_for_symbol(db_path, symbol):
        failures.append("ACTIVE_ORDER_EXISTS_FOR_SYMBOL")
    if not _is_market_open():
        failures.append("MARKET_CLOSED")
    if os.environ.get("KIS_ORDER_DVSN", "00").strip() != "00":
        failures.append("MARKET_ORDER_PATH_TRIGGERED")
        report_market_order_path = True
    else:
        report_market_order_path = False

    current_price = 0.0
    quote_ok = False
    if not failures:
        try:
            current_price, quote_resp = adapter.get_current_price(symbol)
            artifacts.quote_response = quote_resp
            quote_ok = True
        except Exception as exc:
            failures.append(f"QUOTE_FETCH_FAILED:{exc}")
    if quote_ok:
        if current_price <= 0:
            failures.append("INVALID_PRICE")
        limit_price = _compute_limit_price(mode, current_price)
        failures.extend(_validate_notional(limit_price, qty, max_notional))
    else:
        limit_price = 0.0

    report: dict[str, Any] = {
        "task": "T091-A",
        "mode": mode,
        "started_at": started_at,
        "ended_at": _iso(),
        "environment": env_name,
        "symbol": symbol.upper(),
        "qty": qty,
        "current_price": round(float(current_price), 6) if current_price else 0.0,
        "submitted_price": round(float(limit_price), 6) if limit_price else 0.0,
        "requested_notional": round(float(limit_price * qty), 6) if limit_price else 0.0,
        "broker_order_id": None,
        "order_submitted": False,
        "order_status_initial": None,
        "order_status_final": None,
        "filled_qty": 0.0,
        "fill_price": 0.0,
        "cancel_requested": False,
        "cancel_confirmed": False,
        "cancel_race_filled": False,
        "reconciliation_status": None,
        "reconciliation_critical_count": 0,
        "unknown_events": 0,
        "market_order_path": report_market_order_path,
        "fixtures_written": [],
        "failure_reasons": failures.copy(),
        "warnings": warnings.copy(),
        "dry_run": bool(dry_run),
        "missing_env": missing_env,
    }
    if failures:
        report["ended_at"] = _iso()
        status, answer = _build_decision(report)
        report["status"] = status
        report["answer"] = answer
        return report, artifacts

    if dry_run:
        report["warnings"].append("DRY_RUN_NO_BROKER_SUBMIT")
        report["ended_at"] = _iso()
        status, answer = _build_decision(report)
        report["status"] = status
        report["answer"] = answer
        return report, artifacts

    run_id = record_trade_run_start(
        db_path,
        symbol=symbol.upper(),
        side="BUY",
        requested_quantity=qty,
        started_at=_iso(),
        environment=env_name,
        result_status="ORDER_SUBMITTED",
    )
    final_status = "FAILED"
    try:
        order_id, submit_resp = adapter.submit_limit_buy(symbol=symbol, qty=qty, limit_price=limit_price)
        artifacts.submit_response = submit_resp
        report["broker_order_id"] = order_id
        report["order_submitted"] = True
        record_order(
            db_path,
            order_id=order_id,
            run_id=run_id,
            symbol=symbol.upper(),
            side="BUY",
            quantity=qty,
            submitted_at=_iso(),
            status="SUBMITTED",
            environment=env_name,
            raw_status=f"SUBMITTED price={limit_price:.4f}",
        )

        initial = adapter.get_order_snapshot(order_id, symbol)
        artifacts.status_initial = initial
        report["order_status_initial"] = str(initial.get("mapped_status") or initial.get("state") or "UNKNOWN").upper()

        final_snapshot = initial
        cancel_response_payload = None
        requested_cancel = False
        loop_terminal_state: str | None = None

        deadline = time.monotonic() + max(1, hard_timeout_seconds)
        for _ in range(max(1, max_status_poll_attempts)):
            snapshot = adapter.get_order_snapshot(order_id, symbol)
            final_snapshot = snapshot
            mapped = str(snapshot.get("mapped_status") or snapshot.get("state") or "UNKNOWN").upper()
            if mapped in TERMINAL_STATES:
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(max(0, status_poll_interval_seconds))

        mapped_final = str(final_snapshot.get("mapped_status") or final_snapshot.get("state") or "UNKNOWN").upper()

        if mode == MODE_FILL_TEST:
            if mapped_final != "FILLED":
                # safe-cancel branch is WARNING unless safety breaks.
                requested_cancel = True

        if mode == MODE_CANCEL_TEST and mapped_final not in TERMINAL_STATES:
            requested_cancel = True

        if requested_cancel:
            report["cancel_requested"] = True

            def _poll(oid: str) -> dict[str, Any]:
                return adapter.get_order_snapshot(oid, symbol)

            def _cancel(oid: str) -> dict[str, Any]:
                nonlocal cancel_response_payload
                cancel_response_payload = adapter.cancel_order(
                    oid,
                    symbol=symbol,
                    qty=qty,
                    price=limit_price,
                    order_type="00",
                )
                return cancel_response_payload

            def _update(oid: str, st: str, raw: str | None) -> None:
                update_order_status(db_path, oid, st, raw_status=raw)

            def _reconcile(_: str) -> None:
                _run_reconciliation(db_path=db_path, run_id=run_id, symbol=symbol, adapter=adapter)

            def _late_fill(oid: str) -> None:
                fills = adapter.get_fills(oid, symbol)
                _apply_broker_fills(db_path=db_path, run_id=run_id, order_id=oid, symbol=symbol, fills=fills)

            loop_result = cancel_until_terminal(
                order_id,
                poll_status=_poll,
                request_cancel=_cancel,
                update_local_status=_update,
                reconcile=_reconcile,
                on_late_fill=_late_fill,
                max_attempts=max(1, max_cancel_attempts),
                max_elapsed_seconds=max(1, hard_timeout_seconds),
                sleep_fn=lambda backoff: time.sleep(max(float(backoff), float(max(0, cancel_poll_interval_seconds)))),
            )
            mapped_final = loop_result.final_state
            loop_terminal_state = loop_result.final_state
            if mapped_final == "FILLED":
                report["cancel_race_filled"] = True
                report["warnings"].append("CANCEL_RACE_FILLED")
            if mapped_final == "CANCELLED":
                report["cancel_confirmed"] = True
            artifacts.cancel_response = cancel_response_payload

        if mapped_final in TERMINAL_STATES or mapped_final in ACTIVE_ORDER_STATES:
            update_order_status(
                db_path,
                order_id,
                mapped_final,
                raw_status=str(final_snapshot.get("raw_status") or mapped_final),
            )
        else:
            update_order_status(
                db_path,
                order_id,
                "UNKNOWN",
                raw_status=str(final_snapshot.get("raw_status") or mapped_final or "UNKNOWN"),
            )

        artifacts.status_final = adapter.get_order_snapshot(order_id, symbol)
        snapshot_mapped = str(
            artifacts.status_final.get("mapped_status") or artifacts.status_final.get("state") or "UNKNOWN"
        ).upper()
        if snapshot_mapped == "UNKNOWN" and loop_terminal_state in TERMINAL_STATES:
            report["order_status_final"] = loop_terminal_state
        else:
            report["order_status_final"] = str(snapshot_mapped or mapped_final or "UNKNOWN").upper()

        fills = adapter.get_fills(order_id, symbol)
        artifacts.fills_response = fills
        applied_qty, avg_fill = _apply_broker_fills(
            db_path=db_path,
            run_id=run_id,
            order_id=order_id,
            symbol=symbol,
            fills=fills,
        )
        report["filled_qty"] = round(float(applied_qty), 6)
        report["fill_price"] = round(float(avg_fill), 6) if avg_fill is not None else 0.0

        recon = _run_reconciliation(db_path=db_path, run_id=run_id, symbol=symbol, adapter=adapter)
        artifacts.reconciliation_snapshot = {
            "status": recon.status,
            "severity": recon.severity,
            "block_new_orders": recon.block_new_orders,
            "summary_text": recon.summary_text,
            "events": list(recon.events),
        }
        report["reconciliation_status"] = recon.status
        if recon.severity == "CRITICAL":
            report["failure_reasons"].append("RECONCILIATION_CRITICAL_MISMATCH")
        if recon.block_new_orders:
            report["failure_reasons"].append("BROKER_LOCAL_POSITION_MISMATCH")

        unknown_events, _ = _collect_unknown_and_recon(db_path)
        recon_critical = _count_recon_critical_for_run(db_path, run_id)
        report["unknown_events"] = unknown_events
        report["reconciliation_critical_count"] = recon_critical
        if unknown_events > 0:
            report["failure_reasons"].append("UNKNOWN_EVENT")
        if recon_critical > 0 and recon.severity != "CRITICAL":
            report["warnings"].append("TRANSIENT_RECONCILIATION_CRITICAL_DURING_LOOP")

        if report["order_status_final"] not in TERMINAL_STATES:
            report["failure_reasons"].append("UNRESOLVED_FINAL_STATE")
        if mode == MODE_FILL_TEST and report["order_status_final"] == "CANCELLED":
            report["warnings"].append("FILL_TEST_ENDED_SAFE_CANCEL")
        if mode == MODE_CANCEL_TEST and report["order_status_final"] == "FILLED":
            report["warnings"].append("CANCEL_TEST_RACE_FILLED")
        if report["order_status_final"] == "UNKNOWN":
            report["failure_reasons"].append("CANCEL_LOOP_UNKNOWN_ESCALATION")

        if report["order_status_final"] in {"FILLED", "CANCELLED"}:
            final_status = report["order_status_final"]
        elif report["order_status_final"] in {"REJECTED", "EXPIRED"}:
            final_status = report["order_status_final"]
        else:
            final_status = "FAILED"
    except Exception as exc:
        report["failure_reasons"].append(f"SCRIPT_CRASH:{exc}")
    finally:
        report["failure_reasons"] = sorted(set(report["failure_reasons"]))
        report["warnings"] = sorted(set(report["warnings"]))
        status, answer = _build_decision(report)
        report["status"] = status
        report["answer"] = answer
        report["ended_at"] = _iso()
        record_trade_run_finish(db_path, run_id=run_id, result_status=final_status if final_status in {"FILLED", "CANCELLED", "FAILED", "EXPIRED"} else "FAILED", finished_at=_iso())
    return report, artifacts


def _write_fixtures(*, fixture_dir: Path, artifacts: RunArtifacts) -> list[str]:
    fixture_dir.mkdir(parents=True, exist_ok=True)
    out: list[str] = []
    out.append(_write_fixture(fixture_dir, name="task_091a_quote_response.json", response=artifacts.quote_response, captured=artifacts.quote_response is not None, reason=None if artifacts.quote_response is not None else "unavailable"))
    out.append(_write_fixture(fixture_dir, name="task_091a_order_submit_response.json", response=artifacts.submit_response, captured=artifacts.submit_response is not None, reason=None if artifacts.submit_response is not None else "unavailable"))
    out.append(_write_fixture(fixture_dir, name="task_091a_order_status_initial.json", response=artifacts.status_initial, captured=artifacts.status_initial is not None, reason=None if artifacts.status_initial is not None else "unavailable"))
    out.append(_write_fixture(fixture_dir, name="task_091a_order_status_final.json", response=artifacts.status_final, captured=artifacts.status_final is not None, reason=None if artifacts.status_final is not None else "unavailable"))
    out.append(_write_fixture(fixture_dir, name="task_091a_fills_response.json", response=artifacts.fills_response, captured=artifacts.fills_response is not None, reason=None if artifacts.fills_response is not None else "unavailable"))
    out.append(_write_fixture(fixture_dir, name="task_091a_cancel_response.json", response=artifacts.cancel_response, captured=artifacts.cancel_response is not None, reason=None if artifacts.cancel_response is not None else "cancel_not_attempted"))
    out.append(_write_fixture(fixture_dir, name="task_091a_reconciliation_snapshot.json", response=artifacts.reconciliation_snapshot, captured=artifacts.reconciliation_snapshot is not None, reason=None if artifacts.reconciliation_snapshot is not None else "unavailable"))
    return out


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T091-A Controlled Broker Lifecycle Validation")
    lines.append("")
    lines.append("## 3-line Summary")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- key_result: final_state={report.get('order_status_final')} submitted={report.get('order_submitted')}")
    lines.append("")
    lines.append("## 1. Objective")
    lines.append("- Broker lifecycle validation only (not strategy profitability).")
    lines.append("")
    lines.append("## 2. Safety Preflight")
    lines.append(f"- environment: {report['environment']}")
    lines.append(f"- qty: {report['qty']}")
    lines.append(f"- market_order_path: {report['market_order_path']}")
    lines.append(f"- missing_env: {', '.join(report.get('missing_env') or []) or '(none)'}")
    lines.append(f"- unknown_events: {report['unknown_events']}")
    lines.append(f"- reconciliation_critical_count: {report['reconciliation_critical_count']}")
    lines.append("")
    lines.append("## 3. Execution Trace")
    lines.append(f"- quote_fetched: {report.get('current_price', 0) > 0}")
    lines.append(f"- order_submitted: {report['order_submitted']}")
    lines.append(f"- broker_order_id: {report['broker_order_id']}")
    lines.append(f"- order_status_initial: {report['order_status_initial']}")
    lines.append(f"- order_status_final: {report['order_status_final']}")
    lines.append(f"- cancel_requested: {report['cancel_requested']}")
    lines.append(f"- cancel_confirmed: {report['cancel_confirmed']}")
    lines.append(f"- filled_qty: {report['filled_qty']}")
    lines.append(f"- fill_price: {report['fill_price']}")
    lines.append(f"- reconciliation_status: {report['reconciliation_status']}")
    lines.append("")
    lines.append("## 4. Broker vs Local State")
    lines.append(f"- final_state: {report['order_status_final']}")
    lines.append(f"- unknown_events: {report['unknown_events']}")
    lines.append(f"- reconciliation_critical_count: {report['reconciliation_critical_count']}")
    lines.append("")
    lines.append("## 5. Fixture Capture")
    for p in report.get("fixtures_written", []):
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## 6. Anomalies")
    lines.append(f"- cancel_race_filled: {report['cancel_race_filled']}")
    lines.append(f"- warnings: {', '.join(report['warnings']) or '(none)'}")
    lines.append("")
    lines.append("## 7. Decision")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- failure_reasons: {', '.join(report['failure_reasons']) or '(none)'}")
    lines.append("")
    lines.append("## 8. Final Answer")
    lines.append(f"- Is controlled broker lifecycle validated? {report['answer']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task T091-A controlled paper broker lifecycle validation")
    parser.add_argument("--mode", type=str, default=MODE_CANCEL_TEST, choices=sorted(ALLOWED_MODES))
    parser.add_argument("--symbol", type=str, default="AAPL")
    parser.add_argument("--qty", type=int, default=1)
    parser.add_argument("--max-notional", type=float, default=300.0)
    parser.add_argument("--env-file", type=str, default="config/kis_paper.env")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_091a/task_091a_controlled_lifecycle.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_091a/task_091a_controlled_lifecycle.md")
    parser.add_argument("--fixture-dir", type=str, default="tests/fixtures/kis/real")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status-poll-interval-seconds", type=int, default=2)
    parser.add_argument("--max-status-poll-attempts", type=int, default=10)
    parser.add_argument("--cancel-poll-interval-seconds", type=int, default=2)
    parser.add_argument("--max-cancel-attempts", type=int, default=30)
    parser.add_argument("--hard-timeout-seconds", type=int, default=90)
    args = parser.parse_args()

    _load_env_file(Path(args.env_file))
    initialize_store(args.db_path)
    adapter = KISBrokerAdapter(KISClient.from_env())
    report, artifacts = run_controlled_lifecycle(
        mode=args.mode,
        symbol=args.symbol.upper(),
        qty=args.qty,
        max_notional=float(args.max_notional),
        db_path=args.db_path,
        adapter=adapter,
        dry_run=bool(args.dry_run),
        status_poll_interval_seconds=max(0, int(args.status_poll_interval_seconds)),
        max_status_poll_attempts=max(1, int(args.max_status_poll_attempts)),
        cancel_poll_interval_seconds=max(0, int(args.cancel_poll_interval_seconds)),
        max_cancel_attempts=max(1, int(args.max_cancel_attempts)),
        hard_timeout_seconds=max(1, int(args.hard_timeout_seconds)),
    )
    fixtures = _write_fixtures(fixture_dir=Path(args.fixture_dir), artifacts=artifacts)
    report["fixtures_written"] = fixtures

    out_json = Path(args.json_out)
    out_md = Path(args.md_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={out_json}")
    print(f"written_md={out_md}")
    print(f"status={report['status']}")
    print(f"answer={report['answer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
