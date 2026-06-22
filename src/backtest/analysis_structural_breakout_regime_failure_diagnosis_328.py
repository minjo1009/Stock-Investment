from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    StructuralConfig,
    _load_stock_symbols,
    _prepare_preloaded_frames,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_best_combo_323plus import _anchored_oos_window
from src.backtest.analysis_structural_breakout_regime_conditioned_entry_326 import _assign_archetype
from src.backtest.analysis_structural_breakout_path_conditioned_entry_327 import (
    DEFAULT_OUT_DIR as TASK327_OUT_DIR,
    ENTRY_FEATURES,
    PATH_TYPES,
    _annotate_pre_entry_bands,
    _apply_path_labels,
    _enrich_path_metrics,
    _feature_band_edges,
    _metric_band_edges,
)
from src.backtest.analysis_structural_breakout_regime_entry_325 import (
    RANKED_INPUT,
    _build_entry_feature_lookup,
    _build_regime_lookup,
    _build_universe_state_lookup,
    _config_from_scenario,
    _enrich_trade_frame,
    _select_top10_pool,
    _slice_timestamps,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_328_regime_failure_diagnosis")


def _entropy_from_counts(counts: list[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts:
        if count <= 0:
            continue
        prob = count / total
        entropy -= prob * math.log(prob, 2)
    return float(entropy)


def _series_entropy(series: pd.Series) -> float:
    counts = series.astype(str).value_counts().tolist()
    return round(_entropy_from_counts([int(value) for value in counts]), 6)


def _distribution(series: pd.Series, categories: list[str] | None = None) -> dict[str, float]:
    counts = series.astype(str).value_counts(normalize=True).to_dict()
    keys = categories if categories is not None else sorted(str(key) for key in counts.keys())
    return {str(key): float(counts.get(str(key), 0.0)) for key in keys}


def _total_variation_distance(lhs: dict[str, float], rhs: dict[str, float]) -> float:
    keys = sorted(set(lhs) | set(rhs))
    return round(0.5 * sum(abs(float(lhs.get(key, 0.0)) - float(rhs.get(key, 0.0))) for key in keys), 6)


def _labeled_trade_frames(
    *,
    base_dir: Path,
    ranked_input: Path,
    candidate_pool: int,
    jobs: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stocks = _load_stock_symbols(base_dir, StructuralConfig())
    frames, timestamps = _prepare_preloaded_frames(base_dir, stocks)
    scenarios = _select_top10_pool(
        base_dir=base_dir,
        ranked_input=ranked_input,
        candidate_pool=candidate_pool,
        jobs=jobs,
        stocks=stocks,
        frames=frames,
        timestamps=timestamps,
    )
    latest_end = max(timestamps)
    anchored = _anchored_oos_window(latest_end)
    train_timestamps = _slice_timestamps(timestamps, timestamps[0], anchored.train_end)
    oos_timestamps = _slice_timestamps(timestamps, anchored.test_start, anchored.test_end)
    full_timestamps = timestamps

    universe_state_lookup = _build_universe_state_lookup(frames, stocks)
    regime_lookup = _build_regime_lookup(base_dir, universe_state_lookup)
    metadata_lookup = _build_entry_feature_lookup(frames, stocks, universe_state_lookup, regime_lookup)

    train_frames: list[pd.DataFrame] = []
    oos_frames: list[pd.DataFrame] = []
    full_frames: list[pd.DataFrame] = []
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        train_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=train_timestamps, preloaded_symbols=stocks)
        oos_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=oos_timestamps, preloaded_symbols=stocks)
        full_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=full_timestamps, preloaded_symbols=stocks)
        train_frames.append(_enrich_trade_frame(scenario, train_result, frames, metadata_lookup, "train"))
        oos_frames.append(_enrich_trade_frame(scenario, oos_result, frames, metadata_lookup, "anchored_oos"))
        full_frames.append(_enrich_trade_frame(scenario, full_result, frames, metadata_lookup, "full_period"))

    train_df = pd.concat(train_frames, ignore_index=True) if train_frames else pd.DataFrame()
    oos_df = pd.concat(oos_frames, ignore_index=True) if oos_frames else pd.DataFrame()
    full_df = pd.concat(full_frames, ignore_index=True) if full_frames else pd.DataFrame()

    pre_entry_band_edges = _feature_band_edges(train_df, ENTRY_FEATURES)
    metric_band_edges = _metric_band_edges(_enrich_path_metrics(train_df))
    train_df = _annotate_pre_entry_bands(train_df, pre_entry_band_edges)
    oos_df = _annotate_pre_entry_bands(oos_df, pre_entry_band_edges)
    full_df = _annotate_pre_entry_bands(full_df, pre_entry_band_edges)
    train_df = _apply_path_labels(train_df, metric_band_edges)
    oos_df = _apply_path_labels(oos_df, metric_band_edges)
    full_df = _apply_path_labels(full_df, metric_band_edges)
    for df in (train_df, oos_df, full_df):
        df["entry_archetype"] = df.apply(_assign_archetype, axis=1)
    return train_df, oos_df, full_df


def _regime_outcome_separation(df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    global_expectancy = float(pd.to_numeric(df["realized_R"], errors="coerce").mean())
    rows: list[dict[str, Any]] = []
    for regime_state, scoped in df.groupby("regime_state"):
        path_dist = _distribution(scoped["path_type"], PATH_TYPES)
        rows.append(
            {
                "scope": scope_name,
                "regime_state": str(regime_state),
                "trade_count": int(len(scoped)),
                "expectancy_r": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()), 6),
                "win_rate": round(float((pd.to_numeric(scoped["realized_R"], errors="coerce") > 0).mean()), 6),
                "avg_r": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()), 6),
                "realized_r_std": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").std(ddof=0)), 6),
                "early_failure_share": round(path_dist.get("early_failure", 0.0), 6),
                "strong_continuation_share": round(path_dist.get("strong_continuation", 0.0), 6),
                "volatile_noise_share": round(path_dist.get("volatile_noise", 0.0), 6),
                "global_baseline_gap_r": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()) - global_expectancy, 6),
                "path_mix_entropy": round(_series_entropy(scoped["path_type"]), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "expectancy_r"], ascending=[True, False]).reset_index(drop=True)


