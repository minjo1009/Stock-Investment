from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_state_gated_execution_refinement_358 import (
    _baseline_frame,
    _build_task358_context,
    _framework_metrics,
    _select_framework_frame,
)
from src.risk.healthy_expansion_policy import (
    HealthyExpansionPolicyDecision,
    HealthyExpansionPolicyInputs,
    evaluate_healthy_expansion_policy,
)
from src.risk.shadow_adapter import ShadowAdapterConfig, build_shadow_risk_decision


DEFAULT_OUT_DIR = Path("docs/reports/task_360_shadow_integration")
FAILURE_WINDOWS = {
    "full_period": None,
    "anchored_oos": "anchored_oos",
    "2025-12": ("2025-12-01", "2025-12-31"),
    "2026-01": ("2026-01-01", "2026-01-31"),
}


@dataclass(frozen=True)
class ShadowArtifacts:
    baseline_frame: pd.DataFrame
    benchmark_frame: pd.DataFrame
    shadow_log: pd.DataFrame
    baseline_summary: pd.DataFrame
    engine_summary: pd.DataFrame
    window_comparison: pd.DataFrame
    factor_diagnostics: pd.DataFrame
    baseline_preserved: bool
    baseline_metrics_unchanged: bool


@dataclass(frozen=True)
class QualityAwarePolicyDecision:
    policy_stage: str
    size_multiplier: float
    add_allowed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class HealthyAggressivePolicyDecision:
    policy_label: str
    size_multiplier: float
    add_allowed: bool
    reasons: tuple[str, ...]


def _safe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _eligible_days(frame: pd.DataFrame) -> int:
    days = pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna()
    return int(days.nunique())


def _build_task360_context() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    _live_master, live_df, labeled_pool, threshold_df = _build_task358_context()
    thresholds = threshold_df.iloc[0].to_dict() if not threshold_df.empty else {}

    baseline_frame = _baseline_frame(live_df)
    merge_cols = ["event_id"]
    extra_cols = [
        "trade_id",
        "day_key",
        "current_split",
        "sector_group",
        "session_timing_bucket",
        "execution_quality_bucket",
        "gap_environment_state",
        "market_breadth_state",
        "sector_leadership_state",
        "dispersion_20d",
        "mean_pairwise_corr",
        "semis_concentration_ratio",
        "base_score",
        "endogenous_state",
        "day_endogenous_state",
        "same_day_candidate_count",
        "same_day_sector_candidate_count",
    ]
    for col in extra_cols:
        if col in labeled_pool.columns and col not in baseline_frame.columns:
            merge_cols.append(col)
    if len(merge_cols) > 1:
        baseline_frame = baseline_frame.merge(labeled_pool[merge_cols].drop_duplicates(subset=["event_id"]), on="event_id", how="left")
    benchmark_frame = _select_framework_frame(labeled_pool, "full_dislocation_mode", thresholds)
    return baseline_frame.reset_index(drop=True), benchmark_frame.reset_index(drop=True), labeled_pool.reset_index(drop=True), thresholds


def _empty_shadow_log() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "timestamp",
            "symbol",
            "trade_id",
            "signal_id",
            "strategy_id",
            "state_label",
            "continuation_risk_score",
            "gross_exposure_multiplier",
            "allow_new_entry",
            "allow_add",
            "factor_exposure_violated",
            "violated_factors",
            "staged_gate_stage",
            "staged_add_allowed",
            "shadow_reasons",
            "participation_quality_label",
            "participation_expansion_score",
            "participation_fragility_score",
            "participation_confidence",
            "participation_reasons",
            "baseline_realized_R",
            "shadow_size_multiplier",
            "shadow_realized_R_proxy",
            "quality_aware_policy_stage",
            "quality_aware_add_allowed",
            "quality_aware_size_multiplier",
            "quality_aware_realized_R_proxy",
            "quality_aware_reasons",
            "healthy_aggressive_policy_label",
            "healthy_aggressive_final_size_multiplier",
            "healthy_aggressive_final_add_allowed",
            "healthy_aggressive_realized_R_proxy",
            "healthy_aggressive_reasons",
            "hypothetical_blocked_entry",
            "hypothetical_blocked_add",
            "hypothetical_reduced_entry",
            "hypothetical_reduced_add",
            "quality_aware_blocked_entry",
            "quality_aware_blocked_add",
            "quality_aware_reduced_entry",
            "quality_aware_reduced_add",
            "healthy_aggressive_blocked_entry",
            "healthy_aggressive_blocked_add",
            "healthy_aggressive_reduced_entry",
            "healthy_aggressive_reduced_add",
            "fragile_crowding_relax_violation",
            "dislocation_relax_violation",
            "current_split",
            "day_key",
            "sector_group",
        ]
    )


