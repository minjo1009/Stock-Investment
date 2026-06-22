from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_376_persistence_universe_rebuild")
TASK_374_CANDIDATES_PATH = Path("docs/reports/task_374_forward_pure_breakout/forward_pure_breakout_candidates.csv")
TASK_372_LIFECYCLE_PATH = Path("docs/reports/task_372_historical_source_backfill/task_372_lifecycle_backtest_panel.csv")
TASK_375_PREDICTION_PATH = Path("docs/reports/task_375_forward_persistence/forward_persistence_prediction_frame.csv")
FEATURE_SET_VERSION = "task376-persistence-universe-v1"
MIN_BUCKET_COUNT = 30
MIN_TOTAL_BUCKETED = 120

PREDICTION_COLUMNS = [
    "trade_id",
    "symbol",
    "entry_ts",
    "prediction_cutoff_ts",
    "current_split",
    "forward_only_flag",
    "feature_set_version",
    "session_timing_bucket",
    "relative_volume_percentile",
    "price_vs_session_vwap_at_breakout",
    "vwap_deviation_at_breakout",
    "vwap_slope_prebreak",
    "breakout_bar_close_location",
    "market_breadth_state",
    "gap_environment_state",
    "sector_leadership_state",
    "same_day_candidate_count",
    "same_day_sector_candidate_count",
    "dispersion_20d",
    "mean_pairwise_corr",
    "semis_concentration_ratio",
    "daily_bias",
    "context_quality_score",
    "risk_pressure_score",
    "forward_breakout_score",
    "forward_breakout_bucket",
    "forward_high_quality_flag",
    "forward_weak_flag",
    "first_30m_flag",
    "tech_led_narrow_flag",
    "forward_persistence_score",
    "forward_persistence_bucket",
    "predicted_persistence_flag",
]

