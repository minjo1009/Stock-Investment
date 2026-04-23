"""Run one end-to-end paper trade with KIS + Slack."""

from __future__ import annotations

import os
import sqlite3
import time
from datetime import UTC, datetime
import json

from app.reconciliation import ReconciliationOutcome, reconcile_local_and_broker
from integration.kis_client import KISClient
from integration import slack_client
from state.store import (
    FILL_INSERTED,
    POSITION_EVENT_INSERTED,
    apply_fill_to_position,
    build_order_intent_key,
    get_position,
    has_blocking_order_intent,
    has_recent_order_intent,
    initialize_store,
    list_local_filled_order_ids,
    list_open_orders,
    record_reconciliation_event,
    record_reconciliation_run,
    record_position_event,
    record_fill,
    record_order,
    record_trade_run_finish,
    record_trade_run_start,
    upsert_position,
    update_order_status,
)


def _order_decision_message(*, symbol: str, side: str, reason: str, price: float, quantity: int, env: str) -> str:
    return (
        "[ORDER DECISION]\n\n"
        f"symbol: {symbol}\n"
        f"side: {side}\n"
        f"reason: {reason}\n"
        f"price: {price}\n"
        f"quantity: {quantity}\n"
        f"env: {env}"
    )


def _fill_message(*, symbol: str, side: str, quantity: int, status: str, order_id: str) -> str:
    return (
        "[FILL CONFIRMED]\n\n"
        f"symbol: {symbol}\n"
        f"side: {side}\n"
        f"quantity: {quantity}\n"
        f"status: {status}\n"
        f"order_id: {order_id}"
    )


