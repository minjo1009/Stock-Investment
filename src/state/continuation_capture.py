from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from typing import Any

try:
    from src.state.store import (
        close_continuation_lifecycle,
        find_matching_continuation_source_event,
        get_active_continuation_lifecycle,
        get_continuation_lifecycle,
        get_continuation_setup,
        get_continuation_source_event_count,
        get_latest_continuation_snapshot,
        get_latest_continuation_source_event,
        insert_continuation_lifecycle,
        insert_continuation_snapshot,
        insert_continuation_source_event,
        insert_or_ignore_continuation_setup,
        list_continuation_source_events,
        list_continuation_lifecycles,
    )
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from state.store import (
        close_continuation_lifecycle,
        find_matching_continuation_source_event,
        get_active_continuation_lifecycle,
        get_continuation_lifecycle,
        get_continuation_setup,
        get_continuation_source_event_count,
        get_latest_continuation_snapshot,
        get_latest_continuation_source_event,
        insert_continuation_lifecycle,
        insert_continuation_snapshot,
        insert_continuation_source_event,
        insert_or_ignore_continuation_setup,
        list_continuation_source_events,
        list_continuation_lifecycles,
    )


SOURCE_CAPTURED = "SOURCE_CAPTURED"
SESSION_DERIVED = "SESSION_DERIVED"
REPLAY_DERIVED = "REPLAY_DERIVED"

IDENTITY_CONFIDENCE = {
    "explicit_signal_identity": 1.00,
    "explicit_risk_identity": 0.90,
    "explicit_order_fill_identity": 0.85,
    "derived_session_continuity": 0.60,
}


@dataclass(frozen=True)
class SourceContinuationSetup:
    setup_id: str
    symbol: str
    session_date: str
    setup_timestamp: str
    setup_origin: str
    signal_event_id: str | None
    risk_decision_id: str | None


@dataclass(frozen=True)
class SourceContinuationLifecycle:
    lifecycle_id: str
    setup_id: str
    parent_lifecycle_id: str | None
    symbol: str
    session_date: str
    started_at: str
    ended_at: str | None
    identity_origin: str
    identity_confidence: float


@dataclass(frozen=True)
class SourceContinuationEvent:
    source_event_id: str
    lifecycle_id: str
    setup_id: str
    parent_lifecycle_id: str | None
    signal_event_id: str | None
    risk_decision_id: str | None
    order_intent_id: str | None
    order_id: str | None
    fill_id: str | None
    reconciliation_id: str | None
    trade_run_id: str | None
    symbol: str
    session_date: str
    event_type: str
    event_source: str
    event_timestamp: str
    state_label: str
    participation_quality_label: str
    expansion_score: float
    fragility_score: float
    continuation_risk_score: float
    size_multiplier: float
    add_depth: int
    scale_depth: int
    persistence_depth: int


@dataclass(frozen=True)
class SourceContinuationSnapshot:
    snapshot_id: str
    lifecycle_id: str
    setup_id: str
    event_id: str
    snapshot_timestamp: str
    replay_state: str
    size_multiplier: float
    add_depth: int
    scale_depth: int
    persistence_depth: int
    weakening_flag: bool
    invalidated_flag: bool


@dataclass(frozen=True)
class ContinuationCaptureContext:
    setup_id: str
    lifecycle_id: str
    parent_lifecycle_id: str | None
    session_date: str
    identity_origin: str
    identity_confidence: float


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    return float(default) if numeric != numeric else float(numeric)


