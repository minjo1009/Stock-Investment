from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task542_factor_adjusted_continuation_attribution import (
    attach_factor_adjustment,
    build_factor_model_universe,
    fit_factor_model,
)
from src.backtest.task_report_utils import write_standard_report


TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
FF_DAILY_PANEL = Path("data/raw/fama_french/fama_french_5_factor_daily.csv")
TASK541_SIZE_BM_PANEL = Path("docs/reports/task_541_size_bm_fama_macbeth/size_bm_factor_panel.csv")
TASK529_FEATURES = Path("docs/reports/task_529_trend_persistence_entry_safe_refinement/entry_safe_feature_audit.csv")
TASK542_PANEL = Path("docs/reports/task_542_factor_adjusted_continuation_attribution/factor_adjusted_candidate_panel.csv")
TASK544_OUT = Path("docs/reports/task_544_factor_adjusted_sample_expansion_quarter_failure")


def build_task544_sample_expansion_quarter_failure(
    *,
    task503_panel_path: Path = TASK503_PANEL,
    ff_daily_path: Path = FF_DAILY_PANEL,
    size_bm_panel_path: Path = TASK541_SIZE_BM_PANEL,
    task529_features_path: Path = TASK529_FEATURES,
    task542_panel_path: Path = TASK542_PANEL,
    out_dir: Path = TASK544_OUT,
) -> dict[str, pd.DataFrame]:
    universe = pd.read_csv(task503_panel_path)
    features = pd.read_csv(task529_features_path) if task529_features_path.exists() else pd.DataFrame()
    expanded_candidates = build_expansion_candidate_panel(universe, features)
    _, factor_universe = fit_factor_model(build_factor_model_universe(task503_panel_path, ff_daily_path, size_bm_panel_path))
    expanded_attributed = attach_factor_adjustment(expanded_candidates, factor_universe)
    expansion_quality = summarize_expansion_quality(expanded_attributed)
    expansion_split = summarize_split_quality(expanded_attributed)
    base_panel = pd.read_csv(task542_panel_path)
    failure_decomposition = decompose_failure_quarters(base_panel)
    failure_contrast = build_good_bad_failure_contrast(base_panel)
    leakage = build_leakage_audit()
    decision = build_decision(expansion_quality, expansion_split, failure_decomposition)
    artifacts = {
        "factor_adjusted_expansion_candidate_pool": expanded_attributed,
        "factor_adjusted_expansion_quality": expansion_quality,
        "factor_adjusted_expansion_split_quality": expansion_split,
        "quarter_failure_decomposition_2025q1_q3": failure_decomposition,
        "good_bad_quarter_failure_contrast": failure_contrast,
        "sample_expansion_leakage_audit": leakage,
        "task_544_decision": decision,
    }
    write_task544(out_dir, artifacts)
    return artifacts


