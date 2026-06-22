from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_381_timestamp_price_namespace_repair")
TASK_380_CANDIDATES_PATH = Path("docs/reports/task_380_identity_review_protocol/identity_review_protocol_candidates.csv")
TASK_380_NAMESPACE_FIX_PATH = Path("docs/reports/task_380_identity_review_protocol/namespace_fix_required_queue.csv")
TASK_380_MANUAL_PATH = Path("docs/reports/task_380_identity_review_protocol/manual_review_required_queue.csv")
TASK_374_CANDIDATES_PATH = Path("docs/reports/task_374_forward_pure_breakout/forward_pure_breakout_candidates.csv")
TASK_372_LIFECYCLE_PATH = Path("docs/reports/task_372_historical_source_backfill/task_372_lifecycle_backtest_panel.csv")


@dataclass(frozen=True)
class TimestampPriceNamespaceRepair381Artifacts:
    timestamp_price_repair_candidates: pd.DataFrame
    namespace_repair_ready_layer: pd.DataFrame
    manual_namespace_review_queue: pd.DataFrame
    namespace_repair_rejected: pd.DataFrame
    timestamp_repair_audit: pd.DataFrame
    price_anchor_repair_audit: pd.DataFrame
    namespace_repair_decision: pd.DataFrame


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def _safe_numeric(series: pd.Series | None, index: pd.Index, default: float = 0.0) -> pd.Series:
    if series is None:
        return pd.Series(default, index=index, dtype=float)
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = np.nan
    return out


def _trade_id_part(value: Any, index: int) -> str:
    parts = str(value).split("|")
    return parts[index] if len(parts) > index else ""


def _is_intraday_ts(value: Any) -> bool:
    stamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(stamp):
        return False
    return not (stamp.hour == 0 and stamp.minute == 0 and stamp.second == 0)


def _prepare_lifecycle_context(lifecycle: pd.DataFrame) -> pd.DataFrame:
    cols = ["raw_trade_id", "start_event_timestamp", "end_event_timestamp", "lineage_quality", "identity_confidence"]
    out = _ensure_columns(lifecycle, cols)[cols].copy()
    out["candidate_raw_trade_id"] = out["raw_trade_id"].astype(str)
    out["lifecycle_start_event_timestamp"] = pd.to_datetime(out["start_event_timestamp"], errors="coerce", utc=True)
    out["lifecycle_end_event_timestamp"] = pd.to_datetime(out["end_event_timestamp"], errors="coerce", utc=True)
    return out.drop(columns=["raw_trade_id", "start_event_timestamp", "end_event_timestamp"]).drop_duplicates("candidate_raw_trade_id", keep="first")


