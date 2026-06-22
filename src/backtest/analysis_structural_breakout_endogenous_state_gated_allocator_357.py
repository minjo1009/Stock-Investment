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
    BASE_STRUCTURE,
    _anchored_loss_decomposition,
    _best_baseline_frame,
)
from src.backtest.analysis_structural_breakout_event_shock_regime_audit_356 import _episode_mask
from src.backtest.analysis_structural_breakout_regime_sleeve_deployment_354 import (
    _allocator_score,
    _base_size_multiplier,
    _evaluate_selected_configuration,
    _prepare_task354_context,
    _timing_long_frame,
    _timing_score_wide,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_357_endogenous_state_gated_allocator")
CURRENT_FAILURE_START = "2025-12-01"
CURRENT_FAILURE_END = "2026-01-31"
FRAMEWORKS = (
    ("current_baseline_sleeve", "baseline_rank_allocator"),
    ("state_gated_allocator_only", "state_gated_allocator"),
    ("state_gated_allocator_plus_semis_factor_cap", "fragility_adjusted_allocator"),
    ("state_gated_allocator_plus_staged_execution", "marginal_utility_allocator"),
    ("full_dislocation_mode", "marginal_utility_allocator"),
)


def _safe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _eligible_days(frame: pd.DataFrame) -> int:
    days = pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna()
    return int(days.nunique())


def _build_task357_context() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master, selected_df = _prepare_task354_context()
    wide_df = _timing_score_wide(master, selected_df)
    live_df = _timing_long_frame(wide_df)
    enrich_cols = [
        "event_id",
        "market_breadth_state",
        "gap_environment_state",
        "sector_leadership_state",
        "dispersion_20d",
        "mean_pairwise_corr",
        "sector_crowding_high",
        "crowding_state",
        "volatility_state",
        "liquidity_state",
        "macro_shock_state",
        "post_risk_off_state",
        "semis_concentration_ratio",
        "tech_concentration_ratio",
        "top_sector_dominance_score",
    ]
    available_cols = [col for col in enrich_cols if col in master.columns]
    enriched = live_df.merge(master[available_cols].copy(), on="event_id", how="left")
    return master, selected_df, wide_df, enriched


def _base_candidate_pool(live_df: pd.DataFrame) -> pd.DataFrame:
    return live_df[
        live_df["allocator_timing"].astype(str).eq("post_confirmation_allocator")
        & live_df[BASE_STRUCTURE].astype(bool)
    ].copy().reset_index(drop=True)


def _state_thresholds(scoped: pd.DataFrame) -> dict[str, float]:
    train = scoped[scoped["current_split"].astype(str).eq("train")].copy()
    base = train if not train.empty else scoped
    thresholds = {
        "same_day_candidate_mid": float(_safe_numeric(base, "same_day_candidate_count").quantile(0.50)),
        "same_day_candidate_high": float(_safe_numeric(base, "same_day_candidate_count").quantile(0.75)),
        "same_day_sector_mid": float(_safe_numeric(base, "same_day_sector_candidate_count").quantile(0.50)),
        "same_day_sector_high": float(_safe_numeric(base, "same_day_sector_candidate_count").quantile(0.75)),
        "dispersion_high": float(_safe_numeric(base, "dispersion_20d").quantile(0.75)),
        "corr_high": float(_safe_numeric(base, "mean_pairwise_corr").quantile(0.75)),
        "semis_concentration_high": float(_safe_numeric(base, "semis_concentration_ratio").quantile(0.75)),
    }
    for key, value in thresholds.items():
        if math.isnan(value):
            thresholds[key] = 0.0
    return thresholds


def _row_state(row: pd.Series, thresholds: dict[str, float]) -> str:
    same_day_candidate_mid = float(thresholds.get("same_day_candidate_mid", thresholds.get("same_day_candidate_high", 0.0)))
    same_day_sector_mid = float(thresholds.get("same_day_sector_mid", thresholds.get("same_day_sector_high", 0.0)))
    same_day_count = float(pd.to_numeric(pd.Series([row.get("same_day_candidate_count", math.nan)]), errors="coerce").iloc[0])
    same_sector_count = float(pd.to_numeric(pd.Series([row.get("same_day_sector_candidate_count", math.nan)]), errors="coerce").iloc[0])
    dispersion = float(pd.to_numeric(pd.Series([row.get("dispersion_20d", math.nan)]), errors="coerce").iloc[0])
    corr = float(pd.to_numeric(pd.Series([row.get("mean_pairwise_corr", math.nan)]), errors="coerce").iloc[0])
    semis_ratio = float(pd.to_numeric(pd.Series([row.get("semis_concentration_ratio", math.nan)]), errors="coerce").iloc[0])
    session_bucket = str(row.get("session_timing_bucket", "unknown"))
    execution_bucket = str(row.get("execution_quality_bucket", "unknown"))
    sector_group = str(row.get("sector_group", ""))
    gap_state = str(row.get("gap_environment_state", ""))
    breadth_state = str(row.get("market_breadth_state", ""))
    leadership_state = str(row.get("sector_leadership_state", ""))
    crowded_triggers = 0
    crowded_triggers += int(sector_group == "semis" and same_sector_count >= thresholds["same_day_sector_high"])
    crowded_triggers += int(same_day_count >= thresholds["same_day_candidate_high"] and session_bucket in {"first_30m", "unknown"})
    crowded_triggers += int(gap_state == "unstable" and breadth_state == "narrow")
    crowded_triggers += int(dispersion >= thresholds["dispersion_high"] and corr >= thresholds["corr_high"])
    crowded_triggers += int(execution_bucket == "strong" and session_bucket in {"first_30m", "unknown"} and same_day_count >= same_day_candidate_mid)
    crowded_triggers += int(sector_group == "semis" and semis_ratio >= thresholds["semis_concentration_high"])
    crowded_triggers += int(leadership_state == "tech_led" and breadth_state == "narrow")
    if crowded_triggers >= 2:
        return "crowded_dislocation_state"

    normal_triggers = 0
    normal_triggers += int(gap_state == "calm")
    normal_triggers += int(breadth_state == "broad")
    normal_triggers += int(session_bucket in {"mid_session", "last_hour"})
    normal_triggers += int(execution_bucket in {"strong", "mixed"})
    normal_triggers += int(same_day_count <= same_day_candidate_mid)
    normal_triggers += int(same_sector_count <= same_day_sector_mid)
    normal_triggers += int(sector_group != "semis")
    if normal_triggers >= 4:
        return "normal_continuation_state"
    return "uncertain_transition_state"


def _day_state(scoped: pd.DataFrame, thresholds: dict[str, float]) -> str:
    row_states = scoped["endogenous_state"].astype(str)
    crowded_share = float(row_states.eq("crowded_dislocation_state").mean()) if not scoped.empty else 0.0
    normal_share = float(row_states.eq("normal_continuation_state").mean()) if not scoped.empty else 0.0
    semis_share = float(scoped["sector_group"].astype(str).eq("semis").mean()) if not scoped.empty else 0.0
    avg_same_day = float(_safe_numeric(scoped, "same_day_candidate_count").mean()) if not scoped.empty else 0.0
    if crowded_share >= 0.45 or (semis_share >= 0.50 and avg_same_day >= thresholds["same_day_candidate_mid"]):
        return "crowded_dislocation_state"
    if crowded_share <= 0.15 and normal_share >= 0.45:
        return "normal_continuation_state"
    return "uncertain_transition_state"


def _apply_state_labels(scoped: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    out = scoped.copy()
    thresholds = _state_thresholds(out)
    out["endogenous_state"] = out.apply(lambda row: _row_state(row, thresholds), axis=1)
    day_states = out.groupby("day_key", dropna=False).agg(
        day_endogenous_state=("endogenous_state", lambda _series: _day_state(out.loc[_series.index], thresholds))
    )
    out = out.merge(day_states, left_on="day_key", right_index=True, how="left")
    return out.reset_index(drop=True), thresholds


def _state_detector_diagnostics(scoped: pd.DataFrame) -> pd.DataFrame:
    current_mask = _episode_mask(scoped, CURRENT_FAILURE_START, CURRENT_FAILURE_END)
    rows: list[dict[str, Any]] = []
    for split_name, split_df in scoped.groupby("current_split", dropna=False):
        for state_name, state_df in split_df.groupby("endogenous_state", dropna=False):
            rows.append(
                {
                    "scope": "by_split",
                    "bucket_a": str(split_name),
                    "bucket_b": str(state_name),
                    "trade_count": int(len(state_df)),
                    "trade_share": round(float(len(state_df) / max(len(split_df), 1)), 6),
                    "semis_share": round(float(state_df["sector_group"].astype(str).eq("semis").mean()), 6),
                    "first_30m_or_unknown_share": round(float(state_df["session_timing_bucket"].astype(str).isin({"first_30m", "unknown"}).mean()), 6),
                }
            )
    current = scoped[current_mask].copy()
    for state_name, state_df in current.groupby("endogenous_state", dropna=False):
        rows.append(
            {
                "scope": "current_failure_window",
                "bucket_a": CURRENT_FAILURE_START,
                "bucket_b": str(state_name),
                "trade_count": int(len(state_df)),
                "trade_share": round(float(len(state_df) / max(len(current), 1)), 6),
                "semis_share": round(float(state_df["sector_group"].astype(str).eq("semis").mean()), 6),
                "first_30m_or_unknown_share": round(float(state_df["session_timing_bucket"].astype(str).isin({"first_30m", "unknown"}).mean()), 6),
            }
        )
    return pd.DataFrame(rows)


def _position_cap_for_day_state(day_state: str, framework_name: str) -> int:
    if framework_name == "current_baseline_sleeve":
        return 1
    if framework_name == "full_dislocation_mode" and day_state == "crowded_dislocation_state":
        return 0
    if day_state == "normal_continuation_state":
        return 3
    if day_state == "uncertain_transition_state":
        return 2
    return 1


def _state_weight(row_state: str, framework_name: str) -> float:
    if framework_name == "current_baseline_sleeve":
        return 1.0
    if framework_name == "state_gated_allocator_only":
        return {"normal_continuation_state": 1.0, "uncertain_transition_state": 0.75, "crowded_dislocation_state": 0.45}[row_state]
    if framework_name == "state_gated_allocator_plus_semis_factor_cap":
        return {"normal_continuation_state": 1.0, "uncertain_transition_state": 0.70, "crowded_dislocation_state": 0.40}[row_state]
    if framework_name == "state_gated_allocator_plus_staged_execution":
        return {"normal_continuation_state": 1.0, "uncertain_transition_state": 0.65, "crowded_dislocation_state": 0.35}[row_state]
    return {"normal_continuation_state": 1.0, "uncertain_transition_state": 0.55, "crowded_dislocation_state": 0.0}[row_state]


def _staged_weight(row: pd.Series, framework_name: str) -> tuple[str, float]:
    if framework_name != "state_gated_allocator_plus_staged_execution":
        return "full_participation", 1.0
    row_state = str(row["endogenous_state"])
    execution_bucket = str(row.get("execution_quality_bucket", "unknown"))
    session_bucket = str(row.get("session_timing_bucket", "unknown"))
    if row_state == "normal_continuation_state" and execution_bucket in {"strong", "mixed"}:
        return "stage_2_add", 1.0
    if row_state == "crowded_dislocation_state" or session_bucket in {"first_30m", "unknown"}:
        return "stage_1_probe", 0.35 if execution_bucket == "strong" else 0.20
    return "delayed_probe", 0.60


def _marginal_penalty(
    candidate: pd.Series,
    selected_rows: list[pd.Series],
    framework_name: str,
) -> tuple[float, bool]:
    penalty = 0.0
    blocked = False
    if not selected_rows:
        return penalty, blocked
    same_sector = sum(str(row["sector_group"]) == str(candidate["sector_group"]) for row in selected_rows)
    same_session = sum(str(row["session_timing_bucket"]) == str(candidate["session_timing_bucket"]) for row in selected_rows)
    same_symbol = sum(str(row["symbol"]) == str(candidate["symbol"]) for row in selected_rows)
    semis_selected = sum(str(row["sector_group"]) == "semis" for row in selected_rows)

    penalty += 0.30 * same_sector
    penalty += 0.15 * same_session
    penalty += 1.00 * same_symbol
    if str(candidate["sector_group"]) == "semis":
        penalty += 0.40 * semis_selected
        if framework_name in {"state_gated_allocator_plus_semis_factor_cap", "state_gated_allocator_plus_staged_execution", "full_dislocation_mode"} and semis_selected >= 1:
            blocked = True
    return penalty, blocked


def _base_rank_score(scoped: pd.DataFrame) -> pd.Series:
    base = _allocator_score(scoped, BASE_ALLOCATOR)
    regime_score = _safe_numeric(scoped, "regime_score_at_decision_time").fillna(0.0)
    artifact_pct = _safe_numeric(scoped, "artifact_score_percentile_at_decision_time").fillna(0.0)
    return base + (0.15 * regime_score) + (0.10 * artifact_pct)


def _select_framework_frame(scoped: pd.DataFrame, framework_name: str) -> pd.DataFrame:
    if scoped.empty:
        return scoped.copy()
    base = scoped.copy()
    base["base_allocator_score"] = _base_rank_score(base)
    selected_frames: list[pd.DataFrame] = []
    for _, day_df in base.groupby("day_key", sort=True):
        day_df = day_df.copy()
        day_state = str(day_df["day_endogenous_state"].iloc[0])
        day_cap = _position_cap_for_day_state(day_state, framework_name)
        if day_cap <= 0:
            continue
        available = day_df.sort_values(["base_allocator_score", "trade_id"], ascending=[False, True]).copy()
        chosen: list[pd.Series] = []
        while len(chosen) < day_cap and not available.empty:
            scored_rows: list[dict[str, Any]] = []
            for idx, row in available.iterrows():
                state_penalty = 1.0 - _state_weight(str(row["endogenous_state"]), framework_name)
                marginal_penalty, blocked = _marginal_penalty(row, chosen, framework_name)
                adjusted = float(row["base_allocator_score"]) - state_penalty - marginal_penalty
                scored_rows.append(
                    {
                        "idx": idx,
                        "adjusted_allocator_score": adjusted,
                        "marginal_penalty": marginal_penalty + state_penalty,
                        "semis_cap_blocked_flag": blocked,
                    }
                )
            score_df = pd.DataFrame(scored_rows).sort_values(
                ["semis_cap_blocked_flag", "adjusted_allocator_score"],
                ascending=[True, False],
            )
            if score_df.empty:
                break
            top = score_df.iloc[0]
            if bool(top["semis_cap_blocked_flag"]):
                break
            selected_row = available.loc[int(top["idx"])].copy()
            selected_row["adjusted_allocator_score"] = float(top["adjusted_allocator_score"])
            selected_row["marginal_penalty"] = float(top["marginal_penalty"])
            selected_row["semis_cap_blocked_flag"] = False
            chosen.append(selected_row)
            available = available.drop(index=int(top["idx"]))
        if not chosen:
            continue
        selected_day = pd.DataFrame(chosen).reset_index(drop=True)
        selected_day["allocator_rank"] = np.arange(1, len(selected_day) + 1)
        selected_day["framework_name"] = framework_name
        selected_day["allocator_variant"] = dict(FRAMEWORKS)[framework_name]
        selected_day["state_level_gross_cap"] = day_cap
        selected_day["base_size_multiplier"] = _base_size_multiplier(BASE_STRUCTURE, selected_day) * BASE_CAPITAL_FRACTION / max(day_cap, 1)
        stage_info = selected_day.apply(lambda row: _staged_weight(row, framework_name), axis=1)
        selected_day["participation_stage"] = [item[0] for item in stage_info]
        selected_day["stage_weight"] = [item[1] for item in stage_info]
        if framework_name == "state_gated_allocator_plus_semis_factor_cap":
            semis_mask = selected_day["sector_group"].astype(str).eq("semis")
            selected_day.loc[semis_mask, "stage_weight"] = pd.to_numeric(selected_day.loc[semis_mask, "stage_weight"], errors="coerce").fillna(1.0) * 0.50
            selected_day.loc[semis_mask, "participation_stage"] = "semis_factor_capped"
        selected_day["size_multiplier"] = pd.to_numeric(selected_day["base_size_multiplier"], errors="coerce") * pd.to_numeric(selected_day["stage_weight"], errors="coerce")
        selected_frames.append(selected_day)
    if not selected_frames:
        return base.iloc[0:0].copy()
    return pd.concat(selected_frames, ignore_index=True).sort_values(["entry_ts", "trade_id"]).reset_index(drop=True)


def _framework_metrics(framework_name: str, frame: pd.DataFrame, eligible_days: int) -> dict[str, Any]:
    eval_row = _evaluate_selected_configuration(dict(FRAMEWORKS)[framework_name], BASE_STRUCTURE, frame, eligible_days)
    anchored = frame[frame["current_split"].astype(str) == "anchored_oos"].copy()
    anchored["loss_component"] = np.where(_safe_numeric(anchored, "realized_R") < 0, _safe_numeric(anchored, "realized_R").abs(), 0.0)
    total_loss = float(anchored["loss_component"].sum())
    semis_loss_share = float(anchored.loc[anchored["sector_group"].astype(str) == "semis", "loss_component"].sum() / max(total_loss, 1e-9)) if not anchored.empty else math.nan
    first30_loss_share = float(
        anchored.loc[anchored["session_timing_bucket"].astype(str).isin({"first_30m", "unknown"}), "loss_component"].sum() / max(total_loss, 1e-9)
    ) if not anchored.empty else math.nan
    crowded_state_share = float(frame["day_endogenous_state"].astype(str).eq("crowded_dislocation_state").mean()) if not frame.empty else math.nan
    eval_row.update(
        {
            "framework_name": framework_name,
            "allocator_variant": dict(FRAMEWORKS)[framework_name],
            "anchored_oos_drawdown": eval_row["mdd_pct"],
            "semis_loss_share": round(semis_loss_share, 6) if not math.isnan(semis_loss_share) else math.nan,
            "first30_or_unknown_loss_share": round(first30_loss_share, 6) if not math.isnan(first30_loss_share) else math.nan,
            "crowded_state_trade_share": round(crowded_state_share, 6) if not math.isnan(crowded_state_share) else math.nan,
        }
    )
    return eval_row


def _factor_netting_effect(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for framework_name in ("current_baseline_sleeve", "state_gated_allocator_only", "state_gated_allocator_plus_semis_factor_cap", "state_gated_allocator_plus_staged_execution"):
        frame = frames.get(framework_name, pd.DataFrame()).copy()
        anchored = frame[frame["current_split"].astype(str) == "anchored_oos"].copy()
        rows.append(
            {
                "framework_name": framework_name,
                "trade_count": int(len(frame)),
                "anchored_trade_count": int(len(anchored)),
                "semis_trade_share": round(float(frame["sector_group"].astype(str).eq("semis").mean()), 6) if not frame.empty else math.nan,
                "anchored_semis_trade_share": round(float(anchored["sector_group"].astype(str).eq("semis").mean()), 6) if not anchored.empty else math.nan,
                "avg_same_day_sector_candidate_count": round(float(_safe_numeric(frame, "same_day_sector_candidate_count").mean()), 6) if not frame.empty else math.nan,
                "avg_marginal_penalty": round(float(_safe_numeric(frame, "marginal_penalty").mean()), 6) if "marginal_penalty" in frame.columns and not frame.empty else math.nan,
            }
        )
    return pd.DataFrame(rows)


def _staged_execution_comparison(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for framework_name in ("current_baseline_sleeve", "state_gated_allocator_plus_staged_execution"):
        frame = frames.get(framework_name, pd.DataFrame()).copy()
        if frame.empty:
            continue
        for stage_name, scoped in frame.groupby("participation_stage", dropna=False):
            rows.append(
                {
                    "framework_name": framework_name,
                    "participation_stage": str(stage_name),
                    "trade_count": int(len(scoped)),
                    "avg_stage_weight": round(float(_safe_numeric(scoped, "stage_weight").mean()), 6) if "stage_weight" in scoped.columns else 1.0,
                    "expectancy": round(float(_safe_numeric(scoped, "realized_R").mean()), 6),
                    "semis_share": round(float(scoped["sector_group"].astype(str).eq("semis").mean()), 6),
                    "crowded_state_share": round(float(scoped["day_endogenous_state"].astype(str).eq("crowded_dislocation_state").mean()), 6),
                }
            )
    return pd.DataFrame(rows)


def _failure_cluster_contribution(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for framework_name, frame in frames.items():
        loss_df = _anchored_loss_decomposition(frame)
        if loss_df.empty:
            continue
        loss_df = loss_df.copy()
        loss_df["framework_name"] = framework_name
        rows.append(loss_df)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _final_decision(comparison_df: pd.DataFrame) -> pd.DataFrame:
    if comparison_df.empty:
        return pd.DataFrame([{"decision": "NO_DEPLOYABLE_TRADING_UPLIFT", "decision_reason": "No framework outputs were produced."}])
    baseline = comparison_df[comparison_df["framework_name"].astype(str) == "current_baseline_sleeve"].iloc[0]
    trade_count = _safe_numeric(comparison_df, "trade_count") if "trade_count" in comparison_df.columns else pd.Series(np.nan, index=comparison_df.index)
    capital_utilization = _safe_numeric(comparison_df, "capital_utilization") if "capital_utilization" in comparison_df.columns else pd.Series(np.nan, index=comparison_df.index)
    viable = comparison_df[
        (trade_count.fillna(0.0) >= 50)
        & (capital_utilization.fillna(0.0) >= 0.10)
    ].copy()
    rank_source = viable if not viable.empty else comparison_df
    best = rank_source.sort_values(
        ["anchored_oos_net_pnl_r", "rolling_oos_robustness", "semis_loss_share", "net_pnl_r"],
        ascending=[False, False, True, False],
    ).iloc[0]
    anchored_improvement = float(best["anchored_oos_net_pnl_r"]) - float(baseline["anchored_oos_net_pnl_r"])
    semis_improvement = float(baseline["semis_loss_share"]) - float(best["semis_loss_share"])
    if str(best["framework_name"]) == "current_baseline_sleeve":
        decision = "NORMAL_MODE_ONLY"
        reason = "State-aware frameworks do not beat the current baseline on anchored OOS and concentration control."
    elif float(best["anchored_oos_net_pnl_r"]) > 0 and float(best["rolling_oos_robustness"]) >= float(baseline["rolling_oos_robustness"]) and semis_improvement > 0:
        decision = "DISLOCATION_AWARE_SLEEVE"
        reason = "State gating, factor control, and staged participation convert the sleeve into a more deployable dislocation-aware trading mode."
    elif anchored_improvement > 0 and semis_improvement >= 0:
        decision = "STATE_GATED_CONTINUATION"
        reason = "State-aware allocation improves anchored OOS and concentration damage, but the sleeve is not yet fully repaired."
    else:
        decision = "NO_DEPLOYABLE_TRADING_UPLIFT"
        reason = "Allocator, factor cap, and staged participation do not deliver enough anchored OOS improvement to justify deployment uplift."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_framework_name": best["framework_name"],
                "best_allocator_variant": best["allocator_variant"],
                "best_anchored_oos_net_pnl_r": best["anchored_oos_net_pnl_r"],
                "best_anchored_oos_drawdown": best["anchored_oos_drawdown"],
                "best_semis_loss_share": best["semis_loss_share"],
                "best_rolling_oos_robustness": best["rolling_oos_robustness"],
                "anchored_oos_improvement_vs_baseline": round(anchored_improvement, 6),
            }
        ]
    )


def _report(
    out_dir: Path,
    state_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    factor_df: pd.DataFrame,
    staged_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    final_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    lines = [
        "# Task 357 - Endogenous State-Gated Continuation Allocator",
        "",
        f"- decision: {final_row['decision']}",
        f"- best_framework_name: {final_row['best_framework_name']}",
        f"- best_anchored_oos_net_pnl_r: {final_row['best_anchored_oos_net_pnl_r']}",
        "",
        "## Final Interpretation",
        "1. This task redesigns the continuation sleeve as a state-aware allocator rather than searching for new alpha.",
        f"2. Final decision: `{final_row['decision']}`",
        f"3. Best framework: `{final_row['best_framework_name']}`",
        "",
        "## State Detector Diagnostics",
        *(_markdown_table(state_df)),
        "",
        "## Framework Comparison",
        *(_markdown_table(comparison_df)),
        "",
        "## Factor Netting Effect",
        *(_markdown_table(factor_df)),
        "",
        "## Staged Execution Comparison",
        *(_markdown_table(staged_df)),
        "",
        "## Failure Cluster Contribution",
        *(_markdown_table(failure_df.head(20))),
    ]
    (out_dir / "task_357_endogenous_state_gated_allocator.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 357: endogenous state-gated continuation allocator")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    _master, _selected_df, _wide_df, live_df = _build_task357_context()
    base_pool = _base_candidate_pool(live_df)
    labeled_pool, _thresholds = _apply_state_labels(base_pool)
    labeled_pool["base_allocator_score"] = _base_rank_score(labeled_pool)

    # Baseline frame from existing Task 354 best configuration.
    from src.backtest.analysis_structural_breakout_regime_sleeve_deployment_354 import _allocator_comparison

    allocator_df, _competition_df, selected_frames_df = _allocator_comparison(live_df)
    _best_row, baseline_frame = _best_baseline_frame(live_df, allocator_df, selected_frames_df)
    baseline_frame = baseline_frame.merge(
        labeled_pool[
            [
                "event_id",
                "endogenous_state",
                "day_endogenous_state",
                "base_allocator_score",
            ]
        ].drop_duplicates(subset=["event_id"]),
        on="event_id",
        how="left",
    )
    baseline_frame["framework_name"] = "current_baseline_sleeve"
    baseline_frame["allocator_variant"] = "baseline_rank_allocator"
    baseline_frame["marginal_penalty"] = 0.0
    baseline_frame["semis_cap_blocked_flag"] = False
    baseline_frame["participation_stage"] = "full_participation"
    baseline_frame["stage_weight"] = 1.0

    frames: dict[str, pd.DataFrame] = {"current_baseline_sleeve": baseline_frame.copy()}
    for framework_name, _allocator_variant in FRAMEWORKS[1:]:
        frames[framework_name] = _select_framework_frame(labeled_pool, framework_name)

    eligible_days = _eligible_days(live_df)
    comparison_rows = [_framework_metrics(name, frame, eligible_days) for name, frame in frames.items()]
    comparison_df = pd.DataFrame(comparison_rows).sort_values(
        ["anchored_oos_net_pnl_r", "net_pnl_r", "rolling_oos_robustness"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    state_df = _state_detector_diagnostics(labeled_pool)
    factor_df = _factor_netting_effect(frames)
    staged_df = _staged_execution_comparison(frames)
    failure_df = _failure_cluster_contribution(frames)
    final_df = _final_decision(comparison_df)

    state_df.to_csv(out_dir / "task_357_state_detector_diagnostics.csv", index=False)
    comparison_df.to_csv(out_dir / "task_357_allocator_framework_comparison.csv", index=False)
    factor_df.to_csv(out_dir / "task_357_factor_netting_effect.csv", index=False)
    staged_df.to_csv(out_dir / "task_357_staged_execution_comparison.csv", index=False)
    failure_df.to_csv(out_dir / "task_357_failure_cluster_contribution.csv", index=False)
    final_df.to_csv(out_dir / "task_357_final_decision.csv", index=False)
    _report(out_dir, state_df, comparison_df, factor_df, staged_df, failure_df, final_df)


if __name__ == "__main__":
    main()
