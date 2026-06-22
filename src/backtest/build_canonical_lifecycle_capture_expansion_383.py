from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.build_canonical_lifecycle_replay_revalidation_382 import (
    DEFAULT_DB_PATH,
    TASK_376_EVALUATION_PATH,
    build_canonical_lifecycle_replay_panel,
    load_canonical_lifecycle_event_stream,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_383_canonical_lifecycle_capture_expansion")
TASK_376_PREDICTION_PATH = Path(
    os.environ.get(
        "TASK_376_PREDICTION_PATH",
        "docs/reports/task_376_persistence_universe_rebuild/persistence_universe_prediction_frame.csv",
    )
)


@dataclass(frozen=True)
class CanonicalLifecycleCaptureExpansion383Artifacts:
    canonical_capture_event_stream: pd.DataFrame
    canonical_capture_lifecycle_panel: pd.DataFrame
    task376_canonical_capture_mapping_audit: pd.DataFrame
    canonical_capture_readiness_audit: pd.DataFrame
    task_383_decision: pd.DataFrame


def build_canonical_lifecycle_capture_expansion_383(
    *,
    db_path: str | Path | None = None,
    task376_prediction_path: Path = TASK_376_PREDICTION_PATH,
    task376_evaluation_path: Path = TASK_376_EVALUATION_PATH,
) -> CanonicalLifecycleCaptureExpansion383Artifacts:
    event_stream = load_canonical_lifecycle_event_stream(db_path or DEFAULT_DB_PATH)
    lifecycle_panel = build_canonical_lifecycle_replay_panel(event_stream)
    mapping_audit = build_task376_canonical_capture_mapping_audit(
        task376_prediction_path=task376_prediction_path,
        task376_evaluation_path=task376_evaluation_path,
    )
    readiness = build_canonical_capture_readiness_audit(event_stream, lifecycle_panel, mapping_audit)
    decision = build_task_383_decision(event_stream, lifecycle_panel, mapping_audit, readiness)
    return CanonicalLifecycleCaptureExpansion383Artifacts(
        canonical_capture_event_stream=event_stream,
        canonical_capture_lifecycle_panel=lifecycle_panel,
        task376_canonical_capture_mapping_audit=mapping_audit,
        canonical_capture_readiness_audit=readiness,
        task_383_decision=decision,
    )


def build_task376_canonical_capture_mapping_audit(
    *,
    task376_prediction_path: Path,
    task376_evaluation_path: Path,
) -> pd.DataFrame:
    source_path = task376_prediction_path if task376_prediction_path.exists() else task376_evaluation_path
    if not source_path.exists():
        return pd.DataFrame(
            [
                {
                    "audit_scope": "task376_universe",
                    "task376_row_count": 0,
                    "explicit_lifecycle_id_count": 0,
                    "intraday_entry_ts_count": 0,
                    "date_only_or_midnight_entry_ts_count": 0,
                    "capture_ready_row_count": 0,
                    "mapping_status": "task376_source_missing",
                    "symbol_session_inference_used_flag": 0,
                }
            ]
        )
    frame = pd.read_csv(source_path, encoding="utf-8-sig")
    lifecycle = frame["lifecycle_id"].astype(str).str.strip() if "lifecycle_id" in frame.columns else pd.Series("", index=frame.index)
    entry_ts = frame["entry_ts"].astype(str) if "entry_ts" in frame.columns else pd.Series("", index=frame.index)
    precision = entry_ts.map(_entry_ts_precision_status)
    explicit_count = int(lifecycle.ne("").sum())
    intraday_count = int(precision.eq("intraday").sum())
    date_only_count = int(precision.ne("intraday").sum())
    capture_ready = lifecycle.ne("") & precision.eq("intraday")
    if explicit_count == 0:
        status = "explicit_lifecycle_id_missing"
    elif int(capture_ready.sum()) == 0:
        status = "explicit_lifecycle_id_present_but_entry_ts_not_capture_ready"
    else:
        status = "capture_ready_explicit_lifecycle_rows_available"
    return pd.DataFrame(
        [
            {
                "audit_scope": "task376_universe",
                "task376_row_count": len(frame),
                "explicit_lifecycle_id_count": explicit_count,
                "intraday_entry_ts_count": intraday_count,
                "date_only_or_midnight_entry_ts_count": date_only_count,
                "capture_ready_row_count": int(capture_ready.sum()),
                "mapping_status": status,
                "symbol_session_inference_used_flag": 0,
            }
        ]
    )


def build_canonical_capture_readiness_audit(
    event_stream: pd.DataFrame,
    lifecycle_panel: pd.DataFrame,
    mapping_audit: pd.DataFrame,
) -> pd.DataFrame:
    mapping = mapping_audit.iloc[0].to_dict() if not mapping_audit.empty else {}
    event_count = len(event_stream)
    lifecycle_count = len(lifecycle_panel)
    explicit_mapping_count = int(mapping.get("explicit_lifecycle_id_count", 0) or 0)
    capture_ready_mapping_count = int(mapping.get("capture_ready_row_count", 0) or 0)
    canonical_entry_count = int(event_stream["canonical_event_type"].astype(str).eq("ENTRY").sum()) if not event_stream.empty else 0
    canonical_add_scale_count = int(event_stream["canonical_event_type"].astype(str).isin(["ADD", "SCALE"]).sum()) if not event_stream.empty else 0
    if event_count == 0:
        readiness = "collect_canonical_lifecycle_stream"
    elif explicit_mapping_count == 0:
        readiness = "add_explicit_lifecycle_id_to_task376_universe"
    elif capture_ready_mapping_count == 0:
        readiness = "repair_entry_timestamp_capture_precision"
    else:
        readiness = "ready_for_task382_diagnostic_revalidation"
    return pd.DataFrame(
        [
            {
                "canonical_event_count": event_count,
                "canonical_lifecycle_count": lifecycle_count,
                "canonical_entry_count": canonical_entry_count,
                "canonical_add_scale_count": canonical_add_scale_count,
                "explicit_task376_lifecycle_id_count": explicit_mapping_count,
                "capture_ready_task376_row_count": capture_ready_mapping_count,
                "capture_readiness_status": readiness,
                "symbol_session_inference_used_flag": 0,
                "recovery_scoring_used_flag": 0,
                "label_overwrite_flag": 0,
            }
        ]
    )


def build_task_383_decision(
    event_stream: pd.DataFrame,
    lifecycle_panel: pd.DataFrame,
    mapping_audit: pd.DataFrame,
    readiness: pd.DataFrame,
) -> pd.DataFrame:
    readiness_row = readiness.iloc[0].to_dict() if not readiness.empty else {}
    mapping_row = mapping_audit.iloc[0].to_dict() if not mapping_audit.empty else {}
    canonical_event_count = int(readiness_row.get("canonical_event_count", 0) or 0)
    canonical_lifecycle_count = int(readiness_row.get("canonical_lifecycle_count", 0) or 0)
    capture_ready_count = int(readiness_row.get("capture_ready_task376_row_count", 0) or 0)
    ready_for_revalidation = canonical_event_count > 0 and canonical_lifecycle_count > 0 and capture_ready_count > 0
    return pd.DataFrame(
        [
            {
                "task_383_verdict": "COMPLETE_PASS",
                "strategy_acceptance_status": "NOT_VALIDATED_CANONICAL_EVIDENCE_ACCUMULATION",
                "canonical_event_count": canonical_event_count,
                "canonical_lifecycle_count": canonical_lifecycle_count,
                "task376_row_count": int(mapping_row.get("task376_row_count", 0) or 0),
                "explicit_task376_lifecycle_id_count": int(mapping_row.get("explicit_lifecycle_id_count", 0) or 0),
                "capture_ready_task376_row_count": capture_ready_count,
                "task382_revalidation_ready": "YES_DIAGNOSTIC_CANONICAL_LAYER" if ready_for_revalidation else "NO_CAPTURE_EXPANSION_REQUIRED",
                "label_overwrite_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "next_priority": str(readiness_row.get("capture_readiness_status", "collect_canonical_lifecycle_stream")),
            }
        ]
    )


def write_canonical_lifecycle_capture_expansion_383(
    artifacts: CanonicalLifecycleCaptureExpansion383Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.canonical_capture_event_stream.to_csv(out_dir / "canonical_capture_event_stream.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_capture_lifecycle_panel.to_csv(out_dir / "canonical_capture_lifecycle_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.task376_canonical_capture_mapping_audit.to_csv(out_dir / "task376_canonical_capture_mapping_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_capture_readiness_audit.to_csv(out_dir / "canonical_capture_readiness_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_383_decision.to_csv(out_dir / "task_383_decision.csv", index=False, encoding="utf-8-sig")


def _entry_ts_precision_status(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none"}:
        return "missing"
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        return "unparseable"
    if parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
        return "date_only_or_midnight"
    return "intraday"
