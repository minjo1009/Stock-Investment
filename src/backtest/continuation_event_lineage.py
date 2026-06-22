from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


SOURCE_LINKED_SOURCES = {"trade_id_master_match", "breakout_bar_match", "entry_bar_match"}
ADD_EVENTS = {"ADD_ATTEMPT", "ADD_CONFIRMED", "SIZE_INCREASE"}


@dataclass(frozen=True)
class ContinuationEventLineage:
    continuation_id: str
    ordered_events: tuple[dict[str, Any], ...]
    lineage_quality: str
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


def _lineage_break_reason(group: pd.DataFrame) -> str:
    sources = set(group["linkage_source"].astype(str))
    statuses = set(group.get("intraday_match_status", pd.Series(dtype=str)).astype(str)) if "intraday_match_status" in group.columns else set()
    reasons = set(group.get("transition_reason", pd.Series(dtype=str)).astype(str)) if "transition_reason" in group.columns else set()
    event_types = set(group["event_type"].astype(str))
    timestamps = pd.to_datetime(group["timestamp"], errors="coerce", utc=True)

    if "unmatched_synthetic" in sources:
        return "missing_master_match"
    if "missing_intraday_session" in statuses:
        return "missing_intraday_session"
    if "EXIT_TRIGGER" in event_types and any(reason in {"dislocation_exit", "size_to_zero", "no_live_position", "fragile_exit"} for reason in reasons):
        return "terminal_replay_break"
    if timestamps.notna().sum() >= 2:
        deltas = timestamps.sort_values().diff().dropna()
        if not deltas.empty and deltas.max() > pd.Timedelta(minutes=20):
            return "timestamp_gap_break"
    if group["setup_id"].astype(str).nunique() > 1:
        return "setup_boundary_break"
    return "none"


def _lineage_quality(group: pd.DataFrame) -> str:
    sources = set(group["linkage_source"].astype(str))
    if sources and sources.issubset(SOURCE_LINKED_SOURCES):
        return "source_truth"
    if sources and sources.issubset({"replay_continuity_fallback", "unmatched_synthetic"}):
        return "synthetic_only"
    return "mixed"


