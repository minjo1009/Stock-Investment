from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_anchored_oos_failure_uplift_355 import (
    BASE_ALLOCATOR,
    BASE_CAPITAL_FRACTION,
    BASE_MAX_POSITIONS,
    BASE_STRUCTURE,
    _base_candidate_pool,
    _best_baseline_frame,
    _build_task355_context,
    _candidate_from_config,
)
from src.backtest.analysis_structural_breakout_regime_sleeve_deployment_354 import (
    _evaluate_selected_configuration,
    _execution_realism_stress,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_356_event_shock_regime_audit")
CURRENT_EPISODE = "current_failure_window"
EPISODES = (
    {
        "episode_name": "russia_invasion_shock",
        "family": "war_shock",
        "start": "2022-02-24",
        "end": "2022-04-30",
        "anchor_date": "2022-02-24",
    },
    {
        "episode_name": "banking_stress_shock",
        "family": "financial_stress",
        "start": "2023-03-08",
        "end": "2023-04-14",
        "anchor_date": "2023-03-10",
    },
    {
        "episode_name": "macro_rate_shock",
        "family": "macro_rate_shock",
        "start": "2022-06-10",
        "end": "2022-07-31",
        "anchor_date": "2022-06-13",
    },
    {
        "episode_name": "post_risk_off_rebound_shock",
        "family": "post_risk_off_rebound",
        "start": "2022-10-13",
        "end": "2022-11-30",
        "anchor_date": "2022-10-13",
    },
    {
        "episode_name": CURRENT_EPISODE,
        "family": "current_failure",
        "start": "2025-12-01",
        "end": "2026-01-31",
        "anchor_date": "2025-12-01",
    },
)
NUMERIC_SIMILARITY_COLUMNS = (
    "dispersion_20d",
    "mean_pairwise_corr",
    "same_day_candidate_count",
    "same_day_sector_candidate_count",
)
CATEGORICAL_SIMILARITY_COLUMNS = (
    "gap_environment_state",
    "market_breadth_state",
    "sector_leadership_state",
)


def _safe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _eligible_days(frame: pd.DataFrame) -> int:
    days = pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna()
    return int(days.nunique())


def _episode_mask(frame: pd.DataFrame, start: str, end: str) -> pd.Series:
    entry_ts = pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True)
    return (entry_ts >= pd.Timestamp(start, tz="UTC")) & (entry_ts <= pd.Timestamp(end, tz="UTC"))


def _shock_mask(frame: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=frame.index)
    for episode in EPISODES:
        if episode["episode_name"] == CURRENT_EPISODE or episode["episode_name"] == "russia_invasion_shock" or episode["episode_name"] == "banking_stress_shock" or episode["episode_name"] == "macro_rate_shock" or episode["episode_name"] == "post_risk_off_rebound_shock":
            mask |= _episode_mask(frame, episode["start"], episode["end"])
    return mask


def _execution_bucket_mix(scoped: pd.DataFrame) -> str:
    if scoped.empty or "execution_quality_bucket" not in scoped.columns:
        return ""
    mix = scoped["execution_quality_bucket"].astype(str).value_counts(normalize=True).head(3)
    return ";".join(f"{idx}:{round(val, 3)}" for idx, val in mix.items())


def _sector_mix(scoped: pd.DataFrame) -> str:
    if scoped.empty or "sector_group" not in scoped.columns:
        return ""
    mix = scoped["sector_group"].astype(str).value_counts(normalize=True).head(3)
    return ";".join(f"{idx}:{round(val, 3)}" for idx, val in mix.items())


def _combined_stress_retention(frame: pd.DataFrame, eligible_days: int) -> float:
    if frame.empty:
        return math.nan
    stress_df = _execution_realism_stress(frame, eligible_days)
    combined = stress_df[stress_df["stress_scenario"].astype(str) == "combined_stress"]
    if combined.empty:
        return math.nan
    return float(pd.to_numeric(combined["pnl_retention_ratio"], errors="coerce").iloc[0])