def _parse_iso(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _session_date(timestamp: str) -> str:
    return _parse_iso(timestamp).date().isoformat()


def _identity_origin(signal_event_id: str | None, risk_decision_id: str | None, order_or_fill: bool = False) -> str:
    if signal_event_id:
        return "explicit_signal_identity"
    if risk_decision_id:
        return "explicit_risk_identity"
    if order_or_fill:
        return "explicit_order_fill_identity"
    return "derived_session_continuity"


def _build_setup_id(symbol: str, session_date: str, signal_event_id: str | None, risk_decision_id: str | None) -> str:
    if signal_event_id:
        return f"{symbol}|{session_date}|{signal_event_id}"
    if risk_decision_id:
        return f"{symbol}|{session_date}|{risk_decision_id}"
    return f"{symbol}|{session_date}|derived_setup"


def _build_next_lifecycle_id(db_path: str, setup_id: str, symbol: str) -> tuple[str, str | None]:
    lifecycles = list_continuation_lifecycles(db_path, setup_id=setup_id, symbol=symbol, limit=1000)
    if not lifecycles:
        return f"{setup_id}|life_001", None
    ordered = sorted(lifecycles, key=lambda row: (_safe_text(row.get("started_at")), _safe_text(row.get("lifecycle_id"))))
    parent = _safe_text(ordered[-1].get("lifecycle_id")) or None
    ordinal = len(ordered) + 1
    return f"{setup_id}|life_{ordinal:03d}", parent


def ensure_capture_context(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None = None,
    risk_decision_id: str | None = None,
    order_or_fill: bool = False,
    force_new_lifecycle: bool = False,
    reuse_latest_closed: bool = False,
) -> ContinuationCaptureContext:
    normalized_symbol = _safe_text(symbol).upper()
    session_date = _session_date(event_timestamp)
    setup_id = _build_setup_id(normalized_symbol, session_date, signal_event_id, risk_decision_id)
    identity_origin = _identity_origin(signal_event_id, risk_decision_id, order_or_fill=order_or_fill)
    identity_confidence = IDENTITY_CONFIDENCE[identity_origin]
    insert_or_ignore_continuation_setup(
        db_path,
        setup_id=setup_id,
        symbol=normalized_symbol,
        session_date=session_date,
        setup_timestamp=event_timestamp,
        setup_origin=identity_origin,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        created_at=event_timestamp,
    )
    active = None if force_new_lifecycle else get_active_continuation_lifecycle(
        db_path,
        setup_id=setup_id,
        symbol=normalized_symbol,
        session_date=session_date,
    )
    if active is not None:
        return ContinuationCaptureContext(
            setup_id=setup_id,
            lifecycle_id=_safe_text(active.get("lifecycle_id"), "unknown_lifecycle"),
            parent_lifecycle_id=active.get("parent_lifecycle_id"),
            session_date=session_date,
            identity_origin=_safe_text(active.get("identity_origin"), identity_origin),
            identity_confidence=_safe_float(active.get("identity_confidence"), identity_confidence),
        )
    if reuse_latest_closed:
        lifecycles = list_continuation_lifecycles(db_path, setup_id=setup_id, symbol=normalized_symbol, limit=1000)
        if lifecycles:
            ordered = sorted(lifecycles, key=lambda row: (_safe_text(row.get("started_at")), _safe_text(row.get("lifecycle_id"))))
            latest = ordered[-1]
            return ContinuationCaptureContext(
                setup_id=setup_id,
                lifecycle_id=_safe_text(latest.get("lifecycle_id"), "unknown_lifecycle"),
                parent_lifecycle_id=latest.get("parent_lifecycle_id"),
                session_date=session_date,
                identity_origin=_safe_text(latest.get("identity_origin"), identity_origin),
                identity_confidence=_safe_float(latest.get("identity_confidence"), identity_confidence),
            )
    lifecycle_id, parent_lifecycle_id = _build_next_lifecycle_id(db_path, setup_id, normalized_symbol)
    insert_continuation_lifecycle(
        db_path,
        lifecycle_id=lifecycle_id,
        setup_id=setup_id,
        parent_lifecycle_id=parent_lifecycle_id,
        symbol=normalized_symbol,
        session_date=session_date,
        started_at=event_timestamp,
        identity_origin=identity_origin,
        identity_confidence=identity_confidence,
        created_at=event_timestamp,
    )
    return ContinuationCaptureContext(
        setup_id=setup_id,
        lifecycle_id=lifecycle_id,
        parent_lifecycle_id=parent_lifecycle_id,
        session_date=session_date,
        identity_origin=identity_origin,
        identity_confidence=identity_confidence,
    )


def _event_depths(
    db_path: str,
    lifecycle_id: str,
    *,
    event_type: str,
    prior_size_multiplier: float,
    next_size_multiplier: float,
) -> tuple[int, int, int, bool, bool]:
    latest = get_latest_continuation_snapshot(db_path, lifecycle_id)
    add_depth = int(latest["add_depth"]) if latest is not None else 0
    scale_depth = int(latest["scale_depth"]) if latest is not None else 0
    persistence_depth = int(latest["persistence_depth"]) if latest is not None else 0
    weakening_flag = bool(int(latest["weakening_flag"])) if latest is not None else False
    invalidated_flag = bool(int(latest["invalidated_flag"])) if latest is not None else False
    if event_type == "ADD_CONFIRMED":
        add_depth += 1
    if event_type == "SIZE_INCREASE" and next_size_multiplier > prior_size_multiplier:
        scale_depth += 1
    if event_type == "PERSISTENCE_CONFIRMED":
        persistence_depth += 1
    if event_type in {"FRAGILITY_WARNING", "REDUCTION_TRIGGER"}:
        weakening_flag = True
    if event_type == "INVALIDATION":
        invalidated_flag = True
    return add_depth, scale_depth, persistence_depth, weakening_flag, invalidated_flag


def _insert_event_and_snapshot(
    db_path: str,
    *,
    context: ContinuationCaptureContext,
    symbol: str,
    event_timestamp: str,
    event_type: str,
    event_source: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    order_intent_id: str | None,
    order_id: str | None,
    fill_id: str | None,
    reconciliation_id: str | None,
    trade_run_id: str | None,
    replay_state: str,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    prior_size_multiplier: float,
    details: dict[str, Any] | None,
) -> str:
    existing = find_matching_continuation_source_event(
        db_path,
        lifecycle_id=context.lifecycle_id,
        event_type=event_type,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_id=order_id,
        fill_id=fill_id,
    )
    if existing is not None:
        return _safe_text(existing.get("source_event_id"), "unknown_event")
    event_ordinal = get_continuation_source_event_count(db_path, context.lifecycle_id) + 1
    source_event_id = f"{context.lifecycle_id}|evt_{event_ordinal:03d}"
    add_depth, scale_depth, persistence_depth, weakening_flag, invalidated_flag = _event_depths(
        db_path,
        context.lifecycle_id,
        event_type=event_type,
        prior_size_multiplier=prior_size_multiplier,
        next_size_multiplier=size_multiplier,
    )
    insert_continuation_source_event(
        db_path,
        source_event_id=source_event_id,
        lifecycle_id=context.lifecycle_id,
        setup_id=context.setup_id,
        parent_lifecycle_id=context.parent_lifecycle_id,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=order_intent_id,
        order_id=order_id,
        fill_id=fill_id,
        reconciliation_id=reconciliation_id,
        trade_run_id=trade_run_id,
        symbol=_safe_text(symbol).upper(),
        session_date=context.session_date,
        event_type=event_type,
        event_source=event_source,
        event_timestamp=event_timestamp,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        add_depth=add_depth,
        scale_depth=scale_depth,
        persistence_depth=persistence_depth,
        details_json=None if details is None else json.dumps(details, ensure_ascii=True, sort_keys=True),
        created_at=event_timestamp,
    )
    insert_continuation_snapshot(
        db_path,
        snapshot_id=f"{source_event_id}|snap",
        lifecycle_id=context.lifecycle_id,
        setup_id=context.setup_id,
        event_id=source_event_id,
        snapshot_timestamp=event_timestamp,
        replay_state=replay_state,
        size_multiplier=size_multiplier,
        add_depth=add_depth,
        scale_depth=scale_depth,
        persistence_depth=persistence_depth,
        weakening_flag=weakening_flag,
        invalidated_flag=invalidated_flag,
        created_at=event_timestamp,
    )
    if event_type in {"EXIT_TRIGGER", "INVALIDATION"}:
        close_continuation_lifecycle(db_path, context.lifecycle_id, event_timestamp)
    return source_event_id


def capture_signal_risk_stage(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    actionable: bool,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float = 0.0,
    replay_state: str = "PROBE",
    invalidation_reason: str | None = None,
    trade_run_id: str | None = None,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        reuse_latest_closed=True,
    )
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type="SETUP_DETECTED",
        event_source=SOURCE_CAPTURED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=None,
        order_id=None,
        fill_id=None,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=0.0,
        prior_size_multiplier=0.0,
        details={"stage": "signal_risk"},
    )
    if actionable:
        _insert_event_and_snapshot(
            db_path,
            context=context,
            symbol=symbol,
            event_timestamp=event_timestamp,
            event_type="PROBE_ENTRY",
            event_source=SOURCE_CAPTURED,
            signal_event_id=signal_event_id,
            risk_decision_id=risk_decision_id,
            order_intent_id=None,
            order_id=None,
            fill_id=None,
            reconciliation_id=None,
            trade_run_id=trade_run_id,
            replay_state=replay_state,
            state_label=state_label,
            participation_quality_label=participation_quality_label,
            expansion_score=expansion_score,
            fragility_score=fragility_score,
            continuation_risk_score=continuation_risk_score,
            size_multiplier=size_multiplier,
            prior_size_multiplier=0.0,
            details={"stage": "probe"},
        )
    else:
        _insert_event_and_snapshot(
            db_path,
            context=context,
            symbol=symbol,
            event_timestamp=event_timestamp,
            event_type="INVALIDATION",
            event_source=SOURCE_CAPTURED,
            signal_event_id=signal_event_id,
            risk_decision_id=risk_decision_id,
            order_intent_id=None,
            order_id=None,
            fill_id=None,
            reconciliation_id=None,
            trade_run_id=trade_run_id,
            replay_state="EXITED",
            state_label=state_label,
            participation_quality_label=participation_quality_label,
            expansion_score=expansion_score,
            fragility_score=fragility_score,
            continuation_risk_score=continuation_risk_score,
            size_multiplier=0.0,
            prior_size_multiplier=size_multiplier,
            details={"reason": invalidation_reason or "immediate_block"},
        )
    return context


