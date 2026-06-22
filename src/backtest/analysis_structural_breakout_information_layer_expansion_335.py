from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    BAD_STATE_BASES,
    CLEAN_STATE_BASE,
    FROZEN_SELECTED_CLUSTERS,
    FULL_SIZE_MULTIPLIER,
    HOLDOUT_MIN_TRADES,
    PRE_ENTRY_PREDICTOR_FEATURES,
    _available_features,
    _build_prob_tables,
    _fit_logistic,
    _load_frozen_behavior_state,
    _markdown_table,
    _predict_from_tables,
    _predict_with_model,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_335_information_layer_expansion")
TRAIN_BAND_Q_LOW = 0.30
TRAIN_BAND_Q_HIGH = 0.70
OOS_MIN_COUNT = 5
RANK_TARGET_ORDER = {
    "dead_breakout": 0,
    "early_failure": 0,
    "weak_breakout": 0,
    "volatile_whipsaw": 0,
    "failed_pop": 1,
    "slow_grind": 1,
    "uneven_continuation": 1,
    "clean_continuation": 2,
}
FORBIDDEN_POST_ENTRY_FEATURES = {
    "follow_through_3d_pct",
    "follow_through_5d_pct",
    "retrace_3d_pct",
    "retrace_5d_pct",
    "mae_3d_pct",
    "mae_5d_pct",
    "mfe_3d_pct",
    "mfe_5d_pct",
    "realized_R",
    "holding_days",
    "path_type",
    "cluster_label",
    "cluster_label_base",
    "behavior_cluster_id",
}
PHASE1_FAMILIES: dict[str, list[str]] = {
    "core": list(PRE_ENTRY_PREDICTOR_FEATURES),
    "intraday_structure_proxy": [
        "gap_over_planned_entry_pct",
        "pre_breakout_distance_pct",
        "breakout_strength_pct",
        "close_location_pre",
        "range_width_10_pre",
        "squeeze_quality",
    ],
    "volume_participation": [
        "volume_confirmation_pre",
        "vol_contraction_ratio",
        "dollar_volume_pre",
        "turnover_pre",
    ],
    "market_structure": [
        "breadth_above_sma20",
        "breadth_above_sma50",
        "breadth_positive_20d",
        "dispersion_20d",
        "mean_pairwise_corr",
    ],
    "setup_context": [
        "pre_breakout_distance_pct",
        "recent_failed_breakouts_20d",
        "breakout_strength_pct",
        "gap_over_planned_entry_pct",
        "range_width_10_pre",
    ],
    "crowding_concentration": [
        "top_sector_dominance_score",
        "semis_concentration_ratio",
        "tech_concentration_ratio",
        "sector_crowding_high",
        "sector_rs_percentile",
    ],
}
PHASE2_DEFINITION_ONLY: dict[str, list[str]] = {
    "intraday_structure_true": [
        "intraday_volume_surge",
        "breakout_bar_volume_percentile",
        "intraday_range_expansion_ratio",
        "vwap_deviation_at_breakout",
        "same_session_follow_through",
    ],
    "volume_participation_true": [
        "breakout_window_volume_concentration",
        "volume_persistence_after_breakout",
        "volume_imbalance_proxy",
    ],
}


def _family_definition_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rationale = {
        "core": "Task 334 core pre-entry feature set retained as baseline.",
        "intraday_structure_proxy": "Daily/history proxies for breakout execution quality without minute-level data.",
        "volume_participation": "Proxy for real demand and participation quality using pre-entry volume context.",
        "market_structure": "Overall market context and cohesion before breakout.",
        "setup_context": "Breakout setup quality and nearby failure pressure.",
        "crowding_concentration": "Crowding and concentration pressure before breakout.",
        "intraday_structure_true": "Phase 2 slot for real intraday breakout-quality measures once historical intraday data exists.",
        "volume_participation_true": "Phase 2 slot for true breakout-window participation measures once intraday data exists.",
    }
    for family_name, features in PHASE1_FAMILIES.items():
        available = [feature for feature in features if feature in df.columns]
        rows.append(
            {
                "family_name": family_name,
                "phase": "phase_1",
                "status": "available" if available else "unavailable",
                "feature_count_defined": len(features),
                "feature_count_available": len(available),
                "features_defined": "|".join(features),
                "features_available": "|".join(available),
                "rationale": rationale[family_name],
            }
        )
    for family_name, features in PHASE2_DEFINITION_ONLY.items():
        rows.append(
            {
                "family_name": family_name,
                "phase": "phase_2_definition_only",
                "status": "definition_only",
                "feature_count_defined": len(features),
                "feature_count_available": 0,
                "features_defined": "|".join(features),
                "features_available": "",
                "rationale": rationale[family_name],
            }
        )
    return pd.DataFrame(rows)


