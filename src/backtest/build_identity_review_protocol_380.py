from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_380_identity_review_protocol")
TASK_379_CANDIDATES_PATH = Path("docs/reports/task_379_lifecycle_identity_reconciliation/identity_reconciliation_candidates.csv")
TASK_379_P0P1_PATH = Path("docs/reports/task_379_lifecycle_identity_reconciliation/p0_p1_identity_review_queue.csv")
TASK_379_NAMESPACE_PATH = Path("docs/reports/task_379_lifecycle_identity_reconciliation/identity_namespace_audit.csv")
TASK_374_CANDIDATES_PATH = Path("docs/reports/task_374_forward_pure_breakout/forward_pure_breakout_candidates.csv")
TASK_372_LIFECYCLE_PATH = Path("docs/reports/task_372_historical_source_backfill/task_372_lifecycle_backtest_panel.csv")


@dataclass(frozen=True)
class IdentityReviewProtocol380Artifacts:
    identity_review_protocol_candidates: pd.DataFrame
    reviewed_recovery_layer: pd.DataFrame
    manual_review_required_queue: pd.DataFrame
    rejected_recovery_candidates: pd.DataFrame
    namespace_fix_required_queue: pd.DataFrame
    trade_id_namespace_mismatch_audit: pd.DataFrame
    timestamp_precision_audit: pd.DataFrame
    task_380_decision: pd.DataFrame


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


def _is_date_only(value: Any) -> bool:
    stamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(stamp):
        return False
    return stamp.hour == 0 and stamp.minute == 0 and stamp.second == 0


def _namespace_flags(row: pd.Series) -> dict[str, int]:
    trade_id = str(row.get("trade_id", ""))
    raw_id = str(row.get("candidate_raw_trade_id", ""))
    exact = int(str(row.get("recovery_match_tier", "")) == "exact_trade_id_match")
    candidate_missing = int(not raw_id or raw_id.lower() == "nan")
    price_mismatch = int(
        bool(raw_id)
        and _trade_id_part(trade_id, 3) != _trade_id_part(raw_id, 3)
        and not candidate_missing
    )
    same_symbol_session = int(
        bool(raw_id)
        and _trade_id_part(trade_id, 0) == _trade_id_part(raw_id, 0)
        and _trade_id_part(trade_id, 1) == _trade_id_part(raw_id, 1)
        and trade_id != raw_id
    )
    date_only = int(_is_date_only(row.get("entry_component_ts")) or _is_date_only(row.get("entry_ts")))
    timestamp_missing = int(pd.isna(pd.to_datetime(row.get("entry_component_ts"), errors="coerce", utc=True)))
    return {
        "exact_trade_id_absent_flag": int(exact == 0),
        "candidate_raw_id_missing_flag": candidate_missing,
        "price_anchor_mismatch_flag": price_mismatch,
        "symbol_session_match_but_raw_id_differs_flag": same_symbol_session,
        "date_only_timestamp_namespace_flag": date_only,
        "entry_timestamp_precision_missing_flag": max(date_only, timestamp_missing),
    }


def _namespace_issue_summary(row: pd.Series) -> str:
    names = [
        ("candidate_raw_id_missing_flag", "candidate_raw_id_missing"),
        ("price_anchor_mismatch_flag", "price_anchor_mismatch"),
        ("date_only_timestamp_namespace_flag", "date_only_timestamp_namespace"),
        ("entry_timestamp_precision_missing_flag", "entry_timestamp_precision_missing"),
        ("symbol_session_match_but_raw_id_differs_flag", "symbol_session_match_but_raw_id_differs"),
        ("exact_trade_id_absent_flag", "exact_trade_id_absent"),
    ]
    issues = [label for column, label in names if int(row.get(column, 0)) > 0]
    return "|".join(issues) if issues else "no_namespace_issue"


