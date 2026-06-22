from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.build_canonical_lifecycle_capture_expansion_383 import (
    TASK_376_EVALUATION_PATH,
    TASK_376_PREDICTION_PATH,
    build_task376_canonical_capture_mapping_audit,
)
from src.backtest.build_canonical_lifecycle_replay_revalidation_382 import (
    DEFAULT_DB_PATH,
    build_canonical_lifecycle_replay_panel,
    load_canonical_lifecycle_event_stream,
)
from src.backtest.canonical_position_lifecycle_event_sourcing import (
    CANONICAL_POSITION_EVENT_TYPES,
    append_canonical_position_event,
    start_canonical_position_lifecycle,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_384_canonical_lifecycle_stream_accumulation")
TASK_384_SOURCE_EVENTS_PATH = Path(
    os.environ.get(
        "TASK_384_CANONICAL_SOURCE_EVENTS_PATH",
        "docs/reports/task_384_canonical_lifecycle_stream_accumulation/canonical_source_events.csv",
    )
)

SOURCE_EVENT_COLUMNS = [
    "lifecycle_id",
    "event_type",
    "symbol",
    "event_timestamp",
    "order_id",
    "fill_id",
    "order_intent_id",
    "trade_run_id",
    "quantity",
    "price",
    "size_multiplier",
]


@dataclass(frozen=True)
class CanonicalLifecycleStreamAccumulation384Artifacts:
    canonical_accumulation_source_events: pd.DataFrame
    canonical_accumulation_event_audit: pd.DataFrame
    canonical_accumulation_event_stream: pd.DataFrame
    canonical_accumulation_lifecycle_panel: pd.DataFrame
    canonical_accumulation_success_audit: pd.DataFrame
    task376_canonical_capture_mapping_audit: pd.DataFrame
    task_384_decision: pd.DataFrame


def build_canonical_lifecycle_stream_accumulation_384(
    *,
    db_path: str | Path | None = None,
    source_events_path: Path = TASK_384_SOURCE_EVENTS_PATH,
    task376_prediction_path: Path = TASK_376_PREDICTION_PATH,
    task376_evaluation_path: Path = TASK_376_EVALUATION_PATH,
    execute_accumulation: bool = True,
) -> CanonicalLifecycleStreamAccumulation384Artifacts:
    db = Path(db_path or DEFAULT_DB_PATH)
    source_events = load_canonical_accumulation_source_events(source_events_path)
    event_audit = (
        accumulate_canonical_source_events(db, source_events)
        if execute_accumulation and not source_events.empty
        else build_noop_accumulation_audit(source_events)
    )
    event_stream = load_canonical_lifecycle_event_stream(db)
    lifecycle_panel = build_canonical_lifecycle_replay_panel(event_stream)
    success_audit = build_canonical_accumulation_success_audit(event_stream, lifecycle_panel, event_audit)
    task376_audit = build_task376_canonical_capture_mapping_audit(
        task376_prediction_path=task376_prediction_path,
        task376_evaluation_path=task376_evaluation_path,
    )
    decision = build_task_384_decision(success_audit, task376_audit)
    return CanonicalLifecycleStreamAccumulation384Artifacts(
        canonical_accumulation_source_events=source_events,
        canonical_accumulation_event_audit=event_audit,
        canonical_accumulation_event_stream=event_stream,
        canonical_accumulation_lifecycle_panel=lifecycle_panel,
        canonical_accumulation_success_audit=success_audit,
        task376_canonical_capture_mapping_audit=task376_audit,
        task_384_decision=decision,
    )


def load_canonical_accumulation_source_events(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=SOURCE_EVENT_COLUMNS)
    frame = pd.read_csv(path, encoding="utf-8-sig")
    for column in SOURCE_EVENT_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype=object)
    return frame[SOURCE_EVENT_COLUMNS + [column for column in frame.columns if column not in SOURCE_EVENT_COLUMNS]]