def _derive_target(df: pd.DataFrame, target_name: str) -> pd.Series:
    if target_name == "multiclass":
        return df["cluster_label"].astype(str)
    if target_name == "bad_state":
        return df["cluster_label_base"].astype(str).isin(BAD_STATE_BASES).astype(int)
    if target_name == "clean_state":
        return (df["cluster_label_base"].astype(str) == CLEAN_STATE_BASE).astype(int)
    if target_name == "continuation_quality_rank":
        return df["cluster_label_base"].astype(str).map(lambda value: RANK_TARGET_ORDER.get(str(value), 1)).astype(int)
    raise ValueError(f"unknown target: {target_name}")


def _metric_row(y_true: pd.Series, preds: np.ndarray, model_name: str, scope_name: str, target_name: str) -> dict[str, Any]:
    y_true_series = y_true.astype(str)
    pred_series = pd.Series(preds, index=y_true.index).astype(str)
    majority = float(y_true_series.value_counts(normalize=True).max()) if not y_true_series.empty else 0.0
    accuracy = float((y_true_series == pred_series).mean()) if not y_true_series.empty else 0.0
    row = {
        "target": target_name,
        "scope": scope_name,
        "model": model_name,
        "accuracy": round(accuracy, 6),
        "majority_baseline_accuracy": round(majority, 6),
        "lift_vs_baseline": round(accuracy - majority, 6),
        "bad_state_recall": math.nan,
        "clean_state_precision": math.nan,
    }
    if target_name == "bad_state":
        pred_pos = pred_series == "1"
        true_pos = y_true_series == "1"
        recall = float((pred_pos & true_pos).sum() / max(int(true_pos.sum()), 1))
        row["bad_state_recall"] = round(recall, 6)
    if target_name == "clean_state":
        pred_pos = pred_series == "1"
        true_pos = y_true_series == "1"
        precision = float((pred_pos & true_pos).sum() / max(int(pred_pos.sum()), 1))
        row["clean_state_precision"] = round(precision, 6)
    return row


def _majority_predictor(y_train: pd.Series, count: int) -> tuple[np.ndarray, list[dict[str, float]]]:
    majority = y_train.mode().iloc[0]
    classes = [str(value) for value in sorted(set(y_train.astype(str).tolist()))]
    preds = np.asarray([majority] * count)
    probs = [{cls: (1.0 if cls == str(majority) else 0.0) for cls in classes} for _ in range(count)]
    return preds, probs


def _family_features(df: pd.DataFrame, family_name: str) -> list[str]:
    if family_name == "core_only":
        base = PHASE1_FAMILIES["core"]
    elif family_name.startswith("core_plus_"):
        suffix = family_name.removeprefix("core_plus_")
        base = PHASE1_FAMILIES["core"] + PHASE1_FAMILIES[suffix]
    elif family_name in {"core_plus_best_2_families", "core_plus_best_3_families"}:
        raise ValueError("best family aggregates are resolved separately")
    else:
        base = PHASE1_FAMILIES[family_name]
    return _available_features(df, base)


def _resolve_feature_set_features(train_df: pd.DataFrame, feature_set_name: str, ablation_df: pd.DataFrame | None = None) -> list[str]:
    if feature_set_name not in {"core_plus_best_2_families", "core_plus_best_3_families"}:
        return _family_features(train_df, feature_set_name)
    if ablation_df is None:
        return _family_features(train_df, "core_only")
    scoped = ablation_df[ablation_df["feature_set"] == feature_set_name]
    if scoped.empty:
        return _family_features(train_df, "core_only")
    col = "selected_best_2_members" if feature_set_name == "core_plus_best_2_families" else "selected_best_3_members"
    selected = str(scoped[col].iloc[0])
    members = [member for member in selected.split("|") if member]
    return _available_features(train_df, PHASE1_FAMILIES["core"] + sum([PHASE1_FAMILIES[member.removeprefix("core_plus_")] for member in members], []))


def _family_set_name(family_name: str) -> str:
    if family_name == "core":
        return "core_only"
    return f"core_plus_{family_name}"


def _add_train_only_bands(train_df: pd.DataFrame, oos_df: pd.DataFrame, full_df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, tuple[float, float]]]:
    train_out = train_df.copy()
    oos_out = oos_df.copy()
    full_out = full_df.copy()
    edges: dict[str, tuple[float, float]] = {}
    for feature in features:
        if feature not in train_out.columns:
            continue
        train_series = pd.to_numeric(train_out[feature], errors="coerce")
        if train_series.notna().sum() < 5:
            continue
        original_series = train_out[feature]
        if pd.api.types.is_bool_dtype(original_series):
            band_col = f"{feature}_task335_band"
            train_out[band_col] = train_out[feature].astype(str).fillna("missing")
            oos_out[band_col] = oos_out[feature].astype(str).fillna("missing")
            full_out[band_col] = full_out[feature].astype(str).fillna("missing")
        elif pd.api.types.is_numeric_dtype(train_series):
            low = float(train_series.quantile(TRAIN_BAND_Q_LOW))
            high = float(train_series.quantile(TRAIN_BAND_Q_HIGH))
            edges[feature] = (low, high)

            def _band_value(value: Any) -> str:
                numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
                if pd.isna(numeric):
                    return "missing"
                if numeric < low:
                    return "low"
                if numeric > high:
                    return "high"
                return "mid"

            band_col = f"{feature}_task335_band"
            train_out[band_col] = train_out[feature].map(_band_value)
            oos_out[band_col] = oos_out[feature].map(_band_value)
            full_out[band_col] = full_out[feature].map(_band_value)
        else:
            band_col = f"{feature}_task335_band"
            train_out[band_col] = train_out[feature].astype(str).fillna("missing")
            oos_out[band_col] = oos_out[feature].astype(str).fillna("missing")
            full_out[band_col] = full_out[feature].astype(str).fillna("missing")
    return train_out, oos_out, full_out, edges


