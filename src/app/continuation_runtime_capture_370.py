from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

try:
    from src.state.continuation_capture import (
        capture_add_confirmed_only,
        capture_fill_stage,
        capture_order_attempt,
        capture_persistence_if_due,
        capture_probe_entry,
        capture_setup_detected,
        capture_size_increase_only,
        capture_terminal_stage,
    )
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from state.continuation_capture import (
        capture_add_confirmed_only,
        capture_fill_stage,
        capture_order_attempt,
        capture_persistence_if_due,
        capture_probe_entry,
        capture_setup_detected,
        capture_size_increase_only,
        capture_terminal_stage,
    )

CANONICAL_EVENT_TYPE_MAP = {
    "PROBE_ENTRY": "ENTRY",
    "ENTRY": "ENTRY",
    "ADD_CONFIRMED": "ADD",
    "ADD": "ADD",
    "SIZE_INCREASE": "SCALE",
    "SCALE": "SCALE",
    "REDUCTION_TRIGGER": "REDUCE",
    "REDUCE": "REDUCE",
    "EXIT_TRIGGER": "EXIT",
    "CANCEL_CONFIRMED": "EXIT",
    "EXIT": "EXIT",
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _is_paper_environment(environment: str | None) -> bool:
    return str(environment or "").strip().lower() == "paper"


def _default_capture_path(db_path: str) -> Path:
    db_file = Path(db_path)
    stem = db_file.stem or "trading"
    return db_file.with_name(f"{stem}_continuation_capture.jsonl")


def _signal_event_id(run_id: str, symbol: str) -> str:
    return f"{symbol}|{run_id}|signal"


def _risk_decision_id(run_id: str, symbol: str) -> str:
    return f"{symbol}|{run_id}|risk"


def _persist_jsonl(
    *,
    db_path: str,
    environment: str,
    run_id: str,
    event_type: str,
    symbol: str,
    side: str,
    reason: str,
    order_id: str | None,
    result_status: str | None,
    payload: Mapping[str, Any] | None,
) -> None:
    capture_path_raw = os.environ.get("TRADING_CONTINUATION_CAPTURE_PATH")
    capture_path = Path(capture_path_raw) if capture_path_raw else _default_capture_path(db_path)
    record = {
        "captured_at": _now_iso(),
        "capture_schema_version": "task370-v1",
        "capture_source": "paper_runtime_hook",
        "run_id": str(run_id),
        "event_type": str(event_type),
        "symbol": str(symbol),
        "side": str(side),
        "environment": str(environment),
        "reason": str(reason),
        "order_id": "" if order_id is None else str(order_id),
        "result_status": "" if result_status is None else str(result_status),
        "payload": dict(payload or {}),
    }
    try:
        capture_path.parent.mkdir(parents=True, exist_ok=True)
        with capture_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, default=str))
            handle.write("\n")
    except Exception:
        return


def _emit_canonical_lifecycle_event(
    *,
    db_path: str,
    event_type: str,
    symbol: str,
    event_timestamp: str,
    order_id: str | None,
    run_id: str,
    payload: Mapping[str, Any] | None,
) -> str:
    canonical_event_type = CANONICAL_EVENT_TYPE_MAP.get(str(event_type))
    if canonical_event_type is None:
        return "not_canonical_event_type"

    mapped_payload = dict(payload or {})
    lifecycle_id = mapped_payload.get("canonical_lifecycle_id") or mapped_payload.get("lifecycle_id")
    fill_id = mapped_payload.get("fill_id")
    size_multiplier = mapped_payload.get("size_multiplier")
    if size_multiplier is None:
        size_multiplier = mapped_payload.get("next_size_multiplier")
    if size_multiplier is None:
        size_multiplier = mapped_payload.get("filled_quantity")
    price = mapped_payload.get("price")
    if price is None:
        price = mapped_payload.get("limit_price")
    quantity = mapped_payload.get("quantity")
    if quantity is None:
        quantity = mapped_payload.get("filled_quantity")

    try:
        from backtest.canonical_position_lifecycle_event_sourcing import (
            append_canonical_position_event,
            build_canonical_lifecycle_id,
            start_canonical_position_lifecycle,
        )
    except ModuleNotFoundError:
        from src.backtest.canonical_position_lifecycle_event_sourcing import (
            append_canonical_position_event,
            build_canonical_lifecycle_id,
            start_canonical_position_lifecycle,
        )

    if canonical_event_type == "ENTRY":
        stored_lifecycle_id = str(lifecycle_id or build_canonical_lifecycle_id(
            symbol=symbol,
            entry_timestamp=event_timestamp,
            entry_order_id=order_id,
            entry_fill_id=None if fill_id is None else str(fill_id),
            trade_run_id=run_id,
        ))
        start_canonical_position_lifecycle(
            db_path,
            lifecycle_id=stored_lifecycle_id,
            symbol=symbol,
            entry_timestamp=event_timestamp,
            entry_order_id=order_id,
            entry_fill_id=None if fill_id is None else str(fill_id),
            order_intent_id=None if mapped_payload.get("order_intent_id") is None else str(mapped_payload.get("order_intent_id")),
            trade_run_id=run_id,
            quantity=None if quantity is None else float(quantity),
            price=None if price is None else float(price),
            size_multiplier=1.0 if size_multiplier is None else float(size_multiplier),
            details={"runtime_event_type": event_type, "capture_expansion_task": "383"},
        )
        return "canonical_entry_recorded"

    if lifecycle_id is None or not str(lifecycle_id).strip():
        return "missing_explicit_lifecycle_id"

    append_canonical_position_event(
        db_path,
        lifecycle_id=str(lifecycle_id),
        event_type=canonical_event_type,
        event_timestamp=event_timestamp,
        order_id=order_id,
        fill_id=None if fill_id is None else str(fill_id),
        order_intent_id=None if mapped_payload.get("order_intent_id") is None else str(mapped_payload.get("order_intent_id")),
        trade_run_id=run_id,
        quantity=None if quantity is None else float(quantity),
        price=None if price is None else float(price),
        size_multiplier=None if size_multiplier is None else float(size_multiplier),
        details={"runtime_event_type": event_type, "capture_expansion_task": "383"},
    )
    return f"canonical_{canonical_event_type.lower()}_recorded"