def _episode_summary(
    episode: dict[str, str],
    base_pool: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    opening_frame: pd.DataFrame,
) -> dict[str, Any]:
    mask_pool = _episode_mask(base_pool, episode["start"], episode["end"])
    mask_post = _episode_mask(baseline_frame, episode["start"], episode["end"])
    mask_open = _episode_mask(opening_frame, episode["start"], episode["end"])
    pool = base_pool[mask_pool].copy()
    post_selected = baseline_frame[mask_post].copy()
    opening_selected = opening_frame[mask_open].copy()
    eligible_days = max(_eligible_days(pool), 1)
    post_eval = _evaluate_selected_configuration("baseline_deployment", BASE_STRUCTURE, post_selected, eligible_days)
    opening_eval = _evaluate_selected_configuration("shock_timing_downgrade", BASE_STRUCTURE, opening_selected, eligible_days)
    return {
        "episode_name": episode["episode_name"],
        "family": episode["family"],
        "start_date": episode["start"],
        "end_date": episode["end"],
        "pool_trade_count": int(len(pool)),
        "selected_trade_count": int(len(post_selected)),
        "selected_net_pnl_r": post_eval["net_pnl_r"],
        "selected_expectancy": post_eval["expectancy"],
        "selected_cost_adjusted_expectancy": post_eval["cost_adjusted_expectancy"],
        "selected_pnl_retention_ratio": post_eval["pnl_retention_ratio"],
        "selected_gross_pnl_r": post_eval["gross_pnl_r"],
        "opening_drive_net_pnl_r": opening_eval["net_pnl_r"],
        "post_confirmation_net_pnl_r": post_eval["net_pnl_r"],
        "timing_sensitivity_open_minus_post": round(float(opening_eval["net_pnl_r"]) - float(post_eval["net_pnl_r"]), 6),
        "avg_same_day_candidate_count": round(float(_safe_numeric(pool, "same_day_candidate_count").mean()), 6),
        "avg_same_day_sector_candidate_count": round(float(_safe_numeric(pool, "same_day_sector_candidate_count").mean()), 6),
        "first_30m_share": round(float(pool["session_timing_bucket"].astype(str).eq("first_30m").mean()), 6) if not pool.empty else math.nan,
        "semis_share": round(float(pool["sector_group"].astype(str).eq("semis").mean()), 6) if not pool.empty else math.nan,
        "strong_execution_share": round(float(pool["execution_quality_bucket"].astype(str).eq("strong").mean()), 6) if not pool.empty else math.nan,
        "execution_bucket_mix": _execution_bucket_mix(pool),
        "sector_mix": _sector_mix(pool),
        "combined_stress_retention": round(float(_combined_stress_retention(post_selected, eligible_days)), 6) if not post_selected.empty else math.nan,
    }


def _episode_feature_profile(episode: dict[str, str], base_pool: pd.DataFrame) -> dict[str, Any]:
    scoped = base_pool[_episode_mask(base_pool, episode["start"], episode["end"])].copy()
    profile: dict[str, Any] = {
        "episode_name": episode["episode_name"],
        "trade_count": int(len(scoped)),
    }
    for column in NUMERIC_SIMILARITY_COLUMNS:
        profile[column] = float(_safe_numeric(scoped, column).mean()) if not scoped.empty else math.nan
    for column in CATEGORICAL_SIMILARITY_COLUMNS:
        counts = scoped[column].astype(str).value_counts(normalize=True) if (column in scoped.columns and not scoped.empty) else pd.Series(dtype=float)
        profile[f"{column}_dist"] = counts.to_dict()
    return profile


