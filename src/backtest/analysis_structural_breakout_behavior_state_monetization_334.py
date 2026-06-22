from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.backtest.analysis_structural_breakout_behavior_clustered_state_333 import (
    BAD_CLUSTER_BASES,
    DEFAULT_OUT_DIR as TASK333_OUT_DIR,
    PRE_ENTRY_PREDICTOR_FEATURES,
)
from src.backtest.analysis_structural_breakout_regime_failure_diagnosis_328 import _distribution


DEFAULT_OUT_DIR = Path("docs/reports/task_334_behavior_state_monetization")
FROZEN_SELECTED_CLUSTERS = TASK333_OUT_DIR / "task_333_selected_behavior_clusters.csv"
BAD_STATE_BASES = {"dead_breakout", "early_failure", "weak_breakout", "volatile_whipsaw"}
CLEAN_STATE_BASE = "clean_continuation"
FULL_SIZE_MULTIPLIER = 1.25
TARGETS = ("multiclass", "bad_state", "clean_state")
CORE_FEATURES = PRE_ENTRY_PREDICTOR_FEATURES
MARKET_STRUCTURE_FEATURES = [
    "breadth_above_sma20",
    "breadth_above_sma50",
    "breadth_positive_20d",
    "dispersion_20d",
    "mean_pairwise_corr",
]
SETUP_CONTEXT_FEATURES = [
    "pre_breakout_distance_pct",
    "gap_over_planned_entry_pct",
    "breakout_strength_pct",
    "volume_confirmation_pre",
    "recent_failed_breakouts_20d",
]
CROWDING_FEATURES = [
    "top_sector_dominance_score",
    "semis_concentration_ratio",
    "tech_concentration_ratio",
    "sector_crowding_high",
    "sector_rs_percentile",
]
AXIS_STATE_ONLY_FEATURES = [
    "extension_pressure_state",
    "trend_quality_state",
    "participation_quality_state",
    "noise_pressure_state",
]
SCENARIO_FAMILY_FEATURES = ["scenario_family"]
HOLDOUT_MIN_TRADES = 40
RANDOM_STATE = 42


def _load_frozen_behavior_state() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(FROZEN_SELECTED_CLUSTERS)
    train_df = df[df["scope"] == "train"].copy().reset_index(drop=True)
    oos_df = df[df["scope"] == "anchored_oos"].copy().reset_index(drop=True)
    full_df = df[df["scope"] == "full_period"].copy().reset_index(drop=True)
    return train_df, oos_df, full_df


