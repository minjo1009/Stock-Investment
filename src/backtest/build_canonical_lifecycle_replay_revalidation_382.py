from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.canonical_position_lifecycle_event_sourcing import (
    CANONICAL_POSITION_EVENT_TYPES,
    SOURCE_DATASET_VERSION,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_382_canonical_lifecycle_replay_revalidation")
DEFAULT_DB_PATH = Path(os.environ.get("TRADING_DB_PATH", "data/trading.db"))
TASK_376_EVALUATION_PATH = Path(
    "docs/reports/task_376_persistence_universe_rebuild/persistence_universe_evaluation_panel.csv"
)

EVENT_STREAM_COLUMNS = [
    "source_event_id",
    "lifecycle_id",
    "setup_id",
    "symbol",
    "session_date",
    "event_timestamp",
    "event_type",
    "canonical_event_type",
    "event_source",
    "order_id",
    "fill_id",
    "trade_run_id",
    "size_multiplier",
    "add_depth",
    "scale_depth",
    "persistence_depth",
    "quantity",
    "price",
    "identity_policy",
    "source_dataset_version",
    "created_at",
]

REPLAY_COLUMNS = [
    "lifecycle_id",
    "symbol",
    "session_date",
    "entry_ts",
    "last_event_ts",
    "exit_ts",
    "event_count",
    "entry_event_count",
    "add_event_count",
    "scale_event_count",
    "reduce_event_count",
    "exit_event_count",
    "max_add_depth",
    "max_scale_depth",
    "max_persistence_depth",
    "max_size_multiplier",
    "continuation_duration_minutes",
    "source_captured_only_flag",
    "canonical_sequence_valid_flag",
    "explicit_lifecycle_id_flag",
    "add_scale_chain_flag",
    "immediate_exit_flag",
    "canonical_persistence_quality_flag",
    "sequence_status",
]


@dataclass(frozen=True)
class CanonicalLifecycleReplay382Artifacts:
    canonical_lifecycle_event_stream: pd.DataFrame
    canonical_lifecycle_replay_panel: pd.DataFrame
    canonical_persistence_revalidation_panel: pd.DataFrame
    canonical_persistence_bucket_audit: pd.DataFrame
    canonical_revalidation_readiness_audit: pd.DataFrame
    task_382_decision: pd.DataFrame


def build_canonical_lifecycle_replay_revalidation_382(
    *,
    db_path: str | Path | None = None,
    task376_evaluation_path: Path = TASK_376_EVALUATION_PATH,
) -> CanonicalLifecycleReplay382Artifacts:
    event_stream = load_canonical_lifecycle_event_stream(db_path or DEFAULT_DB_PATH)
    replay_panel = build_canonical_lifecycle_replay_panel(event_stream)
    revalidation_panel, readiness = build_canonical_persistence_revalidation_panel(
        replay_panel,
        task376_evaluation_path=task376_evaluation_path,
    )
    bucket_audit = build_canonical_persistence_bucket_audit(revalidation_panel)
    decision = build_task_382_decision(event_stream, replay_panel, revalidation_panel, readiness)
    return CanonicalLifecycleReplay382Artifacts(
        canonical_lifecycle_event_stream=event_stream,
        canonical_lifecycle_replay_panel=replay_panel,
        canonical_persistence_revalidation_panel=revalidation_panel,
        canonical_persistence_bucket_audit=bucket_audit,
        canonical_revalidation_readiness_audit=readiness,
        task_382_decision=decision,
    )


def load_canonical_lifecycle_event_stream(db_path: str | Path) -> pd.DataFrame:
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame(columns=EVENT_STREAM_COLUMNS)

    placeholders = ",".join("?" for _ in CANONICAL_POSITION_EVENT_TYPES)
    query = f"""
        SELECT source_event_id, lifecycle_id, setup_id, symbol, session_date,
               event_timestamp, event_type, event_source, order_id, fill_id,
               trade_run_id, size_multiplier, add_depth, scale_depth, persistence_depth,
               details_json, source_dataset_version, created_at
        FROM continuation_source_events
        WHERE event_type IN ({placeholders})
           OR source_dataset_version = ?
        ORDER BY lifecycle_id ASC, event_timestamp ASC, source_event_id ASC
    """
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(query, tuple(sorted(CANONICAL_POSITION_EVENT_TYPES)) + (SOURCE_DATASET_VERSION,)).fetchall()
    finally:
        con.close()

    records: list[dict[str, Any]] = []
    for row in rows:
        raw = dict(row)
        details = _decode_details(raw.pop("details_json", None))
        canonical_event_type = str(details.get("canonical_event_type") or raw.get("event_type") or "")
        if canonical_event_type not in CANONICAL_POSITION_EVENT_TYPES:
            continue
        records.append(
            {
                **raw,
                "canonical_event_type": canonical_event_type,
                "quantity": details.get("quantity"),
                "price": details.get("price"),
                "identity_policy": details.get("identity_policy"),
            }
        )
    frame = pd.DataFrame(records)
    return _ensure_columns(frame, EVENT_STREAM_COLUMNS)


def build_canonical_lifecycle_replay_panel(event_stream: pd.DataFrame) -> pd.DataFrame:
    event_stream = _ensure_columns(event_stream.copy(), EVENT_STREAM_COLUMNS)
    if event_stream.empty:
        return pd.DataFrame(columns=REPLAY_COLUMNS)

    event_stream["event_timestamp_dt"] = pd.to_datetime(event_stream["event_timestamp"], errors="coerce", utc=True)
    event_stream = event_stream.sort_values(["lifecycle_id", "event_timestamp_dt", "source_event_id"]).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for lifecycle_id, group in event_stream.groupby("lifecycle_id", dropna=False, sort=False):
        event_types = group["canonical_event_type"].astype(str).tolist()
        timestamps = pd.to_datetime(group["event_timestamp"], errors="coerce", utc=True)
        entry_rows = group[group["canonical_event_type"].astype(str).eq("ENTRY")]
        exit_rows = group[group["canonical_event_type"].astype(str).eq("EXIT")]
        entry_ts = entry_rows["event_timestamp"].iloc[0] if not entry_rows.empty else ""
        last_event_ts = group["event_timestamp"].iloc[-1]
        exit_ts = exit_rows["event_timestamp"].iloc[-1] if not exit_rows.empty else ""
        duration = _minute_delta(entry_ts, exit_ts or last_event_ts)
        source_captured_only = group["event_source"].astype(str).eq("SOURCE_CAPTURED").all()
        sequence_valid, sequence_status = _validate_canonical_sequence(event_types, timestamps)
        add_count = int((group["canonical_event_type"].astype(str) == "ADD").sum())
        scale_count = int((group["canonical_event_type"].astype(str) == "SCALE").sum())
        reduce_count = int((group["canonical_event_type"].astype(str) == "REDUCE").sum())
        exit_count = int((group["canonical_event_type"].astype(str) == "EXIT").sum())
        immediate_exit = bool(exit_count > 0 and add_count == 0 and scale_count == 0 and duration <= 15)
        add_scale_chain = bool(add_count > 0 or scale_count > 0)
        quality = bool(sequence_valid and not immediate_exit and (add_scale_chain or duration >= 60))
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "symbol": group["symbol"].iloc[0],
                "session_date": group["session_date"].iloc[0],
                "entry_ts": entry_ts,
                "last_event_ts": last_event_ts,
                "exit_ts": exit_ts,
                "event_count": len(group),
                "entry_event_count": len(entry_rows),
                "add_event_count": add_count,
                "scale_event_count": scale_count,
                "reduce_event_count": reduce_count,
                "exit_event_count": exit_count,
                "max_add_depth": int(pd.to_numeric(group["add_depth"], errors="coerce").fillna(0).max()),
                "max_scale_depth": int(pd.to_numeric(group["scale_depth"], errors="coerce").fillna(0).max()),
                "max_persistence_depth": int(pd.to_numeric(group["persistence_depth"], errors="coerce").fillna(0).max()),
                "max_size_multiplier": float(pd.to_numeric(group["size_multiplier"], errors="coerce").fillna(0).max()),
                "continuation_duration_minutes": duration,
                "source_captured_only_flag": int(source_captured_only),
                "canonical_sequence_valid_flag": int(sequence_valid),
                "explicit_lifecycle_id_flag": int(bool(str(lifecycle_id).strip())),
                "add_scale_chain_flag": int(add_scale_chain),
                "immediate_exit_flag": int(immediate_exit),
                "canonical_persistence_quality_flag": int(quality),
                "sequence_status": sequence_status,
            }
        )
    return _ensure_columns(pd.DataFrame(rows), REPLAY_COLUMNS)


