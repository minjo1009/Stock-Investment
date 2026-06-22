from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_379_lifecycle_identity_reconciliation")
TASK_378_MATCHES_PATH = Path("docs/reports/task_378_lifecycle_recovery/lifecycle_recovery_candidate_matches.csv")
TASK_378_PRIORITY_PATH = Path("docs/reports/task_378_lifecycle_recovery/recovery_priority_status.csv")
TASK_378_DECISION_PATH = Path("docs/reports/task_378_lifecycle_recovery/task_378_decision.csv")
TASK_372_LIFECYCLE_PATH = Path("docs/reports/task_372_historical_source_backfill/task_372_lifecycle_backtest_panel.csv")


@dataclass(frozen=True)
class LifecycleIdentityReconciliation379Artifacts:
    identity_reconciliation_candidates: pd.DataFrame
    identity_confidence_audit: pd.DataFrame
    p0_p1_identity_review_queue: pd.DataFrame
    high_confidence_recovered_candidates: pd.DataFrame
    medium_confidence_review_queue: pd.DataFrame
    low_confidence_reject_queue: pd.DataFrame
    identity_namespace_audit: pd.DataFrame
    task_379_decision: pd.DataFrame


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


def _entry_ts_from_trade_id(value: Any) -> pd.Timestamp:
    parts = str(value).split("|")
    if len(parts) < 3:
        return pd.NaT
    return pd.to_datetime(parts[2], errors="coerce", utc=True)


def _prepare_lifecycle_context(lifecycle: pd.DataFrame) -> pd.DataFrame:
    cols = ["raw_trade_id", "start_event_timestamp", "end_event_timestamp", "identity_origin", "source_linked_flag", "replay_derived_only"]
    out = _ensure_columns(lifecycle, cols)[cols].copy()
    out["candidate_raw_trade_id"] = out["raw_trade_id"].astype(str)
    out["candidate_start_event_timestamp"] = pd.to_datetime(out["start_event_timestamp"], errors="coerce", utc=True)
    out["candidate_end_event_timestamp"] = pd.to_datetime(out["end_event_timestamp"], errors="coerce", utc=True)
    return out.drop(columns=["raw_trade_id", "start_event_timestamp", "end_event_timestamp"]).drop_duplicates(
        "candidate_raw_trade_id", keep="first"
    )


def _time_distance_minutes(row: pd.Series) -> float:
    entry = row.get("entry_component_ts")
    candidate = row.get("candidate_start_event_timestamp")
    if pd.isna(entry) or pd.isna(candidate):
        return float("nan")
    entry_ts = pd.Timestamp(entry)
    candidate_ts = pd.Timestamp(candidate)
    if entry_ts.time().hour == 0 and entry_ts.time().minute == 0 and entry_ts.time().second == 0:
        return 0.0 if entry_ts.date() == candidate_ts.date() else abs((candidate_ts.normalize() - entry_ts.normalize()).total_seconds()) / 60.0
    return abs((candidate_ts - entry_ts).total_seconds()) / 60.0


