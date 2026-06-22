from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_regime_sleeve_deployment_354 import (
    _allocator_comparison,
    _evaluate_selected_configuration,
    _execution_realism_stress,
    _final_decision as _deployment_final_decision,
    _prepare_task354_context,
    _select_with_allocator,
    _sleeve_overlap_netting,
    _timing_long_frame,
    _timing_score_wide,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_355_anchored_oos_failure_uplift")
BASE_STRUCTURE = "sizing_template_aggressive"
BASE_ALLOCATOR = "structural_balance_allocator"
BASE_TIMING = "post_confirmation_allocator"
BASE_BUCKET_NAME = "bucket_20pct"
BASE_CAPITAL_FRACTION = 0.20
BASE_MAX_POSITIONS = 1
CAPPED_AGGRESSIVE_TEMPLATE = {"core": 1.50, "active": 1.25, "light": 0.50, "skip": 0.0}


def _safe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _eligible_days(frame: pd.DataFrame) -> int:
    return int(pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique())


def _build_task355_context() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master, selected_df = _prepare_task354_context()
    wide_df = _timing_score_wide(master, selected_df)
    live_df = _timing_long_frame(wide_df)
    allocator_df, _competition_df, selected_frames_df = _allocator_comparison(live_df)
    return live_df, allocator_df, selected_frames_df


def _best_baseline_frame(live_df: pd.DataFrame, allocator_df: pd.DataFrame, selected_frames_df: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    if allocator_df.empty or selected_frames_df.empty:
        return pd.Series(dtype=object), pd.DataFrame()
    best = allocator_df.iloc[0]
    mask = (
        selected_frames_df["structure_name"].astype(str).eq(str(best["structure_name"]))
        & selected_frames_df["allocator_name"].astype(str).eq(str(best["allocator_name"]))
        & selected_frames_df["allocator_timing"].astype(str).eq(str(best["allocator_timing"]))
        & selected_frames_df["capital_bucket"].astype(str).eq(str(best["capital_bucket"]))
        & (_safe_numeric(selected_frames_df, "max_positions") == float(pd.to_numeric(pd.Series([best["max_positions"]]), errors="coerce").iloc[0]))
    )
    return best, selected_frames_df[mask].copy().reset_index(drop=True)


def _base_candidate_pool(live_df: pd.DataFrame, structure_name: str, allocator_timing: str) -> pd.DataFrame:
    scoped = live_df[live_df["allocator_timing"].astype(str) == allocator_timing].copy()
    if structure_name == "artifact_half_plus":
        return scoped[scoped["artifact_half_plus"].astype(bool)].copy()
    return scoped[scoped[structure_name].astype(bool)].copy()


def _anchored_loss_decomposition(best_frame: pd.DataFrame) -> pd.DataFrame:
    anchored = best_frame[best_frame["current_split"].astype(str) == "anchored_oos"].copy()
    if anchored.empty:
        return pd.DataFrame(columns=["dimension", "bucket", "trade_count", "gross_pnl_r", "loss_share", "expectancy"])
    anchored["loss_component"] = np.where(_safe_numeric(anchored, "realized_R") < 0, _safe_numeric(anchored, "realized_R").abs(), 0.0)
    total_loss = float(anchored["loss_component"].sum())
    anchored["month"] = pd.to_datetime(anchored["entry_ts"], errors="coerce", utc=True).dt.to_period("M").astype(str)
    anchored["quarter"] = pd.to_datetime(anchored["entry_ts"], errors="coerce", utc=True).dt.to_period("Q").astype(str)
    rows: list[dict[str, Any]] = []
    for dimension in (
        "month",
        "quarter",
        "symbol",
        "sector_group",
        "session_timing_bucket",
        "execution_quality_bucket",
        "same_day_candidate_count",
    ):
        for bucket, scoped in anchored.groupby(dimension, dropna=False):
            gross_pnl = float(_safe_numeric(scoped, "realized_R").sum())
            loss_share = float(_safe_numeric(scoped, "loss_component").sum() / max(total_loss, 1e-9))
            rows.append(
                {
                    "dimension": dimension,
                    "bucket": str(bucket),
                    "trade_count": int(len(scoped)),
                    "gross_pnl_r": round(gross_pnl, 6),
                    "loss_share": round(loss_share, 6),
                    "expectancy": round(float(_safe_numeric(scoped, "realized_R").mean()), 6),
                }
            )
    return pd.DataFrame(rows).sort_values(["loss_share", "gross_pnl_r"], ascending=[False, True]).reset_index(drop=True)


def _anchored_cluster_diagnostics(best_frame: pd.DataFrame, base_candidates: pd.DataFrame) -> pd.DataFrame:
    anchored_selected = best_frame[best_frame["current_split"].astype(str) == "anchored_oos"].copy()
    anchored_pool = base_candidates[base_candidates["current_split"].astype(str) == "anchored_oos"].copy()
    selected_ids = set(anchored_selected["event_id"].tolist())
    anchored_pool["selected_flag"] = anchored_pool["event_id"].isin(selected_ids)
    anchored_pool["selection_status"] = np.where(anchored_pool["selected_flag"], "selected", "missed")
    anchored_pool["cluster_month"] = pd.to_datetime(anchored_pool["entry_ts"], errors="coerce", utc=True).dt.to_period("M").astype(str)
    rows: list[dict[str, Any]] = []
    for keys, scoped in anchored_pool.groupby(
        ["cluster_month", "sector_group", "session_timing_bucket", "execution_quality_bucket", "selection_status"],
        dropna=False,
    ):
        month, sector, session, quality, status = keys
        rows.append(
            {
                "cluster_month": month,
                "sector_group": sector,
                "session_timing_bucket": session,
                "execution_quality_bucket": quality,
                "selection_status": status,
                "trade_count": int(len(scoped)),
                "gross_pnl_r": round(float(_safe_numeric(scoped, "realized_R").sum()), 6),
                "expectancy": round(float(_safe_numeric(scoped, "realized_R").mean()), 6),
                "avg_rank_score": round(float(_safe_numeric(scoped, "allocator_rank_score").mean()), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["cluster_month", "gross_pnl_r"], ascending=[True, True]).reset_index(drop=True)


def _apply_capped_aggressive(frame: pd.DataFrame) -> pd.DataFrame:
    scoped = frame.copy()
    scoped["size_multiplier"] = scoped["timing_tier"].map(CAPPED_AGGRESSIVE_TEMPLATE).fillna(0.0) * BASE_CAPITAL_FRACTION / BASE_MAX_POSITIONS
    return scoped


def _candidate_from_config(
    live_df: pd.DataFrame,
    structure_name: str,
    allocator_name: str,
    allocator_timing: str,
    max_positions: int,
    capital_fraction: float,
    *,
    custom_sizing: str | None = None,
) -> pd.DataFrame:
    base = _base_candidate_pool(live_df, structure_name, allocator_timing)
    _eligible, selected = _select_with_allocator(base, allocator_name, structure_name, capital_fraction, max_positions)
    if custom_sizing == "capped_aggressive":
        selected = _apply_capped_aggressive(selected)
    selected["structure_name"] = structure_name
    selected["allocator_name"] = allocator_name
    selected["allocator_timing"] = allocator_timing
    selected["capital_bucket"] = BASE_BUCKET_NAME if abs(capital_fraction - BASE_CAPITAL_FRACTION) < 1e-9 else f"bucket_{int(capital_fraction * 100)}pct"
    selected["capital_fraction"] = capital_fraction
    selected["max_positions"] = max_positions
    return selected


def _combined_stress_retention(frame: pd.DataFrame, eligible_days: int) -> float:
    stress_df = _execution_realism_stress(frame, eligible_days)
    combined = stress_df[stress_df["stress_scenario"].astype(str) == "combined_stress"]
    return float(pd.to_numeric(combined["pnl_retention_ratio"], errors="coerce").iloc[0]) if not combined.empty else math.nan


def _deployment_uplift_score(
    baseline_row: dict[str, Any],
    candidate_row: dict[str, Any],
    combined_stress_retention: float,
) -> float:
    anchored_delta = float(candidate_row["anchored_oos_net_pnl_r"]) - float(baseline_row["anchored_oos_net_pnl_r"])
    expectancy_delta = float(candidate_row["anchored_oos_cost_adjusted_expectancy"]) - float(baseline_row["anchored_oos_cost_adjusted_expectancy"])
    drawdown_relief = float(baseline_row["max_peak_to_trough_pnl_drawdown"]) - float(candidate_row["max_peak_to_trough_pnl_drawdown"])
    rolling_preservation = max(float(candidate_row.get("rolling_oos_robustness", 0.0)) - 0.50, 0.0)
    stress_component = 0.0 if math.isnan(combined_stress_retention) else combined_stress_retention
    return round(
        (0.40 * anchored_delta)
        + (0.25 * expectancy_delta * 10.0)
        + (0.15 * drawdown_relief / 10.0)
        + (0.10 * rolling_preservation)
        + (0.10 * stress_component),
        6,
    )


def _uplift_candidate_comparison(live_df: pd.DataFrame, baseline_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    eligible_days = _eligible_days(live_df)
    baseline_eval = _evaluate_selected_configuration(
        BASE_ALLOCATOR,
        BASE_STRUCTURE,
        baseline_frame,
        eligible_days,
    )
    baseline_eval["candidate_name"] = "baseline_task354_best"
    baseline_eval["uplift_type"] = "baseline"
    baseline_eval["combined_stress_retention"] = _combined_stress_retention(baseline_frame, eligible_days)
    rows: list[dict[str, Any]] = [baseline_eval]
    frames: list[pd.DataFrame] = []

    candidate_specs = [
        ("uplift_earlier_timing", BASE_STRUCTURE, BASE_ALLOCATOR, "opening_drive_allocator", BASE_MAX_POSITIONS, BASE_CAPITAL_FRACTION, None, "single_factor"),
        ("uplift_less_concentrated_slotting", BASE_STRUCTURE, BASE_ALLOCATOR, BASE_TIMING, 3, BASE_CAPITAL_FRACTION, None, "single_factor"),
        ("uplift_capped_aggression", BASE_STRUCTURE, BASE_ALLOCATOR, BASE_TIMING, BASE_MAX_POSITIONS, BASE_CAPITAL_FRACTION, "capped_aggressive", "single_factor"),
        ("uplift_convexity_allocator", BASE_STRUCTURE, "convexity_weighted_allocator", BASE_TIMING, BASE_MAX_POSITIONS, BASE_CAPITAL_FRACTION, None, "single_factor"),
        ("combo_earlier_timing_plus_max3", BASE_STRUCTURE, BASE_ALLOCATOR, "opening_drive_allocator", 3, BASE_CAPITAL_FRACTION, None, "two_factor"),
        ("combo_earlier_timing_plus_convexity", BASE_STRUCTURE, "convexity_weighted_allocator", "opening_drive_allocator", BASE_MAX_POSITIONS, BASE_CAPITAL_FRACTION, None, "two_factor"),
        ("combo_capped_aggression_plus_max3", BASE_STRUCTURE, BASE_ALLOCATOR, BASE_TIMING, 3, BASE_CAPITAL_FRACTION, "capped_aggressive", "two_factor"),
        ("combo_convexity_plus_max3", BASE_STRUCTURE, "convexity_weighted_allocator", BASE_TIMING, 3, BASE_CAPITAL_FRACTION, None, "two_factor"),
    ]

    for candidate_name, structure_name, allocator_name, allocator_timing, max_positions, capital_fraction, custom_sizing, uplift_type in candidate_specs:
        frame = _candidate_from_config(
            live_df,
            structure_name,
            allocator_name,
            allocator_timing,
            max_positions,
            capital_fraction,
            custom_sizing=custom_sizing,
        )
        eval_row = _evaluate_selected_configuration(allocator_name, structure_name, frame, eligible_days)
        eval_row["candidate_name"] = candidate_name
        eval_row["uplift_type"] = uplift_type
        eval_row["allocator_timing"] = allocator_timing
        eval_row["max_positions"] = max_positions
        eval_row["combined_stress_retention"] = _combined_stress_retention(frame, eligible_days)
        eval_row["deployment_uplift_score"] = _deployment_uplift_score(baseline_eval, eval_row, eval_row["combined_stress_retention"])
        rows.append(eval_row)
        frame_copy = frame.copy()
        frame_copy["candidate_name"] = candidate_name
        frames.append(frame_copy)

    out = pd.DataFrame(rows)
    out["deployment_uplift_score"] = out.get("deployment_uplift_score", pd.Series(np.nan, index=out.index)).fillna(0.0)
    out = out.sort_values(
        ["deployment_uplift_score", "anchored_oos_net_pnl_r", "net_pnl_r"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    all_frames = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return out, all_frames


def _uplift_scorecard(uplift_df: pd.DataFrame, baseline_name: str = "baseline_task354_best") -> pd.DataFrame:
    baseline = uplift_df[uplift_df["candidate_name"].astype(str) == baseline_name].iloc[0]
    rows: list[dict[str, Any]] = []
    for _, row in uplift_df.iterrows():
        if str(row["candidate_name"]) == baseline_name:
            continue
        rows.append(
            {
                "candidate_name": row["candidate_name"],
                "uplift_type": row["uplift_type"],
                "anchored_oos_net_pnl_improvement": round(float(row["anchored_oos_net_pnl_r"]) - float(baseline["anchored_oos_net_pnl_r"]), 6),
                "anchored_oos_expectancy_improvement": round(float(row["anchored_oos_cost_adjusted_expectancy"]) - float(baseline["anchored_oos_cost_adjusted_expectancy"]), 6),
                "drawdown_relief": round(float(baseline["max_peak_to_trough_pnl_drawdown"]) - float(row["max_peak_to_trough_pnl_drawdown"]), 6),
                "rolling_robustness_preserved": bool(float(row["rolling_oos_robustness"]) >= max(float(baseline["rolling_oos_robustness"]) - 0.10, 0.0)),
                "stress_retention_preserved": bool(float(row["combined_stress_retention"]) >= 0.50 if not math.isnan(float(row["combined_stress_retention"])) else False),
                "deployment_uplift_score": row["deployment_uplift_score"],
            }
        )
    return pd.DataFrame(rows).sort_values(["deployment_uplift_score"], ascending=[False]).reset_index(drop=True)


def _final_decision(uplift_df: pd.DataFrame, scorecard_df: pd.DataFrame) -> pd.DataFrame:
    if scorecard_df.empty:
        return pd.DataFrame([{"decision": "NO_CLEAR_UPLIFT", "decision_reason": "No uplift candidates were produced.", "best_candidate": ""}])
    best = scorecard_df.iloc[0]
    candidate = uplift_df[uplift_df["candidate_name"].astype(str) == str(best["candidate_name"])].iloc[0]
    anchored_net = float(candidate["anchored_oos_net_pnl_r"])
    rolling_ok = bool(best["rolling_robustness_preserved"])
    stress_ok = bool(best["stress_retention_preserved"])
    uplift_score = float(candidate["deployment_uplift_score"])
    if anchored_net <= 0 and uplift_score <= 0:
        decision = "NO_CLEAR_UPLIFT"
        reason = "No candidate meaningfully improves anchored OOS while preserving deployment quality."
    elif anchored_net <= 0:
        decision = "PARTIAL_UPLIFT_RESEARCH"
        reason = "Some candidates improve anchored OOS damage, but none restore anchored OOS to positive post-cost PnL."
    elif anchored_net > 0 and rolling_ok and stress_ok and float(candidate["combined_stress_retention"]) >= 0.70:
        decision = "TINY_CAPITAL_PILOT_CANDIDATE"
        reason = "Best uplift restores positive anchored OOS and preserves rolling/stress behavior strongly enough for a tiny-capital pilot candidate."
    else:
        decision = "SHADOW_READY_UPLIFT"
        reason = "Best uplift restores anchored OOS positivity, but deployment resilience still warrants shadow-first validation."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_candidate": candidate["candidate_name"],
                "best_anchored_oos_net_pnl_r": anchored_net,
                "best_anchored_oos_cost_adjusted_expectancy": candidate["anchored_oos_cost_adjusted_expectancy"],
                "best_rolling_oos_robustness": candidate["rolling_oos_robustness"],
                "best_combined_stress_retention": candidate["combined_stress_retention"],
                "best_deployment_uplift_score": candidate["deployment_uplift_score"],
            }
        ]
    )


def _report(
    out_dir: Path,
    loss_df: pd.DataFrame,
    cluster_df: pd.DataFrame,
    uplift_df: pd.DataFrame,
    scorecard_df: pd.DataFrame,
    final_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    lines = [
        "# Task 355 - Anchored OOS Failure Uplift",
        "",
        f"- decision: {final_row['decision']}",
        f"- best_candidate: {final_row['best_candidate']}",
        f"- best_anchored_oos_net_pnl_r: {final_row['best_anchored_oos_net_pnl_r']}",
        "",
        "## Final Interpretation",
        "1. This task localizes why Task 354 failed anchored OOS and tests only a small fixed set of deployment uplifts.",
        f"2. Best uplift candidate: `{final_row['best_candidate']}`",
        f"3. Final decision: `{final_row['decision']}`",
        "",
        "## Anchored OOS Loss Decomposition",
        *(_markdown_table(loss_df.head(15))),
        "",
        "## Anchored OOS Cluster Diagnostics",
        *(_markdown_table(cluster_df.head(15))),
        "",
        "## Uplift Candidate Comparison",
        *(_markdown_table(uplift_df)),
        "",
        "## Uplift Scorecard",
        *(_markdown_table(scorecard_df)),
    ]
    (out_dir / "task_355_anchored_oos_failure_uplift.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 355: anchored OOS failure localization and deployment uplift")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    live_df, allocator_df, selected_frames_df = _build_task355_context()
    _best_row, baseline_frame = _best_baseline_frame(live_df, allocator_df, selected_frames_df)
    base_candidates = _base_candidate_pool(live_df, BASE_STRUCTURE, BASE_TIMING)
    loss_df = _anchored_loss_decomposition(baseline_frame)
    cluster_df = _anchored_cluster_diagnostics(baseline_frame, base_candidates)
    uplift_df, _all_uplift_frames = _uplift_candidate_comparison(live_df, baseline_frame)
    scorecard_df = _uplift_scorecard(uplift_df)
    final_df = _final_decision(uplift_df, scorecard_df)

    loss_df.to_csv(out_dir / "task_355_anchored_oos_loss_decomposition.csv", index=False)
    cluster_df.to_csv(out_dir / "task_355_anchored_oos_cluster_diagnostics.csv", index=False)
    uplift_df.to_csv(out_dir / "task_355_uplift_candidate_comparison.csv", index=False)
    scorecard_df.to_csv(out_dir / "task_355_uplift_scorecard.csv", index=False)
    final_df.to_csv(out_dir / "task_355_final_decision.csv", index=False)
    _report(out_dir, loss_df, cluster_df, uplift_df, scorecard_df, final_df)


if __name__ == "__main__":
    main()
