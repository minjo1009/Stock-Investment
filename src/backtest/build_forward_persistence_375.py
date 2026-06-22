from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH
from src.backtest.build_forward_pure_breakout_374 import build_forward_pure_breakout_374


DEFAULT_OUT_DIR = Path("docs/reports/task_375_forward_persistence")
FEATURE_SET_VERSION = "task375-forward-persistence-v1"

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
    "ker",
    "volume_percentile",
    "daily_bias",
    "context_quality_score",
    "risk_pressure_score",
    "forward_breakout_score",
    "forward_breakout_bucket",
    "forward_high_quality_flag",
    "forward_weak_flag",
    "first_30m_flag",
    "tech_led_narrow_flag",
]

OUTCOME_COLUMNS = [
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
    "persistence_duration_minutes",
]

TASK_374_REPORT_DIR = Path("docs/reports/task_374_forward_pure_breakout")


@dataclass(frozen=True)
class ForwardPersistence375Artifacts:
    forward_persistence_prediction_frame: pd.DataFrame
    forward_persistence_labels: pd.DataFrame
    forward_persistence_training_frame: pd.DataFrame
    forward_persistence_evaluation_panel: pd.DataFrame
    persistence_leakage_audit: pd.DataFrame
    persistence_target_summary: pd.DataFrame


def _safe_numeric(series: pd.Series | None, index: pd.Index, default: float = 0.0) -> pd.Series:
    if series is None:
        return pd.Series(default, index=index, dtype=float)
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.fillna(default)


def _bool_flag(frame: pd.DataFrame, column: str) -> pd.Series:
    return _safe_numeric(frame[column] if column in frame.columns else None, frame.index).gt(0)


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = np.nan
    return out


def _has_lifecycle_truth(frame: pd.DataFrame) -> bool:
    truth_columns = [
        "persistence_confirmed_flag",
        "add_confirmed_flag",
        "scale_up_flag",
        "persistence_depth",
        "add_depth",
        "scale_depth",
        "event_count",
    ]
    for column in truth_columns:
        if column in frame.columns and pd.to_numeric(frame[column], errors="coerce").notna().any():
            return True
    return False


def _load_task374_report_fallback() -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    candidates_path = TASK_374_REPORT_DIR / "forward_pure_breakout_candidates.csv"
    evaluation_path = TASK_374_REPORT_DIR / "forward_breakout_evaluation_panel.csv"
    if not candidates_path.exists() or not evaluation_path.exists():
        return None, None
    candidates = pd.read_csv(candidates_path, encoding="utf-8-sig")
    evaluation = pd.read_csv(evaluation_path, encoding="utf-8-sig")
    return candidates, evaluation


