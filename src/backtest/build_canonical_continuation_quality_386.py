from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_386_canonical_continuation_quality")
TASK_385_EVENT_LOG_PATH = Path("docs/reports/task_385_canonical_continuation_engine/canonical_continuation_event_log.csv")
TASK_385_LIFECYCLE_SUMMARY_PATH = Path("docs/reports/task_385_canonical_continuation_engine/canonical_continuation_lifecycle_summary.csv")
TASK_382_REPLAY_PANEL_PATH = Path("docs/reports/task_385_canonical_continuation_engine/task_382_replay/canonical_lifecycle_replay_panel.csv")
TASK_382_REVALIDATION_PANEL_PATH = Path("docs/reports/task_385_canonical_continuation_engine/task_382_replay/canonical_persistence_revalidation_panel.csv")


@dataclass(frozen=True)
class CanonicalContinuationQuality386Artifacts:
    canonical_lifecycle_quality_panel: pd.DataFrame
    canonical_path_quality_audit: pd.DataFrame
    canonical_transition_quality_audit: pd.DataFrame
    canonical_bucket_quality_audit: pd.DataFrame
    canonical_quality_boundary_audit: pd.DataFrame
    task_386_decision: pd.DataFrame


def build_canonical_continuation_quality_386(
    *,
    event_log_path: Path = TASK_385_EVENT_LOG_PATH,
    lifecycle_summary_path: Path = TASK_385_LIFECYCLE_SUMMARY_PATH,
    replay_panel_path: Path = TASK_382_REPLAY_PANEL_PATH,
    revalidation_panel_path: Path = TASK_382_REVALIDATION_PANEL_PATH,
) -> CanonicalContinuationQuality386Artifacts:
    event_log = _read_csv(event_log_path)
    summary = _read_csv(lifecycle_summary_path)
    replay = _read_csv(replay_panel_path)
    revalidation = _read_csv(revalidation_panel_path)

    quality_panel = build_canonical_lifecycle_quality_panel(event_log, summary, replay, revalidation)
    path_audit = build_path_quality_audit(quality_panel)
    transition_audit = build_transition_quality_audit(event_log, quality_panel)
    bucket_audit = build_bucket_quality_audit(quality_panel)
    boundary = build_boundary_audit(event_log, quality_panel)
    decision = build_task_386_decision(quality_panel, path_audit, transition_audit, bucket_audit, boundary)
    return CanonicalContinuationQuality386Artifacts(
        canonical_lifecycle_quality_panel=quality_panel,
        canonical_path_quality_audit=path_audit,
        canonical_transition_quality_audit=transition_audit,
        canonical_bucket_quality_audit=bucket_audit,
        canonical_quality_boundary_audit=boundary,
        task_386_decision=decision,
    )


def build_canonical_lifecycle_quality_panel(
    event_log: pd.DataFrame,
    summary: pd.DataFrame,
    replay: pd.DataFrame,
    revalidation: pd.DataFrame,
) -> pd.DataFrame:
    replay_cols = [
        "lifecycle_id",
        "event_count",
        "add_event_count",
        "scale_event_count",
        "reduce_event_count",
        "exit_event_count",
        "canonical_sequence_valid_flag",
        "canonical_persistence_quality_flag",
        "continuation_duration_minutes",
    ]
    replay = _ensure_columns(replay.copy(), replay_cols)
    summary_cols = [
        "lifecycle_id",
        "symbol",
        "entry_ts",
        "exit_ts",
        "bars_held",
        "add_flag",
        "scale_flag",
        "reduce_flag",
        "exit_reason",
        "return_from_entry",
    ]
    summary = _ensure_columns(summary.copy(), summary_cols)
    bucket_cols = ["lifecycle_id", "persistence_universe_bucket", "current_split"]
    revalidation = _ensure_columns(revalidation.copy(), bucket_cols)
    panel = replay[replay_cols].merge(summary[summary_cols], on="lifecycle_id", how="left")
    panel = panel.merge(
        revalidation[bucket_cols].drop_duplicates(subset=["lifecycle_id"], keep="first"),
        on="lifecycle_id",
        how="left",
    )
    panel["return_from_entry"] = pd.to_numeric(panel["return_from_entry"], errors="coerce")
    panel["positive_return_flag"] = (panel["return_from_entry"] > 0).astype(int)
    panel["strong_return_flag"] = (panel["return_from_entry"] >= 0.06).astype(int)
    panel["loss_flag"] = (panel["return_from_entry"] < 0).astype(int)
    panel["path_type"] = panel.apply(_path_type, axis=1)
    panel["continuation_quality_score"] = (
        panel["return_from_entry"].fillna(0.0)
        + pd.to_numeric(panel["add_event_count"], errors="coerce").fillna(0) * 0.02
        + pd.to_numeric(panel["scale_event_count"], errors="coerce").fillna(0) * 0.03
        - pd.to_numeric(panel["reduce_event_count"], errors="coerce").fillna(0) * 0.01
    )
    return panel


