from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


SOURCE_TRUTH_ORIGINS = {"explicit_breakout_setup", "explicit_entry_setup", "trade_linked_setup"}
SOURCE_TRUTH_LINKS = {"trade_id_master_match", "breakout_bar_match", "entry_bar_match"}


@dataclass(frozen=True)
class SourceTruthContinuationLineage:
    continuation_id: str
    setup_id: str
    ordered_events: tuple[dict[str, Any], ...]
    lineage_confidence: float
    lineage_break_reason: str


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


def _map_lineage_event_type(event_type: str) -> str:
    mapping = {
        "SETUP": "SETUP_DETECTED",
        "PROBE_ENTRY": "PROBE_ENTRY",
        "ADD_ATTEMPT": "ADD_ATTEMPT",
        "ADD_CONFIRMED": "ADD_CONFIRMED",
        "SIZE_INCREASE": "SIZE_INCREASE",
        "PERSISTENCE_CONFIRMED": "PERSISTENCE_CONFIRMED",
        "REDUCTION_TRIGGER": "REDUCTION_TRIGGER",
        "EXIT_TRIGGER": "EXIT_TRIGGER",
        "INVALIDATION": "INVALIDATION",
    }
    return mapping.get(str(event_type), str(event_type))


def _event_source(row: pd.Series) -> str:
    setup_origin_type = _safe_text(row.get("setup_origin_type"))
    linkage_source = _safe_text(row.get("linkage_source"))
    if setup_origin_type in SOURCE_TRUTH_ORIGINS and linkage_source in SOURCE_TRUTH_LINKS:
        return "SOURCE_TRUTH"
    if setup_origin_type in SOURCE_TRUTH_ORIGINS or _safe_text(row.get("setup_origin_type")) in {"chronology_linked_setup"}:
        return "SHADOW_INFERRED"
    return "REPLAY_INFERRED"


def _lineage_break_reason(group: pd.DataFrame) -> str:
    setup_origins = set(group["setup_origin_type"].astype(str))
    statuses = set(group.get("intraday_match_status", pd.Series(dtype=str)).astype(str)) if "intraday_match_status" in group.columns else set()
    reasons = set(group.get("transition_reason", pd.Series(dtype=str)).astype(str)) if "transition_reason" in group.columns else set()
    timestamps = pd.to_datetime(group["timestamp"], errors="coerce", utc=True)

    if setup_origins == {"unmatched_setup"} or setup_origins == {"replay_linked_setup"}:
        return "missing_setup_link"
    if "missing_intraday_session" in statuses:
        return "missing_intraday_session"
    if timestamps.notna().sum() >= 2:
        deltas = timestamps.sort_values().diff().dropna()
        if not deltas.empty and deltas.max() > pd.Timedelta(minutes=20):
            return "timestamp_gap_break"
    if any(reason in {"dislocation_exit", "size_to_zero", "no_live_position", "fragile_exit"} for reason in reasons):
        return "terminal_replay_break"
    if group["setup_id"].astype(str).nunique() > 1:
        return "setup_boundary_break"
    return "none"


def _lineage_quality(group: pd.DataFrame) -> str:
    sources = set(group["event_source"].astype(str))
    if sources == {"SOURCE_TRUTH"}:
        return "source_truth"
    if "SOURCE_TRUTH" in sources or "SHADOW_INFERRED" in sources:
        return "mixed"
    return "synthetic_only"


