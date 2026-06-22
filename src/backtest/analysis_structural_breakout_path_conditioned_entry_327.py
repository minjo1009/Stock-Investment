from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    PostEntryOverlayConfig,
    PreEntryFilterConfig,
    StructuralConfig,
    _load_stock_symbols,
    _prepare_preloaded_frames,
    _safe_quantile_band,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_best_combo_323plus import _anchored_oos_window
from src.backtest.analysis_structural_breakout_exit_size_324 import _load_validation_bands
from src.backtest.analysis_structural_breakout_regime_conditioned_entry_326 import _assign_archetype
from src.backtest.analysis_structural_breakout_regime_entry_325 import (
    DUAL_MAP_FRAME,
    RANKED_INPUT,
    _aggregate_variant_rows,
    _build_entry_feature_lookup,
    _build_regime_lookup,
    _build_universe_state_lookup,
    _build_variant_trade_frame,
    _collect_filter_log,
    _config_from_scenario,
    _enrich_trade_frame,
    _regime_rebuild_table,
    _robustness_check,
    _select_top10_pool,
    _slice_timestamps,
    _summary_table,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_327_path_conditioned_entry")
PATH_TYPES = [
    "strong_continuation",
    "weak_continuation",
    "early_failure",
    "volatile_noise",
    "slow_grind",
]
ENTRY_FEATURES = [
    "rs_percentile_20d",
    "sector_breadth",
    "dist_to_sma200_pct",
    "ret_20d_pre",
    "vol_contraction_ratio",
    "breakout_strength_pct",
]
JOINT_FEATURES = {
    "rs_extension": ("rs_percentile_20d", "dist_to_sma200_pct"),
    "breadth_vol": ("sector_breadth", "vol_contraction_ratio"),
}
MIN_CELL_COUNT = 8
CALIBRATION_BINS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def _feature_band_edges(df: pd.DataFrame, features: list[str]) -> dict[str, tuple[float, float]]:
    edges: dict[str, tuple[float, float]] = {}
    for feature in features:
        series = pd.to_numeric(df.get(feature), errors="coerce").dropna()
        if series.empty:
            continue
        edges[feature] = (float(series.quantile(0.30)), float(series.quantile(0.70)))
    return edges


def _metric_band_edges(df: pd.DataFrame) -> dict[str, tuple[float, float]]:
    metrics = [
        "follow_through_3d_pct",
        "follow_through_5d_pct",
        "mfe_3d_pct",
        "mfe_5d_pct",
        "retrace_3d_pct",
        "retrace_5d_pct",
        "mae_3d_pct",
        "mae_5d_pct",
    ]
    return _feature_band_edges(df, metrics)


def _band_value(value: Any, low: float, high: float, *, positive_metric: bool) -> str:
    if pd.isna(value):
        return "unknown"
    return _safe_quantile_band(float(value), low, high, lower_is_bad=positive_metric)


def _annotate_pre_entry_bands(df: pd.DataFrame, band_edges: dict[str, tuple[float, float]]) -> pd.DataFrame:
    out = df.copy()
    for feature, (low, high) in band_edges.items():
        if feature in out.columns:
            series = pd.to_numeric(out[feature], errors="coerce")
        else:
            series = pd.Series(index=out.index, dtype=float)
        out[f"{feature}_band"] = series.map(
            lambda value: _band_value(value, low, high, positive_metric=False) if pd.notna(value) else "unknown"
        )
    return out


def _enrich_path_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["mfe_3d_pct"] = pd.to_numeric(out.get("follow_through_3d_pct"), errors="coerce")
    out["mfe_5d_pct"] = pd.to_numeric(out.get("follow_through_5d_pct"), errors="coerce")
    out["mae_3d_pct"] = pd.to_numeric(out.get("adverse_excursion_3d_pct"), errors="coerce").abs()
    out["mae_5d_pct"] = pd.to_numeric(out.get("adverse_excursion_5d_pct"), errors="coerce").abs()
    out["retrace_3d_pct"] = pd.to_numeric(out.get("post_breakout_retrace_3d_pct"), errors="coerce")
    out["retrace_5d_pct"] = pd.to_numeric(out.get("post_breakout_retrace_5d_pct"), errors="coerce")
    return out


def _metric_bands_for_row(row: pd.Series, band_edges: dict[str, tuple[float, float]]) -> dict[str, str]:
    out: dict[str, str] = {}
    positive_metrics = {
        "follow_through_3d_pct",
        "follow_through_5d_pct",
        "mfe_3d_pct",
        "mfe_5d_pct",
    }
    for feature, (low, high) in band_edges.items():
        out[feature] = _band_value(row.get(feature, math.nan), low, high, positive_metric=feature in positive_metrics)
    return out


def _label_path_type(row: pd.Series, metric_band_edges: dict[str, tuple[float, float]]) -> str:
    bands = _metric_bands_for_row(row, metric_band_edges)
    ft3 = bands.get("follow_through_3d_pct", "unknown")
    ft5 = bands.get("follow_through_5d_pct", "unknown")
    retrace3 = bands.get("retrace_3d_pct", "unknown")
    retrace5 = bands.get("retrace_5d_pct", "unknown")
    mae3 = bands.get("mae_3d_pct", "unknown")
    mae5 = bands.get("mae_5d_pct", "unknown")
    mfe3 = bands.get("mfe_3d_pct", "unknown")
    mfe5 = bands.get("mfe_5d_pct", "unknown")

    if (mae3 == "high" or mae5 == "high") and (mfe3 == "strong" or mfe5 == "strong"):
        return "volatile_noise"
    if (ft3 in {"weak", "mixed"}) and (ft5 in {"weak", "mixed"}) and (retrace3 == "high" or retrace5 == "high"):
        return "early_failure"
    if (ft3 == "strong" or ft5 == "strong") and retrace3 in {"low", "mid"} and retrace5 in {"low", "mid"} and mae3 in {"low", "mid"}:
        return "strong_continuation"
    if ft3 in {"weak", "mixed"} and ft5 in {"mixed", "strong"} and mae3 == "low" and mae5 == "low":
        return "slow_grind"
    return "weak_continuation"


def _apply_path_labels(df: pd.DataFrame, metric_band_edges: dict[str, tuple[float, float]]) -> pd.DataFrame:
    out = _enrich_path_metrics(df)
    out["path_type"] = out.apply(lambda row: _label_path_type(row, metric_band_edges), axis=1)
    return out


def _label_diagnostics(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope_name, scoped in (("train", train_df), ("anchored_oos", oos_df)):
        total = max(len(scoped), 1)
        for path_type, count in Counter(scoped["path_type"].astype(str)).items():
            rows.append(
                {
                    "diagnostic_type": "class_imbalance",
                    "scope": scope_name,
                    "regime_state": "",
                    "path_type": path_type,
                    "trade_count": int(count),
                    "share": round(count / total, 6),
                }
            )
        grouped = (
            scoped.groupby(["regime_state", "path_type"], as_index=False)
            .agg(trade_count=("realized_R", "size"))
        )
        for record in grouped.to_dict("records"):
            regime_total = int(scoped[scoped["regime_state"] == record["regime_state"]].shape[0]) or 1
            rows.append(
                {
                    "diagnostic_type": "regime_distribution",
                    "scope": scope_name,
                    "regime_state": str(record["regime_state"]),
                    "path_type": str(record["path_type"]),
                    "trade_count": int(record["trade_count"]),
                    "share": round(int(record["trade_count"]) / regime_total, 6),
                }
            )
    train_share = train_df["path_type"].value_counts(normalize=True).to_dict()
    oos_share = oos_df["path_type"].value_counts(normalize=True).to_dict()
    for path_type in PATH_TYPES:
        rows.append(
            {
                "diagnostic_type": "train_vs_oos_drift",
                "scope": "train_vs_oos",
                "regime_state": "",
                "path_type": path_type,
                "trade_count": 0,
                "share": round(float(oos_share.get(path_type, 0.0) - train_share.get(path_type, 0.0)), 6),
            }
        )
    return pd.DataFrame(rows)


def _path_outcome_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    total_r = float(pd.to_numeric(df["realized_R"], errors="coerce").sum()) or 1.0
    grouped = (
        df.groupby("path_type", as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy_r=("realized_R", "mean"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
            avg_r=("realized_R", "mean"),
            total_r=("realized_R", "sum"),
        )
    )
    grouped["pnl_contribution_share"] = grouped["total_r"].map(lambda value: round(float(value) / total_r, 6))
    return grouped.sort_values(["expectancy_r", "trade_count"], ascending=[False, False]).reset_index(drop=True)


def _regime_path_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby(["regime_state", "path_type"], as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy_r=("realized_R", "mean"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
            total_r=("realized_R", "sum"),
        )
    )
    totals = grouped.groupby("regime_state")["trade_count"].sum().to_dict()
    grouped["distribution_share"] = grouped.apply(
        lambda row: round(float(row["trade_count"]) / max(int(totals.get(str(row["regime_state"]), 1)), 1), 6),
        axis=1,
    )
    return grouped.sort_values(["regime_state", "distribution_share"], ascending=[True, False]).reset_index(drop=True)


def _archetype_path_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    scoped = df.copy()
    scoped["entry_archetype"] = scoped.apply(_assign_archetype, axis=1)
    grouped = (
        scoped.groupby(["entry_archetype", "path_type"], as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy_r=("realized_R", "mean"),
            total_r=("realized_R", "sum"),
        )
    )
    totals = grouped.groupby("entry_archetype")["trade_count"].sum().to_dict()
    grouped["distribution_share"] = grouped.apply(
        lambda row: round(float(row["trade_count"]) / max(int(totals.get(str(row["entry_archetype"]), 1)), 1), 6),
        axis=1,
    )
    return grouped.sort_values(["entry_archetype", "distribution_share"], ascending=[True, False]).reset_index(drop=True)


def _smoothed_probability(local_count: int, local_prob: float, fallback_prob: float) -> float:
    if local_count >= MIN_CELL_COUNT:
        return local_prob
    weight = max(min(local_count / MIN_CELL_COUNT, 1.0), 0.0)
    return weight * local_prob + (1.0 - weight) * fallback_prob


def _feature_regime_path_mapping(train_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for feature in ENTRY_FEATURES:
        band_col = f"{feature}_band"
        if band_col not in train_df.columns:
            continue
        global_grouped = (
            train_df.groupby([band_col, "path_type"], as_index=False)
            .agg(trade_count=("realized_R", "size"))
        )
        global_totals = global_grouped.groupby(band_col)["trade_count"].sum().to_dict()
        global_probs = {
            (str(row[band_col]), str(row["path_type"])): float(row["trade_count"]) / max(int(global_totals.get(str(row[band_col]), 1)), 1)
            for row in global_grouped.to_dict("records")
        }
        grouped = (
            train_df.groupby(["regime_state", band_col, "path_type"], as_index=False)
            .agg(trade_count=("realized_R", "size"), expectancy_r=("realized_R", "mean"))
        )
        cell_totals = grouped.groupby(["regime_state", band_col])["trade_count"].sum().to_dict()
        for record in grouped.to_dict("records"):
            regime = str(record["regime_state"])
            band = str(record[band_col])
            path_type = str(record["path_type"])
            total = int(cell_totals.get((regime, band), 1))
            local_prob = float(record["trade_count"]) / max(total, 1)
            fallback_prob = float(global_probs.get((band, path_type), 0.0))
            rows.append(
                {
                    "feature": feature,
                    "feature_band": band,
                    "regime_state": regime,
                    "path_type": path_type,
                    "trade_count": int(record["trade_count"]),
                    "path_probability": round(_smoothed_probability(total, local_prob, fallback_prob), 6),
                    "expectancy_r": round(float(record["expectancy_r"]), 6),
                }
            )
    return pd.DataFrame(rows).sort_values(["feature", "regime_state", "feature_band", "path_type"]).reset_index(drop=True)


def _build_joint_bands(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for joint_name, (lhs, rhs) in JOINT_FEATURES.items():
        lhs_label = lhs.replace("_percentile_20d", "").replace("dist_to_", "dist_").replace("_pct", "").replace("vol_contraction_ratio", "vol").replace("sector_breadth", "breadth").replace("ret_20d_pre", "ret20")
        rhs_label = rhs.replace("_percentile_20d", "").replace("dist_to_", "dist_").replace("_pct", "").replace("vol_contraction_ratio", "vol").replace("sector_breadth", "breadth").replace("ret_20d_pre", "ret20")
        out[f"{joint_name}_band"] = out.apply(
            lambda row: f"{lhs_label}_{row.get(f'{lhs}_band', 'unknown')}__{rhs_label}_{row.get(f'{rhs}_band', 'unknown')}",
            axis=1,
        )
    return out


def _feature_probability_lookup(mapping_df: pd.DataFrame) -> dict[tuple[str, str, str, str], float]:
    return {
        (str(row["feature"]), str(row["feature_band"]), str(row["regime_state"]), str(row["path_type"])): float(row["path_probability"])
        for row in mapping_df.to_dict("records")
    }


def _joint_feature_path_mapping(train_df: pd.DataFrame, feature_mapping_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    feature_lookup = _feature_probability_lookup(feature_mapping_df)
    joint_df = _build_joint_bands(train_df)
    for joint_name, (lhs, rhs) in JOINT_FEATURES.items():
        band_col = f"{joint_name}_band"
        grouped = (
            joint_df.groupby(["regime_state", band_col, "path_type"], as_index=False)
            .agg(trade_count=("realized_R", "size"), expectancy_r=("realized_R", "mean"))
        )
        cell_totals = grouped.groupby(["regime_state", band_col])["trade_count"].sum().to_dict()
        for record in grouped.to_dict("records"):
            regime = str(record["regime_state"])
            joint_band = str(record[band_col])
            path_type = str(record["path_type"])
            total = int(cell_totals.get((regime, joint_band), 1))
            local_prob = float(record["trade_count"]) / max(total, 1)
            lhs_band = joint_band.split("__")[0].split("_")[-1]
            rhs_band = joint_band.split("__")[1].split("_")[-1]
            fallback_probs = [
                float(feature_lookup.get((lhs, lhs_band, regime, path_type), 0.0)),
                float(feature_lookup.get((rhs, rhs_band, regime, path_type), 0.0)),
            ]
            fallback_prob = sum(fallback_probs) / max(len(fallback_probs), 1)
            rows.append(
                {
                    "joint_feature": joint_name,
                    "joint_band": joint_band,
                    "regime_state": regime,
                    "path_type": path_type,
                    "trade_count": int(record["trade_count"]),
                    "path_probability": round(_smoothed_probability(total, local_prob, fallback_prob), 6),
                    "expectancy_r": round(float(record["expectancy_r"]), 6),
                }
            )
    return pd.DataFrame(rows).sort_values(["joint_feature", "regime_state", "joint_band", "path_type"]).reset_index(drop=True)


def _joint_probability_lookup(mapping_df: pd.DataFrame) -> dict[tuple[str, str, str, str], float]:
    return {
        (str(row["joint_feature"]), str(row["joint_band"]), str(row["regime_state"]), str(row["path_type"])): float(row["path_probability"])
        for row in mapping_df.to_dict("records")
    }


def _global_path_prior(train_df: pd.DataFrame) -> dict[str, float]:
    counts = train_df["path_type"].value_counts(normalize=True).to_dict()
    return {path_type: float(counts.get(path_type, 0.0)) for path_type in PATH_TYPES}


def _attach_probability_metadata(
    metadata_lookup: dict[str, dict[str, Any]],
    single_lookup: dict[tuple[str, str, str, str], float],
    joint_lookup: dict[tuple[str, str, str, str], float],
    prior: dict[str, float],
) -> dict[str, dict[str, Any]]:
    for metadata in metadata_lookup.values():
        regime = str(metadata.get("regime_state", ""))
        weighted_scores = {path_type: 0.0 for path_type in PATH_TYPES}
        weighted_denoms = {path_type: 0.0 for path_type in PATH_TYPES}
        for feature in ENTRY_FEATURES:
            band = str(metadata.get(f"{feature}_band", "unknown"))
            if band == "unknown":
                continue
            for path_type in PATH_TYPES:
                prob = single_lookup.get((feature, band, regime, path_type))
                if prob is None:
                    continue
                weighted_scores[path_type] += float(prob)
                weighted_denoms[path_type] += 1.0
        for joint_name, (lhs, rhs) in JOINT_FEATURES.items():
            lhs_band = str(metadata.get(f"{lhs}_band", "unknown"))
            rhs_band = str(metadata.get(f"{rhs}_band", "unknown"))
            if lhs_band == "unknown" or rhs_band == "unknown":
                continue
            lhs_label = lhs.replace("_percentile_20d", "").replace("dist_to_", "dist_").replace("_pct", "").replace("vol_contraction_ratio", "vol").replace("sector_breadth", "breadth").replace("ret_20d_pre", "ret20")
            rhs_label = rhs.replace("_percentile_20d", "").replace("dist_to_", "dist_").replace("_pct", "").replace("vol_contraction_ratio", "vol").replace("sector_breadth", "breadth").replace("ret_20d_pre", "ret20")
            joint_band = f"{lhs_label}_{lhs_band}__{rhs_label}_{rhs_band}"
            metadata[f"{joint_name}_band"] = joint_band
            for path_type in PATH_TYPES:
                prob = joint_lookup.get((joint_name, joint_band, regime, path_type))
                if prob is None:
                    continue
                weighted_scores[path_type] += float(prob) * 2.0
                weighted_denoms[path_type] += 2.0
        probabilities: dict[str, float] = {}
        for path_type in PATH_TYPES:
            if weighted_denoms[path_type] > 0:
                probabilities[path_type] = weighted_scores[path_type] / weighted_denoms[path_type]
            else:
                probabilities[path_type] = float(prior.get(path_type, 0.0))
        total_prob = sum(probabilities.values()) or 1.0
        normalized = {path_type: float(probabilities[path_type]) / total_prob for path_type in PATH_TYPES}
        for path_type in PATH_TYPES:
            metadata[f"prob_{path_type}"] = round(normalized[path_type], 6)
        metadata["expected_path"] = max(PATH_TYPES, key=lambda path_type: normalized[path_type])
    return metadata_lookup


def _attach_probability_columns(df: pd.DataFrame, metadata_lookup: dict[str, dict[str, Any]]) -> pd.DataFrame:
    out = df.copy()
    for path_type in PATH_TYPES:
        out[f"prob_{path_type}"] = out.apply(
            lambda row: metadata_lookup.get(f"{row['symbol']}|{row['entry_date']}", {}).get(f"prob_{path_type}", math.nan),
            axis=1,
        )
    out["expected_path"] = out.apply(
        lambda row: metadata_lookup.get(f"{row['symbol']}|{row['entry_date']}", {}).get("expected_path", ""),
        axis=1,
    )
    return out


def _prediction_metrics(df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame()
    actual = df["path_type"].astype(str)
    predicted = df["expected_path"].astype(str)
    accuracy = float((actual == predicted).mean())
    majority_class = actual.value_counts().idxmax() if not actual.empty else ""
    majority_accuracy = float((actual == majority_class).mean()) if majority_class else 0.0
    tp_strong = int(((predicted == "strong_continuation") & (actual == "strong_continuation")).sum())
    pred_strong = int((predicted == "strong_continuation").sum())
    actual_early = int((actual == "early_failure").sum())
    tp_early = int(((predicted == "early_failure") & (actual == "early_failure")).sum())
    rows.append(
        {
            "metric_type": "summary",
            "scope": scope_name,
            "accuracy": round(accuracy, 6),
            "majority_class_accuracy": round(majority_accuracy, 6),
            "accuracy_lift_vs_baseline": round(accuracy - majority_accuracy, 6),
            "precision_strong_continuation": round(tp_strong / pred_strong, 6) if pred_strong > 0 else 0.0,
            "recall_early_failure": round(tp_early / actual_early, 6) if actual_early > 0 else 0.0,
            "actual_path": "",
            "predicted_path": "",
            "trade_count": int(len(df)),
        }
    )
    grouped = (
        df.groupby(["path_type", "expected_path"], as_index=False)
        .agg(trade_count=("realized_R", "size"))
    )
    for record in grouped.to_dict("records"):
        rows.append(
            {
                "metric_type": "confusion_matrix",
                "scope": scope_name,
                "accuracy": math.nan,
                "majority_class_accuracy": math.nan,
                "accuracy_lift_vs_baseline": math.nan,
                "precision_strong_continuation": math.nan,
                "recall_early_failure": math.nan,
                "actual_path": str(record["path_type"]),
                "predicted_path": str(record["expected_path"]),
                "trade_count": int(record["trade_count"]),
            }
        )
    return pd.DataFrame(rows)


def _binary_calibration(probabilities: pd.Series, actuals: pd.Series) -> dict[str, float]:
    probs = pd.to_numeric(probabilities, errors="coerce").fillna(0.0).clip(lower=0.0, upper=1.0)
    acts = pd.to_numeric(actuals, errors="coerce").fillna(0.0)
    brier = float(((probs - acts) ** 2).mean()) if len(probs) else math.nan
    ece = 0.0
    for start, end in zip(CALIBRATION_BINS[:-1], CALIBRATION_BINS[1:]):
        if end < 1.0:
            mask = (probs >= start) & (probs < end)
        else:
            mask = (probs >= start) & (probs <= end)
        if not mask.any():
            continue
        bin_prob = float(probs[mask].mean())
        bin_freq = float(acts[mask].mean())
        ece += abs(bin_prob - bin_freq) * (float(mask.sum()) / max(len(probs), 1))
    avg_prob = float(probs.mean()) if len(probs) else math.nan
    realized = float(acts.mean()) if len(acts) else math.nan
    return {
        "brier_score": round(brier, 6),
        "ece": round(float(ece), 6),
        "avg_predicted_prob": round(avg_prob, 6),
        "realized_frequency": round(realized, 6),
    }


def _calibration_metrics(df: pd.DataFrame, scope_name: str, train_prior: dict[str, float]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame()
    for path_type in PATH_TYPES:
        probs = df[f"prob_{path_type}"]
        actuals = (df["path_type"].astype(str) == path_type).astype(int)
        stats = _binary_calibration(probs, actuals)
        naive_prob = float(train_prior.get(path_type, 0.0))
        naive_brier = float((((actuals * 1.0) - naive_prob) ** 2).mean()) if len(actuals) else math.nan
        rows.append(
            {
                "scope": scope_name,
                "class_name": path_type,
                "brier_score": stats["brier_score"],
                "naive_brier_score": round(naive_brier, 6),
                "ece": stats["ece"],
                "avg_predicted_prob": stats["avg_predicted_prob"],
                "realized_frequency": stats["realized_frequency"],
            }
        )
    return pd.DataFrame(rows)


def _probability_rules_for_variant(variant: str) -> tuple[dict[str, Any], ...]:
    if variant == "baseline":
        return ()
    if variant == "prob_path_conditioned_size":
        return (
            {"rule_id": "early_failure_reduce", "probability_key": "prob_early_failure", "operator": "gt", "threshold": 0.6, "action": "reduce", "size_multiplier": 0.5},
            {"rule_id": "volatile_noise_reduce", "probability_key": "prob_volatile_noise", "operator": "gt", "threshold": 0.5, "action": "reduce", "size_multiplier": 0.5},
            {"rule_id": "strong_cont_allow", "probability_key": "prob_strong_continuation", "operator": "gt", "threshold": 0.5, "action": "allow", "size_multiplier": 1.0},
        )
    return (
        {"rule_id": "early_failure_skip", "probability_key": "prob_early_failure", "operator": "gt", "threshold": 0.6, "action": "skip", "size_multiplier": 0.0},
        {"rule_id": "volatile_noise_reduce", "probability_key": "prob_volatile_noise", "operator": "gt", "threshold": 0.5, "action": "reduce", "size_multiplier": 0.5},
        {"rule_id": "strong_cont_allow", "probability_key": "prob_strong_continuation", "operator": "gt", "threshold": 0.5, "action": "allow", "size_multiplier": 1.0},
    )


def _variant_pre_entry_filter(variant: str, metadata_lookup: dict[str, dict[str, Any]]) -> PreEntryFilterConfig | None:
    if variant == "baseline":
        return None
    return PreEntryFilterConfig(
        path_probability_filter_mode="rules",
        path_probability_rules=_probability_rules_for_variant(variant),
        metadata_lookup=metadata_lookup,
    )


def _variant_overlay(variant: str, validation_bands: dict[str, dict[str, float]]) -> PostEntryOverlayConfig | None:
    if variant != "prob_path_conditioned_entry + size50":
        return None
    return PostEntryOverlayConfig(post_entry_rule_mode="size_only", size_reduction_fraction=0.5, validation_bands=validation_bands)


def _run_variant_results(
    scenarios: list[str],
    variants: list[str],
    *,
    base_dir: Path,
    stocks: list[str],
    frames: dict[str, pd.DataFrame],
    full_timestamps: list[pd.Timestamp],
    oos_timestamps: list[pd.Timestamp],
    metadata_lookup: dict[str, dict[str, Any]],
    validation_bands: dict[str, dict[str, float]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    results: dict[tuple[str, str, str], dict[str, Any]] = {}
    scope_map = {"full_period": full_timestamps, "anchored_oos": oos_timestamps}
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        for variant in variants:
            pre_entry = _variant_pre_entry_filter(variant, metadata_lookup)
            overlay = _variant_overlay(variant, validation_bands)
            for scope_name, scoped_timestamps in scope_map.items():
                results[(scenario, variant, scope_name)] = run_structural_backtest(
                    cfg,
                    base_dir,
                    preloaded_frames=frames,
                    preloaded_timestamps=scoped_timestamps,
                    preloaded_symbols=stocks,
                    pre_entry_filter=pre_entry,
                    overlay=overlay,
                )
    return results


def _decision_label(
    summary_lookup: dict[tuple[str, str], dict[str, Any]],
    robustness_df: pd.DataFrame,
    prediction_metrics_df: pd.DataFrame,
    calibration_df: pd.DataFrame,
    variant: str,
) -> str:
    base_oos = summary_lookup.get(("baseline", "anchored_oos"), {})
    var_oos = summary_lookup.get((variant, "anchored_oos"), {})
    base_full = summary_lookup.get(("baseline", "full_period"), {})
    var_full = summary_lookup.get((variant, "full_period"), {})
    oos_expectancy_ok = float(var_oos.get("expectancy_r", -999.0)) > float(base_oos.get("expectancy_r", -999.0))
    oos_return_ok = float(var_oos.get("total_return_pct", -999.0)) > float(base_oos.get("total_return_pct", -999.0))
    full_period_ok = float(var_full.get("total_return_pct", -999.0)) >= float(base_full.get("total_return_pct", -999.0)) - 15.0

    oos_pred = prediction_metrics_df[(prediction_metrics_df["scope"] == "anchored_oos") & (prediction_metrics_df["metric_type"] == "summary")]
    accuracy_ok = not oos_pred.empty and float(oos_pred.iloc[0]["accuracy_lift_vs_baseline"]) > 0.0
    recall_ok = not oos_pred.empty and float(oos_pred.iloc[0]["recall_early_failure"]) > 0.0

    oos_cal = calibration_df[calibration_df["scope"] == "anchored_oos"].copy()
    calibration_ok = False
    if not oos_cal.empty:
        calibration_ok = float(oos_cal["brier_score"].mean()) <= float(oos_cal["naive_brier_score"].mean())

    scoped_robustness = robustness_df[(robustness_df["variant"] == variant) & (robustness_df["scope"] == "anchored_oos")].copy()
    regime_row = scoped_robustness[scoped_robustness["dimension"] == "regime"]
    symbol_row = scoped_robustness[scoped_robustness["dimension"] == "symbol_group"]
    robustness_ok = (
        not regime_row.empty
        and not symbol_row.empty
        and float(regime_row.iloc[0]["dominant_group_share"]) < 0.60
        and float(symbol_row.iloc[0]["dominant_group_share"]) < 0.60
    )
    if all((oos_expectancy_ok, oos_return_ok, full_period_ok, accuracy_ok, recall_ok, calibration_ok, robustness_ok)):
        return "PROMOTE"
    return "REJECT"


def _write_markdown_report(
    out_dir: Path,
    path_summary_df: pd.DataFrame,
    prediction_metrics_df: pd.DataFrame,
    calibration_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    def _fmt(df: pd.DataFrame) -> list[str]:
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

    lines = [
        "# Task 327 Revised: Regime-Conditioned Path Prediction",
        "",
        "## Core Answer",
        "",
        "The system predicts failure path probabilities at entry time rather than selecting globally good entries.",
        "",
        "## Path Outcome Summary",
        "",
    ]
    lines.extend(_fmt(path_summary_df))
    lines.extend([
        "",
        "## Prediction Metrics",
        "",
    ])
    lines.extend(_fmt(prediction_metrics_df))
    lines.extend([
        "",
        "## Calibration Metrics",
        "",
    ])
    lines.extend(_fmt(calibration_df))
    lines.extend([
        "",
        "## Integrated Summary",
        "",
    ])
    lines.extend(_fmt(summary_df))
    (out_dir / "task_327_path_conditioned_entry.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 327 Revised: regime-conditioned path prediction.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--ranked-input", default=str(RANKED_INPUT))
    parser.add_argument("--candidate-pool", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ranked_input = Path(args.ranked_input)

    stocks = _load_stock_symbols(base_dir, StructuralConfig())
    frames, timestamps = _prepare_preloaded_frames(base_dir, stocks)
    scenarios = _select_top10_pool(
        base_dir=base_dir,
        ranked_input=ranked_input,
        candidate_pool=args.candidate_pool,
        jobs=args.jobs,
        stocks=stocks,
        frames=frames,
        timestamps=timestamps,
    )

    latest_end = max(timestamps)
    anchored = _anchored_oos_window(latest_end)
    train_timestamps = _slice_timestamps(timestamps, timestamps[0], anchored.train_end)
    full_timestamps = timestamps
    oos_timestamps = _slice_timestamps(timestamps, anchored.test_start, anchored.test_end)

    universe_state_lookup = _build_universe_state_lookup(frames, stocks)
    regime_lookup = _build_regime_lookup(base_dir, universe_state_lookup)
    metadata_lookup = _build_entry_feature_lookup(frames, stocks, universe_state_lookup, regime_lookup)

    train_trade_frames: list[pd.DataFrame] = []
    baseline_trade_frames: list[pd.DataFrame] = []
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        train_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=train_timestamps, preloaded_symbols=stocks)
        full_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=full_timestamps, preloaded_symbols=stocks)
        oos_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=oos_timestamps, preloaded_symbols=stocks)
        train_trade_frames.append(_enrich_trade_frame(scenario, train_result, frames, metadata_lookup, "train"))
        baseline_trade_frames.append(_enrich_trade_frame(scenario, full_result, frames, metadata_lookup, "full_period"))
        baseline_trade_frames.append(_enrich_trade_frame(scenario, oos_result, frames, metadata_lookup, "anchored_oos"))

    train_trade_df = pd.concat(train_trade_frames, ignore_index=True) if train_trade_frames else pd.DataFrame()
    baseline_trade_df = pd.concat(baseline_trade_frames, ignore_index=True) if baseline_trade_frames else pd.DataFrame()
    full_trade_df = baseline_trade_df[baseline_trade_df["scope"] == "full_period"].copy()
    oos_trade_df = baseline_trade_df[baseline_trade_df["scope"] == "anchored_oos"].copy()

    pre_entry_band_edges = _feature_band_edges(train_trade_df, ENTRY_FEATURES)
    metric_band_edges = _metric_band_edges(_enrich_path_metrics(train_trade_df))

    metadata_lookup = _annotate_pre_entry_bands(pd.DataFrame.from_dict(metadata_lookup, orient="index"), pre_entry_band_edges).to_dict("index")
    train_trade_df = _annotate_pre_entry_bands(train_trade_df, pre_entry_band_edges)
    full_trade_df = _annotate_pre_entry_bands(full_trade_df, pre_entry_band_edges)
    oos_trade_df = _annotate_pre_entry_bands(oos_trade_df, pre_entry_band_edges)

    train_trade_df = _apply_path_labels(train_trade_df, metric_band_edges)
    full_trade_df = _apply_path_labels(full_trade_df, metric_band_edges)
    oos_trade_df = _apply_path_labels(oos_trade_df, metric_band_edges)

    label_diag_df = _label_diagnostics(train_trade_df, oos_trade_df)
    path_summary_df = _path_outcome_summary(oos_trade_df)
    regime_path_df = _regime_path_matrix(oos_trade_df)
    archetype_path_df = _archetype_path_matrix(oos_trade_df)
    feature_mapping_df = _feature_regime_path_mapping(train_trade_df)
    joint_mapping_df = _joint_feature_path_mapping(train_trade_df, feature_mapping_df)

    single_lookup = _feature_probability_lookup(feature_mapping_df)
    joint_lookup = _joint_probability_lookup(joint_mapping_df)
    prior = _global_path_prior(train_trade_df)
    metadata_lookup = _attach_probability_metadata(metadata_lookup, single_lookup, joint_lookup, prior)

    train_trade_df = _attach_probability_columns(train_trade_df, metadata_lookup)
    full_trade_df = _attach_probability_columns(full_trade_df, metadata_lookup)
    oos_trade_df = _attach_probability_columns(oos_trade_df, metadata_lookup)

    prediction_metrics_df = pd.concat(
        [
            _prediction_metrics(train_trade_df, "train"),
            _prediction_metrics(oos_trade_df, "anchored_oos"),
            _prediction_metrics(full_trade_df, "full_period"),
        ],
        ignore_index=True,
    )
    calibration_df = pd.concat(
        [
            _calibration_metrics(train_trade_df, "train", prior),
            _calibration_metrics(oos_trade_df, "anchored_oos", prior),
            _calibration_metrics(full_trade_df, "full_period", prior),
        ],
        ignore_index=True,
    )

    validation_bands = _load_validation_bands(Path(DUAL_MAP_FRAME))
    variants = [
        "baseline",
        "prob_path_conditioned_size",
        "prob_path_conditioned_entry",
        "prob_path_conditioned_entry + size50",
    ]
    integrated_results = _run_variant_results(
        scenarios,
        variants,
        base_dir=base_dir,
        stocks=stocks,
        frames=frames,
        full_timestamps=full_timestamps,
        oos_timestamps=oos_timestamps,
        metadata_lookup=metadata_lookup,
        validation_bands=validation_bands,
    )

    summary_raw_df = _aggregate_variant_rows(integrated_results)
    summary_df = _summary_table(summary_raw_df)
    oos_comparison_df = summary_df[summary_df["scope"] == "anchored_oos"].copy()
    full_comparison_df = summary_df[summary_df["scope"] == "full_period"].copy()
    trade_level_delta_df = _collect_filter_log(integrated_results)
    variant_trade_df = _build_variant_trade_frame(integrated_results, frames, metadata_lookup)
    robustness_df = _robustness_check(variant_trade_df)

    summary_lookup = {(str(row["variant"]), str(row["scope"])): row for row in summary_df.to_dict("records")}
    summary_df["decision"] = summary_df["variant"].map(
        lambda variant: _decision_label(summary_lookup, robustness_df, prediction_metrics_df, calibration_df, str(variant)) if str(variant) != "baseline" else "BASELINE"
    )
    oos_comparison_df["decision"] = oos_comparison_df["variant"].map(
        lambda variant: _decision_label(summary_lookup, robustness_df, prediction_metrics_df, calibration_df, str(variant)) if str(variant) != "baseline" else "BASELINE"
    )
    full_comparison_df["decision"] = full_comparison_df["variant"].map(
        lambda variant: _decision_label(summary_lookup, robustness_df, prediction_metrics_df, calibration_df, str(variant)) if str(variant) != "baseline" else "BASELINE"
    )

    trade_path_labels_df = pd.concat([train_trade_df, oos_trade_df, full_trade_df], ignore_index=True)

    trade_path_labels_df.to_csv(out_dir / "task_327_trade_path_labels.csv", index=False)
    label_diag_df.to_csv(out_dir / "task_327_path_label_diagnostics.csv", index=False)
    regime_path_df.to_csv(out_dir / "task_327_regime_path_matrix.csv", index=False)
    archetype_path_df.to_csv(out_dir / "task_327_archetype_path_matrix.csv", index=False)
    feature_mapping_df.to_csv(out_dir / "task_327_feature_regime_path_mapping.csv", index=False)
    joint_mapping_df.to_csv(out_dir / "task_327_joint_feature_path_mapping.csv", index=False)
    prediction_metrics_df.to_csv(out_dir / "task_327_path_prediction_metrics.csv", index=False)
    calibration_df.to_csv(out_dir / "task_327_calibration_metrics.csv", index=False)
    summary_df.to_csv(out_dir / "task_327_summary.csv", index=False)
    oos_comparison_df.to_csv(out_dir / "task_327_oos_comparison.csv", index=False)
    full_comparison_df.to_csv(out_dir / "task_327_full_period_comparison.csv", index=False)
    trade_level_delta_df.to_csv(out_dir / "task_327_trade_level_delta.csv", index=False)
    robustness_df.to_csv(out_dir / "task_327_robustness.csv", index=False)

    _write_markdown_report(out_dir, path_summary_df, prediction_metrics_df, calibration_df, summary_df)


if __name__ == "__main__":
    main()
