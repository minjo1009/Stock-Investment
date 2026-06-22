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
from src.backtest.analysis_structural_breakout_continuation_regime_persistence_351 import (
    _artifact_vs_structure,
    _candidate_rows,
    _positive_tail_persistence,
    _prepare_continuation_master,
)
from src.backtest.analysis_structural_breakout_continuation_regime_reframing_352 import _relative_ranking
from src.backtest.analysis_structural_breakout_regime_continuation_sleeve_353 import (
    SIZING_TEMPLATES,
    _selected_regimes,
)
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import ROLLING_WINDOWS
from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _annual_trade_frequency


DEFAULT_OUT_DIR = Path("docs/reports/task_354_regime_sleeve_deployment")
TIMING_ORDER = (
    "pre_open_allocator",
    "opening_drive_allocator",
    "post_confirmation_allocator",
)
ALPHA_SOURCES = (
    "single_best_binary",
    "top_regime_basket_binary",
    "regime_conditioned_overlay_balanced",
    "sizing_template_aggressive",
    "artifact_half_plus",
)
ALLOCATORS = (
    "regime_priority_allocator",
    "convexity_weighted_allocator",
    "structural_balance_allocator",
    "capital_efficiency_allocator",
)
CAPITAL_BUCKETS = (
    ("bucket_5pct", 0.05),
    ("bucket_10pct", 0.10),
    ("bucket_20pct", 0.20),
)
MAX_POSITIONS = (1, 3, 5)
NETTING_MODES = (
    "allow_duplicate_exposure",
    "symbol_netting",
    "sector_cap_netting",
)
STRESS_SCENARIOS = (
    "baseline",
    "higher_slippage",
    "opening_penalty",
    "confirmation_delay_penalty",
    "combined_stress",
)
AXIS_AVAILABILITY = {
    "volatility_state": "pre_open_allocator",
    "liquidity_state": "pre_open_allocator",
    "market_breadth_state": "pre_open_allocator",
    "sector_leadership_state": "pre_open_allocator",
    "post_risk_off_state": "pre_open_allocator",
    "broad_participation_state": "opening_drive_allocator",
    "session_timing_bucket": "opening_drive_allocator",
    "execution_quality_bucket": "post_confirmation_allocator",
}
TIMING_RANK = {name: idx for idx, name in enumerate(TIMING_ORDER)}


def _safe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _percentile_rank(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.notna().sum() <= 1:
        return pd.Series(np.where(values.notna(), 1.0, math.nan), index=series.index, dtype=float)
    return values.rank(method="average", pct=True)


def _prepare_task354_context() -> tuple[pd.DataFrame, pd.DataFrame]:
    master = _prepare_continuation_master().copy().reset_index(drop=True)
    master["event_id"] = master.index.astype(int)
    master["entry_ts"] = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True)
    if "exit_ts" in master.columns:
        master["exit_ts"] = pd.to_datetime(master["exit_ts"], errors="coerce", utc=True)
    else:
        master["exit_ts"] = master["entry_ts"]
    master["day_key"] = master["entry_ts"].dt.strftime("%Y-%m-%d")
    candidates_df = _candidate_rows(master)
    artifact_df = _artifact_vs_structure(master, candidates_df)
    tail_df = _positive_tail_persistence(master, candidates_df)
    ranked_df = _relative_ranking(candidates_df, artifact_df, tail_df)
    selected_df = _selected_regimes(ranked_df)
    return master, selected_df.reset_index(drop=True)


def _regime_match_mask(master: pd.DataFrame, regime_row: pd.Series) -> pd.Series:
    mask = pd.Series(True, index=master.index)
    axes = str(regime_row["axes"]).split("|")
    buckets = str(regime_row["buckets"]).split("|")
    for axis, bucket in zip(axes, buckets):
        mask &= master[axis].astype(str).eq(bucket)
    return mask


def _regime_availability(regime_row: pd.Series) -> str:
    axes = str(regime_row["axes"]).split("|")
    availability = "pre_open_allocator"
    for axis in axes:
        availability = TIMING_ORDER[max(TIMING_RANK[availability], TIMING_RANK[AXIS_AVAILABILITY.get(axis, "post_confirmation_allocator")])]
    return availability