def _distribution_overlap(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    keys = set(left) | set(right)
    return float(sum(min(float(left.get(key, 0.0)), float(right.get(key, 0.0))) for key in keys))


def _numeric_similarity(left: float, right: float, lower: float, upper: float) -> float:
    if math.isnan(left) or math.isnan(right):
        return 0.0
    width = max(upper - lower, 1e-9)
    return float(max(0.0, 1.0 - (abs(left - right) / width)))


def _shock_similarity(current_profile: dict[str, Any], other_profile: dict[str, Any], base_pool: pd.DataFrame) -> dict[str, Any]:
    numeric_scores: list[float] = []
    for column in NUMERIC_SIMILARITY_COLUMNS:
        all_values = _safe_numeric(base_pool, column).dropna()
        lower = float(all_values.min()) if not all_values.empty else 0.0
        upper = float(all_values.max()) if not all_values.empty else 1.0
        numeric_scores.append(_numeric_similarity(float(current_profile[column]), float(other_profile[column]), lower, upper))
    categorical_scores = [
        _distribution_overlap(current_profile.get(f"{column}_dist", {}), other_profile.get(f"{column}_dist", {}))
        for column in CATEGORICAL_SIMILARITY_COLUMNS
    ]
    all_scores = numeric_scores + categorical_scores
    return {
        "current_episode": CURRENT_EPISODE,
        "comparison_episode": other_profile["episode_name"],
        "trade_count_current": current_profile["trade_count"],
        "trade_count_comparison": other_profile["trade_count"],
        "dispersion_similarity": round(numeric_scores[0], 6),
        "correlation_similarity": round(numeric_scores[1], 6),
        "same_day_intensity_similarity": round(numeric_scores[2], 6),
        "same_day_sector_intensity_similarity": round(numeric_scores[3], 6),
        "gap_state_overlap": round(categorical_scores[0], 6),
        "breadth_state_overlap": round(categorical_scores[1], 6),
        "sector_leadership_overlap": round(categorical_scores[2], 6),
        "shock_regime_similarity_score": round(float(np.mean(all_scores)), 6),
    }


def _replace_shock_window_rows(
    baseline_frame: pd.DataFrame,
    replacement_frame: pd.DataFrame,
) -> pd.DataFrame:
    shock_rows = _shock_mask(baseline_frame)
    replacement_shock = replacement_frame[_shock_mask(replacement_frame)].copy()
    baseline_non_shock = baseline_frame[~shock_rows].copy()
    combined = pd.concat([baseline_non_shock, replacement_shock], ignore_index=True)
    return combined.sort_values(["entry_ts", "trade_id"]).reset_index(drop=True)


def _shock_semis_cap_frame(baseline_frame: pd.DataFrame) -> pd.DataFrame:
    out = baseline_frame.copy()
    mask = _shock_mask(out) & out["sector_group"].astype(str).eq("semis")
    out.loc[mask, "size_multiplier"] = pd.to_numeric(out.loc[mask, "size_multiplier"], errors="coerce").fillna(0.0) * 0.50
    return out


def _shock_skip_frame(baseline_frame: pd.DataFrame) -> pd.DataFrame:
    return baseline_frame[~_shock_mask(baseline_frame)].copy().reset_index(drop=True)


def _episode_only_frame(frame: pd.DataFrame, episode: dict[str, str]) -> pd.DataFrame:
    return frame[_episode_mask(frame, episode["start"], episode["end"])].copy().reset_index(drop=True)


def _all_historical_shocks(episode_library: pd.DataFrame) -> pd.DataFrame:
    return episode_library[~episode_library["episode_name"].astype(str).eq(CURRENT_EPISODE)].copy().reset_index(drop=True)


def _shock_conditional_deployment(
    live_df: pd.DataFrame,
    baseline_frame: pd.DataFrame,
) -> pd.DataFrame:
    opening_frame = _candidate_from_config(
        live_df,
        BASE_STRUCTURE,
        BASE_ALLOCATOR,
        "opening_drive_allocator",
        BASE_MAX_POSITIONS,
        BASE_CAPITAL_FRACTION,
    )
    relaxed_frame = _candidate_from_config(
        live_df,
        BASE_STRUCTURE,
        BASE_ALLOCATOR,
        "post_confirmation_allocator",
        3,
        BASE_CAPITAL_FRACTION,
    )
    rule_frames = {
        "baseline_deployment": baseline_frame,
        "shock_timing_downgrade": _replace_shock_window_rows(baseline_frame, opening_frame),
        "shock_semis_cap": _shock_semis_cap_frame(baseline_frame),
        "shock_competition_relax": _replace_shock_window_rows(baseline_frame, relaxed_frame),
        "shock_skip_rule": _shock_skip_frame(baseline_frame),
    }
    rows: list[dict[str, Any]] = []
    for rule_name, frame in rule_frames.items():
        for episode in EPISODES:
            scoped = _episode_only_frame(frame, episode)
            eligible_days = max(_eligible_days(scoped), 1)
            eval_row = _evaluate_selected_configuration(rule_name, BASE_STRUCTURE, scoped, eligible_days)
            rows.append(
                {
                    "deployment_rule": rule_name,
                    "episode_name": episode["episode_name"],
                    "family": episode["family"],
                    "trade_count": eval_row["trade_count"],
                    "net_pnl_r": eval_row["net_pnl_r"],
                    "cost_adjusted_expectancy": eval_row["cost_adjusted_expectancy"],
                    "pnl_retention_ratio": eval_row["pnl_retention_ratio"],
                    "rolling_oos_robustness": eval_row["rolling_oos_robustness"],
                    "anchored_oos_cost_adjusted_expectancy": eval_row["anchored_oos_cost_adjusted_expectancy"],
                }
            )
        historical = _all_historical_shocks(pd.DataFrame(EPISODES))
        hist_frames = [
            _episode_only_frame(frame, episode.to_dict())
            for _, episode in historical.iterrows()
        ]
        hist_scoped = pd.concat(hist_frames, ignore_index=True) if hist_frames else pd.DataFrame(columns=frame.columns)
        eligible_days = max(_eligible_days(hist_scoped), 1)
        hist_eval = _evaluate_selected_configuration(rule_name, BASE_STRUCTURE, hist_scoped, eligible_days)
        rows.append(
            {
                "deployment_rule": rule_name,
                "episode_name": "all_historical_shocks",
                "family": "aggregate",
                "trade_count": hist_eval["trade_count"],
                "net_pnl_r": hist_eval["net_pnl_r"],
                "cost_adjusted_expectancy": hist_eval["cost_adjusted_expectancy"],
                "pnl_retention_ratio": hist_eval["pnl_retention_ratio"],
                "rolling_oos_robustness": hist_eval["rolling_oos_robustness"],
                "anchored_oos_cost_adjusted_expectancy": hist_eval["anchored_oos_cost_adjusted_expectancy"],
            }
        )
    return pd.DataFrame(rows).sort_values(["episode_name", "net_pnl_r"], ascending=[True, False]).reset_index(drop=True)


def _shock_family_comparison(
    episode_library: pd.DataFrame,
    similarity_df: pd.DataFrame,
) -> pd.DataFrame:
    current = episode_library[episode_library["episode_name"].astype(str).eq(CURRENT_EPISODE)].iloc[0]
    out = episode_library.merge(
        similarity_df[["comparison_episode", "shock_regime_similarity_score"]],
        left_on="episode_name",
        right_on="comparison_episode",
        how="left",
    ).drop(columns=["comparison_episode"], errors="ignore")
    out["current_window_net_pnl_r"] = current["selected_net_pnl_r"]
    out["current_window_semis_share"] = current["semis_share"]
    return out.sort_values(["shock_regime_similarity_score", "selected_net_pnl_r"], ascending=[False, True]).reset_index(drop=True)


def _final_decision(similarity_df: pd.DataFrame, deployment_df: pd.DataFrame) -> pd.DataFrame:
    historical = similarity_df[~similarity_df["comparison_episode"].astype(str).eq(CURRENT_EPISODE)].copy()
    best_match = historical.sort_values(["shock_regime_similarity_score"], ascending=[False]).iloc[0] if not historical.empty else pd.Series(dtype=object)
    current_deploy = deployment_df[deployment_df["episode_name"].astype(str).eq(CURRENT_EPISODE)].copy()
    baseline = current_deploy[current_deploy["deployment_rule"].astype(str) == "baseline_deployment"]
    best_rule = current_deploy.sort_values(["net_pnl_r", "cost_adjusted_expectancy"], ascending=[False, False]).iloc[0] if not current_deploy.empty else pd.Series(dtype=object)
    baseline_net = float(pd.to_numeric(baseline["net_pnl_r"], errors="coerce").iloc[0]) if not baseline.empty else math.nan
    best_net = float(pd.to_numeric(pd.Series([best_rule.get("net_pnl_r", math.nan)]), errors="coerce").iloc[0])
    improvement = best_net - baseline_net if not math.isnan(best_net) and not math.isnan(baseline_net) else math.nan
    best_similarity = float(pd.to_numeric(pd.Series([best_match.get("shock_regime_similarity_score", math.nan)]), errors="coerce").iloc[0])
    if not math.isnan(best_similarity) and best_similarity >= 0.60 and not math.isnan(improvement) and improvement >= 0.25 and best_net >= 0:
        decision = "SHOCK_MANAGEABLE_DEPLOYMENT"
        reason = "Current failure window closely matches a historical shock family and a fixed shock-aware rule restores episode-level PnL."
    elif not math.isnan(best_similarity) and best_similarity >= 0.60:
        decision = "SHOCK_SPECIFIC_FAILURE"
        reason = "Current failure window looks like a prior shock regime, but fixed shock-aware deployment rules do not fully repair the damage."
    elif not math.isnan(best_similarity) and best_similarity <= 0.45:
        decision = "NEW_REGIME_BREAKDOWN"
        reason = "Current failure window does not look sufficiently similar to prior shock episodes, so a deeper sleeve breakdown is more plausible."
    else:
        decision = "NO_CLEAR_SHOCK_EXPLANATION"
        reason = "Shock comparison provides only mixed explanatory power and no single fixed policy stands out."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_match_episode": best_match.get("comparison_episode", ""),
                "best_match_similarity_score": round(best_similarity, 6) if not math.isnan(best_similarity) else math.nan,
                "current_baseline_net_pnl_r": round(baseline_net, 6) if not math.isnan(baseline_net) else math.nan,
                "best_shock_rule": best_rule.get("deployment_rule", ""),
                "best_shock_rule_net_pnl_r": round(best_net, 6) if not math.isnan(best_net) else math.nan,
                "best_shock_rule_improvement_r": round(improvement, 6) if not math.isnan(improvement) else math.nan,
            }
        ]
    )