def _quality_aware_policy(decision: Any) -> QualityAwarePolicyDecision:
    label = str(decision.participation_quality_decision.quality_label)
    stage_name = str(decision.staged_gate_decision.participation_stage)
    reasons = [f"quality_label={label}"]
    if decision.factor_exposure_violated or not decision.exposure_decision.allow_new_entry:
        reasons.append("factor_or_entry_block_preserved")
        return QualityAwarePolicyDecision(
            policy_stage="BLOCK",
            size_multiplier=0.0,
            add_allowed=False,
            reasons=tuple(reasons),
        )

    old_size = float(decision.shadow_size_multiplier)
    if label == "HEALTHY_EXPANSION":
        if stage_name == "stage_2_add":
            reasons.append("healthy_expansion_relaxed_add")
            return QualityAwarePolicyDecision(
                policy_stage="ADD_ALLOWED",
                size_multiplier=max(old_size, 0.70),
                add_allowed=True,
                reasons=tuple(reasons),
            )
        reasons.append("healthy_expansion_probe_relaxation")
        return QualityAwarePolicyDecision(
            policy_stage="PROBE_ONLY",
            size_multiplier=max(old_size, 0.35),
            add_allowed=False,
            reasons=tuple(reasons),
        )
    if label == "NEUTRAL_PARTICIPATION":
        if stage_name == "stage_2_add" and decision.exposure_decision.allow_add:
            reasons.append("neutral_participation_moderate_add")
            return QualityAwarePolicyDecision(
                policy_stage="ADD_ALLOWED",
                size_multiplier=max(old_size, 0.45),
                add_allowed=True,
                reasons=tuple(reasons),
            )
        reasons.append("neutral_participation_probe")
        return QualityAwarePolicyDecision(
            policy_stage="PROBE_ONLY",
            size_multiplier=max(old_size, 0.20),
            add_allowed=False,
            reasons=tuple(reasons),
        )
    if label == "FRAGILE_CROWDING":
        reasons.append("fragile_crowding_strict_suppression")
        if old_size <= 0.0:
            return QualityAwarePolicyDecision(
                policy_stage="BLOCK",
                size_multiplier=0.0,
                add_allowed=False,
                reasons=tuple(reasons),
            )
        return QualityAwarePolicyDecision(
            policy_stage="PROBE_ONLY",
            size_multiplier=min(old_size, 0.15),
            add_allowed=False,
            reasons=tuple(reasons),
        )
    reasons.append("unknown_quality_conservative_probe")
    return QualityAwarePolicyDecision(
        policy_stage="PROBE_ONLY",
        size_multiplier=max(old_size, 0.15),
        add_allowed=False,
        reasons=tuple(reasons),
    )