def emit_continuation_capture_event(
    *,
    db_path: str,
    environment: str,
    run_id: str,
    event_type: str,
    symbol: str,
    side: str,
    reason: str = "",
    order_id: str | None = None,
    result_status: str | None = None,
    payload: Mapping[str, Any] | None = None,
) -> None:
    if not _is_paper_environment(environment):
        return

    event_timestamp = str((payload or {}).get("event_timestamp") or _now_iso())
    signal_event_id = str((payload or {}).get("signal_event_id") or _signal_event_id(run_id, symbol))
    risk_decision_id = str((payload or {}).get("risk_decision_id") or _risk_decision_id(run_id, symbol))
    mapped_payload = dict(payload or {})
    state_label = str(mapped_payload.get("state_label") or reason or event_type)
    quality_label = str(mapped_payload.get("participation_quality_label") or "UNKNOWN")
    expansion_score = float(mapped_payload.get("expansion_score") or 0.0)
    fragility_score = float(mapped_payload.get("fragility_score") or 0.0)
    risk_score = float(mapped_payload.get("continuation_risk_score") or 0.0)
    size_multiplier = float(mapped_payload.get("size_multiplier") or mapped_payload.get("filled_quantity") or 0.0)
    replay_state = str(mapped_payload.get("replay_state") or "UNKNOWN")
    trade_run_id = str(mapped_payload.get("trade_run_id") or run_id)
    order_intent_id = mapped_payload.get("order_intent_id") or mapped_payload.get("intent_key")
    reconciliation_id = mapped_payload.get("reconciliation_id")
    canonical_capture_status = "not_attempted"

    try:
        canonical_capture_status = _emit_canonical_lifecycle_event(
            db_path=db_path,
            event_type=event_type,
            symbol=symbol,
            event_timestamp=event_timestamp,
            order_id=order_id,
            run_id=trade_run_id,
            payload=mapped_payload,
        )
    except Exception:
        canonical_capture_status = "canonical_capture_error"

    try:
        if event_type == "SETUP_DETECTED":
            capture_setup_detected(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                replay_state="SETUP",
                trade_run_id=trade_run_id,
            )
        elif event_type == "PROBE_ENTRY":
            capture_probe_entry(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                size_multiplier=size_multiplier,
                replay_state="PROBE",
                trade_run_id=trade_run_id,
            )
        elif event_type == "ADD_ATTEMPT":
            capture_order_attempt(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                order_id=str(order_id or ""),
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                size_multiplier=size_multiplier,
                position_quantity_before=float(mapped_payload.get("position_quantity_before") or 0.0),
                replay_state="BUILDING",
                trade_run_id=trade_run_id,
                order_intent_id=None if order_intent_id is None else str(order_intent_id),
            )
        elif event_type == "ADD_CONFIRMED":
            capture_add_confirmed_only(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                order_id=order_id,
                fill_id=str(mapped_payload.get("fill_id") or ""),
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                size_multiplier=size_multiplier,
                replay_state="BUILDING",
                trade_run_id=trade_run_id,
                order_intent_id=None if order_intent_id is None else str(order_intent_id),
            )
        elif event_type == "FILL_CONFIRMED":
            capture_fill_stage(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                order_id=order_id,
                fill_id=str(mapped_payload.get("fill_id") or ""),
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                prior_size_multiplier=float(mapped_payload.get("prior_size_multiplier") or mapped_payload.get("position_quantity_before") or 0.0),
                next_size_multiplier=float(mapped_payload.get("next_size_multiplier") or mapped_payload.get("position_quantity_after") or size_multiplier),
                position_quantity_before=float(mapped_payload.get("position_quantity_before") or 0.0),
                position_quantity_after=float(mapped_payload.get("position_quantity_after") or mapped_payload.get("filled_quantity") or size_multiplier),
                replay_state="BUILDING",
                trade_run_id=trade_run_id,
                order_intent_id=None if order_intent_id is None else str(order_intent_id),
                reconciliation_id=None if reconciliation_id is None else str(reconciliation_id),
            )
        elif event_type == "SIZE_INCREASE":
            capture_size_increase_only(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                order_id=order_id,
                fill_id=str(mapped_payload.get("fill_id") or ""),
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                size_multiplier=size_multiplier,
                replay_state="BUILDING",
                trade_run_id=trade_run_id,
                order_intent_id=None if order_intent_id is None else str(order_intent_id),
            )
        elif event_type == "PERSISTENCE_CONFIRMED":
            capture_persistence_if_due(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                size_multiplier=size_multiplier,
                persistence_minutes=int(mapped_payload.get("persistence_minutes") or 15),
                replay_state="PERSISTING",
                trade_run_id=trade_run_id,
            )
        elif event_type == "FRAGILITY_WARNING":
            from state.continuation_capture import capture_weakening_stage

            capture_weakening_stage(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                size_multiplier=size_multiplier,
                replay_state="REDUCING",
                trade_run_id=trade_run_id,
            )
        elif event_type in {"REDUCTION_TRIGGER", "CANCEL_CONFIRMED", "INVALIDATION", "RUNTIME_ERROR"}:
            capture_terminal_stage(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                event_type="INVALIDATION" if event_type in {"CANCEL_CONFIRMED", "RUNTIME_ERROR"} else event_type,
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=max(fragility_score, 1.0 if event_type != "REDUCTION_TRIGGER" else fragility_score),
                continuation_risk_score=max(risk_score, 1.0 if event_type != "REDUCTION_TRIGGER" else risk_score),
                size_multiplier=0.0 if event_type != "REDUCTION_TRIGGER" else size_multiplier,
                replay_state="EXITED" if event_type != "REDUCTION_TRIGGER" else "REDUCING",
                details={"reason": reason, **mapped_payload},
                trade_run_id=trade_run_id,
                order_intent_id=None if order_intent_id is None else str(order_intent_id),
                order_id=order_id,
                fill_id=str(mapped_payload.get("fill_id") or "") or None,
                reconciliation_id=None if reconciliation_id is None else str(reconciliation_id),
            )
        elif event_type == "EXIT_TRIGGER":
            capture_terminal_stage(
                db_path,
                symbol=symbol,
                event_timestamp=event_timestamp,
                signal_event_id=signal_event_id,
                risk_decision_id=risk_decision_id,
                event_type="EXIT_TRIGGER",
                state_label=state_label,
                participation_quality_label=quality_label,
                expansion_score=expansion_score,
                fragility_score=fragility_score,
                continuation_risk_score=risk_score,
                size_multiplier=0.0,
                replay_state="EXITED",
                details={"reason": reason, **mapped_payload},
                trade_run_id=trade_run_id,
                order_intent_id=None if order_intent_id is None else str(order_intent_id),
                order_id=order_id,
                fill_id=str(mapped_payload.get("fill_id") or "") or None,
                reconciliation_id=None if reconciliation_id is None else str(reconciliation_id),
            )
    except Exception:
        # Capture must never affect runtime semantics.
        if canonical_capture_status == "not_attempted":
            canonical_capture_status = "legacy_capture_error"

    persisted_payload = dict(payload or {})
    persisted_payload["canonical_capture_status"] = canonical_capture_status
    _persist_jsonl(
        db_path=db_path,
        environment=environment,
        run_id=run_id,
        event_type=event_type,
        symbol=symbol,
        side=side,
        reason=reason,
        order_id=order_id,
        result_status=result_status,
        payload=persisted_payload,
    )