def _report(
    out_dir: Path,
    episode_df: pd.DataFrame,
    similarity_df: pd.DataFrame,
    current_vs_russia_df: pd.DataFrame,
    family_df: pd.DataFrame,
    deployment_df: pd.DataFrame,
    final_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    lines = [
        "# Task 356 - Event-Shock Regime Audit",
        "",
        f"- decision: {final_row['decision']}",
        f"- best_match_episode: {final_row['best_match_episode']}",
        f"- best_match_similarity_score: {final_row['best_match_similarity_score']}",
        f"- best_shock_rule: {final_row['best_shock_rule']}",
        "",
        "## Final Interpretation",
        "1. This task compares the current anchored OOS failure window against explicit historical shock episodes rather than searching for new alpha.",
        f"2. Final decision: `{final_row['decision']}`",
        f"3. Best historical match: `{final_row['best_match_episode']}`",
        f"4. Best fixed shock-aware rule: `{final_row['best_shock_rule']}`",
        "",
        "## Event Episode Library",
        *(_markdown_table(episode_df)),
        "",
        "## Shock Regime Similarity",
        *(_markdown_table(similarity_df)),
        "",
        "## Current vs Russia War",
        *(_markdown_table(current_vs_russia_df)),
        "",
        "## Shock Family Comparison",
        *(_markdown_table(family_df)),
        "",
        "## Shock-Conditional Deployment",
        *(_markdown_table(deployment_df)),
    ]
    (out_dir / "task_356_event_shock_regime_audit.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 356: event-shock regime equivalence and war-period translation audit")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    live_df, allocator_df, selected_frames_df = _build_task355_context()
    _best_row, baseline_frame = _best_baseline_frame(live_df, allocator_df, selected_frames_df)
    base_pool = _base_candidate_pool(live_df, BASE_STRUCTURE, "post_confirmation_allocator")
    opening_frame = _candidate_from_config(
        live_df,
        BASE_STRUCTURE,
        BASE_ALLOCATOR,
        "opening_drive_allocator",
        BASE_MAX_POSITIONS,
        BASE_CAPITAL_FRACTION,
    )

    episode_rows = [_episode_summary(episode, base_pool, baseline_frame, opening_frame) for episode in EPISODES]
    episode_df = pd.DataFrame(episode_rows)

    profiles = {episode["episode_name"]: _episode_feature_profile(episode, base_pool) for episode in EPISODES}
    current_profile = profiles[CURRENT_EPISODE]
    similarity_rows = [_shock_similarity(current_profile, profile, base_pool) for name, profile in profiles.items() if name != CURRENT_EPISODE]
    similarity_df = pd.DataFrame(similarity_rows).sort_values(["shock_regime_similarity_score"], ascending=[False]).reset_index(drop=True)

    current_vs_russia_df = similarity_df[similarity_df["comparison_episode"].astype(str) == "russia_invasion_shock"].reset_index(drop=True)
    family_df = _shock_family_comparison(episode_df, similarity_df)
    deployment_df = _shock_conditional_deployment(live_df, baseline_frame)
    final_df = _final_decision(similarity_df, deployment_df)

    episode_df.to_csv(out_dir / "task_356_event_episode_library.csv", index=False)
    similarity_df.to_csv(out_dir / "task_356_shock_regime_similarity.csv", index=False)
    current_vs_russia_df.to_csv(out_dir / "task_356_current_vs_russia_war_comparison.csv", index=False)
    family_df.to_csv(out_dir / "task_356_shock_family_comparison.csv", index=False)
    deployment_df.to_csv(out_dir / "task_356_shock_conditional_deployment.csv", index=False)
    final_df.to_csv(out_dir / "task_356_final_decision.csv", index=False)
    _report(out_dir, episode_df, similarity_df, current_vs_russia_df, family_df, deployment_df, final_df)


if __name__ == "__main__":
    main()