def _build_prediction_frame(candidates: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(candidates, PREDICTION_COLUMNS)
    frame = frame[PREDICTION_COLUMNS].copy()
    frame["trade_id"] = frame["trade_id"].astype(str)
    frame["forward_only_flag"] = frame["forward_only_flag"].fillna(True).astype(bool)
    frame["feature_set_version"] = FEATURE_SET_VERSION
    frame["forward_persistence_score"] = (
        0.50 * _safe_numeric(frame.get("forward_breakout_score"), frame.index)
        + 0.30 * _safe_numeric(frame.get("context_quality_score"), frame.index)
        + 0.20 * (1.0 - _safe_numeric(frame.get("risk_pressure_score"), frame.index))
    ).clip(0.0, 1.0).round(6)
    frame["forward_persistence_bucket"] = np.select(
        [
            frame["forward_persistence_score"].ge(0.72) & frame["forward_breakout_bucket"].astype(str).eq("high_quality"),
            frame["forward_persistence_score"].ge(0.58),
            frame["forward_persistence_score"].lt(0.45),
        ],
        ["predicted_expandable", "watchlist", "weak_persistence"],
        default="mixed_persistence",
    )
    frame["predicted_persistence_flag"] = frame["forward_persistence_bucket"].astype(str).eq("predicted_expandable").astype(int)
    return frame.sort_values(["entry_ts", "trade_id"], kind="stable").reset_index(drop=True)


def _row_positive(row: pd.Series, column: str) -> bool:
    value = pd.to_numeric(pd.Series([row.get(column, 0)]), errors="coerce").fillna(0).iloc[0]
    return float(value) > 0.0


def _target_reason(row: pd.Series) -> str:
    if _row_positive(row, "persistence_confirmed_flag"):
        return "persistence_confirmed"
    if _row_positive(row, "add_confirmed_flag"):
        return "add_confirmed"
    if _row_positive(row, "scale_up_flag"):
        return "scale_up"
    return "no_expandable_continuation"


def _label_frame(evaluation_panel: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(evaluation_panel, ["trade_id", "current_split", *OUTCOME_COLUMNS])
    positive = (
        _bool_flag(frame, "persistence_confirmed_flag")
        | _bool_flag(frame, "add_confirmed_flag")
        | _bool_flag(frame, "scale_up_flag")
    )
    invalidated = _bool_flag(frame, "invalidated_flag")
    event_count = _safe_numeric(frame.get("event_count"), frame.index)
    duration = _safe_numeric(frame.get("persistence_duration_minutes"), frame.index)
    immediate_invalidation = invalidated & event_count.le(1) & duration.le(0)

    labels = frame[["trade_id", "current_split", *OUTCOME_COLUMNS]].copy()
    labels["trade_id"] = labels["trade_id"].astype(str)
    labels["forward_persistence_target"] = (positive & ~immediate_invalidation).astype(int)
    labels["target_reason"] = labels.apply(_target_reason, axis=1)
    labels.loc[immediate_invalidation, "target_reason"] = "immediate_invalidation"
    labels["excluded_from_training"] = immediate_invalidation.astype(int)
    labels["exclusion_reason"] = ""
    labels.loc[immediate_invalidation, "exclusion_reason"] = "immediate_invalidation"
    return labels.sort_values(["trade_id"], kind="stable").reset_index(drop=True)


def _evaluation_panel(prediction_frame: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    evaluation = prediction_frame.merge(labels, on=["trade_id", "current_split"], how="left")
    for column in ("forward_persistence_target", "excluded_from_training"):
        if column in evaluation.columns:
            evaluation[column] = _safe_numeric(evaluation[column], evaluation.index).astype(int)
    return evaluation.sort_values(["entry_ts", "trade_id"], kind="stable").reset_index(drop=True)


def _leakage_audit(prediction_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for column in prediction_frame.columns:
        rows.append(
            {
                "feature_name": column,
                "source_frame": "forward_persistence_prediction_frame",
                "temporal_classification": "entry_time",
                "allowed_for_prediction": True,
                "leakage_reason": "",
            }
        )
    blocked = {
        "realized_R": ("outcome", "Realized outcome is known only after exit."),
        "invalidated_flag": ("lifecycle_outcome", "Invalidation is a future lifecycle result."),
        "add_confirmed_flag": ("lifecycle_outcome", "Add confirmation is the future target evidence."),
        "scale_up_flag": ("lifecycle_outcome", "Scale-up confirmation is the future target evidence."),
        "persistence_confirmed_flag": ("lifecycle_outcome", "Persistence confirmation is the future target evidence."),
        "persistence_duration_minutes": ("lifecycle_outcome", "Persistence duration requires post-entry evolution."),
        "event_count": ("post_entry", "Event count accumulates after entry."),
        "forward_persistence_target": ("outcome", "Target label is evaluation-only."),
        "target_reason": ("outcome", "Target reason is evaluation-only."),
        "excluded_from_training": ("outcome", "Training exclusion is label metadata."),
        "exclusion_reason": ("outcome", "Training exclusion reason is label metadata."),
        "lineage_quality": ("post_entry", "Lineage quality belongs to lifecycle evaluation."),
    }
    for feature_name, (classification, reason) in blocked.items():
        rows.append(
            {
                "feature_name": feature_name,
                "source_frame": "forward_persistence_evaluation_panel",
                "temporal_classification": classification,
                "allowed_for_prediction": False,
                "leakage_reason": reason,
            }
        )
    return pd.DataFrame(rows).sort_values(["allowed_for_prediction", "feature_name"], ascending=[False, True], kind="stable").reset_index(drop=True)


def _summary(evaluation_panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scopes = {
        "full_period": evaluation_panel.copy(),
        "anchored_oos": evaluation_panel[evaluation_panel["current_split"].astype(str).eq("anchored_oos")].copy(),
    }
    cuts = {
        "all_forward_candidates": lambda df: df.index == df.index,
        "forward_high_quality": lambda df: df["forward_breakout_bucket"].astype(str).eq("high_quality"),
        "predicted_expandable": lambda df: df["forward_persistence_bucket"].astype(str).eq("predicted_expandable"),
        "training_rows": lambda df: _safe_numeric(df.get("excluded_from_training"), df.index).eq(0),
    }
    for scope_name, scope_df in scopes.items():
        if scope_df.empty:
            continue
        for cut_name, mask_fn in cuts.items():
            cut_df = scope_df[mask_fn(scope_df)].copy()
            target = _safe_numeric(cut_df.get("forward_persistence_target"), cut_df.index)
            realized = pd.to_numeric(cut_df.get("realized_R"), errors="coerce") if "realized_R" in cut_df.columns else pd.Series(dtype=float)
            rows.append(
                {
                    "evaluation_scope": scope_name,
                    "evaluation_cut": cut_name,
                    "trade_count": int(len(cut_df)),
                    "target_positive_count": int(target.sum()) if not cut_df.empty else 0,
                    "target_rate": round(float(target.mean()), 6) if not cut_df.empty else 0.0,
                    "expectancy_realized_R": round(float(realized.mean()), 6) if not realized.empty else 0.0,
                    "immediate_invalidation_exclusions": int(_safe_numeric(cut_df.get("excluded_from_training"), cut_df.index).sum()) if not cut_df.empty else 0,
                }
            )
    if rows:
        summary = pd.DataFrame(rows)
        full = summary[summary["evaluation_scope"].eq("full_period")]
        baseline = full[full["evaluation_cut"].eq("forward_high_quality")]
        predicted = full[full["evaluation_cut"].eq("predicted_expandable")]
        baseline_rate = float(baseline.iloc[0]["target_rate"]) if not baseline.empty else 0.0
        predicted_rate = float(predicted.iloc[0]["target_rate"]) if not predicted.empty else 0.0
        summary.loc[len(summary)] = {
            "evaluation_scope": "meta",
            "evaluation_cut": "prediction_lift",
            "trade_count": int(predicted.iloc[0]["trade_count"]) if not predicted.empty else 0,
            "target_positive_count": int(predicted.iloc[0]["target_positive_count"]) if not predicted.empty else 0,
            "target_rate": round(predicted_rate - baseline_rate, 6),
            "expectancy_realized_R": 0.0,
            "immediate_invalidation_exclusions": int(evaluation_panel["excluded_from_training"].fillna(0).sum()) if "excluded_from_training" in evaluation_panel.columns else 0,
        }
        return summary
    return pd.DataFrame(columns=["evaluation_scope", "evaluation_cut", "trade_count", "target_positive_count", "target_rate", "expectancy_realized_R", "immediate_invalidation_exclusions"])


def build_forward_persistence_375(
    *,
    db_path: str = str(DB_PATH),
    capture_batch_id: str = "task374_default",
    reuse_existing_batch: bool = False,
    prediction_candidates_df: pd.DataFrame | None = None,
    evaluation_panel_df: pd.DataFrame | None = None,
    master_df: pd.DataFrame | None = None,
    policy_pool_df: pd.DataFrame | None = None,
    shadow_log_df: pd.DataFrame | None = None,
    lifecycle_panel_df: pd.DataFrame | None = None,
) -> ForwardPersistence375Artifacts:
    if prediction_candidates_df is None or evaluation_panel_df is None:
        artifacts_374 = build_forward_pure_breakout_374(
            db_path=db_path,
            capture_batch_id=capture_batch_id,
            reuse_existing_batch=reuse_existing_batch,
            master_df=master_df,
            policy_pool_df=policy_pool_df,
            shadow_log_df=shadow_log_df,
            lifecycle_panel_df=lifecycle_panel_df,
        )
        candidates = artifacts_374.forward_pure_breakout_candidates if prediction_candidates_df is None else prediction_candidates_df
        source_evaluation = artifacts_374.forward_breakout_evaluation_panel if evaluation_panel_df is None else evaluation_panel_df
        if evaluation_panel_df is None and not _has_lifecycle_truth(source_evaluation):
            fallback_candidates, fallback_evaluation = _load_task374_report_fallback()
            if fallback_evaluation is not None and _has_lifecycle_truth(fallback_evaluation):
                source_evaluation = fallback_evaluation
                if prediction_candidates_df is None and fallback_candidates is not None:
                    candidates = fallback_candidates
    else:
        candidates = prediction_candidates_df
        source_evaluation = evaluation_panel_df

    prediction_frame = _build_prediction_frame(candidates)
    labels = _label_frame(source_evaluation)
    evaluation_panel = _evaluation_panel(prediction_frame, labels)
    training = evaluation_panel[_safe_numeric(evaluation_panel.get("excluded_from_training"), evaluation_panel.index).eq(0)].copy()
    training = training.drop(columns=[column for column in OUTCOME_COLUMNS if column in training.columns])
    leakage = _leakage_audit(prediction_frame)
    summary = _summary(evaluation_panel)

    return ForwardPersistence375Artifacts(
        forward_persistence_prediction_frame=prediction_frame,
        forward_persistence_labels=labels,
        forward_persistence_training_frame=training.reset_index(drop=True),
        forward_persistence_evaluation_panel=evaluation_panel,
        persistence_leakage_audit=leakage,
        persistence_target_summary=summary,
    )


def write_forward_persistence_375(
    artifacts: ForwardPersistence375Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.forward_persistence_prediction_frame.to_csv(out_dir / "forward_persistence_prediction_frame.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_persistence_labels.to_csv(out_dir / "forward_persistence_labels.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_persistence_training_frame.to_csv(out_dir / "forward_persistence_training_frame.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_persistence_evaluation_panel.to_csv(out_dir / "forward_persistence_evaluation_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.persistence_leakage_audit.to_csv(out_dir / "persistence_leakage_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.persistence_target_summary.to_csv(out_dir / "persistence_target_summary.csv", index=False, encoding="utf-8-sig")