def _top2_subbehavior_share(scoped: pd.DataFrame) -> float:
    grouped = (
        scoped.groupby(["entry_archetype", "path_type"], as_index=False)
        .agg(trade_count=("realized_R", "size"))
        .sort_values("trade_count", ascending=False)
    )
    if grouped.empty:
        return 0.0
    return round(float(grouped.head(2)["trade_count"].sum()) / max(int(len(scoped)), 1), 6)


def _heterogeneity_label(value: float, low: float, high: float) -> str:
    if value <= low:
        return "low"
    if value >= high:
        return "high"
    return "medium"


def _regime_internal_heterogeneity(df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for regime_state, scoped in df.groupby("regime_state"):
        rows.append(
            {
                "scope": scope_name,
                "regime_state": str(regime_state),
                "trade_count": int(len(scoped)),
                "realized_r_variance": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0)), 6),
                "path_type_entropy": round(_series_entropy(scoped["path_type"]), 6),
                "follow_through_variance": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").var(ddof=0)), 6),
                "retrace_variance": round(float(pd.to_numeric(scoped["retrace_5d_pct"], errors="coerce").var(ddof=0)), 6),
                "top_2_subbehavior_share": _top2_subbehavior_share(scoped),
            }
        )
    out = pd.DataFrame(rows)
    score = (
        pd.to_numeric(out["realized_r_variance"], errors="coerce").fillna(0.0).rank(pct=True)
        + pd.to_numeric(out["path_type_entropy"], errors="coerce").fillna(0.0).rank(pct=True)
        + pd.to_numeric(out["follow_through_variance"], errors="coerce").fillna(0.0).rank(pct=True)
        + pd.to_numeric(out["retrace_variance"], errors="coerce").fillna(0.0).rank(pct=True)
        - pd.to_numeric(out["top_2_subbehavior_share"], errors="coerce").fillna(0.0).rank(pct=True)
    )
    out["heterogeneity_score"] = score / 5.0
    low = float(out["heterogeneity_score"].quantile(0.33))
    high = float(out["heterogeneity_score"].quantile(0.67))
    out["heterogeneity_diagnosis"] = out["heterogeneity_score"].map(lambda value: _heterogeneity_label(float(value), low, high))
    return out.sort_values(["scope", "heterogeneity_score"], ascending=[True, False]).reset_index(drop=True)


