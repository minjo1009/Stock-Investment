from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_378_lifecycle_recovery")
TASK_377_QUEUE_PATH = Path("docs/reports/task_377_lifecycle_coverage_expansion/task_377_recovery_priority_queue.csv")
TASK_377_ANCHORED_AUDIT_PATH = Path("docs/reports/task_377_lifecycle_coverage_expansion/task_377_anchored_oos_core_miss_audit.csv")
TASK_377_THEME_AUDIT_PATH = Path("docs/reports/task_377_lifecycle_coverage_expansion/task_377_theme_leader_miss_audit.csv")
TASK_372_LIFECYCLE_PATH = Path("docs/reports/task_372_historical_source_backfill/task_372_lifecycle_backtest_panel.csv")
TASK_372_SOURCE_EVENT_PATH = Path("docs/reports/task_372_historical_source_backfill/task_372_historical_source_event_dataset.csv")
TASK_376_EVALUATION_PATH = Path("docs/reports/task_376_persistence_universe_rebuild/persistence_universe_evaluation_panel.csv")


@dataclass(frozen=True)
class LifecycleRecovery378Artifacts:
    lifecycle_recovery_candidate_matches: pd.DataFrame
    recovery_priority_status: pd.DataFrame
    anchored_oos_recovery_audit: pd.DataFrame
    core_miss_root_cause_audit: pd.DataFrame
    theme_leader_root_cause_audit: pd.DataFrame
    lifecycle_recovery_sample_adequacy: pd.DataFrame
    task_378_decision: pd.DataFrame


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


def _session_date_from_trade_id(value: Any) -> str:
    parts = str(value).split("|")
    return parts[1] if len(parts) > 1 else ""


def _entry_price_from_trade_id(value: Any) -> float:
    parts = str(value).split("|")
    if len(parts) < 4:
        return float("nan")
    return float(pd.to_numeric(pd.Series([parts[3]]), errors="coerce").iloc[0])