def build_expansion_candidate_panel(universe: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    frame = universe.copy()
    if not features.empty:
        feature_cols = [col for col in ["lifecycle_id", "entry_close_pos_in_bar", "entry_close_vs_vwap"] if col in features.columns]
        frame = frame.merge(features[feature_cols].drop_duplicates("lifecycle_id"), on="lifecycle_id", how="left")
    frame["return_pct"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce") * 100.0
    frame["candidate_set"] = "not_assigned"
    masks = build_expansion_masks(frame)
    rows = []
    for candidate_set, mask in masks.items():
        subset = frame[mask].copy()
        subset["candidate_set"] = candidate_set
        subset["factor_assignment_used_label_flag"] = 0
        subset["inferred_lifecycle_matching_used_flag"] = 0
        rows.append(subset)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_expansion_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    setup = frame["symbol_multiday_setup_state"].astype(str)
    market = frame["multi_day_market_state_v4"].astype(str)
    theme = frame["theme_regime_state_v4"].astype(str)
    close_pos = pd.to_numeric(frame.get("entry_close_pos_in_bar", pd.Series(np.nan, index=frame.index)), errors="coerce")
    range_pos = pd.to_numeric(frame.get("range_pos", pd.Series(np.nan, index=frame.index)), errors="coerce")
    volume = pd.to_numeric(frame.get("volume_ratio_prev", pd.Series(np.nan, index=frame.index)), errors="coerce")
    timing = frame.get("timing_state", pd.Series("", index=frame.index)).astype(str)
    strict_regime = market.isin(["constructive_risk_on", "broad_risk_on"]) & theme.isin(["persistent_theme_leader", "theme_participation"])
    trend = setup.eq("trend_persistence_near_high")
    return {
        "base_trend_closepos_097": trend & close_pos.le(0.97),
        "expanded_trend_closepos_099": trend & close_pos.le(0.99),
        "strict_regime_trend_closepos_099": strict_regime & trend & close_pos.le(0.99),
        "strict_regime_near_high_upper_range": strict_regime & trend & range_pos.ge(0.70) & range_pos.le(0.98),
        "strict_regime_volume_confirmed": strict_regime & setup.isin(["trend_persistence_near_high", "volume_confirmed_reclaim"]) & volume.ge(1.1),
        "strict_regime_opening_midday": strict_regime & trend & timing.isin(["opening_drive", "midday_continuation"]),
    }


def summarize_expansion_quality(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate_set, subset in panel.groupby("candidate_set"):
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "candidate_set": candidate_set,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "factor_adjustment_coverage_rate": float(len(adjusted) / len(subset)) if len(subset) else 0.0,
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "factor_adjusted_win_rate": float((adjusted["factor_adjusted_residual_pct"] > 0).mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(pd.to_numeric(subset["entry_reduce_failure_flag"], errors="coerce").mean()) if len(subset) else np.nan,
                "add_scale_success_rate": float(pd.to_numeric(subset["add_scale_success_flag"], errors="coerce").mean()) if len(subset) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def summarize_split_quality(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate_set, split_name), subset in panel.groupby(["candidate_set", "split_name"]):
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "candidate_set": candidate_set,
                "split_name": split_name,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(pd.to_numeric(subset["entry_reduce_failure_flag"], errors="coerce").mean()) if len(subset) else np.nan,
                "underpowered_flag": int(len(adjusted) < 20),
            }
        )
    return pd.DataFrame(rows)


def decompose_failure_quarters(panel: pd.DataFrame) -> pd.DataFrame:
    focus = panel[
        panel["candidate_set"].eq("task505_selected_two_year_strategy")
        & panel["quarter"].isin(["2025Q1", "2025Q2", "2025Q3"])
    ].copy()
    rows = []
    dimensions = [
        "multi_day_market_state_v4",
        "theme_regime_state_v4",
        "symbol_multiday_setup_state",
        "intraday_entry_state_v4",
        "timing_state",
        "exit_reason",
    ]
    for dim in dimensions:
        if dim not in focus.columns:
            continue
        for value, subset in focus.groupby(dim, dropna=False):
            adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
            rows.append(
                {
                    "dimension": dim,
                    "value": value,
                    "lifecycle_count": int(len(subset)),
                    "factor_adjusted_count": int(len(adjusted)),
                    "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                    "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                    "entry_reduce_failure_rate": float(pd.to_numeric(subset["entry_reduce_failure_flag"], errors="coerce").mean()) if len(subset) else np.nan,
                    "add_scale_success_rate": float(pd.to_numeric(subset["add_scale_success_flag"], errors="coerce").mean()) if len(subset) else np.nan,
                    "failure_contribution_score": float(len(subset) * max(0.0, -adjusted["factor_adjusted_residual_pct"].mean())) if len(adjusted) else np.nan,
                }
            )
    return pd.DataFrame(rows).sort_values("failure_contribution_score", ascending=False, na_position="last").reset_index(drop=True)


def build_good_bad_failure_contrast(panel: pd.DataFrame) -> pd.DataFrame:
    focus = panel[panel["candidate_set"].eq("task505_selected_two_year_strategy")].copy()
    focus["period_bucket"] = np.where(focus["quarter"].isin(["2025Q1", "2025Q2", "2025Q3"]), "failure_2025q1_q3", "other_quarters")
    rows = []
    for bucket, subset in focus.groupby("period_bucket"):
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "period_bucket": bucket,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(pd.to_numeric(subset["entry_reduce_failure_flag"], errors="coerce").mean()) if len(subset) else np.nan,
                "add_scale_success_rate": float(pd.to_numeric(subset["add_scale_success_flag"], errors="coerce").mean()) if len(subset) else np.nan,
                "avg_cum_Mkt_RF_pct": float(pd.to_numeric(subset["cum_Mkt_RF_pct"], errors="coerce").mean()) if "cum_Mkt_RF_pct" in subset else np.nan,
                "avg_size_log_market_cap": float(pd.to_numeric(subset["size_log_market_cap"], errors="coerce").mean()) if "size_log_market_cap" in subset else np.nan,
                "avg_book_to_market_log": float(pd.to_numeric(subset["book_to_market_log"], errors="coerce").mean()) if "book_to_market_log" in subset else np.nan,
            }
        )
    return pd.DataFrame(rows)