def _healthy_expansion_aggressive_policy(decision: Any) -> HealthyAggressivePolicyDecision:
    factor_budget_multiplier = 1.0 if not decision.factor_exposure_violated else 0.0
    staged_add_allowed = str(decision.staged_gate_decision.participation_stage) == "stage_2_add"
    result = evaluate_healthy_expansion_policy(
        HealthyExpansionPolicyInputs(
            quality_label=str(decision.participation_quality_decision.quality_label),
            expansion_score=float(decision.participation_quality_decision.expansion_score),
            fragility_score=float(decision.participation_quality_decision.fragility_score),
            confidence=float(decision.participation_quality_decision.confidence),
            state_label=str(decision.state_decision.state_label),
            continuation_risk_score=float(decision.state_decision.continuation_risk_score),
            staged_gate_stage=str(decision.staged_gate_decision.participation_stage),
            staged_add_allowed=staged_add_allowed,
            factor_budget_allowed=not decision.factor_exposure_violated,
            factor_budget_multiplier=factor_budget_multiplier,
            gross_exposure_multiplier=float(decision.exposure_decision.gross_exposure_multiplier),
            current_size_multiplier=float(decision.shadow_size_multiplier),
        )
    )
    return HealthyAggressivePolicyDecision(
        policy_label=result.policy_label,
        size_multiplier=float(result.final_size_multiplier),
        add_allowed=bool(result.final_add_allowed),
        reasons=result.reasons,
    )


