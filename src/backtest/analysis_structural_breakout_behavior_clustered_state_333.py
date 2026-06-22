from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from src.backtest.analysis_structural_breakout_path_conditioned_entry_327 import ENTRY_FEATURES
from src.backtest.analysis_structural_breakout_regime_failure_diagnosis_328 import (
    DEFAULT_BASE_DIR,
    _distribution,
    _labeled_trade_frames,
    _series_entropy,
    _total_variation_distance,
)
from src.backtest.analysis_structural_breakout_state_model_redesign_329 import _attach_axis_states, _drift_sensitivity, _oos_retention, _state_metrics
from src.backtest.analysis_structural_breakout_state_space_realignment_332 import (
    RANKED_INPUT,
    _candidate_c_builder,
    _dense_candidate_c_parents,
)
from src.backtest.analysis_structural_breakout_state_model_stabilization_330 import _build_generic_fold_map


DEFAULT_OUT_DIR = Path("docs/reports/task_333_behavior_clustered_state_model")
BEHAVIOR_CLUSTER_FEATURES = [
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
]
PRE_ENTRY_PREDICTOR_FEATURES = [
    "ret_20d_pre",
    "dist_to_sma200_pct",
    "rs_percentile_20d",
    "sector_breadth",
    "vol_contraction_ratio",
    "breakout_strength_pct",
    "extension_pressure_state",
    "trend_quality_state",
    "participation_quality_state",
    "noise_pressure_state",
]
OOS_MIN_COUNT = 5
CLUSTER_METHODS = ("kmeans", "agglomerative", "gaussian_mixture")
CLUSTER_RANGE = range(4, 9)
RANDOM_STATE = 42
BAD_CLUSTER_BASES = {"early_failure", "dead_breakout"}
REDUCE_CLUSTER_BASES = {"volatile_whipsaw"}
FULLSIZE_CLUSTER_BASES = {"clean_continuation"}
NORMAL_CLUSTER_BASES = {"slow_grind", "failed_pop", "uneven_continuation", "weak_breakout"}


def _prepare_trade_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df, oos_df, full_df = _labeled_trade_frames(
        base_dir=DEFAULT_BASE_DIR,
        ranked_input=Path(RANKED_INPUT),
        candidate_pool=10,
        jobs=2,
    )
    train_df = _attach_axis_states(train_df)
    oos_df = _attach_axis_states(oos_df)
    full_df = _attach_axis_states(full_df)
    return train_df, oos_df, full_df


def _fit_behavior_scaler(train_df: pd.DataFrame) -> StandardScaler:
    scaler = StandardScaler()
    scaler.fit(train_df[BEHAVIOR_CLUSTER_FEATURES].astype(float))
    return scaler


def _transform_behavior_features(df: pd.DataFrame, scaler: StandardScaler) -> np.ndarray:
    return scaler.transform(df[BEHAVIOR_CLUSTER_FEATURES].astype(float))


def _fit_cluster_model(method: str, k: int, train_x: np.ndarray) -> Any:
    if method == "kmeans":
        model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=20)
        model.fit(train_x)
        return model
    if method == "agglomerative":
        model = AgglomerativeClustering(n_clusters=k)
        labels = model.fit_predict(train_x)
        return {"model": model, "train_labels": labels}
    if method == "gaussian_mixture":
        model = GaussianMixture(n_components=k, random_state=RANDOM_STATE, covariance_type="full")
        model.fit(train_x)
        return model
    raise ValueError(f"unsupported method: {method}")


def _cluster_centroids(train_x: np.ndarray, labels: np.ndarray) -> np.ndarray:
    centroids = []
    for label in sorted(set(int(v) for v in labels)):
        centroids.append(train_x[labels == label].mean(axis=0))
    return np.asarray(centroids, dtype=float)