def capture_setup_detected(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    trade_run_id: str | None = None,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    replay_state: str = "SETUP",
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
    )
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type="SETUP_DETECTED",
        event_source=SOURCE_CAPTURED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=None,
        order_id=None,
        fill_id=None,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=0.0,
        prior_size_multiplier=0.0,
        details={"stage": "setup_only"},
    )
    return context


def capture_probe_entry(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    trade_run_id: str | None = None,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    replay_state: str = "PROBE",
    force_new_lifecycle: bool = False,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        force_new_lifecycle=force_new_lifecycle,
    )
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type="PROBE_ENTRY",
        event_source=SOURCE_CAPTURED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=None,
        order_id=None,
        fill_id=None,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        prior_size_multiplier=0.0,
        details={"stage": "probe_only"},
    )
    return context


def capture_order_attempt(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    order_id: str,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    position_quantity_before: float,
    replay_state: str = "BUILDING",
    trade_run_id: str | None = None,
    order_intent_id: str | None = None,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_or_fill=True,
    )
    if position_quantity_before <= 0:
        return context
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type="ADD_ATTEMPT",
        event_source=SOURCE_CAPTURED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=order_intent_id,
        order_id=order_id,
        fill_id=None,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        prior_size_multiplier=size_multiplier,
        details={"position_quantity_before": position_quantity_before},
    )
    return context


