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
    _concentration_share,
    _f,
    _portfolio_metrics,
)
from src.backtest.analysis_structural_breakout_coverage_corrected_revalidation_346 import (
    _corrected_build_split_frames,
    _corrected_entry_only_master,
    _corrected_overlay_master,
)
from src.backtest.analysis_structural_breakout_cross_regime_persistence_349 import (
    REGIME_AXES,
    _apply_regime_labels,
    _regime_thresholds,
)
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import DB_PATH, ROLLING_WINDOWS
from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import (
    _add_execution_bands,
    _execution_quality_score,
    _session_timing_bucket,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import _load_intraday_bars


DEFAULT_OUT_DIR = Path("docs/reports/task_350_alpha_family_viability")
FAILURE_CLASS_ORDER = (
    "crowded_continuation_failure",
    "failed_opening_auction",
    "liquidity_fade",
    "volatility_collapse",
    "narrow_leadership",
    "late_participation",
    "weak_breadth_continuation",
    "exhaustion_breakout",
    "failed_retest",
    "intraday_participation_decay",
)
ENVIRONMENT_AXES = (
    "sector_group",
    "market_cap_proxy",
    "volatility_state",
    "liquidity_state",
    "trend_state",
    "crowding_state",
    "sector_leadership_state",
    "macro_shock_state",
    "post_risk_off_state",
    "broad_participation_state",
)
FILTER_APPROACHES = (
    "baseline",
    "static_subset_filter",
    "regime_filter",
    "crowding_filter",
    "dynamic_participation_suppression",
    "adaptive_intraday_suppression",
)


def _safe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _prepare_unified_master() -> pd.DataFrame:
    intraday_df = _load_intraday_bars(DB_PATH)
    coverage_df, feature_parts = _corrected_build_split_frames(intraday_df)
    covered_entry_master = _corrected_entry_only_master(feature_parts).copy()
    covered_entry_master["trade_id"] = covered_entry_master["trade_id"].astype(str)
    covered_entry_master["breakout_timestamp"] = pd.to_datetime(
        covered_entry_master["breakout_timestamp"], errors="coerce", utc=True
    )
    covered_entry_master["session_timing_bucket"] = covered_entry_master["breakout_timestamp"].map(_session_timing_bucket)
    covered_entry_master = _add_execution_bands(covered_entry_master)
    covered_entry_master = _execution_quality_score(covered_entry_master)
    master_df, _ = _corrected_overlay_master(coverage_df, covered_entry_master)
    master_df["trade_id"] = master_df["trade_id"].astype(str)
    extra_columns = [
        "window_mode",
        "breakout_timestamp",
        "breakout_window_volume_surge",
        "relative_volume_percentile",
        "volume_persistence_3bars",
        "breakout_bar_close_location",
        "multi_bar_follow_through_3bars",
        "intraday_pullback_depth_3bars",
        "price_vs_session_vwap_at_breakout",
        "vwap_deviation_at_breakout",
        "vwap_reversion_flag_3bars",
        "vwap_slope_prebreak",
        "return_next_3bars",
        "return_next_5bars",
        "adverse_excursion_next_3bars",
        "breakout_hold_duration_bars",
        "failed_break_count_prebreak",
        "rejection_wick_ratio",
        "false_break_attempts_prebreak",
        "setup_type",
        "breakout_subtype",
        "atr_regime",
        "contraction_regime",
        "volume_surge_regime",
        "vwap_response",
        "breakout_response",
        "size_proxy_bucket",
        "session_timing_bucket",
        "execution_quality_score",
        "execution_quality_bucket",
    ]
    extra_columns.extend(
        [
            col
            for col in covered_entry_master.columns
            if col.endswith("_band348") and col not in extra_columns
        ]
    )
    covered_cols = ["trade_id"] + [col for col in extra_columns if col in covered_entry_master.columns]
    covered_enriched = covered_entry_master[covered_cols].drop_duplicates("trade_id")
    unified = master_df.merge(covered_enriched, on="trade_id", how="left")
    unified["entry_ts"] = pd.to_datetime(unified["entry_ts"], errors="coerce", utc=True)
    unified["exit_ts"] = pd.to_datetime(unified["exit_ts"], errors="coerce", utc=True)
    unified["breakout_timestamp"] = pd.to_datetime(unified["breakout_timestamp"], errors="coerce", utc=True)
    unified["realized_R"] = pd.to_numeric(unified["realized_R"], errors="coerce")
    unified["covered_execution_available"] = unified["window_mode"].astype(str).eq("entry_only")
    train_df = unified[unified["current_split"] == "train"].copy()
    train_rank = _safe_numeric(train_df, "dollar_volume_pre").rank(method="first")
    eval_rank = _safe_numeric(unified, "dollar_volume_pre").rank(method="first")
    if train_rank.notna().sum() >= 3:
        train_q = pd.qcut(train_rank, q=3, labels=["small", "mid", "large"], duplicates="drop")
        q1 = float(train_rank.quantile(1 / 3))
        q2 = float(train_rank.quantile(2 / 3))
        unified["market_cap_proxy"] = np.where(
            eval_rank <= q1,
            "small",
            np.where(eval_rank <= q2, "mid", "large"),
        )
    else:
        unified["market_cap_proxy"] = "mid"
    return unified.reset_index(drop=True)


def _add_universe_environment_labels(master: pd.DataFrame) -> pd.DataFrame:
    train_df = master[master["current_split"] == "train"].copy()
    thresholds = _regime_thresholds(train_df if not train_df.empty else master)
    out = _apply_regime_labels(master.copy(), thresholds)
    ret10_median = float(_safe_numeric(train_df if not train_df.empty else out, "ret_10d_pre").median())
    failed_break_median = float(_safe_numeric(train_df if not train_df.empty else out, "recent_failed_breakouts_20d").median())
    candidate_counts = out.groupby(out["entry_ts"].dt.strftime("%Y-%m-%d"))["trade_id"].transform("count")
    sector_counts = out.groupby([out["entry_ts"].dt.strftime("%Y-%m-%d"), out["sector_group"].astype(str)])["trade_id"].transform("count")
    train_candidate = candidate_counts[out["current_split"] == "train"]
    train_sector = sector_counts[out["current_split"] == "train"]
    candidate_median = float(pd.to_numeric(train_candidate, errors="coerce").median()) if len(train_candidate) else float(pd.to_numeric(candidate_counts, errors="coerce").median())
    sector_median = float(pd.to_numeric(train_sector, errors="coerce").median()) if len(train_sector) else float(pd.to_numeric(sector_counts, errors="coerce").median())
    out["same_day_candidate_count"] = candidate_counts.astype(int)
    out["same_day_sector_candidate_count"] = sector_counts.astype(int)
    out["crowding_state"] = np.where(
        (_safe_numeric(out, "sector_crowding_high") >= 1)
        | (_safe_numeric(out, "recent_failed_breakouts_20d") > failed_break_median)
        | (pd.to_numeric(out["same_day_sector_candidate_count"], errors="coerce") > sector_median),
        "crowded",
        "non_crowded",
    )
    out["broad_participation_state"] = np.where(
        (pd.to_numeric(out["same_day_candidate_count"], errors="coerce") > candidate_median)
        & (out["market_breadth_state"].astype(str) == "broad"),
        "broad_participation",
        "narrow_participation",
    )
    out["post_risk_off_state"] = np.where(
        (out["macro_shock_state"].astype(str) == "stable")
        & (_safe_numeric(out, "ret_10d_pre") > ret10_median)
        & (_safe_numeric(out, "mean_pairwise_corr") > thresholds["mean_pairwise_corr"]),
        "post_risk_off",
        "normal",
    )
    return out


def _scaled_frame(df: pd.DataFrame, multipliers: pd.Series | None = None) -> pd.DataFrame:
    out = df.copy()
    out["size_multiplier"] = 1.0 if multipliers is None else pd.to_numeric(multipliers, errors="coerce").fillna(1.0)
    out["scaled_R"] = pd.to_numeric(out["realized_R"], errors="coerce") * pd.to_numeric(out["size_multiplier"], errors="coerce")
    return out


def _metrics(df: pd.DataFrame, value_col: str = "scaled_R") -> dict[str, Any]:
    scoped = df.copy()
    if value_col != "scaled_R":
        scoped["scaled_R"] = pd.to_numeric(scoped[value_col], errors="coerce")
    perf = _portfolio_metrics(scoped, column="scaled_R")
    realized = pd.to_numeric(scoped["scaled_R"], errors="coerce")
    cost_adjusted = pd.to_numeric(_apply_cost_scaled(scoped, 0.0010, 0.0005), errors="coerce") if not scoped.empty else pd.Series(dtype=float)
    return {
        "trade_count": int(len(scoped)),
        "expectancy": perf["expectancy"],
        "sharpe_proxy": perf["sharpe"],
        "mdd_pct": perf["max_drawdown_pct"],
        "win_rate": _f(float((realized > 0).mean()) * 100.0) if not realized.empty else math.nan,
        "failure_rate": _f(float((realized <= 0).mean()) * 100.0) if not realized.empty else math.nan,
        "cost_adjusted_expectancy": _f(float(cost_adjusted.mean())) if not cost_adjusted.empty else math.nan,
        "concentration": _f(_concentration_share(scoped, "symbol", "scaled_R")) if not scoped.empty else math.nan,
    }


def _positive_window_share(df: pd.DataFrame) -> float:
    positives = 0
    total = 0
    for window in ROLLING_WINDOWS:
        scoped = df[
            (df["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (df["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        if scoped.empty:
            continue
        total += 1
        if float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()) > 0:
            positives += 1
    return float(positives / max(total, 1))


def _decay_speed(df: pd.DataFrame) -> float:
    window_expectancies: list[float] = []
    for window in ROLLING_WINDOWS:
        scoped = df[
            (df["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (df["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        if scoped.empty:
            continue
        window_expectancies.append(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()))
    if len(window_expectancies) < 2:
        return math.nan
    return _f(float(window_expectancies[-1] - window_expectancies[0]))


def _alpha_family_viability(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    total_positive = float(pd.to_numeric(master["realized_R"], errors="coerce").clip(lower=0).sum())
    crowded_delta = {}
    for axis in ENVIRONMENT_AXES:
        for bucket, scoped in master.groupby(axis, dropna=False):
            metrics = _metrics(_scaled_frame(scoped))
            crowded = scoped[scoped["crowding_state"].astype(str) == "crowded"].copy()
            uncrowded = scoped[scoped["crowding_state"].astype(str) == "non_crowded"].copy()
            crowded_expectancy = float(pd.to_numeric(crowded["realized_R"], errors="coerce").mean()) if not crowded.empty else math.nan
            uncrowded_expectancy = float(pd.to_numeric(uncrowded["realized_R"], errors="coerce").mean()) if not uncrowded.empty else math.nan
            positive_share = float(pd.to_numeric(scoped["realized_R"], errors="coerce").clip(lower=0).sum() / max(total_positive, 1e-9))
            rows.append(
                {
                    "environment_axis": axis,
                    "environment_bucket": str(bucket),
                    **metrics,
                    "persistence": _f(_positive_window_share(scoped)),
                    "decay_speed": _decay_speed(scoped),
                    "crowding_sensitivity": _f(crowded_expectancy - uncrowded_expectancy)
                    if not math.isnan(crowded_expectancy) and not math.isnan(uncrowded_expectancy)
                    else math.nan,
                    "environment_dependence": _f(positive_share),
                }
            )
        axis_rows = pd.DataFrame([row for row in rows if row["environment_axis"] == axis])
        if not axis_rows.empty:
            crowded_delta[axis] = {
                "positive_bucket_share": _f(float((pd.to_numeric(axis_rows["expectancy"], errors="coerce") > 0).mean())),
                "positive_window_share": _f(float(pd.to_numeric(axis_rows["persistence"], errors="coerce").mean())),
                "environment_dependence_mean": _f(float(pd.to_numeric(axis_rows["environment_dependence"], errors="coerce").mean())),
            }
    viability_df = pd.DataFrame(rows)

    decay_rows: list[dict[str, Any]] = []
    decay_groups = {
        "full_family": master,
        "crowded_periods": master[master["crowding_state"].astype(str) == "crowded"].copy(),
        "non_crowded_periods": master[master["crowding_state"].astype(str) == "non_crowded"].copy(),
        "tech_led_periods": master[master["sector_leadership_state"].astype(str) == "tech_led"].copy(),
        "non_tech_led_periods": master[master["sector_leadership_state"].astype(str) == "broad_led"].copy(),
    }
    for label, scoped_group in decay_groups.items():
        previous_expectancy = math.nan
        for window in ROLLING_WINDOWS:
            scoped = scoped_group[
                (scoped_group["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
                & (scoped_group["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
            ].copy()
            metrics = _metrics(_scaled_frame(scoped))
            expectancy = pd.to_numeric(pd.Series([metrics["expectancy"]]), errors="coerce").iloc[0]
            decay_rows.append(
                {
                    "group_name": label,
                    "window_id": window.window_id,
                    "trade_count": metrics["trade_count"],
                    "expectancy": metrics["expectancy"],
                    "sharpe_proxy": metrics["sharpe_proxy"],
                    "failure_rate": metrics["failure_rate"],
                    "cost_adjusted_expectancy": metrics["cost_adjusted_expectancy"],
                    "decay_speed": _f(float(expectancy - previous_expectancy)) if not math.isnan(previous_expectancy) and not pd.isna(expectancy) else math.nan,
                    "environment_dependence": _f(float((scoped["crowding_state"].astype(str) == "crowded").mean())) if not scoped.empty else math.nan,
                }
            )
            previous_expectancy = float(expectancy) if not pd.isna(expectancy) else previous_expectancy
    decay_df = pd.DataFrame(decay_rows)

    persistence_rows = []
    for axis, summary in crowded_delta.items():
        persistence_rows.append({"environment_axis": axis, **summary})
    cross_df = pd.DataFrame(persistence_rows)
    return viability_df, decay_df, cross_df


def _assign_failure_classes(master: pd.DataFrame) -> pd.DataFrame:
    out = master.copy()
    train_df = out[out["current_split"] == "train"].copy()
    gap_median = float(_safe_numeric(train_df if not train_df.empty else out, "gap_over_planned_entry_pct").abs().median())
    failed_break_median = float(_safe_numeric(train_df if not train_df.empty else out, "failed_break_count_prebreak").median())
    loser = pd.to_numeric(out["realized_R"], errors="coerce") <= 0
    bad_state = out["cluster_label_base"].astype(str).isin({"dead_breakout", "failed_pop"})
    covered = out["covered_execution_available"].astype(bool)
    out["failure_crowded_continuation_failure"] = loser & (
        (out["crowding_state"].astype(str) == "crowded")
        & ((out["sector_leadership_state"].astype(str) == "tech_led") | bad_state)
    )
    out["failure_failed_opening_auction"] = loser & covered & (
        (out["session_timing_bucket"].astype(str) == "first_30m")
        & (_safe_numeric(out, "gap_over_planned_entry_pct").abs() > gap_median)
        & (out["breakout_response"].astype(str) != "breakout_hold")
    )
    out["failure_liquidity_fade"] = loser & covered & (
        (out.get("volume_persistence_3bars_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "low")
        & (_safe_numeric(out, "return_next_3bars") <= 0)
    )
    out["failure_volatility_collapse"] = loser & covered & (
        (out["volatility_state"].astype(str) == "high_vol")
        & (_safe_numeric(out, "multi_bar_follow_through_3bars") <= 0)
        & (out.get("volume_persistence_3bars_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "low")
    )
    out["failure_narrow_leadership"] = loser & (
        (out["market_breadth_state"].astype(str) == "narrow")
        & (out["sector_leadership_state"].astype(str) == "tech_led")
    )
    out["failure_late_participation"] = loser & covered & (
        (out["session_timing_bucket"].astype(str) == "last_hour")
        & (_safe_numeric(out, "return_next_3bars") < 0)
    )
    out["failure_weak_breadth_continuation"] = loser & (
        (out["market_breadth_state"].astype(str) == "narrow")
        & (
            (~covered)
            | (out["breakout_response"].astype(str) != "breakout_hold")
            | (_safe_numeric(out, "breakout_strength_pct") < _safe_numeric(train_df if not train_df.empty else out, "breakout_strength_pct").median())
        )
    )
    out["failure_exhaustion_breakout"] = loser & (
        (out["gap_environment_state"].astype(str) == "unstable")
        & (
            (~covered)
            | (_safe_numeric(out, "breakout_bar_close_location") < 0.5)
            | (_safe_numeric(out, "return_next_3bars") <= 0)
        )
    )
    out["failure_failed_retest"] = loser & covered & (
        (
            out.get("false_break_attempts_prebreak_band348", pd.Series(index=out.index, dtype=object)).astype(str)
            == "high"
        )
        | (_safe_numeric(out, "failed_break_count_prebreak") > failed_break_median)
    )
    out["failure_intraday_participation_decay"] = loser & covered & (
        (out["execution_quality_bucket"].astype(str) == "weak")
        & (_safe_numeric(out, "return_next_5bars") <= 0)
    )
    out["primary_failure_class"] = "non_failure"
    bad_trade = loser | bad_state
    for failure_name in FAILURE_CLASS_ORDER:
        col = f"failure_{failure_name}"
        out.loc[bad_trade & out["primary_failure_class"].eq("non_failure") & out[col].astype(bool), "primary_failure_class"] = failure_name
    out.loc[bad_trade & out["primary_failure_class"].eq("non_failure") & ~covered, "primary_failure_class"] = "unclassified_execution_blind"
    return out


def _loss_engine_outputs(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    labeled = _assign_failure_classes(master.copy())
    labeled["scaled_R"] = pd.to_numeric(labeled["realized_R"], errors="coerce")
    bad = labeled[labeled["primary_failure_class"] != "non_failure"].copy()
    total_abs_loss = float(pd.to_numeric(bad["scaled_R"], errors="coerce").clip(upper=0).abs().sum())
    daily_total = bad.groupby(bad["entry_ts"].dt.strftime("%Y-%m-%d"))["scaled_R"].sum()
    daily_cum = daily_total.cumsum()
    running_peak = daily_cum.cummax()
    daily_drawdown = running_peak - daily_cum
    decomposition_rows = []
    for failure_type, scoped in bad.groupby("primary_failure_class", dropna=False):
        losses = pd.to_numeric(scoped["scaled_R"], errors="coerce")
        contribution = float(losses.clip(upper=0).abs().sum())
        repeatability = float(scoped["entry_ts"].dt.strftime("%Y-%m-%d").nunique() / max(len(scoped), 1))
        decomposition_rows.append(
            {
                "failure_class": str(failure_type),
                "trade_count": int(len(scoped)),
                "total_loss_contribution": _f(contribution),
                "mdd_contribution": _f(float(daily_drawdown.max()) * (contribution / max(total_abs_loss, 1e-9))),
                "expectancy_drag": _f(float(losses.mean())),
                "persistence_of_failure_class": _f(_positive_window_share(scoped.assign(realized_R=losses * -1.0))),
                "repeatability": _f(repeatability),
                "crowding_dependence": _f(float((scoped["crowding_state"].astype(str) == "crowded").mean())),
            }
        )
    loss_df = pd.DataFrame(decomposition_rows).sort_values("total_loss_contribution", ascending=False).reset_index(drop=True)
    ranking_df = loss_df.copy()
    ranking_df.insert(0, "rank", range(1, len(ranking_df) + 1))

    cluster_rows = []
    cluster_group = bad.groupby(
        [
            bad["entry_ts"].dt.strftime("%Y-%m-%d"),
            bad["sector_group"].astype(str),
            bad["crowding_state"].astype(str),
            bad["market_breadth_state"].astype(str),
        ],
        dropna=False,
    )
    for (date_key, sector, crowding, breadth), scoped in cluster_group:
        losses = pd.to_numeric(scoped["scaled_R"], errors="coerce")
        cluster_rows.append(
            {
                "cluster_date": date_key,
                "sector_group": sector,
                "crowding_state": crowding,
                "market_breadth_state": breadth,
                "trade_count": int(len(scoped)),
                "cluster_total_loss": _f(float(losses.clip(upper=0).abs().sum())),
                "cluster_expectancy_drag": _f(float(losses.mean())),
                "dominant_failure_class": str(scoped["primary_failure_class"].mode().iloc[0]) if not scoped.empty else "",
            }
        )
    cluster_df = pd.DataFrame(cluster_rows).sort_values(["cluster_total_loss", "trade_count"], ascending=[False, False]).reset_index(drop=True)
    return loss_df, ranking_df, cluster_df


def _action_multiplier(action: pd.Series) -> pd.Series:
    return action.map({"keep": 1.0, "reduce": 0.5, "suppress": 0.0}).fillna(1.0)


def _filter_actions(master: pd.DataFrame, approach: str) -> pd.Series:
    base = pd.Series("keep", index=master.index, dtype=object)
    narrow = master["market_breadth_state"].astype(str) == "narrow"
    crowded = master["crowding_state"].astype(str) == "crowded"
    tech_led = master["sector_leadership_state"].astype(str) == "tech_led"
    unstable_gap = master["gap_environment_state"].astype(str) == "unstable"
    late = master.get("session_timing_bucket", pd.Series(index=master.index, dtype=object)).astype(str) == "last_hour"
    weak_exec = master.get("execution_quality_bucket", pd.Series(index=master.index, dtype=object)).astype(str) == "weak"
    weak_auction = master.get("session_timing_bucket", pd.Series(index=master.index, dtype=object)).astype(str).eq("first_30m") & master.get(
        "breakout_response", pd.Series(index=master.index, dtype=object)
    ).astype(str).ne("breakout_hold")
    if approach == "baseline":
        return base
    if approach == "static_subset_filter":
        return pd.Series(np.where(master["is_base_subset"].astype(bool), "keep", "suppress"), index=master.index)
    if approach == "regime_filter":
        return pd.Series(np.where(narrow & tech_led, "suppress", "keep"), index=master.index)
    if approach == "crowding_filter":
        return pd.Series(np.where(crowded, "suppress", "keep"), index=master.index)
    if approach == "dynamic_participation_suppression":
        out = base.copy()
        out.loc[narrow & tech_led & crowded] = "suppress"
        out.loc[unstable_gap & late] = "suppress"
        out.loc[(crowded & weak_auction) | (master["primary_failure_class"].astype(str) == "crowded_continuation_failure")] = "suppress"
        out.loc[out.eq("keep") & (master["broad_participation_state"].astype(str) == "narrow_participation")] = "reduce"
        out.loc[out.eq("keep") & (master["liquidity_state"].astype(str) == "liquidity_contracting")] = "reduce"
        return out
    if approach == "adaptive_intraday_suppression":
        out = base.copy()
        out.loc[weak_exec] = "suppress"
        out.loc[out.eq("keep") & master.get("execution_quality_bucket", pd.Series(index=master.index, dtype=object)).astype(str).eq("mixed")] = "reduce"
        out.loc[out.eq("keep") & crowded & ~master["covered_execution_available"].astype(bool)] = "reduce"
        return out
    raise ValueError(f"unsupported approach: {approach}")


def _filtering_outputs(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_actions = _filter_actions(master, "baseline")
    baseline_frame = _scaled_frame(master, _action_multiplier(baseline_actions))
    baseline_metrics = _metrics(baseline_frame)
    baseline_negative = float(pd.to_numeric(baseline_frame["scaled_R"], errors="coerce").clip(upper=0).sum())
    baseline_large_loss = float(
        pd.to_numeric(baseline_frame["scaled_R"], errors="coerce")[pd.to_numeric(baseline_frame["scaled_R"], errors="coerce") <= -1.0].sum()
    )
    filter_rows = []
    effect_rows = []
    for approach in FILTER_APPROACHES:
        actions = _filter_actions(master, approach)
        scoped = _scaled_frame(master, _action_multiplier(actions))
        scoped["participation_action"] = actions
        metrics = _metrics(scoped)
        filter_rows.append(
            {
                "approach": approach,
                "expectancy": metrics["expectancy"],
                "sharpe_proxy": metrics["sharpe_proxy"],
                "mdd_pct": metrics["mdd_pct"],
                "failure_rate": metrics["failure_rate"],
                "trade_count": int((actions != "suppress").sum()),
                "participation_reduction_pct": _f(float((actions == "suppress").mean()) * 100.0),
            }
        )
        negative_sum = float(pd.to_numeric(scoped["scaled_R"], errors="coerce").clip(upper=0).sum())
        large_loss_sum = float(
            pd.to_numeric(scoped["scaled_R"], errors="coerce")[pd.to_numeric(scoped["scaled_R"], errors="coerce") <= -1.0].sum()
        )
        effect_rows.append(
            {
                "approach": approach,
                "total_loss_avoided": _f(abs(baseline_negative) - abs(negative_sum)),
                "mdd_relief": _f(baseline_metrics["mdd_pct"] - metrics["mdd_pct"]) if not pd.isna(baseline_metrics["mdd_pct"]) and not pd.isna(metrics["mdd_pct"]) else math.nan,
                "expectancy_improvement": _f(metrics["expectancy"] - baseline_metrics["expectancy"]) if not pd.isna(baseline_metrics["expectancy"]) and not pd.isna(metrics["expectancy"]) else math.nan,
                "participation_reduction_pct": _f(float((actions == "suppress").mean()) * 100.0),
                "large_loss_reduction": _f(abs(baseline_large_loss) - abs(large_loss_sum)),
            }
        )
    return pd.DataFrame(filter_rows), pd.DataFrame(effect_rows)


def _identity_outputs(
    viability_df: pd.DataFrame,
    cross_df: pd.DataFrame,
    loss_df: pd.DataFrame,
    suppression_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    positive_bucket_share = float((pd.to_numeric(viability_df["expectancy"], errors="coerce") > 0).mean()) if not viability_df.empty else 0.0
    positive_window_share = float(pd.to_numeric(cross_df["positive_window_share"], errors="coerce").mean()) if not cross_df.empty else 0.0
    crowded_share = float(pd.to_numeric(loss_df.loc[loss_df["failure_class"] == "crowded_continuation_failure", "total_loss_contribution"], errors="coerce").sum())
    total_loss = float(pd.to_numeric(loss_df["total_loss_contribution"], errors="coerce").sum())
    crowded_ratio = crowded_share / max(total_loss, 1e-9)
    best_suppression = suppression_df[suppression_df["approach"].isin({"dynamic_participation_suppression", "adaptive_intraday_suppression"})].copy()
    best_row = best_suppression.sort_values(
        ["expectancy_improvement", "mdd_relief", "total_loss_avoided"],
        ascending=[False, False, False],
    ).iloc[0]
    rows = [
        {
            "identity_type": "broad_scalable_alpha",
            "score": _f(0.5 * positive_bucket_share + 0.5 * positive_window_share),
            "rationale": "Requires broad positive environment coverage and cross-window persistence.",
        },
        {
            "identity_type": "tactical_anomaly",
            "score": _f(max(0.0, 1.0 - positive_bucket_share) * max(positive_window_share, 0.1)),
            "rationale": "Sparse or uneven environment coverage with isolated surviving pockets.",
        },
        {
            "identity_type": "risk_filter",
            "score": _f(max(float(best_row["mdd_relief"]), 0.0) / 25.0),
            "rationale": "Acts mainly by reducing damage rather than lifting broad continuation returns.",
        },
        {
            "identity_type": "participation_suppressor",
            "score": _f(max(float(best_row["expectancy_improvement"]), 0.0) + max(float(best_row["total_loss_avoided"]), 0.0) / max(total_loss, 1e-9)),
            "rationale": "Primary value comes from suppressing participation in high-risk conditions.",
        },
        {
            "identity_type": "execution_aware_overlay",
            "score": _f(max(float(best_row["large_loss_reduction"]), 0.0) / max(total_loss, 1e-9)),
            "rationale": "Covered-trade execution diagnostics improve loss containment.",
        },
        {
            "identity_type": "crowding_avoidance_mechanism",
            "score": _f(crowded_ratio),
            "rationale": "Loss engine dominated by crowding-linked continuation failures.",
        },
    ]
    identity_df = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    top_identity = identity_df.iloc[0]
    monetization_df = pd.DataFrame(
        [
            {
                "interpretation": "dominant_identity",
                "value": str(top_identity["identity_type"]),
                "evidence": str(top_identity["rationale"]),
            },
            {
                "interpretation": "best_suppression_approach",
                "value": str(best_row["approach"]),
                "evidence": f"expectancy_improvement={best_row['expectancy_improvement']}, mdd_relief={best_row['mdd_relief']}",
            },
            {
                "interpretation": "future_research_bias",
                "value": "pivot_to_crowding_failure_risk_models" if str(top_identity["identity_type"]) in {"participation_suppressor", "crowding_avoidance_mechanism", "risk_filter"} else "continue_breakout_family_research",
                "evidence": "Institutional monetization should follow the surviving identity rather than cosmetic breakout refinement.",
            },
        ]
    )
    return identity_df, monetization_df


def _final_decision(
    cross_df: pd.DataFrame,
    identity_df: pd.DataFrame,
    suppression_df: pd.DataFrame,
    viability_df: pd.DataFrame,
) -> pd.DataFrame:
    positive_bucket_share = float((pd.to_numeric(viability_df["expectancy"], errors="coerce") > 0).mean()) if not viability_df.empty else 0.0
    positive_window_share = float(pd.to_numeric(cross_df["positive_window_share"], errors="coerce").mean()) if not cross_df.empty else 0.0
    top_identity = str(identity_df.iloc[0]["identity_type"]) if not identity_df.empty else "broad_scalable_alpha"
    candidate_suppression = suppression_df[
        suppression_df["approach"].isin({"dynamic_participation_suppression", "adaptive_intraday_suppression"})
    ].copy()
    if candidate_suppression.empty:
        candidate_suppression = suppression_df.copy()
    best_suppression = candidate_suppression.sort_values(
        ["expectancy_improvement", "mdd_relief", "total_loss_avoided"],
        ascending=[False, False, False],
    ).iloc[0]
    expectancy_improvement = float(pd.to_numeric(pd.Series([best_suppression["expectancy_improvement"]]), errors="coerce").iloc[0])
    mdd_relief = float(pd.to_numeric(pd.Series([best_suppression["mdd_relief"]]), errors="coerce").iloc[0])
    if positive_bucket_share >= 0.6 and positive_window_share >= 0.6 and top_identity == "broad_scalable_alpha":
        decision = "STRUCTURALLY_ALIVE_BREAKOUT_FAMILY"
        reason = "Breakout family remains positive across broad environments with limited dependence on suppression logic."
    elif top_identity in {"participation_suppressor", "risk_filter", "crowding_avoidance_mechanism"} and expectancy_improvement > 0 and mdd_relief > 0:
        decision = "FAILURE_SUPPRESSION_ALPHA"
        reason = "Surviving edge comes primarily from failure avoidance and dynamic participation suppression."
    elif positive_bucket_share < 0.35 and top_identity == "tactical_anomaly":
        decision = "TACTICAL_ANOMALY_ONLY"
        reason = "Broad breakout family looks weak while only sparse anomaly pockets remain."
    elif positive_bucket_share < 0.25 and expectancy_improvement <= 0:
        decision = "NO_RELIABLE_ALPHA"
        reason = "Neither broad family persistence nor suppression logic provides reliable edge."
    else:
        decision = "DECAYING_CROWDED_ALPHA_FAMILY"
        reason = "Breakout alpha family still exists in places but is materially decayed and crowding-dependent."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "positive_bucket_share": _f(positive_bucket_share),
                "positive_window_share": _f(positive_window_share),
                "top_identity": top_identity,
                "best_suppression_approach": str(best_suppression["approach"]),
            }
        ]
    )


def _report(
    out_dir: Path,
    final_df: pd.DataFrame,
    identity_df: pd.DataFrame,
    monetization_df: pd.DataFrame,
    loss_df: pd.DataFrame,
    suppression_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    top_loss = loss_df.sort_values("total_loss_contribution", ascending=False).head(5)
    top_suppression = suppression_df.sort_values(
        ["expectancy_improvement", "mdd_relief", "total_loss_avoided"],
        ascending=[False, False, False],
    ).head(5)
    lines = [
        "# Task 350 - Alpha Family Viability & Dynamic Failure Suppression",
        "",
        f"- decision: {final_row['decision']}",
        f"- positive_bucket_share: {final_row['positive_bucket_share']}",
        f"- positive_window_share: {final_row['positive_window_share']}",
        f"- top_identity: {final_row['top_identity']}",
        f"- best_suppression_approach: {final_row['best_suppression_approach']}",
        "",
        "## Final Interpretation",
        f"1. Is breakout still structurally alive as an alpha family? {'yes' if str(final_row['decision']) == 'STRUCTURALLY_ALIVE_BREAKOUT_FAMILY' else 'not broadly'}",
        f"2. Is the current edge mostly crowding/phase artifact? {'yes' if str(final_row['decision']) in {'DECAYING_CROWDED_ALPHA_FAMILY', 'TACTICAL_ANOMALY_ONLY', 'FAILURE_SUPPRESSION_ALPHA'} else 'limited'}",
        f"3. Is the surviving edge actually failure suppression rather than continuation prediction? {'yes' if str(final_row['decision']) == 'FAILURE_SUPPRESSION_ALPHA' else 'not primarily'}",
        f"4. Which failure structures explain most portfolio damage? {', '.join(top_loss['failure_class'].astype(str).head(3).tolist()) if not top_loss.empty else 'insufficient_data'}",
        f"5. Can dynamic participation suppression improve the broad breakout universe? {'yes' if top_suppression.empty is False and float(pd.to_numeric(top_suppression.iloc[0]['expectancy_improvement'], errors='coerce')) > 0 else 'no_clear_evidence'}",
        f"6. Should future research continue breakout refinement, or pivot toward crowding/failure-risk models? {'pivot_to_crowding_failure_risk_models' if str(final_row['decision']) in {'FAILURE_SUPPRESSION_ALPHA', 'DECAYING_CROWDED_ALPHA_FAMILY'} else 'continue_breakout_family_research'}",
        "",
        "## Alpha Identity",
        *(_markdown_table(identity_df)),
        "",
        "## Monetization Interpretation",
        *(_markdown_table(monetization_df)),
        "",
        "## Largest Loss Engines",
        *(_markdown_table(top_loss)),
        "",
        "## Best Suppression Effects",
        *(_markdown_table(top_suppression)),
    ]
    (out_dir / "task_350_alpha_family_viability.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 350: breakout alpha family viability and failure suppression")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    master = _prepare_unified_master()
    master = _add_universe_environment_labels(master)
    master = _assign_failure_classes(master)

    viability_df, decay_df, cross_df = _alpha_family_viability(master)
    loss_df, ranking_df, cluster_df = _loss_engine_outputs(master)
    filtering_df, suppression_df = _filtering_outputs(master)
    identity_df, monetization_df = _identity_outputs(viability_df, cross_df, loss_df, suppression_df)
    final_df = _final_decision(cross_df, identity_df, suppression_df, viability_df)

    viability_df.to_csv(out_dir / "task_350_alpha_family_viability.csv", index=False)
    decay_df.to_csv(out_dir / "task_350_breakout_family_decay_analysis.csv", index=False)
    cross_df.to_csv(out_dir / "task_350_cross_environment_persistence.csv", index=False)
    loss_df.to_csv(out_dir / "task_350_loss_engine_decomposition.csv", index=False)
    ranking_df.to_csv(out_dir / "task_350_failure_contribution_ranking.csv", index=False)
    cluster_df.to_csv(out_dir / "task_350_large_loss_clusters.csv", index=False)
    filtering_df.to_csv(out_dir / "task_350_static_vs_dynamic_filtering.csv", index=False)
    suppression_df.to_csv(out_dir / "task_350_adaptive_suppression_effect.csv", index=False)
    identity_df.to_csv(out_dir / "task_350_alpha_identity_classification.csv", index=False)
    monetization_df.to_csv(out_dir / "task_350_monetization_interpretation.csv", index=False)
    final_df.to_csv(out_dir / "task_350_final_decision.csv", index=False)
    _report(out_dir, final_df, identity_df, monetization_df, loss_df, suppression_df)


if __name__ == "__main__":
    main()