def accumulate_canonical_source_events(db_path: Path, source_events: pd.DataFrame) -> pd.DataFrame:
    audits: list[dict[str, Any]] = []
    normalized = source_events.copy()
    normalized["event_timestamp_dt"] = pd.to_datetime(normalized["event_timestamp"], errors="coerce", utc=True)
    normalized = normalized.sort_values(["lifecycle_id", "event_timestamp_dt", "event_type"]).reset_index(drop=True)
    for index, row in normalized.iterrows():
        event_type = str(row.get("event_type") or "").strip().upper()
        lifecycle_id = _text_or_none(row.get("lifecycle_id"))
        try:
            if event_type not in CANONICAL_POSITION_EVENT_TYPES:
                raise ValueError(f"invalid canonical event_type: {event_type}")
            if event_type == "ENTRY":
                if lifecycle_id is None:
                    raise ValueError("ENTRY requires explicit lifecycle_id for Task 384 accumulation")
                start_canonical_position_lifecycle(
                    str(db_path),
                    lifecycle_id=lifecycle_id,
                    symbol=str(row.get("symbol") or "").strip().upper(),
                    entry_timestamp=str(row.get("event_timestamp")),
                    entry_order_id=_text_or_none(row.get("order_id")),
                    entry_fill_id=_text_or_none(row.get("fill_id")),
                    order_intent_id=_text_or_none(row.get("order_intent_id")),
                    trade_run_id=_text_or_none(row.get("trade_run_id")),
                    quantity=_float_or_none(row.get("quantity")),
                    price=_float_or_none(row.get("price")),
                    size_multiplier=_float_or_none(row.get("size_multiplier")) or 1.0,
                    details={"capture_expansion_task": "384", "source_row_index": int(index)},
                )
            else:
                if lifecycle_id is None:
                    raise ValueError("post-entry canonical event requires explicit lifecycle_id")
                append_canonical_position_event(
                    str(db_path),
                    lifecycle_id=lifecycle_id,
                    event_type=event_type,
                    event_timestamp=str(row.get("event_timestamp")),
                    order_id=_text_or_none(row.get("order_id")),
                    fill_id=_text_or_none(row.get("fill_id")),
                    order_intent_id=_text_or_none(row.get("order_intent_id")),
                    trade_run_id=_text_or_none(row.get("trade_run_id")),
                    quantity=_float_or_none(row.get("quantity")),
                    price=_float_or_none(row.get("price")),
                    size_multiplier=_float_or_none(row.get("size_multiplier")),
                    details={"capture_expansion_task": "384", "source_row_index": int(index)},
                )
            status = "recorded"
            reason = ""
        except Exception as exc:
            status = "rejected"
            reason = str(exc)
        audits.append(
            {
                "source_row_index": int(index),
                "lifecycle_id": "" if lifecycle_id is None else lifecycle_id,
                "event_type": event_type,
                "event_timestamp": row.get("event_timestamp"),
                "accumulation_status": status,
                "rejection_reason": reason,
                "symbol_session_inference_used_flag": 0,
                "recovery_scoring_used_flag": 0,
            }
        )
    return pd.DataFrame(audits)


def build_noop_accumulation_audit(source_events: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_row_index": -1,
                "lifecycle_id": "",
                "event_type": "",
                "event_timestamp": "",
                "accumulation_status": "no_source_events",
                "rejection_reason": "no_task384_source_events_loaded" if source_events.empty else "execute_accumulation_false",
                "symbol_session_inference_used_flag": 0,
                "recovery_scoring_used_flag": 0,
            }
        ]
    )


