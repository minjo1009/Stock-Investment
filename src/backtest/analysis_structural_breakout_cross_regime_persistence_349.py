from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_conditional_edge_integration_342 import (
    _apply_cost_scaled,
    _f,
    _portfolio_metrics,
)
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import ROLLING_WINDOWS, _rolling_label
from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import (
    SUPPORTED_SECTOR,
    _add_execution_bands,
    _annual_trade_frequency,
    _build_sleeve_frames,
    _capital_utilization_ratio,
    _execution_quality_score,
    _prepare_corrected_entry_master,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_349_cross_regime_persistence")
REGIME_AXES = (
    "volatility_state",
    "trend_state",
    "market_breadth_state",
    "sector_leadership_state",
    "liquidity_state",
    "macro_shock_state",
    "gap_environment_state",
)
FAILURE_TYPES = (
    "immediate_rejection",
    "liquidity_fade",
    "opening_imbalance_failure",
    "gap_exhaustion",
    "crowded_continuation_failure",
    "volatility_collapse",
    "failed_breakout_retest",
    "late_participation_trap",
)


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _regime_thresholds(train_df: pd.DataFrame) -> dict[str, float]:
    return {
        "range_width_10_pre": float(_safe_series(train_df, "range_width_10_pre").median()),
        "ret_20d_pre": float(_safe_series(train_df, "ret_20d_pre").median()),
        "breadth_above_sma20": float(_safe_series(train_df, "breadth_above_sma20").median()),
        "breadth_above_sma50": float(_safe_series(train_df, "breadth_above_sma50").median()),
        "breadth_positive_20d": float(_safe_series(train_df, "breadth_positive_20d").median()),
        "top_sector_dominance_score": float(_safe_series(train_df, "top_sector_dominance_score").median()),
        "tech_concentration_ratio": float(_safe_series(train_df, "tech_concentration_ratio").median()),
        "semis_concentration_ratio": float(_safe_series(train_df, "semis_concentration_ratio").median()),
        "dollar_volume_pre": float(_safe_series(train_df, "dollar_volume_pre").median()),
        "turnover_pre": float(_safe_series(train_df, "turnover_pre").median()),
        "vol_contraction_ratio": float(_safe_series(train_df, "vol_contraction_ratio").median()),
        "dispersion_20d": float(_safe_series(train_df, "dispersion_20d").median()),
        "mean_pairwise_corr": float(_safe_series(train_df, "mean_pairwise_corr").median()),
        "gap_abs": float(_safe_series(train_df.assign(gap_abs=_safe_series(train_df, "gap_over_planned_entry_pct").abs()), "gap_abs").median()),
        "sector_rs_percentile": float(_safe_series(train_df, "sector_rs_percentile").median()),
    }


def _apply_regime_labels(df: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    vol = _safe_series(out, "range_width_10_pre")
    ret20 = _safe_series(out, "ret_20d_pre")
    dist20 = _safe_series(out, "dist_to_sma20_pct")
    breadth20 = _safe_series(out, "breadth_above_sma20")
    breadth50 = _safe_series(out, "breadth_above_sma50")
    breadthpos = _safe_series(out, "breadth_positive_20d")
    topdom = _safe_series(out, "top_sector_dominance_score")
    tech = _safe_series(out, "tech_concentration_ratio")
    dollar = _safe_series(out, "dollar_volume_pre")
    turnover = _safe_series(out, "turnover_pre")
    volcontract = _safe_series(out, "vol_contraction_ratio")
    dispersion = _safe_series(out, "dispersion_20d")
    corr = _safe_series(out, "mean_pairwise_corr")
    gap_abs = _safe_series(out, "gap_over_planned_entry_pct").abs()
    sector_rs = _safe_series(out, "sector_rs_percentile")

    out["volatility_state"] = np.where(vol > thresholds["range_width_10_pre"], "high_vol", "low_vol")
    out["trend_state"] = np.where((ret20 > thresholds["ret_20d_pre"]) & (dist20 > 0), "trend", "chop")
    breadth_votes = (
        (breadth20 > thresholds["breadth_above_sma20"]).astype(int)
        + (breadth50 > thresholds["breadth_above_sma50"]).astype(int)
        + (breadthpos > thresholds["breadth_positive_20d"]).astype(int)
    )
    out["market_breadth_state"] = np.where(breadth_votes >= 2, "broad", "narrow")
    out["sector_leadership_state"] = np.where(
        (tech > thresholds["tech_concentration_ratio"]) | (topdom > thresholds["top_sector_dominance_score"]),
        "tech_led",
        "broad_led",
    )
    liquidity_votes = (
        (dollar > thresholds["dollar_volume_pre"]).astype(int)
        + (turnover > thresholds["turnover_pre"]).astype(int)
        + (volcontract > thresholds["vol_contraction_ratio"]).astype(int)
    )
    out["liquidity_state"] = np.where(liquidity_votes >= 2, "liquidity_expanding", "liquidity_contracting")
    out["macro_shock_state"] = np.where(
        (dispersion > thresholds["dispersion_20d"]) & (corr > thresholds["mean_pairwise_corr"]),
        "stressed",
        "stable",
    )
    out["gap_environment_state"] = np.where(gap_abs > thresholds["gap_abs"], "unstable", "calm")
    out["ai_momentum_proxy"] = np.where(
        (out["sector_group"].astype(str) == SUPPORTED_SECTOR) & (sector_rs > thresholds["sector_rs_percentile"]),
        "ai_momentum",
        "non_ai_momentum",
    )
    return out


def _sleeve_metrics(df: pd.DataFrame) -> dict[str, Any]:
    perf = df.copy()
    perf["size_multiplier"] = 1.0
    perf["scaled_R"] = pd.to_numeric(perf["realized_R"], errors="coerce")
    metrics = _portfolio_metrics(perf)
    realized = pd.to_numeric(perf["realized_R"], errors="coerce")
    failure_rate = float((realized <= 0).mean()) if not perf.empty else math.nan
    return {
        "trade_count": int(len(df)),
        "expectancy": metrics["expectancy"],
        "sharpe_proxy": metrics["sharpe"],
        "max_drawdown_pct": metrics["max_drawdown_pct"],
        "win_rate": _f(float((realized > 0).mean()) * 100.0) if not perf.empty else math.nan,
        "failure_rate": _f(failure_rate * 100.0) if not perf.empty else math.nan,
        "cost_adjusted_expectancy": _f(float(pd.to_numeric(_apply_cost_scaled(perf, 0.0010, 0.0005), errors="coerce").mean()))
        if not perf.empty
        else math.nan,
        "cost_sensitivity": _f(metrics["expectancy"] - float(pd.to_numeric(_apply_cost_scaled(perf, 0.0010, 0.0005), errors="coerce").mean()))
        if not perf.empty and not pd.isna(metrics["expectancy"])
        else math.nan,
    }


def _regime_persistence_matrix(base_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope_name, scoped in (
        ("full_period", base_df),
        ("anchored_oos", base_df[base_df["current_split"] == "anchored_oos"].copy()),
    ):
        total_windows = len(ROLLING_WINDOWS)
        for axis in REGIME_AXES:
            for bucket, bucket_df in scoped.groupby(axis, dropna=False):
                metrics = _sleeve_metrics(bucket_df)
                positive_windows = 0
                for window in ROLLING_WINDOWS:
                    win_df = bucket_df[
                        (bucket_df["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
                        & (bucket_df["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
                    ].copy()
                    if not win_df.empty and float(pd.to_numeric(win_df["realized_R"], errors="coerce").mean()) > 0:
                        positive_windows += 1
                rows.append(
                    {
                        "scope": scope_name,
                        "regime_axis": axis,
                        "regime_bucket": str(bucket),
                        **metrics,
                        "edge_persistence": _f(float(positive_windows / max(total_windows, 1))),
                        "decay_speed": _f(float(metrics["expectancy"] / max(metrics["trade_count"], 1))) if metrics["trade_count"] else math.nan,
                    }
                )
    return pd.DataFrame(rows)


def _regime_transition_analysis(base_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    previous_regimes: dict[str, dict[str, str]] = {}
    for window in ROLLING_WINDOWS:
        train_df = base_df[
            (base_df["entry_ts"] >= pd.Timestamp(window.train_start, tz="UTC"))
            & (base_df["entry_ts"] <= pd.Timestamp(window.train_end, tz="UTC"))
        ].copy()
        oos_df = base_df[
            (base_df["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (base_df["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        thresholds = _regime_thresholds(train_df if not train_df.empty else base_df[base_df["current_split"] == "train"].copy())
        labeled = _apply_regime_labels(oos_df, thresholds)
        expectancy = float(pd.to_numeric(labeled["realized_R"], errors="coerce").mean()) if not labeled.empty else math.nan
        failure_rate = float((pd.to_numeric(labeled["realized_R"], errors="coerce") <= 0).mean()) if not labeled.empty else math.nan
        dominant = {axis: str(labeled[axis].mode().iloc[0]) if not labeled.empty and labeled[axis].notna().any() else "unknown" for axis in REGIME_AXES}
        if previous_regimes:
            last_key = sorted(previous_regimes.keys())[-1]
            prev = previous_regimes[last_key]
            transition = ";".join(f"{axis}:{prev[axis]}->{dominant[axis]}" for axis in REGIME_AXES if prev[axis] != dominant[axis]) or "no_change"
        else:
            transition = "initial_window"
        rows.append(
            {
                "window_id": window.window_id,
                "transition_direction": transition,
                "trade_count": int(len(labeled)),
                "expectancy": _f(expectancy) if not math.isnan(expectancy) else math.nan,
                "failure_rate": _f(failure_rate * 100.0) if not math.isnan(failure_rate) else math.nan,
                "dominant_volatility_state": dominant["volatility_state"],
                "dominant_trend_state": dominant["trend_state"],
                "dominant_market_breadth_state": dominant["market_breadth_state"],
                "dominant_sector_leadership_state": dominant["sector_leadership_state"],
            }
        )
        previous_regimes[window.window_id] = dominant
    out = pd.DataFrame(rows)
    if not out.empty:
        out["expectancy_change"] = pd.to_numeric(out["expectancy"], errors="coerce").diff()
        out["failure_rate_change"] = pd.to_numeric(out["failure_rate"], errors="coerce").diff()
    return out


def _regime_edge_decay(matrix_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    anchored = matrix_df[matrix_df["scope"] == "anchored_oos"].copy()
    for axis in REGIME_AXES:
        axis_df = anchored[anchored["regime_axis"] == axis].copy()
        for bucket, bucket_df in axis_df.groupby("regime_bucket", dropna=False):
            expectancy = pd.to_numeric(bucket_df["expectancy"], errors="coerce")
            persistence = pd.to_numeric(bucket_df["edge_persistence"], errors="coerce")
            rows.append(
                {
                    "regime_axis": axis,
                    "regime_bucket": str(bucket),
                    "rolling_expectancy_slope": _f(float(expectancy.mean())) if not expectancy.empty else math.nan,
                    "persistence_ratio": _f(float(persistence.mean())) if not persistence.empty else math.nan,
                    "decay_speed": _f(float((expectancy.min() - expectancy.max()))) if expectancy.notna().any() else math.nan,
                }
            )
    return pd.DataFrame(rows)


def _artifact_tag(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["artifact_ai_momentum"] = (
        (out["sector_group"].astype(str) == SUPPORTED_SECTOR)
        & (_safe_series(out, "sector_rs_percentile") > float(_safe_series(out[out["current_split"] == "train"], "sector_rs_percentile").median()))
    )
    out["artifact_software_internet_concentration"] = out["sector_group"].astype(str) == SUPPORTED_SECTOR
    out["artifact_volatility_expansion_cluster"] = (
        (out["volatility_state"].astype(str) == "high_vol")
        & (out["liquidity_state"].astype(str) == "liquidity_expanding")
    )
    out["artifact_high_beta_melt_up"] = (
        (out["trend_state"].astype(str) == "trend")
        & (out["sector_leadership_state"].astype(str) == "tech_led")
        & (out["market_breadth_state"].astype(str) == "broad")
    )
    out["artifact_liquidity_squeeze"] = (
        (out["liquidity_state"].astype(str) == "liquidity_expanding")
        & (out["market_breadth_state"].astype(str) == "narrow")
    )
    out["artifact_gamma_style_expansion"] = (
        (out["gap_environment_state"].astype(str) == "unstable")
        & (out["sector_leadership_state"].astype(str) == "tech_led")
        & (out["volatility_state"].astype(str) == "high_vol")
    )
    out["artifact_post_risk_off_rebound"] = (
        (out["macro_shock_state"].astype(str) == "stable")
        & (out["trend_state"].astype(str) == "trend")
        & (out["market_breadth_state"].astype(str) == "broad")
    )
    return out


def _market_phase_dependency(base_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tagged = _artifact_tag(base_df)
    rows: list[dict[str, Any]] = []
    artifact_cols = [col for col in tagged.columns if col.startswith("artifact_")]
    total_positive = float(pd.to_numeric(tagged["realized_R"], errors="coerce").clip(lower=0).sum())
    for col in artifact_cols:
        scoped = tagged[tagged[col].astype(bool)].copy()
        contribution = float(pd.to_numeric(scoped["realized_R"], errors="coerce").clip(lower=0).sum())
        rows.append(
            {
                "artifact_name": col.replace("artifact_", ""),
                "trade_count": int(len(scoped)),
                "expectancy": _f(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean())) if not scoped.empty else math.nan,
                "positive_pnl_proxy_share": _f(contribution / max(total_positive, 1e-9)),
            }
        )
    dependency_df = pd.DataFrame(rows)

    theme_rows = []
    for (sector, family), scoped in tagged.groupby(["sector_group", "scenario_family"], dropna=False):
        theme_rows.append(
            {
                "sector_group": str(sector),
                "scenario_family": str(family),
                "trade_count": int(len(scoped)),
                "expectancy": _f(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean())) if not scoped.empty else math.nan,
                "supported_sleeve_share": _f(float((scoped["sector_group"].astype(str) == SUPPORTED_SECTOR).mean())),
            }
        )
    theme_df = pd.DataFrame(theme_rows)

    beta_rows = []
    for sector, scoped in tagged.groupby("sector_group", dropna=False):
        beta_rows.append(
            {
                "sector_group": str(sector),
                "trade_count": int(len(scoped)),
                "expectancy": _f(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean())) if not scoped.empty else math.nan,
                "trend_share": _f(float((scoped["trend_state"].astype(str) == "trend").mean())),
                "tech_led_share": _f(float((scoped["sector_leadership_state"].astype(str) == "tech_led").mean())),
            }
        )
    beta_df = pd.DataFrame(beta_rows)

    temporary_mask = np.zeros(len(tagged), dtype=bool)
    for col in artifact_cols:
        temporary_mask |= tagged[col].astype(bool).to_numpy()
    temporary_contrib = float(pd.to_numeric(tagged.loc[temporary_mask, "realized_R"], errors="coerce").clip(lower=0).sum())
    persistent_contrib = float(pd.to_numeric(tagged.loc[~temporary_mask, "realized_R"], errors="coerce").clip(lower=0).sum())
    attribution_df = pd.DataFrame(
        [
            {
                "persistent_structure_share": _f(persistent_contrib / max(total_positive, 1e-9)),
                "temporary_phase_share": _f(temporary_contrib / max(total_positive, 1e-9)),
            }
        ]
    )
    return dependency_df, theme_df, beta_df, attribution_df


def _assign_failure_types(base_df: pd.DataFrame) -> pd.DataFrame:
    out = base_df.copy()
    loser = pd.to_numeric(out["realized_R"], errors="coerce") <= 0
    bad_state = out["cluster_label_base"].astype(str).isin({"dead_breakout", "failed_pop"})
    gap_abs = _safe_series(out, "gap_over_planned_entry_pct").abs()
    gap_median = float(gap_abs[out["current_split"] == "train"].median()) if (out["current_split"] == "train").any() else float(gap_abs.median())
    out["failure_immediate_rejection"] = (
        (out["breakout_response"].astype(str) != "breakout_hold")
        & (_safe_series(out, "breakout_hold_duration_bars") == 0)
        & loser
    )
    out["failure_liquidity_fade"] = (
        (out.get("volume_persistence_3bars_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "low")
        & (_safe_series(out, "return_next_3bars") <= 0)
        & loser
    )
    out["failure_opening_imbalance_failure"] = (
        (out["session_timing_bucket"].astype(str) == "first_30m")
        & (gap_abs > gap_median)
        & (loser | bad_state)
    )
    out["failure_gap_exhaustion"] = (
        (out["gap_environment_state"].astype(str) == "unstable")
        & (
            (_safe_series(out, "breakout_bar_close_location") < 0.5)
            | (_safe_series(out, "return_next_3bars") <= 0)
        )
        & loser
    )
    out["failure_crowded_continuation_failure"] = (
        ((_safe_series(out, "sector_crowding_high") >= 1) | (out["sector_leadership_state"].astype(str) == "tech_led"))
        & bad_state
    )
    out["failure_volatility_collapse"] = (
        (out["volatility_state"].astype(str) == "high_vol")
        & (_safe_series(out, "multi_bar_follow_through_3bars") <= 0)
        & (out.get("volume_persistence_3bars_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "low")
        & loser
    )
    out["failure_failed_breakout_retest"] = (
        (out.get("false_break_attempts_prebreak_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "high")
        & bad_state
    )
    out["failure_late_participation_trap"] = (
        (out["session_timing_bucket"].astype(str) == "last_hour")
        & (_safe_series(out, "return_next_3bars") < 0)
        & loser
    )
    return out


def _failure_anatomy_outputs(base_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    failed = _assign_failure_types(base_df.copy())
    failed["slippage_sensitive_loss_proxy"] = pd.to_numeric(_apply_cost_scaled(_uniform_scaled(failed), 0.0010, 0.0005), errors="coerce")
    bad_universe = failed[
        (pd.to_numeric(failed["realized_R"], errors="coerce") <= 0)
        | failed["cluster_label_base"].astype(str).isin({"dead_breakout", "failed_pop"})
    ].copy()
    breakdown_rows = []
    timing_rows = []
    micro_rows = []
    for failure_name in FAILURE_TYPES:
        col = f"failure_{failure_name}"
        scoped = bad_universe[bad_universe[col].astype(bool)].copy()
        if scoped.empty:
            breakdown_rows.append(
                {
                    "failure_type": failure_name,
                    "trade_count": 0,
                    "expectancy": math.nan,
                    "share_of_failures": 0.0,
                    "mean_slippage_sensitive_loss_proxy": math.nan,
                }
            )
            continue
        realized = pd.to_numeric(scoped["realized_R"], errors="coerce")
        breakdown_rows.append(
            {
                "failure_type": failure_name,
                "trade_count": int(len(scoped)),
                "expectancy": _f(float(realized.mean())),
                "share_of_failures": _f(float(len(scoped) / max(len(bad_universe), 1))),
                "mean_slippage_sensitive_loss_proxy": _f(float(pd.to_numeric(scoped["slippage_sensitive_loss_proxy"], errors="coerce").mean())),
            }
        )
        for bucket, bucket_df in scoped.groupby("session_timing_bucket", dropna=False):
            timing_rows.append(
                {
                    "failure_type": failure_name,
                    "session_timing_bucket": str(bucket),
                    "trade_count": int(len(bucket_df)),
                    "mean_breakout_hold_duration": _f(float(_safe_series(bucket_df, "breakout_hold_duration_bars").mean())),
                    "failure_frequency": _f(float(len(bucket_df) / max(len(scoped), 1))),
                }
            )
        micro_rows.append(
            {
                "failure_type": failure_name,
                "vwap_hold_share": _f(float((scoped["vwap_response"].astype(str) == "vwap_hold").mean())),
                "breakout_hold_share": _f(float((scoped["breakout_response"].astype(str) == "breakout_hold").mean())),
                "weak_volume_share": _f(float((scoped.get("volume_persistence_3bars_band348", pd.Series(index=scoped.index, dtype=object)).astype(str) == "low").mean())),
                "high_rejection_share": _f(float((scoped.get("rejection_wick_ratio_band348", pd.Series(index=scoped.index, dtype=object)).astype(str) == "high").mean())),
            }
        )
    return pd.DataFrame(breakdown_rows), pd.DataFrame(timing_rows), pd.DataFrame(micro_rows)


def _uniform_scaled(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["size_multiplier"] = 1.0
    out["scaled_R"] = pd.to_numeric(out["realized_R"], errors="coerce")
    return out


def _scorecard(matrix_df: pd.DataFrame, decay_df: pd.DataFrame, theme_df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
    anchored = matrix_df[matrix_df["scope"] == "anchored_oos"].copy()
    regime_positive_share = float((pd.to_numeric(anchored["expectancy"], errors="coerce") > 0).mean()) if not anchored.empty else 0.0
    time_robustness = float((pd.to_numeric(decay_df["persistence_ratio"], errors="coerce") > 0.5).mean()) if not decay_df.empty else 0.0
    cost_robustness = float((pd.to_numeric(anchored["cost_adjusted_expectancy"], errors="coerce") > 0).mean()) if not anchored.empty else 0.0
    sector_robustness = float((pd.to_numeric(theme_df["expectancy"], errors="coerce") > 0).mean()) if not theme_df.empty else 0.0
    exec_bucket = features_df.groupby("execution_quality_bucket")["realized_R"].mean() if not features_df.empty else pd.Series(dtype=float)
    exec_spread = float(exec_bucket.max() - exec_bucket.min()) if len(exec_bucket) >= 2 else 0.0
    symbol_share = float(features_df["symbol"].astype(str).value_counts(normalize=True).iloc[0]) if not features_df.empty else 1.0
    sector_share = float(features_df["sector_group"].astype(str).value_counts(normalize=True).iloc[0]) if not features_df.empty else 1.0
    decay_mean = float(pd.to_numeric(decay_df["decay_speed"], errors="coerce").mean()) if not decay_df.empty else 0.0

    def _band(value: float, reverse: bool = False) -> int:
        comp = -value if reverse else value
        if comp >= 0.75:
            return 3
        if comp >= 0.5:
            return 2
        if comp >= 0.25:
            return 1
        return 0

    return pd.DataFrame(
        [
            {"dimension": "regime_robustness", "score_0_to_3": _band(regime_positive_share)},
            {"dimension": "time_robustness", "score_0_to_3": _band(time_robustness)},
            {"dimension": "cost_robustness", "score_0_to_3": _band(cost_robustness)},
            {"dimension": "sector_robustness", "score_0_to_3": _band(sector_robustness)},
            {"dimension": "execution_robustness", "score_0_to_3": _band(min(exec_spread, 1.0))},
            {"dimension": "concentration_fragility", "score_0_to_3": _band(max(symbol_share, sector_share), reverse=True)},
            {"dimension": "decay_sensitivity", "score_0_to_3": _band(abs(decay_mean), reverse=True)},
        ]
    )


def _viability(base_df: pd.DataFrame, scorecard_df: pd.DataFrame, capacity_df: pd.DataFrame) -> pd.DataFrame:
    anchored = base_df[base_df["current_split"] == "anchored_oos"].copy()
    cap_row = capacity_df[(capacity_df["sleeve_name"] == "base_tactical_sleeve") & (capacity_df["scope"] == "anchored_oos")].iloc[0]
    score_map = {str(row["dimension"]): int(row["score_0_to_3"]) for _, row in scorecard_df.iterrows()}
    exec_fragility = "high" if score_map["execution_robustness"] <= 1 else ("medium" if score_map["execution_robustness"] == 2 else "low")
    shadow_suitability = "ready" if score_map["regime_robustness"] >= 2 and exec_fragility != "high" else "not_ready"
    live_decay = "high" if score_map["decay_sensitivity"] <= 1 else ("medium" if score_map["decay_sensitivity"] == 2 else "low")
    return pd.DataFrame(
        [
            {
                "expected_annual_trade_count": _f(_annual_trade_frequency(base_df)),
                "capital_utilization": cap_row["capital_utilization_ratio"],
                "capacity_risk": cap_row["estimated_capacity_risk"],
                "concentration_risk": "high" if max(float(cap_row["symbol_concentration_share"]), float(cap_row["sector_concentration_share"])) > 0.5 else "medium" if max(float(cap_row["symbol_concentration_share"]), float(cap_row["sector_concentration_share"])) > 0.35 else "low",
                "execution_fragility": exec_fragility,
                "expected_live_slippage": _f(abs(float(pd.to_numeric(anchored["realized_R"], errors="coerce").mean()) - float(pd.to_numeric(_apply_cost_scaled(_uniform_scaled(anchored), 0.0010, 0.0005), errors="coerce").mean()))) if not anchored.empty else math.nan,
                "shadow_monitor_suitability": shadow_suitability,
                "likely_live_decay_risk": live_decay,
            }
        ]
    )


def _shadow_readiness(scorecard_df: pd.DataFrame, failure_df: pd.DataFrame, viability_df: pd.DataFrame) -> pd.DataFrame:
    score_map = {str(row["dimension"]): int(row["score_0_to_3"]) for _, row in scorecard_df.iterrows()}
    failure_nonzero = int((pd.to_numeric(failure_df["trade_count"], errors="coerce") > 0).sum())
    ready = str(viability_df.iloc[0]["shadow_monitor_suitability"]) == "ready"
    rows = [
        ("execution_quality_bucket_stability", "pass" if score_map["execution_robustness"] >= 2 else "fail"),
        ("regime_transition_survival", "pass" if score_map["regime_robustness"] >= 2 and score_map["time_robustness"] >= 2 else "fail"),
        ("cost_drift_tolerance", "pass" if score_map["cost_robustness"] >= 2 else "fail"),
        ("sector_concentration_control", "pass" if score_map["concentration_fragility"] >= 2 else "fail"),
        ("failure_anatomy_repeatability", "pass" if failure_nonzero >= 4 else "fail"),
        ("slippage_monitoring_ready", "pass" if ready else "fail"),
    ]
    return pd.DataFrame(rows, columns=["gate_name", "status"])


def _final_decision(attribution_df: pd.DataFrame, scorecard_df: pd.DataFrame, shadow_df: pd.DataFrame) -> pd.DataFrame:
    temp_share = float(attribution_df.iloc[0]["temporary_phase_share"])
    pers_share = float(attribution_df.iloc[0]["persistent_structure_share"])
    score_map = {str(row["dimension"]): int(row["score_0_to_3"]) for _, row in scorecard_df.iterrows()}
    weak_count = sum(int(score_map[dim] <= 1) for dim in ("regime_robustness", "time_robustness", "cost_robustness", "execution_robustness"))
    shadow_passes = int((shadow_df["status"].astype(str) == "pass").sum())
    if temp_share > pers_share and (score_map["regime_robustness"] <= 1 or score_map["time_robustness"] <= 1):
        decision = "TEMPORARY_MARKET_PHASE_ARTIFACT"
        reason = "Temporary phase concentration dominates and persistence scores break under regime/time checks."
    elif weak_count >= 2:
        decision = "FRAGILE_TACTICAL_EDGE"
        reason = "Tactical sleeve exists, but persistence remains weak across multiple robustness dimensions."
    elif shadow_passes == len(shadow_df) and score_map["regime_robustness"] >= 2 and score_map["execution_robustness"] >= 2:
        decision = "TACTICAL_EDGE_SHADOW_READY"
        reason = "Tactical sleeve survives persistence checks well enough to justify shadow deployment."
    else:
        decision = "PERSISTENT_TACTICAL_EDGE"
        reason = "Tactical sleeve looks structurally persistent, but shadow deployment gates are not fully proven yet."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "persistent_structure_share": _f(pers_share),
                "temporary_phase_share": _f(temp_share),
                "weak_dimension_count": weak_count,
                "shadow_pass_count": shadow_passes,
            }
        ]
    )


def _report(
    out_dir: Path,
    final_df: pd.DataFrame,
    viability_df: pd.DataFrame,
    scorecard_df: pd.DataFrame,
    attribution_df: pd.DataFrame,
    failure_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    viability_row = viability_df.iloc[0]
    attribution_row = attribution_df.iloc[0]
    score_table = scorecard_df.copy()
    failure_sorted = failure_df.sort_values(["trade_count", "share_of_failures"], ascending=[False, False]).head(5)
    lines = [
        "# Task 349 - Cross-Regime Persistence & Failure Anatomy",
        "",
        f"- decision: {final_row['decision']}",
        f"- persistent_structure_share: {final_row['persistent_structure_share']}",
        f"- temporary_phase_share: {final_row['temporary_phase_share']}",
        f"- weak_dimension_count: {final_row['weak_dimension_count']}",
        f"- shadow_pass_count: {final_row['shadow_pass_count']}",
        "",
        "## Final Interpretation",
        f"1. Structural or phase-dependent: {'phase-dependent' if float(attribution_row['temporary_phase_share']) > float(attribution_row['persistent_structure_share']) else 'more structural than phase-bound'}",
        f"2. Survives regime transitions: {'yes, with fragility' if str(final_row['decision']) != 'TEMPORARY_MARKET_PHASE_ARTIFACT' else 'no'}",
        f"3. Breakout logic or liquidity/volatility proxy: {'still strongly influenced by liquidity/volatility conditions' if float(attribution_row['temporary_phase_share']) >= 0.4 else 'breakout logic retains independent structure'}",
        f"4. Winner selection or failure avoidance: {'failure avoidance' if not failure_sorted.empty and float(pd.to_numeric(failure_sorted.iloc[0]['trade_count'], errors='coerce')) > 0 else 'unclear'}",
        f"5. Tactical sleeve deployability: {'not shadow-ready yet' if str(final_row['decision']) == 'TEMPORARY_MARKET_PHASE_ARTIFACT' else viability_row['shadow_monitor_suitability']}",
        f"6. What remains before shadow: regime-transition survival, concentration control, slippage drift monitoring, and execution-quality persistence.",
        "",
        "## Persistence Scorecard",
        *(_markdown_table(score_table)),
        "",
        "## Top Failure Types",
        *(_markdown_table(failure_sorted)),
    ]
    (out_dir / "task_349_cross_regime_persistence.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 349 cross-regime persistence")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master = _prepare_corrected_entry_master()
    train_df = master[master["current_split"] == "train"].copy()
    thresholds = _regime_thresholds(train_df)
    labeled_master = _apply_regime_labels(master, thresholds)
    sleeve_frames = _build_sleeve_frames(labeled_master)
    base_df = sleeve_frames["base_tactical_sleeve"].copy()
    base_df = _add_execution_bands(base_df)
    base_df["session_timing_bucket"] = pd.to_datetime(base_df["breakout_timestamp"], errors="coerce", utc=True).map(
        lambda ts: "unknown" if pd.isna(ts) else ("first_30m" if ((pd.Timestamp(ts).tz_convert("America/New_York") - (pd.Timestamp(ts).tz_convert("America/New_York").normalize() + pd.Timedelta(hours=9, minutes=30))).total_seconds() / 60.0) < 30 else ("last_hour" if ((pd.Timestamp(ts).tz_convert("America/New_York") - (pd.Timestamp(ts).tz_convert("America/New_York").normalize() + pd.Timedelta(hours=9, minutes=30))).total_seconds() / 60.0) >= 330 else "mid_session"))
    )
    base_df = _execution_quality_score(base_df)

    matrix_df = _regime_persistence_matrix(base_df)
    transition_df = _regime_transition_analysis(base_df)
    decay_df = _regime_edge_decay(matrix_df)
    dependency_df, theme_df, beta_df, attribution_df = _market_phase_dependency(base_df)
    failure_df, failure_timing_df, failure_micro_df = _failure_anatomy_outputs(base_df)
    scorecard_df = _scorecard(matrix_df, decay_df, theme_df, base_df)
    capacity_df = pd.read_csv(Path("docs/reports/task_348_tactical_breakout_sleeve/task_348_sleeve_capacity_concentration.csv"))
    viability_df = _viability(base_df, scorecard_df, capacity_df)
    shadow_df = _shadow_readiness(scorecard_df, failure_df, viability_df)
    final_df = _final_decision(attribution_df, scorecard_df, shadow_df)

    matrix_df.to_csv(out_dir / "task_349_regime_persistence_matrix.csv", index=False)
    transition_df.to_csv(out_dir / "task_349_regime_transition_analysis.csv", index=False)
    decay_df.to_csv(out_dir / "task_349_regime_edge_decay.csv", index=False)
    dependency_df.to_csv(out_dir / "task_349_market_phase_dependency.csv", index=False)
    theme_df.to_csv(out_dir / "task_349_theme_concentration.csv", index=False)
    beta_df.to_csv(out_dir / "task_349_sector_beta_dependency.csv", index=False)
    failure_df.to_csv(out_dir / "task_349_failure_anatomy_breakdown.csv", index=False)
    failure_timing_df.to_csv(out_dir / "task_349_failure_timing_analysis.csv", index=False)
    failure_micro_df.to_csv(out_dir / "task_349_failure_microstructure_patterns.csv", index=False)
    scorecard_df.to_csv(out_dir / "task_349_persistence_scorecard.csv", index=False)
    viability_df.to_csv(out_dir / "task_349_tactical_sleeve_viability.csv", index=False)
    shadow_df.to_csv(out_dir / "task_349_shadow_readiness.csv", index=False)
    final_df.to_csv(out_dir / "task_349_final_decision.csv", index=False)
    _report(out_dir, final_df, viability_df, scorecard_df, attribution_df, failure_df)


if __name__ == "__main__":
    main()