def _prepare_candidates(protocol: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    base = protocol.copy()
    for column in ("trade_id", "candidate_raw_trade_id", "candidate_lineage_quality"):
        if column not in base.columns:
            base[column] = ""
        base[column] = base[column].fillna("").astype(str)
    context = _prepare_lifecycle_context(lifecycle)
    out = base.merge(context, on="candidate_raw_trade_id", how="left", suffixes=("", "_lifecycle"))
    if "candidate_start_event_timestamp" in out.columns:
        out["entry_ts_repair_candidate"] = out["candidate_start_event_timestamp"]
    else:
        out["entry_ts_repair_candidate"] = out["lifecycle_start_event_timestamp"]
    out["entry_ts_repair_candidate"] = out["entry_ts_repair_candidate"].where(out["entry_ts_repair_candidate"].notna(), out["lifecycle_start_event_timestamp"])
    out["candidate_price_anchor"] = _safe_numeric(out.get("candidate_raw_entry_price"), out.index)
    if "entry_price" in out.columns:
        out["original_trade_price_anchor"] = _safe_numeric(out.get("entry_price"), out.index)
    else:
        out["original_trade_price_anchor"] = pd.to_numeric(out["trade_id"].map(lambda value: _trade_id_part(value, 3)), errors="coerce").fillna(0.0)
    out["price_abs_diff_repair"] = (out["original_trade_price_anchor"] - out["candidate_price_anchor"]).abs().round(6)
    out["price_rel_diff_repair"] = (out["price_abs_diff_repair"] / out["original_trade_price_anchor"].replace(0, np.nan)).fillna(0.0).round(6)
    return out


def _timestamp_status(row: pd.Series) -> pd.Series:
    candidate = row.get("entry_ts_repair_candidate")
    lineage = str(row.get("candidate_lineage_quality", ""))
    has_candidate = pd.notna(pd.to_datetime(candidate, errors="coerce", utc=True))
    intraday = _is_intraday_ts(candidate)
    if not str(row.get("candidate_raw_trade_id", "")).strip():
        status = "unrepairable_no_candidate"
        source = ""
        confidence = "none"
    elif has_candidate and intraday and lineage == "source_linked":
        status = "repair_candidate_source_linked_intraday_ts"
        source = "task372_lifecycle_start_event_timestamp"
        confidence = "high"
    elif has_candidate and intraday and lineage == "replay_derived":
        status = "repair_candidate_replay_derived_ts"
        source = "task372_lifecycle_start_event_timestamp"
        confidence = "low"
    elif has_candidate and intraday:
        status = "repair_candidate_session_derived_intraday_ts"
        source = "task372_lifecycle_start_event_timestamp"
        confidence = "medium"
    else:
        status = "unrepairable_no_candidate"
        source = ""
        confidence = "none"
    return pd.Series(
        {
            "timestamp_repair_status": status,
            "entry_ts_repair_source": source,
            "timestamp_repair_confidence": confidence,
        }
    )


def _price_status(row: pd.Series) -> pd.Series:
    rel = float(pd.to_numeric(pd.Series([row.get("price_rel_diff_repair")]), errors="coerce").fillna(0).iloc[0])
    if not str(row.get("candidate_raw_trade_id", "")).strip():
        cls = "unrepairable_no_candidate"
        confidence = "none"
    elif rel <= 0.02:
        cls = "price_anchor_minor_mismatch"
        confidence = "high"
    elif rel <= 0.05:
        cls = "price_anchor_material_mismatch"
        confidence = "medium"
    else:
        cls = "price_anchor_material_mismatch"
        confidence = "low"
    return pd.Series({"price_anchor_repair_class": cls, "price_anchor_repair_confidence": confidence})


def _repair_decision(row: pd.Series) -> pd.Series:
    ts_status = str(row.get("timestamp_repair_status", ""))
    price_class = str(row.get("price_anchor_repair_class", ""))
    lineage = str(row.get("candidate_lineage_quality", ""))
    tier = str(row.get("recovery_match_tier", ""))
    if not str(row.get("candidate_raw_trade_id", "")).strip() or ts_status == "unrepairable_no_candidate":
        decision = "insufficient_repair_evidence"
        reason = "missing_timestamp_or_candidate_raw_id"
    elif lineage == "source_linked" and ts_status == "repair_candidate_source_linked_intraday_ts" and price_class == "price_anchor_minor_mismatch" and tier == "exact_trade_id_match":
        decision = "namespace_repair_ready_candidate"
        reason = "exact_identity_source_linked_intraday_ts_minor_price_mismatch"
    elif lineage == "source_linked" and tier in {"symbol_session_single_match", "symbol_session_multi_match"}:
        decision = "manual_namespace_review_required"
        reason = "symbol_session_match_is_not_exact_identity"
    elif lineage == "replay_derived":
        decision = "manual_namespace_review_required"
        reason = "replay_derived_requires_source_linked_confirmation"
    elif price_class == "price_anchor_material_mismatch":
        decision = "manual_namespace_review_required"
        reason = "material_price_anchor_mismatch"
    else:
        decision = "manual_namespace_review_required"
        reason = "requires_namespace_review"
    return pd.Series(
        {
            "namespace_repair_decision_v1": decision,
            "namespace_repair_reason_v1": reason,
            "namespace_repair_ready_flag": int(decision == "namespace_repair_ready_candidate"),
            "accepted_label_update_flag": 0,
            "diagnostic_only_flag": 1,
        }
    )


def _build_repair_candidates(protocol: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    frame = _prepare_candidates(protocol, lifecycle)
    timestamp = frame.apply(_timestamp_status, axis=1)
    price = frame.apply(_price_status, axis=1)
    out = pd.concat([frame, timestamp, price], axis=1)
    decisions = out.apply(_repair_decision, axis=1)
    out = pd.concat([out.drop(columns=[c for c in decisions.columns if c in out.columns], errors="ignore"), decisions], axis=1)
    return out.sort_values(
        ["namespace_repair_ready_flag", "identity_confidence_score_v1", "recovery_priority_score", "trade_id"],
        ascending=[False, False, False, True],
        kind="stable",
    ).reset_index(drop=True)


def _timestamp_repair_audit(repair: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for status, scoped in repair.groupby("timestamp_repair_status", dropna=False, sort=False):
        rows.append(
            {
                "timestamp_repair_status": str(status),
                "row_count": int(len(scoped)),
                "source_linked_count": int(scoped["candidate_lineage_quality"].astype(str).eq("source_linked").sum()) if "candidate_lineage_quality" in scoped.columns else 0,
                "replay_derived_count": int(scoped["candidate_lineage_quality"].astype(str).eq("replay_derived").sum()) if "candidate_lineage_quality" in scoped.columns else 0,
                "repair_ready_count": int(_safe_numeric(scoped.get("namespace_repair_ready_flag"), scoped.index).sum()),
            }
        )
    return pd.DataFrame(rows)


def _price_anchor_repair_audit(repair: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for cls, scoped in repair.groupby("price_anchor_repair_class", dropna=False, sort=False):
        rows.append(
            {
                "price_anchor_repair_class": str(cls),
                "row_count": int(len(scoped)),
                "avg_price_rel_diff": round(float(_safe_numeric(scoped.get("price_rel_diff_repair"), scoped.index).mean()), 6) if not scoped.empty else 0.0,
                "max_price_rel_diff": round(float(_safe_numeric(scoped.get("price_rel_diff_repair"), scoped.index).max()), 6) if not scoped.empty else 0.0,
                "repair_ready_count": int(_safe_numeric(scoped.get("namespace_repair_ready_flag"), scoped.index).sum()),
            }
        )
    return pd.DataFrame(rows)


def _decision(repair: pd.DataFrame) -> pd.DataFrame:
    ready = int(_safe_numeric(repair.get("namespace_repair_ready_flag"), repair.index).sum()) if not repair.empty else 0
    label_updates = int(_safe_numeric(repair.get("accepted_label_update_flag"), repair.index).sum()) if not repair.empty else 0
    date_only = int(_safe_numeric(repair.get("date_only_timestamp_namespace_flag"), repair.index).sum()) if "date_only_timestamp_namespace_flag" in repair.columns else 0
    intraday_candidates = int(repair["timestamp_repair_status"].astype(str).isin({"repair_candidate_source_linked_intraday_ts", "repair_candidate_replay_derived_ts", "repair_candidate_session_derived_intraday_ts"}).sum()) if not repair.empty else 0
    minor = int(repair["price_anchor_repair_class"].astype(str).eq("price_anchor_minor_mismatch").sum()) if not repair.empty else 0
    material = int(repair["price_anchor_repair_class"].astype(str).eq("price_anchor_material_mismatch").sum()) if not repair.empty else 0
    return pd.DataFrame(
        [
            {
                "task_381_verdict": "COMPLETE_PASS" if not repair.empty and label_updates == 0 else "NOT_YET",
                "strategy_acceptance_status": "UNCHANGED_EXPANDED_SAMPLE_REQUIRED",
                "persistence_revalidation_ready": "YES_DIAGNOSTIC_LAYER_ONLY" if ready > 0 else "NO",
                "total_rows": int(len(repair)),
                "date_only_timestamp_rows": date_only,
                "intraday_timestamp_repair_candidate_rows": intraday_candidates,
                "price_anchor_minor_mismatch_rows": minor,
                "price_anchor_material_mismatch_rows": material,
                "namespace_repair_ready_rows": ready,
                "manual_namespace_review_rows": int(repair["namespace_repair_decision_v1"].astype(str).eq("manual_namespace_review_required").sum()) if not repair.empty else 0,
                "namespace_repair_rejected_rows": int(repair["namespace_repair_decision_v1"].astype(str).eq("namespace_repair_rejected").sum()) if not repair.empty else 0,
                "insufficient_repair_evidence_rows": int(repair["namespace_repair_decision_v1"].astype(str).eq("insufficient_repair_evidence").sum()) if not repair.empty else 0,
                "accepted_label_update_rows": label_updates,
                "labels_overwritten": "NO",
                "task_376_ontology_relaxed": "NO",
                "theme_promoted_by_task_381": "NO",
            }
        ]
    )


def build_timestamp_price_namespace_repair_381(
    *,
    protocol_candidates_df: pd.DataFrame | None = None,
    namespace_fix_df: pd.DataFrame | None = None,
    manual_review_df: pd.DataFrame | None = None,
    task374_candidates_df: pd.DataFrame | None = None,
    lifecycle_df: pd.DataFrame | None = None,
) -> TimestampPriceNamespaceRepair381Artifacts:
    protocol = protocol_candidates_df.copy() if protocol_candidates_df is not None else _load_csv(TASK_380_CANDIDATES_PATH)
    if namespace_fix_df is None and TASK_380_NAMESPACE_FIX_PATH.exists():
        _load_csv(TASK_380_NAMESPACE_FIX_PATH)
    if manual_review_df is None and TASK_380_MANUAL_PATH.exists():
        _load_csv(TASK_380_MANUAL_PATH)
    if task374_candidates_df is None and TASK_374_CANDIDATES_PATH.exists():
        _load_csv(TASK_374_CANDIDATES_PATH)
    lifecycle = lifecycle_df.copy() if lifecycle_df is not None else _load_csv(TASK_372_LIFECYCLE_PATH)

    repair = _build_repair_candidates(protocol, lifecycle)
    ready = repair[repair["namespace_repair_decision_v1"].astype(str).eq("namespace_repair_ready_candidate")].copy().reset_index(drop=True)
    manual = repair[repair["namespace_repair_decision_v1"].astype(str).eq("manual_namespace_review_required")].copy().reset_index(drop=True)
    rejected = repair[repair["namespace_repair_decision_v1"].astype(str).isin({"namespace_repair_rejected", "insufficient_repair_evidence"})].copy().reset_index(drop=True)
    ts_audit = _timestamp_repair_audit(repair)
    price_audit = _price_anchor_repair_audit(repair)
    decision = _decision(repair)
    return TimestampPriceNamespaceRepair381Artifacts(
        timestamp_price_repair_candidates=repair,
        namespace_repair_ready_layer=ready,
        manual_namespace_review_queue=manual,
        namespace_repair_rejected=rejected,
        timestamp_repair_audit=ts_audit,
        price_anchor_repair_audit=price_audit,
        namespace_repair_decision=decision,
    )


def write_timestamp_price_namespace_repair_381(
    artifacts: TimestampPriceNamespaceRepair381Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.timestamp_price_repair_candidates.to_csv(out_dir / "timestamp_price_repair_candidates.csv", index=False, encoding="utf-8-sig")
    artifacts.namespace_repair_ready_layer.to_csv(out_dir / "namespace_repair_ready_layer.csv", index=False, encoding="utf-8-sig")
    artifacts.manual_namespace_review_queue.to_csv(out_dir / "manual_namespace_review_queue.csv", index=False, encoding="utf-8-sig")
    artifacts.namespace_repair_rejected.to_csv(out_dir / "namespace_repair_rejected.csv", index=False, encoding="utf-8-sig")
    artifacts.timestamp_repair_audit.to_csv(out_dir / "timestamp_repair_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.price_anchor_repair_audit.to_csv(out_dir / "price_anchor_repair_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.namespace_repair_decision.to_csv(out_dir / "namespace_repair_decision.csv", index=False, encoding="utf-8-sig")