def _cluster_truth_stability(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    train_total = max(len(train_df), 1)
    oos_total = max(len(oos_df), 1)
    for cluster_label, train_scoped in train_df.groupby("cluster_label"):
        oos_scoped = oos_df[oos_df["cluster_label"].astype(str) == str(cluster_label)]
        train_share = float(len(train_scoped) / train_total)
        oos_share = float(len(oos_scoped) / oos_total)
        train_expectancy = float(pd.to_numeric(train_scoped["realized_R"], errors="coerce").mean())
        oos_expectancy = float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").mean()) if not oos_scoped.empty else 0.0
        persistence = (oos_expectancy / train_expectancy) if abs(train_expectancy) > 1e-9 else 0.0
        rows.append(
            {
                "cluster_label": str(cluster_label),
                "cluster_label_base": str(train_scoped["cluster_label_base"].iloc[0]),
                "train_trade_count": int(len(train_scoped)),
                "oos_trade_count": int(len(oos_scoped)),
                "train_cluster_share": round(train_share, 6),
                "oos_cluster_share": round(oos_share, 6),
                "train_oos_cluster_share_shift": round(oos_share - train_share, 6),
                "train_expectancy_R": round(train_expectancy, 6),
                "oos_expectancy_R": round(oos_expectancy, 6),
                "cluster_expectancy_persistence": round(persistence, 6),
                "train_path_entropy": round(float(pd.Series(train_scoped["path_type"].astype(str)).value_counts(normalize=True).pipe(lambda s: -(s * np.log2(s)).sum() if len(s) else 0.0)), 6),
                "oos_path_entropy": round(float(pd.Series(oos_scoped["path_type"].astype(str)).value_counts(normalize=True).pipe(lambda s: -(s * np.log2(s)).sum() if len(s) else 0.0)), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["cluster_expectancy_persistence", "train_trade_count"], ascending=[False, False]).reset_index(drop=True)


def _derive_target(df: pd.DataFrame, target_name: str) -> pd.Series:
    if target_name == "multiclass":
        return df["cluster_label"].astype(str)
    if target_name == "bad_state":
        return df["cluster_label_base"].astype(str).isin(BAD_STATE_BASES).astype(int)
    if target_name == "clean_state":
        return (df["cluster_label_base"].astype(str) == CLEAN_STATE_BASE).astype(int)
    raise ValueError(f"unknown target: {target_name}")


def _available_features(df: pd.DataFrame, features: list[str]) -> list[str]:
    return list(dict.fromkeys(feature for feature in features if feature in df.columns))


def _numeric_and_categorical(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_candidates = {
        "ret_20d_pre",
        "dist_to_sma200_pct",
        "rs_percentile_20d",
        "sector_breadth",
        "vol_contraction_ratio",
        "breakout_strength_pct",
        "breadth_above_sma20",
        "breadth_above_sma50",
        "breadth_positive_20d",
        "dispersion_20d",
        "mean_pairwise_corr",
        "pre_breakout_distance_pct",
        "gap_over_planned_entry_pct",
        "volume_confirmation_pre",
        "recent_failed_breakouts_20d",
        "top_sector_dominance_score",
        "semis_concentration_ratio",
        "tech_concentration_ratio",
        "sector_rs_percentile",
    }
    numeric_cols = [feature for feature in features if feature in numeric_candidates]
    categorical_cols = [feature for feature in features if feature not in numeric_cols]
    return numeric_cols, categorical_cols


def _fit_logistic(train_df: pd.DataFrame, y_train: pd.Series, features: list[str]) -> Pipeline:
    numeric_cols, categorical_cols = _numeric_and_categorical(features)
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=[("impute", SimpleImputer(strategy="median"))]), numeric_cols),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
        ]
    )
    model = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("model", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        ]
    )
    model.fit(train_df[features], y_train)
    return model


def _majority_predictor(y_train: pd.Series, count: int) -> tuple[np.ndarray, list[dict[str, float]]]:
    majority = y_train.mode().iloc[0]
    classes = sorted(y_train.astype(str).unique().tolist())
    if y_train.dtype != object and not isinstance(majority, str):
        classes = sorted(set(y_train.tolist()))
    preds = np.asarray([majority] * count)
    probs = []
    for _ in range(count):
        probs.append({str(cls): (1.0 if cls == majority else 0.0) for cls in classes})
    return preds, probs


def _build_prob_tables(train_df: pd.DataFrame, y_train: pd.Series, features: list[str]) -> dict[str, dict[str, dict[str, float]]]:
    tables: dict[str, dict[str, dict[str, float]]] = {}
    for feature in features:
        tables[feature] = {}
        for value, scoped in train_df.groupby(feature):
            scoped_y = y_train.loc[scoped.index]
            tables[feature][str(value)] = _distribution(scoped_y.astype(str))
    return tables


def _predict_from_tables(df: pd.DataFrame, tables: dict[str, dict[str, dict[str, float]]], classes: list[str]) -> tuple[np.ndarray, list[dict[str, float]]]:
    preds = []
    probs = []
    for _, row in df.iterrows():
        agg = {cls: 0.0 for cls in classes}
        used = 0
        for feature, feature_table in tables.items():
            value = str(row.get(feature, ""))
            dist = feature_table.get(value)
            if not dist:
                continue
            for cls in classes:
                agg[cls] += float(dist.get(str(cls), 0.0))
            used += 1
        if used == 0:
            avg = {cls: 1.0 / max(len(classes), 1) for cls in classes}
        else:
            avg = {cls: agg[cls] / used for cls in classes}
        pred = max(avg.items(), key=lambda item: item[1])[0]
        preds.append(pred)
        probs.append(avg)
    return np.asarray(preds, dtype=object), probs


