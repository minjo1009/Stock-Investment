"""Run one end-to-end paper trade with KIS + Slack."""

from __future__ import annotations

import os
import sqlite3
import time
from datetime import UTC, datetime
import json

try:
    from src.app.continuation_runtime_capture_370 import emit_continuation_capture_event
    from src.app.reconciliation import ReconciliationOutcome, reconcile_local_and_broker
    from src.backtest.canonical_position_lifecycle_event_sourcing import build_canonical_lifecycle_id
    from src.execution.cancel_loop import cancel_until_terminal
    from src.integration import slack_client
    from src.integration.kis_client import KISClient
    from src.state.store import (
        FILL_INSERTED,
        POSITION_EVENT_INSERTED,
        apply_fill_to_position,
        build_order_intent_key,
        get_position,
        get_fills_for_order,
        has_blocking_order_intent,
        has_order_with_status,
        has_recent_order_intent,
        initialize_store,
        list_local_filled_order_ids,
        list_open_orders,
        list_recent_reconciliation_runs,
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
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from app.continuation_runtime_capture_370 import emit_continuation_capture_event
    from app.reconciliation import ReconciliationOutcome, reconcile_local_and_broker
    from backtest.canonical_position_lifecycle_event_sourcing import build_canonical_lifecycle_id
    from execution.cancel_loop import cancel_until_terminal
    from integration import slack_client
    from integration.kis_client import KISClient
    from state.store import (
        FILL_INSERTED,
        POSITION_EVENT_INSERTED,
        apply_fill_to_position,
        build_order_intent_key,
        get_position,
        get_fills_for_order,
        has_blocking_order_intent,
        has_order_with_status,
        has_recent_order_intent,
        initialize_store,
        list_local_filled_order_ids,
        list_open_orders,
        list_recent_reconciliation_runs,
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
        raise RuntimeError("Trading blocked: state DB is missing")
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        table_exists = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='control_state' LIMIT 1"
        ).fetchone()
        if table_exists is None:
            raise RuntimeError("Trading blocked: control_state table is missing")
        row = cur.execute(
            "SELECT run_mode, kill_switch_active, kill_switch_reason FROM control_state WHERE control_key='default'"
        ).fetchone()
    finally:
        con.close()
    if row is None:
        raise RuntimeError("Trading blocked: control_state default row is missing")
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


def _broker_order_snapshot(*, kis: KISClient, order_id: str, symbol: str) -> dict[str, object]:
    row = kis.get_order_snapshot(order_id, symbol=symbol)
    mapped = str(row.get("mapped_status") or "UNKNOWN").upper()
    order_qty = float(row.get("order_qty") or 0.0)
    filled_qty = float(row.get("filled_qty") or 0.0)
    if order_qty > 0 and 0 < filled_qty < order_qty and mapped in {"SUBMITTED", "PENDING"}:
        mapped = "PARTIAL"
    return {
        "state": mapped,
        "raw_status": str(row.get("raw_status") or ""),
        "filled_qty": filled_qty,
        "order_qty": order_qty,
    }


def _request_cancel(
    *,
    kis: KISClient,
    order_id: str,
    symbol: str,
    qty: float,
    price: float,
    order_type: str,
) -> dict[str, object]:
    return kis.cancel_order(
        order_id=order_id,
        account=kis.account_number,
        symbol=symbol,
        qty=qty,
        price=price,
        order_type=order_type,
    )


def _record_fill_and_position(
    *,
    db_path: str,
    run_id: str,
    order_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float | None,
    source: str,
) -> None:
    filled_at = _now_iso()
    synthetic_fill_id = f"{order_id}:{filled_at}:{source}"
    fill_write_result = record_fill(
        db_path,
        fill_id=synthetic_fill_id,
        order_id=order_id,
        run_id=run_id,
        symbol=symbol,
        side=side,
        filled_quantity=quantity,
        fill_price=price,
        filled_at=filled_at,
        source=source,
    )
    if fill_write_result == FILL_INSERTED:
        current = get_position(db_path, symbol)
        old_quantity = 0.0 if current is None else float(current["quantity"])
        old_avg_price = 0.0 if current is None else float(current["avg_price"])
        normalized_price = price if price is not None else old_avg_price
        new_quantity, new_avg_price = apply_fill_to_position(
            old_quantity=old_quantity,
            old_avg_price=old_avg_price,
            fill_side=side,
            fill_quantity=float(quantity),
            fill_price=normalized_price,
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
            fill_price=normalized_price,
            position_qty_after=new_quantity,
            avg_price_after=new_avg_price,
            created_at=filled_at,
        )
        if event_result != POSITION_EVENT_INSERTED:
            print(f"[position] duplicate position event ignored: fill_id={synthetic_fill_id}")
    else:
        print(f"[position] duplicate fill ignored, position unchanged: fill_id={synthetic_fill_id}")


def _apply_broker_fill_correction(
    *,
    kis: KISClient,
    db_path: str,
    run_id: str,
    order_id: str,
    symbol: str,
    side: str,
    fallback_price: float,
    late_fill: bool = False,
) -> float:
    broker_fills = kis.get_fills(order_id, symbol=symbol)
    if not broker_fills:
        return 0.0
    local_fills = get_fills_for_order(db_path, order_id)
    local_total = sum(float(row.get("filled_quantity") or 0.0) for row in local_fills)
    broker_total = sum(float(fill.get("filled_qty") or 0.0) for fill in broker_fills)
    delta = broker_total - local_total
    if delta <= 1e-9:
        return 0.0

    weighted_value = 0.0
    weighted_qty = 0.0
    for fill in broker_fills:
        qty = float(fill.get("filled_qty") or 0.0)
        px = fill.get("fill_price")
        if qty > 0 and px not in (None, ""):
            weighted_value += qty * float(px)
            weighted_qty += qty
    avg_fill_price = (weighted_value / weighted_qty) if weighted_qty > 0 else fallback_price
    _record_fill_and_position(
        db_path=db_path,
        run_id=run_id,
        order_id=order_id,
        symbol=symbol,
        side=side,
        quantity=delta,
        price=avg_fill_price,
        source="ORDER_STATUS",
    )
    if late_fill:
        now = _now_iso()
        recon_id = record_reconciliation_run(
            db_path,
            run_id=run_id,
            started_at=now,
            finished_at=now,
            status="MISMATCH",
            max_severity="CRITICAL",
            block_new_orders=False,
            summary_text="late fill detected after cancel confirmation",
            raw_snapshot_json=json.dumps({"order_id": order_id, "late_fill_qty": delta}),
        )
        record_reconciliation_event(
            db_path,
            reconciliation_id=recon_id,
            symbol=symbol,
            local_order_id=order_id,
            broker_order_id=order_id,
            event_type="LATE_FILL",
            severity="CRITICAL",
            local_status="CANCELLED",
            broker_status="FILLED",
            details={"late_fill_qty": delta, "avg_fill_price": avg_fill_price},
            created_at=now,
        )
        print(
            f"[LATE_FILL_APPLIED] order_id={order_id} "
            f"late_fill_qty={delta:.6f} avg_fill_price={avg_fill_price:.4f}"
        )
    return delta


def _run_reconciliation_check(
    *,
    db_path: str,
    run_id: str,
    symbol: str,
    kis: KISClient,
) -> tuple[ReconciliationOutcome, str | None]:
    started_at = _now_iso()
    try:
        broker_orders = kis.fetch_broker_order_statuses(symbol=symbol)
    except Exception as exc:
        finished_at = _now_iso()
        reconciliation_id = record_reconciliation_run(
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
        ), reconciliation_id

    try:
        local_open_orders = [row for row in list_open_orders(db_path) if str(row.get("symbol") or "").upper() == symbol.upper()]
        local_filled_order_ids = list_local_filled_order_ids(db_path, symbol=symbol)
    except Exception as exc:
        finished_at = _now_iso()
        snapshot_json = json.dumps({"broker_orders": broker_orders}, ensure_ascii=True, default=str)
        reconciliation_id = record_reconciliation_run(
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
        ), reconciliation_id

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
    return outcome, reconciliation_id


def _table_exists(db_path: str, table_name: str) -> bool:
    if not os.path.exists(db_path):
        return False
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table_name,),
        ).fetchone()
        return row is not None
    finally:
        con.close()