def _shadow_log_from_baseline(
    baseline_frame: pd.DataFrame,
    candidate_pool: pd.DataFrame,
    config: ShadowAdapterConfig | None = None,
) -> pd.DataFrame:
    if baseline_frame.empty:
        return _empty_shadow_log()
    cfg = config or ShadowAdapterConfig()
    rows: list[dict[str, Any]] = []
    for day_key, day_baseline in baseline_frame.sort_values(["entry_ts", "trade_id"]).groupby("day_key", dropna=False):
        day_slice = candidate_pool[candidate_pool["day_key"].astype(str) == str(day_key)].copy()
        current_gross = 0.0
        from src.risk.factor_budget import FactorBudgetState

        budget_state = FactorBudgetState()
        for _, row in day_baseline.iterrows():
            decision = build_shadow_risk_decision(
                row,
                day_slice,
                current_gross_exposure=current_gross,
                factor_budget_state=budget_state,
                config=cfg,
            )
            stage_name = str(decision.staged_gate_decision.participation_stage)
            staged_add_allowed = stage_name == "stage_2_add"
            quality_policy = _quality_aware_policy(decision)
            healthy_policy = _healthy_expansion_aggressive_policy(decision)
            blocked_entry = not decision.exposure_decision.allow_new_entry or decision.shadow_size_multiplier <= 0.0
            blocked_add = not decision.exposure_decision.allow_add or not staged_add_allowed
            reduced_entry = decision.exposure_decision.allow_new_entry and decision.exposure_decision.gross_exposure_multiplier < 0.999
            reduced_add = staged_add_allowed and decision.shadow_size_multiplier < 0.999
            quality_blocked_entry = quality_policy.policy_stage == "BLOCK" or quality_policy.size_multiplier <= 0.0
            quality_blocked_add = not quality_policy.add_allowed
            quality_reduced_entry = quality_policy.policy_stage != "BLOCK" and quality_policy.size_multiplier < 0.999
            quality_reduced_add = quality_policy.add_allowed and quality_policy.size_multiplier < 0.999
            healthy_blocked_entry = healthy_policy.policy_label == "KEEP_SUPPRESSED" and healthy_policy.size_multiplier <= 0.0
            healthy_blocked_add = not healthy_policy.add_allowed
            healthy_reduced_entry = healthy_policy.policy_label not in {"NO_CHANGE", "KEEP_SUPPRESSED"} and healthy_policy.size_multiplier < 0.999
            healthy_reduced_add = healthy_policy.add_allowed and healthy_policy.size_multiplier < 0.999
            realized_r = _safe_numeric(pd.DataFrame([row]), "realized_R").fillna(0.0).iloc[0]
            shadow_proxy = float(realized_r) * float(decision.shadow_size_multiplier)
            quality_proxy = float(realized_r) * float(quality_policy.size_multiplier)
            healthy_proxy = float(realized_r) * float(healthy_policy.size_multiplier)
            fragile_violation = bool(
                str(decision.participation_quality_decision.quality_label) == "FRAGILE_CROWDING"
                and (healthy_policy.add_allowed or healthy_policy.size_multiplier > decision.shadow_size_multiplier + 1e-12)
            )
            dislocation_violation = bool(
                str(decision.state_decision.state_label) == "DISLOCATION"
                and (healthy_policy.add_allowed or healthy_policy.size_multiplier > decision.shadow_size_multiplier + 1e-12)
            )

            rows.append(
                {
                    "timestamp": row.get("entry_ts"),
                    "symbol": row.get("symbol"),
                    "trade_id": row.get("trade_id"),
                    "signal_id": decision.signal_id,
                    "strategy_id": decision.strategy_id,
                    "state_label": decision.state_decision.state_label,
                    "continuation_risk_score": decision.state_decision.continuation_risk_score,
                    "gross_exposure_multiplier": decision.exposure_decision.gross_exposure_multiplier,
                    "allow_new_entry": decision.exposure_decision.allow_new_entry,
                    "allow_add": decision.exposure_decision.allow_add,
                    "factor_exposure_violated": decision.factor_exposure_violated,
                    "violated_factors": "|".join(decision.violated_factors),
                    "staged_gate_stage": stage_name,
                    "staged_add_allowed": staged_add_allowed,
                    "shadow_reasons": "|".join(
                        tuple(decision.state_decision.reasons)
                        + tuple(decision.exposure_decision.reasons)
                        + tuple(decision.block_reasons)
                    ),
                    "participation_quality_label": decision.participation_quality_decision.quality_label,
                    "participation_expansion_score": decision.participation_quality_decision.expansion_score,
                    "participation_fragility_score": decision.participation_quality_decision.fragility_score,
                    "participation_confidence": decision.participation_quality_decision.confidence,
                    "participation_reasons": "|".join(decision.participation_quality_decision.reasons),
                    "baseline_realized_R": realized_r,
                    "shadow_size_multiplier": decision.shadow_size_multiplier,
                    "shadow_realized_R_proxy": shadow_proxy,
                    "quality_aware_policy_stage": quality_policy.policy_stage,
                    "quality_aware_add_allowed": quality_policy.add_allowed,
                    "quality_aware_size_multiplier": quality_policy.size_multiplier,
                    "quality_aware_realized_R_proxy": quality_proxy,
                    "quality_aware_reasons": "|".join(quality_policy.reasons),
                    "healthy_aggressive_policy_label": healthy_policy.policy_label,
                    "healthy_aggressive_final_size_multiplier": healthy_policy.size_multiplier,
                    "healthy_aggressive_final_add_allowed": healthy_policy.add_allowed,
                    "healthy_aggressive_realized_R_proxy": healthy_proxy,
                    "healthy_aggressive_reasons": "|".join(healthy_policy.reasons),
                    "hypothetical_blocked_entry": blocked_entry,
                    "hypothetical_blocked_add": blocked_add,
                    "hypothetical_reduced_entry": reduced_entry,
                    "hypothetical_reduced_add": reduced_add,
                    "quality_aware_blocked_entry": quality_blocked_entry,
                    "quality_aware_blocked_add": quality_blocked_add,
                    "quality_aware_reduced_entry": quality_reduced_entry,
                    "quality_aware_reduced_add": quality_reduced_add,
                    "healthy_aggressive_blocked_entry": healthy_blocked_entry,
                    "healthy_aggressive_blocked_add": healthy_blocked_add,
                    "healthy_aggressive_reduced_entry": healthy_reduced_entry,
                    "healthy_aggressive_reduced_add": healthy_reduced_add,
                    "fragile_crowding_relax_violation": fragile_violation,
                    "dislocation_relax_violation": dislocation_violation,
                    "current_split": row.get("current_split"),
                    "day_key": row.get("day_key"),
                    "sector_group": row.get("sector_group"),
                }
            )
            if decision.exposure_decision.allow_new_entry and decision.shadow_size_multiplier > 0:
                current_gross += float(decision.shadow_size_multiplier)
                budget_state = decision.next_factor_budget_state
    return pd.DataFrame(rows)