def _predict_with_model(model: Pipeline, df: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, list[dict[str, float]]]:
    preds = model.predict(df[features])
    classes = [str(v) for v in model.classes_]
    probas = model.predict_proba(df[features])
    probs = [{classes[idx]: float(row[idx]) for idx in range(len(classes))} for row in probas]
    return preds, probs


def _metric_row(y_true: pd.Series, preds: np.ndarray, probs: list[dict[str, float]], model_name: str, scope_name: str, target_name: str) -> dict[str, Any]:
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
    }
    if target_name in {"bad_state", "clean_state"}:
        positive_label = "1"
        pred_pos = pred_series == positive_label
        true_pos = y_true_series == positive_label
        precision = float((pred_pos & true_pos).sum() / max(int(pred_pos.sum()), 1))
        recall = float((pred_pos & true_pos).sum() / max(int(true_pos.sum()), 1))
        row["precision_positive"] = round(precision, 6)
        row["recall_positive"] = round(recall, 6)
    else:
        row["precision_positive"] = math.nan
        row["recall_positive"] = math.nan
    return row


def _single_feature_ceiling(train_df: pd.DataFrame, oos_df: pd.DataFrame, target_name: str, features: list[str]) -> pd.DataFrame:
    y_train = _derive_target(train_df, target_name)
    y_oos = _derive_target(oos_df, target_name)
    rows = []
    for feature in features:
        if feature not in train_df.columns or feature not in oos_df.columns:
            continue
        tables = _build_prob_tables(train_df[[feature]], y_train, [feature])
        preds, probs = _predict_from_tables(oos_df[[feature]], tables, sorted(y_train.astype(str).unique()))
        row = _metric_row(y_oos, preds, probs, f"single_feature::{feature}", "anchored_oos", target_name)
        row["feature_family"] = "single_feature"
        rows.append(row)
    return pd.DataFrame(rows).sort_values("lift_vs_baseline", ascending=False).reset_index(drop=True)


def _evaluate_feature_set(train_df: pd.DataFrame, eval_df: pd.DataFrame, target_name: str, features: list[str], family_name: str, model_kind: str) -> dict[str, Any]:
    features = _available_features(train_df, features)
    y_train = _derive_target(train_df, target_name)
    y_eval = _derive_target(eval_df, target_name)
    classes = sorted(y_train.astype(str).unique())
    if model_kind == "majority":
        preds, probs = _majority_predictor(y_train.astype(str), len(eval_df))
    elif model_kind == "band_probability":
        tables = _build_prob_tables(train_df, y_train, features)
        preds, probs = _predict_from_tables(eval_df, tables, classes)
    elif model_kind == "logistic":
        model = _fit_logistic(train_df, y_train, features)
        preds, probs = _predict_with_model(model, eval_df, features)
    else:
        raise ValueError(model_kind)
    row = _metric_row(y_eval, preds, probs, model_kind, "anchored_oos" if "anchored_oos" in set(eval_df.get("scope", [])) else "eval", target_name)
    row["feature_family"] = family_name
    row["feature_count"] = len(features)
    return row