def _load_runtime_candidate(db_path: str) -> tuple[dict[str, object] | None, bool]:
    """Return best runtime candidate from indicator_snapshots.

    Returns:
    - (candidate, runtime_mode_active)
    - runtime_mode_active=True means indicator snapshots exist and should control entry/no-entry.
    """
    if not _table_exists(db_path, "indicator_snapshots"):
        return None, False

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cols = {
            str(r[1]).lower()
            for r in con.execute("PRAGMA table_info(indicator_snapshots)").fetchall()
        }
        has_selected_col = "selected_for_portfolio" in cols
        latest = con.execute("SELECT MAX(created_at) AS created_at FROM indicator_snapshots").fetchone()
        latest_created = str(latest["created_at"] if isinstance(latest, sqlite3.Row) else (latest[0] if latest else "") or "")
        if not latest_created:
            return None, False

        selected_filter = "AND COALESCE(selected_for_portfolio, 0) = 1" if has_selected_col else ""
        candidate_row = con.execute(
            f"""
            SELECT symbol, action, side, reason, score, close
            FROM indicator_snapshots
            WHERE created_at = ? AND entry_allowed = 1 AND data_fresh = 1
              {selected_filter}
            ORDER BY score DESC, symbol ASC
            LIMIT 1
            """,
            (latest_created,),
        ).fetchone()
        if candidate_row is None:
            return None, True
        return dict(candidate_row), True
    finally:
        con.close()