def _proxy_shadow_frame(
    baseline_frame: pd.DataFrame,
    shadow_log: pd.DataFrame,
    realized_proxy_column: str = "shadow_realized_R_proxy",
    size_column: str = "shadow_size_multiplier",
) -> pd.DataFrame:
    if baseline_frame.empty:
        return baseline_frame.copy()
    proxy = baseline_frame.copy().reset_index(drop=True)
    merged = proxy.merge(
        shadow_log[["trade_id", size_column, realized_proxy_column]],
        on="trade_id",
        how="left",
    )
    if "realized_R" in merged.columns:
        merged["realized_R"] = _safe_numeric(merged, realized_proxy_column).fillna(_safe_numeric(merged, "realized_R"))
    merged[size_column] = _safe_numeric(merged, size_column).fillna(1.0)
    return merged


def _window_mask(frame: pd.DataFrame, window_name: str) -> pd.Series:
    if window_name == "full_period":
        return pd.Series(True, index=frame.index)
    if window_name == "anchored_oos":
        return frame["current_split"].astype(str).eq("anchored_oos")
    start, end = FAILURE_WINDOWS[window_name]
    ts = pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True)
    return (ts >= pd.Timestamp(start, tz="UTC")) & (ts <= pd.Timestamp(end, tz="UTC"))