def _evaluate_feature_set(
    train_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    target_name: str,
    features: list[str],
    family_name: str,
    model_kind: str,
) -> tuple[dict[str, Any], np.ndarray, list[dict[str, float]]]:
    features = _available_features(train_df, features)
    y_train = _derive_target(train_df, target_name)
    y_eval = _derive_target(eval_df, target_name)
    classes = sorted(y_train.astype(str).unique().tolist())
    if model_kind == "majority":
        preds, probs = _majority_predictor(y_train.astype(str), len(eval_df))
    elif model_kind == "band_probability":
        band_features = [f"{feature}_task335_band" for feature in features if f"{feature}_task335_band" in train_df.columns]
        tables = _build_prob_tables(train_df, y_train, band_features)
        preds, probs = _predict_from_tables(eval_df, tables, classes)
    elif model_kind == "logistic":
        model = _fit_logistic(train_df, y_train, features)
        preds, probs = _predict_with_model(model, eval_df, features)
    else:
        raise ValueError(model_kind)
    row = _metric_row(y_eval, preds, model_kind, str(eval_df["scope"].iloc[0]) if "scope" in eval_df.columns else "eval", target_name)
    row["family_name"] = family_name
    row["feature_count"] = len(features)
    return row, preds, probs


def _rank_single_family_rows(ablation_df: pd.DataFrame) -> list[str]:
    rows = ablation_df[
        (ablation_df["scope"] == "anchored_oos")
        & (ablation_df["target"].isin(["bad_state", "clean_state"]))
        & (ablation_df["family_name"].isin([_family_set_name(name) for name in PHASE1_FAMILIES if name != "core"]))
    ].copy()
    if rows.empty:
        return []
    summary_rows = []
    for family_name, scoped in rows.groupby("family_name"):
        bad_rows = scoped[scoped["target"] == "bad_state"]
        clean_rows = scoped[scoped["target"] == "clean_state"]
        bad_recall = float(pd.to_numeric(bad_rows["bad_state_recall"], errors="coerce").max()) if not bad_rows.empty else -999.0
        lift = float(pd.to_numeric(bad_rows["lift_vs_baseline"], errors="coerce").max()) if not bad_rows.empty else -999.0
        clean_precision = float(pd.to_numeric(clean_rows["clean_state_precision"], errors="coerce").max()) if not clean_rows.empty else -999.0
        summary_rows.append({"family_name": family_name, "bad_recall": bad_recall, "lift": lift, "clean_precision": clean_precision})
    summary_df = pd.DataFrame(summary_rows).sort_values(["bad_recall", "lift", "clean_precision", "family_name"], ascending=[False, False, False, True])
    return summary_df["family_name"].tolist()


def _family_decision(lift: float, bad_recall: float, clean_precision: float, base_bad_recall: float, base_clean_precision: float) -> str:
    if lift > 0:
        return "keep"
    if bad_recall > base_bad_recall and clean_precision >= (base_clean_precision - 0.15):
        return "conditional_keep"
    return "discard"


