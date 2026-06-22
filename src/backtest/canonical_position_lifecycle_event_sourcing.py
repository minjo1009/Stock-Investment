from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime

try:
    from state.store import (
        close_continuation_lifecycle,
        get_continuation_lifecycle,
        get_continuation_source_event_count,
        initialize_store,
        insert_continuation_lifecycle,
        insert_continuation_snapshot,
        insert_continuation_source_event,
        insert_or_ignore_continuation_setup,
        list_continuation_source_events,
    )
except ModuleNotFoundError:
    from src.state.store import (
        close_continuation_lifecycle,
        get_continuation_lifecycle,
        get_continuation_source_event_count,
        initialize_store,
        insert_continuation_lifecycle,
        insert_continuation_snapshot,
        insert_continuation_source_event,
        insert_or_ignore_continuation_setup,
        list_continuation_source_events,
    )


CANONICAL_POSITION_EVENT_TYPES = {"ENTRY", "ADD", "SCALE", "REDUCE", "EXIT"}
TERMINAL_CANONICAL_POSITION_EVENT_TYPES = {"EXIT"}
SOURCE_DATASET_VERSION = "canonical-position-lifecycle-event-sourcing-v1"


@dataclass(frozen=True)
class CanonicalLifecycleStart:
    lifecycle_id: str
    setup_id: str
    entry_event_id: str


def build_canonical_lifecycle_id(
    *,
    symbol: str,
    entry_timestamp: str,
    entry_order_id: str | None = None,
    entry_fill_id: str | None = None,
    trade_run_id: str | None = None,
    sequence: str | int | None = None,
) -> str:
    """Build the ID at ENTRY time from explicit entry-time identifiers only."""
    _require_intraday_timestamp(entry_timestamp, field_name="entry_timestamp")
    session_date = entry_timestamp[:10]
    seed = entry_fill_id or entry_order_id or trade_run_id or sequence or entry_timestamp
    return f"LIFECYCLE|{_slug(symbol)}|{session_date}|{_slug(str(seed))}"


def start_canonical_position_lifecycle(
    db_path: str,
    *,
    symbol: str,
    entry_timestamp: str,
    lifecycle_id: str | None = None,
    setup_id: str | None = None,
    entry_order_id: str | None = None,
    entry_fill_id: str | None = None,
    order_intent_id: str | None = None,
    trade_run_id: str | None = None,
    quantity: float | None = None,
    price: float | None = None,
    size_multiplier: float = 1.0,
    capture_mode: str = "paper_runtime",
    capture_batch_id: str | None = None,
    created_at: str | None = None,
    details: dict | None = None,
) -> CanonicalLifecycleStart:
    """Create a canonical lifecycle at ENTRY and record the ENTRY event.

    No symbol/date reconstruction is performed here. The returned lifecycle_id is the only
    identity post-entry events may use.
    """
    _require_intraday_timestamp(entry_timestamp, field_name="entry_timestamp")
    initialize_store(db_path)
    stored_lifecycle_id = lifecycle_id or build_canonical_lifecycle_id(
        symbol=symbol,
        entry_timestamp=entry_timestamp,
        entry_order_id=entry_order_id,
        entry_fill_id=entry_fill_id,
        trade_run_id=trade_run_id,
    )
    _require_nonempty(stored_lifecycle_id, field_name="lifecycle_id")
    if get_continuation_lifecycle(db_path, stored_lifecycle_id) is not None:
        raise ValueError(f"canonical lifecycle already exists: {stored_lifecycle_id}")

    session_date = entry_timestamp[:10]
    stored_setup_id = setup_id or f"SETUP|{stored_lifecycle_id}"
    stored_created_at = created_at or entry_timestamp
    insert_or_ignore_continuation_setup(
        db_path,
        setup_id=stored_setup_id,
        symbol=symbol,
        session_date=session_date,
        setup_timestamp=entry_timestamp,
        setup_origin="canonical_position_lifecycle_entry",
        signal_event_id=None,
        risk_decision_id=None,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        source_dataset_version=SOURCE_DATASET_VERSION,
        created_at=stored_created_at,
    )
    insert_continuation_lifecycle(
        db_path,
        lifecycle_id=stored_lifecycle_id,
        setup_id=stored_setup_id,
        parent_lifecycle_id=None,
        symbol=symbol,
        session_date=session_date,
        started_at=entry_timestamp,
        identity_origin="canonical_entry_event",
        identity_confidence=1.0,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        source_dataset_version=SOURCE_DATASET_VERSION,
        created_at=stored_created_at,
    )
    entry_event = _record_canonical_position_event(
        db_path,
        lifecycle_id=stored_lifecycle_id,
        canonical_event_type="ENTRY",
        event_timestamp=entry_timestamp,
        order_id=entry_order_id,
        fill_id=entry_fill_id,
        order_intent_id=order_intent_id,
        trade_run_id=trade_run_id,
        quantity=quantity,
        price=price,
        size_multiplier=size_multiplier,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        created_at=stored_created_at,
        details=details,
    )
    return CanonicalLifecycleStart(
        lifecycle_id=stored_lifecycle_id,
        setup_id=stored_setup_id,
        entry_event_id=entry_event["source_event_id"],
    )