def _timing_score_wide(master: pd.DataFrame, selected_df: pd.DataFrame) -> pd.DataFrame:
    wide = master[
        [
            "event_id",
            "trade_id",
            "symbol",
            "entry_ts",
            "exit_ts",
            "day_key",
            "current_split",
            "sector_group",
            "session_timing_bucket",
            "execution_quality_bucket",
            "same_day_candidate_count",
            "same_day_sector_candidate_count",
            "realized_R",
        ]
    ].copy()
    for col in (
        "pre_only_score",
        "opening_only_score",
        "post_only_score",
        "pre_only_artifact_score",
        "opening_only_artifact_score",
        "post_only_artifact_score",
        "pre_only_top_score",
        "opening_only_top_score",
        "post_only_top_score",
    ):
        wide[col] = 0.0

    top_regime_id = str(selected_df.iloc[0]["regime_id"]) if not selected_df.empty else ""
    for _, regime_row in selected_df.iterrows():
        mask = _regime_match_mask(master, regime_row)
        if not mask.any():
            continue
        availability = _regime_availability(regime_row)
        score = float(pd.to_numeric(pd.Series([regime_row["continuation_quality_score"]]), errors="coerce").iloc[0])
        artifact_score = float(
            pd.to_numeric(pd.Series([regime_row.get("artifact_adjusted_weight", 0.0)]), errors="coerce").fillna(0.0).iloc[0]
        )
        score_col = {
            "pre_open_allocator": "pre_only_score",
            "opening_drive_allocator": "opening_only_score",
            "post_confirmation_allocator": "post_only_score",
        }[availability]
        artifact_col = {
            "pre_open_allocator": "pre_only_artifact_score",
            "opening_drive_allocator": "opening_only_artifact_score",
            "post_confirmation_allocator": "post_only_artifact_score",
        }[availability]
        top_col = {
            "pre_open_allocator": "pre_only_top_score",
            "opening_drive_allocator": "opening_only_top_score",
            "post_confirmation_allocator": "post_only_top_score",
        }[availability]
        wide.loc[mask, score_col] += score
        wide.loc[mask, artifact_col] += artifact_score
        if str(regime_row["regime_id"]) == top_regime_id:
            wide.loc[mask, top_col] += score

    wide["pre_open_score"] = wide["pre_only_score"]
    wide["opening_drive_score"] = wide["pre_only_score"] + wide["opening_only_score"]
    wide["post_confirmation_score"] = wide["opening_drive_score"] + wide["post_only_score"]
    wide["pre_open_artifact_score"] = wide["pre_only_artifact_score"]
    wide["opening_drive_artifact_score"] = wide["pre_only_artifact_score"] + wide["opening_only_artifact_score"]
    wide["post_confirmation_artifact_score"] = wide["opening_drive_artifact_score"] + wide["post_only_artifact_score"]
    wide["pre_open_top_regime_score"] = wide["pre_only_top_score"]
    wide["opening_drive_top_regime_score"] = wide["pre_only_top_score"] + wide["opening_only_top_score"]
    wide["post_confirmation_top_regime_score"] = wide["opening_drive_top_regime_score"] + wide["post_only_top_score"]
    return wide.reset_index(drop=True)