def _predict_cluster_labels(model: Any, method: str, train_x: np.ndarray, x: np.ndarray) -> np.ndarray:
    if method == "kmeans":
        return model.predict(x)
    if method == "gaussian_mixture":
        return model.predict(x)
    if method == "agglomerative":
        train_labels = np.asarray(model["train_labels"], dtype=int)
        centroids = _cluster_centroids(train_x, train_labels)
        distances = ((x[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        return distances.argmin(axis=1)
    raise ValueError(f"unsupported method: {method}")


def _assign_clusters(train_df: pd.DataFrame, oos_df: pd.DataFrame, full_df: pd.DataFrame, scaler: StandardScaler, method: str, k: int) -> tuple[Any, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_x = _transform_behavior_features(train_df, scaler)
    oos_x = _transform_behavior_features(oos_df, scaler)
    full_x = _transform_behavior_features(full_df, scaler)
    model = _fit_cluster_model(method, k, train_x)
    train_labels = _predict_cluster_labels(model, method, train_x, train_x)
    oos_labels = _predict_cluster_labels(model, method, train_x, oos_x)
    full_labels = _predict_cluster_labels(model, method, train_x, full_x)

    def _with_labels(df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
        out = df.copy()
        out["behavior_cluster_id"] = labels.astype(int)
        return out

    return model, _with_labels(train_df, train_labels), _with_labels(oos_df, oos_labels), _with_labels(full_df, full_labels)


def _within_cluster_behavior_variance(df: pd.DataFrame) -> float:
    rows = []
    for _, scoped in df.groupby("behavior_cluster_id"):
        rows.append(float(pd.to_numeric(scoped[BEHAVIOR_CLUSTER_FEATURES].stack(), errors="coerce").var(ddof=0)))
    return round(float(pd.Series(rows, dtype=float).mean()), 6) if rows else 0.0


def _cluster_density_stats(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> tuple[int, int, float]:
    states = sorted(set(train_df["behavior_cluster_id"].astype(int)) | set(oos_df["behavior_cluster_id"].astype(int)))
    min_train = min(int((train_df["behavior_cluster_id"] == state).sum()) for state in states) if states else 0
    min_oos = min(int((oos_df["behavior_cluster_id"] == state).sum()) for state in states) if states else 0
    sparse = sum(
        1
        for state in states
        if int((train_df["behavior_cluster_id"] == state).sum()) < 25 or int((oos_df["behavior_cluster_id"] == state).sum()) < OOS_MIN_COUNT
    )
    sparsity = float(sparse / max(len(states), 1))
    return min_train, min_oos, round(sparsity, 6)


def _cluster_model_candidate_row(method: str, k: int, train_df: pd.DataFrame, oos_df: pd.DataFrame) -> dict[str, Any]:
    metrics = _state_metrics(train_df, "behavior_cluster_id")
    min_train, min_oos, sparsity_risk = _cluster_density_stats(train_df, oos_df)
    cluster_share_shift = _total_variation_distance(
        _distribution(train_df["behavior_cluster_id"].astype(str)),
        _distribution(oos_df["behavior_cluster_id"].astype(str)),
    )
    return {
        "method": method,
        "k": k,
        "within_cluster_behavior_variance": _within_cluster_behavior_variance(train_df),
        "path_entropy": metrics["within_state_path_entropy_mean"],
        "between_cluster_expectancy_dispersion": metrics["between_state_expectancy_dispersion"],
        "oos_cluster_assignment_stability": round(1.0 - cluster_share_shift, 6),
        "oos_linkage_retention": _oos_retention(train_df, oos_df, "behavior_cluster_id"),
        "min_train_cluster_count": min_train,
        "min_oos_cluster_count": min_oos,
        "sparsity_risk": sparsity_risk,
    }


def _candidate_sort_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["selection_rank_1"] = out["oos_linkage_retention"].astype(float)
    out["selection_rank_2"] = out["between_cluster_expectancy_dispersion"].astype(float)
    out["selection_rank_3"] = -out["within_cluster_behavior_variance"].astype(float)
    out["selection_rank_4"] = -out["path_entropy"].astype(float)
    out["selection_rank_5"] = out["min_train_cluster_count"].astype(float)
    out["selection_rank_6"] = out["oos_cluster_assignment_stability"].astype(float)
    out["selection_rank_7"] = -out["sparsity_risk"].astype(float)
    return out


def _select_best_cluster_candidate(candidate_df: pd.DataFrame) -> dict[str, Any]:
    ranked = _candidate_sort_key(candidate_df).sort_values(
        [
            "selection_rank_1",
            "selection_rank_2",
            "selection_rank_3",
            "selection_rank_4",
            "selection_rank_5",
            "selection_rank_6",
            "selection_rank_7",
            "method",
            "k",
        ],
        ascending=[False, False, False, False, False, False, False, True, True],
    )
    return ranked.iloc[0].to_dict()


def _cluster_diagnostics(df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    rows = []
    total_r = float(pd.to_numeric(df["realized_R"], errors="coerce").sum()) if not df.empty else 0.0
    for cluster_id, scoped in df.groupby("behavior_cluster_id"):
        path_dist = _distribution(scoped["path_type"])
        rows.append(
            {
                "scope": scope_name,
                "behavior_cluster_id": int(cluster_id),
                "trade_count": int(len(scoped)),
                "expectancy_R": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()), 6),
                "win_rate": round(float((pd.to_numeric(scoped["realized_R"], errors="coerce") > 0).mean()), 6),
                "total_R": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").sum()), 6),
                "cluster_pnl_share": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").sum()) / total_r, 6) if abs(total_r) > 1e-9 else 0.0,
                "avg_follow_through_3d": round(float(pd.to_numeric(scoped["follow_through_3d_pct"], errors="coerce").mean()), 6),
                "avg_follow_through_5d": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").mean()), 6),
                "avg_retrace_3d": round(float(pd.to_numeric(scoped["retrace_3d_pct"], errors="coerce").mean()), 6),
                "avg_retrace_5d": round(float(pd.to_numeric(scoped["retrace_5d_pct"], errors="coerce").mean()), 6),
                "avg_MAE": round(float(pd.to_numeric(scoped["mae_5d_pct"], errors="coerce").mean()), 6),
                "avg_MFE": round(float(pd.to_numeric(scoped["mfe_5d_pct"], errors="coerce").mean()), 6),
                "avg_holding_days": round(float(pd.to_numeric(scoped["holding_days"], errors="coerce").mean()), 6),
                "path_entropy": round(_series_entropy(scoped["path_type"]), 6),
                "internal_R_variance": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0)), 6),
                "dominant_path_share": round(float(max(path_dist.values()) if path_dist else 0.0), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "behavior_cluster_id"]).reset_index(drop=True)


def _cluster_train_oos_deltas(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    train_total = max(len(train_df), 1)
    oos_total = max(len(oos_df), 1)
    for cluster_id in sorted(set(train_df["behavior_cluster_id"].astype(int)) | set(oos_df["behavior_cluster_id"].astype(int))):
        train_scoped = train_df[train_df["behavior_cluster_id"] == cluster_id]
        oos_scoped = oos_df[oos_df["behavior_cluster_id"] == cluster_id]
        train_share = float(len(train_scoped) / train_total)
        oos_share = float(len(oos_scoped) / oos_total)
        train_expectancy = float(pd.to_numeric(train_scoped["realized_R"], errors="coerce").mean()) if not train_scoped.empty else 0.0
        oos_expectancy = float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").mean()) if not oos_scoped.empty else 0.0
        retention = (oos_expectancy / train_expectancy) if abs(train_expectancy) > 1e-9 else 0.0
        rows.append(
            {
                "behavior_cluster_id": int(cluster_id),
                "OOS_retention": round(retention, 6),
                "train_vs_OOS_cluster_share_shift": round(oos_share - train_share, 6),
            }
        )
    return pd.DataFrame(rows)


def _label_cluster_rows(train_diag_df: pd.DataFrame) -> pd.DataFrame:
    q_ft = float(train_diag_df["avg_follow_through_5d"].quantile(0.7))
    q_low_ft = float(train_diag_df["avg_follow_through_3d"].quantile(0.3))
    q_retrace = float(train_diag_df["avg_retrace_5d"].quantile(0.7))
    q_mae = float(train_diag_df["avg_MAE"].quantile(0.7))
    q_mfe = float(train_diag_df["avg_MFE"].quantile(0.7))
    q_low_mfe = float(train_diag_df["avg_MFE"].quantile(0.3))
    q_hold = float(train_diag_df["avg_holding_days"].quantile(0.7))
    rows = []
    used: dict[str, int] = {}
    for record in train_diag_df.sort_values("behavior_cluster_id").to_dict("records"):
        expectancy = float(record["expectancy_R"])
        ft3 = float(record["avg_follow_through_3d"])
        ft5 = float(record["avg_follow_through_5d"])
        retrace = float(record["avg_retrace_5d"])
        mae = float(record["avg_MAE"])
        mfe = float(record["avg_MFE"])
        holding = float(record["avg_holding_days"])
        if expectancy > 0 and ft5 >= q_ft and retrace < q_retrace and mae < q_mae:
            base = "clean_continuation"
        elif expectancy <= 0 and ft3 <= q_low_ft and mfe <= q_low_mfe:
            base = "dead_breakout"
        elif expectancy <= 0 and retrace >= q_retrace and mae >= q_mae:
            base = "early_failure"
        elif mfe >= q_mfe and mae >= q_mae:
            base = "volatile_whipsaw"
        elif ft3 <= q_low_ft and ft5 > ft3 and holding >= q_hold:
            base = "slow_grind"
        elif mfe >= q_mfe and retrace >= q_retrace:
            base = "failed_pop"
        elif expectancy > 0:
            base = "uneven_continuation"
        else:
            base = "weak_breakout"
        used[base] = used.get(base, 0) + 1
        label = base if used[base] == 1 else f"{base}_{used[base]}"
        rows.append(
            {
                "behavior_cluster_id": int(record["behavior_cluster_id"]),
                "cluster_label": label,
                "cluster_label_base": base,
                "label_rationale": f"expectancy={expectancy:.3f}; ft5={ft5:.3f}; retrace5={retrace:.3f}; mae={mae:.3f}; mfe={mfe:.3f}",
            }
        )
    return pd.DataFrame(rows)


def _selected_behavior_clusters(df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
    label_lookup = labels_df.set_index("behavior_cluster_id")["cluster_label"].to_dict()
    base_lookup = labels_df.set_index("behavior_cluster_id")["cluster_label_base"].to_dict()
    out = df.copy()
    out["cluster_label"] = out["behavior_cluster_id"].map(label_lookup)
    out["cluster_label_base"] = out["behavior_cluster_id"].map(base_lookup)
    return out


def _rebuild_task329_and_candidate_c(train_df: pd.DataFrame, oos_df: pd.DataFrame, full_df: pd.DataFrame) -> tuple[tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame], tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    task329_axes = ["extension_pressure", "trend_quality", "participation_quality"]
    task329_train = train_df.copy()
    task329_oos = oos_df.copy()
    task329_full = full_df.copy()
    raw_train = task329_train.apply(lambda row: "|".join(f"{axis}:{row.get(f'{axis}_state', 'unknown')}" for axis in task329_axes), axis=1)
    task329_map = _build_generic_fold_map(raw_train)
    for df in (task329_train, task329_oos, task329_full):
        raw_values = df.apply(lambda row: "|".join(f"{axis}:{row.get(f'{axis}_state', 'unknown')}" for axis in task329_axes), axis=1)
        df["task_329_state_model"] = raw_values.map(lambda value: task329_map.get(str(value), str(value)))

    dense_parents = _dense_candidate_c_parents(train_df)
    builder = _candidate_c_builder(dense_parents)
    raw_train_c = train_df.apply(builder, axis=1)
    candidate_c_map = _build_generic_fold_map(raw_train_c)
    cand_train = train_df.copy()
    cand_oos = oos_df.copy()
    cand_full = full_df.copy()
    for df in (cand_train, cand_oos, cand_full):
        raw_values = df.apply(builder, axis=1)
        df["candidate_C_state"] = raw_values.map(lambda value: candidate_c_map.get(str(value), str(value)))
    return (task329_train, task329_oos, task329_full), (cand_train, cand_oos, cand_full)


def _framework_comparison_row(name: str, train_df: pd.DataFrame, oos_df: pd.DataFrame, group_col: str, interpretability: str) -> dict[str, Any]:
    metrics = _state_metrics(train_df, group_col)
    states = sorted(set(train_df[group_col].astype(str)) | set(oos_df[group_col].astype(str)))
    train_avg = float(len(train_df) / max(len(set(train_df[group_col].astype(str))), 1))
    oos_avg = float(len(oos_df) / max(len(set(oos_df[group_col].astype(str))), 1))
    sparse = sum(
        1 for state in states if int((train_df[group_col].astype(str) == state).sum()) < 25 or int((oos_df[group_col].astype(str) == state).sum()) < OOS_MIN_COUNT
    )
    return {
        "framework": name,
        "payoff_separation": metrics["between_state_expectancy_dispersion"],
        "within_state_behavior_variance": _within_cluster_behavior_variance(train_df.rename(columns={group_col: "behavior_cluster_id"})) if group_col == "behavior_cluster_id" else round(float(pd.to_numeric(train_df["realized_R"], errors="coerce").var(ddof=0)), 6),
        "path_entropy": metrics["within_state_path_entropy_mean"],
        "OOS_retention": _oos_retention(train_df, oos_df, group_col),
        "density": round(train_avg, 6),
        "sparsity_risk": round(float(sparse / max(len(states), 1)), 6),
        "interpretability": interpretability,
    }


def _feature_to_cluster_mapping(train_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in ENTRY_FEATURES:
        band_col = f"{feature}_band"
        if band_col not in train_df.columns:
            continue
        for band, scoped in train_df.groupby(band_col):
            dist = _distribution(scoped["cluster_label"])
            for cluster_label, prob in dist.items():
                rows.append(
                    {
                        "mapping_type": "feature_band",
                        "feature_name": feature,
                        "feature_value": str(band),
                        "cluster_label": cluster_label,
                        "trade_count": int(len(scoped)),
                        "cluster_probability": round(float(prob), 6),
                    }
                )
    return pd.DataFrame(rows).sort_values(["feature_name", "feature_value", "cluster_probability"], ascending=[True, True, False]).reset_index(drop=True)


def _state_to_cluster_mapping(train_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for axis_col in ["extension_pressure_state", "trend_quality_state", "participation_quality_state", "noise_pressure_state"]:
        for state_value, scoped in train_df.groupby(axis_col):
            dist = _distribution(scoped["cluster_label"])
            for cluster_label, prob in dist.items():
                rows.append(
                    {
                        "mapping_type": "axis_state",
                        "source_name": axis_col,
                        "source_value": str(state_value),
                        "cluster_label": cluster_label,
                        "trade_count": int(len(scoped)),
                        "cluster_probability": round(float(prob), 6),
                    }
                )
    for scenario_family, scoped in train_df.groupby("scenario_family"):
        dist = _distribution(scoped["cluster_label"])
        for cluster_label, prob in dist.items():
            rows.append(
                {
                    "mapping_type": "scenario_family",
                    "source_name": "scenario_family",
                    "source_value": str(scenario_family),
                    "cluster_label": cluster_label,
                    "trade_count": int(len(scoped)),
                    "cluster_probability": round(float(prob), 6),
                }
            )
    return pd.DataFrame(rows).sort_values(["mapping_type", "source_name", "source_value", "cluster_probability"], ascending=[True, True, True, False]).reset_index(drop=True)


def _build_band_probability_tables(train_df: pd.DataFrame) -> dict[str, dict[str, dict[str, float]]]:
    tables: dict[str, dict[str, dict[str, float]]] = {}
    sources = [f"{feature}_band" for feature in ENTRY_FEATURES] + [
        "extension_pressure_state",
        "trend_quality_state",
        "participation_quality_state",
        "noise_pressure_state",
        "scenario_family",
    ]
    for source in sources:
        if source not in train_df.columns:
            continue
        tables[source] = {}
        for value, scoped in train_df.groupby(source):
            tables[source][str(value)] = _distribution(scoped["cluster_label"])
    return tables


def _predict_band_probability(df: pd.DataFrame, tables: dict[str, dict[str, dict[str, float]]], cluster_labels: list[str]) -> tuple[np.ndarray, list[dict[str, float]]]:
    preds = []
    probs = []
    sources = [f"{feature}_band" for feature in ENTRY_FEATURES] + [
        "extension_pressure_state",
        "trend_quality_state",
        "participation_quality_state",
        "noise_pressure_state",
        "scenario_family",
    ]
    for _, row in df.iterrows():
        agg = {label: 0.0 for label in cluster_labels}
        used = 0
        for source in sources:
            value = str(row.get(source, ""))
            dist = tables.get(source, {}).get(value)
            if not dist:
                continue
            for label in cluster_labels:
                agg[label] += float(dist.get(label, 0.0))
            used += 1
        if used == 0:
            base = {label: 1.0 / max(len(cluster_labels), 1) for label in cluster_labels}
        else:
            base = {label: agg[label] / used for label in cluster_labels}
        pred = max(base.items(), key=lambda item: item[1])[0]
        preds.append(pred)
        probs.append(base)
    return np.asarray(preds, dtype=object), probs


def _make_supervised_features(train_df: pd.DataFrame, oos_df: pd.DataFrame, full_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    numeric_cols = [c for c in PRE_ENTRY_PREDICTOR_FEATURES if c in {"ret_20d_pre", "dist_to_sma200_pct", "rs_percentile_20d", "sector_breadth", "vol_contraction_ratio", "breakout_strength_pct"}]
    categorical_cols = [c for c in PRE_ENTRY_PREDICTOR_FEATURES if c not in numeric_cols]
    return train_df[PRE_ENTRY_PREDICTOR_FEATURES].copy(), oos_df[PRE_ENTRY_PREDICTOR_FEATURES].copy(), full_df[PRE_ENTRY_PREDICTOR_FEATURES].copy(), numeric_cols, categorical_cols


def _fit_supervised_models(train_df: pd.DataFrame, train_y: pd.Series) -> dict[str, Any]:
    x_train, _, _, numeric_cols, categorical_cols = _make_supervised_features(train_df, train_df, train_df)
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
    logistic = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("model", LogisticRegression(max_iter=2000, multi_class="multinomial", penalty="l2", random_state=RANDOM_STATE)),
        ]
    )
    tree = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("model", DecisionTreeClassifier(max_depth=3, random_state=RANDOM_STATE)),
        ]
    )
    logistic.fit(x_train, train_y)
    tree.fit(x_train, train_y)
    return {"logistic_regression": logistic, "decision_tree": tree}


def _majority_baseline(train_y: pd.Series, df: pd.DataFrame) -> tuple[np.ndarray, list[dict[str, float]]]:
    majority = str(train_y.astype(str).mode().iloc[0])
    labels = sorted(train_y.astype(str).unique())
    probs = {label: (1.0 if label == majority else 0.0) for label in labels}
    return np.asarray([majority] * len(df), dtype=object), [probs.copy() for _ in range(len(df))]


def _predict_supervised(model: Any, df: pd.DataFrame) -> tuple[np.ndarray, list[dict[str, float]]]:
    x, _, _, _, _ = _make_supervised_features(df, df, df)
    preds = model.predict(x)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x)
        classes = [str(v) for v in model.classes_]
        probs = [{classes[idx]: float(row[idx]) for idx in range(len(classes))} for row in proba]
    else:
        classes = sorted(set(str(v) for v in preds))
        probs = [{label: (1.0 if str(pred) == label else 0.0) for label in classes} for pred in preds]
    return np.asarray(preds, dtype=object), probs


def _probability_metrics(y_true: pd.Series, y_pred: np.ndarray, probs: list[dict[str, float]], label_bases: pd.Series, model_name: str, scope_name: str) -> tuple[dict[str, Any], pd.DataFrame]:
    y_true = y_true.astype(str)
    labels = sorted(set(y_true) | set(str(v) for v in y_pred))
    accuracy = float((y_true.to_numpy() == y_pred).mean()) if len(y_true) else 0.0
    majority = float(y_true.value_counts(normalize=True).max()) if not y_true.empty else 0.0
    bad_mask = label_bases.astype(str).isin(BAD_CLUSTER_BASES)
    clean_mask = label_bases.astype(str) == "clean_continuation"
    pred_base = pd.Series([str(v).split("_")[0] for v in y_pred], index=label_bases.index)
    bad_precision = float(((pred_base.isin(BAD_CLUSTER_BASES)) & bad_mask).sum() / max(int(pred_base.isin(BAD_CLUSTER_BASES).sum()), 1))
    bad_recall = float(((pred_base.isin(BAD_CLUSTER_BASES)) & bad_mask).sum() / max(int(bad_mask.sum()), 1))
    clean_precision = float(((pred_base == "clean_continuation") & clean_mask).sum() / max(int((pred_base == "clean_continuation").sum()), 1))
    clean_recall = float(((pred_base == "clean_continuation") & clean_mask).sum() / max(int(clean_mask.sum()), 1))

    brier_rows = []
    ece_rows = []
    for label in labels:
        truth = (y_true == label).astype(float).to_numpy()
        pred_prob = np.asarray([float(prob.get(label, 0.0)) for prob in probs], dtype=float)
        brier_rows.append(float(np.mean((pred_prob - truth) ** 2)))
        bins = np.linspace(0.0, 1.0, 6)
        ece = 0.0
        for start, end in zip(bins[:-1], bins[1:]):
            if end == 1.0:
                mask = (pred_prob >= start) & (pred_prob <= end)
            else:
                mask = (pred_prob >= start) & (pred_prob < end)
            if not mask.any():
                continue
            ece += abs(float(pred_prob[mask].mean()) - float(truth[mask].mean())) * (mask.sum() / max(len(pred_prob), 1))
        ece_rows.append(ece)
    metrics_row = {
        "scope": scope_name,
        "model": model_name,
        "accuracy": round(accuracy, 6),
        "majority_baseline_accuracy": round(majority, 6),
        "lift_vs_baseline": round(accuracy - majority, 6),
        "precision_bad_clusters": round(bad_precision, 6),
        "recall_bad_clusters": round(bad_recall, 6),
        "precision_clean_continuation": round(clean_precision, 6),
        "recall_clean_continuation": round(clean_recall, 6),
        "brier_score_mean": round(float(np.mean(brier_rows)) if brier_rows else 0.0, 6),
        "ece_mean": round(float(np.mean(ece_rows)) if ece_rows else 0.0, 6),
    }
    cm_rows = []
    for actual in labels:
        for predicted in labels:
            cm_rows.append(
                {
                    "scope": scope_name,
                    "model": model_name,
                    "actual_cluster_label": actual,
                    "predicted_cluster_label": predicted,
                    "trade_count": int(((y_true == actual) & (pd.Series(y_pred, index=y_true.index).astype(str) == predicted)).sum()),
                }
            )
    return metrics_row, pd.DataFrame(cm_rows)


def _action_multiplier(label_base: str) -> float:
    if label_base in BAD_CLUSTER_BASES:
        return 0.0
    if label_base in REDUCE_CLUSTER_BASES:
        return 0.5
    return 1.0


def _diagnostic_action_test(df: pd.DataFrame, y_pred: np.ndarray, label_lookup: dict[str, str], model_name: str, scope_name: str) -> tuple[dict[str, Any], pd.DataFrame]:
    out = df.copy()
    out["predicted_cluster_label"] = pd.Series(y_pred, index=out.index).astype(str)
    out["predicted_cluster_label_base"] = out["predicted_cluster_label"].map(lambda value: label_lookup.get(str(value), str(value).split("_")[0]))
    out["diagnostic_multiplier"] = out["predicted_cluster_label_base"].map(_action_multiplier)
    out["diagnostic_adjusted_R"] = pd.to_numeric(out["realized_R"], errors="coerce") * pd.to_numeric(out["diagnostic_multiplier"], errors="coerce")
    trade_count = int((out["diagnostic_multiplier"] > 0).sum())
    baseline_total = float(pd.to_numeric(out["realized_R"], errors="coerce").sum())
    adjusted_total = float(pd.to_numeric(out["diagnostic_adjusted_R"], errors="coerce").sum())
    baseline_expectancy = float(pd.to_numeric(out["realized_R"], errors="coerce").mean()) if not out.empty else 0.0
    adjusted_expectancy = float(pd.to_numeric(out.loc[out["diagnostic_multiplier"] > 0, "diagnostic_adjusted_R"], errors="coerce").mean()) if trade_count > 0 else 0.0
    saved_loss = float((-pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0) & (pd.to_numeric(out["realized_R"], errors="coerce") < 0), "realized_R"], errors="coerce")).sum())
    missed_gain = float(pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0) & (pd.to_numeric(out["realized_R"], errors="coerce") > 0), "realized_R"], errors="coerce").sum())
    metrics = {
        "scope": scope_name,
        "model": model_name,
        "baseline_expectancy": round(baseline_expectancy, 6),
        "diagnostic_expectancy": round(adjusted_expectancy, 6),
        "baseline_return_proxy": round(baseline_total, 6),
        "diagnostic_return_proxy": round(adjusted_total, 6),
        "trade_count": int(len(out)),
        "diagnostic_trade_count": trade_count,
        "saved_loss": round(saved_loss, 6),
        "missed_gain": round(missed_gain, 6),
    }
    delta_df = out[
        [
            "scope",
            "scenario",
            "scenario_family",
            "trade_id",
            "symbol",
            "entry_date",
            "realized_R",
            "predicted_cluster_label",
            "predicted_cluster_label_base",
            "diagnostic_multiplier",
            "diagnostic_adjusted_R",
        ]
    ].copy()
    delta_df["model"] = model_name
    return metrics, delta_df


