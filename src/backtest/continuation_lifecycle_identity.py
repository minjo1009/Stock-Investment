from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


IDENTITY_CONFIDENCE = {
    "explicit_setup_identity": 1.00,
    "explicit_trade_identity": 0.90,
    "explicit_session_identity": 0.80,
    "derived_session_continuity": 0.60,
    "replay_fallback_identity": 0.35,
}


@dataclass(frozen=True)
class ContinuationLifecycleIdentity:
    lifecycle_id: str
    setup_id: str
    symbol: str
    session_date: str
    lifecycle_start_ts: pd.Timestamp | None
    lifecycle_end_ts: pd.Timestamp | None
    identity_origin: str
    identity_confidence: float


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(numeric):
        return float(default)
    return numeric


def _identity_origin(setup_origin_type: str, session_bar_match: bool) -> str:
    if setup_origin_type in {"explicit_breakout_setup", "explicit_entry_setup"}:
        return "explicit_setup_identity"
    if setup_origin_type == "trade_linked_setup":
        return "explicit_trade_identity"
    if setup_origin_type == "chronology_linked_setup" and session_bar_match:
        return "explicit_session_identity"
    if setup_origin_type == "chronology_linked_setup":
        return "derived_session_continuity"
    return "replay_fallback_identity"


def _coalesce_columns(frame: pd.DataFrame, base_name: str, default: Any) -> pd.DataFrame:
    if base_name in frame.columns:
        frame[base_name] = frame[base_name].where(frame[base_name].notna(), default)
        return frame
    candidate_cols = [column for column in frame.columns if column == base_name or column.startswith(f"{base_name}_")]
    if not candidate_cols:
        frame[base_name] = default
        return frame
    combined = frame[candidate_cols[0]]
    for column in candidate_cols[1:]:
        combined = combined.where(combined.notna(), frame[column])
    frame[base_name] = combined.where(combined.notna(), default)
    return frame