LIFECYCLE_COLUMNS = [
    "raw_trade_id",
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

FORBIDDEN_PREDICTION_COLUMNS = {
    "stateful_persistence_target_v1",
    "target_reason",
    "label_eligible_flag",
    "lifecycle_coverage_flag",
    "target_confidence",
    "exclusion_reason",
    "realized_R",
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
}


@dataclass(frozen=True)
class PersistenceUniverse376Artifacts:
    persistence_universe_prediction_frame: pd.DataFrame
    stateful_persistence_labels: pd.DataFrame
    persistence_universe_evaluation_panel: pd.DataFrame
    persistence_universe_bucket_audit: pd.DataFrame
    persistence_universe_leakage_audit: pd.DataFrame
    persistence_universe_sample_adequacy_audit: pd.DataFrame
    persistence_universe_decision: pd.DataFrame


def _safe_numeric(series: pd.Series | None, index: pd.Index, default: float = 0.0) -> pd.Series:
    if series is None:
        return pd.Series(default, index=index, dtype=float)
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _raw_numeric(series: pd.Series | None, index: pd.Index) -> pd.Series:
    if series is None:
        return pd.Series(np.nan, index=index, dtype=float)
    return pd.to_numeric(series, errors="coerce")


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = np.nan
    return out


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def _prepare_candidates(candidates: pd.DataFrame, persistence_prediction: pd.DataFrame | None = None) -> pd.DataFrame:
    out = candidates.copy()
    out["trade_id"] = out["trade_id"].astype(str)
    out["entry_ts"] = pd.to_datetime(out["entry_ts"], errors="coerce", utc=True)
    out = out.sort_values(["entry_ts", "trade_id"], kind="stable").drop_duplicates("trade_id", keep="first")
    if persistence_prediction is not None and not persistence_prediction.empty:
        diag_cols = ["trade_id", "forward_persistence_score", "forward_persistence_bucket", "predicted_persistence_flag"]
        diag = _ensure_columns(persistence_prediction, diag_cols)[diag_cols].copy()
        diag["trade_id"] = diag["trade_id"].astype(str)
        diag = diag.drop_duplicates("trade_id", keep="first")
        out = out.merge(diag, on="trade_id", how="left", suffixes=("", "_task375"))
        for column in ("forward_persistence_score", "forward_persistence_bucket", "predicted_persistence_flag"):
            task375_col = f"{column}_task375"
            if task375_col in out.columns:
                out[column] = out[column].where(out[column].notna(), out[task375_col])
                out = out.drop(columns=[task375_col])
    if "forward_persistence_score" not in out.columns or out["forward_persistence_score"].isna().all():
        out["forward_persistence_score"] = (
            0.50 * _safe_numeric(out.get("forward_breakout_score"), out.index)
            + 0.30 * _safe_numeric(out.get("context_quality_score"), out.index)
            + 0.20 * (1.0 - _safe_numeric(out.get("risk_pressure_score"), out.index))
        ).clip(0.0, 1.0).round(6)
    if "forward_persistence_bucket" not in out.columns:
        out["forward_persistence_bucket"] = np.nan
    out["forward_persistence_bucket"] = out["forward_persistence_bucket"].fillna(
        pd.Series(
            np.select(
                [
                    _safe_numeric(out.get("forward_persistence_score"), out.index).ge(0.72)
                    & out["forward_breakout_bucket"].astype(str).eq("high_quality"),
                    _safe_numeric(out.get("forward_persistence_score"), out.index).ge(0.58),
                    _safe_numeric(out.get("forward_persistence_score"), out.index).lt(0.45),
                ],
                ["predicted_expandable", "watchlist", "weak_persistence"],
                default="mixed_persistence",
            ),
            index=out.index,
        )
    )
    if "predicted_persistence_flag" not in out.columns:
        out["predicted_persistence_flag"] = out["forward_persistence_bucket"].astype(str).eq("predicted_expandable").astype(int)
    return out.reset_index(drop=True)


def _prepare_lifecycle(lifecycle: pd.DataFrame) -> pd.DataFrame:
    if lifecycle.empty:
        return _ensure_columns(lifecycle, LIFECYCLE_COLUMNS)
    out = _ensure_columns(lifecycle, LIFECYCLE_COLUMNS)
    out = out[out["evaluation_scope"].astype(str).eq("full_period")].copy()
    out["raw_trade_id"] = out["raw_trade_id"].astype(str)
    out["source_linked_sort"] = _safe_numeric(out.get("source_linked_flag"), out.index)
    out["identity_confidence_sort"] = _safe_numeric(out.get("identity_confidence"), out.index)
    out["event_count_sort"] = _safe_numeric(out.get("event_count"), out.index)
    out["end_event_timestamp_sort"] = pd.to_datetime(out.get("end_event_timestamp"), errors="coerce", utc=True)
    out = out.sort_values(
        ["raw_trade_id", "source_linked_sort", "identity_confidence_sort", "event_count_sort", "end_event_timestamp_sort"],
        ascending=[True, False, False, False, False],
        kind="stable",
    ).drop_duplicates("raw_trade_id", keep="first")
    return out.drop(columns=[c for c in out.columns if c.endswith("_sort")]).reset_index(drop=True)


def _theme_prior(symbol: Any) -> float:
    text = str(symbol).upper()
    if text in {"AAPL", "MSFT", "GOOGL", "META", "AMZN", "COST"}:
        return 1.0
    if text in {"NVDA", "AMD", "AVGO", "QCOM"}:
        return 0.45
    if text in {"NFLX", "TSLA"}:
        return 0.30
    return 0.20


def _risk_gate(frame: pd.DataFrame) -> pd.Series:
    risk = _safe_numeric(frame.get("risk_pressure_score"), frame.index)
    hard_fail = (
        risk.ge(0.55)
        | _safe_numeric(frame.get("forward_weak_flag"), frame.index).gt(0)
        | frame["forward_breakout_bucket"].astype(str).isin({"fragile_candidate", "blocked_candidate"})
        | _safe_numeric(frame.get("first_30m_flag"), frame.index).gt(0)
        | _safe_numeric(frame.get("tech_led_narrow_flag"), frame.index).gt(0)
    )
    return pd.Series(
        np.select(
            [risk.le(0.40) & ~hard_fail, risk.gt(0.40) & risk.le(0.52) & ~hard_fail],
            ["pass", "soft_pass"],
            default="fail",
        ),
        index=frame.index,
    )


def _build_prediction_frame(candidates: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(candidates, PREDICTION_COLUMNS)
    frame["feature_set_version"] = FEATURE_SET_VERSION
    frame["forward_only_flag"] = frame["forward_only_flag"].fillna(True).astype(bool)
    frame["theme_prior_v1"] = frame["symbol"].map(_theme_prior).astype(float)
    frame["data_leadership_gate_v1"] = (
        frame["market_breadth_state"].astype(str).eq("broad")
        & frame["sector_leadership_state"].astype(str).isin({"broad_led", "broad_risk_on"})
        & ~_safe_numeric(frame.get("tech_led_narrow_flag"), frame.index).gt(0)
    ).astype(int)
    frame["risk_gate_v1"] = _risk_gate(frame)
    insufficient = (
        ~frame["forward_only_flag"].astype(bool)
        | _raw_numeric(frame.get("context_quality_score"), frame.index).isna()
        | _raw_numeric(frame.get("risk_pressure_score"), frame.index).isna()
        | _raw_numeric(frame.get("forward_persistence_score"), frame.index).isna()
    )
    suppressed = (
        frame["risk_gate_v1"].eq("fail")
        | frame["market_breadth_state"].astype(str).eq("narrow")
        | _safe_numeric(frame.get("tech_led_narrow_flag"), frame.index).gt(0)
    )
    persistence_core = (
        frame["data_leadership_gate_v1"].eq(1)
        & frame["risk_gate_v1"].isin({"pass", "soft_pass"})
        & frame["theme_prior_v1"].ge(1.0)
        & _safe_numeric(frame.get("forward_persistence_score"), frame.index).ge(0.66)
        & frame["forward_breakout_bucket"].astype(str).isin({"high_quality", "mixed_quality"})
    )
    qualified_watchlist = (
        frame["data_leadership_gate_v1"].eq(1)
        & frame["risk_gate_v1"].isin({"pass", "soft_pass"})
        & _safe_numeric(frame.get("forward_persistence_score"), frame.index).ge(0.58)
        & frame["forward_breakout_bucket"].astype(str).isin({"high_quality", "mixed_quality"})
        & ~persistence_core
    )
    tactical = (
        _safe_numeric(frame.get("forward_breakout_score"), frame.index).ge(0.68)
        & ~frame["risk_gate_v1"].eq("fail")
        & frame["data_leadership_gate_v1"].eq(0)
    )
    frame["persistence_universe_bucket"] = np.select(
        [insufficient, suppressed, persistence_core, qualified_watchlist, tactical],
        ["insufficient_data", "suppressed_crowding_risk", "persistence_core", "qualified_watchlist", "tactical_breakout_only"],
        default="reject",
    )
    columns = [
        *PREDICTION_COLUMNS,
        "theme_prior_v1",
        "data_leadership_gate_v1",
        "risk_gate_v1",
        "persistence_universe_bucket",
    ]
    return frame[columns].sort_values(["entry_ts", "trade_id"], kind="stable").reset_index(drop=True)


def _lifecycle_observed(frame: pd.DataFrame) -> pd.Series:
    observed_cols = [
        "event_count",
        "persistence_depth",
        "add_depth",
        "scale_depth",
        "source_linked_flag",
        "invalidated_flag",
        "persistence_confirmed_flag",
        "add_confirmed_flag",
        "scale_up_flag",
        "persistence_duration_minutes",
        "lineage_quality",
    ]
    existing = [c for c in observed_cols if c in frame.columns]
    if not existing:
        return pd.Series(False, index=frame.index)
    return frame[existing].notna().any(axis=1)


def _target_reason(row: pd.Series) -> str:
    for column, reason in (
        ("persistence_confirmed_flag", "persistence_confirmed"),
        ("add_confirmed_flag", "add_confirmed"),
        ("scale_up_flag", "scale_up"),
        ("persistence_depth", "persistence_depth"),
        ("add_depth", "add_depth"),
        ("scale_depth", "scale_depth"),
    ):
        value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").fillna(0).iloc[0]
        if float(value) > 0:
            return reason
    return "no_stateful_persistence"


def _build_labels(joined: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(joined, ["trade_id", "current_split", *[c for c in LIFECYCLE_COLUMNS if c != "raw_trade_id"]])
    observed = _lifecycle_observed(frame)
    event_count = _safe_numeric(frame.get("event_count"), frame.index)
    duration = _safe_numeric(frame.get("persistence_duration_minutes"), frame.index)
    persistence_depth = _safe_numeric(frame.get("persistence_depth"), frame.index)
    add_depth = _safe_numeric(frame.get("add_depth"), frame.index)
    scale_depth = _safe_numeric(frame.get("scale_depth"), frame.index)
    invalidated = _safe_numeric(frame.get("invalidated_flag"), frame.index).gt(0)
    fragile = _safe_numeric(frame.get("fragile_transition_flag"), frame.index).gt(0)
    immediate_invalidation = invalidated & event_count.le(1) & duration.le(0) & persistence_depth.eq(0) & add_depth.eq(0) & scale_depth.eq(0)
    positive_state = (
        _safe_numeric(frame.get("persistence_confirmed_flag"), frame.index).gt(0)
        | _safe_numeric(frame.get("add_confirmed_flag"), frame.index).gt(0)
        | _safe_numeric(frame.get("scale_up_flag"), frame.index).gt(0)
        | persistence_depth.ge(1)
        | add_depth.ge(1)
        | scale_depth.ge(1)
    )
    quality_ok = ~fragile & ~invalidated
    target = observed & positive_state & quality_ok & ~immediate_invalidation
    source_linked = _safe_numeric(frame.get("source_linked_flag"), frame.index).gt(0)
    lineage = frame["lineage_quality"].astype(str)

    labels = frame[["trade_id", "current_split", *[c for c in LIFECYCLE_COLUMNS if c not in {"raw_trade_id", "evaluation_scope"}]]].copy()
    labels["lifecycle_coverage_flag"] = observed.astype(int)
    labels["stateful_persistence_target_v1"] = pd.Series(np.where(observed, target.astype(int), np.nan), index=frame.index)
    labels["target_reason"] = frame.apply(_target_reason, axis=1)
    labels.loc[~observed, "target_reason"] = "coverage_missing"
    labels.loc[immediate_invalidation, "target_reason"] = "immediate_invalidation"
    labels["label_eligible_flag"] = (observed & ~immediate_invalidation).astype(int)
    labels["exclusion_reason"] = ""
    labels.loc[~observed, "exclusion_reason"] = "coverage_missing"
    labels.loc[immediate_invalidation, "exclusion_reason"] = "immediate_invalidation"
    labels["target_confidence"] = np.select(
        [~observed, source_linked | lineage.eq("source_linked"), positive_state & lineage.eq("replay_derived")],
        ["low", "high", "medium"],
        default="low",
    )
    return labels.sort_values(["trade_id"], kind="stable").reset_index(drop=True)


def _leakage_audit(prediction_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for column in prediction_frame.columns:
        rows.append(
            {
                "feature_name": column,
                "source_frame": "persistence_universe_prediction_frame",
                "temporal_classification": "entry_time",
                "allowed_for_prediction": True,
                "leakage_reason": "",
            }
        )
    blocked = {
        "realized_R": ("outcome", "Realized outcome remains evaluation-only."),
        "event_count": ("post_entry", "Lifecycle events accumulate after entry."),
        "persistence_depth": ("lifecycle_outcome", "Depth is target evidence."),
        "add_depth": ("lifecycle_outcome", "Depth is target evidence."),
        "scale_depth": ("lifecycle_outcome", "Depth is target evidence."),
        "invalidated_flag": ("lifecycle_outcome", "Invalidation is future lifecycle evidence."),
        "fragile_transition_flag": ("lifecycle_outcome", "Fragility is future lifecycle evidence."),
        "add_confirmed_flag": ("lifecycle_outcome", "Future target evidence."),
        "scale_up_flag": ("lifecycle_outcome", "Future target evidence."),
        "persistence_confirmed_flag": ("lifecycle_outcome", "Future target evidence."),
        "persistence_duration_minutes": ("lifecycle_outcome", "Duration is known after entry."),
        "stateful_persistence_target_v1": ("outcome", "Target label is evaluation-only."),
        "target_reason": ("outcome", "Label explanation is evaluation-only."),
        "label_eligible_flag": ("outcome", "Eligibility is label metadata."),
        "lifecycle_coverage_flag": ("post_entry", "Coverage is lifecycle-side metadata."),
        "target_confidence": ("post_entry", "Confidence is lifecycle-side metadata."),
        "exclusion_reason": ("outcome", "Exclusion reason is label metadata."),
    }
    for feature_name, (classification, reason) in blocked.items():
        rows.append(
            {
                "feature_name": feature_name,
                "source_frame": "stateful_persistence_labels",
                "temporal_classification": classification,
                "allowed_for_prediction": False,
                "leakage_reason": reason,
            }
        )
    return pd.DataFrame(rows).sort_values(["allowed_for_prediction", "feature_name"], ascending=[False, True], kind="stable").reset_index(drop=True)


def _bucket_audit(evaluation: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scopes = {
        "full_period": evaluation.copy(),
        "anchored_oos": evaluation[evaluation["current_split"].astype(str).eq("anchored_oos")].copy(),
    }
    for scope, scoped in scopes.items():
        if scoped.empty:
            continue
        for bucket, cut in scoped.groupby("persistence_universe_bucket", dropna=False):
            eligible = cut[_safe_numeric(cut.get("label_eligible_flag"), cut.index).gt(0)].copy()
            target = _raw_numeric(eligible.get("stateful_persistence_target_v1"), eligible.index)
            realized = _raw_numeric(eligible.get("realized_R"), eligible.index)
            rows.append(
                {
                    "evaluation_scope": scope,
                    "persistence_universe_bucket": str(bucket),
                    "trade_count": int(len(cut)),
                    "labeled_count": int(len(eligible)),
                    "target_positive_count": int(target.fillna(0).sum()) if not eligible.empty else 0,
                    "target_rate": round(float(target.mean()), 6) if target.notna().any() else 0.0,
                    "expectancy_realized_R": round(float(realized.mean()), 6) if realized.notna().any() else 0.0,
                    "coverage_missing_count": int((_safe_numeric(cut.get("lifecycle_coverage_flag"), cut.index) == 0).sum()),
                }
            )
    return pd.DataFrame(rows)


def _sample_adequacy(evaluation: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, scoped in {
        "full_period": evaluation.copy(),
        "anchored_oos": evaluation[evaluation["current_split"].astype(str).eq("anchored_oos")].copy(),
    }.items():
        counts = scoped["persistence_universe_bucket"].astype(str).value_counts()
        total = int(len(scoped))
        min_bucket = int(counts.min()) if not counts.empty else 0
        hard_gate = total >= MIN_TOTAL_BUCKETED and min_bucket >= MIN_BUCKET_COUNT
        rows.append(
            {
                "evaluation_scope": scope,
                "total_bucketed": total,
                "min_bucket_count": min_bucket,
                "gate_status": "hard_gate" if hard_gate else "diagnostic_only",
                "gate_reason": "sufficient_bucket_counts" if hard_gate else "insufficient_bucket_counts",
                "hard_gate_reactivation_threshold": "min_30_per_bucket_and_min_120_total_bucketed",
            }
        )
    return pd.DataFrame(rows)


def _decision(prediction: pd.DataFrame, labels: pd.DataFrame, bucket_audit: pd.DataFrame, sample_audit: pd.DataFrame) -> pd.DataFrame:
    boundary_clean = not any(column in prediction.columns for column in FORBIDDEN_PREDICTION_COLUMNS)
    labels_present = not labels.empty
    coverage_present = int(_safe_numeric(labels.get("lifecycle_coverage_flag"), labels.index).sum()) > 0 if not labels.empty else False
    sample_present = not sample_audit.empty

    full = bucket_audit[bucket_audit["evaluation_scope"].astype(str).eq("full_period")].copy()
    core = full[full["persistence_universe_bucket"].astype(str).eq("persistence_core")]
    generic_labeled = int(full["labeled_count"].sum()) if not full.empty else 0
    core_labeled = int(core.iloc[0]["labeled_count"]) if not core.empty else 0
    core_rate = float(core.iloc[0]["target_rate"]) if not core.empty else 0.0
    overall_positive = int(full["target_positive_count"].sum()) if not full.empty else 0
    overall_labeled = int(full["labeled_count"].sum()) if not full.empty else 0
    overall_rate = overall_positive / overall_labeled if overall_labeled else 0.0
    anchored_gate = sample_audit[sample_audit["evaluation_scope"].astype(str).eq("anchored_oos")]
    anchored_status = str(anchored_gate.iloc[0]["gate_status"]) if not anchored_gate.empty else "diagnostic_only"
    full_gate = sample_audit[sample_audit["evaluation_scope"].astype(str).eq("full_period")]
    full_status = str(full_gate.iloc[0]["gate_status"]) if not full_gate.empty else "diagnostic_only"

    if not coverage_present:
        acceptance = "INSUFFICIENT_EVIDENCE"
    elif full_status != "hard_gate":
        acceptance = "EXPANDED_SAMPLE_REQUIRED"
    elif core_labeled > 0 and core_rate > overall_rate and anchored_status == "diagnostic_only":
        acceptance = "FULL_PERIOD_ACCEPT_ANCHORED_DIAGNOSTIC_ONLY"
    elif generic_labeled == 0:
        acceptance = "EXPANDED_SAMPLE_REQUIRED"
    else:
        acceptance = "NOT_ACCEPTED"
    task_complete = boundary_clean and labels_present and sample_present
    return pd.DataFrame(
        [
            {
                "task_376_verdict": "COMPLETE_PASS" if task_complete else "NOT_YET",
                "acceptance_decision": acceptance,
                "prediction_boundary_clean": boundary_clean,
                "labels_present": labels_present,
                "lifecycle_coverage_present": coverage_present,
                "sample_adequacy_present": sample_present,
                "full_period_gate_status": full_status,
                "anchored_oos_gate_status": anchored_status,
                "core_target_rate": round(core_rate, 6),
                "overall_target_rate": round(overall_rate, 6),
            }
        ]
    )


def build_persistence_universe_376(
    *,
    candidates_df: pd.DataFrame | None = None,
    lifecycle_df: pd.DataFrame | None = None,
    persistence_prediction_df: pd.DataFrame | None = None,
) -> PersistenceUniverse376Artifacts:
    candidates = candidates_df.copy() if candidates_df is not None else _load_csv(TASK_374_CANDIDATES_PATH)
    lifecycle = lifecycle_df.copy() if lifecycle_df is not None else _load_csv(TASK_372_LIFECYCLE_PATH)
    if persistence_prediction_df is None and TASK_375_PREDICTION_PATH.exists():
        persistence_prediction = _load_csv(TASK_375_PREDICTION_PATH)
    else:
        persistence_prediction = persistence_prediction_df

    candidates = _prepare_candidates(candidates, persistence_prediction)
    prediction = _build_prediction_frame(candidates)
    lifecycle_prepared = _prepare_lifecycle(lifecycle)
    joined = prediction.merge(
        lifecycle_prepared.rename(columns={"raw_trade_id": "trade_id"}),
        on="trade_id",
        how="left",
        suffixes=("", "_lifecycle"),
    )
    labels = _build_labels(joined)
    evaluation = prediction.merge(labels, on=["trade_id", "current_split"], how="left")
    bucket_audit = _bucket_audit(evaluation)
    leakage = _leakage_audit(prediction)
    sample_audit = _sample_adequacy(evaluation)
    decision = _decision(prediction, labels, bucket_audit, sample_audit)
    return PersistenceUniverse376Artifacts(
        persistence_universe_prediction_frame=prediction,
        stateful_persistence_labels=labels,
        persistence_universe_evaluation_panel=evaluation,
        persistence_universe_bucket_audit=bucket_audit,
        persistence_universe_leakage_audit=leakage,
        persistence_universe_sample_adequacy_audit=sample_audit,
        persistence_universe_decision=decision,
    )


def write_persistence_universe_376(
    artifacts: PersistenceUniverse376Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.persistence_universe_prediction_frame.to_csv(out_dir / "persistence_universe_prediction_frame.csv", index=False, encoding="utf-8-sig")
    artifacts.stateful_persistence_labels.to_csv(out_dir / "stateful_persistence_labels.csv", index=False, encoding="utf-8-sig")
    artifacts.persistence_universe_evaluation_panel.to_csv(out_dir / "persistence_universe_evaluation_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.persistence_universe_bucket_audit.to_csv(out_dir / "persistence_universe_bucket_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.persistence_universe_leakage_audit.to_csv(out_dir / "persistence_universe_leakage_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.persistence_universe_sample_adequacy_audit.to_csv(out_dir / "persistence_universe_sample_adequacy_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.persistence_universe_decision.to_csv(out_dir / "persistence_universe_decision.csv", index=False, encoding="utf-8-sig")
