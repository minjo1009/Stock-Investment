from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_anchored_oos_failure_uplift_355 import (
    _anchored_loss_decomposition,
    _best_baseline_frame,
)
from src.backtest.analysis_structural_breakout_regime_sleeve_deployment_354 import (
    _allocator_comparison,
    _evaluate_selected_configuration,
)
from src.backtest.analysis_structural_breakout_endogenous_state_gated_allocator_357 import (
    BASE_CAPITAL_FRACTION,
    BASE_STRUCTURE,
    _apply_state_labels,
    _base_candidate_pool,
    _build_task357_context,
    _safe_numeric,
    _state_detector_diagnostics,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_358_state_gated_execution_refinement")
FRAMEWORK_ORDER = (
    "current_baseline_sleeve",
    "full_dislocation_mode",
    "reduced_dislocation_mode",
    "confirmation_sensitive_mode",
    "portfolio_utility_mode",
)
ADD_FEATURE_COLUMNS = (
    "breakout_response",
    "breakout_hold_duration_bars",
    "vwap_response",
    "price_vs_session_vwap_at_breakout",
    "volume_persistence_3bars_band348",
    "breakout_window_volume_surge_band348",
    "adverse_excursion_next_3bars_band348",
    "intraday_pullback_depth_3bars_band348",
)


def _eligible_days(frame: pd.DataFrame) -> int:
    days = pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna()
    return int(days.nunique())


def _build_task358_context() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master, _selected_df, _wide_df, live_df = _build_task357_context()
    extra_cols = ["event_id"] + [col for col in ADD_FEATURE_COLUMNS if col in master.columns]
    enriched = live_df.merge(master[extra_cols].copy(), on="event_id", how="left")
    pool = _base_candidate_pool(enriched)
    labeled_pool, thresholds = _apply_state_labels(pool)
    labeled_pool["base_score"] = _safe_numeric(labeled_pool, "base_allocator_score")
    if labeled_pool["base_score"].isna().all():
        regime = _safe_numeric(labeled_pool, "regime_score_at_decision_time").fillna(0.0)
        artifact = _safe_numeric(labeled_pool, "artifact_score_percentile_at_decision_time").fillna(0.0)
        labeled_pool["base_score"] = regime + (0.10 * artifact)
    return master, live_df, labeled_pool.reset_index(drop=True), pd.DataFrame([thresholds])


def _state_caps(framework_name: str) -> dict[str, int]:
    if framework_name == "full_dislocation_mode":
        return {"normal_continuation_state": 3, "uncertain_transition_state": 1, "crowded_dislocation_state": 0}
    if framework_name == "reduced_dislocation_mode":
        return {"normal_continuation_state": 3, "uncertain_transition_state": 2, "crowded_dislocation_state": 1}
    if framework_name == "confirmation_sensitive_mode":
        return {"normal_continuation_state": 3, "uncertain_transition_state": 2, "crowded_dislocation_state": 1}
    if framework_name == "portfolio_utility_mode":
        return {"normal_continuation_state": 3, "uncertain_transition_state": 2, "crowded_dislocation_state": 1}
    return {"normal_continuation_state": 1, "uncertain_transition_state": 1, "crowded_dislocation_state": 1}


def _stage_weights(framework_name: str, row_state: str) -> tuple[float, float]:
    if framework_name == "current_baseline_sleeve":
        return 1.0, 0.0
    if framework_name == "full_dislocation_mode":
        if row_state == "normal_continuation_state":
            return 0.50, 0.50
        if row_state == "uncertain_transition_state":
            return 0.25, 0.0
        return 0.0, 0.0
    if framework_name == "reduced_dislocation_mode":
        if row_state == "normal_continuation_state":
            return 0.50, 0.50
        if row_state == "uncertain_transition_state":
            return 0.25, 0.25
        return 0.10, 0.0
    if framework_name == "confirmation_sensitive_mode":
        if row_state == "normal_continuation_state":
            return 0.45, 0.55
        if row_state == "uncertain_transition_state":
            return 0.25, 0.20
        return 0.10, 0.10
    if row_state == "normal_continuation_state":
        return 0.45, 0.55
    if row_state == "uncertain_transition_state":
        return 0.25, 0.30
    return 0.15, 0.0


def _coarse_band_ok(value: str | float | int | None) -> bool:
    text = str(value)
    return text not in {"low", "high", "unknown", "nan", "None"}


def _add_allowed(row: pd.Series, framework_name: str, thresholds: dict[str, float], semis_budget_ok: bool) -> bool:
    row_state = str(row["endogenous_state"])
    if framework_name == "current_baseline_sleeve":
        return False
    if row_state == "crowded_dislocation_state" and framework_name in {"full_dislocation_mode", "reduced_dislocation_mode", "portfolio_utility_mode"}:
        return False
    if row_state == "crowded_dislocation_state" and framework_name == "confirmation_sensitive_mode":
        if str(row.get("session_timing_bucket", "")) in {"first_30m", "unknown"}:
            return False
    if row_state == "uncertain_transition_state":
        if str(row.get("execution_quality_bucket", "")) in {"weak", "unknown"}:
            return False
        if str(row.get("session_timing_bucket", "")) in {"first_30m", "unknown"}:
            return False

    same_day_high = float(thresholds.get("same_day_candidate_high", 0.0))
    if float(pd.to_numeric(pd.Series([row.get("same_day_candidate_count", 0.0)]), errors="coerce").fillna(0.0).iloc[0]) > same_day_high:
        return False
    if not semis_budget_ok:
        return False

    breakout_ok = (
        str(row.get("breakout_response", "breakout_hold")) == "breakout_hold"
        or float(pd.to_numeric(pd.Series([row.get("breakout_hold_duration_bars", 1.0)]), errors="coerce").fillna(1.0).iloc[0]) >= 1.0
    )
    vwap_ok = (
        str(row.get("vwap_response", "vwap_hold")) == "vwap_hold"
        or float(pd.to_numeric(pd.Series([row.get("price_vs_session_vwap_at_breakout", 1.0)]), errors="coerce").fillna(1.0).iloc[0]) > 0.0
    )
    volume_ok = _coarse_band_ok(row.get("volume_persistence_3bars_band348", "mid")) and _coarse_band_ok(row.get("breakout_window_volume_surge_band348", "mid"))
    adverse_ok = str(row.get("adverse_excursion_next_3bars_band348", "mid")) != "high" and str(row.get("intraday_pullback_depth_3bars_band348", "mid")) != "high"
    crowding_ok = str(row.get("crowding_state", "non_crowded")) != "crowded"
    return bool(breakout_ok and vwap_ok and volume_ok and adverse_ok and crowding_ok)


def _marginal_penalty(
    candidate: pd.Series,
    selected_rows: list[pd.Series],
    framework_name: str,
    thresholds: dict[str, float],
    semis_budget_used: float,
    semis_budget_cap: float,
) -> tuple[float, bool]:
    same_symbol = sum(str(row["symbol"]) == str(candidate["symbol"]) for row in selected_rows)
    if same_symbol > 0:
        return 1e6, True

    same_sector = sum(str(row["sector_group"]) == str(candidate["sector_group"]) for row in selected_rows)
    same_session = sum(str(row["session_timing_bucket"]) == str(candidate["session_timing_bucket"]) for row in selected_rows)
    same_day_count = float(pd.to_numeric(pd.Series([candidate.get("same_day_candidate_count", 0.0)]), errors="coerce").fillna(0.0).iloc[0])
    same_day_sector_count = float(pd.to_numeric(pd.Series([candidate.get("same_day_sector_candidate_count", 0.0)]), errors="coerce").fillna(0.0).iloc[0])
    penalty = 0.0
    penalty += 0.20 * same_sector
    penalty += 0.15 * same_session
    penalty += 0.04 * math.log1p(max(same_day_count, 0.0))
    penalty += 0.06 * math.log1p(max(same_day_sector_count, 0.0))
    penalty += 0.10 if str(candidate["endogenous_state"]) == "crowded_dislocation_state" else 0.0

    blocked = False
    if framework_name in {"confirmation_sensitive_mode", "portfolio_utility_mode", "reduced_dislocation_mode", "full_dislocation_mode"}:
        if str(candidate["sector_group"]) == "semis":
            penalty += 0.20 * len([row for row in selected_rows if str(row["sector_group"]) == "semis"])
            if semis_budget_used >= semis_budget_cap - 1e-9:
                blocked = True
    return penalty, blocked


def _framework_params(framework_name: str, thresholds: dict[str, float]) -> dict[str, Any]:
    same_day_sector_mid = float(thresholds.get("same_day_sector_mid", 0.0))
    params = {
        "baseline_rank_allocator": {
            "semis_count_cap": math.inf,
            "semis_daily_size_cap": math.inf,
            "first30_session_cap": math.inf,
            "use_marginal_score": False,
        },
        "full_dislocation_mode": {
            "semis_count_cap": 1,
            "semis_daily_size_cap": 0.20,
            "first30_session_cap": 1,
            "use_marginal_score": True,
        },
        "reduced_dislocation_mode": {
            "semis_count_cap": 1,
            "semis_daily_size_cap": 0.35,
            "first30_session_cap": 1,
            "use_marginal_score": True,
        },
        "confirmation_sensitive_mode": {
            "semis_count_cap": 1,
            "semis_daily_size_cap": 0.45,
            "first30_session_cap": 1,
            "use_marginal_score": True,
        },
        "portfolio_utility_mode": {
            "semis_count_cap": 99,
            "semis_daily_size_cap": 0.60,
            "first30_session_cap": 1,
            "use_marginal_score": True,
            "sector_count_reference": same_day_sector_mid,
        },
    }
    return params[framework_name]


def _select_framework_frame(scoped: pd.DataFrame, framework_name: str, thresholds: dict[str, float]) -> pd.DataFrame:
    if scoped.empty:
        return scoped.copy()
    params = _framework_params(framework_name, thresholds)
    caps = _state_caps(framework_name)
    base = scoped.copy().sort_values(["day_key", "base_score", "trade_id"], ascending=[True, False, True])
    selected_frames: list[pd.DataFrame] = []
    for _, day_df in base.groupby("day_key", sort=True):
        day_df = day_df.copy()
        day_state = str(day_df["day_endogenous_state"].iloc[0])
        day_cap = int(caps.get(day_state, 0))
        if day_cap <= 0:
            continue
        selected_rows: list[pd.Series] = []
        semis_budget_used = 0.0
        semis_count = 0
        first30_count = 0
        available = day_df.copy()
        while len(selected_rows) < day_cap and not available.empty:
            scored: list[dict[str, Any]] = []
            for idx, row in available.iterrows():
                penalty, blocked_budget = _marginal_penalty(
                    row,
                    selected_rows,
                    framework_name,
                    thresholds,
                    semis_budget_used,
                    float(params["semis_daily_size_cap"]),
                )
                adjusted = float(row["base_score"]) - penalty if params["use_marginal_score"] else float(row["base_score"])
                scored.append(
                    {
                        "idx": idx,
                        "adjusted_score": adjusted,
                        "overlap_penalty": penalty,
                        "blocked_by_semis_budget": blocked_budget,
                    }
                )
            score_df = pd.DataFrame(scored).sort_values(["blocked_by_semis_budget", "adjusted_score"], ascending=[True, False])
            if score_df.empty:
                break
            top = score_df.iloc[0]
            row = available.loc[int(top["idx"])].copy()
            if bool(top["blocked_by_semis_budget"]):
                break
            if str(row["sector_group"]) == "semis" and semis_count >= int(params["semis_count_cap"]):
                available = available.drop(index=int(top["idx"]))
                continue
            if str(row["session_timing_bucket"]) == "first_30m" and first30_count >= int(params["first30_session_cap"]):
                available = available.drop(index=int(top["idx"]))
                continue

            probe_weight, add_weight = _stage_weights(framework_name, str(row["endogenous_state"]))
            base_size = float(_safe_numeric(pd.DataFrame([row]), "base_size_multiplier").iloc[0]) if "base_size_multiplier" in row.index else 0.0
            if base_size == 0.0:
                base_size = BASE_CAPITAL_FRACTION / max(day_cap, 1)
            semis_budget_ok = not (str(row["sector_group"]) == "semis" and (semis_budget_used + base_size * (probe_weight + add_weight)) > float(params["semis_daily_size_cap"]) + 1e-9)
            add_allowed = _add_allowed(row, framework_name, thresholds, semis_budget_ok)
            final_weight = probe_weight + (add_weight if add_allowed else 0.0)
            if final_weight <= 0.0:
                available = available.drop(index=int(top["idx"]))
                continue

            row["framework_name"] = framework_name
            row["allocator_variant"] = "baseline_rank_allocator" if framework_name == "current_baseline_sleeve" else "marginal_utility_allocator"
            row["base_score"] = float(row["base_score"])
            row["marginal_score"] = float(top["adjusted_score"])
            row["overlap_penalty"] = float(top["overlap_penalty"])
            row["blocked_by_semis_budget"] = False
            row["state_level_gross_cap"] = day_cap
            row["semis_budget_used"] = semis_budget_used
            row["base_size_multiplier"] = base_size
            row["probe_weight"] = probe_weight
            row["add_weight"] = add_weight if add_allowed else 0.0
            row["stage_weight"] = final_weight
            row["participation_stage"] = "probe_plus_add" if add_allowed and add_weight > 0 else "probe_only"
            row["size_multiplier"] = base_size * final_weight
            row["allocator_rank"] = len(selected_rows) + 1
            selected_rows.append(row)
            if str(row["sector_group"]) == "semis":
                semis_budget_used += base_size * final_weight
                semis_count += 1
            if str(row["session_timing_bucket"]) == "first_30m":
                first30_count += 1
            available = available.drop(index=int(top["idx"]))
        if selected_rows:
            selected_frames.append(pd.DataFrame(selected_rows))
    if not selected_frames:
        return base.iloc[0:0].copy()
    return pd.concat(selected_frames, ignore_index=True).sort_values(["entry_ts", "trade_id"]).reset_index(drop=True)


def _baseline_frame(live_df: pd.DataFrame) -> pd.DataFrame:
    allocator_df, _competition_df, selected_frames_df = _allocator_comparison(live_df)
    _best_row, baseline_frame = _best_baseline_frame(live_df, allocator_df, selected_frames_df)
    baseline_frame = baseline_frame.copy().reset_index(drop=True)
    baseline_frame["framework_name"] = "current_baseline_sleeve"
    baseline_frame["allocator_variant"] = "baseline_rank_allocator"
    baseline_frame["base_score"] = np.nan
    baseline_frame["marginal_score"] = np.nan
    baseline_frame["overlap_penalty"] = 0.0
    baseline_frame["blocked_by_semis_budget"] = False
    baseline_frame["semis_budget_used"] = 0.0
    baseline_frame["probe_weight"] = 1.0
    baseline_frame["add_weight"] = 0.0
    baseline_frame["stage_weight"] = 1.0
    baseline_frame["participation_stage"] = "full_participation"
    return baseline_frame


def _framework_metrics(framework_name: str, frame: pd.DataFrame, eligible_days: int) -> dict[str, Any]:
    eval_row = _evaluate_selected_configuration("marginal_utility_allocator", BASE_STRUCTURE, frame, eligible_days)
    anchored = frame[frame["current_split"].astype(str) == "anchored_oos"].copy()
    anchored["loss_component"] = np.where(_safe_numeric(anchored, "realized_R") < 0, _safe_numeric(anchored, "realized_R").abs(), 0.0)
    total_loss = float(anchored["loss_component"].sum())
    semis_loss_share = float(anchored.loc[anchored["sector_group"].astype(str) == "semis", "loss_component"].sum() / max(total_loss, 1e-9)) if not anchored.empty else math.nan
    first30_loss_share = float(anchored.loc[anchored["session_timing_bucket"].astype(str).isin({"first_30m", "unknown"}), "loss_component"].sum() / max(total_loss, 1e-9)) if not anchored.empty else math.nan
    eval_row.update(
        {
            "framework_name": framework_name,
            "allocator_variant": "baseline_rank_allocator" if framework_name == "current_baseline_sleeve" else "marginal_utility_allocator",
            "anchored_oos_drawdown": eval_row["mdd_pct"],
            "semis_loss_share": round(semis_loss_share, 6) if not math.isnan(semis_loss_share) else math.nan,
            "first30_or_unknown_loss_share": round(first30_loss_share, 6) if not math.isnan(first30_loss_share) else math.nan,
        }
    )
    return eval_row


def _semis_budget_comparison(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for framework_name in ("reduced_dislocation_mode", "confirmation_sensitive_mode", "portfolio_utility_mode"):
        frame = frames.get(framework_name, pd.DataFrame()).copy()
        anchored = frame[frame["current_split"].astype(str) == "anchored_oos"].copy()
        rows.append(
            {
                "framework_name": framework_name,
                "trade_count": int(len(frame)),
                "semis_trade_share": round(float(frame["sector_group"].astype(str).eq("semis").mean()), 6) if not frame.empty else math.nan,
                "anchored_semis_trade_share": round(float(anchored["sector_group"].astype(str).eq("semis").mean()), 6) if not anchored.empty else math.nan,
                "avg_semis_budget_used": round(float(_safe_numeric(frame, "semis_budget_used").mean()), 6) if "semis_budget_used" in frame.columns and not frame.empty else math.nan,
                "blocked_by_semis_budget_count": int(frame["blocked_by_semis_budget"].astype(bool).sum()) if "blocked_by_semis_budget" in frame.columns else 0,
            }
        )
    return pd.DataFrame(rows)


def _staged_execution_playbook(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for framework_name in ("current_baseline_sleeve", "reduced_dislocation_mode", "confirmation_sensitive_mode", "portfolio_utility_mode"):
        frame = frames.get(framework_name, pd.DataFrame()).copy()
        if frame.empty:
            continue
        for stage_name, scoped in frame.groupby("participation_stage", dropna=False):
            rows.append(
                {
                    "framework_name": framework_name,
                    "participation_stage": str(stage_name),
                    "trade_count": int(len(scoped)),
                    "avg_probe_weight": round(float(_safe_numeric(scoped, "probe_weight").mean()), 6) if "probe_weight" in scoped.columns else 1.0,
                    "avg_add_weight": round(float(_safe_numeric(scoped, "add_weight").mean()), 6) if "add_weight" in scoped.columns else 0.0,
                    "expectancy": round(float(_safe_numeric(scoped, "realized_R").mean()), 6),
                    "semis_share": round(float(scoped["sector_group"].astype(str).eq("semis").mean()), 6),
                }
            )
    return pd.DataFrame(rows)


def _failure_cluster_contribution(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for name, frame in frames.items():
        out = _anchored_loss_decomposition(frame)
        if out.empty:
            continue
        out = out.copy()
        out["framework_name"] = name
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _final_decision(comparison_df: pd.DataFrame) -> pd.DataFrame:
    baseline = comparison_df[comparison_df["framework_name"].astype(str) == "current_baseline_sleeve"].iloc[0]
    benchmark = comparison_df[comparison_df["framework_name"].astype(str) == "full_dislocation_mode"].iloc[0]
    practical = comparison_df[comparison_df["framework_name"].astype(str).isin({"reduced_dislocation_mode", "confirmation_sensitive_mode", "portfolio_utility_mode"})].copy()
    practical = practical.sort_values(
        ["anchored_oos_net_pnl_r", "semis_loss_share", "capital_utilization", "net_pnl_r"],
        ascending=[False, True, False, False],
    )
    best_practical = practical.iloc[0] if not practical.empty else benchmark

    anchored_improvement = float(best_practical["anchored_oos_net_pnl_r"]) - float(baseline["anchored_oos_net_pnl_r"])
    semis_improvement = float(baseline["semis_loss_share"]) - float(best_practical["semis_loss_share"])
    if anchored_improvement > 0 and semis_improvement > 0 and float(best_practical["rolling_oos_robustness"]) >= float(baseline["rolling_oos_robustness"]) and float(best_practical["capital_utilization"]) >= 0.60:
        decision = "DISLOCATION_AWARE_STAGED_SLEEVE"
        reason = "A practical non-skip state-gated sleeve improves anchored OOS and concentration damage while retaining usable capital utilization."
    elif anchored_improvement > 0 and semis_improvement >= 0:
        decision = "PRACTICAL_STATE_GATED_SLEEVE"
        reason = "A practical state-gated sleeve improves anchored OOS and concentration damage, but staged execution is not yet strong enough for a full dislocation-aware promotion."
    elif float(benchmark["anchored_oos_net_pnl_r"]) > float(best_practical["anchored_oos_net_pnl_r"]):
        decision = "BENCHMARK_SKIP_ONLY"
        reason = "Only the benchmark skip-heavy dislocation mode materially outperforms baseline damage control."
    else:
        decision = "NO_PRACTICAL_UPLIFT"
        reason = "Practical non-skip refinements do not improve anchored OOS and concentration enough over baseline."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_practical_framework": best_practical["framework_name"],
                "best_practical_anchored_oos_net_pnl_r": best_practical["anchored_oos_net_pnl_r"],
                "benchmark_anchored_oos_net_pnl_r": benchmark["anchored_oos_net_pnl_r"],
                "anchored_oos_improvement_vs_baseline": round(anchored_improvement, 6),
                "semis_loss_share_improvement_vs_baseline": round(semis_improvement, 6),
            }
        ]
    )


def _report(
    out_dir: Path,
    state_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    semis_df: pd.DataFrame,
    staged_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    final_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    lines = [
        "# Task 358 - Practical State-Gated Execution Refinement",
        "",
        f"- decision: {final_row['decision']}",
        f"- best_practical_framework: {final_row['best_practical_framework']}",
        f"- anchored_oos_improvement_vs_baseline: {final_row['anchored_oos_improvement_vs_baseline']}",
        "",
        "## Final Interpretation",
        "1. This task refines Task 357 toward a practical non-skip state-gated + staged execution sleeve.",
        f"2. Final decision: `{final_row['decision']}`",
        f"3. Best practical framework: `{final_row['best_practical_framework']}`",
        "",
        "## State Detector Diagnostics",
        *(_markdown_table(state_df)),
        "",
        "## Framework Comparison",
        *(_markdown_table(comparison_df)),
        "",
        "## Semis Budget Comparison",
        *(_markdown_table(semis_df)),
        "",
        "## Staged Execution Playbook",
        *(_markdown_table(staged_df)),
        "",
        "## Failure Cluster Contribution",
        *(_markdown_table(failure_df.head(20))),
    ]
    (out_dir / "task_358_state_gated_execution_refinement.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 358: practical state-gated + staged continuation sleeve refinement")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    live_master, live_df, labeled_pool, threshold_df = _build_task358_context()
    thresholds = threshold_df.iloc[0].to_dict() if not threshold_df.empty else {}

    baseline_frame = _baseline_frame(live_df)
    label_cols = ["event_id", "endogenous_state", "day_endogenous_state", "base_score"]
    for col in ADD_FEATURE_COLUMNS:
        if col in labeled_pool.columns and col not in label_cols:
            label_cols.append(col)
    baseline_frame = baseline_frame.merge(labeled_pool[label_cols].drop_duplicates(subset=["event_id"]), on="event_id", how="left")

    frames: dict[str, pd.DataFrame] = {"current_baseline_sleeve": baseline_frame}
    for framework_name in FRAMEWORK_ORDER[1:]:
        frames[framework_name] = _select_framework_frame(labeled_pool, framework_name, thresholds)

    eligible_days = _eligible_days(labeled_pool)
    comparison_rows = [_framework_metrics(name, frame, eligible_days) for name, frame in frames.items()]
    comparison_df = pd.DataFrame(comparison_rows).sort_values(
        ["anchored_oos_net_pnl_r", "capital_utilization", "net_pnl_r"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    state_df = _state_detector_diagnostics(labeled_pool)
    semis_df = _semis_budget_comparison(frames)
    staged_df = _staged_execution_playbook(frames)
    failure_df = _failure_cluster_contribution(frames)
    final_df = _final_decision(comparison_df)

    state_df.to_csv(out_dir / "task_358_state_detector_refinement.csv", index=False)
    comparison_df.to_csv(out_dir / "task_358_framework_comparison.csv", index=False)
    semis_df.to_csv(out_dir / "task_358_semis_budget_comparison.csv", index=False)
    staged_df.to_csv(out_dir / "task_358_staged_execution_playbook.csv", index=False)
    failure_df.to_csv(out_dir / "task_358_failure_cluster_contribution.csv", index=False)
    final_df.to_csv(out_dir / "task_358_final_decision.csv", index=False)
    _report(out_dir, state_df, comparison_df, semis_df, staged_df, failure_df, final_df)


if __name__ == "__main__":
    main()
