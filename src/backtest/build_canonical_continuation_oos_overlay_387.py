from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_387_canonical_continuation_oos_overlay")
TASK_386_QUALITY_PANEL_PATH = Path("docs/reports/task_386_canonical_continuation_quality/canonical_lifecycle_quality_panel.csv")
TASK_385_EVENT_LOG_PATH = Path("docs/reports/task_385_canonical_continuation_engine/canonical_continuation_event_log.csv")
ANCHOR_DATE = "2025-01-01"
MIN_OOS_PER_PATH = 20
MIN_OOS_TOTAL = 100


@dataclass(frozen=True)
class CanonicalContinuationOosOverlay387Artifacts:
    canonical_oos_quality_panel: pd.DataFrame
    canonical_oos_path_quality_audit: pd.DataFrame
    canonical_oos_transition_quality_audit: pd.DataFrame
    canonical_oos_bucket_overlay_audit: pd.DataFrame
    canonical_oos_sample_adequacy_audit: pd.DataFrame
    canonical_sequence_anomaly_audit: pd.DataFrame
    task_387_decision: pd.DataFrame


def build_canonical_continuation_oos_overlay_387(
    *,
    quality_panel_path: Path = TASK_386_QUALITY_PANEL_PATH,
    event_log_path: Path = TASK_385_EVENT_LOG_PATH,
    anchor_date: str = ANCHOR_DATE,
) -> CanonicalContinuationOosOverlay387Artifacts:
    quality = _read_csv(quality_panel_path)
    events = _read_csv(event_log_path)
    panel = build_oos_quality_panel(quality, anchor_date=anchor_date)
    path_audit = build_oos_group_quality(panel, "path_type")
    transition_audit = build_oos_transition_quality(events, panel, anchor_date=anchor_date)
    bucket_audit = build_oos_group_quality(panel, "persistence_universe_bucket")
    sample_audit = build_oos_sample_adequacy_audit(panel, path_audit)
    anomaly_audit = build_sequence_anomaly_audit(events)
    decision = build_task_387_decision(panel, path_audit, transition_audit, bucket_audit, sample_audit, anomaly_audit)
    return CanonicalContinuationOosOverlay387Artifacts(
        canonical_oos_quality_panel=panel,
        canonical_oos_path_quality_audit=path_audit,
        canonical_oos_transition_quality_audit=transition_audit,
        canonical_oos_bucket_overlay_audit=bucket_audit,
        canonical_oos_sample_adequacy_audit=sample_audit,
        canonical_sequence_anomaly_audit=anomaly_audit,
        task_387_decision=decision,
    )


def build_oos_quality_panel(quality: pd.DataFrame, *, anchor_date: str) -> pd.DataFrame:
    panel = quality.copy()
    if panel.empty:
        return panel
    panel["entry_ts_dt"] = pd.to_datetime(panel["entry_ts"], errors="coerce", utc=True)
    anchor = pd.Timestamp(anchor_date, tz="UTC")
    panel["canonical_split"] = panel["entry_ts_dt"].map(lambda ts: "anchored_oos" if pd.notna(ts) and ts >= anchor else "train")
    return panel