def run() -> None:
    symbol = "NO_RUNTIME_SIGNAL"
    quantity = 1
    signal = "NONE"
    reason = "runtime_signal_required"
    db_path = os.environ.get("TRADING_DB_PATH", "trading.db")
    runtime_environment = os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper"
    if runtime_environment != "paper":
        raise RuntimeError("Trading blocked: real-capital/live KIS environment is forbidden")

    initialize_store(db_path)
    if has_order_with_status(db_path, status="UNKNOWN"):
        raise RuntimeError("TRADING HALTED: UNKNOWN ORDER EXISTS")
    _assert_trading_allowed(db_path)

    runtime_candidate, runtime_mode_active = _load_runtime_candidate(db_path)
    if not runtime_mode_active:
        run_id = record_trade_run_start(
            db_path,
            symbol="NO_RUNTIME_SNAPSHOT",
            side="NONE",
            requested_quantity=0,
            started_at=_now_iso(),
            environment=runtime_environment,
            result_status="SKIPPED_NO_RUNTIME_SNAPSHOT",
        )
        emit_continuation_capture_event(
            db_path=db_path,
            environment=runtime_environment,
            run_id=run_id,
            event_type="INVALIDATION",
            symbol="NO_RUNTIME_SNAPSHOT",
            side="NONE",
            reason="runtime_signal_required_no_indicator_snapshots",
            result_status="SKIPPED_NO_RUNTIME_SNAPSHOT",
            payload={"runtime_mode_active": False},
        )
        record_trade_run_finish(db_path, run_id=run_id, result_status="SKIPPED_NO_RUNTIME_SNAPSHOT", finished_at=_now_iso())
        print("[NO RUNTIME SNAPSHOT] runtime indicator snapshot required; dummy fallback is disabled.")
        return
    if runtime_mode_active:
        if runtime_candidate is None:
            run_id = record_trade_run_start(
                db_path,
                symbol="NO_SIGNAL",
                side="NONE",
                requested_quantity=0,
                started_at=_now_iso(),
                environment=runtime_environment,
                result_status="SKIPPED_NO_SIGNAL",
            )
            emit_continuation_capture_event(
                db_path=db_path,
                environment=runtime_environment,
                run_id=run_id,
                event_type="INVALIDATION",
                symbol="NO_SIGNAL",
                side="NONE",
                reason="runtime_no_candidate",
                result_status="SKIPPED_NO_SIGNAL",
                payload={"runtime_mode_active": True},
            )
            record_trade_run_finish(db_path, run_id=run_id, result_status="SKIPPED_NO_SIGNAL", finished_at=_now_iso())
            print("[NO SIGNAL] runtime indicator snapshot exists but no entry candidate.")
            return
        symbol = str(runtime_candidate.get("symbol") or symbol).upper()
        signal = str(runtime_candidate.get("side") or "BUY").upper()
        if signal not in {"BUY", "SELL"}:
            signal = "BUY"
        reason = str(runtime_candidate.get("reason") or "runtime_signal")

    run_id = record_trade_run_start(
        db_path,
        symbol=symbol,
        side=signal,
        requested_quantity=quantity,
        started_at=_now_iso(),
        environment=runtime_environment,
        result_status="ORDER_SUBMITTED",
    )
    run_result_status = "FAILED"
    order_id: str | None = None
    canonical_lifecycle_id: str | None = None

    try:
        kis = KISClient.from_env()
        emit_continuation_capture_event(
            db_path=db_path,
            environment=runtime_environment,
            run_id=run_id,
            event_type="SETUP_DETECTED",
            symbol=symbol,
            side=signal,
            reason=reason,
            result_status=run_result_status,
            payload={
                "requested_quantity": quantity,
                "runtime_mode_active": runtime_mode_active,
            },
        )
        auth_state = kis.describe_auth_state()
        if auth_state.get("token_present") and not auth_state.get("expired"):
            print("[auth] cached token reused")
        else:
            print("[auth] token issue path (cache missing/expired)")

        recon, reconciliation_id = _run_reconciliation_check(db_path=db_path, run_id=run_id, symbol=symbol, kis=kis)
        _send_recon_alert_if_enabled(outcome=recon, symbol=symbol)
        if recon.block_new_orders:
            print("[RECON BLOCK] local/broker mismatch detected")
            run_result_status = "SKIPPED_RECON_BLOCK"
            emit_continuation_capture_event(
                db_path=db_path,
                environment=runtime_environment,
                run_id=run_id,
                event_type="INVALIDATION",
                symbol=symbol,
                side=signal,
                reason="reconciliation_block",
                result_status=run_result_status,
                payload={
                    "reconciliation_status": recon.status,
                    "reconciliation_severity": recon.severity,
                    "reconciliation_id": reconciliation_id,
                },
            )
            return

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
            emit_continuation_capture_event(
                db_path=db_path,
                environment=runtime_environment,
                run_id=run_id,
                event_type="INVALIDATION",
                symbol=symbol,
                side=signal,
                reason="duplicate_open_order_intent",
                result_status=run_result_status,
                payload={"intent_key": intent_key},
            )
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
            emit_continuation_capture_event(
                db_path=db_path,
                environment=runtime_environment,
                run_id=run_id,
                event_type="INVALIDATION",
                symbol=symbol,
                side=signal,
                reason="duplicate_recent_order_intent",
                result_status=run_result_status,
                payload={
                    "intent_key": intent_key,
                    "recent_window_sec": recent_window_sec,
                },
            )
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

        current_position = get_position(db_path, symbol)
        position_before_submit = 0.0 if current_position is None else float(current_position["quantity"])
        if position_before_submit > 0:
            emit_continuation_capture_event(
                db_path=db_path,
                environment=runtime_environment,
                run_id=run_id,
                event_type="ADD_ATTEMPT",
                symbol=symbol,
                side=signal,
                reason="existing_position_add_attempt",
                result_status=run_result_status,
                payload={
                    "position_quantity_before": position_before_submit,
                    "size_multiplier": position_before_submit,
                    "intent_key": intent_key,
                    "trade_run_id": run_id,
                },
            )

        order_id = kis.submit_order(symbol=symbol, side=signal, quantity=quantity, limit_price=price)
        submitted_at = _now_iso()
        canonical_lifecycle_id = build_canonical_lifecycle_id(
            symbol=symbol,
            entry_timestamp=submitted_at,
            entry_order_id=order_id,
            trade_run_id=run_id,
        )
        record_order(
            db_path,
            order_id=order_id,
            run_id=run_id,
            symbol=symbol,
            side=signal,
            quantity=quantity,
            intent_key=intent_key,
            submitted_at=submitted_at,
            status="SUBMITTED",
            environment=kis.environment,
            raw_status="SUBMITTED",
        )
        run_result_status = "ORDER_SUBMITTED"
        emit_continuation_capture_event(
            db_path=db_path,
            environment=runtime_environment,
            run_id=run_id,
            event_type="PROBE_ENTRY",
            symbol=symbol,
            side=signal,
            reason="order_submitted",
            order_id=order_id,
            result_status=run_result_status,
            payload={
                "intent_key": intent_key,
                "limit_price": price,
                "trade_run_id": run_id,
                "event_timestamp": submitted_at,
                "canonical_lifecycle_id": canonical_lifecycle_id,
            },
        )

        final_status = "PENDING"
        for _ in range(10):
            snap = _broker_order_snapshot(kis=kis, order_id=order_id, symbol=symbol)
            final_status = str(snap.get("state") or "UNKNOWN").upper()
            if final_status == "PARTIAL":
                update_order_status(db_path, order_id, "PARTIAL", raw_status=str(snap.get("raw_status") or "PARTIAL"))
            if final_status == "FILLED":
                break
            time.sleep(1)

        if final_status == "FILLED":
            update_order_status(db_path, order_id, "FILLED", raw_status=final_status)
            position_before_fill_row = get_position(db_path, symbol)
            position_before_fill = 0.0 if position_before_fill_row is None else float(position_before_fill_row["quantity"])
            _apply_broker_fill_correction(
                kis=kis,
                db_path=db_path,
                run_id=run_id,
                order_id=order_id,
                symbol=symbol,
                side=signal,
                fallback_price=price,
            )
            position_after_fill_row = get_position(db_path, symbol)
            position_after_fill = 0.0 if position_after_fill_row is None else float(position_after_fill_row["quantity"])
            order_fills = get_fills_for_order(db_path, order_id)
            latest_fill_id = str(order_fills[-1].get("fill_id") or "") if order_fills else ""
            slack_client.send_message(
                _fill_message(symbol=symbol, side=signal, quantity=quantity, status=final_status, order_id=order_id)
            )
            run_result_status = "FILLED"
            emit_continuation_capture_event(
                db_path=db_path,
                environment=runtime_environment,
                run_id=run_id,
                event_type="FILL_CONFIRMED",
                symbol=symbol,
                side=signal,
                reason="broker_filled",
                order_id=order_id,
                result_status=run_result_status,
                payload={
                    "filled_quantity": quantity,
                    "fill_status": final_status,
                    "fill_id": latest_fill_id,
                    "intent_key": intent_key,
                    "trade_run_id": run_id,
                    "canonical_lifecycle_id": canonical_lifecycle_id,
                    "position_quantity_before": position_before_fill,
                    "position_quantity_after": position_after_fill,
                    "prior_size_multiplier": position_before_fill,
                    "next_size_multiplier": position_after_fill,
                },
            )
            return

        if order_id is not None:
            def _poll_status(oid: str) -> dict[str, object]:
                return _broker_order_snapshot(kis=kis, order_id=oid, symbol=symbol)

            def _cancel_req(oid: str) -> None:
                return _request_cancel(
                    kis=kis,
                    order_id=oid,
                    symbol=symbol,
                    qty=float(quantity),
                    price=price,
                    order_type=os.environ.get("KIS_ORDER_DVSN", "00"),
                )

            def _update_local(oid: str, status: str, raw_status: str | None) -> None:
                update_order_status(db_path, oid, status, raw_status=raw_status)

            def _reconcile(_oid: str) -> None:
                _run_reconciliation_check(db_path=db_path, run_id=run_id, symbol=symbol, kis=kis)

            def _late_fill(oid: str) -> None:
                _apply_broker_fill_correction(
                    kis=kis,
                    db_path=db_path,
                    run_id=run_id,
                    order_id=oid,
                    symbol=symbol,
                    side=signal,
                    fallback_price=price,
                    late_fill=True,
                )

            result = cancel_until_terminal(
                order_id,
                poll_status=_poll_status,
                request_cancel=_cancel_req,
                update_local_status=_update_local,
                reconcile=_reconcile,
                on_late_fill=_late_fill,
            )
            final_terminal = result.final_state
            if final_terminal == "FILLED":
                position_before_fill_row = get_position(db_path, symbol)
                position_before_fill = 0.0 if position_before_fill_row is None else float(position_before_fill_row["quantity"])
                _apply_broker_fill_correction(
                    kis=kis,
                    db_path=db_path,
                    run_id=run_id,
                    order_id=order_id,
                    symbol=symbol,
                    side=signal,
                    fallback_price=price,
                )
                position_after_fill_row = get_position(db_path, symbol)
                position_after_fill = 0.0 if position_after_fill_row is None else float(position_after_fill_row["quantity"])
                order_fills = get_fills_for_order(db_path, order_id)
                latest_fill_id = str(order_fills[-1].get("fill_id") or "") if order_fills else ""
                run_result_status = "FILLED"
                slack_client.send_message(
                    _fill_message(symbol=symbol, side=signal, quantity=quantity, status="FILLED", order_id=order_id)
                )
                emit_continuation_capture_event(
                    db_path=db_path,
                    environment=runtime_environment,
                    run_id=run_id,
                    event_type="FILL_CONFIRMED",
                    symbol=symbol,
                    side=signal,
                    reason="filled_during_cancel_loop",
                    order_id=order_id,
                    result_status=run_result_status,
                    payload={
                        "filled_quantity": quantity,
                        "terminal_state": final_terminal,
                        "fill_id": latest_fill_id,
                        "intent_key": intent_key,
                        "trade_run_id": run_id,
                        "canonical_lifecycle_id": canonical_lifecycle_id,
                        "position_quantity_before": position_before_fill,
                        "position_quantity_after": position_after_fill,
                        "prior_size_multiplier": position_before_fill,
                        "next_size_multiplier": position_after_fill,
                    },
                )
                return
            if final_terminal == "CANCELLED":
                late_qty = _apply_broker_fill_correction(
                    kis=kis,
                    db_path=db_path,
                    run_id=run_id,
                    order_id=order_id,
                    symbol=symbol,
                    side=signal,
                    fallback_price=price,
                    late_fill=True,
                )
                latest_recon = list_recent_reconciliation_runs(db_path, limit=1)
                reconciliation_id = str(latest_recon[0].get("reconciliation_id") or "") if latest_recon else ""
                run_result_status = "FILLED" if late_qty > 0 else "CANCELLED"
                slack_client.send_message(
                    "[CANCEL CONFIRMED]\n\n"
                    f"symbol: {symbol}\n"
                    f"side: {signal}\n"
                    f"quantity: {quantity}\n"
                    f"status: {final_terminal}\n"
                    f"order_id: {order_id}"
                )
                emit_continuation_capture_event(
                    db_path=db_path,
                    environment=runtime_environment,
                    run_id=run_id,
                    event_type="CANCEL_CONFIRMED",
                    symbol=symbol,
                    side=signal,
                    reason="cancel_loop_terminal",
                    order_id=order_id,
                    result_status=run_result_status,
                    payload={
                        "late_fill_quantity": late_qty,
                        "terminal_state": final_terminal,
                        "intent_key": intent_key,
                        "trade_run_id": run_id,
                        "canonical_lifecycle_id": canonical_lifecycle_id,
                        "reconciliation_id": reconciliation_id,
                    },
                )
                return
            run_result_status = "UNKNOWN"
            raise RuntimeError(f"Cancel loop unresolved for order_id={order_id}, state={final_terminal}")
    except Exception:
        emit_continuation_capture_event(
            db_path=db_path,
            environment=runtime_environment,
            run_id=run_id,
            event_type="RUNTIME_ERROR",
            symbol=symbol,
            side=signal,
            reason="exception_raised",
            order_id=order_id,
            result_status=run_result_status,
        )
        if order_id is not None and run_result_status == "UNKNOWN":
            try:
                update_order_status(db_path, order_id, "UNKNOWN", raw_status="UNKNOWN")
            except Exception:
                pass
        elif order_id is not None and run_result_status not in ("FILLED", "TIMEOUT"):
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