def _diagnostic_target(row: pd.Series) -> float:
    positive = any(
        float(pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").fillna(0).iloc[0]) > 0
        for column in (
            "persistence_confirmed_flag",
            "add_confirmed_flag",
            "scale_up_flag",
            "persistence_depth",
            "add_depth",
            "scale_depth",
        )
    )
    invalidated = float(pd.to_numeric(pd.Series([row.get("invalidated_flag")]), errors="coerce").fillna(0).iloc[0]) > 0
    fragile = float(pd.to_numeric(pd.Series([row.get("fragile_transition_flag")]), errors="coerce").fillna(0).iloc[0]) > 0
    return float(1 if positive and not invalidated and not fragile else 0)


def _prepare_queue(queue: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        "trade_id",
        "symbol",
        "current_split",
        "persistence_universe_bucket",
        "lifecycle_coverage_flag",
        "stateful_persistence_target_v1",
        "target_reason",
        "target_confidence",
        "risk_gate_v1",
        "data_leadership_gate_v1",
        "market_breadth_state",
        "sector_leadership_state",
        "tech_led_narrow_flag",
        "theme_prior_v1",
        "forward_breakout_bucket",
        "forward_persistence_score",
        "theme_group",
        "coverage_gap_class",
        "recovery_priority_tier",
        "recovery_priority_score",
    ]
    out = _ensure_columns(queue, base_cols)[base_cols].copy()
    out["trade_id"] = out["trade_id"].astype(str)
    out["symbol"] = out["symbol"].astype(str)
    out["session_date"] = out["trade_id"].map(_session_date_from_trade_id)
    out["entry_price"] = out["trade_id"].map(_entry_price_from_trade_id)
    return out


def _prepare_lifecycle(lifecycle: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "raw_trade_id",
        "symbol",
        "session_date",
        "event_count",
        "persistence_depth",
        "add_depth",
        "scale_depth",
        "source_linked_flag",
        "fragile_transition_flag",
        "invalidated_flag",
        "add_confirmed_flag",
        "scale_up_flag",
        "persistence_confirmed_flag",
        "lineage_quality",
        "identity_confidence",
        "persistence_duration_minutes",
        "realized_R",
        "start_event_timestamp",
        "end_event_timestamp",
        "evaluation_scope",
    ]
    out = _ensure_columns(lifecycle, cols)[cols].copy()
    out = out[out["evaluation_scope"].astype(str).eq("full_period")].copy()
    out["raw_trade_id"] = out["raw_trade_id"].astype(str)
    out["symbol"] = out["symbol"].astype(str)
    out["session_date"] = out["session_date"].astype(str)
    out["raw_entry_price"] = out["raw_trade_id"].map(_entry_price_from_trade_id)
    out["diagnostic_stateful_target"] = out.apply(_diagnostic_target, axis=1)
    return out.reset_index(drop=True)


def _prepare_source_events(source_events: pd.DataFrame) -> pd.DataFrame:
    cols = ["symbol", "session_date", "event_type", "event_source", "source_event_id", "lifecycle_id"]
    out = _ensure_columns(source_events, cols)[cols].copy()
    out["symbol"] = out["symbol"].astype(str)
    out["session_date"] = out["session_date"].astype(str)
    grouped = (
        out.groupby(["symbol", "session_date"], dropna=False)
        .agg(
            source_event_count=("source_event_id", "count"),
            source_lifecycle_count=("lifecycle_id", "nunique"),
            source_event_types=("event_type", lambda values: "|".join(sorted(set(str(v) for v in values if str(v))))),
        )
        .reset_index()
    )
    return grouped


def _match_tier(row: pd.Series) -> str:
    if int(row.get("exact_trade_id_count", 0)) > 0:
        return "exact_trade_id_match"
    symbol_session_count = int(row.get("symbol_session_lifecycle_count", 0))
    if symbol_session_count == 1:
        return "symbol_session_single_match"
    if symbol_session_count > 1:
        return "symbol_session_multi_match"
    if int(row.get("source_event_count", 0)) > 0:
        return "source_event_candidate_match"
    return "no_recovery_evidence"


def _identity_review_status(row: pd.Series) -> str:
    tier = str(row.get("recovery_match_tier", ""))
    if tier == "exact_trade_id_match":
        return "diagnostic_exact_match"
    if tier == "symbol_session_single_match":
        return "needs_identity_review"
    if tier == "symbol_session_multi_match":
        return "needs_identity_disambiguation"
    if tier == "source_event_candidate_match":
        return "needs_source_event_backfill"
    return "no_current_evidence"


def _build_candidate_matches(queue: pd.DataFrame, lifecycle: pd.DataFrame, source_events: pd.DataFrame) -> pd.DataFrame:
    exact = (
        lifecycle.groupby("raw_trade_id", dropna=False)
        .agg(exact_trade_id_count=("raw_trade_id", "size"))
        .reset_index()
        .rename(columns={"raw_trade_id": "trade_id"})
    )
    symbol_session = (
        lifecycle.groupby(["symbol", "session_date"], dropna=False)
        .agg(
            symbol_session_lifecycle_count=("raw_trade_id", "nunique"),
            candidate_raw_trade_id=("raw_trade_id", "first"),
            candidate_raw_entry_price=("raw_entry_price", "first"),
            candidate_identity_confidence=("identity_confidence", "max"),
            candidate_lineage_quality=("lineage_quality", "first"),
            candidate_event_count=("event_count", "max"),
            candidate_diagnostic_stateful_target=("diagnostic_stateful_target", "max"),
        )
        .reset_index()
    )
    frame = queue.merge(exact, on="trade_id", how="left")
    frame = frame.merge(symbol_session, on=["symbol", "session_date"], how="left")
    frame = frame.merge(source_events, on=["symbol", "session_date"], how="left")
    for column in ("exact_trade_id_count", "symbol_session_lifecycle_count", "source_event_count", "source_lifecycle_count"):
        frame[column] = _safe_numeric(frame.get(column), frame.index).astype(int)
    frame["recovery_match_tier"] = frame.apply(_match_tier, axis=1)
    frame["recovery_identity_status"] = frame.apply(_identity_review_status, axis=1)
    frame["price_abs_diff"] = (_safe_numeric(frame.get("entry_price"), frame.index) - _safe_numeric(frame.get("candidate_raw_entry_price"), frame.index)).abs().round(6)
    frame["candidate_recovery_match_flag"] = frame["recovery_match_tier"].ne("no_recovery_evidence").astype(int)
    frame["accepted_label_update_flag"] = 0
    frame["diagnostic_only_flag"] = 1
    return frame.sort_values(
        ["candidate_recovery_match_flag", "recovery_priority_score", "symbol"],
        ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)


def _root_cause(row: pd.Series) -> str:
    causes: list[str] = []
    tier = str(row.get("recovery_match_tier", ""))
    if tier in {"symbol_session_single_match", "symbol_session_multi_match"}:
        causes.append("coverage_identity_gap")
    elif tier == "source_event_candidate_match":
        causes.append("source_event_to_lifecycle_gap")
    elif str(row.get("current_split", "")) == "anchored_oos":
        causes.append("anchored_oos_undercovered")
    if str(row.get("risk_gate_v1", "")) == "fail" or str(row.get("market_breadth_state", "")) == "narrow" or float(pd.to_numeric(pd.Series([row.get("tech_led_narrow_flag")]), errors="coerce").fillna(0).iloc[0]) > 0:
        causes.append("risk_or_breadth_suppression")
    if str(row.get("theme_group", "")) in {"semis_leader", "platform_quality_leader"} and float(pd.to_numeric(pd.Series([row.get("theme_prior_v1")]), errors="coerce").fillna(0).iloc[0]) < 1.0:
        causes.append("theme_prior_design_limit")
    if not causes and str(row.get("persistence_universe_bucket", "")) != "persistence_core":
        causes.append("prediction_gate_miss")
    if not causes:
        causes.append("coverage_identity_gap")
    return "|".join(causes)


def _recovery_priority_status(matches: pd.DataFrame) -> pd.DataFrame:
    frame = matches.copy()
    frame["root_cause_class"] = frame.apply(_root_cause, axis=1)
    keep = [
        "trade_id",
        "symbol",
        "session_date",
        "current_split",
        "persistence_universe_bucket",
        "coverage_gap_class",
        "theme_group",
        "recovery_priority_tier",
        "recovery_priority_score",
        "recovery_match_tier",
        "recovery_identity_status",
        "candidate_recovery_match_flag",
        "accepted_label_update_flag",
        "diagnostic_only_flag",
        "root_cause_class",
    ]
    return frame[keep].sort_values(["recovery_priority_score", "trade_id"], ascending=[False, True], kind="stable").reset_index(drop=True)


def _anchored_oos_recovery_audit(anchored_audit: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(anchored_audit, ["trade_id", "core_miss_reasons", "coverage_status"]).copy()
    merged = frame.merge(
        matches[
            [
                "trade_id",
                "recovery_match_tier",
                "recovery_identity_status",
                "candidate_recovery_match_flag",
                "accepted_label_update_flag",
                "diagnostic_only_flag",
            ]
        ],
        on="trade_id",
        how="left",
    )
    merged["anchored_oos_interpretability_status"] = "diagnostic_only_undercovered"
    merged.loc[merged["coverage_status"].astype(str).eq("covered"), "anchored_oos_interpretability_status"] = "diagnostic_only_covered_sparse"
    return merged.reset_index(drop=True)


def _core_miss_root_cause_audit(matches: pd.DataFrame) -> pd.DataFrame:
    core_like = matches[matches["coverage_gap_class"].astype(str).isin({"core_missing", "watchlist_missing", "anchored_oos_core_or_watchlist_missing"})].copy()
    core_like["root_cause_class"] = core_like.apply(_root_cause, axis=1)
    return core_like.reset_index(drop=True)


def _theme_leader_root_cause_audit(theme_audit: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(theme_audit, ["trade_id", "theme_audit_status", "core_miss_reasons"]).copy()
    merged = frame.merge(
        matches[
            [
                "trade_id",
                "recovery_match_tier",
                "recovery_identity_status",
                "candidate_recovery_match_flag",
                "accepted_label_update_flag",
                "diagnostic_only_flag",
            ]
        ],
        on="trade_id",
        how="left",
    )
    merged["theme_promoted_by_task_378_flag"] = 0
    merged["root_cause_class"] = merged.apply(_root_cause, axis=1)
    return merged.reset_index(drop=True)


def _sample_adequacy(matches: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope_name, scoped in {
        "all_missing": matches,
        "p0_p1_missing": matches[matches["recovery_priority_tier"].astype(str).isin({"p0_anchored_or_core", "p1_watchlist_or_theme"})],
        "anchored_oos_missing": matches[matches["current_split"].astype(str).eq("anchored_oos")],
    }.items():
        rows.append(
            {
                "scope": scope_name,
                "missing_rows": int(len(scoped)),
                "candidate_recovery_rows": int(_safe_numeric(scoped.get("candidate_recovery_match_flag"), scoped.index).sum()) if not scoped.empty else 0,
                "exact_trade_id_rows": int(scoped["recovery_match_tier"].astype(str).eq("exact_trade_id_match").sum()) if not scoped.empty else 0,
                "symbol_session_rows": int(scoped["recovery_match_tier"].astype(str).isin({"symbol_session_single_match", "symbol_session_multi_match"}).sum()) if not scoped.empty else 0,
                "source_event_only_rows": int(scoped["recovery_match_tier"].astype(str).eq("source_event_candidate_match").sum()) if not scoped.empty else 0,
                "accepted_label_update_rows": int(_safe_numeric(scoped.get("accepted_label_update_flag"), scoped.index).sum()) if not scoped.empty else 0,
                "gate_status": "diagnostic_only",
            }
        )
    return pd.DataFrame(rows)


def _next_priority(matches: pd.DataFrame) -> str:
    p0p1 = matches[matches["recovery_priority_tier"].astype(str).isin({"p0_anchored_or_core", "p1_watchlist_or_theme"})]
    if not p0p1.empty and p0p1["recovery_match_tier"].astype(str).isin({"symbol_session_single_match", "symbol_session_multi_match"}).any():
        return "manual_identity_review_for_p0_p1"
    if matches["recovery_match_tier"].astype(str).eq("source_event_candidate_match").any():
        return "source_event_to_lifecycle_backfill"
    return "expanded_lifecycle_capture_required"


def _decision(matches: pd.DataFrame, adequacy: pd.DataFrame) -> pd.DataFrame:
    total = int(len(matches))
    candidate = int(_safe_numeric(matches.get("candidate_recovery_match_flag"), matches.index).sum()) if total else 0
    p0p1 = matches[matches["recovery_priority_tier"].astype(str).isin({"p0_anchored_or_core", "p1_watchlist_or_theme"})]
    p0p1_symbol_session = int(p0p1["recovery_match_tier"].astype(str).isin({"symbol_session_single_match", "symbol_session_multi_match"}).sum()) if not p0p1.empty else 0
    label_updates = int(_safe_numeric(matches.get("accepted_label_update_flag"), matches.index).sum()) if total else 0
    return pd.DataFrame(
        [
            {
                "task_378_verdict": "COMPLETE_PASS" if total > 0 and label_updates == 0 and not adequacy.empty else "NOT_YET",
                "strategy_acceptance_status": "UNCHANGED_EXPANDED_SAMPLE_REQUIRED",
                "next_priority": _next_priority(matches),
                "missing_rows": total,
                "candidate_recovery_rows": candidate,
                "candidate_recovery_share": round(candidate / total, 6) if total else 0.0,
                "p0_p1_missing_rows": int(len(p0p1)),
                "p0_p1_symbol_session_recovery_rows": p0p1_symbol_session,
                "accepted_label_update_rows": label_updates,
                "task_376_ontology_relaxed": "NO",
                "theme_promoted_by_task_378": "NO",
                "anchored_oos_core_absence_interpretable": "NO",
            }
        ]
    )


def build_lifecycle_recovery_378(
    *,
    recovery_queue_df: pd.DataFrame | None = None,
    anchored_audit_df: pd.DataFrame | None = None,
    theme_audit_df: pd.DataFrame | None = None,
    lifecycle_df: pd.DataFrame | None = None,
    source_event_df: pd.DataFrame | None = None,
    evaluation_panel_df: pd.DataFrame | None = None,
) -> LifecycleRecovery378Artifacts:
    queue = _prepare_queue(recovery_queue_df.copy() if recovery_queue_df is not None else _load_csv(TASK_377_QUEUE_PATH))
    lifecycle = _prepare_lifecycle(lifecycle_df.copy() if lifecycle_df is not None else _load_csv(TASK_372_LIFECYCLE_PATH))
    source_events = _prepare_source_events(source_event_df.copy() if source_event_df is not None else _load_csv(TASK_372_SOURCE_EVENT_PATH))
    anchored_audit = anchored_audit_df.copy() if anchored_audit_df is not None else _load_csv(TASK_377_ANCHORED_AUDIT_PATH)
    theme_audit = theme_audit_df.copy() if theme_audit_df is not None else _load_csv(TASK_377_THEME_AUDIT_PATH)
    if evaluation_panel_df is None and TASK_376_EVALUATION_PATH.exists():
        _load_csv(TASK_376_EVALUATION_PATH)

    matches = _build_candidate_matches(queue, lifecycle, source_events)
    priority_status = _recovery_priority_status(matches)
    anchored_recovery = _anchored_oos_recovery_audit(anchored_audit, matches)
    core_root = _core_miss_root_cause_audit(matches)
    theme_root = _theme_leader_root_cause_audit(theme_audit, matches)
    adequacy = _sample_adequacy(matches)
    decision = _decision(matches, adequacy)
    return LifecycleRecovery378Artifacts(
        lifecycle_recovery_candidate_matches=matches,
        recovery_priority_status=priority_status,
        anchored_oos_recovery_audit=anchored_recovery,
        core_miss_root_cause_audit=core_root,
        theme_leader_root_cause_audit=theme_root,
        lifecycle_recovery_sample_adequacy=adequacy,
        task_378_decision=decision,
    )


def write_lifecycle_recovery_378(
    artifacts: LifecycleRecovery378Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.lifecycle_recovery_candidate_matches.to_csv(out_dir / "lifecycle_recovery_candidate_matches.csv", index=False, encoding="utf-8-sig")
    artifacts.recovery_priority_status.to_csv(out_dir / "recovery_priority_status.csv", index=False, encoding="utf-8-sig")
    artifacts.anchored_oos_recovery_audit.to_csv(out_dir / "anchored_oos_recovery_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.core_miss_root_cause_audit.to_csv(out_dir / "core_miss_root_cause_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.theme_leader_root_cause_audit.to_csv(out_dir / "theme_leader_root_cause_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.lifecycle_recovery_sample_adequacy.to_csv(out_dir / "lifecycle_recovery_sample_adequacy.csv", index=False, encoding="utf-8-sig")
    artifacts.task_378_decision.to_csv(out_dir / "task_378_decision.csv", index=False, encoding="utf-8-sig")