def capture_fill_stage(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    order_id: str,
    fill_id: str,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    prior_size_multiplier: float,
    next_size_multiplier: float,
    position_quantity_before: float,
    position_quantity_after: float,
    replay_state: str = "BUILDING",
    trade_run_id: str | None = None,
    order_intent_id: str | None = None,
    reconciliation_id: str | None = None,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_or_fill=True,
    )
    if position_quantity_before > 0:
        _insert_event_and_snapshot(
            db_path,
            context=context,
            symbol=symbol,
            event_timestamp=event_timestamp,
            event_type="ADD_CONFIRMED",
            event_source=SOURCE_CAPTURED,
            signal_event_id=signal_event_id,
            risk_decision_id=risk_decision_id,
            order_intent_id=order_intent_id,
            order_id=order_id,
            fill_id=fill_id,
            reconciliation_id=reconciliation_id,
            trade_run_id=trade_run_id,
            replay_state=replay_state,
            state_label=state_label,
            participation_quality_label=participation_quality_label,
            expansion_score=expansion_score,
            fragility_score=fragility_score,
            continuation_risk_score=continuation_risk_score,
            size_multiplier=next_size_multiplier,
            prior_size_multiplier=prior_size_multiplier,
            details={
                "position_quantity_before": position_quantity_before,
                "position_quantity_after": position_quantity_after,
            },
        )
    if position_quantity_after > position_quantity_before or next_size_multiplier > prior_size_multiplier:
        _insert_event_and_snapshot(
            db_path,
            context=context,
            symbol=symbol,
            event_timestamp=event_timestamp,
            event_type="SIZE_INCREASE",
            event_source=SOURCE_CAPTURED,
            signal_event_id=signal_event_id,
            risk_decision_id=risk_decision_id,
            order_intent_id=order_intent_id,
            order_id=order_id,
            fill_id=fill_id,
            reconciliation_id=reconciliation_id,
            trade_run_id=trade_run_id,
            replay_state=replay_state,
            state_label=state_label,
            participation_quality_label=participation_quality_label,
            expansion_score=expansion_score,
            fragility_score=fragility_score,
            continuation_risk_score=continuation_risk_score,
            size_multiplier=next_size_multiplier,
            prior_size_multiplier=prior_size_multiplier,
            details={
                "position_quantity_before": position_quantity_before,
                "position_quantity_after": position_quantity_after,
            },
        )
    return context