def _feature_family_ablation(train_df: pd.DataFrame, oos_df: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    family_set_features: dict[str, list[str]] = {"core_only": _family_features(train_df, "core_only")}
    for family_name in PHASE1_FAMILIES:
        if family_name == "core":
            continue
        family_set_features[_family_set_name(family_name)] = _family_features(train_df, _family_set_name(family_name))

    datasets = {"train": train_df, "anchored_oos": oos_df, "full_period": full_df}
    for family_set_name, features in family_set_features.items():
        available_count = len(features)
        unavailable = available_count == 0
        for scope_name, scoped_df in datasets.items():
            for target_name in ["multiclass", "bad_state", "clean_state", "continuation_quality_rank"]:
                base_bad_recall = math.nan
                base_clean_precision = math.nan
                for model_kind in ["majority", "band_probability", "logistic"]:
                    row, _, _ = _evaluate_feature_set(train_df, scoped_df, target_name, features, family_set_name, model_kind)
                    row["scope"] = scope_name
                    row["status"] = "unavailable" if unavailable else "available"
                    row["feature_set"] = family_set_name
                    row["selected_best_2_members"] = ""
                    row["selected_best_3_members"] = ""
                    rows.append(row)

    ablation_df = pd.DataFrame(rows)
    ranked_singletons = _rank_single_family_rows(ablation_df)
    if not ranked_singletons:
        ranked_singletons = [name for name in family_set_features.keys() if name != "core_only"]
    top_two = ranked_singletons[:2]
    top_three = ranked_singletons[:3]
    aggregate_sets = {
        "core_plus_best_2_families": _available_features(
            train_df,
            PHASE1_FAMILIES["core"] + sum([PHASE1_FAMILIES[name.removeprefix("core_plus_")] for name in top_two], []),
        ),
        "core_plus_best_3_families": _available_features(
            train_df,
            PHASE1_FAMILIES["core"] + sum([PHASE1_FAMILIES[name.removeprefix("core_plus_")] for name in top_three], []),
        ),
    }
    aggregate_rows = []
    for family_set_name, features in aggregate_sets.items():
        for scope_name, scoped_df in datasets.items():
            for target_name in ["multiclass", "bad_state", "clean_state", "continuation_quality_rank"]:
                for model_kind in ["majority", "band_probability", "logistic"]:
                    row, _, _ = _evaluate_feature_set(train_df, scoped_df, target_name, features, family_set_name, model_kind)
                    row["scope"] = scope_name
                    row["status"] = "unavailable" if len(features) == 0 else "available"
                    row["feature_set"] = family_set_name
                    row["selected_best_2_members"] = "|".join(top_two) if family_set_name == "core_plus_best_2_families" else ""
                    row["selected_best_3_members"] = "|".join(top_three) if family_set_name == "core_plus_best_3_families" else ""
                    aggregate_rows.append(row)
    if aggregate_rows:
        ablation_df = pd.concat([ablation_df, pd.DataFrame(aggregate_rows)], ignore_index=True)
    base_bad = ablation_df[
        (ablation_df["feature_set"] == "core_only")
        & (ablation_df["scope"] == "anchored_oos")
        & (ablation_df["target"] == "bad_state")
        & (ablation_df["model"] == "logistic")
    ]
    base_clean = ablation_df[
        (ablation_df["feature_set"] == "core_only")
        & (ablation_df["scope"] == "anchored_oos")
        & (ablation_df["target"] == "clean_state")
        & (ablation_df["model"] == "logistic")
    ]
    base_bad_recall = float(base_bad["bad_state_recall"].iloc[0]) if not base_bad.empty else -999.0
    base_clean_precision = float(base_clean["clean_state_precision"].iloc[0]) if not base_clean.empty else -999.0
    ablation_df["decision"] = ablation_df.apply(
        lambda row: _family_decision(
            float(row["lift_vs_baseline"]),
            float(row["bad_state_recall"]) if not pd.isna(row["bad_state_recall"]) else -999.0,
            float(row["clean_state_precision"]) if not pd.isna(row["clean_state_precision"]) else -999.0,
            base_bad_recall,
            base_clean_precision,
        )
        if row["scope"] == "anchored_oos" and row["target"] in {"bad_state", "clean_state"}
        else "",
        axis=1,
    )
    return ablation_df.sort_values(["feature_set", "scope", "target", "model"]).reset_index(drop=True)


def _feature_to_behavior_mapping(train_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family_name, features in PHASE1_FAMILIES.items():
        available_features = _available_features(train_df, features)
        if not available_features:
            rows.append(
                {
                    "mapping_type": "family_status",
                    "family_name": family_name,
                    "feature_name": "",
                    "feature_value": "",
                    "cluster_label": "",
                    "cluster_probability": math.nan,
                    "trade_count": 0,
                    "status": "unavailable",
                }
            )
            continue
        for feature in available_features:
            band_col = f"{feature}_task335_band"
            source_col = band_col if band_col in train_df.columns else feature
            for value, scoped in train_df.groupby(source_col):
                dist = scoped["cluster_label"].astype(str).value_counts(normalize=True)
                for cluster_label, prob in dist.items():
                    rows.append(
                        {
                            "mapping_type": "feature_band",
                            "family_name": family_name,
                            "feature_name": feature,
                            "feature_value": str(value),
                            "cluster_label": str(cluster_label),
                            "cluster_probability": round(float(prob), 6),
                            "trade_count": int(len(scoped)),
                            "status": "available",
                        }
                    )
    return pd.DataFrame(rows).sort_values(["family_name", "feature_name", "feature_value", "cluster_probability"], ascending=[True, True, True, False]).reset_index(drop=True)


def _build_model_payload(train_df: pd.DataFrame, target_name: str, features: list[str], model_name: str) -> tuple[str, list[str], Any, float | None]:
    features = _available_features(train_df, features)
    y_train = _derive_target(train_df, target_name)
    if model_name == "band_probability":
        band_features = [f"{feature}_task335_band" for feature in features if f"{feature}_task335_band" in train_df.columns]
        tables = _build_prob_tables(train_df, y_train, band_features)
        return ("band_probability", band_features, tables, None)
    model = _fit_logistic(train_df, y_train, features)
    probs = model.predict_proba(train_df[features])
    pos_idx = list(model.classes_).index(1) if 1 in set(model.classes_) else list(model.classes_).index("1")
    threshold = float(np.quantile(probs[:, pos_idx], 2 / 3))
    return ("logistic", features, model, threshold)


def _predict_payload(payload: tuple[str, list[str], Any, float | None], df: pd.DataFrame) -> tuple[np.ndarray, list[dict[str, float]]]:
    model_type, features, fitted, _ = payload
    if model_type == "band_probability":
        train_classes = sorted({str(label) for feature_table in fitted.values() for dist in feature_table.values() for label in dist.keys()})
        return _predict_from_tables(df, fitted, train_classes)
    return _predict_with_model(fitted, df, features)


def _diagnostic_overlay(
    df: pd.DataFrame,
    bad_payload: tuple[str, list[str], Any, float | None],
    clean_payload: tuple[str, list[str], Any, float | None],
    policy_name: str,
    scope_name: str,
) -> tuple[dict[str, Any], pd.DataFrame]:
    out = df.copy()
    bad_preds, bad_probs = _predict_payload(bad_payload, out)
    clean_preds, clean_probs = _predict_payload(clean_payload, out)
    bad_type, _, _, bad_threshold = bad_payload
    clean_type, _, _, clean_threshold = clean_payload
    if bad_type == "logistic":
        bad_scores = np.asarray([float(prob.get("1", prob.get(1, 0.0))) for prob in bad_probs], dtype=float)
        pred_bad = bad_scores >= float(bad_threshold)
    else:
        pred_bad = np.asarray([str(pred) == "1" for pred in bad_preds], dtype=bool)
    if clean_type == "logistic":
        clean_scores = np.asarray([float(prob.get("1", prob.get(1, 0.0))) for prob in clean_probs], dtype=float)
        pred_clean = clean_scores >= float(clean_threshold)
    else:
        pred_clean = np.asarray([str(pred) == "1" for pred in clean_preds], dtype=bool)
    multiplier = np.where(pred_bad, 0.0, np.where(pred_clean, FULL_SIZE_MULTIPLIER, 1.0))
    out["pred_bad_state"] = pred_bad.astype(int)
    out["pred_clean_state"] = pred_clean.astype(int)
    out["diagnostic_multiplier"] = multiplier
    out["diagnostic_adjusted_R"] = pd.to_numeric(out["realized_R"], errors="coerce") * pd.to_numeric(out["diagnostic_multiplier"], errors="coerce")
    baseline_return = float(pd.to_numeric(out["realized_R"], errors="coerce").sum())
    adjusted_return = float(pd.to_numeric(out["diagnostic_adjusted_R"], errors="coerce").sum())
    baseline_expectancy = float(pd.to_numeric(out["realized_R"], errors="coerce").mean()) if not out.empty else 0.0
    adjusted_expectancy = float(pd.to_numeric(out.loc[out["diagnostic_multiplier"] > 0, "diagnostic_adjusted_R"], errors="coerce").mean()) if (out["diagnostic_multiplier"] > 0).any() else 0.0
    saved_loss = float((-pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0.0) & (pd.to_numeric(out["realized_R"], errors="coerce") < 0), "realized_R"], errors="coerce")).sum())
    missed_gain = float(pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0.0) & (pd.to_numeric(out["realized_R"], errors="coerce") > 0), "realized_R"], errors="coerce").sum())
    metrics = {
        "scope": scope_name,
        "policy_name": policy_name,
        "baseline_expectancy": round(baseline_expectancy, 6),
        "diagnostic_expectancy": round(adjusted_expectancy, 6),
        "baseline_return_proxy": round(baseline_return, 6),
        "diagnostic_return_proxy": round(adjusted_return, 6),
        "trade_count": int(len(out)),
        "diagnostic_trade_count": int((out["diagnostic_multiplier"] > 0).sum()),
        "saved_loss": round(saved_loss, 6),
        "missed_gain": round(missed_gain, 6),
    }
    delta_cols = [
        "scope",
        "scenario",
        "scenario_family",
        "trade_id",
        "symbol",
        "sector_bucket",
        "entry_date",
        "realized_R",
        "cluster_label",
        "cluster_label_base",
        "pred_bad_state",
        "pred_clean_state",
        "diagnostic_multiplier",
        "diagnostic_adjusted_R",
    ]
    delta_df = out[delta_cols].copy()
    delta_df["policy_name"] = policy_name
    return metrics, delta_df