def _window_comparison(
    baseline_frame: pd.DataFrame,
    shadow_log: pd.DataFrame,
    shadow_proxy_frame: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    merged = baseline_frame.merge(
        shadow_log[
            [
                "trade_id",
                "hypothetical_blocked_entry",
                "hypothetical_blocked_add",
                "hypothetical_reduced_entry",
                "hypothetical_reduced_add",
                "continuation_risk_score",
                "state_label",
                "factor_exposure_violated",
                "staged_add_allowed",
            ]
        ],
        on="trade_id",
        how="left",
    )
    for window_name in FAILURE_WINDOWS:
        mask = _window_mask(merged, window_name)
        base = merged[mask].copy()
        proxy = shadow_proxy_frame[_window_mask(shadow_proxy_frame, window_name)].copy()
        if base.empty:
            continue
        rows.append(
            {
                "window_name": window_name,
                "baseline_trade_count": int(len(base)),
                "shadow_blocked_entries": int(base["hypothetical_blocked_entry"].fillna(False).astype(bool).sum()),
                "shadow_blocked_adds": int(base["hypothetical_blocked_add"].fillna(False).astype(bool).sum()),
                "shadow_reduced_entries": int(base["hypothetical_reduced_entry"].fillna(False).astype(bool).sum()),
                "shadow_reduced_adds": int(base["hypothetical_reduced_add"].fillna(False).astype(bool).sum()),
                "avg_continuation_risk_score": round(float(_safe_numeric(base, "continuation_risk_score").mean()), 6),
                "state_label_distribution": "|".join(
                    f"{k}:{v}" for k, v in base["state_label"].fillna("UNKNOWN").value_counts(normalize=True).round(4).sort_index().items()
                ),
                "factor_violation_rate": round(float(base["factor_exposure_violated"].fillna(False).astype(bool).mean()), 6),
                "dislocation_add_block_rate": round(
                    float(
                        (
                            base["state_label"].fillna("").astype(str).eq("DISLOCATION")
                            & ~base["staged_add_allowed"].fillna(False).astype(bool)
                        ).mean()
                    ),
                    6,
                ),
                "baseline_net_pnl_r": round(float(_safe_numeric(base, "realized_R").sum()), 6),
                "shadow_gated_pnl_proxy_r": round(float(_safe_numeric(proxy, "realized_R").sum()), 6),
                "failure_window_loss_reduction_proxy": round(
                    float(_safe_numeric(base, "realized_R").clip(upper=0).sum() - _safe_numeric(proxy, "realized_R").clip(upper=0).sum()),
                    6,
                ),
            }
        )

    for bucket_name, bucket_mask in (
        ("semis_bucket", merged["sector_group"].astype(str).eq("semis")),
        ("non_semis_bucket", ~merged["sector_group"].astype(str).eq("semis")),
    ):
        base = merged[bucket_mask].copy()
        proxy_mask = shadow_proxy_frame["sector_group"].astype(str).eq("semis")
        if bucket_name == "non_semis_bucket":
            proxy_mask = ~proxy_mask
        proxy = shadow_proxy_frame[proxy_mask].copy()
        if base.empty:
            continue
        rows.append(
            {
                "window_name": bucket_name,
                "baseline_trade_count": int(len(base)),
                "shadow_blocked_entries": int(base["hypothetical_blocked_entry"].fillna(False).astype(bool).sum()),
                "shadow_blocked_adds": int(base["hypothetical_blocked_add"].fillna(False).astype(bool).sum()),
                "shadow_reduced_entries": int(base["hypothetical_reduced_entry"].fillna(False).astype(bool).sum()),
                "shadow_reduced_adds": int(base["hypothetical_reduced_add"].fillna(False).astype(bool).sum()),
                "avg_continuation_risk_score": round(float(_safe_numeric(base, "continuation_risk_score").mean()), 6),
                "state_label_distribution": "|".join(
                    f"{k}:{v}" for k, v in base["state_label"].fillna("UNKNOWN").value_counts(normalize=True).round(4).sort_index().items()
                ),
                "factor_violation_rate": round(float(base["factor_exposure_violated"].fillna(False).astype(bool).mean()), 6),
                "dislocation_add_block_rate": round(
                    float(
                        (
                            base["state_label"].fillna("").astype(str).eq("DISLOCATION")
                            & ~base["staged_add_allowed"].fillna(False).astype(bool)
                        ).mean()
                    ),
                    6,
                ),
                "baseline_net_pnl_r": round(float(_safe_numeric(base, "realized_R").sum()), 6),
                "shadow_gated_pnl_proxy_r": round(float(_safe_numeric(proxy, "realized_R").sum()), 6),
                "failure_window_loss_reduction_proxy": round(
                    float(_safe_numeric(base, "realized_R").clip(upper=0).sum() - _safe_numeric(proxy, "realized_R").clip(upper=0).sum()),
                    6,
                ),
            }
        )
    return pd.DataFrame(rows)


def _factor_diagnostics(shadow_log: pd.DataFrame) -> pd.DataFrame:
    if shadow_log.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    exploded = shadow_log.copy()
    violated_text = exploded["violated_factors"].fillna("").astype(str)
    violated_text = violated_text.where(violated_text.ne(""), np.nan)
    exploded["violated_factor"] = violated_text.str.split("|")
    exploded = exploded.explode("violated_factor")
    violated = exploded[exploded["violated_factor"].notna()].copy()
    for factor_name, scoped in violated.groupby("violated_factor", dropna=False):
        rows.append(
            {
                "factor_name": str(factor_name),
                "violation_count": int(len(scoped)),
                "violation_rate": round(float(len(scoped) / max(len(shadow_log), 1)), 6),
                "avg_risk_score": round(float(_safe_numeric(scoped, "continuation_risk_score").mean()), 6),
                "blocked_entry_rate": round(float(scoped["hypothetical_blocked_entry"].astype(bool).mean()), 6),
            }
        )
    for state_label, scoped in shadow_log.groupby("state_label", dropna=False):
        rows.append(
            {
                "factor_name": f"STATE::{state_label}",
                "violation_count": int(scoped["factor_exposure_violated"].fillna(False).astype(bool).sum()),
                "violation_rate": round(float(scoped["factor_exposure_violated"].fillna(False).astype(bool).mean()), 6),
                "avg_risk_score": round(float(_safe_numeric(scoped, "continuation_risk_score").mean()), 6),
                "blocked_entry_rate": round(float(scoped["hypothetical_blocked_entry"].astype(bool).mean()), 6),
            }
        )
    return pd.DataFrame(rows)


def _engine_summary(
    baseline_metrics: dict[str, Any],
    benchmark_metrics: dict[str, Any],
    shadow_proxy_metrics: dict[str, Any],
    shadow_log: pd.DataFrame,
    baseline_preserved: bool,
) -> pd.DataFrame:
    blocked_entries = int(shadow_log["hypothetical_blocked_entry"].fillna(False).astype(bool).sum()) if not shadow_log.empty else 0
    blocked_adds = int(shadow_log["hypothetical_blocked_add"].fillna(False).astype(bool).sum()) if not shadow_log.empty else 0
    reduced_entries = int(shadow_log["hypothetical_reduced_entry"].fillna(False).astype(bool).sum()) if not shadow_log.empty else 0
    reduced_adds = int(shadow_log["hypothetical_reduced_add"].fillna(False).astype(bool).sum()) if not shadow_log.empty else 0
    state_dist = (
        "|".join(f"{k}:{v}" for k, v in shadow_log["state_label"].value_counts(normalize=True).round(4).sort_index().items())
        if not shadow_log.empty
        else ""
    )
    return pd.DataFrame(
        [
            {
                "mode": "baseline",
                "net_pnl_r": baseline_metrics.get("net_pnl_r"),
                "anchored_oos_net_pnl_r": baseline_metrics.get("anchored_oos_net_pnl_r"),
                "trade_count": baseline_metrics.get("trade_count"),
                "rolling_oos_robustness": baseline_metrics.get("rolling_oos_robustness"),
                "blocked_entries": 0,
                "blocked_adds": 0,
                "reduced_entries": 0,
                "reduced_adds": 0,
                "state_distribution": "",
                "baseline_preserved": baseline_preserved,
            },
            {
                "mode": "shadow_gated_proxy",
                "net_pnl_r": shadow_proxy_metrics.get("net_pnl_r"),
                "anchored_oos_net_pnl_r": shadow_proxy_metrics.get("anchored_oos_net_pnl_r"),
                "trade_count": shadow_proxy_metrics.get("trade_count"),
                "rolling_oos_robustness": shadow_proxy_metrics.get("rolling_oos_robustness"),
                "blocked_entries": blocked_entries,
                "blocked_adds": blocked_adds,
                "reduced_entries": reduced_entries,
                "reduced_adds": reduced_adds,
                "state_distribution": state_dist,
                "baseline_preserved": baseline_preserved,
            },
            {
                "mode": "full_dislocation_benchmark",
                "net_pnl_r": benchmark_metrics.get("net_pnl_r"),
                "anchored_oos_net_pnl_r": benchmark_metrics.get("anchored_oos_net_pnl_r"),
                "trade_count": benchmark_metrics.get("trade_count"),
                "rolling_oos_robustness": benchmark_metrics.get("rolling_oos_robustness"),
                "blocked_entries": math.nan,
                "blocked_adds": math.nan,
                "reduced_entries": math.nan,
                "reduced_adds": math.nan,
                "state_distribution": "",
                "baseline_preserved": baseline_preserved,
            },
        ]
    )


def generate_shadow_artifacts(enable_shadow_state_engine: bool = False) -> ShadowArtifacts:
    baseline_frame, benchmark_frame, labeled_pool, _thresholds = _build_task360_context()
    baseline_before = baseline_frame.copy(deep=True)
    eligible_days = _eligible_days(labeled_pool)
    baseline_metrics = _framework_metrics("current_baseline_sleeve", baseline_frame.copy(), eligible_days)
    benchmark_metrics = _framework_metrics("full_dislocation_mode", benchmark_frame.copy(), eligible_days)

    if not enable_shadow_state_engine:
        shadow_log = _empty_shadow_log()
        shadow_proxy_frame = baseline_frame.copy()
        shadow_proxy_metrics = baseline_metrics.copy()
    else:
        shadow_log = _shadow_log_from_baseline(baseline_frame.copy(), labeled_pool.copy())
        shadow_proxy_frame = _proxy_shadow_frame(baseline_frame.copy(), shadow_log)
        shadow_proxy_metrics = _framework_metrics("shadow_gated_proxy", shadow_proxy_frame.copy(), eligible_days)

    baseline_preserved = baseline_before.equals(baseline_frame)
    baseline_after_metrics = _framework_metrics("current_baseline_sleeve", baseline_frame.copy(), eligible_days)
    metric_keys = (
        "net_pnl_r",
        "anchored_oos_net_pnl_r",
        "trade_count",
        "rolling_oos_robustness",
        "capital_utilization",
        "concentration",
    )
    baseline_metrics_unchanged = all(
        baseline_metrics.get(key) == baseline_after_metrics.get(key)
        for key in metric_keys
    )
    baseline_summary = pd.DataFrame([baseline_metrics])
    engine_summary = _engine_summary(
        baseline_metrics,
        benchmark_metrics,
        shadow_proxy_metrics,
        shadow_log,
        baseline_preserved and baseline_metrics_unchanged,
    )
    window_comparison = _window_comparison(baseline_frame, shadow_log, shadow_proxy_frame) if enable_shadow_state_engine else pd.DataFrame()
    factor_diagnostics = _factor_diagnostics(shadow_log) if enable_shadow_state_engine else pd.DataFrame()
    return ShadowArtifacts(
        baseline_frame=baseline_frame,
        benchmark_frame=benchmark_frame,
        shadow_log=shadow_log,
        baseline_summary=baseline_summary,
        engine_summary=engine_summary,
        window_comparison=window_comparison,
        factor_diagnostics=factor_diagnostics,
        baseline_preserved=baseline_preserved,
        baseline_metrics_unchanged=baseline_metrics_unchanged,
    )


def _report(out_dir: Path, artifacts: ShadowArtifacts, enable_shadow_state_engine: bool) -> None:
    baseline_row = artifacts.engine_summary[artifacts.engine_summary["mode"].astype(str) == "baseline"].iloc[0]
    shadow_row = artifacts.engine_summary[artifacts.engine_summary["mode"].astype(str) == "shadow_gated_proxy"].iloc[0]
    benchmark_row = artifacts.engine_summary[artifacts.engine_summary["mode"].astype(str) == "full_dislocation_benchmark"].iloc[0]
    lines = [
        "# Task 360 - Read-only Shadow Integration & Historical Replay Evaluation",
        "",
        f"- shadow_enabled: {enable_shadow_state_engine}",
        f"- baseline_preserved: {artifacts.baseline_preserved}",
        f"- baseline_metrics_unchanged: {artifacts.baseline_metrics_unchanged}",
        f"- baseline_net_pnl_r: {baseline_row['net_pnl_r']}",
        f"- shadow_proxy_net_pnl_r: {shadow_row['net_pnl_r']}",
        f"- benchmark_net_pnl_r: {benchmark_row['net_pnl_r']}",
        "",
        "## Summary",
        "1. Baseline continuation sleeve behavior remains unchanged.",
        "2. Shadow mode computes read-only state/factor/exposure/staged decisions on copied rows.",
        "3. Shadow proxy metrics are diagnostic only and do not alter actual fills or baseline PnL.",
        "",
        "## Engine Summary",
        *(_markdown_table(artifacts.engine_summary)),
        "",
        "## Window Comparison",
        *(_markdown_table(artifacts.window_comparison if not artifacts.window_comparison.empty else pd.DataFrame([{'status': 'shadow_disabled_or_no_data'}]))),
        "",
        "## Factor Diagnostics",
        *(_markdown_table(artifacts.factor_diagnostics if not artifacts.factor_diagnostics.empty else pd.DataFrame([{'status': 'shadow_disabled_or_no_violations'}]))),
    ]
    (out_dir / "task_360_shadow_integration.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 360: read-only shadow integration and historical replay evaluation")
    parser.add_argument("--enable-shadow-state-engine", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = generate_shadow_artifacts(enable_shadow_state_engine=bool(args.enable_shadow_state_engine))
    artifacts.shadow_log.to_csv(out_dir / "task_360_shadow_decision_log.csv", index=False)
    artifacts.engine_summary.to_csv(out_dir / "task_360_shadow_engine_summary.csv", index=False)
    artifacts.window_comparison.to_csv(out_dir / "task_360_shadow_window_comparison.csv", index=False)
    artifacts.factor_diagnostics.to_csv(out_dir / "task_360_shadow_factor_diagnostics.csv", index=False)
    _report(out_dir, artifacts, bool(args.enable_shadow_state_engine))


if __name__ == "__main__":
    main()