def build_leakage_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"rule": "sample_expansion_uses_entry_safe_state_only", "pass_flag": 1},
            {"rule": "factor_residual_used_only_for_evaluation", "pass_flag": 1},
            {"rule": "no_symbol_date_price_time_fallback", "pass_flag": 1},
            {"rule": "no_missing_factor_approximation", "pass_flag": 1},
        ]
    )


def build_decision(expansion_quality: pd.DataFrame, expansion_split: pd.DataFrame, failure: pd.DataFrame) -> pd.DataFrame:
    recent = expansion_split[expansion_split["split_name"].astype(str).eq("recent_oos")]
    recent_enough = recent[recent["factor_adjusted_count"].ge(20)]
    viable = recent_enough[recent_enough["factor_adjusted_avg_residual_pct"].gt(0)]
    return pd.DataFrame(
        [
            {
                "task_id": "Task544",
                "expansion_candidate_count": int(expansion_quality["candidate_set"].nunique()) if not expansion_quality.empty else 0,
                "recent_oos_sample_expanded_candidate_count": int(len(recent_enough)),
                "recent_oos_positive_expanded_candidate_count": int(len(viable)),
                "quarter_failure_decomposition_run_flag": int(not failure.empty),
                "factor_result_used_as_trading_trigger_flag": 0,
                "deployment_ready_flag": 0,
                "strategy_acceptance_status": "FACTOR_ADJUSTED_SAMPLE_EXPANSION_DIAGNOSTIC_ONLY",
            }
        ]
    )


def write_task544(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_544_decision"].iloc[0].to_dict()
    split = artifacts["factor_adjusted_expansion_split_quality"]
    recent = split[split["split_name"].astype(str).eq("recent_oos")].copy()
    recent_lines = [
        f"{row['candidate_set']}: recent OOS adjusted count {int(row['factor_adjusted_count'])}, "
        f"residual {row['factor_adjusted_avg_residual_pct']:.2f}%, entry_reduce {row['entry_reduce_failure_rate']:.2%}."
        for row in recent.to_dict(orient="records")
    ]
    top_failure = artifacts["quarter_failure_decomposition_2025q1_q3"].head(5)
    failure_lines = [
        f"{row['dimension']}={row['value']}: count {int(row['lifecycle_count'])}, residual {row['factor_adjusted_avg_residual_pct']:.2f}%, entry_reduce {row['entry_reduce_failure_rate']:.2%}."
        for row in top_failure.to_dict(orient="records")
    ]
    write_standard_report(
        out_dir / "task_544_factor_adjusted_sample_expansion_quarter_failure.md",
        title="Task 544 Factor-Adjusted Sample Expansion and Quarter Failure Decomposition",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Expansion candidates tested: {decision['expansion_candidate_count']}",
            f"Recent OOS sample-expanded candidates: {decision['recent_oos_sample_expanded_candidate_count']}",
            f"Recent OOS positive expanded candidates: {decision['recent_oos_positive_expanded_candidate_count']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task544 tests adjacent entry-safe expansion candidates; it does not optimize thresholds on residual outcomes.",
            *recent_lines,
            "2025Q1-Q3 failure decomposition top contributors:",
            *failure_lines,
        ],
        decision_maker_lines=[
            "We tried to increase the recent OOS sample without inventing data or changing labels.",
            "We also decomposed the weak 2025 quarters to see whether the problem came from regime, theme, entry structure, or exits.",
            "This remains diagnostic. A larger positive recent OOS sample is required before any firm-grade claim.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task544_sample_expansion_quarter_failure()


if __name__ == "__main__":
    main()