def build_continuation_event_lineage(
    multi_event_dataset_df: pd.DataFrame,
    row_identity_df: pd.DataFrame,
    continuation_identity_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if multi_event_dataset_df.empty:
        empty_row = pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "event_id",
                "event_type",
                "timestamp",
                "linkage_source",
                "lineage_confidence",
                "lineage_quality",
                "lineage_break_reason",
                "source_linked_flag",
            ]
        )
        empty_cont = pd.DataFrame(
            columns=[
                "continuation_id",
                "lineage_quality",
                "lineage_break_reason",
                "event_count",
                "distinct_event_type_count",
                "max_lineage_confidence",
                "source_linked_flag",
            ]
        )
        empty_depth = pd.DataFrame(columns=["metric_name", "bucket", "bucket_value"])
        empty_fidelity = pd.DataFrame(columns=["metric_name", "metric_value"])
        return empty_row, empty_cont, empty_depth, empty_fidelity

    merged = multi_event_dataset_df.merge(
        row_identity_df[
            [
                "continuation_id",
                "event_id",
                "linkage_source",
                "lineage_confidence",
                "source_linked_flag",
                "intraday_match_status",
            ]
        ],
        on=["continuation_id", "event_id"],
        how="left",
    )
    merged["timestamp"] = pd.to_datetime(merged["timestamp"], errors="coerce", utc=True)
    if "intraday_match_status_x" in merged.columns or "intraday_match_status_y" in merged.columns:
        left_status = merged["intraday_match_status_x"] if "intraday_match_status_x" in merged.columns else pd.Series(index=merged.index, dtype=object)
        right_status = merged["intraday_match_status_y"] if "intraday_match_status_y" in merged.columns else pd.Series(index=merged.index, dtype=object)
        merged["intraday_match_status"] = left_status.where(left_status.notna(), right_status)
        merged = merged.drop(columns=[column for column in ("intraday_match_status_x", "intraday_match_status_y") if column in merged.columns])

    continuation_rows: list[dict[str, Any]] = []
    lineage_rows: list[pd.DataFrame] = []
    lineages: list[ContinuationEventLineage] = []
    for continuation_id, group in merged.groupby("continuation_id", dropna=False, sort=False):
        ordered = group.sort_values(["timestamp", "event_index", "event_id"], kind="stable").reset_index(drop=True)
        quality = _lineage_quality(ordered)
        break_reason = _lineage_break_reason(ordered)
        lineages.append(
            ContinuationEventLineage(
                continuation_id=_safe_text(continuation_id, "unknown_continuation"),
                ordered_events=tuple(ordered.to_dict("records")),
                lineage_quality=quality,
                lineage_break_reason=break_reason,
            )
        )
        scoped = ordered.copy()
        scoped["lineage_quality"] = quality
        scoped["lineage_break_reason"] = break_reason
        lineage_rows.append(scoped)
        continuation_rows.append(
            {
                "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                "setup_id": _safe_text(ordered.iloc[0].get("setup_id"), "unknown_setup"),
                "symbol": _safe_text(ordered.iloc[0].get("symbol"), "UNKNOWN"),
                "lineage_quality": quality,
                "lineage_break_reason": break_reason,
                "event_count": int(len(ordered)),
                "distinct_event_type_count": int(ordered["event_type"].astype(str).nunique()),
                "max_lineage_confidence": round(float(pd.to_numeric(ordered["lineage_confidence"], errors="coerce").fillna(0.0).max()), 6),
                "source_linked_flag": bool(ordered["source_linked_flag"].any()),
            }
        )

    lineage_row_df = pd.concat(lineage_rows, ignore_index=True) if lineage_rows else pd.DataFrame()
    continuation_lineage_df = pd.DataFrame(continuation_rows)
    if not continuation_identity_df.empty and not continuation_lineage_df.empty:
        continuation_lineage_df = continuation_identity_df.merge(
            continuation_lineage_df,
            on=["continuation_id", "setup_id"],
            how="left",
            suffixes=("_identity", ""),
        )
        if "source_linked_flag_identity" in continuation_lineage_df.columns:
            if "source_linked_flag" in continuation_lineage_df.columns:
                continuation_lineage_df["source_linked_flag"] = (
                    continuation_lineage_df["source_linked_flag"].fillna(False).astype(bool)
                    | continuation_lineage_df["source_linked_flag_identity"].fillna(False).astype(bool)
                )
            else:
                continuation_lineage_df["source_linked_flag"] = continuation_lineage_df["source_linked_flag_identity"].fillna(False).astype(bool)
            continuation_lineage_df = continuation_lineage_df.drop(columns=["source_linked_flag_identity"])
        continuation_lineage_df["source_linked_flag"] = continuation_lineage_df["source_linked_flag"].fillna(False).astype(bool)

    continuation_depth_df = _build_continuation_depth_distribution(lineage_row_df, continuation_lineage_df)
    replay_fidelity_df = _build_replay_fidelity_metrics(lineage_row_df, continuation_lineage_df)
    return lineage_row_df, continuation_lineage_df, continuation_depth_df, replay_fidelity_df