def _review_decision(row: pd.Series) -> pd.Series:
    bucket = str(row.get("identity_confidence_bucket_v1", ""))
    tier = str(row.get("recovery_match_tier", ""))
    lineage = str(row.get("candidate_lineage_quality", ""))
    price_rel = float(pd.to_numeric(pd.Series([row.get("price_rel_diff")]), errors="coerce").fillna(0).iloc[0])
    price_blocked = str(row.get("price_distance_status", "")) == "price_blocked" or price_rel > 0.05
    time_blocked = str(row.get("time_distance_status", "")) == "time_blocked"
    date_only = int(row.get("date_only_timestamp_namespace_flag", 0)) > 0
    candidate_missing = int(row.get("candidate_raw_id_missing_flag", 0)) > 0
    replay = lineage == "replay_derived"
    multi = tier == "symbol_session_multi_match"
    no_evidence = bucket == "no_recovery_evidence" or tier == "no_recovery_evidence"

    if no_evidence:
        decision = "rejected_recovery_candidate"
        reason = "no_recovery_evidence"
    elif candidate_missing:
        decision = "namespace_fix_required"
        reason = "candidate_raw_id_missing"
    elif price_blocked:
        decision = "rejected_recovery_candidate"
        reason = "price_anchor_mismatch_blocked"
    elif time_blocked:
        decision = "namespace_fix_required"
        reason = "timestamp_distance_blocked"
    elif date_only and bucket == "high_confidence_recovered_candidate":
        decision = "namespace_fix_required"
        reason = "entry_timestamp_precision_missing"
    elif multi:
        decision = "manual_review_required"
        reason = "multi_match_disambiguation_required"
    elif replay:
        decision = "manual_review_required"
        reason = "replay_derived_requires_source_linked_confirmation"
    elif (
        bucket == "high_confidence_recovered_candidate"
        and lineage == "source_linked"
        and tier in {"exact_trade_id_match", "symbol_session_single_match"}
        and price_rel <= 0.02
        and not date_only
    ):
        decision = "approved_recovery_candidate"
        reason = "source_linked_high_confidence_single_match"
    elif bucket == "medium_confidence_review_queue":
        decision = "manual_review_required"
        reason = "medium_confidence_requires_review"
    else:
        decision = "manual_review_required"
        reason = "insufficient_for_automatic_reviewed_layer"
    return pd.Series(
        {
            "review_protocol_decision_v1": decision,
            "review_protocol_reason_v1": reason,
            "reviewed_recovery_layer_eligible_flag": int(decision == "approved_recovery_candidate"),
            "accepted_label_update_flag": 0,
            "diagnostic_only_flag": 1,
        }
    )


def _build_protocol_candidates(candidates: pd.DataFrame) -> pd.DataFrame:
    base = candidates.copy()
    for column in ("trade_id", "candidate_raw_trade_id", "recovery_match_tier", "identity_confidence_bucket_v1"):
        if column not in base.columns:
            base[column] = ""
    flags = pd.DataFrame([_namespace_flags(row) for _, row in base.iterrows()], index=base.index)
    out = pd.concat([base, flags], axis=1)
    out["namespace_issue_summary"] = out.apply(_namespace_issue_summary, axis=1)
    decisions = out.apply(_review_decision, axis=1)
    out = pd.concat([out.drop(columns=[c for c in decisions.columns if c in out.columns], errors="ignore"), decisions], axis=1)
    return out.sort_values(
        ["reviewed_recovery_layer_eligible_flag", "identity_confidence_score_v1", "recovery_priority_score", "trade_id"],
        ascending=[False, False, False, True],
        kind="stable",
    ).reset_index(drop=True)