def capture_size_increase_only(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    order_id: str | None,
    fill_id: str | None,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    replay_state: str = "BUILDING",
    trade_run_id: str | None = None,
    order_intent_id: str | None = None,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_or_fill=True,
    )
    latest = get_latest_continuation_snapshot(db_path, context.lifecycle_id)
    prior_size_multiplier = _safe_float(latest.get("size_multiplier"), 0.0) if latest is not None else 0.0
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type="SIZE_INCREASE",
        event_source=SOURCE_CAPTURED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=order_intent_id,
        order_id=order_id,
        fill_id=fill_id,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        prior_size_multiplier=prior_size_multiplier,
        details={"stage": "size_increase_only"},
    )
    return context


def capture_add_confirmed_only(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    order_id: str | None,
    fill_id: str | None,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    replay_state: str = "BUILDING",
    trade_run_id: str | None = None,
    order_intent_id: str | None = None,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_or_fill=True,
    )
    latest = get_latest_continuation_snapshot(db_path, context.lifecycle_id)
    prior_size_multiplier = _safe_float(latest.get("size_multiplier"), 0.0) if latest is not None else 0.0
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type="ADD_CONFIRMED",
        event_source=SOURCE_CAPTURED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=order_intent_id,
        order_id=order_id,
        fill_id=fill_id,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        prior_size_multiplier=prior_size_multiplier,
        details={"stage": "add_confirmed_only"},
    )
    return context


def capture_persistence_if_due(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    persistence_minutes: int = 15,
    replay_state: str = "PERSISTING",
    trade_run_id: str | None = None,
) -> ContinuationCaptureContext | None:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
    )
    latest = get_latest_continuation_source_event(db_path, context.lifecycle_id)
    if latest is None:
        return None
    probe_rows = [
        row for row in list_continuation_lifecycles(db_path, setup_id=context.setup_id, symbol=_safe_text(symbol).upper(), limit=1000)
        if _safe_text(row.get("lifecycle_id")) == context.lifecycle_id
    ]
    _ = probe_rows
    source_rows = []  # avoid extra import churn; fetch all lifecycle events below
    del source_rows
    latest_snapshot = get_latest_continuation_snapshot(db_path, context.lifecycle_id)
    if latest_snapshot is not None and int(latest_snapshot["persistence_depth"]) > 0:
        return context
    lifecycle_events = list_continuation_source_events(db_path, lifecycle_id=context.lifecycle_id, limit=1000)
    probe_event = next((row for row in lifecycle_events if _safe_text(row.get("event_type")) == "PROBE_ENTRY"), None)
    if probe_event is None:
        return None
    elapsed_minutes = (_parse_iso(event_timestamp) - _parse_iso(_safe_text(probe_event.get("event_timestamp")))).total_seconds() / 60.0
    if elapsed_minutes < persistence_minutes:
        return context
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type="PERSISTENCE_CONFIRMED",
        event_source=SESSION_DERIVED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=None,
        order_id=None,
        fill_id=None,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        prior_size_multiplier=size_multiplier,
        details={"elapsed_minutes": round(elapsed_minutes, 6), "persistence_minutes": persistence_minutes},
    )
    return context