def _best_rows_by_target(ablation_df: pd.DataFrame, target_name: str) -> dict[str, Any]:
    scoped = ablation_df[
        (ablation_df["scope"] == "anchored_oos")
        & (ablation_df["target"] == target_name)
        & (ablation_df["model"] != "majority")
        & (ablation_df["status"] == "available")
    ].copy()
    if scoped.empty:
        return {}
    if target_name == "bad_state":
        scoped = scoped.sort_values(["bad_state_recall", "lift_vs_baseline", "accuracy"], ascending=[False, False, False])
    elif target_name == "clean_state":
        scoped = scoped.sort_values(["clean_state_precision", "lift_vs_baseline", "accuracy"], ascending=[False, False, False])
    else:
        scoped = scoped.sort_values(["lift_vs_baseline", "accuracy"], ascending=[False, False])
    return scoped.iloc[0].to_dict()


def _holdout_rows_for_group(
    train_df: pd.DataFrame,
    target_name: str,
    feature_set_name: str,
    model_name: str,
    group_col: str,
    features: list[str],
) -> pd.DataFrame:
    rows = []
    if group_col not in train_df.columns:
        return pd.DataFrame([{"target": target_name, "feature_set": feature_set_name, "model": model_name, "holdout_type": group_col, "holdout_value": "", "status": "unavailable"}])
    counts = train_df[group_col].astype(str).value_counts()
    groups = counts.index.tolist()
    for group in groups:
        count = int(counts[group])
        if count < HOLDOUT_MIN_TRADES:
            rows.append({"target": target_name, "feature_set": feature_set_name, "model": model_name, "holdout_type": group_col, "holdout_value": str(group), "status": "insufficient_density"})
            continue
        holdout_df = train_df[train_df[group_col].astype(str) == str(group)].copy()
        fit_df = train_df[train_df[group_col].astype(str) != str(group)].copy()
        if holdout_df.empty or fit_df.empty:
            rows.append({"target": target_name, "feature_set": feature_set_name, "model": model_name, "holdout_type": group_col, "holdout_value": str(group), "status": "unavailable"})
            continue
        row, _, _ = _evaluate_feature_set(fit_df, holdout_df, target_name, features, feature_set_name, model_name)
        row["holdout_type"] = group_col
        row["holdout_value"] = str(group)
        row["status"] = "ok"
        rows.append(row)
    return pd.DataFrame(rows)