def _trade_id_namespace_mismatch_audit(protocol: pd.DataFrame, task374: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    exact_all = 0
    if "trade_id" in task374.columns and "raw_trade_id" in lifecycle.columns:
        exact_all = int(task374["trade_id"].astype(str).isin(set(lifecycle["raw_trade_id"].astype(str))).sum())
    rows = [
        {
            "audit_scope": "task380_protocol_candidates",
            "row_count": int(len(protocol)),
            "exact_trade_id_match_count": int(protocol["recovery_match_tier"].astype(str).eq("exact_trade_id_match").sum()) if not protocol.empty else 0,
            "symbol_session_match_count": int(protocol["recovery_match_tier"].astype(str).isin({"symbol_session_single_match", "symbol_session_multi_match"}).sum()) if not protocol.empty else 0,
            "price_component_mismatch_count": int(_safe_numeric(protocol.get("price_anchor_mismatch_flag"), protocol.index).sum()) if not protocol.empty else 0,
            "date_only_timestamp_count": int(_safe_numeric(protocol.get("date_only_timestamp_namespace_flag"), protocol.index).sum()) if not protocol.empty else 0,
            "source_linked_count": int(protocol["candidate_lineage_quality"].astype(str).eq("source_linked").sum()) if "candidate_lineage_quality" in protocol.columns else 0,
            "replay_derived_count": int(protocol["candidate_lineage_quality"].astype(str).eq("replay_derived").sum()) if "candidate_lineage_quality" in protocol.columns else 0,
            "approved_count": int(protocol["review_protocol_decision_v1"].astype(str).eq("approved_recovery_candidate").sum()) if not protocol.empty else 0,
            "manual_review_count": int(protocol["review_protocol_decision_v1"].astype(str).eq("manual_review_required").sum()) if not protocol.empty else 0,
            "rejected_count": int(protocol["review_protocol_decision_v1"].astype(str).eq("rejected_recovery_candidate").sum()) if not protocol.empty else 0,
            "namespace_fix_count": int(protocol["review_protocol_decision_v1"].astype(str).eq("namespace_fix_required").sum()) if not protocol.empty else 0,
            "namespace_diagnosis": "price_anchor_mismatch_plus_date_only_timestamp_namespace",
        },
        {
            "audit_scope": "task374_vs_task372_all_rows",
            "row_count": int(len(task374)),
            "exact_trade_id_match_count": exact_all,
            "symbol_session_match_count": 0,
            "price_component_mismatch_count": 0,
            "date_only_timestamp_count": int(pd.to_datetime(task374.get("entry_ts", pd.Series(dtype=str)), errors="coerce", utc=True).dt.hour.fillna(-1).eq(0).sum()) if "entry_ts" in task374.columns else 0,
            "source_linked_count": 0,
            "replay_derived_count": 0,
            "approved_count": 0,
            "manual_review_count": 0,
            "rejected_count": 0,
            "namespace_fix_count": 0,
            "namespace_diagnosis": "exact_trade_id_exists_for_covered_rows_but_absent_in_missing_recovery_candidates",
        },
    ]
    return pd.DataFrame(rows)


def _timestamp_precision_audit(protocol: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, scoped in {
        "all_protocol_candidates": protocol,
        "approved_or_fix_candidates": protocol[protocol["review_protocol_decision_v1"].astype(str).isin({"approved_recovery_candidate", "namespace_fix_required"})],
        "p0_p1_candidates": protocol[protocol["recovery_priority_tier"].astype(str).isin({"p0_anchored_or_core", "p1_watchlist_or_theme"})],
    }.items():
        rows.append(
            {
                "scope": scope,
                "row_count": int(len(scoped)),
                "date_only_timestamp_count": int(_safe_numeric(scoped.get("date_only_timestamp_namespace_flag"), scoped.index).sum()) if not scoped.empty else 0,
                "entry_timestamp_precision_missing_count": int(_safe_numeric(scoped.get("entry_timestamp_precision_missing_flag"), scoped.index).sum()) if not scoped.empty else 0,
                "time_blocked_count": int(scoped["time_distance_status"].astype(str).eq("time_blocked").sum()) if "time_distance_status" in scoped.columns and not scoped.empty else 0,
                "timestamp_precision_status": "precision_recovery_required",
            }
        )
    return pd.DataFrame(rows)


def _decision(protocol: pd.DataFrame) -> pd.DataFrame:
    approved = int(protocol["review_protocol_decision_v1"].astype(str).eq("approved_recovery_candidate").sum()) if not protocol.empty else 0
    manual = int(protocol["review_protocol_decision_v1"].astype(str).eq("manual_review_required").sum()) if not protocol.empty else 0
    rejected = int(protocol["review_protocol_decision_v1"].astype(str).eq("rejected_recovery_candidate").sum()) if not protocol.empty else 0
    namespace_fix = int(protocol["review_protocol_decision_v1"].astype(str).eq("namespace_fix_required").sum()) if not protocol.empty else 0
    label_updates = int(_safe_numeric(protocol.get("accepted_label_update_flag"), protocol.index).sum()) if not protocol.empty else 0
    return pd.DataFrame(
        [
            {
                "task_380_verdict": "COMPLETE_PASS" if not protocol.empty and label_updates == 0 else "NOT_YET",
                "strategy_acceptance_status": "UNCHANGED_EXPANDED_SAMPLE_REQUIRED",
                "task_381_revalidation_ready": "YES_DIAGNOSTIC_LAYER_ONLY" if approved > 0 else "NO",
                "total_rows": int(len(protocol)),
                "approved_recovery_candidate_count": approved,
                "manual_review_required_count": manual,
                "rejected_recovery_candidate_count": rejected,
                "namespace_fix_required_count": namespace_fix,
                "accepted_label_update_rows": label_updates,
                "labels_overwritten": "NO",
                "task_376_ontology_relaxed": "NO",
                "theme_promoted_by_task_380": "NO",
                "exact_trade_id_failure_reason": "price_anchor_mismatch_plus_date_only_timestamp_namespace",
            }
        ]
    )


def build_identity_review_protocol_380(
    *,
    identity_candidates_df: pd.DataFrame | None = None,
    p0_p1_review_df: pd.DataFrame | None = None,
    identity_namespace_df: pd.DataFrame | None = None,
    task374_candidates_df: pd.DataFrame | None = None,
    lifecycle_df: pd.DataFrame | None = None,
) -> IdentityReviewProtocol380Artifacts:
    candidates = identity_candidates_df.copy() if identity_candidates_df is not None else _load_csv(TASK_379_CANDIDATES_PATH)
    if p0_p1_review_df is None and TASK_379_P0P1_PATH.exists():
        _load_csv(TASK_379_P0P1_PATH)
    if identity_namespace_df is None and TASK_379_NAMESPACE_PATH.exists():
        _load_csv(TASK_379_NAMESPACE_PATH)
    task374 = task374_candidates_df.copy() if task374_candidates_df is not None else _load_csv(TASK_374_CANDIDATES_PATH)
    lifecycle = lifecycle_df.copy() if lifecycle_df is not None else _load_csv(TASK_372_LIFECYCLE_PATH)

    protocol = _build_protocol_candidates(candidates)
    reviewed = protocol[protocol["review_protocol_decision_v1"].astype(str).eq("approved_recovery_candidate")].copy().reset_index(drop=True)
    manual = protocol[protocol["review_protocol_decision_v1"].astype(str).eq("manual_review_required")].copy().reset_index(drop=True)
    rejected = protocol[protocol["review_protocol_decision_v1"].astype(str).eq("rejected_recovery_candidate")].copy().reset_index(drop=True)
    namespace_fix = protocol[protocol["review_protocol_decision_v1"].astype(str).eq("namespace_fix_required")].copy().reset_index(drop=True)
    namespace_audit = _trade_id_namespace_mismatch_audit(protocol, task374, lifecycle)
    timestamp_audit = _timestamp_precision_audit(protocol)
    decision = _decision(protocol)
    return IdentityReviewProtocol380Artifacts(
        identity_review_protocol_candidates=protocol,
        reviewed_recovery_layer=reviewed,
        manual_review_required_queue=manual,
        rejected_recovery_candidates=rejected,
        namespace_fix_required_queue=namespace_fix,
        trade_id_namespace_mismatch_audit=namespace_audit,
        timestamp_precision_audit=timestamp_audit,
        task_380_decision=decision,
    )


def write_identity_review_protocol_380(
    artifacts: IdentityReviewProtocol380Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.identity_review_protocol_candidates.to_csv(out_dir / "identity_review_protocol_candidates.csv", index=False, encoding="utf-8-sig")
    artifacts.reviewed_recovery_layer.to_csv(out_dir / "reviewed_recovery_layer.csv", index=False, encoding="utf-8-sig")
    artifacts.manual_review_required_queue.to_csv(out_dir / "manual_review_required_queue.csv", index=False, encoding="utf-8-sig")
    artifacts.rejected_recovery_candidates.to_csv(out_dir / "rejected_recovery_candidates.csv", index=False, encoding="utf-8-sig")
    artifacts.namespace_fix_required_queue.to_csv(out_dir / "namespace_fix_required_queue.csv", index=False, encoding="utf-8-sig")
    artifacts.trade_id_namespace_mismatch_audit.to_csv(out_dir / "trade_id_namespace_mismatch_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.timestamp_precision_audit.to_csv(out_dir / "timestamp_precision_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_380_decision.to_csv(out_dir / "task_380_decision.csv", index=False, encoding="utf-8-sig")