def _predictability_ceiling(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    family_sets = {
        "core_feature_set": CORE_FEATURES,
        "axis_state_only": AXIS_STATE_ONLY_FEATURES,
        "scenario_family_only": SCENARIO_FAMILY_FEATURES,
    }
    for target_name in TARGETS:
        y_train = _derive_target(train_df, target_name)
        majority_preds, majority_probs = _majority_predictor(y_train.astype(str), len(oos_df))
        majority_row = _metric_row(_derive_target(oos_df, target_name), majority_preds, majority_probs, "majority", "anchored_oos", target_name)
        majority_row["feature_family"] = "baseline"
        majority_row["feature_count"] = 0
        rows.append(majority_row)
        for family_name, features in family_sets.items():
            rows.append(_evaluate_feature_set(train_df, oos_df, target_name, features, family_name, "band_probability"))
            rows.append(_evaluate_feature_set(train_df, oos_df, target_name, features, family_name, "logistic"))
    out = pd.DataFrame(rows)
    return out.sort_values(["target", "lift_vs_baseline", "model"], ascending=[True, False, True]).reset_index(drop=True)


def _feature_family_incremental_lift(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    families = {
        "market_structure": MARKET_STRUCTURE_FEATURES,
        "setup_context": SETUP_CONTEXT_FEATURES,
        "crowding": CROWDING_FEATURES,
    }
    for target_name in ("bad_state", "clean_state"):
        base_row = _evaluate_feature_set(train_df, oos_df, target_name, CORE_FEATURES, "core_feature_set", "logistic")
        for family_name, family_features in families.items():
            combined = CORE_FEATURES + family_features
            family_row = _evaluate_feature_set(train_df, oos_df, target_name, combined, family_name, "logistic")
            rows.append(
                {
                    "target": target_name,
                    "family_name": family_name,
                    "base_lift": base_row["lift_vs_baseline"],
                    "family_lift": family_row["lift_vs_baseline"],
                    "lift_delta": round(float(family_row["lift_vs_baseline"]) - float(base_row["lift_vs_baseline"]), 6),
                    "base_recall_positive": base_row["recall_positive"],
                    "family_recall_positive": family_row["recall_positive"],
                    "recall_delta": round(float(family_row["recall_positive"]) - float(base_row["recall_positive"]), 6),
                    "accepted": bool(float(family_row["lift_vs_baseline"]) > float(base_row["lift_vs_baseline"]) or float(family_row["recall_positive"]) > float(base_row["recall_positive"])),
                }
            )
    return pd.DataFrame(rows).sort_values(["target", "accepted", "lift_delta", "recall_delta"], ascending=[True, False, False, False]).reset_index(drop=True)


def _expanded_family_candidate_metrics(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    family_sets = {
        "market_structure": CORE_FEATURES + MARKET_STRUCTURE_FEATURES,
        "setup_context": CORE_FEATURES + SETUP_CONTEXT_FEATURES,
        "crowding": CORE_FEATURES + CROWDING_FEATURES,
    }
    for target_name in ("bad_state", "clean_state"):
        for family_name, features in family_sets.items():
            rows.append(_evaluate_feature_set(train_df, oos_df, target_name, features, family_name, "band_probability"))
            rows.append(_evaluate_feature_set(train_df, oos_df, target_name, features, family_name, "logistic"))
    return pd.DataFrame(rows).sort_values(["target", "lift_vs_baseline", "recall_positive", "accuracy"], ascending=[True, False, False, False]).reset_index(drop=True)


def _group_holdout_lift(train_df: pd.DataFrame, target_name: str, features: list[str], group_col: str, top_n: int = 10) -> pd.DataFrame:
    if group_col not in train_df.columns:
        return pd.DataFrame()
    counts = train_df[group_col].astype(str).value_counts()
    groups = [group for group, count in counts.items() if int(count) >= HOLDOUT_MIN_TRADES][:top_n]
    rows = []
    for group in groups:
        holdout_df = train_df[train_df[group_col].astype(str) == str(group)].copy()
        fit_df = train_df[train_df[group_col].astype(str) != str(group)].copy()
        if holdout_df.empty or fit_df.empty:
            continue
        eval_row = _evaluate_feature_set(fit_df, holdout_df, target_name, features, f"holdout::{group_col}", "logistic")
        rows.append(
            {
                "target": target_name,
                "holdout_type": group_col,
                "holdout_value": str(group),
                "accuracy": eval_row["accuracy"],
                "lift_vs_baseline": eval_row["lift_vs_baseline"],
                "recall_positive": eval_row["recall_positive"],
            }
        )
    return pd.DataFrame(rows)


def _diagnostic_overlay(df: pd.DataFrame, bad_preds: np.ndarray, clean_preds: np.ndarray, model_name: str, scope_name: str) -> tuple[dict[str, Any], pd.DataFrame]:
    out = df.copy()
    out["pred_bad_state"] = pd.Series(bad_preds, index=out.index).astype(str)
    out["pred_clean_state"] = pd.Series(clean_preds, index=out.index).astype(str)
    multiplier = np.where(out["pred_bad_state"] == "1", 0.0, np.where(out["pred_clean_state"] == "1", FULL_SIZE_MULTIPLIER, 1.0))
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
        "policy_name": model_name,
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
    delta_df["policy_name"] = model_name
    return metrics, delta_df


def _choose_best_binary_model(ceiling_df: pd.DataFrame, target_name: str) -> dict[str, Any]:
    scoped = ceiling_df[(ceiling_df["target"] == target_name) & (ceiling_df["model"] != "majority")].copy()
    if scoped.empty:
        return {}
    scoped = scoped.sort_values(["recall_positive", "lift_vs_baseline", "accuracy"], ascending=[False, False, False])
    return scoped.iloc[0].to_dict()


def _combine_binary_candidates(ceiling_df: pd.DataFrame, expanded_family_df: pd.DataFrame) -> pd.DataFrame:
    base = ceiling_df[ceiling_df["target"].isin(["bad_state", "clean_state"])].copy()
    cols = sorted(set(base.columns) | set(expanded_family_df.columns))
    return pd.concat([base.reindex(columns=cols), expanded_family_df.reindex(columns=cols)], ignore_index=True).reset_index(drop=True)


def _family_features(family_name: str) -> list[str]:
    family_map = {
        "core_feature_set": CORE_FEATURES,
        "axis_state_only": AXIS_STATE_ONLY_FEATURES,
        "scenario_family_only": SCENARIO_FAMILY_FEATURES,
        "market_structure": CORE_FEATURES + MARKET_STRUCTURE_FEATURES,
        "setup_context": CORE_FEATURES + SETUP_CONTEXT_FEATURES,
        "crowding": CORE_FEATURES + CROWDING_FEATURES,
    }
    return family_map[family_name]


def _fit_best_model(train_df: pd.DataFrame, target_name: str, family_name: str, model_name: str) -> Any:
    features = _available_features(train_df, _family_features(family_name))
    y_train = _derive_target(train_df, target_name)
    if model_name == "band_probability":
        return ("band_probability", features, _build_prob_tables(train_df, y_train, features), sorted(y_train.astype(str).unique()))
    if model_name == "logistic":
        return ("logistic", features, _fit_logistic(train_df, y_train, features))
    raise ValueError(model_name)


def _predict_best_model(model_payload: Any, df: pd.DataFrame) -> np.ndarray:
    model_type = model_payload[0]
    if model_type == "band_probability":
        _, features, tables, classes = model_payload
        preds, _ = _predict_from_tables(df[features], tables, classes)
        return preds
    if model_type == "logistic":
        _, features, model = model_payload
        preds, _ = _predict_with_model(model, df, features)
        return preds
    raise ValueError(model_type)


def _target_design_comparison(candidate_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target_name, scoped in candidate_df.groupby("target"):
        non_majority = scoped[scoped["model"] != "majority"].copy()
        if non_majority.empty:
            continue
        ranked = non_majority.sort_values(["recall_positive", "lift_vs_baseline", "accuracy"], ascending=[False, False, False])
        best = ranked.iloc[0]
        rows.append(
            {
                "target": target_name,
                "best_feature_family": str(best["feature_family"]),
                "best_model": str(best["model"]),
                "accuracy": round(float(best["accuracy"]), 6),
                "lift_vs_baseline": round(float(best["lift_vs_baseline"]), 6),
                "recall_positive": round(float(best.get("recall_positive", math.nan)), 6) if not pd.isna(best.get("recall_positive", math.nan)) else math.nan,
                "precision_positive": round(float(best.get("precision_positive", math.nan)), 6) if not pd.isna(best.get("precision_positive", math.nan)) else math.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("target").reset_index(drop=True)


def _production_candidate_selection(
    cluster_stability_df: pd.DataFrame,
    ceiling_df: pd.DataFrame,
    family_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    diagnostic_df: pd.DataFrame,
    ) -> pd.DataFrame:
    all_candidates = _combine_binary_candidates(ceiling_df, family_df)
    best_bad = _choose_best_binary_model(all_candidates, "bad_state")
    best_action_oos = diagnostic_df[diagnostic_df["scope"] == "anchored_oos"].sort_values("diagnostic_expectancy", ascending=False).iloc[0]
    best_action_full = diagnostic_df[diagnostic_df["scope"] == "full_period"].sort_values("diagnostic_expectancy", ascending=False).iloc[0]
    holdout_mean_lift = float(pd.to_numeric(holdout_df["lift_vs_baseline"], errors="coerce").mean()) if not holdout_df.empty else -999.0
    decision = "NO_EDGE"
    rationale = "current information layer does not produce deployable OOS predictive edge"
    if (
        float(best_bad.get("recall_positive", 0.0)) > 0.20
        and float(best_action_oos["diagnostic_expectancy"]) > float(best_action_oos["baseline_expectancy"])
        and float(best_action_full["diagnostic_return_proxy"]) >= float(best_action_full["baseline_return_proxy"]) * 0.90
        and float(best_action_oos["saved_loss"]) > float(best_action_oos["missed_gain"])
        and holdout_mean_lift > 0.0
    ):
        decision = "PARTIAL_EDGE"
        rationale = "bad-state avoidance shows positive OOS economic relevance with tolerable full-period damage"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": rationale,
                "best_bad_target_model": f"{best_bad.get('feature_family', 'n/a')}::{best_bad.get('model', 'n/a')}",
                "best_bad_state_recall": round(float(best_bad.get("recall_positive", 0.0)), 6),
                "oos_diagnostic_expectancy_delta": round(float(best_action_oos["diagnostic_expectancy"]) - float(best_action_oos["baseline_expectancy"]), 6),
                "full_period_return_damage_ratio": round(float(best_action_full["diagnostic_return_proxy"]) / max(float(best_action_full["baseline_return_proxy"]), 1e-9), 6),
                "mean_holdout_lift": round(holdout_mean_lift, 6),
            }
        ]
    )


def _markdown_table(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["_No rows_"]
    cols = [str(column) for column in df.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for record in df.to_dict("records"):
        row = []
        for col in cols:
            value = record.get(col, "")
            if isinstance(value, float):
                row.append("" if math.isnan(value) else f"{value:.6g}")
            else:
                row.append(str(value))
        lines.append("| " + " | ".join(row) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 334: behavior-state monetization audit.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df, oos_df, full_df = _load_frozen_behavior_state()
    cluster_stability_df = _cluster_truth_stability(train_df, oos_df)
    ceiling_df = _predictability_ceiling(train_df, oos_df)
    single_feature_rows = pd.concat(
        [
            _single_feature_ceiling(train_df, oos_df, "bad_state", CORE_FEATURES + MARKET_STRUCTURE_FEATURES + SETUP_CONTEXT_FEATURES + CROWDING_FEATURES),
            _single_feature_ceiling(train_df, oos_df, "clean_state", CORE_FEATURES + MARKET_STRUCTURE_FEATURES + SETUP_CONTEXT_FEATURES + CROWDING_FEATURES),
        ],
        ignore_index=True,
    )
    family_df = _feature_family_incremental_lift(train_df, oos_df)
    expanded_family_df = _expanded_family_candidate_metrics(train_df, oos_df)
    all_binary_candidates = _combine_binary_candidates(ceiling_df, expanded_family_df)
    target_design_df = _target_design_comparison(all_binary_candidates)

    best_bad = _choose_best_binary_model(all_binary_candidates, "bad_state")
    best_clean = _choose_best_binary_model(all_binary_candidates, "clean_state")
    bad_payload = _fit_best_model(train_df, "bad_state", str(best_bad["feature_family"]), str(best_bad["model"]))
    clean_payload = _fit_best_model(train_df, "clean_state", str(best_clean["feature_family"]), str(best_clean["model"]))
    bad_holdout_features = _available_features(train_df, _family_features(str(best_bad["feature_family"])))
    holdout_df = pd.concat(
        [
            _group_holdout_lift(train_df, "bad_state", bad_holdout_features, "sector_bucket"),
            _group_holdout_lift(train_df, "bad_state", bad_holdout_features, "symbol"),
        ],
        ignore_index=True,
    )

    diagnostic_rows = []
    trade_delta_rows = []
    for scope_name, scoped_df in (("train", train_df), ("anchored_oos", oos_df), ("full_period", full_df)):
        bad_preds = _predict_best_model(bad_payload, scoped_df)
        clean_preds = _predict_best_model(clean_payload, scoped_df)
        metrics, delta_df = _diagnostic_overlay(scoped_df, bad_preds, clean_preds, "bad_skip_clean_overweight", scope_name)
        diagnostic_rows.append(metrics)
        trade_delta_rows.append(delta_df)
    diagnostic_df = pd.DataFrame(diagnostic_rows).sort_values("scope").reset_index(drop=True)
    trade_delta_df = pd.concat(trade_delta_rows, ignore_index=True)

    selection_df = _production_candidate_selection(cluster_stability_df, ceiling_df, family_df, holdout_df, diagnostic_df)

    md_lines = [
        "# Task 334: Behavior State Monetization",
        "",
        "## Core Answer",
        "",
        f"- Final production candidate status: `{selection_df.iloc[0]['decision']}`.",
        f"- Best bad-state predictor: `{selection_df.iloc[0]['best_bad_target_model']}`.",
        "",
        "## Cluster Truth Stability",
        "",
    ]
    md_lines.extend(_markdown_table(cluster_stability_df))
    md_lines.extend(["", "## Predictability Ceiling", ""])
    md_lines.extend(_markdown_table(ceiling_df))
    md_lines.extend(["", "## Target Design Comparison", ""])
    md_lines.extend(_markdown_table(target_design_df))
    md_lines.extend(["", "## Feature Family Expansion", ""])
    md_lines.extend(_markdown_table(family_df))
    md_lines.extend(["", "## Holdout Audit", ""])
    md_lines.extend(_markdown_table(holdout_df))
    md_lines.extend(["", "## Economic Action Diagnostic", ""])
    md_lines.extend(_markdown_table(diagnostic_df))

    cluster_stability_df.to_csv(out_dir / "task_334_cluster_truth_stability.csv", index=False)
    ceiling_df.to_csv(out_dir / "task_334_predictability_ceiling.csv", index=False)
    single_feature_rows.to_csv(out_dir / "task_334_single_feature_ceiling.csv", index=False)
    family_df.to_csv(out_dir / "task_334_feature_family_incremental_lift.csv", index=False)
    expanded_family_df.to_csv(out_dir / "task_334_expanded_family_candidate_metrics.csv", index=False)
    holdout_df.to_csv(out_dir / "task_334_symbol_sector_holdout.csv", index=False)
    target_design_df.to_csv(out_dir / "task_334_target_design_comparison.csv", index=False)
    diagnostic_df.to_csv(out_dir / "task_334_economic_action_diagnostic.csv", index=False)
    trade_delta_df.to_csv(out_dir / "task_334_trade_level_overlay_delta.csv", index=False)
    selection_df.to_csv(out_dir / "task_334_production_candidate_selection.csv", index=False)
    (out_dir / "task_334_behavior_state_monetization.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