def build_canonical_persistence_revalidation_panel(
    replay_panel: pd.DataFrame,
    *,
    task376_evaluation_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    replay_panel = _ensure_columns(replay_panel.copy(), REPLAY_COLUMNS)
    if replay_panel.empty:
        return replay_panel.copy(), _readiness_audit(
            explicit_join_available=False,
            canonical_lifecycle_count=0,
            joined_lifecycle_count=0,
            reason="no_canonical_lifecycle_events",
        )
    if not task376_evaluation_path.exists():
        panel = replay_panel.copy()
        panel["persistence_universe_bucket"] = "unmapped_no_task376_panel"
        return panel, _readiness_audit(
            explicit_join_available=False,
            canonical_lifecycle_count=len(replay_panel),
            joined_lifecycle_count=0,
            reason="task376_panel_missing",
        )

    task376 = pd.read_csv(task376_evaluation_path, encoding="utf-8-sig")
    if "lifecycle_id" not in task376.columns:
        panel = replay_panel.copy()
        panel["persistence_universe_bucket"] = "unmapped_no_explicit_lifecycle_id"
        return panel, _readiness_audit(
            explicit_join_available=False,
            canonical_lifecycle_count=len(replay_panel),
            joined_lifecycle_count=0,
            reason="task376_lacks_explicit_lifecycle_id",
        )

    keep_columns = [
        column
        for column in [
            "lifecycle_id",
            "trade_id",
            "current_split",
            "persistence_universe_bucket",
            "data_leadership_gate_v1",
            "risk_gate_v1",
            "theme_prior_v1",
        ]
        if column in task376.columns
    ]
    task376 = task376[keep_columns].drop_duplicates(subset=["lifecycle_id"], keep="first")
    panel = replay_panel.merge(task376, on="lifecycle_id", how="left", indicator="task376_join_status")
    joined = int(panel["task376_join_status"].astype(str).eq("both").sum())
    panel["persistence_universe_bucket"] = panel["persistence_universe_bucket"].fillna("unmapped_explicit_lifecycle_id")
    return panel, _readiness_audit(
        explicit_join_available=True,
        canonical_lifecycle_count=len(replay_panel),
        joined_lifecycle_count=joined,
        reason="explicit_lifecycle_id_join_available" if joined else "explicit_lifecycle_id_join_empty",
    )


def build_canonical_persistence_bucket_audit(revalidation_panel: pd.DataFrame) -> pd.DataFrame:
    panel = revalidation_panel.copy()
    if panel.empty or "persistence_universe_bucket" not in panel.columns:
        return pd.DataFrame(
            columns=[
                "persistence_universe_bucket",
                "canonical_lifecycle_count",
                "canonical_quality_count",
                "canonical_quality_rate",
                "avg_add_count",
                "avg_scale_count",
                "avg_duration_minutes",
            ]
        )
    grouped = panel.groupby("persistence_universe_bucket", dropna=False)
    rows = []
    for bucket, group in grouped:
        quality = pd.to_numeric(group["canonical_persistence_quality_flag"], errors="coerce").fillna(0)
        rows.append(
            {
                "persistence_universe_bucket": bucket,
                "canonical_lifecycle_count": len(group),
                "canonical_quality_count": int(quality.sum()),
                "canonical_quality_rate": float(quality.mean()) if len(group) else 0.0,
                "avg_add_count": float(pd.to_numeric(group["add_event_count"], errors="coerce").fillna(0).mean()),
                "avg_scale_count": float(pd.to_numeric(group["scale_event_count"], errors="coerce").fillna(0).mean()),
                "avg_duration_minutes": float(
                    pd.to_numeric(group["continuation_duration_minutes"], errors="coerce").fillna(0).mean()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("canonical_lifecycle_count", ascending=False).reset_index(drop=True)


def build_task_382_decision(
    event_stream: pd.DataFrame,
    replay_panel: pd.DataFrame,
    revalidation_panel: pd.DataFrame,
    readiness: pd.DataFrame,
) -> pd.DataFrame:
    readiness_row = readiness.iloc[0].to_dict() if not readiness.empty else {}
    joined_count = int(readiness_row.get("joined_lifecycle_count", 0) or 0)
    explicit_join = bool(readiness_row.get("explicit_join_available_flag", False))
    valid_sequence_count = int(pd.to_numeric(replay_panel.get("canonical_sequence_valid_flag"), errors="coerce").fillna(0).sum()) if not replay_panel.empty else 0
    quality_count = int(pd.to_numeric(replay_panel.get("canonical_persistence_quality_flag"), errors="coerce").fillna(0).sum()) if not replay_panel.empty else 0
    revalidation_ready = "YES_CANONICAL_EXPLICIT_LAYER_ONLY" if explicit_join and joined_count > 0 else "NO_CANONICAL_MAPPING_REQUIRED"
    return pd.DataFrame(
        [
            {
                "task_382_verdict": "COMPLETE_PASS",
                "strategy_acceptance_status": "NOT_VALIDATED_CANONICAL_REVALIDATION_PENDING",
                "canonical_event_count": len(event_stream),
                "canonical_lifecycle_count": len(replay_panel),
                "canonical_sequence_valid_count": valid_sequence_count,
                "canonical_quality_lifecycle_count": quality_count,
                "explicit_task376_join_available_flag": int(explicit_join),
                "joined_task376_lifecycle_count": joined_count,
                "persistence_revalidation_ready": revalidation_ready,
                "label_overwrite_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "next_priority": "collect_canonical_lifecycle_stream" if len(replay_panel) == 0 else "add_explicit_lifecycle_id_to_universe_mapping",
            }
        ]
    )


def write_canonical_lifecycle_replay_revalidation_382(
    artifacts: CanonicalLifecycleReplay382Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.canonical_lifecycle_event_stream.to_csv(out_dir / "canonical_lifecycle_event_stream.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_lifecycle_replay_panel.to_csv(out_dir / "canonical_lifecycle_replay_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_persistence_revalidation_panel.to_csv(out_dir / "canonical_persistence_revalidation_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_persistence_bucket_audit.to_csv(out_dir / "canonical_persistence_bucket_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_revalidation_readiness_audit.to_csv(out_dir / "canonical_revalidation_readiness_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_382_decision.to_csv(out_dir / "task_382_decision.csv", index=False, encoding="utf-8-sig")


def _validate_canonical_sequence(event_types: list[str], timestamps: pd.Series) -> tuple[bool, str]:
    if not event_types:
        return False, "empty_lifecycle"
    if event_types[0] != "ENTRY":
        return False, "missing_entry_first_event"
    if event_types.count("ENTRY") != 1:
        return False, "entry_count_not_one"
    if timestamps.isna().any():
        return False, "timestamp_parse_failure"
    if not timestamps.is_monotonic_increasing:
        return False, "timestamp_order_violation"
    if "EXIT" in event_types and event_types.index("EXIT") != len(event_types) - 1:
        return False, "event_after_exit"
    return True, "valid"


def _readiness_audit(
    *,
    explicit_join_available: bool,
    canonical_lifecycle_count: int,
    joined_lifecycle_count: int,
    reason: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "explicit_join_available_flag": int(explicit_join_available),
                "canonical_lifecycle_count": canonical_lifecycle_count,
                "joined_lifecycle_count": joined_lifecycle_count,
                "readiness_reason": reason,
                "symbol_session_inference_used_flag": 0,
                "recovery_scoring_used_flag": 0,
            }
        ]
    )


def _minute_delta(start: object, end: object) -> float:
    start_dt = pd.to_datetime(start, errors="coerce", utc=True)
    end_dt = pd.to_datetime(end, errors="coerce", utc=True)
    if pd.isna(start_dt) or pd.isna(end_dt):
        return 0.0
    return float((end_dt - start_dt).total_seconds() / 60.0)


def _decode_details(value: object) -> dict:
    if value is None:
        return {}
    try:
        decoded = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype=object)
    return frame[columns + [column for column in frame.columns if column not in columns]]