def build_source_truth_lineage(
    source_truth_replay_dataset_df: pd.DataFrame,
    setup_identity_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if source_truth_replay_dataset_df.empty:
        empty_row = pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "event_id",
                "lineage_event_type",
                "event_source",
                "lineage_confidence",
                "lineage_quality",
                "lineage_break_reason",
                "source_truth_flag",
            ]
        )
        empty_summary = pd.DataFrame(columns=["continuation_id", "setup_id", "lineage_confidence", "lineage_quality", "lineage_break_reason"])
        empty_fidelity = pd.DataFrame(columns=["metric_name", "metric_value"])
        empty_conf = pd.DataFrame(columns=["continuation_id", "setup_id", "lineage_confidence", "lineage_quality", "source_truth_flag"])
        return empty_row, empty_summary, empty_fidelity, empty_conf

    frame = source_truth_replay_dataset_df.copy()
    setup = setup_identity_df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    if not setup.empty:
        frame = frame.merge(setup, on=["setup_id", "symbol", "session_date"], how="left")

    frame["lineage_event_type"] = frame["event_type"].astype(str).map(_map_lineage_event_type)
    frame["event_source"] = frame.apply(_event_source, axis=1)

    lineage_rows: list[pd.DataFrame] = []
    continuation_rows: list[dict[str, Any]] = []
    confidence_rows: list[dict[str, Any]] = []
    for continuation_id, group in frame.groupby("continuation_id", dropna=False, sort=False):
        ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        weakening_idx: int | None = None
        reduction_indices = ordered.index[ordered["lineage_event_type"].astype(str).eq("REDUCTION_TRIGGER")].tolist()
        if reduction_indices:
            weakening_idx = int(reduction_indices[0])
            ordered.loc[weakening_idx, "lineage_event_type"] = "FRAGILITY_WARNING"

        ordered["lineage_confidence"] = pd.to_numeric(ordered.get("lineage_confidence"), errors="coerce").fillna(0.10)
        lineage_confidence = round(float(ordered["lineage_confidence"].min()), 6)
        break_reason = _lineage_break_reason(ordered)
        quality = _lineage_quality(ordered)
        source_truth_flag = quality == "source_truth"
        ordered["lineage_quality"] = quality
        ordered["lineage_break_reason"] = break_reason
        ordered["source_truth_flag"] = source_truth_flag
        lineage_rows.append(ordered)
        continuation_rows.append(
            {
                "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                "setup_id": _safe_text(ordered.iloc[0].get("setup_id"), "unknown_setup"),
                "symbol": _safe_text(ordered.iloc[0].get("symbol"), "UNKNOWN"),
                "lineage_confidence": lineage_confidence,
                "lineage_quality": quality,
                "lineage_break_reason": break_reason,
                "source_truth_flag": source_truth_flag,
                "event_count": int(len(ordered)),
                "distinct_lineage_event_type_count": int(ordered["lineage_event_type"].astype(str).nunique()),
            }
        )
        confidence_rows.append(
            {
                "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                "setup_id": _safe_text(ordered.iloc[0].get("setup_id"), "unknown_setup"),
                "lineage_confidence": lineage_confidence,
                "lineage_quality": quality,
                "source_truth_flag": source_truth_flag,
            }
        )

    lineage_row_df = pd.concat(lineage_rows, ignore_index=True) if lineage_rows else pd.DataFrame()
    lineage_summary_df = pd.DataFrame(continuation_rows).sort_values(
        ["lineage_confidence", "continuation_id"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
    lineage_confidence_df = pd.DataFrame(confidence_rows).sort_values(
        ["lineage_confidence", "continuation_id"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
    replay_fidelity_df = build_replay_fidelity_diagnostics(lineage_row_df, lineage_summary_df)
    return lineage_row_df, lineage_summary_df, replay_fidelity_df, lineage_confidence_df


def build_replay_fidelity_diagnostics(
    lineage_row_df: pd.DataFrame,
    lineage_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    if lineage_summary_df.empty:
        return pd.DataFrame(columns=["metric_name", "metric_value"])

    continuation_count = max(len(lineage_summary_df), 1)
    source_truth_share = float(lineage_summary_df["lineage_quality"].astype(str).eq("source_truth").sum() / continuation_count)
    inferred_share = float(lineage_summary_df["lineage_quality"].astype(str).ne("source_truth").sum() / continuation_count)
    multi_stage_share = float(
        (
            pd.to_numeric(lineage_summary_df["distinct_lineage_event_type_count"], errors="coerce").fillna(0.0).ge(4)
            & lineage_summary_df["continuation_id"].astype(str).isin(
                lineage_row_df.loc[lineage_row_df["lineage_event_type"].astype(str).eq("PROBE_ENTRY"), "continuation_id"].astype(str)
            )
        ).sum()
        / continuation_count
    )
    confidence_ge_080_share = float(pd.to_numeric(lineage_summary_df["lineage_confidence"], errors="coerce").fillna(0.0).ge(0.80).sum() / continuation_count)

    add_or_scale_share = float(
        lineage_row_df.groupby("continuation_id", dropna=False)["lineage_event_type"]
        .agg(lambda values: any(str(value) in {"ADD_CONFIRMED", "SIZE_INCREASE"} for value in values))
        .sum()
        / continuation_count
    )
    replay_fidelity_score = (
        0.40 * source_truth_share
        + 0.20 * multi_stage_share
        + 0.20 * confidence_ge_080_share
        + 0.20 * add_or_scale_share
    )

    metrics = [
        {"metric_name": "source_truth_lineage_share", "metric_value": round(source_truth_share, 6)},
        {"metric_name": "inferred_lineage_share", "metric_value": round(inferred_share, 6)},
        {"metric_name": "multi_stage_lineage_share", "metric_value": round(multi_stage_share, 6)},
        {"metric_name": "share_confidence_ge_0_80", "metric_value": round(confidence_ge_080_share, 6)},
        {"metric_name": "share_add_or_scale_lineage", "metric_value": round(add_or_scale_share, 6)},
        {"metric_name": "replay_fidelity_score", "metric_value": round(replay_fidelity_score, 6)},
    ]

    confidence_distribution = (
        lineage_summary_df.assign(
            confidence_bucket=pd.cut(
                pd.to_numeric(lineage_summary_df["lineage_confidence"], errors="coerce").fillna(0.0),
                bins=[-0.001, 0.349999, 0.649999, 0.799999, 1.000001],
                labels=["0.10-0.35", "0.35-0.65", "0.65-0.80", "0.80-1.00"],
            )
        )
        .groupby("confidence_bucket", dropna=False, observed=False)
        .size()
        .reset_index(name="count")
    )
    for _, row in confidence_distribution.iterrows():
        metrics.append(
            {
                "metric_name": f"lineage_confidence_distribution::{_safe_text(row['confidence_bucket'], 'unknown')}",
                "metric_value": round(float(_safe_float(row["count"], 0.0) / continuation_count), 6),
            }
        )
    return pd.DataFrame(metrics)