def _time_split_oos_rows(
    oos_df: pd.DataFrame,
    train_df: pd.DataFrame,
    target_name: str,
    feature_set_name: str,
    model_name: str,
    features: list[str],
) -> pd.DataFrame:
    payload = _build_model_payload(train_df, target_name, features, model_name)
    out_rows = []
    oos_work = oos_df.copy()
    oos_work["entry_month"] = pd.to_datetime(oos_work["entry_date"], errors="coerce").dt.to_period("M").astype(str)
    for month, scoped in oos_work.groupby("entry_month"):
        if len(scoped) < OOS_MIN_COUNT:
            out_rows.append({"target": target_name, "feature_set": feature_set_name, "model": model_name, "holdout_type": "time_split_oos", "holdout_value": str(month), "status": "insufficient_density"})
            continue
        preds, _ = _predict_payload(payload, scoped)
        row = _metric_row(_derive_target(scoped, target_name), preds, model_name, "anchored_oos", target_name)
        row["holdout_type"] = "time_split_oos"
        row["holdout_value"] = str(month)
        row["feature_set"] = feature_set_name
        row["status"] = "ok"
        out_rows.append(row)
    return pd.DataFrame(out_rows)


def _economic_action_metrics(ablation_df: pd.DataFrame, train_df: pd.DataFrame, oos_df: pd.DataFrame, full_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    best_bad = _best_rows_by_target(ablation_df, "bad_state")
    best_clean = _best_rows_by_target(ablation_df, "clean_state")
    bad_payload = _build_model_payload(train_df, "bad_state", _resolve_feature_set_features(train_df, str(best_bad["feature_set"]), ablation_df), str(best_bad["model"]))
    clean_payload = _build_model_payload(train_df, "clean_state", _resolve_feature_set_features(train_df, str(best_clean["feature_set"]), ablation_df), str(best_clean["model"]))
    rows = []
    delta_rows = []
    for scope_name, scoped in (("train", train_df), ("anchored_oos", oos_df), ("full_period", full_df)):
        metrics, delta = _diagnostic_overlay(scoped, bad_payload, clean_payload, "bad_skip_clean_fullsize", scope_name)
        rows.append(metrics)
        delta_rows.append(delta)
    return pd.DataFrame(rows).sort_values("scope").reset_index(drop=True), pd.concat(delta_rows, ignore_index=True)


def _final_decision(ablation_df: pd.DataFrame, holdout_df: pd.DataFrame, economic_df: pd.DataFrame) -> pd.DataFrame:
    oos_rows = ablation_df[(ablation_df["scope"] == "anchored_oos") & (ablation_df["status"] == "available")].copy()
    positive_lift_exists = bool((pd.to_numeric(oos_rows["lift_vs_baseline"], errors="coerce") > 0).any()) if not oos_rows.empty else False
    bad_recall_best = float(pd.to_numeric(oos_rows["bad_state_recall"], errors="coerce").max()) if not oos_rows.empty else -999.0
    clean_precision_best = float(pd.to_numeric(oos_rows["clean_state_precision"], errors="coerce").max()) if not oos_rows.empty else -999.0
    ok_holdouts = holdout_df[holdout_df.get("status", "ok") == "ok"].copy()
    holdout_mean_lift = float(pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce").mean()) if not ok_holdouts.empty else -999.0
    holdout_positive_share = float((pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce") > 0).mean()) if not ok_holdouts.empty else 0.0
    oos_action = economic_df[economic_df["scope"] == "anchored_oos"].iloc[0]
    full_action = economic_df[economic_df["scope"] == "full_period"].iloc[0]
    expectancy_delta = float(oos_action["diagnostic_expectancy"]) - float(oos_action["baseline_expectancy"])
    saved_loss_gt_missed = float(oos_action["saved_loss"]) > float(oos_action["missed_gain"])
    trade_count_ratio = float(oos_action["diagnostic_trade_count"]) / max(float(oos_action["trade_count"]), 1.0)
    full_period_damage = float(full_action["diagnostic_return_proxy"]) / max(float(full_action["baseline_return_proxy"]), 1e-9)

    decision = "NO_INFORMATION_EDGE"
    reason = "no family set produced stable OOS lift with robust holdout support"
    if (
        positive_lift_exists
        and bad_recall_best >= 0.35
        and holdout_mean_lift > 0
        and holdout_positive_share >= 0.5
        and expectancy_delta > 0
        and saved_loss_gt_missed
        and trade_count_ratio >= 0.75
        and full_period_damage >= 0.9
        and clean_precision_best >= 0.20
    ):
        decision = "STRONG_INFORMATION_EDGE"
        reason = "family expansion produced consistent OOS lift and economically usable behavior-state separation"
    elif (
        (positive_lift_exists or bad_recall_best >= 0.35)
        and expectancy_delta > 0
        and full_period_damage >= 0.8
        and trade_count_ratio >= 0.5
    ):
        decision = "PARTIAL_INFORMATION_EDGE"
        reason = "subset information edge exists but robustness remains uneven across holdouts"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "positive_oos_lift_exists": positive_lift_exists,
                "best_bad_state_recall": round(bad_recall_best, 6),
                "best_clean_state_precision": round(clean_precision_best, 6),
                "holdout_mean_lift": round(holdout_mean_lift, 6),
                "holdout_positive_share": round(holdout_positive_share, 6),
                "oos_expectancy_delta": round(expectancy_delta, 6),
                "trade_count_retention": round(trade_count_ratio, 6),
                "full_period_return_damage_ratio": round(full_period_damage, 6),
            }
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 335: information layer expansion for behavior-state predictability.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df, oos_df, full_df = _load_frozen_behavior_state()
    all_phase1_features = sorted({feature for features in PHASE1_FAMILIES.values() for feature in features})
    train_df, oos_df, full_df, _ = _add_train_only_bands(train_df, oos_df, full_df, all_phase1_features)

    family_defs_df = _family_definition_rows(train_df)
    ablation_df = _feature_family_ablation(train_df, oos_df, full_df)
    mapping_df = _feature_to_behavior_mapping(train_df)

    prediction_rows = []
    singleton_families = ["core_only"] + [_family_set_name(name) for name in PHASE1_FAMILIES if name != "core"] + ["core_plus_best_2_families", "core_plus_best_3_families"]
    datasets = {"train": train_df, "anchored_oos": oos_df, "full_period": full_df}
    for feature_set_name in singleton_families:
        features = _resolve_feature_set_features(train_df, feature_set_name, ablation_df)
        for scope_name, scoped in datasets.items():
            for target_name in ["multiclass", "bad_state", "clean_state", "continuation_quality_rank"]:
                for model_name in ["majority", "band_probability", "logistic"]:
                    row, _, _ = _evaluate_feature_set(train_df, scoped, target_name, features, feature_set_name, model_name)
                    row["scope"] = scope_name
                    row["feature_set"] = feature_set_name
                    row["saved_loss_proxy"] = math.nan
                    row["missed_gain_proxy"] = math.nan
                    row["oos_expectancy_delta_proxy"] = math.nan
                    prediction_rows.append(row)
    prediction_df = pd.DataFrame(prediction_rows).sort_values(["feature_set", "scope", "target", "model"]).reset_index(drop=True)

    economic_df, trade_delta_df = _economic_action_metrics(ablation_df, train_df, oos_df, full_df)
    oos_action = economic_df[economic_df["scope"] == "anchored_oos"].iloc[0]
    prediction_df.loc[prediction_df["scope"] == "anchored_oos", "saved_loss_proxy"] = float(oos_action["saved_loss"])
    prediction_df.loc[prediction_df["scope"] == "anchored_oos", "missed_gain_proxy"] = float(oos_action["missed_gain"])
    prediction_df.loc[prediction_df["scope"] == "anchored_oos", "oos_expectancy_delta_proxy"] = round(float(oos_action["diagnostic_expectancy"]) - float(oos_action["baseline_expectancy"]), 6)

    best_bad = _best_rows_by_target(ablation_df, "bad_state")
    best_clean = _best_rows_by_target(ablation_df, "clean_state")
    best_bad_features = _resolve_feature_set_features(train_df, str(best_bad["feature_set"]), ablation_df)
    best_clean_features = _resolve_feature_set_features(train_df, str(best_clean["feature_set"]), ablation_df)
    holdout_df = pd.concat(
        [
            _holdout_rows_for_group(train_df, "bad_state", str(best_bad["feature_set"]), str(best_bad["model"]), "symbol", best_bad_features),
            _holdout_rows_for_group(train_df, "bad_state", str(best_bad["feature_set"]), str(best_bad["model"]), "sector_bucket", best_bad_features),
            _holdout_rows_for_group(train_df, "bad_state", str(best_bad["feature_set"]), str(best_bad["model"]), "scenario_family", best_bad_features),
            _time_split_oos_rows(oos_df, train_df, "bad_state", str(best_bad["feature_set"]), str(best_bad["model"]), best_bad_features),
            _holdout_rows_for_group(train_df, "clean_state", str(best_clean["feature_set"]), str(best_clean["model"]), "symbol", best_clean_features),
            _holdout_rows_for_group(train_df, "clean_state", str(best_clean["feature_set"]), str(best_clean["model"]), "sector_bucket", best_clean_features),
            _holdout_rows_for_group(train_df, "clean_state", str(best_clean["feature_set"]), str(best_clean["model"]), "scenario_family", best_clean_features),
            _time_split_oos_rows(oos_df, train_df, "clean_state", str(best_clean["feature_set"]), str(best_clean["model"]), best_clean_features),
        ],
        ignore_index=True,
    )

    final_decision_df = _final_decision(ablation_df, holdout_df, economic_df)

    md_lines = [
        "# Task 335: Information Layer Expansion",
        "",
        f"- Final decision: `{final_decision_df.iloc[0]['decision']}`.",
        f"- Best bad-state feature set: `{best_bad.get('feature_set', 'n/a')}` via `{best_bad.get('model', 'n/a')}`.",
        f"- Best clean-state feature set: `{best_clean.get('feature_set', 'n/a')}` via `{best_clean.get('model', 'n/a')}`.",
        "",
        "## Feature Family Definitions",
        "",
    ]
    md_lines.extend(_markdown_table(family_defs_df))
    md_lines.extend(["", "## Feature Family Ablation", ""])
    md_lines.extend(_markdown_table(ablation_df[ablation_df["scope"] == "anchored_oos"].head(24)))
    md_lines.extend(["", "## Prediction Metrics", ""])
    md_lines.extend(_markdown_table(prediction_df[prediction_df["scope"] == "anchored_oos"].head(24)))
    md_lines.extend(["", "## Holdout Results", ""])
    md_lines.extend(_markdown_table(holdout_df.head(24)))
    md_lines.extend(["", "## Economic Action Test", ""])
    md_lines.extend(_markdown_table(economic_df))
    md_lines.extend(
        [
            "",
            "## Final Answer",
            "",
            f"- Current conclusion: `{final_decision_df.iloc[0]['decision']}`.",
            "- Phase 1 used repo-historical proxy families only.",
            "- Phase 2 blind spot remains true intraday breakout-quality information such as VWAP deviation and same-session continuation.",
            "- Next step is Phase 2 intraday ingestion only if the best Phase 1 family set shows partial edge with acceptable holdout robustness.",
        ]
    )

    family_defs_df.to_csv(out_dir / "task_335_feature_family_definitions.csv", index=False)
    ablation_df.to_csv(out_dir / "task_335_feature_family_ablation.csv", index=False)
    prediction_df.to_csv(out_dir / "task_335_prediction_metrics.csv", index=False)
    mapping_df.to_csv(out_dir / "task_335_feature_to_behavior_mapping.csv", index=False)
    economic_df.to_csv(out_dir / "task_335_economic_action_test.csv", index=False)
    trade_delta_df.to_csv(out_dir / "task_335_trade_level_delta.csv", index=False)
    holdout_df.to_csv(out_dir / "task_335_holdout_results.csv", index=False)
    final_decision_df.to_csv(out_dir / "task_335_final_decision.csv", index=False)
    (out_dir / "task_335_information_layer_expansion.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