def _timing_long_frame(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    timing_map = {
        "pre_open_allocator": (
            "pre_open_available",
            "pre_open_score",
            "pre_open_artifact_score",
            "pre_open_top_regime_score",
        ),
        "opening_drive_allocator": (
            "opening_window_available",
            "opening_drive_score",
            "opening_drive_artifact_score",
            "opening_drive_top_regime_score",
        ),
        "post_confirmation_allocator": (
            "post_breakout_confirmation",
            "post_confirmation_score",
            "post_confirmation_artifact_score",
            "post_confirmation_top_regime_score",
        ),
    }
    for allocator_timing, (availability_group, score_col, artifact_col, top_col) in timing_map.items():
        frame = wide[
            [
                "event_id",
                "trade_id",
                "symbol",
                "entry_ts",
                "exit_ts",
                "day_key",
                "current_split",
                "sector_group",
                "session_timing_bucket",
                "execution_quality_bucket",
                "same_day_candidate_count",
                "same_day_sector_candidate_count",
                "realized_R",
            ]
        ].copy()
        frame["allocator_timing"] = allocator_timing
        frame["feature_availability_group"] = availability_group
        frame["regime_score_at_decision_time"] = pd.to_numeric(wide[score_col], errors="coerce")
        frame["artifact_score_at_decision_time"] = pd.to_numeric(wide[artifact_col], errors="coerce")
        frame["top_regime_score_at_decision_time"] = pd.to_numeric(wide[top_col], errors="coerce")
        frame["eligible_at_decision_time"] = frame["regime_score_at_decision_time"] > 0
        frame["delayed_signal_penalty_flag"] = (
            (allocator_timing == "post_confirmation_allocator")
            & (pd.to_numeric(wide["post_only_score"], errors="coerce") > 0)
        )
        rows.append(frame)
    long_df = pd.concat(rows, ignore_index=True)
    for timing in TIMING_ORDER:
        mask = long_df["allocator_timing"].astype(str).eq(timing) & (pd.to_numeric(long_df["regime_score_at_decision_time"], errors="coerce") > 0)
        long_df.loc[mask, "regime_score_percentile_at_decision_time"] = _percentile_rank(
            long_df.loc[mask, "regime_score_at_decision_time"]
        )
        artifact_mask = long_df["allocator_timing"].astype(str).eq(timing) & (
            pd.to_numeric(long_df["artifact_score_at_decision_time"], errors="coerce") > 0
        )
        long_df.loc[artifact_mask, "artifact_score_percentile_at_decision_time"] = _percentile_rank(
            long_df.loc[artifact_mask, "artifact_score_at_decision_time"]
        )
    long_df["timing_tier"] = np.select(
        [
            pd.to_numeric(long_df["regime_score_percentile_at_decision_time"], errors="coerce") >= 0.8,
            pd.to_numeric(long_df["regime_score_percentile_at_decision_time"], errors="coerce") >= 0.5,
            pd.to_numeric(long_df["regime_score_at_decision_time"], errors="coerce") > 0,
        ],
        ["core", "active", "light"],
        default="skip",
    )
    long_df["artifact_tier"] = np.select(
        [
            pd.to_numeric(long_df["artifact_score_percentile_at_decision_time"], errors="coerce") >= 0.8,
            pd.to_numeric(long_df["artifact_score_percentile_at_decision_time"], errors="coerce") >= 0.5,
            pd.to_numeric(long_df["artifact_score_at_decision_time"], errors="coerce") > 0,
        ],
        ["core", "active", "light"],
        default="skip",
    )
    long_df["single_best_binary"] = pd.to_numeric(long_df["top_regime_score_at_decision_time"], errors="coerce") > 0
    long_df["top_regime_basket_binary"] = pd.to_numeric(long_df["regime_score_at_decision_time"], errors="coerce") > 0
    long_df["regime_conditioned_overlay_balanced"] = long_df["top_regime_basket_binary"]
    long_df["sizing_template_aggressive"] = long_df["top_regime_basket_binary"]
    long_df["artifact_half_plus"] = (
        pd.to_numeric(long_df["artifact_score_percentile_at_decision_time"], errors="coerce") >= 0.5
    ) & (pd.to_numeric(long_df["artifact_score_at_decision_time"], errors="coerce") > 0)
    return long_df.sort_values(["entry_ts", "allocator_timing", "regime_score_at_decision_time"], ascending=[True, True, False]).reset_index(drop=True)


def _base_size_multiplier(alpha_source: str, frame: pd.DataFrame) -> pd.Series:
    if alpha_source == "regime_conditioned_overlay_balanced":
        return frame["timing_tier"].map(SIZING_TEMPLATES["balanced"]).fillna(0.0)
    if alpha_source == "sizing_template_aggressive":
        return frame["timing_tier"].map(SIZING_TEMPLATES["aggressive"]).fillna(0.0)
    return pd.Series(1.0, index=frame.index, dtype=float)


def _allocator_score(frame: pd.DataFrame, allocator_name: str) -> pd.Series:
    regime_score = pd.to_numeric(frame["regime_score_at_decision_time"], errors="coerce").fillna(0.0)
    regime_pct = pd.to_numeric(frame["regime_score_percentile_at_decision_time"], errors="coerce").fillna(0.0)
    artifact_score = pd.to_numeric(frame["artifact_score_at_decision_time"], errors="coerce").fillna(0.0)
    artifact_pct = pd.to_numeric(frame["artifact_score_percentile_at_decision_time"], errors="coerce").fillna(0.0)
    top_score = pd.to_numeric(frame["top_regime_score_at_decision_time"], errors="coerce").fillna(0.0)
    same_day = pd.to_numeric(frame["same_day_candidate_count"], errors="coerce").replace(0, 1).fillna(1.0)
    same_sector = pd.to_numeric(frame["same_day_sector_candidate_count"], errors="coerce").replace(0, 1).fillna(1.0)
    if allocator_name == "regime_priority_allocator":
        return regime_score
    if allocator_name == "convexity_weighted_allocator":
        return regime_score * (1.0 + regime_pct) + (0.25 * top_score) + (0.10 * artifact_score)
    if allocator_name == "structural_balance_allocator":
        return artifact_score * (1.0 + artifact_pct) + (0.20 * regime_pct)
    return (regime_score / same_day) + (0.50 * artifact_score / same_sector) + (0.10 * regime_pct)


def _gross_and_net_metrics(frame: pd.DataFrame, slippage_rate: float, fee_rate: float) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    scoped = frame.copy()
    scoped["scaled_R"] = pd.to_numeric(scoped["realized_R"], errors="coerce") * pd.to_numeric(scoped["size_multiplier"], errors="coerce")
    net_series = pd.to_numeric(_apply_cost_scaled(scoped, slippage_rate, fee_rate), errors="coerce")
    scoped["net_scaled_R"] = net_series
    gross_metrics = _portfolio_metrics(scoped, column="scaled_R")
    net_metrics = _portfolio_metrics(scoped, column="net_scaled_R")
    return scoped, gross_metrics, net_metrics


def _positive_window_share_from_net(frame: pd.DataFrame) -> tuple[float, float]:
    positives = 0
    total = 0
    window_net: list[float] = []
    for window in ROLLING_WINDOWS:
        scoped = frame[
            (frame["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (frame["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        if scoped.empty:
            continue
        total += 1
        net_pnl = float(pd.to_numeric(scoped["net_scaled_R"], errors="coerce").sum())
        window_net.append(net_pnl)
        if net_pnl > 0:
            positives += 1
    return float(positives / max(total, 1)), _f(float(np.mean(window_net))) if window_net else math.nan


def _evaluate_selected_configuration(
    name: str,
    structure_name: str,
    selected: pd.DataFrame,
    eligible_days: int,
    slippage_rate: float = 0.0010,
    fee_rate: float = 0.0005,
    signals_seen: int | None = None,
    avg_rank_of_selected_signal: float | None = None,
    pnl_lost_due_to_competition: float | None = None,
) -> dict[str, Any]:
    if selected.empty:
        return {
            "structure_name": structure_name,
            "allocator_name": name,
            "trade_count": 0,
            "signals_seen": int(signals_seen or 0),
            "signals_selected": 0,
            "selection_rate": 0.0,
            "avg_rank_of_selected_signal": math.nan,
            "expectancy": math.nan,
            "cost_adjusted_expectancy": math.nan,
            "sharpe_proxy": math.nan,
            "mdd_pct": math.nan,
            "capital_utilization": 0.0,
            "concentration": math.nan,
            "gross_pnl_r": 0.0,
            "net_pnl_r": 0.0,
            "gross_return_pct": 0.0,
            "net_return_pct": 0.0,
            "annualized_pnl_proxy": 0.0,
            "pnl_per_trade": math.nan,
            "pnl_per_active_day": math.nan,
            "max_peak_to_trough_pnl_drawdown": 0.0,
            "anchored_oos_net_pnl_r": 0.0,
            "rolling_window_net_pnl_r": math.nan,
            "rolling_oos_robustness": 0.0,
            "anchored_oos_cost_adjusted_expectancy": math.nan,
            "pnl_retention_ratio": math.nan,
            "pnl_lost_due_to_competition": math.nan,
        }
    scoped, gross_metrics, net_metrics = _gross_and_net_metrics(selected, slippage_rate, fee_rate)
    gross_pnl = float(pd.to_numeric(scoped["scaled_R"], errors="coerce").sum())
    net_pnl = float(pd.to_numeric(scoped["net_scaled_R"], errors="coerce").sum())
    active_days = pd.to_datetime(scoped["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique()
    capital_utilization = float(active_days / max(eligible_days, 1))
    anchored = scoped[scoped["current_split"].astype(str) == "anchored_oos"].copy()
    anchored_net = float(pd.to_numeric(anchored["net_scaled_R"], errors="coerce").sum()) if not anchored.empty else 0.0
    anchored_cost_expectancy = float(pd.to_numeric(anchored["net_scaled_R"], errors="coerce").mean()) if not anchored.empty else math.nan
    rolling_share, rolling_window_net = _positive_window_share_from_net(scoped)
    retention = net_pnl / gross_pnl if abs(gross_pnl) > 1e-9 else math.nan
    selection_rate = float(len(scoped) / max(int(signals_seen or len(scoped)), 1))
    return {
        "structure_name": structure_name,
        "allocator_name": name,
        "trade_count": int(len(scoped)),
        "signals_seen": int(signals_seen or len(scoped)),
        "signals_selected": int(len(scoped)),
        "selection_rate": _f(selection_rate),
        "avg_rank_of_selected_signal": _f(float(avg_rank_of_selected_signal)) if avg_rank_of_selected_signal is not None else math.nan,
        "expectancy": gross_metrics["expectancy"],
        "cost_adjusted_expectancy": _f(float(pd.to_numeric(scoped["net_scaled_R"], errors="coerce").mean())),
        "sharpe_proxy": net_metrics["sharpe"],
        "mdd_pct": net_metrics["max_drawdown_pct"],
        "capital_utilization": _f(capital_utilization),
        "concentration": _f(_concentration_share(scoped, "symbol", "scaled_R")) if not scoped.empty else math.nan,
        "gross_pnl_r": _f(gross_pnl),
        "net_pnl_r": _f(net_pnl),
        "gross_return_pct": gross_metrics["return_pct"],
        "net_return_pct": net_metrics["return_pct"],
        "annualized_pnl_proxy": net_metrics["cagr"],
        "pnl_per_trade": _f(net_pnl / max(len(scoped), 1)),
        "pnl_per_active_day": _f(net_pnl / max(active_days, 1)),
        "max_peak_to_trough_pnl_drawdown": net_metrics["max_drawdown_pct"],
        "anchored_oos_net_pnl_r": _f(anchored_net),
        "rolling_window_net_pnl_r": rolling_window_net,
        "rolling_oos_robustness": _f(rolling_share),
        "anchored_oos_cost_adjusted_expectancy": _f(anchored_cost_expectancy) if not math.isnan(anchored_cost_expectancy) else math.nan,
        "pnl_retention_ratio": _f(retention) if not math.isnan(retention) else math.nan,
        "pnl_lost_due_to_competition": _f(float(pnl_lost_due_to_competition)) if pnl_lost_due_to_competition is not None else math.nan,
    }


def _select_with_allocator(
    candidates: pd.DataFrame,
    allocator_name: str,
    structure_name: str,
    capital_fraction: float,
    max_positions: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    eligible = candidates.copy()
    if eligible.empty:
        return eligible.copy(), eligible.copy()
    eligible["allocator_rank_score"] = _allocator_score(eligible, allocator_name)
    eligible = eligible.sort_values(
        ["day_key", "allocator_rank_score", "artifact_score_at_decision_time", "trade_id"],
        ascending=[True, False, False, True],
    ).copy()
    eligible["allocator_rank"] = eligible.groupby("day_key").cumcount() + 1
    selected = eligible[eligible["allocator_rank"] <= max_positions].copy()
    base_mult_all = _base_size_multiplier(structure_name, eligible)
    base_mult_selected = _base_size_multiplier(structure_name, selected)
    eligible["size_multiplier"] = base_mult_all * capital_fraction / max_positions
    selected["size_multiplier"] = base_mult_selected * capital_fraction / max_positions
    return eligible.reset_index(drop=True), selected.reset_index(drop=True)


def _full_participation_baseline(
    eligible: pd.DataFrame,
    structure_name: str,
    capital_fraction: float,
) -> pd.DataFrame:
    baseline = eligible.copy()
    if baseline.empty:
        baseline["size_multiplier"] = 0.0
        return baseline
    counts = baseline.groupby("day_key")["event_id"].transform("count").replace(0, 1)
    baseline["size_multiplier"] = _base_size_multiplier(structure_name, baseline) * capital_fraction / counts
    return baseline


def _allocator_comparison(timing_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    eligible_days = pd.to_datetime(timing_df["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique()
    allocator_rows: list[dict[str, Any]] = []
    competition_rows: list[dict[str, Any]] = []
    selected_frames: list[pd.DataFrame] = []
    for structure_name in ALPHA_SOURCES:
        for allocator_timing in TIMING_ORDER:
            base = timing_df[timing_df["allocator_timing"].astype(str) == allocator_timing].copy()
            if structure_name == "artifact_half_plus":
                base = base[base["artifact_half_plus"].astype(bool)].copy()
            else:
                base = base[base[structure_name].astype(bool)].copy()
            if base.empty:
                continue
            for allocator_name in ALLOCATORS:
                for bucket_name, capital_fraction in CAPITAL_BUCKETS:
                    for max_positions in MAX_POSITIONS:
                        eligible, selected = _select_with_allocator(base, allocator_name, structure_name, capital_fraction, max_positions)
                        baseline = _full_participation_baseline(eligible, structure_name, capital_fraction)
                        baseline_eval = _evaluate_selected_configuration(
                            allocator_name,
                            structure_name,
                            baseline,
                            int(eligible_days),
                        )
                        selected_eval_once = _evaluate_selected_configuration(
                            allocator_name,
                            structure_name,
                            selected,
                            int(eligible_days),
                        )
                        selected_eval = selected_eval_once.copy()
                        selected_eval["signals_seen"] = int(len(eligible))
                        selected_eval["selection_rate"] = _f(float(len(selected) / max(len(eligible), 1)))
                        selected_eval["avg_rank_of_selected_signal"] = (
                            _f(float(pd.to_numeric(selected["allocator_rank"], errors="coerce").mean())) if not selected.empty else math.nan
                        )
                        selected_eval["pnl_lost_due_to_competition"] = _f(
                            max(0.0, float(baseline_eval["net_pnl_r"]) - float(selected_eval_once["net_pnl_r"]))
                        )
                        selected_eval.update(
                            {
                                "allocator_timing": allocator_timing,
                                "capital_bucket": bucket_name,
                                "capital_fraction": capital_fraction,
                                "max_positions": max_positions,
                            }
                        )
                        allocator_rows.append(selected_eval)
                        competition_rows.append(
                            {
                                "structure_name": structure_name,
                                "allocator_name": allocator_name,
                                "allocator_timing": allocator_timing,
                                "capital_bucket": bucket_name,
                                "capital_fraction": capital_fraction,
                                "max_positions": max_positions,
                                "signals_seen": int(len(eligible)),
                                "signals_selected": int(len(selected)),
                                "selection_rate": _f(float(len(selected) / max(len(eligible), 1))),
                                "avg_rank_of_selected_signal": _f(float(pd.to_numeric(selected["allocator_rank"], errors="coerce").mean())) if not selected.empty else math.nan,
                                "gross_pnl_r": selected_eval["gross_pnl_r"],
                                "net_pnl_r": selected_eval["net_pnl_r"],
                                "pnl_lost_due_to_competition": _f(max(0.0, float(baseline_eval["net_pnl_r"]) - float(selected_eval["net_pnl_r"]))),
                                "rolling_oos_robustness": selected_eval["rolling_oos_robustness"],
                                "anchored_oos_net_pnl_r": selected_eval["anchored_oos_net_pnl_r"],
                            }
                        )
                        if not selected.empty:
                            selected_copy = selected.copy()
                            selected_copy["structure_name"] = structure_name
                            selected_copy["allocator_name"] = allocator_name
                            selected_copy["allocator_timing"] = allocator_timing
                            selected_copy["capital_bucket"] = bucket_name
                            selected_copy["capital_fraction"] = capital_fraction
                            selected_copy["max_positions"] = max_positions
                            selected_frames.append(selected_copy)
    allocator_df = pd.DataFrame(allocator_rows).sort_values(
        ["net_pnl_r", "pnl_retention_ratio", "rolling_oos_robustness"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    competition_df = pd.DataFrame(competition_rows).sort_values(
        ["net_pnl_r", "selection_rate"], ascending=[False, False]
    ).reset_index(drop=True)
    selected_frame_df = pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame()
    return allocator_df, competition_df, selected_frame_df


def _stress_adjusted_frame(frame: pd.DataFrame, scenario: str) -> tuple[pd.DataFrame, float, float]:
    scoped = frame.copy()
    scoped["stress_realized_R"] = pd.to_numeric(scoped["realized_R"], errors="coerce")
    slippage_rate = 0.0010
    fee_rate = 0.0005
    if scenario == "higher_slippage":
        slippage_rate = 0.0020
        fee_rate = 0.0010
    elif scenario == "opening_penalty":
        opening_penalty = np.where(
            scoped["session_timing_bucket"].astype(str).eq("first_30m")
            | scoped["allocator_timing"].astype(str).eq("opening_drive_allocator"),
            0.10,
            0.0,
        )
        scoped["stress_realized_R"] = scoped["stress_realized_R"] - opening_penalty
    elif scenario == "confirmation_delay_penalty":
        delay_penalty = np.where(scoped["delayed_signal_penalty_flag"].astype(bool), 0.15, 0.0)
        scoped["stress_realized_R"] = scoped["stress_realized_R"] - delay_penalty
    elif scenario == "combined_stress":
        slippage_rate = 0.0020
        fee_rate = 0.0010
        opening_penalty = np.where(
            scoped["session_timing_bucket"].astype(str).eq("first_30m")
            | scoped["allocator_timing"].astype(str).eq("opening_drive_allocator"),
            0.10,
            0.0,
        )
        delay_penalty = np.where(scoped["delayed_signal_penalty_flag"].astype(bool), 0.15, 0.0)
        scoped["stress_realized_R"] = scoped["stress_realized_R"] - opening_penalty - delay_penalty
    scoped["realized_R"] = scoped["stress_realized_R"]
    return scoped, slippage_rate, fee_rate


def _execution_realism_stress(best_config_frame: pd.DataFrame, eligible_days: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if best_config_frame.empty:
        return pd.DataFrame(columns=["stress_scenario"])
    base_eval = _evaluate_selected_configuration("best_config", str(best_config_frame["structure_name"].iloc[0]), best_config_frame, eligible_days)
    base_net = float(base_eval["net_pnl_r"])
    for scenario in STRESS_SCENARIOS:
        stressed_frame, slip, fee = _stress_adjusted_frame(best_config_frame, scenario)
        eval_row = _evaluate_selected_configuration("best_config", str(best_config_frame["structure_name"].iloc[0]), stressed_frame, eligible_days, slip, fee)
        eval_row["stress_scenario"] = scenario
        eval_row["raw_net_pnl_r"] = _f(base_net)
        eval_row["stress_group"] = "execution_realism"
        eval_row["slippage_adjusted_expectancy"] = eval_row["cost_adjusted_expectancy"]
        eval_row["expected_live_slippage"] = (
            "contained"
            if eval_row["cost_adjusted_expectancy"] > 0.50
            else "manageable"
            if eval_row["cost_adjusted_expectancy"] > 0.20
            else "elevated"
        )
        eval_row["execution_fragility"] = (
            "low"
            if float(eval_row["pnl_retention_ratio"]) >= 0.75
            else "medium"
            if float(eval_row["pnl_retention_ratio"]) >= 0.50
            else "high"
        )
        eval_row["stress_pass"] = bool(float(eval_row["net_pnl_r"]) > 0 and float(eval_row["pnl_retention_ratio"]) >= 0.50)
        rows.append(eval_row)
    return pd.DataFrame(rows).sort_values(["stress_scenario"]).reset_index(drop=True)


def _apply_netting(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    scoped = frame.copy()
    if mode == "allow_duplicate_exposure":
        return scoped
    sort_cols = ["day_key", "allocator_rank_score", "artifact_score_at_decision_time", "trade_id"]
    scoped = scoped.sort_values(sort_cols, ascending=[True, False, False, True]).copy()
    if mode == "symbol_netting":
        return scoped.drop_duplicates(subset=["day_key", "symbol"], keep="first").reset_index(drop=True)
    return scoped.drop_duplicates(subset=["day_key", "sector_group"], keep="first").reset_index(drop=True)


def _sleeve_overlap_netting(best_config_frame: pd.DataFrame, eligible_days: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if best_config_frame.empty:
        return pd.DataFrame(columns=["netting_mode"])
    baseline_eval = _evaluate_selected_configuration("best_config", str(best_config_frame["structure_name"].iloc[0]), best_config_frame, eligible_days)
    raw_net = float(baseline_eval["net_pnl_r"])
    raw_drawdown = float(baseline_eval["max_peak_to_trough_pnl_drawdown"])
    raw_concentration = float(baseline_eval["concentration"])
    for mode in NETTING_MODES:
        netted = _apply_netting(best_config_frame, mode)
        eval_row = _evaluate_selected_configuration("best_config", str(best_config_frame["structure_name"].iloc[0]), netted, eligible_days)
        rows.append(
            {
                "netting_mode": mode,
                "trade_count": eval_row["trade_count"],
                "raw_net_pnl_r": _f(raw_net),
                "netted_net_pnl_r": eval_row["net_pnl_r"],
                "net_pnl_delta": _f(float(eval_row["net_pnl_r"]) - raw_net),
                "drawdown_delta": _f(float(eval_row["max_peak_to_trough_pnl_drawdown"]) - raw_drawdown),
                "concentration_delta": _f(float(eval_row["concentration"]) - raw_concentration),
                "pnl_retention_ratio": _f(float(eval_row["net_pnl_r"]) / raw_net) if abs(raw_net) > 1e-9 else math.nan,
                "rolling_oos_robustness": eval_row["rolling_oos_robustness"],
                "anchored_oos_net_pnl_r": eval_row["anchored_oos_net_pnl_r"],
            }
        )
    return pd.DataFrame(rows).sort_values(["netting_mode"]).reset_index(drop=True)


def _shadow_pilot_readiness(
    best_row: pd.Series,
    stress_df: pd.DataFrame,
    netting_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    best_net = float(pd.to_numeric(pd.Series([best_row["net_pnl_r"]]), errors="coerce").iloc[0])
    anchored_net = float(pd.to_numeric(pd.Series([best_row["anchored_oos_net_pnl_r"]]), errors="coerce").iloc[0])
    rolling_share = float(pd.to_numeric(pd.Series([best_row["rolling_oos_robustness"]]), errors="coerce").iloc[0])
    combined = stress_df[stress_df["stress_scenario"].astype(str) == "combined_stress"]
    combined_retention = float(pd.to_numeric(combined["pnl_retention_ratio"], errors="coerce").iloc[0]) if not combined.empty else math.nan
    symbol_net = netting_df[netting_df["netting_mode"].astype(str) == "symbol_netting"]
    symbol_retention = float(pd.to_numeric(symbol_net["pnl_retention_ratio"], errors="coerce").iloc[0]) if not symbol_net.empty else math.nan
    gates = [
        ("net_pnl_positive", best_net > 0, best_net, "> 0"),
        ("anchored_oos_net_pnl_positive", anchored_net > 0, anchored_net, "> 0"),
        ("rolling_pnl_persistence", rolling_share >= 0.75, rolling_share, ">= 0.75"),
        ("combined_stress_retention", (not math.isnan(combined_retention)) and combined_retention >= 0.50, combined_retention, ">= 0.50"),
        ("symbol_netting_retention", (not math.isnan(symbol_retention)) and symbol_retention >= 0.70, symbol_retention, ">= 0.70"),
    ]
    for gate_name, status, evidence, threshold in gates:
        rows.append(
            {
                "gate_name": gate_name,
                "status": bool(status),
                "evidence_value": _f(float(evidence)) if evidence is not None and not math.isnan(float(evidence)) else math.nan,
                "threshold": threshold,
            }
        )
    shadow_ready = all(bool(row["status"]) for row in rows[:3])
    tiny_capital_ready = shadow_ready and all(bool(row["status"]) for row in rows)
    rows.append({"gate_name": "shadow_monitor_ready", "status": shadow_ready, "evidence_value": math.nan, "threshold": "all core gates"})
    rows.append({"gate_name": "tiny_capital_pilot_ready", "status": tiny_capital_ready, "evidence_value": math.nan, "threshold": "all gates"})
    return pd.DataFrame(rows)


def _final_decision(
    allocator_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    netting_df: pd.DataFrame,
    readiness_df: pd.DataFrame,
) -> pd.DataFrame:
    best_row = allocator_df.iloc[0] if not allocator_df.empty else pd.Series(dtype=object)
    combined = stress_df[stress_df["stress_scenario"].astype(str) == "combined_stress"]
    combined_retention = float(pd.to_numeric(combined["pnl_retention_ratio"], errors="coerce").iloc[0]) if not combined.empty else math.nan
    allow_row = netting_df[netting_df["netting_mode"].astype(str) == "allow_duplicate_exposure"]
    net_row = netting_df[netting_df["netting_mode"].astype(str) == "symbol_netting"]
    overlap_retention = float(pd.to_numeric(net_row["pnl_retention_ratio"], errors="coerce").iloc[0]) if not net_row.empty else math.nan
    shadow_ready = bool(readiness_df[readiness_df["gate_name"].astype(str) == "shadow_monitor_ready"]["status"].iloc[0]) if (readiness_df["gate_name"].astype(str) == "shadow_monitor_ready").any() else False
    tiny_ready = bool(readiness_df[readiness_df["gate_name"].astype(str) == "tiny_capital_pilot_ready"]["status"].iloc[0]) if (readiness_df["gate_name"].astype(str) == "tiny_capital_pilot_ready").any() else False
    best_net = float(pd.to_numeric(pd.Series([best_row.get("net_pnl_r", math.nan)]), errors="coerce").iloc[0])
    anchored_net = float(pd.to_numeric(pd.Series([best_row.get("anchored_oos_net_pnl_r", math.nan)]), errors="coerce").iloc[0])
    rolling_share = float(pd.to_numeric(pd.Series([best_row.get("rolling_oos_robustness", 0.0)]), errors="coerce").iloc[0])

    if math.isnan(best_net) or best_net <= 0 or anchored_net <= 0:
        decision = "RESEARCH_ONLY"
        reason = "Best allocator does not retain positive post-cost PnL through anchored OOS."
    elif tiny_ready and rolling_share >= 0.75 and (not math.isnan(combined_retention)) and combined_retention >= 0.75 and (not math.isnan(overlap_retention)) and overlap_retention >= 0.80:
        decision = "TACTICAL_DEPLOYMENT_READY"
        reason = "Allocator, stress, and overlap checks all retain strong PnL, supporting tactical deployment."
    elif tiny_ready:
        decision = "TINY_CAPITAL_PILOT_READY"
        reason = "Best configuration retains enough post-cost PnL and robustness to justify a tiny-capital pilot."
    elif shadow_ready:
        decision = "SHADOW_READY"
        reason = "Sleeve remains positive with acceptable OOS behavior, but stress and overlap retention still cap live capital."
    else:
        decision = "RESEARCH_ONLY"
        reason = "Deployment realism weakens PnL enough that more validation is still required."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_structure": best_row.get("structure_name", ""),
                "best_allocator": best_row.get("allocator_name", ""),
                "best_allocator_timing": best_row.get("allocator_timing", ""),
                "best_capital_bucket": best_row.get("capital_bucket", ""),
                "best_max_positions": best_row.get("max_positions", math.nan),
                "best_net_pnl_r": best_net,
                "best_anchored_oos_net_pnl_r": anchored_net,
                "best_rolling_oos_robustness": rolling_share,
                "combined_stress_retention": _f(combined_retention) if not math.isnan(combined_retention) else math.nan,
                "symbol_netting_retention": _f(overlap_retention) if not math.isnan(overlap_retention) else math.nan,
                "shadow_monitor_ready": shadow_ready,
                "tiny_capital_pilot_ready": tiny_ready,
            }
        ]
    )


def _report(
    out_dir: Path,
    live_df: pd.DataFrame,
    allocator_df: pd.DataFrame,
    competition_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    netting_df: pd.DataFrame,
    readiness_df: pd.DataFrame,
    final_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    lines = [
        "# Task 354 - Regime Sleeve Deployment Realism",
        "",
        f"- decision: {final_row['decision']}",
        f"- best_structure: {final_row['best_structure']}",
        f"- best_allocator: {final_row['best_allocator']}",
        f"- best_allocator_timing: {final_row['best_allocator_timing']}",
        f"- best_net_pnl_r: {final_row['best_net_pnl_r']}",
        "",
        "## Final Interpretation",
        "1. This task evaluates deployment realism, not new alpha discovery.",
        f"2. Best allocator structure: `{final_row['best_structure']} / {final_row['best_allocator']}`",
        f"3. Final decision: `{final_row['decision']}`",
        f"4. Tiny-capital pilot ready: `{bool(final_row['tiny_capital_pilot_ready'])}`",
        "",
        "## Allocator Comparison",
        *(_markdown_table(allocator_df.head(12))),
        "",
        "## Concurrent Signal Competition",
        *(_markdown_table(competition_df.head(12))),
        "",
        "## Execution Realism Stress",
        *(_markdown_table(stress_df)),
        "",
        "## Overlap Netting",
        *(_markdown_table(netting_df)),
        "",
        "## Shadow / Pilot Readiness",
        *(_markdown_table(readiness_df)),
        "",
        "## Live Timing Reconstruction Sample",
        *(_markdown_table(live_df.head(12))),
    ]
    (out_dir / "task_354_regime_sleeve_deployment.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 354: regime sleeve deployment realism, capital allocation, and PnL reporting")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    master, selected_df = _prepare_task354_context()
    wide_df = _timing_score_wide(master, selected_df)
    live_df = _timing_long_frame(wide_df)
    allocator_df, competition_df, selected_frames_df = _allocator_comparison(live_df)

    if not allocator_df.empty and not selected_frames_df.empty:
        best = allocator_df.iloc[0]
        best_mask = (
            selected_frames_df["structure_name"].astype(str).eq(str(best["structure_name"]))
            & selected_frames_df["allocator_name"].astype(str).eq(str(best["allocator_name"]))
            & selected_frames_df["allocator_timing"].astype(str).eq(str(best["allocator_timing"]))
            & selected_frames_df["capital_bucket"].astype(str).eq(str(best["capital_bucket"]))
            & (pd.to_numeric(selected_frames_df["max_positions"], errors="coerce") == pd.to_numeric(pd.Series([best["max_positions"]]), errors="coerce").iloc[0])
        )
        best_frame = selected_frames_df[best_mask].copy()
    else:
        best_frame = pd.DataFrame()
    eligible_days = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique()
    stress_df = _execution_realism_stress(best_frame, int(eligible_days))
    netting_df = _sleeve_overlap_netting(best_frame, int(eligible_days))
    readiness_df = _shadow_pilot_readiness(allocator_df.iloc[0] if not allocator_df.empty else pd.Series(dtype=object), stress_df, netting_df)
    final_df = _final_decision(allocator_df, stress_df, netting_df, readiness_df)

    live_df.to_csv(out_dir / "task_354_live_decision_reconstruction.csv", index=False)
    allocator_df.to_csv(out_dir / "task_354_capital_allocator_comparison.csv", index=False)
    competition_df.to_csv(out_dir / "task_354_concurrent_signal_competition.csv", index=False)
    stress_df.to_csv(out_dir / "task_354_execution_realism_stress.csv", index=False)
    netting_df.to_csv(out_dir / "task_354_sleeve_overlap_netting.csv", index=False)
    readiness_df.to_csv(out_dir / "task_354_shadow_pilot_readiness.csv", index=False)
    final_df.to_csv(out_dir / "task_354_final_decision.csv", index=False)
    _report(out_dir, live_df, allocator_df, competition_df, stress_df, netting_df, readiness_df, final_df)


if __name__ == "__main__":
    main()
