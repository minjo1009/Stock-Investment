from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable


TERMINAL_STATES = {"FILLED", "CANCELLED", "REJECTED", "EXPIRED"}
ACTIVE_CANCEL_STATES = {"SUBMITTED", "PENDING", "PARTIAL", "CANCEL_REQUESTED", "CANCEL_IN_PROGRESS"}


@dataclass(frozen=True)
class CancelLoopResult:
    final_state: str
    attempts: int
    elapsed_seconds: float


def _normalize_state(payload: Any) -> tuple[str, str | None]:
    if isinstance(payload, dict):
        raw = str(payload.get("raw_status") or "").strip() or None
        mapped = str(payload.get("state") or payload.get("mapped_status") or "UNKNOWN").strip().upper()
        filled_qty = payload.get("filled_qty")
        order_qty = payload.get("order_qty")
        try:
            if (
                filled_qty is not None
                and order_qty is not None
                and float(order_qty) > 0
                and 0 < float(filled_qty) < float(order_qty)
                and mapped in {"SUBMITTED", "PENDING"}
            ):
                mapped = "PARTIAL"
        except Exception:
            pass
        return mapped or "UNKNOWN", raw
    return str(payload or "UNKNOWN").strip().upper() or "UNKNOWN", None


def _backoff_seconds(attempt: int, *, cap: int) -> int:
    # 2,2,4,4,8,8,10,10,...
    step = 2 ** ((max(attempt, 1) + 1) // 2)
    return min(cap, max(2, step))


def cancel_until_terminal(
    order_id: str,
    *,
    poll_status: Callable[[str], Any],
    request_cancel: Callable[[str], None],
    update_local_status: Callable[[str, str, str | None], None],
    reconcile: Callable[[str], None],
    on_late_fill: Callable[[str], None] | None = None,
    max_attempts: int = 30,
    max_elapsed_seconds: int = 60,
    sleep_fn: Callable[[float], None] = time.sleep,
    monotonic_fn: Callable[[], float] = time.monotonic,
    log_fn: Callable[[str], None] = print,
) -> CancelLoopResult:
    start = monotonic_fn()
    attempts = 0
    local_state = "CANCEL_REQUESTED"
    update_local_status(order_id, "CANCEL_REQUESTED", None)
    log_fn(f"[CANCEL_REQUESTED] order_id={order_id}")

    while True:
        attempts += 1
        elapsed = monotonic_fn() - start

        if attempts > max_attempts or elapsed > max_elapsed_seconds:
            update_local_status(order_id, "UNKNOWN", "CANCEL_LOOP_TIMEOUT")
            reconcile(order_id)
            log_fn(f"[UNKNOWN_ESCALATED] order_id={order_id} attempts={attempts} elapsed={elapsed:.1f}s")
            return CancelLoopResult(final_state="UNKNOWN", attempts=attempts, elapsed_seconds=elapsed)

        broker_payload = poll_status(order_id)
        broker_state, raw_status = _normalize_state(broker_payload)

        if local_state == "CANCELLED" and broker_state == "FILLED" and on_late_fill is not None:
            on_late_fill(order_id)

        if broker_state in TERMINAL_STATES:
            if broker_state == "CANCELLED" and on_late_fill is not None:
                try:
                    filled_qty = float((broker_payload or {}).get("filled_qty") or 0.0)
                except Exception:
                    filled_qty = 0.0
                if filled_qty > 0:
                    on_late_fill(order_id)
                    log_fn(f"[LATE_FILL_APPLIED] order_id={order_id} filled_qty={filled_qty}")
            update_local_status(order_id, broker_state, raw_status)
            reconcile(order_id)
            if broker_state == "FILLED" and local_state in {"CANCEL_REQUESTED", "CANCEL_IN_PROGRESS", "CANCELLED"}:
                log_fn(f"[CANCEL_RACE_FILLED] order_id={order_id} raw_status={raw_status or broker_state}")
            elif broker_state == "CANCELLED":
                log_fn(f"[CANCEL_CONFIRMED] order_id={order_id}")
            return CancelLoopResult(final_state=broker_state, attempts=attempts, elapsed_seconds=elapsed)

        if broker_state in ACTIVE_CANCEL_STATES or broker_state == "UNKNOWN":
            if local_state != "CANCEL_IN_PROGRESS":
                update_local_status(order_id, "CANCEL_IN_PROGRESS", raw_status or broker_state)
                local_state = "CANCEL_IN_PROGRESS"
                log_fn(f"[CANCEL_IN_PROGRESS] order_id={order_id} broker_state={broker_state}")
            try:
                log_fn(f"[CANCEL_API_REQUEST] order_id={order_id} attempt={attempts}")
                cancel_response = request_cancel(order_id)
                if isinstance(cancel_response, dict):
                    success = bool(cancel_response.get("success", False))
                    response_status = str(cancel_response.get("broker_status") or "UNKNOWN").strip().upper()
                    log_fn(
                        f"[CANCEL_API_RESPONSE] order_id={order_id} success={success} "
                        f"broker_status={response_status}"
                    )
                    if success and response_status in TERMINAL_STATES:
                        update_local_status(order_id, response_status, response_status)
                        reconcile(order_id)
                        if response_status == "FILLED":
                            log_fn(f"[CANCEL_RACE_FILLED] order_id={order_id} raw_status={response_status}")
                        elif response_status == "CANCELLED":
                            log_fn(f"[CANCEL_CONFIRMED] order_id={order_id}")
                        return CancelLoopResult(final_state=response_status, attempts=attempts, elapsed_seconds=elapsed)
                    if not success:
                        log_fn(
                            f"[CANCEL_FAILED] order_id={order_id} attempt={attempts} "
                            f"broker_status={response_status}"
                        )
                else:
                    log_fn(f"[CANCEL_API_RESPONSE] order_id={order_id} success=True broker_status=UNKNOWN")
            except Exception as exc:
                log_fn(f"[CANCEL_FAILED] order_id={order_id} attempt={attempts} error={exc}")
                log_fn(f"[CANCEL_RETRY] order_id={order_id} attempt={attempts} error={exc}")
            reconcile(order_id)
            sleep_fn(_backoff_seconds(attempts, cap=10))
            continue

        # Defensive fallback for unmapped broker states.
        update_local_status(order_id, "UNKNOWN", raw_status or broker_state)
        reconcile(order_id)
        log_fn(f"[UNKNOWN_ESCALATED] order_id={order_id} broker_state={broker_state}")
        return CancelLoopResult(final_state="UNKNOWN", attempts=attempts, elapsed_seconds=elapsed)
