from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_intraday_signal_strengthening_339 import (
    _holdout_rows_for_subset,
    _saved_loss_missed_gain,
    _symbol_concentration_share,
)
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import (
    DB_PATH,
    DEFAULT_COST_SCENARIOS,
    INITIAL_CAPITAL,
    ROLLING_WINDOWS,
    TARGET_WINDOW_MODE,
    _apply_cost_to_r,
    _cagr_proxy,
    _current_subset_mask,
    _daily_sharpe_proxy,
    _equity_points,
    _expectancy,
    _load_entry_only_master,
    _max_drawdown_proxy,
    _rolling_label,
    _strategy_metrics,
    _trade_ratio,
    _win_rate,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_341_subset_refinement")
MIN_HOLDOUT_TRADES = 5
MAX_REFINEMENT_CANDIDATES = 3
MAX_CONDITIONS_PER_CANDIDATE = 2
SUCCESS_DECISION_MIN_POSITIVE_WINDOWS = 3

NUMERIC_WINDOW_FEATURES = [
    "price_vs_session_vwap_at_breakout",
    "breakout_hold_duration_bars",
    "breakout_bar_close_location",
    "return_next_3bars",
    "adverse_excursion_next_3bars",
    "intraday_pullback_depth_3bars",
    "volume_persistence_3bars",
    "breakout_window_volume_surge",
    "relative_volume_percentile",
    "multi_bar_follow_through_3bars",
]
CATEGORICAL_WINDOW_FEATURES = [
    "vwap_response",
    "breakout_response",
    "sector_group",
    "scenario_family",
    "breakout_subtype",
]
QUALITY_FEATURES = NUMERIC_WINDOW_FEATURES + CATEGORICAL_WINDOW_FEATURES


@dataclass(frozen=True)
class ConditionSpec:
    feature_name: str
    operator: str
    threshold_source: str
    threshold_value: Any
    preferred_direction: str
    family: str
    note: str


def _window_group(expectancy_delta: float) -> str:
    return "success_window" if float(expectancy_delta) > 0 else "failure_window"


def _threshold_value(train_df: pd.DataFrame, spec: ConditionSpec) -> Any:
    if spec.threshold_source == "fixed":
        return spec.threshold_value
    series = pd.to_numeric(train_df[spec.feature_name], errors="coerce")
    if series.notna().empty or not series.notna().any():
        return math.nan
    if spec.threshold_source == "train_median":
        return float(series.median())
    if spec.threshold_source == "train_upper_half":
        return float(series.quantile(0.5))
    raise ValueError(f"Unsupported threshold source: {spec.threshold_source}")


def _condition_label(spec: ConditionSpec, threshold: Any) -> str:
    if spec.threshold_source == "fixed":
        return f"{spec.feature_name} {spec.operator} {spec.threshold_value}"
    if pd.isna(threshold):
        return f"{spec.feature_name} {spec.operator} train_threshold_unavailable"
    return f"{spec.feature_name} {spec.operator} {round(float(threshold), 6)}"


def _apply_condition(df: pd.DataFrame, train_df: pd.DataFrame, spec: ConditionSpec) -> tuple[pd.Series, Any]:
    threshold = _threshold_value(train_df, spec)
    series = df[spec.feature_name]
    if spec.operator == "==":
        mask = series.astype(str) == str(spec.threshold_value)
    else:
        numeric = pd.to_numeric(series, errors="coerce")
        if pd.isna(threshold):
            mask = pd.Series(False, index=df.index)
        elif spec.operator == ">":
            mask = numeric > float(threshold)
        elif spec.operator == ">=":
            mask = numeric >= float(threshold)
        elif spec.operator == "<":
            mask = numeric < float(threshold)
        elif spec.operator == "<=":
            mask = numeric <= float(threshold)
        else:
            raise ValueError(f"Unsupported operator: {spec.operator}")
    return mask.fillna(False), threshold


def _build_base_subset_master() -> pd.DataFrame:
    master = _load_entry_only_master(DB_PATH)
    master = master[master["window_mode"] == TARGET_WINDOW_MODE].copy()
    master = master[_current_subset_mask(master)].copy().reset_index(drop=True)
    return master


def _rolling_subset_windows(master_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []
    for window in ROLLING_WINDOWS:
        train_mask = (master_df["entry_ts"] >= pd.Timestamp(window.train_start)) & (master_df["entry_ts"] <= pd.Timestamp(window.train_end))
        oos_mask = (master_df["entry_ts"] >= pd.Timestamp(window.oos_start)) & (master_df["entry_ts"] <= pd.Timestamp(window.oos_end))
        train_df = master_df[train_mask].copy()
        oos_df = master_df[oos_mask].copy()
        labeled_oos = _rolling_label(train_df, oos_df) if not train_df.empty and not oos_df.empty else oos_df.copy()
        subset_oos = labeled_oos[_current_subset_mask(labeled_oos)].copy()
        baseline_expectancy = _expectancy(oos_df)
        subset_expectancy = _expectancy(subset_oos)
        expectancy_delta = float(subset_expectancy - baseline_expectancy) if not math.isnan(subset_expectancy) and not math.isnan(baseline_expectancy) else math.nan
        group = _window_group(expectancy_delta if not math.isnan(expectancy_delta) else 0.0)
        subset_oos["window_id"] = window.window_id
        subset_oos["window_group"] = group
        subset_oos["window_expectancy_delta"] = expectancy_delta
        rows.append(subset_oos)
        summaries.append(
            {
                "window_id": window.window_id,
                "window_group": group,
                "subset_trade_count": int(len(subset_oos)),
                "baseline_expectancy": round(baseline_expectancy, 6) if not math.isnan(baseline_expectancy) else math.nan,
                "subset_expectancy": round(subset_expectancy, 6) if not math.isnan(subset_expectancy) else math.nan,
                "expectancy_delta": round(expectancy_delta, 6) if not math.isnan(expectancy_delta) else math.nan,
            }
        )
    window_trades = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return window_trades, pd.DataFrame(summaries)


def _window_comparison(window_subset_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    success_df = window_subset_df[window_subset_df["window_group"] == "success_window"].copy()
    failure_df = window_subset_df[window_subset_df["window_group"] == "failure_window"].copy()
    for feature in NUMERIC_WINDOW_FEATURES:
        success_vals = pd.to_numeric(success_df.get(feature), errors="coerce")
        failure_vals = pd.to_numeric(failure_df.get(feature), errors="coerce")
        for group_name, scoped, other in (
            ("success_window", success_vals, failure_vals),
            ("failure_window", failure_vals, success_vals),
        ):
            mean_value = float(scoped.mean()) if scoped.notna().any() else math.nan
            median_value = float(scoped.median()) if scoped.notna().any() else math.nan
            delta = mean_value - float(other.mean()) if scoped.notna().any() and other.notna().any() else math.nan
            rows.append(
                {
                    "window_id": "aggregate",
                    "window_group": group_name,
                    "feature_name": feature,
                    "group_mean": round(mean_value, 6) if not math.isnan(mean_value) else math.nan,
                    "group_median": round(median_value, 6) if not math.isnan(median_value) else math.nan,
                    "group_share_if_binary": math.nan,
                    "delta_vs_other_group": round(delta, 6) if not math.isnan(delta) else math.nan,
                    "trade_count": int(scoped.notna().sum()),
                }
            )
    for feature in CATEGORICAL_WINDOW_FEATURES:
        categories = sorted(window_subset_df[feature].astype(str).dropna().unique().tolist())
        for category in categories:
            success_share = float((success_df[feature].astype(str) == category).mean()) if not success_df.empty else math.nan
            failure_share = float((failure_df[feature].astype(str) == category).mean()) if not failure_df.empty else math.nan
            for group_name, share_value, other_share, scoped_df in (
                ("success_window", success_share, failure_share, success_df),
                ("failure_window", failure_share, success_share, failure_df),
            ):
                rows.append(
                    {
                        "window_id": "aggregate",
                        "window_group": group_name,
                        "feature_name": f"{feature}={category}",
                        "group_mean": math.nan,
                        "group_median": math.nan,
                        "group_share_if_binary": round(share_value, 6) if not math.isnan(share_value) else math.nan,
                        "delta_vs_other_group": round(share_value - other_share, 6) if not math.isnan(share_value) and not math.isnan(other_share) else math.nan,
                        "trade_count": int(len(scoped_df)),
                    }
                )
    return pd.DataFrame(rows)


def _subset_quality_decomposition(base_subset_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    comparisons = {
        "winner_vs_loser": (
            base_subset_df[pd.to_numeric(base_subset_df["realized_R"], errors="coerce") > 0].copy(),
            base_subset_df[pd.to_numeric(base_subset_df["realized_R"], errors="coerce") <= 0].copy(),
        ),
    }
    for comparison_scope, (winner_df, loser_df) in comparisons.items():
        for feature in NUMERIC_WINDOW_FEATURES:
            winner_vals = pd.to_numeric(winner_df.get(feature), errors="coerce")
            loser_vals = pd.to_numeric(loser_df.get(feature), errors="coerce")
            rows.append(
                {
                    "comparison_scope": comparison_scope,
                    "feature_name": feature,
                    "bucket_or_stat": "mean",
                    "winner_value": round(float(winner_vals.mean()), 6) if winner_vals.notna().any() else math.nan,
                    "loser_value": round(float(loser_vals.mean()), 6) if loser_vals.notna().any() else math.nan,
                    "delta": round(float(winner_vals.mean() - loser_vals.mean()), 6) if winner_vals.notna().any() and loser_vals.notna().any() else math.nan,
                    "trade_count_winner": int(winner_vals.notna().sum()),
                    "trade_count_loser": int(loser_vals.notna().sum()),
                }
            )
            rows.append(
                {
                    "comparison_scope": comparison_scope,
                    "feature_name": feature,
                    "bucket_or_stat": "median",
                    "winner_value": round(float(winner_vals.median()), 6) if winner_vals.notna().any() else math.nan,
                    "loser_value": round(float(loser_vals.median()), 6) if loser_vals.notna().any() else math.nan,
                    "delta": round(float(winner_vals.median() - loser_vals.median()), 6) if winner_vals.notna().any() and loser_vals.notna().any() else math.nan,
                    "trade_count_winner": int(winner_vals.notna().sum()),
                    "trade_count_loser": int(loser_vals.notna().sum()),
                }
            )
        for feature in CATEGORICAL_WINDOW_FEATURES:
            categories = sorted(base_subset_df[feature].astype(str).dropna().unique().tolist())
            for category in categories:
                winner_share = float((winner_df[feature].astype(str) == category).mean()) if not winner_df.empty else math.nan
                loser_share = float((loser_df[feature].astype(str) == category).mean()) if not loser_df.empty else math.nan
                rows.append(
                    {
                        "comparison_scope": comparison_scope,
                        "feature_name": feature,
                        "bucket_or_stat": category,
                        "winner_value": round(winner_share, 6) if not math.isnan(winner_share) else math.nan,
                        "loser_value": round(loser_share, 6) if not math.isnan(loser_share) else math.nan,
                        "delta": round(winner_share - loser_share, 6) if not math.isnan(winner_share) and not math.isnan(loser_share) else math.nan,
                        "trade_count_winner": int(len(winner_df)),
                        "trade_count_loser": int(len(loser_df)),
                    }
                )
    return pd.DataFrame(rows)


def _condition_specs() -> dict[str, list[ConditionSpec]]:
    return {
        "candidate_A": [
            ConditionSpec("vwap_response", "==", "fixed", "vwap_hold", "higher", "vwap", "Require intraday VWAP hold state."),
            ConditionSpec("price_vs_session_vwap_at_breakout", ">", "fixed", 0.0, "higher", "vwap", "Require breakout price to stay above session VWAP."),
            ConditionSpec("breakout_response", "==", "fixed", "breakout_hold", "higher", "hold", "Require breakout bar to close in hold state."),
            ConditionSpec("breakout_bar_close_location", ">=", "train_median", None, "higher", "hold", "Require breakout close location in upper half of train distribution."),
        ],
        "candidate_B": [
            ConditionSpec("breakout_response", "==", "fixed", "breakout_hold", "higher", "hold", "Require breakout hold response."),
            ConditionSpec("breakout_bar_close_location", ">=", "train_median", None, "higher", "hold", "Require stronger breakout close location."),
            ConditionSpec("adverse_excursion_next_3bars", "<=", "train_median", None, "lower", "adverse_excursion", "Require low early adverse excursion when available."),
            ConditionSpec("intraday_pullback_depth_3bars", "<=", "train_median", None, "lower", "adverse_excursion", "Require shallow intraday pullback depth when available."),
        ],
        "candidate_C": [
            ConditionSpec("volume_persistence_3bars", ">=", "train_median", None, "higher", "volume_persistence", "Require strong post-break volume persistence when available."),
            ConditionSpec("breakout_window_volume_surge", ">=", "train_median", None, "higher", "volume_surge", "Require breakout window volume above train median."),
            ConditionSpec("relative_volume_percentile", ">=", "train_median", None, "higher", "volume_surge", "Require relative volume percentile above train median."),
        ],
    }


def _binary_condition_summary(
    window_subset_df: pd.DataFrame,
    base_subset_df: pd.DataFrame,
    anchored_subset_df: pd.DataFrame,
    current_train_df: pd.DataFrame,
    spec: ConditionSpec,
) -> dict[str, Any]:
    success_df = window_subset_df[window_subset_df["window_group"] == "success_window"].copy()
    failure_df = window_subset_df[window_subset_df["window_group"] == "failure_window"].copy()
    winner_df = base_subset_df[pd.to_numeric(base_subset_df["realized_R"], errors="coerce") > 0].copy()
    loser_df = base_subset_df[pd.to_numeric(base_subset_df["realized_R"], errors="coerce") <= 0].copy()
    success_mask, threshold = _apply_condition(success_df, current_train_df, spec)
    failure_mask, _ = _apply_condition(failure_df, current_train_df, spec)
    winner_mask, _ = _apply_condition(winner_df, current_train_df, spec)
    loser_mask, _ = _apply_condition(loser_df, current_train_df, spec)
    anchored_mask, _ = _apply_condition(anchored_subset_df, current_train_df, spec)
    success_share = float(success_mask.mean()) if len(success_mask) else math.nan
    failure_share = float(failure_mask.mean()) if len(failure_mask) else math.nan
    winner_share = float(winner_mask.mean()) if len(winner_mask) else math.nan
    loser_share = float(loser_mask.mean()) if len(loser_mask) else math.nan
    anchored_cond = anchored_subset_df[anchored_mask].copy()
    anchored_base_exp = _expectancy(anchored_subset_df)
    anchored_cond_exp = _expectancy(anchored_cond)
    anchored_delta = anchored_cond_exp - anchored_base_exp if not math.isnan(anchored_cond_exp) and not math.isnan(anchored_base_exp) else math.nan
    return {
        "spec": spec,
        "threshold": threshold,
        "success_delta": success_share - failure_share if not math.isnan(success_share) and not math.isnan(failure_share) else math.nan,
        "winner_delta": winner_share - loser_share if not math.isnan(winner_share) and not math.isnan(loser_share) else math.nan,
        "anchored_expectancy_delta": anchored_delta,
        "anchored_trade_count": int(len(anchored_cond)),
        "condition_text": _condition_label(spec, threshold),
    }


def _signed_alignment(result: dict[str, Any]) -> bool:
    success_delta = float(result["success_delta"]) if not pd.isna(result["success_delta"]) else math.nan
    winner_delta = float(result["winner_delta"]) if not pd.isna(result["winner_delta"]) else math.nan
    anchored_delta = float(result["anchored_expectancy_delta"]) if not pd.isna(result["anchored_expectancy_delta"]) else math.nan
    if math.isnan(success_delta) or math.isnan(winner_delta):
        return False
    if success_delta == 0 or winner_delta == 0:
        return False
    if np.sign(success_delta) != np.sign(winner_delta):
        return False
    if not math.isnan(anchored_delta) and anchored_delta != 0 and np.sign(anchored_delta) != np.sign(success_delta):
        return False
    return True


def _build_refinement_candidates(
    window_subset_df: pd.DataFrame,
    base_subset_df: pd.DataFrame,
    current_train_df: pd.DataFrame,
) -> pd.DataFrame:
    anchored_subset_df = base_subset_df[base_subset_df["current_split"] == "anchored_oos"].copy()
    rows = []
    specs_by_candidate = _condition_specs()
    for candidate_id, specs in specs_by_candidate.items():
        evaluations = [_binary_condition_summary(window_subset_df, base_subset_df, anchored_subset_df, current_train_df, spec) for spec in specs]
        eligible = [item for item in evaluations if _signed_alignment(item)]
        eligible.sort(
            key=lambda item: (
                abs(float(item["success_delta"])) if not pd.isna(item["success_delta"]) else -1.0,
                abs(float(item["winner_delta"])) if not pd.isna(item["winner_delta"]) else -1.0,
                float(item["anchored_trade_count"]),
            ),
            reverse=True,
        )
        selected = eligible[:MAX_CONDITIONS_PER_CANDIDATE]
        if not selected:
            selected = evaluations[:1]
        rows.append(
            {
                "candidate_id": candidate_id,
                "base_subset_definition": "window_mode=entry_only AND atr_regime=high_atr AND contraction_regime=vol_expanding",
                "refinement_conditions": " AND ".join(item["condition_text"] for item in selected),
                "condition_source": "; ".join(
                    f"{item['spec'].feature_name}|success_delta={round(float(item['success_delta']), 6) if not pd.isna(item['success_delta']) else 'nan'}|winner_delta={round(float(item['winner_delta']), 6) if not pd.isna(item['winner_delta']) else 'nan'}|anchored_delta={round(float(item['anchored_expectancy_delta']), 6) if not pd.isna(item['anchored_expectancy_delta']) else 'nan'}"
                    for item in selected
                ),
                "train_threshold_source": "; ".join(f"{item['spec'].feature_name}:{item['spec'].threshold_source}" for item in selected),
                "live_eligible": True,
                "interpretability_note": " ".join(item["spec"].note for item in selected),
            }
        )
    return pd.DataFrame(rows).head(MAX_REFINEMENT_CANDIDATES)


def _conditions_for_candidate(candidate_row: pd.Series) -> list[ConditionSpec]:
    specs = _condition_specs()[str(candidate_row["candidate_id"])]
    selected_texts = {token.strip() for token in str(candidate_row["refinement_conditions"]).split(" AND ") if token.strip()}
    resolved: list[ConditionSpec] = []
    train_stub = pd.DataFrame({spec.feature_name: [0.0] for spec in specs if spec.threshold_source != "fixed"})
    for spec in specs:
        threshold = spec.threshold_value if spec.threshold_source == "fixed" else 0.0
        text = _condition_label(spec, threshold)
        prefix = text.split(" train_threshold_unavailable")[0]
        if any(item.startswith(prefix.split(" ")[0]) and item.split(" ")[1] == spec.operator for item in selected_texts):
            resolved.append(spec)
    if resolved:
        return resolved[:MAX_CONDITIONS_PER_CANDIDATE]
    return specs[:1]


def _apply_refinement(df: pd.DataFrame, train_df: pd.DataFrame, condition_specs: list[ConditionSpec]) -> tuple[pd.DataFrame, list[str]]:
    scoped = df.copy()
    labels: list[str] = []
    for spec in condition_specs:
        mask, threshold = _apply_condition(scoped, train_df, spec)
        labels.append(_condition_label(spec, threshold))
        scoped = scoped[mask].copy()
    return scoped, labels


def _baseline_scope_for_holdout(master_df: pd.DataFrame) -> pd.DataFrame:
    scoped = master_df.copy()
    scoped["split"] = scoped["current_split"]
    scoped["window_mode"] = TARGET_WINDOW_MODE
    return scoped


def _refined_candidate_metrics(
    base_subset_df: pd.DataFrame,
    candidate_row: pd.Series,
    current_train_df: pd.DataFrame,
) -> dict[str, Any]:
    condition_specs = _conditions_for_candidate(candidate_row)
    refined_all, labels = _apply_refinement(base_subset_df, current_train_df, condition_specs)
    anchored_base = base_subset_df[base_subset_df["current_split"] == "anchored_oos"].copy()
    anchored_refined = refined_all[refined_all["current_split"] == "anchored_oos"].copy()
    saved_loss, missed_gain = _saved_loss_missed_gain(anchored_base, anchored_refined)
    holdout_input = _baseline_scope_for_holdout(base_subset_df)
    holdout_subset = _baseline_scope_for_holdout(refined_all)
    holdout_df = _holdout_rows_for_subset(holdout_input, holdout_subset, str(candidate_row["candidate_id"]))
    ok_holdouts = holdout_df[holdout_df["status"] == "ok"].copy()
    holdout_mean_lift = float(pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce").mean()) if not ok_holdouts.empty else math.nan
    holdout_positive_share = float((pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce") > 0).mean()) if not ok_holdouts.empty else 0.0
    symbol_share = _symbol_concentration_share(anchored_refined)
    rolling_rows = []
    positive_windows = 0
    converted_failures = 0
    for window in ROLLING_WINDOWS:
        train_mask = (base_subset_df["entry_ts"] >= pd.Timestamp(window.train_start)) & (base_subset_df["entry_ts"] <= pd.Timestamp(window.train_end))
        oos_mask = (base_subset_df["entry_ts"] >= pd.Timestamp(window.oos_start)) & (base_subset_df["entry_ts"] <= pd.Timestamp(window.oos_end))
        train_df = base_subset_df[train_mask].copy()
        oos_df = base_subset_df[oos_mask].copy()
        refined_oos, _ = _apply_refinement(oos_df, train_df, condition_specs)
        base_expectancy = _expectancy(oos_df)
        refined_expectancy = _expectancy(refined_oos)
        delta = refined_expectancy - base_expectancy if not math.isnan(refined_expectancy) and not math.isnan(base_expectancy) else math.nan
        positive = bool(not math.isnan(refined_expectancy) and refined_expectancy > 0)
        positive_windows += int(positive)
        if window.window_id in {"window_1", "window_2"} and positive:
            converted_failures += 1
        rolling_rows.append(
            {
                "candidate_id": str(candidate_row["candidate_id"]),
                "window_id": window.window_id,
                "rolling_expectancy": round(refined_expectancy, 6) if not math.isnan(refined_expectancy) else math.nan,
                "rolling_lift_vs_base_subset": round(delta, 6) if not math.isnan(delta) else math.nan,
                "rolling_trade_count": int(len(refined_oos)),
            }
        )
    return {
        "candidate_id": str(candidate_row["candidate_id"]),
        "refinement_conditions": " AND ".join(labels),
        "anchored_oos_expectancy": round(_expectancy(anchored_refined), 6) if not anchored_refined.empty else math.nan,
        "anchored_oos_expectancy_delta_vs_base_subset": round(_expectancy(anchored_refined) - _expectancy(anchored_base), 6) if not anchored_refined.empty else math.nan,
        "saved_loss": round(saved_loss, 6),
        "missed_gain": round(missed_gain, 6),
        "trade_count": int(len(anchored_refined)),
        "holdout_mean_lift": round(holdout_mean_lift, 6) if not math.isnan(holdout_mean_lift) else math.nan,
        "holdout_positive_share": round(holdout_positive_share, 6),
        "symbol_concentration_share": round(symbol_share, 6) if not math.isnan(symbol_share) else math.nan,
        "rolling_positive_window_count": int(positive_windows),
        "converted_failure_windows": int(converted_failures),
        "validation_status": "ok" if len(anchored_refined) > 0 else "insufficient_sample",
        "rolling_details": " | ".join(
            f"{row['window_id']}:{row['rolling_expectancy']}:{row['rolling_trade_count']}" for row in rolling_rows
        ),
        "rolling_rows": rolling_rows,
        "refined_df": refined_all,
    }


def _refined_subset_validation(base_subset_df: pd.DataFrame, candidates_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    current_train_df = base_subset_df[base_subset_df["current_split"] == "train"].copy()
    rows = []
    refined_map: dict[str, pd.DataFrame] = {}
    base_anchored = base_subset_df[base_subset_df["current_split"] == "anchored_oos"].copy()
    base_holdout = _holdout_rows_for_subset(_baseline_scope_for_holdout(base_subset_df), _baseline_scope_for_holdout(base_subset_df), "base_subset")
    base_ok_holdouts = base_holdout[base_holdout["status"] == "ok"].copy()
    rows.append(
        {
            "candidate_id": "base_subset",
            "refinement_conditions": "",
            "anchored_oos_expectancy": round(_expectancy(base_anchored), 6),
            "anchored_oos_expectancy_delta_vs_base_subset": 0.0,
            "saved_loss": 0.0,
            "missed_gain": 0.0,
            "trade_count": int(len(base_anchored)),
            "holdout_mean_lift": round(float(pd.to_numeric(base_ok_holdouts["lift_vs_baseline"], errors="coerce").mean()), 6) if not base_ok_holdouts.empty else math.nan,
            "holdout_positive_share": round(float((pd.to_numeric(base_ok_holdouts["lift_vs_baseline"], errors="coerce") > 0).mean()), 6) if not base_ok_holdouts.empty else 0.0,
            "symbol_concentration_share": round(_symbol_concentration_share(base_anchored), 6),
            "rolling_positive_window_count": int(sum(1 for w in ROLLING_WINDOWS if not math.isnan(_expectancy(base_subset_df[(base_subset_df["entry_ts"] >= pd.Timestamp(w.oos_start)) & (base_subset_df["entry_ts"] <= pd.Timestamp(w.oos_end))])) and _expectancy(base_subset_df[(base_subset_df["entry_ts"] >= pd.Timestamp(w.oos_start)) & (base_subset_df["entry_ts"] <= pd.Timestamp(w.oos_end))]) > 0)),
            "converted_failure_windows": 0,
            "validation_status": "ok",
            "rolling_details": "",
        }
    )
    refined_map["base_subset"] = base_subset_df.copy()
    for _, candidate_row in candidates_df.iterrows():
        metrics = _refined_candidate_metrics(base_subset_df, candidate_row, current_train_df)
        refined_map[str(candidate_row["candidate_id"])] = metrics.pop("refined_df")
        metrics.pop("rolling_rows")
        rows.append(metrics)
    return pd.DataFrame(rows), refined_map


def _execution_stress(base_subset_df: pd.DataFrame, refined_df: pd.DataFrame) -> pd.DataFrame:
    scenarios = [
        ("baseline_cost", DEFAULT_COST_SCENARIOS[1].slippage_rate, DEFAULT_COST_SCENARIOS[1].fee_rate),
        ("cost_2x", DEFAULT_COST_SCENARIOS[2].slippage_rate, DEFAULT_COST_SCENARIOS[2].fee_rate),
        ("cost_3x", DEFAULT_COST_SCENARIOS[3].slippage_rate, DEFAULT_COST_SCENARIOS[3].fee_rate),
    ]
    rows = []
    for label, scoped_df in (("base_subset", base_subset_df), ("top_refined_candidate", refined_df)):
        anchored = scoped_df[scoped_df["current_split"] == "anchored_oos"].copy()
        for scenario_name, slippage, fee in scenarios:
            adjusted = _apply_cost_to_r(anchored, slippage, fee)
            rows.append(
                {
                    "candidate_scope": label,
                    "cost_scenario": scenario_name,
                    "slippage_rate": slippage,
                    "fee_rate": fee,
                    "expectancy_after_cost": round(float(adjusted.mean()), 6) if not adjusted.empty else math.nan,
                    "return_proxy_after_cost": round(float(adjusted.sum()), 6) if not adjusted.empty else math.nan,
                    "win_rate_after_cost": round(float((adjusted > 0).mean()), 6) if not adjusted.empty else math.nan,
                    "trade_count": int(len(anchored)),
                    "edge_survives_cost": bool(float(adjusted.mean()) > 0) if not adjusted.empty else False,
                }
            )
    return pd.DataFrame(rows)


def _success_signature(window_subset_df: pd.DataFrame) -> list[dict[str, str]]:
    signatures: list[dict[str, str]] = []
    success_df = window_subset_df[window_subset_df["window_group"] == "success_window"].copy()
    failure_df = window_subset_df[window_subset_df["window_group"] == "failure_window"].copy()
    for feature in ("sector_group", "scenario_family", "breakout_subtype", "vwap_response", "breakout_response"):
        if success_df.empty or failure_df.empty:
            continue
        categories = sorted(window_subset_df[feature].astype(str).dropna().unique().tolist())
        best_category = None
        best_delta = -math.inf
        for category in categories:
            delta = float((success_df[feature].astype(str) == category).mean() - (failure_df[feature].astype(str) == category).mean())
            if delta > best_delta:
                best_delta = delta
                best_category = category
        if best_category is not None and best_delta > 0:
            signatures.append({"feature": feature, "value": best_category, "delta": round(best_delta, 6)})
    signatures.sort(key=lambda item: item["delta"], reverse=True)
    return signatures


def _evaluate_regime_conditioning(base_subset_df: pd.DataFrame, window_subset_df: pd.DataFrame) -> pd.DataFrame:
    signatures = _success_signature(window_subset_df)
    rules: list[list[dict[str, str]]] = []
    if signatures:
        rules.append([signatures[0]])
    if len(signatures) >= 2:
        rules.append([signatures[0], signatures[1]])
    rows = []
    for idx, rule in enumerate(rules, start=1):
        scoped = base_subset_df.copy()
        for clause in rule:
            scoped = scoped[scoped[clause["feature"]].astype(str) == str(clause["value"])].copy()
        anchored = scoped[scoped["current_split"] == "anchored_oos"].copy()
        positive_windows = 0
        for window in ROLLING_WINDOWS:
            oos_df = scoped[(scoped["entry_ts"] >= pd.Timestamp(window.oos_start)) & (scoped["entry_ts"] <= pd.Timestamp(window.oos_end))].copy()
            if not oos_df.empty and float(pd.to_numeric(oos_df["realized_R"], errors="coerce").mean()) > 0:
                positive_windows += 1
        holdout_df = _holdout_rows_for_subset(_baseline_scope_for_holdout(base_subset_df), _baseline_scope_for_holdout(scoped), f"regime_rule_{idx}")
        ok_holdouts = holdout_df[holdout_df["status"] == "ok"].copy()
        rows.append(
            {
                "regime_rule_id": f"regime_rule_{idx}",
                "regime_conditions": " AND ".join(f"{clause['feature']}={clause['value']}" for clause in rule),
                "anchored_oos_expectancy": round(_expectancy(anchored), 6) if not anchored.empty else math.nan,
                "rolling_positive_window_count": int(positive_windows),
                "holdout_mean_lift": round(float(pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce").mean()), 6) if not ok_holdouts.empty else math.nan,
                "trade_count": int(len(anchored)),
                "status": "ok" if len(anchored) > 0 else "insufficient_sample",
            }
        )
    return pd.DataFrame(rows)


def _size_overlay_test(base_subset_df: pd.DataFrame, refined_df: pd.DataFrame, regime_df: pd.DataFrame) -> pd.DataFrame:
    anchored_base = base_subset_df[base_subset_df["current_split"] == "anchored_oos"].copy()
    regime_condition_text = ""
    if not regime_df.empty:
        regime_condition_text = str(regime_df.iloc[0]["regime_conditions"])
    strong_ids = set()
    if regime_condition_text:
        strong_df = refined_df.copy()
        for token in regime_condition_text.split(" AND "):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            strong_df = strong_df[strong_df[key].astype(str) == value].copy()
        strong_ids = set(strong_df["trade_id"].astype(str))
    refined_ids = set(refined_df["trade_id"].astype(str))
    rows = []

    def _policy_frame(policy_name: str) -> pd.DataFrame:
        scoped = anchored_base.copy()
        if policy_name == "base_subset_only":
            scoped["sized_R"] = pd.to_numeric(scoped["realized_R"], errors="coerce")
        elif policy_name == "refined_binary":
            scoped["sized_R"] = np.where(scoped["trade_id"].astype(str).isin(refined_ids), pd.to_numeric(scoped["realized_R"], errors="coerce"), 0.0)
        else:
            multipliers = np.where(
                scoped["trade_id"].astype(str).isin(strong_ids),
                1.5,
                np.where(scoped["trade_id"].astype(str).isin(refined_ids), 1.0, 0.5),
            )
            scoped["sized_R"] = pd.to_numeric(scoped["realized_R"], errors="coerce") * multipliers
        return scoped

    for policy_name in ("base_subset_only", "refined_binary", "size_overlay"):
        scoped = _policy_frame(policy_name)
        traded = scoped[pd.to_numeric(scoped["sized_R"], errors="coerce") != 0].copy()
        points, final_capital = _equity_points(traded.rename(columns={"sized_R": "realized_R"}), column="realized_R") if not traded.empty else ([], INITIAL_CAPITAL)
        saved_loss = float((-pd.to_numeric(scoped.loc[pd.to_numeric(scoped["sized_R"], errors="coerce") == 0, "realized_R"], errors="coerce").clip(upper=0)).sum())
        missed_gain = float(pd.to_numeric(scoped.loc[(pd.to_numeric(scoped["sized_R"], errors="coerce") == 0) & (pd.to_numeric(scoped["realized_R"], errors="coerce") > 0), "realized_R"], errors="coerce").sum())
        rows.append(
            {
                "policy_name": policy_name,
                "trade_count": int(len(traded)),
                "expectancy": round(float(pd.to_numeric(traded["sized_R"], errors="coerce").mean()), 6) if not traded.empty else math.nan,
                "return_proxy": round(float(pd.to_numeric(scoped["sized_R"], errors="coerce").sum()), 6),
                "saved_loss": round(saved_loss, 6),
                "missed_gain": round(missed_gain, 6),
                "max_drawdown_proxy": round(_max_drawdown_proxy(points), 6) if points else math.nan,
                "status": "ok" if not traded.empty else "insufficient_sample",
            }
        )
    return pd.DataFrame(rows)


def _final_decision(
    validation_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    regime_df: pd.DataFrame,
) -> pd.DataFrame:
    refined = validation_df[validation_df["candidate_id"] != "base_subset"].copy()
    if refined.empty:
        return pd.DataFrame([{"decision": "REJECT_REFINED", "decision_reason": "no refinement candidate was generated"}])
    best = refined.sort_values(
        ["rolling_positive_window_count", "anchored_oos_expectancy_delta_vs_base_subset", "holdout_mean_lift", "trade_count"],
        ascending=[False, False, False, False],
    ).iloc[0]
    best_name = str(best["candidate_id"])
    best_stress = stress_df[stress_df["candidate_scope"] == "top_refined_candidate"].copy()
    survives_2x = bool(best_stress.loc[best_stress["cost_scenario"] == "cost_2x", "edge_survives_cost"].astype(bool).any())
    holdout_lift = float(best["holdout_mean_lift"]) if not pd.isna(best["holdout_mean_lift"]) else math.nan
    anchored_delta = float(best["anchored_oos_expectancy_delta_vs_base_subset"]) if not pd.isna(best["anchored_oos_expectancy_delta_vs_base_subset"]) else math.nan
    positive_windows = int(best["rolling_positive_window_count"])
    converted_failures = int(best["converted_failure_windows"])
    symbol_share = float(best["symbol_concentration_share"]) if not pd.isna(best["symbol_concentration_share"]) else 1.0
    if math.isnan(anchored_delta) or anchored_delta <= 0 or not survives_2x or (not math.isnan(holdout_lift) and holdout_lift <= 0 and regime_df.empty):
        decision = "REJECT_REFINED"
        reason = f"{best_name} did not improve anchored OOS robustness enough after cost or holdout checks"
    elif (
        positive_windows >= SUCCESS_DECISION_MIN_POSITIVE_WINDOWS
        and converted_failures >= 1
        and not math.isnan(holdout_lift)
        and holdout_lift > 0
        and symbol_share <= 0.60
    ):
        decision = "STRONG_REFINED_EDGE"
        reason = f"{best_name} improved rolling stability and held up in anchored OOS, holdouts, and 2x cost"
    elif not regime_df.empty:
        regime_best = regime_df.sort_values(["rolling_positive_window_count", "anchored_oos_expectancy", "holdout_mean_lift"], ascending=[False, False, False]).iloc[0]
        regime_holdout = float(regime_best["holdout_mean_lift"]) if not pd.isna(regime_best["holdout_mean_lift"]) else math.nan
        if int(regime_best["rolling_positive_window_count"]) >= SUCCESS_DECISION_MIN_POSITIVE_WINDOWS and float(regime_best["anchored_oos_expectancy"]) > 0 and (math.isnan(regime_holdout) or regime_holdout >= 0):
            decision = "REGIME_CONDITIONAL_EDGE"
            reason = f"{best_name} is not universal, but {regime_best['regime_conditions']} stabilizes the edge enough to justify regime-conditional deployment"
        else:
            decision = "WEAK_REFINED_EDGE"
            reason = f"{best_name} improved recent OOS but still lacks enough cross-window or holdout stability"
    else:
        decision = "WEAK_REFINED_EDGE"
        reason = f"{best_name} improved recent OOS but still lacks enough cross-window or holdout stability"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_candidate_id": best_name,
                "anchored_oos_expectancy_delta_vs_base_subset": round(anchored_delta, 6) if not math.isnan(anchored_delta) else math.nan,
                "rolling_positive_window_count": positive_windows,
                "converted_failure_windows": converted_failures,
                "holdout_mean_lift": round(holdout_lift, 6) if not math.isnan(holdout_lift) else math.nan,
                "survives_2x_cost": survives_2x,
                "symbol_concentration_share": round(symbol_share, 6),
            }
        ]
    )


def _markdown_report(
    out_dir: Path,
    window_summary_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    regime_df: pd.DataFrame,
    overlay_df: pd.DataFrame,
    final_decision_df: pd.DataFrame,
) -> None:
    decision = str(final_decision_df.iloc[0]["decision"])
    best_candidate = str(final_decision_df.iloc[0]["best_candidate_id"])
    best_validation = validation_df[validation_df["candidate_id"] == best_candidate].iloc[0] if best_candidate in set(validation_df["candidate_id"]) else None
    regime_line = "No live-eligible regime rule improved the base subset enough." if regime_df.empty else str(regime_df.sort_values(["anchored_oos_expectancy"], ascending=False).iloc[0]["regime_conditions"])
    lines: list[str] = [
        "# Task 341: Strong Subset Refinement & Regime-Specific Edge Strengthening",
        "",
        f"Final decision: **{decision}**",
        "",
        "## Window Failure vs Success",
        "",
        "",
        "Failure and success windows were compared inside the fixed `entry_only + high_atr + vol_expanding` subset to isolate what changed across time.",
        "",
        "## Best Refinement Read",
        "",
    ]
    lines.extend(_markdown_table(window_summary_df[["window_id", "window_group", "subset_trade_count", "subset_expectancy", "expectancy_delta"]]))
    lines.append("")
    if best_validation is not None:
        lines.extend(
            [
                f"- Best candidate: `{best_candidate}`",
                f"- Anchored OOS expectancy delta vs base subset: `{best_validation['anchored_oos_expectancy_delta_vs_base_subset']}`",
                f"- Rolling positive windows: `{best_validation['rolling_positive_window_count']}`",
                f"- Converted failure windows: `{best_validation['converted_failure_windows']}`",
                f"- Holdout mean lift: `{best_validation['holdout_mean_lift']}`",
                f"- Symbol concentration share: `{best_validation['symbol_concentration_share']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Regime Conditioning",
            "",
            f"- Strongest live-eligible regime signature: `{regime_line}`",
            "",
            "## Size Overlay",
            "",
            "",
            "## Interpretation",
            "",
            f"- The key difference between failure and success windows is summarized by the subset refinement tables and the resulting regime signature above.",
            f"- The best refinement candidate was `{best_candidate}`, but the final classification remained `{decision}` after rolling, holdout, and cost checks.",
            f"- Next step: {'engine gating for a live-eligible regime overlay' if decision in {'STRONG_REFINED_EDGE', 'REGIME_CONDITIONAL_EDGE'} else 'research-only monitoring and more evidence accumulation'}",
        ]
    )
    lines.extend(_markdown_table(overlay_df[["policy_name", "trade_count", "expectancy", "return_proxy", "saved_loss", "missed_gain", "max_drawdown_proxy"]]))
    lines.append("")
    (out_dir / "task_341_subset_refinement.md").write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: Path = DEFAULT_OUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_subset_df = _build_base_subset_master()
    current_train_df = base_subset_df[base_subset_df["current_split"] == "train"].copy()
    window_subset_df, window_summary_df = _rolling_subset_windows(base_subset_df)
    window_comparison_df = _window_comparison(window_subset_df)
    quality_df = _subset_quality_decomposition(base_subset_df)
    candidates_df = _build_refinement_candidates(window_subset_df, base_subset_df, current_train_df)
    validation_df, refined_map = _refined_subset_validation(base_subset_df, candidates_df)
    top_refined_id = (
        validation_df[validation_df["candidate_id"] != "base_subset"]
        .sort_values(["rolling_positive_window_count", "anchored_oos_expectancy_delta_vs_base_subset", "holdout_mean_lift"], ascending=[False, False, False])
        .iloc[0]["candidate_id"]
        if len(validation_df[validation_df["candidate_id"] != "base_subset"]) > 0
        else "base_subset"
    )
    top_refined_df = refined_map[top_refined_id]
    stress_df = _execution_stress(base_subset_df, top_refined_df)
    regime_df = _evaluate_regime_conditioning(base_subset_df, window_subset_df)
    overlay_df = _size_overlay_test(base_subset_df, top_refined_df, regime_df)
    final_decision_df = _final_decision(validation_df, stress_df, regime_df)

    window_comparison_df.to_csv(output_dir / "task_341_window_comparison.csv", index=False)
    quality_df.to_csv(output_dir / "task_341_subset_quality_decomposition.csv", index=False)
    candidates_df.to_csv(output_dir / "task_341_refinement_candidates.csv", index=False)
    validation_df.to_csv(output_dir / "task_341_refined_subset_validation.csv", index=False)
    stress_df.to_csv(output_dir / "task_341_execution_stress.csv", index=False)
    regime_df.to_csv(output_dir / "task_341_regime_conditioning.csv", index=False)
    overlay_df.to_csv(output_dir / "task_341_size_overlay_test.csv", index=False)
    final_decision_df.to_csv(output_dir / "task_341_final_decision.csv", index=False)
    _markdown_report(output_dir, window_summary_df, validation_df, regime_df, overlay_df, final_decision_df)


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 341: Strong subset refinement and regime-specific edge strengthening.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