def _prepare_candidates(matches: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    base = matches.copy()
    for column in ("trade_id", "candidate_raw_trade_id", "symbol", "recovery_match_tier", "recovery_priority_tier"):
        if column not in base.columns:
            base[column] = ""
        base[column] = base[column].fillna("").astype(str)
    context = _prepare_lifecycle_context(lifecycle)
    out = base.merge(context, on="candidate_raw_trade_id", how="left")
    out["entry_component_ts"] = out["trade_id"].map(_entry_ts_from_trade_id)
    out["entry_time_distance_minutes"] = out.apply(_time_distance_minutes, axis=1)
    out["price_rel_diff"] = (
        _safe_numeric(out.get("price_abs_diff"), out.index)
        / _safe_numeric(out.get("entry_price"), out.index).replace(0, np.nan)
    ).fillna(0.0).round(6)
    out["accepted_label_update_flag"] = 0
    out["diagnostic_only_flag"] = 1
    return out


def _price_component(price_rel_diff: float) -> tuple[float, str]:
    if price_rel_diff <= 0.01:
        return 0.20, "price_close"
    if price_rel_diff <= 0.02:
        return 0.12, "price_moderate"
    if price_rel_diff <= 0.05:
        return 0.03, "price_wide"
    return -0.15, "price_blocked"


def _time_component(minutes: float) -> tuple[float, str]:
    if pd.isna(minutes):
        return 0.0, "time_unknown"
    if minutes <= 5:
        return 0.15, "time_close"
    if minutes <= 30:
        return 0.08, "time_moderate"
    if minutes <= 390:
        return 0.02, "time_same_session"
    return -0.12, "time_blocked"


def _score_row(row: pd.Series) -> pd.Series:
    tier = str(row.get("recovery_match_tier", ""))
    lineage = str(row.get("candidate_lineage_quality", ""))
    score = 0.0
    reasons: list[str] = []
    if tier == "exact_trade_id_match":
        score += 0.45
        reasons.append("exact_trade_id")
    elif tier == "symbol_session_single_match":
        score += 0.25
        reasons.append("symbol_session_single")
    elif tier == "symbol_session_multi_match":
        score += 0.10
        reasons.append("symbol_session_multi")
    elif tier == "source_event_candidate_match":
        score += 0.05
        reasons.append("source_event_candidate")
    else:
        return pd.Series(
            {
                "identity_confidence_score_v1": 0.0,
                "identity_confidence_bucket_v1": "no_recovery_evidence",
                "identity_score_reasons": "no_recovery_evidence",
                "price_distance_status": "no_recovery_evidence",
                "time_distance_status": "no_recovery_evidence",
                "replay_derived_penalty_flag": 0,
            }
        )

    if lineage == "source_linked":
        score += 0.25
        reasons.append("source_linked")
    elif lineage == "replay_derived":
        score -= 0.10
        reasons.append("replay_derived_penalty")
    elif lineage:
        score += 0.08
        reasons.append("session_derived")

    price_score, price_status = _price_component(float(pd.to_numeric(pd.Series([row.get("price_rel_diff")]), errors="coerce").fillna(0).iloc[0]))
    time_score, time_status = _time_component(float(pd.to_numeric(pd.Series([row.get("entry_time_distance_minutes")]), errors="coerce").iloc[0]))
    score += price_score + time_score
    reasons.extend([price_status, time_status])

    event_count = float(pd.to_numeric(pd.Series([row.get("candidate_event_count")]), errors="coerce").fillna(0).iloc[0])
    if event_count >= 3:
        score += 0.08
        reasons.append("event_count_3_plus")
    elif event_count >= 2:
        score += 0.03
        reasons.append("event_count_2_plus")

    if float(pd.to_numeric(pd.Series([row.get("candidate_diagnostic_stateful_target")]), errors="coerce").fillna(0).iloc[0]) > 0:
        score += 0.05
        reasons.append("diagnostic_positive_state")
    if tier == "symbol_session_multi_match":
        score -= 0.10
        reasons.append("multi_match_penalty")

    if lineage == "replay_derived":
        score = min(score, 0.69)
    score = round(float(np.clip(score, 0.0, 1.0)), 6)
    if score >= 0.75:
        bucket = "high_confidence_recovered_candidate"
    elif score >= 0.45:
        bucket = "medium_confidence_review_queue"
    elif score > 0:
        bucket = "low_confidence_reject_queue"
    else:
        bucket = "no_recovery_evidence"
    return pd.Series(
        {
            "identity_confidence_score_v1": score,
            "identity_confidence_bucket_v1": bucket,
            "identity_score_reasons": "|".join(reasons),
            "price_distance_status": price_status,
            "time_distance_status": time_status,
            "replay_derived_penalty_flag": int(lineage == "replay_derived"),
        }
    )


def _build_identity_candidates(matches: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    frame = _prepare_candidates(matches, lifecycle)
    scored = frame.apply(_score_row, axis=1)
    out = pd.concat([frame, scored], axis=1)
    return out.sort_values(
        ["identity_confidence_score_v1", "recovery_priority_score", "trade_id"],
        ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)


def _confidence_audit(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for bucket, bucket_df in candidates.groupby("identity_confidence_bucket_v1", dropna=False, sort=False):
        rows.append(
            {
                "identity_confidence_bucket_v1": str(bucket),
                "row_count": int(len(bucket_df)),
                "p0_p1_count": int(bucket_df["recovery_priority_tier"].astype(str).isin({"p0_anchored_or_core", "p1_watchlist_or_theme"}).sum()),
                "replay_derived_count": int(_safe_numeric(bucket_df.get("replay_derived_penalty_flag"), bucket_df.index).sum()),
                "price_blocked_count": int(bucket_df["price_distance_status"].astype(str).eq("price_blocked").sum()),
                "time_blocked_count": int(bucket_df["time_distance_status"].astype(str).eq("time_blocked").sum()),
                "accepted_label_update_rows": int(_safe_numeric(bucket_df.get("accepted_label_update_flag"), bucket_df.index).sum()),
            }
        )
    return pd.DataFrame(rows)


def _identity_namespace_audit(candidates: pd.DataFrame) -> pd.DataFrame:
    total = int(len(candidates))
    return pd.DataFrame(
        [
            {
                "audit_name": "identity_namespace_summary",
                "total_rows": total,
                "exact_trade_id_match_rows": int(candidates["recovery_match_tier"].astype(str).eq("exact_trade_id_match").sum()) if total else 0,
                "symbol_session_candidate_rows": int(candidates["recovery_match_tier"].astype(str).isin({"symbol_session_single_match", "symbol_session_multi_match"}).sum()) if total else 0,
                "no_recovery_evidence_rows": int(candidates["recovery_match_tier"].astype(str).eq("no_recovery_evidence").sum()) if total else 0,
                "candidate_raw_trade_id_differs_rows": int((candidates["trade_id"].astype(str) != candidates["candidate_raw_trade_id"].astype(str)).sum()) if total else 0,
                "namespace_status": "exact_trade_id_reconciliation_failure",
            }
        ]
    )


def _decision(candidates: pd.DataFrame) -> pd.DataFrame:
    p0p1 = candidates[candidates["recovery_priority_tier"].astype(str).isin({"p0_anchored_or_core", "p1_watchlist_or_theme"})].copy()
    high = int(candidates["identity_confidence_bucket_v1"].astype(str).eq("high_confidence_recovered_candidate").sum()) if not candidates.empty else 0
    medium = int(candidates["identity_confidence_bucket_v1"].astype(str).eq("medium_confidence_review_queue").sum()) if not candidates.empty else 0
    low = int(candidates["identity_confidence_bucket_v1"].astype(str).eq("low_confidence_reject_queue").sum()) if not candidates.empty else 0
    no_evidence = int(candidates["identity_confidence_bucket_v1"].astype(str).eq("no_recovery_evidence").sum()) if not candidates.empty else 0
    label_updates = int(_safe_numeric(candidates.get("accepted_label_update_flag"), candidates.index).sum()) if not candidates.empty else 0
    return pd.DataFrame(
        [
            {
                "task_379_verdict": "COMPLETE_PASS" if not candidates.empty and label_updates == 0 else "NOT_YET",
                "strategy_acceptance_status": "UNCHANGED_EXPANDED_SAMPLE_REQUIRED",
                "next_priority": "manual_review_high_medium_confidence_before_revalidation",
                "total_rows": int(len(candidates)),
                "p0_p1_rows": int(len(p0p1)),
                "high_confidence_rows": high,
                "medium_confidence_rows": medium,
                "low_confidence_rows": low,
                "no_recovery_evidence_rows": no_evidence,
                "p0_p1_high_confidence_rows": int(p0p1["identity_confidence_bucket_v1"].astype(str).eq("high_confidence_recovered_candidate").sum()) if not p0p1.empty else 0,
                "p0_p1_medium_confidence_rows": int(p0p1["identity_confidence_bucket_v1"].astype(str).eq("medium_confidence_review_queue").sum()) if not p0p1.empty else 0,
                "price_blocked_rows": int(candidates["price_distance_status"].astype(str).eq("price_blocked").sum()) if not candidates.empty else 0,
                "time_blocked_rows": int(candidates["time_distance_status"].astype(str).eq("time_blocked").sum()) if not candidates.empty else 0,
                "replay_derived_only_rows": int(_safe_numeric(candidates.get("replay_derived_penalty_flag"), candidates.index).sum()) if not candidates.empty else 0,
                "accepted_label_update_rows": label_updates,
                "task_376_ontology_relaxed": "NO",
                "theme_promoted_by_task_379": "NO",
                "labels_overwritten": "NO",
                "task_381_revalidation_ready": "NO",
            }
        ]
    )


def build_lifecycle_identity_reconciliation_379(
    *,
    recovery_matches_df: pd.DataFrame | None = None,
    recovery_priority_df: pd.DataFrame | None = None,
    task_378_decision_df: pd.DataFrame | None = None,
    lifecycle_df: pd.DataFrame | None = None,
) -> LifecycleIdentityReconciliation379Artifacts:
    matches = recovery_matches_df.copy() if recovery_matches_df is not None else _load_csv(TASK_378_MATCHES_PATH)
    if recovery_priority_df is None and TASK_378_PRIORITY_PATH.exists():
        _load_csv(TASK_378_PRIORITY_PATH)
    if task_378_decision_df is None and TASK_378_DECISION_PATH.exists():
        _load_csv(TASK_378_DECISION_PATH)
    lifecycle = lifecycle_df.copy() if lifecycle_df is not None else _load_csv(TASK_372_LIFECYCLE_PATH)

    candidates = _build_identity_candidates(matches, lifecycle)
    p0p1 = candidates[candidates["recovery_priority_tier"].astype(str).isin({"p0_anchored_or_core", "p1_watchlist_or_theme"})].copy()
    high = candidates[candidates["identity_confidence_bucket_v1"].astype(str).eq("high_confidence_recovered_candidate")].copy()
    medium = candidates[candidates["identity_confidence_bucket_v1"].astype(str).eq("medium_confidence_review_queue")].copy()
    low = candidates[candidates["identity_confidence_bucket_v1"].astype(str).isin({"low_confidence_reject_queue", "no_recovery_evidence"})].copy()
    audit = _confidence_audit(candidates)
    namespace = _identity_namespace_audit(candidates)
    decision = _decision(candidates)
    return LifecycleIdentityReconciliation379Artifacts(
        identity_reconciliation_candidates=candidates,
        identity_confidence_audit=audit,
        p0_p1_identity_review_queue=p0p1.reset_index(drop=True),
        high_confidence_recovered_candidates=high.reset_index(drop=True),
        medium_confidence_review_queue=medium.reset_index(drop=True),
        low_confidence_reject_queue=low.reset_index(drop=True),
        identity_namespace_audit=namespace,
        task_379_decision=decision,
    )


def write_lifecycle_identity_reconciliation_379(
    artifacts: LifecycleIdentityReconciliation379Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.identity_reconciliation_candidates.to_csv(out_dir / "identity_reconciliation_candidates.csv", index=False, encoding="utf-8-sig")
    artifacts.identity_confidence_audit.to_csv(out_dir / "identity_confidence_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.p0_p1_identity_review_queue.to_csv(out_dir / "p0_p1_identity_review_queue.csv", index=False, encoding="utf-8-sig")
    artifacts.high_confidence_recovered_candidates.to_csv(out_dir / "high_confidence_recovered_candidates.csv", index=False, encoding="utf-8-sig")
    artifacts.medium_confidence_review_queue.to_csv(out_dir / "medium_confidence_review_queue.csv", index=False, encoding="utf-8-sig")
    artifacts.low_confidence_reject_queue.to_csv(out_dir / "low_confidence_reject_queue.csv", index=False, encoding="utf-8-sig")
    artifacts.identity_namespace_audit.to_csv(out_dir / "identity_namespace_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_379_decision.to_csv(out_dir / "task_379_decision.csv", index=False, encoding="utf-8-sig")