def _build_continuation_depth_distribution(
    lineage_row_df: pd.DataFrame,
    continuation_lineage_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if continuation_lineage_df.empty:
        return pd.DataFrame(columns=["metric_name", "bucket", "bucket_value"])

    event_count_dist = (
        continuation_lineage_df.groupby("event_count", dropna=False).size().reset_index(name="count").sort_values("event_count", kind="stable")
    )
    for _, row in event_count_dist.iterrows():
        rows.append({"metric_name": "continuation_depth_distribution", "bucket": str(int(_safe_float(row["event_count"], 0))), "bucket_value": int(row["count"])})

    persistence = (
        lineage_row_df.assign(has_persist=lineage_row_df["event_type"].astype(str).eq("PERSISTENCE_CONFIRMED"))
        .groupby("continuation_id", dropna=False)["has_persist"]
        .sum()
        .reset_index(name="persist_count")
    )
    persist_dist = persistence.groupby("persist_count", dropna=False).size().reset_index(name="count").sort_values("persist_count", kind="stable")
    for _, row in persist_dist.iterrows():
        rows.append({"metric_name": "persistence_depth_distribution", "bucket": str(int(_safe_float(row["persist_count"], 0))), "bucket_value": int(row["count"])})

    add_rows = []
    for continuation_id, group in lineage_row_df.groupby("continuation_id", dropna=False, sort=False):
        event_types = set(group["event_type"].astype(str))
        if "SIZE_INCREASE" in event_types:
            bucket = "SIZE_INCREASE"
        elif "ADD_CONFIRMED" in event_types:
            bucket = "ADD_CONFIRMED"
        elif "ADD_ATTEMPT" in event_types:
            bucket = "ADD_ATTEMPT_ONLY"
        else:
            bucket = "NO_ADD"
        add_rows.append({"continuation_id": continuation_id, "bucket": bucket})
    add_depth = pd.DataFrame(add_rows)
    if not add_depth.empty:
        add_dist = add_depth.groupby("bucket", dropna=False).size().reset_index(name="count").sort_values("bucket", kind="stable")
        for _, row in add_dist.iterrows():
            rows.append({"metric_name": "add_depth_distribution", "bucket": _safe_text(row["bucket"]), "bucket_value": int(row["count"])})

    return pd.DataFrame(rows)


def _build_replay_fidelity_metrics(
    lineage_row_df: pd.DataFrame,
    continuation_lineage_df: pd.DataFrame,
) -> pd.DataFrame:
    if continuation_lineage_df.empty:
        return pd.DataFrame(columns=["metric_name", "metric_value"])

    continuation_count = max(int(len(continuation_lineage_df)), 1)
    source_linked_share = float(continuation_lineage_df["lineage_quality"].astype(str).eq("source_truth").sum() / continuation_count)
    synthetic_only_share = float(continuation_lineage_df["lineage_quality"].astype(str).eq("synthetic_only").sum() / continuation_count)
    multi_stage_share = float(pd.to_numeric(continuation_lineage_df["distinct_event_type_count"], errors="coerce").fillna(0.0).ge(3).sum() / continuation_count)
    confidence_ge_080_share = float(pd.to_numeric(continuation_lineage_df["max_lineage_confidence"], errors="coerce").fillna(0.0).ge(0.80).sum() / continuation_count)
    replay_fidelity_score = 0.50 * source_linked_share + 0.25 * multi_stage_share + 0.25 * confidence_ge_080_share

    confidence_distribution = (
        continuation_lineage_df.assign(
            confidence_bucket=pd.cut(
                pd.to_numeric(continuation_lineage_df["max_lineage_confidence"], errors="coerce").fillna(0.0),
                bins=[-0.001, 0.349999, 0.649999, 0.799999, 1.000001],
                labels=["0.10-0.35", "0.35-0.65", "0.65-0.80", "0.80-1.00"],
            )
        )
        .groupby("confidence_bucket", dropna=False, observed=False)
        .size()
        .reset_index(name="count")
    )

    metrics = [
        {"metric_name": "source_linked_continuation_share", "metric_value": round(source_linked_share, 6)},
        {"metric_name": "synthetic_only_share", "metric_value": round(synthetic_only_share, 6)},
        {"metric_name": "multi_stage_continuation_share", "metric_value": round(multi_stage_share, 6)},
        {"metric_name": "share_confidence_ge_0_80", "metric_value": round(confidence_ge_080_share, 6)},
        {"metric_name": "replay_fidelity_score", "metric_value": round(replay_fidelity_score, 6)},
    ]
    for _, row in confidence_distribution.iterrows():
        metrics.append(
            {
                "metric_name": f"lineage_confidence_distribution::{_safe_text(row['confidence_bucket'], 'unknown')}",
                "metric_value": round(float(_safe_float(row["count"], 0.0) / continuation_count), 6),
            }
        )
    return pd.DataFrame(metrics)