def _assert_trading_allowed(db_path: str) -> None:
    if not os.path.exists(db_path):
        return
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        row = cur.execute(
            "SELECT run_mode, kill_switch_active, kill_switch_reason FROM control_state WHERE control_key='default'"
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return
    run_mode, kill_switch_active, kill_switch_reason = row
    if int(kill_switch_active) == 1:
        raise RuntimeError(f"Trading blocked by kill switch: {kill_switch_reason or 'no reason'}")
    if str(run_mode).strip().upper() != "LIVE_ENABLED":
        raise RuntimeError(f"Trading blocked by control_state run_mode={run_mode}")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _is_true(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _send_recon_alert_if_enabled(*, outcome: ReconciliationOutcome, symbol: str) -> None:
    if not _is_true(os.environ.get("TRADING_RECON_ALERT")):
        return
    if outcome.status == "ERROR" or outcome.severity == "CRITICAL":
        first_event = outcome.events[0] if outcome.events else {}
        message = (
            "[RECON ALERT]\n\n"
            f"status: {outcome.status}\n"
            f"severity: {outcome.severity}\n"
            f"events: {len(outcome.events)}\n"
            f"symbol: {symbol}\n"
            f"details: {first_event.get('event_type', outcome.summary_text)}"
        )
        try:
            slack_client.send_message(message)
        except Exception as exc:
            print(f"[RECON ALERT ERROR] {exc}")


def _run_reconciliation_check(
    *,
    db_path: str,
    run_id: str,
    symbol: str,
    kis: KISClient,
) -> ReconciliationOutcome:
    started_at = _now_iso()
    try:
        broker_orders = kis.fetch_broker_order_statuses(symbol=symbol)
    except Exception as exc:
        finished_at = _now_iso()
        record_reconciliation_run(
            db_path,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status="ERROR",
            max_severity="CRITICAL",
            block_new_orders=True,
            summary_text=f"broker truth fetch failed: {exc}",
            raw_snapshot_json=json.dumps({"broker_orders": []}),
        )
        return ReconciliationOutcome(
            status="ERROR",
            severity="CRITICAL",
            block_new_orders=True,
            summary_text=f"broker truth fetch failed: {exc}",
            events=(),
        )

    try:
        local_open_orders = [row for row in list_open_orders(db_path) if str(row.get("symbol") or "").upper() == symbol.upper()]
        local_filled_order_ids = list_local_filled_order_ids(db_path, symbol=symbol)
    except Exception as exc:
        finished_at = _now_iso()
        snapshot_json = json.dumps({"broker_orders": broker_orders}, ensure_ascii=True, default=str)
        record_reconciliation_run(
            db_path,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status="ERROR",
            max_severity="CRITICAL",
            block_new_orders=True,
            summary_text=f"local state read failed: {exc}",
            raw_snapshot_json=snapshot_json,
        )
        return ReconciliationOutcome(
            status="ERROR",
            severity="CRITICAL",
            block_new_orders=True,
            summary_text=f"local state read failed: {exc}",
            events=(),
        )

    outcome = reconcile_local_and_broker(
        local_open_orders=local_open_orders,
        local_filled_order_ids=local_filled_order_ids,
        broker_orders=broker_orders,
    )
    finished_at = _now_iso()
    snapshot_json = json.dumps({"broker_orders": broker_orders}, ensure_ascii=True, default=str)
    reconciliation_id = record_reconciliation_run(
        db_path,
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        status=outcome.status,
        max_severity=outcome.severity,
        block_new_orders=outcome.block_new_orders,
        summary_text=outcome.summary_text,
        raw_snapshot_json=snapshot_json,
    )
    for event in outcome.events:
        record_reconciliation_event(
            db_path,
            reconciliation_id=reconciliation_id,
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


def run() -> None:
    symbol = "AAPL"
    quantity = 1
    signal = "BUY"
    reason = "dummy_signal_true"
    db_path = os.environ.get("TRADING_DB_PATH", "trading.db")

    initialize_store(db_path)
    _assert_trading_allowed(db_path)
    run_id = record_trade_run_start(
        db_path,
        symbol=symbol,
        side=signal,
        requested_quantity=quantity,
        started_at=_now_iso(),
        environment=os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper",
        result_status="ORDER_SUBMITTED",
    )
    run_result_status = "FAILED"
    order_id: str | None = None

    try:
        kis = KISClient.from_env()
        auth_state = kis.describe_auth_state()
        if auth_state.get("token_present") and not auth_state.get("expired"):
            print("[auth] cached token reused")
        else:
            print("[auth] token issue path (cache missing/expired)")

        recon = _run_reconciliation_check(db_path=db_path, run_id=run_id, symbol=symbol, kis=kis)
        _send_recon_alert_if_enabled(outcome=recon, symbol=symbol)
        if recon.block_new_orders:
            print("[RECON BLOCK] local/broker mismatch detected")
            run_result_status = "SKIPPED_RECON_BLOCK"
            return

        before_qty = 0
        try:
            before_qty = kis.get_position_quantity(symbol)
        except Exception:
            before_qty = 0

        price = kis.get_current_price(symbol)
        intent_key = build_order_intent_key(
            symbol=symbol,
            side=signal,
            intended_price=price,
            quantity=float(quantity),
            strategy_id="default",
        )

        if has_blocking_order_intent(db_path, intent_key=intent_key):
            print("[IDEMPOTENT BLOCK] duplicate order intent detected (open order exists)")
            run_result_status = "SKIPPED_DUPLICATE"
            return

        recent_window_sec_raw = os.environ.get("TRADING_INTENT_RECENT_SEC", "0")
        try:
            recent_window_sec = int(recent_window_sec_raw)
        except ValueError:
            recent_window_sec = 0
        if recent_window_sec > 0 and has_recent_order_intent(
            db_path,
            intent_key=intent_key,
            within_seconds=recent_window_sec,
            now_iso=_now_iso(),
        ):
            print(
                f"[IDEMPOTENT BLOCK] duplicate order intent detected (recent window={recent_window_sec}s)"
            )
            run_result_status = "SKIPPED_DUPLICATE"
            return

        slack_client.send_message(
            _order_decision_message(
                symbol=symbol,
                side=signal,
                reason=reason,
                price=price,
                quantity=quantity,
                env=kis.environment,
            )
        )

        order_id = kis.submit_order(symbol=symbol, side=signal, quantity=quantity, limit_price=price)
        record_order(
            db_path,
            order_id=order_id,
            run_id=run_id,
            symbol=symbol,
            side=signal,
            quantity=quantity,
            intent_key=intent_key,
            submitted_at=_now_iso(),
            status="SUBMITTED",
            environment=kis.environment,
            raw_status="SUBMITTED",
        )
        run_result_status = "ORDER_SUBMITTED"

        final_status = "PENDING"
        fill_source: str | None = None
        for _ in range(10):
            final_status = kis.get_order_status(order_id)
            if final_status == "FILLED":
                fill_source = "ORDER_STATUS"
                break
            try:
                current_qty = kis.get_position_quantity(symbol)
                if current_qty >= before_qty + quantity:
                    final_status = "FILLED"
                    fill_source = "POSITION_DELTA_FALLBACK"
                    break
            except Exception:
                pass
            time.sleep(1)

        if final_status == "FILLED":
            update_order_status(db_path, order_id, "FILLED", raw_status=final_status)
            filled_at = _now_iso()
            source = fill_source or "ORDER_STATUS"
            synthetic_fill_id = f"{order_id}:{filled_at}:{source}"
            fill_write_result = record_fill(
                db_path,
                fill_id=synthetic_fill_id,
                order_id=order_id,
                run_id=run_id,
                symbol=symbol,
                side=signal,
                filled_quantity=quantity,
                fill_price=price,
                filled_at=filled_at,
                source=source,
            )
            if fill_write_result == FILL_INSERTED:
                current = get_position(db_path, symbol)
                old_quantity = 0.0 if current is None else float(current["quantity"])
                old_avg_price = 0.0 if current is None else float(current["avg_price"])
                new_quantity, new_avg_price = apply_fill_to_position(
                    old_quantity=old_quantity,
                    old_avg_price=old_avg_price,
                    fill_side=signal,
                    fill_quantity=float(quantity),
                    fill_price=price,
                )
                upsert_position(
                    db_path,
                    symbol=symbol,
                    side="LONG",
                    quantity=new_quantity,
                    avg_price=new_avg_price,
                    updated_at=filled_at,
                )
                event_result = record_position_event(
                    db_path,
                    run_id=run_id,
                    order_id=order_id,
                    fill_id=synthetic_fill_id,
                    symbol=symbol,
                    side="LONG",
                    fill_qty=float(quantity),
                    fill_price=price,
                    position_qty_after=new_quantity,
                    avg_price_after=new_avg_price,
                    created_at=filled_at,
                )
                if event_result != POSITION_EVENT_INSERTED:
                    print(f"[position] duplicate position event ignored: fill_id={synthetic_fill_id}")
            else:
                print(f"[position] duplicate fill ignored, position unchanged: fill_id={synthetic_fill_id}")
            slack_client.send_message(
                _fill_message(symbol=symbol, side=signal, quantity=quantity, status=final_status, order_id=order_id)
            )
            run_result_status = "FILLED"
            return

        if order_id is not None:
            update_order_status(db_path, order_id, "TIMEOUT", raw_status=final_status)
        timeout_text = (
            "[FILL CONFIRMED]\n\n"
            f"symbol: {symbol}\n"
            f"side: {signal}\n"
            f"quantity: {quantity}\n"
            "status: TIMEOUT\n"
            f"order_id: {order_id}"
        )
        slack_client.send_message(timeout_text)
        run_result_status = "TIMEOUT"
        raise RuntimeError(f"Order fill polling timeout for order_id={order_id}")
    except Exception:
        if order_id is not None and run_result_status not in ("FILLED", "TIMEOUT"):
            try:
                update_order_status(db_path, order_id, "FAILED", raw_status="FAILED")
            except Exception:
                pass
        run_result_status = "FAILED" if run_result_status == "ORDER_SUBMITTED" else run_result_status
        raise
    finally:
        record_trade_run_finish(db_path, run_id=run_id, result_status=run_result_status, finished_at=_now_iso())


if __name__ == "__main__":
    run()