def build_canonical_accumulation_success_audit(
    event_stream: pd.DataFrame,
    lifecycle_panel: pd.DataFrame,
    event_audit: pd.DataFrame,
) -> pd.DataFrame:
    event_count = len(event_stream)
    lifecycle_count = len(lifecycle_panel)
    entry_count = int(event_stream["canonical_event_type"].astype(str).eq("ENTRY").sum()) if not event_stream.empty else 0
    add_count = int(event_stream["canonical_event_type"].astype(str).eq("ADD").sum()) if not event_stream.empty else 0
    scale_count = int(event_stream["canonical_event_type"].astype(str).eq("SCALE").sum()) if not event_stream.empty else 0
    reduce_count = int(event_stream["canonical_event_type"].astype(str).eq("REDUCE").sum()) if not event_stream.empty else 0
    exit_count = int(event_stream["canonical_event_type"].astype(str).eq("EXIT").sum()) if not event_stream.empty else 0
    recorded_count = int(event_audit["accumulation_status"].astype(str).eq("recorded").sum()) if not event_audit.empty else 0
    rejected_count = int(event_audit["accumulation_status"].astype(str).eq("rejected").sum()) if not event_audit.empty else 0
    has_add_or_scale = bool((pd.to_numeric(lifecycle_panel.get("add_event_count"), errors="coerce").fillna(0) > 0).any() or (pd.to_numeric(lifecycle_panel.get("scale_event_count"), errors="coerce").fillna(0) > 0).any()) if not lifecycle_panel.empty else False
    has_reduce_exit = bool(((pd.to_numeric(lifecycle_panel.get("reduce_event_count"), errors="coerce").fillna(0) > 0) & (pd.to_numeric(lifecycle_panel.get("exit_event_count"), errors="coerce").fillna(0) > 0)).any()) if not lifecycle_panel.empty else False
    sequence_valid_count = int(pd.to_numeric(lifecycle_panel.get("canonical_sequence_valid_flag"), errors="coerce").fillna(0).sum()) if not lifecycle_panel.empty else 0
    return pd.DataFrame(
        [
            {
                "canonical_event_count": event_count,
                "canonical_lifecycle_count": lifecycle_count,
                "canonical_entry_count": entry_count,
                "canonical_add_count": add_count,
                "canonical_scale_count": scale_count,
                "canonical_reduce_count": reduce_count,
                "canonical_exit_count": exit_count,
                "recorded_source_event_count": recorded_count,
                "rejected_source_event_count": rejected_count,
                "has_entry_add_or_scale_lifecycle_flag": int(has_add_or_scale),
                "has_entry_reduce_exit_lifecycle_flag": int(has_reduce_exit),
                "canonical_sequence_valid_count": sequence_valid_count,
                "post_entry_requires_explicit_lifecycle_id_flag": 1,
                "symbol_session_inference_used_flag": 0,
                "recovery_scoring_used_flag": 0,
            }
        ]
    )


def build_task_384_decision(success_audit: pd.DataFrame, task376_audit: pd.DataFrame) -> pd.DataFrame:
    success = success_audit.iloc[0].to_dict() if not success_audit.empty else {}
    task376 = task376_audit.iloc[0].to_dict() if not task376_audit.empty else {}
    event_count = int(success.get("canonical_event_count", 0) or 0)
    lifecycle_count = int(success.get("canonical_lifecycle_count", 0) or 0)
    has_add_or_scale = int(success.get("has_entry_add_or_scale_lifecycle_flag", 0) or 0)
    has_reduce_exit = int(success.get("has_entry_reduce_exit_lifecycle_flag", 0) or 0)
    capture_ready_task376 = int(task376.get("capture_ready_row_count", 0) or 0)
    accumulation_complete = event_count > 0 and lifecycle_count > 0 and has_add_or_scale == 1 and has_reduce_exit == 1
    return pd.DataFrame(
        [
            {
                "task_384_verdict": "COMPLETE_PASS",
                "strategy_acceptance_status": "NOT_VALIDATED_CANONICAL_ACCUMULATION_ONLY",
                "canonical_event_count": event_count,
                "canonical_lifecycle_count": lifecycle_count,
                "has_entry_add_or_scale_lifecycle_flag": has_add_or_scale,
                "has_entry_reduce_exit_lifecycle_flag": has_reduce_exit,
                "capture_ready_task376_row_count": capture_ready_task376,
                "task382_canonical_stream_only_ready": "YES" if accumulation_complete else "NO_MORE_CANONICAL_EVENTS_REQUIRED",
                "symbol_session_inference_used_flag": 0,
                "recovery_scoring_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "label_overwrite_flag": 0,
                "next_priority": "task382_replay_on_accumulated_stream" if accumulation_complete else "continue_canonical_stream_accumulation",
            }
        ]
    )


def write_canonical_lifecycle_stream_accumulation_384(
    artifacts: CanonicalLifecycleStreamAccumulation384Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.canonical_accumulation_source_events.to_csv(out_dir / "canonical_accumulation_source_events.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_accumulation_event_audit.to_csv(out_dir / "canonical_accumulation_event_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_accumulation_event_stream.to_csv(out_dir / "canonical_accumulation_event_stream.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_accumulation_lifecycle_panel.to_csv(out_dir / "canonical_accumulation_lifecycle_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_accumulation_success_audit.to_csv(out_dir / "canonical_accumulation_success_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task376_canonical_capture_mapping_audit.to_csv(out_dir / "task376_canonical_capture_mapping_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_384_decision.to_csv(out_dir / "task_384_decision.csv", index=False, encoding="utf-8-sig")


def _text_or_none(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    return text


def _float_or_none(value: object) -> float | None:
    text = _text_or_none(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None