def append_canonical_position_event(
    db_path: str,
    *,
    lifecycle_id: str,
    event_type: str,
    event_timestamp: str,
    order_id: str | None = None,
    fill_id: str | None = None,
    order_intent_id: str | None = None,
    trade_run_id: str | None = None,
    quantity: float | None = None,
    price: float | None = None,
    size_multiplier: float | None = None,
    capture_mode: str = "paper_runtime",
    capture_batch_id: str | None = None,
    created_at: str | None = None,
    details: dict | None = None,
) -> dict:
    """Append ADD/SCALE/REDUCE/EXIT to an existing canonical lifecycle_id."""
    _require_nonempty(lifecycle_id, field_name="lifecycle_id")
    if event_type == "ENTRY":
        raise ValueError("use start_canonical_position_lifecycle for ENTRY")
    return _record_canonical_position_event(
        db_path,
        lifecycle_id=lifecycle_id,
        canonical_event_type=event_type,
        event_timestamp=event_timestamp,
        order_id=order_id,
        fill_id=fill_id,
        order_intent_id=order_intent_id,
        trade_run_id=trade_run_id,
        quantity=quantity,
        price=price,
        size_multiplier=size_multiplier,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        created_at=created_at,
        details=details,
    )


def list_canonical_position_events(db_path: str, *, lifecycle_id: str) -> list[dict]:
    _require_nonempty(lifecycle_id, field_name="lifecycle_id")
    events = list_continuation_source_events(db_path, lifecycle_id=lifecycle_id)
    canonical_events: list[dict] = []
    for event in events:
        details = _decode_details(event.get("details_json"))
        canonical_event = dict(event)
        canonical_event["canonical_event_type"] = details.get("canonical_event_type", event["event_type"])
        canonical_event["quantity"] = details.get("quantity")
        canonical_event["price"] = details.get("price")
        canonical_events.append(canonical_event)
    return canonical_events