def _path_mix_string(scoped: pd.DataFrame) -> str:
    dist = _distribution(scoped["path_type"], PATH_TYPES)
    return "|".join(f"{key}:{dist[key]:.3f}" for key in PATH_TYPES if dist.get(key, 0.0) > 0)


def _regime_archetype_stability(df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby(["regime_state", "entry_archetype"], as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy_r=("realized_R", "mean"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
            total_r=("realized_R", "sum"),
        )
    )
    archetype_disp = grouped.groupby("entry_archetype")["expectancy_r"].std(ddof=0).to_dict()
    regime_disp = grouped.groupby("regime_state")["expectancy_r"].std(ddof=0).to_dict()
    regime_totals = grouped.groupby("regime_state")["trade_count"].sum().to_dict()
    dominant_share = {
        regime_state: round(float(scoped["trade_count"].max()) / max(int(regime_totals.get(regime_state, 1)), 1), 6)
        for regime_state, scoped in grouped.groupby("regime_state")
    }
    rows: list[dict[str, Any]] = []
    for record in grouped.to_dict("records"):
        regime_state = str(record["regime_state"])
        archetype = str(record["entry_archetype"])
        scoped = df[(df["regime_state"] == regime_state) & (df["entry_archetype"] == archetype)]
        rows.append(
            {
                "scope": scope_name,
                "regime_state": regime_state,
                "entry_archetype": archetype,
                "trade_count": int(record["trade_count"]),
                "expectancy_r": round(float(record["expectancy_r"]), 6),
                "win_rate": round(float(record["win_rate"]), 6),
                "total_r": round(float(record["total_r"]), 6),
                "path_mix": _path_mix_string(scoped),
                "archetype_cross_regime_expectancy_std": round(float(archetype_disp.get(archetype, 0.0) or 0.0), 6),
                "regime_cross_archetype_expectancy_std": round(float(regime_disp.get(regime_state, 0.0) or 0.0), 6),
                "dominant_archetype_share": round(float(dominant_share.get(regime_state, 0.0)), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "regime_state", "trade_count"], ascending=[True, True, False]).reset_index(drop=True)


def _feature_band_mix_shift(train_scoped: pd.DataFrame, oos_scoped: pd.DataFrame) -> float:
    shifts: list[float] = []
    for feature in ENTRY_FEATURES:
        band_col = f"{feature}_band"
        train_dist = _distribution(train_scoped.get(band_col, pd.Series(dtype=str)), ["low", "mid", "high", "unknown"])
        oos_dist = _distribution(oos_scoped.get(band_col, pd.Series(dtype=str)), ["low", "mid", "high", "unknown"])
        shifts.append(_total_variation_distance(train_dist, oos_dist))
    return round(sum(shifts) / max(len(shifts), 1), 6)


def _regime_drift(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    train_total = max(len(train_df), 1)
    oos_total = max(len(oos_df), 1)
    regimes = sorted(set(train_df["regime_state"].astype(str)) | set(oos_df["regime_state"].astype(str)))
    rows: list[dict[str, Any]] = []
    for regime_state in regimes:
        train_scoped = train_df[train_df["regime_state"].astype(str) == regime_state].copy()
        oos_scoped = oos_df[oos_df["regime_state"].astype(str) == regime_state].copy()
        train_share = float(len(train_scoped) / train_total)
        oos_share = float(len(oos_scoped) / oos_total)
        train_expectancy = float(pd.to_numeric(train_scoped["realized_R"], errors="coerce").mean()) if not train_scoped.empty else 0.0
        oos_expectancy = float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").mean()) if not oos_scoped.empty else 0.0
        path_mix_shift = _total_variation_distance(_distribution(train_scoped["path_type"], PATH_TYPES), _distribution(oos_scoped["path_type"], PATH_TYPES))
        archetype_mix_shift = _total_variation_distance(
            _distribution(train_scoped["entry_archetype"]),
            _distribution(oos_scoped["entry_archetype"]),
        )
        feature_mix_shift = _feature_band_mix_shift(train_scoped, oos_scoped)
        share_delta = round(oos_share - train_share, 6)
        expectancy_delta = round(oos_expectancy - train_expectancy, 6)
        if abs(share_delta) >= 0.08 and max(path_mix_shift, archetype_mix_shift) >= 0.25:
            drift_type = "mixed_drift"
        elif abs(share_delta) >= 0.08:
            drift_type = "regime_distribution_drift"
        elif max(path_mix_shift, archetype_mix_shift, feature_mix_shift) >= 0.25 or abs(expectancy_delta) >= 0.35:
            drift_type = "entry_linkage_drift"
        else:
            drift_type = "stable"
        rows.append(
            {
                "regime_state": regime_state,
                "train_trade_count": int(len(train_scoped)),
                "oos_trade_count": int(len(oos_scoped)),
                "trade_share_delta": share_delta,
                "expectancy_delta": expectancy_delta,
                "path_mix_shift": path_mix_shift,
                "feature_band_mix_shift": feature_mix_shift,
                "archetype_mix_shift": archetype_mix_shift,
                "drift_type": drift_type,
            }
        )
    return pd.DataFrame(rows).sort_values(["drift_type", "path_mix_shift", "expectancy_delta"], ascending=[True, False, True]).reset_index(drop=True)


def _failure_mode_attribution(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    grouped = (
        oos_df.groupby(["regime_state", "entry_archetype"], as_index=False)
        .agg(trade_count=("realized_R", "size"), expectancy_r=("realized_R", "mean"))
    )
    weak = grouped[grouped["expectancy_r"] < 0].copy()
    for record in weak.to_dict("records"):
        regime_state = str(record["regime_state"])
        archetype = str(record["entry_archetype"])
        oos_scoped = oos_df[(oos_df["regime_state"] == regime_state) & (oos_df["entry_archetype"] == archetype)].copy()
        train_scoped = train_df[(train_df["regime_state"] == regime_state) & (train_df["entry_archetype"] == archetype)].copy()
        if oos_scoped.empty:
            continue
        train_ft = float(pd.to_numeric(train_scoped["follow_through_5d_pct"], errors="coerce").mean()) if not train_scoped.empty else 0.0
        oos_ft = float(pd.to_numeric(oos_scoped["follow_through_5d_pct"], errors="coerce").mean())
        train_retrace = float(pd.to_numeric(train_scoped["retrace_5d_pct"], errors="coerce").mean()) if not train_scoped.empty else 0.0
        oos_retrace = float(pd.to_numeric(oos_scoped["retrace_5d_pct"], errors="coerce").mean())
        train_mae = float(pd.to_numeric(train_scoped["mae_5d_pct"], errors="coerce").mean()) if not train_scoped.empty else 0.0
        oos_mae = float(pd.to_numeric(oos_scoped["mae_5d_pct"], errors="coerce").mean())
        train_path = _distribution(train_scoped["path_type"], PATH_TYPES)
        oos_path = _distribution(oos_scoped["path_type"], PATH_TYPES)
        class_shift = _total_variation_distance(train_path, oos_path)
        ft_collapse = max(train_ft - oos_ft, 0.0)
        retrace_spike = max(oos_retrace - train_retrace, 0.0)
        mae_spike = max(oos_mae - train_mae, 0.0)
        false_cont_score = min(
            max(train_path.get("strong_continuation", 0.0) - oos_path.get("strong_continuation", 0.0), 0.0)
            + max(oos_path.get("early_failure", 0.0) - train_path.get("early_failure", 0.0), 0.0),
            max(ft_collapse, 0.0),
        )
        driver_scores = {
            "low_follow_through": ft_collapse,
            "high_retrace": retrace_spike,
            "high_volatility_noise": mae_spike + max(oos_path.get("volatile_noise", 0.0) - train_path.get("volatile_noise", 0.0), 0.0),
            "false_continuation": false_cont_score,
            "train_oos_class_drift": class_shift,
        }
        local_scores = {key: value for key, value in driver_scores.items() if key != "train_oos_class_drift"}
        best_local_driver, best_local_score = max(local_scores.items(), key=lambda item: item[1])
        if class_shift >= 0.35 and best_local_score < 0.08:
            failure_driver = "train_oos_class_drift"
        else:
            failure_driver = best_local_driver
        rows.append(
            {
                "regime_state": regime_state,
                "entry_archetype": archetype,
                "trade_count": int(record["trade_count"]),
                "expectancy_r": round(float(record["expectancy_r"]), 6),
                "failure_driver": failure_driver,
                "follow_through_delta": round(oos_ft - train_ft, 6),
                "retrace_delta": round(oos_retrace - train_retrace, 6),
                "mae_delta": round(oos_mae - train_mae, 6),
                "class_drift": class_shift,
                "strong_continuation_share_delta": round(oos_path.get("strong_continuation", 0.0) - train_path.get("strong_continuation", 0.0), 6),
                "early_failure_share_delta": round(oos_path.get("early_failure", 0.0) - train_path.get("early_failure", 0.0), 6),
                "volatile_noise_share_delta": round(oos_path.get("volatile_noise", 0.0) - train_path.get("volatile_noise", 0.0), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["expectancy_r", "trade_count"]).reset_index(drop=True)


def _linkage_diagnosis(
    train_sep: pd.DataFrame,
    oos_sep: pd.DataFrame,
    heterogeneity: pd.DataFrame,
    archetype_stability: pd.DataFrame,
    drift_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    hetero_lookup = heterogeneity.set_index(["scope", "regime_state"]).to_dict("index")
    drift_lookup = drift_df.set_index("regime_state").to_dict("index") if not drift_df.empty else {}
    train_archetype = archetype_stability[archetype_stability["scope"] == "train"].copy()
    train_lookup = train_sep.set_index("regime_state").to_dict("index") if not train_sep.empty else {}
    oos_lookup = oos_sep.set_index("regime_state").to_dict("index") if not oos_sep.empty else {}
    regimes = sorted(set(train_lookup) | set(oos_lookup))
    for regime_state in regimes:
        train_row = train_lookup.get(regime_state, {})
        oos_row = oos_lookup.get(regime_state, {})
        hetero_row = hetero_lookup.get(("train", regime_state), {})
        drift_row = drift_lookup.get(regime_state, {})
        dominant_share = float(
            train_archetype[train_archetype["regime_state"] == regime_state]["dominant_archetype_share"].iloc[0]
        ) if not train_archetype[train_archetype["regime_state"] == regime_state].empty else 0.0
        train_gap = abs(float(train_row.get("global_baseline_gap_r", 0.0)))
        train_entropy = float(train_row.get("path_mix_entropy", 0.0))
        hetero_score = float(hetero_row.get("heterogeneity_score", 0.0))
        linkage_strength = round(max(train_gap, 0.0) * (1.0 - min(train_entropy / 2.5, 1.0)), 6)
        stability_score = round(max(1.0 - float(drift_row.get("path_mix_shift", 1.0)) - abs(float(drift_row.get("trade_share_delta", 0.0))), 0.0), 6)
        train_expectancy = float(train_row.get("expectancy_r", 0.0))
        oos_expectancy = float(oos_row.get("expectancy_r", 0.0))
        if abs(train_expectancy) > 1e-9:
            oos_retention = round(oos_expectancy / train_expectancy, 6)
        else:
            oos_retention = 0.0
        if linkage_strength >= 0.20 and stability_score >= 0.55 and oos_retention > 0.4:
            diagnosis = "strong_and_stable"
        elif linkage_strength >= 0.20 and (stability_score < 0.55 or oos_retention <= 0.4):
            diagnosis = "strong_but_not_stable"
        elif linkage_strength < 0.20 and stability_score >= 0.45 and hetero_score < 0.55:
            diagnosis = "weak_but_consistent"
        elif hetero_score >= 0.55 or dominant_share >= 0.65:
            diagnosis = "weak_and_noisy"
        else:
            diagnosis = "structurally_misspecified"
        rows.append(
            {
                "regime_state": regime_state,
                "linkage_strength_score": linkage_strength,
                "stability_score": stability_score,
                "oos_retention_score": oos_retention,
                "train_expectancy_r": round(train_expectancy, 6),
                "oos_expectancy_r": round(oos_expectancy, 6),
                "train_heterogeneity_score": round(hetero_score, 6),
                "dominant_archetype_share": round(dominant_share, 6),
                "diagnosis": diagnosis,
            }
        )
    return pd.DataFrame(rows).sort_values(["linkage_strength_score", "stability_score"], ascending=[False, False]).reset_index(drop=True)


def _root_cause_ranking(
    linkage_df: pd.DataFrame,
    heterogeneity_df: pd.DataFrame,
    drift_df: pd.DataFrame,
    archetype_stability_df: pd.DataFrame,
) -> pd.DataFrame:
    misspecification = float((linkage_df["diagnosis"] == "structurally_misspecified").mean()) if not linkage_df.empty else 0.0
    heterogeneity = float((heterogeneity_df[heterogeneity_df["scope"] == "train"]["heterogeneity_diagnosis"] == "high").mean()) if not heterogeneity_df.empty else 0.0
    weak_linkage = float((linkage_df["diagnosis"].isin({"weak_but_consistent", "weak_and_noisy"})).mean()) if not linkage_df.empty else 0.0
    drift = float((drift_df["drift_type"].isin({"entry_linkage_drift", "mixed_drift"})).mean()) if not drift_df.empty else 0.0
    dominant_dependence = float((archetype_stability_df[archetype_stability_df["scope"] == "train"]["dominant_archetype_share"] >= 0.65).mean()) if not archetype_stability_df.empty else 0.0
    scores = [
        {
            "root_cause": "regime_misspecification",
            "evidence_score": round(misspecification + max(0.0, 0.5 - weak_linkage) * 0.3, 6),
            "evidence_summary": "low separation or structurally misspecified regimes dominate",
        },
        {
            "root_cause": "within_regime_heterogeneity",
            "evidence_score": round(heterogeneity + dominant_dependence * 0.25, 6),
            "evidence_summary": "high internal variance and subbehavior concentration dominate regimes",
        },
        {
            "root_cause": "weak_entry_feature_linkage",
            "evidence_score": round(weak_linkage + dominant_dependence * 0.2, 6),
            "evidence_summary": "regime does not convert into stable archetype-level expectancy separation",
        },
        {
            "root_cause": "oos_drift",
            "evidence_score": round(drift, 6),
            "evidence_summary": "train-to-OOS regime/path/archetype relationship shifts materially",
        },
        {
            "root_cause": "combination_effect",
            "evidence_score": round((misspecification + heterogeneity + weak_linkage + drift) / 4.0, 6),
            "evidence_summary": "multiple failure modes contribute without a single dominant cause",
        },
    ]
    out = pd.DataFrame(scores).sort_values("evidence_score", ascending=False).reset_index(drop=True)
    top_two_gap = float(out.iloc[0]["evidence_score"] - out.iloc[1]["evidence_score"]) if len(out) > 1 else 1.0
    if top_two_gap > 0.08:
        out.loc[out["root_cause"] == "combination_effect", "evidence_score"] *= 0.85
        out = out.sort_values("evidence_score", ascending=False).reset_index(drop=True)
    out["contribution_rank"] = range(1, len(out) + 1)
    return out[["contribution_rank", "root_cause", "evidence_score", "evidence_summary"]]


def _diagnostic_backtest_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope_name, scoped in df.groupby("scope"):
        total_r = float(pd.to_numeric(scoped["realized_R"], errors="coerce").sum())
        grouped_regime = (
            scoped.groupby("regime_state", as_index=False)
            .agg(trade_count=("realized_R", "size"), total_r=("realized_R", "sum"))
        )
        for record in grouped_regime.to_dict("records"):
            rows.append(
                {
                    "scope": scope_name,
                    "diagnostic_type": "remove_regime_counterfactual",
                    "regime_state": str(record["regime_state"]),
                    "entry_archetype": "",
                    "trade_count": int(record["trade_count"]),
                    "total_r": round(float(record["total_r"]), 6),
                    "counterfactual_total_r": round(total_r - float(record["total_r"]), 6),
                    "contribution_share": round(float(record["total_r"]) / total_r, 6) if total_r != 0 else 0.0,
                }
            )
        grouped_bucket = (
            scoped.groupby(["regime_state", "entry_archetype"], as_index=False)
            .agg(trade_count=("realized_R", "size"), total_r=("realized_R", "sum"))
        )
        weak_bucket = grouped_bucket.sort_values("total_r").head(min(5, len(grouped_bucket)))
        for record in weak_bucket.to_dict("records"):
            rows.append(
                {
                    "scope": scope_name,
                    "diagnostic_type": "remove_weak_bucket_counterfactual",
                    "regime_state": str(record["regime_state"]),
                    "entry_archetype": str(record["entry_archetype"]),
                    "trade_count": int(record["trade_count"]),
                    "total_r": round(float(record["total_r"]), 6),
                    "counterfactual_total_r": round(total_r - float(record["total_r"]), 6),
                    "contribution_share": round(float(record["total_r"]) / total_r, 6) if total_r != 0 else 0.0,
                }
            )
        loss_regime = grouped_regime[grouped_regime["total_r"] < 0].copy()
        dominant_loss_share = 0.0
        if not loss_regime.empty:
            total_loss = abs(float(loss_regime["total_r"].sum()))
            dominant_loss_share = abs(float(loss_regime["total_r"].min())) / max(total_loss, 1e-9)
        rows.append(
            {
                "scope": scope_name,
                "diagnostic_type": "concentration",
                "regime_state": "",
                "entry_archetype": "",
                "trade_count": int(len(scoped)),
                "total_r": round(total_r, 6),
                "counterfactual_total_r": math.nan,
                "contribution_share": round(dominant_loss_share, 6),
            }
        )
    return pd.DataFrame(rows)


def _write_markdown_report(
    out_dir: Path,
    linkage_df: pd.DataFrame,
    root_cause_df: pd.DataFrame,
    drift_df: pd.DataFrame,
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

    top_root = root_cause_df.iloc[0] if not root_cause_df.empty else {}
    lines = [
        "# Task 328: Regime Failure Diagnosis",
        "",
        "## Core Answer",
        "",
        f"- Main root cause: `{top_root.get('root_cause', 'unknown')}`.",
        "- This report answers whether regime definitions are wrong, whether regime alone is too coarse, whether entry linkage is weak, and whether OOS drift is dominant.",
        "",
        "## Regime Entry Linkage Diagnosis",
        "",
    ]
    lines.extend(_fmt(linkage_df))
    lines.extend([
        "",
        "## Regime Drift",
        "",
    ])
    lines.extend(_fmt(drift_df))
    lines.extend([
        "",
        "## Root Cause Ranking",
        "",
    ])
    lines.extend(_fmt(root_cause_df))
    lines.extend([
        "",
        "## Final Conclusion",
        "",
    ])
    if not linkage_df.empty:
        misspecified_share = float((linkage_df["diagnosis"] == "structurally_misspecified").mean())
        weak_noisy_share = float((linkage_df["diagnosis"] == "weak_and_noisy").mean())
        unstable_share = float((linkage_df["diagnosis"] == "strong_but_not_stable").mean())
        lines.append(f"- Regime definition wrong? `{misspecified_share:.2%}` of regimes look structurally misspecified.")
        lines.append(f"- Regime alone too coarse? `{weak_noisy_share:.2%}` of regimes look weak and noisy from internal heterogeneity.")
        lines.append(f"- Entry feature linkage weak or unstable? `{unstable_share:.2%}` of regimes lose linkage stability into OOS.")
    lines.append("- Root causes are ranked above in descending evidence strength.")
    (out_dir / "task_328_regime_failure_diagnosis.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 328: regime failure diagnosis for structural breakout.")
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

    train_df, oos_df, full_df = _labeled_trade_frames(
        base_dir=base_dir,
        ranked_input=ranked_input,
        candidate_pool=args.candidate_pool,
        jobs=args.jobs,
    )

    train_sep_df = _regime_outcome_separation(train_df, "train")
    oos_sep_df = _regime_outcome_separation(oos_df, "anchored_oos")
    full_sep_df = _regime_outcome_separation(full_df, "full_period")
    separation_df = pd.concat([train_sep_df, oos_sep_df, full_sep_df], ignore_index=True)

    train_hetero_df = _regime_internal_heterogeneity(train_df, "train")
    oos_hetero_df = _regime_internal_heterogeneity(oos_df, "anchored_oos")
    full_hetero_df = _regime_internal_heterogeneity(full_df, "full_period")
    heterogeneity_df = pd.concat([train_hetero_df, oos_hetero_df, full_hetero_df], ignore_index=True)

    archetype_train_df = _regime_archetype_stability(train_df, "train")
    archetype_oos_df = _regime_archetype_stability(oos_df, "anchored_oos")
    archetype_full_df = _regime_archetype_stability(full_df, "full_period")
    archetype_stability_df = pd.concat([archetype_train_df, archetype_oos_df, archetype_full_df], ignore_index=True)

    failure_mode_df = _failure_mode_attribution(train_df, oos_df)
    drift_df = _regime_drift(train_df, oos_df)
    linkage_df = _linkage_diagnosis(train_sep_df, oos_sep_df, heterogeneity_df, archetype_stability_df, drift_df)
    root_cause_df = _root_cause_ranking(linkage_df, heterogeneity_df, drift_df, archetype_stability_df)

    baseline_df = pd.concat([train_df, oos_df, full_df], ignore_index=True)
    diagnostic_backtest_df = _diagnostic_backtest_summary(baseline_df)

    separation_df.to_csv(out_dir / "task_328_regime_outcome_separation.csv", index=False)
    heterogeneity_df.to_csv(out_dir / "task_328_regime_internal_heterogeneity.csv", index=False)
    archetype_stability_df.to_csv(out_dir / "task_328_regime_archetype_stability.csv", index=False)
    failure_mode_df.to_csv(out_dir / "task_328_failure_mode_attribution.csv", index=False)
    drift_df.to_csv(out_dir / "task_328_regime_drift.csv", index=False)
    linkage_df.to_csv(out_dir / "task_328_regime_entry_linkage_diagnosis.csv", index=False)
    root_cause_df.to_csv(out_dir / "task_328_root_cause_ranking.csv", index=False)
    diagnostic_backtest_df.to_csv(out_dir / "task_328_diagnostic_backtest_summary.csv", index=False)
    _write_markdown_report(out_dir, linkage_df, root_cause_df, drift_df)


if __name__ == "__main__":
    main()