def _markdown_table(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["_No rows_"]
    cols = [str(column) for column in df.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for record in df.to_dict("records"):
        row: list[str] = []
        for col in cols:
            value = record.get(col, "")
            if isinstance(value, float):
                row.append("" if math.isnan(value) else f"{value:.6g}")
            else:
                row.append(str(value))
        lines.append("| " + " | ".join(row) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 333: behavior-clustered state model.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--ranked-input", default=str(RANKED_INPUT))
    parser.add_argument("--candidate-pool", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df, oos_df, full_df = _labeled_trade_frames(
        base_dir=Path(args.base_dir),
        ranked_input=Path(args.ranked_input),
        candidate_pool=args.candidate_pool,
        jobs=args.jobs,
    )
    train_df = _attach_axis_states(train_df)
    oos_df = _attach_axis_states(oos_df)
    full_df = _attach_axis_states(full_df)

    scaler = _fit_behavior_scaler(train_df)
    candidate_rows = []
    chosen_payload: dict[str, Any] | None = None
    for method in CLUSTER_METHODS:
        for k in CLUSTER_RANGE:
            _, cand_train, cand_oos, cand_full = _assign_clusters(train_df, oos_df, full_df, scaler, method, k)
            row = _cluster_model_candidate_row(method, k, cand_train, cand_oos)
            candidate_rows.append(row)
            if chosen_payload is None:
                chosen_payload = {"method": method, "k": k, "train_df": cand_train, "oos_df": cand_oos, "full_df": cand_full}
    candidate_df = pd.DataFrame(candidate_rows)
    best = _select_best_cluster_candidate(candidate_df)
    selected_method = str(best["method"])
    selected_k = int(best["k"])
    _, selected_train_df, selected_oos_df, selected_full_df = _assign_clusters(train_df, oos_df, full_df, scaler, selected_method, selected_k)

    diagnostics_df = pd.concat(
        [
            _cluster_diagnostics(selected_train_df, "train"),
            _cluster_diagnostics(selected_oos_df, "anchored_oos"),
            _cluster_diagnostics(selected_full_df, "full_period"),
        ],
        ignore_index=True,
    )
    deltas_df = _cluster_train_oos_deltas(selected_train_df, selected_oos_df)
    diagnostics_df = diagnostics_df.merge(deltas_df, on="behavior_cluster_id", how="left")
    labels_df = _label_cluster_rows(diagnostics_df[diagnostics_df["scope"] == "train"].copy())
    selected_train_df = _selected_behavior_clusters(selected_train_df, labels_df)
    selected_oos_df = _selected_behavior_clusters(selected_oos_df, labels_df)
    selected_full_df = _selected_behavior_clusters(selected_full_df, labels_df)
    selected_clusters_df = pd.concat([selected_train_df, selected_oos_df, selected_full_df], ignore_index=True)

    task329_frames, candidate_c_frames = _rebuild_task329_and_candidate_c(train_df, oos_df, full_df)
    comparison_rows = [
        _framework_comparison_row("behavior_clusters", selected_train_df, selected_oos_df, "cluster_label", "medium_high"),
        _framework_comparison_row("task_329_state_model", task329_frames[0], task329_frames[1], "task_329_state_model", "high"),
        _framework_comparison_row("task_332_candidate_C", candidate_c_frames[0], candidate_c_frames[1], "candidate_C_state", "medium"),
    ]
    comparison_df = pd.DataFrame(comparison_rows)

    feature_map_df = _feature_to_cluster_mapping(selected_train_df)
    state_map_df = _state_to_cluster_mapping(selected_train_df)

    train_y = selected_train_df["cluster_label"].astype(str)
    label_base_lookup = labels_df.set_index("cluster_label")["cluster_label_base"].to_dict()
    cluster_labels = sorted(train_y.unique())
    band_tables = _build_band_probability_tables(selected_train_df)
    supervised_models = _fit_supervised_models(selected_train_df, train_y)

    prediction_rows = []
    confusion_rows = []
    diagnostic_rows = []
    trade_delta_rows = []
    datasets = {
        "train": selected_train_df,
        "anchored_oos": selected_oos_df,
        "full_period": selected_full_df,
    }
    for scope_name, scoped_df in datasets.items():
        y_true = scoped_df["cluster_label"].astype(str)
        label_bases = scoped_df["cluster_label"].map(lambda value: label_base_lookup.get(str(value), str(value).split("_")[0]))
        majority_pred, majority_probs = _majority_baseline(train_y, scoped_df)
        band_pred, band_probs = _predict_band_probability(scoped_df, band_tables, cluster_labels)
        for model_name, preds, probs in (
            ("majority_baseline", majority_pred, majority_probs),
            ("band_probability_aggregation", band_pred, band_probs),
        ):
            metric_row, cm_df = _probability_metrics(y_true, preds, probs, label_bases, model_name, scope_name)
            prediction_rows.append(metric_row)
            confusion_rows.append(cm_df)
            action_row, trade_delta_df = _diagnostic_action_test(scoped_df, preds, label_base_lookup, model_name, scope_name)
            diagnostic_rows.append(action_row)
            trade_delta_rows.append(trade_delta_df)
        for model_name, model in supervised_models.items():
            preds, probs = _predict_supervised(model, scoped_df)
            metric_row, cm_df = _probability_metrics(y_true, preds, probs, label_bases, model_name, scope_name)
            prediction_rows.append(metric_row)
            confusion_rows.append(cm_df)
            action_row, trade_delta_df = _diagnostic_action_test(scoped_df, preds, label_base_lookup, model_name, scope_name)
            diagnostic_rows.append(action_row)
            trade_delta_rows.append(trade_delta_df)

    prediction_df = pd.DataFrame(prediction_rows).sort_values(["scope", "accuracy", "model"], ascending=[True, False, True]).reset_index(drop=True)
    confusion_df = pd.concat(confusion_rows, ignore_index=True) if confusion_rows else pd.DataFrame()
    diagnostic_action_df = pd.DataFrame(diagnostic_rows).sort_values(["scope", "diagnostic_expectancy"], ascending=[True, False]).reset_index(drop=True)
    trade_delta_df = pd.concat(trade_delta_rows, ignore_index=True) if trade_delta_rows else pd.DataFrame()

    oos_behavior = comparison_df[comparison_df["framework"] == "behavior_clusters"].iloc[0]
    oos_task329 = comparison_df[comparison_df["framework"] == "task_329_state_model"].iloc[0]
    oos_best_pred = prediction_df[(prediction_df["scope"] == "anchored_oos") & (prediction_df["model"] != "majority_baseline")].sort_values(
        ["accuracy", "precision_bad_clusters"], ascending=[False, False]
    )
    best_oos_pred_row = oos_best_pred.iloc[0] if not oos_best_pred.empty else prediction_df.iloc[0]
    best_action_oos = diagnostic_action_df[(diagnostic_action_df["scope"] == "anchored_oos") & (diagnostic_action_df["model"] == best_oos_pred_row["model"])].iloc[0]
    best_action_full = diagnostic_action_df[(diagnostic_action_df["scope"] == "full_period") & (diagnostic_action_df["model"] == best_oos_pred_row["model"])].iloc[0]
    decision = "BEHAVIOR_STATE_REJECT"
    if (
        float(oos_behavior["within_state_behavior_variance"]) <= float(oos_task329["within_state_behavior_variance"])
        and float(oos_behavior["path_entropy"]) <= float(oos_task329["path_entropy"])
        and float(oos_behavior["OOS_retention"]) > -0.2
        and float(best_oos_pred_row["lift_vs_baseline"]) > 0
        and float(best_action_oos["diagnostic_expectancy"]) > float(best_action_oos["baseline_expectancy"])
        and float(best_action_full["diagnostic_return_proxy"]) >= float(best_action_full["baseline_return_proxy"]) * 0.85
    ):
        decision = "BEHAVIOR_STATE_ACCEPT"
    elif float(best_oos_pred_row["lift_vs_baseline"]) > 0 or float(oos_behavior["OOS_retention"]) > float(oos_task329["OOS_retention"]):
        decision = "BEHAVIOR_STATE_NEEDS_REFINEMENT"

    md_lines = [
        "# Task 333: Behavior Clustered State Model",
        "",
        f"- Final decision: `{decision}`.",
        f"- Selected cluster model: `{selected_method}` with `K={selected_k}`.",
        f"- Best OOS predictor: `{best_oos_pred_row['model']}` with OOS lift `{float(best_oos_pred_row['lift_vs_baseline']):.3f}`.",
        "",
        "## Cluster Model Candidates",
        "",
    ]
    md_lines.extend(_markdown_table(candidate_df))
    md_lines.extend([
        "",
        "## Behavior vs Axis State Comparison",
        "",
    ])
    md_lines.extend(_markdown_table(comparison_df))
    md_lines.extend([
        "",
        "## Prediction Metrics",
        "",
    ])
    md_lines.extend(_markdown_table(prediction_df[prediction_df["scope"] == "anchored_oos"]))
    md_lines.extend([
        "",
        "## Diagnostic Action Test",
        "",
    ])
    md_lines.extend(_markdown_table(diagnostic_action_df[diagnostic_action_df["scope"].isin(["anchored_oos", "full_period"])]))

    candidate_df.to_csv(out_dir / "task_333_cluster_model_candidates.csv", index=False)
    selected_clusters_df.to_csv(out_dir / "task_333_selected_behavior_clusters.csv", index=False)
    diagnostics_df.to_csv(out_dir / "task_333_behavior_cluster_diagnostics.csv", index=False)
    labels_df.to_csv(out_dir / "task_333_behavior_cluster_labels.csv", index=False)
    comparison_df.to_csv(out_dir / "task_333_behavior_vs_axis_state_comparison.csv", index=False)
    feature_map_df.to_csv(out_dir / "task_333_feature_to_behavior_cluster_mapping.csv", index=False)
    state_map_df.to_csv(out_dir / "task_333_state_to_behavior_cluster_mapping.csv", index=False)
    prediction_df.to_csv(out_dir / "task_333_behavior_cluster_prediction_metrics.csv", index=False)
    confusion_df.to_csv(out_dir / "task_333_behavior_cluster_confusion_matrix.csv", index=False)
    diagnostic_action_df.to_csv(out_dir / "task_333_diagnostic_action_test.csv", index=False)
    trade_delta_df.to_csv(out_dir / "task_333_trade_level_cluster_delta.csv", index=False)
    (out_dir / "task_333_behavior_clustered_state_model.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