def _record_canonical_position_event(
    db_path: str,
    *,
    lifecycle_id: str,
    canonical_event_type: str,
    event_timestamp: str,
    order_id: str | None,
    fill_id: str | None,
    order_intent_id: str | None,
    trade_run_id: str | None,
    quantity: float | None,
    price: float | None,
    size_multiplier: float | None,
    capture_mode: str,
    capture_batch_id: str | None,
    created_at: str | None,
    details: dict | None,
) -> dict:
    _require_intraday_timestamp(event_timestamp, field_name="event_timestamp")
    if canonical_event_type not in CANONICAL_POSITION_EVENT_TYPES:
        raise ValueError(f"invalid canonical position event_type: {canonical_event_type}")
    lifecycle = get_continuation_lifecycle(db_path, lifecycle_id)
    if lifecycle is None:
        raise ValueError(f"unknown canonical lifecycle_id: {lifecycle_id}")
    if lifecycle.get("ended_at"):
        raise ValueError(f"canonical lifecycle is already closed: {lifecycle_id}")
    if _to_datetime(event_timestamp) < _to_datetime(str(lifecycle["started_at"])):
        raise ValueError("event_timestamp cannot be before lifecycle started_at")

    previous_events = list_continuation_source_events(db_path, lifecycle_id=lifecycle_id)
    if previous_events:
        latest_timestamp = str(previous_events[-1]["event_timestamp"])
        if _to_datetime(event_timestamp) < _to_datetime(latest_timestamp):
            raise ValueError("canonical position events must be appended in timestamp order")

    add_depth = int(previous_events[-1]["add_depth"]) if previous_events else 0
    scale_depth = int(previous_events[-1]["scale_depth"]) if previous_events else 0
    persistence_depth = int(previous_events[-1]["persistence_depth"]) if previous_events else 0
    previous_size = float(previous_events[-1]["size_multiplier"]) if previous_events else 1.0
    if canonical_event_type == "ADD":
        add_depth += 1
    elif canonical_event_type == "SCALE":
        scale_depth += 1

    stored_size_multiplier = previous_size if size_multiplier is None else float(size_multiplier)
    sequence = get_continuation_source_event_count(db_path, lifecycle_id) + 1
    source_event_id = f"CANONICAL|{lifecycle_id}|{sequence:06d}|{canonical_event_type}"
    stored_created_at = created_at or event_timestamp
    details_json = _encode_details(
        {
            **(details or {}),
            "canonical_event_type": canonical_event_type,
            "canonical_lifecycle_id": lifecycle_id,
            "quantity": quantity,
            "price": price,
            "identity_policy": "explicit_lifecycle_id_only",
            "recovery_or_symbol_session_match_used": False,
        }
    )
    insert_continuation_source_event(
        db_path,
        source_event_id=source_event_id,
        lifecycle_id=lifecycle_id,
        setup_id=str(lifecycle["setup_id"]),
        parent_lifecycle_id=lifecycle.get("parent_lifecycle_id"),
        signal_event_id=None,
        risk_decision_id=None,
        order_intent_id=order_intent_id,
        order_id=order_id,
        fill_id=fill_id,
        reconciliation_id=None,
        trade_run_id=trade_run_id,
        symbol=str(lifecycle["symbol"]),
        session_date=str(lifecycle["session_date"]),
        event_type=canonical_event_type,
        event_source="SOURCE_CAPTURED",
        event_timestamp=event_timestamp,
        state_label=None,
        participation_quality_label=None,
        expansion_score=0.0,
        fragility_score=0.0,
        continuation_risk_score=0.0,
        size_multiplier=stored_size_multiplier,
        add_depth=add_depth,
        scale_depth=scale_depth,
        persistence_depth=persistence_depth,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        source_dataset_version=SOURCE_DATASET_VERSION,
        details_json=details_json,
        created_at=stored_created_at,
    )
    insert_continuation_snapshot(
        db_path,
        snapshot_id=f"SNAPSHOT|{source_event_id}",
        lifecycle_id=lifecycle_id,
        setup_id=str(lifecycle["setup_id"]),
        event_id=source_event_id,
        snapshot_timestamp=event_timestamp,
        replay_state=canonical_event_type,
        size_multiplier=stored_size_multiplier,
        add_depth=add_depth,
        scale_depth=scale_depth,
        persistence_depth=persistence_depth,
        weakening_flag=canonical_event_type in {"REDUCE", "EXIT"},
        invalidated_flag=False,
        capture_mode=capture_mode,
        capture_batch_id=capture_batch_id,
        source_dataset_version=SOURCE_DATASET_VERSION,
        created_at=stored_created_at,
    )
    if canonical_event_type in TERMINAL_CANONICAL_POSITION_EVENT_TYPES:
        close_continuation_lifecycle(db_path, lifecycle_id, event_timestamp)
    return {
        "source_event_id": source_event_id,
        "lifecycle_id": lifecycle_id,
        "canonical_event_type": canonical_event_type,
        "sequence": sequence,
    }


def _require_nonempty(value: str | None, *, field_name: str) -> None:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} is required")


def _require_intraday_timestamp(value: str, *, field_name: str) -> None:
    _require_nonempty(value, field_name=field_name)
    if "T" not in value:
        raise ValueError(f"{field_name} must include intraday timestamp precision")
    _to_datetime(value)


def _to_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip().upper()).strip("_")


def _encode_details(details: dict) -> str:
    return json.dumps(details, ensure_ascii=True, sort_keys=True)


def _decode_details(value: object) -> dict:
    if not value:
        return {}
    try:
        decoded = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}