def capture_due_persistence_for_open_lifecycles(
    db_path: str,
    *,
    event_timestamp: str,
    persistence_minutes: int = 15,
    state_label: str = "PERSIST",
    replay_state: str = "PERSISTING",
) -> int:
    emitted = 0
    for lifecycle in list_continuation_lifecycles(db_path, limit=100000):
        if str(lifecycle.get("ended_at") or "").strip():
            continue
        lifecycle_id = _safe_text(lifecycle.get("lifecycle_id"))
        symbol = _safe_text(lifecycle.get("symbol")).upper()
        if not lifecycle_id or not symbol:
            continue
        lifecycle_events = list_continuation_source_events(db_path, lifecycle_id=lifecycle_id, limit=1000)
        if not lifecycle_events:
            continue
        latest_event = lifecycle_events[-1]
        latest_snapshot = get_latest_continuation_snapshot(db_path, lifecycle_id)
        if latest_snapshot is not None and int(latest_snapshot.get("persistence_depth") or 0) > 0:
            continue
        before_count = len(lifecycle_events)
        capture_persistence_if_due(
            db_path,
            symbol=symbol,
            event_timestamp=event_timestamp,
            signal_event_id=_safe_text(latest_event.get("signal_event_id")) or None,
            risk_decision_id=_safe_text(latest_event.get("risk_decision_id")) or None,
            state_label=state_label,
            participation_quality_label=_safe_text(latest_event.get("participation_quality_label"), "UNKNOWN"),
            expansion_score=_safe_float(latest_event.get("expansion_score"), 0.0),
            fragility_score=_safe_float(latest_event.get("fragility_score"), 0.0),
            continuation_risk_score=_safe_float(latest_event.get("continuation_risk_score"), 0.0),
            size_multiplier=_safe_float(latest_event.get("size_multiplier"), 0.0),
            persistence_minutes=persistence_minutes,
            replay_state=replay_state,
            trade_run_id=_safe_text(latest_event.get("trade_run_id")) or None,
        )
        after_count = len(list_continuation_source_events(db_path, lifecycle_id=lifecycle_id, limit=1000))
        if after_count > before_count:
            emitted += 1
    return emitted


def capture_weakening_stage(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    replay_state: str = "REDUCING",
    trade_run_id: str | None = None,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
    )
    latest_snapshot = get_latest_continuation_snapshot(db_path, context.lifecycle_id)
    event_type = "REDUCTION_TRIGGER" if latest_snapshot is not None and bool(int(latest_snapshot["weakening_flag"])) else "FRAGILITY_WARNING"
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type=event_type,
        event_source=SESSION_DERIVED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=None,
        order_id=None,
        fill_id=None,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        prior_size_multiplier=size_multiplier,
        details={"stage": "weakening"},
    )
    return context


def capture_terminal_stage(
    db_path: str,
    *,
    symbol: str,
    event_timestamp: str,
    signal_event_id: str | None,
    risk_decision_id: str | None,
    event_type: str,
    state_label: str,
    participation_quality_label: str,
    expansion_score: float,
    fragility_score: float,
    continuation_risk_score: float,
    size_multiplier: float,
    replay_state: str,
    details: dict[str, Any] | None = None,
    trade_run_id: str | None = None,
    order_intent_id: str | None = None,
    order_id: str | None = None,
    fill_id: str | None = None,
    reconciliation_id: str | None = None,
) -> ContinuationCaptureContext:
    context = ensure_capture_context(
        db_path,
        symbol=symbol,
        event_timestamp=event_timestamp,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
    )
    _insert_event_and_snapshot(
        db_path,
        context=context,
        symbol=symbol,
        event_timestamp=event_timestamp,
        event_type=event_type,
        event_source=SOURCE_CAPTURED if event_type in {"INVALIDATION", "EXIT_TRIGGER"} else SESSION_DERIVED,
        signal_event_id=signal_event_id,
        risk_decision_id=risk_decision_id,
        order_intent_id=order_intent_id,
        order_id=order_id,
        fill_id=fill_id,
        reconciliation_id=reconciliation_id,
        trade_run_id=trade_run_id,
        replay_state=replay_state,
        state_label=state_label,
        participation_quality_label=participation_quality_label,
        expansion_score=expansion_score,
        fragility_score=fragility_score,
        continuation_risk_score=continuation_risk_score,
        size_multiplier=size_multiplier,
        prior_size_multiplier=size_multiplier,
        details=details,
    )
    return context