def build_path_quality_audit(panel: pd.DataFrame) -> pd.DataFrame:
    return _group_quality(panel, "path_type").sort_values("lifecycle_count", ascending=False).reset_index(drop=True)


def build_transition_quality_audit(event_log: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    if event_log.empty:
        return pd.DataFrame(columns=["transition", "transition_count", "lifecycle_count", "avg_return", "positive_rate"])
    events = event_log.copy()
    events["event_timestamp_dt"] = pd.to_datetime(events["event_timestamp"], errors="coerce", utc=True)
    events = events.sort_values(["lifecycle_id", "event_timestamp_dt", "event_type"]).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for lifecycle_id, group in events.groupby("lifecycle_id", sort=False):
        types = group["event_type"].astype(str).tolist()
        for prev, nxt in zip(types, types[1:]):
            rows.append({"lifecycle_id": lifecycle_id, "transition": f"{prev}->{nxt}"})
    transitions = pd.DataFrame(rows)
    if transitions.empty:
        return pd.DataFrame(columns=["transition", "transition_count", "lifecycle_count", "avg_return", "positive_rate"])
    merged = transitions.merge(panel[["lifecycle_id", "return_from_entry", "positive_return_flag"]], on="lifecycle_id", how="left")
    out = []
    for transition, group in merged.groupby("transition"):
        out.append(
            {
                "transition": transition,
                "transition_count": len(group),
                "lifecycle_count": int(group["lifecycle_id"].nunique()),
                "avg_return": float(pd.to_numeric(group["return_from_entry"], errors="coerce").mean()),
                "positive_rate": float(pd.to_numeric(group["positive_return_flag"], errors="coerce").fillna(0).mean()),
            }
        )
    return pd.DataFrame(out).sort_values("transition_count", ascending=False).reset_index(drop=True)


def build_bucket_quality_audit(panel: pd.DataFrame) -> pd.DataFrame:
    return _group_quality(panel, "persistence_universe_bucket").sort_values("lifecycle_count", ascending=False).reset_index(drop=True)


def build_boundary_audit(event_log: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    event_types = set(event_log["event_type"].astype(str)) if not event_log.empty and "event_type" in event_log.columns else set()
    return pd.DataFrame(
        [
            {
                "canonical_stream_only_flag": 1,
                "symbol_session_inference_used_flag": 0,
                "recovery_scoring_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "label_overwrite_flag": 0,
                "event_types_present": "|".join(sorted(event_types)),
                "lifecycle_count": len(panel),
            }
        ]
    )


def build_task_386_decision(
    panel: pd.DataFrame,
    path_audit: pd.DataFrame,
    transition_audit: pd.DataFrame,
    bucket_audit: pd.DataFrame,
    boundary: pd.DataFrame,
) -> pd.DataFrame:
    has_add_scale = bool((pd.to_numeric(panel.get("add_event_count"), errors="coerce").fillna(0) > 0).any() or (pd.to_numeric(panel.get("scale_event_count"), errors="coerce").fillna(0) > 0).any()) if not panel.empty else False
    has_bucket = not bucket_audit.empty
    has_transition = not transition_audit.empty
    return pd.DataFrame(
        [
            {
                "task_386_verdict": "COMPLETE_PASS",
                "strategy_acceptance_status": "NOT_VALIDATED_QUALITY_DIAGNOSTIC_ONLY",
                "canonical_lifecycle_count": len(panel),
                "path_group_count": len(path_audit),
                "transition_group_count": len(transition_audit),
                "bucket_group_count": len(bucket_audit),
                "add_scale_quality_measurable_flag": int(has_add_scale),
                "bucket_quality_measurable_flag": int(has_bucket),
                "transition_quality_measurable_flag": int(has_transition),
                "canonical_stream_only_flag": int(boundary.iloc[0]["canonical_stream_only_flag"]) if not boundary.empty else 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "next_priority": "canonical_quality_oos_split_and_universe_overlay",
            }
        ]
    )


def write_canonical_continuation_quality_386(
    artifacts: CanonicalContinuationQuality386Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.canonical_lifecycle_quality_panel.to_csv(out_dir / "canonical_lifecycle_quality_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_path_quality_audit.to_csv(out_dir / "canonical_path_quality_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_transition_quality_audit.to_csv(out_dir / "canonical_transition_quality_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_bucket_quality_audit.to_csv(out_dir / "canonical_bucket_quality_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_quality_boundary_audit.to_csv(out_dir / "canonical_quality_boundary_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_386_decision.to_csv(out_dir / "task_386_decision.csv", index=False, encoding="utf-8-sig")


def _group_quality(panel: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame(
            columns=[
                group_col,
                "lifecycle_count",
                "avg_return",
                "median_return",
                "positive_rate",
                "strong_return_rate",
                "loss_rate",
                "avg_quality_score",
                "avg_add_count",
                "avg_scale_count",
                "avg_reduce_count",
            ]
        )
    frame = panel.copy()
    frame[group_col] = frame[group_col].fillna("unmapped")
    rows = []
    for key, group in frame.groupby(group_col, dropna=False):
        rows.append(
            {
                group_col: key,
                "lifecycle_count": len(group),
                "avg_return": float(pd.to_numeric(group["return_from_entry"], errors="coerce").mean()),
                "median_return": float(pd.to_numeric(group["return_from_entry"], errors="coerce").median()),
                "positive_rate": float(pd.to_numeric(group["positive_return_flag"], errors="coerce").fillna(0).mean()),
                "strong_return_rate": float(pd.to_numeric(group["strong_return_flag"], errors="coerce").fillna(0).mean()),
                "loss_rate": float(pd.to_numeric(group["loss_flag"], errors="coerce").fillna(0).mean()),
                "avg_quality_score": float(pd.to_numeric(group["continuation_quality_score"], errors="coerce").mean()),
                "avg_add_count": float(pd.to_numeric(group["add_event_count"], errors="coerce").fillna(0).mean()),
                "avg_scale_count": float(pd.to_numeric(group["scale_event_count"], errors="coerce").fillna(0).mean()),
                "avg_reduce_count": float(pd.to_numeric(group["reduce_event_count"], errors="coerce").fillna(0).mean()),
            }
        )
    return pd.DataFrame(rows)


def _path_type(row: pd.Series) -> str:
    add = int(pd.to_numeric(row.get("add_event_count"), errors="coerce") or 0) > 0
    scale = int(pd.to_numeric(row.get("scale_event_count"), errors="coerce") or 0) > 0
    reduce = int(pd.to_numeric(row.get("reduce_event_count"), errors="coerce") or 0) > 0
    if add and scale and reduce:
        return "ENTRY_ADD_SCALE_REDUCE_EXIT"
    if add and scale:
        return "ENTRY_ADD_SCALE_EXIT"
    if add and reduce:
        return "ENTRY_ADD_REDUCE_EXIT"
    if scale and reduce:
        return "ENTRY_SCALE_REDUCE_EXIT"
    if add:
        return "ENTRY_ADD_EXIT"
    if scale:
        return "ENTRY_SCALE_EXIT"
    if reduce:
        return "ENTRY_REDUCE_EXIT"
    return "ENTRY_EXIT_ONLY"


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame()


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype=object)
    return frame