def build_continuation_lifecycle_identity(
    setup_frame: pd.DataFrame,
    multi_event_dataset_df: pd.DataFrame,
    source_truth_replay_dataset_df: pd.DataFrame,
    setup_identity_df: pd.DataFrame,
    lineage_rows_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    _ = setup_frame
    _ = multi_event_dataset_df
    _ = source_truth_replay_dataset_df
    if lineage_rows_df.empty:
        lifecycle_columns = [
            "lifecycle_id",
            "setup_id",
            "symbol",
            "session_date",
            "lifecycle_start_ts",
            "lifecycle_end_ts",
            "identity_origin",
            "identity_confidence",
            "parent_lifecycle_id",
            "is_root_lifecycle",
            "lifecycle_rank_within_setup",
        ]
        event_columns = [
            "continuation_id",
            "lifecycle_id",
            "setup_id",
            "parent_lifecycle_id",
            "canonical_event_id",
            "event_rank_within_lifecycle",
        ]
        summary_columns = ["identity_origin", "lifecycle_count", "root_lifecycle_count", "avg_identity_confidence"]
        return pd.DataFrame(columns=lifecycle_columns), pd.DataFrame(columns=event_columns), pd.DataFrame(columns=summary_columns)

    setup = setup_identity_df.copy()
    frame = lineage_rows_df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    if not setup.empty:
        setup = setup.drop_duplicates(subset=["setup_id"], keep="first")
        frame = frame.merge(
            setup[["setup_id", "setup_origin_type", "setup_confidence", "session_bar_match"]],
            on="setup_id",
            how="left",
        )
    frame = _coalesce_columns(frame, "setup_origin_type", "replay_linked_setup")
    frame = _coalesce_columns(frame, "setup_confidence", 0.35)
    frame = _coalesce_columns(frame, "session_bar_match", False)

    lifecycle_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    for setup_id, setup_group in frame.groupby("setup_id", dropna=False, sort=False):
        ordered_setup = (
            setup_group.groupby("continuation_id", dropna=False)
            .agg(
                symbol=("symbol", "first"),
                session_date=("session_date", "first"),
                lifecycle_start_ts=("timestamp", "min"),
                lifecycle_end_ts=("timestamp", "max"),
                setup_origin_type=("setup_origin_type", "first"),
                setup_confidence=("setup_confidence", "first"),
                session_bar_match=("session_bar_match", "first"),
            )
            .reset_index()
            .sort_values(["lifecycle_start_ts", "continuation_id"], kind="stable")
            .reset_index(drop=True)
        )

        previous_lifecycle_id: str | None = None
        previous_terminal = False
        for rank, (_, lifecycle_row) in enumerate(ordered_setup.iterrows(), start=1):
            continuation_id = _safe_text(lifecycle_row.get("continuation_id"), "unknown_continuation")
            lifecycle_id = continuation_id
            identity_origin = _identity_origin(
                _safe_text(lifecycle_row.get("setup_origin_type"), "replay_linked_setup"),
                bool(lifecycle_row.get("session_bar_match", False)),
            )
            parent_lifecycle_id = previous_lifecycle_id if rank > 1 and previous_terminal else None
            lifecycle_rows.append(
                {
                    "lifecycle_id": lifecycle_id,
                    "setup_id": _safe_text(setup_id, "unknown_setup"),
                    "symbol": _safe_text(lifecycle_row.get("symbol"), "UNKNOWN"),
                    "session_date": _safe_text(lifecycle_row.get("session_date"), "unknown_date"),
                    "lifecycle_start_ts": pd.to_datetime(lifecycle_row.get("lifecycle_start_ts"), errors="coerce", utc=True),
                    "lifecycle_end_ts": pd.to_datetime(lifecycle_row.get("lifecycle_end_ts"), errors="coerce", utc=True),
                    "identity_origin": identity_origin,
                    "identity_confidence": round(IDENTITY_CONFIDENCE[identity_origin], 6),
                    "parent_lifecycle_id": parent_lifecycle_id,
                    "is_root_lifecycle": parent_lifecycle_id is None,
                    "lifecycle_rank_within_setup": rank,
                }
            )

            lifecycle_events = frame[frame["continuation_id"].astype(str).eq(continuation_id)].sort_values(
                ["symbol", "session_date", "timestamp", "event_index", "event_id"],
                kind="stable",
            ).reset_index(drop=True)
            for event_rank, (_, event_row) in enumerate(lifecycle_events.iterrows(), start=1):
                event_rows.append(
                    {
                        "continuation_id": continuation_id,
                        "lifecycle_id": lifecycle_id,
                        "setup_id": _safe_text(setup_id, "unknown_setup"),
                        "parent_lifecycle_id": parent_lifecycle_id,
                        "canonical_event_id": f"{lifecycle_id}|evt_{event_rank:03d}",
                        "event_rank_within_lifecycle": event_rank,
                    }
                )
            previous_lifecycle_id = lifecycle_id
            terminal_events = set(lifecycle_events["lineage_event_type"].astype(str))
            previous_terminal = bool({"EXIT_TRIGGER", "INVALIDATION"} & terminal_events)

    lifecycle_identity_df = pd.DataFrame(lifecycle_rows).sort_values(
        ["symbol", "session_date", "lifecycle_start_ts", "lifecycle_id"],
        kind="stable",
    ).reset_index(drop=True)
    event_identity_df = pd.DataFrame(event_rows).sort_values(
        ["lifecycle_id", "event_rank_within_lifecycle"],
        kind="stable",
    ).reset_index(drop=True)
    identity_origin_summary_df = (
        lifecycle_identity_df.groupby("identity_origin", dropna=False)
        .agg(
            lifecycle_count=("lifecycle_id", "size"),
            root_lifecycle_count=("is_root_lifecycle", lambda values: int(pd.Series(values).fillna(False).astype(bool).sum())),
            avg_identity_confidence=("identity_confidence", lambda values: round(float(pd.to_numeric(values, errors="coerce").fillna(0.0).mean()), 6)),
        )
        .reset_index()
        .sort_values(["lifecycle_count", "identity_origin"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    return lifecycle_identity_df, event_identity_df, identity_origin_summary_df