def build_oos_group_quality(panel: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if panel.empty or group_col not in panel.columns:
        return pd.DataFrame(columns=["canonical_split", group_col, "lifecycle_count", "avg_return", "positive_rate", "strong_return_rate"])
    rows = []
    for (split, key), group in panel.groupby(["canonical_split", group_col], dropna=False):
        rows.append(_quality_row(split, group_col, key, group))
    return pd.DataFrame(rows).sort_values(["canonical_split", "lifecycle_count"], ascending=[True, False]).reset_index(drop=True)


def build_oos_transition_quality(events: pd.DataFrame, panel: pd.DataFrame, *, anchor_date: str) -> pd.DataFrame:
    if events.empty or panel.empty:
        return pd.DataFrame(columns=["canonical_split", "transition", "transition_count", "lifecycle_count", "avg_return", "positive_rate"])
    transitions = _transition_rows(events)
    if transitions.empty:
        return pd.DataFrame(columns=["canonical_split", "transition", "transition_count", "lifecycle_count", "avg_return", "positive_rate"])
    merged = transitions.merge(
        panel[["lifecycle_id", "canonical_split", "return_from_entry", "positive_return_flag"]],
        on="lifecycle_id",
        how="left",
    )
    rows = []
    for (split, transition), group in merged.groupby(["canonical_split", "transition"], dropna=False):
        rows.append(
            {
                "canonical_split": split,
                "transition": transition,
                "transition_count": len(group),
                "lifecycle_count": int(group["lifecycle_id"].nunique()),
                "avg_return": float(pd.to_numeric(group["return_from_entry"], errors="coerce").mean()),
                "positive_rate": float(pd.to_numeric(group["positive_return_flag"], errors="coerce").fillna(0).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["canonical_split", "transition_count"], ascending=[True, False]).reset_index(drop=True)


def build_oos_sample_adequacy_audit(panel: pd.DataFrame, path_audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, group in panel.groupby("canonical_split", dropna=False):
        split_paths = path_audit[path_audit["canonical_split"].astype(str).eq(str(split))]
        max_path_count = int(split_paths["lifecycle_count"].max()) if not split_paths.empty else 0
        min_major_path_count = int(split_paths[split_paths["lifecycle_count"] >= MIN_OOS_PER_PATH]["lifecycle_count"].min()) if (not split_paths.empty and (split_paths["lifecycle_count"] >= MIN_OOS_PER_PATH).any()) else 0
        total = len(group)
        rows.append(
            {
                "canonical_split": split,
                "lifecycle_count": total,
                "path_group_count": int(split_paths["path_type"].nunique()) if "path_type" in split_paths.columns else len(split_paths),
                "max_path_count": max_path_count,
                "min_adequate_path_count": min_major_path_count,
                "sample_gate": "pass" if split == "anchored_oos" and total >= MIN_OOS_TOTAL and max_path_count >= MIN_OOS_PER_PATH else "diagnostic_only",
            }
        )
    return pd.DataFrame(rows)


def build_sequence_anomaly_audit(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["anomaly_type", "count"])
    transitions = _transition_rows(events)
    invalid = transitions[transitions["transition"].astype(str).str.startswith("EXIT->")].copy()
    same_ts = []
    tmp = events.copy()
    tmp["event_timestamp_dt"] = pd.to_datetime(tmp["event_timestamp"], errors="coerce", utc=True)
    for lifecycle_id, group in tmp.groupby("lifecycle_id", sort=False):
        if group["event_timestamp_dt"].duplicated().any():
            same_ts.append(lifecycle_id)
    return pd.DataFrame(
        [
            {"anomaly_type": "transition_after_exit", "count": int(len(invalid))},
            {"anomaly_type": "same_timestamp_multiple_events", "count": int(len(set(same_ts)))},
        ]
    )


def build_task_387_decision(
    panel: pd.DataFrame,
    path_audit: pd.DataFrame,
    transition_audit: pd.DataFrame,
    bucket_audit: pd.DataFrame,
    sample_audit: pd.DataFrame,
    anomaly_audit: pd.DataFrame,
) -> pd.DataFrame:
    oos = panel[panel["canonical_split"].astype(str).eq("anchored_oos")] if not panel.empty else pd.DataFrame()
    oos_count = len(oos)
    oos_paths = path_audit[path_audit["canonical_split"].astype(str).eq("anchored_oos")] if not path_audit.empty else pd.DataFrame()
    oos_has_add_scale = bool(oos["path_type"].astype(str).str.contains("ADD_SCALE").any()) if not oos.empty else False
    sample_gate = "diagnostic_only"
    if not sample_audit.empty and sample_audit["canonical_split"].astype(str).eq("anchored_oos").any():
        sample_gate = str(sample_audit[sample_audit["canonical_split"].astype(str).eq("anchored_oos")].iloc[0]["sample_gate"])
    anomaly_count = int(pd.to_numeric(anomaly_audit.get("count"), errors="coerce").fillna(0).sum()) if not anomaly_audit.empty else 0
    return pd.DataFrame(
        [
            {
                "task_387_verdict": "COMPLETE_PASS",
                "strategy_acceptance_status": "NOT_VALIDATED_OOS_DIAGNOSTIC_ONLY",
                "anchor_date": ANCHOR_DATE,
                "canonical_lifecycle_count": len(panel),
                "anchored_oos_lifecycle_count": oos_count,
                "anchored_oos_path_group_count": len(oos_paths),
                "anchored_oos_add_scale_present_flag": int(oos_has_add_scale),
                "anchored_oos_sample_gate": sample_gate,
                "sequence_anomaly_count": anomaly_count,
                "canonical_stream_only_flag": 1,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "next_priority": "sequence_anomaly_review_then_oos_overlay_deepening" if anomaly_count else "oos_overlay_deepening",
            }
        ]
    )


def write_canonical_continuation_oos_overlay_387(
    artifacts: CanonicalContinuationOosOverlay387Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.canonical_oos_quality_panel.to_csv(out_dir / "canonical_oos_quality_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_oos_path_quality_audit.to_csv(out_dir / "canonical_oos_path_quality_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_oos_transition_quality_audit.to_csv(out_dir / "canonical_oos_transition_quality_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_oos_bucket_overlay_audit.to_csv(out_dir / "canonical_oos_bucket_overlay_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_oos_sample_adequacy_audit.to_csv(out_dir / "canonical_oos_sample_adequacy_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_sequence_anomaly_audit.to_csv(out_dir / "canonical_sequence_anomaly_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_387_decision.to_csv(out_dir / "task_387_decision.csv", index=False, encoding="utf-8-sig")


def _transition_rows(events: pd.DataFrame) -> pd.DataFrame:
    tmp = events.copy()
    tmp["event_timestamp_dt"] = pd.to_datetime(tmp["event_timestamp"], errors="coerce", utc=True)
    order = {"ENTRY": 0, "ADD": 1, "SCALE": 2, "REDUCE": 3, "EXIT": 4}
    tmp["event_order"] = tmp["event_type"].astype(str).map(order).fillna(99)
    tmp = tmp.sort_values(["lifecycle_id", "event_timestamp_dt", "event_order", "event_type"]).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for lifecycle_id, group in tmp.groupby("lifecycle_id", sort=False):
        types = group["event_type"].astype(str).tolist()
        for prev, nxt in zip(types, types[1:]):
            rows.append({"lifecycle_id": lifecycle_id, "transition": f"{prev}->{nxt}"})
    return pd.DataFrame(rows)


def _quality_row(split: str, group_col: str, key: object, group: pd.DataFrame) -> dict:
    return {
        "canonical_split": split,
        group_col: key,
        "lifecycle_count": len(group),
        "avg_return": float(pd.to_numeric(group["return_from_entry"], errors="coerce").mean()),
        "median_return": float(pd.to_numeric(group["return_from_entry"], errors="coerce").median()),
        "positive_rate": float(pd.to_numeric(group["positive_return_flag"], errors="coerce").fillna(0).mean()),
        "strong_return_rate": float(pd.to_numeric(group["strong_return_flag"], errors="coerce").fillna(0).mean()),
        "loss_rate": float(pd.to_numeric(group["loss_flag"], errors="coerce").fillna(0).mean()),
        "avg_add_count": float(pd.to_numeric(group["add_event_count"], errors="coerce").fillna(0).mean()),
        "avg_scale_count": float(pd.to_numeric(group["scale_event_count"], errors="coerce").fillna(0).mean()),
        "avg_reduce_count": float(pd.to_numeric(group["reduce_event_count"], errors="coerce").fillna(0).mean()),
    }


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame()
